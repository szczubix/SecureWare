"""Zadania w tle i ich stan (heartbeat).

W Compose/produkcji zadania wykonuje osobny kontener `worker`
(`python -m forvium.worker`), a API ma je wylaczone
(`FORVIUM_RUN_BACKGROUND_JOBS=false`), dzieki czemu instancje API mozna
skalowac bez dublowania pracy. Lokalnie (jeden proces) zadania moga dzialac
w API.

Kazde wykonanie zapisuje stan w `job_runs` (ostatni start, sukces, blad,
czas trwania) - na tym opiera sie monitoring i healthcheck workera.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column
from starlette.concurrency import run_in_threadpool

from forvium.core.clock import clock
from forvium.core.db import Base

logger = logging.getLogger("forvium.jobs")


class JobRun(Base):
    __tablename__ = "job_runs"

    job: Mapped[str] = mapped_column(String(64), primary_key=True)
    interval_seconds: Mapped[int] = mapped_column(Integer, default=0)
    last_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(300), nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    runs: Mapped[int] = mapped_column(Integer, default=0)
    failures: Mapped[int] = mapped_column(Integer, default=0)


def background_jobs(app) -> list[tuple[str, int, Callable[[], object]]]:
    from forvium.audit.export import run_audit_export
    from forvium.notifications.mailer import run_delivery
    from forvium.reports.service import run_report_job
    from forvium.security.anomalies import run_anomaly_job
    from forvium.support_access.scheduler import run_sweep

    s = app.state.settings
    jobs = [
        ("support-sweep", s.support_sweep_interval_seconds, lambda: run_sweep(app)),
        ("email-delivery", s.email_interval_seconds, lambda: run_delivery(app)),
        ("anomaly-detection", s.anomaly_interval_seconds, lambda: run_anomaly_job(app)),
        ("audit-export", s.audit_export_interval_seconds if app.state.audit_sinks else 0,
         lambda: run_audit_export(app)),
        ("access-reports", s.report_interval_seconds, lambda: run_report_job(app)),
    ]
    return [j for j in jobs if j[1] > 0]


def _record(app, job: str, interval: int, started: datetime, duration_ms: int, error: str | None) -> None:
    with app.state.db.sessionmaker() as db:
        run = db.get(JobRun, job) or JobRun(job=job, runs=0, failures=0)
        run.interval_seconds = interval
        run.last_started_at = started
        run.last_duration_ms = duration_ms
        run.runs = (run.runs or 0) + 1
        if error is None:
            run.last_success_at = clock.now()
        else:
            run.failures = (run.failures or 0) + 1
            run.last_error = error[:300]
            run.last_error_at = clock.now()
        db.merge(run)
        db.commit()


def run_job_once(app, job: str, interval: int, fn: Callable[[], object]) -> None:
    started, t0 = clock.now(), time.monotonic()
    error = None
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - blad jednego przebiegu nie zatrzymuje workera
        error = f"{type(exc).__name__}: {exc}"
        logger.exception("Zadanie %s nie powiodło się", job)
    duration = int((time.monotonic() - t0) * 1000)
    try:
        _record(app, job, interval, started, duration, error)
    except Exception:  # pragma: no cover - stan zadania jest pomocniczy
        logger.exception("Nie udało się zapisać stanu zadania %s", job)


async def _loop(app, job: str, interval: int, fn) -> None:
    while True:
        await asyncio.sleep(interval)
        await run_in_threadpool(run_job_once, app, job, interval, fn)


def start_jobs(app) -> list[asyncio.Task]:
    return [asyncio.create_task(_loop(app, name, interval, fn)) for name, interval, fn in background_jobs(app)]


def stale_jobs(db, now: datetime | None = None, tolerance: float = 3.0) -> list[str]:
    """Zadania bez udanego przebiegu przez `tolerance` x interwal - podstawa healthchecku i alertow."""
    now = now or clock.now()
    stale = []
    for run in db.scalars(select(JobRun)):
        if not run.interval_seconds:
            continue
        reference = run.last_success_at or run.last_started_at
        if reference is None or (now - reference).total_seconds() > tolerance * run.interval_seconds + 30:
            stale.append(run.job)
    return stale
