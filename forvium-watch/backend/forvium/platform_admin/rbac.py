"""Platform Administration: role i uprawnienia operatorow Forvium."""

from __future__ import annotations

from enum import StrEnum


class PlatformPermission(StrEnum):
    USERS_READ = "platform.users.read"
    TICKETS_READ = "platform.tickets.read"
    SUPPORT_ACCESS_REQUEST = "platform.support_access.request"
    SUPPORT_ACCESS_START = "platform.support_access.start"
    AUDIT_READ = "platform.audit.read"
    # Zarezerwowane dla przyszlej procedury Break Glass; nie nadawane zadnej roli.
    BREAK_GLASS = "platform.break_glass"


class PlatformRole(StrEnum):
    SUPPORT_L1 = "support_l1"
    SUPPORT_L2 = "support_l2"
    PLATFORM_ADMIN = "platform_admin"


PLATFORM_ROLE_PERMISSIONS: dict[PlatformRole, frozenset[PlatformPermission]] = {
    PlatformRole.SUPPORT_L1: frozenset(
        {
            PlatformPermission.USERS_READ,
            PlatformPermission.TICKETS_READ,
            PlatformPermission.SUPPORT_ACCESS_REQUEST,
            PlatformPermission.SUPPORT_ACCESS_START,
        }
    ),
    PlatformRole.SUPPORT_L2: frozenset(
        {
            PlatformPermission.USERS_READ,
            PlatformPermission.TICKETS_READ,
            PlatformPermission.SUPPORT_ACCESS_REQUEST,
            PlatformPermission.SUPPORT_ACCESS_START,
        }
    ),
    PlatformRole.PLATFORM_ADMIN: frozenset(set(PlatformPermission) - {PlatformPermission.BREAK_GLASS}),
}


def platform_permissions(role: str | None) -> frozenset[PlatformPermission]:
    if not role:
        return frozenset()
    try:
        return PLATFORM_ROLE_PERMISSIONS[PlatformRole(role)]
    except ValueError:
        return frozenset()
