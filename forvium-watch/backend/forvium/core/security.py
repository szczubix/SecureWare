"""Hasla, tokeny i TOTP.

Tokeny sesji sa losowe, a w bazie przechowywany jest wylacznie ich skrot
SHA-256. Prefiks tokenu okresla jego typ, dzieki czemu kazdy typ sesji jest
weryfikowany we wlasnej tabeli i nie da sie uzyc jednego w miejscu drugiego.
"""

from __future__ import annotations

import hashlib
import secrets

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


def verify_totp(secret: str | None, code: str | None, valid_window: int = 1) -> bool:
    if not secret or not code:
        return False
    return pyotp.TOTP(secret).verify(code.strip(), valid_window=valid_window)
