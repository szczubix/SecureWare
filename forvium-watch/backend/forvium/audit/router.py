"""Audit Log - przeglad i eksport dla przelozonych supportu i bezpieczenstwa (admin.forvium.com)."""

from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from forvium.access import OperatorPrincipal, require_platform_permission
from forvium.audit.models import AuditEvent
from forvium.audit.service import AuditFilter
from forvium.core.context import Ctx, get_ctx
from forvium.platform_admin.rbac import PlatformPermission as PP

router = APIRouter(prefix="/api/admin/audit", tags=["audit (admin)"])

CSV_COLUMNS = ["occurred_at", "action", "outcome", "actor_type", "actor_user_id", "on_behalf_of_user_id",
               "organization_id", "support_request_id", "support_session_id", "is_break_glass", "http_method",
               "route", "status_code", "ip_address"]


def audit_filter(
    organization_id: str | None = None,
    operator_id: str | None = None,
    ticket: str | None = None,
    support_session_id: str | None = None,
    support_request_id: str | None = None,
    action_prefix: str | None = None,
    outcome: str | None = None,
    break_glass: bool | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> AuditFilter:
    strip = lambda d: d.replace(tzinfo=None) if d and d.tzinfo else d  # noqa: E731 - czas w UTC (naive)
    return AuditFilter(organization_id=organization_id, actor_user_id=operator_id, ticket_number=ticket,
                       support_session_id=support_session_id, support_request_id=support_request_id,
                       action_prefix=action_prefix, outcome=outcome, break_glass=break_glass,
                       since=strip(since), until=strip(until))


def event_out(e: AuditEvent) -> dict:
    return {
        "id": e.id, "occurred_at": e.occurred_at.isoformat() + "Z", "action": e.action, "outcome": e.outcome,
        "actor_user_id": e.actor_user_id, "actor_type": e.actor_type, "on_behalf_of_user_id": e.on_behalf_of_user_id,
        "organization_id": e.organization_id, "support_session_id": e.support_session_id,
        "support_request_id": e.support_request_id, "is_break_glass": e.is_break_glass, "method": e.http_method,
        "route": e.route, "status_code": e.status_code, "details": e.details,
    }


@router.get("")
def list_events(f: AuditFilter = Depends(audit_filter), limit: int = Query(100, ge=1, le=500),
                offset: int = Query(0, ge=0),
                op: OperatorPrincipal = Depends(require_platform_permission(PP.AUDIT_READ)),
                ctx: Ctx = Depends(get_ctx)):
    events, total = ctx.audit.query(ctx.db, f, limit=limit, offset=offset)
    return {"total": total, "limit": limit, "offset": offset, "events": [event_out(e) for e in events]}


@router.get("/export.csv")
def export_csv(f: AuditFilter = Depends(audit_filter),
               op: OperatorPrincipal = Depends(require_platform_permission(PP.AUDIT_READ)),
               ctx: Ctx = Depends(get_ctx)):
    """Eksport do przegladow (do 50 000 zdarzen). Sam eksport tez trafia do audytu."""
    events, total = ctx.audit.query(ctx.db, f, limit=50_000)
    ctx.audit.log(ctx.db, "audit.exported", actor_user_id=op.user.id, actor_type="operator", ip_address=ctx.ip,
                  details={"rows": len(events), "total": total,
                           "filters": {k: str(v) for k, v in vars(f).items() if v is not None}})
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_COLUMNS + ["details"])
    for e in events:
        row = event_out(e)
        writer.writerow([e.occurred_at.isoformat() + "Z", e.action, e.outcome, e.actor_type, e.actor_user_id,
                         e.on_behalf_of_user_id, e.organization_id, e.support_request_id, e.support_session_id,
                         e.is_break_glass, e.http_method, e.route, e.status_code, e.ip_address,
                         row["details"]])
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": 'attachment; filename="forvium-audit.csv"'})
