"""Punkt wejscia ASGI: `uvicorn forvium.asgi:app`."""

from forvium.main import create_app

app = create_app()
