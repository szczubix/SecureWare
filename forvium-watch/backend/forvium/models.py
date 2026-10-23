"""Rejestr wszystkich modeli (import na potrzeby Base.metadata)."""

from forvium.audit.models import AuditEvent  # noqa: F401
from forvium.identity.models import User, UserSession  # noqa: F401
from forvium.notifications.models import EmailOutbox, Notification  # noqa: F401
from forvium.organizations.models import (  # noqa: F401
    DiagnosticEvent,
    Membership,
    Organization,
    OrgUnit,
    Technology,
)
from forvium.support_access.models import (  # noqa: F401
    SupportAccessRequest,
    SupportConsent,
    SupportSession,
)
from forvium.support_tickets.models import SupportTicket  # noqa: F401
