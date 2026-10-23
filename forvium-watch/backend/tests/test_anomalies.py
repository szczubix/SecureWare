"""Wykrywanie anomalii i alerty bezpieczenstwa."""

from __future__ import annotations

from datetime import UTC, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from forvium.core.clock import clock
from forvium.notifications.models import EmailOutbox
from forvium.security.anomalies import run_anomaly_job


def _alerts(env, token, **params):
    q = "&".join(f"{k}={v}" for k, v in params.items())
    r = env.client.get("/api/admin/security/alerts?" + q, headers=env.h(token))
    assert r.status_code == 200, r.text
    return r.json()["alerts"]


def _by_rule(alerts, rule):
    return [a for a in alerts if a["rule"] == rule]


def test_denial_burst_raises_alert_and_terminates_session(env):
    s = env.open_support_session()
    h = env.h(s["support"])
    for path in ("/export", "/secrets", "/members", "/api-tokens", "/export"):
        assert env.client.get(env.org_url(path), headers=h).status_code == 403
    assert run_anomaly_job(env.app) >= 1
    marta = env.login_admin("marta")
    alert = _by_rule(_alerts(env, marta), "denial_burst")[0]
    assert alert["severity"] == "high" and alert["auto_action"] == "session_terminated"
    assert alert["operator_user_id"] == env.ids["users"]["ola"] and alert["support_session_id"] == s["session_id"]
    # Sesja zostala zakonczona automatycznie, klient dostal podsumowanie z powodem.
    assert env.client.get(env.org_url("/dashboard"), headers=h).status_code == 401
    notes = env.client.get("/api/app/notifications", headers=env.h(s["alice"])).json()["notifications"]
    ended = next(n for n in notes if n["event"] == "support_access.session_ended")
    assert ended["data"]["summary"]["end_reason"] == "terminated_by_anomaly"
    # Kierownik supportu i oficerowie dostali powiadomienie; deduplikacja przy kolejnym przebiegu.
    admin_notes = env.client.get("/api/admin/notifications", headers=env.h(marta)).json()["notifications"]
    assert any(n["event"] == "security.alert" for n in admin_notes)
    run_anomaly_job(env.app)
    assert len(_by_rule(_alerts(env, marta, status="open"), "denial_burst")) == 1


def test_reuse_of_ended_session_token(env):
    s = env.open_support_session()
    env.client.post("/api/app/support/session/end", headers=env.h(s["support"]))
    for _ in range(3):
        assert env.client.get(env.org_url("/dashboard"), headers=env.h(s["support"])).status_code == 401
    run_anomaly_job(env.app)
    alert = _by_rule(_alerts(env, env.login_admin("marta")), "post_session_access")[0]
    assert alert["severity"] == "high" and alert["details"]["attempts"] == 3


def test_session_volume_and_multi_org(env):
    audit = env.app.state.audit
    ola = env.ids["users"]["ola"]
    orgs = [env.ids["orgs"]["acme"], env.ids["orgs"]["beta"], "org-3", "org-4", "org-5"]
    for i, org in enumerate(orgs):
        audit.record("support.session.started", actor_user_id=ola, actor_type="operator", organization_id=org,
                     support_session_id=f"s{i}")
    run_anomaly_job(env.app)
    alerts = _alerts(env, env.login_admin("marta"))
    assert _by_rule(alerts, "session_volume")[0]["details"]["sessions"] == 5
    assert len(_by_rule(alerts, "multi_org")[0]["details"]["organizations"]) == 5


def test_off_hours_session_is_flagged_without_email(env):
    tz = ZoneInfo("Europe/Warsaw")
    now_local = clock.now().replace(tzinfo=UTC).astimezone(tz)
    saturday = (now_local + timedelta(days=(5 - now_local.weekday()) % 7 or 7)).replace(hour=3, minute=0)
    clock.advance(saturday.astimezone(UTC).replace(tzinfo=None) - clock.now())
    s = env.open_support_session()
    run_anomaly_job(env.app)
    alert = _by_rule(_alerts(env, env.login_admin("marta")), "off_hours")[0]
    assert alert["severity"] == "low" and alert["support_session_id"] == s["session_id"]
    with env.app.state.db.sessionmaker() as db:
        assert not db.scalars(select(EmailOutbox).where(EmailOutbox.subject.like("%poza godzinami%"))).all()


def test_operator_lockout_alert(env):
    op = env.login_admin("ola")
    for _ in range(5):
        env.create_request(op, mfa_code="000000")
    run_anomaly_job(env.app)
    assert _by_rule(_alerts(env, env.login_admin("marta")), "mfa_lockout")


def test_alert_handling(env):
    s = env.open_support_session()
    env.client.post("/api/app/support/session/end", headers=env.h(s["support"]))
    for _ in range(3):
        env.client.get(env.org_url("/dashboard"), headers=env.h(s["support"]))
    run_anomaly_job(env.app)
    marta = env.login_admin("marta")
    alert = _by_rule(_alerts(env, marta), "post_session_access")[0]
    url = f"/api/admin/security/alerts/{alert['id']}"
    assert env.client.post(url + "/acknowledge", headers=env.h(marta), json={}).json()["alert"]["status"] == "acknowledged"
    assert env.client.post(url + "/resolve", headers=env.h(marta), json={"notes": "ok"}).status_code == 422
    r = env.client.post(url + "/resolve", headers=env.h(marta),
                        json={"notes": "Operator zamknął kartę i odświeżył - brak naruszenia."})
    assert r.json()["alert"]["status"] == "resolved"
    assert not _by_rule(_alerts(env, marta), "post_session_access")  # domyslnie tylko otwarte
    assert env.audit(action="security.alert.resolved")
    # Zwykly operator nie ma dostepu do alertow.
    assert env.client.get("/api/admin/security/alerts", headers=env.h(s["op"])).status_code == 403


def test_cannot_handle_alert_about_own_actions(env):
    marta_id = env.ids["users"]["marta"]
    env.app.state.audit.record("security.lockout", actor_user_id=marta_id, actor_type="operator")
    run_anomaly_job(env.app)
    ewa = env.login_admin("ewa")
    alert = _by_rule(_alerts(env, ewa), "mfa_lockout")[0]
    marta = env.login_admin("marta")
    r = env.client.post(f"/api/admin/security/alerts/{alert['id']}/acknowledge", headers=env.h(marta), json={})
    assert r.status_code == 403
    r = env.client.post(f"/api/admin/security/alerts/{alert['id']}/acknowledge", headers=env.h(ewa), json={})
    assert r.status_code == 200
