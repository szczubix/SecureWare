"""Przedluzanie sesji wsparcia."""

from __future__ import annotations

from datetime import timedelta

from forvium.core.clock import clock

REASON = "Diagnoza wymaga jeszcze sprawdzenia logow agentow"


def _extend(env, op, session_id, **body):
    payload = {"minutes": 15, "reason": REASON, **body}
    if "mfa_code" not in payload and "webauthn" not in payload:
        payload["mfa_code"] = env.otp("ola")
    return env.client.post(f"/api/admin/support-access/sessions/{session_id}/extend", headers=env.h(op), json=payload)


def test_extend_session_with_mfa_and_customer_notification(env):
    s = env.open_support_session()
    info = env.client.get("/api/app/support/session", headers=env.h(s["support"])).json()
    r = _extend(env, s["op"], s["session_id"], minutes=10)
    assert r.status_code == 200, r.text
    session = r.json()["session"]
    assert session["extensions_count"] == 1 and session["original_expires_at"] == info["expires_at"]
    after = env.client.get("/api/app/support/session", headers=env.h(s["support"])).json()
    assert after["remaining_seconds"] > info["remaining_seconds"] + 9 * 60 - 60
    notes = env.client.get("/api/app/notifications", headers=env.h(s["alice"])).json()["notifications"]
    assert any(n["event"] == "support_access.session_extended" and REASON in n["body"] for n in notes)
    assert env.audit(action="support.session.extended")[0].details["extension"] == 1
    # Sesja dziala dluzej niz pierwotne 15 min.
    clock.advance(timedelta(minutes=17))
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(s["support"])).status_code == 200


def test_extension_limits(env):
    s = env.open_support_session()
    op, sid = s["op"], s["session_id"]
    assert _extend(env, op, sid, mfa_code="000000").status_code == 401
    assert _extend(env, op, sid, reason="bo tak").status_code == 422
    assert _extend(env, op, sid, minutes=60).status_code == 422
    assert _extend(env, op, sid).status_code == 200
    assert _extend(env, op, sid).status_code == 200
    r = _extend(env, op, sid)  # trzecie przedluzenie
    assert r.status_code == 409 and r.json()["error"] == "extension_limit"


def _dt(iso):
    from datetime import datetime

    return datetime.fromisoformat(iso.rstrip("Z"))


def test_extension_capped_at_45_minutes_total(env):
    s = env.open_support_session()
    op, sid = s["op"], s["session_id"]
    assert _extend(env, op, sid).status_code == 200  # 15 -> 30 min
    clock.advance(timedelta(minutes=20))
    session = _extend(env, op, sid).json()["session"]  # 30 -> 45 min
    assert _dt(session["expires_at"]) - _dt(session["started_at"]) == timedelta(minutes=45)


def test_extension_never_exceeds_consent_validity(env):
    op = env.login_admin("ola")
    request_id = env.create_request(op).json()["request"]["id"]
    consent = env.approve(env.login_app("alice"), request_id, valid_hours=1).json()["consent"]
    clock.advance(timedelta(minutes=40))
    sid = env.start(op, request_id).json()["session"]["id"]  # sesja do ~55. minuty zgody
    session = _extend(env, op, sid).json()["session"]
    assert session["expires_at"] == consent["valid_until"]  # przyciete do konca zgody
    r = _extend(env, op, sid)
    assert r.status_code == 409 and r.json()["error"] == "extension_window_exhausted"


def test_cannot_extend_after_revocation_or_someone_elses_session(env):
    s = env.open_support_session()
    marta = env.login_admin("marta")
    r = env.client.post(f"/api/admin/support-access/sessions/{s['session_id']}/extend", headers=env.h(marta),
                        json={"minutes": 5, "reason": REASON, "mfa_code": env.otp("marta")})
    assert r.status_code == 404
    env.client.post(env.org_url(f"/support-access/consents/{s['consent_id']}/revoke"), headers=env.h(s["alice"]))
    r = _extend(env, s["op"], s["session_id"])
    assert r.status_code == 409
