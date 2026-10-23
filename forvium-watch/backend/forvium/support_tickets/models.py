"""Support Tickets: zgloszenia supportowe, do ktorych przypinany jest dostep serwisowy."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from forvium.core.db import Base, new_id


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    number: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # np. FW-1042
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    reporter_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(16), default=TicketStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime)
