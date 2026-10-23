"""Podsumowanie sesji wsparcia dla klienta (na podstawie Audit Log)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from forvium.audit.models import AuditEvent
from forvium.support_access.models import SupportSession

# Przyjazne nazwy widokow (szablon trasy -> etykieta).
VIEW_LABELS = {
    "/api/app/orgs/{org_id}/dashboard": "Dashboard",
    "/api/app/orgs/{org_id}/units": "Struktura jednostek",
    "/api/app/orgs/{org_id}/technologies": "Technologie",
    "/api/app/orgs/{org_id}/cves": "Lista CVE",
    "/api/app/orgs/{org_id}/config/status": "Stan konfiguracji",
    "/api/app/orgs/{org_id}/errors": "Bledy",
}

END_REASON_LABELS = {
    "ended_by_operator": "zakonczona przez operatora",
    "terminated_by_customer": "zakonczona przez Twoja organizacje",
    "terminated_by_supervisor": "zakonczona przez przelozonego supportu Forvium",
    "consent_revoked": "zgoda zostala cofnieta",
    "consent_expired": "zgoda wygasla",
    "session_expired": "uplynal czas sesji",
    "ticket_closed": "zgloszenie zostalo zamkniete",
    "terminated_by_anomaly": "zakonczona automatycznie przez system bezpieczenstwa Forvium",
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


def summary_text(summary: dict) -> str:
    minutes, seconds = divmod(summary["duration_seconds"], 60)
    lines = [
        f"Czas trwania: {minutes} min {seconds} s",
        f"Powod zakonczenia: {END_REASON_LABELS.get(summary['end_reason'] or '', summary['end_reason'])}",
        f"Liczba operacji (tylko odczyt): {summary['api_calls']}",
        f"Zablokowane proby: {summary['denied_calls']}",
        "Ogladane widoki: " + (", ".join(summary["views"]) or "brak"),
    ]
    return "\n".join(lines)
