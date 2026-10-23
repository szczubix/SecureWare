"""Break Glass - punkt rozszerzenia (WYLACZONY).

Dostep awaryjny nie jest zaimplementowany ani aktywny. Model danych
przewiduje `AccessMode.BREAK_GLASS`, ale `service.create_request` odrzuca ten
tryb, dopoki `BREAK_GLASS_POLICY.enabled` jest False, a zadna rola platformowa
nie posiada `PlatformPermission.BREAK_GLASS`.

Przyszla implementacja MUSI zapewnic:
  * osobna polityke (ta klasa) zatwierdzona przez dzial bezpieczenstwa,
  * szczegolowe uzasadnienie (min. dlugosc, kategoria incydentu),
  * silna autoryzacje: MFA sprzetowe + zatwierdzenie drugiej osoby (4 oczy),
  * twardy limit czasu, bez mozliwosci przedluzenia,
  * natychmiastowe powiadomienie wlascicieli organizacji i zespolu bezpieczenstwa,
  * niezalezny strumien audytu (osobny sink, np. WORM), poza standardowym Audit Log,
  * obowiazkowy przeglad po incydencie.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BreakGlassPolicy:
    enabled: bool = False
    max_session_minutes: int = 30
    min_justification_length: int = 200
    requires_second_approver: bool = True
    requires_hardware_mfa: bool = True
    notify_security_team: bool = True
    independent_audit_sink: str | None = None


BREAK_GLASS_POLICY = BreakGlassPolicy()


class BreakGlassDisabled(Exception):
    pass


def ensure_break_glass_allowed() -> None:
    if not BREAK_GLASS_POLICY.enabled:
        raise BreakGlassDisabled("Procedura Break Glass nie jest aktywna.")
    raise NotImplementedError("Break Glass wymaga osobnej implementacji i polityki.")
