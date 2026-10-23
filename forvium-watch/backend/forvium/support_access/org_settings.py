"""Ustawienia dostepu serwisowego organizacji (zatwierdzanie przez dwie osoby)."""

from __future__ import annotations

from forvium.core.context import Ctx
from forvium.identity.models import User
from forvium.identity.service import consume_totp
from forvium.organizations.models import Organization
from forvium.support_access.service import _deny, _org_approvers


def settings_out(org: Organization) -> dict:
    return {"dual_approval": org.support_dual_approval,
            "dual_approval_disable_requested_by": org.support_dual_approval_disable_requested_by}


def set_dual_approval(ctx: Ctx, user: User, org: Organization, *, enabled: bool, mfa_code: str | None) -> dict:
    """Wlaczenie dziala od razu. Wylaczenie (oslabienie ochrony) wymaga drugiej osoby:
    pierwsza zglasza wylaczenie, druga je potwierdza."""
    action = "support.settings.dual_approval"
    base = {"actor_user_id": user.id, "actor_type": "user", "organization_id": org.id}
    if user.platform_role is not None:
        raise _deny(ctx, action, "operator_cannot_change", "Konto operatora Forvium nie może zmieniać ustawień.", **base)
    # Wszystkie odmowy przed zuzyciem kodu MFA i przed zapisami.
    if not enabled and org.support_dual_approval and org.support_dual_approval_disable_requested_by == user.id:
        raise _deny(ctx, action, "second_approver_required",
                    "Wyłączenie musi potwierdzić inna osoba niż zgłaszająca.", status=409, **base)
    if user.mfa_secret and not consume_totp(user, mfa_code):
        raise _deny(ctx, action, "mfa_required", "Potwierdź zmianę kodem MFA.", status=401, **base)

    others = _org_approvers(ctx, org.id, exclude_user_id=user.id)
    if enabled:
        changed = not org.support_dual_approval or org.support_dual_approval_disable_requested_by is not None
        org.support_dual_approval = True
        org.support_dual_approval_disable_requested_by = None
        if changed:
            ctx.audit.log(ctx.db, "support.settings.dual_approval_enabled", ip_address=ctx.ip, **base)
            ctx.notifications.notify(ctx.db, others, event="support_access.settings_changed",
                                     title="Włączono zatwierdzanie dostępu serwisowego przez dwie osoby",
                                     body=f"{user.display_name} włączył(a) wymóg dwóch zatwierdzeń.",
                                     organization_id=org.id)
        return settings_out(org)

    if not org.support_dual_approval:
        return settings_out(org)
    requested_by = org.support_dual_approval_disable_requested_by
    if requested_by is None:
        org.support_dual_approval_disable_requested_by = user.id
        ctx.audit.log(ctx.db, "support.settings.dual_approval_disable_requested", ip_address=ctx.ip, **base)
        ctx.notifications.notify(ctx.db, others, event="support_access.settings_change_requested",
                                 title="Prośba o wyłączenie zatwierdzania przez dwie osoby",
                                 body=(f"{user.display_name} chce wyłączyć wymóg dwóch zatwierdzeń dostępu "
                                       "serwisowego Forvium. Zmiana wymaga potwierdzenia przez inna osobę: "
                                       "Ustawienia -> Dostęp serwisowy."),
                                 organization_id=org.id)
        return settings_out(org)
    org.support_dual_approval = False
    org.support_dual_approval_disable_requested_by = None
    ctx.audit.log(ctx.db, "support.settings.dual_approval_disabled", ip_address=ctx.ip,
                  details={"requested_by": requested_by}, **base)
    ctx.notifications.notify(ctx.db, others, event="support_access.settings_changed",
                             title="Wyłączono zatwierdzanie dostępu serwisowego przez dwie osoby",
                             body=f"{user.display_name} potwierdził(a) wyłączenie wymogu dwóch zatwierdzeń.",
                             organization_id=org.id)
    return settings_out(org)
