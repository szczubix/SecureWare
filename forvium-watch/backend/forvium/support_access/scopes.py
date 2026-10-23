"""Zakresy dostepu serwisowego mapowane na istniejace uprawnienia RBAC.

Efektywne uprawnienia sesji wsparcia:

    uprawnienia roli uzytkownika referencyjnego
  & uprawnienia wynikajace z zakresow w zgodzie klienta
  & uprawnienia wynikajace z zakresow dopuszczonych dla roli operatora
  & SUPPORT_READ_ONLY_PERMISSIONS
  - SUPPORT_FORBIDDEN_PERMISSIONS

Sesja nigdy nie ma wiecej, niz ma uzytkownik referencyjny, niz dopuszcza
rola operatora i niz zatwierdzil klient.
"""

from __future__ import annotations

from enum import StrEnum

from forvium.organizations.rbac import Permission, permissions_for_role
from forvium.platform_admin.rbac import PlatformRole


class SupportScope(StrEnum):
    DASHBOARD = "dashboard"
    UNITS = "units"
    TECHNOLOGIES_CVE = "technologies_cve"
    DIAGNOSTICS = "diagnostics"


SCOPE_PERMISSIONS: dict[SupportScope, frozenset[Permission]] = {
    SupportScope.DASHBOARD: frozenset({Permission.DASHBOARD_READ}),
    SupportScope.UNITS: frozenset({Permission.UNITS_READ}),
    SupportScope.TECHNOLOGIES_CVE: frozenset({Permission.TECHNOLOGIES_READ, Permission.CVES_READ}),
    SupportScope.DIAGNOSTICS: frozenset({Permission.CONFIG_READ, Permission.ERRORS_READ}),
}

# Jedyne uprawnienia, jakie moga w ogole trafic do sesji wsparcia (READ_ONLY).
SUPPORT_READ_ONLY_PERMISSIONS: frozenset[Permission] = frozenset().union(*SCOPE_PERMISSIONS.values())

# Twarda lista zakazow - niezalezna od zakresu, roli i trybu.
SUPPORT_FORBIDDEN_PERMISSIONS: frozenset[Permission] = frozenset(
    {
        Permission.SETTINGS_UPDATE,
        Permission.UNITS_MANAGE,
        Permission.MEMBERS_MANAGE,
        Permission.ORG_DELETE,
        Permission.DATA_EXPORT,
        Permission.BILLING_PAY,
        Permission.SUBSCRIPTION_MANAGE,
        Permission.SMTP_MANAGE,
        Permission.WEBHOOKS_MANAGE,
        Permission.SECRETS_READ,
        Permission.API_TOKENS_MANAGE,
        Permission.SUPPORT_ACCESS_APPROVE,
        Permission.SUPPORT_ACCESS_VIEW,
        Permission.MEMBERS_READ,
    }
)

# Maksymalne zakresy, o jakie moze wnioskowac operator danej roli platformowej.
OPERATOR_SCOPE_CAP: dict[PlatformRole, frozenset[SupportScope]] = {
    PlatformRole.SUPPORT_L1: frozenset({SupportScope.DASHBOARD, SupportScope.UNITS, SupportScope.DIAGNOSTICS}),
    PlatformRole.SUPPORT_L2: frozenset(SupportScope),
    PlatformRole.SUPPORT_LEAD: frozenset(SupportScope),
    PlatformRole.PLATFORM_ADMIN: frozenset(SupportScope),
}


def operator_scope_cap(platform_role: str | None) -> frozenset[SupportScope]:
    try:
        return OPERATOR_SCOPE_CAP.get(PlatformRole(platform_role or ""), frozenset())
    except ValueError:
        return frozenset()


def parse_scopes(values: list[str]) -> frozenset[SupportScope]:
    return frozenset(SupportScope(v) for v in values)


def scope_permissions(scopes: frozenset[SupportScope]) -> frozenset[Permission]:
    return frozenset().union(*(SCOPE_PERMISSIONS[s] for s in scopes)) if scopes else frozenset()


def effective_support_permissions(
    *,
    reference_user_role: str | None,
    consent_scopes: frozenset[SupportScope],
    operator_platform_role: str | None,
) -> frozenset[Permission]:
    allowed_scopes = consent_scopes & operator_scope_cap(operator_platform_role)
    perms = (
        permissions_for_role(reference_user_role or "")
        & scope_permissions(allowed_scopes)
        & SUPPORT_READ_ONLY_PERMISSIONS
    )
    return frozenset(perms - SUPPORT_FORBIDDEN_PERMISSIONS)
