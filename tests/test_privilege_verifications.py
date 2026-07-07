from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all SQLAlchemy models for test metadata
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.city import City
from app.models.client import ClientProfile
from app.models.partner import Partner, PartnerOffer
from app.models.payment import Subscription, SubscriptionStatus
from app.models.user import AdminUser, User, UserRole
from app.models.verification import PrivilegeVerificationSession, PrivilegeVerificationStatus


@pytest.fixture()
def verification_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    with session_factory() as session:
        admin = AdminUser(
            email="admin@example.com",
            password_hash=hash_password("AdminPassword123"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        client_user = User(
            email="client@example.com",
            phone="+79990000001",
            password_hash=hash_password("ClientPassword123"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        other_client_user = User(
            email="other-client@example.com",
            phone="+79990000002",
            password_hash=hash_password("OtherClientPassword123"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        partner_user = User(
            email="partner@example.com",
            phone="+79990000003",
            password_hash=hash_password("PartnerPassword123"),
            role=UserRole.PARTNER.value,
            is_active=True,
        )
        other_partner_user = User(
            email="other-partner@example.com",
            phone="+79990000004",
            password_hash=hash_password("OtherPartnerPassword123"),
            role=UserRole.PARTNER.value,
            is_active=True,
        )
        inactive_partner_user = User(
            email="inactive-partner@example.com",
            phone="+79990000005",
            password_hash=hash_password("InactivePartnerPassword123"),
            role=UserRole.PARTNER.value,
            is_active=True,
        )
        session.add_all([admin, client_user, other_client_user, partner_user, other_partner_user, inactive_partner_user])
        session.flush()

        city = City(name="Москва", slug="moscow", is_active=True, sort_order=10)
        other_city = City(name="Санкт-Петербург", slug="spb", is_active=True, sort_order=20)
        session.add_all([city, other_city])
        session.flush()

        client_profile = ClientProfile(
            user_id=client_user.id,
            full_name="Client One",
            source="seed",
            is_active=True,
        )
        other_client_profile = ClientProfile(
            user_id=other_client_user.id,
            full_name="Client Two",
            source="seed",
            is_active=True,
        )
        session.add_all([client_profile, other_client_profile])
        session.flush()

        partner = Partner(
            city_id=city.id,
            owner_user_id=partner_user.id,
            category_slug="beauty",
            name="Alpha Beauty",
            is_active=True,
            is_verified=True,
            sort_order=10,
        )
        other_partner = Partner(
            city_id=other_city.id,
            owner_user_id=other_partner_user.id,
            category_slug="fitness",
            name="Beta Yoga",
            is_active=True,
            is_verified=False,
            sort_order=20,
        )
        inactive_partner = Partner(
            city_id=city.id,
            owner_user_id=inactive_partner_user.id,
            name="Hidden Partner",
            is_active=False,
            is_verified=False,
            sort_order=30,
        )
        session.add_all([partner, other_partner, inactive_partner])
        session.flush()

        offer = PartnerOffer(
            partner_id=partner.id,
            title="Active Discount",
            base_price=2000,
            discount_percent=10,
            is_active=True,
            sort_order=10,
        )
        second_offer = PartnerOffer(partner_id=partner.id, title="Second Active Discount", is_active=True, sort_order=15)
        inactive_offer = PartnerOffer(partner_id=partner.id, title="Inactive Discount", is_active=False, sort_order=20)
        other_offer = PartnerOffer(partner_id=other_partner.id, title="Other Discount", is_active=True, sort_order=10)
        selected_offer = PartnerOffer(
            partner_id=partner.id,
            title="Selected Spa",
            base_price=5000,
            discount_percent=10,
            is_active=True,
            sort_order=25,
        )
        session.add_all([offer, second_offer, inactive_offer, other_offer, selected_offer])
        session.flush()

        now = datetime.now(timezone.utc)
        session.add(
            Subscription(
                client_id=client_profile.id,
                status=SubscriptionStatus.active.value,
                starts_at=now - timedelta(days=1),
                ends_at=now + timedelta(days=30),
            )
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            client.session_factory = session_factory  # type: ignore[attr-defined]
            yield client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_login(client: TestClient, login: str, password: str) -> str:
    response = client.post("/api/v1/auth/user-login", json={"login": login, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _admin_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPassword123"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _client_token(client: TestClient) -> str:
    return _user_login(client, "client@example.com", "ClientPassword123")


def _other_client_token(client: TestClient) -> str:
    return _user_login(client, "other-client@example.com", "OtherClientPassword123")


def _partner_token(client: TestClient) -> str:
    return _user_login(client, "partner@example.com", "PartnerPassword123")


def _other_partner_token(client: TestClient) -> str:
    return _user_login(client, "other-partner@example.com", "OtherPartnerPassword123")


def _partner_miniapp_token(client: TestClient, login: str = "partner@example.com", password: str = "PartnerPassword123") -> str:
    response = client.post("/api/v1/partner/login", json={"login": login, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _session(client: TestClient) -> Session:
    return client.session_factory()  # type: ignore[attr-defined,no-any-return]


def _create_verification(
    client: TestClient,
    *,
    client_id: int = 1,
    partner_id: int = 1,
    offer_id: int | None = None,
    status: str = PrivilegeVerificationStatus.active.value,
    expires_delta: timedelta = timedelta(minutes=15),
    token: str | None = None,
    code: str = "123456",
) -> int:
    now = datetime.now(timezone.utc)
    with _session(client) as session:
        verification = PrivilegeVerificationSession(
            client_id=client_id,
            partner_id=partner_id,
            offer_id=offer_id,
            code=code,
            token=token,
            status=status,
            source="test",
            expires_at=now + expires_delta,
            confirmed_at=now if status == PrivilegeVerificationStatus.confirmed.value else None,
            created_at=now,
        )
        session.add(verification)
        session.commit()
        return verification.id


def _assert_old_verify_qr_response(data: dict[str, object]) -> None:
    assert data["id"]
    assert data["session_id"] == data["id"]
    assert data["code"]
    assert data["display_code"] == data["code"]
    assert data["token"]
    assert data["qr_payload"] == f"bloomclub:privilege:{data['token']}"
    assert data["expires_at"]


def _assert_privilege_session_qr_response(data: dict[str, object]) -> None:
    assert data["session_id"]
    assert data["display_code"]
    assert data["token"]
    assert data["qr_payload"] == f"bloomclub:privilege:{data['token']}"
    assert data["expires_at"]


def test_client_post_verify_without_token_returns_401(verification_client: TestClient) -> None:
    response = verification_client.post("/api/v1/clients/partners/1/verify", json={})

    assert response.status_code == 401


def test_client_post_verify_with_partner_token_returns_403(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={},
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 403


def test_client_post_verify_without_body_keeps_offer_unset(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["offer_id"] is None
    assert data["offer_title"] is None
    assert data["code"]
    assert data["status"] == "active"
    assert data["expires_at"]

    list_response = verification_client.get(
        "/api/v1/clients/me/verifications",
        headers=_auth_headers(_client_token(verification_client)),
    )
    assert list_response.status_code == 200
    assert any(item["id"] == data["id"] for item in list_response.json())

def test_client_post_verify_with_empty_body_keeps_offer_unset(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["offer_id"] is None
    assert data["offer_title"] is None
    assert data["code"]
    assert data["status"] == "active"
    assert data["expires_at"]

    list_response = verification_client.get(
        "/api/v1/clients/me/verifications",
        headers=_auth_headers(_client_token(verification_client)),
    )
    assert list_response.status_code == 200
    assert any(item["id"] == data["id"] for item in list_response.json())


def test_client_post_verify_creates_active_session_for_active_partner(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"source": "web"},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == 1
    assert data["partner_id"] == 1
    assert data["partner_name"] == "Alpha Beauty"
    assert data["offer_id"] is None
    assert data["offer_title"] is None
    assert data["status"] == "active"
    assert data["source"] == "web"
    assert data["subscription_required"] is False
    assert len(data["code"]) == 6
    assert data["code"].isdigit()
    assert 0 < data["ttl_seconds"] <= 900
    created_at = datetime.fromisoformat(data["created_at"])
    expires_at = datetime.fromisoformat(data["expires_at"])
    assert abs((expires_at - created_at).total_seconds() - 900) < 1
    assert 850 <= data["ttl_seconds"] <= 900


def test_client_post_verify_with_inactive_or_missing_partner_returns_404(verification_client: TestClient) -> None:
    token = _client_token(verification_client)

    inactive_response = verification_client.post(
        "/api/v1/clients/partners/3/verify",
        json={},
        headers=_auth_headers(token),
    )
    missing_response = verification_client.post(
        "/api/v1/clients/partners/999/verify",
        json={},
        headers=_auth_headers(token),
    )

    assert inactive_response.status_code == 404
    assert inactive_response.json()["detail"] == "Partner not found"
    assert missing_response.status_code == 404


def test_confirmed_session_in_current_month_does_not_block_new_qr_session(verification_client: TestClient) -> None:
    existing_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        offer_id=1,
        status=PrivilegeVerificationStatus.confirmed.value,
    )

    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 1},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    _assert_old_verify_qr_response(data)
    assert data["id"] != existing_id


def test_expired_session_does_not_block_new_qr_session(verification_client: TestClient) -> None:
    existing_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        offer_id=1,
        status=PrivilegeVerificationStatus.expired.value,
        expires_delta=timedelta(minutes=-1),
    )

    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 1},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    _assert_old_verify_qr_response(data)
    assert data["id"] != existing_id


def test_pending_session_does_not_block_new_qr_session(verification_client: TestClient) -> None:
    existing_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        offer_id=1,
        status=PrivilegeVerificationStatus.pending.value,
    )

    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 1},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    _assert_old_verify_qr_response(data)
    assert data["id"] != existing_id


def test_active_session_without_confirmed_at_does_not_block_new_qr_session(verification_client: TestClient) -> None:
    existing_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        offer_id=1,
        status=PrivilegeVerificationStatus.active.value,
    )

    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 1},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    _assert_old_verify_qr_response(data)
    assert data["id"] != existing_id


def test_cancelled_session_does_not_block_new_qr_session(verification_client: TestClient) -> None:
    existing_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        offer_id=1,
        status=PrivilegeVerificationStatus.cancelled.value,
    )

    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 1},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    _assert_old_verify_qr_response(data)
    assert data["id"] != existing_id


def test_multiple_qr_sessions_can_be_created_for_same_client_partner_and_offer(
    verification_client: TestClient,
) -> None:
    token = _auth_headers(_client_token(verification_client))
    responses = [
        verification_client.post(
            "/api/v1/clients/partners/1/verify",
            json={"offer_id": 1},
            headers=token,
        )
        for _ in range(3)
    ]

    assert [response.status_code for response in responses] == [200, 200, 200]
    payloads = [response.json() for response in responses]
    for data in payloads:
        _assert_old_verify_qr_response(data)
        assert data["partner_id"] == 1
        assert data["offer_id"] == 1
    assert len({data["id"] for data in payloads}) == 3
    assert len({data["token"] for data in payloads}) == 3


def test_old_verify_endpoint_allows_repeated_creation(verification_client: TestClient) -> None:
    token = _auth_headers(_client_token(verification_client))
    first = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 1},
        headers=token,
    )
    second = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 2},
        headers=token,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    first_data = first.json()
    second_data = second.json()
    _assert_old_verify_qr_response(first_data)
    _assert_old_verify_qr_response(second_data)
    assert second_data["id"] != first_data["id"]
    assert second_data["token"] != first_data["token"]


def test_client_post_verify_with_active_offer_creates_session_with_offer_info(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 1},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["offer_id"] == 1
    assert data["offer_title"] == "Active Discount"
    assert data["code"]
    assert data["status"] == "active"
    assert data["expires_at"]

    list_response = verification_client.get(
        "/api/v1/clients/me/verifications",
        headers=_auth_headers(_client_token(verification_client)),
    )
    assert list_response.status_code == 200
    assert any(item["id"] == data["id"] for item in list_response.json())


def test_client_post_verify_with_inactive_offer_returns_404(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 3},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Offer not found"


def test_client_post_verify_with_offer_from_another_partner_returns_404(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 4},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Offer not found"


def test_client_post_verify_without_active_subscription_returns_400(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 1},
        headers=_auth_headers(_other_client_token(verification_client)),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Active subscription required"


def test_client_post_verify_creates_new_active_session_instead_of_reusing_existing_one(
    verification_client: TestClient,
) -> None:
    token = _auth_headers(_client_token(verification_client))
    first = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 1},
        headers=token,
    )
    second = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 1},
        headers=token,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] != first.json()["id"]
    assert second.json()["code"] != first.json()["code"] or second.json()["token"] != first.json()["token"]


def test_client_get_own_verifications_returns_only_own_sessions(verification_client: TestClient) -> None:
    own_id = _create_verification(verification_client, client_id=1, partner_id=1)
    _create_verification(verification_client, client_id=2, partner_id=1)

    response = verification_client.get(
        "/api/v1/clients/me/verifications",
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data] == [own_id]


def test_client_get_own_verifications_supports_status_filter(verification_client: TestClient) -> None:
    _create_verification(verification_client, client_id=1, partner_id=1, status="active")
    confirmed_id = _create_verification(verification_client, client_id=1, partner_id=1, status="confirmed")

    response = verification_client.get(
        "/api/v1/clients/me/verifications?status=confirmed",
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [confirmed_id]


def test_client_verification_status_filters_normalize_expired_and_support_all_used(
    verification_client: TestClient,
) -> None:
    active_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        status=PrivilegeVerificationStatus.active.value,
        expires_delta=timedelta(minutes=1),
    )
    expired_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        status=PrivilegeVerificationStatus.active.value,
        expires_delta=timedelta(seconds=-1),
    )
    confirmed_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        status=PrivilegeVerificationStatus.confirmed.value,
    )
    used_id = _create_verification(verification_client, client_id=1, partner_id=1, status="used")

    headers = _auth_headers(_client_token(verification_client))

    active_response = verification_client.get("/api/v1/clients/me/verifications?status=active", headers=headers)
    expired_response = verification_client.get("/api/v1/clients/me/verifications?status=expired", headers=headers)
    confirmed_response = verification_client.get("/api/v1/clients/me/verifications?status=confirmed", headers=headers)
    used_response = verification_client.get("/api/v1/clients/me/verifications?status=used", headers=headers)
    all_response = verification_client.get("/api/v1/clients/me/verifications?status=all", headers=headers)

    assert active_response.status_code == 200
    assert expired_response.status_code == 200
    assert confirmed_response.status_code == 200
    assert used_response.status_code == 200
    assert all_response.status_code == 200
    assert [item["id"] for item in active_response.json()] == [active_id]
    assert [item["id"] for item in expired_response.json()] == [expired_id]
    assert [item["id"] for item in confirmed_response.json()] == [used_id, confirmed_id]
    assert [item["id"] for item in used_response.json()] == [used_id, confirmed_id]
    assert [item["id"] for item in all_response.json()] == [used_id, confirmed_id, expired_id, active_id]
    assert all(item["status"] != "active" for item in confirmed_response.json())

    with _session(verification_client) as session:
        stored = session.get(PrivilegeVerificationSession, expired_id)
        assert stored is not None
        assert stored.status == PrivilegeVerificationStatus.expired.value



def test_client_get_confirmed_verification_returns_saved_price_snapshot(verification_client: TestClient) -> None:
    verification_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        offer_id=1,
        status=PrivilegeVerificationStatus.confirmed.value,
    )
    with _session(verification_client) as session:
        stored = session.get(PrivilegeVerificationSession, verification_id)
        assert stored is not None
        stored.saving_base_price = 3000
        stored.saving_final_price = 2100
        stored.saving_discount_percent = 30
        stored.saving_amount = 900
        stored.saving_partner_name = "Snapshot Partner"
        stored.saving_offer_title = "Snapshot Privilege"
        session.commit()

    response = verification_client.get(
        "/api/v1/clients/me/verifications?status=confirmed",
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["id"] == verification_id
    assert item["partner_name"] == "Snapshot Partner"
    assert item["offer_title"] == "Snapshot Privilege"
    assert item["regular_price"] == "3000.00"
    assert item["club_price"] == "2100.00"
    assert item["base_price"] == "3000.00"
    assert item["final_price"] == "2100.00"
    assert item["discount_percent"] == "30.00"
    assert item["saving_amount"] == "900.00"


def test_client_get_active_verification_with_offer_returns_price_preview(verification_client: TestClient) -> None:
    verification_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        offer_id=5,
        status=PrivilegeVerificationStatus.active.value,
    )

    response = verification_client.get(
        "/api/v1/clients/me/verifications?status=active",
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["id"] == verification_id
    assert item["partner_name"] == "Alpha Beauty"
    assert item["offer_title"] == "Selected Spa"
    assert item["regular_price"] == "5000.00"
    assert item["club_price"] == "4500.00"
    assert item["base_price"] == "5000.00"
    assert item["final_price"] == "4500.00"
    assert item["discount_percent"] == "10.00"
    assert item["saving_amount"] == "500.00"


def test_client_get_no_offer_verification_does_not_return_random_partner_offer_prices(
    verification_client: TestClient,
) -> None:
    verification_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        offer_id=None,
        status=PrivilegeVerificationStatus.active.value,
    )

    response = verification_client.get(
        "/api/v1/clients/me/verifications?status=active",
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["id"] == verification_id
    assert item["partner_name"] == "Alpha Beauty"
    assert item["offer_id"] is None
    assert item["offer_title"] is None
    assert item["regular_price"] is None
    assert item["club_price"] is None
    assert item["base_price"] is None
    assert item["final_price"] is None
    assert item["discount_percent"] is None
    assert item["saving_amount"] == "0.00"

def test_partner_get_own_verifications_returns_only_own_partner_sessions(verification_client: TestClient) -> None:
    own_id = _create_verification(verification_client, client_id=1, partner_id=1)
    _create_verification(verification_client, client_id=1, partner_id=2)

    response = verification_client.get(
        "/api/v1/partners/me/verifications",
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data] == [own_id]
    assert data[0]["client_name"] == "Client One"


def test_partner_confirm_own_active_session_succeeds_and_sets_confirmed_at(verification_client: TestClient) -> None:
    verification_id = _create_verification(verification_client, client_id=1, partner_id=1)

    response = verification_client.post(
        f"/api/v1/partners/me/verifications/{verification_id}/confirm",
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == verification_id
    assert data["status"] == "confirmed"
    assert data["confirmed_at"] is not None
    with _session(verification_client) as session:
        stored = session.get(PrivilegeVerificationSession, verification_id)
        assert stored is not None
        assert stored.status == "confirmed"
        assert stored.confirmed_at is not None


def test_partner_confirm_another_partner_session_returns_404(verification_client: TestClient) -> None:
    verification_id = _create_verification(verification_client, client_id=1, partner_id=2)

    response = verification_client.post(
        f"/api/v1/partners/me/verifications/{verification_id}/confirm",
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Verification session not found"


def test_partner_confirm_expired_active_session_sets_expired_and_returns_400(verification_client: TestClient) -> None:
    verification_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        expires_delta=timedelta(minutes=-1),
    )

    response = verification_client.post(
        f"/api/v1/partners/me/verifications/{verification_id}/confirm",
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Verification session expired"
    with _session(verification_client) as session:
        stored = session.get(PrivilegeVerificationSession, verification_id)
        assert stored is not None
        assert stored.status == "expired"


def test_partner_confirm_non_active_session_returns_400(verification_client: TestClient) -> None:
    verification_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        status=PrivilegeVerificationStatus.expired.value,
    )

    response = verification_client.post(
        f"/api/v1/partners/me/verifications/{verification_id}/confirm",
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Verification session is not active"


def test_partner_confirm_confirmed_or_used_session_returns_400(verification_client: TestClient) -> None:
    confirmed_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        status=PrivilegeVerificationStatus.confirmed.value,
    )
    used_id = _create_verification(verification_client, client_id=1, partner_id=1, status="used")

    confirmed_response = verification_client.post(
        f"/api/v1/partners/me/verifications/{confirmed_id}/confirm",
        headers=_auth_headers(_partner_token(verification_client)),
    )
    used_response = verification_client.post(
        f"/api/v1/partners/me/verifications/{used_id}/confirm",
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert confirmed_response.status_code == 400
    assert confirmed_response.json()["detail"] == "Verification session is already confirmed"
    assert used_response.status_code == 400
    assert used_response.json()["detail"] == "Verification session is already confirmed"


def test_admin_get_verifications_returns_all_sessions(verification_client: TestClient) -> None:
    first_id = _create_verification(verification_client, client_id=1, partner_id=1, offer_id=1)
    second_id = _create_verification(verification_client, client_id=2, partner_id=2)

    response = verification_client.get(
        "/api/v1/admin/verifications",
        headers=_auth_headers(_admin_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data] == [second_id, first_id]
    assert data[1]["partner_name"] == "Alpha Beauty"
    assert data[1]["city_name"] == "Москва"
    assert data[1]["offer_title"] == "Active Discount"


def test_admin_get_verifications_filters_by_partner_client_and_status(verification_client: TestClient) -> None:
    matching_id = _create_verification(
        verification_client,
        client_id=1,
        partner_id=1,
        status=PrivilegeVerificationStatus.confirmed.value,
    )
    _create_verification(verification_client, client_id=2, partner_id=1, status="confirmed")
    _create_verification(verification_client, client_id=1, partner_id=2, status="confirmed")
    _create_verification(verification_client, client_id=1, partner_id=1, status="active")

    response = verification_client.get(
        "/api/v1/admin/verifications?partner_id=1&client_id=1&status=confirmed",
        headers=_auth_headers(_admin_token(verification_client)),
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [matching_id]


def test_tokens_with_wrong_roles_are_rejected_on_relevant_endpoints(verification_client: TestClient) -> None:
    client_token = _client_token(verification_client)
    partner_token = _partner_token(verification_client)
    admin_token = _admin_token(verification_client)

    partner_response = verification_client.get(
        "/api/v1/partners/me/verifications",
        headers=_auth_headers(client_token),
    )
    admin_response = verification_client.get(
        "/api/v1/admin/verifications",
        headers=_auth_headers(client_token),
    )
    client_response = verification_client.get(
        "/api/v1/clients/me/verifications",
        headers=_auth_headers(partner_token),
    )
    admin_on_client_response = verification_client.get(
        "/api/v1/clients/me/verifications",
        headers=_auth_headers(admin_token),
    )
    client_on_admin_response = verification_client.get(
        "/api/v1/admin/verifications",
        headers=_auth_headers(partner_token),
    )

    assert partner_response.status_code == 403
    assert admin_response.status_code == 401
    assert client_response.status_code == 403
    assert admin_on_client_response.status_code == 401
    assert client_on_admin_response.status_code == 401


def test_other_client_cannot_see_first_client_verifications(verification_client: TestClient) -> None:
    _create_verification(verification_client, client_id=1, partner_id=1)

    response = verification_client.get(
        "/api/v1/clients/me/verifications",
        headers=_auth_headers(_other_client_token(verification_client)),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_other_partner_can_confirm_only_own_session(verification_client: TestClient) -> None:
    own_id = _create_verification(verification_client, client_id=1, partner_id=2)

    response = verification_client.post(
        f"/api/v1/partners/me/verifications/{own_id}/confirm",
        headers=_auth_headers(_other_partner_token(verification_client)),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


def test_privilege_session_endpoint_active_subscription_creates_qr_session(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/privileges/sessions",
        json={"partner_id": 1, "privilege_id": 1},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["session_id"]
    assert data["partner"] == {"id": 1, "name": "Alpha Beauty"}
    assert data["privilege"] == {"id": 1, "title": "Active Discount"}
    assert data["status"] == "pending"
    assert data["display_code"]
    assert data["token"]
    assert data["token"] != "1"
    assert data["qr_payload"] == f"bloomclub:privilege:{data['token']}"
    assert data["qr_payload"].startswith("bloomclub:privilege:")
    assert data["expires_at"]

    with _session(verification_client) as session:
        created = session.get(PrivilegeVerificationSession, data["session_id"])
        assert created is not None
        assert created.token == data["token"]
        assert created.client_id == 1
        assert created.partner_id == 1
        assert created.offer_id == 1
        assert created.status == PrivilegeVerificationStatus.pending.value
        assert created.expires_at is not None


def test_privilege_session_endpoint_without_active_subscription_returns_403(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/privileges/sessions",
        json={"partner_id": 1, "privilege_id": 1},
        headers=_auth_headers(_other_client_token(verification_client)),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Active subscription required"

    with _session(verification_client) as session:
        other_client_sessions = session.execute(
            select(PrivilegeVerificationSession).where(PrivilegeVerificationSession.client_id == 2)
        ).scalars().all()
        assert other_client_sessions == []


def test_privilege_session_qr_payload_does_not_include_personal_data(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/privileges/sessions",
        json={"partner_id": 1},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 201
    data = response.json()
    qr_payload = data["qr_payload"]
    assert qr_payload.startswith("bloomclub:privilege:")
    assert "client@example.com" not in qr_payload
    assert "+79990000001" not in qr_payload
    assert data["token"] != str(data["session_id"])
    assert data["token"] != "1"


def test_privilege_session_endpoint_allows_repeated_creation(verification_client: TestClient) -> None:
    token = _auth_headers(_client_token(verification_client))
    first = verification_client.post(
        "/api/v1/privileges/sessions",
        json={"partner_id": 1, "privilege_id": 1},
        headers=token,
    )
    second = verification_client.post(
        "/api/v1/privileges/sessions",
        json={"partner_id": 1, "privilege_id": 1},
        headers=token,
    )

    assert first.status_code == 201
    assert second.status_code == 201
    first_data = first.json()
    second_data = second.json()
    _assert_privilege_session_qr_response(first_data)
    _assert_privilege_session_qr_response(second_data)
    assert first_data["session_id"] != second_data["session_id"]
    assert first_data["token"] != second_data["token"]
    assert first_data["qr_payload"] != second_data["qr_payload"]


def test_privilege_session_endpoint_returns_controlled_errors_for_missing_partner_or_offer(
    verification_client: TestClient,
) -> None:
    token = _auth_headers(_client_token(verification_client))
    missing_partner = verification_client.post(
        "/api/v1/privileges/sessions",
        json={"partner_id": 999, "privilege_id": 1},
        headers=token,
    )
    missing_offer = verification_client.post(
        "/api/v1/privileges/sessions",
        json={"partner_id": 1, "privilege_id": 999},
        headers=token,
    )

    assert missing_partner.status_code == 404
    assert missing_partner.json()["detail"] == "Partner not found"
    assert missing_offer.status_code == 404
    assert missing_offer.json()["detail"] == "Offer not found"


def test_old_verify_response_remains_backward_compatible_and_includes_qr_fields(
    verification_client: TestClient,
) -> None:
    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 1},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"]
    assert data["session_id"] == data["id"]
    assert data["code"]
    assert data["display_code"] == data["code"]
    assert data["status"] == "active"
    assert data["token"]
    assert data["token"] != str(data["id"])
    assert data["token"] != str(data["client_id"])
    assert data["qr_payload"] == f"bloomclub:privilege:{data['token']}"
    assert data["expires_at"]


def test_partner_login_valid_credentials_returns_partner_access_token(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/partner/login",
        json={"login": "partner@example.com", "password": "PartnerPassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["partner"] == {"id": 1, "name": "Alpha Beauty", "display_name": "Alpha Beauty", "is_active": True}
    assert data["stats"] == {"confirmed_today": 0, "confirmed_month": 0, "savings_month": "0.00"}
    assert "password" not in str(data).lower()
    assert "password_hash" not in str(data).lower()


def test_partner_login_invalid_password_returns_controlled_401(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/partner/login",
        json={"login": "partner@example.com", "password": "WrongPassword123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid partner credentials"


def test_partner_login_non_partner_user_returns_403(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/partner/login",
        json={"login": "client@example.com", "password": "ClientPassword123"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Partner access required"


def test_partner_login_inactive_partner_returns_403(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/partner/login",
        json={"login": "inactive-partner@example.com", "password": "InactivePartnerPassword123"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Partner is inactive"


def test_partner_login_token_can_call_partner_me(verification_client: TestClient) -> None:
    response = verification_client.get(
        "/api/v1/partner/me",
        headers=_auth_headers(_partner_miniapp_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_partner"] is True
    assert data["partner"]["id"] == 1


def test_partner_login_token_can_scan_and_confirm(verification_client: TestClient) -> None:
    token = _partner_miniapp_token(verification_client)
    verification_id = _create_verification(
        verification_client,
        offer_id=1,
        status=PrivilegeVerificationStatus.pending.value,
        token="miniapp-token",
    )

    scan = verification_client.post(
        "/api/v1/partner/privileges/scan",
        json={"qr_payload": "bloomclub:privilege:miniapp-token"},
        headers=_auth_headers(token),
    )
    assert scan.status_code == 200
    assert scan.json()["session_id"] == verification_id

    confirm = verification_client.post(
        "/api/v1/partner/privileges/confirm",
        json={"session_id": verification_id, "saving_amount": 125},
        headers=_auth_headers(token),
    )
    assert confirm.status_code == 200
    assert confirm.json()["saving_amount"] == "200.00"


def test_partner_scan_and_confirm_without_token_fail(verification_client: TestClient) -> None:
    scan = verification_client.post("/api/v1/partner/privileges/scan", json={"qr_payload": "bloomclub:privilege:nope"})
    assert scan.status_code == 401

    confirm = verification_client.post("/api/v1/partner/privileges/confirm", json={"session_id": 1})
    assert confirm.status_code == 401


def test_partner_access_token_cannot_confirm_another_partner_qr(verification_client: TestClient) -> None:
    verification_id = _create_verification(verification_client, partner_id=2, token="another-partner-qr")

    response = verification_client.post(
        "/api/v1/partner/privileges/confirm",
        json={"session_id": verification_id},
        headers=_auth_headers(_partner_miniapp_token(verification_client)),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "QR belongs to another partner"


def test_partner_singular_me_non_partner_returns_false(verification_client: TestClient) -> None:
    response = verification_client.get(
        "/api/v1/partner/me",
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    assert response.json() == {"is_partner": False, "partner": None, "stats": None}


def test_partner_singular_me_partner_returns_partner_and_stats(verification_client: TestClient) -> None:
    response = verification_client.get(
        "/api/v1/partner/me",
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_partner"] is True
    assert data["partner"] == {"id": 1, "name": "Alpha Beauty", "display_name": "Alpha Beauty", "is_active": True}
    assert data["stats"] == {"confirmed_today": 0, "confirmed_month": 0, "savings_month": "0.00"}


def test_non_partner_cannot_scan_or_confirm_singular_partner_qr(verification_client: TestClient) -> None:
    response = verification_client.post(
        "/api/v1/partner/privileges/scan",
        json={"qr_payload": "bloomclub:privilege:nope"},
        headers=_auth_headers(_client_token(verification_client)),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Partner access required"

    response = verification_client.post(
        "/api/v1/partner/privileges/confirm",
        json={"session_id": 1},
        headers=_auth_headers(_client_token(verification_client)),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Partner access required"


def test_partner_can_scan_own_valid_qr_by_payload_and_code(verification_client: TestClient) -> None:
    verification_id = _create_verification(
        verification_client,
        offer_id=1,
        status=PrivilegeVerificationStatus.pending.value,
        token="scan-token",
        code="771772",
    )

    by_payload = verification_client.post(
        "/api/v1/partner/privileges/scan",
        json={"qr_payload": "bloomclub:privilege:scan-token"},
        headers=_auth_headers(_partner_token(verification_client)),
    )
    assert by_payload.status_code == 200
    data = by_payload.json()
    assert data["session_id"] == verification_id
    assert data["status"] == PrivilegeVerificationStatus.pending.value
    assert data["can_confirm"] is True
    assert data["client"] == {"display_name": "Client One", "subscription_active": True}
    assert data["partner"] == {"id": 1, "name": "Alpha Beauty"}
    assert data["privilege"] == {"id": 1, "title": "Active Discount"}
    assert data["estimated_saving_amount"] == "200.00"
    assert data["regular_price"] == "2000.00"
    assert data["club_price"] == "1800.00"
    assert data["expires_at"]

    by_code = verification_client.post(
        "/api/v1/partner/privileges/scan",
        json={"code": "771772"},
        headers=_auth_headers(_partner_token(verification_client)),
    )
    assert by_code.status_code == 200
    assert by_code.json()["session_id"] == verification_id


def test_partner_scan_controlled_errors(verification_client: TestClient) -> None:
    not_found = verification_client.post(
        "/api/v1/partner/privileges/scan",
        json={"qr_payload": "bloomclub:privilege:missing"},
        headers=_auth_headers(_partner_token(verification_client)),
    )
    assert not_found.status_code == 404
    assert not_found.json()["detail"] == "QR not found"

    expired_id = _create_verification(
        verification_client,
        token="expired-token",
        expires_delta=timedelta(minutes=-1),
    )
    expired = verification_client.post(
        "/api/v1/partner/privileges/scan",
        json={"qr_payload": "bloomclub:privilege:expired-token"},
        headers=_auth_headers(_partner_token(verification_client)),
    )
    assert expired.status_code == 400
    assert expired.json()["detail"] == "QR expired"
    with _session(verification_client) as session:
        assert session.get(PrivilegeVerificationSession, expired_id).status == PrivilegeVerificationStatus.expired.value

    confirmed = _create_verification(
        verification_client,
        token="confirmed-token",
        status=PrivilegeVerificationStatus.confirmed.value,
    )
    response = verification_client.post(
        "/api/v1/partner/privileges/scan",
        json={"qr_payload": "bloomclub:privilege:confirmed-token"},
        headers=_auth_headers(_partner_token(verification_client)),
    )
    assert confirmed
    assert response.status_code == 400
    assert response.json()["detail"] == "QR already confirmed"

    _create_verification(verification_client, partner_id=2, token="other-partner-token")
    another_partner = verification_client.post(
        "/api/v1/partner/privileges/scan",
        json={"qr_payload": "bloomclub:privilege:other-partner-token"},
        headers=_auth_headers(_partner_token(verification_client)),
    )
    assert another_partner.status_code == 403
    assert another_partner.json()["detail"] == "QR belongs to another partner"


def test_partner_can_confirm_own_qr_and_stats_update(verification_client: TestClient) -> None:
    verification_id = _create_verification(
        verification_client,
        offer_id=1,
        status=PrivilegeVerificationStatus.pending.value,
        token="confirm-token",
    )

    response = verification_client.post(
        "/api/v1/partner/privileges/confirm",
        json={"session_id": verification_id, "saving_amount": 500, "comment": "ok"},
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == PrivilegeVerificationStatus.confirmed.value
    assert data["confirmed_at"] is not None
    assert data["saving_amount"] == "200.00"
    with _session(verification_client) as session:
        stored = session.get(PrivilegeVerificationSession, verification_id)
        assert stored.status == PrivilegeVerificationStatus.confirmed.value
        assert stored.confirmed_at is not None
        assert stored.confirmed_by_partner_id == 1
        assert stored.saving_amount == 200
        assert stored.saving_base_price == 2000
        assert stored.saving_final_price == 1800
        assert stored.saving_discount_percent == 10
        assert stored.saving_used_at is not None

    stats = verification_client.get(
        "/api/v1/partner/me",
        headers=_auth_headers(_partner_token(verification_client)),
    )
    assert stats.status_code == 200
    assert stats.json()["stats"] == {"confirmed_today": 1, "confirmed_month": 1, "savings_month": "200.00"}


def test_partner_confirm_missing_offer_prices_uses_zero_saving(verification_client: TestClient) -> None:
    verification_id = _create_verification(
        verification_client,
        offer_id=2,
        status=PrivilegeVerificationStatus.pending.value,
        token="missing-price-token",
    )

    response = verification_client.post(
        "/api/v1/partner/privileges/confirm",
        json={"session_id": verification_id, "saving_amount": 777},
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 200
    assert response.json()["saving_amount"] == "0.00"
    with _session(verification_client) as session:
        stored = session.get(PrivilegeVerificationSession, verification_id)
        assert stored.saving_amount == 0
        assert stored.saving_base_price is None
        assert stored.saving_final_price is None
        assert stored.saving_discount_percent is None


def test_partner_confirm_negative_offer_saving_is_clamped_to_zero(verification_client: TestClient) -> None:
    with _session(verification_client) as session:
        offer = session.get(PartnerOffer, 1)
        offer.discount_percent = -10
        session.commit()
    verification_id = _create_verification(
        verification_client,
        offer_id=1,
        status=PrivilegeVerificationStatus.pending.value,
        token="negative-saving-token",
    )

    response = verification_client.post(
        "/api/v1/partner/privileges/confirm",
        json={"session_id": verification_id},
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 200
    assert response.json()["saving_amount"] == "0.00"
    with _session(verification_client) as session:
        stored = session.get(PrivilegeVerificationSession, verification_id)
        assert stored.saving_amount == 0
        assert stored.saving_final_price == 2000


def test_client_savings_total_increases_by_calculated_offer_saving(verification_client: TestClient) -> None:
    verification_id = _create_verification(
        verification_client,
        offer_id=1,
        status=PrivilegeVerificationStatus.pending.value,
        token="client-saving-token",
    )
    confirm = verification_client.post(
        "/api/v1/partner/privileges/confirm",
        json={"session_id": verification_id, "saving_amount": 1},
        headers=_auth_headers(_partner_token(verification_client)),
    )
    assert confirm.status_code == 200

    response = verification_client.get(
        "/api/v1/clients/me/savings",
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_saving_amount"] == "200.00"
    assert data["items"][0]["saving_amount"] == "200.00"
    assert data["items"][0]["base_price"] == "2000.00"
    assert data["items"][0]["final_price"] == "1800.00"


def test_partner_confirm_controlled_errors(verification_client: TestClient) -> None:
    confirmed_id = _create_verification(
        verification_client,
        status=PrivilegeVerificationStatus.confirmed.value,
        token="already-confirmed",
    )
    response = verification_client.post(
        "/api/v1/partner/privileges/confirm",
        json={"session_id": confirmed_id},
        headers=_auth_headers(_partner_token(verification_client)),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "QR already confirmed"

    other_partner_id = _create_verification(verification_client, partner_id=2, token="confirm-other-partner")
    response = verification_client.post(
        "/api/v1/partner/privileges/confirm",
        json={"session_id": other_partner_id},
        headers=_auth_headers(_partner_token(verification_client)),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "QR belongs to another partner"

    expired_id = _create_verification(verification_client, token="confirm-expired", expires_delta=timedelta(minutes=-1))
    response = verification_client.post(
        "/api/v1/partner/privileges/confirm",
        json={"session_id": expired_id},
        headers=_auth_headers(_partner_token(verification_client)),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "QR expired"


def test_partner_confirm_requires_active_client_subscription(verification_client: TestClient) -> None:
    verification_id = _create_verification(
        verification_client,
        client_id=2,
        token="inactive-subscription-client",
    )

    response = verification_client.post(
        "/api/v1/partner/privileges/confirm",
        json={"session_id": verification_id},
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Active subscription required"


def test_client_post_verify_with_selected_offer_id_stores_exact_offer_not_first(
    verification_client: TestClient,
) -> None:
    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"offer_id": 5},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["offer_id"] == 5
    assert data["offer_title"] == "Selected Spa"
    _assert_old_verify_qr_response(data)
    with _session(verification_client) as session:
        stored = session.get(PrivilegeVerificationSession, data["id"])
        assert stored.offer_id == 5


def test_client_post_verify_with_selected_privilege_id_stores_exact_offer_not_first(
    verification_client: TestClient,
) -> None:
    response = verification_client.post(
        "/api/v1/clients/partners/1/verify",
        json={"privilege_id": 5},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["offer_id"] == 5
    assert data["offer_title"] == "Selected Spa"
    with _session(verification_client) as session:
        stored = session.get(PrivilegeVerificationSession, data["id"])
        assert stored.offer_id == 5


def test_privilege_session_with_selected_offer_id_stores_exact_offer_id(
    verification_client: TestClient,
) -> None:
    response = verification_client.post(
        "/api/v1/privileges/sessions",
        json={"partner_id": 1, "offer_id": 5},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["privilege"] == {"id": 5, "title": "Selected Spa"}
    _assert_privilege_session_qr_response(data)
    with _session(verification_client) as session:
        stored = session.get(PrivilegeVerificationSession, data["session_id"])
        assert stored.offer_id == 5


def test_privilege_session_rejects_offer_from_another_partner_and_inactive_offer(
    verification_client: TestClient,
) -> None:
    other_partner_offer = verification_client.post(
        "/api/v1/privileges/sessions",
        json={"partner_id": 1, "offer_id": 4},
        headers=_auth_headers(_client_token(verification_client)),
    )
    inactive_offer = verification_client.post(
        "/api/v1/privileges/sessions",
        json={"partner_id": 1, "offer_id": 3},
        headers=_auth_headers(_client_token(verification_client)),
    )

    assert other_partner_offer.status_code == 404
    assert other_partner_offer.json()["detail"] == "Offer not found"
    assert inactive_offer.status_code == 404
    assert inactive_offer.json()["detail"] == "Offer not found"


def test_partner_scan_uses_selected_session_offer_prices_5000_10_percent(
    verification_client: TestClient,
) -> None:
    verification_id = _create_verification(
        verification_client,
        offer_id=5,
        status=PrivilegeVerificationStatus.pending.value,
        token="selected-offer-scan-token",
    )

    response = verification_client.post(
        "/api/v1/partner/privileges/scan",
        json={"qr_payload": "bloomclub:privilege:selected-offer-scan-token"},
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == verification_id
    assert data["privilege"] == {"id": 5, "title": "Selected Spa"}
    assert data["regular_price"] == "5000.00"
    assert data["club_price"] == "4500.00"
    assert data["estimated_saving_amount"] == "500.00"


def test_partner_confirm_uses_selected_session_offer_prices_5000_10_percent(
    verification_client: TestClient,
) -> None:
    verification_id = _create_verification(
        verification_client,
        offer_id=5,
        status=PrivilegeVerificationStatus.pending.value,
        token="selected-offer-confirm-token",
    )

    response = verification_client.post(
        "/api/v1/partner/privileges/confirm",
        json={"session_id": verification_id},
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 200
    assert response.json()["saving_amount"] == "500.00"
    with _session(verification_client) as session:
        stored = session.get(PrivilegeVerificationSession, verification_id)
        assert stored.saving_base_price == 5000
        assert stored.saving_final_price == 4500
        assert stored.saving_discount_percent == 10
        assert stored.saving_amount == 500
        assert stored.saving_offer_title == "Selected Spa"


def test_partner_scan_session_without_offer_does_not_show_random_partner_offer_price(
    verification_client: TestClient,
) -> None:
    verification_id = _create_verification(
        verification_client,
        offer_id=None,
        status=PrivilegeVerificationStatus.pending.value,
        token="no-offer-scan-token",
    )

    response = verification_client.post(
        "/api/v1/partner/privileges/scan",
        json={"qr_payload": "bloomclub:privilege:no-offer-scan-token"},
        headers=_auth_headers(_partner_token(verification_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == verification_id
    assert data["privilege"] is None
    assert data["regular_price"] is None
    assert data["club_price"] is None
    assert data["estimated_saving_amount"] == "0.00"
