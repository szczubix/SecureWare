"""Zgloszenia: klient (app.forvium.com) i support Forvium (admin.forvium.com).

Klient widzi tylko zgloszenia swojej organizacji i wiadomosci niewewnetrzne. Sesja wsparcia
nie ma uprawnien do zgloszen (twarda lista zakazow), wiec operator w trybie wsparcia nie
czyta ani nie pisze zgloszen w imieniu klienta - robi to w panelu admin, pod swoim nazwiskiem.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select

from forvium.access import OperatorPrincipal, OrgAccess, require_org_permission, require_platform_permission
from forvium.core.context import Ctx, DomainError, get_ctx
from forvium.identity.models import User
from forvium.organizations.models import Organization
from forvium.organizations.rbac import Permission as P
from forvium.platform_admin.rbac import PlatformPermission as PP, platform_permissions
from forvium.support_tickets import service
from forvium.support_tickets.models import SupportTicket, TicketPriority, TicketStatus

app_router = APIRouter(prefix="/api/app/orgs/{org_id}/tickets", tags=["support tickets (app)"])
admin_router = APIRouter(prefix="/api/admin/tickets", tags=["support tickets (admin)"])


class TicketIn(BaseModel):
    subject: str = Field(min_length=3, max_length=300)
    description: str = Field(min_length=10, max_length=service.MAX_BODY)
    priority: TicketPriority = TicketPriority.NORMAL


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=service.MAX_BODY)


class AdminMessageIn(MessageIn):
    internal: bool = False


def _emails(ctx: Ctx, ids) -> dict:
    ids = {i for i in ids if i}
    return dict(ctx.db.execute(select(User.id, User.email).where(User.id.in_(ids))).all()) if ids else {}


def _access_requests(ctx: Ctx, ticket: SupportTicket) -> list[dict]:
    from forvium.support_access.models import SupportAccessRequest

    rows = list(ctx.db.scalars(select(SupportAccessRequest).where(SupportAccessRequest.ticket_id == ticket.id)
                               .order_by(SupportAccessRequest.created_at)))
    emails = _emails(ctx, [r.operator_user_id for r in rows])
    return [{"id": r.id, "created_at": service._iso(r.created_at), "status": r.status, "mode": r.mode,
             "operator_email": emails.get(r.operator_user_id), "scopes": r.requested_scopes} for r in rows]


def _forvium_staff(ctx: Ctx, permission: PP) -> list[User]:
    return [u for u in ctx.db.scalars(select(User).where(User.platform_role.is_not(None), User.is_active.is_(True)))
            if permission in platform_permissions(u.platform_role)]


def _customers(ctx: Ctx, ticket: SupportTicket, exclude: str | None = None) -> list[User]:
    ids = service.thread_participants(ctx.db, ticket, "customer") | {ticket.reporter_user_id}
    return [u for u in ctx.db.scalars(select(User).where(User.id.in_({i for i in ids if i}), User.is_active.is_(True)))
            if u.id != exclude]


def _forvium_participants(ctx: Ctx, ticket: SupportTicket, exclude: str | None = None) -> list[User]:
    ids = service.thread_participants(ctx.db, ticket, "forvium")
    people = list(ctx.db.scalars(select(User).where(User.id.in_(ids), User.is_active.is_(True)))) if ids else []
    # Nikt z Forvium jeszcze nie odpisal - informujemy osoby zarzadzajace zgloszeniami.
    return [u for u in (people or _forvium_staff(ctx, PP.TICKETS_MANAGE)) if u.id != exclude]


def _org_ticket(ctx: Ctx, access: OrgAccess, ticket_id: str) -> SupportTicket:
    ticket = ctx.db.get(SupportTicket, ticket_id)
    if ticket is None or ticket.organization_id != access.organization.id:
        raise DomainError(404, "ticket_not_found", "Nie znaleziono zgłoszenia.")
    return ticket


def _log(ctx: Ctx, action: str, ticket: SupportTicket, actor: User, actor_type: str, **details) -> None:
    ctx.audit.log(ctx.db, action, actor_user_id=actor.id, actor_type=actor_type, organization_id=ticket.organization_id,
                  ip_address=ctx.ip, details={"ticket": ticket.number, **details})


# ============================================================================ klient


@app_router.get("")
def list_tickets(status: str | None = None, access: OrgAccess = Depends(require_org_permission(P.TICKETS_READ)),
                 ctx: Ctx = Depends(get_ctx)):
    stmt = select(SupportTicket).where(SupportTicket.organization_id == access.organization.id) \
        .order_by(SupportTicket.created_at.desc()).limit(300)
    if status:
        stmt = stmt.where(SupportTicket.status == status)
    rows = list(ctx.db.scalars(stmt))
    emails = _emails(ctx, [t.reporter_user_id for t in rows])
    return {"tickets": [service.ticket_out(t, emails=emails) for t in rows],
            "can_create": P.TICKETS_CREATE in access.permissions}


@app_router.post("")
def create_ticket(body: TicketIn, access: OrgAccess = Depends(require_org_permission(P.TICKETS_CREATE)),
                  ctx: Ctx = Depends(get_ctx)):
    actor = access.principal.actor
    ticket = service.create(ctx, organization_id=access.organization.id, subject=body.subject,
                            description=body.description, priority=body.priority, reporter_user_id=actor.id,
                            by_customer=True)
    _log(ctx, "support_tickets.created", ticket, actor, "user", priority=ticket.priority, side="customer")
    label = service.PRIORITY_LABELS[ticket.priority]
    ctx.notifications.notify(ctx.db, _forvium_staff(ctx, PP.TICKETS_MANAGE), event="support_tickets.created",
                             title=f"Nowe zgłoszenie {ticket.number} ({access.organization.name}, priorytet: {label})",
                             body=f"{ticket.subject}\nZgłasza: {actor.email}. Szczegóły w panelu: Zgłoszenia.",
                             data={"ticket_id": ticket.id})
    return {"ticket": service.ticket_out(ticket)}


@app_router.get("/{ticket_id}")
def ticket_detail(ticket_id: str, access: OrgAccess = Depends(require_org_permission(P.TICKETS_READ)),
                  ctx: Ctx = Depends(get_ctx)):
    ticket = _org_ticket(ctx, access, ticket_id)
    msgs = service.messages(ctx.db, ticket, include_internal=False)
    emails = _emails(ctx, [ticket.reporter_user_id, *(m.author_user_id for m in msgs)])
    return {"ticket": {**service.ticket_out(ticket, emails=emails), "description": ticket.description},
            "messages": [service.message_out(m, emails) for m in msgs],
            "access_requests": _access_requests(ctx, ticket),
            "can_reply": P.TICKETS_CREATE in access.permissions and ticket.status != TicketStatus.CLOSED}


@app_router.post("/{ticket_id}/messages")
def customer_reply(ticket_id: str, body: MessageIn, access: OrgAccess = Depends(require_org_permission(P.TICKETS_CREATE)),
                   ctx: Ctx = Depends(get_ctx)):
    ticket = _org_ticket(ctx, access, ticket_id)
    if ticket.status == TicketStatus.CLOSED:
        raise DomainError(409, "ticket_closed", "Zgłoszenie jest zamknięte - utwórz nowe.")
    actor = access.principal.actor
    msg = service.add_message(ctx, ticket, author_user_id=actor.id, side="customer", body=body.body)
    _log(ctx, "support_tickets.message_added", ticket, actor, "user", side="customer")
    ctx.notifications.notify(ctx.db, _forvium_participants(ctx, ticket), event="support_tickets.customer_reply",
                             title=f"Odpowiedź klienta w {ticket.number}",
                             body=f"{actor.email}: {msg.body[:500]}", data={"ticket_id": ticket.id})
    return {"message": service.message_out(msg, {actor.id: actor.email})}


@app_router.post("/{ticket_id}/close")
def customer_close(ticket_id: str, access: OrgAccess = Depends(require_org_permission(P.TICKETS_CREATE)),
                   ctx: Ctx = Depends(get_ctx)):
    ticket = _org_ticket(ctx, access, ticket_id)
    if ticket.status == TicketStatus.CLOSED:
        return {"ticket": service.ticket_out(ticket), "support_sessions_ended": 0}
    actor = access.principal.actor
    ended = service.set_status(ctx, ticket, TicketStatus.CLOSED, by_user_id=actor.id, actor_type="user")
    _log(ctx, "support_tickets.closed", ticket, actor, "user", side="customer", support_sessions_ended=ended)
    ctx.notifications.notify(ctx.db, _forvium_participants(ctx, ticket), event="support_tickets.closed",
                             title=f"Klient zamknął zgłoszenie {ticket.number}",
                             body=f"Zamknął: {actor.email}. Zakończone sesje wsparcia: {ended}.",
                             data={"ticket_id": ticket.id})
    return {"ticket": service.ticket_out(ticket), "support_sessions_ended": ended}


# ============================================================================ Forvium


@admin_router.get("/{ticket_id}")
def admin_ticket_detail(ticket_id: str, op: OperatorPrincipal = Depends(require_platform_permission(PP.TICKETS_READ)),
                        ctx: Ctx = Depends(get_ctx)):
    ticket = ctx.db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise DomainError(404, "ticket_not_found", "Nie znaleziono zgłoszenia.")
    org = ctx.db.get(Organization, ticket.organization_id)
    msgs = service.messages(ctx.db, ticket, include_internal=True)
    emails = _emails(ctx, [ticket.reporter_user_id, *(m.author_user_id for m in msgs)])
    return {"ticket": {**service.ticket_out(ticket, organization_name=org.name if org else None, emails=emails),
                       "description": ticket.description},
            "messages": [service.message_out(m, emails) for m in msgs],
            "access_requests": _access_requests(ctx, ticket)}


@admin_router.post("/{ticket_id}/messages")
def forvium_reply(ticket_id: str, body: AdminMessageIn,
                  op: OperatorPrincipal = Depends(require_platform_permission(PP.TICKETS_READ)),
                  ctx: Ctx = Depends(get_ctx)):
    ticket = ctx.db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise DomainError(404, "ticket_not_found", "Nie znaleziono zgłoszenia.")
    if ticket.status == TicketStatus.CLOSED and not body.internal:
        raise DomainError(409, "ticket_closed", "Zgłoszenie jest zamknięte - otwórz je ponownie, aby odpowiedzieć klientowi.")
    msg = service.add_message(ctx, ticket, author_user_id=op.user.id, side="forvium", body=body.body,
                              internal=body.internal)
    _log(ctx, "support_tickets.message_added", ticket, op.user, "operator", side="forvium", internal=body.internal)
    if not body.internal:
        ctx.notifications.notify(ctx.db, _customers(ctx, ticket), event="support_tickets.forvium_reply",
                                 title=f"Odpowiedź supportu Forvium w {ticket.number}",
                                 body=f"{msg.body[:1000]}\n\nOdpowiesz w aplikacji: Zgłoszenia.",
                                 organization_id=ticket.organization_id, data={"ticket_id": ticket.id})
    return {"message": service.message_out(msg, {op.user.id: op.user.email})}
