"""Warstwa bazy danych (SQLAlchemy 2.x)."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


# Jawne nazwy ograniczen: stabilne migracje (takze w trybie batch na SQLite).
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def new_id() -> str:
    return str(uuid.uuid4())


class Database:
    """Dwie pule polaczen:

    * glowna - transakcja zadania API (jedno polaczenie na zadanie; liczbe zadan naraz
      ogranicza core/concurrency.py do rozmiaru tej puli),
    * pomocnicza (`aux_sessionmaker`) - zapisy w niezaleznych transakcjach w trakcie zadania:
      audyt odmow i operacji API, limity prob, jednorazowe wyzwania WebAuthn.

    Gdyby oba rodzaje polaczen pochodzily z jednej puli, pod obciazeniem wszystkie watki
    moglyby trzymac polaczenie glowne i czekac na drugie z tej samej, wyczerpanej puli
    (zakleszczenie - wykryte testem obciazeniowym, deploy/loadtest). Rozmiary:
    FORVIUM_DB_POOL_SIZE / FORVIUM_DB_MAX_OVERFLOW / FORVIUM_DB_AUX_POOL_SIZE.
    """

    def __init__(self, url: str, pool_size: int = 10, max_overflow: int = 10, aux_pool_size: int = 5) -> None:
        kwargs: dict = {}
        aux_kwargs: dict = {}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
            if url in ("sqlite://", "sqlite:///:memory:"):
                kwargs["poolclass"] = StaticPool
            aux_kwargs = kwargs
        else:
            kwargs.update(pool_size=pool_size, max_overflow=max_overflow, pool_timeout=10, pool_pre_ping=True)
            aux_kwargs = {"pool_size": aux_pool_size, "max_overflow": aux_pool_size, "pool_timeout": 10,
                          "pool_pre_ping": True}
        self.engine = create_engine(url, **kwargs)
        self.sessionmaker = sessionmaker(bind=self.engine, expire_on_commit=False)
        # Pamiec SQLite (testy): jedno wspolne polaczenie, wiec ta sama pula.
        self.aux_engine = self.engine if kwargs.get("poolclass") is StaticPool else create_engine(url, **aux_kwargs)
        self.aux_sessionmaker = sessionmaker(bind=self.aux_engine, expire_on_commit=False)
        self.max_connections = pool_size + max_overflow

    def create_all(self) -> None:
        # Import modeli, aby zarejestrowaly sie w metadanych.
        from forvium import models  # noqa: F401

        Base.metadata.create_all(self.engine)


def get_db(request: Request) -> Iterator[Session]:
    db: Database = request.app.state.db
    session = db.sessionmaker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
