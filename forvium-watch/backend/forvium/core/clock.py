"""Zrodlo czasu. Wszystkie znaczniki czasu sa w UTC (naive), co upraszcza
porownania niezaleznie od silnika bazy. Testy przesuwaja czas przez `clock.advance`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


class Clock:
    def __init__(self) -> None:
        self._offset = timedelta(0)

    def now(self) -> datetime:
        return datetime.now(UTC).replace(tzinfo=None) + self._offset

    def advance(self, delta: timedelta) -> None:
        self._offset += delta

    def reset(self) -> None:
        self._offset = timedelta(0)


clock = Clock()
