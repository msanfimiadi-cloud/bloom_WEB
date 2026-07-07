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
from app.core.categories import get_women_club_categories
from app.models.category import Category
from app.models.city import City
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
        session.add_all(
            [
                City(name="Поздний город", slug="late-city", is_active=True, sort_order=20),
                City(name="Ранний город", slug="early-city", is_active=True, sort_order=10),
            ]
        )
        session.add_all(
            [
                Category(
                    name=category["title"],
                    slug=category["slug"],
                    is_active=category["is_active"],
                    sort_order=category["sort_order"],
                )
                for category in get_women_club_categories()
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


def test_admin_cities_returns_401_without_token(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/admin/cities")

    assert response.status_code == 401


def test_admin_categories_returns_401_without_token(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/admin/categories")

    assert response.status_code == 401


def test_admin_categories_returns_expected_categories(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/categories", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    titles = [category["title"] for category in data]
    assert "Красота" in titles
    assert "Маникюр / педикюр" in titles
    assert "Другое" in titles
    assert [category["sort_order"] for category in data] == sorted(
        category["sort_order"] for category in data
    )
    assert data[0]["slug"] == "krasota"
    assert data[0]["name"] == "Красота"
    assert data[0]["title"] == "Красота"
    assert data[0]["is_active"] is True
    assert data[0]["sort_order"] == 1
    assert data[-1]["slug"] == "drugoe"


def test_admin_category_create_success(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/categories",
        headers=_auth_headers(admin_token),
        json={"name": "  Новая категория  ", "slug": "  new-category  ", "is_active": True, "sort_order": 42},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"]
    assert data["name"] == "Новая категория"
    assert data["title"] == "Новая категория"
    assert data["slug"] == "new-category"
    assert data["is_active"] is True
    assert data["sort_order"] == 42

    list_response = admin_client.get("/api/v1/admin/categories", headers=_auth_headers(admin_token))
    assert "new-category" in [category["slug"] for category in list_response.json()]


def test_admin_category_create_duplicate_slug_returns_409(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/categories",
        headers=_auth_headers(admin_token),
        json={"name": "Дубликат", "slug": "krasota"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Category with this slug already exists"


def test_admin_category_patch_updates_name_slug_and_active_flag(admin_client: TestClient, admin_token: str) -> None:
    categories_response = admin_client.get("/api/v1/admin/categories", headers=_auth_headers(admin_token))
    category_id = categories_response.json()[0]["id"]

    response = admin_client.patch(
        f"/api/v1/admin/categories/{category_id}",
        headers=_auth_headers(admin_token),
        json={
            "name": "  Обновленная категория  ",
            "slug": "  updated-category  ",
            "is_active": False,
            "sort_order": 77,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == category_id
    assert data["name"] == "Обновленная категория"
    assert data["title"] == "Обновленная категория"
    assert data["slug"] == "updated-category"
    assert data["is_active"] is False
    assert data["sort_order"] == 77


def test_admin_category_patch_missing_category_returns_404(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.patch(
        "/api/v1/admin/categories/9999",
        headers=_auth_headers(admin_token),
        json={"name": "Missing"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_admin_cities_returns_cities_ordered_by_sort_order(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/cities", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert [city["slug"] for city in data] == ["early-city", "late-city"]
    assert [city["sort_order"] for city in data] == [10, 20]


def test_admin_city_create_strips_values_and_creates_city(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/cities",
        headers=_auth_headers(admin_token),
        json={"name": "  Новый город  ", "slug": "  new-city  ", "is_active": False, "sort_order": 15},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"]
    assert data["name"] == "Новый город"
    assert data["slug"] == "new-city"
    assert data["is_active"] is False
    assert data["sort_order"] == 15


def test_admin_city_create_duplicate_returns_409(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/cities",
        headers=_auth_headers(admin_token),
        json={"name": "Ранний город", "slug": "unique-slug"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "City with this slug or name already exists"


def test_admin_city_patch_updates_city(admin_client: TestClient, admin_token: str) -> None:
    cities_response = admin_client.get("/api/v1/admin/cities", headers=_auth_headers(admin_token))
    city_id = cities_response.json()[0]["id"]

    response = admin_client.patch(
        f"/api/v1/admin/cities/{city_id}",
        headers=_auth_headers(admin_token),
        json={"name": "  Обновленный город  ", "slug": "  updated-city  ", "sort_order": 30},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == city_id
    assert data["name"] == "Обновленный город"
    assert data["slug"] == "updated-city"
    assert data["sort_order"] == 30


def test_admin_city_patch_duplicate_returns_409(admin_client: TestClient, admin_token: str) -> None:
    cities_response = admin_client.get("/api/v1/admin/cities", headers=_auth_headers(admin_token))
    city_id = cities_response.json()[0]["id"]

    response = admin_client.patch(
        f"/api/v1/admin/cities/{city_id}",
        headers=_auth_headers(admin_token),
        json={"slug": "late-city"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "City with this slug or name already exists"


def test_admin_city_patch_missing_city_returns_404(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.patch(
        "/api/v1/admin/cities/9999",
        headers=_auth_headers(admin_token),
        json={"name": "Missing"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "City not found"


def test_admin_me_still_works_with_admin_token(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/me", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    assert response.json() == {"id": 1, "email": "admin@example.com", "role": "admin", "legacy_content_write_enabled": True}


def _set_legacy_content_flag(value: bool) -> bool:
    from app.core.config import settings

    previous = settings.WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED
    object.__setattr__(settings, "WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED", value)
    return previous


def _restore_legacy_content_flag(previous: bool) -> None:
    from app.core.config import settings

    object.__setattr__(settings, "WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED", previous)


def test_admin_me_exposes_legacy_content_write_flag(admin_client: TestClient, admin_token: str) -> None:
    previous = _set_legacy_content_flag(False)
    try:
        response = admin_client.get("/api/v1/admin/me", headers=_auth_headers(admin_token))
    finally:
        _restore_legacy_content_flag(previous)

    assert response.status_code == 200
    assert response.json()["legacy_content_write_enabled"] is False


def test_legacy_content_write_flag_defaults_true() -> None:
    from app.core.config import Settings

    assert Settings().WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED is True


def test_admin_legacy_content_write_returns_403_when_flag_disabled(
    admin_client: TestClient, admin_token: str
) -> None:
    previous = _set_legacy_content_flag(False)
    try:
        response = admin_client.post(
            "/api/v1/admin/cities",
            headers=_auth_headers(admin_token),
            json={"name": "Тест", "slug": "test-city", "is_active": True, "sort_order": 30},
        )
    finally:
        _restore_legacy_content_flag(previous)

    assert response.status_code == 403
    assert "Legacy WEB content editing is disabled" in response.json()["detail"]


def test_admin_legacy_content_write_works_when_flag_enabled(
    admin_client: TestClient, admin_token: str
) -> None:
    previous = _set_legacy_content_flag(True)
    try:
        response = admin_client.post(
            "/api/v1/admin/cities",
            headers=_auth_headers(admin_token),
            json={"name": "Тест", "slug": "test-city", "is_active": True, "sort_order": 30},
        )
    finally:
        _restore_legacy_content_flag(previous)

    assert response.status_code == 200
    assert response.json()["slug"] == "test-city"


def test_admin_users_are_not_blocked_by_legacy_content_flag(
    admin_client: TestClient, admin_token: str
) -> None:
    previous = _set_legacy_content_flag(False)
    try:
        response = admin_client.post(
            "/api/v1/admin/users",
            headers=_auth_headers(admin_token),
            json={"email": "client@example.com", "password": "StrongPassword123", "role": "client", "is_active": True},
        )
    finally:
        _restore_legacy_content_flag(previous)

    assert response.status_code == 200
    assert response.json()["email"] == "client@example.com"
