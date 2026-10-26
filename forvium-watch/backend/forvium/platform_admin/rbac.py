"""Platform Administration: role i uprawnienia operatorow Forvium."""

from __future__ import annotations

from enum import StrEnum


class PlatformPermission(StrEnum):
    USERS_READ = "platform.users.read"
    TICKETS_READ = "platform.tickets.read"
    SUPPORT_ACCESS_REQUEST = "platform.support_access.request"
    SUPPORT_ACCESS_START = "platform.support_access.start"
    AUDIT_READ = "platform.audit.read"
    # Nadzor: podglad wszystkich sesji wsparcia i wymuszone zakonczenie.
    SUPPORT_OVERSIGHT = "platform.support_access.oversight"
    # Break Glass: wniosek (operator), zatwierdzenie i przeglad (oficer bezpieczenstwa).
    BREAK_GLASS_REQUEST = "platform.break_glass.request"
    BREAK_GLASS_APPROVE = "platform.break_glass.approve"
    BREAK_GLASS_REVIEW = "platform.break_glass.review"
    # Zarzadzanie platforma (admin.forvium.com).
    ORGS_MANAGE = "platform.orgs.manage"
    USERS_MANAGE = "platform.users.manage"  # blokada/odblokowanie kont klientow, ponowna aktywacja
    TICKETS_MANAGE = "platform.tickets.manage"
    OPERATORS_MANAGE = "platform.operators.manage"
    # Zatwierdzanie nadania roli uprzywilejowanej (4 oczy) - oficer bezpieczenstwa.
    OPERATORS_APPROVE = "platform.operators.approve"


class PlatformRole(StrEnum):
    SUPPORT_L1 = "support_l1"
    SUPPORT_L2 = "support_l2"
    SUPPORT_LEAD = "support_lead"
    SECURITY_OFFICER = "security_officer"
    PLATFORM_ADMIN = "platform_admin"


_SUPPORT_BASE = frozenset(
    {
        PlatformPermission.USERS_READ,
        PlatformPermission.TICKETS_READ,
        PlatformPermission.SUPPORT_ACCESS_REQUEST,
        PlatformPermission.SUPPORT_ACCESS_START,
    }
)

PLATFORM_ROLE_PERMISSIONS: dict[PlatformRole, frozenset[PlatformPermission]] = {
    PlatformRole.SUPPORT_L1: _SUPPORT_BASE,
    PlatformRole.SUPPORT_L2: _SUPPORT_BASE | {PlatformPermission.BREAK_GLASS_REQUEST},
    PlatformRole.SUPPORT_LEAD: _SUPPORT_BASE | {
        PlatformPermission.AUDIT_READ,
        PlatformPermission.SUPPORT_OVERSIGHT,
        PlatformPermission.BREAK_GLASS_REQUEST,
        # Zgloszenia zaklada i zamyka kierownik (dostep serwisowy wymaga otwartego zgloszenia,
        # wiec operator L1/L2 nie tworzy sobie podstawy dostepu sam).
        PlatformPermission.TICKETS_MANAGE,
    },
    # Oficer bezpieczenstwa zatwierdza i przeglada Break Glass, ale sam nie otwiera sesji.
    PlatformRole.SECURITY_OFFICER: frozenset(
        {
            PlatformPermission.USERS_READ,
            PlatformPermission.TICKETS_READ,
            PlatformPermission.AUDIT_READ,
            PlatformPermission.SUPPORT_OVERSIGHT,
            PlatformPermission.BREAK_GLASS_APPROVE,
            PlatformPermission.BREAK_GLASS_REVIEW,
            PlatformPermission.OPERATORS_APPROVE,
        }
    ),
    # Administrator platformy nie uczestniczy w Break Glass (rozdzial obowiazkow).
    PlatformRole.PLATFORM_ADMIN: frozenset(
        set(PlatformPermission)
        - {
            PlatformPermission.BREAK_GLASS_REQUEST,
            PlatformPermission.BREAK_GLASS_APPROVE,
            PlatformPermission.BREAK_GLASS_REVIEW,
            # Nie zatwierdza nadania rol uprzywilejowanych, ktore sam zleca.
            PlatformPermission.OPERATORS_APPROVE,
        }
    ),
}

# Role, ktorych nadanie wymaga zatwierdzenia przez oficera bezpieczenstwa.
PRIVILEGED_ROLES = frozenset({PlatformRole.PLATFORM_ADMIN, PlatformRole.SECURITY_OFFICER})


def platform_permissions(role: str | None) -> frozenset[PlatformPermission]:
    if not role:
        return frozenset()
    try:
        return PLATFORM_ROLE_PERMISSIONS[PlatformRole(role)]
    except ValueError:
        return frozenset()
