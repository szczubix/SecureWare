"""Platform Administration - uzytkownicy, zgloszenia, audyt (admin.forvium.com)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select

from forvium.access import OperatorPrincipal, get_operator, require_platform_permission
from forvium.core.context import Ctx, DomainError, get_ctx
from forvium.identity.models import User
from forvium.notifications.models import Notification
from forvium.organizations.models import Membership, Organization
from forvium.platform_admin.rbac import PlatformPermission as PP
from forvium.support_tickets.models import SupportTicket

router = APIRouter(prefix="/api/admin", tags=["platform admin"])


@router.get("/users")
def list_users(q: str = "", op: OperatorPrincipal = Depends(require_platform_permission(PP.USERS_READ)),
               ctx: Ctx = Depends(get_ctx)):
    stmt = select(User).where(User.platform_role.is_(None)).order_by(User.email).limit(100)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.display_name.ilike(like)))
    return {"users": [{"id": u.id, "email": u.email, "display_name": u.display_name, "is_active": u.is_active}
                      for u in ctx.db.scalars(stmt)]}


@router.get("/users/{user_id}")
def user_detail(user_id: str, op: OperatorPrincipal = Depends(require_platform_permission(PP.USERS_READ)),
                ctx: Ctx = Depends(get_ctx)):
    user = ctx.db.get(User, user_id)
    if user is None or user.platform_role is not None:
        raise DomainError(404, "user_not_found", "Nie znaleziono uzytkownika.")
    rows = ctx.db.execute(select(Organization, Membership.role)
                          .join(Membership, Membership.organization_id == Organization.id)
                          .where(Membership.user_id == user.id, Organization.deleted_at.is_(None))).all()
    return {
        "user": {"id": user.id, "email": user.email, "display_name": user.display_name, "is_active": user.is_active},
        "organizations": [{"id": o.id, "name": o.name, "role": r} for o, r in rows],
    }


@router.get("/tickets")
def list_tickets(organization_id: str | None = None,
                 op: OperatorPrincipal = Depends(require_platform_permission(PP.TICKETS_READ)),
                 ctx: Ctx = Depends(get_ctx)):
    stmt = select(SupportTicket).order_by(SupportTicket.created_at.desc()).limit(200)
    if organization_id:
        stmt = stmt.where(SupportTicket.organization_id == organization_id)
    return {"tickets": [{"id": t.id, "number": t.number, "organization_id": t.organization_id,
                         "subject": t.subject, "status": t.status} for t in ctx.db.scalars(stmt)]}


@router.get("/notifications")
def notifications(op: OperatorPrincipal = Depends(get_operator), ctx: Ctx = Depends(get_ctx)):
    rows = ctx.db.scalars(select(Notification).where(Notification.user_id == op.user.id)
                          .order_by(Notification.created_at.desc()).limit(50))
    return {"notifications": [{"id": n.id, "event": n.event, "title": n.title, "body": n.body, "data": n.data,
                               "created_at": n.created_at.isoformat() + "Z"} for n in rows]}
