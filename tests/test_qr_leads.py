from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all SQLAlchemy models for test metadata
from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.city import City
from app.models.lead import LeadClick
from app.models.partner import Partner, PartnerQrLink
from app.models.user import AdminUser, User, UserRole


@pytest.fixture()
def qr_client() -> Generator[TestClient, None, None]:
    object.__setattr__(settings, "WEB_PUBLIC_URL", "https://bloomclub.test")
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
        owner = User(
            email="partner@example.com",
            phone="+79990000001",
            password_hash=hash_password("PartnerPassword123"),
            role=UserRole.PARTNER.value,
            is_active=True,
        )
        other_owner = User(
            email="other@example.com",
            phone="+79990000002",
            password_hash=hash_password("OtherPassword123"),
            role=UserRole.PARTNER.value,
            is_active=True,
        )
        session.add_all([owner, other_owner])
        session.flush()
        city = City(name="Москва", slug="moscow", is_active=True, sort_order=10)
        other_city = City(name="Санкт-Петербург", slug="spb", is_active=True, sort_order=20)
        session.add_all([city, other_city])
        session.flush()
        partner = Partner(
            city_id=city.id,
            owner_user_id=owner.id,
            category_slug="krasota",
            name="Alpha Beauty",
            is_active=True,
            is_verified=True,
            sort_order=10,
        )
        other_partner = Partner(
            city_id=other_city.id,
            owner_user_id=other_owner.id,
            category_slug="fitnes-yoga",
            name="Beta Yoga",
            is_active=True,
            is_verified=False,
            sort_order=20,
        )
        session.add_all([partner, other_partner])
        session.flush()
        session.add_all(
            [
                PartnerQrLink(partner_id=partner.id, slug="alpha-first", target_url="https://alpha.test/first"),
                PartnerQrLink(partner_id=partner.id, slug="alpha-second"),
                PartnerQrLink(partner_id=other_partner.id, slug="beta-first", target_url="https://beta.test"),
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


@pytest.fixture()
def admin_token(qr_client: TestClient) -> str:
    response = qr_client.post(
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


def _partner_token(client: TestClient) -> str:
    return _user_login(client, "partner@example.com", "PartnerPassword123")


def _other_partner_token(client: TestClient) -> str:
    return _user_login(client, "other@example.com", "OtherPassword123")


def _session(client: TestClient) -> Session:
    return client.session_factory()  # type: ignore[attr-defined,no-any-return]


def test_admin_post_qr_link_generates_slug_and_qr_url(qr_client: TestClient, admin_token: str) -> None:
    response = qr_client.post(
        "/api/v1/admin/partners/1/qr-links",
        json={"target_url": "https://alpha.test/generated"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["partner_id"] == 1
    assert data["slug"].startswith("partner-1-")
    assert data["qr_url"] == f"https://bloomclub.test/r/p/{data['slug']}"
    assert data["partner_name"] == "Alpha Beauty"


def test_admin_post_qr_link_custom_slug_normalizes_and_returns_qr_url(
    qr_client: TestClient,
    admin_token: str,
) -> None:
    response = qr_client.post(
        "/api/v1/admin/partners/1/qr-links",
        json={"slug": "  Custom_Slug-42  "},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["slug"] == "custom_slug-42"
    assert response.json()["qr_url"] == "https://bloomclub.test/r/p/custom_slug-42"


def test_admin_post_duplicate_slug_returns_409(qr_client: TestClient, admin_token: str) -> None:
    response = qr_client.post(
        "/api/v1/admin/partners/1/qr-links",
        json={"slug": "alpha-first"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "QR slug already exists"


def test_admin_post_invalid_slug_returns_400(qr_client: TestClient, admin_token: str) -> None:
    response = qr_client.post(
        "/api/v1/admin/partners/1/qr-links",
        json={"slug": "bad slug!"},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid QR slug"


def test_admin_get_partner_qr_links_returns_only_that_partner_ordered(
    qr_client: TestClient,
    admin_token: str,
) -> None:
    response = qr_client.get("/api/v1/admin/partners/1/qr-links", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    assert [item["slug"] for item in response.json()] == ["alpha-first", "alpha-second"]


def test_admin_patch_qr_link_updates_target_url_and_is_active(qr_client: TestClient, admin_token: str) -> None:
    response = qr_client.patch(
        "/api/v1/admin/qr-links/1",
        json={"target_url": "https://alpha.test/updated", "is_active": False},
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["target_url"] == "https://alpha.test/updated"
    assert data["is_active"] is False


def test_partner_get_me_qr_links_returns_only_own_links(qr_client: TestClient) -> None:
    token = _partner_token(qr_client)

    response = qr_client.get("/api/v1/partners/me/qr-links", headers=_auth_headers(token))

    assert response.status_code == 200
    assert [item["slug"] for item in response.json()] == ["alpha-first", "alpha-second"]


def test_public_redirect_records_lead_click_and_redirects(qr_client: TestClient) -> None:
    response = qr_client.get(
        "/r/p/alpha-first?session_id=s1&utm_source=vk&utm_medium=cpc&utm_campaign=may",
        headers={"referer": "https://ref.example", "user-agent": "UnitTestAgent/1.0"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == "https://alpha.test/first"
    with _session(qr_client) as session:
        click = session.execute(select(LeadClick)).scalar_one()
        assert click.partner_id == 1
        assert click.qr_link_id == 1
        assert click.city_id == 1
        assert click.source == "web_qr"
        assert click.session_id == "s1"
        assert click.referer == "https://ref.example"
        assert click.utm_source == "vk"
        assert click.utm_medium == "cpc"
        assert click.utm_campaign == "may"


def test_public_inactive_or_missing_slug_returns_404(qr_client: TestClient, admin_token: str) -> None:
    qr_client.patch(
        "/api/v1/admin/qr-links/1",
        json={"is_active": False},
        headers=_auth_headers(admin_token),
    )

    inactive = qr_client.get("/r/p/alpha-first", follow_redirects=False)
    missing = qr_client.get("/r/p/missing", follow_redirects=False)

    assert inactive.status_code == 404
    assert inactive.json()["detail"] == "QR link not found"
    assert missing.status_code == 404


def test_lead_click_hashes_ip_and_user_agent_without_raw_values(qr_client: TestClient) -> None:
    response = qr_client.get(
        "/r/p/alpha-first",
        headers={"user-agent": "RawAgent/2.0"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    with _session(qr_client) as session:
        click = session.execute(select(LeadClick)).scalar_one()
        assert click.ip_hash is not None
        assert len(click.ip_hash) == 64
        assert click.user_agent_hash is not None
        assert len(click.user_agent_hash) == 64
        assert click.user_agent_hash != "RawAgent/2.0"
        assert not hasattr(click, "ip_address")
        assert not hasattr(click, "user_agent")


def test_admin_lead_stats_returns_aggregate_clicks(qr_client: TestClient, admin_token: str) -> None:
    qr_client.get("/r/p/alpha-first", follow_redirects=False)
    qr_client.get("/r/p/alpha-first", follow_redirects=False)
    qr_client.get("/r/p/beta-first", follow_redirects=False)

    response = qr_client.get("/api/v1/admin/leads/partners", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert [(item["partner_id"], item["qr_slug"], item["total_clicks"]) for item in data] == [
        (1, "alpha-first", 2),
        (2, "beta-first", 1),
    ]
    assert data[0]["city_name"] == "Москва"


def test_partner_lead_stats_returns_only_own_partner_stats(qr_client: TestClient) -> None:
    token = _partner_token(qr_client)
    qr_client.get("/r/p/alpha-first", follow_redirects=False)
    qr_client.get("/r/p/alpha-first", follow_redirects=False)
    qr_client.get("/r/p/beta-first", follow_redirects=False)

    response = qr_client.get("/api/v1/partners/me/leads", headers=_auth_headers(token))

    assert response.status_code == 200
    assert [(item["partner_id"], item["qr_slug"], item["total_clicks"]) for item in response.json()] == [
        (1, "alpha-first", 2),
    ]


def test_partner_cannot_see_other_partner_lead_stats(qr_client: TestClient) -> None:
    other_token = _other_partner_token(qr_client)
    qr_client.get("/r/p/alpha-first", follow_redirects=False)
    qr_client.get("/r/p/beta-first", follow_redirects=False)

    response = qr_client.get("/api/v1/partners/me/leads", headers=_auth_headers(other_token))

    assert response.status_code == 200
    assert [(item["partner_id"], item["qr_slug"], item["total_clicks"]) for item in response.json()] == [
        (2, "beta-first", 1),
    ]
