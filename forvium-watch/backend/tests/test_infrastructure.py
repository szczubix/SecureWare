"""Migracje, kolejka e-mail i inne elementy infrastruktury."""

from __future__ import annotations

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
    assert run_delivery(env.app) == 1
    assert sender.sent[0][0] == "alice@acme.example"
    assert "FW-1001" in sender.sent[0][1]
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
