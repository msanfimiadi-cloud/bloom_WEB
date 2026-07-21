from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import subprocess

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
from app.models.partner import Partner, PartnerOffer, PartnerQrLink
from app.models.user import AdminUser, User, UserRole
from app.models.verification import PrivilegeVerificationSession, PrivilegeVerificationStatus


@contextmanager
def _make_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    now = datetime.now(timezone.utc).replace(microsecond=0)
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
        session.add_all([admin, client_user, other_client_user, partner_user, other_partner_user])
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
            category_slug="beauty",
            name="Alpha Beauty",
            is_active=True,
            is_verified=True,
            created_at=now - timedelta(hours=8),
        )
        other_partner = Partner(
            city_id=city.id,
            owner_user_id=other_partner_user.id,
            category_slug="fitness",
            name="Beta Yoga",
            is_active=True,
            is_verified=True,
            created_at=now - timedelta(hours=7),
        )
        session.add_all([partner, other_partner])
        session.flush()

        offer = PartnerOffer(
            partner_id=partner.id,
            title="Alpha Offer",
            is_active=True,
            created_at=now - timedelta(hours=6),
        )
        other_offer = PartnerOffer(
            partner_id=other_partner.id,
            title="Beta Offer",
            is_active=True,
            created_at=now - timedelta(hours=5),
        )
        session.add_all([offer, other_offer])
        session.flush()
        for idx in range(105):
            session.add(
                PartnerOffer(
                    partner_id=partner.id,
                    title=f"Bulk Offer {idx}",
                    is_active=True,
                    created_at=now - timedelta(days=3) + timedelta(minutes=idx),
                )
            )

        qr_link = PartnerQrLink(partner_id=partner.id, slug="alpha-qr", created_at=now - timedelta(hours=4))
        other_qr_link = PartnerQrLink(
            partner_id=other_partner.id,
            slug="beta-qr",
            created_at=now - timedelta(hours=3),
        )
        session.add_all([qr_link, other_qr_link])
        session.flush()

        session.add_all(
            [
                LeadClick(
                    partner_id=partner.id,
                    qr_link_id=qr_link.id,
                    source="qr",
                    created_at=now - timedelta(minutes=30),
                ),
                LeadClick(
                    partner_id=other_partner.id,
                    qr_link_id=other_qr_link.id,
                    source="qr",
                    created_at=now - timedelta(minutes=20),
                ),
                PrivilegeVerificationSession(
                    client_id=client_profile.id,
                    partner_id=partner.id,
                    offer_id=offer.id,
                    code="111111",
                    status=PrivilegeVerificationStatus.confirmed.value,
                    source="web",
                    created_at=now - timedelta(hours=2),
                    confirmed_at=now - timedelta(hours=1),
                    expires_at=now + timedelta(minutes=10),
                ),
                PrivilegeVerificationSession(
                    client_id=client_profile.id,
                    partner_id=partner.id,
                    offer_id=offer.id,
                    code="222222",
                    status=PrivilegeVerificationStatus.active.value,
                    source="web",
                    created_at=now - timedelta(hours=10),
                    expires_at=now - timedelta(minutes=5),
                ),
                PrivilegeVerificationSession(
                    client_id=other_client_profile.id,
                    partner_id=other_partner.id,
                    offer_id=other_offer.id,
                    code="333333",
                    status=PrivilegeVerificationStatus.expired.value,
                    source="web",
                    created_at=now - timedelta(hours=9),
                    expires_at=now - timedelta(minutes=15),
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


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client: TestClient, login: str, password: str) -> str:
    response = client.post("/api/v1/auth/user-login", json={"login": login, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _admin_login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPassword123"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def test_client_sees_only_own_privilege_events() -> None:
    with _make_client() as client:
        token = _login(client, "client@example.com", "ClientPassword123")
        response = client.get("/api/v1/clients/me/activity", headers=_auth_headers(token))

    assert response.status_code == 200
    items = response.json()["items"]
    assert {item["client_name"] for item in items} == {"Client One"}
    assert {"privilege_created", "privilege_confirmed", "privilege_expired"}.issubset(
        {item["event_type"] for item in items}
    )


def test_partner_sees_own_privilege_qr_and_offer_events_only() -> None:
    with _make_client() as client:
        token = _login(client, "partner@example.com", "PartnerPassword123")
        response = client.get("/api/v1/partners/me/activity?limit=100", headers=_auth_headers(token))

    assert response.status_code == 200
    items = response.json()["items"]
    assert all(item["partner_name"] == "Alpha Beauty" for item in items)
    event_types = {item["event_type"] for item in items}
    assert {"privilege_created", "privilege_confirmed", "privilege_expired", "qr_clicked", "offer_created"}.issubset(
        event_types
    )
    assert "Beta Yoga" not in {item["partner_name"] for item in items}


def test_admin_sees_global_events_and_filters_work() -> None:
    with _make_client() as client:
        token = _admin_login(client)
        headers = _auth_headers(token)
        response = client.get("/api/v1/admin/activity?limit=100", headers=headers)
        event_type_response = client.get("/api/v1/admin/activity?event_type=qr_clicked", headers=headers)
        partner_response = client.get("/api/v1/admin/activity?partner_id=2&limit=100", headers=headers)

    assert response.status_code == 200
    items = response.json()["items"]
    assert {"Alpha Beauty", "Beta Yoga"}.issubset({item["partner_name"] for item in items})
    assert {"partner_created", "offer_created", "qr_link_created", "qr_clicked", "privilege_created"}.issubset(
        {item["event_type"] for item in items}
    )
    assert event_type_response.status_code == 200
    assert {item["event_type"] for item in event_type_response.json()["items"]} == {"qr_clicked"}
    assert partner_response.status_code == 200
    assert {item["partner_name"] for item in partner_response.json()["items"]} == {"Beta Yoga"}


def test_limit_is_capped_and_events_are_sorted_desc() -> None:
    with _make_client() as client:
        token = _login(client, "partner@example.com", "PartnerPassword123")
        response = client.get("/api/v1/partners/me/activity?limit=500", headers=_auth_headers(token))

    assert response.status_code == 200
    items = response.json()["items"]
    occurred_at = [item["occurred_at"] for item in items]
    assert len(items) == 100
    assert occurred_at == sorted(occurred_at, reverse=True)


def test_expired_event_includes_active_sessions_past_expires_at() -> None:
    with _make_client() as client:
        token = _login(client, "client@example.com", "ClientPassword123")
        response = client.get("/api/v1/clients/me/activity", headers=_auth_headers(token))

    assert response.status_code == 200
    expired_items = [item for item in response.json()["items"] if item["event_type"] == "privilege_expired"]
    assert any(item["status"] == PrivilegeVerificationStatus.active.value for item in expired_items)


def test_no_migrations_required_alembic_heads_unchanged() -> None:
    result = subprocess.run(["alembic", "heads"], check=True, capture_output=True, text=True)

    assert result.stdout.strip() == "20260721_0032 (head)"
