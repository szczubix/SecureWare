"""Aktywacja kont linkiem z e-maila (nowi klienci i nowi operatorzy).

Forvium zaklada konto, ale nigdy nie zna hasla ani sekretu MFA uzytkownika:
jednorazowy link (waznosc 72 h) trafia wylacznie na adres e-mail konta - nie jest
zwracany operatorowi w API. Uzytkownik sam ustawia haslo i aplikacje
uwierzytelniajaca (sekret TOTP potwierdzony poprawnym kodem). Inaczej operator
zakladajacy konto klienta moglby sie na nie zalogowac z pominieciem zgody klienta.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pyotp
from sqlalchemy import DateTime, ForeignKey, String, select
from sqlalchemy.orm import Mapped, mapped_column

from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError
from forvium.core.crypto import EncryptedString
from forvium.core.db import Base, new_id
from forvium.core.security import hash_password, match_totp_step, new_token, new_totp_secret, token_digest
from forvium.identity.models import User

ACTIVATION_TTL = timedelta(hours=72)
MIN_PASSWORD_LENGTH = 12
TOKEN_PREFIX = "fwa_"


class AccountActivation(Base):
    __tablename__ = "account_activations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # "user" (app) | "operator" (admin)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    created_by: Mapped[str] = mapped_column(String(36))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Sekret TOTP przygotowany dla uzytkownika, zanim potwierdzi go kodem.
    pending_mfa_secret: Mapped[str | None] = mapped_column(EncryptedString("account_activations.pending_mfa_secret"),
                                                           nullable=True)


def unusable_password_hash() -> str:
    """Hash losowego hasla, ktorego nikt nie zna - konto przed aktywacja nie da sie zalogowac."""
    return hash_password(new_token("x"))


def issue(ctx: Ctx, user: User, *, kind: str, created_by: str, actor_type: str = "operator") -> None:
    """Nowy link aktywacyjny (poprzednie niewykorzystane przestaja dzialac), wyslany e-mailem."""
    if user.activated_at is not None:
        raise DomainError(409, "already_activated", "Konto jest już aktywne.")
    now = clock.now()
    for old in ctx.db.scalars(select(AccountActivation).where(AccountActivation.user_id == user.id,
                                                              AccountActivation.used_at.is_(None))):
        old.used_at = now
    token = new_token(TOKEN_PREFIX)
    ctx.db.add(AccountActivation(user_id=user.id, kind=kind, token_hash=token_digest(token), created_at=now,
                                 created_by=created_by, expires_at=now + ACTIVATION_TTL))
    origin = ctx.settings.admin_origin if kind == "operator" else ctx.settings.app_origin
    link = f"{origin}/activate.html#token={token}"
    panel = "panelu operatorów Forvium" if kind == "operator" else "Forvium Watch"
    # Tylko e-mail (bez kopii w powiadomieniu w aplikacji i bez zwracania linku w API).
    ctx.notifications.email_only(
        ctx.db, user, subject=f"Aktywuj konto w {panel}",
        body=(f"Dzień dobry {user.display_name},\n\nzałożono dla Ciebie konto w {panel}. Aby je aktywować, "
              f"otwórz link (ważny 72 godziny, jednorazowy) i ustaw hasło oraz aplikację uwierzytelniającą:\n\n"
              f"{link}\n\nJeśli nie spodziewasz się tej wiadomości, zignoruj ją."))
    ctx.audit.log(ctx.db, "identity.activation.issued", actor_user_id=created_by, actor_type=actor_type,
                  ip_address=ctx.ip, details={"user_id": user.id, "kind": kind})


def _load(ctx: Ctx, token: str, kind: str) -> tuple[AccountActivation, User]:
    ctx.throttle.check("activation_ip", ctx.ip, actor_type="anonymous", ip_address=ctx.ip)
    activation = ctx.db.scalar(select(AccountActivation).where(AccountActivation.token_hash == token_digest(token or "")))
    user = ctx.db.get(User, activation.user_id) if activation else None
    if (activation is None or user is None or activation.kind != kind or activation.used_at is not None
            or clock.now() >= activation.expires_at or user.activated_at is not None or user.blocked_at is not None):
        ctx.audit.record("identity.activation", outcome="denied", actor_type="anonymous", ip_address=ctx.ip,
                         details={"reason": "invalid_token"})
        ctx.throttle.fail("activation_ip", ctx.ip, actor_type="anonymous", ip_address=ctx.ip)
        raise DomainError(404, "activation_invalid", "Link aktywacyjny jest nieprawidłowy, wykorzystany albo wygasł.")
    return activation, user


def info(ctx: Ctx, token: str, kind: str) -> dict:
    activation, user = _load(ctx, token, kind)
    if not activation.pending_mfa_secret:
        activation.pending_mfa_secret = new_totp_secret()
    issuer = "Forvium Admin" if kind == "operator" else "Forvium Watch"
    uri = pyotp.TOTP(activation.pending_mfa_secret).provisioning_uri(name=user.email, issuer_name=issuer)
    return {"email": user.email, "display_name": user.display_name, "mfa_secret": activation.pending_mfa_secret,
            "otpauth_uri": uri, "expires_at": activation.expires_at.isoformat() + "Z",
            "min_password_length": MIN_PASSWORD_LENGTH}


def complete(ctx: Ctx, token: str, kind: str, password: str, mfa_code: str) -> None:
    activation, user = _load(ctx, token, kind)
    if len(password or "") < MIN_PASSWORD_LENGTH or (password or "").lower() in user.email.lower():
        raise DomainError(422, "password_too_weak",
                          f"Hasło musi mieć co najmniej {MIN_PASSWORD_LENGTH} znaków i nie może zawierać adresu e-mail.")
    step = match_totp_step(activation.pending_mfa_secret, mfa_code, clock.now())
    if step is None:
        ctx.audit.record("identity.activation", outcome="denied", actor_user_id=user.id, actor_type="anonymous",
                         ip_address=ctx.ip, details={"reason": "invalid_mfa_code"})
        ctx.throttle.fail("activation_ip", ctx.ip, actor_type="anonymous", ip_address=ctx.ip)
        raise DomainError(422, "mfa_code_invalid", "Kod z aplikacji uwierzytelniającej jest nieprawidłowy.")
    now = clock.now()
    user.password_hash = hash_password(password)
    user.mfa_secret = activation.pending_mfa_secret
    user.mfa_last_step = step
    user.activated_at = now
    user.is_active = True
    activation.used_at = now
    activation.pending_mfa_secret = None
    ctx.audit.log(ctx.db, "identity.activation.completed", actor_user_id=user.id,
                  actor_type="operator" if kind == "operator" else "user", ip_address=ctx.ip,
                  details={"kind": kind})
