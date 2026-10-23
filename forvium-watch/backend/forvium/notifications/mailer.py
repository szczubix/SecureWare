"""Wysylka kolejki e-mail (`email_outbox`).

Platformowy SMTP Forvium konfigurowany jest zmiennymi `FORVIUM_SMTP_*`; to nie
jest SMTP organizacji klienta. Bez `FORVIUM_SMTP_HOST` wiadomosci sa tylko
logowane (tryb dev).
"""

from __future__ import annotations

import logging
import smtplib
from datetime import timedelta
from email.message import EmailMessage
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from forvium.core.clock import clock
from forvium.core.config import Settings
from forvium.notifications.models import EmailOutbox

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5


class EmailSender(Protocol):
    def send(self, to_address: str, subject: str, body: str) -> None: ...


class SmtpSender:
    def __init__(self, settings: Settings) -> None:
        self.s = settings

    def send(self, to_address: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = self.s.smtp_from
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(self.s.smtp_host, self.s.smtp_port, timeout=15) as smtp:
            if self.s.smtp_starttls:
                smtp.starttls()
            if self.s.smtp_username:
                smtp.login(self.s.smtp_username, self.s.smtp_password)
            smtp.send_message(msg)


class LogSender:
    """Tryb dev: zapisuje tylko odbiorce i temat."""

    def send(self, to_address: str, subject: str, body: str) -> None:
        logger.info("E-mail (dev, niewysłany) do %s: %s", to_address, subject)


def sender_from_settings(settings: Settings) -> EmailSender:
    return SmtpSender(settings) if settings.smtp_host else LogSender()


def _backoff(attempts: int) -> timedelta:
    return timedelta(minutes=min(60, 2 ** attempts))


def run_delivery(app) -> int:
    db = app.state.db.sessionmaker()
    try:
        sent = deliver_pending(db, app.state.email_sender)
        db.commit()
        return sent
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def deliver_pending(db: Session, sender: EmailSender, batch_size: int = 50) -> int:
    """Wysyla oczekujace wiadomosci; zwraca liczbe wyslanych.

    Na PostgreSQL wiersze sa blokowane `FOR UPDATE SKIP LOCKED`, wiec kilka
    instancji API moze dzialac rownolegle bez podwojnej wysylki.
    """
    now = clock.now()
    stmt = (
        select(EmailOutbox)
        .where(
            EmailOutbox.sent_at.is_(None),
            EmailOutbox.failed_at.is_(None),
            (EmailOutbox.next_attempt_at.is_(None)) | (EmailOutbox.next_attempt_at <= now),
        )
        .order_by(EmailOutbox.created_at)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    sent = 0
    for msg in db.scalars(stmt):
        try:
            sender.send(msg.to_address, msg.subject, msg.body)
        except Exception as exc:  # noqa: BLE001 - kazdy blad wysylki to ponowienie
            msg.attempts += 1
            msg.last_error = type(exc).__name__[:200]
            if msg.attempts >= MAX_ATTEMPTS:
                msg.failed_at = now
                logger.error("E-mail %s nie został wysłany po %s próbach", msg.id, msg.attempts)
            else:
                msg.next_attempt_at = now + _backoff(msg.attempts)
            continue
        msg.attempts += 1
        msg.sent_at = now
        msg.last_error = None
        sent += 1
    return sent
