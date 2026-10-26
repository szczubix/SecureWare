"""Ograniczenie liczby zadan obslugiwanych jednoczesnie przez proces API.

Zaleznosci FastAPI (uwierzytelnianie) i endpointy synchroniczne dzialaja w puli watkow,
a polaczenie z baza jest pobierane juz w zaleznosci. Bez limitu, pod duzym obciazeniem,
zadania trzymajace polaczenie czekaja na wolny watek, a watki - na polaczenie z
wyczerpanej puli (zakleszczenie wykryte testem obciazeniowym, deploy/loadtest).

Middleware wpuszcza do aplikacji najwyzej tyle zadan, ile jest polaczen w glownej puli;
pozostale czekaja w kolejce (bez polaczenia z baza), a po `queue_timeout` dostaja
503 z naglowkiem Retry-After - kontrolowane odrzucenie zamiast zawieszenia procesu.
"""

from __future__ import annotations

import asyncio
import json

from starlette.types import ASGIApp, Receive, Scope, Send

from forvium.core.i18n import lang_from_scope, tr

_EXEMPT = ("/healthz", "/metrics")


class ConcurrencyLimitMiddleware:
    def __init__(self, app: ASGIApp, limit: int, queue_timeout: float = 15.0) -> None:
        self.app = app
        self.limit = limit
        self.queue_timeout = queue_timeout
        self._semaphore: asyncio.Semaphore | None = None
        self.rejected = 0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in _EXEMPT:
            await self.app(scope, receive, send)
            return
        if self._semaphore is None:  # tworzony w petli zdarzen procesu
            self._semaphore = asyncio.Semaphore(self.limit)
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self.queue_timeout)
        except TimeoutError:
            self.rejected += 1
            message = tr("Serwer jest chwilowo przeciążony - spróbuj ponownie.", lang_from_scope(scope))
            body = json.dumps({"error": "overloaded", "message": message}).encode()
            await send({"type": "http.response.start", "status": 503,
                        "headers": [(b"content-type", b"application/json"), (b"retry-after", b"5"),
                                    (b"content-length", str(len(body)).encode())]})
            await send({"type": "http.response.body", "body": body})
            return
        try:
            await self.app(scope, receive, send)
        finally:
            self._semaphore.release()
