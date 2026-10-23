"""Uwierzytelnianie i autoryzacja - wspolne dla klientow, operatorow i sesji wsparcia.

Trzy rozlaczne typy tokenow:
  * `fwu_` - sesja klienta (app.forvium.com),
  * `fwo_` - sesja operatora (admin.forvium.com),
  * `fws_` - sesja wsparcia (app.forvium.com w trybie wsparcia).

API klienta (`/api/app`) przyjmuje `fwu_` i `fws_`, API administracyjne
(`/api/admin`) wylacznie `fwo_`. Sesja wsparcia przechodzi przez TE SAME
sprawdzenia RBAC co klient (`require_org_permission`) - nie ma osobnej sciezki
omijajacej uprawnienia.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import Depends, Request
from sqlalchemy import select, text

from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError, get_ctx
from forvium.core.security import (
    OPERATOR_TOKEN_PREFIX,
    SUPPORT_TOKEN_PREFIX,
    USER_TOKEN_PREFIX,
    token_digest,
)
from forvium.identity.models import User, UserSession
from forvium.organizations.models import Membership, Organization
from forvium.organizations.rbac import Permission, permissions_for_role
from forvium.platform_admin.rbac import PlatformPermission, platform_permissions
from forvium.support_access import service as support
from forvium.support_access.models import SupportSession

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
# Jedyne trasy zapisu dostepne w trybie wsparcia (zakonczenie wlasnej sesji).
SUPPORT_WRITE_ALLOWLIST = frozenset({"/api/app/support/session/end"})


def _bearer(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return None


def _load_user_session(ctx: Ctx, token: str, kind: str) -> tuple[UserSession, User] | None:
    sess = ctx.db.scalar(select(UserSession).where(UserSession.token_hash == token_digest(token)))
    if sess is None or sess.kind != kind or sess.revoked_at is not None or clock.now() >= sess.expires_at:
        return None
    user = ctx.db.get(User, sess.user_id)
    if user is None or not user.is_active:
        return None
    return sess, user


# ----------------------------------------------------------------- app.forvium.com


@dataclass
class AppPrincipal:
    """Podmiot w API klienta.

    `actor` to rzeczywista osoba (klient albo operator w trybie wsparcia),
    `reference_user` - uzytkownik, w ktorego kontekscie dziala aplikacja.
    """

    kind: str  # "user" | "support"
    actor: User
    reference_user: User
    user_session: UserSession | None = None
    support: support.ValidatedSupportSession | None = None
    extra: dict = field(default_factory=dict)

    @property
    def is_support(self) -> bool:
        return self.kind == "support"

    @property
    def support_session(self) -> SupportSession | None:
        return self.support.session if self.support else None


def get_app_principal(request: Request, ctx: Ctx = Depends(get_ctx)) -> AppPrincipal:
    token = _bearer(request)
    if token and token.startswith(SUPPORT_TOKEN_PREFIX):
        validated = support.validate_support_token(ctx, token)
        s = validated.session
        # Druga linia obrony: RLS w PostgreSQL ogranicza cala transakcje do organizacji sesji.
        if ctx.db.get_bind().dialect.name == "postgresql":
            ctx.db.execute(text("SELECT set_config('forvium.support_org', :org, true)"), {"org": s.organization_id})
        # Kontekst dla middleware audytu: kazda operacja API w trybie wsparcia.
        request.state.audit_actor = {
            "action": "support.api_call",
            "actor_user_id": s.operator_user_id,
            "actor_type": "support",
            "on_behalf_of_user_id": s.reference_user_id,
            "organization_id": s.organization_id,
            "support_session_id": s.id,
            "support_request_id": s.request_id,
        }
        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)
        if request.method not in SAFE_METHODS and route_path not in SUPPORT_WRITE_ALLOWLIST:
            raise DomainError(403, "support_read_only", "Tryb wsparcia jest tylko do odczytu (READ_ONLY).")
        return AppPrincipal("support", validated.operator, validated.reference_user, support=validated)

    if token and token.startswith(USER_TOKEN_PREFIX):
        loaded = _load_user_session(ctx, token, "user")
        if loaded:
            sess, user = loaded
            return AppPrincipal("user", user, user, user_session=sess)

    if token and token.startswith(OPERATOR_TOKEN_PREFIX):
        # Sesja operatora nigdy nie jest akceptowana w API klienta.
        ctx.audit.record("app.access_denied", outcome="denied", actor_type="anonymous", ip_address=ctx.ip,
                         details={"reason": "operator_token_on_app_api"})
    raise DomainError(401, "unauthenticated", "Wymagane uwierzytelnienie.")


def require_user_principal(principal: AppPrincipal = Depends(get_app_principal)) -> AppPrincipal:
    """Operacje na wlasnym koncie (haslo, MFA, tokeny) - nigdy w trybie wsparcia."""
    if principal.is_support:
        raise DomainError(403, "forbidden_in_support_mode", "Operacja niedostepna w trybie wsparcia Forvium.")
    return principal


@dataclass
class OrgAccess:
    organization: Organization
    principal: AppPrincipal
    permissions: frozenset[Permission]
    # None = wszystkie jednostki; zbior = ograniczenie wynikajace ze zgody
    unit_ids: set[str] | None = None


def _resolve_org_access(ctx: Ctx, principal: AppPrincipal, org_id: str) -> OrgAccess:
    if principal.is_support:
        s = principal.support
        assert s is not None
        if s.session.organization_id != org_id:
            raise DomainError(403, "support_org_mismatch", "Sesja wsparcia nie obejmuje tej organizacji.")
        return OrgAccess(
            s.organization, principal, s.permissions, support.unit_filter_ids(ctx, org_id, s.session.unit_ids)
        )

    org = ctx.db.get(Organization, org_id)
    member = ctx.db.scalar(
        select(Membership).where(Membership.organization_id == org_id, Membership.user_id == principal.actor.id)
    )
    if org is None or org.deleted_at is not None or member is None:
        raise DomainError(404, "organization_not_found", "Nie znaleziono organizacji.")
    return OrgAccess(org, principal, permissions_for_role(member.role))


def require_org_permission(permission: Permission):
    """Zaleznosc RBAC dla tras `/api/app/orgs/{org_id}/...`."""

    def dependency(
        org_id: str,
        principal: AppPrincipal = Depends(get_app_principal),
        ctx: Ctx = Depends(get_ctx),
    ) -> OrgAccess:
        access = _resolve_org_access(ctx, principal, org_id)
        if permission not in access.permissions:
            if principal.is_support:
                raise DomainError(403, "forbidden_in_support_mode",
                                  "Operacja niedostepna w trybie wsparcia Forvium lub poza zakresem zgody.")
            raise DomainError(403, "forbidden", "Brak uprawnien.")
        return access

    return dependency


# --------------------------------------------------------------- admin.forvium.com


@dataclass
class OperatorPrincipal:
    user: User
    session: UserSession
    permissions: frozenset[PlatformPermission]


def get_operator(request: Request, ctx: Ctx = Depends(get_ctx)) -> OperatorPrincipal:
    token = _bearer(request)
    if token and token.startswith(OPERATOR_TOKEN_PREFIX):
        loaded = _load_user_session(ctx, token, "operator")
        if loaded and loaded[1].platform_role:
            sess, user = loaded
            request.state.audit_actor = {
                "action": "operator.api_call",
                "actor_user_id": user.id,
                "actor_type": "operator",
            }
            return OperatorPrincipal(user, sess, platform_permissions(user.platform_role))
    if token and token.startswith(SUPPORT_TOKEN_PREFIX):
        ctx.audit.record("admin.access_denied", outcome="denied", actor_type="anonymous", ip_address=ctx.ip,
                         details={"reason": "support_token_on_admin_api"})
    raise DomainError(401, "unauthenticated", "Wymagane uwierzytelnienie operatora.")


def require_platform_permission(permission: PlatformPermission):
    def dependency(op: OperatorPrincipal = Depends(get_operator)) -> OperatorPrincipal:
        if permission not in op.permissions:
            raise DomainError(403, "forbidden", "Brak uprawnien operatora.")
        return op

    return dependency
