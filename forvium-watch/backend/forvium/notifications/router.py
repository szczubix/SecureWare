from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select

from forvium.access import AppPrincipal, require_user_principal
from forvium.core.context import Ctx, get_ctx
from forvium.notifications.models import Notification

router = APIRouter(prefix="/api/app/notifications", tags=["notifications"])


@router.get("")
def my_notifications(principal: AppPrincipal = Depends(require_user_principal), ctx: Ctx = Depends(get_ctx)):
    rows = ctx.db.scalars(select(Notification).where(Notification.user_id == principal.actor.id)
                          .order_by(Notification.created_at.desc()).limit(50))
    return {"notifications": [{"id": n.id, "event": n.event, "title": n.title, "body": n.body, "data": n.data,
                               "organization_id": n.organization_id, "created_at": n.created_at.isoformat() + "Z",
                               "read": n.read_at is not None} for n in rows]}
