"""Zgoda stala (pre-approval)."""

from __future__ import annotations

from datetime import timedelta

from forvium.core.clock import clock


def _create(env, token, **body):
    payload = {"scopes": ["dashboard", "diagnostics"], "max_session_minutes": 10, "valid_days": 30,
               "mfa_code": env.otp("alice"), **body}
    return env.client.post(env.org_url("/support-access/standing-consents"), headers=env.h(token), json=payload)


def test_request_within_standing_consent_is_auto_approved(env):
    alice = env.login_app("alice")
    r = _create(env, alice)
    assert r.status_code == 200, r.text
    standing_id = r.json()["standing_consent"]["id"]

    op = env.login_admin("ola")
    req = env.create_request(op, scopes=["dashboard"], duration=10).json()["request"]
    assert req["status"] == "approved"
    st = env.start(op, req["id"])
    assert st.status_code == 200
    token = env.launch(st.json()["launch_url"])
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(token)).status_code == 200

    hist = env.client.get(env.org_url("/support-access"), headers=env.h(alice)).json()
    consent = hist["requests"][0]["consent"]
    assert consent["basis"] == "standing" and consent["standing_consent_id"] == standing_id
    notes = env.client.get("/api/app/notifications", headers=env.h(alice)).json()["notifications"]
    assert any(n["event"] == "support_access.auto_approved" for n in notes)
    assert env.audit(action="support.request.auto_approved")


def test_request_outside_standing_consent_needs_manual_approval(env):
    alice = env.login_app("alice")
    _create(env, alice, allowed_platform_roles=["support_l2"])
    op = env.login_admin("ola")
    # Zakres szerszy niz w zgodzie stalej.
    assert env.create_request(op, scopes=["technologies_cve"], duration=10).json()["request"]["status"] == "pending"
    # Czas dluzszy niz w zgodzie stalej.
    assert env.create_request(op, scopes=["dashboard"], duration=15).json()["request"]["status"] == "pending"
    # Rola operatora spoza listy.
    piotr = env.login_admin("piotr")
    r = env.create_request(piotr, operator="piotr", scopes=["dashboard"], duration=10)
    assert r.json()["request"]["status"] == "pending"


def test_revoking_standing_consent_ends_derived_sessions(env):
    alice = env.login_app("alice")
    standing_id = _create(env, alice).json()["standing_consent"]["id"]
    op = env.login_admin("ola")
    req = env.create_request(op, scopes=["dashboard"], duration=10).json()["request"]
    token = env.launch(env.start(op, req["id"]).json()["launch_url"])

    r = env.client.post(env.org_url(f"/support-access/standing-consents/{standing_id}/revoke"), headers=env.h(alice))
    assert r.status_code == 200 and r.json()["standing_consent"]["active"] is False
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(token)).status_code == 401
    # Nowe prosby znow wymagaja recznej zgody.
    assert env.create_request(op, scopes=["dashboard"], duration=10).json()["request"]["status"] == "pending"


def test_standing_consent_expires(env):
    alice = env.login_app("alice")
    _create(env, alice, valid_days=1)
    clock.advance(timedelta(days=1, minutes=1))
    op = env.login_admin("ola")
    assert env.create_request(op, scopes=["dashboard"], duration=10).json()["request"]["status"] == "pending"


def test_standing_consent_requires_mfa_and_permission(env):
    alice = env.login_app("alice")
    r = _create(env, alice, mfa_code="000000")
    assert r.status_code == 401 and r.json()["error"] == "mfa_required"
    # Czlonek bez uprawnienia approve.
    bob = env.login_app("bob")
    assert _create(env, bob, mfa_code=env.otp("bob")).status_code == 403
    # Operator Forvium (nawet jako admin organizacji) nie moze udzielic zgody stalej.
    ola_app = env.login_app("ola")
    r = _create(env, ola_app, mfa_code=env.otp("ola"))
    assert r.status_code == 403 and r.json()["error"] == "operator_cannot_approve"
    # Za dlugi czas sesji.
    assert _create(env, alice, max_session_minutes=60).status_code == 422
