"""Cykliczne wygaszanie sesji wsparcia i prosb bez decyzji.

Dostep jest i tak blokowany przy kazdym zadaniu; ten proces sprawia, ze
status i audyt (`support.session.expired`) pojawiaja sie rowniez wtedy, gdy
nikt juz nie korzysta z sesji.
"""

from __future__ import annotations

from fastapi import FastAPI

from forvium.core.context import Ctx
from forvium.support_access.service import sweep_expired


def run_sweep(app: FastAPI) -> int:
    state = app.state
    db = state.db.sessionmaker()
    try:
        ctx = Ctx.from_state(state, db, None)
        count = sweep_expired(ctx)
        db.commit()
        return count
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
