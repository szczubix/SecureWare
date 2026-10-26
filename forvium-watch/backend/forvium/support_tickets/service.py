"""Support Tickets: zgloszenia klientow i Forvium, rozmowa w zgloszeniu, statusy.

Dostep serwisowy zawsze wymaga otwartego zgloszenia danej organizacji, wiec zamkniecie
zgloszenia (przez klienta albo Forvium) konczy sesje wsparcia na nim oparte.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from forvium.core.clock import clock
from forvium.support_tickets.models import SupportTicket, SupportTicketMessage, TicketPriority, TicketStatus

PRIORITY_LABELS = {"low": "niski", "normal": "normalny", "high": "wysoki", "critical": "krytyczny"}
STATUS_LABELS = {"open": "otwarte", "in_progress": "w toku", "closed": "zamknięte"}
MAX_BODY = 10_000


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


def next_number(db: Session) -> str:
    numbers = [int(n.split("-", 1)[1]) for n in db.scalars(select(SupportTicket.number))
               if n.startswith("FW-") and n[3:].isdigit()]
    return f"FW-{max(numbers, default=1000) + 1}"


def _iso(d):
    return d.isoformat() + "Z" if d else None


def ticket_out(t: SupportTicket, *, organization_name: str | None = None, emails: dict | None = None) -> dict:
    out = {"id": t.id, "number": t.number, "organization_id": t.organization_id, "subject": t.subject,
           "status": t.status, "priority": t.priority or TicketPriority.NORMAL,
           "reporter_user_id": t.reporter_user_id, "created_by_customer": bool(t.created_by_customer),
           "created_at": _iso(t.created_at), "updated_at": _iso(t.updated_at or t.created_at),
           "closed_at": _iso(t.closed_at)}
    if organization_name is not None:
        out["organization_name"] = organization_name
    if emails is not None:
        out["reporter_email"] = emails.get(t.reporter_user_id)
    return out


def message_out(m: SupportTicketMessage, emails: dict) -> dict:
    return {"id": m.id, "author_side": m.author_side, "author_email": emails.get(m.author_user_id),
            "internal": bool(m.internal), "body": m.body, "created_at": _iso(m.created_at)}


def messages(db: Session, ticket: SupportTicket, *, include_internal: bool) -> list[SupportTicketMessage]:
    stmt = select(SupportTicketMessage).where(SupportTicketMessage.ticket_id == ticket.id) \
        .order_by(SupportTicketMessage.created_at, SupportTicketMessage.id)
    if not include_internal:
        stmt = stmt.where(SupportTicketMessage.internal.is_(False))
    return list(db.scalars(stmt))


def create(ctx, *, organization_id: str, subject: str, description: str | None, priority: str,
           reporter_user_id: str | None, by_customer: bool) -> SupportTicket:
    now = clock.now()
    ticket = SupportTicket(number=next_number(ctx.db), organization_id=organization_id, subject=subject.strip(),
                           description=(description or "").strip() or None, priority=priority,
                           reporter_user_id=reporter_user_id, created_by_customer=by_customer,
                           created_at=now, updated_at=now)
    ctx.db.add(ticket)
    ctx.db.flush()
    return ticket


def add_message(ctx, ticket: SupportTicket, *, author_user_id: str, side: str, body: str,
                internal: bool = False) -> SupportTicketMessage:
    msg = SupportTicketMessage(ticket_id=ticket.id, organization_id=ticket.organization_id,
                               author_user_id=author_user_id, author_side=side, internal=internal,
                               body=body.strip(), created_at=clock.now())
    ctx.db.add(msg)
    ticket.updated_at = msg.created_at
    # Odpowiedz Forvium na nowe zgloszenie = praca w toku.
    if side == "forvium" and not internal and ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS
    ctx.db.flush()
    return msg


def set_status(ctx, ticket: SupportTicket, status: TicketStatus, *, by_user_id: str, actor_type: str) -> int:
    """Zmienia status; zamkniecie konczy aktywne sesje wsparcia na tym zgloszeniu. Zwraca ich liczbe."""
    from forvium.support_access.models import SessionStatus, SupportSession
    from forvium.support_access.service import _terminate_session

    ticket.status = status
    ticket.updated_at = clock.now()
    ticket.closed_at = clock.now() if status == TicketStatus.CLOSED else None
    if status != TicketStatus.CLOSED:
        return 0
    sessions = list(ctx.db.scalars(select(SupportSession).where(SupportSession.status == SessionStatus.ACTIVE,
                                                                SupportSession.ticket_id == ticket.id)))
    for s in sessions:
        _terminate_session(ctx, s, SessionStatus.REVOKED, "ticket_closed", by_user_id, actor_type=actor_type)
    return len(sessions)


def thread_participants(db: Session, ticket: SupportTicket, side: str) -> set[str]:
    return set(db.scalars(select(SupportTicketMessage.author_user_id).where(
        SupportTicketMessage.ticket_id == ticket.id, SupportTicketMessage.author_side == side)))
