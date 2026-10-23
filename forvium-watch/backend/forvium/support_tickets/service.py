from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from forvium.support_tickets.models import SupportTicket, TicketStatus


def find_active_ticket(db: Session, number: str, organization_id: str) -> SupportTicket | None:
    """Zwraca otwarte zgloszenie nalezace do danej organizacji albo None."""
    ticket = db.scalar(select(SupportTicket).where(SupportTicket.number == number.strip()))
    if ticket is None or ticket.organization_id != organization_id:
        return None
    if ticket.status == TicketStatus.CLOSED:
        return None
    return ticket


def is_ticket_active(db: Session, ticket_id: str) -> bool:
    ticket = db.get(SupportTicket, ticket_id)
    return ticket is not None and ticket.status != TicketStatus.CLOSED
