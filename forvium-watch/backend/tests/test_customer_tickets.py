"""Zgloszenia od klienta: tworzenie, rozmowa z supportem, notatki wewnetrzne, zamkniecie."""

from __future__ import annotations

from sqlalchemy import select, text

from forvium.notifications.models import Notification


def _create(env, token, subject="Agent w Krakowie nie raportuje", priority="high"):
    return env.client.post(env.org_url("/tickets"), headers=env.h(token), json={
        "subject": subject, "description": "Od wczoraj brak danych z agenta w Oddziale Kraków.",
        "priority": priority})


def _events(env, user_key):
    with env.app.state.db.sessionmaker() as s:
        return [n.event for n in s.scalars(select(Notification).where(
            Notification.user_id == env.ids["users"][user_key]).order_by(Notification.created_at))]


def test_customer_creates_ticket_and_talks_with_support(env):
    bob = env.login_app("bob")
    r = _create(env, bob)
    assert r.status_code == 200, r.text
    ticket = r.json()["ticket"]
    assert ticket["number"] == "FW-2002" and ticket["created_by_customer"] and ticket["priority"] == "high"
    # Kierownik supportu i administrator dostaja powiadomienie.
    assert "support_tickets.created" in _events(env, "marta")
    assert "support_tickets.created" in _events(env, "adam")

    marta = env.login_admin("marta")
    r = env.client.post(f"/api/admin/tickets/{ticket['id']}/messages", headers=env.h(marta),
                        json={"body": "Sprawdzamy - prosimy o zgodę na dostęp do diagnostyki."})
    assert r.status_code == 200
    env.client.post(f"/api/admin/tickets/{ticket['id']}/messages", headers=env.h(marta),
                    json={"body": "Notatka: prawdopodobnie certyfikat agenta.", "internal": True})
    assert "support_tickets.forvium_reply" in _events(env, "bob")

    detail = env.client.get(env.org_url(f"/tickets/{ticket['id']}"), headers=env.h(bob)).json()
    assert detail["ticket"]["status"] == "in_progress"
    assert [m["body"] for m in detail["messages"]] == ["Sprawdzamy - prosimy o zgodę na dostęp do diagnostyki."]
    assert detail["ticket"]["description"].startswith("Od wczoraj")

    r = env.client.post(env.org_url(f"/tickets/{ticket['id']}/messages"), headers=env.h(bob),
                        json={"body": "Zgoda będzie za chwilę."})
    assert r.status_code == 200
    assert "support_tickets.customer_reply" in _events(env, "marta")
    admin_view = env.client.get(f"/api/admin/tickets/{ticket['id']}", headers=env.h(marta)).json()
    assert [m["internal"] for m in admin_view["messages"]] == [False, True, False]
    assert env.audit(action="support_tickets.created")


def test_access_request_on_customer_ticket_and_close_ends_session(env):
    bob = env.login_app("bob")
    ticket = _create(env, bob).json()["ticket"]
    env.ids["tickets"]["bob_ticket"] = ticket["number"]
    op = env.login_admin("ola")
    req = env.create_request(op, ticket="bob_ticket")
    assert req.status_code == 200, req.text
    request_id = req.json()["request"]["id"]
    alice = env.login_app("alice")
    assert env.approve(alice, request_id).status_code == 200
    st = env.start(op, request_id)
    support = env.launch(st.json()["launch_url"])
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(support)).status_code == 200

    detail = env.client.get(env.org_url(f"/tickets/{ticket['id']}"), headers=env.h(bob)).json()
    assert [a["status"] for a in detail["access_requests"]] == ["approved"]
    assert detail["access_requests"][0]["operator_email"] == "ola@forvium.com"

    r = env.client.post(env.org_url(f"/tickets/{ticket['id']}/close"), headers=env.h(bob))
    assert r.json()["support_sessions_ended"] == 1
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(support)).status_code == 401
    r = env.client.post(env.org_url(f"/tickets/{ticket['id']}/messages"), headers=env.h(bob), json={"body": "x"})
    assert r.status_code == 409


def test_ticket_isolation_and_support_session_has_no_access(env):
    bob = env.login_app("bob")
    ticket = _create(env, bob).json()["ticket"]
    carol = env.login_app("carol")
    beta_url = f"/api/app/orgs/{env.ids['orgs']['beta']}/tickets/{ticket['id']}"
    assert env.client.get(beta_url, headers=env.h(carol)).status_code == 404
    assert env.client.get(env.org_url("/tickets"), headers=env.h(carol)).status_code == 404

    flow = env.open_support_session()
    assert env.client.get(env.org_url("/tickets"), headers=env.h(flow["support"])).status_code == 403
    assert _create(env, flow["support"]).status_code == 403

    # Opis i wiadomosci sa zaszyfrowane w bazie.
    with env.app.state.db.sessionmaker() as s:
        raw = s.execute(text("SELECT description FROM support_tickets WHERE id = :id"), {"id": ticket["id"]}).scalar()
    assert "Kraków" not in raw


def test_closed_ticket_reply_rules_for_forvium(env):
    bob = env.login_app("bob")
    ticket = _create(env, bob).json()["ticket"]
    env.client.post(env.org_url(f"/tickets/{ticket['id']}/close"), headers=env.h(bob))
    marta = env.login_admin("marta")
    url = f"/api/admin/tickets/{ticket['id']}/messages"
    assert env.client.post(url, headers=env.h(marta), json={"body": "Odpowiedź"}).status_code == 409
    assert env.client.post(url, headers=env.h(marta), json={"body": "Notatka", "internal": True}).status_code == 200
    r = env.client.put(f"/api/admin/tickets/{ticket['id']}/status", headers=env.h(marta), json={"status": "open"})
    assert r.json()["ticket"]["status"] == "open"
    assert "support_tickets.status_changed" in _events(env, "bob")
