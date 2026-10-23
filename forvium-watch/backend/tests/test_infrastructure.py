"""Migracje, kolejka e-mail i inne elementy infrastruktury."""

from __future__ import annotations

import json
from datetime import timedelta

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, select

from forvium import models  # noqa: F401
from forvium.core.clock import clock
from forvium.core.db import Base
from forvium.core.migrations import upgrade_head
from forvium.notifications.mailer import MAX_ATTEMPTS, deliver_pending, run_delivery
from forvium.notifications.models import EmailOutbox


def test_migrations_match_models(tmp_path):
    url = f"sqlite:///{tmp_path}/m.db"
    upgrade_head(url)
    engine = create_engine(url)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == [], "Modele zmienione bez migracji - uruchom `alembic revision --autogenerate`"


class FakeSender:
    def __init__(self, fail=False):
        self.fail = fail
        self.sent = []

    def send(self, to_address, subject, body):
        if self.fail:
            raise ConnectionRefusedError("smtp down")
        self.sent.append((to_address, subject))


def test_email_outbox_delivered(env):
    op = env.login_admin("ola")
    env.create_request(op)
    sender = FakeSender()
    env.app.state.email_sender = sender
    assert run_delivery(env.app) == 2  # dwie osoby z prawem zatwierdzania w Acme
    assert sorted(to for to, _ in sender.sent) == ["alice@acme.example", "dorota@acme.example"]
    assert all("FW-1001" in subject for _, subject in sender.sent)
    assert run_delivery(env.app) == 0  # nie wysyla drugi raz


def test_email_retry_with_backoff_then_gives_up(env):
    env.create_request(env.login_admin("ola"))
    with env.app.state.db.sessionmaker() as db:
        failing = FakeSender(fail=True)
        assert deliver_pending(db, failing) == 0
        db.commit()
        msg = db.scalar(select(EmailOutbox))
        assert msg.attempts == 1 and msg.last_error == "ConnectionRefusedError" and msg.next_attempt_at
        # Przed terminem ponowienia nic sie nie dzieje.
        assert deliver_pending(db, FakeSender()) == 0
        for _ in range(MAX_ATTEMPTS - 1):
            clock.advance(timedelta(hours=1))
            deliver_pending(db, failing)
            db.commit()
        db.refresh(msg)
        assert msg.failed_at is not None and msg.attempts == MAX_ATTEMPTS
        clock.advance(timedelta(hours=1))
        assert deliver_pending(db, FakeSender()) == 0


def test_audit_export_to_chained_file_and_http(env, tmp_path):
    from forvium.audit.chain import verify_file
    from forvium.audit.export import FileSink, run_audit_export
    from forvium.audit.models import AuditEvent

    received = []

    class FakeHttp:
        def send(self, events):
            received.extend(events)

    path = tmp_path / "export" / "audit.jsonl"
    env.app.state.audit_sinks = [FakeHttp(), FileSink(str(path), b"klucz")]
    env.open_support_session()
    with env.app.state.db.sessionmaker() as db:
        total = db.query(AuditEvent).count()
    first = run_audit_export(env.app)
    assert first < total  # najswiezsze zdarzenia czekaja, az sie "ustala"
    clock.advance(timedelta(minutes=1))
    assert first + run_audit_export(env.app) == total
    assert run_audit_export(env.app) == 0  # bez duplikatow
    assert len(received) == total
    ok, count, _ = verify_file(str(path), b"klucz")
    assert ok and count == total
    # Kolejne zdarzenia dopisuja sie do tego samego lancucha.
    env.login_app("alice")
    clock.advance(timedelta(minutes=1))
    assert run_audit_export(env.app) == 1
    ok, count, _ = verify_file(str(path), b"klucz")
    assert ok and count == total + 1
    # Zly klucz = lancuch niezweryfikowany.
    assert not verify_file(str(path), b"inny")[0]


def test_audit_export_retries_after_sink_failure(env, tmp_path):
    from forvium.audit.export import run_audit_export

    class Broken:
        def send(self, events):
            raise ConnectionError("SIEM niedostepny")

    env.app.state.audit_sinks = [Broken()]
    env.login_app("alice")
    clock.advance(timedelta(minutes=1))
    import pytest

    with pytest.raises(ConnectionError):
        run_audit_export(env.app)
    sent = []

    class Ok:
        def send(self, events):
            sent.extend(events)

    env.app.state.audit_sinks = [Ok()]
    assert run_audit_export(env.app) >= 1 and sent


def test_transaction_committed_before_response_is_sent(env):
    """Regresja: commit musi nastapic, zanim klient dostanie odpowiedz (inaczej wyscig logowanie -> /me)."""
    import asyncio

    from forvium.identity.models import UserSession
    from forvium.seed import DEMO_PASSWORD

    app = env.app
    seen = {}
    body = json.dumps({"email": env.emails["alice"], "password": DEMO_PASSWORD, "mfa_code": env.otp("alice")}).encode()

    async def run():
        sent = False

        async def receive():
            nonlocal sent
            if sent:
                await asyncio.sleep(3600)
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            if message["type"] == "http.response.start":
                with app.state.db.sessionmaker() as db:
                    seen["sessions_at_response_start"] = db.query(UserSession).count()
                seen["status"] = message["status"]

        scope = {"type": "http", "method": "POST", "path": "/api/app/auth/login", "raw_path": b"/api/app/auth/login",
                 "query_string": b"", "headers": [(b"content-type", b"application/json")],
                 "client": ("127.0.0.1", 1), "server": ("test", 80), "scheme": "http", "http_version": "1.1",
                 "root_path": "", "app": app}
        await app(scope, receive, send)

    asyncio.run(run())
    assert seen == {"sessions_at_response_start": 1, "status": 200}
