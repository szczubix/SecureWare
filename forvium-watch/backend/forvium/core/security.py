"""Hasla, tokeny i TOTP.

Tokeny sesji sa losowe, a w bazie przechowywany jest wylacznie ich skrot
SHA-256. Prefiks tokenu okresla jego typ, dzieki czemu kazdy typ sesji jest
weryfikowany we wlasnej tabeli i nie da sie uzyc jednego w miejscu drugiego.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

USER_TOKEN_PREFIX = "fwu_"  # sesja klienta (app.forvium.com)
OPERATOR_TOKEN_PREFIX = "fwo_"  # sesja operatora (admin.forvium.com)
SUPPORT_TOKEN_PREFIX = "fws_"  # sesja wsparcia (app.forvium.com w trybie wsparcia)
LAUNCH_CODE_PREFIX = "fwl_"  # jednorazowy kod przekazania sesji wsparcia

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def new_token(prefix: str) -> str:
    return prefix + secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_totp_secret() -> str:
    return pyotp.random_base32()


def match_totp_step(secret: str | None, code: str | None, at: datetime, valid_window: int = 1) -> int | None:
    """Zwraca numer kroku czasowego TOTP pasujacego do kodu albo None.

    Wywolujacy odrzuca kroki <= ostatnio uzytego, co blokuje ponowne uzycie kodu.
    """
    if not secret or not code:
        return None
    totp = pyotp.TOTP(secret)
    ts = int(at.replace(tzinfo=UTC).timestamp())
    for offset in range(-valid_window, valid_window + 1):
        t = ts + offset * totp.interval
        if hmac.compare_digest(totp.at(t), code.strip()):
            return t // totp.interval
    return None
