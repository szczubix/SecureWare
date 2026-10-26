"""Support Access: prosby o dostep, zgody klienta i sesje wsparcia.

Rekordy nie sa nigdy usuwane ani ukrywane - historia dostepu jest zawsze
widoczna dla klienta.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from forvium.core.db import Base, new_id


class AccessMode(StrEnum):
    STANDARD = "standard"
    # Zarezerwowane dla przyszlej procedury Break Glass (patrz break_glass.py).
    BREAK_GLASS = "break_glass"


class AccessLevel(StrEnum):
    READ_ONLY = "READ_ONLY"


class ConsentBasis(StrEnum):
    CUSTOMER = "customer"  # zatwierdzenie konkretnej prosby przez klienta
    STANDING = "standing"  # automatycznie, na podstawie zgody stalej klienta
    BREAK_GLASS = "break_glass"  # procedura awaryjna (bez zgody klienta, 4 oczy po stronie Forvium)


class RequestStatus(StrEnum):
    PENDING = "pending"
    PENDING_SECOND_APPROVAL = "pending_second_approval"  # Break Glass
    PENDING_CUSTOMER_CONFIRMATION = "pending_customer_confirmation"  # zatwierdzanie przez dwie osoby
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"  # brak decyzji klienta w wyznaczonym czasie


class SessionStatus(StrEnum):
    ACTIVE = "active"
    ENDED = "ended"  # zakonczona przez operatora lub klienta
    EXPIRED = "expired"
    REVOKED = "revoked"  # cofniecie zgody / zablokowanie


class SupportAccessRequest(Base):
    __tablename__ = "support_access_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    mode: Mapped[str] = mapped_column(String(16), default=AccessMode.STANDARD)
    operator_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    reference_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    ticket_id: Mapped[str] = mapped_column(ForeignKey("support_tickets.id"))
    ticket_number: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(String(4000))
    requested_scopes: Mapped[list] = mapped_column(JSON)
    requested_duration_minutes: Mapped[int] = mapped_column(Integer)
    access_level: Mapped[str] = mapped_column(String(16), default=AccessLevel.READ_ONLY)
    status: Mapped[str] = mapped_column(String(32), default=RequestStatus.PENDING, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    decision_deadline: Mapped[datetime] = mapped_column(DateTime)
    decided_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decision_note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # Zatwierdzanie przez dwie osoby po stronie klienta
    first_approved_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    first_approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pending_grant: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Break Glass
    incident_category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    review_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(String(4000), nullable=True)


class SupportConsent(Base):
    """Zgoda klienta: organizacja, zakres i termin waznosci."""

    __tablename__ = "support_consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    request_id: Mapped[str] = mapped_column(ForeignKey("support_access_requests.id"), unique=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    operator_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    reference_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    granted_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    scopes: Mapped[list] = mapped_column(JSON)
    # None = wszystkie jednostki; w przeciwnym razie lista ID (wraz z poddrzewami)
    unit_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    access_level: Mapped[str] = mapped_column(String(16), default=AccessLevel.READ_ONLY)
    max_session_minutes: Mapped[int] = mapped_column(Integer)
    granted_at: Mapped[datetime] = mapped_column(DateTime)
    valid_until: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    basis: Mapped[str] = mapped_column(String(16), default=ConsentBasis.CUSTOMER)
    second_approver_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    standing_consent_id: Mapped[str | None] = mapped_column(ForeignKey("support_standing_consents.id"),
                                                            nullable=True, index=True)


class SupportStandingConsent(Base):
    """Zgoda stala: klient z gory zgadza sie na sesje w okreslonych granicach.

    Kazda prosba mieszczaca sie w granicach jest zatwierdzana automatycznie
    (klient i tak dostaje powiadomienie), a cofniecie zgody stalej konczy
    wszystkie wynikajace z niej zgody i sesje.
    """

    __tablename__ = "support_standing_consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    granted_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    scopes: Mapped[list] = mapped_column(JSON)
    unit_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    max_session_minutes: Mapped[int] = mapped_column(Integer)
    # None = kazda rola supportu; w przeciwnym razie lista PlatformRole
    allowed_platform_roles: Mapped[list | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    valid_until: Mapped[datetime] = mapped_column(DateTime)
    # Przy zatwierdzaniu przez dwie osoby zgoda stala dziala dopiero po potwierdzeniu.
    confirmed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class SupportSession(Base):
    """Odrebna sesja wsparcia. Nie jest sesja klienta ani sesja operatora."""

    __tablename__ = "support_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    operator_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    reference_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    consent_id: Mapped[str] = mapped_column(ForeignKey("support_consents.id"), index=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("support_access_requests.id"))
    ticket_id: Mapped[str] = mapped_column(ForeignKey("support_tickets.id"))
    ticket_number: Mapped[str] = mapped_column(String(32))
    access_level: Mapped[str] = mapped_column(String(16), default=AccessLevel.READ_ONLY)
    # Zamrozony w chwili startu zestaw uprawnien (lista Permission). Przy kazdym
    # zadaniu jest dodatkowo przeliczany i przecinany z biezacym stanem.
    permissions: Mapped[list] = mapped_column(JSON)
    scopes: Mapped[list] = mapped_column(JSON)
    unit_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    # Przedluzenia (ponowne MFA + powiadomienie klienta).
    extensions_count: Mapped[int] = mapped_column(Integer, default=0)
    original_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default=SessionStatus.ACTIVE, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    end_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Token sesji wsparcia (skrot). Wydawany dopiero po wymianie kodu startowego.
    token_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    # Jednorazowy kod przekazania do app.forvium.com (skrot) i jego waznosc.
    launch_code_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    launch_code_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
