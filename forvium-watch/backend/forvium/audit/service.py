"""Zapis audytu.

* `log(db, ...)` - zdarzenia udanych operacji zapisywane w tej samej
  transakcji co zmiana (nie ma zmiany bez wpisu i wpisu bez zmiany).
* `record(...)` - odmowy, nieudane proby i operacje API zapisywane we WLASNEJ
  transakcji, wiec przetrwaja rollback odrzuconego zadania.

Do `details` trafiaja wylacznie metadane. Klucze wygladajace na poufne sa
maskowane, a wartosci tekstowe obcinane, by nie przeniesc do logu tresci danych.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from forvium.audit.chain import ChainedJsonlFile, event_dict
from forvium.audit.models import AuditEvent
from forvium.core.clock import clock
from forvium.core.db import new_id

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
    def __init__(self, session_factory: sessionmaker, break_glass_sink: ChainedJsonlFile | None = None) -> None:
        self._session_factory = session_factory
        self._break_glass_sink = break_glass_sink
        self._mode_cache: dict[str, bool] = {}

    def log(self, db: Session, action: str, **kwargs: Any) -> None:
        """Zdarzenie w transakcji biznesowej: zapisane wtedy i tylko wtedy, gdy zmiana."""
        event = self._event(action, **kwargs)
        event.is_break_glass = self._is_break_glass(db, event)
        db.add(event)
        self._mirror(event)

    def independent_session(self) -> Session:
        """Sesja z puli pomocniczej (niezalezne transakcje w trakcie zadania)."""
        return self._session_factory()

    def record(self, action: str, **kwargs: Any) -> None:
        """Zdarzenie w niezaleznej transakcji (odmowy, nieudane proby, operacje API)."""
        session: Session = self._session_factory()
        try:
            event = self._event(action, **kwargs)
            event.is_break_glass = self._is_break_glass(session, event)
            session.add(event)
            session.commit()
        finally:
            session.close()
        self._mirror(event)

    def _is_break_glass(self, db: Session, event: AuditEvent) -> bool:
        """Oznaczenie wyznaczane z trybu prosby - wywolujacy nie moze go pominac."""
        if event.action.startswith("break_glass."):
            return True
        from forvium.support_access.models import AccessMode, SupportAccessRequest, SupportSession

        request_id = event.support_request_id
        if not request_id and event.support_session_id:
            session = db.get(SupportSession, event.support_session_id)
            request_id = session.request_id if session else None
        if not request_id:
            return False
        if request_id not in self._mode_cache:
            req = db.get(SupportAccessRequest, request_id)
            if req is None:
                return False
            if len(self._mode_cache) > 10_000:
                self._mode_cache.clear()
            self._mode_cache[request_id] = req.mode == AccessMode.BREAK_GLASS
        return self._mode_cache[request_id]

    def _mirror(self, event: AuditEvent) -> None:
        """Niezalezny strumien Break Glass (osobny plik z lancuchem skrotow)."""
        if event.is_break_glass and self._break_glass_sink is not None:
            if event.id is None:
                event.id = new_id()
            self._break_glass_sink.append([event_dict(event)])

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
            id=new_id(),
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

    def query(self, db: Session, f: AuditFilter, *, limit: int = 100, offset: int = 0) -> tuple[list[AuditEvent], int]:
        stmt = select(AuditEvent)
        if f.organization_id:
            stmt = stmt.where(AuditEvent.organization_id == f.organization_id)
        if f.support_session_id:
            stmt = stmt.where(AuditEvent.support_session_id == f.support_session_id)
        if f.support_request_id:
            stmt = stmt.where(AuditEvent.support_request_id == f.support_request_id)
        if f.actor_user_id:
            stmt = stmt.where(AuditEvent.actor_user_id == f.actor_user_id)
        if f.action_prefix:
            stmt = stmt.where(AuditEvent.action.startswith(f.action_prefix))
        if f.outcome:
            stmt = stmt.where(AuditEvent.outcome == f.outcome)
        if f.break_glass is not None:
            stmt = stmt.where(AuditEvent.is_break_glass.is_(f.break_glass))
        if f.since:
            stmt = stmt.where(AuditEvent.occurred_at >= f.since)
        if f.until:
            stmt = stmt.where(AuditEvent.occurred_at < f.until)
        if f.ticket_number:
            from forvium.support_access.models import SupportAccessRequest

            stmt = stmt.where(AuditEvent.support_request_id.in_(
                select(SupportAccessRequest.id).where(SupportAccessRequest.ticket_number == f.ticket_number)))
        total = db.scalar(select(func.count()).select_from(stmt.subquery()))
        rows = db.scalars(stmt.order_by(AuditEvent.occurred_at.desc(), AuditEvent.id).limit(limit).offset(offset))
        return list(rows), total or 0


@dataclass
class AuditFilter:
    organization_id: str | None = None
    support_session_id: str | None = None
    support_request_id: str | None = None
    actor_user_id: str | None = None
    ticket_number: str | None = None
    action_prefix: str | None = None
    outcome: str | None = None
    break_glass: bool | None = None
    since: datetime | None = None
    until: datetime | None = None
