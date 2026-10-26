"""Pierwsze konta operatorow na swiezej instalacji (bez danych demo).

    docker compose -f compose.yaml -f compose.prod.yaml run --rm migrate \\
        python -m forvium.platform_admin.bootstrap --email admin@firma.pl --name "Jan Admin" --role platform_admin

Dziala tylko wtedy, gdy na platformie nie ma jeszcze niezablokowanego konta z dana rola
(administrator platformy albo oficer bezpieczenstwa) - kolejne osoby dodaje sie juz
w panelu admin (a role uprzywilejowane zatwierdza oficer bezpieczenstwa). Konto aktywuje
sam uzytkownik linkiem z e-maila; link jest tez wypisywany tutaj, bo przy pierwszym
uruchomieniu poczta moze jeszcze nie dzialac.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace

from sqlalchemy import func, select

from forvium.core.clock import clock
from forvium.core.config import get_settings
from forvium.core.context import Ctx
from forvium.identity import activation
from forvium.identity.models import User
from forvium.main import create_app
from forvium.platform_admin.rbac import PlatformRole

BOOTSTRAP_ROLES = (PlatformRole.PLATFORM_ADMIN, PlatformRole.SECURITY_OFFICER)


def bootstrap(app, email: str, name: str, role: str) -> str:
    if role not in BOOTSTRAP_ROLES:
        raise SystemExit(f"Rola musi byc jedna z: {', '.join(BOOTSTRAP_ROLES)}")
    email = email.strip().lower()
    with app.state.db.sessionmaker() as db:
        ctx = Ctx.from_state(app.state, db, None)
        # Takze konto czekajace na aktywacje blokuje kolejny bootstrap (liczy sie kazde niezablokowane).
        existing = db.scalar(select(func.count()).select_from(User).where(User.platform_role == role,
                                                                          User.blocked_at.is_(None)))
        if existing:
            raise SystemExit(f"Na platformie jest juz konto z rola {role} - kolejne osoby dodaj w panelu admin.")
        if db.scalar(select(User.id).where(User.email == email)):
            raise SystemExit(f"Konto {email} juz istnieje.")
        user = User(email=email, display_name=name.strip(), password_hash=activation.unusable_password_hash(),
                    is_active=False, platform_role=role, created_at=clock.now())
        db.add(user)
        db.flush()
        link = activation.issue(ctx, user, kind="operator", created_by="system", actor_type="system")
        ctx.audit.log(db, "platform.operator.bootstrapped", actor_type="system",
                      details={"user_id": user.id, "role": role})
        db.commit()
        return link


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--role", required=True, choices=list(BOOTSTRAP_ROLES))
    args = parser.parse_args(argv)
    app = create_app(replace(get_settings(), run_background_jobs=False))
    link = bootstrap(app, args.email, args.name, args.role)
    print(f"Utworzono konto {args.email} ({args.role}). Link aktywacyjny (72 h, jednorazowy) wyslano e-mailem:\n{link}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
