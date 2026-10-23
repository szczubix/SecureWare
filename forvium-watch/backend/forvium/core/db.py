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
    def __init__(self, url: str) -> None:
        kwargs: dict = {}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
            if url in ("sqlite://", "sqlite:///:memory:"):
                kwargs["poolclass"] = StaticPool
        self.engine = create_engine(url, **kwargs)
        self.sessionmaker = sessionmaker(bind=self.engine, expire_on_commit=False)

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
