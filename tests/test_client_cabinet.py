from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all SQLAlchemy models for test metadata
import app.api.v1.endpoints.clients as clients_endpoint
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.category import Category
from app.models.city import City
from app.models.client import ClientProfile
from app.models.giveaway import Giveaway, GiveawayNumber
from app.models.partner import Partner, PartnerOffer, PartnerPhoto
from app.models.payment import PaymentRequest, PaymentRequestStatus, Subscription, SubscriptionStatus
from app.models.user import AdminUser, User, UserRole


@pytest.fixture()
def client_cabinet_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    Base.metadata.create_all(bind=engine)
    with session_factory() as session:
        session.add(
            AdminUser(
                email="admin@example.com",
                password_hash=hash_password("AdminPassword123"),
                role=UserRole.ADMIN.value,
                is_active=True,
            )
        )
        client_user = User(
            email="client@example.com",
            phone="+79990000001",
            password_hash=hash_password("ClientPassword123"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        client_with_profile = User(
            email="profile@example.com",
            phone="+79990000002",
            password_hash=hash_password("ProfilePassword123"),
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
        unified_admin_user = User(
            email="unified-admin@example.com",
            phone="+79990000004",
            password_hash=hash_password("UnifiedAdminPassword123"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        session.add_all([client_user, client_with_profile, partner_user, unified_admin_user])
        session.flush()

        moscow = City(name="Москва", slug="moscow", is_active=True, sort_order=10)
        spb = City(name="Санкт-Петербург", slug="spb", is_active=True, sort_order=20)
        inactive_city = City(name="Казань", slug="kazan", is_active=False, sort_order=30)
        session.add_all([moscow, spb, inactive_city])
        session.flush()
        session.add_all(
            [
                Category(name="Beauty Active", slug="beauty", is_active=True, sort_order=10),
                Category(name="Fitness Inactive", slug="fitness", is_active=False, sort_order=20),
            ]
        )

        session.add(
            ClientProfile(
                user_id=client_with_profile.id,
                selected_city_id=spb.id,
                full_name="Existing Client",
                source="seed",
                is_active=True,
            )
        )

        active_moscow = Partner(
            city_id=moscow.id,
            owner_user_id=partner_user.id,
            category_slug="beauty",
            name="Alpha Beauty",
            description="Beauty description",
            address="Moscow address",
            phone="+70000000001",
            website_url="https://alpha.example.com",
            social_url="https://social.example.com/alpha",
            working_hours="10:00-20:00",
            logo_url="https://alpha.example.com/logo.png",
            cover_url="https://alpha.example.com/cover.png",
            is_active=True,
            is_verified=True,
            sort_order=20,
        )
        active_spb = Partner(
            city_id=spb.id,
            category_slug="fitness",
            name="Beta Yoga",
            cover_url="/uploads/partners/2/cover.webp",
            is_active=True,
            is_verified=False,
            sort_order=10,
        )
        inactive_partner = Partner(
            city_id=moscow.id,
            category_slug="beauty",
            name="Gamma Hidden",
            is_active=False,
            is_verified=True,
            sort_order=1,
        )
        session.add_all([active_moscow, active_spb, inactive_partner])
        session.flush()

        session.add_all(
            [
                PartnerOffer(
                    partner_id=active_moscow.id,
                    title="Second active",
                    benefit_text="-10%",
                    is_active=True,
                    sort_order=20,
                ),
                PartnerOffer(
                    partner_id=active_moscow.id,
                    title="First active",
                    is_active=True,
                    sort_order=10,
                ),
                PartnerOffer(
                    partner_id=active_moscow.id,
                    title="Inactive offer",
                    is_active=False,
                    sort_order=1,
                ),
                PartnerOffer(
                    partner_id=active_spb.id,
                    title="Other partner offer",
                    is_active=True,
                    sort_order=1,
                ),
            ]
        )

        session.add_all(
            [
                PartnerPhoto(
                    partner_id=active_moscow.id,
                    url="/uploads/partners/1/photos/photo-second.webp",
                    alt_text="Second active photo",
                    sort_order=20,
                    is_active=True,
                    created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                ),
                PartnerPhoto(
                    partner_id=active_moscow.id,
                    url="/uploads/partners/1/photos/photo-first.webp",
                    alt_text="First active photo",
                    sort_order=10,
                    is_active=True,
                    created_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
                ),
                PartnerPhoto(
                    partner_id=active_moscow.id,
                    url="/uploads/partners/1/photos/photo-first-created.webp",
                    alt_text="Earlier created photo",
                    sort_order=10,
                    is_active=True,
                    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                ),
                PartnerPhoto(
                    partner_id=active_moscow.id,
                    url="/uploads/partners/1/photos/photo-hidden.webp",
                    alt_text="Inactive photo",
                    sort_order=1,
                    is_active=False,
                    created_at=datetime(2025, 12, 31, tzinfo=timezone.utc),
                ),
                PartnerPhoto(
                    partner_id=active_spb.id,
                    url="/uploads/partners/2/photos/yoga.webp",
                    alt_text="Yoga studio",
                    sort_order=1,
                    is_active=True,
                    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                ),
            ]
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
def admin_token(client_cabinet_client: TestClient) -> str:
    response = client_cabinet_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPassword123"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_login(client: TestClient, login: str, password: str) -> str:
    response = client.post("/api/v1/auth/user-login", json={"login": login, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _client_token(client: TestClient) -> str:
    return _user_login(client, "client@example.com", "ClientPassword123")


def _profile_client_token(client: TestClient) -> str:
    return _user_login(client, "profile@example.com", "ProfilePassword123")


def _partner_token(client: TestClient) -> str:
    return _user_login(client, "partner@example.com", "PartnerPassword123")


def _unified_admin_token(client: TestClient) -> str:
    return _user_login(client, "unified-admin@example.com", "UnifiedAdminPassword123")


def _parse_api_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def test_client_me_without_token_returns_401(client_cabinet_client: TestClient) -> None:
    response = client_cabinet_client.get("/api/v1/clients/me")

    assert response.status_code == 401


def test_client_me_with_admin_user_token_returns_401(
    client_cabinet_client: TestClient,
    admin_token: str,
) -> None:
    response = client_cabinet_client.get("/api/v1/clients/me", headers=_auth_headers(admin_token))

    assert response.status_code == 401


def test_client_me_with_partner_unified_token_returns_403(client_cabinet_client: TestClient) -> None:
    token = _partner_token(client_cabinet_client)

    response = client_cabinet_client.get("/api/v1/clients/me", headers=_auth_headers(token))

    assert response.status_code == 403


def test_client_cities_returns_active_cities_with_expected_fields_and_order(
    client_cabinet_client: TestClient,
) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get("/api/v1/clients/cities", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Москва", "slug": "moscow"},
        {"id": 2, "name": "Санкт-Петербург", "slug": "spb"},
    ]


def test_client_cities_does_not_require_admin_role(client_cabinet_client: TestClient) -> None:
    token = _partner_token(client_cabinet_client)

    response = client_cabinet_client.get("/api/v1/clients/cities", headers=_auth_headers(token))

    assert response.status_code == 403
    assert response.json()["detail"] == "User role required"


def test_client_cities_sorting_is_stable_by_sort_order_then_name(
    client_cabinet_client: TestClient,
    admin_token: str,
) -> None:
    create_response = client_cabinet_client.post(
        "/api/v1/admin/cities",
        headers=_auth_headers(admin_token),
        json={"name": "Абакан", "slug": "abakan", "is_active": True, "sort_order": 10},
    )
    assert create_response.status_code == 200

    token = _client_token(client_cabinet_client)
    response = client_cabinet_client.get("/api/v1/clients/cities", headers=_auth_headers(token))

    assert response.status_code == 200
    assert [city["name"] for city in response.json()] == ["Абакан", "Москва", "Санкт-Петербург"]


def test_client_me_with_client_token_auto_creates_profile(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get("/api/v1/clients/me", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert data["email"] == "client@example.com"
    assert data["phone"] == "+79990000001"
    assert data["source"] == "web"
    assert data["is_active"] is True
    assert data["selected_city_id"] is None
    assert data["selected_city_name"] is None


def test_client_me_patch_updates_full_name_and_selected_city_id(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.patch(
        "/api/v1/clients/me",
        headers=_auth_headers(token),
        json={"full_name": "  Jane Client  ", "selected_city_id": 1},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Jane Client"
    assert data["selected_city_id"] == 1
    assert data["selected_city_name"] == "Москва"


def test_client_me_patch_selected_city_id_inactive_returns_404(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.patch(
        "/api/v1/clients/me",
        headers=_auth_headers(token),
        json={"selected_city_id": 3},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "City not found"


def test_client_me_patch_selected_city_id_missing_returns_404(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.patch(
        "/api/v1/clients/me",
        headers=_auth_headers(token),
        json={"selected_city_id": 999},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "City not found"


def test_client_me_patch_selected_city_id_null_clears_city(client_cabinet_client: TestClient) -> None:
    token = _profile_client_token(client_cabinet_client)

    response = client_cabinet_client.patch(
        "/api/v1/clients/me",
        headers=_auth_headers(token),
        json={"full_name": "   ", "selected_city_id": None},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Name must not be empty"




def test_client_me_patch_updates_contact_fields_without_overwriting_synthetic_login(client_cabinet_client: TestClient) -> None:
    token = _profile_client_token(client_cabinet_client)

    response = client_cabinet_client.patch(
        "/api/v1/clients/me",
        headers=_auth_headers(token),
        json={
            "name": "  Jane Client  ",
            "email": " winner@example.com ",
            "phone": " 89990000011 ",
            "city_slug": "moscow",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Jane Client"
    assert data["contact_email"] == "winner@example.com"
    assert data["phone"] == "+79990000011"
    assert data["selected_city_name"] == "Москва"




def test_client_me_patch_city_text_roundtrip(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    patch_response = client_cabinet_client.patch(
        "/api/v1/clients/me",
        headers=_auth_headers(token),
        json={
            "full_name": "Данил",
            "phone": "89005443434",
            "contact_email": "test@example.com",
            "city": "Новосибирск",
        },
    )

    assert patch_response.status_code == 200

    profile_response = client_cabinet_client.get("/api/v1/clients/me", headers=_auth_headers(token))
    assert profile_response.status_code == 200
    data = profile_response.json()
    assert data["full_name"] == "Данил"
    assert data["phone"] == "+79005443434"
    assert data["contact_email"] == "test@example.com"
    assert data["city"] == "Новосибирск"


def test_client_me_patch_invalid_email_returns_400(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.patch(
        "/api/v1/clients/me",
        headers=_auth_headers(token),
        json={"email": "invalid-email"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email format"
def test_client_me_subscription_returns_inactive_when_none(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get("/api/v1/clients/me/subscription", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    assert data["status"] == "inactive"
    assert data["expires_at"] is None
    assert data["end_date"] is None


def test_client_me_subscription_returns_current_active_not_latest_invalid(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    profile_response = client_cabinet_client.get("/api/v1/clients/me", headers=_auth_headers(token))
    profile_id = profile_response.json()["id"]
    now = datetime.now(timezone.utc)

    with next(app.dependency_overrides[get_db]()) as session:
        session.add_all(
            [
                Subscription(
                    client_id=profile_id,
                    status=SubscriptionStatus.expired.value,
                    starts_at=now - timedelta(days=60),
                    ends_at=now - timedelta(days=30),
                ),
                Subscription(
                    client_id=profile_id,
                    status=SubscriptionStatus.paused.value,
                    starts_at=now,
                    ends_at=now + timedelta(days=30),
                ),
                Subscription(
                    client_id=profile_id,
                    status=SubscriptionStatus.active.value,
                    starts_at=now + timedelta(days=31),
                    ends_at=now + timedelta(days=60),
                ),
                Subscription(
                    client_id=profile_id,
                    status=SubscriptionStatus.active.value,
                    starts_at=now - timedelta(days=1),
                    ends_at=now + timedelta(days=30),
                ),
            ]
        )
        session.commit()

    response = client_cabinet_client.get("/api/v1/clients/me/subscription", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == SubscriptionStatus.active.value
    assert data["client_id"] == profile_id
    assert data["source_payment_request_id"] is None


def test_client_can_activate_trial_subscription_for_15_days(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    before = datetime.now(timezone.utc)

    response = client_cabinet_client.post("/api/v1/clients/me/trial-subscription", headers=_auth_headers(token))
    after = datetime.now(timezone.utc)

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True
    assert data["subscription_active"] is True
    assert data["status"] == SubscriptionStatus.active.value
    assert data["source"] == "trial"
    assert data["type"] == "trial"
    assert data["trial_used"] is True
    assert data["trial_available"] is False
    expires_at = _parse_api_datetime(data["expires_at"])
    assert before + timedelta(days=15) <= expires_at <= after + timedelta(days=15)
    assert data["subscription_until"] == data["expires_at"]

    subscription_response = client_cabinet_client.get("/api/v1/clients/me/subscription", headers=_auth_headers(token))
    assert subscription_response.status_code == 200
    assert subscription_response.json()["source"] == "trial"



def test_documented_risk_trial_subscription_is_per_client_profile_today(
    client_cabinet_client: TestClient,
) -> None:
    """Documentation regression: duplicated profiles can each activate one trial today."""
    first_token = _client_token(client_cabinet_client)
    second_token = _profile_client_token(client_cabinet_client)

    first_response = client_cabinet_client.post(
        "/api/v1/clients/me/trial-subscription",
        headers=_auth_headers(first_token),
    )
    second_response = client_cabinet_client.post(
        "/api/v1/clients/me/trial-subscription",
        headers=_auth_headers(second_token),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["client_id"] != second_response.json()["client_id"]
    assert first_response.json()["trial_used"] is True
    assert second_response.json()["trial_used"] is True


def test_client_trial_subscription_creates_base_giveaway_number(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    with next(app.dependency_overrides[get_db]()) as session:
        session.add(Giveaway(title="active", is_active=True, winners_count=1))
        session.commit()

    response = client_cabinet_client.post("/api/v1/clients/me/trial-subscription", headers=_auth_headers(token))
    assert response.status_code == 200

    giveaway_response = client_cabinet_client.get("/api/v1/clients/giveaway", headers=_auth_headers(token))
    assert giveaway_response.status_code == 200
    data = giveaway_response.json()
    assert data["has_active_giveaway"] is True
    assert data["user_numbers_count"] == 1
    assert data["numbers"][0]["source"] == "subscription"

    repeat_response = client_cabinet_client.get("/api/v1/clients/giveaway", headers=_auth_headers(token))
    assert repeat_response.status_code == 200
    with next(app.dependency_overrides[get_db]()) as session:
        assert session.query(GiveawayNumber).count() == 1


def test_active_giveaway_visible_with_zero_entries_for_guest(client_cabinet_client: TestClient) -> None:
    with next(app.dependency_overrides[get_db]()) as session:
        session.add(Giveaway(title="active", is_active=True, winners_count=1))
        session.commit()

    response = client_cabinet_client.get("/api/v1/clients/giveaway")
    assert response.status_code == 200
    data = response.json()
    assert data["has_active_giveaway"] is True
    assert data["giveaway"]["title"] == "active"
    assert data["guest"] is True
    assert data["numbers"] == []

def test_client_trial_subscription_repeated_activation_is_blocked(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    first_response = client_cabinet_client.post("/api/v1/clients/me/trial-subscription", headers=_auth_headers(token))
    assert first_response.status_code == 200
    first_expires_at = first_response.json()["expires_at"]

    second_response = client_cabinet_client.post("/api/v1/clients/me/trial-subscription", headers=_auth_headers(token))

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Trial subscription already activated"
    subscription_response = client_cabinet_client.get("/api/v1/clients/me/subscription", headers=_auth_headers(token))
    assert subscription_response.status_code == 200
    assert subscription_response.json()["expires_at"] == first_expires_at


def test_client_trial_subscription_does_not_shorten_later_paid_subscription(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    profile_response = client_cabinet_client.get("/api/v1/clients/me", headers=_auth_headers(token))
    profile_id = profile_response.json()["id"]
    now = datetime.now(timezone.utc)
    paid_until = now + timedelta(days=45)

    with next(app.dependency_overrides[get_db]()) as session:
        session.add(
            Subscription(
                client_id=profile_id,
                status=SubscriptionStatus.active.value,
                starts_at=now - timedelta(days=1),
                ends_at=paid_until,
                source="paid",
            )
        )
        session.commit()

    response = client_cabinet_client.post("/api/v1/clients/me/trial-subscription", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "paid"
    assert _parse_api_datetime(data["expires_at"]) == paid_until
    assert data["trial_used"] is True


def test_client_trial_subscription_makes_expired_subscription_active(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    profile_response = client_cabinet_client.get("/api/v1/clients/me", headers=_auth_headers(token))
    profile_id = profile_response.json()["id"]
    now = datetime.now(timezone.utc)

    with next(app.dependency_overrides[get_db]()) as session:
        session.add(
            Subscription(
                client_id=profile_id,
                status=SubscriptionStatus.expired.value,
                starts_at=now - timedelta(days=45),
                ends_at=now - timedelta(days=15),
                source="paid",
            )
        )
        session.commit()

    response = client_cabinet_client.post("/api/v1/clients/me/trial-subscription", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True
    assert data["source"] == "trial"
    assert _parse_api_datetime(data["expires_at"]) > now


def test_client_trial_subscription_available_after_old_promo_deadline(
    client_cabinet_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class AfterPromoDateTime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[no-untyped-def]
            fixed = datetime(2026, 6, 16, 0, 0, tzinfo=timezone.utc)
            return fixed if tz is None else fixed.astimezone(tz)

    monkeypatch.setattr(clients_endpoint, "datetime", AfterPromoDateTime)
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.post("/api/v1/clients/me/trial-subscription", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["trial_used"] is True


def test_client_trial_subscription_without_token_returns_401(client_cabinet_client: TestClient) -> None:
    response = client_cabinet_client.post("/api/v1/clients/me/trial-subscription", json={})

    assert response.status_code == 401


def test_client_trial_subscription_with_partner_or_admin_user_token_returns_403(
    client_cabinet_client: TestClient,
) -> None:
    partner_token = _partner_token(client_cabinet_client)
    admin_user_token = _unified_admin_token(client_cabinet_client)

    partner_response = client_cabinet_client.post(
        "/api/v1/clients/me/trial-subscription",
        headers=_auth_headers(partner_token),
    )
    admin_response = client_cabinet_client.post(
        "/api/v1/clients/me/trial-subscription",
        headers=_auth_headers(admin_user_token),
    )

    assert partner_response.status_code == 403
    assert admin_response.status_code == 403


def test_client_catalog_partners_returns_only_active_partners(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get("/api/v1/clients/catalog/partners", headers=_auth_headers(token))

    assert response.status_code == 200
    assert [partner["name"] for partner in response.json()] == ["Beta Yoga", "Alpha Beauty"]



def test_client_catalog_partners_returns_active_photos_only_sorted_without_admin_fields(
    client_cabinet_client: TestClient,
) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get(
        "/api/v1/clients/catalog/partners?city_id=1",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    partner = data[0]
    assert [photo["url"] for photo in partner["photos"]] == [
        "/uploads/partners/1/photos/photo-first.webp",
        "/uploads/partners/1/photos/photo-first-created.webp",
        "/uploads/partners/1/photos/photo-second.webp",
    ]
    assert "/uploads/partners/1/photos/photo-hidden.webp" not in [photo["url"] for photo in partner["photos"]]
    assert partner["photo_url"] == "/uploads/partners/1/photos/photo-first.webp"
    assert partner["image_url"] == "/uploads/partners/1/photos/photo-first.webp"
    assert all("is_active" not in photo for photo in partner["photos"])
    assert all("partner_id" not in photo for photo in partner["photos"])
    assert "owner_user_id" not in partner


def test_client_catalog_partner_image_url_uses_active_gallery_photo_before_cover(
    client_cabinet_client: TestClient,
) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get("/api/v1/clients/catalog/partners", headers=_auth_headers(token))

    assert response.status_code == 200
    data = {partner["name"]: partner for partner in response.json()}
    assert data["Alpha Beauty"]["image_url"] == "/uploads/partners/1/photos/photo-first.webp"
    assert data["Beta Yoga"]["photo_url"] == "/uploads/partners/2/photos/yoga.webp"
    assert data["Beta Yoga"]["image_url"] == "/uploads/partners/2/photos/yoga.webp"


def test_client_catalog_partners_filters_by_city_id(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get(
        "/api/v1/clients/catalog/partners?city_id=1",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert [partner["name"] for partner in response.json()] == ["Alpha Beauty"]


def test_client_catalog_partners_filters_by_city_slug(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get(
        "/api/v1/clients/catalog/partners?city_slug=spb",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()
    assert [partner["name"] for partner in data] == ["Beta Yoga"]
    assert data[0]["city_name"] == "Санкт-Петербург"


def test_client_catalog_partners_uses_selected_city_id_when_no_city_filter(
    client_cabinet_client: TestClient,
) -> None:
    token = _profile_client_token(client_cabinet_client)

    response = client_cabinet_client.get("/api/v1/clients/catalog/partners", headers=_auth_headers(token))

    assert response.status_code == 200
    assert [partner["name"] for partner in response.json()] == ["Beta Yoga"]


def test_client_catalog_city_slug_inactive_or_missing_returns_404(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    inactive_response = client_cabinet_client.get(
        "/api/v1/clients/catalog/partners?city_slug=kazan",
        headers=_auth_headers(token),
    )
    missing_response = client_cabinet_client.get(
        "/api/v1/clients/catalog/partners?city_slug=missing",
        headers=_auth_headers(token),
    )

    assert inactive_response.status_code == 404
    assert inactive_response.json()["detail"] == "City not found"
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "City not found"


def test_client_catalog_partners_filters_by_category_slug(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get(
        "/api/v1/clients/catalog/partners?category_slug=beauty",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert [partner["name"] for partner in response.json()] == ["Alpha Beauty"]


def test_client_catalog_partner_visibility_with_m2m_categories_city_and_active_offer(
    client_cabinet_client: TestClient,
    admin_token: str,
) -> None:
    token = _client_token(client_cabinet_client)

    category_payloads = [
        {"name": "Красота", "slug": "krasota", "is_active": True, "sort_order": 10},
        {"name": "Маникюр / педикюр", "slug": "manikyur-pedikyur", "is_active": True, "sort_order": 20},
        {"name": "Брови / ресницы", "slug": "brovi-resnitsy", "is_active": True, "sort_order": 30},
        {"name": "Косметология", "slug": "kosmetologiya", "is_active": True, "sort_order": 40},
    ]
    created_categories: list[dict[str, object]] = []
    for payload in category_payloads:
        response = client_cabinet_client.post("/api/v1/admin/categories", headers=_auth_headers(admin_token), json=payload)
        assert response.status_code == 200
        created_categories.append(response.json())

    partner_response = client_cabinet_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json={
            "city_id": 1,
            "name": "Счастье есть",
            "is_active": True,
            "is_verified": True,
            "category_slug": "krasota",
            "category_ids": [category["id"] for category in created_categories],
            "cover_url": "/uploads/partners/schastye/cover.webp",
        },
    )
    assert partner_response.status_code == 200
    partner_id = partner_response.json()["id"]

    offer_response = client_cabinet_client.post(
        f"/api/v1/admin/partners/{partner_id}/offers",
        headers=_auth_headers(admin_token),
        json={
            "title": 'Наращивание ресниц "Классика" |Топ-мастер Арина ❤️|',
            "base_price": "2250.00",
            "discount_percent": "11.00",
            "is_active": True,
            "sort_order": 1,
        },
    )
    assert offer_response.status_code == 200

    catalog_response = client_cabinet_client.get("/api/v1/clients/catalog/partners", headers=_auth_headers(token))
    assert catalog_response.status_code == 200
    by_name = {partner["name"]: partner for partner in catalog_response.json()}
    assert "Счастье есть" in by_name

    catalog_partner = by_name["Счастье есть"]
    assert catalog_partner["category_slug"] == "krasota"
    assert catalog_partner["photo_url"] is None
    assert catalog_partner["image_url"] == "/uploads/partners/schastye/cover.webp"
    assert catalog_partner["category_slugs"] == [
        "krasota",
        "manikyur-pedikyur",
        "brovi-resnitsy",
        "kosmetologiya",
    ]
    assert len(catalog_partner["categories"]) == 4
    assert sorted(catalog_partner["category_ids"]) == sorted([category["id"] for category in created_categories])

    for category in ("krasota", "manikyur-pedikyur", "brovi-resnitsy", "kosmetologiya"):
        category_response = client_cabinet_client.get(
            f"/api/v1/clients/catalog/partners?category_slug={category}",
            headers=_auth_headers(token),
        )
        assert category_response.status_code == 200
        assert "Счастье есть" in [item["name"] for item in category_response.json()]

    detail_response = client_cabinet_client.get(f"/api/v1/clients/partners/{partner_id}", headers=_auth_headers(token))
    assert detail_response.status_code == 200
    assert detail_response.json()["name"] == "Счастье есть"

    offers_response = client_cabinet_client.get(f"/api/v1/clients/partners/{partner_id}/offers", headers=_auth_headers(token))
    assert offers_response.status_code == 200
    offers = offers_response.json()
    assert len(offers) == 1
    assert offers[0]["title"] == 'Наращивание ресниц "Классика" |Топ-мастер Арина ❤️|'
    assert offers[0]["base_price"] == "2250.00"
    assert offers[0]["discount_percent"] == "11.00"
    assert offers[0]["image_url"] is None

    same_city_response = client_cabinet_client.get(
        "/api/v1/clients/catalog/partners?city_id=1",
        headers=_auth_headers(token),
    )
    assert same_city_response.status_code == 200
    assert "Счастье есть" in [item["name"] for item in same_city_response.json()]

    other_city_response = client_cabinet_client.get(
        "/api/v1/clients/catalog/partners?city_id=2",
        headers=_auth_headers(token),
    )
    assert other_city_response.status_code == 200
    assert "Счастье есть" not in [item["name"] for item in other_city_response.json()]


def test_client_catalog_partners_returns_category_fields_for_active_and_inactive_categories(
    client_cabinet_client: TestClient,
) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get("/api/v1/clients/catalog/partners", headers=_auth_headers(token))

    assert response.status_code == 200
    data = {partner["name"]: partner for partner in response.json()}
    assert data["Alpha Beauty"]["category_slug"] == "beauty"
    assert data["Alpha Beauty"]["category"] is None
    assert data["Beta Yoga"]["category_id"] is None
    assert data["Beta Yoga"]["category_name"] is None
    assert data["Beta Yoga"]["category_slug"] == "fitness"
    assert data["Beta Yoga"]["category"] is None
    assert data["Alpha Beauty"]["photo_url"] == "/uploads/partners/1/photos/photo-first.webp"
    assert data["Alpha Beauty"]["image_url"] == "/uploads/partners/1/photos/photo-first.webp"
    assert isinstance(data["Alpha Beauty"]["categories"], list)
    assert isinstance(data["Alpha Beauty"]["category_ids"], list)
    assert isinstance(data["Alpha Beauty"]["category_slugs"], list)


def test_client_catalog_partners_humanizes_display_city_and_category_names(
    client_cabinet_client: TestClient,
    admin_token: str,
) -> None:
    token = _client_token(client_cabinet_client)

    city_response = client_cabinet_client.post(
        "/api/v1/admin/cities",
        headers=_auth_headers(admin_token),
        json={"name": "новосибирск", "slug": "novosibirsk", "is_active": True, "sort_order": 1},
    )
    assert city_response.status_code == 200
    city_id = city_response.json()["id"]

    category_response = client_cabinet_client.post(
        "/api/v1/admin/categories",
        headers=_auth_headers(admin_token),
        json={"name": "красота", "slug": "krasota", "is_active": True, "sort_order": 1},
    )
    assert category_response.status_code == 200
    category_id = category_response.json()["id"]

    partner_response = client_cabinet_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json={
            "city_id": city_id,
            "name": "Lowercase Partner",
            "is_active": True,
            "is_verified": True,
            "category_slug": "krasota",
            "category_ids": [category_id],
        },
    )
    assert partner_response.status_code == 200

    response = client_cabinet_client.get(
        "/api/v1/clients/catalog/partners?city_slug=novosibirsk&category_slug=krasota",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    partner = data[0]

    assert partner["city_name"] == "Новосибирск"
    assert partner["category_name"] == "Красота"
    assert partner["category"]["name"] == "Красота"
    assert partner["categories"][0]["name"] == "Красота"

    assert partner["city_id"] == city_id
    assert partner["category_slug"] == "krasota"
    assert partner["category"]["slug"] == "krasota"
    assert partner["category_slugs"] == ["krasota"]


def test_client_catalog_partners_q_search_works(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get(
        "/api/v1/clients/catalog/partners?q=yOg",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert [partner["name"] for partner in response.json()] == ["Beta Yoga"]


def test_client_partner_detail_returns_active_partner_with_city_name(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get("/api/v1/clients/partners/1", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Alpha Beauty"
    assert data["city_name"] == "Москва"
    assert data["category_slug"] == "beauty"
    assert data["category"] is None
    assert data["is_verified"] is True
    assert data["photo_url"] == "/uploads/partners/1/photos/photo-first.webp"
    assert [photo["url"] for photo in data["photos"]] == [
        "/uploads/partners/1/photos/photo-first.webp",
        "/uploads/partners/1/photos/photo-first-created.webp",
        "/uploads/partners/1/photos/photo-second.webp",
    ]
    assert all("is_active" not in photo for photo in data["photos"])
    assert all("partner_id" not in photo for photo in data["photos"])
    assert "is_active" not in data
    assert "owner_user_id" not in data




def test_client_partner_detail_without_photos_returns_null_photo_url(
    client_cabinet_client: TestClient,
    admin_token: str,
) -> None:
    token = _client_token(client_cabinet_client)

    create_response = client_cabinet_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json={"city_id": 1, "name": "No Photo Partner", "is_active": True},
    )
    assert create_response.status_code == 200
    partner_id = create_response.json()["id"]

    response = client_cabinet_client.get(f"/api/v1/clients/partners/{partner_id}", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "No Photo Partner"
    assert data["photo_url"] is None
    assert data["photos"] == []
def test_client_partner_detail_missing_or_inactive_partner_returns_404(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    inactive_response = client_cabinet_client.get("/api/v1/clients/partners/3", headers=_auth_headers(token))
    missing_response = client_cabinet_client.get("/api/v1/clients/partners/999", headers=_auth_headers(token))

    assert inactive_response.status_code == 404
    assert inactive_response.json()["detail"] == "Partner not found"
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Partner not found"


def test_client_partner_offers_returns_only_active_offers_ordered(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.get("/api/v1/clients/partners/1/offers", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert [offer["title"] for offer in data] == ["First active", "Second active"]
    assert [offer["sort_order"] for offer in data] == [10, 20]
    assert {offer["partner_id"] for offer in data} == {1}


def test_client_payment_requests_without_token_returns_401(client_cabinet_client: TestClient) -> None:
    response = client_cabinet_client.post("/api/v1/clients/me/payment-requests", json={})

    assert response.status_code == 401


def test_client_payment_requests_with_partner_or_admin_user_token_returns_403(
    client_cabinet_client: TestClient,
) -> None:
    partner_token = _partner_token(client_cabinet_client)
    admin_user_token = _unified_admin_token(client_cabinet_client)

    partner_response = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(partner_token),
        json={},
    )
    admin_response = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(admin_user_token),
        json={},
    )

    assert partner_response.status_code == 403
    assert admin_response.status_code == 403


def test_client_can_create_payment_request(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    profile = client_cabinet_client.get("/api/v1/clients/me", headers=_auth_headers(token)).json()

    response = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(token),
        json={"amount": "1234.50", "source": " web ", "comment": "  first request  "},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["client_id"] == profile["id"]
    assert data["amount"] == "1234.50"
    assert data["status"] == PaymentRequestStatus.pending.value
    assert data["source"] == "web"
    assert data["comment"] == "first request"
    assert data["receipts"] == []


def test_client_payment_request_default_amount_is_standard_subscription(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(token),
        json={},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == "349.00"
    assert data["status"] == PaymentRequestStatus.pending.value
    assert data["source"] == "web"




def test_client_payment_request_accepts_empty_body(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)

    response = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        content="",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["amount"] == "349.00"
    assert data["status"] == PaymentRequestStatus.pending.value


def test_client_can_list_only_own_payment_requests(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    other_token = _profile_client_token(client_cabinet_client)
    own_first = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(token),
        json={"amount": "10.00", "source": "web"},
    ).json()
    other = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(other_token),
        json={"amount": "20.00", "source": "vk"},
    ).json()
    own_second = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(token),
        json={"amount": "30.00", "source": "web"},
    ).json()

    response = client_cabinet_client.get("/api/v1/clients/me/payment-requests", headers=_auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data] == [own_second["id"], own_first["id"]]
    assert other["id"] not in [item["id"] for item in data]
    assert all(item["client_id"] == own_first["client_id"] for item in data)


def test_client_can_get_own_payment_request_by_id(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    created = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(token),
        json={"amount": "99.00"},
    ).json()

    response = client_cabinet_client.get(
        f"/api/v1/clients/me/payment-requests/{created['id']}",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["client_id"] == created["client_id"]


def test_client_cannot_read_another_client_payment_request(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    other_token = _profile_client_token(client_cabinet_client)
    other = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(other_token),
        json={"amount": "20.00"},
    ).json()

    response = client_cabinet_client.get(
        f"/api/v1/clients/me/payment-requests/{other['id']}",
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


def test_client_mark_paid_pending_to_paid_and_paid_idempotent(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    created = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(token),
        json={"amount": "99.00", "comment": "Initial"},
    ).json()

    paid_response = client_cabinet_client.post(
        f"/api/v1/clients/me/payment-requests/{created['id']}/mark-paid",
        headers=_auth_headers(token),
    )
    idempotent_response = client_cabinet_client.post(
        f"/api/v1/clients/me/payment-requests/{created['id']}/mark-paid",
        headers=_auth_headers(token),
        json={},
    )
    comment_response = client_cabinet_client.post(
        f"/api/v1/clients/me/payment-requests/{created['id']}/mark-paid",
        headers=_auth_headers(token),
        json={"comment": "Paid in bank app"},
    )

    assert paid_response.status_code == 200
    paid_data = paid_response.json()
    assert paid_data["status"] == PaymentRequestStatus.paid.value
    assert paid_data["updated_at"] is not None
    assert paid_data["comment"] == "Initial"

    assert idempotent_response.status_code == 200
    assert idempotent_response.json()["status"] == PaymentRequestStatus.paid.value

    assert comment_response.status_code == 200
    comment_data = comment_response.json()
    assert comment_data["status"] == PaymentRequestStatus.paid.value
    assert "Initial" in comment_data["comment"]
    assert "Paid in bank app" in comment_data["comment"]


def test_client_cannot_mark_paid_another_client_payment_request(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    other_token = _profile_client_token(client_cabinet_client)
    other = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(other_token),
        json={"amount": "20.00"},
    ).json()

    response = client_cabinet_client.post(
        f"/api/v1/clients/me/payment-requests/{other['id']}/mark-paid",
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


def test_client_mark_paid_approved_or_rejected_returns_400(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    approved = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(token),
        json={"amount": "10.00"},
    ).json()
    rejected = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(token),
        json={"amount": "20.00"},
    ).json()
    with next(app.dependency_overrides[get_db]()) as session:
        session.get(PaymentRequest, approved["id"]).status = PaymentRequestStatus.approved.value
        session.get(PaymentRequest, rejected["id"]).status = PaymentRequestStatus.rejected.value
        session.commit()

    approved_response = client_cabinet_client.post(
        f"/api/v1/clients/me/payment-requests/{approved['id']}/mark-paid",
        headers=_auth_headers(token),
        json={},
    )
    rejected_response = client_cabinet_client.post(
        f"/api/v1/clients/me/payment-requests/{rejected['id']}/mark-paid",
        headers=_auth_headers(token),
        json={},
    )

    assert approved_response.status_code == 400
    assert rejected_response.status_code == 400


def test_client_can_create_receipt_for_own_payment_request(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    created = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(token),
        json={"amount": "99.00"},
    ).json()

    response = client_cabinet_client.post(
        f"/api/v1/clients/me/payment-requests/{created['id']}/receipts",
        headers=_auth_headers(token),
        json={"file_url": "https://example.com/receipt.png", "uploaded_via": " web "},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["payment_request_id"] == created["id"]
    assert data["file_url"] == "https://example.com/receipt.png"
    assert data["uploaded_via"] == "web"


def test_client_cannot_add_receipt_to_another_client_payment_request(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    other_token = _profile_client_token(client_cabinet_client)
    other = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(other_token),
        json={"amount": "20.00"},
    ).json()

    response = client_cabinet_client.post(
        f"/api/v1/clients/me/payment-requests/{other['id']}/receipts",
        headers=_auth_headers(token),
        json={"file_url": "https://example.com/receipt.png"},
    )

    assert response.status_code == 404


def test_client_payment_request_reads_include_receipts(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    created = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(token),
        json={"amount": "99.00"},
    ).json()
    receipt = client_cabinet_client.post(
        f"/api/v1/clients/me/payment-requests/{created['id']}/receipts",
        headers=_auth_headers(token),
        json={"file_url": "https://example.com/receipt.png"},
    ).json()

    detail_response = client_cabinet_client.get(
        f"/api/v1/clients/me/payment-requests/{created['id']}",
        headers=_auth_headers(token),
    )
    list_response = client_cabinet_client.get("/api/v1/clients/me/payment-requests", headers=_auth_headers(token))

    assert detail_response.status_code == 200
    assert detail_response.json()["receipts"] == [receipt]
    assert list_response.status_code == 200
    assert list_response.json()[0]["receipts"] == [receipt]


def test_client_payment_request_mark_paid_does_not_create_subscription(client_cabinet_client: TestClient) -> None:
    token = _client_token(client_cabinet_client)
    profile = client_cabinet_client.get("/api/v1/clients/me", headers=_auth_headers(token)).json()
    created = client_cabinet_client.post(
        "/api/v1/clients/me/payment-requests",
        headers=_auth_headers(token),
        json={"amount": "99.00"},
    ).json()

    response = client_cabinet_client.post(
        f"/api/v1/clients/me/payment-requests/{created['id']}/mark-paid",
        headers=_auth_headers(token),
        json={},
    )
    subscription_response = client_cabinet_client.get("/api/v1/clients/me/subscription", headers=_auth_headers(token))

    assert response.status_code == 200
    assert subscription_response.status_code == 200
    subscription_data = subscription_response.json()
    assert subscription_data["is_active"] is False
    assert subscription_data["status"] == "inactive"
    with next(app.dependency_overrides[get_db]()) as session:
        assert session.query(Subscription).filter(Subscription.client_id == profile["id"]).count() == 0


def _seed_linking_profiles(client: TestClient, *, target_trial_used: bool = False, multiple: bool = False) -> None:
    with next(client.app.dependency_overrides[get_db]()) as session:
        vk_user = User(
            email="linked-vk@example.com",
            phone="+79991112234",
            role=UserRole.CLIENT.value,
            is_active=True,
            password_hash=hash_password("LinkedPassword123"),
        )
        tg_user = User(
            email=None,
            phone=None,
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        session.add_all([vk_user, tg_user])
        session.flush()
        vk_profile = ClientProfile(
            user_id=vk_user.id,
            vk_user_id="777001",
            contact_email="linked-vk@example.com",
            trial_subscription_used_at=datetime.now(timezone.utc) if target_trial_used else None,
            is_active=True,
            source="vk-miniapp",
        )
        tg_profile = ClientProfile(
            user_id=tg_user.id,
            telegram_user_id="999001",
            telegram_username="bloom_tg",
            is_active=True,
            source="telegram-miniapp",
        )
        session.add_all([vk_profile, tg_profile])
        if multiple:
            other_user = User(email="other-vk@example.com", phone=None, role=UserRole.CLIENT.value, is_active=True)
            session.add(other_user)
            session.flush()
            session.add(ClientProfile(user_id=other_user.id, vk_user_id="777002", contact_email="linked-vk@example.com", is_active=True, source="vk-miniapp"))
        session.commit()


def _tg_linking_token(client: TestClient) -> str:
    from app.core.security import create_access_token
    with next(client.app.dependency_overrides[get_db]()) as session:
        user_id = session.execute(select(User.id).where(User.email.is_(None))).scalar_one()
    return create_access_token(f"user:{user_id}")


def test_linking_status_for_new_tg_profile_can_start(client_cabinet_client: TestClient) -> None:
    _seed_linking_profiles(client_cabinet_client)
    token = _tg_linking_token(client_cabinet_client)

    response = client_cabinet_client.get("/api/v1/clients/me/linking-status", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["has_telegram_identity"] is True
    assert response.json()["is_linked"] is False
    assert response.json()["can_start_linking"] is True


def test_linking_start_not_found(client_cabinet_client: TestClient) -> None:
    _seed_linking_profiles(client_cabinet_client)
    token = _tg_linking_token(client_cabinet_client)

    response = client_cabinet_client.post(
        "/api/v1/clients/me/linking/start",
        json={"identifier": "missing@example.com"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json() == {"status": "not_found", "challenge_id": None, "masked_identifier": None, "expires_in_seconds": None, "dev_code": None}


def test_linking_start_existing_vk_profile_creates_challenge(client_cabinet_client: TestClient) -> None:
    _seed_linking_profiles(client_cabinet_client)
    token = _tg_linking_token(client_cabinet_client)

    response = client_cabinet_client.post(
        "/api/v1/clients/me/linking/start",
        json={"identifier": "LINKED-VK@example.com"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "challenge_created"
    assert body["challenge_id"]
    assert body["masked_identifier"] == "l***@example.com"
    assert body["expires_in_seconds"] == 600
    assert body["dev_code"] and len(body["dev_code"]) == 6


def test_linking_start_multiple_matches(client_cabinet_client: TestClient) -> None:
    _seed_linking_profiles(client_cabinet_client, multiple=True)
    token = _tg_linking_token(client_cabinet_client)

    response = client_cabinet_client.post(
        "/api/v1/clients/me/linking/start",
        json={"identifier": "linked-vk@example.com"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "multiple_matches"


def test_linking_confirm_invalid_expired_and_success(client_cabinet_client: TestClient) -> None:
    from app.models.client import AccountLinkingChallenge, ClientIdentityLink

    _seed_linking_profiles(client_cabinet_client)
    token = _tg_linking_token(client_cabinet_client)
    start = client_cabinet_client.post(
        "/api/v1/clients/me/linking/start",
        json={"identifier": "linked-vk@example.com"},
        headers=_auth_headers(token),
    ).json()

    bad = client_cabinet_client.post(
        "/api/v1/clients/me/linking/confirm",
        json={"challenge_id": start["challenge_id"], "code": "000000"},
        headers=_auth_headers(token),
    )
    assert bad.status_code == 400
    assert bad.json()["detail"] == "invalid_code"

    with next(client_cabinet_client.app.dependency_overrides[get_db]()) as session:
        challenge = session.get(AccountLinkingChallenge, start["challenge_id"])
        challenge.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        session.commit()
    expired = client_cabinet_client.post(
        "/api/v1/clients/me/linking/confirm",
        json={"challenge_id": start["challenge_id"], "code": start["dev_code"]},
        headers=_auth_headers(token),
    )
    assert expired.status_code == 400
    assert expired.json()["detail"] == "expired_challenge"

    start = client_cabinet_client.post(
        "/api/v1/clients/me/linking/start",
        json={"identifier": "linked-vk@example.com"},
        headers=_auth_headers(token),
    ).json()
    ok = client_cabinet_client.post(
        "/api/v1/clients/me/linking/confirm",
        json={"challenge_id": start["challenge_id"], "code": start["dev_code"]},
        headers=_auth_headers(token),
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["status"] == "linked"
    assert body["client"]["vk_user_id"] == "777001"
    assert body["access_token"]
    with next(client_cabinet_client.app.dependency_overrides[get_db]()) as session:
        target = session.execute(select(ClientProfile).where(ClientProfile.vk_user_id == "777001")).scalar_one()
        assert target.telegram_user_id == "999001"
        link = session.execute(select(ClientIdentityLink).where(ClientIdentityLink.provider == "telegram")).scalar_one()
        assert link.client_profile_id == target.id


def test_linking_conflicts_target_has_other_telegram(client_cabinet_client: TestClient) -> None:
    _seed_linking_profiles(client_cabinet_client)
    token = _tg_linking_token(client_cabinet_client)
    with next(client_cabinet_client.app.dependency_overrides[get_db]()) as session:
        target = session.execute(select(ClientProfile).where(ClientProfile.vk_user_id == "777001")).scalar_one()
        target.telegram_user_id = "another-tg"
        session.commit()
    start = client_cabinet_client.post(
        "/api/v1/clients/me/linking/start",
        json={"identifier": "linked-vk@example.com"},
        headers=_auth_headers(token),
    ).json()

    response = client_cabinet_client.post(
        "/api/v1/clients/me/linking/confirm",
        json={"challenge_id": start["challenge_id"], "code": start["dev_code"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "target_has_another_telegram_identity"


def test_linking_conflicts_temporary_profile_has_trial(client_cabinet_client: TestClient) -> None:
    _seed_linking_profiles(client_cabinet_client)
    token = _tg_linking_token(client_cabinet_client)
    with next(client_cabinet_client.app.dependency_overrides[get_db]()) as session:
        tg = session.execute(select(ClientProfile).where(ClientProfile.telegram_user_id == "999001")).scalar_one()
        tg.trial_subscription_used_at = datetime.now(timezone.utc)
        session.commit()
    start = client_cabinet_client.post(
        "/api/v1/clients/me/linking/start",
        json={"identifier": "linked-vk@example.com"},
        headers=_auth_headers(token),
    ).json()

    response = client_cabinet_client.post(
        "/api/v1/clients/me/linking/confirm",
        json={"challenge_id": start["challenge_id"], "code": start["dev_code"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "temporary_profile_has_activity"


def test_trial_not_reissued_after_linking_to_vk_profile_with_used_trial(client_cabinet_client: TestClient) -> None:
    _seed_linking_profiles(client_cabinet_client, target_trial_used=True)
    token = _tg_linking_token(client_cabinet_client)
    start = client_cabinet_client.post(
        "/api/v1/clients/me/linking/start",
        json={"identifier": "linked-vk@example.com"},
        headers=_auth_headers(token),
    ).json()
    linked = client_cabinet_client.post(
        "/api/v1/clients/me/linking/confirm",
        json={"challenge_id": start["challenge_id"], "code": start["dev_code"]},
        headers=_auth_headers(token),
    ).json()
    linked_token = linked["access_token"]

    state = client_cabinet_client.get("/api/v1/clients/me/subscription", headers=_auth_headers(linked_token))
    assert state.status_code == 200
    assert state.json()["trial_used"] is True
    assert state.json()["trial_available"] is False
    repeat = client_cabinet_client.post("/api/v1/clients/me/trial-subscription", headers=_auth_headers(linked_token))
    assert repeat.status_code == 400
    assert repeat.json()["detail"] == "Trial subscription already activated"
