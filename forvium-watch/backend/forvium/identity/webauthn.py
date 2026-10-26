"""WebAuthn (klucze sprzetowe FIDO2 / passkeys) dla operatorow Forvium.

Klucz sluzy jako silniejsza forma ponownej weryfikacji (step-up) zamiast
TOTP; polityka Break Glass wymaga go (`requires_hardware_mfa`). Kazde wyzwanie
jest jednorazowe, wazne 2 minuty i przypiete do uzytkownika oraz celu.
Wymagana jest weryfikacja uzytkownika (PIN / biometria na kluczu), a licznik
podpisow chroni przed sklonowanymi kluczami.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlparse

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, LargeBinary, String, select, update
from sqlalchemy.orm import Mapped, mapped_column
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidRegistrationResponse
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError
from forvium.core.db import Base, new_id
from forvium.identity.models import User
from forvium.core.i18n import L

CHALLENGE_TTL = timedelta(minutes=2)
PURPOSE_REGISTER = "register"
PURPOSE_STEP_UP = "step_up"
PURPOSE_LOGIN = "login"


class WebAuthnCredential(Base):
    __tablename__ = "webauthn_credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    credential_id: Mapped[str] = mapped_column(String(512), unique=True, index=True)  # base64url
    public_key: Mapped[bytes] = mapped_column(LargeBinary)  # klucz publiczny COSE (nie jest sekretem)
    sign_count: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(100))
    aaguid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transports: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class WebAuthnChallenge(Base):
    __tablename__ = "webauthn_challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(16))
    challenge: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


def rp_id(ctx: Ctx) -> str:
    return ctx.settings.webauthn_rp_id or urlparse(ctx.settings.admin_origin).hostname


def _origin(ctx: Ctx) -> str:
    return ctx.settings.admin_origin


def _new_challenge(ctx: Ctx, user: User, purpose: str) -> bytes:
    raw = secrets.token_bytes(32)
    ctx.db.add(WebAuthnChallenge(user_id=user.id, purpose=purpose, challenge=bytes_to_base64url(raw),
                                 expires_at=clock.now() + CHALLENGE_TTL))
    return raw


def _consume_challenge(ctx: Ctx, user: User, purpose: str, challenge_b64: str) -> bytes | None:
    """Atomowo zuzywa wyzwanie we wlasnej transakcji - nie da sie go uzyc drugi raz,
    nawet gdy zadanie, w ktorym je przedstawiono, zakonczy sie bledem."""
    if not challenge_b64:
        return None
    now = clock.now()
    with ctx.audit.independent_session() as s:  # osobna pula - patrz core/db.py
        result = s.execute(
            update(WebAuthnChallenge)
            .where(WebAuthnChallenge.challenge == challenge_b64, WebAuthnChallenge.user_id == user.id,
                   WebAuthnChallenge.purpose == purpose, WebAuthnChallenge.used_at.is_(None),
                   WebAuthnChallenge.expires_at > now)
            .values(used_at=now)
        )
        s.commit()
    if result.rowcount != 1:
        return None
    return base64url_to_bytes(challenge_b64)


def _challenge_from(credential: dict) -> str:
    try:
        client_data = json.loads(base64url_to_bytes(credential["response"]["clientDataJSON"]))
        return client_data["challenge"]
    except (KeyError, ValueError, TypeError):
        return ""


def credentials_of(ctx: Ctx, user: User) -> list[WebAuthnCredential]:
    return list(ctx.db.scalars(select(WebAuthnCredential).where(WebAuthnCredential.user_id == user.id)
                               .order_by(WebAuthnCredential.created_at)))


# ------------------------------------------------------------------ rejestracja


def registration_options(ctx: Ctx, user: User) -> dict:
    challenge = _new_challenge(ctx, user, PURPOSE_REGISTER)
    options = generate_registration_options(
        rp_id=rp_id(ctx),
        rp_name="Forvium Admin",
        user_id=user.id.encode(),
        user_name=user.email,
        user_display_name=user.display_name,
        challenge=challenge,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id))
                             for c in credentials_of(ctx, user)],
    )
    return json.loads(options_to_json(options))


def finish_registration(ctx: Ctx, user: User, credential: dict, name: str) -> WebAuthnCredential:
    expected = _consume_challenge(ctx, user, PURPOSE_REGISTER, _challenge_from(credential))
    if expected is None:
        raise DomainError(400, "webauthn_challenge_invalid", "Wyzwanie WebAuthn jest nieprawidłowe lub wygasło.")
    try:
        verified = verify_registration_response(credential=credential, expected_challenge=expected,
                                                expected_rp_id=rp_id(ctx), expected_origin=_origin(ctx),
                                                require_user_verification=True)
    except InvalidRegistrationResponse as exc:
        ctx.audit.record("identity.webauthn.register", outcome="denied", actor_user_id=user.id,
                         actor_type="operator", ip_address=ctx.ip, details={"reason": "invalid_attestation"})
        raise DomainError(400, "webauthn_invalid", L("Nie udało się zweryfikować klucza: {error}", error=str(exc))) from exc
    cred = WebAuthnCredential(
        user_id=user.id,
        credential_id=bytes_to_base64url(verified.credential_id),
        public_key=verified.credential_public_key,
        sign_count=verified.sign_count,
        name=(name or "Klucz bezpieczeństwa").strip()[:100],
        aaguid=verified.aaguid,
        transports=(credential.get("response") or {}).get("transports"),
        created_at=clock.now(),
    )
    ctx.db.add(cred)
    ctx.db.flush()
    ctx.audit.log(ctx.db, "identity.webauthn.registered", actor_user_id=user.id, actor_type="operator",
                  ip_address=ctx.ip, details={"credential": cred.id, "name": cred.name, "aaguid": cred.aaguid})
    ctx.notifications.notify(ctx.db, [user], event="identity.webauthn.registered",
                             title="Dodano klucz bezpieczeństwa do konta Forvium",
                             body=L("Do Twojego konta dodano klucz '{name}'. Jeśli to nie Ty, "
                                    "natychmiast skontaktuj się z zespołem bezpieczeństwa.", name=cred.name))
    return cred


def remove_credential(ctx: Ctx, user: User, credential_pk: str) -> None:
    cred = ctx.db.get(WebAuthnCredential, credential_pk)
    if cred is None or cred.user_id != user.id:
        raise DomainError(404, "credential_not_found", "Nie znaleziono klucza.")
    ctx.db.delete(cred)
    ctx.audit.log(ctx.db, "identity.webauthn.removed", actor_user_id=user.id, actor_type="operator",
                  ip_address=ctx.ip, details={"credential": credential_pk, "name": cred.name})
    ctx.notifications.notify(ctx.db, [user], event="identity.webauthn.removed",
                             title="Usunięto klucz bezpieczeństwa z konta Forvium",
                             body=L("Z Twojego konta usunięto klucz '{name}'.", name=cred.name))


# ------------------------------------------------------------- asercja (step-up)


def assertion_options(ctx: Ctx, user: User, purpose: str = PURPOSE_STEP_UP) -> dict:
    creds = credentials_of(ctx, user)
    if not creds:
        raise DomainError(409, "webauthn_not_registered", "Najpierw dodaj klucz bezpieczeństwa.")
    challenge = _new_challenge(ctx, user, purpose)
    options = generate_authentication_options(
        rp_id=rp_id(ctx), challenge=challenge, user_verification=UserVerificationRequirement.REQUIRED,
        allow_credentials=[PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id)) for c in creds],
    )
    return json.loads(options_to_json(options))


def verify_assertion(ctx: Ctx, user: User, credential: dict | None, purpose: str = PURPOSE_STEP_UP) -> bool:
    """Weryfikuje asercje WebAuthn uzytkownika; zuzywa wyzwanie i aktualizuje licznik."""
    if not isinstance(credential, dict):
        return False
    expected = _consume_challenge(ctx, user, purpose, _challenge_from(credential))
    if expected is None:
        return False
    with ctx.db.no_autoflush:
        cred = ctx.db.scalar(select(WebAuthnCredential).where(
            WebAuthnCredential.credential_id == str(credential.get("rawId") or credential.get("id") or "")))
    if cred is None or cred.user_id != user.id:
        return False
    try:
        verified = verify_authentication_response(
            credential=credential, expected_challenge=expected, expected_rp_id=rp_id(ctx),
            expected_origin=_origin(ctx), credential_public_key=cred.public_key,
            credential_current_sign_count=cred.sign_count, require_user_verification=True)
    except InvalidAuthenticationResponse:
        return False
    cred.sign_count = verified.new_sign_count
    cred.last_used_at = clock.now()
    return True
