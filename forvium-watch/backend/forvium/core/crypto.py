"""Szyfrowanie danych w spoczynku (sekrety MFA, sekrety i konfiguracja organizacji).

* AES-256-GCM, losowy nonce, AAD = nazwa kolumny (szyfrogramu nie da sie
  przeniesc do innego pola).
* Format: ``fwenc:v1:<kid>:<base64url(nonce || ciphertext)>`` - identyfikator
  klucza pozwala rotowac klucze bez przestojow (stare odczytujemy, nowe
  zapisujemy aktywnym kluczem; `python -m forvium.core.crypto reencrypt`).
* Klucze danych (DEK) pochodza z KMS:
  - HashiCorp Vault Transit: `FORVIUM_DATA_KEYS_WRAPPED="kid:vault:v1:..."` + `FORVIUM_VAULT_ADDR`,
    `FORVIUM_VAULT_TOKEN`, `FORVIUM_VAULT_TRANSIT_KEY` - DEK sa odszyfrowywane w Vault przy starcie
    i trzymane tylko w pamieci procesu,
  - albo wprost `FORVIUM_DATA_KEYS="kid:base64"` (np. wstrzykiwane przez menedzera sekretow).
  Aktywny klucz: `FORVIUM_DATA_KEY_ID`. Bez klucza aplikacja NIE wystartuje
  (wyjatek: `FORVIUM_ALLOW_INSECURE_DEV_KEY=true` - staly klucz deweloperski).
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import sys
import urllib.request
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

logger = logging.getLogger(__name__)

PREFIX = "fwenc:v1:"
DEV_KEY_ID = "dev"


class CryptoConfigError(RuntimeError):
    pass


def _b64d(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _b64e(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


@dataclass
class KeyRing:
    keys: dict[str, bytes]
    active_kid: str

    def __post_init__(self) -> None:
        if self.active_kid not in self.keys:
            raise CryptoConfigError(f"Brak aktywnego klucza '{self.active_kid}' w pierścieniu kluczy.")
        for kid, key in self.keys.items():
            if len(key) != 32:
                raise CryptoConfigError(f"Klucz '{kid}' musi miec 32 bajty (AES-256).")
            if ":" in kid:
                raise CryptoConfigError("Identyfikator klucza nie może zawierać ':'.")

    def encrypt(self, plaintext: bytes, context: str) -> str:
        nonce = os.urandom(12)
        ct = AESGCM(self.keys[self.active_kid]).encrypt(nonce, plaintext, context.encode())
        return f"{PREFIX}{self.active_kid}:{_b64e(nonce + ct)}"

    def decrypt(self, token: str, context: str) -> bytes:
        kid, payload = token[len(PREFIX):].split(":", 1)
        key = self.keys.get(kid)
        if key is None:
            raise CryptoConfigError(f"Dane zaszyfrowano nieznanym kluczem '{kid}'.")
        raw = _b64d(payload)
        return AESGCM(key).decrypt(raw[:12], raw[12:], context.encode())

    @staticmethod
    def is_encrypted(value: str | None) -> bool:
        return isinstance(value, str) and value.startswith(PREFIX)

    def key_id_of(self, token: str) -> str:
        return token[len(PREFIX):].split(":", 1)[0]


# ----------------------------------------------------------------- dostawcy kluczy


def _parse_pairs(value: str) -> list[tuple[str, str]]:
    pairs = []
    for item in filter(None, (p.strip() for p in value.split(","))):
        kid, _, material = item.partition(":")
        if not kid or not material:
            raise CryptoConfigError("Oczekiwany format: kid:wartość[,kid:wartość]")
        pairs.append((kid, material))
    return pairs


def vault_transit_unwrap(addr: str, token: str, key_name: str, ciphertext: str, timeout: int = 10) -> bytes:
    body = json.dumps({"ciphertext": ciphertext}).encode()
    req = urllib.request.Request(f"{addr.rstrip('/')}/v1/transit/decrypt/{key_name}", data=body, method="POST",
                                 headers={"X-Vault-Token": token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - adres z konfiguracji
        data = json.load(resp)
    return base64.b64decode(data["data"]["plaintext"])


def keyring_from_settings(settings) -> KeyRing:
    keys: dict[str, bytes] = {}
    if settings.data_keys:
        for kid, material in _parse_pairs(settings.data_keys):
            keys[kid] = base64.b64decode(material)
    if settings.data_keys_wrapped:
        if not (settings.vault_addr and settings.vault_token):
            raise CryptoConfigError("FORVIUM_DATA_KEYS_WRAPPED wymaga FORVIUM_VAULT_ADDR i FORVIUM_VAULT_TOKEN.")
        for kid, wrapped in _parse_pairs(settings.data_keys_wrapped):
            keys[kid] = vault_transit_unwrap(settings.vault_addr, settings.vault_token,
                                             settings.vault_transit_key, wrapped)
    if not keys:
        if not settings.allow_insecure_dev_key:
            raise CryptoConfigError(
                "Brak klucza szyfrowania danych. Skonfiguruj FORVIUM_DATA_KEYS_WRAPPED (Vault) lub "
                "FORVIUM_DATA_KEYS; tylko lokalnie: FORVIUM_ALLOW_INSECURE_DEV_KEY=true.")
        logger.warning("UWAGA: używany jest stały klucz deweloperski - nie do produkcji.")
        keys[DEV_KEY_ID] = hashlib.sha256(b"forvium-insecure-dev-key").digest()
        return KeyRing(keys, DEV_KEY_ID)
    active = settings.data_key_id or next(iter(keys))
    return KeyRing(keys, active)


# Pierscien ustawiany przy starcie aplikacji (create_app) - uzywany przez typy kolumn.
_keyring: KeyRing | None = None


def set_keyring(keyring: KeyRing) -> None:
    global _keyring
    _keyring = keyring


def get_keyring() -> KeyRing:
    if _keyring is None:
        raise CryptoConfigError("Pierścień kluczy nie został zainicjalizowany.")
    return _keyring


# ------------------------------------------------------------------ typy kolumn


class EncryptedString(TypeDecorator):
    """Tekst szyfrowany w bazie. Odczyt toleruje dane sprzed szyfrowania (tekst jawny)."""

    impl = Text
    cache_ok = True

    def __init__(self, context: str) -> None:
        super().__init__()
        self.context = context

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return get_keyring().encrypt(value.encode(), self.context)

    def process_result_value(self, value, dialect):
        if value is None or not KeyRing.is_encrypted(value):
            return value
        return get_keyring().decrypt(value, self.context).decode()


class EncryptedJSON(TypeDecorator):
    """Struktura JSON szyfrowana w bazie (sekrety, SMTP, webhooki)."""

    impl = Text
    cache_ok = True

    def __init__(self, context: str) -> None:
        super().__init__()
        self.context = context

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return get_keyring().encrypt(json.dumps(value, sort_keys=True).encode(), self.context)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if KeyRing.is_encrypted(value):
            return json.loads(get_keyring().decrypt(value, self.context))
        return json.loads(value) if isinstance(value, str) else value


# ------------------------------------------------------------- rotacja kluczy

ENCRYPTED_COLUMNS = [
    ("forvium.identity.models", "User", ["mfa_secret"]),
    ("forvium.organizations.models", "Organization", ["secrets", "smtp_config", "webhooks"]),
    ("forvium.support_access.recording", "SupportSessionSnapshot", ["html"]),
    ("forvium.reports.service", "AccessReport", ["pdf"]),
    ("forvium.identity.activation", "AccountActivation", ["pending_mfa_secret"]),
    ("forvium.support_tickets.models", "SupportTicket", ["description"]),
    ("forvium.support_tickets.models", "SupportTicketMessage", ["body"]),
]


def reencrypt_all(session) -> int:
    """Przepisuje wszystkie zaszyfrowane pola aktywnym kluczem (rotacja / szyfrowanie starych danych)."""
    import importlib

    from sqlalchemy import select, text
    from sqlalchemy.orm.attributes import flag_modified

    keyring = get_keyring()
    changed = 0
    for module, cls_name, attrs in ENCRYPTED_COLUMNS:
        cls = getattr(importlib.import_module(module), cls_name)
        table = cls.__table__.name
        for obj in session.scalars(select(cls)):
            raw = session.execute(text(f"SELECT {', '.join(attrs)} FROM {table} WHERE id = :id"),
                                  {"id": obj.id}).one()
            for attr, stored in zip(attrs, raw):
                if stored is None:
                    continue
                if KeyRing.is_encrypted(stored) and keyring.key_id_of(stored) == keyring.active_kid:
                    continue
                flag_modified(obj, attr)
                changed += 1
    session.flush()
    return changed


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
    import argparse

    from forvium.core.config import get_settings
    from forvium.core.db import Database

    parser = argparse.ArgumentParser(description="Narzędzia szyfrowania danych Forvium")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("reencrypt", help="zaszyfruj/przepisz wszystkie pola aktywnym kluczem")
    sub.add_parser("generate-key", help="wygeneruj nowy klucz danych (base64)")
    args = parser.parse_args(argv)
    if args.cmd == "generate-key":
        print(base64.b64encode(os.urandom(32)).decode())
        return 0
    settings = get_settings()
    set_keyring(keyring_from_settings(settings))
    db = Database(settings.database_url)
    with db.sessionmaker() as session:
        n = reencrypt_all(session)
        session.commit()
    print(f"Przepisano {n} pól aktywnym kluczem '{get_keyring().active_kid}'.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    # `python -m` laduje ten plik jako `__main__` (osobny obiekt modulu). Uruchamiamy main()
    # z modulu `forvium.core.crypto`, aby pierscien kluczy trafil tam, skad czytaja go typy kolumn.
    from forvium.core.crypto import main as _main

    sys.exit(_main())
