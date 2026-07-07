from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
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
from app.models.partner import Partner, PartnerQrLink
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
