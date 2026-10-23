"""Break Glass - procedura awaryjna."""

from __future__ import annotations

import json
from datetime import timedelta

from forvium.audit.chain import verify_file
from forvium.core.clock import clock

JUSTIFICATION = (
    "Aktywny incydent bezpieczenstwa: agenci w organizacji raportuja masowe wykrycia krytycznej podatnosci, "
    "a wlasciciel organizacji jest nieosiagalny od 6 godzin (urlop, brak zastepstwa). Potrzebny wglad w liste "
    "CVE i stan konfiguracji, aby potwierdzic, czy alarmy nie sa wynikiem bledu skanera."
)


def _key(env, op_token, who):
    """Klucz WebAuthn operatora (rejestrowany przy pierwszym uzyciu)."""
    keys = env.__dict__.setdefault("_keys", {})
    if who not in keys:
        keys[who] = env.register_key(op_token, who)
    return keys[who]


def bg_request(env, op_token, operator="ola", **overrides):
    body = {
        "organization_id": env.ids["orgs"]["acme"],
        "reference_user_id": env.ids["users"]["bob"],
        "reason": JUSTIFICATION,
        "ticket_number": "FW-1001",
        "duration_minutes": 30,
        "scopes": ["technologies_cve", "diagnostics"],
        "mode": "break_glass",
        "incident_category": "security_incident",
        **overrides,
    }
    if "mfa_code" not in body and "webauthn" not in body:
        body["webauthn"] = env.assertion(op_token, _key(env, op_token, operator))
    return env.client.post("/api/admin/support-access/requests", headers=env.h(op_token), json=body)


def bg_decide(env, officer_token, request_id, officer="ewa", decision="approve", **body):
    payload = dict(body)
    if decision == "approve" and "mfa_code" not in payload:
        payload["webauthn"] = env.assertion(officer_token, _key(env, officer_token, officer))
    return env.client.post(f"/api/admin/break-glass/requests/{request_id}/{decision}",
                           headers=env.h(officer_token), json=payload)


def bg_start(env, op_token, request_id, operator="ola", duration=None):
    return env.client.post(f"/api/admin/support-access/requests/{request_id}/sessions", headers=env.h(op_token),
                           json={"webauthn": env.assertion(op_token, _key(env, op_token, operator)),
                                 "duration_minutes": duration})


def test_break_glass_disabled_by_default(env):
    op = env.login_admin("ola")
    r = bg_request(env, op, mfa_code=env.otp("ola"))
    assert r.status_code == 403 and r.json()["error"] == "break_glass_disabled"


def test_full_break_glass_flow(bg_env):
    env = bg_env
    op = env.login_admin("ola")
    r = bg_request(env, op)
    assert r.status_code == 200, r.text
    req = r.json()["request"]
    assert req["status"] == "pending_second_approval" and req["mode"] == "break_glass"

    # Bez drugiej osoby nie ma sesji.
    assert env.start(op, req["id"]).json()["error"] == "no_consent"

    ewa = env.login_admin("ewa")
    pending = env.client.get("/api/admin/break-glass/requests?status=pending_second_approval",
                             headers=env.h(ewa)).json()["requests"]
    assert [p["id"] for p in pending] == [req["id"]]
    a = bg_decide(env, ewa, req["id"])
    assert a.status_code == 200, a.text
    assert a.json()["consent"]["basis"] == "break_glass"

    st = bg_start(env, op, req["id"], duration=30)
    assert st.status_code == 200
    expires = st.json()["session"]["expires_at"]
    assert expires  # do 30 min (polityka awaryjna)
    token = env.launch(st.json()["launch_url"])
    info = env.client.get("/api/app/support/session", headers=env.h(token)).json()
    assert info["banner"] == "TRYB AWARYJNY FORVIUM (BREAK GLASS) — TYLKO ODCZYT"
    assert 25 * 60 < info["remaining_seconds"] <= 30 * 60
    h = env.h(token)
    assert env.client.get(env.org_url("/cves"), headers=h).status_code == 200
    # Nadal READ_ONLY i bez eksportu.
    assert env.client.put(env.org_url("/settings"), headers=h, json={"settings": {}}).status_code == 403
    assert env.client.get(env.org_url("/export"), headers=h).status_code == 403
    env.client.post("/api/app/support/session/end", headers=h)

    # Klient zostal powiadomiony (aplikacja + e-mail), zespol bezpieczenstwa rowniez.
    alice = env.login_app("alice")
    events = [n["event"] for n in env.client.get("/api/app/notifications", headers=env.h(alice)).json()["notifications"]]
    assert {"break_glass.approved", "support_access.session_started", "support_access.session_ended"} <= set(events)
    from sqlalchemy import select

    from forvium.notifications.models import EmailOutbox

    with env.app.state.db.sessionmaker() as db:
        security_mails = [m.subject for m in db.scalars(select(EmailOutbox).where(
            EmailOutbox.to_address == "security@forvium.com"))]
    assert any("Wniosek Break Glass" in s for s in security_mails)
    assert any("zatwierdzony" in s for s in security_mails)
    assert any("start sesji" in s for s in security_mails)

    # Niezalezny audyt: wszystkie zdarzenia oznaczone i w osobnym, poprawnym lancuchu.
    flagged = env.audit(is_break_glass=True)
    actions = {e.action for e in flagged}
    assert {"break_glass.requested", "break_glass.approved", "support.session.started",
            "support.api_call", "support.session.ended"} <= actions
    ok, count, _ = verify_file(str(env.bg_audit_path))
    assert ok and count == len(flagged)

    # Przeglad po incydencie: niezalezna osoba (nie ola, nie ewa).
    review = {"notes": "Potwierdzono blad sygnatur skanera; zadnych dzialan poza odczytem CVE. Sprawa zamknieta."}
    r = env.client.post(f"/api/admin/break-glass/requests/{req['id']}/review", headers=env.h(ewa), json=review)
    assert r.status_code == 403 and r.json()["error"] == "reviewer_not_independent"
    tomasz = env.login_admin("tomasz")
    todo = env.client.get("/api/admin/break-glass/requests?review_pending=true", headers=env.h(tomasz)).json()
    assert [t["id"] for t in todo["requests"]] == [req["id"]]
    r = env.client.post(f"/api/admin/break-glass/requests/{req['id']}/review", headers=env.h(tomasz), json=review)
    assert r.status_code == 200
    notes = env.client.get("/api/app/notifications", headers=env.h(alice)).json()["notifications"]
    report = next(n for n in notes if n["event"] == "break_glass.reviewed")
    assert "Lista CVE" in report["body"]


def test_four_eyes_and_permissions(bg_env):
    env = bg_env
    op = env.login_admin("ola")
    req = bg_request(env, op).json()["request"]
    # Wnioskujacy nie ma uprawnienia do zatwierdzania.
    r = bg_decide(env, op, req["id"], officer="ola")
    assert r.status_code == 403
    # L1 nie moze wnioskowac.
    piotr = env.login_admin("piotr")
    r = bg_request(env, piotr, operator="piotr", scopes=["dashboard"])
    assert r.status_code == 403 and r.json()["error"] == "operator_not_permitted"
    # Oficer bezpieczenstwa nie moze sam otworzyc sesji awaryjnej.
    ewa = env.login_admin("ewa")
    assert bg_request(env, ewa, operator="ewa").status_code == 403
    # Odrzucenie.
    r = env.client.post(f"/api/admin/break-glass/requests/{req['id']}/reject", headers=env.h(ewa),
                        json={"note": "Brak przeslanek"})
    assert r.status_code == 200
    assert env.start(op, req["id"]).json()["error"] == "no_consent"


def test_justification_and_category_required(bg_env):
    env = bg_env
    op = env.login_admin("ola")
    r = bg_request(env, op, reason="Pilne, klient nie odpowiada na telefon.")
    assert r.status_code == 422 and r.json()["error"] == "reason_too_short"
    r = bg_request(env, op, incident_category="ciekawosc")
    assert r.status_code == 422 and r.json()["error"] == "incident_category_invalid"
    r = bg_request(env, op, duration_minutes=60)
    assert r.status_code == 422 and r.json()["error"] == "duration_invalid"


def test_unapproved_request_expires(bg_env):
    env = bg_env
    op = env.login_admin("ola")
    req = bg_request(env, op).json()["request"]
    clock.advance(timedelta(minutes=61))
    ewa = env.login_admin("ewa")
    r = bg_decide(env, ewa, req["id"])
    assert r.status_code == 409


def test_customer_can_revoke_break_glass_consent(bg_env):
    env = bg_env
    op = env.login_admin("ola")
    req = bg_request(env, op).json()["request"]
    consent_id = bg_decide(env, env.login_admin("ewa"), req["id"]).json()["consent"]["id"]
    token = env.launch(bg_start(env, op, req["id"]).json()["launch_url"])
    alice = env.login_app("alice")
    r = env.client.post(env.org_url(f"/support-access/consents/{consent_id}/revoke"), headers=env.h(alice))
    assert r.status_code == 200
    assert env.client.get(env.org_url("/cves"), headers=env.h(token)).status_code == 401


def test_break_glass_audit_stream_detects_tampering(bg_env):
    env = bg_env
    op = env.login_admin("ola")
    bg_request(env, op)
    lines = env.bg_audit_path.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["event"]["actor_user_id"] = "ktos-inny"
    env.bg_audit_path.write_text("\n".join([json.dumps(rec)] + lines[1:]) + "\n")
    ok, _, message = verify_file(str(env.bg_audit_path))
    assert not ok and "zmienione" in message
