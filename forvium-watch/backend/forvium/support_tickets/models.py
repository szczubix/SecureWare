"""Support Tickets: zgloszenia supportowe, do ktorych przypinany jest dostep serwisowy."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from forvium.core.crypto import EncryptedString
from forvium.core.db import Base, new_id


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class TicketPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    number: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # np. FW-1042
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    reporter_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(16), default=TicketStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    priority: Mapped[str] = mapped_column(String(16), default=TicketPriority.NORMAL)
    # Opis od klienta moze zawierac dane wrazliwe - szyfrowany w bazie.
    description: Mapped[str | None] = mapped_column(EncryptedString("support_tickets.description"), nullable=True)
    created_by_customer: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SupportTicketMessage(Base):
    """Wiadomosc w zgloszeniu. `internal` = notatka Forvium niewidoczna dla klienta."""

    __tablename__ = "support_ticket_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("support_tickets.id"), index=True)
    organization_id: Mapped[str] = mapped_column(String(36), index=True)  # RLS
    author_user_id: Mapped[str] = mapped_column(String(36))
    author_side: Mapped[str] = mapped_column(String(16))  # "customer" | "forvium"
    internal: Mapped[bool] = mapped_column(Boolean, default=False)
    body: Mapped[str] = mapped_column(EncryptedString("support_ticket_messages.body"))
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
