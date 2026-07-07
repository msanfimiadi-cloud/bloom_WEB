from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


DB_POOL_RECYCLE_SECONDS = 1800


def _sync_database_url(url: str) -> str:
    return (
        url.replace("sqlite+aiosqlite://", "sqlite://")
        .replace("postgresql+asyncpg://", "postgresql+psycopg://")
    )


def _engine_options(database_url: str) -> dict[str, object]:
    url = make_url(database_url)
    options: dict[str, object] = {"future": True, "pool_pre_ping": True}
    if url.get_backend_name() != "sqlite":
        options["pool_recycle"] = DB_POOL_RECYCLE_SECONDS
    return options


_sync_url = _sync_database_url(settings.DATABASE_URL)
engine = create_engine(_sync_url, **_engine_options(_sync_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
