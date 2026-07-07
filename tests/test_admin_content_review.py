from __future__ import annotations

from collections.abc import Generator

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
from app.models.partner import Partner, PartnerOffer, PartnerPhoto
from app.models.user import AdminUser, UserRole


@pytest.fixture()
def admin_client() -> Generator[TestClient, None, None]:
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
                password_hash=hash_password("StrongPassword123"),
                role=UserRole.ADMIN.value,
                is_active=True,
            )
        )
        city = City(name="Москва", slug="moscow", is_active=True, sort_order=10)
        session.add(city)
        session.flush()
        partner = Partner(
            city_id=city.id,
            category_slug="krasota",
            name="Alpha Beauty",
            is_active=True,
            sort_order=20,
        )
        session.add(partner)
        session.flush()
        session.add_all(
            [
                PartnerOffer(
                    partner_id=partner.id,
                    title="Pending offer",
                    description="Pending description",
                    benefit_text="Pending benefit",
                    image_url="/uploads/partners/1/offers/1/offer.webp",
                    is_active=False,
                    sort_order=10,
                ),
                PartnerOffer(
                    partner_id=partner.id,
                    title="Active offer",
                    is_active=True,
                    sort_order=20,
                ),
                PartnerPhoto(
                    partner_id=partner.id,
                    url="/uploads/partners/1/photos/pending.webp",
                    alt_text="Pending photo",
                    sort_order=5,
                    is_active=False,
                ),
                PartnerPhoto(
                    partner_id=partner.id,
                    url="/uploads/partners/1/photos/active.webp",
                    alt_text="Active photo",
                    sort_order=6,
                    is_active=True,
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
def admin_token(admin_client: TestClient) -> str:
    response = admin_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "StrongPassword123"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_admin_content_review_requires_admin_auth(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/admin/content-review")

    assert response.status_code == 401


def test_admin_content_review_returns_inactive_offers_and_photos(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/content-review", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert [offer["title"] for offer in data["offers"]] == ["Pending offer"]
    assert data["offers"][0]["partner_id"] == 1
    assert data["offers"][0]["partner_name"] == "Alpha Beauty"
    assert data["offers"][0]["benefit_text"] == "Pending benefit"
    assert data["offers"][0]["description"] == "Pending description"
    assert data["offers"][0]["image_url"] == "/uploads/partners/1/offers/1/offer.webp"
    assert data["offers"][0]["created_at"]
    assert [photo["alt_text"] for photo in data["photos"]] == ["Pending photo"]
    assert data["photos"][0]["partner_id"] == 1
    assert data["photos"][0]["partner_name"] == "Alpha Beauty"
    assert data["photos"][0]["url"] == "/uploads/partners/1/photos/pending.webp"
    assert data["photos"][0]["sort_order"] == 5
    assert data["photos"][0]["created_at"]


def test_admin_content_review_excludes_active_content(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/content-review", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert "Active offer" not in [offer["title"] for offer in data["offers"]]
    assert "Active photo" not in [photo["alt_text"] for photo in data["photos"]]


def test_admin_content_review_activation_removes_items(admin_client: TestClient, admin_token: str) -> None:
    headers = _auth_headers(admin_token)

    offer_response = admin_client.patch("/api/v1/admin/offers/1", headers=headers, json={"is_active": True})
    photo_response = admin_client.patch("/api/v1/admin/partner-photos/1", headers=headers, json={"is_active": True})
    review_response = admin_client.get("/api/v1/admin/content-review", headers=headers)

    assert offer_response.status_code == 200
    assert photo_response.status_code == 200
    assert review_response.status_code == 200
    assert review_response.json() == {"offers": [], "photos": []}
