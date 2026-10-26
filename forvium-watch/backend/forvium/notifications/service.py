from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from forvium.core.clock import clock
from forvium.core.i18n import default_lang, normalize, tr
from forvium.identity.models import User
from forvium.notifications.models import EmailOutbox, Notification


def recipient_lang(db: Session, user: User, organization_id: str | None = None) -> str:
    """Jezyk odbiorcy: wlasny wybor, jezyk organizacji (wskazanej albo jedynej), domyslny platformy."""
    lang = normalize(user.locale)
    if lang:
        return lang
    from forvium.organizations.models import Membership, Organization

    if organization_id is None and user.platform_role is None:
        ids = db.scalars(select(Membership.organization_id).where(Membership.user_id == user.id).limit(2)).all()
        organization_id = ids[0] if len(ids) == 1 else None
    if organization_id:
        org = db.get(Organization, organization_id)
        if org is not None and normalize(org.locale):
            return org.locale
    return default_lang()


class NotificationEngine:
    """Wysyla powiadomienie w aplikacji i (opcjonalnie) e-mail do odbiorcow.

    Tytul i tresc to tekst zrodlowy albo L(...) (core/i18n.py) - kazdy odbiorca dostaje je
    w swoim jezyku.
    """

    def notify(
        self,
        db: Session,
        recipients: Iterable[User],
        *,
        event: str,
        title,
        body,
        organization_id: str | None = None,
        data: dict | None = None,
        email: bool = True,
    ) -> None:
        now = clock.now()
        for user in recipients:
            lang = recipient_lang(db, user, organization_id)
            subject, text = tr(title, lang)[:200], tr(body, lang)
            db.add(
                Notification(
                    user_id=user.id,
                    organization_id=organization_id,
                    event=event,
                    title=subject,
                    body=text[:2000],
                    data=data or {},
                    created_at=now,
                )
            )
            if email:
                db.add(EmailOutbox(to_address=user.email, subject=subject, body=text, created_at=now))

    def email_only(self, db: Session, user: User, *, subject, body) -> None:
        """Sam e-mail, bez kopii w aplikacji (np. link aktywacyjny, ktory ma trafic tylko do skrzynki)."""
        lang = recipient_lang(db, user)
        db.add(EmailOutbox(to_address=user.email, subject=tr(subject, lang), body=tr(body, lang),
                           created_at=clock.now()))
