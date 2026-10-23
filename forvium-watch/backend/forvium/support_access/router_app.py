"""Support Access - API klienta (app.forvium.com)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select

from forvium.access import AppPrincipal, OrgAccess, get_app_principal, require_org_permission
from forvium.audit.models import AuditEvent
from forvium.core.context import Ctx, DomainError, get_ctx
from forvium.organizations.rbac import Permission as P
from forvium.support_access import service
from forvium.support_access.models import SupportAccessRequest, SupportConsent, SupportSession
from forvium.support_access.schemas import (
    ApproveIn,
    LaunchIn,
    RejectIn,
    consent_out,
    request_out,
    session_out,
)

router = APIRouter(prefix="/api/app", tags=["support access (app)"])


# ------------------------------------------------- sesja wsparcia (strona operatora)


@router.post("/support/launch")
def launch(body: LaunchIn, ctx: Ctx = Depends(get_ctx)):
    """Wymiana jednorazowego kodu z panelu admin na token sesji wsparcia."""
    session, token = service.exchange_launch_code(ctx, body.code)
    return {"token": token, "session": session_out(session)}


def _support_only(principal: AppPrincipal = Depends(get_app_principal)) -> AppPrincipal:
    if not principal.is_support:
        raise DomainError(404, "not_support_session", "Brak aktywnej sesji wsparcia.")
    return principal


@router.get("/support/session")
def current_support_session(principal: AppPrincipal = Depends(_support_only)):
    """Dane do stalego banera trybu wsparcia."""
    s = principal.support
    return {
        "banner": "TRYB WSPARCIA FORVIUM — TYLKO ODCZYT",
        "session_id": s.session.id,
        "organization": {"id": s.organization.id, "name": s.organization.name},
        "operator_id": s.operator.id,
        "reference_user": {"id": s.reference_user.id, "display_name": s.reference_user.display_name},
        "ticket_number": s.session.ticket_number,
        "access_level": s.session.access_level,
        "expires_at": s.session.expires_at.isoformat() + "Z",
        "remaining_seconds": service.remaining_seconds(s.session),
        "permissions": sorted(s.permissions),
    }


@router.post("/support/session/end")
def end_current_support_session(principal: AppPrincipal = Depends(_support_only), ctx: Ctx = Depends(get_ctx)):
    service.end_session(ctx, principal.support.session, principal.actor.id, "ended_by_operator")
    return {"ok": True}


# ------------------------------------------------- zgody i historia (strona klienta)


@router.get("/orgs/{org_id}/support-access")
def history(access: OrgAccess = Depends(require_org_permission(P.SUPPORT_ACCESS_VIEW)), ctx: Ctx = Depends(get_ctx)):
    """Pelna historia dostepu serwisowego - bez mozliwosci ukrycia czy usuniecia wpisow."""
    service.sweep_expired(ctx)
    org_id = access.organization.id
    requests = list(ctx.db.scalars(select(SupportAccessRequest).where(SupportAccessRequest.organization_id == org_id)
                                   .order_by(SupportAccessRequest.created_at.desc())))
    consents = {c.request_id: c for c in ctx.db.scalars(select(SupportConsent)
                                                        .where(SupportConsent.organization_id == org_id))}
    sessions = list(ctx.db.scalars(select(SupportSession).where(SupportSession.organization_id == org_id)
                                   .order_by(SupportSession.started_at.desc())))
    return {
        "requests": [{**request_out(r), "consent": consent_out(consents.get(r.id))} for r in requests],
        "sessions": [session_out(s) for s in sessions],
    }


@router.get("/orgs/{org_id}/support-access/sessions/{session_id}/activity")
def session_activity(session_id: str, access: OrgAccess = Depends(require_org_permission(P.SUPPORT_ACCESS_VIEW)),
                     ctx: Ctx = Depends(get_ctx)):
    events = ctx.db.scalars(select(AuditEvent).where(AuditEvent.support_session_id == session_id,
                                                     AuditEvent.organization_id == access.organization.id)
                            .order_by(AuditEvent.occurred_at))
    return {"events": [{"occurred_at": e.occurred_at.isoformat() + "Z", "action": e.action, "outcome": e.outcome,
                        "method": e.http_method, "route": e.route, "status_code": e.status_code,
                        "operator_id": e.actor_user_id if e.actor_type in ("support", "operator") else None}
                       for e in events]}


@router.post("/orgs/{org_id}/support-access/requests/{request_id}/approve")
def approve(request_id: str, body: ApproveIn,
            access: OrgAccess = Depends(require_org_permission(P.SUPPORT_ACCESS_APPROVE)),
            ctx: Ctx = Depends(get_ctx)):
    consent = service.approve_request(ctx, access.principal.actor, organization_id=access.organization.id,
                                      request_id=request_id, scopes=body.scopes, unit_ids=body.unit_ids,
                                      valid_hours=body.valid_hours, note=body.note)
    return {"consent": consent_out(consent)}


@router.post("/orgs/{org_id}/support-access/requests/{request_id}/reject")
def reject(request_id: str, body: RejectIn,
           access: OrgAccess = Depends(require_org_permission(P.SUPPORT_ACCESS_APPROVE)),
           ctx: Ctx = Depends(get_ctx)):
    service.reject_request(ctx, access.principal.actor, organization_id=access.organization.id,
                           request_id=request_id, note=body.note)
    return {"ok": True}


@router.post("/orgs/{org_id}/support-access/consents/{consent_id}/revoke")
def revoke(consent_id: str, access: OrgAccess = Depends(require_org_permission(P.SUPPORT_ACCESS_APPROVE)),
           ctx: Ctx = Depends(get_ctx)):
    consent = service.revoke_consent(ctx, access.principal.actor, organization_id=access.organization.id,
                                     consent_id=consent_id)
    return {"consent": consent_out(consent)}


@router.post("/orgs/{org_id}/support-access/sessions/{session_id}/terminate")
def terminate(session_id: str, access: OrgAccess = Depends(require_org_permission(P.SUPPORT_ACCESS_APPROVE)),
              ctx: Ctx = Depends(get_ctx)):
    session = ctx.db.get(SupportSession, session_id)
    if session is None or session.organization_id != access.organization.id:
        raise DomainError(404, "session_not_found", "Nie znaleziono sesji.")
    service.end_session(ctx, session, access.principal.actor.id, "terminated_by_customer")
    return {"session": session_out(session)}
