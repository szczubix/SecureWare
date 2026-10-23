"""Identity & Access: konta, zwykle sesje klientow i operatorow."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from forvium.core.db import Base, new_id


class User(Base):
    """Konto. Operator Forvium to konto z rola platformowa (`platform_role`).

    Konto operatora jest zwyklym kontem w Identity & Access, ale jego sesje
    operatorskie (admin) i sesje wsparcia sa calkowicie odrebne od sesji
    klientow.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Ostatnio wykorzystany krok TOTP - ten sam kod nie zadziala drugi raz.
    mfa_last_step: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # None = zwykly klient. Wartosci: patrz platform_admin.rbac.PlatformRole
    platform_role: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class UserSession(Base):
    """Zwykla sesja: `kind` = "user" (app) albo "operator" (admin)."""

    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
