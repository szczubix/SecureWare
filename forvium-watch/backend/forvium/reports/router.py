"""Raporty dostepu: lista, pobieranie PDF i tworzenie na zadanie (klient i Forvium)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import select

from forvium.access import OperatorPrincipal, OrgAccess, require_org_permission, require_platform_permission
from forvium.core.context import Ctx, DomainError, get_ctx
from forvium.organizations.rbac import Permission as P
from forvium.platform_admin.rbac import PlatformPermission as PP
from forvium.reports import service
from forvium.reports.service import KIND_CUSTOMER, AccessReport

app_router = APIRouter(prefix="/api/app", tags=["access reports (app)"])
admin_router = APIRouter(prefix="/api/admin/access-reports", tags=["access reports (admin)"])


class PeriodIn(BaseModel):
    year: int = Field(ge=2020, le=2100)
    month: int = Field(ge=1, le=12)


class AdminGenerateIn(PeriodIn):
    kind: str = Field(pattern="^(customer|auditor)$")
    organization_id: str | None = None


def _pdf_response(report: AccessReport) -> Response:
    name = f"forvium-raport-dostepu-{report.kind}-{report.period_start:%Y-%m}.pdf"
    return Response(service.pdf_bytes(report), media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store",
        "X-Content-SHA256": report.sha256})


# ------------------------------------------------------------------------- klient
# Uprawnienia klienta do Support Access; sesja wsparcia nigdy ich nie ma
# (SUPPORT_FORBIDDEN_PERMISSIONS), wiec operator nie pobierze raportu o sobie.


@app_router.get("/orgs/{org_id}/access-reports")
def list_org_reports(access: OrgAccess = Depends(require_org_permission(P.SUPPORT_ACCESS_VIEW)),
                     ctx: Ctx = Depends(get_ctx)):
    rows = ctx.db.scalars(select(AccessReport).where(AccessReport.kind == KIND_CUSTOMER,
                                                     AccessReport.organization_id == access.organization.id)
                          .order_by(AccessReport.period_start.desc()))
    return {"reports": [service.report_out(r) for r in rows]}


@app_router.get("/orgs/{org_id}/access-reports/{report_id}/pdf")
def download_org_report(report_id: str, access: OrgAccess = Depends(require_org_permission(P.SUPPORT_ACCESS_VIEW)),
                        ctx: Ctx = Depends(get_ctx)):
    report = ctx.db.get(AccessReport, report_id)
    if report is None or report.kind != KIND_CUSTOMER or report.organization_id != access.organization.id:
        raise DomainError(404, "report_not_found", "Nie znaleziono raportu.")
    ctx.audit.log(ctx.db, "reports.downloaded", actor_user_id=access.principal.actor.id, actor_type="user",
                  organization_id=report.organization_id, ip_address=ctx.ip,
                  details={"report_id": report.id, "kind": report.kind})
    return _pdf_response(report)


@app_router.post("/orgs/{org_id}/access-reports")
def generate_org_report(body: PeriodIn,
                        access: OrgAccess = Depends(require_org_permission(P.SUPPORT_ACCESS_VIEW)),
                        ctx: Ctx = Depends(get_ctx)):
    start, end = service.month_bounds(body.year, body.month)
    report = service.generate(ctx, KIND_CUSTOMER, access.organization.id, start, end,
                              created_by=access.principal.actor.id)
    return {"report": service.report_out(report)}


# -------------------------------------------------------------------------- Forvium


@admin_router.get("")
def list_reports(kind: str | None = None, organization_id: str | None = None,
                 op: OperatorPrincipal = Depends(require_platform_permission(PP.AUDIT_READ)),
                 ctx: Ctx = Depends(get_ctx)):
    stmt = select(AccessReport).order_by(AccessReport.period_start.desc(), AccessReport.kind).limit(500)
    if kind:
        stmt = stmt.where(AccessReport.kind == kind)
    if organization_id:
        stmt = stmt.where(AccessReport.organization_id == organization_id)
    from forvium.organizations.models import Organization

    names = dict(ctx.db.execute(select(Organization.id, Organization.name)).all())
    return {"reports": [{**service.report_out(r), "organization_name": names.get(r.organization_id)}
                        for r in ctx.db.scalars(stmt)]}


@admin_router.get("/{report_id}/pdf")
def download_report(report_id: str, op: OperatorPrincipal = Depends(require_platform_permission(PP.AUDIT_READ)),
                    ctx: Ctx = Depends(get_ctx)):
    report = ctx.db.get(AccessReport, report_id)
    if report is None:
        raise DomainError(404, "report_not_found", "Nie znaleziono raportu.")
    ctx.audit.log(ctx.db, "reports.downloaded", actor_user_id=op.user.id, actor_type="operator",
                  organization_id=report.organization_id, ip_address=ctx.ip,
                  details={"report_id": report.id, "kind": report.kind})
    return _pdf_response(report)


@admin_router.post("")
def generate_report(body: AdminGenerateIn, op: OperatorPrincipal = Depends(require_platform_permission(PP.AUDIT_READ)),
                    ctx: Ctx = Depends(get_ctx)):
    if (body.kind == KIND_CUSTOMER) != bool(body.organization_id):
        raise DomainError(422, "invalid_scope", "Raport klienta wymaga organizacji, raport audytora - bez niej.")
    start, end = service.month_bounds(body.year, body.month)
    report = service.generate(ctx, body.kind, body.organization_id if body.kind == KIND_CUSTOMER else None,
                              start, end, created_by=op.user.id)
    return {"report": service.report_out(report)}


