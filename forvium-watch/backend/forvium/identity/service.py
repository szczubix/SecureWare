from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError
from forvium.core.security import (
    OPERATOR_TOKEN_PREFIX,
    USER_TOKEN_PREFIX,
    new_token,
    token_digest,
    match_totp_step,
    verify_password,
)
from forvium.identity.models import User, UserSession


def consume_totp(user: User, code: str | None) -> bool:
    """Sprawdza kod TOTP i oznacza jego krok jako zuzyty (ochrona przed ponownym uzyciem)."""
    step = match_totp_step(user.mfa_secret, code, clock.now())
    if step is None or (user.mfa_last_step is not None and step <= user.mfa_last_step):
        return False
    user.mfa_last_step = step
    return True


def _check_password(ctx: Ctx, action: str, email: str, password: str, kind: str) -> User:
    """Pierwszy skladnik logowania; kazda porazka liczy sie do limitu prob."""
    ctx.throttle.check("login_ip", ctx.ip, actor_type="anonymous", ip_address=ctx.ip)
    ctx.throttle.check("login_account", email, actor_type="anonymous", ip_address=ctx.ip)
    user = ctx.db.scalar(select(User).where(User.email == email))
    ok = user is not None and user.is_active and verify_password(user.password_hash, password)
    if ok and kind == "operator" and not user.platform_role:
        ok = False
    if not ok:
        _deny(ctx, action, email, user, "invalid_credentials")
    return user


def _deny(ctx: Ctx, action: str, email: str, user: User | None, reason: str):
    audit = {"actor_user_id": user.id if user else None, "actor_type": "anonymous", "ip_address": ctx.ip}
    ctx.audit.record(action, outcome="denied", details={"reason": reason}, **audit)
    ctx.throttle.fail("login_account", email, **audit)
    ctx.throttle.fail("login_ip", ctx.ip, **audit)
    if reason == "webauthn_required":
        raise DomainError(401, "webauthn_required", "To konto loguje się wyłącznie kluczem bezpieczeństwa.")
    raise DomainError(401, "invalid_credentials", "Nieprawidłowe dane logowania.")


def operator_login_options(ctx: Ctx, *, email: str, password: str) -> dict:
    """Krok 1 logowania kluczem: po sprawdzeniu hasla zwraca wyzwanie WebAuthn (cel "login").

    Haslo jest wymagane juz tutaj, zeby lista kluczy (allowCredentials) nie zdradzala,
    ktore konta istnieja i jakie maja klucze."""
    from forvium.identity.webauthn import PURPOSE_LOGIN, assertion_options, credentials_of

    email = email.strip().lower()
    user = _check_password(ctx, "identity.login.operator", email, password, "operator")
    if not credentials_of(ctx, user):
        raise DomainError(409, "webauthn_not_registered", "To konto nie ma klucza bezpieczeństwa - zaloguj się kodem MFA.")
    return assertion_options(ctx, user, PURPOSE_LOGIN)


def login(ctx: Ctx, *, email: str, password: str, mfa_code: str | None, kind: str, ttl_minutes: int,
          webauthn: dict | None = None) -> str:
    """Logowanie haslem + drugi skladnik. `kind`: "user" (app) albo "operator" (admin).

    Operator moze uzyc klucza WebAuthn (asercja z `operator_login_options`) zamiast TOTP;
    przy `operator_login_webauthn_only` operator z kluczem nie zaloguje sie juz kodem TOTP."""
    from forvium.identity.webauthn import PURPOSE_LOGIN, credentials_of, verify_assertion

    action = "identity.login.operator" if kind == "operator" else "identity.login.user"
    email = email.strip().lower()
    user = _check_password(ctx, action, email, password, kind)
    method = None
    if kind == "operator" and webauthn is not None:
        if not verify_assertion(ctx, user, webauthn, PURPOSE_LOGIN):
            _deny(ctx, action, email, user, "invalid_credentials")
        method = "webauthn"
    elif kind == "operator" or user.mfa_secret:
        if kind == "operator" and ctx.settings.operator_login_webauthn_only and credentials_of(ctx, user):
            _deny(ctx, action, email, user, "webauthn_required")
        if not consume_totp(user, mfa_code):
            _deny(ctx, action, email, user, "invalid_credentials")
        method = "totp"

    ctx.throttle.reset("login_account", email)
    # Haslo sprawdzamy wobec aktualnej polityki (lista wyciekow mogla sie zmienic) - tylko tu
    # mamy je jawnie. Naruszenie nie blokuje logowania, ale wymusza zmiane hasla.
    from forvium.identity.passwords import problems

    violations = problems(password, email=user.email, display_name=user.display_name)
    if violations and not user.password_change_required:
        user.password_change_required = True
        ctx.audit.log(ctx.db, "identity.password.change_required", actor_user_id=user.id, actor_type=kind,
                      ip_address=ctx.ip, details={"reasons": violations})
    token = new_token(OPERATOR_TOKEN_PREFIX if kind == "operator" else USER_TOKEN_PREFIX)
    now = clock.now()
    ctx.db.add(UserSession(user_id=user.id, kind=kind, token_hash=token_digest(token), created_at=now,
                           expires_at=now + timedelta(minutes=ttl_minutes)))
    ctx.audit.log(ctx.db, action, actor_user_id=user.id, actor_type=kind, ip_address=ctx.ip,
                  details={"second_factor": method})
    return token


def logout(ctx: Ctx, session: UserSession) -> None:
    session.revoked_at = clock.now()
