"""Logika Support Access: prosba -> zgoda -> sesja -> walidacja kazdego zadania."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select

from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError
from forvium.core.security import (
    LAUNCH_CODE_PREFIX,
    SUPPORT_TOKEN_PREFIX,
    new_token,
    token_digest,
)
from forvium.identity.models import User
from forvium.identity.service import consume_totp
from forvium.organizations.models import Membership, Organization
from forvium.organizations.rbac import Permission, permissions_for_role
from forvium.platform_admin.rbac import PlatformPermission, platform_permissions
from forvium.support_access.break_glass import BreakGlassDisabled, IncidentCategory, ensure_break_glass_allowed
from forvium.support_access.models import (
    AccessLevel,
    AccessMode,
    ConsentBasis,
    RequestStatus,
    SessionStatus,
    SupportAccessRequest,
    SupportConsent,
    SupportSession,
    SupportStandingConsent,
)
from forvium.support_access.scopes import (
    SupportScope,
    effective_support_permissions,
    operator_scope_cap,
    parse_scopes,
)
from forvium.support_access.summary import session_summary, summary_text
from forvium.support_tickets.service import find_active_ticket, is_ticket_active

# ---------------------------------------------------------------- pomocnicze


def _deny(ctx: Ctx, action: str, code: str, message: str, status: int = 403, **audit_kwargs) -> DomainError:
    """Rejestruje nieudana probe i zwraca wyjatek do podniesienia."""
    details = audit_kwargs.pop("details", {}) or {}
    details["reason"] = code
    ctx.audit.record(action, outcome="denied", ip_address=ctx.ip, details=details, **audit_kwargs)
    return DomainError(status, code, message)


def _membership(ctx: Ctx, organization_id: str, user_id: str) -> Membership | None:
    return ctx.db.scalar(
        select(Membership).where(Membership.organization_id == organization_id, Membership.user_id == user_id)
    )


def _org_approvers(ctx: Ctx, organization_id: str, exclude_user_id: str | None = None) -> list[User]:
    rows = ctx.db.execute(
        select(User, Membership.role)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.organization_id == organization_id, User.is_active.is_(True))
    ).all()
    return [
        user
        for user, role in rows
        if Permission.SUPPORT_ACCESS_APPROVE in permissions_for_role(role) and user.id != exclude_user_id
    ]


def _verify_operator_mfa(ctx: Ctx, operator: User, mfa_code: str | None, action: str, **audit_kwargs) -> None:
    who = {"actor_user_id": operator.id, "actor_type": "operator", "ip_address": ctx.ip}
    ctx.throttle.check("mfa_stepup", operator.id, **who)
    if consume_totp(operator, mfa_code):
        ctx.throttle.reset("mfa_stepup", operator.id)
        return
    ctx.throttle.fail("mfa_stepup", operator.id, **who)
    raise _deny(ctx, action, "mfa_reverification_failed", "Wymagana ponowna weryfikacja MFA operatora.",
                status=401, actor_user_id=operator.id, actor_type="operator", **audit_kwargs)


def _require_platform(ctx: Ctx, operator: User, permission: PlatformPermission, action: str) -> None:
    if not operator.is_active or permission not in platform_permissions(operator.platform_role):
        raise _deny(ctx, action, "operator_not_permitted", "Brak uprawnien operatora.",
                    actor_user_id=operator.id, actor_type="operator")


# ------------------------------------------------------------------- prosby


def create_request(
    ctx: Ctx,
    operator: User,
    *,
    organization_id: str,
    reference_user_id: str,
    reason: str,
    ticket_number: str,
    duration_minutes: int | None,
    scopes: list[str],
    mfa_code: str | None,
    mode: str = AccessMode.STANDARD,
    incident_category: str | None = None,
) -> SupportAccessRequest:
    break_glass = mode == AccessMode.BREAK_GLASS
    action = "break_glass.request.create" if break_glass else "support.request.create"
    base = {"actor_user_id": operator.id, "actor_type": "operator", "organization_id": organization_id,
            "on_behalf_of_user_id": reference_user_id}

    if break_glass:
        try:
            ensure_break_glass_allowed(ctx.break_glass)
        except BreakGlassDisabled:
            raise _deny(ctx, action, "break_glass_disabled", "Dostep awaryjny (Break Glass) jest wylaczony.", **base)
        _require_platform(ctx, operator, PlatformPermission.BREAK_GLASS_REQUEST, action)
    elif mode != AccessMode.STANDARD:
        raise _deny(ctx, action, "mode_invalid", "Nieznany tryb dostepu.", status=422, **base)
    else:
        _require_platform(ctx, operator, PlatformPermission.SUPPORT_ACCESS_REQUEST, action)

    org = ctx.db.get(Organization, organization_id)
    if org is None or org.deleted_at is not None:
        raise _deny(ctx, action, "organization_not_found", "Nie znaleziono organizacji.", status=404, **base)

    reference = ctx.db.get(User, reference_user_id)
    if reference is None or not reference.is_active or _membership(ctx, organization_id, reference_user_id) is None:
        raise _deny(ctx, action, "reference_user_invalid",
                    "Uzytkownik referencyjny nie nalezy do organizacji.", status=422, **base)
    if reference.id == operator.id:
        raise _deny(ctx, action, "self_reference", "Operator nie moze odtwarzac wlasnego widoku.", status=422, **base)

    min_reason = ctx.break_glass.min_justification_length if break_glass else ctx.policy.min_reason_length
    if len((reason or "").strip()) < min_reason:
        raise _deny(ctx, action, "reason_too_short",
                    f"Podaj szczegolowe uzasadnienie (min. {min_reason} znakow).", status=422, **base)
    if break_glass:
        try:
            incident_category = IncidentCategory(incident_category or "").value
        except ValueError:
            raise _deny(ctx, action, "incident_category_invalid", "Wybierz kategorie incydentu.", status=422, **base)
    else:
        incident_category = None

    ticket = find_active_ticket(ctx.db, ticket_number or "", organization_id)
    if ticket is None:
        raise _deny(ctx, action, "ticket_invalid",
                    "Zgloszenie nie istnieje, jest zamkniete lub dotyczy innej organizacji.", status=422, **base)

    try:
        requested = parse_scopes(scopes)
    except ValueError:
        raise _deny(ctx, action, "scope_invalid", "Nieznany zakres dostepu.", status=422, **base)
    if not requested:
        raise _deny(ctx, action, "scope_empty", "Wybierz co najmniej jeden zakres.", status=422, **base)
    if not requested <= operator_scope_cap(operator.platform_role):
        raise _deny(ctx, action, "scope_exceeds_operator",
                    "Zakres przekracza uprawnienia operatora.", **base)

    max_minutes = ctx.break_glass.max_session_minutes if break_glass else ctx.policy.max_session_minutes
    duration = duration_minutes or ctx.policy.default_session_minutes
    if duration < 1 or duration > max_minutes:
        raise _deny(ctx, action, "duration_invalid",
                    f"Czas dostepu musi miescic sie w 1-{max_minutes} min.", status=422, **base)

    # Ponowna weryfikacja MFA jako ostatni krok przed zapisem (kod jest jednorazowy).
    _verify_operator_mfa(ctx, operator, mfa_code, action, organization_id=organization_id)

    now = clock.now()
    req = SupportAccessRequest(
        mode=AccessMode.BREAK_GLASS if break_glass else AccessMode.STANDARD,
        operator_user_id=operator.id,
        organization_id=organization_id,
        reference_user_id=reference_user_id,
        ticket_id=ticket.id,
        ticket_number=ticket.number,
        reason=reason.strip(),
        requested_scopes=sorted(s.value for s in requested),
        requested_duration_minutes=duration,
        access_level=AccessLevel.READ_ONLY,
        status=RequestStatus.PENDING_SECOND_APPROVAL if break_glass else RequestStatus.PENDING,
        incident_category=incident_category,
        created_at=now,
        decision_deadline=now + (timedelta(minutes=ctx.break_glass.approval_window_minutes) if break_glass
                                 else timedelta(hours=ctx.policy.decision_window_hours)),
    )
    ctx.db.add(req)
    ctx.db.flush()

    if break_glass:
        from forvium.support_access.break_glass_service import on_break_glass_requested

        on_break_glass_requested(ctx, req, operator, org)
        return req

    ctx.audit.log(
        ctx.db,
        "support.request.created",
        support_request_id=req.id,
        ip_address=ctx.ip,
        details={"ticket": ticket.number, "scopes": req.requested_scopes, "duration_minutes": duration,
                 "reason": req.reason},
        **base,
    )

    approvers = _org_approvers(ctx, organization_id, exclude_user_id=operator.id)
    standing = find_matching_standing_consent(ctx, organization_id, operator, requested, duration)
    if standing is not None:
        consent = _auto_approve_from_standing(ctx, req, standing)
        ctx.notifications.notify(
            ctx.db,
            approvers,
            event="support_access.auto_approved",
            title=f"Dostep serwisowy Forvium zatwierdzony automatycznie ({ticket.number})",
            body=(
                f"Operator Forvium ({operator.id}) uzyskal dostep READ_ONLY do organizacji {org.name} "
                f"na podstawie Waszej zgody stalej. Powod: {req.reason}. Zgoda wazna do "
                f"{consent.valid_until.isoformat()} UTC. Mozesz ja cofnac: Ustawienia -> Dostep serwisowy."
            ),
            organization_id=organization_id,
            data={"request_id": req.id, "consent_id": consent.id, "standing_consent_id": standing.id},
        )
        return req

    ctx.notifications.notify(
        ctx.db,
        approvers,
        event="support_access.requested",
        title=f"Forvium prosi o dostep serwisowy ({ticket.number})",
        body=(
            f"Operator Forvium ({operator.id}) prosi o dostep serwisowy READ_ONLY do organizacji "
            f"{org.name} na {duration} min. Powod: {req.reason}. Zatwierdz lub odrzuc prosbe "
            "w aplikacji: Ustawienia -> Dostep serwisowy."
        ),
        organization_id=organization_id,
        data={"request_id": req.id},
    )
    return req


def find_matching_standing_consent(
    ctx: Ctx, organization_id: str, operator: User, scopes: frozenset[SupportScope], duration: int
) -> SupportStandingConsent | None:
    now = clock.now()
    candidates = ctx.db.scalars(
        select(SupportStandingConsent).where(
            SupportStandingConsent.organization_id == organization_id,
            SupportStandingConsent.revoked_at.is_(None),
            SupportStandingConsent.valid_until > now,
        ).order_by(SupportStandingConsent.created_at)
    )
    for standing in candidates:
        if not scopes <= parse_scopes(standing.scopes):
            continue
        if duration > standing.max_session_minutes:
            continue
        if standing.allowed_platform_roles and operator.platform_role not in standing.allowed_platform_roles:
            continue
        return standing
    return None


def _auto_approve_from_standing(ctx: Ctx, req: SupportAccessRequest, standing: SupportStandingConsent) -> SupportConsent:
    now = clock.now()
    req.status = RequestStatus.APPROVED
    req.decided_by_user_id = standing.granted_by_user_id
    req.decided_at = now
    req.decision_note = f"Zatwierdzono automatycznie (zgoda stala {standing.id})"
    consent = SupportConsent(
        request_id=req.id,
        organization_id=req.organization_id,
        operator_user_id=req.operator_user_id,
        reference_user_id=req.reference_user_id,
        granted_by_user_id=standing.granted_by_user_id,
        scopes=list(req.requested_scopes),
        unit_ids=standing.unit_ids,
        access_level=AccessLevel.READ_ONLY,
        max_session_minutes=req.requested_duration_minutes,
        granted_at=now,
        valid_until=min(now + timedelta(hours=ctx.policy.standing_grant_hours), standing.valid_until),
        basis=ConsentBasis.STANDING,
        standing_consent_id=standing.id,
    )
    ctx.db.add(consent)
    ctx.db.flush()
    ctx.audit.log(ctx.db, "support.request.auto_approved", actor_type="system",
                  organization_id=req.organization_id, on_behalf_of_user_id=req.reference_user_id,
                  support_request_id=req.id, ip_address=ctx.ip,
                  details={"consent_id": consent.id, "standing_consent_id": standing.id, "scopes": consent.scopes,
                           "valid_until": consent.valid_until.isoformat()})
    return consent


def _expire_stale_request(ctx: Ctx, req: SupportAccessRequest) -> None:
    if req.status in (RequestStatus.PENDING, RequestStatus.PENDING_SECOND_APPROVAL) \
            and clock.now() >= req.decision_deadline:
        req.status = RequestStatus.EXPIRED
        ctx.audit.log(ctx.db, "support.request.expired", actor_type="system", organization_id=req.organization_id,
                         support_request_id=req.id)


def _load_request_for_org(ctx: Ctx, request_id: str, organization_id: str) -> SupportAccessRequest:
    req = ctx.db.get(SupportAccessRequest, request_id)
    if req is None or req.organization_id != organization_id:
        raise DomainError(404, "request_not_found", "Nie znaleziono prosby.")
    _expire_stale_request(ctx, req)
    return req


def approve_request(
    ctx: Ctx,
    approver: User,
    *,
    organization_id: str,
    request_id: str,
    scopes: list[str] | None,
    unit_ids: list[str] | None,
    valid_hours: int | None,
    note: str | None,
) -> SupportConsent:
    """Zatwierdzenie przez uprawnionego przedstawiciela organizacji.

    Uprawnienie `SUPPORT_ACCESS_APPROVE` jest sprawdzane wczesniej przez RBAC
    (zaleznosc trasy); tutaj dodatkowo blokujemy samozatwierdzenie.
    """
    action = "support.request.approve"
    req = _load_request_for_org(ctx, request_id, organization_id)
    base = {"actor_user_id": approver.id, "actor_type": "user", "organization_id": organization_id,
            "support_request_id": req.id}

    if approver.id == req.operator_user_id:
        raise _deny(ctx, action, "self_approval", "Nie mozna zatwierdzic wlasnej prosby o dostep.", **base)
    if approver.platform_role is not None:
        # Zgode wydaje wylacznie przedstawiciel klienta, nigdy konto operatorskie Forvium.
        raise _deny(ctx, action, "operator_cannot_approve",
                    "Konto operatora Forvium nie moze zatwierdzac dostepu serwisowego.", **base)
    if req.status != RequestStatus.PENDING:
        raise _deny(ctx, action, "request_not_pending", "Prosba nie oczekuje na decyzje.", status=409, **base)

    requested = parse_scopes(req.requested_scopes)
    try:
        granted = parse_scopes(scopes) if scopes is not None else requested
    except ValueError:
        raise _deny(ctx, action, "scope_invalid", "Nieznany zakres dostepu.", status=422, **base)
    if not granted or not granted <= requested:
        raise _deny(ctx, action, "scope_exceeds_request",
                    "Zgoda moze obejmowac tylko zakresy, o ktore wnioskowano.", status=422, **base)

    if unit_ids:
        from forvium.organizations.models import OrgUnit

        found = set(
            ctx.db.scalars(
                select(OrgUnit.id).where(OrgUnit.organization_id == organization_id, OrgUnit.id.in_(unit_ids))
            )
        )
        if found != set(unit_ids):
            raise _deny(ctx, action, "unit_invalid", "Nieprawidlowe jednostki.", status=422, **base)

    hours = valid_hours or ctx.policy.default_consent_hours
    if hours < 1 or hours > ctx.policy.max_consent_hours:
        raise _deny(ctx, action, "validity_invalid",
                    f"Waznosc zgody: 1-{ctx.policy.max_consent_hours} h.", status=422, **base)

    now = clock.now()
    req.status = RequestStatus.APPROVED
    req.decided_by_user_id = approver.id
    req.decided_at = now
    req.decision_note = (note or "").strip() or None
    consent = SupportConsent(
        request_id=req.id,
        organization_id=organization_id,
        operator_user_id=req.operator_user_id,
        reference_user_id=req.reference_user_id,
        granted_by_user_id=approver.id,
        scopes=sorted(s.value for s in granted),
        unit_ids=sorted(unit_ids) if unit_ids else None,
        access_level=AccessLevel.READ_ONLY,
        max_session_minutes=req.requested_duration_minutes,
        granted_at=now,
        valid_until=now + timedelta(hours=hours),
    )
    ctx.db.add(consent)
    ctx.db.flush()

    operator = ctx.db.get(User, req.operator_user_id)
    if operator:
        ctx.notifications.notify(
            ctx.db, [operator], event="support_access.approved",
            title=f"Zgoda na dostep serwisowy ({req.ticket_number}) udzielona",
            body=f"Zgoda wazna do {consent.valid_until.isoformat()} UTC, zakres: {', '.join(consent.scopes)}.",
            organization_id=organization_id, data={"request_id": req.id, "consent_id": consent.id},
        )
    ctx.audit.log(
        ctx.db,
        "support.request.approved",
        ip_address=ctx.ip,
        details={"consent_id": consent.id, "scopes": consent.scopes, "unit_ids": consent.unit_ids,
                 "valid_until": consent.valid_until.isoformat()},
        **base,
    )
    return consent


def reject_request(ctx: Ctx, user: User, *, organization_id: str, request_id: str, note: str | None) -> None:
    action = "support.request.reject"
    req = _load_request_for_org(ctx, request_id, organization_id)
    base = {"actor_user_id": user.id, "actor_type": "user", "organization_id": organization_id,
            "support_request_id": req.id}
    if user.id == req.operator_user_id:
        raise _deny(ctx, action, "self_decision", "Nie mozna decydowac o wlasnej prosbie.", **base)
    if req.status != RequestStatus.PENDING:
        raise _deny(ctx, action, "request_not_pending", "Prosba nie oczekuje na decyzje.", status=409, **base)
    req.status = RequestStatus.REJECTED
    req.decided_by_user_id = user.id
    req.decided_at = clock.now()
    req.decision_note = (note or "").strip() or None
    operator = ctx.db.get(User, req.operator_user_id)
    if operator:
        ctx.notifications.notify(
            ctx.db, [operator], event="support_access.rejected",
            title=f"Prosba o dostep serwisowy ({req.ticket_number}) odrzucona",
            body="Klient odrzucil prosbe o dostep serwisowy.", organization_id=organization_id,
            data={"request_id": req.id},
        )
    ctx.audit.log(ctx.db, "support.request.rejected", ip_address=ctx.ip, **base)


def cancel_request(ctx: Ctx, operator: User, request_id: str) -> None:
    req = ctx.db.get(SupportAccessRequest, request_id)
    if req is None or req.operator_user_id != operator.id:
        raise DomainError(404, "request_not_found", "Nie znaleziono prosby.")
    if req.status not in (RequestStatus.PENDING, RequestStatus.PENDING_SECOND_APPROVAL):
        raise DomainError(409, "request_not_pending", "Prosba nie oczekuje na decyzje.")
    req.status = RequestStatus.CANCELLED
    ctx.audit.log(ctx.db, "support.request.cancelled", actor_user_id=operator.id, actor_type="operator",
                     organization_id=req.organization_id, support_request_id=req.id, ip_address=ctx.ip)


# ------------------------------------------------------------------- zgody


def _terminate_session(ctx: Ctx, session: SupportSession, status: SessionStatus, reason: str,
                       by_user_id: str | None, actor_type: str | None = None) -> None:
    if session.status != SessionStatus.ACTIVE:
        return
    session.status = status
    session.ended_at = clock.now()
    session.ended_by_user_id = by_user_id
    session.end_reason = reason
    # Skrot tokenu zostaje, aby kolejne proby uzycia zakonczonej sesji byly
    # odrzucane i audytowane z tozsamoscia operatora (status != ACTIVE).
    session.launch_code_hash = None
    action = {
        SessionStatus.EXPIRED: "support.session.expired",
        SessionStatus.REVOKED: "support.session.revoked",
    }.get(status, "support.session.ended")
    ctx.audit.log(
        ctx.db,
        action,
        actor_user_id=by_user_id,
        actor_type=actor_type or ("system" if by_user_id is None
                                  else "operator" if by_user_id == session.operator_user_id else "user"),
        on_behalf_of_user_id=session.reference_user_id,
        organization_id=session.organization_id,
        support_session_id=session.id,
        support_request_id=session.request_id,
        ip_address=ctx.ip,
        details={"reason": reason, "operator_user_id": session.operator_user_id},
    )
    _notify_session_summary(ctx, session)


def _notify_session_summary(ctx: Ctx, session: SupportSession) -> None:
    """Klient dostaje podsumowanie kazdej zakonczonej sesji (w aplikacji i e-mailem)."""
    summary = session_summary(ctx.db, session)
    ctx.notifications.notify(
        ctx.db,
        _org_approvers(ctx, session.organization_id, exclude_user_id=session.operator_user_id),
        event="support_access.session_ended",
        title=f"Zakonczono sesje wsparcia Forvium ({session.ticket_number})",
        body=(f"Operator Forvium {session.operator_user_id} zakonczyl sesje wsparcia w trybie tylko do odczytu.\n"
              + summary_text(summary)
              + "\nPelna lista operacji: Ustawienia -> Dostep serwisowy -> Historia sesji."),
        organization_id=session.organization_id,
        data={"session_id": session.id, "summary": summary},
    )


def revoke_consent(ctx: Ctx, user: User, *, organization_id: str, consent_id: str) -> SupportConsent:
    consent = ctx.db.get(SupportConsent, consent_id)
    if consent is None or consent.organization_id != organization_id:
        raise DomainError(404, "consent_not_found", "Nie znaleziono zgody.")
    if consent.revoked_at is not None:
        return consent
    consent.revoked_at = clock.now()
    consent.revoked_by_user_id = user.id
    ctx.audit.log(ctx.db, "support.consent.revoked", actor_user_id=user.id, actor_type="user",
                     organization_id=organization_id, support_request_id=consent.request_id, ip_address=ctx.ip,
                     details={"consent_id": consent.id})
    for session in ctx.db.scalars(
        select(SupportSession).where(SupportSession.consent_id == consent.id,
                                     SupportSession.status == SessionStatus.ACTIVE)
    ):
        _terminate_session(ctx, session, SessionStatus.REVOKED, "consent_revoked", user.id)
    operator = ctx.db.get(User, consent.operator_user_id)
    if operator:
        ctx.notifications.notify(ctx.db, [operator], event="support_access.consent_revoked",
                                 title="Klient cofnal zgode na dostep serwisowy",
                                 body="Wszystkie aktywne sesje wsparcia zostaly zakonczone.",
                                 organization_id=organization_id, data={"consent_id": consent.id})
    return consent


# ------------------------------------------------------------------- sesje


def start_session(
    ctx: Ctx, operator: User, *, request_id: str, mfa_code: str | None, duration_minutes: int | None
) -> tuple[SupportSession, str]:
    action = "support.session.start"
    req = ctx.db.get(SupportAccessRequest, request_id)
    if req is None:
        raise _deny(ctx, action, "request_not_found", "Nie znaleziono prosby.", status=404,
                    actor_user_id=operator.id, actor_type="operator")
    base = {"actor_user_id": operator.id, "actor_type": "operator", "organization_id": req.organization_id,
            "on_behalf_of_user_id": req.reference_user_id, "support_request_id": req.id}

    _require_platform(ctx, operator, PlatformPermission.SUPPORT_ACCESS_START, action)
    if req.operator_user_id != operator.id:
        raise _deny(ctx, action, "not_request_owner", "Sesje moze uruchomic tylko operator, ktory zlozyl prosbe.",
                    **base)
    _expire_stale_request(ctx, req)
    if req.status != RequestStatus.APPROVED:
        raise _deny(ctx, action, "no_consent", "Brak zgody klienta na dostep serwisowy.", **base)

    consent = ctx.db.scalar(select(SupportConsent).where(SupportConsent.request_id == req.id))
    now = clock.now()
    if consent is None or consent.revoked_at is not None or now >= consent.valid_until:
        raise _deny(ctx, action, "consent_inactive", "Zgoda klienta zostala cofnieta lub wygasla.", **base)

    if not is_ticket_active(ctx.db, req.ticket_id):
        raise _deny(ctx, action, "ticket_closed", "Zgloszenie supportowe jest zamkniete.", **base)

    active = ctx.db.scalar(
        select(SupportSession).where(SupportSession.consent_id == consent.id,
                                     SupportSession.status == SessionStatus.ACTIVE)
    )
    if active is not None and now < active.expires_at:
        raise _deny(ctx, action, "session_already_active", "Sesja w ramach tej zgody jest juz aktywna.",
                    status=409, **base)

    member = _membership(ctx, req.organization_id, req.reference_user_id)
    permissions = effective_support_permissions(
        reference_user_role=member.role if member else None,
        consent_scopes=parse_scopes(consent.scopes),
        operator_platform_role=operator.platform_role,
    )
    if not permissions:
        raise _deny(ctx, action, "empty_permissions", "Zakres zgody nie daje zadnych uprawnien.", **base)

    policy_max = ctx.break_glass.max_session_minutes if req.mode == AccessMode.BREAK_GLASS \
        else ctx.policy.max_session_minutes
    minutes = min(duration_minutes or consent.max_session_minutes, consent.max_session_minutes, policy_max)
    if minutes < 1:
        raise _deny(ctx, action, "duration_invalid", "Nieprawidlowy czas sesji.", status=422, **base)
    expires_at = min(now + timedelta(minutes=minutes), consent.valid_until)

    # Zapisy dopiero po wszystkich sprawdzeniach (odmowy sa audytowane w osobnej transakcji).
    _verify_operator_mfa(ctx, operator, mfa_code, action, organization_id=req.organization_id,
                         support_request_id=req.id)
    if active is not None:
        _terminate_session(ctx, active, SessionStatus.EXPIRED, "session_expired", None)

    launch_code = new_token(LAUNCH_CODE_PREFIX)
    session = SupportSession(
        operator_user_id=operator.id,
        organization_id=req.organization_id,
        reference_user_id=req.reference_user_id,
        consent_id=consent.id,
        request_id=req.id,
        ticket_id=req.ticket_id,
        ticket_number=req.ticket_number,
        access_level=AccessLevel.READ_ONLY,
        permissions=sorted(p.value for p in permissions),
        scopes=list(consent.scopes),
        unit_ids=consent.unit_ids,
        started_at=now,
        expires_at=expires_at,
        status=SessionStatus.ACTIVE,
        launch_code_hash=token_digest(launch_code),
        launch_code_expires_at=now + timedelta(seconds=ctx.policy.launch_code_seconds),
    )
    ctx.db.add(session)
    ctx.db.flush()

    ctx.notifications.notify(
        ctx.db, _org_approvers(ctx, req.organization_id, exclude_user_id=operator.id),
        event="support_access.session_started",
        title=(f"PROCEDURA AWARYJNA: rozpoczeto sesje Forvium Break Glass ({req.ticket_number})"
               if req.mode == AccessMode.BREAK_GLASS else f"Rozpoczeto sesje wsparcia Forvium ({req.ticket_number})"),
        body=(f"Operator Forvium {operator.id} rozpoczal sesje wsparcia w trybie tylko do odczytu "
              f"(zgloszenie {req.ticket_number}). Sesja wygasa {expires_at.isoformat()} UTC. "
              "Mozesz ja zakonczyc lub cofnac zgode w kazdej chwili: Ustawienia -> Dostep serwisowy."),
        organization_id=req.organization_id, data={"session_id": session.id},
    )
    if req.mode == AccessMode.BREAK_GLASS:
        from forvium.support_access.break_glass_service import notify_security_team

        notify_security_team(ctx, f"Break Glass: start sesji ({req.ticket_number})",
                             f"Operator {operator.id} rozpoczal sesje awaryjna {session.id} w organizacji "
                             f"{req.organization_id} do {expires_at.isoformat()} UTC.")
    ctx.audit.log(
        ctx.db,
        "support.session.started",
        support_session_id=session.id,
        ip_address=ctx.ip,
        details={"expires_at": expires_at.isoformat(), "permissions": session.permissions,
                 "consent_id": consent.id, "ticket": req.ticket_number},
        **base,
    )
    return session, launch_code


def exchange_launch_code(ctx: Ctx, code: str) -> tuple[SupportSession, str]:
    """Wymienia jednorazowy kod na token sesji wsparcia (wywolywane z app.forvium.com).

    Token sesji wsparcia nigdy nie trafia do panelu admin; nie jest tez
    zapisywany w ciasteczkach klienta, wiec nie nadpisuje jego sesji.
    """
    action = "support.session.launch"
    ctx.throttle.check("launch_ip", ctx.ip, actor_type="anonymous", ip_address=ctx.ip)
    now = clock.now()
    session = ctx.db.scalar(select(SupportSession).where(SupportSession.launch_code_hash == token_digest(code or "")))
    if session is None or session.status != SessionStatus.ACTIVE or session.launch_code_expires_at is None \
            or now >= session.launch_code_expires_at or now >= session.expires_at:
        ctx.throttle.fail("launch_ip", ctx.ip, actor_type="anonymous", ip_address=ctx.ip)
        raise _deny(ctx, action, "launch_code_invalid", "Kod uruchomienia jest nieprawidlowy lub wygasl.",
                    status=401, actor_type="anonymous",
                    support_session_id=session.id if session else None,
                    organization_id=session.organization_id if session else None)
    token = new_token(SUPPORT_TOKEN_PREFIX)
    session.token_hash = token_digest(token)
    session.launch_code_hash = None
    session.launch_code_expires_at = None
    ctx.audit.log(ctx.db, "support.session.launched", actor_user_id=session.operator_user_id, actor_type="support",
                     on_behalf_of_user_id=session.reference_user_id, organization_id=session.organization_id,
                     support_session_id=session.id, support_request_id=session.request_id, ip_address=ctx.ip)
    return session, token


@dataclass
class ValidatedSupportSession:
    session: SupportSession
    operator: User
    reference_user: User
    organization: Organization
    permissions: frozenset[Permission]
    mode: str = AccessMode.STANDARD


def validate_support_token(ctx: Ctx, token: str) -> ValidatedSupportSession:
    """Pelna walidacja sesji wsparcia - wywolywana przy KAZDYM zadaniu API.

    Zmiany statusu (wygasniecie, cofniecie) sa zatwierdzane od razu, bo
    zadanie zakonczy sie wyjatkiem i rollbackiem.
    """
    action = "support.access_denied"
    ctx.throttle.check("support_token_ip", ctx.ip, actor_type="anonymous", ip_address=ctx.ip)
    now = clock.now()
    session = ctx.db.scalar(select(SupportSession).where(SupportSession.token_hash == token_digest(token)))
    if session is None:
        ctx.throttle.fail("support_token_ip", ctx.ip, actor_type="anonymous", ip_address=ctx.ip)
        raise _deny(ctx, action, "invalid_support_token", "Sesja wsparcia jest nieprawidlowa lub zakonczona.",
                    status=401, actor_type="anonymous")

    base = {"actor_user_id": session.operator_user_id, "actor_type": "support",
            "on_behalf_of_user_id": session.reference_user_id, "organization_id": session.organization_id,
            "support_session_id": session.id, "support_request_id": session.request_id}

    def fail(status: SessionStatus, reason: str) -> DomainError:
        _terminate_session(ctx, session, status, reason, None)
        ctx.db.commit()
        return _deny(ctx, action, reason, "Sesja wsparcia nie jest juz aktywna.", status=401, **base)

    if session.status != SessionStatus.ACTIVE:
        raise _deny(ctx, action, "session_not_active", "Sesja wsparcia nie jest juz aktywna.", status=401, **base)
    if now >= session.expires_at:
        raise fail(SessionStatus.EXPIRED, "session_expired")

    consent = ctx.db.get(SupportConsent, session.consent_id)
    if consent is None or consent.revoked_at is not None:
        raise fail(SessionStatus.REVOKED, "consent_revoked")
    if now >= consent.valid_until:
        raise fail(SessionStatus.EXPIRED, "consent_expired")
    if consent.standing_consent_id:
        standing = ctx.db.get(SupportStandingConsent, consent.standing_consent_id)
        if standing is None or standing.revoked_at is not None or now >= standing.valid_until:
            raise fail(SessionStatus.REVOKED, "consent_revoked")
    req = ctx.db.get(SupportAccessRequest, session.request_id)
    if req is None or req.status != RequestStatus.APPROVED:
        raise fail(SessionStatus.REVOKED, "request_not_approved")

    operator = ctx.db.get(User, session.operator_user_id)
    if operator is None or not operator.is_active or \
            PlatformPermission.SUPPORT_ACCESS_START not in platform_permissions(operator.platform_role):
        raise fail(SessionStatus.REVOKED, "operator_not_permitted")

    org = ctx.db.get(Organization, session.organization_id)
    if org is None or org.deleted_at is not None:
        raise fail(SessionStatus.REVOKED, "organization_unavailable")

    reference = ctx.db.get(User, session.reference_user_id)
    member = _membership(ctx, session.organization_id, session.reference_user_id)
    if reference is None or not reference.is_active or member is None:
        raise fail(SessionStatus.REVOKED, "reference_user_unavailable")

    if not is_ticket_active(ctx.db, session.ticket_id):
        raise fail(SessionStatus.ENDED, "ticket_closed")

    # Przeliczenie uprawnien na biezacym stanie i przeciecie z zamrozonym zestawem.
    current = effective_support_permissions(
        reference_user_role=member.role,
        consent_scopes=parse_scopes(consent.scopes),
        operator_platform_role=operator.platform_role,
    )
    frozen = frozenset(Permission(p) for p in session.permissions)
    return ValidatedSupportSession(session, operator, reference, org, current & frozen, req.mode)


def end_session(ctx: Ctx, session: SupportSession, by_user_id: str, reason: str,
                actor_type: str | None = None) -> None:
    _terminate_session(ctx, session, SessionStatus.ENDED, reason, by_user_id, actor_type)


def sweep_expired(ctx: Ctx) -> int:
    """Oznacza wygasle sesje i prosby (do wywolywania cyklicznie przez scheduler)."""
    now = clock.now()
    count = 0
    for session in ctx.db.scalars(
        select(SupportSession).where(SupportSession.status == SessionStatus.ACTIVE, SupportSession.expires_at <= now)
    ):
        _terminate_session(ctx, session, SessionStatus.EXPIRED, "session_expired", None)
        count += 1
    for req in ctx.db.scalars(
        select(SupportAccessRequest).where(SupportAccessRequest.status.in_(
            [RequestStatus.PENDING, RequestStatus.PENDING_SECOND_APPROVAL]),
                                           SupportAccessRequest.decision_deadline <= now)
    ):
        _expire_stale_request(ctx, req)
    return count


def unit_filter_ids(ctx: Ctx, organization_id: str, root_ids: list[str] | None) -> set[str] | None:
    """Zwraca zbior ID jednostek dostepnych w ramach zgody (z poddrzewami) albo None = wszystkie."""
    if not root_ids:
        return None
    from forvium.organizations.models import OrgUnit

    units = list(ctx.db.scalars(select(OrgUnit).where(OrgUnit.organization_id == organization_id)))
    children: dict[str | None, list[str]] = {}
    for u in units:
        children.setdefault(u.parent_id, []).append(u.id)
    allowed: set[str] = set()
    stack = list(root_ids)
    while stack:
        uid = stack.pop()
        if uid in allowed:
            continue
        allowed.add(uid)
        stack.extend(children.get(uid, []))
    return allowed


def remaining_seconds(session: SupportSession, now: datetime | None = None) -> int:
    return max(0, int((session.expires_at - (now or clock.now())).total_seconds()))


__all__ = [
    "SupportScope",
    "create_request",
    "approve_request",
    "reject_request",
    "cancel_request",
    "revoke_consent",
    "start_session",
    "exchange_launch_code",
    "validate_support_token",
    "end_session",
    "sweep_expired",
    "unit_filter_ids",
    "remaining_seconds",
]
