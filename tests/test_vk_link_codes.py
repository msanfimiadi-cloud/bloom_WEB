from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all SQLAlchemy models for test metadata
from app.core.config import settings
from app.core.security import hash_password, hash_password_setup_token, verify_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.city import City
from app.models.client import (
    ClientPasswordSetupToken,
    ClientProfile,
    VkLinkCode,
    VkLinkCodeStatus,
)
from app.models.user import User, UserRole

BOT_API_TOKEN = "test-vk-bot-service-token"


@pytest.fixture()
def vk_link_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    Base.metadata.create_all(bind=engine)
    with session_factory() as session:
        session.add_all(
            [
                User(
                    email="client@example.com",
                    phone="+79990000001",
                    password_hash=hash_password("ClientPassword123"),
                    role=UserRole.CLIENT.value,
                    is_active=True,
                ),
                User(
                    email="other@example.com",
                    phone="+79990000002",
                    password_hash=hash_password("OtherPassword123"),
                    role=UserRole.CLIENT.value,
                    is_active=True,
                ),
                City(name="Moscow", slug="moscow", is_active=True),
                City(name="Hidden", slug="hidden", is_active=False),
            ]
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    old_token = settings.BOT_API_TOKEN
    object.__setattr__(settings, "BOT_API_TOKEN", BOT_API_TOKEN)
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        object.__setattr__(settings, "BOT_API_TOKEN", old_token)
        engine.dispose()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _bot_headers(token: str = BOT_API_TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_login(
    client: TestClient,
    login: str = "client@example.com",
    password: str = "ClientPassword123",
) -> str:
    response = client.post(
        "/api/v1/auth/user-login", json={"login": login, "password": password}
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _create_code(client: TestClient) -> str:
    token = _user_login(client)
    response = client.post(
        "/api/v1/clients/me/vk-link-codes", headers=_auth_headers(token)
    )
    assert response.status_code == 200
    return str(response.json()["code"])


def _db_session() -> Session:
    return next(app.dependency_overrides[get_db]())


def test_create_vk_link_code_without_token_returns_401(
    vk_link_client: TestClient,
) -> None:
    response = vk_link_client.post("/api/v1/clients/me/vk-link-codes")

    assert response.status_code == 401


def test_client_creates_vk_link_code(vk_link_client: TestClient) -> None:
    token = _user_login(vk_link_client)

    response = vk_link_client.post(
        "/api/v1/clients/me/vk-link-codes", headers=_auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["code"]) == 8
    assert data["code"].isalnum()
    assert data["code"] == data["code"].upper()
    assert data["status"] == "active"
    assert data["expires_at"]
    assert 0 < data["ttl_seconds"] <= 600


def test_creating_second_code_cancels_previous_active_code(
    vk_link_client: TestClient,
) -> None:
    token = _user_login(vk_link_client)
    first = vk_link_client.post(
        "/api/v1/clients/me/vk-link-codes", headers=_auth_headers(token)
    ).json()["code"]
    second = vk_link_client.post(
        "/api/v1/clients/me/vk-link-codes", headers=_auth_headers(token)
    ).json()["code"]

    assert first != second
    with _db_session() as session:
        first_code = session.execute(
            select(VkLinkCode).where(VkLinkCode.code == first)
        ).scalar_one()
        second_code = session.execute(
            select(VkLinkCode).where(VkLinkCode.code == second)
        ).scalar_one()
        assert first_code.status == VkLinkCodeStatus.CANCELLED.value
        assert second_code.status == VkLinkCodeStatus.ACTIVE.value


def test_bot_exchange_without_service_token_returns_401(
    vk_link_client: TestClient,
) -> None:
    response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        json={"vk_user_id": "123", "code": "ABC12345"},
    )

    assert response.status_code == 401


def test_bot_exchange_with_wrong_service_token_returns_401(
    vk_link_client: TestClient,
) -> None:
    response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers("wrong-token"),
        json={"vk_user_id": "123", "code": "ABC12345"},
    )

    assert response.status_code == 401


def test_bot_exchange_valid_code_links_vk_and_returns_working_token(
    vk_link_client: TestClient,
) -> None:
    code = _create_code(vk_link_client)

    response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "  vk-123  ", "code": f"  {code.lower()}  "},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "client@example.com"
    with _db_session() as session:
        profile = session.execute(
            select(ClientProfile).where(ClientProfile.vk_user_id == "vk-123")
        ).scalar_one()
        link_code = session.execute(
            select(VkLinkCode).where(VkLinkCode.code == code)
        ).scalar_one()
        assert profile.vk_user_id == "vk-123"
        assert link_code.status == VkLinkCodeStatus.USED.value
        assert link_code.used_at is not None

    me_response = vk_link_client.get(
        "/api/v1/auth/user-me", headers=_auth_headers(data["access_token"])
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "client@example.com"


def test_bot_exchange_accepts_case_and_space_variants(
    vk_link_client: TestClient,
) -> None:
    variants = [
        lambda code: code,
        lambda code: code.lower(),
        lambda code: f"   {code[:3].lower()}{code[3:].upper()}   ",
        lambda code: f"{code} ",
    ]

    for index, make_payload_code in enumerate(variants, start=1):
        code = _create_code(vk_link_client)

        response = vk_link_client.post(
            "/api/v1/bot/vk/exchange-link-code",
            headers=_bot_headers(),
            json={
                "vk_user_id": f"vk-normalized-{index}",
                "code": make_payload_code(code),
            },
        )

        assert response.status_code == 200
        with _db_session() as session:
            link_code = session.execute(
                select(VkLinkCode).where(VkLinkCode.code == code)
            ).scalar_one()
            profile = session.execute(
                select(ClientProfile).where(
                    ClientProfile.vk_user_id == f"vk-normalized-{index}"
                )
            ).scalar_one()
            assert link_code.status == VkLinkCodeStatus.USED.value
            profile.vk_user_id = None
            session.commit()


def test_exchange_fresh_code_with_naive_utc_expiry_is_valid(
    vk_link_client: TestClient,
) -> None:
    code = _create_code(vk_link_client)
    with _db_session() as session:
        link_code = session.execute(
            select(VkLinkCode).where(VkLinkCode.code == code)
        ).scalar_one()
        link_code.expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=5)
        ).replace(tzinfo=None)
        session.commit()

    response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-naive-fresh", "code": code},
    )

    assert response.status_code == 200
    with _db_session() as session:
        profile = session.execute(
            select(ClientProfile).where(ClientProfile.vk_user_id == "vk-naive-fresh")
        ).scalar_one()
        assert profile.vk_user_id == "vk-naive-fresh"


def test_invalid_exchange_attempt_does_not_consume_valid_code(
    vk_link_client: TestClient,
) -> None:
    code = _create_code(vk_link_client)

    missing_response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-invalid-first", "code": "NO-SUCH-CODE"},
    )

    assert missing_response.status_code == 404
    with _db_session() as session:
        link_code = session.execute(
            select(VkLinkCode).where(VkLinkCode.code == code)
        ).scalar_one()
        assert link_code.status == VkLinkCodeStatus.ACTIVE.value
        assert link_code.used_at is None

    valid_response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-invalid-first", "code": code},
    )

    assert valid_response.status_code == 200


def test_exchange_rejects_profile_already_linked_to_different_vk_without_consuming_code(
    vk_link_client: TestClient,
) -> None:
    code = _create_code(vk_link_client)
    with _db_session() as session:
        profile = session.execute(
            select(ClientProfile).join(User).where(User.email == "client@example.com")
        ).scalar_one()
        profile.vk_user_id = "vk-existing"
        session.commit()

    response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-new", "code": code},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Client profile is already linked"
    with _db_session() as session:
        profile = session.execute(
            select(ClientProfile).join(User).where(User.email == "client@example.com")
        ).scalar_one()
        link_code = session.execute(
            select(VkLinkCode).where(VkLinkCode.code == code)
        ).scalar_one()
        assert profile.vk_user_id == "vk-existing"
        assert link_code.status == VkLinkCodeStatus.ACTIVE.value
        assert link_code.used_at is None


def test_exchange_rejects_vk_user_linked_to_different_profile_without_consuming_code(
    vk_link_client: TestClient,
) -> None:
    token = _user_login(vk_link_client)
    code = vk_link_client.post(
        "/api/v1/clients/me/vk-link-codes", headers=_auth_headers(token)
    ).json()["code"]
    with _db_session() as session:
        other_user = session.execute(
            select(User).where(User.email == "other@example.com")
        ).scalar_one()
        session.add(
            ClientProfile(
                user_id=other_user.id,
                vk_user_id="vk-conflict",
                is_active=True,
                source="vk",
            )
        )
        session.commit()

    response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-conflict", "code": code},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "VK user is already linked"
    with _db_session() as session:
        link_code = session.execute(
            select(VkLinkCode).where(VkLinkCode.code == code)
        ).scalar_one()
        assert link_code.status == VkLinkCodeStatus.ACTIVE.value
        assert link_code.used_at is None


def test_exchange_missing_code_returns_404(vk_link_client: TestClient) -> None:
    response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "123", "code": "missing"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Link code not found"


def test_exchange_expired_code_marks_expired_and_returns_400(
    vk_link_client: TestClient,
) -> None:
    code = _create_code(vk_link_client)
    with _db_session() as session:
        link_code = session.execute(
            select(VkLinkCode).where(VkLinkCode.code == code)
        ).scalar_one()
        link_code.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        session.commit()

    response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "123", "code": code},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Link code expired"
    with _db_session() as session:
        link_code = session.execute(
            select(VkLinkCode).where(VkLinkCode.code == code)
        ).scalar_one()
        assert link_code.status == VkLinkCodeStatus.EXPIRED.value


def test_exchange_used_or_cancelled_code_returns_400(
    vk_link_client: TestClient,
) -> None:
    used_code = _create_code(vk_link_client)
    used_response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "123", "code": used_code},
    )
    assert used_response.status_code == 200

    used_again_response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "123", "code": used_code},
    )
    assert used_again_response.status_code == 400
    assert used_again_response.json()["detail"] == "Link code already used"

    token = _user_login(vk_link_client)
    cancelled_code = vk_link_client.post(
        "/api/v1/clients/me/vk-link-codes", headers=_auth_headers(token)
    ).json()["code"]
    vk_link_client.post(
        "/api/v1/clients/me/vk-link-codes", headers=_auth_headers(token)
    )
    cancelled_response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "456", "code": cancelled_code},
    )
    assert cancelled_response.status_code == 400
    assert cancelled_response.json()["detail"] == "Link code is not active"


def test_exchange_empty_vk_user_id_returns_400(vk_link_client: TestClient) -> None:
    code = _create_code(vk_link_client)

    response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "   ", "code": code},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "VK user ID is required"


def test_bot_vk_token_returns_token_for_linked_vk_user_id(
    vk_link_client: TestClient,
) -> None:
    code = _create_code(vk_link_client)
    exchange_response = vk_link_client.post(
        "/api/v1/bot/vk/exchange-link-code",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-linked", "code": code},
    )
    assert exchange_response.status_code == 200

    response = vk_link_client.post(
        "/api/v1/bot/vk/token",
        headers=_bot_headers(),
        json={"vk_user_id": " vk-linked "},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    me_response = vk_link_client.get(
        "/api/v1/clients/me", headers=_auth_headers(data["access_token"])
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "client@example.com"


def test_bot_vk_token_returns_404_for_unlinked_vk_user_id(
    vk_link_client: TestClient,
) -> None:
    response = vk_link_client.post(
        "/api/v1/bot/vk/token",
        headers=_bot_headers(),
        json={"vk_user_id": "not-linked"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "VK user is not linked"


def test_bot_onboard_client_without_service_token_returns_401(
    vk_link_client: TestClient,
) -> None:
    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        json={"vk_user_id": "vk-onboard-1"},
    )

    assert response.status_code == 401


def test_bot_onboard_client_with_wrong_service_token_returns_401(
    vk_link_client: TestClient,
) -> None:
    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers("wrong-token"),
        json={"vk_user_id": "vk-onboard-1"},
    )

    assert response.status_code == 401


def test_bot_onboard_client_empty_vk_user_id_returns_400(
    vk_link_client: TestClient,
) -> None:
    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "   "},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "vk_user_id must not be empty"


def test_bot_onboard_client_creates_client_user_with_temporary_password_and_profile(
    vk_link_client: TestClient,
) -> None:
    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={
            "vk_user_id": "  vk-new-client  ",
            "full_name": "  New Client  ",
            "source": None,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["is_new"] is True
    assert data["password_setup_required"] is True
    temporary_password = data["temporary_password"]
    assert isinstance(temporary_password, str)
    assert len(temporary_password) >= 20
    assert data["login"].startswith("vk_")
    assert data["login"].endswith("@vk.local")
    assert (
        data["web_login_url"]
        == f"{settings.WEB_PUBLIC_URL}/?client_login={data['login'].replace('@', '%40')}"
    )
    assert f"login={data['login'].replace('@', '%40')}" in data["password_setup_url"]
    assert data["user"]["email"] == data["login"]
    assert data["user"]["phone"] is None
    assert data["user"]["role"] == UserRole.CLIENT.value
    assert "password_hash" not in data["user"]
    assert data["client"]["vk_user_id"] == "vk-new-client"
    assert data["client"]["full_name"] == "New Client"
    assert data["client"]["source"] == "vk"
    assert data["client"]["is_active"] is True

    with _db_session() as session:
        profile = session.execute(
            select(ClientProfile).where(ClientProfile.vk_user_id == "vk-new-client")
        ).scalar_one()
        user = session.execute(
            select(User).where(User.id == profile.user_id)
        ).scalar_one()
        assert user.role == UserRole.CLIENT.value
        assert user.is_active is True
        assert user.password_hash is not None
        assert user.password_hash != temporary_password
        assert temporary_password not in user.password_hash
        assert verify_password(temporary_password, user.password_hash)
        assert user.email == data["login"]
        assert user.phone is None
        assert profile.full_name == "New Client"
        assert profile.source == "vk"

    login_response = vk_link_client.post(
        "/api/v1/auth/user-login",
        json={"login": data["login"], "password": temporary_password},
    )
    assert login_response.status_code == 200


def test_bot_onboard_client_returned_token_works_for_client_me(
    vk_link_client: TestClient,
) -> None:
    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-token-client"},
    )
    assert response.status_code == 200

    me_response = vk_link_client.get(
        "/api/v1/clients/me",
        headers=_auth_headers(response.json()["access_token"]),
    )

    assert me_response.status_code == 200
    assert me_response.json()["vk_user_id"] == "vk-token-client"


def test_bot_onboard_client_repeated_vk_user_id_returns_existing_profile(
    vk_link_client: TestClient,
) -> None:
    first_response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-repeat"},
    )
    assert first_response.status_code == 200
    first_data = first_response.json()

    second_response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": " vk-repeat "},
    )

    assert second_response.status_code == 200
    second_data = second_response.json()
    assert second_data["is_new"] is False
    assert second_data["user"]["id"] == first_data["user"]["id"]
    assert second_data["client"]["id"] == first_data["client"]["id"]
    assert second_data["login"] == first_data["login"]
    assert second_data["login"].startswith("vk_")
    assert second_data["login"].endswith("@vk.local")
    assert second_data["temporary_password"] is None
    assert second_data["password_setup_required"] is True
    assert second_data["password_setup_url"]
    with _db_session() as session:
        users_count = len(
            session.execute(select(User).where(User.email == first_data["login"]))
            .scalars()
            .all()
        )
        profiles_count = len(
            session.execute(
                select(ClientProfile).where(ClientProfile.vk_user_id == "vk-repeat")
            )
            .scalars()
            .all()
        )
        assert users_count == 1
        assert profiles_count == 1


def test_bot_onboard_client_restores_missing_bind_for_existing_synthetic_account(
    vk_link_client: TestClient,
) -> None:
    with _db_session() as session:
        user = User(
            email="vk_d7a4bcaee5a6c79f523d4c356a74b016@vk.local",
            phone=None,
            password_hash=hash_password("ExistingSyntheticPass123"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        session.add(user)
        session.flush()
        session.add(
            ClientProfile(
                user_id=user.id,
                vk_user_id=None,
                is_active=True,
                source="vk",
            )
        )
        session.commit()

    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-restore-bind"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_new"] is False
    assert data["temporary_password"] is None
    assert data["client"]["vk_user_id"] == "vk-restore-bind"

    with _db_session() as session:
        profile = session.execute(
            select(ClientProfile).where(ClientProfile.id == data["client"]["id"])
        ).scalar_one()
        assert profile.vk_user_id == "vk-restore-bind"


def test_bot_onboard_client_later_contact_does_not_overwrite_synthetic_login(
    vk_link_client: TestClient,
) -> None:
    first_response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-later-contact"},
    )
    assert first_response.status_code == 200
    first_login = first_response.json()["login"]

    second_response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={
            "vk_user_id": "vk-later-contact",
            "email": "Real@Example.COM",
            "phone": "+79990001122",
        },
    )

    assert second_response.status_code == 200
    data = second_response.json()
    assert data["login"] == first_login
    assert data["user"]["email"] == first_login
    assert data["user"]["phone"] == "+79990001122"


def test_bot_onboard_client_existing_real_email_not_overwritten(
    vk_link_client: TestClient,
) -> None:
    with _db_session() as session:
        user = User(
            email="real-existing@example.com",
            phone=None,
            password_hash=None,
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        session.add(user)
        session.flush()
        session.add(
            ClientProfile(
                user_id=user.id, vk_user_id="vk-real-email", is_active=True, source="vk"
            )
        )
        session.commit()

    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-real-email"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["login"] == "real-existing@example.com"
    assert data["user"]["email"] == "real-existing@example.com"


def _extract_setup_token(setup_url: str) -> str:
    parsed = urlparse(setup_url)
    values = parse_qs(parsed.query).get("setup_token")
    assert values
    return values[0]


def test_bot_onboard_client_returns_password_setup_url_and_stores_only_token_hash(
    vk_link_client: TestClient,
) -> None:
    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-setup-url", "email": "  ClientSetup@Example.COM  "},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["password_setup_required"] is True
    assert data["password_setup_url"].startswith(
        f"{settings.WEB_PUBLIC_URL}/?setup_token="
    )
    assert data["login"] == "clientsetup@example.com"
    assert (
        data["web_login_url"]
        == f"{settings.WEB_PUBLIC_URL}/?client_login=clientsetup%40example.com"
    )
    assert data["password_setup_ttl_seconds"] == 3600
    assert data["password_setup_expires_at"]
    assert "login=clientsetup%40example.com" in data["password_setup_url"]

    plain_token = _extract_setup_token(data["password_setup_url"])
    with _db_session() as session:
        setup_token = session.execute(select(ClientPasswordSetupToken)).scalar_one()
        assert setup_token.token_hash == hash_password_setup_token(plain_token)
        assert setup_token.token_hash != plain_token
        assert plain_token not in setup_token.token_hash
        assert setup_token.purpose == "vk_onboarding_password_setup"
        assert setup_token.used_at is None
        assert setup_token.source == "vk"
        assert setup_token.vk_user_id == "vk-setup-url"


def test_password_setup_complete_sets_password_and_user_can_login(
    vk_link_client: TestClient,
) -> None:
    onboard_response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-complete", "phone": " +79990007777 "},
    )
    assert onboard_response.status_code == 200
    plain_token = _extract_setup_token(onboard_response.json()["password_setup_url"])

    complete_response = vk_link_client.post(
        "/api/v1/auth/password-setup/complete",
        json={
            "token": plain_token,
            "password": "ClientPass123",
            "password_confirm": "ClientPass123",
        },
    )

    assert complete_response.status_code == 200
    assert complete_response.json()["ok"] is True
    assert complete_response.json()["login"] == onboard_response.json()["login"]
    with _db_session() as session:
        profile = session.execute(
            select(ClientProfile).where(ClientProfile.vk_user_id == "vk-complete")
        ).scalar_one()
        user = session.get(User, profile.user_id)
        assert user is not None
        assert user.password_hash is not None
        assert verify_password("ClientPass123", user.password_hash)
        setup_token = session.execute(select(ClientPasswordSetupToken)).scalar_one()
        assert setup_token.used_at is not None

    login_response = vk_link_client.post(
        "/api/v1/auth/user-login",
        json={"login": "+79990007777", "password": "ClientPass123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["user"]["role"] == UserRole.CLIENT.value


def test_password_setup_complete_allows_login_with_synthetic_vk_login(
    vk_link_client: TestClient,
) -> None:
    onboard_response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-synthetic-complete"},
    )
    assert onboard_response.status_code == 200
    onboard_data = onboard_response.json()
    returned_login = onboard_data["login"]
    plain_token = _extract_setup_token(onboard_data["password_setup_url"])

    complete_response = vk_link_client.post(
        "/api/v1/auth/password-setup/complete",
        json={
            "token": plain_token,
            "password": "ClientPass123",
            "password_confirm": "ClientPass123",
        },
    )

    assert complete_response.status_code == 200
    assert complete_response.json()["login"] == returned_login

    login_response = vk_link_client.post(
        "/api/v1/auth/user-login",
        json={"login": returned_login, "password": "ClientPass123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == returned_login


def test_password_setup_token_reuse_is_rejected(vk_link_client: TestClient) -> None:
    onboard_response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-reuse", "email": "reuse@example.com"},
    )
    plain_token = _extract_setup_token(onboard_response.json()["password_setup_url"])
    first = vk_link_client.post(
        "/api/v1/auth/password-setup/complete",
        json={
            "token": plain_token,
            "password": "ClientPass123",
            "password_confirm": "ClientPass123",
        },
    )
    assert first.status_code == 200

    second = vk_link_client.post(
        "/api/v1/auth/password-setup/complete",
        json={
            "token": plain_token,
            "password": "OtherPass123",
            "password_confirm": "OtherPass123",
        },
    )
    assert second.status_code == 400


def test_expired_password_setup_token_is_rejected(vk_link_client: TestClient) -> None:
    onboard_response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-expired", "email": "expired@example.com"},
    )
    plain_token = _extract_setup_token(onboard_response.json()["password_setup_url"])
    with _db_session() as session:
        setup_token = session.execute(select(ClientPasswordSetupToken)).scalar_one()
        setup_token.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        session.commit()

    response = vk_link_client.post(
        "/api/v1/auth/password-setup/complete",
        json={
            "token": plain_token,
            "password": "ClientPass123",
            "password_confirm": "ClientPass123",
        },
    )
    assert response.status_code == 400


def test_password_setup_mismatch_is_rejected(vk_link_client: TestClient) -> None:
    onboard_response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-mismatch", "email": "mismatch@example.com"},
    )
    plain_token = _extract_setup_token(onboard_response.json()["password_setup_url"])

    response = vk_link_client.post(
        "/api/v1/auth/password-setup/complete",
        json={
            "token": plain_token,
            "password": "ClientPass123",
            "password_confirm": "DifferentPass123",
        },
    )
    assert response.status_code == 400


def test_onboarding_existing_client_with_password_gets_setup_url_without_plain_password(
    vk_link_client: TestClient,
) -> None:
    with _db_session() as session:
        user = User(
            email="existing-password@example.com",
            phone=None,
            password_hash=hash_password("ExistingPass123"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        session.add(user)
        session.flush()
        session.add(
            ClientProfile(
                user_id=user.id,
                vk_user_id="vk-has-password",
                is_active=True,
                source="vk",
            )
        )
        session.commit()

    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-has-password"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["password_setup_required"] is True
    assert data["password_setup_url"].startswith(
        f"{settings.WEB_PUBLIC_URL}/?setup_token="
    )
    assert data["password_setup_expires_at"]
    assert data["password_setup_ttl_seconds"] == 3600
    assert data["temporary_password"] is None
    assert data["login"] == "existing-password@example.com"
    assert (
        data["web_login_url"]
        == f"{settings.WEB_PUBLIC_URL}/?client_login=existing-password%40example.com"
    )


def test_bot_onboard_client_active_city_slug_sets_selected_city_id(
    vk_link_client: TestClient,
) -> None:
    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-with-city", "selected_city_slug": " moscow "},
    )

    assert response.status_code == 200
    data = response.json()
    with _db_session() as session:
        city = session.execute(select(City).where(City.slug == "moscow")).scalar_one()
        assert data["client"]["selected_city_id"] == city.id


def test_bot_onboard_client_existing_profile_updates_selected_city(
    vk_link_client: TestClient,
) -> None:
    first_response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-city-sync"},
    )
    assert first_response.status_code == 200
    assert first_response.json()["client"]["selected_city_id"] is None

    second_response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-city-sync", "selected_city_slug": "moscow"},
    )

    assert second_response.status_code == 200
    assert second_response.json()["is_new"] is False
    with _db_session() as session:
        city = session.execute(select(City).where(City.slug == "moscow")).scalar_one()
        profile = session.execute(
            select(ClientProfile).where(ClientProfile.vk_user_id == "vk-city-sync")
        ).scalar_one()
        assert second_response.json()["client"]["selected_city_id"] == city.id
        assert profile.selected_city_id == city.id


@pytest.mark.parametrize("city_slug", ["missing", "hidden"])
def test_bot_onboard_client_missing_or_inactive_city_slug_returns_404(
    vk_link_client: TestClient,
    city_slug: str,
) -> None:
    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-bad-city", "selected_city_slug": city_slug},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "City not found"


def test_bot_onboard_client_existing_linked_inactive_user_returns_clean_error(
    vk_link_client: TestClient,
) -> None:
    with _db_session() as session:
        user = User(
            email="inactive-client@example.com",
            phone="+79990000003",
            password_hash=None,
            role=UserRole.CLIENT.value,
            is_active=False,
        )
        session.add(user)
        session.flush()
        session.add(
            ClientProfile(
                user_id=user.id,
                vk_user_id="vk-inactive-user",
                is_active=True,
                source="vk",
            )
        )
        session.commit()

    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-inactive-user"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Client user not found"


def test_bot_onboard_client_existing_linked_non_client_user_returns_clean_error(
    vk_link_client: TestClient,
) -> None:
    with _db_session() as session:
        user = User(
            email="partner-linked@example.com",
            phone="+79990000004",
            password_hash=None,
            role=UserRole.PARTNER.value,
            is_active=True,
        )
        session.add(user)
        session.flush()
        session.add(
            ClientProfile(
                user_id=user.id, vk_user_id="vk-non-client", is_active=True, source="vk"
            )
        )
        session.commit()

    response = vk_link_client.post(
        "/api/v1/bot/vk/onboard-client",
        headers=_bot_headers(),
        json={"vk_user_id": "vk-non-client"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Linked user is not a client"
