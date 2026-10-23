"""Obowiazkowe scenariusze Support Access (sekcja 9 specyfikacji) + przypadki dodatkowe."""

from __future__ import annotations

from datetime import timedelta

import pytest

from forvium.core.clock import clock

# --------------------------------------------------------------------- 1


def test_01_cannot_open_session_without_consent(env):
    op = env.login_admin("ola")
    req = env.create_request(op)
    assert req.status_code == 200
    request_id = req.json()["request"]["id"]
    assert req.json()["request"]["status"] == "pending"

    r = env.start(op, request_id)
    assert r.status_code == 403
    assert r.json()["error"] == "no_consent"

    # Odrzucona prosba rowniez nie pozwala na start.
    alice = env.login_app("alice")
    rej = env.client.post(env.org_url(f"/support-access/requests/{request_id}/reject"), headers=env.h(alice),
                          json={"note": "nie teraz"})
    assert rej.status_code == 200
    assert env.start(op, request_id).json()["error"] == "no_consent"

    denied = env.audit(action="support.session.start", outcome="denied")
    assert len(denied) == 2
    assert all(e.actor_user_id == env.ids["users"]["ola"] for e in denied)


def test_01b_mfa_reverification_required(env):
    op = env.login_admin("ola")
    r = env.create_request(op, mfa_code="000000")
    assert r.status_code == 401
    assert r.json()["error"] == "mfa_reverification_failed"

    req = env.create_request(op).json()["request"]
    env.approve(env.login_app("alice"), req["id"])
    bad = env.client.post(f"/api/admin/support-access/requests/{req['id']}/sessions", headers=env.h(op),
                          json={"mfa_code": "000000"})
    assert bad.status_code == 401
    assert len(env.audit(outcome="denied", actor_user_id=env.ids["users"]["ola"])) >= 2


# --------------------------------------------------------------------- 2


def test_02_operator_cannot_approve_own_request(env):
    op = env.login_admin("ola")
    request_id = env.create_request(op).json()["request"]["id"]

    # Ola jest tez administratorem Acme w aplikacji klienta - nadal nie moze zatwierdzic.
    ola_app = env.login_app("ola")
    r = env.approve(ola_app, request_id)
    assert r.status_code == 403
    assert r.json()["error"] == "self_approval"

    # Token operatora nie dziala w API klienta.
    r = env.approve(op, request_id)
    assert r.status_code == 401

    # Zwykly czlonek bez uprawnienia approve rowniez nie moze.
    r = env.approve(env.login_app("bob"), request_id)
    assert r.status_code == 403

    assert env.audit(action="support.request.approve", outcome="denied")[0].details["reason"] == "self_approval"


def test_02b_support_session_cannot_approve_requests(env):
    s = env.open_support_session()
    request_id = env.create_request(s["op"]).json()["request"]["id"]
    r = env.approve(s["support"], request_id)
    assert r.status_code == 403
    assert r.json()["error"] == "support_read_only"


# --------------------------------------------------------------------- 3


def test_03_revoking_consent_blocks_further_requests_immediately(env):
    s = env.open_support_session()
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(s["support"])).status_code == 200

    r = env.client.post(env.org_url(f"/support-access/consents/{s['consent_id']}/revoke"), headers=env.h(s["alice"]))
    assert r.status_code == 200

    r = env.client.get(env.org_url("/dashboard"), headers=env.h(s["support"]))
    assert r.status_code == 401

    # Ponowny start w ramach cofnietej zgody jest niemozliwy.
    assert env.start(s["op"], s["request_id"]).json()["error"] == "consent_inactive"

    assert env.audit(action="support.consent.revoked")
    revoked = env.audit(action="support.session.revoked", support_session_id=s["session_id"])
    assert revoked and revoked[0].details["reason"] == "consent_revoked"

    hist = env.client.get(env.org_url("/support-access"), headers=env.h(s["alice"])).json()
    assert hist["sessions"][0]["status"] == "revoked"


# --------------------------------------------------------------------- 4


def test_04_session_expiry_blocks_access(env):
    s = env.open_support_session()
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(s["support"])).status_code == 200

    clock.advance(timedelta(minutes=15, seconds=1))
    r = env.client.get(env.org_url("/dashboard"), headers=env.h(s["support"]))
    assert r.status_code == 401

    expired = env.audit(action="support.session.expired", support_session_id=s["session_id"])
    assert len(expired) == 1
    assert expired[0].actor_type == "system"


def test_04b_session_cannot_exceed_15_minutes(env):
    op = env.login_admin("ola")
    r = env.create_request(op, duration=60)
    assert r.status_code == 422
    assert r.json()["error"] == "duration_invalid"


def test_04c_launch_code_is_single_use_and_short_lived(env):
    op = env.login_admin("ola")
    request_id = env.create_request(op).json()["request"]["id"]
    env.approve(env.login_app("alice"), request_id)
    url = env.start(op, request_id).json()["launch_url"]
    code = url.split("#code=")[1]
    assert env.client.post("/api/app/support/launch", json={"code": code}).status_code == 200
    assert env.client.post("/api/app/support/launch", json={"code": code}).status_code == 401


# --------------------------------------------------------------------- 5


def test_05_session_for_one_org_gives_no_access_to_another(env):
    s = env.open_support_session()
    for path in ("/dashboard", "/units", "/technologies", "/cves", "/errors"):
        r = env.client.get(env.org_url(path, org="beta"), headers=env.h(s["support"]))
        assert r.status_code == 403, path
        assert r.json()["error"] == "support_org_mismatch"

    # Prosba nie moze wskazac uzytkownika z innej organizacji ani obcego zgloszenia.
    op = s["op"]
    assert env.create_request(op, reference="carol").json()["error"] == "reference_user_invalid"
    assert env.create_request(op, ticket="beta").json()["error"] == "ticket_invalid"
    assert env.create_request(op, ticket="acme_closed").json()["error"] == "ticket_invalid"


def test_05b_consent_unit_scope_limits_visible_units(env):
    s = env.open_support_session(unit_ids=[env.ids["units"]["waw"]])
    units = env.client.get(env.org_url("/units"), headers=env.h(s["support"])).json()["units"]
    assert {u["id"] for u in units} == {env.ids["units"]["waw"]}
    techs = env.client.get(env.org_url("/technologies"), headers=env.h(s["support"])).json()["technologies"]
    assert [t["name"] for t in techs] == ["nginx"]


def test_05c_permissions_never_exceed_scope_reference_user_or_operator(env):
    # Klient zatwierdza tylko dashboard -> CVE i diagnostyka niedostepne.
    s = env.open_support_session(scopes=["dashboard"])
    h = env.h(s["support"])
    dash = env.client.get(env.org_url("/dashboard"), headers=h)
    assert dash.status_code == 200 and "cves" not in dash.json()
    assert env.client.get(env.org_url("/cves"), headers=h).status_code == 403
    assert env.client.get(env.org_url("/errors"), headers=h).status_code == 403

    # Operator L1 nie moze nawet wnioskowac o CVE.
    piotr = env.login_admin("piotr")
    r = env.create_request(piotr, operator="piotr", scopes=["technologies_cve"])
    assert r.status_code == 403 and r.json()["error"] == "scope_exceeds_operator"


# --------------------------------------------------------------------- 6


WRITE_ENDPOINTS = [
    ("put", "/settings", {"settings": {"timezone": "UTC"}}),
    ("put", "/members/{bob}/role", {"role": "owner"}),
    ("delete", "/members/{bob}", None),
    ("delete", "", None),
    ("post", "/billing/payments", {}),
    ("put", "/subscription", {"plan": "free"}),
    ("put", "/smtp", {"host": "evil", "port": 25, "username": "x", "password": "y"}),
    ("post", "/webhooks", {"url": "https://evil.example"}),
]


@pytest.mark.parametrize("method,path,body", WRITE_ENDPOINTS)
def test_06_write_endpoints_reject_read_only(env, method, path, body):
    s = env.open_support_session()
    url = env.org_url(path.format(bob=env.ids["users"]["bob"]))
    kwargs = {"headers": env.h(s["support"])}
    if body is not None:
        kwargs["json"] = body
    r = getattr(env.client, method)(url, **kwargs)
    assert r.status_code == 403
    assert r.json()["error"] == "support_read_only"

    # Nic sie nie zmienilo.
    dash = env.client.get(env.org_url("/config/status"), headers=env.h(s["alice"])).json()
    assert dash["subscription_plan"] == "business"
    assert dash["webhooks_count"] == 1


def test_06b_sensitive_reads_are_blocked(env):
    s = env.open_support_session()
    for path in ("/secrets", "/api-tokens", "/members", "/support-access"):
        r = env.client.get(env.org_url(path), headers=env.h(s["support"]))
        assert r.status_code == 403, path
    status = env.client.get(env.org_url("/config/status"), headers=env.h(s["support"])).json()
    flat = repr(status)
    assert "smtp-super-secret" not in flat and "sk-acme-secret" not in flat and "token=abc123" not in flat


# --------------------------------------------------------------------- 7


def test_07_data_export_is_blocked(env):
    s = env.open_support_session()
    r = env.client.get(env.org_url("/export"), headers=env.h(s["support"]))
    assert r.status_code == 403
    assert r.json()["error"] == "forbidden_in_support_mode"
    # Uzytkownik referencyjny (bob, member) sam ma prawo eksportu - sesja go nie dziedziczy.
    assert env.client.get(env.org_url("/export"), headers=env.h(env.login_app("bob"))).status_code == 200


# --------------------------------------------------------------------- 8


def test_08_password_mfa_and_subscription_changes_are_blocked(env):
    s = env.open_support_session()
    h = env.h(s["support"])
    r = env.client.post("/api/app/account/password", headers=h,
                        json={"current_password": "x", "new_password": "y" * 20})
    assert r.status_code == 403
    assert env.client.post("/api/app/account/mfa/reset", headers=h).status_code == 403
    assert env.client.put(env.org_url("/subscription"), headers=h, json={"plan": "free"}).status_code == 403
    # Odczyt tokenow i powiadomien klienta rowniez zablokowany.
    assert env.client.get("/api/app/account/tokens", headers=h).status_code == 403
    assert env.client.get("/api/app/notifications", headers=h).status_code == 403


# --------------------------------------------------------------------- 9


def test_09_support_session_does_not_affect_user_sessions(env):
    bob = env.login_app("bob")
    before = env.client.get("/api/app/me", headers=env.h(bob)).json()
    assert before["mode"] == "user"

    s = env.open_support_session()  # bob jest uzytkownikiem referencyjnym
    me_support = env.client.get("/api/app/me", headers=env.h(s["support"])).json()
    assert me_support["mode"] == "support"
    assert me_support["user"]["id"] == env.ids["users"]["bob"]
    assert me_support["support"]["operator_id"] == env.ids["users"]["ola"]

    # Sesja klienta dziala bez zmian i ma pelne uprawnienia klienta.
    assert env.client.get("/api/app/me", headers=env.h(bob)).json() == before
    assert env.client.get(env.org_url("/export"), headers=env.h(bob)).status_code == 200

    # Zakonczenie sesji wsparcia nie wylogowuje klienta ani operatora.
    assert env.client.post("/api/app/support/session/end", headers=env.h(s["support"])).status_code == 200
    assert env.client.get("/api/app/me", headers=env.h(bob)).status_code == 200
    assert env.client.get("/api/admin/me", headers=env.h(s["op"])).status_code == 200
    assert env.client.get("/api/app/me", headers=env.h(s["support"])).status_code == 401

    # Token wsparcia nie dziala w panelu admin, a token operatora w aplikacji klienta.
    s2 = env.open_support_session()
    assert env.client.get("/api/admin/me", headers=env.h(s2["support"])).status_code == 401
    assert env.client.get("/api/app/me", headers=env.h(s2["op"])).status_code == 401


# --------------------------------------------------------------------- 10


def test_10_all_operator_actions_are_audited(env):
    s = env.open_support_session()
    h = env.h(s["support"])
    env.client.get(env.org_url("/dashboard"), headers=h)
    env.client.get(env.org_url("/cves"), headers=h)
    env.client.put(env.org_url("/settings"), headers=h, json={"settings": {"x": 1}})
    env.client.get(env.org_url("/export"), headers=h)
    env.client.get(env.org_url("/dashboard", org="beta"), headers=h)
    env.client.post("/api/app/support/session/end", headers=h)
    env.client.get(env.org_url("/dashboard"), headers=h)  # po zakonczeniu

    ola, bob = env.ids["users"]["ola"], env.ids["users"]["bob"]
    actions = [e.action for e in env.audit()]
    for expected in ("support.request.created", "support.request.approved", "support.session.started",
                     "support.session.launched", "support.session.ended", "support.access_denied"):
        assert expected in actions, expected

    calls = env.audit(action="support.api_call", support_session_id=s["session_id"])
    routes = [(c.http_method, c.route, c.status_code) for c in calls]
    assert ("GET", "/api/app/orgs/{org_id}/dashboard", 200) in routes
    assert ("GET", "/api/app/orgs/{org_id}/cves", 200) in routes
    assert ("PUT", "/api/app/orgs/{org_id}/settings", 403) in routes
    assert ("GET", "/api/app/orgs/{org_id}/export", 403) in routes
    assert ("POST", "/api/app/support/session/end", 200) in routes
    assert len(calls) == 6
    for c in calls:
        assert c.actor_user_id == ola and c.on_behalf_of_user_id == bob and c.actor_type == "support"
    assert {c.outcome for c in calls} == {"success", "denied"}

    # Brak poufnych danych w logu.
    dump = repr([(e.details, e.route) for e in env.audit()])
    for secret in ("smtp-super-secret", "sk-acme-secret", "fws_", "fwo_", "fwu_", "fwl_", "Forvium-demo"):
        assert secret not in dump

    # Klient widzi aktywnosc operatora w historii dostepu.
    act = env.client.get(env.org_url(f"/support-access/sessions/{s['session_id']}/activity"),
                         headers=env.h(s["alice"])).json()["events"]
    assert any(e["route"] == "/api/app/orgs/{org_id}/export" and e["outcome"] == "denied" for e in act)


# --------------------------------------------------------------------- dodatkowe


def test_notifications_sent_to_customer_approvers(env):
    op = env.login_admin("ola")
    env.create_request(op)
    alice = env.login_app("alice")
    notes = env.client.get("/api/app/notifications", headers=env.h(alice)).json()["notifications"]
    assert notes[0]["event"] == "support_access.requested"
    # Operator nie dostaje powiadomienia o wlasnej prosbie, mimo ze jest adminem Acme.
    ola_app = env.login_app("ola")
    assert env.client.get("/api/app/notifications", headers=env.h(ola_app)).json()["notifications"] == []
    with env.app.state.db.sessionmaker() as db:
        from sqlalchemy import select

        from forvium.notifications.models import EmailOutbox

        assert [m.to_address for m in db.scalars(select(EmailOutbox))] == ["alice@acme.example"]


def test_banner_info_and_history_visible_to_customer(env):
    s = env.open_support_session()
    info = env.client.get("/api/app/support/session", headers=env.h(s["support"])).json()
    assert info["banner"] == "TRYB WSPARCIA FORVIUM — TYLKO ODCZYT"
    assert info["organization"]["name"] == "Acme Sp. z o.o."
    assert info["operator_id"] == env.ids["users"]["ola"]
    assert 0 < info["remaining_seconds"] <= 15 * 60

    hist = env.client.get(env.org_url("/support-access"), headers=env.h(s["alice"])).json()
    assert hist["requests"][0]["consent"]["id"] == s["consent_id"]
    assert hist["sessions"][0]["status"] == "active"


def test_customer_can_terminate_active_session(env):
    s = env.open_support_session()
    r = env.client.post(env.org_url(f"/support-access/sessions/{s['session_id']}/terminate"), headers=env.h(s["alice"]))
    assert r.status_code == 200
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(s["support"])).status_code == 401


def test_closing_ticket_ends_session(env):
    s = env.open_support_session()
    from sqlalchemy import select

    from forvium.support_tickets.models import SupportTicket

    with env.app.state.db.sessionmaker() as db:
        t = db.scalar(select(SupportTicket).where(SupportTicket.number == "FW-1001"))
        t.status = "closed"
        db.commit()
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(s["support"])).status_code == 401


def test_break_glass_is_disabled(env):
    op = env.login_admin("ola")
    r = env.client.post("/api/admin/support-access/requests", headers=env.h(op), json={
        "organization_id": env.ids["orgs"]["acme"], "reference_user_id": env.ids["users"]["bob"],
        "reason": "Awaria krytyczna, brak kontaktu z klientem", "ticket_number": "FW-1001",
        "scopes": ["dashboard"], "mfa_code": env.otp("ola"), "mode": "break_glass"})
    assert r.status_code == 403 and r.json()["error"] == "break_glass_disabled"
    assert env.client.get("/api/admin/support-access/policy", headers=env.h(op)).json()["break_glass_enabled"] is False


def test_only_requesting_operator_can_start_session(env):
    op = env.login_admin("ola")
    request_id = env.create_request(op).json()["request"]["id"]
    env.approve(env.login_app("alice"), request_id)
    piotr = env.login_admin("piotr")
    r = env.start(piotr, request_id, operator="piotr")
    assert r.status_code == 403 and r.json()["error"] == "not_request_owner"
