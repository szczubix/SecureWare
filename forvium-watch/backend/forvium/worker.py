"""Proces zadan w tle: `python -m forvium.worker` (kontener `worker`).

`python -m forvium.worker --check` sluzy jako healthcheck kontenera: konczy sie
kodem 1, gdy ktores zadanie nie wykonalo sie poprawnie od >3 interwalow.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import signal
import sys
from dataclasses import replace

from forvium.core.config import get_settings
from forvium.core.logging import configure_logging

logger = logging.getLogger("forvium.worker")


def _app():
    from forvium.main import create_app

    # Worker buduje ten sam stan aplikacji co API (klucze, audyt, polityki), ale sam
    # uruchamia zadania jawnie - bez cyklu zycia serwera HTTP.
    return create_app(replace(get_settings(), run_background_jobs=False))


async def _run() -> None:
    from forvium.jobs import background_jobs, start_jobs

    app = _app()
    names = [name for name, _, _ in background_jobs(app)]
    logger.info("Worker uruchomiony", extra={"jobs": names})
    tasks = start_jobs(app)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop.set)
    await stop.wait()
    logger.info("Worker kończy pracę")
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


def check() -> int:
    from forvium.jobs import JobRun, stale_jobs

    app = _app()
    with app.state.db.sessionmaker() as db:
        if db.query(JobRun).count() == 0:
            print("brak jeszcze przebiegów zadań")
            return 0
        stale = stale_jobs(db)
    if stale:
        print("zadania bez udanego przebiegu:", ", ".join(stale))
        return 1
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="healthcheck: sprawdź świeżość zadań")
    args = parser.parse_args(argv)
    configure_logging(get_settings())
    if args.check:
        return check()
    asyncio.run(_run())
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
