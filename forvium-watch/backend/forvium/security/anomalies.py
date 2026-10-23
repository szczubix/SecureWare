"""Wykrywanie anomalii w uzyciu dostepu serwisowego.

Proces w tle co `FORVIUM_ANOMALY_INTERVAL_SECONDS` przeglada Audit Log z
ostatniej godziny i tworzy alerty (`security_alerts`) dla podejrzanych wzorcow.
Kazdy alert ma klucz deduplikacji, wiec ten sam incydent nie generuje
kolejnych alertow przy nastepnych przebiegach.

Reguly:
* denial_burst (wysoki)    - seria odmow w jednej sesji wsparcia; sesja jest
                             automatycznie konczona,
* post_session_access (wysoki) - proby uzycia tokenu zakonczonej sesji
                             (mozliwa kradziez tokenu),
* session_volume (sredni)  - duzo sesji jednego operatora w krotkim czasie,
* multi_org (sredni)       - sesje jednego operatora w wielu organizacjach,
* mfa_lockout (sredni)     - blokada po nieudanych probach MFA/logowania operatora,
* off_hours (niski)        - sesja rozpoczeta poza godzinami pracy,
* break_glass_used (wysoki) - kazde uzycie procedury awaryjnej.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import JSON, DateTime, String, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column

from forvium.audit.models import AuditEvent
from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError
from forvium.core.db import Base, new_id
from forvium.identity.models import User
from forvium.platform_admin.rbac import PlatformPermission, platform_permissions

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rule: Mapped[str] = mapped_column(String(40), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    title: Mapped[str] = mapped_column(String(300))
    dedup_key: Mapped[str] = mapped_column(String(200), unique=True)
    operator_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    support_session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    auto_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)  # open | acknowledged | resolved
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    handled_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)


@dataclass(frozen=True)
class AnomalyPolicy:
    denial_burst_count: int = 5
    denial_burst_window: timedelta = timedelta(minutes=10)
    auto_terminate_on_denial_burst: bool = True
    post_session_attempts: int = 3
    session_volume_count: int = 5
    multi_org_count: int = 3
    window: timedelta = timedelta(hours=1)
    business_hours: tuple[int, int] = (7, 19)  # [od, do) w strefie ponizej, pon-pt
    timezone: str = "Europe/Warsaw"


@dataclass
class Finding:
    rule: str
    severity: str
    title: str
    dedup_key: str
    operator_user_id: str | None = None
    organization_id: str | None = None
    support_session_id: str | None = None
    details: dict | None = None


def _events(ctx: Ctx, since: datetime, *actions: str) -> list[AuditEvent]:
    return list(ctx.db.scalars(select(AuditEvent).where(AuditEvent.occurred_at >= since,
                                                        AuditEvent.action.in_(actions))
                               .order_by(AuditEvent.occurred_at)))


def _bucket(ts: datetime, size: timedelta) -> str:
    return str(int(ts.timestamp() // size.total_seconds()))


def detect(ctx: Ctx, policy: AnomalyPolicy) -> list[Finding]:
    now = clock.now()
    findings: list[Finding] = []

    # 1. Seria odmow w sesji wsparcia.
    denied = defaultdict(list)
    for e in _events(ctx, now - policy.denial_burst_window, "support.api_call"):
        if e.outcome != "success" and e.support_session_id:
            denied[e.support_session_id].append(e)
    for session_id, events in denied.items():
        if len(events) >= policy.denial_burst_count:
            e = events[-1]
            findings.append(Finding(
                "denial_burst", "high", f"Seria {len(events)} zablokowanych operacji w sesji wsparcia",
                f"denial_burst:{session_id}", e.actor_user_id, e.organization_id, session_id,
                {"denied": len(events), "routes": sorted({x.route or "" for x in events})}))

    # 2. Uzycie tokenu zakonczonej sesji.
    reuse = defaultdict(list)
    for e in _events(ctx, now - policy.window, "support.access_denied"):
        if (e.details or {}).get("reason") == "session_not_active" and e.support_session_id:
            reuse[e.support_session_id].append(e)
    for session_id, events in reuse.items():
        if len(events) >= policy.post_session_attempts:
            e = events[-1]
            findings.append(Finding(
                "post_session_access", "high", "Proby uzycia tokenu zakonczonej sesji wsparcia",
                f"post_session_access:{session_id}", e.actor_user_id, e.organization_id, session_id,
                {"attempts": len(events), "ips": sorted({x.ip_address or "" for x in events})}))

    # 3-4. Wolumen sesji i liczba organizacji na operatora.
    started = defaultdict(list)
    for e in _events(ctx, now - policy.window, "support.session.started"):
        if e.actor_user_id:
            started[e.actor_user_id].append(e)
    bucket = _bucket(now, policy.window)
    for operator_id, events in started.items():
        if len(events) >= policy.session_volume_count:
            findings.append(Finding(
                "session_volume", "medium", f"{len(events)} sesji wsparcia operatora w ciagu godziny",
                f"session_volume:{operator_id}:{bucket}", operator_id, details={"sessions": len(events)}))
        orgs = {e.organization_id for e in events}
        if len(orgs) >= policy.multi_org_count:
            findings.append(Finding(
                "multi_org", "medium", f"Sesje operatora w {len(orgs)} organizacjach w ciagu godziny",
                f"multi_org:{operator_id}:{bucket}", operator_id, details={"organizations": sorted(orgs)}))

    # 5. Sesje poza godzinami pracy.
    tz = ZoneInfo(policy.timezone)
    start_h, end_h = policy.business_hours
    for events in started.values():
        for e in events:
            local = e.occurred_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
            if local.weekday() >= 5 or not start_h <= local.hour < end_h:
                findings.append(Finding(
                    "off_hours", "low", "Sesja wsparcia rozpoczeta poza godzinami pracy",
                    f"off_hours:{e.support_session_id}", e.actor_user_id, e.organization_id, e.support_session_id,
                    {"local_time": local.strftime("%Y-%m-%d %H:%M %Z")}))

    # 6. Blokady MFA / logowania operatorow.
    for e in _events(ctx, now - policy.window, "security.lockout"):
        if e.actor_type == "operator" and e.actor_user_id:
            findings.append(Finding(
                "mfa_lockout", "medium", "Blokada konta operatora po nieudanych probach weryfikacji",
                f"mfa_lockout:{e.id}", e.actor_user_id, details=e.details))

    # 7. Uzycie Break Glass.
    for e in _events(ctx, now - policy.window, "break_glass.approved"):
        findings.append(Finding(
            "break_glass_used", "high", "Zatwierdzono procedure Break Glass",
            f"break_glass_used:{e.support_request_id}", None, e.organization_id,
            details={"request_id": e.support_request_id, "approved_by": e.actor_user_id}))
    return findings


def _recipients(ctx: Ctx) -> list[User]:
    users = ctx.db.scalars(select(User).where(User.platform_role.is_not(None), User.is_active.is_(True)))
    return [u for u in users if PlatformPermission.SUPPORT_OVERSIGHT in platform_permissions(u.platform_role)]


def run_detection(ctx: Ctx, policy: AnomalyPolicy) -> list[SecurityAlert]:
    """Zapisuje nowe alerty (deduplikacja po kluczu), powiadamia i wykonuje automatyczne akcje."""
    from forvium.support_access.break_glass_service import notify_security_team
    from forvium.support_access.models import SupportSession
    from forvium.support_access.service import end_session

    created: list[SecurityAlert] = []
    existing = set(ctx.db.scalars(select(SecurityAlert.dedup_key)))
    for f in detect(ctx, policy):
        if f.dedup_key in existing:
            continue
        existing.add(f.dedup_key)
        alert = SecurityAlert(rule=f.rule, severity=f.severity, title=f.title, dedup_key=f.dedup_key,
                              operator_user_id=f.operator_user_id, organization_id=f.organization_id,
                              support_session_id=f.support_session_id, details=f.details or {},
                              created_at=clock.now())
        if f.rule == "denial_burst" and policy.auto_terminate_on_denial_burst and f.support_session_id:
            session = ctx.db.get(SupportSession, f.support_session_id)
            if session is not None and session.status == "active":
                end_session(ctx, session, None, "terminated_by_anomaly", actor_type="system")
                alert.auto_action = "session_terminated"
        try:
            with ctx.db.begin_nested():
                ctx.db.add(alert)
        except IntegrityError:  # rownolegly przebieg na innej instancji
            continue
        created.append(alert)
        ctx.audit.log(ctx.db, "security.alert.raised", actor_type="system", actor_user_id=f.operator_user_id,
                      organization_id=f.organization_id, support_session_id=f.support_session_id,
                      details={"rule": f.rule, "severity": f.severity, "alert_id": alert.id,
                               "auto_action": alert.auto_action})
        if SEVERITY_ORDER[f.severity] >= SEVERITY_ORDER["medium"]:
            body = (f"[{f.severity.upper()}] {f.title}\nOperator: {f.operator_user_id or '-'}\n"
                    f"Organizacja: {f.organization_id or '-'}\nSesja: {f.support_session_id or '-'}\n"
                    + (f"Automatyczna akcja: {alert.auto_action}\n" if alert.auto_action else "")
                    + "Szczegoly: admin.forvium.com -> Alerty.")
            ctx.notifications.notify(ctx.db, _recipients(ctx), event="security.alert",
                                     title=f"Alert bezpieczenstwa: {f.title}", body=body,
                                     organization_id=f.organization_id, data={"alert_id": alert.id},
                                     email=SEVERITY_ORDER[f.severity] >= SEVERITY_ORDER["high"])
            if SEVERITY_ORDER[f.severity] >= SEVERITY_ORDER["high"]:
                notify_security_team(ctx, f"Alert: {f.title}", body)
    return created


def handle_alert(ctx: Ctx, user: User, alert_id: str, status: str, notes: str | None) -> SecurityAlert:
    alert = ctx.db.get(SecurityAlert, alert_id)
    if alert is None:
        raise DomainError(404, "alert_not_found", "Nie znaleziono alertu.")
    if status not in ("acknowledged", "resolved"):
        raise DomainError(422, "status_invalid", "Nieprawidlowy status.")
    if status == "resolved" and len((notes or "").strip()) < 10:
        raise DomainError(422, "notes_required", "Opisz, jak rozwiazano alert.")
    if alert.operator_user_id == user.id:
        raise DomainError(403, "self_handling", "Nie mozna obslugiwac alertu dotyczacego wlasnych dzialan.")
    alert.status = status
    alert.handled_by_user_id = user.id
    alert.handled_at = clock.now()
    alert.notes = (notes or "").strip() or alert.notes
    ctx.audit.log(ctx.db, f"security.alert.{status}", actor_user_id=user.id, actor_type="operator",
                  ip_address=ctx.ip, organization_id=alert.organization_id,
                  details={"alert_id": alert.id, "rule": alert.rule, "notes": alert.notes})
    return alert


def alert_out(a: SecurityAlert) -> dict:
    iso = lambda d: d.isoformat() + "Z" if d else None  # noqa: E731
    return {"id": a.id, "rule": a.rule, "severity": a.severity, "title": a.title, "status": a.status,
            "operator_user_id": a.operator_user_id, "organization_id": a.organization_id,
            "support_session_id": a.support_session_id, "details": a.details, "auto_action": a.auto_action,
            "created_at": iso(a.created_at), "handled_by_user_id": a.handled_by_user_id,
            "handled_at": iso(a.handled_at), "notes": a.notes}


def run_anomaly_job(app) -> int:
    db = app.state.db.sessionmaker()
    try:
        ctx = Ctx.from_state(app.state, db, None)
        n = len(run_detection(ctx, app.state.anomaly_policy))
        db.commit()
        return n
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
