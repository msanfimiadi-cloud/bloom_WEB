from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all SQLAlchemy models for test metadata
from app.core.categories import get_women_club_categories
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.category import Category
from app.models.city import City
from app.models.partner import Partner
from app.models.user import AdminUser, User, UserRole


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
        city_one = City(name="Москва", slug="moscow", is_active=True, sort_order=10)
        city_two = City(name="Санкт-Петербург", slug="spb", is_active=True, sort_order=20)
        partner_owner = User(email="owner@example.com", role=UserRole.PARTNER.value, is_active=True)
        client_owner = User(email="client@example.com", role=UserRole.CLIENT.value, is_active=True)
        session.add_all([city_one, city_two, partner_owner, client_owner])
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
        session.flush()
        session.add_all(
            [
                Partner(
                    city_id=city_one.id,
                    owner_user_id=partner_owner.id,
                    category_slug="krasota",
                    name="Alpha Beauty",
                    is_active=True,
                    is_verified=True,
                    sort_order=20,
                ),
                Partner(
                    city_id=city_two.id,
                    category_slug="fitnes-yoga",
                    name="Beta Yoga",
                    is_active=False,
                    sort_order=10,
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


def _partner_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "city_id": 1,
        "category_slug": "krasota",
        "name": "Новый партнер",
        "description": "Описание",
        "address": "Адрес",
        "phone": "+79990000000",
        "website_url": "https://example.com",
        "social_url": "https://social.example.com",
        "working_hours": "10:00-20:00",
        "logo_url": "https://example.com/logo.png",
        "cover_url": "https://example.com/cover.png",
        "is_active": True,
        "is_verified": False,
        "sort_order": 5,
    }
    payload.update(overrides)
    return payload


def test_admin_partners_returns_401_without_token(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/admin/partners")

    assert response.status_code == 401


def test_admin_partners_returns_list_ordered_with_admin_token(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/partners", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert [partner["name"] for partner in data] == ["Beta Yoga", "Alpha Beauty"]
    assert [partner["sort_order"] for partner in data] == [10, 20]
    assert data[0]["city_name"] == "Санкт-Петербург"
    assert data[1]["owner_email"] == "owner@example.com"
    assert isinstance(data[0]["categories"], list)
    assert isinstance(data[0]["category_ids"], list)
    assert isinstance(data[0]["category_slugs"], list)


def test_admin_partner_create_with_valid_city(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json=_partner_payload(name="  Новый партнер  ", description="  Описание  "),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"]
    assert data["city_id"] == 1
    assert data["name"] == "Новый партнер"
    assert data["description"] == "Описание"
    assert data["city_name"] == "Москва"


def test_admin_partner_create_missing_city_returns_404(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json=_partner_payload(city_id=9999),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "City not found"


def test_admin_partner_create_empty_name_returns_400(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json=_partner_payload(name="   "),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Partner name must not be empty"


def test_admin_partner_create_non_partner_owner_returns_400(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json=_partner_payload(owner_user_id=2),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Owner user must have partner role"


def test_admin_partner_create_partner_owner_succeeds_with_owner_email(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json=_partner_payload(owner_user_id=1),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["owner_user_id"] == 1
    assert data["owner_email"] == "owner@example.com"


def test_admin_partner_create_unknown_category_returns_400(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json=_partner_payload(category_slug="unknown-category"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown category slug"


def test_admin_partner_create_update_and_list_persists_admin_fields(admin_client: TestClient, admin_token: str) -> None:
    create_response = admin_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json=_partner_payload(name="Regression Partner", owner_user_id=1, sort_order=77, is_verified=True),
    )
    assert create_response.status_code == 200
    created = create_response.json()

    partner_id = created["id"]
    update_response = admin_client.patch(
        f"/api/v1/admin/partners/{partner_id}",
        headers=_auth_headers(admin_token),
        json={
            "name": "Regression Partner Updated",
            "city_id": 2,
            "owner_user_id": 1,
            "sort_order": 99,
            "is_active": False,
            "is_verified": True,
            "category_slug": "fitnes-yoga",
            "phone": "+79991112233",
            "website_url": "https://updated.example.com",
            "social_url": "https://social.updated.example.com",
            "description": "Updated description",
            "address": "Updated address",
            "working_hours": "09:00-21:00",
            "logo_url": "https://updated.example.com/logo.png",
            "cover_url": "https://updated.example.com/cover.png",
        },
    )
    assert update_response.status_code == 200

    get_response = admin_client.get(f"/api/v1/admin/partners/{partner_id}", headers=_auth_headers(admin_token))
    assert get_response.status_code == 200
    partner = get_response.json()
    assert partner["name"] == "Regression Partner Updated"
    assert partner["city_id"] == 2
    assert partner["is_active"] is False
    assert partner["is_verified"] is True
    assert partner["sort_order"] == 99
    assert partner["phone"] == "+79991112233"
    assert partner["website_url"] == "https://updated.example.com"

    list_response = admin_client.get("/api/v1/admin/partners", headers=_auth_headers(admin_token))
    assert list_response.status_code == 200
    saved = next(item for item in list_response.json() if item["id"] == partner_id)
    assert saved["name"] == "Regression Partner Updated"
    assert saved["city_id"] == 2
    assert saved["sort_order"] == 99
    assert saved["is_active"] is False
    assert saved["is_verified"] is True



def test_admin_partner_create_update_and_list_preserves_multiple_categories(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    category_response = admin_client.get("/api/v1/admin/categories", headers=_auth_headers(admin_token))
    assert category_response.status_code == 200
    categories_by_slug = {category["slug"]: category for category in category_response.json()}
    create_category_ids = [
        categories_by_slug["krasota"]["id"],
        categories_by_slug["manikyur-pedikyur"]["id"],
        categories_by_slug["brovi-resnitsy"]["id"],
        categories_by_slug["kosmetologiya"]["id"],
    ]

    create_response = admin_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json=_partner_payload(name="Multi Category Beauty", category_ids=create_category_ids),
    )
    assert create_response.status_code == 200
    created = create_response.json()
    partner_id = created["id"]
    assert created["category_ids"] == create_category_ids
    assert created["category_slugs"] == ["krasota", "manikyur-pedikyur", "brovi-resnitsy", "kosmetologiya"]
    assert [category["slug"] for category in created["categories"]] == created["category_slugs"]

    update_category_ids = [
        categories_by_slug["manikyur-pedikyur"]["id"],
        categories_by_slug["brovi-resnitsy"]["id"],
        categories_by_slug["kosmetologiya"]["id"],
    ]
    update_response = admin_client.patch(
        f"/api/v1/admin/partners/{partner_id}",
        headers=_auth_headers(admin_token),
        json={"category_ids": update_category_ids},
    )
    assert update_response.status_code == 200
    assert update_response.json()["category_ids"] == update_category_ids

    refetch_response = admin_client.get(f"/api/v1/admin/partners/{partner_id}", headers=_auth_headers(admin_token))
    assert refetch_response.status_code == 200
    refetched = refetch_response.json()
    assert refetched["category_ids"] == update_category_ids
    assert refetched["category_slugs"] == ["manikyur-pedikyur", "brovi-resnitsy", "kosmetologiya"]
    assert [category["slug"] for category in refetched["categories"]] == refetched["category_slugs"]

    list_response = admin_client.get("/api/v1/admin/partners", headers=_auth_headers(admin_token))
    assert list_response.status_code == 200
    listed = next(partner for partner in list_response.json() if partner["id"] == partner_id)
    assert listed["category_ids"] == update_category_ids
    assert [category["slug"] for category in listed["categories"]] == [
        "manikyur-pedikyur",
        "brovi-resnitsy",
        "kosmetologiya",
    ]

    manicure_filter_response = admin_client.get(
        "/api/v1/admin/partners?category_slug=manikyur-pedikyur",
        headers=_auth_headers(admin_token),
    )
    assert manicure_filter_response.status_code == 200
    assert "Multi Category Beauty" in [partner["name"] for partner in manicure_filter_response.json()]

def test_admin_partner_get_returns_partner_with_city_name(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/partners/1", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Alpha Beauty"
    assert data["city_name"] == "Москва"



def test_admin_partner_patch_replaces_categories_with_smaller_set_and_removes_unchecked(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    category_response = admin_client.get("/api/v1/admin/categories", headers=_auth_headers(admin_token))
    assert category_response.status_code == 200
    categories_by_slug = {category["slug"]: category for category in category_response.json()}
    original_category_ids = [
        categories_by_slug["krasota"]["id"],
        categories_by_slug["manikyur-pedikyur"]["id"],
        categories_by_slug["brovi-resnitsy"]["id"],
        categories_by_slug["kosmetologiya"]["id"],
    ]
    create_response = admin_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json=_partner_payload(name="Unchecked Category Partner", category_ids=original_category_ids),
    )
    assert create_response.status_code == 200
    partner_id = create_response.json()["id"]

    selected_after_uncheck = original_category_ids[1:]
    update_response = admin_client.patch(
        f"/api/v1/admin/partners/{partner_id}",
        headers=_auth_headers(admin_token),
        json={"category_ids": selected_after_uncheck},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["category_ids"] == selected_after_uncheck
    assert categories_by_slug["krasota"]["id"] not in updated["category_ids"]
    assert updated["category_slugs"] == ["manikyur-pedikyur", "brovi-resnitsy", "kosmetologiya"]

    list_response = admin_client.get("/api/v1/admin/partners", headers=_auth_headers(admin_token))
    assert list_response.status_code == 200
    listed = next(partner for partner in list_response.json() if partner["id"] == partner_id)
    assert listed["category_ids"] == selected_after_uncheck
    assert "krasota" not in listed["category_slugs"]



def test_admin_partner_patch_removes_exact_manicure_category_and_preserves_other_russian_categories(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    category_response = admin_client.get("/api/v1/admin/categories", headers=_auth_headers(admin_token))
    assert category_response.status_code == 200
    categories_by_slug = {category["slug"]: category for category in category_response.json()}
    exact_slugs = [
        "krasota",
        "manikyur-pedikyur",
        "volosy-okrashivanie",
        "brovi-resnitsy",
        "kosmetologiya",
    ]
    original_category_ids = [categories_by_slug[slug]["id"] for slug in exact_slugs]
    manicure_id = categories_by_slug["manikyur-pedikyur"]["id"]
    selected_after_uncheck = [category_id for category_id in original_category_ids if category_id != manicure_id]

    create_response = admin_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json=_partner_payload(
            name="Счастье есть",
            description="Initial description",
            phone="+79990000000",
            category_ids=original_category_ids,
        ),
    )
    assert create_response.status_code == 200
    partner_id = create_response.json()["id"]
    assert [category["name"] for category in create_response.json()["categories"]] == [
        "Красота",
        "Маникюр / педикюр",
        "Волосы / окрашивание",
        "Брови / ресницы",
        "Косметология",
    ]

    update_response = admin_client.patch(
        f"/api/v1/admin/partners/{partner_id}",
        headers=_auth_headers(admin_token),
        json={
            "category_ids": selected_after_uncheck,
            "description": "Updated description",
            "phone": "+79991112233",
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert manicure_id not in updated["category_ids"]
    assert updated["category_ids"] == selected_after_uncheck
    assert [category["name"] for category in updated["categories"]] == [
        "Красота",
        "Волосы / окрашивание",
        "Брови / ресницы",
        "Косметология",
    ]
    assert "Маникюр / педикюр" not in [category["name"] for category in updated["categories"]]
    assert updated["description"] == "Updated description"
    assert updated["phone"] == "+79991112233"

    refetch_response = admin_client.get(f"/api/v1/admin/partners/{partner_id}", headers=_auth_headers(admin_token))
    assert refetch_response.status_code == 200
    refetched = refetch_response.json()
    assert refetched["category_ids"] == selected_after_uncheck
    assert [category["name"] for category in refetched["categories"]] == [
        "Красота",
        "Волосы / окрашивание",
        "Брови / ресницы",
        "Косметология",
    ]

    list_response = admin_client.get("/api/v1/admin/partners", headers=_auth_headers(admin_token))
    assert list_response.status_code == 200
    listed = next(partner for partner in list_response.json() if partner["id"] == partner_id)
    assert listed["category_ids"] == selected_after_uncheck
    assert "Маникюр / педикюр" not in [category["name"] for category in listed["categories"]]


def test_admin_partner_patch_duplicate_label_removes_only_submitted_unchecked_category_id(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    duplicate_response = admin_client.post(
        "/api/v1/admin/categories",
        headers=_auth_headers(admin_token),
        json={"name": "Маникюр / педикюр", "slug": "manikyur-pedikyur-duplicate", "is_active": True, "sort_order": 99},
    )
    assert duplicate_response.status_code == 200
    duplicate_id = duplicate_response.json()["id"]

    category_response = admin_client.get("/api/v1/admin/categories", headers=_auth_headers(admin_token))
    assert category_response.status_code == 200
    categories_by_slug = {category["slug"]: category for category in category_response.json()}
    manicure_id = categories_by_slug["manikyur-pedikyur"]["id"]
    original_category_ids = [
        categories_by_slug["krasota"]["id"],
        manicure_id,
        duplicate_id,
        categories_by_slug["kosmetologiya"]["id"],
    ]

    create_response = admin_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json=_partner_payload(name="Duplicate Label Partner", category_ids=original_category_ids),
    )
    assert create_response.status_code == 200
    partner_id = create_response.json()["id"]

    selected_after_uncheck = [category_id for category_id in original_category_ids if category_id != manicure_id]
    update_response = admin_client.patch(
        f"/api/v1/admin/partners/{partner_id}",
        headers=_auth_headers(admin_token),
        json={"category_ids": selected_after_uncheck},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert manicure_id not in updated["category_ids"]
    assert duplicate_id in updated["category_ids"]
    assert set(category["id"] for category in updated["categories"]) == set(selected_after_uncheck)

def test_admin_partner_patch_can_clear_categories_with_empty_array(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    category_response = admin_client.get("/api/v1/admin/categories", headers=_auth_headers(admin_token))
    assert category_response.status_code == 200
    category_ids = [category["id"] for category in category_response.json()[:2]]
    create_response = admin_client.post(
        "/api/v1/admin/partners",
        headers=_auth_headers(admin_token),
        json=_partner_payload(name="Clear Category Partner", category_ids=category_ids),
    )
    assert create_response.status_code == 200
    partner_id = create_response.json()["id"]

    update_response = admin_client.patch(
        f"/api/v1/admin/partners/{partner_id}",
        headers=_auth_headers(admin_token),
        json={"category_ids": []},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["category_ids"] == []
    assert updated["category_slugs"] == []
    assert updated["categories"] == []
    assert updated["category_slug"] is None


def test_admin_partner_patch_deduplicates_category_ids(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    category_response = admin_client.get("/api/v1/admin/categories", headers=_auth_headers(admin_token))
    assert category_response.status_code == 200
    category_ids = [category["id"] for category in category_response.json()[:2]]

    update_response = admin_client.patch(
        "/api/v1/admin/partners/1",
        headers=_auth_headers(admin_token),
        json={"category_ids": [category_ids[0], category_ids[0], category_ids[1]]},
    )

    assert update_response.status_code == 200
    assert update_response.json()["category_ids"] == category_ids


def test_admin_partner_patch_invalid_category_id_returns_controlled_error(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_client.patch(
        "/api/v1/admin/partners/1",
        headers=_auth_headers(admin_token),
        json={"category_ids": [999999]},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Category not found"}


def test_admin_partner_patch_accepts_categories_alias_for_category_ids(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    category_response = admin_client.get("/api/v1/admin/categories", headers=_auth_headers(admin_token))
    assert category_response.status_code == 200
    category_ids = [category["id"] for category in category_response.json()[:2]]

    response = admin_client.patch(
        "/api/v1/admin/partners/1",
        headers=_auth_headers(admin_token),
        json={"categories": category_ids},
    )

    assert response.status_code == 200
    assert response.json()["category_ids"] == category_ids

def test_admin_partner_get_missing_returns_404(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/partners/9999", headers=_auth_headers(admin_token))

    assert response.status_code == 404
    assert response.json()["detail"] == "Partner not found"


def test_admin_partner_patch_updates_fields(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.patch(
        "/api/v1/admin/partners/1",
        headers=_auth_headers(admin_token),
        json={
            "city_id": 2,
            "category_slug": "fitnes-yoga",
            "name": "  Updated Partner  ",
            "is_active": False,
            "sort_order": 1,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["city_id"] == 2
    assert data["city_name"] == "Санкт-Петербург"
    assert data["category_slug"] == "fitnes-yoga"
    assert data["name"] == "Updated Partner"
    assert data["is_active"] is False
    assert data["sort_order"] == 1


def test_admin_partner_patch_can_clear_owner_user_id(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.patch(
        "/api/v1/admin/partners/1",
        headers=_auth_headers(admin_token),
        json={"owner_user_id": None},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["owner_user_id"] is None
    assert data["owner_email"] is None


def test_admin_partners_list_supports_city_id_filter(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/partners?city_id=1", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert [partner["name"] for partner in data] == ["Alpha Beauty"]


def test_admin_partners_list_supports_is_active_filter(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/partners?is_active=false", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert [partner["name"] for partner in data] == ["Beta Yoga"]


def test_admin_partners_list_supports_category_slug_filter(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get(
        "/api/v1/admin/partners?category_slug=fitnes-yoga",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.json()
    assert [partner["name"] for partner in data] == ["Beta Yoga"]


def test_admin_partners_list_supports_q_search(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/partners?q=beaut", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert [partner["name"] for partner in data] == ["Alpha Beauty"]

TINY_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\x9cc``\x00\x00"
    b"\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
)
TINY_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xd9"
TINY_WEBP_BYTES = b"RIFF\x0c\x00\x00\x00WEBPVP8 \x00\x00\x00\x00"


def _upload_file(content: bytes, filename: str, content_type: str) -> dict[str, tuple[str, bytes, str]]:
    return {"file": (filename, content, content_type)}


def test_admin_uploads_valid_png_logo_updates_partner(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/images?kind=logo",
        headers=_auth_headers(admin_token),
        files=_upload_file(TINY_PNG_BYTES, "ignored-original-name.png", "image/png"),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "logo"
    assert data["url"].startswith("/uploads/partners/1/logo-")
    assert data["url"].endswith(".png")

    partner_response = admin_client.get("/api/v1/admin/partners/1", headers=_auth_headers(admin_token))
    assert partner_response.status_code == 200
    assert partner_response.json()["logo_url"] == data["url"]


def test_admin_uploads_valid_jpeg_and_webp_logo(admin_client: TestClient, admin_token: str) -> None:
    jpeg_response = admin_client.post(
        "/api/v1/admin/partners/1/images?kind=logo",
        headers=_auth_headers(admin_token),
        files=_upload_file(TINY_JPEG_BYTES, "logo.jpeg", "image/jpeg"),
    )
    assert jpeg_response.status_code == 200
    assert jpeg_response.json()["url"].endswith(".jpg")

    webp_response = admin_client.post(
        "/api/v1/admin/partners/1/images?kind=logo",
        headers=_auth_headers(admin_token),
        files=_upload_file(TINY_WEBP_BYTES, "logo.webp", "image/webp"),
    )
    assert webp_response.status_code == 200
    assert webp_response.json()["url"].endswith(".webp")


def test_admin_uploads_cover_updates_cover_url(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/images?kind=cover",
        headers=_auth_headers(admin_token),
        files=_upload_file(TINY_PNG_BYTES, "cover.png", "image/png"),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "cover"
    assert data["url"].startswith("/uploads/partners/1/cover-")

    partner_response = admin_client.get("/api/v1/admin/partners/1", headers=_auth_headers(admin_token))
    assert partner_response.json()["cover_url"] == data["url"]


def test_admin_upload_rejects_invalid_kind(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/images?kind=gallery",
        headers=_auth_headers(admin_token),
        files=_upload_file(TINY_PNG_BYTES, "logo.png", "image/png"),
    )

    assert response.status_code == 400


def test_admin_upload_rejects_invalid_content_type(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/images?kind=logo",
        headers=_auth_headers(admin_token),
        files=_upload_file(b"<svg></svg>", "logo.svg", "image/svg+xml"),
    )

    assert response.status_code == 400


def test_admin_upload_rejects_invalid_image_bytes(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/images?kind=logo",
        headers=_auth_headers(admin_token),
        files=_upload_file(b"not an image", "logo.png", "image/png"),
    )

    assert response.status_code == 400


def test_admin_upload_rejects_too_large_file(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/images?kind=logo",
        headers=_auth_headers(admin_token),
        files=_upload_file(b"\x89PNG\r\n\x1a\n" + (b"0" * (5 * 1024 * 1024)), "logo.png", "image/png"),
    )

    assert response.status_code == 400


def test_admin_upload_rejects_unauthorized_request(admin_client: TestClient) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/images?kind=logo",
        files=_upload_file(TINY_PNG_BYTES, "logo.png", "image/png"),
    )

    assert response.status_code == 401


def test_admin_upload_missing_partner_returns_404(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/999/images?kind=logo",
        headers=_auth_headers(admin_token),
        files=_upload_file(TINY_PNG_BYTES, "logo.png", "image/png"),
    )

    assert response.status_code == 404


def test_admin_uploads_partner_photo_lists_sorted_and_patches(admin_client: TestClient, admin_token: str) -> None:
    first = admin_client.post(
        "/api/v1/admin/partners/1/photos",
        headers=_auth_headers(admin_token),
        data={"alt_text": "Витрина", "sort_order": "20"},
        files=_upload_file(TINY_PNG_BYTES, "gallery.png", "image/png"),
    )
    second = admin_client.post(
        "/api/v1/admin/partners/1/photos",
        headers=_auth_headers(admin_token),
        data={"alt_text": "Зал", "sort_order": "10"},
        files=_upload_file(TINY_PNG_BYTES, "gallery-2.png", "image/png"),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["url"].startswith("/uploads/partners/1/photos/photo-")
    assert first.json()["url"].endswith(".png")
    assert first.json()["is_active"] is True

    list_response = admin_client.get("/api/v1/admin/partners/1/photos", headers=_auth_headers(admin_token))
    assert list_response.status_code == 200
    assert [photo["alt_text"] for photo in list_response.json()] == ["Зал", "Витрина"]

    patch_response = admin_client.patch(
        f"/api/v1/admin/partner-photos/{first.json()['id']}",
        headers=_auth_headers(admin_token),
        json={"alt_text": "Новое описание", "sort_order": 5, "is_active": False},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["alt_text"] == "Новое описание"
    assert patch_response.json()["sort_order"] == 5
    assert patch_response.json()["is_active"] is False


def test_admin_partner_photo_upload_rejects_invalid_file_type(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/photos",
        headers=_auth_headers(admin_token),
        files=_upload_file(b"<svg></svg>", "gallery.svg", "image/svg+xml"),
    )

    assert response.status_code == 400
