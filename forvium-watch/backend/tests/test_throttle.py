"""Limity nieudanych prob."""

from __future__ import annotations

from datetime import timedelta

from forvium.core.clock import clock
from forvium.seed import DEMO_PASSWORD


def _login(env, password, key="bob"):
    return env.client.post("/api/app/auth/login",
                           json={"email": env.emails[key], "password": password, "mfa_code": env.otp(key)})


def test_login_lockout_after_repeated_failures(env):
    for _ in range(5):
        assert _login(env, "zle-haslo").status_code == 401
    r = _login(env, DEMO_PASSWORD)  # poprawne haslo, ale konto zablokowane
    assert r.status_code == 429 and r.json()["error"] == "too_many_attempts"
    assert env.audit(action="security.lockout")
    assert env.audit(action="security.throttled")
    clock.advance(timedelta(minutes=16))
    assert _login(env, DEMO_PASSWORD).status_code == 200


def test_lockout_is_per_account(env):
    for _ in range(5):
        _login(env, "zle-haslo", key="bob")
    assert _login(env, DEMO_PASSWORD, key="alice").status_code == 200


def test_success_resets_counter(env):
    for _ in range(4):
        _login(env, "zle-haslo")
    assert _login(env, DEMO_PASSWORD).status_code == 200
    for _ in range(4):
        _login(env, "zle-haslo")
    assert _login(env, DEMO_PASSWORD).status_code == 200


def test_mfa_stepup_lockout(env):
    op = env.login_admin("ola")
    for _ in range(5):
        assert env.create_request(op, mfa_code="000000").status_code == 401
    r = env.create_request(op)  # poprawny kod, ale blokada
    assert r.status_code == 429
    lock = env.audit(action="security.lockout")
    assert lock[0].actor_user_id == env.ids["users"]["ola"]


def test_launch_code_bruteforce_is_throttled(env):
    for _ in range(10):
        assert env.client.post("/api/app/support/launch", json={"code": "fwl_zgadywanie"}).status_code == 401
    assert env.client.post("/api/app/support/launch", json={"code": "fwl_zgadywanie"}).status_code == 429


def test_lockout_keys_are_not_stored_in_plain_text(env):
    for _ in range(5):
        _login(env, "zle-haslo")
    from sqlalchemy import select

    from forvium.identity.throttle import RateLimitBucket

    with env.app.state.db.sessionmaker() as db:
        keys = [b.key for b in db.scalars(select(RateLimitBucket))]
    assert keys and all("@" not in k and "testclient" not in k for k in keys)
