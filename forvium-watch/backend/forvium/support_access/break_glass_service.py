"""Break Glass - zatwierdzanie (4 oczy), odrzucanie, przeglad po incydencie."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError
from forvium.identity.models import User
from forvium.notifications.models import EmailOutbox
from forvium.organizations.models import Organization
from forvium.platform_admin.rbac import PlatformPermission, platform_permissions
from forvium.support_access.models import (
    AccessLevel,
    AccessMode,
    ConsentBasis,
    RequestStatus,
    SessionStatus,
    SupportAccessRequest,
    SupportConsent,
    SupportSession,
)
from forvium.support_access.service import (
    _deny,
    _expire_stale_request,
    _org_approvers,
    _require_platform,
    _verify_operator_mfa,
)
from forvium.support_access.summary import session_summary, summary_text


def _platform_users_with(ctx: Ctx, permission: PlatformPermission, exclude: set[str] = frozenset()) -> list[User]:
    users = ctx.db.scalars(select(User).where(User.platform_role.is_not(None), User.is_active.is_(True)))
    return [u for u in users if permission in platform_permissions(u.platform_role) and u.id not in exclude]


def notify_security_team(ctx: Ctx, subject: str, body: str) -> None:
    """E-mail na adresy zespolu bezpieczenstwa (FORVIUM_SECURITY_TEAM_EMAILS)."""
    now = clock.now()
    for address in ctx.break_glass.security_team_emails:
        ctx.db.add(EmailOutbox(to_address=address, subject=f"[Forvium SECURITY] {subject}", body=body,
                               created_at=now))


def on_break_glass_requested(ctx: Ctx, req: SupportAccessRequest, operator: User, org: Organization) -> None:
    ctx.audit.log(
        ctx.db, "break_glass.requested", actor_user_id=operator.id, actor_type="operator",
        organization_id=req.organization_id, on_behalf_of_user_id=req.reference_user_id,
        support_request_id=req.id, ip_address=ctx.ip,
        details={"ticket": req.ticket_number, "incident_category": req.incident_category,
                 "scopes": req.requested_scopes, "duration_minutes": req.requested_duration_minutes,
                 "justification": req.reason},
    )
    body = (f"Operator {operator.id} wnioskuje o dostęp awaryjny (Break Glass) do organizacji {org.name} "
            f"({req.organization_id}), zgłoszenie {req.ticket_number}, kategoria {req.incident_category}, "
            f"{req.requested_duration_minutes} min.\nUzasadnienie: {req.reason}\n"
            f"Wniosek wygasa {req.decision_deadline.isoformat()} UTC. Decyzja: admin.forvium.com -> Break Glass.")
    ctx.notifications.notify(
        ctx.db, _platform_users_with(ctx, PlatformPermission.BREAK_GLASS_APPROVE, {operator.id}),
        event="break_glass.requested", title=f"Wniosek Break Glass ({req.ticket_number})", body=body,
        organization_id=req.organization_id, data={"request_id": req.id},
    )
    notify_security_team(ctx, f"Wniosek Break Glass ({req.ticket_number})", body)


def _load(ctx: Ctx, request_id: str) -> SupportAccessRequest:
    req = ctx.db.get(SupportAccessRequest, request_id)
    if req is None or req.mode != AccessMode.BREAK_GLASS:
        raise DomainError(404, "request_not_found", "Nie znaleziono wniosku Break Glass.")
    _expire_stale_request(ctx, req)
    return req


def approve_break_glass(ctx: Ctx, officer: User, *, request_id: str, mfa_code: str | None,
                        note: str | None, webauthn: dict | None = None) -> SupportConsent:
    action = "break_glass.approve"
    req = _load(ctx, request_id)
    base = {"actor_user_id": officer.id, "actor_type": "operator", "organization_id": req.organization_id,
            "support_request_id": req.id}
    _require_platform(ctx, officer, PlatformPermission.BREAK_GLASS_APPROVE, action)
    if officer.id == req.operator_user_id:
        raise _deny(ctx, action, "self_approval", "Wniosek musi zatwierdzić inna osoba (zasada 4 oczu).", **base)
    if req.status != RequestStatus.PENDING_SECOND_APPROVAL:
        raise _deny(ctx, action, "request_not_pending", "Wniosek nie oczekuje na zatwierdzenie.", status=409, **base)
    _verify_operator_mfa(ctx, officer, mfa_code, action, webauthn=webauthn,
                         require_hardware=ctx.break_glass.requires_hardware_mfa,
                         organization_id=req.organization_id, support_request_id=req.id)

    now = clock.now()
    req.status = RequestStatus.APPROVED
    req.decided_by_user_id = officer.id
    req.decided_at = now
    req.decision_note = (note or "").strip() or None
    consent = SupportConsent(
        request_id=req.id,
        organization_id=req.organization_id,
        operator_user_id=req.operator_user_id,
        reference_user_id=req.reference_user_id,
        granted_by_user_id=officer.id,
        scopes=list(req.requested_scopes),
        unit_ids=None,
        access_level=AccessLevel.READ_ONLY,
        max_session_minutes=req.requested_duration_minutes,
        granted_at=now,
        valid_until=now + timedelta(hours=ctx.break_glass.consent_hours),
        basis=ConsentBasis.BREAK_GLASS,
    )
    ctx.db.add(consent)
    ctx.db.flush()
    ctx.audit.log(ctx.db, "break_glass.approved", ip_address=ctx.ip,
                  details={"consent_id": consent.id, "valid_until": consent.valid_until.isoformat()}, **base)

    org = ctx.db.get(Organization, req.organization_id)
    body = (f"Forvium uruchomiło procedure awaryjna (Break Glass) dla organizacji {org.name}: "
            f"operator {req.operator_user_id} może otworzyć sesję TYLKO DO ODCZYTU do "
            f"{req.requested_duration_minutes} min, zgłoszenie {req.ticket_number}.\n"
            f"Kategoria incydentu: {req.incident_category}\nUzasadnienie: {req.reason}\n"
            f"Wniosek zatwierdził oficer bezpieczeństwa Forvium ({officer.id}). Możecie natychmiast cofnąć te "
            "zgodę: Ustawienia -> Dostęp serwisowy. Po incydencie otrzymacie raport z przeglądu.")
    ctx.notifications.notify(ctx.db, _org_approvers(ctx, req.organization_id),
                             event="break_glass.approved",
                             title=f"PROCEDURA AWARYJNA Forvium ({req.ticket_number})", body=body,
                             organization_id=req.organization_id,
                             data={"request_id": req.id, "consent_id": consent.id})
    operator = ctx.db.get(User, req.operator_user_id)
    if operator:
        ctx.notifications.notify(ctx.db, [operator], event="break_glass.approved",
                                 title=f"Break Glass zatwierdzony ({req.ticket_number})",
                                 body=f"Zgoda awaryjna ważna do {consent.valid_until.isoformat()} UTC.",
                                 organization_id=req.organization_id, data={"request_id": req.id})
    notify_security_team(ctx, f"Break Glass zatwierdzony ({req.ticket_number})", body)
    return consent


def reject_break_glass(ctx: Ctx, officer: User, *, request_id: str, note: str | None) -> None:
    action = "break_glass.reject"
    req = _load(ctx, request_id)
    base = {"actor_user_id": officer.id, "actor_type": "operator", "organization_id": req.organization_id,
            "support_request_id": req.id}
    _require_platform(ctx, officer, PlatformPermission.BREAK_GLASS_APPROVE, action)
    if officer.id == req.operator_user_id:
        raise _deny(ctx, action, "self_decision", "Nie można decydować o własnym wniosku.", **base)
    if req.status != RequestStatus.PENDING_SECOND_APPROVAL:
        raise _deny(ctx, action, "request_not_pending", "Wniosek nie oczekuje na zatwierdzenie.", status=409, **base)
    req.status = RequestStatus.REJECTED
    req.decided_by_user_id = officer.id
    req.decided_at = clock.now()
    req.decision_note = (note or "").strip() or None
    ctx.audit.log(ctx.db, "break_glass.rejected", ip_address=ctx.ip, details={"note": req.decision_note}, **base)
    operator = ctx.db.get(User, req.operator_user_id)
    if operator:
        ctx.notifications.notify(ctx.db, [operator], event="break_glass.rejected",
                                 title=f"Break Glass odrzucony ({req.ticket_number})",
                                 body=req.decision_note or "Wniosek odrzucony.",
                                 organization_id=req.organization_id, data={"request_id": req.id})


def review_break_glass(ctx: Ctx, reviewer: User, *, request_id: str, notes: str) -> SupportAccessRequest:
    """Przeglad po incydencie - niezalezny od wnioskujacego i zatwierdzajacego."""
    action = "break_glass.review"
    req = _load(ctx, request_id)
    base = {"actor_user_id": reviewer.id, "actor_type": "operator", "organization_id": req.organization_id,
            "support_request_id": req.id}
    _require_platform(ctx, reviewer, PlatformPermission.BREAK_GLASS_REVIEW, action)
    if reviewer.id in (req.operator_user_id, req.decided_by_user_id):
        raise _deny(ctx, action, "reviewer_not_independent",
                    "Przegląd musi wykonać osoba niezależna od wnioskującego i zatwierdzającego.", **base)
    if req.status != RequestStatus.APPROVED or req.review_completed_at is not None:
        raise _deny(ctx, action, "review_not_applicable", "Wniosek nie wymaga przeglądu.", status=409, **base)
    sessions = list(ctx.db.scalars(select(SupportSession).where(SupportSession.request_id == req.id)))
    if any(s.status == SessionStatus.ACTIVE and clock.now() < s.expires_at for s in sessions):
        raise _deny(ctx, action, "session_active", "Sesja awaryjna wciąż trwa.", status=409, **base)
    if len((notes or "").strip()) < 50:
        raise _deny(ctx, action, "notes_too_short", "Opisz ustalenia przeglądu (min. 50 znaków).", status=422,
                    **base)

    req.review_completed_at = clock.now()
    req.reviewed_by_user_id = reviewer.id
    req.review_notes = notes.strip()
    summaries = [session_summary(ctx.db, s) for s in sessions]
    ctx.audit.log(ctx.db, "break_glass.reviewed", ip_address=ctx.ip,
                  details={"sessions": len(sessions), "notes": req.review_notes}, **base)
    body = "\n\n".join(
        [f"Przegląd procedury awaryjnej Forvium ({req.ticket_number}) został zakończony.",
         f"Ustalenia: {req.review_notes}"]
        + [f"Sesja {i + 1}:\n{summary_text(sm)}" for i, sm in enumerate(summaries)]
        + ["Szczegółowa lista operacji: Ustawienia -> Dostęp serwisowy -> Historia sesji."]
    )
    ctx.notifications.notify(ctx.db, _org_approvers(ctx, req.organization_id), event="break_glass.reviewed",
                             title=f"Raport z procedury awaryjnej Forvium ({req.ticket_number})", body=body,
                             organization_id=req.organization_id, data={"request_id": req.id})
    notify_security_team(ctx, f"Break Glass - przegląd zakończony ({req.ticket_number})", body)
    return req


def list_break_glass(ctx: Ctx, *, status: str | None = None, review_pending: bool = False) -> list[SupportAccessRequest]:
    for req in ctx.db.scalars(select(SupportAccessRequest).where(
            SupportAccessRequest.mode == AccessMode.BREAK_GLASS,
            SupportAccessRequest.status == RequestStatus.PENDING_SECOND_APPROVAL)):
        _expire_stale_request(ctx, req)
    stmt = select(SupportAccessRequest).where(SupportAccessRequest.mode == AccessMode.BREAK_GLASS)
    if status:
        stmt = stmt.where(SupportAccessRequest.status == status)
    if review_pending:
        stmt = stmt.where(SupportAccessRequest.status == RequestStatus.APPROVED,
                          SupportAccessRequest.review_completed_at.is_(None))
    return list(ctx.db.scalars(stmt.order_by(SupportAccessRequest.created_at.desc())))
