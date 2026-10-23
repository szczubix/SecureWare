"""Kontekst serwisow budowany dla kazdego zadania."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from forvium.audit.service import AuditLog
from forvium.core.db import get_db
from forvium.notifications.service import NotificationEngine
from forvium.support_access.policy import SupportAccessPolicy


class DomainError(Exception):
    """Blad domenowy mapowany na odpowiedz HTTP (status + kod + komunikat)."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
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


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def get_ctx(request: Request, db: Session = Depends(get_db)) -> Ctx:
    state = request.app.state
    return Ctx(
        db=db,
        audit=state.audit,
        notifications=state.notifications,
        policy=state.support_policy,
        ip=client_ip(request),
    )
