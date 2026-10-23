"""Support Access - API administracyjne (admin.forvium.com)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from forvium.access import OperatorPrincipal, require_platform_permission
from forvium.core.context import Ctx, DomainError, get_ctx
from forvium.platform_admin.rbac import PlatformPermission as PP
from forvium.support_access import service
from forvium.support_access.break_glass import BREAK_GLASS_POLICY
from forvium.support_access.models import SessionStatus, SupportAccessRequest, SupportConsent, SupportSession
from forvium.support_access.schemas import CreateRequestIn, StartSessionIn, consent_out, request_out, session_out
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
        "break_glass_enabled": BREAK_GLASS_POLICY.enabled,
    }


@router.post("/requests")
def create(body: CreateRequestIn, op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_ACCESS_REQUEST)),
           ctx: Ctx = Depends(get_ctx)):
    req = service.create_request(
        ctx, op.user, organization_id=body.organization_id, reference_user_id=body.reference_user_id,
        reason=body.reason, ticket_number=body.ticket_number, duration_minutes=body.duration_minutes,
        scopes=body.scopes, mfa_code=body.mfa_code, mode=body.mode,
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
                                          duration_minutes=body.duration_minutes)
    app_origin = request.app.state.settings.app_origin
    # Kod jest przekazywany we fragmencie URL (#), wiec nie trafia do logow serwera.
    return {"session": session_out(session), "launch_url": f"{app_origin}/support-launch.html#code={code}"}


@router.post("/sessions/{session_id}/end")
def end(session_id: str, op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_ACCESS_START)),
        ctx: Ctx = Depends(get_ctx)):
    session = ctx.db.get(SupportSession, session_id)
    if session is None or session.operator_user_id != op.user.id:
        raise DomainError(404, "session_not_found", "Nie znaleziono sesji.")
    service.end_session(ctx, session, op.user.id, "ended_by_operator")
    return {"session": session_out(session)}
