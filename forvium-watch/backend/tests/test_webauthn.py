"""WebAuthn (klucze FIDO2 / passkeys) dla operatorow."""

from __future__ import annotations

from datetime import timedelta

from webauthn_helper import SoftAuthenticator

from forvium.core.clock import clock


def _approved_request(env, op):
    request_id = env.create_request(op).json()["request"]["id"]
    env.approve(env.login_app("alice"), request_id)
    return request_id


def _start(env, op, request_id, assertion):
    return env.client.post(f"/api/admin/support-access/requests/{request_id}/sessions", headers=env.h(op),
                           json={"webauthn": assertion})


def test_register_key_and_use_it_for_step_up(env):
    op = env.login_admin("ola")
    key = env.register_key(op, "ola")
    creds = env.client.get("/api/admin/webauthn/credentials", headers=env.h(op)).json()["credentials"]
    assert [c["name"] for c in creds] == ["klucz-ola"]

    request_id = _approved_request(env, op)
    r = _start(env, op, request_id, env.assertion(op, key))
    assert r.status_code == 200, r.text
    assert env.audit(action="identity.webauthn.registered")
    notes = env.client.get("/api/admin/notifications", headers=env.h(op)).json()["notifications"]
    assert any(n["event"] == "identity.webauthn.registered" for n in notes)


def test_registration_requires_step_up(env):
    op = env.login_admin("ola")
    r = env.client.post("/api/admin/webauthn/register/options", headers=env.h(op), json={"mfa_code": "000000"})
    assert r.status_code == 401


def _end(env, op, start_response):
    session_id = start_response.json()["session"]["id"]
    assert env.client.post(f"/api/admin/support-access/sessions/{session_id}/end", headers=env.h(op)).status_code == 200


def test_assertion_cannot_be_replayed(env):
    op = env.login_admin("ola")
    key = env.register_key(op, "ola")
    request_id = _approved_request(env, op)
    assertion = env.assertion(op, key)
    first = _start(env, op, request_id, assertion)
    assert first.status_code == 200
    _end(env, op, first)
    # Ta sama asercja (zuzyte wyzwanie) nie przejdzie drugi raz.
    r = _start(env, op, request_id, assertion)
    assert r.status_code == 401 and r.json()["error"] == "mfa_reverification_failed"


def test_assertions_with_wrong_origin_rp_or_without_user_verification_are_rejected(env):
    op = env.login_admin("ola")
    key = env.register_key(op, "ola")
    request_id = _approved_request(env, op)
    # Zly origin (phishing), brak weryfikacji uzytkownika (PIN/biometria), zly RP.
    for kwargs in ({"origin": "https://admin.forvium.evil"}, {"user_verified": False}, {"rp_id": "evil.test"}):
        r = _start(env, op, request_id, env.assertion(op, key, **kwargs))
        assert r.status_code == 401, kwargs
    # Poprawna asercja nadal dziala (licznik prob resetuje sie po sukcesie).
    assert _start(env, op, request_id, env.assertion(op, key)).status_code == 200


def test_expired_foreign_or_unknown_keys_are_rejected(env):
    op = env.login_admin("ola")
    key = env.register_key(op, "ola")
    request_id = _approved_request(env, op)
    options = env.client.post("/api/admin/webauthn/assertion/options", headers=env.h(op)).json()["options"]
    clock.advance(timedelta(minutes=3))
    assert _start(env, op, request_id, key.assert_(options)).status_code == 401  # wygasle wyzwanie
    marta = env.login_admin("marta")
    marta_key = env.register_key(marta, "marta")
    options = env.client.post("/api/admin/webauthn/assertion/options", headers=env.h(op)).json()["options"]
    assert _start(env, op, request_id, marta_key.assert_(options)).status_code == 401  # klucz innej osoby
    stranger = SoftAuthenticator("admin.forvium.test", "https://admin.forvium.test")
    options = env.client.post("/api/admin/webauthn/assertion/options", headers=env.h(op)).json()["options"]
    assert _start(env, op, request_id, stranger.assert_(options)).status_code == 401  # nieznany klucz
    # Kolejne bledy koncza sie blokada (limit prob MFA).
    for _ in range(2):
        _start(env, op, request_id, stranger.assert_(
            env.client.post("/api/admin/webauthn/assertion/options", headers=env.h(op)).json()["options"]))
    assert _start(env, op, request_id, env.assertion(op, key)).status_code == 429


def test_cloned_key_is_detected_by_sign_counter(env):
    op = env.login_admin("ola")
    key = env.register_key(op, "ola")
    request_id = _approved_request(env, op)
    first = _start(env, op, request_id, env.assertion(op, key))
    assert first.status_code == 200
    _end(env, op, first)
    key.sign_count = 0  # klon z "cofnietym" licznikiem
    options = env.client.post("/api/admin/webauthn/assertion/options", headers=env.h(op)).json()["options"]
    assert _start(env, op, request_id, key.assert_(options)).status_code == 401


def test_break_glass_requires_hardware_key(bg_env):
    from test_break_glass import bg_request

    env = bg_env
    op = env.login_admin("ola")
    r = bg_request(env, op, mfa_code=env.otp("ola"))
    assert r.status_code == 401 and r.json()["error"] == "hardware_mfa_required"
    assert env.client.get("/api/admin/support-access/policy",
                          headers=env.h(op)).json()["break_glass_requires_webauthn"] is True


def test_remove_key(env):
    op = env.login_admin("ola")
    key = env.register_key(op, "ola")
    cred_id = env.client.get("/api/admin/webauthn/credentials", headers=env.h(op)).json()["credentials"][0]["id"]
    r = env.client.post(f"/api/admin/webauthn/credentials/{cred_id}/remove", headers=env.h(op),
                        json={"webauthn": env.assertion(op, key)})
    assert r.status_code == 200
    assert env.client.get("/api/admin/webauthn/credentials", headers=env.h(op)).json()["credentials"] == []
    assert env.audit(action="identity.webauthn.removed")
