"""Polityka standardowego dostepu serwisowego."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SupportAccessPolicy:
    default_session_minutes: int = 15
    max_session_minutes: int = 15
    # Ile czasu klient ma na decyzje, zanim prosba wygasnie.
    decision_window_hours: int = 72
    # Domyslna i maksymalna waznosc zgody udzielonej przez klienta.
    default_consent_hours: int = 24
    max_consent_hours: int = 7 * 24
    # Waznosc jednorazowego kodu przekazania sesji do app.forvium.com.
    launch_code_seconds: int = 60
    min_reason_length: int = 15


DEFAULT_POLICY = SupportAccessPolicy()
