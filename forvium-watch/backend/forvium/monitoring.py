"""Monitoring: identyfikator zadania, log dostepu, metryki Prometheus i stan zadan w tle.

* `RequestContextMiddleware` nadaje kazdemu zadaniu identyfikator (przyjmuje
  `X-Request-ID` z gatewaya, jesli ma poprawny format), zwraca go w odpowiedzi,
  dolacza do wszystkich logow i mierzy czas obslugi. Log dostepu zawiera tylko
  metadane: metode, szablon trasy, kod, czas - bez query stringa i tresci.
* `/metrics` (format Prometheus) jest dostepne tylko w sieci wewnetrznej - gateway
  odpowiada na nie 404, a opcjonalny `FORVIUM_METRICS_TOKEN` wymaga naglowka
  `Authorization: Bearer ...`. Metryki biznesowe i stan zadan czytane sa z bazy
  przy kazdym odczycie, wiec kazda replika API raportuje to samo.
"""

from __future__ import annotations

import contextvars
import hmac
import logging
import re
import time
import uuid

from fastapi import APIRouter, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, generate_latest
from prometheus_client.core import GaugeMetricFamily
from sqlalchemy import func, select
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from forvium.core.clock import clock

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
access_logger = logging.getLogger("forvium.access")


class RequestIdFilter(logging.Filter):
    """Dopisuje `request_id` do kazdego rekordu logu emitowanego w trakcie zadania."""

    def filter(self, record: logging.LogRecord) -> bool:
        rid = request_id_var.get()
        if rid and not hasattr(record, "request_id"):
            record.request_id = rid
        return True


class Metrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.requests = Counter("forvium_http_requests_total", "Zadania HTTP",
                                ["method", "route", "status"], registry=self.registry)
        self.latency = Histogram("forvium_http_request_duration_seconds", "Czas obslugi zadania HTTP",
                                 ["method", "route"], registry=self.registry,
                                 buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5))


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        incoming = dict(scope.get("headers") or []).get(b"x-request-id", b"").decode("latin-1")
        rid = incoming if _VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(rid)
        status_holder = {"status": 500}
        t0 = time.monotonic()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                message.setdefault("headers", [])
                message["headers"] = [*message["headers"], (b"x-request-id", rid.encode())]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.monotonic() - t0
            route_obj = scope.get("route")
            # Szablon trasy (np. /api/app/orgs/{org_id}/dashboard) - ograniczona liczba etykiet.
            route = getattr(route_obj, "path", None) or "unmatched"
            status = status_holder["status"]
            metrics: Metrics | None = getattr(scope["app"].state, "metrics", None)
            if metrics is not None and route != "/metrics":
                metrics.requests.labels(scope["method"], route, str(status)).inc()
                metrics.latency.labels(scope["method"], route).observe(duration)
            if route not in ("/healthz", "/metrics"):
                client = scope.get("client")
                access_logger.info("%s %s %s", scope["method"], route, status, extra={
                    "method": scope["method"], "route": route, "status": status,
                    "duration_ms": round(duration * 1000, 1), "client_ip": client[0] if client else None})
            request_id_var.reset(token)


class DatabaseCollector:
    """Metryki z bazy, liczone przy odczycie `/metrics`."""

    def __init__(self, app) -> None:
        self.app = app

    def collect(self):
        from forvium.jobs import JobRun, stale_jobs
        from forvium.notifications.models import EmailOutbox
        from forvium.security.anomalies import SEVERITY_ORDER, SecurityAlert
        from forvium.support_access.models import RequestStatus, SessionStatus, SupportAccessRequest, SupportSession

        now = clock.now()
        with self.app.state.db.sessionmaker() as db:
            runs = list(db.scalars(select(JobRun)))
            stale = set(stale_jobs(db, now))
            sessions = dict(db.execute(select(SupportSession.status, func.count())
                                       .where(SupportSession.status == SessionStatus.ACTIVE,
                                              SupportSession.expires_at > now)
                                       .group_by(SupportSession.status)).all())
            pending = db.scalar(select(func.count()).select_from(SupportAccessRequest).where(
                SupportAccessRequest.status.in_([RequestStatus.PENDING, RequestStatus.PENDING_SECOND_APPROVAL,
                                                 RequestStatus.PENDING_CUSTOMER_CONFIRMATION])))
            alerts = dict(db.execute(select(SecurityAlert.severity, func.count())
                                     .where(SecurityAlert.status == "open")
                                     .group_by(SecurityAlert.severity)).all())
            queued = db.scalar(select(func.count()).select_from(EmailOutbox).where(
                EmailOutbox.sent_at.is_(None), EmailOutbox.failed_at.is_(None)))
            failed = db.scalar(select(func.count()).select_from(EmailOutbox).where(EmailOutbox.failed_at.is_not(None)))

        age = GaugeMetricFamily("forvium_job_last_success_age_seconds",
                                "Sekundy od ostatniego udanego przebiegu zadania w tle", labels=["task"])
        interval = GaugeMetricFamily("forvium_job_interval_seconds", "Interwal zadania w tle", labels=["task"])
        is_stale = GaugeMetricFamily("forvium_job_stale", "1 = zadanie nie dziala (brak udanego przebiegu)",
                                     labels=["task"])
        runs_total = GaugeMetricFamily("forvium_job_runs", "Liczba przebiegow zadania", labels=["task"])
        failures = GaugeMetricFamily("forvium_job_failures", "Liczba nieudanych przebiegow zadania", labels=["task"])
        for run in runs:
            ref = run.last_success_at or run.last_started_at
            age.add_metric([run.job], (now - ref).total_seconds() if ref else float("inf"))
            interval.add_metric([run.job], run.interval_seconds or 0)
            is_stale.add_metric([run.job], 1 if run.job in stale else 0)
            runs_total.add_metric([run.job], run.runs or 0)
            failures.add_metric([run.job], run.failures or 0)
        yield from (age, interval, is_stale, runs_total, failures)

        yield GaugeMetricFamily("forvium_support_sessions_active", "Aktywne sesje wsparcia",
                                value=sessions.get(SessionStatus.ACTIVE, 0))
        yield GaugeMetricFamily("forvium_support_requests_pending", "Prosby o dostep czekajace na decyzje",
                                value=pending or 0)
        open_alerts = GaugeMetricFamily("forvium_security_alerts_open", "Otwarte alerty bezpieczenstwa",
                                        labels=["severity"])
        for severity in SEVERITY_ORDER:
            open_alerts.add_metric([severity], alerts.get(severity, 0))
        yield open_alerts
        yield GaugeMetricFamily("forvium_email_outbox_queued", "E-maile czekajace na wysylke", value=queued or 0)
        yield GaugeMetricFamily("forvium_email_outbox_failed", "E-maile, ktorych nie udalo sie wyslac",
                                value=failed or 0)


def install(app) -> None:
    metrics = Metrics()
    metrics.registry.register(DatabaseCollector(app))
    app.state.metrics = metrics
    app.add_middleware(RequestContextMiddleware)
    app.include_router(router)


router = APIRouter()


@router.get("/metrics", include_in_schema=False)
def metrics_endpoint(request: Request):
    token = request.app.state.settings.metrics_token
    if token:
        supplied = request.headers.get("authorization", "")
        if not hmac.compare_digest(supplied.encode(), f"Bearer {token}".encode()):
            raise HTTPException(status_code=401)
    return Response(generate_latest(request.app.state.metrics.registry), media_type=CONTENT_TYPE_LATEST)
