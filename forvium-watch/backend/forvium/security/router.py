"""Alerty bezpieczenstwa (admin.forvium.com)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select

from forvium.access import OperatorPrincipal, require_platform_permission
from forvium.core.context import Ctx, get_ctx
from forvium.platform_admin.rbac import PlatformPermission as PP
from forvium.security.anomalies import SecurityAlert, alert_out, handle_alert

router = APIRouter(prefix="/api/admin/security", tags=["security alerts (admin)"])


class AlertActionIn(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


@router.get("/alerts")
def list_alerts(status: str | None = "open", severity: str | None = None,
                op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_OVERSIGHT)),
                ctx: Ctx = Depends(get_ctx)):
    stmt = select(SecurityAlert).order_by(SecurityAlert.created_at.desc()).limit(200)
    if status:
        stmt = stmt.where(SecurityAlert.status == status)
    if severity:
        stmt = stmt.where(SecurityAlert.severity == severity)
    return {"alerts": [alert_out(a) for a in ctx.db.scalars(stmt)]}


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge(alert_id: str, body: AlertActionIn,
                op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_OVERSIGHT)),
                ctx: Ctx = Depends(get_ctx)):
    return {"alert": alert_out(handle_alert(ctx, op.user, alert_id, "acknowledged", body.notes))}


@router.post("/alerts/{alert_id}/resolve")
def resolve(alert_id: str, body: AlertActionIn,
            op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_OVERSIGHT)),
            ctx: Ctx = Depends(get_ctx)):
    return {"alert": alert_out(handle_alert(ctx, op.user, alert_id, "resolved", body.notes))}


@router.get("/jobs")
def background_job_status(op: OperatorPrincipal = Depends(require_platform_permission(PP.SUPPORT_OVERSIGHT)),
                          ctx: Ctx = Depends(get_ctx)):
    """Stan zadan w tle - zatrzymany worker oznacza m.in. brak wygaszania sesji i wykrywania anomalii."""
    from forvium.core.clock import clock
    from forvium.jobs import JobRun, stale_jobs

    stale = set(stale_jobs(ctx.db, clock.now()))
    iso = lambda d: d.isoformat() + "Z" if d else None  # noqa: E731
    return {"stale": sorted(stale), "jobs": [
        {"job": r.job, "interval_seconds": r.interval_seconds, "last_success_at": iso(r.last_success_at),
         "last_error": r.last_error, "last_error_at": iso(r.last_error_at), "runs": r.runs,
         "failures": r.failures, "stale": r.job in stale}
        for r in ctx.db.scalars(select(JobRun).order_by(JobRun.job))]}
