"""Podsumowanie sesji wsparcia dla klienta (na podstawie Audit Log)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from forvium.audit.models import AuditEvent
from forvium.core.i18n import Joined, L, join
from forvium.support_access.models import SupportSession

# Przyjazne nazwy widokow (szablon trasy -> etykieta).
VIEW_LABELS = {
    "/api/app/orgs/{org_id}/dashboard": "Dashboard",
    "/api/app/orgs/{org_id}/units": "Struktura jednostek",
    "/api/app/orgs/{org_id}/technologies": "Technologie",
    "/api/app/orgs/{org_id}/cves": "Lista CVE",
    "/api/app/orgs/{org_id}/config/status": "Stan konfiguracji",
    "/api/app/orgs/{org_id}/errors": "Błędy",
}

END_REASON_LABELS = {
    "ended_by_operator": "zakończona przez operatora",
    "terminated_by_customer": "zakończona przez Twoją organizację",
    "terminated_by_supervisor": "zakończona przez przełożonego supportu Forvium",
    "consent_revoked": "zgoda została cofnięta",
    "consent_expired": "zgoda wygasła",
    "session_expired": "upłynął czas sesji",
    "ticket_closed": "zgłoszenie zostało zamknięte",
    "terminated_by_anomaly": "zakończona automatycznie przez system bezpieczeństwa Forvium",
}


def session_summary(db: Session, session: SupportSession) -> dict:
    events = list(db.scalars(select(AuditEvent).where(AuditEvent.support_session_id == session.id,
                                                      AuditEvent.action == "support.api_call")))
    views: list[str] = []
    for e in events:
        label = VIEW_LABELS.get(e.route or "")
        if label and e.outcome == "success" and label not in views:
            views.append(label)
    end = session.ended_at or session.expires_at
    return {
        "duration_seconds": max(0, int((end - session.started_at).total_seconds())),
        "api_calls": len(events),
        "denied_calls": sum(1 for e in events if e.outcome != "success"),
        "views": views,
        "end_reason": session.end_reason,
    }


def summary_text(summary: dict) -> Joined:
    minutes, seconds = divmod(summary["duration_seconds"], 60)
    reason = summary["end_reason"] or ""
    return join("\n", [
        L("Czas trwania: {minutes} min {seconds} s", minutes=minutes, seconds=seconds),
        L("Powód zakończenia: {reason}", reason=END_REASON_LABELS.get(reason, reason)),
        L("Liczba operacji (tylko odczyt): {n}", n=summary["api_calls"]),
        L("Zablokowane próby: {n}", n=summary["denied_calls"]),
        L("Oglądane widoki: {views}", views=join(", ", summary["views"]) if summary["views"] else L("brak")),
    ])
