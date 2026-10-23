"""Zadania w tle: zapis stanu i wykrywanie zatrzymanych zadan."""

from __future__ import annotations

from datetime import timedelta

from forvium.core.clock import clock
from forvium.jobs import JobRun, background_jobs, run_job_once, stale_jobs


def test_job_runs_are_recorded(env):
    run_job_once(env.app, "ok-job", 60, lambda: None)

    def boom():
        raise RuntimeError("SMTP niedostępny")

    run_job_once(env.app, "bad-job", 60, boom)
    with env.app.state.db.sessionmaker() as db:
        ok, bad = db.get(JobRun, "ok-job"), db.get(JobRun, "bad-job")
        assert ok.runs == 1 and ok.failures == 0 and ok.last_success_at is not None
        assert bad.failures == 1 and bad.last_success_at is None and "SMTP niedostępny" in bad.last_error
        assert stale_jobs(db) == []  # swiezo wystartowane
        clock.advance(timedelta(minutes=10))
        assert sorted(stale_jobs(db)) == ["bad-job", "ok-job"]


def test_default_job_set(env):
    names = [name for name, _, _ in background_jobs(env.app)]
    assert {"support-sweep", "email-delivery", "anomaly-detection"} <= set(names)
    assert "audit-export" not in names  # brak skonfigurowanego magazynu eksportu
