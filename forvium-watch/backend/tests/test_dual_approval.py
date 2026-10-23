"""Zatwierdzanie dostepu przez dwie osoby po stronie klienta."""

from __future__ import annotations


def _enable(env, token, who):
    return env.client.put(env.org_url("/support-access/settings"), headers=env.h(token),
                          json={"dual_approval": True, "mfa_code": env.otp(who)})


def test_request_needs_two_different_approvers(env):
    alice, dorota = env.login_app("alice"), env.login_app("dorota")
    assert _enable(env, alice, "alice").json()["dual_approval"] is True
    op = env.login_admin("ola")
    request_id = env.create_request(op).json()["request"]["id"]

    r = env.approve(alice, request_id, scopes=["dashboard", "diagnostics"], unit_ids=[env.ids["units"]["waw"]])
    assert r.json() == {"status": "pending_customer_confirmation", "consent": None}
    assert env.start(op, request_id).json()["error"] == "no_consent"
    notes = env.client.get("/api/app/notifications", headers=env.h(dorota)).json()["notifications"]
    assert notes[0]["event"] == "support_access.confirmation_required"

    # Ta sama osoba nie potwierdzi.
    r = env.approve(alice, request_id)
    assert r.status_code == 403 and r.json()["error"] == "second_approver_required"
    # Druga osoba nie moze rozszerzyc zakresu z pierwszego zatwierdzenia.
    r = env.approve(dorota, request_id, scopes=["dashboard", "technologies_cve"])
    assert r.status_code == 422
    r = env.approve(dorota, request_id, scopes=["dashboard"])
    assert r.status_code == 200 and r.json()["status"] == "approved"
    consent = r.json()["consent"]
    assert consent["scopes"] == ["dashboard"] and consent["unit_ids"] == [env.ids["units"]["waw"]]
    assert consent["granted_by_user_id"] == env.ids["users"]["alice"]
    assert consent["second_approver_user_id"] == env.ids["users"]["dorota"]
    assert env.start(op, request_id).status_code == 200
    approved = env.audit(action="support.request.approved")[0]
    assert approved.details["first_approver"] == env.ids["users"]["alice"]
    assert approved.details["second_approver"] == env.ids["users"]["dorota"]


def test_reject_during_confirmation(env):
    alice, dorota = env.login_app("alice"), env.login_app("dorota")
    _enable(env, alice, "alice")
    op = env.login_admin("ola")
    request_id = env.create_request(op).json()["request"]["id"]
    env.approve(alice, request_id)
    r = env.client.post(env.org_url(f"/support-access/requests/{request_id}/reject"), headers=env.h(dorota),
                        json={"note": "nie zgadzam sie"})
    assert r.status_code == 200
    assert env.start(op, request_id).json()["error"] == "no_consent"


def test_standing_consent_needs_confirmation(env):
    alice, dorota = env.login_app("alice"), env.login_app("dorota")
    _enable(env, alice, "alice")
    r = env.client.post(env.org_url("/support-access/standing-consents"), headers=env.h(alice),
                        json={"scopes": ["dashboard"], "max_session_minutes": 10, "valid_days": 30,
                              "mfa_code": env.otp("alice")})
    standing = r.json()["standing_consent"]
    assert standing["pending_confirmation"] is True and standing["active"] is False
    op = env.login_admin("ola")
    # Niepotwierdzona zgoda stala niczego nie zatwierdza automatycznie.
    assert env.create_request(op, scopes=["dashboard"], duration=10).json()["request"]["status"] == "pending"
    url = env.org_url(f"/support-access/standing-consents/{standing['id']}/confirm")
    assert env.client.post(url, headers=env.h(alice), json={"mfa_code": env.otp("alice")}).status_code == 403
    r = env.client.post(url, headers=env.h(dorota), json={"mfa_code": env.otp("dorota")})
    assert r.status_code == 200 and r.json()["standing_consent"]["active"] is True
    assert env.create_request(op, scopes=["dashboard"], duration=10).json()["request"]["status"] == "approved"


def test_disabling_protection_requires_second_person(env):
    alice, dorota = env.login_app("alice"), env.login_app("dorota")
    _enable(env, alice, "alice")
    off = {"dual_approval": False}
    r = env.client.put(env.org_url("/support-access/settings"), headers=env.h(alice), json={**off, "mfa_code": env.otp("alice")})
    assert r.json() == {"dual_approval": True, "dual_approval_disable_requested_by": env.ids["users"]["alice"]}
    r = env.client.put(env.org_url("/support-access/settings"), headers=env.h(alice), json={**off, "mfa_code": env.otp("alice")})
    assert r.status_code == 409
    r = env.client.put(env.org_url("/support-access/settings"), headers=env.h(dorota), json={**off, "mfa_code": env.otp("dorota")})
    assert r.json()["dual_approval"] is False
    assert env.audit(action="support.settings.dual_approval_disabled")
    # Bez MFA zmiana jest odrzucana; tryb wsparcia nie ma do niej dostepu.
    r = env.client.put(env.org_url("/support-access/settings"), headers=env.h(alice), json={"dual_approval": True, "mfa_code": "000000"})
    assert r.status_code == 401
