from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all SQLAlchemy models for test metadata
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.client import BrowserLoginToken
from app.services.browser_login_tokens import BrowserLoginTokenService, hash_browser_login_token


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    with session_factory() as session:
        yield session


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_internal_browser_login_token_endpoint_creates_hashed_token(client, db_session):
    response = client.post(
        "/api/v1/internal/browser-login-token",
        headers={"Authorization": f"Bearer {settings.BOT_SERVICE_TOKEN}"},
        json={
            "provider": "telegram",
            "provider_user_id": "12345",
            "display_name": "Bloom User",
            "username": "bloom_user",
            "photo_url": "https://example.test/avatar.jpg",
            "referral_code": "ABC123",
            "source": "telegram_bot",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token"]
    assert payload["login_url"] == f"https://app.bloomclub.ru/login?t={payload['token']}"

    token_record = db_session.execute(select(BrowserLoginToken)).scalar_one()
    assert token_record.token_hash == hash_browser_login_token(payload["token"])
    assert token_record.token_hash != payload["token"]
    assert token_record.provider == "telegram"
    assert token_record.provider_user_id == "12345"
    assert token_record.referral_code == "ABC123"
    assert token_record.source == "telegram_bot"


def test_browser_login_token_service_lifecycle(db_session):
    service = BrowserLoginTokenService(db_session)
    token, token_record = service.create_token(
        provider="vk",
        provider_user_id="42",
        source="vk_bot",
        ttl_seconds=60,
    )
    db_session.commit()

    found = service.get_by_token(token)
    assert found is not None
    assert found.id == token_record.id
    assert service.is_expired(found, now=datetime.now(timezone.utc) + timedelta(seconds=61))

    service.mark_used(found)
    assert found.used_at is not None
    service.revoke(found)
    assert found.revoked_at is not None
