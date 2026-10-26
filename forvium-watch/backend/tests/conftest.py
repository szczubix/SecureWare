from __future__ import annotations

import base64
import os
from datetime import UTC, timedelta

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text

from forvium.audit.models import AuditEvent
from forvium.core.clock import clock
from forvium.core.config import Settings
from forvium.core.migrations import upgrade_head
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
        """Kod TOTP dla biezacego czasu; zegar przesuwa sie o krok, bo kod jest jednorazowy."""
        clock.advance(timedelta(seconds=30))
        return pyotp.TOTP(TOTP[key]).at(clock.now().replace(tzinfo=UTC))

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
                "reason": "Diagnoza błędu wyswietlania CVE zgloszonego przez klienta",
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

    # ---------------------------------------------------------- WebAuthn
    def register_key(self, op_token: str, who: str):
        """Rejestruje programowy klucz FIDO2 dla operatora i zwraca autentykator."""
        from webauthn_helper import SoftAuthenticator

        auth = SoftAuthenticator("admin.forvium.test", "https://admin.forvium.test")
        r = self.client.post("/api/admin/webauthn/register/options", headers=self.h(op_token),
                             json={"mfa_code": self.otp(who)})
        assert r.status_code == 200, r.text
        r = self.client.post("/api/admin/webauthn/register/verify", headers=self.h(op_token),
                             json={"credential": auth.register(r.json()["options"]), "name": f"klucz-{who}"})
        assert r.status_code == 200, r.text
        return auth

    def assertion(self, op_token: str, auth, **kwargs) -> dict:
        r = self.client.post("/api/admin/webauthn/assertion/options", headers=self.h(op_token))
        assert r.status_code == 200, r.text
        return auth.assert_(r.json()["options"], **kwargs)

    def org_url(self, path: str, org="acme") -> str:
        return f"/api/app/orgs/{self.ids['orgs'][org]}{path}"


# Klucze danych tylko dla testow (32 bajty, base64).
TEST_DATA_KEYS = "k1:" + base64.b64encode(b"k" * 32).decode() + ",k0:" + base64.b64encode(b"0" * 32).decode()


def _database_url(tmp_path) -> str:
    """Domyslnie plikowy SQLite (a nie in-memory na jednym polaczeniu), aby
    niezalezne transakcje audytu dzialaly jak w produkcji. Ustaw
    FORVIUM_TEST_DATABASE_URL=postgresql+psycopg://..., by testowac na PostgreSQL
    (kazdy test dostaje czysty schemat)."""
    pg = os.environ.get("FORVIUM_TEST_DATABASE_URL")
    if not pg:
        return f"sqlite:///{tmp_path}/fw.db"
    engine = create_engine(pg)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()
    return pg


def make_env(tmp_path, **settings_overrides) -> Env:
    clock.reset()
    url = _database_url(tmp_path)
    upgrade_head(url)  # schemat z migracji Alembic, tak jak w produkcji
    settings_overrides.setdefault("data_keys", TEST_DATA_KEYS)
    settings_overrides.setdefault("data_key_id", "k1")
    app = create_app(Settings(database_url=url, app_origin="https://app.forvium.test",
                              admin_origin="https://admin.forvium.test", **settings_overrides))
    with app.state.db.sessionmaker() as s:
        data = seed(s)
        s.commit()
        return Env(app, data)


@pytest.fixture
def env(tmp_path):
    e = make_env(tmp_path)
    yield e
    e.app.state.db.engine.dispose()
    clock.reset()


@pytest.fixture
def bg_env(tmp_path):
    """Srodowisko z wlaczonym Break Glass i niezaleznym strumieniem audytu."""
    e = make_env(tmp_path, break_glass_enabled=True, security_team_emails=["security@forvium.com"],
                 break_glass_audit_path=str(tmp_path / "break-glass-audit.jsonl"))
    e.bg_audit_path = tmp_path / "break-glass-audit.jsonl"
    yield e
    e.app.state.db.engine.dispose()
    clock.reset()
