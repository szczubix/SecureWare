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
from forvium.core.i18n import L, join

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


def _verify_operator_mfa(ctx: Ctx, operator: User, mfa_code: str | None, action: str, *,
                         webauthn: dict | None = None, require_hardware: bool = False, **audit_kwargs) -> None:
    """Ponowna weryfikacja operatora: klucz WebAuthn (preferowany) albo jednorazowy kod TOTP.

    `require_hardware=True` (np. Break Glass) akceptuje wylacznie WebAuthn.
    """
    from forvium.identity.webauthn import verify_assertion

    who = {"actor_user_id": operator.id, "actor_type": "operator", "ip_address": ctx.ip}
    ctx.throttle.check("mfa_stepup", operator.id, **who)
    if webauthn is not None:
        ok, method = verify_assertion(ctx, operator, webauthn), "webauthn"
    elif require_hardware:
        raise _deny(ctx, action, "hardware_mfa_required",
                    "Ta operacja wymaga potwierdzenia kluczem bezpieczeństwa (WebAuthn).",
                    status=401, actor_user_id=operator.id, actor_type="operator", **audit_kwargs)
    else:
        ok, method = consume_totp(operator, mfa_code), "totp"
    if ok:
        ctx.throttle.reset("mfa_stepup", operator.id)
        return
    ctx.throttle.fail("mfa_stepup", operator.id, **who)
    raise _deny(ctx, action, "mfa_reverification_failed", "Wymagana ponowna weryfikacja MFA operatora.",
                status=401, actor_user_id=operator.id, actor_type="operator",
                details={"method": method}, **audit_kwargs)


def _require_platform(ctx: Ctx, operator: User, permission: PlatformPermission, action: str) -> None:
    if not operator.is_active or permission not in platform_permissions(operator.platform_role):
        raise _deny(ctx, action, "operator_not_permitted", "Brak uprawnień operatora.",
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
    webauthn: dict | None = None,
) -> SupportAccessRequest:
    break_glass = mode == AccessMode.BREAK_GLASS
    action = "break_glass.request.create" if break_glass else "support.request.create"
    base = {"actor_user_id": operator.id, "actor_type": "operator", "organization_id": organization_id,
            "on_behalf_of_user_id": reference_user_id}

    if break_glass:
        try:
            ensure_break_glass_allowed(ctx.break_glass)
        except BreakGlassDisabled:
            raise _deny(ctx, action, "break_glass_disabled", "Dostęp awaryjny (Break Glass) jest wyłączony.", **base)
        _require_platform(ctx, operator, PlatformPermission.BREAK_GLASS_REQUEST, action)
    elif mode != AccessMode.STANDARD:
        raise _deny(ctx, action, "mode_invalid", "Nieznany tryb dostępu.", status=422, **base)
    else:
        _require_platform(ctx, operator, PlatformPermission.SUPPORT_ACCESS_REQUEST, action)

    org = ctx.db.get(Organization, organization_id)
    if org is None or org.deleted_at is not None:
        raise _deny(ctx, action, "organization_not_found", "Nie znaleziono organizacji.", status=404, **base)

    reference = ctx.db.get(User, reference_user_id)
    if reference is None or not reference.is_active or _membership(ctx, organization_id, reference_user_id) is None:
        raise _deny(ctx, action, "reference_user_invalid",
                    "Użytkownik referencyjny nie należy do organizacji.", status=422, **base)
    if reference.id == operator.id:
        raise _deny(ctx, action, "self_reference", "Operator nie może odtwarzać własnego widoku.", status=422, **base)

    min_reason = ctx.break_glass.min_justification_length if break_glass else ctx.policy.min_reason_length
    if len((reason or "").strip()) < min_reason:
        raise _deny(ctx, action, "reason_too_short",
                    L("Podaj szczegółowe uzasadnienie (min. {n} znaków).", n=min_reason), status=422, **base)
    if break_glass:
        try:
            incident_category = IncidentCategory(incident_category or "").value
        except ValueError:
            raise _deny(ctx, action, "incident_category_invalid", "Wybierz kategorię incydentu.", status=422, **base)
    else:
        incident_category = None

    ticket = find_active_ticket(ctx.db, ticket_number or "", organization_id)
    if ticket is None:
        raise _deny(ctx, action, "ticket_invalid",
                    "Zgłoszenie nie istnieje, jest zamknięte lub dotyczy innej organizacji.", status=422, **base)

    try:
        requested = parse_scopes(scopes)
    except ValueError:
        raise _deny(ctx, action, "scope_invalid", "Nieznany zakres dostępu.", status=422, **base)
    if not requested:
        raise _deny(ctx, action, "scope_empty", "Wybierz co najmniej jeden zakres.", status=422, **base)
    if not requested <= operator_scope_cap(operator.platform_role):
        raise _deny(ctx, action, "scope_exceeds_operator",
                    "Zakres przekracza uprawnienia operatora.", **base)

    max_minutes = ctx.break_glass.max_session_minutes if break_glass else ctx.policy.max_session_minutes
    duration = duration_minutes or ctx.policy.default_session_minutes
    if duration < 1 or duration > max_minutes:
        raise _deny(ctx, action, "duration_invalid",
                    L("Czas dostępu musi mieścić się w 1-{n} min.", n=max_minutes), status=422, **base)

    # Ponowna weryfikacja MFA jako ostatni krok przed zapisem (kod jest jednorazowy).
    _verify_operator_mfa(ctx, operator, mfa_code, action, webauthn=webauthn,
                         require_hardware=break_glass and ctx.break_glass.requires_hardware_mfa,
                         organization_id=organization_id)

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
            title=L("Dostęp serwisowy Forvium zatwierdzony automatycznie ({ticket})", ticket=ticket.number),
            body=L(
                "Operator Forvium ({operator}) uzyskał dostęp READ_ONLY do organizacji {org} "
                "na podstawie Waszej zgody stałej. Powód: {reason}. Zgoda ważna do "
                "{until} UTC. Możesz ją cofnąć: Ustawienia -> Dostęp serwisowy.",
                operator=operator.id, org=org.name, reason=req.reason, until=consent.valid_until.isoformat(),
            ),
            organization_id=organization_id,
            data={"request_id": req.id, "consent_id": consent.id, "standing_consent_id": standing.id},
        )
        return req

    ctx.notifications.notify(
        ctx.db,
        approvers,
        event="support_access.requested",
        title=L("Forvium prosi o dostęp serwisowy ({ticket})", ticket=ticket.number),
        body=L(
            "Operator Forvium ({operator}) prosi o dostęp serwisowy READ_ONLY do organizacji "
            "{org} na {minutes} min. Powód: {reason}. Zatwierdź lub odrzuć prośbę "
            "w aplikacji: Ustawienia -> Dostęp serwisowy.",
            operator=operator.id, org=org.name, minutes=duration, reason=req.reason,
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
            SupportStandingConsent.confirmed_at.is_not(None),
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
    req.decision_note = str(L("Zatwierdzono automatycznie (zgoda stała {id})", id=standing.id))
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
    if req.status in (RequestStatus.PENDING, RequestStatus.PENDING_SECOND_APPROVAL,
                      RequestStatus.PENDING_CUSTOMER_CONFIRMATION) \
            and clock.now() >= req.decision_deadline:
        req.status = RequestStatus.EXPIRED
        ctx.audit.log(ctx.db, "support.request.expired", actor_type="system", organization_id=req.organization_id,
                         support_request_id=req.id)


def _load_request_for_org(ctx: Ctx, request_id: str, organization_id: str) -> SupportAccessRequest:
    req = ctx.db.get(SupportAccessRequest, request_id)
    if req is None or req.organization_id != organization_id:
        raise DomainError(404, "request_not_found", "Nie znaleziono prośby.")
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
) -> SupportConsent | None:
    """Zatwierdzenie przez uprawnionego przedstawiciela organizacji.

    Uprawnienie `SUPPORT_ACCESS_APPROVE` jest sprawdzane wczesniej przez RBAC
    (zaleznosc trasy); tutaj dodatkowo blokujemy samozatwierdzenie.

    Gdy organizacja wlaczyla zatwierdzanie przez dwie osoby, pierwsze
    zatwierdzenie tylko zapisuje parametry zgody (status
    `pending_customer_confirmation`), a zgoda powstaje dopiero po potwierdzeniu
    przez INNEGO uprawnionego przedstawiciela (moze on jeszcze zawezic zakres).
    Zwraca zgode albo None, gdy czeka ona na drugie zatwierdzenie.
    """
    action = "support.request.approve"
    req = _load_request_for_org(ctx, request_id, organization_id)
    base = {"actor_user_id": approver.id, "actor_type": "user", "organization_id": organization_id,
            "support_request_id": req.id}

    if approver.id == req.operator_user_id:
        raise _deny(ctx, action, "self_approval", "Nie można zatwierdzić własnej prośby o dostęp.", **base)
    if approver.platform_role is not None:
        # Zgode wydaje wylacznie przedstawiciel klienta, nigdy konto operatorskie Forvium.
        raise _deny(ctx, action, "operator_cannot_approve",
                    "Konto operatora Forvium nie może zatwierdzać dostępu serwisowego.", **base)
    confirming = req.status == RequestStatus.PENDING_CUSTOMER_CONFIRMATION
    if req.status != RequestStatus.PENDING and not confirming:
        raise _deny(ctx, action, "request_not_pending", "Prośba nie oczekuje na decyzje.", status=409, **base)
    if confirming and approver.id == req.first_approved_by_user_id:
        raise _deny(ctx, action, "second_approver_required",
                    "Zgodę musi potwierdzić inna osoba niż pierwsza zatwierdzająca.", **base)

    # Przy potwierdzeniu punktem odniesienia sa parametry z pierwszego zatwierdzenia.
    grant = (req.pending_grant or {}) if confirming else {}
    requested = parse_scopes(grant.get("scopes") or req.requested_scopes)
    try:
        granted = parse_scopes(scopes) if scopes is not None else requested
    except ValueError:
        raise _deny(ctx, action, "scope_invalid", "Nieznany zakres dostępu.", status=422, **base)
    if not granted or not granted <= requested:
        raise _deny(ctx, action, "scope_exceeds_request",
                    "Zgoda może obejmować tylko zakresy, o które wnioskowano.", status=422, **base)

    if confirming:
        first_units = grant.get("unit_ids")
        # Pusta lista nie moze znaczyc "wszystkie jednostki" - druga osoba moze tylko zawezic.
        if not unit_ids:
            unit_ids = first_units
        elif first_units and not set(unit_ids) <= set(first_units):
            raise _deny(ctx, action, "unit_exceeds_first_approval",
                        "Potwierdzenie może tylko zawęzić jednostki.", status=422, **base)
        valid_hours = min(valid_hours or grant["valid_hours"], grant["valid_hours"])
    if unit_ids:
        from forvium.organizations.models import OrgUnit

        found = set(
            ctx.db.scalars(
                select(OrgUnit.id).where(OrgUnit.organization_id == organization_id, OrgUnit.id.in_(unit_ids))
            )
        )
        if found != set(unit_ids):
            raise _deny(ctx, action, "unit_invalid", "Nieprawidłowe jednostki.", status=422, **base)

    hours = valid_hours or ctx.policy.default_consent_hours
    if hours < 1 or hours > ctx.policy.max_consent_hours:
        raise _deny(ctx, action, "validity_invalid",
                    L("Ważność zgody: 1-{n} h.", n=ctx.policy.max_consent_hours), status=422, **base)

    now = clock.now()
    org = ctx.db.get(Organization, organization_id)
    if org.support_dual_approval and not confirming:
        req.status = RequestStatus.PENDING_CUSTOMER_CONFIRMATION
        req.first_approved_by_user_id = approver.id
        req.first_approved_at = now
        req.pending_grant = {"scopes": sorted(s.value for s in granted),
                             "unit_ids": sorted(unit_ids) if unit_ids else None, "valid_hours": hours,
                             "note": (note or "").strip() or None}
        ctx.audit.log(ctx.db, "support.request.first_approval", ip_address=ctx.ip,
                      details={"grant": req.pending_grant}, **base)
        ctx.notifications.notify(
            ctx.db, _org_approvers(ctx, organization_id, exclude_user_id=approver.id),
            event="support_access.confirmation_required",
            title=L("Potwierdź dostęp serwisowy Forvium ({ticket})", ticket=req.ticket_number),
            body=L("{name} zatwierdził(a) dostęp serwisowy (zakres: {scopes}). Wasza organizacja wymaga "
                   "drugiego potwierdzenia: Ustawienia -> Dostęp serwisowy.",
                   name=approver.display_name, scopes=", ".join(req.pending_grant["scopes"])),
            organization_id=organization_id, data={"request_id": req.id},
        )
        return None

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
    if confirming:
        consent.granted_by_user_id = req.first_approved_by_user_id
        consent.second_approver_user_id = approver.id
    ctx.db.add(consent)
    ctx.db.flush()

    operator = ctx.db.get(User, req.operator_user_id)
    if operator:
        ctx.notifications.notify(
            ctx.db, [operator], event="support_access.approved",
            title=L("Zgoda na dostęp serwisowy ({ticket}) udzielona", ticket=req.ticket_number),
            body=L("Zgoda ważna do {until} UTC, zakres: {scopes}.", until=consent.valid_until.isoformat(),
                   scopes=", ".join(consent.scopes)),
            organization_id=organization_id, data={"request_id": req.id, "consent_id": consent.id},
        )
    ctx.audit.log(
        ctx.db,
        "support.request.approved",
        ip_address=ctx.ip,
        details={"consent_id": consent.id, "scopes": consent.scopes, "unit_ids": consent.unit_ids,
                 "valid_until": consent.valid_until.isoformat(),
                 "first_approver": req.first_approved_by_user_id if confirming else approver.id,
                 "second_approver": approver.id if confirming else None},
        **base,
    )
    return consent


def reject_request(ctx: Ctx, user: User, *, organization_id: str, request_id: str, note: str | None) -> None:
    action = "support.request.reject"
    req = _load_request_for_org(ctx, request_id, organization_id)
    base = {"actor_user_id": user.id, "actor_type": "user", "organization_id": organization_id,
            "support_request_id": req.id}
    if user.id == req.operator_user_id:
        raise _deny(ctx, action, "self_decision", "Nie można decydować o własnej prośbie.", **base)
    if req.status not in (RequestStatus.PENDING, RequestStatus.PENDING_CUSTOMER_CONFIRMATION):
        raise _deny(ctx, action, "request_not_pending", "Prośba nie oczekuje na decyzje.", status=409, **base)
    req.status = RequestStatus.REJECTED
    req.decided_by_user_id = user.id
    req.decided_at = clock.now()
    req.decision_note = (note or "").strip() or None
    operator = ctx.db.get(User, req.operator_user_id)
    if operator:
        ctx.notifications.notify(
            ctx.db, [operator], event="support_access.rejected",
            title=L("Prośba o dostęp serwisowy ({ticket}) odrzucona", ticket=req.ticket_number),
            body="Klient odrzucił prośbę o dostęp serwisowy.", organization_id=organization_id,
            data={"request_id": req.id},
        )
    ctx.audit.log(ctx.db, "support.request.rejected", ip_address=ctx.ip, **base)


def cancel_request(ctx: Ctx, operator: User, request_id: str) -> None:
    req = ctx.db.get(SupportAccessRequest, request_id)
    if req is None or req.operator_user_id != operator.id:
        raise DomainError(404, "request_not_found", "Nie znaleziono prośby.")
    if req.status not in (RequestStatus.PENDING, RequestStatus.PENDING_SECOND_APPROVAL):
        raise DomainError(409, "request_not_pending", "Prośba nie oczekuje na decyzje.")
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
        title=L("Zakończono sesję wsparcia Forvium ({ticket})", ticket=session.ticket_number),
        body=join("\n", [
            L("Operator Forvium {operator} zakończył sesję wsparcia w trybie tylko do odczytu.",
              operator=session.operator_user_id),
            summary_text(summary),
            L("Pełna lista operacji: Ustawienia -> Dostęp serwisowy -> Historia sesji."),
        ]),
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
                                 title="Klient cofnął zgodę na dostęp serwisowy",
                                 body="Wszystkie aktywne sesje wsparcia zostały zakończone.",
                                 organization_id=organization_id, data={"consent_id": consent.id})
    return consent


# ------------------------------------------------------------------- sesje


def start_session(
    ctx: Ctx, operator: User, *, request_id: str, mfa_code: str | None, duration_minutes: int | None,
    webauthn: dict | None = None,
) -> tuple[SupportSession, str]:
    action = "support.session.start"
    req = ctx.db.get(SupportAccessRequest, request_id)
    if req is None:
        raise _deny(ctx, action, "request_not_found", "Nie znaleziono prośby.", status=404,
                    actor_user_id=operator.id, actor_type="operator")
    base = {"actor_user_id": operator.id, "actor_type": "operator", "organization_id": req.organization_id,
            "on_behalf_of_user_id": req.reference_user_id, "support_request_id": req.id}

    _require_platform(ctx, operator, PlatformPermission.SUPPORT_ACCESS_START, action)
    if req.operator_user_id != operator.id:
        raise _deny(ctx, action, "not_request_owner", "Sesje może uruchomić tylko operator, który złożył prośbę.",
                    **base)
    _expire_stale_request(ctx, req)
    if req.status != RequestStatus.APPROVED:
        raise _deny(ctx, action, "no_consent", "Brak zgody klienta na dostęp serwisowy.", **base)

    consent = ctx.db.scalar(select(SupportConsent).where(SupportConsent.request_id == req.id))
    now = clock.now()
    if consent is None or consent.revoked_at is not None or now >= consent.valid_until:
        raise _deny(ctx, action, "consent_inactive", "Zgoda klienta została cofnięta lub wygasła.", **base)

    if not is_ticket_active(ctx.db, req.ticket_id):
        raise _deny(ctx, action, "ticket_closed", "Zgłoszenie supportowe jest zamknięte.", **base)

    active = ctx.db.scalar(
        select(SupportSession).where(SupportSession.consent_id == consent.id,
                                     SupportSession.status == SessionStatus.ACTIVE)
    )
    if active is not None and now < active.expires_at:
        raise _deny(ctx, action, "session_already_active", "Sesja w ramach tej zgody jest już aktywna.",
                    status=409, **base)

    member = _membership(ctx, req.organization_id, req.reference_user_id)
    permissions = effective_support_permissions(
        reference_user_role=member.role if member else None,
        consent_scopes=parse_scopes(consent.scopes),
        operator_platform_role=operator.platform_role,
    )
    if not permissions:
        raise _deny(ctx, action, "empty_permissions", "Zakres zgody nie daje żadnych uprawnień.", **base)

    policy_max = ctx.break_glass.max_session_minutes if req.mode == AccessMode.BREAK_GLASS \
        else ctx.policy.max_session_minutes
    minutes = min(duration_minutes or consent.max_session_minutes, consent.max_session_minutes, policy_max)
    if minutes < 1:
        raise _deny(ctx, action, "duration_invalid", "Nieprawidłowy czas sesji.", status=422, **base)
    expires_at = min(now + timedelta(minutes=minutes), consent.valid_until)

    # Zapisy dopiero po wszystkich sprawdzeniach (odmowy sa audytowane w osobnej transakcji).
    _verify_operator_mfa(ctx, operator, mfa_code, action, webauthn=webauthn,
                         require_hardware=req.mode == AccessMode.BREAK_GLASS and ctx.break_glass.requires_hardware_mfa,
                         organization_id=req.organization_id, support_request_id=req.id)
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
        title=(L("PROCEDURA AWARYJNA: rozpoczęto sesję Forvium Break Glass ({ticket})", ticket=req.ticket_number)
               if req.mode == AccessMode.BREAK_GLASS
               else L("Rozpoczęto sesję wsparcia Forvium ({ticket})", ticket=req.ticket_number)),
        body=L("Operator Forvium {operator} rozpoczął sesję wsparcia w trybie tylko do odczytu "
               "(zgłoszenie {ticket}). Sesja wygasa {until} UTC. "
               "Możesz ją zakończyć lub cofnąć zgodę w każdej chwili: Ustawienia -> Dostęp serwisowy.",
               operator=operator.id, ticket=req.ticket_number, until=expires_at.isoformat()),
        organization_id=req.organization_id, data={"session_id": session.id},
    )
    if req.mode == AccessMode.BREAK_GLASS:
        from forvium.support_access.break_glass_service import notify_security_team

        notify_security_team(ctx, L("Break Glass: start sesji ({ticket})", ticket=req.ticket_number),
                             L("Operator {operator} rozpoczął sesję awaryjną {session} w organizacji "
                               "{org} do {until} UTC.", operator=operator.id, session=session.id,
                               org=req.organization_id, until=expires_at.isoformat()))
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
        raise _deny(ctx, action, "launch_code_invalid", "Kod uruchomienia jest nieprawidłowy lub wygasł.",
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
        raise _deny(ctx, action, "invalid_support_token", "Sesja wsparcia jest nieprawidłowa lub zakończona.",
                    status=401, actor_type="anonymous")

    base = {"actor_user_id": session.operator_user_id, "actor_type": "support",
            "on_behalf_of_user_id": session.reference_user_id, "organization_id": session.organization_id,
            "support_session_id": session.id, "support_request_id": session.request_id}

    def fail(status: SessionStatus, reason: str) -> DomainError:
        _terminate_session(ctx, session, status, reason, None)
        ctx.db.commit()
        return _deny(ctx, action, reason, "Sesja wsparcia nie jest już aktywna.", status=401, **base)

    if session.status != SessionStatus.ACTIVE:
        raise _deny(ctx, action, "session_not_active", "Sesja wsparcia nie jest już aktywna.", status=401, **base)
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


def extend_session(ctx: Ctx, operator: User, *, session_id: str, minutes: int, reason: str,
                   mfa_code: str | None, webauthn: dict | None = None) -> SupportSession:
    """Przedluzenie trwajacej sesji zamiast otwierania nowej: ponowne MFA, uzasadnienie,
    limity liczby i lacznego czasu, nigdy poza waznosc zgody; klient dostaje powiadomienie."""
    action = "support.session.extend"
    session = ctx.db.get(SupportSession, session_id)
    if session is None or session.operator_user_id != operator.id:
        raise DomainError(404, "session_not_found", "Nie znaleziono sesji.")
    req = ctx.db.get(SupportAccessRequest, session.request_id)
    break_glass = req.mode == AccessMode.BREAK_GLASS
    base = {"actor_user_id": operator.id, "actor_type": "operator", "organization_id": session.organization_id,
            "on_behalf_of_user_id": session.reference_user_id, "support_session_id": session.id,
            "support_request_id": session.request_id}
    now = clock.now()
    _require_platform(ctx, operator, PlatformPermission.SUPPORT_ACCESS_START, action)
    if session.status != SessionStatus.ACTIVE or now >= session.expires_at:
        raise _deny(ctx, action, "session_not_active", "Sesja nie jest już aktywna.", status=409, **base)
    consent = ctx.db.get(SupportConsent, session.consent_id)
    if consent is None or consent.revoked_at is not None or now >= consent.valid_until:
        raise _deny(ctx, action, "consent_inactive", "Zgoda klienta została cofnięta lub wygasła.", **base)
    if session.extensions_count >= ctx.policy.max_extensions:
        raise _deny(ctx, action, "extension_limit", "Wykorzystano limit przedłużeń tej sesji.", status=409, **base)
    if not 1 <= minutes <= ctx.policy.max_extension_minutes:
        raise _deny(ctx, action, "duration_invalid",
                    L("Przedłużenie: 1-{n} min.", n=ctx.policy.max_extension_minutes), status=422, **base)
    if len((reason or "").strip()) < ctx.policy.min_reason_length:
        raise _deny(ctx, action, "reason_too_short", "Podaj powód przedłużenia.", status=422, **base)
    total_max = ctx.break_glass.max_total_session_minutes if break_glass else ctx.policy.max_total_session_minutes
    new_expires = min(session.expires_at + timedelta(minutes=minutes),
                      session.started_at + timedelta(minutes=total_max), consent.valid_until)
    if new_expires <= session.expires_at:
        raise _deny(ctx, action, "extension_window_exhausted",
                    "Nie można przedłużyć: osiągnięto limit czasu sesji lub ważności zgody.", status=409, **base)
    _verify_operator_mfa(ctx, operator, mfa_code, action, webauthn=webauthn,
                         require_hardware=break_glass and ctx.break_glass.requires_hardware_mfa,
                         organization_id=session.organization_id, support_request_id=session.request_id)

    previous = session.expires_at
    session.original_expires_at = session.original_expires_at or previous
    session.expires_at = new_expires
    session.extensions_count += 1
    added = int((new_expires - previous).total_seconds() // 60)
    ctx.audit.log(ctx.db, "support.session.extended", ip_address=ctx.ip,
                  details={"previous_expires_at": previous.isoformat(), "expires_at": new_expires.isoformat(),
                           "extension": session.extensions_count, "reason": reason.strip()}, **base)
    ctx.notifications.notify(
        ctx.db, _org_approvers(ctx, session.organization_id, exclude_user_id=operator.id),
        event="support_access.session_extended",
        title=L("Przedłużono sesję wsparcia Forvium ({ticket})", ticket=session.ticket_number),
        body=L("Operator {operator} przedłużył sesję tylko do odczytu o {minutes} min (do "
               "{until} UTC). Powód: {reason}. Możesz ją zakończyć w każdej chwili: "
               "Ustawienia -> Dostęp serwisowy.", operator=operator.id, minutes=added,
               until=new_expires.isoformat(), reason=reason.strip()),
        organization_id=session.organization_id, data={"session_id": session.id},
    )
    if break_glass:
        from forvium.support_access.break_glass_service import notify_security_team

        notify_security_team(ctx, L("Break Glass: przedłużenie sesji ({ticket})", ticket=session.ticket_number),
                             L("Sesja {session} przedłużona do {until} UTC. Powód: {reason}", session=session.id,
                               until=new_expires.isoformat(), reason=reason.strip()))
    return session


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
            [RequestStatus.PENDING, RequestStatus.PENDING_SECOND_APPROVAL,
             RequestStatus.PENDING_CUSTOMER_CONFIRMATION]),
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
