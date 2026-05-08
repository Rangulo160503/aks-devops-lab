"""SQLAlchemy engine + session helpers.

The engine is created lazily and cached per process so each Gunicorn worker
gets its own connection pool. Schema creation here is intentionally minimal
(`Base.metadata.create_all`) so the lab can run without Alembic. Real Alembic
migrations live under `app/backend/migrations/`.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .config import Settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _engine_kwargs(url: str) -> dict[str, Any]:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}, "future": True}
    return {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 5,
        "future": True,
    }


def init_engine(settings: Settings) -> Engine:
    global _engine, _SessionLocal
    _engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")
    return _engine


@contextmanager
def session_scope() -> Iterator[Session]:
    if _SessionLocal is None:
        raise RuntimeError("Session factory not initialized. Call init_engine() first.")
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping() -> bool:
    """Used by /readyz. Returns True iff the DB answers `SELECT 1`."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True


def create_all() -> None:
    """Lab-only convenience: create tables from ORM metadata."""
    from . import models

    models.Base.metadata.create_all(bind=get_engine())
