"""Wersja angielska: kompletnosc katalogu i wybor jezyka (API, powiadomienia, e-maile, raporty)."""

from __future__ import annotations

import ast
import re
import string
from pathlib import Path

import pytest
from sqlalchemy import select

from forvium.core.i18n import L, join, negotiate, tr, tr_stored
from forvium.locales.en import EN

SRC = Path(__file__).resolve().parents[1] / "forvium"
POLISH = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")
# Narzedzia CLI, logi i dane demonstracyjne - nie trafiaja do uzytkownika panelu.
SKIP_FILES = {"seed.py", "worker.py", "jobs.py", "audit/verify.py", "audit/chain.py", "core/crypto.py",
              "core/i18n.py", "locales/en.py"}
SKIP_CALLS = {"debug", "info", "warning", "error", "exception", "critical", "print", "add_argument",
              "ArgumentParser", "CryptoConfigError", "SystemExit", "RuntimeError", "ValueError"}
# Wywolania, ktorych argumenty tekstowe zawsze trafiaja do uzytkownika.
USER_FACING = {"DomainError", "_deny", "deny", "notify", "email_only", "notify_security_team", "L", "t", "tr"}
# Slowniki etykiet widocznych dla uzytkownika (wartosci tlumaczone przy wyswietleniu).
LABEL_DICTS = re.compile(r"(_LABELS|^MESSAGES)$")


def _name(func: ast.expr) -> str:
    return func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")


def _name_of_call(tree, const) -> str:
    """Nazwa funkcji, ktorej pierwszym argumentem jest dana stala (t("Status") w pdf.py)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.args and node.args[0] is const:
            return _name(node.func)
    return ""


def _scan():
    """Zwraca (teksty do przetlumaczenia, f-stringi do zamiany na L(...)) jako (plik:linia, tekst)."""
    texts, fstrings = [], []
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC).as_posix()
        if rel in SKIP_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        skip, user_facing, labels = set(), set(), set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) for t in node.targets):
                name = next(t.id for t in node.targets if isinstance(t, ast.Name))
                if name == "MONTHS":  # nazwy miesiecy: reports/service.py ma obie wersje jezykowe
                    skip.update(id(n) for n in ast.walk(node.value))
                elif LABEL_DICTS.search(name) and isinstance(node.value, ast.Dict):
                    labels.update(id(v) for v in node.value.values)
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                    skip.add(id(body[0].value))  # docstring
            if isinstance(node, ast.Call):
                name = _name(node.func)
                args = [*node.args, *(k.value for k in node.keywords)]
                for sub in (n for a in args for n in ast.walk(a)):
                    if name in SKIP_CALLS:
                        skip.add(id(sub))
                    elif name in USER_FACING:
                        user_facing.add(id(sub))
        for node in ast.walk(tree):
            where = f"{rel}:{getattr(node, 'lineno', '?')}"
            if id(node) in skip:
                continue
            if isinstance(node, ast.JoinedStr):
                literal = "".join(v.value for v in node.values if isinstance(v, ast.Constant))
                if POLISH.search(literal) or (id(node) in user_facing and re.search(r"[A-Za-z]{3}", literal)):
                    fstrings.append((where, literal))
                for v in node.values:
                    skip.add(id(v))
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                if (POLISH.search(node.value) or id(node) in labels
                        or (id(node) in user_facing and re.search(r"[A-Za-z]{3}", node.value)
                            and (" " in node.value or _name_of_call(tree, node) in ("t", "tr", "L")))):
                    texts.append((where, node.value))
    return texts, fstrings


def test_no_fstrings_in_user_facing_texts():
    _, fstrings = _scan()
    assert not fstrings, "Uzyj L('szablon {x}', x=...) zamiast f-stringa:\n" + "\n".join(
        f"  {w}: {t!r}" for w, t in fstrings)


def test_every_polish_text_has_english_translation():
    texts, _ = _scan()
    missing = sorted({t for _, t in texts if t not in EN})
    assert not missing, "Brak tlumaczen w forvium/locales/en.py:\n" + "\n".join(f"  {t!r}" for t in missing)


def test_translations_keep_placeholders_and_are_english():
    fields = lambda s: sorted(f for _, f, _, _ in string.Formatter().parse(s) if f)  # noqa: E731
    for pl, en in EN.items():
        assert fields(pl) == fields(en), f"inne parametry: {pl!r} -> {en!r}"
        assert not POLISH.search(en), f"polskie znaki w tlumaczeniu: {en!r}"


def test_negotiate_and_render():
    assert negotiate("en-GB,en;q=0.9,pl;q=0.8") == "en"
    assert negotiate("pl-PL,pl;q=0.9,en;q=0.5") == "pl"
    assert negotiate("de-DE, fr;q=0.8") == "pl"
    assert negotiate("") == "pl"
    msg = L("Czas sesji: 1-{n} min.", n=15)
    assert str(msg) == "Czas sesji: 1-15 min."
    assert msg.render("en") == "Session duration: 1-15 min."
    assert tr(join("\n", [msg, "Nie znaleziono sesji."]), "en") == "Session duration: 1-15 min.\nSession not found."
    assert tr_stored("Zatwierdzono automatycznie (zgoda stała abc-1)", "en") == \
        "Approved automatically (standing consent abc-1)"
    assert tr_stored("dowolny tekst klienta", "en") == "dowolny tekst klienta"


# ------------------------------------------------------------------ API i powiadomienia
def test_api_errors_follow_accept_language(env):
    r = env.client.get("/api/app/me")
    assert r.status_code == 401 and r.json()["message"] == "Wymagane uwierzytelnienie."
    r = env.client.get("/api/app/me", headers={"Accept-Language": "en-US,en;q=0.9"})
    assert r.json() == {"error": "unauthenticated", "message": "Authentication required."}
    r = env.client.post("/api/app/auth/login", headers={"Accept-Language": "en"},
                        json={"email": "nobody@example.com", "password": "x" * 12, "mfa_code": "000000"})
    assert r.json()["message"] == "Invalid sign-in details."


def test_user_locale_preference_drives_notifications(env):
    from forvium.notifications.models import EmailOutbox, Notification
    from forvium.seed import DEMO_PASSWORD

    token = env.login_app("bob")
    r = env.client.put("/api/app/account/locale", headers=env.h(token), json={"locale": "de"})
    assert r.status_code == 422
    r = env.client.put("/api/app/account/locale", headers=env.h(token), json={"locale": "en"})
    assert r.status_code == 200 and r.json() == {"locale": "en"}
    assert env.client.get("/api/app/me", headers=env.h(token)).json()["user"]["locale"] == "en"
    assert env.audit(action="identity.locale.changed")[-1].details == {"from": None, "to": "en"}

    # Powiadomienie o zmianie hasla po angielsku, mimo polskiego naglowka zadania.
    r = env.client.post("/api/app/account/password", headers={**env.h(token), "Accept-Language": "pl"},
                        json={"current_password": DEMO_PASSWORD, "new_password": "Zupelnie-Nowe-Haslo-77"})
    assert r.status_code == 200, r.text
    with env.app.state.db.sessionmaker() as db:
        note = db.scalars(select(Notification).where(Notification.user_id == env.ids["users"]["bob"])
                          .order_by(Notification.created_at.desc())).first()
        assert note.title == "Password changed"
        mail = db.scalars(select(EmailOutbox).where(EmailOutbox.to_address == env.emails["bob"])
                          .order_by(EmailOutbox.created_at.desc())).first()
        assert mail.subject == "Password changed" and "If this wasn't you" in mail.body


def test_admin_locale_endpoint(env):
    op = env.login_admin("ola")
    r = env.client.put("/api/admin/account/locale", headers=env.h(op), json={"locale": "en"})
    assert r.status_code == 200
    assert env.client.get("/api/admin/me", headers=env.h(op)).json()["user"]["locale"] == "en"


def test_organization_locale_drives_members_and_reports(env):
    from datetime import datetime

    from forvium.identity.models import User
    from forvium.notifications.models import EmailOutbox
    from forvium.reports.service import ReportData
    from forvium.reports.pdf import render

    adam = env.login_admin("adam")
    org = env.ids["orgs"]["acme"]
    r = env.client.put(f"/api/admin/organizations/{org}", headers=env.h(adam),
                       json={"locale": "en", "mfa_code": env.otp("adam")})
    assert r.status_code == 200, r.text
    assert r.json()["organization"]["locale"] == "en"

    alice = env.login_app("alice")
    r = env.client.post(env.org_url("/members"), headers=env.h(alice),
                        json={"email": "new.person@acme.example", "display_name": "Nowa Osoba", "role": "viewer"})
    assert r.status_code == 200, r.text
    with env.app.state.db.sessionmaker() as db:
        user = db.scalar(select(User).where(User.email == "new.person@acme.example"))
        assert user.locale is None  # dziedziczy jezyk organizacji
        mail = db.scalar(select(EmailOutbox).where(EmailOutbox.to_address == user.email))
        assert mail.subject == "Activate your account in Forvium Watch"
        assert mail.body.startswith("Hello Nowa Osoba,") and "activate.html?lang=en#token=fwa_" in mail.body

    pdf = render(ReportData(kind="customer", period_start=datetime(2026, 9, 1), period_end=datetime(2026, 10, 1),
                            organization_name="Acme", lang="en"))
    assert pdf.startswith(b"%PDF")


def test_api_error_with_parameters_is_translated(env):
    op = env.login_admin("ola")
    r = env.create_request(op, duration=999)
    assert r.status_code == 422 and r.json()["message"] == "Czas dostępu musi mieścić się w 1-15 min."
    env.client.headers["Accept-Language"] = "en"
    try:
        r = env.create_request(op, duration=999)
    finally:
        del env.client.headers["Accept-Language"]
    assert r.json() == {"error": "duration_invalid", "message": "The access duration must be between 1 and 15 min."}


@pytest.mark.parametrize("lang", ["pl", "en"])
def test_support_banner_in_request_language(env, lang):
    s = env.open_support_session()
    r = env.client.get("/api/app/support/session", headers={**env.h(s["support"]), "Accept-Language": lang})
    assert r.status_code == 200
    banner = r.json()["banner"]
    assert ("TYLKO ODCZYT" in banner) == (lang == "pl")
    assert ("READ ONLY" in banner) == (lang == "en")
