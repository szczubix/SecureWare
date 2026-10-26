"""Polityka hasel: wycieki, dane osobowe, wymuszona zmiana, reset dostepu przez wlasciciela i Forvium."""

from __future__ import annotations

import hashlib

import pytest
from sqlalchemy import update

from forvium.identity.models import User
from forvium.identity.passwords import is_breached, problems
from forvium.seed import DEMO_PASSWORD
from test_platform_management import _activate, _activation_token

GOOD = "Zielony-Rower-Przy-Wiśle-7"


def test_policy_rules():
    assert problems("krótkie1") == ["too_short"]
    assert "breached" in problems("q1w2e3r4t5y6")
    assert "breached" in problems("Password1234")  # porownanie bez wielkosci liter
    assert "personal" in problems("alice-sekretne-haslo", email="alice@acme.example")
    assert "personal" in problems("Kowalska#2026#haslo", display_name="Alicja Kowalska")
    assert "trivial" in problems("aaaaaaaaaaaaaa")
    assert problems(GOOD, email="alice@acme.example", display_name="Alicja Kowalska") == []


def test_full_pwned_passwords_file(tmp_path, monkeypatch):
    unique = "Unikalne-Haslo-Testowe-9431"
    assert not is_breached(unique)
    hashes = sorted([hashlib.sha1(unique.encode()).hexdigest().upper(), "0" * 40, "F" * 40])
    path = tmp_path / "pwned.txt"
    path.write_text("".join(f"{h}:{i + 1}\n" for i, h in enumerate(hashes)))
    monkeypatch.setenv("FORVIUM_BREACHED_PASSWORDS_FILE", str(path))
    assert is_breached(unique)
    assert not is_breached(GOOD)


def test_change_password_enforces_policy_and_logs_out_other_sessions(env):
    other = env.login_app("alice")
    alice = env.login_app("alice")
    url = "/api/app/account/password"
    r = env.client.post(url, headers=env.h(alice), json={"current_password": DEMO_PASSWORD, "new_password": "1qaz2wsx3edc"})
    assert r.status_code == 422 and "wyciekach" in r.json()["message"]
    r = env.client.post(url, headers=env.h(alice), json={"current_password": "zle", "new_password": GOOD})
    assert r.status_code == 422
    r = env.client.post(url, headers=env.h(alice), json={"current_password": DEMO_PASSWORD, "new_password": GOOD})
    assert r.status_code == 200
    assert env.client.get("/api/app/me", headers=env.h(other)).status_code == 401
    assert env.client.get("/api/app/me", headers=env.h(alice)).status_code == 200


def test_breached_password_forces_change_after_login(env):
    # Haslo ustawione przed aktualizacja listy wyciekow.
    from forvium.core.security import hash_password

    with env.app.state.db.sessionmaker() as s:
        s.execute(update(User).where(User.email == env.emails["bob"]).values(password_hash=hash_password("qwerty123456")))
        s.commit()
    r = env.client.post("/api/app/auth/login", json={"email": env.emails["bob"], "password": "qwerty123456",
                                                     "mfa_code": env.otp("bob")})
    assert r.status_code == 200
    bob = r.json()["token"]
    me = env.client.get("/api/app/me", headers=env.h(bob)).json()
    assert me["password_change_required"] is True
    r = env.client.get(env.org_url("/dashboard"), headers=env.h(bob))
    assert r.status_code == 403 and r.json()["error"] == "password_change_required"
    r = env.client.post("/api/app/account/password", headers=env.h(bob),
                        json={"current_password": "qwerty123456", "new_password": GOOD})
    assert r.status_code == 200
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(bob)).status_code == 200
    assert env.audit(action="identity.password.change_required")


def test_operator_change_password_needs_step_up(env):
    ola = env.login_admin("ola")
    url = "/api/admin/account/password"
    body = {"current_password": DEMO_PASSWORD, "new_password": GOOD}
    assert env.client.post(url, headers=env.h(ola), json={**body, "mfa_code": "000000"}).status_code == 401
    assert env.client.post(url, headers=env.h(ola), json={**body, "mfa_code": env.otp("ola")}).status_code == 200


def test_owner_resets_member_access(env):
    alice = env.login_app("alice")
    bob_id = env.ids["users"]["bob"]
    bob = env.login_app("bob")
    url = env.org_url(f"/members/{bob_id}/reset-access")
    assert env.client.post(url, headers=env.h(alice), json={"mfa_code": "000000"}).status_code == 401
    r = env.client.post(url, headers=env.h(alice), json={"mfa_code": env.otp("alice")})
    assert r.status_code == 200 and r.json()["member"]["state"] == "pending_activation"
    assert env.client.get("/api/app/me", headers=env.h(bob)).status_code == 401
    r = env.client.post("/api/app/auth/login", json={"email": env.emails["bob"], "password": DEMO_PASSWORD,
                                                     "mfa_code": env.otp("bob")})
    assert r.status_code == 401
    # Link idzie na e-mail Boba, nie do Alicji (odpowiedz API go nie zawiera).
    assert "fwa_" not in r.text
    _activate(env, _activation_token(env, env.emails["bob"]), password=GOOD)
    assert env.audit(action="organizations.member.access_reset")


def test_reset_access_restrictions(env):
    dorota = env.login_app("dorota")  # administrator Acme
    alice_id = env.ids["users"]["alice"]
    r = env.client.post(env.org_url(f"/members/{alice_id}/reset-access"), headers=env.h(dorota),
                        json={"mfa_code": env.otp("dorota")})
    assert r.status_code == 403 and r.json()["error"] == "owner_required"
    # Ola (operator) jest tez czlonkiem Acme - konta operatora klient nie resetuje.
    r = env.client.post(env.org_url(f"/members/{env.ids['users']['ola']}/reset-access"), headers=env.h(dorota),
                        json={"mfa_code": env.otp("dorota")})
    assert r.status_code == 409
    alice = env.login_app("alice")
    r = env.client.post(env.org_url(f"/members/{alice_id}/reset-access"), headers=env.h(alice),
                        json={"mfa_code": env.otp("alice")})
    assert r.status_code == 403 and r.json()["error"] == "self_reset_forbidden"


def test_forvium_resets_owner_access(env):
    adam = env.login_admin("adam")
    r = env.client.post(f"/api/admin/users/{env.ids['users']['carol']}/reset-access", headers=env.h(adam),
                        json={"reason": "Jedyna właścicielka zgubiła telefon", "mfa_code": env.otp("adam")})
    assert r.status_code == 200 and r.json()["user"]["state"] == "pending_activation"
    assert "fwa_" not in r.text
    _activate(env, _activation_token(env, env.emails["carol"]), password=GOOD)


@pytest.mark.parametrize("password", ["Krótkie1!", "1qaz2wsx3edc"])
def test_activation_uses_policy(env, password):
    adam = env.login_admin("adam")
    env.client.post("/api/admin/organizations", headers=env.h(adam), json={
        "name": "Delta S.A.", "owner_email": "owner@delta.example", "owner_name": "Owner Delta",
        "mfa_code": env.otp("adam")})
    token = _activation_token(env, "owner@delta.example")
    env.client.post("/api/app/activation/info", json={"token": token})
    r = env.client.post("/api/app/activation/complete", json={"token": token, "password": password, "mfa_code": "1"})
    assert r.status_code == 422 and r.json()["error"] == "password_policy"
