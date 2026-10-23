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


def login(ctx: Ctx, *, email: str, password: str, mfa_code: str | None, kind: str, ttl_minutes: int) -> str:
    """Logowanie haslem + TOTP. `kind`: "user" (app) albo "operator" (admin)."""
    action = "identity.login.operator" if kind == "operator" else "identity.login.user"
    user = ctx.db.scalar(select(User).where(User.email == email.strip().lower()))
    ok = user is not None and user.is_active and verify_password(user.password_hash, password)
    if ok and kind == "operator" and not user.platform_role:
        ok = False
    if ok and (kind == "operator" or user.mfa_secret):
        ok = consume_totp(user, mfa_code)
    if not ok:
        ctx.audit.record(action, outcome="denied", actor_user_id=user.id if user else None,
                         actor_type="anonymous", ip_address=ctx.ip, details={"reason": "invalid_credentials"})
        raise DomainError(401, "invalid_credentials", "Nieprawidlowe dane logowania.")

    token = new_token(OPERATOR_TOKEN_PREFIX if kind == "operator" else USER_TOKEN_PREFIX)
    now = clock.now()
    ctx.db.add(UserSession(user_id=user.id, kind=kind, token_hash=token_digest(token), created_at=now,
                           expires_at=now + timedelta(minutes=ttl_minutes)))
    ctx.audit.log(ctx.db, action, actor_user_id=user.id, actor_type=kind, ip_address=ctx.ip)
    return token


def logout(ctx: Ctx, session: UserSession) -> None:
    session.revoked_at = clock.now()
