"""Punkt wejscia ASGI: `uvicorn forvium.asgi:app`."""

from forvium.core.config import get_settings
from forvium.core.logging import configure_logging
from forvium.main import create_app

configure_logging(get_settings())
app = create_app()
