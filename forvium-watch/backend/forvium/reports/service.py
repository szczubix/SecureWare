"""Okresowe raporty dostepu serwisowego (PDF).

* Raport klienta (`customer`): co miesiac dla kazdej organizacji - wszystkie prosby
  Forvium o dostep, decyzje, sesje (czas, zakres, ogladane widoki, zablokowane proby,
  powod zakonczenia), zgody stale, Break Glass, otwarcia nagran przez Forvium. Rowniez
  wtedy, gdy dostepu nie bylo - to tez jest informacja dla klienta.
* Raport audytora (`auditor`): ten sam okres dla calej platformy - podsumowanie per
  organizacja i per operator, Break Glass i stan przegladow, alerty bezpieczenstwa.

Raport zawiera odcisk zdarzen audytu z okresu (SHA-256 po identyfikatorach, czasach
i akcjach), ktory audytor moze porownac z eksportem audytu, a skrot samego pliku PDF
jest zapisany w bazie i podawany w powiadomieniu. PDF przechowywany jest zaszyfrowany.
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column

from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError
from forvium.core.crypto import EncryptedString
from forvium.core.db import Base, new_id
from forvium.core.i18n import L, current_lang, default_lang, join, normalize

KIND_CUSTOMER = "customer"
KIND_AUDITOR = "auditor"
MONTHS = {
    "pl": ["styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec", "lipiec", "sierpień", "wrzesień",
           "październik", "listopad", "grudzień"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
           "October", "November", "December"],
}


class AccessReport(Base):
    __tablename__ = "access_reports"
    __table_args__ = (UniqueConstraint("kind", "organization_id", "period_start"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    kind: Mapped[str] = mapped_column(String(16), index=True)
    # NULL dla raportu audytora (cala platforma).
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    created_by: Mapped[str] = mapped_column(String(36))  # "system" albo id uzytkownika
    sha256: Mapped[str] = mapped_column(String(64))
    audit_digest: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(Integer)
    pdf: Mapped[str] = mapped_column(EncryptedString("access_reports.pdf"))  # base64


def month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1)
    end = datetime(year + (month == 12), month % 12 + 1, 1)
    return start, end


def previous_month(now: datetime) -> tuple[datetime, datetime]:
    year, month = (now.year - 1, 12) if now.month == 1 else (now.year, now.month - 1)
    return month_bounds(year, month)


def period_label(start: datetime, lang: str | None = None) -> str:
    names = MONTHS.get(lang or current_lang(), MONTHS["pl"])
    return f"{names[start.month - 1]} {start.year}"


# ------------------------------------------------------------------- dane raportu


@dataclass
class ReportData:
    kind: str
    period_start: datetime
    period_end: datetime
    organization_name: str | None
    lang: str = "pl"
    requests: list[dict] = field(default_factory=list)
    sessions: list[dict] = field(default_factory=list)
    standing: list[dict] = field(default_factory=list)
    recordings_viewed: list[dict] = field(default_factory=list)
    denied_attempts: int = 0
    alerts: list[dict] = field(default_factory=list)
    audit_events: int = 0
    audit_digest: str = ""


def _fmt(d: datetime | None) -> str:
    return d.strftime("%Y-%m-%d %H:%M") if d else "—"


def collect(ctx: Ctx, kind: str, organization_id: str | None, start: datetime, end: datetime) -> ReportData:
    from forvium.audit.models import AuditEvent
    from forvium.identity.models import User
    from forvium.organizations.models import Organization
    from forvium.security.anomalies import SecurityAlert
    from forvium.support_access.models import AccessMode, SupportAccessRequest, SupportSession
    from forvium.support_access.summary import session_summary

    db = ctx.db
    emails = dict(db.execute(select(User.id, User.email)).all())
    orgs = dict(db.execute(select(Organization.id, Organization.name)).all())
    who = lambda uid: emails.get(uid, uid or "—")  # noqa: E731

    def scoped(stmt, column):
        return stmt.where(column == organization_id) if organization_id else stmt

    org = db.get(Organization, organization_id) if organization_id else None
    data = ReportData(kind=kind, period_start=start, period_end=end,
                      organization_name=org.name if org else None,
                      lang=normalize(org.locale if org else None) or default_lang())
    for r in db.scalars(scoped(select(SupportAccessRequest).where(SupportAccessRequest.created_at >= start,
                                                                 SupportAccessRequest.created_at < end),
                               SupportAccessRequest.organization_id).order_by(SupportAccessRequest.created_at)):
        data.requests.append({
            "created_at": _fmt(r.created_at), "ticket": r.ticket_number, "organization": orgs.get(r.organization_id),
            "operator": who(r.operator_user_id), "break_glass": r.mode == AccessMode.BREAK_GLASS,
            "reason": r.reason, "scopes": ", ".join(r.requested_scopes or []), "status": r.status,
            "decided_by": who(r.decided_by_user_id) if r.decided_by_user_id else "—",
            "reviewed": bool(r.review_completed_at),
        })
    for s in db.scalars(scoped(select(SupportSession).where(SupportSession.started_at >= start,
                                                           SupportSession.started_at < end),
                               SupportSession.organization_id).order_by(SupportSession.started_at)):
        summary = session_summary(db, s)
        data.sessions.append({
            "started_at": _fmt(s.started_at), "ticket": s.ticket_number, "organization": orgs.get(s.organization_id),
            "operator": who(s.operator_user_id), "minutes": round(summary["duration_seconds"] / 60, 1),
            "extensions": s.extensions_count or 0, "views": summary["views"],
            "api_calls": summary["api_calls"], "denied": summary["denied_calls"], "end_reason": s.end_reason,
        })
    events = list(db.scalars(scoped(select(AuditEvent).where(AuditEvent.occurred_at >= start,
                                                             AuditEvent.occurred_at < end),
                                    AuditEvent.organization_id).order_by(AuditEvent.occurred_at, AuditEvent.id)))
    digest = hashlib.sha256()
    for e in events:
        digest.update(f"{e.id}|{e.occurred_at.isoformat()}|{e.action}|{e.outcome}\n".encode())
        if e.action.startswith("support.standing_consent.") and e.outcome == "success":
            data.standing.append({"at": _fmt(e.occurred_at), "action": e.action.rsplit(".", 1)[1],
                                  "by": who(e.actor_user_id), "organization": orgs.get(e.organization_id)})
        elif e.action == "support.recording.viewed":
            data.recordings_viewed.append({"at": _fmt(e.occurred_at), "by": who(e.actor_user_id),
                                           "organization": orgs.get(e.organization_id)})
        elif e.action.startswith("support.") and e.outcome == "denied":
            data.denied_attempts += 1
    data.audit_events = len(events)
    data.audit_digest = digest.hexdigest()
    if kind == KIND_AUDITOR:
        data.alerts = [{"at": _fmt(a.created_at), "severity": a.severity, "title": a.title, "status": a.status}
                       for a in db.scalars(select(SecurityAlert).where(SecurityAlert.created_at >= start,
                                                                       SecurityAlert.created_at < end)
                                           .order_by(SecurityAlert.created_at))]
    return data


# --------------------------------------------------------------- tworzenie raportu


def generate(ctx: Ctx, kind: str, organization_id: str | None, start: datetime, end: datetime,
             created_by: str = "system") -> AccessReport:
    from forvium.reports.pdf import render

    if end > clock.now():
        raise DomainError(422, "period_not_finished", "Raport można utworzyć tylko za zakończony okres.")
    existing = ctx.db.scalar(select(AccessReport).where(
        AccessReport.kind == kind, AccessReport.period_start == start,
        AccessReport.organization_id.is_(None) if organization_id is None
        else AccessReport.organization_id == organization_id))
    if existing:
        return existing
    data = collect(ctx, kind, organization_id, start, end)
    pdf = render(data)
    report = AccessReport(kind=kind, organization_id=organization_id, period_start=start, period_end=end,
                          created_at=clock.now(), created_by=created_by, sha256=hashlib.sha256(pdf).hexdigest(),
                          audit_digest=data.audit_digest, size=len(pdf), pdf=base64.b64encode(pdf).decode())
    ctx.db.add(report)
    ctx.db.flush()
    ctx.audit.log(ctx.db, "reports.generated", actor_type="system" if created_by == "system" else "operator",
                  actor_user_id=None if created_by == "system" else created_by, organization_id=organization_id,
                  details={"report_id": report.id, "kind": kind, "period": start.date().isoformat(),
                           "sha256": report.sha256, "sessions": len(data.sessions), "requests": len(data.requests)})
    _notify(ctx, report, data)
    return report


def _notify(ctx: Ctx, report: AccessReport, data: ReportData) -> None:
    from forvium.identity.models import User
    from forvium.platform_admin.rbac import PlatformPermission, platform_permissions
    from forvium.support_access.service import _org_approvers

    stats = L("Sesje wsparcia: {sessions}, prośby o dostęp: {requests}, zablokowane próby: {denied}.\n"
              "SHA-256 pliku: {sha256}", sessions=len(data.sessions), requests=len(data.requests),
              denied=data.denied_attempts, sha256=report.sha256)
    if report.kind == KIND_CUSTOMER:
        recipients = _org_approvers(ctx, report.organization_id)
        where = L("Raport pobierzesz w aplikacji: Ustawienia -> Dostęp serwisowy -> Raporty dostępu.")
    else:
        recipients = [u for u in ctx.db.scalars(select(User).where(User.platform_role.is_not(None),
                                                                   User.is_active.is_(True)))
                      if PlatformPermission.AUDIT_READ in platform_permissions(u.platform_role)]
        where = L("Raport pobierzesz w panelu admin: zakładka Raporty.")
    ctx.notifications.notify(
        ctx.db, recipients, event="reports.access_report_ready",
        title=_PeriodTitle(report.period_start), body=join("\n", [stats, where]),
        organization_id=report.organization_id, data={"report_id": report.id})


class _PeriodTitle(L):
    """Tytul z nazwa miesiaca w jezyku odbiorcy."""

    __slots__ = ("start",)

    def __init__(self, start: datetime) -> None:
        super().__init__("Raport dostępu serwisowego Forvium za {period}")
        self.start = start

    def render(self, lang: str | None = None) -> str:
        lang = lang or current_lang()
        return L(self.template, period=period_label(self.start, lang)).render(lang)


def report_out(r: AccessReport) -> dict:
    return {"id": r.id, "kind": r.kind, "organization_id": r.organization_id,
            "period_start": r.period_start.date().isoformat(), "period_end": r.period_end.date().isoformat(),
            "period_label": period_label(r.period_start), "created_at": r.created_at.isoformat() + "Z",
            "created_by": r.created_by, "sha256": r.sha256, "audit_digest": r.audit_digest, "size": r.size}


def pdf_bytes(report: AccessReport) -> bytes:
    return base64.b64decode(report.pdf)


def generate_due(ctx: Ctx) -> int:
    """Raporty za poprzedni miesiac, ktorych jeszcze nie ma (idempotentne)."""
    from forvium.organizations.models import Organization

    start, end = previous_month(clock.now())
    created = 0
    for org_id in ctx.db.scalars(select(Organization.id).order_by(Organization.id)):
        if not _exists(ctx, KIND_CUSTOMER, org_id, start):
            generate(ctx, KIND_CUSTOMER, org_id, start, end)
            created += 1
    if not _exists(ctx, KIND_AUDITOR, None, start):
        generate(ctx, KIND_AUDITOR, None, start, end)
        created += 1
    return created


def _exists(ctx: Ctx, kind: str, org_id: str | None, start: datetime) -> bool:
    cond = AccessReport.organization_id.is_(None) if org_id is None else AccessReport.organization_id == org_id
    return ctx.db.scalar(select(AccessReport.id).where(AccessReport.kind == kind, cond,
                                                       AccessReport.period_start == start)) is not None


def run_report_job(app) -> int:
    db = app.state.db.sessionmaker()
    try:
        ctx = Ctx.from_state(app.state, db, None)
        n = generate_due(ctx)
        db.commit()
        return n
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
