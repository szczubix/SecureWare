"""Podglad na zywo i nagrywanie sesji wsparcia (zrzuty widoku).

W trybie wsparcia frontend app.forvium.com po kazdym wyrenderowanym widoku
wysyla zrzut DOM (`POST /api/app/support/session/snapshot`). Zrzut:

* jest sanityzowany po stronie serwera (biala lista, bez skryptow, linkow,
  wartosci pol formularzy),
* zawiera dane klienta, wiec jest szyfrowany w bazie (jak sekrety) i
  usuwany po `retention_days`,
* jest widoczny dla klienta na zywo i jako nagranie po zakonczeniu sesji,
  a po stronie Forvium tylko dla rol z `platform.audit.read` (przeglady,
  reklamacje) - kazde takie otwarcie trafia do audytu.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, delete, func, select
from sqlalchemy.orm import Mapped, mapped_column

from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError
from forvium.core.crypto import EncryptedString
from forvium.core.db import Base, new_id
from forvium.security.html_sanitizer import sanitize_html
from forvium.support_access.models import SessionStatus, SupportSession


@dataclass(frozen=True)
class RecordingPolicy:
    max_snapshot_bytes: int = 300_000
    max_snapshots_per_session: int = 500
    min_interval_seconds: float = 0.5
    retention_days: int = 30


class SupportSessionSnapshot(Base):
    __tablename__ = "support_session_snapshots"
    __table_args__ = (UniqueConstraint("session_id", "seq"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("support_sessions.id"), index=True)
    organization_id: Mapped[str] = mapped_column(String(36), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    view: Mapped[str] = mapped_column(String(100))
    captured_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    size: Mapped[int] = mapped_column(Integer)
    html: Mapped[str] = mapped_column(EncryptedString("support_session_snapshots.html"))


def store_snapshot(ctx: Ctx, policy: RecordingPolicy, session: SupportSession, view: str, html: str) -> dict:
    clean = sanitize_html(html)
    size = len(clean.encode())
    if size > policy.max_snapshot_bytes:
        raise DomainError(413, "snapshot_too_large", "Zrzut widoku jest zbyt duży.")
    last = ctx.db.execute(
        select(func.count(SupportSessionSnapshot.id), func.max(SupportSessionSnapshot.seq),
               func.max(SupportSessionSnapshot.captured_at))
        .where(SupportSessionSnapshot.session_id == session.id)
    ).one()
    count, max_seq, last_at = last
    if count >= policy.max_snapshots_per_session:
        raise DomainError(429, "snapshot_limit", "Osiągnięto limit zrzutów w tej sesji.")
    now = clock.now()
    if last_at and (now - last_at).total_seconds() < policy.min_interval_seconds:
        raise DomainError(429, "snapshot_rate", "Zbyt częste zrzuty.")
    snap = SupportSessionSnapshot(session_id=session.id, organization_id=session.organization_id,
                                  seq=(max_seq or 0) + 1, view=(view or "")[:100], captured_at=now, size=size,
                                  html=clean)
    ctx.db.add(snap)
    return {"seq": snap.seq, "size": size}


def _session_for_org(ctx: Ctx, organization_id: str, session_id: str) -> SupportSession:
    session = ctx.db.get(SupportSession, session_id)
    if session is None or session.organization_id != organization_id:
        raise DomainError(404, "session_not_found", "Nie znaleziono sesji.")
    return session


def _snapshot_out(s: SupportSessionSnapshot, with_html: bool) -> dict:
    out = {"seq": s.seq, "view": s.view, "captured_at": s.captured_at.isoformat() + "Z", "size": s.size}
    if with_html:
        out["html"] = s.html
    return out


def live_view(ctx: Ctx, organization_id: str, session_id: str, after_seq: int) -> dict:
    """Stan sesji dla podgladu klienta: najnowszy zrzut (jesli nowszy niz `after_seq`) i ostatnie operacje."""
    from forvium.audit.models import AuditEvent
    from forvium.support_access.service import remaining_seconds

    session = _session_for_org(ctx, organization_id, session_id)
    latest = ctx.db.scalar(select(SupportSessionSnapshot).where(SupportSessionSnapshot.session_id == session.id)
                           .order_by(SupportSessionSnapshot.seq.desc()).limit(1))
    events = ctx.db.scalars(select(AuditEvent).where(AuditEvent.support_session_id == session.id,
                                                     AuditEvent.action == "support.api_call",
                                                     AuditEvent.route != "/api/app/support/session/snapshot")
                            .order_by(AuditEvent.occurred_at.desc()).limit(15))
    active = session.status == SessionStatus.ACTIVE and clock.now() < session.expires_at
    return {
        "session_id": session.id,
        "status": session.status if not (session.status == SessionStatus.ACTIVE and not active) else "expired",
        "active": active,
        "operator_id": session.operator_user_id,
        "remaining_seconds": remaining_seconds(session) if active else 0,
        "current_view": latest.view if latest else None,
        "snapshot": _snapshot_out(latest, True) if latest and latest.seq > after_seq else None,
        "latest_seq": latest.seq if latest else 0,
        "activity": [{"occurred_at": e.occurred_at.isoformat() + "Z", "method": e.http_method, "route": e.route,
                      "outcome": e.outcome} for e in events],
    }


def recording_index(ctx: Ctx, organization_id: str | None, session_id: str) -> list[dict]:
    session = ctx.db.get(SupportSession, session_id)
    if session is None or (organization_id and session.organization_id != organization_id):
        raise DomainError(404, "session_not_found", "Nie znaleziono sesji.")
    return [_snapshot_out(s, False) for s in ctx.db.scalars(
        select(SupportSessionSnapshot).where(SupportSessionSnapshot.session_id == session_id)
        .order_by(SupportSessionSnapshot.seq))]


def recording_frame(ctx: Ctx, organization_id: str | None, session_id: str, seq: int) -> dict:
    session = ctx.db.get(SupportSession, session_id)
    if session is None or (organization_id and session.organization_id != organization_id):
        raise DomainError(404, "session_not_found", "Nie znaleziono sesji.")
    snap = ctx.db.scalar(select(SupportSessionSnapshot).where(SupportSessionSnapshot.session_id == session_id,
                                                              SupportSessionSnapshot.seq == seq))
    if snap is None:
        raise DomainError(404, "snapshot_not_found", "Nie znaleziono zrzutu.")
    return _snapshot_out(snap, True)


def purge_expired(ctx: Ctx, policy: RecordingPolicy) -> int:
    cutoff = clock.now() - timedelta(days=policy.retention_days)
    result = ctx.db.execute(delete(SupportSessionSnapshot).where(SupportSessionSnapshot.captured_at < cutoff))
    if result.rowcount:
        ctx.audit.log(ctx.db, "support.recording.purged", actor_type="system",
                      details={"snapshots": result.rowcount, "retention_days": policy.retention_days})
    return result.rowcount or 0
