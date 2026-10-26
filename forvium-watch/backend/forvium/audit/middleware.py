"""Middleware ASGI rejestrujace kazda operacje API wykonana w trybie wsparcia
(oraz kazde wywolanie API administracyjnego przez operatora).

Zapisywane sa: metoda, szablon trasy (np. `/api/app/orgs/{org_id}/dashboard`),
kod odpowiedzi i obie tozsamosci. Tresc zadan i odpowiedzi nie jest logowana.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SupportAuditMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Wspolny slownik stanu, do ktorego zaleznosci wpisuja `audit_actor`.
        scope.setdefault("state", {})
        status_holder = {"status": 500}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            actor = scope.get("state", {}).get("audit_actor")
            if actor:
                route = scope.get("route")
                status = status_holder["status"]
                client = scope.get("client")
                audit = scope["app"].state.audit
                fields = dict(actor)
                action = fields.pop("action")
                audit.record(
                    action,
                    outcome="success" if status < 400 else "denied",
                    http_method=scope["method"],
                    route=getattr(route, "path", scope["path"]),
                    status_code=status,
                    ip_address=client[0] if client else None,
                    **fields,
                )
