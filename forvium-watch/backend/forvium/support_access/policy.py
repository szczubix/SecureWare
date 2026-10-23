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
    # Zgoda stala: maksymalna waznosc i waznosc pojedynczej zgody z niej wynikajacej.
    max_standing_consent_days: int = 365
    standing_grant_hours: int = 4
    # Przedluzanie sesji: maks. liczba przedluzen, dlugosc jednego i laczny limit czasu sesji.
    max_extensions: int = 2
    max_extension_minutes: int = 15
    max_total_session_minutes: int = 45


DEFAULT_POLICY = SupportAccessPolicy()
