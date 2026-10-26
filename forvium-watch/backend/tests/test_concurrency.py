"""Limit jednoczesnych zadan: nadmiar czeka w kolejce, po czasie 503 zamiast zawieszenia."""

from __future__ import annotations

import asyncio

from forvium.core.concurrency import ConcurrencyLimitMiddleware


def test_limit_queues_and_rejects_after_timeout():
    active, peak, sent = 0, 0, []

    async def app(scope, receive, send):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.05)
        active -= 1
        await send({"type": "http.response.start", "status": 200, "headers": []})

    async def run():
        mw = ConcurrencyLimitMiddleware(app, limit=2, queue_timeout=0.12)

        async def call(path="/api/x"):
            async def send(msg):
                if msg["type"] == "http.response.start":
                    sent.append(msg["status"])
            await mw({"type": "http", "path": path}, None, send)

        await asyncio.gather(*(call() for _ in range(6)))
        assert peak == 2 and sent.count(200) == 6  # 6 x 50 ms przy limicie 2 miesci sie w kolejce
        sent.clear()
        mw.queue_timeout = 0.01
        await asyncio.gather(*(call() for _ in range(6)), call("/healthz"))
        assert sent.count(503) >= 3 and mw.rejected >= 3

    asyncio.run(run())
