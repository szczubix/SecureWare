"""Zgody stale (pre-approval) - zarzadzane przez uprawnionego przedstawiciela klienta."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError
from forvium.identity.models import User
from forvium.identity.service import consume_totp
from forvium.organizations.models import Organization, OrgUnit
from forvium.platform_admin.rbac import PlatformRole
from forvium.support_access.models import SupportConsent, SupportStandingConsent
from forvium.support_access.scopes import parse_scopes
from forvium.support_access.service import _deny, _org_approvers, revoke_consent


def create_standing_consent(
    ctx: Ctx,
    user: User,
    *,
    organization_id: str,
    scopes: list[str],
    unit_ids: list[str] | None,
    max_session_minutes: int,
    valid_days: int,
    allowed_platform_roles: list[str] | None,
    note: str | None,
    mfa_code: str | None,
) -> SupportStandingConsent:
    action = "support.standing_consent.create"
    base = {"actor_user_id": user.id, "actor_type": "user", "organization_id": organization_id}
    if user.platform_role is not None:
        raise _deny(ctx, action, "operator_cannot_approve",
                    "Konto operatora Forvium nie może udzielać zgód.", **base)
    try:
        parsed = parse_scopes(scopes)
    except ValueError:
        raise _deny(ctx, action, "scope_invalid", "Nieznany zakres dostępu.", status=422, **base)
    if not parsed:
        raise _deny(ctx, action, "scope_empty", "Wybierz co najmniej jeden zakres.", status=422, **base)
    if not 1 <= max_session_minutes <= ctx.policy.max_session_minutes:
        raise _deny(ctx, action, "duration_invalid",
                    f"Czas sesji: 1-{ctx.policy.max_session_minutes} min.", status=422, **base)
    if not 1 <= valid_days <= ctx.policy.max_standing_consent_days:
        raise _deny(ctx, action, "validity_invalid",
                    f"Ważność zgody stałej: 1-{ctx.policy.max_standing_consent_days} dni.", status=422, **base)
    if allowed_platform_roles:
        try:
            allowed_platform_roles = sorted({PlatformRole(r).value for r in allowed_platform_roles})
        except ValueError:
            raise _deny(ctx, action, "role_invalid", "Nieznana rola supportu.", status=422, **base)
    if unit_ids:
        found = set(ctx.db.scalars(select(OrgUnit.id).where(OrgUnit.organization_id == organization_id,
                                                            OrgUnit.id.in_(unit_ids))))
        if found != set(unit_ids):
            raise _deny(ctx, action, "unit_invalid", "Nieprawidłowe jednostki.", status=422, **base)
    # Zgoda stala jest silniejsza niz pojedyncza decyzja - wymaga MFA przedstawiciela klienta.
    if user.mfa_secret and not consume_totp(user, mfa_code):
        raise _deny(ctx, action, "mfa_required", "Potwierdź zgodę stała kodem MFA.", status=401, **base)

    now = clock.now()
    org = ctx.db.get(Organization, organization_id)
    dual = bool(org and org.support_dual_approval)
    standing = SupportStandingConsent(
        organization_id=organization_id,
        granted_by_user_id=user.id,
        scopes=sorted(s.value for s in parsed),
        unit_ids=sorted(unit_ids) if unit_ids else None,
        max_session_minutes=max_session_minutes,
        allowed_platform_roles=allowed_platform_roles or None,
        note=(note or "").strip() or None,
        created_at=now,
        valid_until=now + timedelta(days=valid_days),
        # Przy zatwierdzaniu przez dwie osoby zgoda stala czeka na potwierdzenie.
        confirmed_by_user_id=None if dual else user.id,
        confirmed_at=None if dual else now,
    )
    ctx.db.add(standing)
    ctx.db.flush()
    ctx.audit.log(ctx.db, "support.standing_consent.created", ip_address=ctx.ip,
                  details={"standing_consent_id": standing.id, "scopes": standing.scopes,
                           "unit_ids": standing.unit_ids, "max_session_minutes": max_session_minutes,
                           "allowed_platform_roles": standing.allowed_platform_roles,
                           "valid_until": standing.valid_until.isoformat()}, **base)
    ctx.notifications.notify(
        ctx.db, _org_approvers(ctx, organization_id, exclude_user_id=user.id),
        event="support_access.standing_consent_created",
        title=("Potwierdź zgodę stała na dostęp serwisowy Forvium" if dual
               else "Utworzono zgodę stała na dostęp serwisowy Forvium"),
        body=(f"{user.display_name} udzielił(a) zgody stałej (zakres: {', '.join(standing.scopes)}, "
              f"do {max_session_minutes} min na sesje, ważna do {standing.valid_until.date()}). "
              + ("Zgoda zacznie obowiązywać po potwierdzeniu przez druga osobę. " if dual else "")
              + "Można ja cofnąć w Ustawienia -> Dostęp serwisowy."),
        organization_id=organization_id, data={"standing_consent_id": standing.id},
    )
    return standing


def confirm_standing_consent(ctx: Ctx, user: User, *, organization_id: str, standing_id: str,
                             mfa_code: str | None) -> SupportStandingConsent:
    """Druga osoba potwierdza zgode stala (zatwierdzanie przez dwie osoby)."""
    action = "support.standing_consent.confirm"
    base = {"actor_user_id": user.id, "actor_type": "user", "organization_id": organization_id}
    standing = ctx.db.get(SupportStandingConsent, standing_id)
    if standing is None or standing.organization_id != organization_id:
        raise DomainError(404, "standing_consent_not_found", "Nie znaleziono zgody stałej.")
    if standing.confirmed_at is not None or standing.revoked_at is not None:
        raise _deny(ctx, action, "not_pending", "Zgoda stała nie czeka na potwierdzenie.", status=409, **base)
    if user.id == standing.granted_by_user_id:
        raise _deny(ctx, action, "second_approver_required",
                    "Zgodę stała musi potwierdzić inna osoba niż tworząca.", **base)
    if user.platform_role is not None:
        raise _deny(ctx, action, "operator_cannot_approve", "Konto operatora Forvium nie może udzielać zgód.", **base)
    if user.mfa_secret and not consume_totp(user, mfa_code):
        raise _deny(ctx, action, "mfa_required", "Potwierdź zgodę stała kodem MFA.", status=401, **base)
    standing.confirmed_by_user_id = user.id
    standing.confirmed_at = clock.now()
    ctx.audit.log(ctx.db, "support.standing_consent.confirmed", ip_address=ctx.ip,
                  details={"standing_consent_id": standing.id, "created_by": standing.granted_by_user_id}, **base)
    return standing


def revoke_standing_consent(ctx: Ctx, user: User, *, organization_id: str, standing_id: str) -> SupportStandingConsent:
    standing = ctx.db.get(SupportStandingConsent, standing_id)
    if standing is None or standing.organization_id != organization_id:
        raise DomainError(404, "standing_consent_not_found", "Nie znaleziono zgody stałej.")
    if standing.revoked_at is not None:
        return standing
    standing.revoked_at = clock.now()
    standing.revoked_by_user_id = user.id
    ctx.audit.log(ctx.db, "support.standing_consent.revoked", actor_user_id=user.id, actor_type="user",
                  organization_id=organization_id, ip_address=ctx.ip, details={"standing_consent_id": standing.id})
    # Kaskada: wszystkie zgody wynikajace ze zgody stalej i ich aktywne sesje.
    for consent in list(ctx.db.scalars(select(SupportConsent).where(
            SupportConsent.standing_consent_id == standing.id, SupportConsent.revoked_at.is_(None)))):
        revoke_consent(ctx, user, organization_id=organization_id, consent_id=consent.id)
    return standing


def standing_out(s: SupportStandingConsent) -> dict:
    iso = lambda d: d.isoformat() + "Z" if d else None  # noqa: E731
    return {
        "id": s.id,
        "organization_id": s.organization_id,
        "granted_by_user_id": s.granted_by_user_id,
        "scopes": s.scopes,
        "unit_ids": s.unit_ids,
        "max_session_minutes": s.max_session_minutes,
        "allowed_platform_roles": s.allowed_platform_roles,
        "note": s.note,
        "created_at": iso(s.created_at),
        "valid_until": iso(s.valid_until),
        "revoked_at": iso(s.revoked_at),
        "confirmed_by_user_id": s.confirmed_by_user_id,
        "pending_confirmation": s.confirmed_at is None and s.revoked_at is None,
        "active": s.revoked_at is None and s.confirmed_at is not None and clock.now() < s.valid_until,
    }
