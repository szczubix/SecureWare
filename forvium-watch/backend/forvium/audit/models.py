"""Audit Log: niezmienialny dziennik zdarzen bezpieczenstwa."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from forvium.core.db import Base, new_id


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    outcome: Mapped[str] = mapped_column(String(16))  # success | denied | failure
    # Tozsamosc rzeczywista (kto wykonal) i referencyjna (w czyim kontekscie).
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    actor_type: Mapped[str] = mapped_column(String(16))  # user | operator | support | system | anonymous
    on_behalf_of_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    support_session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    support_request_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    # Zdarzenie procedury Break Glass (ustawiane automatycznie na podstawie trybu prosby).
    is_break_glass: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    # Dla operacji API: metoda + szablon trasy (bez wartosci parametrow i bez tresci)
    http_method: Mapped[str | None] = mapped_column(String(8), nullable=True)
    route: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status_code: Mapped[int | None] = mapped_column(nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
