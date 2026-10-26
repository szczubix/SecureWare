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

    # Zadania w tle w procesie API (lokalnie). W Compose/produkcji: false + osobny kontener worker.
    run_background_jobs: bool = field(default_factory=lambda: _env("RUN_BACKGROUND_JOBS", "true") == "true")
    # Logi: "json" (produkcja, zbieranie przez Loki/ELK) albo "text".
    log_format: str = field(default_factory=lambda: _env("LOG_FORMAT", "text"))
    # Sprawdzanie, czy sa raporty dostepu za poprzedni miesiac do utworzenia (0 = wylaczone).
    report_interval_seconds: int = field(default_factory=lambda: int(_env("REPORT_INTERVAL_SECONDS", "3600")))
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))
    # Opcjonalny token dla /metrics (poza tym endpoint jest dostepny tylko w sieci wewnetrznej).
    metrics_token: str = field(default_factory=lambda: _env("METRICS_TOKEN", ""))

    # Co ile sekund wygaszac sesje wsparcia w tle (0 = wylaczone).
    support_sweep_interval_seconds: int = field(
        default_factory=lambda: int(_env("SUPPORT_SWEEP_INTERVAL_SECONDS", "60"))
    )
    # Co ile sekund uruchamiac wykrywanie anomalii (0 = wylaczone).
    anomaly_interval_seconds: int = field(default_factory=lambda: int(_env("ANOMALY_INTERVAL_SECONDS", "60")))
    # Co ile sekund wysylac kolejke e-mail (0 = wylaczone).
    email_interval_seconds: int = field(default_factory=lambda: int(_env("EMAIL_INTERVAL_SECONDS", "15")))

    # Platformowy SMTP Forvium (powiadomienia). Brak hosta = e-maile tylko logowane.
    smtp_host: str = field(default_factory=lambda: _env("SMTP_HOST", ""))
    smtp_port: int = field(default_factory=lambda: int(_env("SMTP_PORT", "587")))
    smtp_username: str = field(default_factory=lambda: _env("SMTP_USERNAME", ""))
    smtp_password: str = field(default_factory=lambda: _env("SMTP_PASSWORD", ""), repr=False)
    smtp_from: str = field(default_factory=lambda: _env("SMTP_FROM", "Forvium Watch <no-reply@forvium.com>"))
    smtp_starttls: bool = field(default_factory=lambda: _env("SMTP_STARTTLS", "true") == "true")

    # Break Glass (domyslnie wylaczony) - patrz support_access/break_glass.py
    break_glass_enabled: bool = field(default_factory=lambda: _env("BREAK_GLASS_ENABLED", "false") == "true")
    security_team_emails: list[str] = field(
        default_factory=lambda: [e.strip() for e in _env("SECURITY_TEAM_EMAILS", "").split(",") if e.strip()]
    )
    # Niezalezny, lancuchowo podpisany strumien zdarzen Break Glass (JSONL).
    break_glass_audit_path: str = field(default_factory=lambda: _env("BREAK_GLASS_AUDIT_PATH", ""))

    # Eksport calego audytu do zewnetrznego magazynu (plik JSONL i/lub HTTP, np. SIEM).
    audit_export_path: str = field(default_factory=lambda: _env("AUDIT_EXPORT_PATH", ""))
    audit_export_url: str = field(default_factory=lambda: _env("AUDIT_EXPORT_URL", ""))
    audit_export_hmac_key: str = field(default_factory=lambda: _env("AUDIT_EXPORT_HMAC_KEY", ""), repr=False)
    # SIEM (audit/siem.py): splunk | elastic | syslog
    audit_siem_type: str = field(default_factory=lambda: _env("AUDIT_SIEM_TYPE", ""))
    audit_siem_url: str = field(default_factory=lambda: _env("AUDIT_SIEM_URL", ""))
    audit_siem_token: str = field(default_factory=lambda: _env("AUDIT_SIEM_TOKEN", ""), repr=False)
    audit_siem_index: str = field(default_factory=lambda: _env("AUDIT_SIEM_INDEX", ""))
    audit_siem_ca_file: str = field(default_factory=lambda: _env("AUDIT_SIEM_CA_FILE", ""))
    audit_export_interval_seconds: int = field(
        default_factory=lambda: int(_env("AUDIT_EXPORT_INTERVAL_SECONDS", "30"))
    )

    # Szyfrowanie danych w spoczynku - patrz core/crypto.py
    data_keys: str = field(default_factory=lambda: _env("DATA_KEYS", ""), repr=False)
    data_key_id: str = field(default_factory=lambda: _env("DATA_KEY_ID", ""))
    data_keys_wrapped: str = field(default_factory=lambda: _env("DATA_KEYS_WRAPPED", ""))
    vault_addr: str = field(default_factory=lambda: _env("VAULT_ADDR", ""))
    vault_token: str = field(default_factory=lambda: _env("VAULT_TOKEN", ""), repr=False)
    vault_transit_key: str = field(default_factory=lambda: _env("VAULT_TRANSIT_KEY", "forvium-data"))
    allow_insecure_dev_key: bool = field(
        default_factory=lambda: _env("ALLOW_INSECURE_DEV_KEY", "false") == "true")

    # WebAuthn: identyfikator RP (domyslnie host panelu admin); origin = ADMIN_ORIGIN.
    webauthn_rp_id: str = field(default_factory=lambda: _env("WEBAUTHN_RP_ID", ""))
    # Operator z zarejestrowanym kluczem loguje sie tylko kluczem (odporne na phishing), nie kodem TOTP.
    operator_login_webauthn_only: bool = field(
        default_factory=lambda: _env("OPERATOR_LOGIN_WEBAUTHN_ONLY", "false") == "true")

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
