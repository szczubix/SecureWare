"""Przygotowanie testu obciazeniowego: tokeny sesji (klienci, operator) i prawdziwa sesja wsparcia.

    python deploy/loadtest/prepare.py http://localhost:8080 > /tmp/forvium-tokens.json

Wymaga stosu z danymi demo (docker compose up) i pakietu pyotp. Loguje sie przez gateway
(kilka zadan - w granicach limitow), tworzy prosbe o dostep, zgode klienta, start sesji
i wymienia kod jednorazowy na token wsparcia.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request

import pyotp

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
PASSWORD = "Demo-Haslo-2026!"
TOTP = {
    "alice": ("alice@acme.example", "JBSWY3DPEHPK3PXPALICEAAA"),
    "bob": ("bob@acme.example", "JBSWY3DPEHPK3PXPBOBBBBBB"),
    "dorota": ("dorota@acme.example", "JBSWY3DPEHPK3PXPDOROTADD"),
    "carol": ("carol@beta.example", "JBSWY3DPEHPK3PXPCAROLCCC"),
    "ola": ("ola@forvium.com", "JBSWY3DPEHPK3PXPOLAOOOOO"),
    "marta": ("marta@forvium.com", "JBSWY3DPEHPK3PXPMARTAMMM"),
}
_used: dict[str, int] = {}


def code(who: str) -> str:
    while int(time.time() // 30) == _used.get(who):  # kod TOTP jest jednorazowy
        time.sleep(0.5)
    _used[who] = int(time.time() // 30)
    return pyotp.TOTP(TOTP[who][1]).now()


def call(path: str, body: dict | None = None, token: str | None = None, method: str | None = None) -> dict:
    host = "api." + BASE.split("//", 1)[1]
    headers = {"Host": host, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers=headers, method=method or ("POST" if body is not None else "GET"))
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=30) as resp:
        return json.loads(resp.read() or b"{}")


def login(who: str, panel: str) -> str:
    email, _ = TOTP[who]
    return call(f"/api/{panel}/auth/login", {"email": email, "password": PASSWORD, "mfa_code": code(who)})["token"]


def main() -> None:
    customers = {who: login(who, "app") for who in ("alice", "bob", "dorota", "carol")}
    ola, marta = login("ola", "admin"), login("marta", "admin")
    acme = next(o["id"] for o in call("/api/app/me", token=customers["alice"])["organizations"])
    beta = next(o["id"] for o in call("/api/app/me", token=customers["carol"])["organizations"])
    bob_id = call("/api/app/me", token=customers["bob"])["user"]["id"]
    req = call("/api/admin/support-access/requests", {
        "organization_id": acme, "reference_user_id": bob_id, "ticket_number": "FW-1001",
        "reason": "Test obciazeniowy - diagnoza wydajnosci panelu", "duration_minutes": 15,
        "scopes": ["dashboard", "units", "technologies_cve", "diagnostics"], "mfa_code": code("ola")}, token=ola)
    request_id = req["request"]["id"]
    call(f"/api/app/orgs/{acme}/support-access/requests/{request_id}/approve", {}, token=customers["alice"])
    started = call(f"/api/admin/support-access/requests/{request_id}/sessions", {"mfa_code": code("ola")}, token=ola)
    support = call("/api/app/support/launch", {"code": started["launch_url"].split("#code=", 1)[1]})["token"]
    json.dump({
        "customers": [{"token": customers[w], "org": beta if w == "carol" else acme} for w in customers],
        "support": {"token": support, "org": acme},
        "operators": [marta],  # kierownik supportu: prosby, audyt, zgloszenia
    }, sys.stdout)


if __name__ == "__main__":
    main()
