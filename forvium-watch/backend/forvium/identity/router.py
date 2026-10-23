"""Identity & Access - logowanie oraz operacje na wlasnym koncie."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select

from forvium.access import AppPrincipal, OperatorPrincipal, get_app_principal, get_operator, require_user_principal
from forvium.core.context import Ctx, DomainError, get_ctx
from forvium.core.security import hash_password, new_totp_secret, verify_password
from forvium.identity import service
from forvium.identity.models import User
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
    return out


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str


@app_router.post("/account/password")
def change_password(body: PasswordChangeIn, principal: AppPrincipal = Depends(require_user_principal),
                    ctx: Ctx = Depends(get_ctx)):
    user = principal.actor
    if not verify_password(user.password_hash, body.current_password) or len(body.new_password) < 12:
        raise DomainError(422, "password_invalid", "Nieprawidłowe hasło.")
    user.password_hash = hash_password(body.new_password)
    ctx.audit.log(ctx.db, "identity.password.changed", actor_user_id=user.id, actor_type="user", ip_address=ctx.ip)
    return {"ok": True}


@app_router.post("/account/mfa/reset")
def reset_mfa(principal: AppPrincipal = Depends(require_user_principal), ctx: Ctx = Depends(get_ctx)):
    user = principal.actor
    user.mfa_secret = new_totp_secret()
    ctx.audit.log(ctx.db, "identity.mfa.reset", actor_user_id=user.id, actor_type="user", ip_address=ctx.ip)
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
            "permissions": sorted(op.permissions)}


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
