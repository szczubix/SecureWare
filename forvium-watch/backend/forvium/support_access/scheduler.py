"""Cykliczne wygaszanie sesji wsparcia i prosb bez decyzji.

Dostep jest i tak blokowany przy kazdym zadaniu; ten proces sprawia, ze
status i audyt (`support.session.expired`) pojawiaja sie rowniez wtedy, gdy
nikt juz nie korzysta z sesji.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from forvium.core.context import Ctx
from forvium.support_access.service import sweep_expired

logger = logging.getLogger(__name__)


def run_sweep(app: FastAPI) -> int:
    state = app.state
    db = state.db.sessionmaker()
    try:
        ctx = Ctx(db=db, audit=state.audit, notifications=state.notifications, policy=state.support_policy, ip=None)
        count = sweep_expired(ctx)
        db.commit()
        return count
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def sweep_loop(app: FastAPI, interval_seconds: int) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await run_in_threadpool(run_sweep, app)
        except Exception:  # pragma: no cover - petla musi przetrwac pojedynczy blad
            logger.exception("Support Access sweep failed")
