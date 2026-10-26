"""Eksport Audit Log do zewnetrznego magazynu (poza baza aplikacji).

Proces w tle co `FORVIUM_AUDIT_EXPORT_INTERVAL_SECONDS` wysyla nowe zdarzenia do:

* pliku JSONL z lancuchem skrotow (`FORVIUM_AUDIT_EXPORT_PATH`) - np. wolumen
  WORM / bucket z object lock, zbierany dalej przez agenta logow,
* endpointu HTTP (`FORVIUM_AUDIT_EXPORT_URL`) - partie JSON podpisane
  naglowkiem `X-Forvium-Signature: sha256=<HMAC(body)>`,
* SIEM: Splunk HEC, Elastic (Bulk API, ECS) albo syslog RFC 5424 przez TLS/TCP
  (np. Wazuh) - patrz audit/siem.py.

Zdarzenie jest oznaczane jako wyeksportowane (`audit_exports`) dopiero, gdy
trafi do wszystkich skonfigurowanych miejsc. Ponowienie po bledzie moze
wyslac to samo zdarzenie drugi raz - odbiorca deduplikuje po `event.id`.
Eksportowane sa zdarzenia starsze niz kilka sekund, zeby nie pominac
transakcji zatwierdzanych w innej kolejnosci niz znaczniki czasu.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import urllib.request
from datetime import datetime, timedelta
from typing import Protocol

from sqlalchemy import DateTime, ForeignKey, String, select, text
from sqlalchemy.orm import Mapped, Session, mapped_column

from forvium.audit.chain import ChainedJsonlFile, event_dict
from forvium.audit.models import AuditEvent
from forvium.core.clock import clock
from forvium.core.db import Base

SETTLE = timedelta(seconds=10)
BATCH = 1000
_ADVISORY_LOCK_ID = 7_406_001  # jeden eksporter naraz na PostgreSQL


class AuditExport(Base):
    __tablename__ = "audit_exports"

    event_id: Mapped[str] = mapped_column(ForeignKey("audit_events.id"), primary_key=True)
    exported_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    chain_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AuditSink(Protocol):
    def send(self, events: list[dict]) -> str | None: ...


class FileSink:
    def __init__(self, path: str, key: bytes | None) -> None:
        self.file = ChainedJsonlFile(path, key)

    def send(self, events: list[dict]) -> str | None:
        return self.file.append(events)


class HttpSink:
    def __init__(self, url: str, key: bytes | None, timeout: int = 10) -> None:
        self.url = url
        self.key = key
        self.timeout = timeout

    def send(self, events: list[dict]) -> str | None:
        body = json.dumps({"source": "forvium-watch", "events": events}, default=str).encode()
        headers = {"Content-Type": "application/json"}
        if self.key:
            headers["X-Forvium-Signature"] = "sha256=" + hmac.new(self.key, body, hashlib.sha256).hexdigest()
        req = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 - URL z konfiguracji
            if resp.status >= 300:
                raise RuntimeError(f"HTTP {resp.status}")
        return None


def sinks_from_settings(settings) -> list[AuditSink]:
    key = settings.audit_export_hmac_key.encode() or None
    sinks: list[AuditSink] = []
    if settings.audit_export_url:
        sinks.append(HttpSink(settings.audit_export_url, key))
    if settings.audit_export_path:
        sinks.append(FileSink(settings.audit_export_path, key))
    from forvium.audit.siem import sink_from_settings

    siem = sink_from_settings(settings)
    if siem is not None:
        sinks.append(siem)
    return sinks


def export_pending(db: Session, sinks: list[AuditSink]) -> int:
    if not sinks:
        return 0
    if db.get_bind().dialect.name == "postgresql":
        if not db.scalar(text("SELECT pg_try_advisory_xact_lock(:id)"), {"id": _ADVISORY_LOCK_ID}):
            return 0  # inna instancja wlasnie eksportuje
    exported = select(AuditExport.event_id)
    events = list(db.scalars(
        select(AuditEvent)
        .where(AuditEvent.id.not_in(exported), AuditEvent.occurred_at < clock.now() - SETTLE)
        .order_by(AuditEvent.occurred_at, AuditEvent.id)
        .limit(BATCH)
    ))
    if not events:
        return 0
    payload = [event_dict(e) for e in events]
    last_hash = None
    for sink in sinks:
        last_hash = sink.send(payload) or last_hash
    now = clock.now()
    for i, e in enumerate(events):
        db.add(AuditExport(event_id=e.id, exported_at=now, chain_hash=last_hash if i == len(events) - 1 else None))
    return len(events)


def run_audit_export(app) -> int:
    db = app.state.db.sessionmaker()
    try:
        total = 0
        while True:
            n = export_pending(db, app.state.audit_sinks)
            db.commit()
            total += n
            if n < BATCH:
                return total
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
