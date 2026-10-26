"""Zarzadzanie platforma (admin.forvium.com): organizacje, konta klientow, operatorzy, zgloszenia.

Zasady:
* kazda zmiana wymaga ponownej weryfikacji operatora (klucz WebAuthn albo jednorazowy
  kod TOTP), trafia do audytu, a zainteresowani dostaja powiadomienie;
* Forvium nie zna hasel ani sekretow MFA - nowe konta aktywuje sam uzytkownik linkiem
  z e-maila (identity/activation.py); czlonkami istniejacej organizacji zarzadza klient;
* nadanie roli uprzywilejowanej (administrator platformy, oficer bezpieczenstwa)
  wymaga zatwierdzenia przez oficera bezpieczenstwa (4 oczy, inna osoba niz zlecajacy);
* nikt nie zmienia wlasnej roli ani nie blokuje wlasnego konta, a platforma zawsze ma
  co najmniej jednego aktywnego administratora.

Kolejnosc w kazdej operacji: walidacja i odmowy -> ponowna weryfikacja MFA -> zapis.
"""

from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select, update

from forvium.access import OperatorPrincipal, require_platform_permission
from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError, get_ctx
from forvium.identity import activation
from forvium.identity.models import User, UserSession
from forvium.identity.webauthn import WebAuthnCredential
from forvium.organizations.models import Membership, Organization, OrgUnit
from forvium.organizations.rbac import OrgRole
from forvium.platform_admin.rbac import PRIVILEGED_ROLES, PlatformPermission as PP, PlatformRole, platform_permissions
from forvium.support_access.models import SessionStatus, SupportSession
from forvium.support_tickets import service as tickets
from forvium.support_tickets.models import SupportTicket, TicketPriority, TicketStatus
from forvium.core.i18n import L, default_lang, join, tr

router = APIRouter(prefix="/api/admin", tags=["platform management (admin)"])

PLANS = ("standard", "business", "enterprise")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ROLE_LABELS = {
    "support_l1": "Support L1", "support_l2": "Support L2", "support_lead": "Kierownik supportu",
    "security_officer": "Oficer bezpieczeństwa", "platform_admin": "Administrator platformy",
}


class StepUp(BaseModel):
    mfa_code: str | None = None
    webauthn: dict | None = None


def _deny(ctx: Ctx, op: OperatorPrincipal, action: str, status: int, code: str, message: str, **details) -> DomainError:
    ctx.audit.record(action, outcome="denied", actor_user_id=op.user.id, actor_type="operator", ip_address=ctx.ip,
                     details={"reason": code, **details})
    return DomainError(status, code, message)


def _step_up(ctx: Ctx, op: OperatorPrincipal, body: StepUp, action: str) -> None:
    from forvium.support_access.service import _verify_operator_mfa

    _verify_operator_mfa(ctx, op.user, body.mfa_code, action, webauthn=body.webauthn)


def _log(ctx: Ctx, op: OperatorPrincipal, action: str, *, organization_id: str | None = None, **details) -> None:
    ctx.audit.log(ctx.db, action, actor_user_id=op.user.id, actor_type="operator", ip_address=ctx.ip,
                  organization_id=organization_id, details=details)


def _iso(d):
    return d.isoformat() + "Z" if d else None


def _account_state(u: User) -> str:
    if u.blocked_at is not None:
        return "blocked"
    if u.activated_at is None:
        return "pending_activation"
    return "active" if u.is_active else "inactive"


def _revoke_user_sessions(ctx: Ctx, user: User) -> None:
    ctx.db.execute(update(UserSession).where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
                   .values(revoked_at=clock.now()))


def _end_support_sessions(ctx: Ctx, op: OperatorPrincipal, reason: str, *conditions) -> int:
    from forvium.support_access.service import _terminate_session

    sessions = list(ctx.db.scalars(select(SupportSession).where(SupportSession.status == SessionStatus.ACTIVE,
                                                                *conditions)))
    for s in sessions:
        _terminate_session(ctx, s, SessionStatus.REVOKED, reason, op.user.id, actor_type="operator")
    return len(sessions)


def _org_admins(ctx: Ctx, organization_id: str, exclude: str | None = None) -> list[User]:
    from forvium.support_access.service import _org_approvers

    return _org_approvers(ctx, organization_id, exclude_user_id=exclude)


def _operators_with(ctx: Ctx, permission: PP, exclude: set[str] = frozenset()) -> list[User]:
    return [u for u in ctx.db.scalars(select(User).where(User.platform_role.is_not(None), User.is_active.is_(True)))
            if permission in platform_permissions(u.platform_role) and u.id not in exclude]


def _check_email(ctx: Ctx, op: OperatorPrincipal, action: str, email: str) -> str:
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 320:
        raise _deny(ctx, op, action, 422, "email_invalid", "Nieprawidłowy adres e-mail.")
    return email


# =========================================================================== organizacje


class OrganizationCreateIn(StepUp):
    name: str = Field(min_length=2, max_length=200)
    subscription_plan: str = "standard"
    locale: Literal["pl", "en"] | None = None  # domyslnie FORVIUM_DEFAULT_LOCALE
    owner_email: str
    owner_name: str = Field(min_length=2, max_length=200)


class OrganizationUpdateIn(StepUp):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    subscription_plan: str | None = None
    locale: Literal["pl", "en"] | None = None


def _org_out(o: Organization, members: int = 0, open_tickets: int = 0) -> dict:
    return {"id": o.id, "name": o.name, "subscription_plan": o.subscription_plan, "created_at": _iso(o.created_at),
            "deleted_at": _iso(o.deleted_at), "members": members, "open_tickets": open_tickets,
            "dual_approval": bool(o.support_dual_approval), "locale": o.locale}


@router.get("/organizations")
def list_organizations(q: str = "", op: OperatorPrincipal = Depends(require_platform_permission(PP.USERS_READ)),
                       ctx: Ctx = Depends(get_ctx)):
    stmt = select(Organization).order_by(Organization.name).limit(200)
    if q:
        stmt = stmt.where(Organization.name.ilike(f"%{q}%"))
    members = dict(ctx.db.execute(select(Membership.organization_id, func.count()).group_by(Membership.organization_id)).all())
    tickets = dict(ctx.db.execute(select(SupportTicket.organization_id, func.count())
                                  .where(SupportTicket.status != TicketStatus.CLOSED)
                                  .group_by(SupportTicket.organization_id)).all())
    return {"organizations": [_org_out(o, members.get(o.id, 0), tickets.get(o.id, 0)) for o in ctx.db.scalars(stmt)],
            "plans": list(PLANS)}


@router.get("/organizations/{org_id}")
def organization_detail(org_id: str, op: OperatorPrincipal = Depends(require_platform_permission(PP.USERS_READ)),
                        ctx: Ctx = Depends(get_ctx)):
    org = ctx.db.get(Organization, org_id)
    if org is None:
        raise DomainError(404, "organization_not_found", "Nie znaleziono organizacji.")
    members = ctx.db.execute(select(User, Membership.role).join(Membership, Membership.user_id == User.id)
                             .where(Membership.organization_id == org.id).order_by(User.email)).all()
    units = ctx.db.scalars(select(OrgUnit).where(OrgUnit.organization_id == org.id).order_by(OrgUnit.name))
    tickets = ctx.db.scalars(select(SupportTicket).where(SupportTicket.organization_id == org.id)
                             .order_by(SupportTicket.created_at.desc()))
    return {
        "organization": _org_out(org),
        "members": [{"user_id": u.id, "email": u.email, "display_name": u.display_name, "role": role,
                     "state": _account_state(u)} for u, role in members],
        "units": [{"id": u.id, "name": u.name, "parent_id": u.parent_id} for u in units],
        "tickets": [_ticket_out(t) for t in tickets],
    }


@router.post("/organizations")
def create_organization(body: OrganizationCreateIn,
                        op: OperatorPrincipal = Depends(require_platform_permission(PP.ORGS_MANAGE)),
                        ctx: Ctx = Depends(get_ctx)):
    """Nowa organizacja z pierwszym wlascicielem. Nowe konto wlasciciel aktywuje sam (link w e-mailu)."""
    action = "platform.organization.create"
    if body.subscription_plan not in PLANS:
        raise _deny(ctx, op, action, 422, "plan_invalid", "Nieznany plan subskrypcji.")
    email = _check_email(ctx, op, action, body.owner_email)
    owner = ctx.db.scalar(select(User).where(User.email == email))
    if owner is not None and owner.platform_role is not None:
        raise _deny(ctx, op, action, 409, "owner_is_operator",
                    "Konto operatora Forvium nie może być właścicielem organizacji klienta.")
    if owner is not None and owner.blocked_at is not None:
        raise _deny(ctx, op, action, 409, "owner_blocked", "Konto wskazanego właściciela jest zablokowane.")
    _step_up(ctx, op, body, action)

    now = clock.now()
    org = Organization(name=body.name.strip(), subscription_plan=body.subscription_plan, created_at=now,
                       locale=body.locale or default_lang(), settings={}, smtp_config={}, webhooks=[], secrets={})
    ctx.db.add(org)
    ctx.db.flush()
    ctx.db.add(OrgUnit(organization_id=org.id, name=tr("Centrala", org.locale)))
    new_account = owner is None
    if new_account:
        owner = User(email=email, display_name=body.owner_name.strip(), password_hash=activation.unusable_password_hash(),
                     is_active=False, created_at=now)
        ctx.db.add(owner)
        ctx.db.flush()
    ctx.db.add(Membership(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER))
    ctx.db.flush()
    if new_account:
        activation.issue(ctx, owner, kind="user", created_by=op.user.id)
    else:
        ctx.notifications.notify(ctx.db, [owner], event="platform.organization.owner_added",
                                 title=L("Jesteś właścicielem organizacji {org} w Forvium Watch", org=org.name),
                                 body=L("Forvium założyło organizację i wskazało Cię jako właściciela."),
                                 organization_id=org.id)
    _log(ctx, op, "platform.organization.created", organization_id=org.id, name=org.name,
         plan=org.subscription_plan, locale=org.locale, owner_user_id=owner.id, owner_new_account=new_account)
    return {"organization": _org_out(org, 1), "owner": {"id": owner.id, "email": owner.email,
                                                         "state": _account_state(owner)}}


@router.put("/organizations/{org_id}")
def update_organization(org_id: str, body: OrganizationUpdateIn,
                        op: OperatorPrincipal = Depends(require_platform_permission(PP.ORGS_MANAGE)),
                        ctx: Ctx = Depends(get_ctx)):
    action = "platform.organization.update"
    org = ctx.db.get(Organization, org_id)
    if org is None or org.deleted_at is not None:
        raise DomainError(404, "organization_not_found", "Nie znaleziono organizacji.")
    if body.subscription_plan is not None and body.subscription_plan not in PLANS:
        raise _deny(ctx, op, action, 422, "plan_invalid", "Nieznany plan subskrypcji.")
    changes = {}
    if body.name is not None and body.name.strip() != org.name:
        changes["name"] = {"from": org.name, "to": body.name.strip()}
    if body.subscription_plan is not None and body.subscription_plan != org.subscription_plan:
        changes["subscription_plan"] = {"from": org.subscription_plan, "to": body.subscription_plan}
    if body.locale is not None and body.locale != org.locale:
        changes["locale"] = {"from": org.locale, "to": body.locale}
    if not changes:
        return {"organization": _org_out(org)}
    _step_up(ctx, op, body, action)
    if "name" in changes:
        org.name = changes["name"]["to"]
    if "subscription_plan" in changes:
        org.subscription_plan = changes["subscription_plan"]["to"]
    if "locale" in changes:
        org.locale = changes["locale"]["to"]
    _log(ctx, op, "platform.organization.updated", organization_id=org.id, changes=changes)
    described = ", ".join(f"{k}: {v['from']} -> {v['to']}" for k, v in changes.items())
    ctx.notifications.notify(ctx.db, _org_admins(ctx, org.id), event="platform.organization.updated",
                             title=L("Forvium zmieniło dane organizacji {org}", org=org.name),
                             body=L("Zmiany: {changes}.", changes=described), organization_id=org.id)
    return {"organization": _org_out(org)}


# ======================================================================= konta klientow


class BlockIn(StepUp):
    reason: str = Field(min_length=5, max_length=500)


def _customer(ctx: Ctx, user_id: str) -> User:
    user = ctx.db.get(User, user_id)
    if user is None or user.platform_role is not None:
        raise DomainError(404, "user_not_found", "Nie znaleziono użytkownika.")
    return user


def _user_org_ids(ctx: Ctx, user: User) -> list[str]:
    return list(ctx.db.scalars(select(Membership.organization_id).where(Membership.user_id == user.id)))


@router.post("/users/{user_id}/block")
def block_user(user_id: str, body: BlockIn, op: OperatorPrincipal = Depends(require_platform_permission(PP.USERS_MANAGE)),
               ctx: Ctx = Depends(get_ctx)):
    """Blokada konta klienta (np. przejete konto). Klient widzi to w powiadomieniach i audycie."""
    action = "platform.user.block"
    user = _customer(ctx, user_id)
    if user.blocked_at is not None:
        raise _deny(ctx, op, action, 409, "already_blocked", "Konto jest już zablokowane.", user_id=user.id)
    _step_up(ctx, op, body, action)
    user.blocked_at, user.blocked_reason, user.is_active = clock.now(), body.reason.strip(), False
    _revoke_user_sessions(ctx, user)
    ended = _end_support_sessions(ctx, op, "reference_user_blocked", SupportSession.reference_user_id == user.id)
    orgs = _user_org_ids(ctx, user)
    for org_id in orgs:
        _log(ctx, op, "platform.user.blocked", organization_id=org_id, user_id=user.id, reason=user.blocked_reason,
             support_sessions_ended=ended)
        ctx.notifications.notify(ctx.db, _org_admins(ctx, org_id, exclude=user.id), event="platform.user.blocked",
                                 title=L("Forvium zablokowało konto {email}", email=user.email),
                                 body=L("Powód: {reason}", reason=user.blocked_reason), organization_id=org_id)
    if not orgs:
        _log(ctx, op, "platform.user.blocked", user_id=user.id, reason=user.blocked_reason)
    ctx.notifications.email_only(ctx.db, user, subject=L("Twoje konto Forvium Watch zostało zablokowane"),
                                 body=L("Powód: {reason}\nW razie pytań skontaktuj się z supportem Forvium.",
                                        reason=user.blocked_reason))
    return {"user": {"id": user.id, "state": _account_state(user)}}


@router.post("/users/{user_id}/unblock")
def unblock_user(user_id: str, body: StepUp,
                 op: OperatorPrincipal = Depends(require_platform_permission(PP.USERS_MANAGE)),
                 ctx: Ctx = Depends(get_ctx)):
    action = "platform.user.unblock"
    user = _customer(ctx, user_id)
    if user.blocked_at is None:
        raise _deny(ctx, op, action, 409, "not_blocked", "Konto nie jest zablokowane.", user_id=user.id)
    _step_up(ctx, op, body, action)
    user.blocked_at, user.blocked_reason = None, None
    user.is_active = user.activated_at is not None
    for org_id in _user_org_ids(ctx, user) or [None]:
        _log(ctx, op, "platform.user.unblocked", organization_id=org_id, user_id=user.id)
        if org_id:
            ctx.notifications.notify(ctx.db, _org_admins(ctx, org_id, exclude=user.id), event="platform.user.unblocked",
                                     title=L("Forvium odblokowało konto {email}", email=user.email),
                                     body=L("Konto znów może się logować."),
                                     organization_id=org_id)
    return {"user": {"id": user.id, "state": _account_state(user)}}


@router.post("/users/{user_id}/reset-access")
def reset_user_access(user_id: str, body: BlockIn,
                      op: OperatorPrincipal = Depends(require_platform_permission(PP.USERS_MANAGE)),
                      ctx: Ctx = Depends(get_ctx)):
    """Reset dostepu klienta (np. jedyny wlasciciel zgubil telefon). Forvium nie poznaje nowego
    hasla - link aktywacyjny trafia na e-mail konta; administratorzy organizacji dostaja informacje."""
    action = "platform.user.reset_access"
    user = _customer(ctx, user_id)
    if user.blocked_at is not None or user.activated_at is None:
        raise _deny(ctx, op, action, 409, "not_resettable", "Konto jest zablokowane albo czeka na aktywację.")
    _step_up(ctx, op, body, action)
    activation.reset_access(ctx, user, created_by=op.user.id, actor_type="operator")
    for org_id in _user_org_ids(ctx, user) or [None]:
        _log(ctx, op, "platform.user.access_reset", organization_id=org_id, user_id=user.id, reason=body.reason)
        if org_id:
            ctx.notifications.notify(ctx.db, _org_admins(ctx, org_id, exclude=user.id), event="platform.user.access_reset",
                                     title=L("Forvium zresetowało dostęp {email}", email=user.email),
                                     body=L("Powód: {reason}. Link aktywacyjny wysłano na adres tej osoby.",
                                            reason=body.reason),
                                     organization_id=org_id)
    return {"user": {"id": user.id, "state": _account_state(user)}}


@router.post("/users/{user_id}/resend-activation")
def resend_activation(user_id: str, body: StepUp, op: OperatorPrincipal = Depends(require_platform_permission(PP.USERS_READ)),
                      ctx: Ctx = Depends(get_ctx)):
    """Nowy link aktywacyjny (na adres e-mail konta). Klient: USERS_MANAGE, operator: OPERATORS_MANAGE."""
    action = "platform.user.resend_activation"
    user = ctx.db.get(User, user_id)
    if user is None:
        raise DomainError(404, "user_not_found", "Nie znaleziono użytkownika.")
    needed = PP.OPERATORS_MANAGE if user.platform_role else PP.USERS_MANAGE
    if needed not in op.permissions:
        raise _deny(ctx, op, action, 403, "operator_not_permitted", "Brak uprawnień operatora.")
    if user.activated_at is not None or user.blocked_at is not None:
        raise _deny(ctx, op, action, 409, "not_pending_activation", "Konto nie czeka na aktywację.")
    _step_up(ctx, op, body, action)
    activation.issue(ctx, user, kind="operator" if user.platform_role else "user", created_by=op.user.id)
    return {"ok": True}


# ============================================================================ operatorzy


class OperatorCreateIn(StepUp):
    email: str
    display_name: str = Field(min_length=2, max_length=200)
    role: str


class RoleIn(StepUp):
    role: str


class RejectIn(StepUp):
    reason: str | None = Field(default=None, max_length=500)


def _operator_out(u: User, keys: set[str]) -> dict:
    return {"id": u.id, "email": u.email, "display_name": u.display_name, "role": u.platform_role,
            "role_label": tr(ROLE_LABELS.get(u.platform_role or "", u.platform_role)), "state": _account_state(u),
            "has_security_key": u.id in keys, "pending_role": u.pending_platform_role,
            "pending_role_requested_by": u.pending_role_requested_by,
            "pending_role_requested_at": _iso(u.pending_role_requested_at), "created_at": _iso(u.created_at)}


def _operator(ctx: Ctx, user_id: str) -> User:
    user = ctx.db.get(User, user_id)
    if user is None or user.platform_role is None:
        raise DomainError(404, "operator_not_found", "Nie znaleziono operatora.")
    return user


def _valid_role(role: str) -> PlatformRole | None:
    try:
        return PlatformRole(role)
    except ValueError:
        return None


def _active_admins(ctx: Ctx) -> int:
    return ctx.db.scalar(select(func.count()).select_from(User).where(
        User.platform_role == PlatformRole.PLATFORM_ADMIN, User.is_active.is_(True))) or 0


@router.get("/operators")
def list_operators(op: OperatorPrincipal = Depends(require_platform_permission(PP.USERS_READ)),
                   ctx: Ctx = Depends(get_ctx)):
    if not ({PP.OPERATORS_MANAGE, PP.OPERATORS_APPROVE} & op.permissions):
        raise DomainError(403, "operator_not_permitted", "Brak uprawnień operatora.")
    keys = set(ctx.db.scalars(select(WebAuthnCredential.user_id)))
    rows = ctx.db.scalars(select(User).where(User.platform_role.is_not(None)).order_by(User.email))
    return {"operators": [_operator_out(u, keys) for u in rows], "roles": {k: tr(v) for k, v in ROLE_LABELS.items()},
            "privileged_roles": sorted(PRIVILEGED_ROLES)}


@router.post("/operators")
def create_operator(body: OperatorCreateIn, op: OperatorPrincipal = Depends(require_platform_permission(PP.OPERATORS_MANAGE)),
                    ctx: Ctx = Depends(get_ctx)):
    """Nowy operator z rola nieuprzywilejowana; role uprzywilejowane - zmiana roli z zatwierdzeniem."""
    action = "platform.operator.create"
    email = _check_email(ctx, op, action, body.email)
    role = _valid_role(body.role)
    if role is None:
        raise _deny(ctx, op, action, 422, "role_invalid", "Nieznana rola operatora.")
    if role in PRIVILEGED_ROLES:
        raise _deny(ctx, op, action, 422, "privileged_role_needs_approval",
                    "Rolę uprzywilejowaną nadaje się istniejącemu operatorowi i wymaga ona zatwierdzenia "
                    "przez oficera bezpieczeństwa.")
    if ctx.db.scalar(select(User.id).where(User.email == email)):
        raise _deny(ctx, op, action, 409, "email_taken", "Konto z tym adresem już istnieje.")
    _step_up(ctx, op, body, action)
    user = User(email=email, display_name=body.display_name.strip(), password_hash=activation.unusable_password_hash(),
                is_active=False, platform_role=role, created_at=clock.now())
    ctx.db.add(user)
    ctx.db.flush()
    activation.issue(ctx, user, kind="operator", created_by=op.user.id)
    _log(ctx, op, "platform.operator.created", user_id=user.id, role=role)
    return {"operator": _operator_out(user, set())}


@router.put("/operators/{user_id}/role")
def change_operator_role(user_id: str, body: RoleIn,
                         op: OperatorPrincipal = Depends(require_platform_permission(PP.OPERATORS_MANAGE)),
                         ctx: Ctx = Depends(get_ctx)):
    action = "platform.operator.role_change"
    target = _operator(ctx, user_id)
    role = _valid_role(body.role)
    if role is None:
        raise _deny(ctx, op, action, 422, "role_invalid", "Nieznana rola operatora.")
    if target.id == op.user.id:
        raise _deny(ctx, op, action, 403, "self_change_forbidden", "Nie możesz zmienić własnej roli.")
    if role == target.platform_role:
        raise _deny(ctx, op, action, 409, "role_unchanged", "Operator ma już tę rolę.")
    if (target.platform_role == PlatformRole.PLATFORM_ADMIN and target.is_active and _active_admins(ctx) <= 1):
        raise _deny(ctx, op, action, 409, "last_platform_admin", "To ostatni aktywny administrator platformy.")
    _step_up(ctx, op, body, action)
    officers = _operators_with(ctx, PP.OPERATORS_APPROVE, exclude={op.user.id, target.id})
    if role in PRIVILEGED_ROLES:
        target.pending_platform_role = role
        target.pending_role_requested_by = op.user.id
        target.pending_role_requested_at = clock.now()
        _log(ctx, op, "platform.operator.role_change_requested", user_id=target.id, role_from=target.platform_role,
             role_to=role)
        ctx.notifications.notify(ctx.db, officers, event="platform.operator.role_approval_required",
                                 title=L("Do zatwierdzenia: rola {role} dla {email}", role=ROLE_LABELS[role],
                                         email=target.email),
                                 body=L("Zlecił: {who}. Zatwierdź albo odrzuć w panelu: Operatorzy.", who=op.user.email))
        return {"status": "pending_approval", "operator": _operator_out(target, set())}
    previous = target.platform_role
    target.platform_role = role
    target.pending_platform_role = target.pending_role_requested_by = target.pending_role_requested_at = None
    _log(ctx, op, "platform.operator.role_changed", user_id=target.id, role_from=previous, role_to=role)
    ctx.notifications.notify(ctx.db, [target, *officers], event="platform.operator.role_changed",
                             title=L("Zmieniono rolę operatora {email}", email=target.email),
                             body=L("{old} -> {new} (zmienił: {who}).", old=ROLE_LABELS.get(previous, previous),
                                    new=ROLE_LABELS[role], who=op.user.email))
    return {"status": "changed", "operator": _operator_out(target, set())}


def _pending(ctx: Ctx, op: OperatorPrincipal, action: str, user_id: str) -> User:
    target = _operator(ctx, user_id)
    if not target.pending_platform_role:
        raise _deny(ctx, op, action, 409, "nothing_pending", "Brak zmiany roli do zatwierdzenia.")
    if op.user.id in (target.pending_role_requested_by, target.id):
        raise _deny(ctx, op, action, 403, "independent_approver_required",
                    "Zmianę musi zatwierdzić inna osoba niż zlecający i niż operator, którego dotyczy.")
    return target


@router.post("/operators/{user_id}/role/approve")
def approve_role(user_id: str, body: StepUp,
                 op: OperatorPrincipal = Depends(require_platform_permission(PP.OPERATORS_APPROVE)),
                 ctx: Ctx = Depends(get_ctx)):
    action = "platform.operator.role_approve"
    target = _pending(ctx, op, action, user_id)
    _step_up(ctx, op, body, action)
    previous, role, requester = target.platform_role, target.pending_platform_role, target.pending_role_requested_by
    target.platform_role = role
    target.pending_platform_role = target.pending_role_requested_by = target.pending_role_requested_at = None
    _log(ctx, op, "platform.operator.role_changed", user_id=target.id, role_from=previous, role_to=role,
         requested_by=requester, approved_by=op.user.id)
    recipients = [u for u in (target, ctx.db.get(User, requester)) if u is not None]
    recipients += _operators_with(ctx, PP.OPERATORS_APPROVE, exclude={op.user.id, *(u.id for u in recipients)})
    ctx.notifications.notify(ctx.db, recipients, event="platform.operator.role_changed",
                             title=L("Zatwierdzono rolę {role} dla {email}", role=ROLE_LABELS[role], email=target.email),
                             body=L("Zlecił: {requester}, zatwierdził: {who}.", requester=requester, who=op.user.email))
    return {"status": "changed", "operator": _operator_out(target, set())}


@router.post("/operators/{user_id}/role/reject")
def reject_role(user_id: str, body: RejectIn,
                op: OperatorPrincipal = Depends(require_platform_permission(PP.OPERATORS_APPROVE)),
                ctx: Ctx = Depends(get_ctx)):
    action = "platform.operator.role_reject"
    target = _pending(ctx, op, action, user_id)
    _step_up(ctx, op, body, action)
    role, requester = target.pending_platform_role, target.pending_role_requested_by
    target.pending_platform_role = target.pending_role_requested_by = target.pending_role_requested_at = None
    _log(ctx, op, "platform.operator.role_rejected", user_id=target.id, role=role, requested_by=requester,
         reason=body.reason)
    requester_user = ctx.db.get(User, requester) if requester else None
    if requester_user:
        ctx.notifications.notify(ctx.db, [requester_user], event="platform.operator.role_rejected",
                                 title=L("Odrzucono rolę {role} dla {email}", role=ROLE_LABELS.get(role, role),
                                         email=target.email),
                                 body=join(" ", [L("Odrzucił: {who}.", who=op.user.email),
                                                 *([body.reason.strip()] if (body.reason or "").strip() else [])]))
    return {"status": "rejected", "operator": _operator_out(target, set())}


@router.post("/operators/{user_id}/block")
def block_operator(user_id: str, body: BlockIn,
                   op: OperatorPrincipal = Depends(require_platform_permission(PP.OPERATORS_MANAGE)),
                   ctx: Ctx = Depends(get_ctx)):
    action = "platform.operator.block"
    target = _operator(ctx, user_id)
    if target.id == op.user.id:
        raise _deny(ctx, op, action, 403, "self_change_forbidden", "Nie możesz zablokować własnego konta.")
    if target.blocked_at is not None:
        raise _deny(ctx, op, action, 409, "already_blocked", "Konto jest już zablokowane.")
    if target.platform_role == PlatformRole.PLATFORM_ADMIN and target.is_active and _active_admins(ctx) <= 1:
        raise _deny(ctx, op, action, 409, "last_platform_admin", "To ostatni aktywny administrator platformy.")
    _step_up(ctx, op, body, action)
    target.blocked_at, target.blocked_reason, target.is_active = clock.now(), body.reason.strip(), False
    _revoke_user_sessions(ctx, target)
    ended = _end_support_sessions(ctx, op, "operator_blocked", SupportSession.operator_user_id == target.id)
    _log(ctx, op, "platform.operator.blocked", user_id=target.id, reason=target.blocked_reason,
         support_sessions_ended=ended)
    ctx.notifications.notify(ctx.db, _operators_with(ctx, PP.OPERATORS_APPROVE, exclude={op.user.id}),
                             event="platform.operator.blocked", title=L("Zablokowano operatora {email}", email=target.email),
                             body=L("Zablokował: {who}. Powód: {reason}. Zakończone sesje wsparcia: {ended}.",
                                    who=op.user.email, reason=target.blocked_reason, ended=ended))
    return {"operator": _operator_out(target, set())}


@router.post("/operators/{user_id}/unblock")
def unblock_operator(user_id: str, body: StepUp,
                     op: OperatorPrincipal = Depends(require_platform_permission(PP.OPERATORS_MANAGE)),
                     ctx: Ctx = Depends(get_ctx)):
    action = "platform.operator.unblock"
    target = _operator(ctx, user_id)
    if target.id == op.user.id:
        raise _deny(ctx, op, action, 403, "self_change_forbidden", "Nie możesz odblokować własnego konta.")
    if target.blocked_at is None:
        raise _deny(ctx, op, action, 409, "not_blocked", "Konto nie jest zablokowane.")
    _step_up(ctx, op, body, action)
    target.blocked_at, target.blocked_reason = None, None
    target.is_active = target.activated_at is not None
    _log(ctx, op, "platform.operator.unblocked", user_id=target.id)
    ctx.notifications.notify(ctx.db, _operators_with(ctx, PP.OPERATORS_APPROVE, exclude={op.user.id}),
                             event="platform.operator.unblocked", title=L("Odblokowano operatora {email}", email=target.email),
                             body=L("Odblokował: {who}.", who=op.user.email))
    return {"operator": _operator_out(target, set())}


# ============================================================================= zgloszenia


class TicketCreateIn(StepUp):
    organization_id: str
    subject: str = Field(min_length=3, max_length=300)
    description: str | None = Field(default=None, max_length=10_000)
    priority: TicketPriority = TicketPriority.NORMAL
    reporter_user_id: str | None = None


class TicketStatusIn(BaseModel):
    status: str


def _ticket_out(t: SupportTicket) -> dict:
    return tickets.ticket_out(t)


@router.get("/tickets/all")
def list_all_tickets(status: str | None = None, q: str = "",
                     op: OperatorPrincipal = Depends(require_platform_permission(PP.TICKETS_READ)),
                     ctx: Ctx = Depends(get_ctx)):
    names = dict(ctx.db.execute(select(Organization.id, Organization.name)).all())
    stmt = select(SupportTicket).order_by(SupportTicket.created_at.desc()).limit(300)
    if status:
        stmt = stmt.where(SupportTicket.status == status)
    if q:
        stmt = stmt.where(or_(SupportTicket.number.ilike(f"%{q}%"), SupportTicket.subject.ilike(f"%{q}%")))
    rows = list(ctx.db.scalars(stmt))
    emails = dict(ctx.db.execute(select(User.id, User.email).where(
        User.id.in_({t.reporter_user_id for t in rows if t.reporter_user_id}))).all())
    return {"tickets": [tickets.ticket_out(t, organization_name=names.get(t.organization_id), emails=emails)
                        for t in rows]}


@router.post("/tickets")
def create_ticket(body: TicketCreateIn, op: OperatorPrincipal = Depends(require_platform_permission(PP.TICKETS_MANAGE)),
                  ctx: Ctx = Depends(get_ctx)):
    action = "platform.ticket.create"
    org = ctx.db.get(Organization, body.organization_id)
    if org is None or org.deleted_at is not None:
        raise DomainError(404, "organization_not_found", "Nie znaleziono organizacji.")
    if body.reporter_user_id and not ctx.db.scalar(select(Membership.id).where(
            Membership.organization_id == org.id, Membership.user_id == body.reporter_user_id)):
        raise _deny(ctx, op, action, 422, "reporter_not_member", "Zgłaszający nie należy do tej organizacji.")
    _step_up(ctx, op, body, action)
    ticket = tickets.create(ctx, organization_id=org.id, subject=body.subject, description=body.description,
                            priority=body.priority, reporter_user_id=body.reporter_user_id, by_customer=False)
    _log(ctx, op, "platform.ticket.created", organization_id=org.id, ticket=ticket.number, subject=ticket.subject)
    ctx.notifications.notify(ctx.db, _org_admins(ctx, org.id), event="platform.ticket.created",
                             title=L("Forvium otworzyło zgłoszenie {ticket}", ticket=ticket.number), body=ticket.subject,
                             organization_id=org.id, data={"ticket_id": ticket.id})
    return {"ticket": _ticket_out(ticket)}


@router.put("/tickets/{ticket_id}/status")
def set_ticket_status(ticket_id: str, body: TicketStatusIn,
                      op: OperatorPrincipal = Depends(require_platform_permission(PP.TICKETS_MANAGE)),
                      ctx: Ctx = Depends(get_ctx)):
    """Zmiana statusu (bez MFA - nie rozszerza dostepu). Zamkniecie konczy sesje wsparcia na tym zgloszeniu."""
    ticket = ctx.db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise DomainError(404, "ticket_not_found", "Nie znaleziono zgłoszenia.")
    try:
        status = TicketStatus(body.status)
    except ValueError:
        raise DomainError(422, "status_invalid", "Nieznany status zgłoszenia.") from None
    if status == ticket.status:
        return {"ticket": _ticket_out(ticket)}
    previous = ticket.status
    ended = tickets.set_status(ctx, ticket, status, by_user_id=op.user.id, actor_type="operator")
    _log(ctx, op, "platform.ticket.status_changed", organization_id=ticket.organization_id, ticket=ticket.number,
         status_from=previous, status_to=status, support_sessions_ended=ended)
    reporter = ctx.db.get(User, ticket.reporter_user_id) if ticket.reporter_user_id else None
    if reporter is not None and reporter.is_active:
        ctx.notifications.notify(ctx.db, [reporter], event="support_tickets.status_changed",
                                 title=L("Zgłoszenie {ticket}: {status}", ticket=ticket.number, status=tickets.STATUS_LABELS[status]),
                                 body=ticket.subject, organization_id=ticket.organization_id,
                                 data={"ticket_id": ticket.id})
    return {"ticket": _ticket_out(ticket), "support_sessions_ended": ended}
