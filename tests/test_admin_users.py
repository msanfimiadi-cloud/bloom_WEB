from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all SQLAlchemy models for test metadata
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.city import City
from app.models.client import (
    AccountLinkingChallenge,
    ClientIdentityLink,
    ClientPasswordSetupToken,
    ClientProfile,
    ClientReferral,
    GiveawayEntry,
)
from app.models.payment import Subscription, SubscriptionStatus
from app.models.user import AdminUser, User, UserRole


@pytest.fixture()
def admin_users_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    Base.metadata.create_all(bind=engine)
    with session_factory() as session:
        session.add(
            AdminUser(
                email="admin@example.com",
                password_hash=hash_password("StrongPassword123"),
                role=UserRole.ADMIN.value,
                is_active=True,
            )
        )
        session.add_all(
            [
                User(
                    email="existing-partner@example.com",
                    phone="+79990000001",
                    password_hash=hash_password("PartnerPassword123"),
                    role=UserRole.PARTNER.value,
                    is_active=True,
                ),
                User(
                    email="existing-client@example.com",
                    phone="+79990000002",
                    password_hash=hash_password("ClientPassword123"),
                    role=UserRole.CLIENT.value,
                    is_active=False,
                ),
                User(
                    email="manager@example.com",
                    phone="+79990000003",
                    password_hash=hash_password("AdminUserPassword123"),
                    role=UserRole.ADMIN.value,
                    is_active=True,
                ),
            ]
        )
        session.flush()
        city = City(name="Moscow", slug="moskva", is_active=True, sort_order=1)
        session.add(city)
        session.flush()
        partner_user = session.query(User).filter(User.email == "existing-partner@example.com").one()
        client_user = session.query(User).filter(User.email == "existing-client@example.com").one()
        session.add_all(
            [
                ClientProfile(
                    user_id=partner_user.id,
                    full_name="Анна Иванова",
                    contact_email="anna.real@example.com",
                    selected_city_id=city.id,
                    vk_user_id="1234567",
                    telegram_user_id="998877",
                    telegram_username="anna_bloom",
                    trial_subscription_used_at=datetime.now(timezone.utc),
                ),
                ClientProfile(
                    user_id=client_user.id,
                    contact_email="fallback@example.com",
                ),
            ]
        )
        session.flush()
        partner_profile = session.query(ClientProfile).filter(ClientProfile.vk_user_id == "1234567").one()
        session.add(
            Subscription(
                client_id=partner_profile.id,
                status=SubscriptionStatus.active.value,
                starts_at=datetime.now(timezone.utc) - timedelta(days=1),
                ends_at=datetime.now(timezone.utc) + timedelta(days=30),
                source="paid",
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
        engine.dispose()


@pytest.fixture()
def admin_token(admin_users_client: TestClient) -> str:
    response = admin_users_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "StrongPassword123"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "email": "new-user@example.com",
        "phone": "+79990000009",
        "password": "NewPassword123",
        "role": "partner",
        "is_active": True,
    }
    payload.update(overrides)
    return payload


def test_admin_users_returns_401_without_token(admin_users_client: TestClient) -> None:
    response = admin_users_client.get("/api/v1/admin/users")

    assert response.status_code == 401


def test_admin_users_post_creates_partner_user_with_email_password(
    admin_users_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_users_client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(admin_token),
        json={"email": "  Partner.New@Example.COM  ", "password": "PartnerNew123", "role": "partner"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 4
    assert data["email"] == "partner.new@example.com"
    assert data["phone"] is None
    assert data["role"] == "partner"
    assert data["is_active"] is True
    assert "password_hash" not in data


def test_admin_users_created_partner_can_login_via_user_login(
    admin_users_client: TestClient,
    admin_token: str,
) -> None:
    create_response = admin_users_client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(admin_token),
        json={"email": "login-partner@example.com", "password": "PartnerNew123", "role": "partner"},
    )
    assert create_response.status_code == 200

    login_response = admin_users_client.post(
        "/api/v1/auth/user-login",
        json={"login": "LOGIN-PARTNER@example.com", "password": "PartnerNew123"},
    )

    assert login_response.status_code == 200
    assert login_response.json()["user"]["role"] == "partner"


def test_admin_users_post_creates_client_user_with_phone_password(
    admin_users_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_users_client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(admin_token),
        json={"phone": "  +79990000999  ", "password": "ClientNew123", "role": "client"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] is None
    assert data["phone"] == "+79990000999"
    assert data["role"] == "client"


def test_admin_users_post_duplicate_email_returns_409(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(admin_token),
        json=_user_payload(email="existing-partner@example.com", phone="+79990001000"),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "User with this email or phone already exists"


def test_admin_users_post_duplicate_phone_returns_409(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(admin_token),
        json=_user_payload(email="unique@example.com", phone="+79990000001"),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "User with this email or phone already exists"


def test_admin_users_post_missing_email_and_phone_returns_400(
    admin_users_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_users_client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(admin_token),
        json={"email": " ", "phone": " ", "password": "NewPassword123", "role": "client"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email or phone is required"


def test_admin_users_post_invalid_role_returns_400(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(admin_token),
        json=_user_payload(role="owner"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid user role"


def test_admin_users_post_short_password_returns_400(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(admin_token),
        json=_user_payload(password="short"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Password must be at least 8 characters"


def test_admin_users_list_filters_by_role(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.get("/api/v1/admin/users?role=partner", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert [user["email"] for user in data] == ["existing-partner@example.com"]


def test_admin_users_list_filters_by_is_active(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.get("/api/v1/admin/users?is_active=false", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert [user["email"] for user in data] == ["existing-client@example.com"]


def test_admin_users_list_q_search_works(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.get("/api/v1/admin/users?q=000003", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert [user["email"] for user in data] == ["manager@example.com"]




def test_admin_users_list_returns_vk_and_display_fields(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.get("/api/v1/admin/users", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    partner = next(user for user in data if user["email"] == "existing-partner@example.com")
    assert partner["full_name"] == "Анна Иванова"
    assert partner["contact_email"] == "anna.real@example.com"
    assert partner["selected_city_name"] == "Moscow"
    assert partner["vk_user_id"] == "1234567"
    assert partner["vk_url"] == "https://vk.com/id1234567"
    assert partner["telegram_user_id"] == "998877"
    assert partner["telegram_username"] == "anna_bloom"
    assert partner["telegram_url"] == "https://t.me/anna_bloom"
    assert partner["trial_status"] == "Активировал"
    assert partner["paid_subscription_status"] == "Подключена"
    assert partner["active_subscription_type"] == "paid"
    assert partner["subscription_active_until"] is not None
    assert partner["display_name"] == "Анна Иванова"
    assert partner["is_synthetic_email"] is False


def test_admin_users_list_vk_url_is_null_without_vk_id(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.get("/api/v1/admin/users", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    client = next(user for user in data if user["email"] == "existing-client@example.com")
    assert client["vk_user_id"] is None
    assert client["vk_url"] is None
    assert client["telegram_user_id"] is None
    assert client["telegram_url"] is None
    assert client["trial_status"] == "Не активировал"
    assert client["paid_subscription_status"] == "Не подключена"
    assert client["active_subscription_type"] == "none"


def test_admin_users_list_display_name_fallbacks(admin_users_client: TestClient, admin_token: str) -> None:
    create_fallback_email = admin_users_client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(admin_token),
        json={"email": "vk_hash@vk.local", "password": "StrongPass123", "role": "client"},
    )
    assert create_fallback_email.status_code == 200
    created = create_fallback_email.json()

    response = admin_users_client.get("/api/v1/admin/users", headers=_auth_headers(admin_token))
    data = response.json()

    with_contact_email = next(user for user in data if user["email"] == "existing-client@example.com")
    assert with_contact_email["display_name"] == "fallback@example.com"

    with_user_email = next(user for user in data if user["email"] == "manager@example.com")
    assert with_user_email["display_name"] == "manager@example.com"

    synthetic = next(user for user in data if user["id"] == created["id"])
    assert synthetic["is_synthetic_email"] is True


def test_admin_users_list_q_search_includes_profile_city_vk(admin_users_client: TestClient, admin_token: str) -> None:
    for query in ("anna", "anna.real", "mos", "1234567"):
        response = admin_users_client.get(f"/api/v1/admin/users?q={query}", headers=_auth_headers(admin_token))
        assert response.status_code == 200
        emails = [user["email"] for user in response.json()]
        assert "existing-partner@example.com" in emails


def test_admin_users_list_response_has_no_sensitive_fields(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.get("/api/v1/admin/users", headers=_auth_headers(admin_token))
    assert response.status_code == 200
    for user in response.json():
        assert "password_hash" not in user
        assert "tokens" not in user
        assert "setup_tokens" not in user
        assert "temporary_password" not in user
def test_admin_users_patch_updates_email_phone_role_is_active(
    admin_users_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_users_client.patch(
        "/api/v1/admin/users/1",
        headers=_auth_headers(admin_token),
        json={
            "email": "  UPDATED@Example.COM ",
            "phone": " +79990001111 ",
            "role": "client",
            "is_active": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["email"] == "updated@example.com"
    assert data["phone"] == "+79990001111"
    assert data["role"] == "client"
    assert data["is_active"] is False


def test_admin_users_patch_updates_password_and_rotates_login(
    admin_users_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_users_client.patch(
        "/api/v1/admin/users/1",
        headers=_auth_headers(admin_token),
        json={"password": "UpdatedPassword123"},
    )
    assert response.status_code == 200

    old_login_response = admin_users_client.post(
        "/api/v1/auth/user-login",
        json={"login": "existing-partner@example.com", "password": "PartnerPassword123"},
    )
    new_login_response = admin_users_client.post(
        "/api/v1/auth/user-login",
        json={"login": "existing-partner@example.com", "password": "UpdatedPassword123"},
    )

    assert old_login_response.status_code == 401
    assert new_login_response.status_code == 200


def test_admin_users_patch_cannot_clear_both_email_and_phone(
    admin_users_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_users_client.patch(
        "/api/v1/admin/users/1",
        headers=_auth_headers(admin_token),
        json={"email": None, "phone": " "},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email or phone is required"


def test_admin_users_patch_missing_user_returns_404(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.patch(
        "/api/v1/admin/users/9999",
        headers=_auth_headers(admin_token),
        json={"email": "missing@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"



def test_admin_users_delete_requires_admin_token(admin_users_client: TestClient) -> None:
    response = admin_users_client.delete('/api/v1/admin/users/1')
    assert response.status_code == 401


def test_admin_users_delete_missing_user_returns_404(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.delete('/api/v1/admin/users/9999', headers=_auth_headers(admin_token))
    assert response.status_code == 404
    assert response.json()['detail'] == 'User not found'


def test_admin_users_delete_client_user_and_related_records(admin_users_client: TestClient, admin_token: str) -> None:
    create_user = admin_users_client.post(
        '/api/v1/admin/users', headers=_auth_headers(admin_token), json={'email': 'vk-client@example.com', 'password': 'ClientVk123', 'role': 'client'}
    )
    assert create_user.status_code == 200
    user_id = create_user.json()['id']

    response = admin_users_client.delete(f'/api/v1/admin/users/{user_id}', headers=_auth_headers(admin_token))
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['deleted_user_id'] == user_id
    assert 'deleted' in data
    assert data['deleted']['user'] == 1


def test_admin_users_delete_client_user_with_referral_identity_and_challenge_records(
    admin_users_client: TestClient, admin_token: str
) -> None:
    create_referrer = admin_users_client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(admin_token),
        json={"email": "referrer@example.com", "password": "ClientVk123", "role": "client"},
    )
    create_referred = admin_users_client.post(
        "/api/v1/admin/users",
        headers=_auth_headers(admin_token),
        json={"email": "referred@example.com", "password": "ClientVk123", "role": "client"},
    )
    assert create_referrer.status_code == 200
    assert create_referred.status_code == 200
    referrer_user_id = create_referrer.json()["id"]
    referred_user_id = create_referred.json()["id"]

    with next(app.dependency_overrides[get_db]()) as session:
        referrer = ClientProfile(user_id=referrer_user_id, contact_email="referrer-profile@example.com")
        referred = ClientProfile(user_id=referred_user_id, contact_email="referred-profile@example.com")
        session.add_all([referrer, referred])
        session.flush()
        referral = ClientReferral(
            referrer_client_id=referrer.id,
            referred_client_id=referred.id,
            referral_code="REF-DELETE",
            reward_entries_count=5,
        )
        session.add(referral)
        session.flush()
        referred.referred_by_referral_id = referral.id
        session.add_all(
            [
                GiveawayEntry(client_id=referrer.id, entries_count=1, source="referral", related_referral_id=referral.id),
                GiveawayEntry(client_id=referred.id, entries_count=1, source="signup"),
                ClientIdentityLink(client_profile_id=referrer.id, provider="vk", provider_user_id="delete-vk"),
                AccountLinkingChallenge(
                    id="delete-challenge",
                    current_client_profile_id=referrer.id,
                    target_client_profile_id=referred.id,
                    identifier_type="email",
                    identifier_hash="hash",
                    code_hash="code",
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                ),
                ClientPasswordSetupToken(
                    user_id=referrer_user_id,
                    token_hash="delete-token",
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                ),
            ]
        )
        session.commit()

    response = admin_users_client.delete(
        f"/api/v1/admin/users/{referrer_user_id}", headers=_auth_headers(admin_token)
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deleted"]["account_linking_challenges"] == 1
    assert data["deleted"]["client_identity_links"] == 1
    assert data["deleted"]["client_password_setup_tokens"] == 1
    assert data["deleted"]["client_referrals"] == 1
    assert data["deleted"]["giveaway_entries"] == 1
    assert data["deleted"]["user"] == 1

    with next(app.dependency_overrides[get_db]()) as session:
        assert session.get(User, referrer_user_id) is None
        assert session.query(ClientReferral).count() == 0
        assert session.query(GiveawayEntry).count() == 1
        assert session.query(AccountLinkingChallenge).count() == 0
        assert session.query(ClientIdentityLink).count() == 0
        assert session.query(ClientPasswordSetupToken).count() == 0


def test_admin_users_delete_cannot_delete_self(admin_users_client: TestClient, admin_token: str) -> None:
    create_user = admin_users_client.post(
        '/api/v1/admin/users', headers=_auth_headers(admin_token), json={'email': 'admin@example.com', 'password': 'AdminRole123', 'role': 'client'}
    )
    assert create_user.status_code == 200

    response = admin_users_client.delete(f"/api/v1/admin/users/{create_user.json()['id']}", headers=_auth_headers(admin_token))
    assert response.status_code == 400
    assert response.json()['detail'] == 'Нельзя удалить самого себя'


def test_admin_users_delete_cannot_delete_last_admin_role_user(admin_users_client: TestClient, admin_token: str) -> None:
    create_response = admin_users_client.post(
        '/api/v1/admin/users', headers=_auth_headers(admin_token), json={'email': 'extra-admin@example.com', 'password': 'AdminRole123', 'role': 'admin'}
    )
    assert create_response.status_code == 200
    extra_admin_id = create_response.json()['id']

    response = admin_users_client.delete(f'/api/v1/admin/users/{extra_admin_id}', headers=_auth_headers(admin_token))
    assert response.status_code == 200

    response = admin_users_client.delete('/api/v1/admin/users/3', headers=_auth_headers(admin_token))
    assert response.status_code == 400
    assert response.json()['detail'] == 'Нельзя удалить последнего администратора'


def test_admin_users_includes_provider_only_login_code_user_without_email_phone(admin_users_client: TestClient, admin_token: str) -> None:
    # The login-code resolver creates a normal client user with no email/phone.
    response = admin_users_client.post(
        "/api/v1/internal/login-code",
        json={
            "provider": "telegram",
            "provider_user_id": "tg-admin-visible",
            "username": "admin_visible",
            "first_name": "Login",
            "last_name": "Code",
            "source": "telegram_bot",
        },
        headers={"Authorization": f"Bearer {__import__('app.core.config').core.config.settings.BOT_SERVICE_TOKEN}"},
    )
    assert response.status_code == 200
    login_response = admin_users_client.post("/api/v1/auth/login-code", json={"code": response.json()["login_code"]})
    assert login_response.status_code == 200

    users_response = admin_users_client.get("/api/v1/admin/users", headers=_auth_headers(admin_token))

    assert users_response.status_code == 200
    user = next(item for item in users_response.json() if item["telegram_user_id"] == "tg-admin-visible")
    assert user["email"] is None
    assert user["phone"] is None
    assert user["role"] == "client"
    assert user["display_name"] == "Login Code"
    assert user["telegram_username"] == "admin_visible"


def test_admin_users_shows_vk_provider_user_id_and_username(admin_users_client: TestClient, admin_token: str) -> None:
    response = admin_users_client.post(
        "/api/v1/internal/login-code",
        json={
            "provider": "vk",
            "provider_user_id": "vk-admin-visible",
            "username": "vk_domain",
            "first_name": "VK",
            "last_name": "Code",
            "source": "vk_bot",
        },
        headers={"Authorization": f"Bearer {__import__('app.core.config').core.config.settings.BOT_SERVICE_TOKEN}"},
    )
    assert response.status_code == 200
    assert admin_users_client.post("/api/v1/auth/login-code", json={"code": response.json()["login_code"]}).status_code == 200

    users_response = admin_users_client.get("/api/v1/admin/users", headers=_auth_headers(admin_token))

    assert users_response.status_code == 200
    user = next(item for item in users_response.json() if item["vk_user_id"] == "vk-admin-visible")
    assert user["vk_username"] == "vk_domain"
    assert user["vk_url"] == "https://vk.com/vk_domain"
