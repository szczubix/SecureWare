"""Proste zadania cykliczne uruchamiane w cyklu zycia aplikacji."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)


async def periodic(name: str, interval_seconds: int, fn: Callable[[], object]) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await run_in_threadpool(fn)
        except Exception:  # pragma: no cover - petla musi przetrwac pojedynczy blad
            logger.exception("Zadanie cykliczne %s nie powiodlo sie", name)
