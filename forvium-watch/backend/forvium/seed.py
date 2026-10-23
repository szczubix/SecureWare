"""Dane demonstracyjne (dev/testy): `python -m forvium.seed`."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from forvium.core.clock import clock
from forvium.core.security import hash_password
from forvium.identity.models import User
from forvium.organizations.models import DiagnosticEvent, Membership, Organization, OrgUnit, Technology
from forvium.support_tickets.models import SupportTicket, TicketStatus

DEMO_PASSWORD = "Forvium-demo-2026!"

# Stale sekrety TOTP wylacznie dla danych demo/testow.
TOTP = {
    "alice": "JBSWY3DPEHPK3PXPALICEAAA",
    "bob": "JBSWY3DPEHPK3PXPBOBBBBBB",
    "carol": "JBSWY3DPEHPK3PXPCAROLCCC",
    "ola": "JBSWY3DPEHPK3PXPOLAOOOOO",
    "piotr": "JBSWY3DPEHPK3PXPPIOTRPPP",
    "marta": "JBSWY3DPEHPK3PXPMARTAMMM",
    "ewa": "JBSWY3DPEHPK3PXPEWAEEEEE",
    "tomasz": "JBSWY3DPEHPK3PXPTOMASZTT",
}


def seed(db: Session) -> dict:
    now = clock.now()
    pw = hash_password(DEMO_PASSWORD)

    def user(key: str, email: str, name: str, platform_role: str | None = None) -> User:
        u = User(email=email, display_name=name, password_hash=pw, mfa_secret=TOTP[key], is_active=True,
                 platform_role=platform_role, created_at=now)
        db.add(u)
        return u

    alice = user("alice", "alice@acme.example", "Alicja Kowalska")
    bob = user("bob", "bob@acme.example", "Bartosz Nowak")
    carol = user("carol", "carol@beta.example", "Karolina Wisniewska")
    ola = user("ola", "ola@forvium.com", "Ola (Support L2)", platform_role="support_l2")
    piotr = user("piotr", "piotr@forvium.com", "Piotr (Support L1)", platform_role="support_l1")
    marta = user("marta", "marta@forvium.com", "Marta (Kierownik supportu)", platform_role="support_lead")
    ewa = user("ewa", "ewa@forvium.com", "Ewa (Oficer bezpieczenstwa)", platform_role="security_officer")
    tomasz = user("tomasz", "tomasz@forvium.com", "Tomasz (Oficer bezpieczenstwa)", platform_role="security_officer")

    acme = Organization(name="Acme Sp. z o.o.", subscription_plan="business", created_at=now,
                        settings={"timezone": "Europe/Warsaw", "scan_interval_h": 6},
                        smtp_config={"host": "smtp.acme.example", "port": 587, "username": "watch",
                                     "password": "smtp-super-secret"},
                        webhooks=["https://hooks.acme.example/forvium?token=abc123"],
                        secrets={"siem_api_key": "sk-acme-secret"})
    beta = Organization(name="Beta S.A.", subscription_plan="standard", created_at=now,
                        secrets={"siem_api_key": "sk-beta-secret"})
    db.add_all([acme, beta])
    db.flush()

    hq = OrgUnit(organization_id=acme.id, name="Centrala")
    db.add(hq)
    db.flush()
    waw = OrgUnit(organization_id=acme.id, parent_id=hq.id, name="Oddzial Warszawa")
    krk = OrgUnit(organization_id=acme.id, parent_id=hq.id, name="Oddzial Krakow")
    beta_unit = OrgUnit(organization_id=beta.id, name="Beta HQ")
    db.add_all([waw, krk, beta_unit])
    db.flush()

    db.add_all([
        Technology(organization_id=acme.id, unit_id=waw.id, name="nginx", version="1.24.0",
                   cves=[{"id": "CVE-2024-7347", "severity": "medium"}]),
        Technology(organization_id=acme.id, unit_id=krk.id, name="OpenSSH", version="9.6p1",
                   cves=[{"id": "CVE-2024-6387", "severity": "critical"}]),
        Technology(organization_id=beta.id, unit_id=beta_unit.id, name="Apache httpd", version="2.4.58",
                   cves=[{"id": "CVE-2024-38476", "severity": "high"}]),
        DiagnosticEvent(organization_id=acme.id, level="error", component="scanner",
                        message="Agent w Oddziale Krakow nie raportuje od 3 h", created_at=now - timedelta(hours=1)),
        DiagnosticEvent(organization_id=acme.id, level="warning", component="smtp",
                        message="Odrzucone polaczenie TLS do serwera SMTP", created_at=now - timedelta(hours=2)),
    ])

    db.add_all([
        Membership(organization_id=acme.id, user_id=alice.id, role="owner"),
        Membership(organization_id=acme.id, user_id=bob.id, role="member"),
        Membership(organization_id=beta.id, user_id=carol.id, role="owner"),
        # Operator, ktory jest jednoczesnie administratorem organizacji klienta
        # (np. konto testowe) - nie moze zatwierdzic wlasnej prosby.
        Membership(organization_id=acme.id, user_id=ola.id, role="admin"),
    ])

    t_acme = SupportTicket(number="FW-1001", organization_id=acme.id, reporter_user_id=bob.id,
                           subject="Dashboard nie pokazuje CVE dla Oddzialu Krakow", created_at=now)
    t_closed = SupportTicket(number="FW-1002", organization_id=acme.id, subject="Stare zgloszenie",
                             status=TicketStatus.CLOSED, created_at=now)
    t_beta = SupportTicket(number="FW-2001", organization_id=beta.id, reporter_user_id=carol.id,
                           subject="Blad konfiguracji SMTP", created_at=now)
    db.add_all([t_acme, t_closed, t_beta])
    db.flush()

    return {
        "users": {"alice": alice, "bob": bob, "carol": carol, "ola": ola, "piotr": piotr,
                  "marta": marta, "ewa": ewa, "tomasz": tomasz},
        "orgs": {"acme": acme, "beta": beta},
        "units": {"hq": hq, "waw": waw, "krk": krk, "beta": beta_unit},
        "tickets": {"acme": t_acme, "acme_closed": t_closed, "beta": t_beta},
    }


if __name__ == "__main__":  # pragma: no cover
    from forvium.core.config import get_settings
    from forvium.core.db import Database

    from forvium.core.migrations import upgrade_head

    url = get_settings().database_url
    upgrade_head(url)
    database = Database(url)
    with database.sessionmaker() as session:
        from sqlalchemy import select

        if session.scalar(select(User.id).limit(1)) is not None:
            print("Baza zawiera juz dane - pomijam seed.")
            raise SystemExit(0)
        data = seed(session)
        session.commit()
        print("Zaladowano dane demo. Haslo dla wszystkich kont:", DEMO_PASSWORD)
        for key, u in data["users"].items():
            print(f"  {u.email:24} TOTP: {TOTP[key]}")
