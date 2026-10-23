"""Zapis audytu.

* `log(db, ...)` - zdarzenia udanych operacji zapisywane w tej samej
  transakcji co zmiana (nie ma zmiany bez wpisu i wpisu bez zmiany).
* `record(...)` - odmowy, nieudane proby i operacje API zapisywane we WLASNEJ
  transakcji, wiec przetrwaja rollback odrzuconego zadania.

Do `details` trafiaja wylacznie metadane. Klucze wygladajace na poufne sa
maskowane, a wartosci tekstowe obcinane, by nie przeniesc do logu tresci danych.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from forvium.audit.models import AuditEvent
from forvium.core.clock import clock

_SENSITIVE_MARKERS = (
    "password",
    "passwd",
    "secret",
    "token",
    "mfa",
    "otp",
    "totp",
    "code",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "smtp",
    "webhook",
)
_MAX_VALUE_LEN = 200
REDACTED = "[REDACTED]"


def sanitize(value: Any, depth: int = 0) -> Any:
    if depth > 4:
        return REDACTED
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            key = str(k)
            if any(marker in key.lower() for marker in _SENSITIVE_MARKERS):
                out[key] = REDACTED
            else:
                out[key] = sanitize(v, depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        return [sanitize(v, depth + 1) for v in list(value)[:50]]
    if isinstance(value, str):
        return value[:_MAX_VALUE_LEN]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:_MAX_VALUE_LEN]


class AuditLog:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def log(self, db: Session, action: str, **kwargs: Any) -> None:
        """Zdarzenie w transakcji biznesowej: zapisane wtedy i tylko wtedy, gdy zmiana."""
        db.add(self._event(action, **kwargs))

    def record(self, action: str, **kwargs: Any) -> None:
        """Zdarzenie w niezaleznej transakcji (odmowy, nieudane proby, operacje API)."""
        session: Session = self._session_factory()
        try:
            session.add(self._event(action, **kwargs))
            session.commit()
        finally:
            session.close()

    @staticmethod
    def _event(
        action: str,
        *,
        outcome: str = "success",
        actor_user_id: str | None = None,
        actor_type: str = "system",
        on_behalf_of_user_id: str | None = None,
        organization_id: str | None = None,
        support_session_id: str | None = None,
        support_request_id: str | None = None,
        http_method: str | None = None,
        route: str | None = None,
        status_code: int | None = None,
        ip_address: str | None = None,
        details: dict | None = None,
    ) -> AuditEvent:
        return AuditEvent(
            occurred_at=clock.now(),
            action=action,
            outcome=outcome,
            actor_user_id=actor_user_id,
            actor_type=actor_type,
            on_behalf_of_user_id=on_behalf_of_user_id,
            organization_id=organization_id,
            support_session_id=support_session_id,
            support_request_id=support_request_id,
            http_method=http_method,
            route=route,
            status_code=status_code,
            ip_address=ip_address,
            details=sanitize(details or {}),
        )

    def query(
        self,
        db: Session,
        *,
        organization_id: str | None = None,
        support_session_id: str | None = None,
        action_prefix: str | None = None,
        limit: int = 500,
    ) -> list[AuditEvent]:
        stmt = select(AuditEvent).order_by(AuditEvent.occurred_at.desc(), AuditEvent.id)
        if organization_id:
            stmt = stmt.where(AuditEvent.organization_id == organization_id)
        if support_session_id:
            stmt = stmt.where(AuditEvent.support_session_id == support_session_id)
        if action_prefix:
            stmt = stmt.where(AuditEvent.action.startswith(action_prefix))
        return list(db.scalars(stmt.limit(limit)))
