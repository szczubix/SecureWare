"""Identity & Access - logowanie oraz operacje na wlasnym koncie."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select

from forvium.access import AppPrincipal, OperatorPrincipal, get_app_principal, get_operator, require_user_principal
from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError, get_ctx
from forvium.core.security import hash_password, new_totp_secret, verify_password
from forvium.identity import service
from forvium.identity.models import User, UserSession
from forvium.organizations.models import Membership, Organization

app_router = APIRouter(prefix="/api/app", tags=["identity (app)"])
admin_router = APIRouter(prefix="/api/admin", tags=["identity (admin)"])


class LoginIn(BaseModel):
    email: str
    password: str
    mfa_code: str | None = None
    webauthn: dict | None = None


class PasswordIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    token: str


def _user_out(user: User) -> dict:
    return {"id": user.id, "email": user.email, "display_name": user.display_name}


# ------------------------------------------------------------------- app


@app_router.post("/auth/login", response_model=TokenOut)
def app_login(body: LoginIn, request: Request, ctx: Ctx = Depends(get_ctx)):
    s = request.app.state.settings
    return {"token": service.login(ctx, email=body.email, password=body.password, mfa_code=body.mfa_code,
                                   kind="user", ttl_minutes=s.user_session_ttl_minutes)}


@app_router.post("/auth/logout")
def app_logout(principal: AppPrincipal = Depends(require_user_principal), ctx: Ctx = Depends(get_ctx)):
    service.logout(ctx, principal.user_session)
    return {"ok": True}


@app_router.get("/me")
def app_me(principal: AppPrincipal = Depends(get_app_principal), ctx: Ctx = Depends(get_ctx)):
    """Kontekst biezacej sesji. W trybie wsparcia zwraca uzytkownika referencyjnego
    oraz jawna informacje o trybie wsparcia (nigdy nie udaje zwyklej sesji)."""
    out: dict = {"user": _user_out(principal.reference_user), "mode": principal.kind}
    if principal.is_support:
        s = principal.support
        out["support"] = {"session_id": s.session.id, "operator_id": s.operator.id,
                          "organization_id": s.organization.id, "access_level": s.session.access_level}
        out["organizations"] = [{"id": s.organization.id, "name": s.organization.name, "role": None}]
        return out
    rows = ctx.db.execute(
        select(Organization, Membership.role)
        .join(Membership, Membership.organization_id == Organization.id)
        .where(Membership.user_id == principal.actor.id, Organization.deleted_at.is_(None))
    ).all()
    out["organizations"] = [{"id": o.id, "name": o.name, "role": role} for o, role in rows]
    out["password_change_required"] = bool(principal.actor.password_change_required)
    return out


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str


def _set_password(ctx: Ctx, user: User, session: UserSession | None, new_password: str, actor_type: str) -> None:
    """Nowe haslo: polityka, wylogowanie pozostalych sesji, powiadomienie."""
    from forvium.identity.passwords import validate

    if verify_password(user.password_hash, new_password):
        raise DomainError(422, "password_reused", "Nowe hasło musi być inne niż obecne.")
    validate(new_password, email=user.email, display_name=user.display_name)
    user.password_hash = hash_password(new_password)
    user.password_changed_at = clock.now()
    user.password_change_required = False
    others = select(UserSession).where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
    if session is not None:
        others = others.where(UserSession.id != session.id)
    for other in ctx.db.scalars(others):
        other.revoked_at = clock.now()
    ctx.audit.log(ctx.db, "identity.password.changed", actor_user_id=user.id, actor_type=actor_type, ip_address=ctx.ip)
    ctx.notifications.notify(ctx.db, [user], event="identity.password.changed", title="Zmieniono hasło",
                             body="Hasło do Twojego konta zostało zmienione, a pozostałe sesje wylogowane. "
                                  "Jeśli to nie Ty - natychmiast skontaktuj się z administratorem.")


@app_router.post("/account/password")
def change_password(body: PasswordChangeIn, principal: AppPrincipal = Depends(require_user_principal),
                    ctx: Ctx = Depends(get_ctx)):
    user = principal.actor
    who = {"actor_user_id": user.id, "actor_type": "user", "ip_address": ctx.ip}
    ctx.throttle.check("mfa_stepup", user.id, **who)
    if not verify_password(user.password_hash, body.current_password):
        ctx.audit.record("identity.password.change", outcome="denied", details={"reason": "invalid_current"}, **who)
        ctx.throttle.fail("mfa_stepup", user.id, **who)
        raise DomainError(422, "password_invalid", "Nieprawidłowe obecne hasło.")
    _set_password(ctx, user, principal.user_session, body.new_password, "user")
    return {"ok": True}


class MfaResetIn(BaseModel):
    current_password: str
    mfa_code: str | None = None


@app_router.post("/account/mfa/reset")
def reset_mfa(body: MfaResetIn, principal: AppPrincipal = Depends(require_user_principal),
              ctx: Ctx = Depends(get_ctx)):
    """Nowy sekret TOTP. Wymaga hasla i biezacego kodu - inaczej skradziony token sesji
    wystarczylby, by przejac MFA i przejsc kazda ponowna weryfikacje (zgody stale, ustawienia)."""
    user = principal.actor
    who = {"actor_user_id": user.id, "actor_type": "user", "ip_address": ctx.ip}
    ctx.throttle.check("mfa_stepup", user.id, **who)
    ok = verify_password(user.password_hash, body.current_password) and (
        not user.mfa_secret or service.consume_totp(user, body.mfa_code))
    if not ok:
        ctx.audit.record("identity.mfa.reset", outcome="denied", details={"reason": "invalid_credentials"}, **who)
        ctx.throttle.fail("mfa_stepup", user.id, **who)
        raise DomainError(401, "invalid_credentials", "Nieprawidłowe hasło lub kod MFA.")
    ctx.throttle.reset("mfa_stepup", user.id)
    user.mfa_secret = new_totp_secret()
    user.mfa_last_step = None
    # Pozostale sesje uzytkownika przestaja dzialac (kradziony token traci waznosc).
    now = clock.now()
    others = select(UserSession).where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
    if principal.user_session is not None:
        others = others.where(UserSession.id != principal.user_session.id)
    for other in ctx.db.scalars(others):
        other.revoked_at = now
    ctx.audit.log(ctx.db, "identity.mfa.reset", **who)
    ctx.notifications.notify(ctx.db, [user], event="identity.mfa.reset",
                             title="Zmieniono drugi składnik logowania (MFA)",
                             body="Na Twoim koncie ustawiono nowy sekret aplikacji uwierzytelniającej, a pozostałe "
                                  "sesje zostały wylogowane. Jeśli to nie Ty - natychmiast zmień hasło i skontaktuj "
                                  "się z administratorem organizacji.")
    return {"secret": user.mfa_secret}


@app_router.get("/account/tokens")
def list_tokens(principal: AppPrincipal = Depends(require_user_principal)):
    return {"tokens": []}


# ------------------------------------------------------------------- admin


@admin_router.post("/auth/login", response_model=TokenOut)
def admin_login(body: LoginIn, request: Request, ctx: Ctx = Depends(get_ctx)):
    s = request.app.state.settings
    return {"token": service.login(ctx, email=body.email, password=body.password, mfa_code=body.mfa_code,
                                   kind="operator", ttl_minutes=s.operator_session_ttl_minutes,
                                   webauthn=body.webauthn)}


@admin_router.post("/auth/login/webauthn/options")
def admin_login_webauthn_options(body: PasswordIn, ctx: Ctx = Depends(get_ctx)):
    return {"options": service.operator_login_options(ctx, email=body.email, password=body.password)}


@admin_router.post("/auth/logout")
def admin_logout(op: OperatorPrincipal = Depends(get_operator), ctx: Ctx = Depends(get_ctx)):
    service.logout(ctx, op.session)
    return {"ok": True}


@admin_router.get("/me")
def admin_me(op: OperatorPrincipal = Depends(get_operator)):
    return {"user": _user_out(op.user), "platform_role": op.user.platform_role,
            "permissions": sorted(op.permissions), "password_change_required": bool(op.user.password_change_required)}


class OperatorPasswordIn(PasswordChangeIn):
    mfa_code: str | None = None
    webauthn: dict | None = None


@admin_router.post("/account/password")
def operator_change_password(body: OperatorPasswordIn, op: OperatorPrincipal = Depends(get_operator),
                             ctx: Ctx = Depends(get_ctx)):
    """Zmiana hasla operatora: obecne haslo + ponowna weryfikacja (klucz albo kod MFA)."""
    from forvium.support_access.service import _verify_operator_mfa

    who = {"actor_user_id": op.user.id, "actor_type": "operator", "ip_address": ctx.ip}
    ctx.throttle.check("mfa_stepup", op.user.id, **who)
    if not verify_password(op.user.password_hash, body.current_password):
        ctx.audit.record("identity.password.change", outcome="denied", details={"reason": "invalid_current"}, **who)
        ctx.throttle.fail("mfa_stepup", op.user.id, **who)
        raise DomainError(422, "password_invalid", "Nieprawidłowe obecne hasło.")
    from forvium.identity.passwords import validate

    validate(body.new_password, email=op.user.email, display_name=op.user.display_name)
    _verify_operator_mfa(ctx, op.user, body.mfa_code, "identity.password.change", webauthn=body.webauthn)
    _set_password(ctx, op.user, op.session, body.new_password, "operator")
    return {"ok": True}


# ------------------------------------------------------------- WebAuthn (admin)


class StepUpIn(BaseModel):
    mfa_code: str | None = None
    webauthn: dict | None = None


class RegisterVerifyIn(BaseModel):
    credential: dict
    name: str = "Klucz bezpieczeństwa"


def _credential_out(c) -> dict:
    return {"id": c.id, "name": c.name, "created_at": c.created_at.isoformat() + "Z",
            "last_used_at": c.last_used_at.isoformat() + "Z" if c.last_used_at else None,
            "transports": c.transports}


@admin_router.get("/webauthn/credentials")
def webauthn_credentials(op: OperatorPrincipal = Depends(get_operator), ctx: Ctx = Depends(get_ctx)):
    from forvium.identity import webauthn

    return {"credentials": [_credential_out(c) for c in webauthn.credentials_of(ctx, op.user)]}


@admin_router.post("/webauthn/register/options")
def webauthn_register_options(body: StepUpIn, op: OperatorPrincipal = Depends(get_operator),
                              ctx: Ctx = Depends(get_ctx)):
    """Dodanie klucza wymaga ponownej weryfikacji (TOTP albo juz zarejestrowanym kluczem)."""
    from forvium.identity import webauthn
    from forvium.support_access.service import _verify_operator_mfa

    _verify_operator_mfa(ctx, op.user, body.mfa_code, "identity.webauthn.register", webauthn=body.webauthn)
    return {"options": webauthn.registration_options(ctx, op.user)}


@admin_router.post("/webauthn/register/verify")
def webauthn_register_verify(body: RegisterVerifyIn, op: OperatorPrincipal = Depends(get_operator),
                             ctx: Ctx = Depends(get_ctx)):
    from forvium.identity import webauthn

    return {"credential": _credential_out(webauthn.finish_registration(ctx, op.user, body.credential, body.name))}


@admin_router.post("/webauthn/assertion/options")
def webauthn_assertion_options(op: OperatorPrincipal = Depends(get_operator), ctx: Ctx = Depends(get_ctx)):
    from forvium.identity import webauthn

    return {"options": webauthn.assertion_options(ctx, op.user)}


@admin_router.post("/webauthn/credentials/{credential_pk}/remove")
def webauthn_remove(credential_pk: str, body: StepUpIn, op: OperatorPrincipal = Depends(get_operator),
                    ctx: Ctx = Depends(get_ctx)):
    from forvium.identity import webauthn
    from forvium.support_access.service import _verify_operator_mfa

    _verify_operator_mfa(ctx, op.user, body.mfa_code, "identity.webauthn.remove", webauthn=body.webauthn)
    webauthn.remove_credential(ctx, op.user, credential_pk)
    return {"ok": True}


# ------------------------------------------------------- aktywacja kont (bez logowania)


class ActivationInfoIn(BaseModel):
    token: str


class ActivationCompleteIn(BaseModel):
    token: str
    password: str
    mfa_code: str


@app_router.post("/activation/info")
def app_activation_info(body: ActivationInfoIn, ctx: Ctx = Depends(get_ctx)):
    from forvium.identity import activation

    return activation.info(ctx, body.token, "user")


@app_router.post("/activation/complete")
def app_activation_complete(body: ActivationCompleteIn, ctx: Ctx = Depends(get_ctx)):
    from forvium.identity import activation

    activation.complete(ctx, body.token, "user", body.password, body.mfa_code)
    return {"ok": True}


@admin_router.post("/activation/info")
def admin_activation_info(body: ActivationInfoIn, ctx: Ctx = Depends(get_ctx)):
    from forvium.identity import activation

    return activation.info(ctx, body.token, "operator")


@admin_router.post("/activation/complete")
def admin_activation_complete(body: ActivationCompleteIn, ctx: Ctx = Depends(get_ctx)):
    from forvium.identity import activation

    activation.complete(ctx, body.token, "operator", body.password, body.mfa_code)
    return {"ok": True}
