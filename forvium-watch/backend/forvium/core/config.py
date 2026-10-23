"""Konfiguracja aplikacji (zmienne srodowiskowe z prefiksem FORVIUM_)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name: str, default: str) -> str:
    return os.environ.get(f"FORVIUM_{name}", default)


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=lambda: _env("DATABASE_URL", "sqlite:///./forvium.db"))
    admin_origin: str = field(default_factory=lambda: _env("ADMIN_ORIGIN", "https://admin.forvium.com"))
    app_origin: str = field(default_factory=lambda: _env("APP_ORIGIN", "https://app.forvium.com"))

    # Schemat bazy zarzadzany jest migracjami Alembic (`alembic upgrade head`).
    # create_all tylko w testach / szybkim dev.
    auto_create_schema: bool = field(default_factory=lambda: _env("AUTO_CREATE_SCHEMA", "false") == "true")

    # Co ile sekund wygaszac sesje wsparcia w tle (0 = wylaczone).
    support_sweep_interval_seconds: int = field(
        default_factory=lambda: int(_env("SUPPORT_SWEEP_INTERVAL_SECONDS", "60"))
    )
    # Co ile sekund wysylac kolejke e-mail (0 = wylaczone).
    email_interval_seconds: int = field(default_factory=lambda: int(_env("EMAIL_INTERVAL_SECONDS", "15")))

    # Platformowy SMTP Forvium (powiadomienia). Brak hosta = e-maile tylko logowane.
    smtp_host: str = field(default_factory=lambda: _env("SMTP_HOST", ""))
    smtp_port: int = field(default_factory=lambda: int(_env("SMTP_PORT", "587")))
    smtp_username: str = field(default_factory=lambda: _env("SMTP_USERNAME", ""))
    smtp_password: str = field(default_factory=lambda: _env("SMTP_PASSWORD", ""), repr=False)
    smtp_from: str = field(default_factory=lambda: _env("SMTP_FROM", "Forvium Watch <no-reply@forvium.com>"))
    smtp_starttls: bool = field(default_factory=lambda: _env("SMTP_STARTTLS", "true") == "true")

    # Zwykle sesje
    user_session_ttl_minutes: int = 12 * 60
    operator_session_ttl_minutes: int = 8 * 60

    # Ponowna weryfikacja MFA operatora (step-up) jest wymagana przy kazdej
    # operacji Support Access; kod TOTP jest sprawdzany w tym samym zadaniu.
    totp_valid_window: int = 1

    @property
    def cors_origins(self) -> list[str]:
        return [self.admin_origin, self.app_origin]


def get_settings() -> Settings:
    return Settings()
