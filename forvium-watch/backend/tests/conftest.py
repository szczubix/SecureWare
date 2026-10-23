from __future__ import annotations

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from forvium.audit.models import AuditEvent
from forvium.core.clock import clock
from forvium.core.config import Settings
from forvium.main import create_app
from forvium.seed import DEMO_PASSWORD, TOTP, seed


class Env:
    def __init__(self, app, data):
        self.app = app
        self.client = TestClient(app)
        self.ids = {
            "users": {k: u.id for k, u in data["users"].items()},
            "orgs": {k: o.id for k, o in data["orgs"].items()},
            "units": {k: u.id for k, u in data["units"].items()},
            "tickets": {k: t.number for k, t in data["tickets"].items()},
        }
        self.emails = {k: u.email for k, u in data["users"].items()}

    # ---------------------------------------------------------- pomocnicze
    @staticmethod
    def otp(key: str) -> str:
        return pyotp.TOTP(TOTP[key]).now()

    @staticmethod
    def h(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    def login_app(self, key: str) -> str:
        r = self.client.post("/api/app/auth/login",
                             json={"email": self.emails[key], "password": DEMO_PASSWORD, "mfa_code": self.otp(key)})
        assert r.status_code == 200, r.text
        return r.json()["token"]

    def login_admin(self, key: str) -> str:
        r = self.client.post("/api/admin/auth/login",
                             json={"email": self.emails[key], "password": DEMO_PASSWORD, "mfa_code": self.otp(key)})
        assert r.status_code == 200, r.text
        return r.json()["token"]

    def create_request(self, op_token: str, *, operator="ola", org="acme", reference="bob", ticket="acme",
                       scopes=("dashboard", "units", "technologies_cve", "diagnostics"), duration=15,
                       mfa_code=None):
        return self.client.post(
            "/api/admin/support-access/requests",
            headers=self.h(op_token),
            json={
                "organization_id": self.ids["orgs"][org],
                "reference_user_id": self.ids["users"][reference],
                "reason": "Diagnoza bledu wyswietlania CVE zgloszonego przez klienta",
                "ticket_number": self.ids["tickets"][ticket],
                "duration_minutes": duration,
                "scopes": list(scopes),
                "mfa_code": mfa_code or self.otp(operator),
            },
        )

    def approve(self, client_token: str, request_id: str, org="acme", **body):
        return self.client.post(f"/api/app/orgs/{self.ids['orgs'][org]}/support-access/requests/{request_id}/approve",
                                headers=self.h(client_token), json=body)

    def start(self, op_token: str, request_id: str, operator="ola", duration=None):
        return self.client.post(f"/api/admin/support-access/requests/{request_id}/sessions",
                                headers=self.h(op_token),
                                json={"mfa_code": self.otp(operator), "duration_minutes": duration})

    def launch(self, launch_url: str) -> str:
        code = launch_url.split("#code=", 1)[1]
        r = self.client.post("/api/app/support/launch", json={"code": code})
        assert r.status_code == 200, r.text
        return r.json()["token"]

    def open_support_session(self, **approve_body) -> dict:
        """Pelny przeplyw: prosba -> zgoda klienta -> start -> wymiana kodu."""
        op = self.login_admin("ola")
        alice = self.login_app("alice")
        req = self.create_request(op)
        assert req.status_code == 200, req.text
        request_id = req.json()["request"]["id"]
        ap = self.approve(alice, request_id, **approve_body)
        assert ap.status_code == 200, ap.text
        st = self.start(op, request_id)
        assert st.status_code == 200, st.text
        token = self.launch(st.json()["launch_url"])
        return {"op": op, "alice": alice, "request_id": request_id, "consent_id": ap.json()["consent"]["id"],
                "session_id": st.json()["session"]["id"], "support": token}

    def audit(self, **filters) -> list[AuditEvent]:
        with self.app.state.db.sessionmaker() as s:
            stmt = select(AuditEvent).order_by(AuditEvent.occurred_at)
            for k, v in filters.items():
                stmt = stmt.where(getattr(AuditEvent, k) == v)
            return list(s.scalars(stmt))

    def org_url(self, path: str, org="acme") -> str:
        return f"/api/app/orgs/{self.ids['orgs'][org]}{path}"


@pytest.fixture
def env(tmp_path):
    clock.reset()
    # Plikowa baza (a nie in-memory na jednym polaczeniu), aby niezalezne
    # transakcje audytu dzialaly jak w produkcji.
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path}/fw.db", app_origin="https://app.forvium.test",
                              admin_origin="https://admin.forvium.test"))
    with app.state.db.sessionmaker() as s:
        data = seed(s)
        s.commit()
        e = Env(app, data)
    yield e
    clock.reset()
