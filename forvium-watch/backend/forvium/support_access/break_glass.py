"""Break Glass - awaryjny dostep serwisowy bez zgody klienta.

Domyslnie WYLACZONY (`FORVIUM_BREAK_GLASS_ENABLED=false`). Po wlaczeniu:

* osobna polityka (`BreakGlassPolicy`) - wlasne limity czasu i wymagania,
* szczegolowe uzasadnienie (min. 200 znakow) i kategoria incydentu,
* silna autoryzacja: MFA wnioskujacego operatora (SUPPORT_L2 / SUPPORT_LEAD)
  ORAZ zatwierdzenie drugiej osoby - oficera bezpieczenstwa - z jego MFA
  (zasada czterech oczu; nikt nie zatwierdza wlasnego wniosku),
* krotki czas: sesja do 30 min, zgoda awaryjna wazna 2 h, wniosek bez
  zatwierdzenia wygasa po 1 h,
* natychmiastowe powiadomienia: oficerowie bezpieczenstwa i adresy zespolu
  bezpieczenstwa przy wniosku; klient (w aplikacji i e-mailem) przy
  zatwierdzeniu, starcie i zakonczeniu sesji. Klient moze zakonczyc sesje i
  cofnac zgode awaryjna jak kazda inna,
* niezalezny audyt: wszystkie zdarzenia Break Glass (takze kazda operacja API
  w sesji awaryjnej) sa oznaczane `is_break_glass` i dodatkowo zapisywane do
  osobnego, lancuchowo podpisanego strumienia (`FORVIUM_BREAK_GLASS_AUDIT_PATH`),
* obowiazkowy przeglad po incydencie (`BREAK_GLASS_REVIEW`, inna osoba niz
  wnioskujacy), z podsumowaniem wyslanym do klienta.

Sesja awaryjna pozostaje READ_ONLY i podlega tym samym kontrolom RBAC, co
standardowa.

Ograniczenie: MFA to TOTP. Klucze sprzetowe (WebAuthn) wymagaja osobnej
implementacji - `requires_hardware_mfa=True` blokuje procedure, dopoki jej nie ma.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class IncidentCategory(StrEnum):
    SECURITY_INCIDENT = "security_incident"
    CRITICAL_OUTAGE = "critical_outage"
    DATA_INTEGRITY = "data_integrity"


@dataclass(frozen=True)
class BreakGlassPolicy:
    enabled: bool = False
    max_session_minutes: int = 30
    consent_hours: int = 2
    approval_window_minutes: int = 60
    min_justification_length: int = 200
    requires_second_approver: bool = True
    requires_hardware_mfa: bool = False
    security_team_emails: tuple[str, ...] = field(default_factory=tuple)
    independent_audit_path: str | None = None

    @classmethod
    def from_settings(cls, settings) -> BreakGlassPolicy:
        return cls(
            enabled=settings.break_glass_enabled,
            security_team_emails=tuple(settings.security_team_emails),
            independent_audit_path=settings.break_glass_audit_path or None,
        )


class BreakGlassDisabled(Exception):
    pass


def ensure_break_glass_allowed(policy: BreakGlassPolicy) -> None:
    if not policy.enabled:
        raise BreakGlassDisabled("Procedura Break Glass nie jest aktywna.")
    if policy.requires_hardware_mfa:
        raise BreakGlassDisabled("Polityka wymaga kluczy sprzetowych, ktore nie sa jeszcze obslugiwane.")
