"""Izolacja na poziomie PostgreSQL: RLS i uprawnienia roli aplikacji.

Uruchamiane tylko z FORVIUM_TEST_DATABASE_URL (PostgreSQL, konto z prawem CREATEROLE).
"""

from __future__ import annotations

import copy
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from forvium.core.config import Settings
from forvium.main import create_app

PG_URL = os.environ.get("FORVIUM_TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not PG_URL.startswith("postgresql"), reason="wymaga PostgreSQL")

APP_PASSWORD = "forvium-app-test"


@pytest.fixture
def app_role_env(tmp_path):
    """Srodowisko po migracjach, w ktorym istnieje rola forvium_app z nadanymi uprawnieniami."""
    admin = create_engine(PG_URL)
    with admin.begin() as conn:
        conn.execute(text(
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'forvium_app') THEN "
            "CREATE ROLE forvium_app; END IF; END $$"))
        # Rola mogla powstac wczesniej (np. z deploy/postgres/roles.sql) - ustalamy znany stan.
        conn.execute(text(f"ALTER ROLE forvium_app LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD '{APP_PASSWORD}'"))
    admin.dispose()
    from conftest import make_env  # migracje uruchamiane po utworzeniu roli -> 0002 nadaje uprawnienia

    env = make_env(tmp_path)
    app_url = make_url(PG_URL).set(username="forvium_app", password=APP_PASSWORD)
    env.app_url = app_url.render_as_string(hide_password=False)
    yield env
    env.app.state.db.engine.dispose()


def test_app_role_cannot_modify_audit(app_role_env):
    env = app_role_env
    engine = create_engine(env.app_url)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM audit_events")).scalar() >= 0
        for stmt in ("UPDATE audit_events SET outcome = 'x'", "DELETE FROM audit_events",
                     "TRUNCATE audit_events", "DELETE FROM audit_exports"):
            with pytest.raises(DBAPIError, match="permission denied"):
                conn.execute(text(stmt))
            conn.rollback()
    engine.dispose()


def test_rls_limits_support_transaction_to_its_organization(app_role_env):
    env = app_role_env
    acme, beta = env.ids["orgs"]["acme"], env.ids["orgs"]["beta"]
    engine = create_engine(env.app_url)
    with engine.connect() as conn:
        # Zwykla transakcja: widac wszystko (autoryzacja w aplikacji).
        orgs = {r[0] for r in conn.execute(text("SELECT organization_id FROM technologies"))}
        assert orgs == {acme, beta}
        conn.rollback()

        # Transakcja w trybie wsparcia: tylko organizacja z sesji, nawet przy jawnym zapytaniu o inna.
        conn.execute(text("SELECT set_config('forvium.support_org', :o, true)"), {"o": acme})
        assert conn.execute(text("SELECT count(*) FROM technologies WHERE organization_id = :b"),
                            {"b": beta}).scalar() == 0
        assert conn.execute(text("SELECT count(*) FROM organizations")).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM support_tickets WHERE organization_id = :b"),
                            {"b": beta}).scalar() == 0
        with pytest.raises(DBAPIError, match="row-level security"):
            conn.execute(text("INSERT INTO diagnostic_events (id, organization_id, level, component, message, "
                              "created_at) VALUES ('x', :b, 'error', 'x', 'x', now())"), {"b": beta})
        conn.rollback()

        # Ustawienie jest lokalne dla transakcji.
        assert conn.execute(text("SELECT count(*) FROM organizations")).scalar() == 2
    engine.dispose()


def test_full_flow_works_under_app_role_with_rls(app_role_env):
    env = app_role_env
    from conftest import TEST_DATA_KEYS

    app = create_app(Settings(database_url=env.app_url, data_keys=TEST_DATA_KEYS, data_key_id="k1",
                              app_origin="https://app.forvium.test",
                              admin_origin="https://admin.forvium.test"))
    env2 = copy.copy(env)
    env2.app = app
    env2.client = TestClient(app)
    s = env2.open_support_session()
    h = env2.h(s["support"])
    assert env2.client.get(env2.org_url("/dashboard"), headers=h).status_code == 200
    assert env2.client.get(env2.org_url("/cves"), headers=h).status_code == 200
    assert env2.client.get(env2.org_url("/dashboard", org="beta"), headers=h).status_code == 403
    assert env2.client.post("/api/app/support/session/end", headers=h).status_code == 200
    assert env2.audit(action="support.session.ended")
    app.state.db.engine.dispose()
