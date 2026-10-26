"""Jedyny model uprawnien w obrebie organizacji.

Sesja wsparcia NIE ma wlasnego systemu uprawnien: jej efektywny zestaw
uprawnien jest obliczany z tych samych `Permission` (patrz
`support_access.scopes.effective_support_permissions`) i sprawdzany przez ta
sama zaleznosc `require_org_permission`.
"""

from __future__ import annotations

from enum import StrEnum


class Permission(StrEnum):
    # Odczyt
    DASHBOARD_READ = "org.dashboard.read"
    UNITS_READ = "org.units.read"
    TECHNOLOGIES_READ = "org.technologies.read"
    CVES_READ = "org.cves.read"
    CONFIG_READ = "org.config.read"
    ERRORS_READ = "org.errors.read"
    MEMBERS_READ = "org.members.read"
    # Zapis / operacje wrazliwe
    SETTINGS_UPDATE = "org.settings.update"
    UNITS_MANAGE = "org.units.manage"
    MEMBERS_MANAGE = "org.members.manage"
    ORG_DELETE = "org.delete"
    DATA_EXPORT = "org.data.export"
    BILLING_PAY = "org.billing.pay"
    SUBSCRIPTION_MANAGE = "org.subscription.manage"
    SMTP_MANAGE = "org.smtp.manage"
    WEBHOOKS_MANAGE = "org.webhooks.manage"
    SECRETS_READ = "org.secrets.read"
    API_TOKENS_MANAGE = "org.api_tokens.manage"
    # Support Access po stronie klienta
    SUPPORT_ACCESS_VIEW = "org.support_access.view"
    SUPPORT_ACCESS_APPROVE = "org.support_access.approve"
    # Zgloszenia do supportu Forvium (Support Tickets)
    TICKETS_READ = "org.tickets.read"
    TICKETS_CREATE = "org.tickets.create"


class OrgRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


_READ = {
    Permission.DASHBOARD_READ,
    Permission.UNITS_READ,
    Permission.TECHNOLOGIES_READ,
    Permission.CVES_READ,
    Permission.CONFIG_READ,
    Permission.ERRORS_READ,
    Permission.MEMBERS_READ,
    Permission.SUPPORT_ACCESS_VIEW,
    Permission.TICKETS_READ,
}

ROLE_PERMISSIONS: dict[OrgRole, frozenset[Permission]] = {
    OrgRole.OWNER: frozenset(Permission),
    OrgRole.ADMIN: frozenset(set(Permission) - {Permission.ORG_DELETE}),
    OrgRole.MEMBER: frozenset(_READ | {Permission.DATA_EXPORT, Permission.TICKETS_CREATE}),
    OrgRole.VIEWER: frozenset(_READ - {Permission.MEMBERS_READ}),
}


def permissions_for_role(role: str) -> frozenset[Permission]:
    try:
        return ROLE_PERMISSIONS[OrgRole(role)]
    except ValueError:
        return frozenset()
