"""Organizations & RBAC: organizacje, jednostki, czlonkostwa i dane domenowe."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from forvium.core.crypto import EncryptedJSON
from forvium.core.i18n import default_lang
from forvium.core.db import Base, new_id


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200))
    subscription_plan: Mapped[str] = mapped_column(String(40), default="standard")
    # Konfiguracja i sekrety organizacji. Sekrety nigdy nie sa zwracane w trybie wsparcia.
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    # Pola z sekretami sa szyfrowane w bazie (core/crypto.py).
    smtp_config: Mapped[dict] = mapped_column(EncryptedJSON("organizations.smtp_config"), default=dict)
    webhooks: Mapped[list] = mapped_column(EncryptedJSON("organizations.webhooks"), default=list)
    secrets: Mapped[dict] = mapped_column(EncryptedJSON("organizations.secrets"), default=dict)
    # Dostep serwisowy wymaga zatwierdzenia przez dwie rozne osoby z organizacji.
    support_dual_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    # Wylaczenie tej ochrony tez wymaga drugiej osoby: kto zainicjowal wylaczenie.
    support_dual_approval_disable_requested_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # Domyslny jezyk czlonkow organizacji (powiadomienia, e-maile) i raportow dostepu.
    locale: Mapped[str] = mapped_column(String(5), default=default_lang, server_default="pl")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class OrgUnit(Base):
    """Jednostka organizacyjna (drzewo)."""

    __tablename__ = "org_units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200))


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("organization_id", "user_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))  # organizations.rbac.OrgRole


class Technology(Base):
    """Technologia wykryta w jednostce (inwentarz monitorowany przez Watch)."""

    __tablename__ = "technologies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    unit_id: Mapped[str] = mapped_column(ForeignKey("org_units.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[str] = mapped_column(String(64))
    cves: Mapped[list] = mapped_column(JSON, default=list)  # [{"id": "CVE-...", "severity": "high"}]


class DiagnosticEvent(Base):
    """Blad lub ostrzezenie konfiguracji widoczne w diagnostyce."""

    __tablename__ = "diagnostic_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    level: Mapped[str] = mapped_column(String(16))
    component: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime)
