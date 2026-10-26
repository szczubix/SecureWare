from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from forvium.core.clock import clock
from forvium.identity.models import User
from forvium.notifications.models import EmailOutbox, Notification


class NotificationEngine:
    """Wysyla powiadomienie w aplikacji i (opcjonalnie) e-mail do odbiorcow."""

    def notify(
        self,
        db: Session,
        recipients: Iterable[User],
        *,
        event: str,
        title: str,
        body: str,
        organization_id: str | None = None,
        data: dict | None = None,
        email: bool = True,
    ) -> None:
        now = clock.now()
        for user in recipients:
            db.add(
                Notification(
                    user_id=user.id,
                    organization_id=organization_id,
                    event=event,
                    title=title,
                    body=body,
                    data=data or {},
                    created_at=now,
                )
            )
            if email:
                db.add(EmailOutbox(to_address=user.email, subject=title, body=body, created_at=now))

    def email_only(self, db: Session, user: User, *, subject: str, body: str) -> None:
        """Sam e-mail, bez kopii w aplikacji (np. link aktywacyjny, ktory ma trafic tylko do skrzynki)."""
        db.add(EmailOutbox(to_address=user.email, subject=subject, body=body, created_at=clock.now()))
