"""Polityka hasel (zgodnie z NIST SP 800-63B): dlugosc zamiast regul skladni, odrzucanie
hasel z wyciekow i hasel zwiazanych z kontem. Sprawdzanie dziala w calosci offline.

* minimum `FORVIUM_PASSWORD_MIN_LENGTH` znakow (domyslnie 12), maksimum 128;
* nie moze byc na liscie hasel z wyciekow - dolaczona lista (data/common-passwords.txt.gz)
  oraz, opcjonalnie, pelna baza Pwned Passwords: plik `FORVIUM_BREACHED_PASSWORDS_FILE`
  z posortowanymi skrotami SHA-1 (format "SHA1:liczba" albo sam skrot w linii),
  przeszukiwany binarnie bez wczytywania do pamieci;
* nie moze zawierac adresu e-mail (czesci przed @), imienia/nazwiska ani nazwy produktu;
* nie moze byc jednym powtorzonym znakiem ani prosta sekwencja.

Haslo niespelniajace polityki przy logowaniu (np. lista zostala zaktualizowana) ustawia
`password_change_required` - do zmiany hasla konto moze tylko zmienic haslo i sie wylogowac.
"""

from __future__ import annotations

import gzip
import hashlib
import os
import re
from functools import lru_cache
from pathlib import Path

from forvium.core.context import DomainError
from forvium.core.i18n import L, join

MAX_LENGTH = 128
_DATA = Path(__file__).parent / "data" / "common-passwords.txt.gz"
_PRODUCT_WORDS = ("forvium", "watch")
_SEQUENCES = ("0123456789" * 2, "abcdefghijklmnopqrstuvwxyz" * 2, "qwertyuiopasdfghjklzxcvbnm" * 2)


def min_length() -> int:
    return max(8, int(os.environ.get("FORVIUM_PASSWORD_MIN_LENGTH", "12")))


@lru_cache(maxsize=1)
def _common() -> frozenset[str]:
    with gzip.open(_DATA, "rt", encoding="utf-8") as f:
        return frozenset(line.strip() for line in f if line.strip())


def _in_sorted_hash_file(path: str, sha1_hex: str) -> bool:
    """Wyszukiwanie binarne w posortowanym pliku skrotow SHA-1 (np. Pwned Passwords).

    Niezmienniki: `lo` wskazuje poczatek linii, linie przed `lo` maja klucz < celu, a cel
    (jesli jest w pliku) zaczyna sie w przedziale [lo, hi).
    """
    target = sha1_hex.upper().encode()

    def key_of(line: bytes) -> bytes:
        return line.split(b":", 1)[0].strip().upper()

    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        lo, hi = 0, f.tell()
        while lo < hi:
            mid = (lo + hi) // 2
            f.seek(mid - 1 if mid > 0 else 0)
            # Jesli mid nie jest poczatkiem linii, przejdz na poczatek nastepnej.
            if mid > 0 and f.read(1) != b"\n":
                f.readline()
            start = f.tell()
            if start >= hi:
                hi = mid  # mid wypadl w ostatniej linii zakresu - szukamy na lewo od niego
                continue
            line = f.readline()
            k = key_of(line)
            if k == target:
                return True
            if k < target:
                lo = f.tell()
            else:
                hi = start
        f.seek(lo)
        return key_of(f.readline()) == target


def is_breached(password: str) -> bool:
    if password.lower() in _common():
        return True
    path = os.environ.get("FORVIUM_BREACHED_PASSWORDS_FILE")
    if path and Path(path).is_file():
        return _in_sorted_hash_file(path, hashlib.sha1(password.encode()).hexdigest())  # noqa: S324 - format HIBP
    return False


def problems(password: str, *, email: str = "", display_name: str = "") -> list[str]:
    """Lista naruszen polityki (pusta = haslo w porzadku). Kody: too_short, too_long, breached, personal, trivial."""
    out: list[str] = []
    if len(password) < min_length():
        out.append("too_short")
    if len(password) > MAX_LENGTH:
        out.append("too_long")
    lowered = password.lower()
    personal = [email.split("@", 1)[0].lower(), *(p.lower() for p in re.split(r"[\s.\-_]+", display_name))]
    if any(len(p) >= 4 and p in lowered for p in personal) or any(w in lowered for w in _PRODUCT_WORDS):
        out.append("personal")
    if len(set(lowered)) <= 2 or any(lowered in seq for seq in _SEQUENCES):
        out.append("trivial")
    if "too_short" not in out and is_breached(password):
        out.append("breached")
    return out


MESSAGES = {
    "too_short": "Hasło musi mieć co najmniej {n} znaków.",
    "too_long": "Hasło może mieć najwyżej {max} znaków.",
    "breached": "To hasło występuje w znanych wyciekach danych - wybierz inne.",
    "personal": "Hasło nie może zawierać adresu e-mail, imienia, nazwiska ani nazwy Forvium.",
    "trivial": "Hasło jest zbyt proste (powtórzenia albo sekwencje znaków).",
}


def validate(password: str, *, email: str = "", display_name: str = "") -> None:
    found = problems(password or "", email=email, display_name=display_name)
    if found:
        raise DomainError(422, "password_policy", join(" ", [L(MESSAGES[p], n=min_length(), max=MAX_LENGTH) for p in found]))
