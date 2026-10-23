"""Support Access - API administracyjne (admin.forvium.com)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from forvium.access import OperatorPrincipal, require_platform_permission
from forvium.core.context import Ctx, DomainError, get_ctx
from forvium.platform_admin.rbac import PlatformPermission as PP
from forvium.support_access import service
from forvium.support_access import break_glass_service as bg
from forvium.support_access import recording
from forvium.support_access.break_glass import IncidentCategory
from forvium.support_access.models import SessionStatus, SupportAccessRequest, SupportConsent, SupportSession
from forvium.support_access.schemas import (
    BreakGlassDecisionIn,
    BreakGlassReviewIn,
    CreateRequestIn,
    ExtendSessionIn,
    StartSessionIn,
    consent_out,
    request_out,
    session_out,
)
from forvium.support_access.scopes import SupportScope, operator_scope_cap

router = APIRouter(prefix="/api/admin/support-access", tags=["support access (admin)"])


@router.get("/policy")
def policy(request: Request, op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_ACCESS_REQUEST))):
    p = request.app.state.support_policy
    return {
        "default_session_minutes": p.default_session_minutes,
        "max_session_minutes": p.max_session_minutes,
        "access_levels": ["READ_ONLY"],
        "scopes": [s.value for s in SupportScope],
        "operator_allowed_scopes": sorted(s.value for s in operator_scope_cap(op.user.platform_role)),
        "break_glass_enabled": request.app.state.break_glass_policy.enabled,
        "break_glass_requires_webauthn": request.app.state.break_glass_policy.requires_hardware_mfa,
        "break_glass_max_session_minutes": request.app.state.break_glass_policy.max_session_minutes,
        "break_glass_min_justification": request.app.state.break_glass_policy.min_justification_length,
        "incident_categories": [c.value for c in IncidentCategory],
    }


@router.post("/requests")
def create(body: CreateRequestIn, op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_ACCESS_REQUEST)),
           ctx: Ctx = Depends(get_ctx)):
    req = service.create_request(
        ctx, op.user, organization_id=body.organization_id, reference_user_id=body.reference_user_id,
        reason=body.reason, ticket_number=body.ticket_number, duration_minutes=body.duration_minutes,
        scopes=body.scopes, mfa_code=body.mfa_code, mode=body.mode, incident_category=body.incident_category,
        webauthn=body.webauthn,
    )
    return {"request": request_out(req)}


@router.get("/requests")
def my_requests(op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_ACCESS_REQUEST)),
                ctx: Ctx = Depends(get_ctx)):
    service.sweep_expired(ctx)
    reqs = list(ctx.db.scalars(select(SupportAccessRequest).where(SupportAccessRequest.operator_user_id == op.user.id)
                               .order_by(SupportAccessRequest.created_at.desc())))
    consents = {c.request_id: c for c in ctx.db.scalars(
        select(SupportConsent).where(SupportConsent.request_id.in_([r.id for r in reqs])))}
    active = {s.request_id: s for s in ctx.db.scalars(
        select(SupportSession).where(SupportSession.operator_user_id == op.user.id,
                                     SupportSession.status == SessionStatus.ACTIVE))}
    return {"requests": [{**request_out(r), "consent": consent_out(consents.get(r.id)),
                          "active_session": session_out(active[r.id]) if r.id in active else None} for r in reqs]}


@router.post("/requests/{request_id}/cancel")
def cancel(request_id: str, op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_ACCESS_REQUEST)),
           ctx: Ctx = Depends(get_ctx)):
    service.cancel_request(ctx, op.user, request_id)
    return {"ok": True}


@router.post("/requests/{request_id}/sessions")
def start(request_id: str, body: StartSessionIn, request: Request,
          op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_ACCESS_START)),
          ctx: Ctx = Depends(get_ctx)):
    session, code = service.start_session(ctx, op.user, request_id=request_id, mfa_code=body.mfa_code,
                                          duration_minutes=body.duration_minutes, webauthn=body.webauthn)
    app_origin = request.app.state.settings.app_origin
    # Kod jest przekazywany we fragmencie URL (#), wiec nie trafia do logow serwera.
    return {"session": session_out(session), "launch_url": f"{app_origin}/support-launch.html#code={code}"}


@router.post("/sessions/{session_id}/extend")
def extend(session_id: str, body: ExtendSessionIn,
           op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_ACCESS_START)),
           ctx: Ctx = Depends(get_ctx)):
    session = service.extend_session(ctx, op.user, session_id=session_id, minutes=body.minutes, reason=body.reason,
                                     mfa_code=body.mfa_code, webauthn=body.webauthn)
    return {"session": session_out(session)}


@router.post("/sessions/{session_id}/end")
def end(session_id: str, op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_ACCESS_START)),
        ctx: Ctx = Depends(get_ctx)):
    session = ctx.db.get(SupportSession, session_id)
    if session is None or session.operator_user_id != op.user.id:
        raise DomainError(404, "session_not_found", "Nie znaleziono sesji.")
    service.end_session(ctx, session, op.user.id, "ended_by_operator")
    return {"session": session_out(session)}


# ------------------------------------------------------------------ Break Glass

bg_router = APIRouter(prefix="/api/admin/break-glass", tags=["break glass (admin)"])


def _bg_out(ctx: Ctx, r: SupportAccessRequest) -> dict:
    sessions = ctx.db.scalars(select(SupportSession).where(SupportSession.request_id == r.id)
                              .order_by(SupportSession.started_at))
    return {**request_out(r), "review_notes": r.review_notes, "reviewed_by_user_id": r.reviewed_by_user_id,
            "sessions": [session_out(s) for s in sessions]}


@bg_router.get("/requests")
def bg_requests(status: str | None = None, review_pending: bool = False,
                op: OperatorPrincipal = Depends(require_platform_permission(PP.BREAK_GLASS_APPROVE)),
                ctx: Ctx = Depends(get_ctx)):
    return {"requests": [_bg_out(ctx, r) for r in bg.list_break_glass(ctx, status=status,
                                                                      review_pending=review_pending)]}


@bg_router.post("/requests/{request_id}/approve")
def bg_approve(request_id: str, body: BreakGlassDecisionIn,
               op: OperatorPrincipal = Depends(require_platform_permission(PP.BREAK_GLASS_APPROVE)),
               ctx: Ctx = Depends(get_ctx)):
    consent = bg.approve_break_glass(ctx, op.user, request_id=request_id, mfa_code=body.mfa_code, note=body.note,
                                     webauthn=body.webauthn)
    return {"consent": consent_out(consent)}


@bg_router.post("/requests/{request_id}/reject")
def bg_reject(request_id: str, body: BreakGlassDecisionIn,
              op: OperatorPrincipal = Depends(require_platform_permission(PP.BREAK_GLASS_APPROVE)),
              ctx: Ctx = Depends(get_ctx)):
    bg.reject_break_glass(ctx, op.user, request_id=request_id, note=body.note)
    return {"ok": True}


@bg_router.post("/requests/{request_id}/review")
def bg_review(request_id: str, body: BreakGlassReviewIn,
              op: OperatorPrincipal = Depends(require_platform_permission(PP.BREAK_GLASS_REVIEW)),
              ctx: Ctx = Depends(get_ctx)):
    req = bg.review_break_glass(ctx, op.user, request_id=request_id, notes=body.notes)
    return {"request": _bg_out(ctx, req)}


# ------------------------------------------------------------------ nadzor

@router.get("/oversight/sessions")
def oversight_sessions(status: str | None = None, operator_id: str | None = None, organization_id: str | None = None,
                       op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_OVERSIGHT)),
                       ctx: Ctx = Depends(get_ctx)):
    """Wszystkie sesje wsparcia (wszyscy operatorzy) - dla kierownika supportu i bezpieczenstwa."""
    from forvium.identity.models import User
    from forvium.organizations.models import Organization

    service.sweep_expired(ctx)
    stmt = select(SupportSession, SupportAccessRequest, User, Organization) \
        .join(SupportAccessRequest, SupportAccessRequest.id == SupportSession.request_id) \
        .join(User, User.id == SupportSession.operator_user_id) \
        .join(Organization, Organization.id == SupportSession.organization_id)
    if status:
        stmt = stmt.where(SupportSession.status == status)
    if operator_id:
        stmt = stmt.where(SupportSession.operator_user_id == operator_id)
    if organization_id:
        stmt = stmt.where(SupportSession.organization_id == organization_id)
    rows = ctx.db.execute(stmt.order_by(SupportSession.started_at.desc()).limit(200)).all()
    return {"sessions": [{**session_out(s), "mode": r.mode, "reason": r.reason, "operator_email": u.email,
                          "organization_name": o.name} for s, r, u, o in rows]}


@router.post("/oversight/sessions/{session_id}/terminate")
def oversight_terminate(session_id: str,
                        op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_OVERSIGHT)),
                        ctx: Ctx = Depends(get_ctx)):
    session = ctx.db.get(SupportSession, session_id)
    if session is None:
        raise DomainError(404, "session_not_found", "Nie znaleziono sesji.")
    service.end_session(ctx, session, op.user.id, "terminated_by_supervisor", actor_type="operator")
    return {"session": session_out(session)}



# ------------------------------------------------------------- nagrania sesji

@router.get("/sessions/{session_id}/recording")
def admin_recording_list(session_id: str, op: OperatorPrincipal = Depends(require_platform_permission(PP.AUDIT_READ)),
                         ctx: Ctx = Depends(get_ctx)):
    return {"frames": recording.recording_index(ctx, None, session_id)}


@router.get("/sessions/{session_id}/recording/{seq}")
def admin_recording_get(session_id: str, seq: int,
                        op: OperatorPrincipal = Depends(require_platform_permission(PP.AUDIT_READ)),
                        ctx: Ctx = Depends(get_ctx)):
    """Nagranie zawiera dane klienta - kazde otwarcie klatki przez Forvium trafia do audytu."""
    frame = recording.recording_frame(ctx, None, session_id, seq)
    session = ctx.db.get(SupportSession, session_id)
    ctx.audit.log(ctx.db, "support.recording.viewed", actor_user_id=op.user.id, actor_type="operator",
                  organization_id=session.organization_id, support_session_id=session_id, ip_address=ctx.ip,
                  details={"seq": seq})
    return frame
