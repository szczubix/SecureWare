"""Bezpieczenstwo konta klienta: reset MFA."""

from __future__ import annotations

from forvium.seed import DEMO_PASSWORD


def test_mfa_reset_requires_password_and_current_code(env):
    # Regresja (przeglad bezpieczenstwa): sam token sesji nie wystarcza do przejecia MFA.
    alice = env.login_app("alice")
    url = "/api/app/account/mfa/reset"
    assert env.client.post(url, headers=env.h(alice), json={"current_password": DEMO_PASSWORD}).status_code == 401
    r = env.client.post(url, headers=env.h(alice), json={"current_password": "zle", "mfa_code": env.otp("alice")})
    assert r.status_code == 401
    denied = [e for e in env.audit(action="identity.mfa.reset") if e.outcome == "denied"]
    assert len(denied) == 2


def test_mfa_reset_revokes_other_sessions_and_notifies(env):
    other = env.login_app("alice")
    current = env.login_app("alice")
    r = env.client.post("/api/app/account/mfa/reset", headers=env.h(current),
                        json={"current_password": DEMO_PASSWORD, "mfa_code": env.otp("alice")})
    assert r.status_code == 200 and r.json()["secret"]
    assert env.client.get("/api/app/me", headers=env.h(other)).status_code == 401
    assert env.client.get("/api/app/me", headers=env.h(current)).status_code == 200
    notes = env.client.get("/api/app/notifications", headers=env.h(current)).json()["notifications"]
    assert any(n["event"] == "identity.mfa.reset" for n in notes)
