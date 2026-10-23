"""Okresowe raporty dostepu (PDF) dla klientow i audytorow."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select, text

from forvium.core.clock import clock
from forvium.reports.service import AccessReport, month_bounds, previous_month, run_report_job


def _session_with_activity(env):
    op = env.login_admin("ola")
    request_id = env.create_request(op).json()["request"]["id"]
    env.approve(env.login_app("alice"), request_id)
    return op, request_id


def _next_month():
    """Przesuwa zegar na poczatek nastepnego miesiaca (raport obejmie biezaca aktywnosc)."""
    now = clock.now()
    _, end = month_bounds(now.year, now.month)
    clock.advance(end - now + timedelta(hours=1))


def _pdf_text(pdf: bytes) -> str:
    import io

    from pypdf import PdfReader

    return "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)


def test_monthly_reports_generated_once_and_notified(env):
    _session_with_activity(env)
    _next_month()
    assert run_report_job(env.app) == 3  # Acme, Beta, audytor
    assert run_report_job(env.app) == 0  # idempotentnie

    alice = env.login_app("alice")
    reports = env.client.get(env.org_url("/access-reports"), headers=env.h(alice)).json()["reports"]
    assert len(reports) == 1
    r = env.client.get(env.org_url(f"/access-reports/{reports[0]['id']}/pdf"), headers=env.h(alice))
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")
    import hashlib
    assert hashlib.sha256(r.content).hexdigest() == reports[0]["sha256"] == r.headers["x-content-sha256"]
    assert env.audit(action="reports.downloaded")

    notes = env.client.get("/api/app/notifications", headers=env.h(alice)).json()["notifications"]
    assert any(n["event"] == "reports.access_report_ready" for n in notes)


def test_customer_report_contents(env):
    _session_with_activity(env)
    _next_month()
    run_report_job(env.app)
    with env.app.state.db.sessionmaker() as s:
        acme = s.scalar(select(AccessReport).where(AccessReport.organization_id == env.ids["orgs"]["acme"]))
        beta = s.scalar(select(AccessReport).where(AccessReport.organization_id == env.ids["orgs"]["beta"]))
        from forvium.reports.service import pdf_bytes
        acme_text, beta_text = _pdf_text(pdf_bytes(acme)), _pdf_text(pdf_bytes(beta))
        # PDF jest zaszyfrowany w bazie.
        raw = s.execute(text("SELECT pdf FROM access_reports WHERE id = :id"), {"id": acme.id}).scalar()
        assert not raw.startswith("JVBER")  # base64("%PDF")
    assert "Raport dostępu serwisowego" in acme_text and "Acme" in acme_text
    assert "ola@forvium.com" in acme_text and "zatwierdzona" in acme_text
    # Raport Bety nie zawiera danych Acme.
    assert "ola@forvium.com" not in beta_text
    assert "Forvium nie prosiło o dostęp" in beta_text


def test_report_access_control(env):
    _session_with_activity(env)
    _next_month()
    run_report_job(env.app)
    carol = env.login_app("carol")  # Beta
    alice = env.login_app("alice")
    acme_report = env.client.get(env.org_url("/access-reports"), headers=env.h(alice)).json()["reports"][0]
    # Cudza organizacja: 404 (bez ujawniania, ze istnieje).
    assert env.client.get(env.org_url("/access-reports"), headers=env.h(carol)).status_code == 404
    r = env.client.get(env.org_url(f"/access-reports/{acme_report['id']}/pdf", org="beta"), headers=env.h(carol))
    assert r.status_code == 404
    # Operator: raport audytora tylko z platform.audit.read.
    piotr = env.login_admin("piotr")
    assert env.client.get("/api/admin/access-reports", headers=env.h(piotr)).status_code == 403
    marta = env.login_admin("marta")
    reports = env.client.get("/api/admin/access-reports?kind=auditor", headers=env.h(marta)).json()["reports"]
    assert len(reports) == 1
    r = env.client.get(f"/api/admin/access-reports/{reports[0]['id']}/pdf", headers=env.h(marta))
    assert r.status_code == 200
    text_ = _pdf_text(r.content)
    assert "Raport audytora" in text_ and "Acme" in text_


def test_on_demand_generation_only_for_finished_periods(env):
    alice = env.login_app("alice")
    now = clock.now()
    r = env.client.post(env.org_url("/access-reports"), headers=env.h(alice),
                        json={"year": now.year, "month": now.month})
    assert r.status_code == 422
    start, _ = previous_month(now)
    r = env.client.post(env.org_url("/access-reports"), headers=env.h(alice),
                        json={"year": start.year, "month": start.month})
    assert r.status_code == 200, r.text
    again = env.client.post(env.org_url("/access-reports"), headers=env.h(alice),
                            json={"year": start.year, "month": start.month})
    assert again.json()["report"]["id"] == r.json()["report"]["id"]


def test_month_bounds():
    assert month_bounds(2026, 12) == (datetime(2026, 12, 1), datetime(2027, 1, 1))
    assert previous_month(datetime(2026, 1, 15)) == (datetime(2025, 12, 1), datetime(2026, 1, 1))


def test_support_session_cannot_read_reports(env):
    start, end = previous_month(clock.now())
    with env.app.state.db.sessionmaker() as s:
        from forvium.core.context import Ctx
        from forvium.reports.service import KIND_CUSTOMER, generate

        report = generate(Ctx.from_state(env.app.state, s, None), KIND_CUSTOMER, env.ids["orgs"]["acme"], start, end)
        report_id = report.id
        s.commit()
    support = env.open_support_session()["support"]
    assert env.client.get(env.org_url("/access-reports"), headers=env.h(support)).status_code == 403
    r = env.client.get(env.org_url(f"/access-reports/{report_id}/pdf"), headers=env.h(support))
    assert r.status_code == 403
