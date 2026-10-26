"""Organizations & RBAC - API klienta (app.forvium.com).

Kazda trasa deklaruje wymagane `Permission` przez `require_org_permission`.
Te same deklaracje obowiazuja klienta i sesje wsparcia.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from forvium.access import OrgAccess, require_org_permission
from forvium.core.clock import clock
from forvium.core.context import Ctx, DomainError, get_ctx
from forvium.organizations.models import DiagnosticEvent, Membership, OrgUnit, Technology
from forvium.organizations.rbac import OrgRole
from forvium.organizations.rbac import Permission as P
from forvium.core.i18n import L

router = APIRouter(prefix="/api/app/orgs/{org_id}", tags=["organizations"])


def _units(ctx: Ctx, access: OrgAccess) -> list[OrgUnit]:
    units = list(ctx.db.scalars(select(OrgUnit).where(OrgUnit.organization_id == access.organization.id)))
    if access.unit_ids is not None:
        units = [u for u in units if u.id in access.unit_ids]
    return units


def _technologies(ctx: Ctx, access: OrgAccess) -> list[Technology]:
    techs = list(ctx.db.scalars(select(Technology).where(Technology.organization_id == access.organization.id)))
    if access.unit_ids is not None:
        techs = [t for t in techs if t.unit_id in access.unit_ids]
    return techs


# ------------------------------------------------------------------ odczyt


@router.get("/dashboard")
def dashboard(access: OrgAccess = Depends(require_org_permission(P.DASHBOARD_READ)), ctx: Ctx = Depends(get_ctx)):
    techs = _technologies(ctx, access)
    cves = [c for t in techs for c in (t.cves or [])]
    out = {
        "organization": {"id": access.organization.id, "name": access.organization.name},
        "units": len(_units(ctx, access)),
        "technologies": len(techs),
    }
    # Liczby CVE tylko, gdy uprawnienia (lub zgoda) je obejmuja.
    if P.CVES_READ in access.permissions:
        out["cves"] = {
            "total": len(cves),
            "critical": sum(1 for c in cves if c.get("severity") == "critical"),
            "high": sum(1 for c in cves if c.get("severity") == "high"),
        }
    return out


@router.get("/units")
def units(access: OrgAccess = Depends(require_org_permission(P.UNITS_READ)), ctx: Ctx = Depends(get_ctx)):
    return {"units": [{"id": u.id, "name": u.name, "parent_id": u.parent_id} for u in _units(ctx, access)]}


@router.get("/technologies")
def technologies(access: OrgAccess = Depends(require_org_permission(P.TECHNOLOGIES_READ)),
                 ctx: Ctx = Depends(get_ctx)):
    return {"technologies": [{"id": t.id, "unit_id": t.unit_id, "name": t.name, "version": t.version}
                             for t in _technologies(ctx, access)]}


@router.get("/cves")
def cves(access: OrgAccess = Depends(require_org_permission(P.CVES_READ)), ctx: Ctx = Depends(get_ctx)):
    items = [{"technology_id": t.id, "technology": t.name, **c}
             for t in _technologies(ctx, access) for c in (t.cves or [])]
    return {"cves": items}


@router.get("/config/status")
def config_status(access: OrgAccess = Depends(require_org_permission(P.CONFIG_READ))):
    org = access.organization
    # Wylacznie stan konfiguracji - bez hostow, loginow, sekretow czy adresow webhookow.
    return {
        "smtp_configured": bool(org.smtp_config),
        "webhooks_count": len(org.webhooks or []),
        "secrets_count": len(org.secrets or {}),
        "settings_keys": sorted((org.settings or {}).keys()),
        "subscription_plan": org.subscription_plan,
    }


@router.get("/errors")
def errors(access: OrgAccess = Depends(require_org_permission(P.ERRORS_READ)), ctx: Ctx = Depends(get_ctx)):
    rows = ctx.db.scalars(
        select(DiagnosticEvent).where(DiagnosticEvent.organization_id == access.organization.id)
        .order_by(DiagnosticEvent.created_at.desc()).limit(200)
    )
    return {"errors": [{"id": e.id, "level": e.level, "component": e.component, "message": e.message,
                        "created_at": e.created_at.isoformat()} for e in rows]}


@router.get("/members")
def members(access: OrgAccess = Depends(require_org_permission(P.MEMBERS_READ)), ctx: Ctx = Depends(get_ctx)):
    from forvium.identity.models import User

    rows = ctx.db.execute(
        select(User, Membership.role).join(Membership, Membership.user_id == User.id)
        .where(Membership.organization_id == access.organization.id)
    ).all()
    from forvium.platform_admin.manage import _account_state

    return {"members": [{"user_id": u.id, "email": u.email, "display_name": u.display_name, "role": r,
                         "state": _account_state(u)} for u, r in rows]}


# ------------------------------------------------------- zapis i operacje wrazliwe


class SettingsIn(BaseModel):
    settings: dict


@router.put("/settings")
def update_settings(body: SettingsIn, access: OrgAccess = Depends(require_org_permission(P.SETTINGS_UPDATE))):
    access.organization.settings = {**(access.organization.settings or {}), **body.settings}
    return {"ok": True}


class RoleIn(BaseModel):
    role: OrgRole


@router.put("/members/{user_id}/role")
def change_role(user_id: str, body: RoleIn, access: OrgAccess = Depends(require_org_permission(P.MEMBERS_MANAGE)),
                ctx: Ctx = Depends(get_ctx)):
    m = ctx.db.scalar(select(Membership).where(Membership.organization_id == access.organization.id,
                                               Membership.user_id == user_id))
    if m is None:
        raise DomainError(404, "member_not_found", "Nie znaleziono członka.")
    m.role = body.role
    return {"ok": True}


class InviteIn(BaseModel):
    email: str
    display_name: str = Field(min_length=2, max_length=200)
    role: OrgRole = OrgRole.MEMBER


@router.post("/members")
def invite_member(body: InviteIn, access: OrgAccess = Depends(require_org_permission(P.MEMBERS_MANAGE)),
                  ctx: Ctx = Depends(get_ctx)):
    """Zaproszenie do organizacji. Nowe konto uzytkownik aktywuje sam (link w e-mailu),
    istniejace konto klienta zostaje dodane od razu. Konta operatorow Forvium nie mozna dodac."""
    from forvium.identity import activation
    from forvium.identity.models import User
    from forvium.platform_admin.manage import EMAIL_RE

    org, actor = access.organization, access.principal.actor
    email = body.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise DomainError(422, "email_invalid", "Nieprawidłowy adres e-mail.")
    if body.role == OrgRole.OWNER and ctx.db.scalar(select(Membership.role).where(
            Membership.organization_id == org.id, Membership.user_id == actor.id)) != OrgRole.OWNER:
        raise DomainError(403, "owner_required", "Właściciela może dodać tylko właściciel.")
    user = ctx.db.scalar(select(User).where(User.email == email))
    if user is not None and user.platform_role is not None:
        raise DomainError(409, "operator_account", "Konta operatora Forvium nie można dodać do organizacji.")
    if user is not None and ctx.db.scalar(select(Membership.id).where(Membership.organization_id == org.id,
                                                                      Membership.user_id == user.id)):
        raise DomainError(409, "already_member", "Ta osoba już należy do organizacji.")
    new_account = user is None
    if new_account:
        user = User(email=email, display_name=body.display_name.strip(),
                    password_hash=activation.unusable_password_hash(), is_active=False, created_at=clock.now())
        ctx.db.add(user)
        ctx.db.flush()
    ctx.db.add(Membership(organization_id=org.id, user_id=user.id, role=body.role))
    ctx.db.flush()
    if new_account:
        activation.issue(ctx, user, kind="user", created_by=actor.id, actor_type="user")
    else:
        ctx.notifications.notify(ctx.db, [user], event="organizations.member_added",
                                 title=L("Dodano Cię do organizacji {org}", org=org.name),
                                 body=L("Rola: {role}. Dodał(a): {who}.", role=body.role, who=actor.email),
                                 organization_id=org.id)
    ctx.audit.log(ctx.db, "organizations.member.invited", actor_user_id=actor.id, actor_type="user",
                  organization_id=org.id, ip_address=ctx.ip,
                  details={"user_id": user.id, "role": body.role, "new_account": new_account})
    return {"member": {"user_id": user.id, "email": user.email, "role": body.role,
                       "state": "pending_activation" if new_account else "active"}}


class ResetAccessIn(BaseModel):
    mfa_code: str | None = None


@router.post("/members/{user_id}/reset-access")
def reset_member_access(user_id: str, body: ResetAccessIn,
                        access: OrgAccess = Depends(require_org_permission(P.MEMBERS_MANAGE)),
                        ctx: Ctx = Depends(get_ctx)):
    """Pracownik zgubil telefon albo haslo: konto wraca do aktywacji, link idzie na jego e-mail.

    Tylko dla osob nalezacych wylacznie do tej organizacji (inaczej wlasciciel jednej organizacji
    moglby odciac komus dostep do innych) - pozostale przypadki obsluguje Forvium."""
    from forvium.identity import activation
    from forvium.identity.models import User
    from forvium.identity.service import consume_totp

    actor, org = access.principal.actor, access.organization
    action = "organizations.member.reset_access"
    who = {"actor_user_id": actor.id, "actor_type": "user", "organization_id": org.id, "ip_address": ctx.ip}

    def deny(status: int, code: str, message: str) -> DomainError:
        ctx.audit.record(action, outcome="denied", details={"reason": code, "user_id": user_id}, **who)
        return DomainError(status, code, message)

    member = ctx.db.scalar(select(Membership).where(Membership.organization_id == org.id,
                                                    Membership.user_id == user_id))
    target = ctx.db.get(User, user_id) if member else None
    if target is None:
        raise DomainError(404, "member_not_found", "Nie znaleziono członka.")
    if target.id == actor.id:
        raise deny(403, "self_reset_forbidden", "Nie możesz zresetować własnego dostępu - poproś innego administratora.")
    actor_role = ctx.db.scalar(select(Membership.role).where(Membership.organization_id == org.id,
                                                             Membership.user_id == actor.id))
    if member.role == OrgRole.OWNER and actor_role != OrgRole.OWNER:
        raise deny(403, "owner_required", "Dostęp właściciela może zresetować tylko inny właściciel.")
    if target.blocked_at is not None or target.platform_role is not None:
        raise deny(409, "not_resettable", "Tego konta nie można zresetować.")
    other_orgs = ctx.db.scalar(select(func.count()).select_from(Membership).where(
        Membership.user_id == target.id, Membership.organization_id != org.id))
    if other_orgs:
        raise deny(409, "member_of_other_organizations",
                   "Ta osoba należy też do innych organizacji - reset dostępu wykona support Forvium.")
    ctx.throttle.check("mfa_stepup", actor.id, **who)
    if actor.mfa_secret and not consume_totp(actor, body.mfa_code):
        ctx.throttle.fail("mfa_stepup", actor.id, **who)
        raise deny(401, "mfa_reverification_failed", "Potwierdź operację kodem z aplikacji uwierzytelniającej.")
    activation.reset_access(ctx, target, created_by=actor.id, actor_type="user")
    ctx.audit.log(ctx.db, "organizations.member.access_reset", details={"user_id": target.id}, **who)
    from forvium.support_access.service import _org_approvers

    ctx.notifications.notify(ctx.db, _org_approvers(ctx, org.id, exclude_user_id=actor.id),
                             event="organizations.member.access_reset", title=L("Zresetowano dostęp {email}", email=target.email),
                             body=L("Zresetował(a): {who}. Nowy link aktywacyjny wysłano na adres tej osoby.",
                                    who=actor.email),
                             organization_id=org.id)
    return {"member": {"user_id": target.id, "email": target.email, "state": "pending_activation"}}


@router.delete("/members/{user_id}")
def remove_member(user_id: str, access: OrgAccess = Depends(require_org_permission(P.MEMBERS_MANAGE)),
                  ctx: Ctx = Depends(get_ctx)):
    m = ctx.db.scalar(select(Membership).where(Membership.organization_id == access.organization.id,
                                               Membership.user_id == user_id))
    if m is not None:
        ctx.db.delete(m)
    return {"ok": True}


@router.delete("")
def delete_organization(access: OrgAccess = Depends(require_org_permission(P.ORG_DELETE))):
    access.organization.deleted_at = clock.now()
    return {"ok": True}


@router.get("/export")
def export_data(access: OrgAccess = Depends(require_org_permission(P.DATA_EXPORT)), ctx: Ctx = Depends(get_ctx)):
    return {"technologies": [{"name": t.name, "version": t.version, "cves": t.cves}
                             for t in _technologies(ctx, access)]}


@router.post("/billing/payments")
def pay(access: OrgAccess = Depends(require_org_permission(P.BILLING_PAY))):
    return {"ok": True}


class SubscriptionIn(BaseModel):
    plan: str


@router.put("/subscription")
def change_subscription(body: SubscriptionIn, access: OrgAccess = Depends(require_org_permission(P.SUBSCRIPTION_MANAGE))):
    access.organization.subscription_plan = body.plan
    return {"ok": True}


class SmtpIn(BaseModel):
    host: str
    port: int
    username: str
    password: str


@router.put("/smtp")
def update_smtp(body: SmtpIn, access: OrgAccess = Depends(require_org_permission(P.SMTP_MANAGE))):
    access.organization.smtp_config = body.model_dump()
    return {"ok": True}


class WebhookIn(BaseModel):
    url: str


@router.post("/webhooks")
def add_webhook(body: WebhookIn, access: OrgAccess = Depends(require_org_permission(P.WEBHOOKS_MANAGE))):
    access.organization.webhooks = [*(access.organization.webhooks or []), body.url]
    return {"ok": True}


@router.get("/secrets")
def read_secrets(access: OrgAccess = Depends(require_org_permission(P.SECRETS_READ))):
    return {"secrets": access.organization.secrets}


@router.get("/api-tokens")
def api_tokens(access: OrgAccess = Depends(require_org_permission(P.API_TOKENS_MANAGE))):
    return {"tokens": []}
