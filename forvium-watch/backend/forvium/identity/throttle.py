"""Limity nieudanych prob (logowanie, MFA step-up, kody startowe, tokeny wsparcia).

Liczniki sa trzymane w bazie (dzialaja przy wielu instancjach API) i
zapisywane we wlasnej transakcji, bo zadanie z nieudana proba konczy sie
rollbackiem. Klucze sa przechowywane jako skroty, bez adresow e-mail i IP.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from forvium.audit.service import AuditLog
from forvium.core.clock import clock
from forvium.core.context import DomainError
from forvium.core.db import Base


class RateLimitBucket(Base):
    __tablename__ = "rate_limit_buckets"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(32))
    failures: Mapped[int] = mapped_column(Integer, default=0)
    window_started_at: Mapped[datetime] = mapped_column(DateTime)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


@dataclass(frozen=True)
class Rule:
    limit: int
    window: timedelta
    lockout: timedelta


RULES: dict[str, Rule] = {
    "login_account": Rule(5, timedelta(minutes=15), timedelta(minutes=15)),
    "login_ip": Rule(20, timedelta(minutes=15), timedelta(minutes=15)),
    "mfa_stepup": Rule(5, timedelta(minutes=15), timedelta(minutes=15)),
    "launch_ip": Rule(10, timedelta(minutes=15), timedelta(minutes=15)),
    "support_token_ip": Rule(30, timedelta(minutes=15), timedelta(minutes=15)),
    "activation_ip": Rule(10, timedelta(minutes=15), timedelta(minutes=15)),
}


def _key(kind: str, value: str) -> str:
    return hashlib.sha256(f"{kind}:{value.lower()}".encode()).hexdigest()


class Throttle:
    def __init__(self, session_factory: sessionmaker, audit: AuditLog) -> None:
        self._session_factory = session_factory
        self._audit = audit

    def _with_session(self, fn):
        session: Session = self._session_factory()
        try:
            result = fn(session)
            session.commit()
            return result
        finally:
            session.close()

    def check(self, kind: str, value: str | None, **audit_kwargs) -> None:
        """Podnosi 429, jesli klucz jest zablokowany."""
        if not value:
            return
        key = _key(kind, value)
        bucket = self._with_session(lambda s: s.get(RateLimitBucket, key))
        if bucket and bucket.locked_until and clock.now() < bucket.locked_until:
            self._audit.record("security.throttled", outcome="denied", details={"kind": kind}, **audit_kwargs)
            raise DomainError(429, "too_many_attempts", "Zbyt wiele nieudanych prób. Spróbuj ponownie później.")

    def fail(self, kind: str, value: str | None, **audit_kwargs) -> None:
        if not value:
            return
        rule = RULES[kind]
        key = _key(kind, value)
        now = clock.now()

        def update(s: Session) -> bool:
            bucket = s.get(RateLimitBucket, key)
            if bucket is None or now - bucket.window_started_at > rule.window:
                if bucket is None:
                    bucket = RateLimitBucket(key=key, kind=kind)
                    s.add(bucket)
                bucket.failures = 0
                bucket.window_started_at = now
                bucket.locked_until = None
            bucket.failures += 1
            if bucket.failures >= rule.limit:
                bucket.locked_until = now + rule.lockout
                return True
            return False

        if self._with_session(update):
            self._audit.record("security.lockout", outcome="denied",
                               details={"kind": kind, "lockout_minutes": int(rule.lockout.total_seconds() // 60)},
                               **audit_kwargs)

    def reset(self, kind: str, value: str | None) -> None:
        if not value:
            return
        key = _key(kind, value)

        def delete(s: Session) -> None:
            bucket = s.get(RateLimitBucket, key)
            if bucket is not None:
                s.delete(bucket)

        self._with_session(delete)
