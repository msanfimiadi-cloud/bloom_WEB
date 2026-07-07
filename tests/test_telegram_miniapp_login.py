from __future__ import annotations

import hmac
import json
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import settings
from app.core.security import decode_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.client import ClientProfile
from app.models.payment import Subscription, SubscriptionStatus
from app.models.user import User, UserRole


TELEGRAM_BOT_TOKEN = "123456:test-telegram-bot-token"


def _build_init_data(
    *,
    user: dict[str, object] | str | None = None,
    auth_date: int | None = None,
    bot_token: str = TELEGRAM_BOT_TOKEN,
) -> str:
    if user is None:
        user = {
            "id": 123456,
            "first_name": "Анна",
            "last_name": "Bloom",
            "username": "anna",
            "photo_url": "https://example.com/anna.jpg",
        }
    user_value = user if isinstance(user, str) else json.dumps(user, ensure_ascii=False, separators=(",", ":"))
    params = {
        "auth_date": str(auth_date or int(datetime.now(timezone.utc).timestamp())),
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "user": user_value,
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), sha256).digest()
    params["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), sha256).hexdigest()
    return urlencode(params)


def _open_override_session() -> tuple[Generator[Session, None, None], Session]:
    session_gen = app.dependency_overrides[get_db]()
    return session_gen, next(session_gen)


@pytest.fixture()
def telegram_miniapp_client() -> Generator[TestClient, None, None]:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    original_token = settings.TELEGRAM_BOT_TOKEN
    original_max_age = settings.TELEGRAM_MINIAPP_AUTH_MAX_AGE_SECONDS
    object.__setattr__(settings, "TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    object.__setattr__(settings, "TELEGRAM_MINIAPP_AUTH_MAX_AGE_SECONDS", 86400)

    with session_factory() as session:
        user = User(role=UserRole.CLIENT.value, is_active=True)
        session.add(user)
        session.flush()
        session.add(
            ClientProfile(
                user_id=user.id,
                telegram_user_id="777001",
                telegram_username="old_username",
                telegram_first_name="Old",
                telegram_last_name="Name",
                telegram_photo_url="https://example.com/old.jpg",
                full_name="Old Name",
                source="telegram-miniapp",
                is_active=True,
            )
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        object.__setattr__(settings, "TELEGRAM_BOT_TOKEN", original_token)
        object.__setattr__(settings, "TELEGRAM_MINIAPP_AUTH_MAX_AGE_SECONDS", original_max_age)
        engine.dispose()


def test_telegram_miniapp_login_valid_init_data_passes(telegram_miniapp_client: TestClient) -> None:
    response = telegram_miniapp_client.post(
        "/api/v1/auth/telegram-miniapp-login",
        json={"init_data": _build_init_data()},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"] == {
        "id": body["user"]["id"],
        "telegram_user_id": "123456",
        "first_name": "Анна",
        "last_name": "Bloom",
        "username": "anna",
        "photo_url": "https://example.com/anna.jpg",
        "role": UserRole.CLIENT.value,
    }
    assert body["client"]["telegram_user_id"] == "123456"
    assert body["client"]["source"] == "telegram-miniapp"
    assert body["subscription"] == {"is_active": False, "expires_at": None}
    assert decode_access_token(body["access_token"])["sub"] == f"user:{body['user']['id']}"


def test_telegram_miniapp_login_invalid_hash_rejected(telegram_miniapp_client: TestClient) -> None:
    response = telegram_miniapp_client.post(
        "/api/v1/auth/telegram-miniapp-login",
        json={"init_data": _build_init_data() + "tampered"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_hash"


def test_telegram_miniapp_login_missing_init_data_rejected(telegram_miniapp_client: TestClient) -> None:
    response = telegram_miniapp_client.post("/api/v1/auth/telegram-miniapp-login", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "missing_init_data"


def test_telegram_miniapp_login_expired_auth_date_rejected(telegram_miniapp_client: TestClient) -> None:
    stale_ts = int((datetime.now(timezone.utc) - timedelta(days=2)).timestamp())
    response = telegram_miniapp_client.post(
        "/api/v1/auth/telegram-miniapp-login",
        json={"init_data": _build_init_data(auth_date=stale_ts)},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "expired_auth_date"


def test_telegram_miniapp_login_missing_bot_token_controlled_error(telegram_miniapp_client: TestClient) -> None:
    object.__setattr__(settings, "TELEGRAM_BOT_TOKEN", "")
    response = telegram_miniapp_client.post(
        "/api/v1/auth/telegram-miniapp-login",
        json={"init_data": _build_init_data()},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "missing_telegram_bot_token"
    assert "access_token" not in response.json()


def test_telegram_miniapp_login_invalid_user_payload_rejected(telegram_miniapp_client: TestClient) -> None:
    response = telegram_miniapp_client.post(
        "/api/v1/auth/telegram-miniapp-login",
        json={"init_data": _build_init_data(user={"username": "missing_id"})},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid_user_payload"


def test_telegram_miniapp_login_existing_client_reused_and_updated(telegram_miniapp_client: TestClient) -> None:
    response = telegram_miniapp_client.post(
        "/api/v1/auth/telegram-miniapp-login",
        json={
            "init_data": _build_init_data(
                user={
                    "id": 777001,
                    "first_name": "New",
                    "last_name": "Name",
                    "username": "new_username",
                    "photo_url": "https://example.com/new.jpg",
                }
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["client"]["telegram_username"] == "new_username"

    session_gen, session = _open_override_session()
    try:
        profiles = session.execute(select(ClientProfile).where(ClientProfile.telegram_user_id == "777001")).scalars().all()
        assert len(profiles) == 1
        assert session.query(User).count() == 1
        assert profiles[0].telegram_first_name == "New"
        assert profiles[0].telegram_photo_url == "https://example.com/new.jpg"
    finally:
        session_gen.close()


def test_telegram_miniapp_login_new_client_created(telegram_miniapp_client: TestClient) -> None:
    response = telegram_miniapp_client.post(
        "/api/v1/auth/telegram-miniapp-login",
        json={"init_data": _build_init_data(user={"id": 888002, "first_name": "Ева"})},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["client"]["telegram_user_id"] == "888002"
    assert body["client"]["full_name"] == "Ева"
    assert body["user"]["role"] == UserRole.CLIENT.value


def test_telegram_miniapp_login_includes_active_subscription(telegram_miniapp_client: TestClient) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    session_gen, session = _open_override_session()
    try:
        profile = session.execute(select(ClientProfile).where(ClientProfile.telegram_user_id == "777001")).scalar_one()
        session.add(
            Subscription(
                client_id=profile.id,
                status=SubscriptionStatus.active.value,
                starts_at=datetime.now(timezone.utc) - timedelta(days=1),
                ends_at=expires_at,
                source="test",
            )
        )
        session.commit()
    finally:
        session_gen.close()

    response = telegram_miniapp_client.post(
        "/api/v1/auth/telegram-miniapp-login",
        json={"init_data": _build_init_data(user={"id": 777001, "first_name": "Sub"})},
    )

    assert response.status_code == 200
    subscription = response.json()["subscription"]
    assert subscription["is_active"] is True
    assert subscription["expires_at"] is not None


def test_vk_auth_contract_paths_still_preserved(telegram_miniapp_client: TestClient) -> None:
    post_routes = {route.path for route in app.router.routes if "POST" in getattr(route, "methods", set())}

    assert "/api/v1/auth/vk-miniapp-login" in post_routes
    assert "/auth/vk-miniapp-login" in post_routes
    assert "/api/v1/auth/telegram-miniapp-login" in post_routes


def test_documented_risk_telegram_login_uses_telegram_user_id_only_not_existing_phone_or_email(
    telegram_miniapp_client: TestClient,
) -> None:
    """Documentation regression: Telegram login must not silently merge by unverified phone/email today."""
    session_gen, session = _open_override_session()
    try:
        existing_user = User(
            email="same-telegram-person@example.com",
            phone="+79990008888",
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        session.add(existing_user)
        session.flush()
        existing_profile = ClientProfile(
            user_id=existing_user.id,
            contact_email="same-telegram-person@example.com",
            source="web",
            is_active=True,
        )
        session.add(existing_profile)
        session.commit()
        existing_user_id = existing_user.id
        existing_profile_id = existing_profile.id
    finally:
        session_gen.close()

    response = telegram_miniapp_client.post(
        "/api/v1/auth/telegram-miniapp-login",
        json={"init_data": _build_init_data(user={"id": 889900, "first_name": "Same"})},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["client"]["telegram_user_id"] == "889900"
    assert body["client"]["id"] != existing_profile_id
    assert body["user"]["id"] != existing_user_id

    session_gen, session = _open_override_session()
    try:
        original_profile = session.get(ClientProfile, existing_profile_id)
        new_profile = session.execute(select(ClientProfile).where(ClientProfile.telegram_user_id == "889900")).scalar_one()
        assert original_profile is not None
        assert original_profile.telegram_user_id is None
        assert new_profile.user_id != existing_user_id
    finally:
        session_gen.close()
