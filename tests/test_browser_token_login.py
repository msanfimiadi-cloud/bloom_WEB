from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.client import BrowserLoginToken, ClientIdentityLink, ClientProfile
from app.models.user import User, UserRole
from app.services.browser_login_tokens import BrowserLoginTokenService


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
    engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _create_profile(db_session, *, telegram_user_id: str | None = None, vk_user_id: str | None = None) -> ClientProfile:
    user = User(role=UserRole.CLIENT.value, is_active=True)
    db_session.add(user)
    db_session.flush()
    profile = ClientProfile(
        user_id=user.id,
        telegram_user_id=telegram_user_id,
        telegram_first_name="Browser",
        telegram_last_name="User",
        vk_user_id=vk_user_id,
        source="test",
        is_active=True,
    )
    db_session.add(profile)
    db_session.flush()
    return profile


def _create_token(db_session, *, provider: str = "telegram", provider_user_id: str = "tg-1", ttl_seconds: int = 60):
    token, record = BrowserLoginTokenService(db_session).create_token(
        provider=provider,
        provider_user_id=provider_user_id,
        ttl_seconds=ttl_seconds,
        source="telegram_bot",
    )
    db_session.commit()
    return token, record


def test_browser_token_login_valid_token_issues_jwt_and_marks_used(client, db_session) -> None:
    profile = _create_profile(db_session, telegram_user_id="tg-valid")
    token, record = _create_token(db_session, provider_user_id="tg-valid")

    response = client.post("/api/v1/auth/browser-token-login", json={"token": token})

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
    assert payload["client"]["id"] == profile.id
    db_session.refresh(record)
    assert record.used_at is not None


def test_browser_token_login_expired_token_returns_403(client, db_session) -> None:
    _create_profile(db_session, telegram_user_id="tg-expired")
    token, _ = _create_token(db_session, provider_user_id="tg-expired", ttl_seconds=-1)

    response = client.post("/api/v1/auth/browser-token-login", json={"token": token})

    assert response.status_code == 403
    assert response.json()["detail"] == "token_expired"


def test_browser_token_login_revoked_token_returns_403(client, db_session) -> None:
    _create_profile(db_session, telegram_user_id="tg-revoked")
    token, record = _create_token(db_session, provider_user_id="tg-revoked")
    record.revoked_at = datetime.now(timezone.utc)
    db_session.commit()

    response = client.post("/api/v1/auth/browser-token-login", json={"token": token})

    assert response.status_code == 403
    assert response.json()["detail"] == "token_revoked"


def test_browser_token_login_already_used_token_returns_403(client, db_session) -> None:
    _create_profile(db_session, telegram_user_id="tg-used")
    token, record = _create_token(db_session, provider_user_id="tg-used")
    record.used_at = datetime.now(timezone.utc)
    db_session.commit()

    response = client.post("/api/v1/auth/browser-token-login", json={"token": token})

    assert response.status_code == 403
    assert response.json()["detail"] == "token_already_used"


def test_browser_token_login_profile_not_found_returns_409(client, db_session) -> None:
    token, _ = _create_token(db_session, provider_user_id="tg-missing")

    response = client.post("/api/v1/auth/browser-token-login", json={"token": token})

    assert response.status_code == 409
    assert response.json()["detail"] == "profile_not_found"


def test_browser_token_login_legacy_linked_creates_identity_link_and_issues_jwt(client, db_session) -> None:
    profile = _create_profile(db_session, telegram_user_id="tg-legacy")
    token, _ = _create_token(db_session, provider_user_id="tg-legacy")

    response = client.post("/api/v1/auth/browser-token-login", json={"token": token})

    assert response.status_code == 200
    assert response.json()["client"]["id"] == profile.id
    link = db_session.execute(select(ClientIdentityLink).where(ClientIdentityLink.provider_user_id == "tg-legacy")).scalar_one()
    assert link.client_profile_id == profile.id


def test_browser_token_login_linked_identity_issues_jwt(client, db_session) -> None:
    profile = _create_profile(db_session)
    db_session.add(ClientIdentityLink(client_profile_id=profile.id, provider="telegram", provider_user_id="tg-linked"))
    token, _ = _create_token(db_session, provider_user_id="tg-linked")

    response = client.post("/api/v1/auth/browser-token-login", json={"token": token})

    assert response.status_code == 200
    assert response.json()["client"]["id"] == profile.id


def test_browser_token_login_repeated_login_returns_already_used(client, db_session) -> None:
    _create_profile(db_session, telegram_user_id="tg-repeat-login")
    token, _ = _create_token(db_session, provider_user_id="tg-repeat-login")

    first = client.post("/api/v1/auth/browser-token-login", json={"token": token})
    second = client.post("/api/v1/auth/browser-token-login", json={"token": token})

    assert first.status_code == 200
    assert second.status_code == 403
    assert second.json()["detail"] == "token_already_used"


def test_browser_token_login_missing_token_returns_404(client) -> None:
    response = client.post("/api/v1/auth/browser-token-login", json={"token": "missing"})

    assert response.status_code == 404
    assert response.json()["detail"] == "token_not_found"
