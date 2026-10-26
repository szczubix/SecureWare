"""Monitoring: identyfikator zadania, metryki Prometheus, stan zadan w tle."""

from __future__ import annotations

from datetime import timedelta

from conftest import make_env

from forvium.core.clock import clock
from forvium.jobs import run_job_once


def test_request_id_is_propagated_or_generated(env):
    r = env.client.get("/healthz", headers={"X-Request-ID": "gw-1234567890"})
    assert r.headers["x-request-id"] == "gw-1234567890"
    r = env.client.get("/healthz", headers={"X-Request-ID": "x;rm -rf /"})
    assert len(r.headers["x-request-id"]) == 32


def test_metrics_expose_http_jobs_and_domain_gauges(env):
    run_job_once(env.app, "support-sweep", 60, lambda: None)
    env.login_admin("ola")
    body = env.client.get("/metrics").text
    assert 'forvium_http_requests_total{method="POST",route="/api/admin/auth/login",status="200"}' in body
    assert 'forvium_job_stale{task="support-sweep"} 0.0' in body
    assert "forvium_support_sessions_active 0.0" in body
    assert 'forvium_security_alerts_open{severity="high"}' in body
    # Bez etykiet o wysokiej krotnosci (identyfikatory w sciezce).
    assert env.ids["orgs"]["acme"] not in body


def test_stale_job_visible_in_metrics_and_admin(env):
    run_job_once(env.app, "anomaly-detection", 60, lambda: None)
    clock.advance(timedelta(minutes=10))
    assert 'forvium_job_stale{task="anomaly-detection"} 1.0' in env.client.get("/metrics").text
    marta = env.login_admin("marta")
    r = env.client.get("/api/admin/security/jobs", headers=env.h(marta))
    assert r.status_code == 200 and r.json()["stale"] == ["anomaly-detection"]
    piotr = env.login_admin("piotr")
    assert env.client.get("/api/admin/security/jobs", headers=env.h(piotr)).status_code == 403


def test_metrics_token(tmp_path):
    env = make_env(tmp_path, metrics_token="s3cret")
    assert env.client.get("/metrics").status_code == 401
    assert env.client.get("/metrics", headers={"Authorization": "Bearer s3cret"}).status_code == 200
