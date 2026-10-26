"""Kontekst serwisow budowany dla kazdego zadania."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from forvium.audit.service import AuditLog
from forvium.core.db import get_db
from forvium.notifications.service import NotificationEngine
from forvium.support_access.policy import SupportAccessPolicy

if TYPE_CHECKING:
    from forvium.identity.throttle import Throttle


class DomainError(Exception):
    """Blad domenowy mapowany na odpowiedz HTTP (status + kod + komunikat)."""

    def __init__(self, status_code: int, code: str, message) -> None:
        # message: tekst zrodlowy (pl) albo L(...); tlumaczony przy odpowiedzi (core/i18n.py).
        super().__init__(str(message))
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass
class Ctx:
    db: Session
    audit: AuditLog
    notifications: NotificationEngine
    policy: SupportAccessPolicy
    ip: str | None
    throttle: Throttle
    settings: Any  # forvium.core.config.Settings
    break_glass: Any  # forvium.support_access.break_glass.BreakGlassPolicy

    @classmethod
    def from_state(cls, state: Any, db: Session, ip: str | None) -> Ctx:
        return cls(db=db, audit=state.audit, notifications=state.notifications, policy=state.support_policy,
                   ip=ip, throttle=state.throttle, settings=state.settings,
                   break_glass=state.break_glass_policy)


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


# scope="function": commit/rollback PRZED wyslaniem odpowiedzi. Domyslnie FastAPI konczy
# zaleznosci z yield dopiero po odpowiedzi, a wtedy klient moglby wyslac kolejne zadanie
# (np. GET /me zaraz po logowaniu), zanim zmiana trafi do bazy.
def get_ctx(request: Request, db: Session = Depends(get_db, scope="function")) -> Ctx:
    return Ctx.from_state(request.app.state, db, client_ip(request))
