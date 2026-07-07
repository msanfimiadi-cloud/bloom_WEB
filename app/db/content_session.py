from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.session import DB_POOL_RECYCLE_SECONDS, _sync_database_url


def _engine_options(database_url: str) -> dict[str, object]:
    url = make_url(database_url)
    options: dict[str, object] = {"future": True, "pool_pre_ping": True}
    if url.get_backend_name() != "sqlite":
        options["pool_recycle"] = DB_POOL_RECYCLE_SECONDS
    return options


_content_sync_url = _sync_database_url(settings.CONTENT_DATABASE_URL)
content_engine = create_engine(_content_sync_url, **_engine_options(_content_sync_url))
ContentSessionLocal = sessionmaker(bind=content_engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_content_db() -> Generator[Session, None, None]:
    with ContentSessionLocal() as session:
        yield session
