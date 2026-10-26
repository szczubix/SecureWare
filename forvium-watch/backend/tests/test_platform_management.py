"""Zarzadzanie platforma: organizacje, aktywacja kont, blokady, operatorzy, zgloszenia."""

from __future__ import annotations

import re
from datetime import timedelta

import pyotp
from sqlalchemy import select

from forvium.core.clock import clock
from forvium.notifications.models import EmailOutbox, Notification
from forvium.seed import DEMO_PASSWORD


def _activation_token(env, email: str) -> str:
    with env.app.state.db.sessionmaker() as s:
        mails = list(s.scalars(select(EmailOutbox).where(EmailOutbox.to_address == email)
                               .order_by(EmailOutbox.created_at)))
    assert mails, f"brak e-maila do {email}"
    return re.search(r"#token=(fwa_[\w-]+)", mails[-1].body).group(1)


def _activate(env, token: str, panel: str = "app", password: str = "Nowe-haslo-2026!x") -> str:
    info = env.client.post(f"/api/{panel}/activation/info", json={"token": token})
    assert info.status_code == 200, info.text
    secret = info.json()["mfa_secret"]
    code = pyotp.TOTP(secret).at(clock.now())
    r = env.client.post(f"/api/{panel}/activation/complete",
                        json={"token": token, "password": password, "mfa_code": code})
    assert r.status_code == 200, r.text
    return secret


def _create_org(env, op, who="adam", **kw):
    body = {"name": "Gamma Sp. z o.o.", "subscription_plan": "business", "owner_email": "gosia@gamma.example",
            "owner_name": "Gosia Gamma", "mfa_code": env.otp(who), **kw}
    return env.client.post("/api/admin/organizations", headers=env.h(op), json=body)


def test_create_organization_with_owner_activated_by_email_link(env):
    adam = env.login_admin("adam")
    r = _create_org(env, adam)
    assert r.status_code == 200, r.text
    assert r.json()["owner"]["state"] == "pending_activation"
    # Link aktywacyjny nie wraca do operatora - tylko e-mail na adres konta.
    assert "fwa_" not in r.text
    org_id = r.json()["organization"]["id"]

    # Przed aktywacja nie da sie zalogowac.
    login = {"email": "gosia@gamma.example", "password": DEMO_PASSWORD}
    assert env.client.post("/api/app/auth/login", json=login).status_code == 401

    token = _activation_token(env, "gosia@gamma.example")
    # Token klienta nie dziala w panelu operatorow.
    assert env.client.post("/api/admin/activation/info", json={"token": token}).status_code == 404
    secret = _activate(env, token)
    clock.advance(timedelta(seconds=31))
    r = env.client.post("/api/app/auth/login", json={"email": "gosia@gamma.example", "password": "Nowe-haslo-2026!x",
                                                     "mfa_code": pyotp.TOTP(secret).at(clock.now())})
    assert r.status_code == 200, r.text
    me = env.client.get("/api/app/me", headers=env.h(r.json()["token"])).json()
    assert me["organizations"] == [{"id": org_id, "name": "Gamma Sp. z o.o.", "role": "owner"}]
    # Link jest jednorazowy.
    assert env.client.post("/api/app/activation/info", json={"token": token}).status_code == 404
    assert env.audit(action="platform.organization.created")
    assert env.audit(action="identity.activation.completed")


def test_activation_rejects_weak_password_and_wrong_code(env):
    adam = env.login_admin("adam")
    _create_org(env, adam)
    token = _activation_token(env, "gosia@gamma.example")
    env.client.post("/api/app/activation/info", json={"token": token})
    r = env.client.post("/api/app/activation/complete", json={"token": token, "password": "krotkie", "mfa_code": "1"})
    assert r.status_code == 422 and r.json()["error"] == "password_policy"
    r = env.client.post("/api/app/activation/complete",
                        json={"token": token, "password": "Dlugie-haslo-2026!", "mfa_code": "000000"})
    assert r.status_code == 422 and r.json()["error"] == "mfa_code_invalid"


def test_organization_management_permissions_and_step_up(env):
    marta, piotr = env.login_admin("marta"), env.login_admin("piotr")
    assert _create_org(env, marta, who="marta").status_code == 403
    assert _create_org(env, piotr, who="piotr").status_code == 403
    adam = env.login_admin("adam")
    r = _create_org(env, adam, mfa_code="000000")
    assert r.status_code == 401
    orgs = env.client.get("/api/admin/organizations", headers=env.h(adam)).json()["organizations"]
    assert [o["name"] for o in orgs] == ["Acme Sp. z o.o.", "Beta S.A."]
    # Operator nie moze byc wlascicielem organizacji klienta.
    r = _create_org(env, adam, owner_email="ola@forvium.com")
    assert r.status_code == 409 and r.json()["error"] == "owner_is_operator"


def test_update_organization_notifies_customer(env):
    adam = env.login_admin("adam")
    r = env.client.put(f"/api/admin/organizations/{env.ids['orgs']['acme']}", headers=env.h(adam),
                       json={"subscription_plan": "enterprise", "mfa_code": env.otp("adam")})
    assert r.status_code == 200 and r.json()["organization"]["subscription_plan"] == "enterprise"
    alice = env.login_app("alice")
    notes = env.client.get("/api/app/notifications", headers=env.h(alice)).json()["notifications"]
    assert notes[0]["event"] == "platform.organization.updated"


def test_block_customer_revokes_sessions_and_support_sessions(env):
    flow = env.open_support_session()  # bob jest uzytkownikiem referencyjnym
    bob = env.login_app("bob")
    adam = env.login_admin("adam")
    r = env.client.post(f"/api/admin/users/{env.ids['users']['bob']}/block", headers=env.h(adam),
                        json={"reason": "Podejrzenie przejęcia konta", "mfa_code": env.otp("adam")})
    assert r.status_code == 200 and r.json()["user"]["state"] == "blocked"
    assert env.client.get("/api/app/me", headers=env.h(bob)).status_code == 401
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(flow["support"])).status_code == 401
    r = env.client.post("/api/app/auth/login", json={"email": env.emails["bob"], "password": DEMO_PASSWORD,
                                                     "mfa_code": env.otp("bob")})
    assert r.status_code == 401
    with env.app.state.db.sessionmaker() as s:
        events = {n.event for n in s.scalars(select(Notification).where(
            Notification.user_id == env.ids["users"]["alice"]))}
    assert "platform.user.blocked" in events
    r = env.client.post(f"/api/admin/users/{env.ids['users']['bob']}/unblock", headers=env.h(adam),
                        json={"mfa_code": env.otp("adam")})
    assert r.json()["user"]["state"] == "active"
    env.login_app("bob")
    # Support L1 nie blokuje kont.
    piotr = env.login_admin("piotr")
    r = env.client.post(f"/api/admin/users/{env.ids['users']['bob']}/block", headers=env.h(piotr),
                        json={"reason": "test blokady", "mfa_code": env.otp("piotr")})
    assert r.status_code == 403


def test_operator_lifecycle_with_privileged_role_approval(env):
    adam = env.login_admin("adam")
    r = env.client.post("/api/admin/operators", headers=env.h(adam), json={
        "email": "nowy@forvium.com", "display_name": "Nowy Operator", "role": "platform_admin",
        "mfa_code": env.otp("adam")})
    assert r.status_code == 422 and r.json()["error"] == "privileged_role_needs_approval"
    r = env.client.post("/api/admin/operators", headers=env.h(adam), json={
        "email": "nowy@forvium.com", "display_name": "Nowy Operator", "role": "support_l1",
        "mfa_code": env.otp("adam")})
    assert r.status_code == 200, r.text
    new_id = r.json()["operator"]["id"]
    _activate(env, _activation_token(env, "nowy@forvium.com"), panel="admin")

    # Rola uprzywilejowana czeka na oficera bezpieczenstwa.
    r = env.client.put(f"/api/admin/operators/{new_id}/role", headers=env.h(adam),
                       json={"role": "security_officer", "mfa_code": env.otp("adam")})
    assert r.json()["status"] == "pending_approval"
    assert r.json()["operator"]["role"] == "support_l1"
    # Administrator nie zatwierdza sam.
    r = env.client.post(f"/api/admin/operators/{new_id}/role/approve", headers=env.h(adam),
                        json={"mfa_code": env.otp("adam")})
    assert r.status_code == 403
    ewa = env.login_admin("ewa")
    r = env.client.post(f"/api/admin/operators/{new_id}/role/approve", headers=env.h(ewa),
                        json={"mfa_code": env.otp("ewa")})
    assert r.status_code == 200 and r.json()["operator"]["role"] == "security_officer"
    changed = env.audit(action="platform.operator.role_changed")[-1]
    assert changed.details["requested_by"] == env.ids["users"]["adam"]
    assert changed.details["approved_by"] == env.ids["users"]["ewa"]

    # Zmiana na role nieuprzywilejowana jest natychmiastowa; wlasnej roli zmienic nie mozna.
    r = env.client.put(f"/api/admin/operators/{new_id}/role", headers=env.h(adam),
                       json={"role": "support_l2", "mfa_code": env.otp("adam")})
    assert r.json()["status"] == "changed"
    r = env.client.put(f"/api/admin/operators/{env.ids['users']['adam']}/role", headers=env.h(adam),
                       json={"role": "support_l2", "mfa_code": env.otp("adam")})
    assert r.status_code == 403


def test_approver_must_be_independent_of_target(env):
    adam = env.login_admin("adam")
    tomasz = env.ids["users"]["tomasz"]
    r = env.client.put(f"/api/admin/operators/{tomasz}/role", headers=env.h(adam),
                       json={"role": "platform_admin", "mfa_code": env.otp("adam")})
    assert r.json()["status"] == "pending_approval"
    t = env.login_admin("tomasz")
    r = env.client.post(f"/api/admin/operators/{tomasz}/role/approve", headers=env.h(t),
                        json={"mfa_code": env.otp("tomasz")})
    assert r.status_code == 403 and r.json()["error"] == "independent_approver_required"
    ewa = env.login_admin("ewa")
    r = env.client.post(f"/api/admin/operators/{tomasz}/role/reject", headers=env.h(ewa),
                        json={"reason": "Brak uzasadnienia", "mfa_code": env.otp("ewa")})
    assert r.json()["status"] == "rejected" and r.json()["operator"]["role"] == "security_officer"


def test_block_operator_ends_support_sessions_and_protects_last_admin(env):
    flow = env.open_support_session()  # operator: ola
    adam = env.login_admin("adam")
    r = env.client.post(f"/api/admin/operators/{env.ids['users']['ola']}/block", headers=env.h(adam),
                        json={"reason": "Zgubiony laptop", "mfa_code": env.otp("adam")})
    assert r.status_code == 200, r.text
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(flow["support"])).status_code == 401
    assert env.client.get("/api/admin/me", headers=env.h(flow["op"])).status_code == 401
    ended = env.audit(action="support.session.revoked")
    assert ended and ended[-1].details["reason"] == "operator_blocked"
    r = env.client.post(f"/api/admin/operators/{env.ids['users']['adam']}/block", headers=env.h(adam),
                        json={"reason": "test blokady", "mfa_code": env.otp("adam")})
    assert r.status_code == 403


def test_tickets_create_and_close_ends_sessions(env):
    flow = env.open_support_session()
    ola = env.login_admin("ola")
    r = env.client.post("/api/admin/tickets", headers=env.h(ola), json={
        "organization_id": env.ids["orgs"]["acme"], "subject": "Nowe zgłoszenie", "mfa_code": env.otp("ola")})
    assert r.status_code == 403  # L2 nie tworzy sobie zgloszen (podstawy dostepu)
    marta = env.login_admin("marta")
    r = env.client.post("/api/admin/tickets", headers=env.h(marta), json={
        "organization_id": env.ids["orgs"]["acme"], "subject": "Brak raportów skanera",
        "mfa_code": env.otp("marta")})
    assert r.status_code == 200 and r.json()["ticket"]["number"] == "FW-2002"
    all_tickets = env.client.get("/api/admin/tickets/all", headers=env.h(marta)).json()["tickets"]
    fw1001 = next(t["id"] for t in all_tickets if t["number"] == env.ids["tickets"]["acme"])
    r = env.client.put(f"/api/admin/tickets/{fw1001}/status", headers=env.h(marta),
                       json={"status": "closed"})
    assert r.status_code == 200, r.text
    assert r.json()["support_sessions_ended"] == 1
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(flow["support"])).status_code == 401
    tickets = env.client.get("/api/admin/tickets/all?status=open", headers=env.h(marta)).json()["tickets"]
    assert {t["number"] for t in tickets} == {"FW-2001", "FW-2002"}


def test_customer_invites_member_who_activates_account(env):
    alice = env.login_app("alice")
    r = env.client.post(env.org_url("/members"), headers=env.h(alice),
                        json={"email": "nowa@acme.example", "display_name": "Nowa Osoba", "role": "member"})
    assert r.status_code == 200 and r.json()["member"]["state"] == "pending_activation"
    _activate(env, _activation_token(env, "nowa@acme.example"))
    members = env.client.get(env.org_url("/members"), headers=env.h(alice)).json()["members"]
    assert {m["email"]: m["state"] for m in members}["nowa@acme.example"] == "active"
    # Operatora Forvium nie da sie dodac jako czlonka; sesja wsparcia nie zaprasza.
    r = env.client.post(env.org_url("/members"), headers=env.h(alice),
                        json={"email": "piotr@forvium.com", "display_name": "Piotr", "role": "admin"})
    assert r.status_code == 409
    flow = env.open_support_session()
    r = env.client.post(env.org_url("/members"), headers=env.h(flow["support"]),
                        json={"email": "x@acme.example", "display_name": "X Y", "role": "admin"})
    assert r.status_code == 403
    # Administrator nie dodaje wlasciciela.
    dorota = env.login_app("dorota")
    r = env.client.post(env.org_url("/members"), headers=env.h(dorota),
                        json={"email": "y@acme.example", "display_name": "Y Z", "role": "owner"})
    assert r.status_code == 403


def test_bootstrap_only_when_role_missing(env):
    import pytest

    from forvium.platform_admin.bootstrap import bootstrap

    # Seed ma juz administratora i oficerow - bootstrap odmawia.
    with pytest.raises(SystemExit):
        bootstrap(env.app, "drugi@forvium.com", "Drugi Admin", "platform_admin")
    adam = env.login_admin("adam")
    for who in ("ewa", "tomasz"):
        env.client.post(f"/api/admin/operators/{env.ids['users'][who]}/block", headers=env.h(adam),
                        json={"reason": "test bootstrapu", "mfa_code": env.otp("adam")})
    link = bootstrap(env.app, "oficer@forvium.com", "Nowy Oficer", "security_officer")
    token = link.split("#token=", 1)[1]
    assert link.startswith("https://admin.forvium.test/activate.html#token=")
    _activate(env, token, panel="admin")
    with pytest.raises(SystemExit):
        bootstrap(env.app, "kolejny@forvium.com", "Kolejny", "security_officer")


def test_bootstrap_refuses_while_first_account_pending(env):
    """Konto czekajace na aktywacje tez blokuje kolejny bootstrap."""
    import pytest

    from forvium.platform_admin.bootstrap import bootstrap

    adam = env.login_admin("adam")
    for who in ("ewa", "tomasz"):
        env.client.post(f"/api/admin/operators/{env.ids['users'][who]}/block", headers=env.h(adam),
                        json={"reason": "test bootstrapu", "mfa_code": env.otp("adam")})
    bootstrap(env.app, "oficer@forvium.com", "Nowy Oficer", "security_officer")
    with pytest.raises(SystemExit):
        bootstrap(env.app, "drugi@forvium.com", "Drugi Oficer", "security_officer")
