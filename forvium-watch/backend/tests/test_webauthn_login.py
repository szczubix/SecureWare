"""Logowanie operatora haslem + kluczem WebAuthn (zamiast kodu TOTP)."""

from __future__ import annotations

from conftest import make_env

from forvium.seed import DEMO_PASSWORD


def _options(env, who, password=DEMO_PASSWORD):
    return env.client.post("/api/admin/auth/login/webauthn/options",
                           json={"email": env.emails[who], "password": password})


def _login_with_key(env, who, auth):
    r = _options(env, who)
    assert r.status_code == 200, r.text
    return env.client.post("/api/admin/auth/login", json={
        "email": env.emails[who], "password": DEMO_PASSWORD, "webauthn": auth.assert_(r.json()["options"])})


def test_operator_logs_in_with_key(env):
    auth = env.register_key(env.login_admin("ola"), "ola")
    r = _login_with_key(env, "ola", auth)
    assert r.status_code == 200, r.text
    me = env.client.get("/api/admin/me", headers=env.h(r.json()["token"]))
    assert me.json()["user"]["email"] == env.emails["ola"]
    ok = [e for e in env.audit(action="identity.login.operator") if e.outcome == "success"]
    assert ok[-1].details["second_factor"] == "webauthn"


def test_options_require_valid_password(env):
    env.register_key(env.login_admin("ola"), "ola")
    r = _options(env, "ola", password="zle-haslo")
    assert r.status_code == 401
    assert "allowCredentials" not in r.text
    denied = [e for e in env.audit(action="identity.login.operator") if e.outcome == "denied"]
    assert denied and denied[-1].details["reason"] == "invalid_credentials"


def test_operator_without_key_gets_clear_error(env):
    r = _options(env, "piotr")
    assert r.status_code == 409 and r.json()["error"] == "webauthn_not_registered"


def test_login_challenge_is_single_use_and_purpose_bound(env):
    op = env.login_admin("ola")
    auth = env.register_key(op, "ola")
    # Asercja na wyzwanie step-up nie wystarczy do logowania.
    r = env.client.post("/api/admin/auth/login", json={
        "email": env.emails["ola"], "password": DEMO_PASSWORD, "webauthn": env.assertion(op, auth)})
    assert r.status_code == 401
    # Ta sama asercja logowania nie zadziala drugi raz.
    assertion = auth.assert_(_options(env, "ola").json()["options"])
    body = {"email": env.emails["ola"], "password": DEMO_PASSWORD, "webauthn": assertion}
    assert env.client.post("/api/admin/auth/login", json=body).status_code == 200
    assert env.client.post("/api/admin/auth/login", json=body).status_code == 401
    # Klucz nie zastepuje hasla.
    assertion = auth.assert_(_options(env, "ola").json()["options"])
    r = env.client.post("/api/admin/auth/login", json={
        "email": env.emails["ola"], "password": "zle-haslo", "webauthn": assertion})
    assert r.status_code == 401


def test_webauthn_only_policy_blocks_totp_for_operators_with_key(tmp_path):
    env = make_env(tmp_path, operator_login_webauthn_only=True)
    auth = env.register_key(env.login_admin("ola"), "ola")
    r = env.client.post("/api/admin/auth/login", json={
        "email": env.emails["ola"], "password": DEMO_PASSWORD, "mfa_code": env.otp("ola")})
    assert r.status_code == 401 and r.json()["error"] == "webauthn_required"
    assert _login_with_key(env, "ola", auth).status_code == 200
    # Operator bez klucza nadal loguje sie kodem TOTP.
    env.login_admin("piotr")
