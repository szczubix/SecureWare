"""Konfiguracja logow: tekst (lokalnie) albo JSON w jednej linii (produkcja, Loki/ELK).

Do logow trafiaja wylacznie metadane (bez tresci zadan, tokenow i sekretow) -
tak jak w Audit Log.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

_STD_ATTRS = set(vars(logging.LogRecord("", 0, "", 0, "", (), None))) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        out = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in vars(record).items():
            if key not in _STD_ATTRS and not key.startswith("_"):
                out[key] = value
        if record.exc_info:
            out["exc"] = self.formatException(record.exc_info)
        return json.dumps(out, ensure_ascii=False, default=str)


def configure_logging(settings) -> None:
    handler = logging.StreamHandler(sys.stdout)
    if settings.log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    from forvium.monitoring import RequestIdFilter

    handler.addFilter(RequestIdFilter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(settings.log_level.upper())
    # Dostep HTTP logujemy sami (middleware z identyfikatorem zadania), bez duplikatu z uvicorn.
    logging.getLogger("uvicorn.access").disabled = True
