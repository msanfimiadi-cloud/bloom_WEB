from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all SQLAlchemy models for test metadata
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.city import City
from app.models.client import ClientProfile
from app.models.lead import LeadClick
from app.models.partner import Partner, PartnerOffer, PartnerQrLink
from app.models.user import AdminUser, User, UserRole
from app.models.verification import PrivilegeVerificationSession, PrivilegeVerificationStatus


@pytest.fixture()
def analytics_client() -> Generator[TestClient, None, None]:
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
        partner_user = User(
            email="partner@example.com",
            phone="+79990000001",
            password_hash=hash_password("PartnerPassword123"),
            role=UserRole.PARTNER.value,
            is_active=True,
        )
        other_partner_user = User(
            email="other-partner@example.com",
            phone="+79990000002",
            password_hash=hash_password("OtherPartnerPassword123"),
            role=UserRole.PARTNER.value,
            is_active=True,
        )
        zero_partner_user = User(
            email="zero-partner@example.com",
            phone="+79990000003",
            password_hash=hash_password("ZeroPartnerPassword123"),
            role=UserRole.PARTNER.value,
            is_active=True,
        )
        client_user = User(
            email="client@example.com",
            phone="+79990000004",
            password_hash=hash_password("ClientPassword123"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        other_client_user = User(
            email="other-client@example.com",
            phone="+79990000005",
            password_hash=hash_password("OtherClientPassword123"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        session.add_all([admin, partner_user, other_partner_user, zero_partner_user, client_user, other_client_user])
        session.flush()

        city = City(name="Москва", slug="moscow", is_active=True, sort_order=10)
        session.add(city)
        session.flush()

        client_profile = ClientProfile(user_id=client_user.id, full_name="Client One", is_active=True)
        other_client_profile = ClientProfile(user_id=other_client_user.id, full_name="Client Two", is_active=True)
        session.add_all([client_profile, other_client_profile])
        session.flush()

        partner = Partner(
            city_id=city.id,
            owner_user_id=partner_user.id,
            category_slug="krasota",
            name="Alpha Beauty",
            is_active=True,
            is_verified=True,
            sort_order=10,
        )
        other_partner = Partner(
            city_id=city.id,
            owner_user_id=other_partner_user.id,
            category_slug="fitnes-yoga",
            name="Beta Yoga",
            is_active=True,
            is_verified=True,
            sort_order=20,
        )
        zero_partner = Partner(
            city_id=city.id,
            owner_user_id=zero_partner_user.id,
            category_slug="zdorove",
            name="Zero Spa",
            is_active=True,
            is_verified=False,
            sort_order=30,
        )
        session.add_all([partner, other_partner, zero_partner])
        session.flush()
        session.add(PartnerOffer(partner_id=partner.id, title="Permanent offer", is_active=True))

        alpha_qr_one = PartnerQrLink(partner_id=partner.id, slug="alpha-one")
        alpha_qr_two = PartnerQrLink(partner_id=partner.id, slug="alpha-two")
        beta_qr = PartnerQrLink(partner_id=other_partner.id, slug="beta-one")
        session.add_all([alpha_qr_one, alpha_qr_two, beta_qr])
        session.flush()

        session.add_all(
            [
                LeadClick(partner_id=partner.id, qr_link_id=alpha_qr_one.id, source="qr", session_id="alpha-1"),
                LeadClick(partner_id=partner.id, qr_link_id=alpha_qr_one.id, source="qr", session_id="alpha-2"),
                LeadClick(partner_id=partner.id, qr_link_id=alpha_qr_two.id, source="qr", session_id="alpha-3"),
                LeadClick(partner_id=other_partner.id, qr_link_id=beta_qr.id, source="qr", session_id="beta-1"),
                LeadClick(partner_id=None, qr_link_id=None, source="catalog", session_id="anonymous"),
            ]
        )

        now = datetime.now(timezone.utc)
        session.add_all(
            [
                PrivilegeVerificationSession(
                    client_id=client_profile.id,
                    partner_id=partner.id,
                    code="111111",
                    status=PrivilegeVerificationStatus.active.value,
                    source="test",
                    expires_at=now + timedelta(minutes=10),
                    created_at=now,
                ),
                PrivilegeVerificationSession(
                    client_id=client_profile.id,
                    partner_id=partner.id,
                    code="222222",
                    status=PrivilegeVerificationStatus.active.value,
                    source="test",
                    expires_at=now - timedelta(minutes=10),
                    created_at=now,
                ),
                PrivilegeVerificationSession(
                    client_id=client_profile.id,
                    partner_id=partner.id,
                    code="333333",
                    status=PrivilegeVerificationStatus.expired.value,
                    source="test",
                    expires_at=now + timedelta(minutes=10),
                    created_at=now,
                ),
                PrivilegeVerificationSession(
                    client_id=client_profile.id,
                    partner_id=partner.id,
                    code="444444",
                    status=PrivilegeVerificationStatus.confirmed.value,
                    source="test",
                    expires_at=now + timedelta(minutes=10),
                    confirmed_at=now,
                    created_at=now,
                ),
                PrivilegeVerificationSession(
                    client_id=client_profile.id,
                    partner_id=partner.id,
                    code="555555",
                    status=PrivilegeVerificationStatus.cancelled.value,
                    source="test",
                    expires_at=now + timedelta(minutes=10),
                    created_at=now,
                ),
                PrivilegeVerificationSession(
                    client_id=other_client_profile.id,
                    partner_id=other_partner.id,
                    code="666666",
                    status=PrivilegeVerificationStatus.confirmed.value,
                    source="test",
                    expires_at=now + timedelta(minutes=10),
                    confirmed_at=now,
                    created_at=now,
                ),
                PrivilegeVerificationSession(
                    client_id=other_client_profile.id,
                    partner_id=other_partner.id,
                    code="777777",
                    status=PrivilegeVerificationStatus.active.value,
                    source="test",
                    expires_at=now + timedelta(minutes=10),
                    created_at=now,
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
            client.session_factory = session_factory  # type: ignore[attr-defined]
            yield client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPassword123"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _user_login(client: TestClient, login: str, password: str) -> str:
    response = client.post("/api/v1/auth/user-login", json={"login": login, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _partner_token(client: TestClient) -> str:
    return _user_login(client, "partner@example.com", "PartnerPassword123")


def _other_partner_token(client: TestClient) -> str:
    return _user_login(client, "other-partner@example.com", "OtherPartnerPassword123")


def _client_token(client: TestClient) -> str:
    return _user_login(client, "client@example.com", "ClientPassword123")


def test_partner_sees_only_own_analytics(analytics_client: TestClient) -> None:
    response = analytics_client.get(
        "/api/v1/partners/me/analytics",
        headers=_auth_headers(_partner_token(analytics_client)),
    )

    assert response.status_code == 200
    assert response.json() == {
        "partner_id": 1,
        "partner_name": "Alpha Beauty",
        "qr_links_count": 2,
        "lead_clicks_count": 3,
        "privileges_created_count": 5,
        "privileges_confirmed_count": 1,
        "active_privileges_count": 1,
        "expired_privileges_count": 2,
        "conversion_to_privilege_percent": 166.7,
        "confirmation_rate_percent": 20.0,
    }


def test_admin_sees_selected_partner_analytics(analytics_client: TestClient) -> None:
    response = analytics_client.get(
        "/api/v1/admin/partners/2/analytics",
        headers=_auth_headers(_admin_token(analytics_client)),
    )

    assert response.status_code == 200
    assert response.json() == {
        "partner_id": 2,
        "partner_name": "Beta Yoga",
        "qr_links_count": 1,
        "lead_clicks_count": 1,
        "privileges_created_count": 2,
        "privileges_confirmed_count": 1,
        "active_privileges_count": 1,
        "expired_privileges_count": 0,
        "conversion_to_privilege_percent": 200.0,
        "confirmation_rate_percent": 50.0,
    }


def test_zero_denominators_return_zero_percentages(analytics_client: TestClient) -> None:
    response = analytics_client.get(
        "/api/v1/admin/partners/3/analytics",
        headers=_auth_headers(_admin_token(analytics_client)),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["partner_id"] == 3
    assert data["qr_links_count"] == 0
    assert data["lead_clicks_count"] == 0
    assert data["privileges_created_count"] == 0
    assert data["conversion_to_privilege_percent"] == 0.0
    assert data["confirmation_rate_percent"] == 0.0


def test_other_partner_token_gets_other_partner_scope(analytics_client: TestClient) -> None:
    response = analytics_client.get(
        "/api/v1/partners/me/analytics",
        headers=_auth_headers(_other_partner_token(analytics_client)),
    )

    assert response.status_code == 200
    assert response.json()["partner_id"] == 2
    assert response.json()["partner_name"] == "Beta Yoga"
    assert response.json()["lead_clicks_count"] == 1


def test_partner_endpoint_rejects_client_or_missing_partner_role(analytics_client: TestClient) -> None:
    response = analytics_client.get(
        "/api/v1/partners/me/analytics",
        headers=_auth_headers(_client_token(analytics_client)),
    )

    assert response.status_code == 403


def test_admin_endpoint_rejects_non_admin(analytics_client: TestClient) -> None:
    response = analytics_client.get(
        "/api/v1/admin/partners/1/analytics",
        headers=_auth_headers(_partner_token(analytics_client)),
    )

    assert response.status_code in {401, 403}


def test_admin_unknown_partner_returns_404(analytics_client: TestClient) -> None:
    response = analytics_client.get(
        "/api/v1/admin/partners/999/analytics",
        headers=_auth_headers(_admin_token(analytics_client)),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Partner not found"


def test_admin_reset_starts_new_statistics_without_deleting_business_data(
    analytics_client: TestClient,
) -> None:
    admin_token = _admin_token(analytics_client)

    reset_response = analytics_client.post(
        "/api/v1/admin/partners/1/analytics/reset",
        headers=_auth_headers(admin_token),
    )

    assert reset_response.status_code == 200
    reset_data = reset_response.json()
    assert reset_data["qr_links_count"] == 2
    assert reset_data["lead_clicks_count"] == 0
    assert reset_data["privileges_created_count"] == 0
    assert reset_data["privileges_confirmed_count"] == 0

    session_factory = analytics_client.session_factory  # type: ignore[attr-defined]
    with session_factory() as session:
        partner = session.get(Partner, 1)
        assert partner is not None
        assert partner.analytics_reset_at is not None
        assert session.execute(select(func.count()).select_from(PartnerOffer)).scalar_one() == 1
        assert session.execute(select(func.count()).select_from(PrivilegeVerificationSession)).scalar_one() == 7

        reset_at = partner.analytics_reset_at
        qr_link_id = session.execute(
            select(PartnerQrLink.id).where(PartnerQrLink.partner_id == partner.id).limit(1)
        ).scalar_one()
        client_id = session.execute(
            select(ClientProfile.id).order_by(ClientProfile.id.asc()).limit(1)
        ).scalar_one()
        session.add(
            LeadClick(
                partner_id=partner.id,
                qr_link_id=qr_link_id,
                source="qr",
                session_id="after-reset",
                created_at=reset_at + timedelta(seconds=1),
            )
        )
        session.add(
            PrivilegeVerificationSession(
                client_id=client_id,
                partner_id=partner.id,
                code="888888",
                status=PrivilegeVerificationStatus.confirmed.value,
                source="test",
                expires_at=reset_at + timedelta(minutes=10),
                confirmed_at=reset_at + timedelta(seconds=1),
                saving_amount=Decimal("125.00"),
                created_at=reset_at + timedelta(seconds=1),
            )
        )
        session.commit()

    analytics_response = analytics_client.get(
        "/api/v1/admin/partners/1/analytics",
        headers=_auth_headers(admin_token),
    )
    assert analytics_response.status_code == 200
    assert analytics_response.json()["lead_clicks_count"] == 1
    assert analytics_response.json()["privileges_created_count"] == 1
    assert analytics_response.json()["privileges_confirmed_count"] == 1

    partner_response = analytics_client.get(
        "/api/v1/partner/me",
        headers=_auth_headers(_partner_token(analytics_client)),
    )
    assert partner_response.status_code == 200
    assert partner_response.json()["stats"]["confirmed_total"] == 1
    assert partner_response.json()["stats"]["unique_clients_total"] == 1
    assert Decimal(partner_response.json()["stats"]["savings_month"]) == Decimal("125.00")


def test_partner_cannot_reset_own_statistics(analytics_client: TestClient) -> None:
    response = analytics_client.post(
        "/api/v1/admin/partners/1/analytics/reset",
        headers=_auth_headers(_partner_token(analytics_client)),
    )

    assert response.status_code in {401, 403}


def test_admin_statistics_counts_partner_views_offers_and_contact_clicks(analytics_client: TestClient) -> None:
    client_headers = _auth_headers(_client_token(analytics_client))
    for payload in (
        {"event_type": "partner_view", "partner_id": 1},
        {"event_type": "partner_view", "partner_id": 1},
        {"event_type": "offer_view", "partner_id": 1, "offer_id": 1},
        {"event_type": "offer_select", "partner_id": 1, "offer_id": 1},
        {"event_type": "contact_click", "partner_id": 1, "target": "Запись онлайн"},
    ):
        response = analytics_client.post("/api/v1/clients/analytics/events", json=payload, headers=client_headers)
        assert response.status_code == 201, response.text

    response = analytics_client.get(
        "/api/v1/admin/statistics?period=month", headers=_auth_headers(_admin_token(analytics_client))
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["summary"]["partner_views"] == 2
    assert data["summary"]["unique_partner_viewers"] == 1
    assert data["summary"]["offer_views"] == 1
    assert data["summary"]["offer_selections"] == 1
    assert data["summary"]["contact_clicks"] == 1
    partner = next(item for item in data["partners"] if item["partner_id"] == 1)
    assert partner["views"] == 2
    assert partner["codes_issued"] == 5
    assert partner["contact_click_breakdown"] == {"Запись онлайн": 1}
    assert data["offers"][0]["offer_title"] == "Permanent offer"
    assert data["offers"][0]["selections"] == 1
    assert len(data["recent_events"]) == 5


def test_admin_statistics_supports_partner_filter_and_rejects_inverted_dates(analytics_client: TestClient) -> None:
    headers = _auth_headers(_admin_token(analytics_client))
    filtered = analytics_client.get("/api/v1/admin/statistics?partner_id=2", headers=headers)
    assert filtered.status_code == 200, filtered.text
    assert [item["partner_id"] for item in filtered.json()["partners"]] == [2]

    invalid = analytics_client.get(
        "/api/v1/admin/statistics?period=custom&date_from=2026-09-02&date_to=2026-09-01",
        headers=headers,
    )
    assert invalid.status_code == 422


def test_admin_statistics_is_not_available_to_partners(analytics_client: TestClient) -> None:
    response = analytics_client.get(
        "/api/v1/admin/statistics", headers=_auth_headers(_partner_token(analytics_client))
    )
    assert response.status_code in {401, 403}


def test_client_analytics_validates_offer_belongs_to_partner(analytics_client: TestClient) -> None:
    response = analytics_client.post(
        "/api/v1/clients/analytics/events",
        json={"event_type": "offer_select", "partner_id": 2, "offer_id": 1},
        headers=_auth_headers(_client_token(analytics_client)),
    )
    assert response.status_code == 404
