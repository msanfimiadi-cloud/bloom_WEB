from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.content_base import ContentBase
from app.db.content_session import get_content_db
from app.db.session import get_db
from app.main import app
from app.models.user import AdminUser, UserRole


@pytest.fixture()
def content_admin_client() -> Generator[tuple[TestClient, str], None, None]:
    main_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    content_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    main_session_factory = sessionmaker(
        bind=main_engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    content_session_factory = sessionmaker(
        bind=content_engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    Base.metadata.create_all(bind=main_engine)
    ContentBase.metadata.create_all(bind=content_engine)
    with main_session_factory() as session:
        admin = AdminUser(
            email="admin@example.com",
            password_hash=hash_password("StrongPassword123"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        session.add(admin)
        session.commit()
        admin_id = admin.id

    def override_get_db() -> Generator[Session, None, None]:
        with main_session_factory() as session:
            yield session

    def override_get_content_db() -> Generator[Session, None, None]:
        with content_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_content_db] = override_get_content_db
    try:
        with TestClient(app) as client:
            yield client, create_access_token(str(admin_id))
    finally:
        app.dependency_overrides.clear()
        main_engine.dispose()
        content_engine.dispose()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_content_admin_crud_bootstraps_content_database(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client
    headers = _auth_headers(token)

    assert (
        client.post(
            "/api/content/admin/cities", json={"name": "Москва", "slug": "moscow"}
        ).status_code
        == 401
    )

    city_response = client.post(
        "/api/content/admin/cities",
        headers=headers,
        json={"name": "Москва", "slug": "moscow"},
    )
    assert city_response.status_code == 201
    city_id = city_response.json()["id"]

    category_response = client.post(
        "/api/content/admin/categories",
        headers=headers,
        json={"name": "Красота", "slug": "beauty"},
    )
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    partner_response = client.post(
        "/api/content/admin/partners",
        headers=headers,
        json={
            "city_id": city_id,
            "category_slug": "beauty",
            "category_ids": [category_id],
            "name": "Bloom Spa",
            "description": "Спа-партнёр клуба",
            "address": "Тверская, 1",
            "phone": "+79990000000",
        },
    )
    assert partner_response.status_code == 201
    partner = partner_response.json()
    partner_id = partner["id"]
    assert partner["category_ids"] == [category_id]

    offer_response = client.post(
        f"/api/content/admin/partners/{partner_id}/offers",
        headers=headers,
        json={"title": "Массаж", "benefit_text": "Скидка 20%", "base_price": "3000.00"},
    )
    assert offer_response.status_code == 201
    offer_id = offer_response.json()["id"]

    partner_photo_response = client.post(
        f"/api/content/admin/partners/{partner_id}/photos",
        headers=headers,
        json={"url": "https://example.com/partner.jpg", "alt_text": "Интерьер"},
    )
    assert partner_photo_response.status_code == 201

    offer_photo_response = client.post(
        f"/api/content/admin/offers/{offer_id}/photos",
        headers=headers,
        json={"url": "https://example.com/offer.jpg", "alt_text": "Услуга"},
    )
    assert offer_photo_response.status_code == 201

    giveaway_response = client.post(
        "/api/content/admin/giveaways",
        headers=headers,
        json={"title": "Первый розыгрыш", "current": "Сертификат"},
    )
    assert giveaway_response.status_code == 201

    banner_response = client.post(
        "/api/content/admin/banners",
        headers=headers,
        json={
            "title": "Добро пожаловать",
            "image_url": "https://example.com/banner.jpg",
        },
    )
    assert banner_response.status_code == 201

    assert (
        client.patch(
            f"/api/content/admin/cities/{city_id}",
            headers=headers,
            json={"sort_order": 10},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/content/admin/categories/{category_id}",
            headers=headers,
            json={"sort_order": 20},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/content/admin/partners/{partner_id}",
            headers=headers,
            json={"is_verified": True},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/content/admin/offers/{offer_id}",
            headers=headers,
            json={"is_active": False},
        ).status_code
        == 200
    )

    assert (
        client.get("/api/content/admin/cities", headers=headers).json()[0]["name"]
        == "Москва"
    )
    assert (
        client.get(
            f"/api/content/admin/partners/{partner_id}/offers", headers=headers
        ).status_code
        == 200
    )
    assert (
        client.get(
            f"/api/content/admin/partners/{partner_id}/photos", headers=headers
        ).status_code
        == 200
    )
    assert (
        client.get(
            f"/api/content/admin/offers/{offer_id}/photos", headers=headers
        ).status_code
        == 200
    )
    assert (
        client.get("/api/content/admin/giveaways", headers=headers).status_code == 200
    )
    assert client.get("/api/content/admin/banners", headers=headers).status_code == 200


def test_content_admin_accepts_server_to_server_telegram_token(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, _token = content_admin_client
    original_token = settings.TELEGRAM_ADMIN_API_TOKEN
    object.__setattr__(
        settings, "TELEGRAM_ADMIN_API_TOKEN", "telegram-admin-test-token"
    )
    try:
        bearer_response = client.get(
            "/api/content/admin/cities",
            headers={"Authorization": "Bearer telegram-admin-test-token"},
        )
        legacy_header_response = client.get(
            "/api/content/admin/cities",
            headers={"X-Telegram-Admin-Token": "telegram-admin-test-token"},
        )
    finally:
        object.__setattr__(settings, "TELEGRAM_ADMIN_API_TOKEN", original_token)

    assert bearer_response.status_code == 200
    assert legacy_header_response.status_code == 200


def test_content_admin_detail_endpoints_and_offer_bot_price_aliases(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client
    headers = _auth_headers(token)

    city_id = client.post(
        "/api/content/admin/cities",
        headers=headers,
        json={"name": "Новосибирск", "slug": "novosibirsk"},
    ).json()["id"]
    partner = client.post(
        "/api/content/admin/partners",
        headers=headers,
        json={"city_id": city_id, "name": "Bloom Fit"},
    ).json()
    partner_id = partner["id"]

    offer_response = client.post(
        f"/api/content/admin/partners/{partner_id}/offers",
        headers=headers,
        json={
            "title": "Абонемент",
            "terms": "Только для участниц клуба",
            "regular_price": "5000.00",
            "club_price": "3500.00",
        },
    )
    assert offer_response.status_code == 201
    offer = offer_response.json()
    offer_id = offer["id"]
    assert offer["base_price"] == "5000.00"
    assert offer["regular_price"] == "5000.00"
    assert offer["club_price"] == "3500.00"
    assert offer["saving"] == "1500.00"
    assert offer["terms"] == "Только для участниц клуба"

    assert (
        client.get(f"/api/content/admin/partners/{partner_id}", headers=headers).json()[
            "name"
        ]
        == "Bloom Fit"
    )
    assert (
        client.get(f"/api/content/admin/offers/{offer_id}", headers=headers).json()[
            "saving"
        ]
        == "1500.00"
    )

    patched_offer = client.patch(
        f"/api/content/admin/offers/{offer_id}",
        headers=headers,
        json={"club_price": "4000.00"},
    ).json()
    assert patched_offer["club_price"] == "4000.00"
    assert patched_offer["saving"] == "1000.00"

    giveaway_response = client.post(
        "/api/content/admin/giveaways",
        headers=headers,
        json={"title": "Июнь", "current": "Подарок"},
    )
    giveaway_id = giveaway_response.json()["id"]
    assert (
        client.get(
            f"/api/content/admin/giveaways/{giveaway_id}", headers=headers
        ).json()["title"]
        == "Июнь"
    )


def test_public_content_endpoints_remain_read_only(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client

    create_response = client.post(
        "/api/content/cities",
        headers=_auth_headers(token),
        json={"name": "Москва", "slug": "moscow"},
    )

    assert create_response.status_code == 405


def test_public_content_blocks_returns_active_block(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client
    headers = _auth_headers(token)

    create_response = client.post(
        "/api/content/admin/blocks",
        headers=headers,
        json={
            "key": "home.hero.title",
            "placement": "static_texts",
            "locale": "ru",
            "title": "Hero title",
            "body": "Добро пожаловать",
            "metadata_json": {"editable": True},
            "is_active": True,
        },
    )
    assert create_response.status_code == 201

    response = client.get("/api/content/blocks?type=static_texts")

    assert response.status_code == 200
    assert response.json() == [
        {
            "key": "home.hero.title",
            "placement": "static_texts",
            "locale": "ru",
            "title": "Hero title",
            "body": "Добро пожаловать",
            "metadata_json": {"editable": True},
            "is_active": True,
        }
    ]


def test_public_content_blocks_does_not_return_inactive_block(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client

    create_response = client.post(
        "/api/content/admin/blocks",
        headers=_auth_headers(token),
        json={
            "key": "home.hero.subtitle",
            "placement": "static_texts",
            "locale": "ru",
            "body": "Inactive text",
            "is_active": False,
        },
    )
    assert create_response.status_code == 201

    response = client.get("/api/content/blocks?type=static_texts")

    assert response.status_code == 200
    assert response.json() == []


def test_admin_create_content_block_requires_admin_token(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, _token = content_admin_client

    response = client.post(
        "/api/content/admin/blocks",
        json={
            "key": "nav.home.label",
            "placement": "static_texts",
            "locale": "ru",
            "body": "Главная",
        },
    )

    assert response.status_code == 401


def test_admin_create_content_block_with_admin_token(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client

    response = client.post(
        "/api/content/admin/blocks",
        headers=_auth_headers(token),
        json={
            "key": "nav.home.label",
            "placement": "static_texts",
            "locale": "ru",
            "title": "Navigation home",
            "body": "Главная",
            "metadata_json": {"source": "telegram_admin_preview"},
            "is_active": True,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "key": "nav.home.label",
        "placement": "static_texts",
        "locale": "ru",
        "title": "Navigation home",
        "body": "Главная",
        "metadata_json": {"source": "telegram_admin_preview"},
        "is_active": True,
    }


def test_admin_update_content_block_updates_existing_block(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client
    headers = _auth_headers(token)

    create_response = client.post(
        "/api/content/admin/blocks",
        headers=headers,
        json={
            "key": "nav.partners.label",
            "placement": "static_texts",
            "locale": "ru",
            "body": "Партнёры",
            "is_active": True,
        },
    )
    assert create_response.status_code == 201

    response = client.patch(
        "/api/content/admin/blocks/nav.partners.label",
        headers=headers,
        json={"body": "Клуб", "metadata_json": {"updated": True}},
    )

    assert response.status_code == 200
    assert response.json()["key"] == "nav.partners.label"
    assert response.json()["locale"] == "ru"
    assert response.json()["body"] == "Клуб"
    assert response.json()["metadata_json"] == {"updated": True}


def test_admin_update_content_block_creates_missing_key(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client

    response = client.patch(
        "/api/content/admin/blocks/nav.privileges.label",
        headers=_auth_headers(token),
        json={"body": "Привилегии", "is_active": True},
    )

    assert response.status_code == 200
    assert response.json() == {
        "key": "nav.privileges.label",
        "placement": "static_texts",
        "locale": "ru",
        "title": None,
        "body": "Привилегии",
        "metadata_json": None,
        "is_active": True,
    }


def test_public_static_texts_returns_created_telegram_miniapp_blocks(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client
    headers = _auth_headers(token)
    expected_keys = [
        "nav.home.label",
        "nav.partners.label",
        "nav.privileges.label",
        "nav.savings.label",
        "nav.profile.label",
        "home.hero.title",
        "home.hero.subtitle",
    ]

    for key in expected_keys:
        response = client.patch(
            f"/api/content/admin/blocks/{key}",
            headers=headers,
            json={
                "placement": "static_texts",
                "locale": "ru",
                "body": f"Text for {key}",
                "is_active": True,
            },
        )
        assert response.status_code == 200

    response = client.get("/api/content/blocks?type=static_texts")

    assert response.status_code == 200
    blocks_by_key = {block["key"]: block for block in response.json()}
    assert sorted(blocks_by_key) == sorted(expected_keys)
    for key in expected_keys:
        assert blocks_by_key[key]["body"] == f"Text for {key}"
        assert blocks_by_key[key]["placement"] == "static_texts"
        assert blocks_by_key[key]["locale"] == "ru"
        assert blocks_by_key[key]["is_active"] is True


PNG_BYTES = b"\x89PNG\r\n\x1a\ncontent-cms-upload"
JPG_BYTES = b"\xff\xd8\xffcontent-cms-upload"
WEBP_BYTES = b"RIFF\x12\x00\x00\x00WEBPcontent"


@pytest.fixture()
def content_upload_settings(tmp_path):
    original_upload_dir = settings.UPLOAD_DIR
    original_web_public_url = settings.WEB_PUBLIC_URL
    object.__setattr__(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    object.__setattr__(settings, "WEB_PUBLIC_URL", "https://bloomclub.ru")
    try:
        yield tmp_path / "uploads"
    finally:
        object.__setattr__(settings, "UPLOAD_DIR", original_upload_dir)
        object.__setattr__(settings, "WEB_PUBLIC_URL", original_web_public_url)


def _upload_file(
    client: TestClient, token: str, filename: str, content: bytes, content_type: str
):
    return client.post(
        "/api/content/uploads",
        headers=_auth_headers(token),
        files={"file": (filename, content, content_type)},
    )


def test_content_upload_requires_admin_token(
    content_admin_client: tuple[TestClient, str],
    content_upload_settings,
) -> None:
    client, _token = content_admin_client

    response = client.post(
        "/api/content/uploads",
        files={"file": ("image.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code in {401, 403}


def test_content_upload_rejects_unsupported_format(
    content_admin_client: tuple[TestClient, str],
    content_upload_settings,
) -> None:
    client, token = content_admin_client

    response = _upload_file(
        client, token, "script.exe", b"MZ executable", "application/octet-stream"
    )

    assert response.status_code == 400


def test_content_upload_rejects_large_file(
    content_admin_client: tuple[TestClient, str],
    content_upload_settings,
) -> None:
    client, token = content_admin_client
    too_large_png = PNG_BYTES + (b"0" * (10 * 1024 * 1024 + 1))

    response = _upload_file(client, token, "large.png", too_large_png, "image/png")

    assert response.status_code == 400


@pytest.mark.parametrize(
    ("filename", "content", "content_type", "expected_suffix"),
    [
        ("image.png", PNG_BYTES, "image/png", ".png"),
        ("image.jpg", JPG_BYTES, "image/jpeg", ".jpg"),
        ("image.jpeg", JPG_BYTES, "image/jpeg", ".jpeg"),
        ("image.webp", WEBP_BYTES, "image/webp", ".webp"),
    ],
)
def test_content_upload_accepts_valid_images_and_creates_file(
    content_admin_client: tuple[TestClient, str],
    content_upload_settings,
    filename: str,
    content: bytes,
    content_type: str,
    expected_suffix: str,
) -> None:
    client, token = content_admin_client

    response = _upload_file(client, token, filename, content, content_type)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"].endswith(expected_suffix)
    assert data["path"] == f"/uploads/content/{data['filename']}"
    assert data["url"] == f"https://bloomclub.ru/uploads/content/{data['filename']}"
    assert data["content_type"] == content_type
    assert data["size"] == len(content)
    saved_file = content_upload_settings / "content" / data["filename"]
    assert saved_file.exists()
    assert saved_file.read_bytes() == content


def test_content_admin_token_auth_status_codes(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, _token = content_admin_client
    original_token = settings.TELEGRAM_ADMIN_API_TOKEN
    object.__setattr__(
        settings, "TELEGRAM_ADMIN_API_TOKEN", "telegram-admin-test-token"
    )
    try:
        missing = client.get("/api/content/admin/cities")
        assert missing.status_code == 401

        wrong_bearer = client.get(
            "/api/content/admin/cities",
            headers={"Authorization": "Bearer wrong-telegram-token"},
        )
        assert wrong_bearer.status_code == 403

        wrong_header = client.get(
            "/api/content/admin/cities",
            headers={"X-Telegram-Admin-Token": "wrong-telegram-token"},
        )
        assert wrong_header.status_code == 403

        bearer_ok = client.get(
            "/api/content/admin/cities",
            headers={"Authorization": "Bearer telegram-admin-test-token"},
        )
        assert bearer_ok.status_code == 200

        header_ok = client.get(
            "/api/content/admin/cities",
            headers={"X-Telegram-Admin-Token": "telegram-admin-test-token"},
        )
        assert header_ok.status_code == 200
    finally:
        object.__setattr__(settings, "TELEGRAM_ADMIN_API_TOKEN", original_token)


def test_legacy_web_admin_content_write_flag_blocks_old_content_editing(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client
    original_flag = settings.WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED
    object.__setattr__(settings, "WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED", False)
    try:
        response = client.post(
            "/api/v1/admin/cities",
            headers=_auth_headers(token),
            json={"name": "Legacy City", "slug": "legacy-city"},
        )
        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "Legacy WEB content editing is disabled; use Content Admin API"
        )

        read_response = client.get("/api/v1/admin/cities", headers=_auth_headers(token))
        assert read_response.status_code == 200
    finally:
        object.__setattr__(
            settings, "WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED", original_flag
        )


def test_content_admin_giveaway_items_crud_and_public_active_items(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client
    headers = _auth_headers(token)
    giveaway_id = client.post(
        "/api/content/admin/giveaways",
        headers=headers,
        json={"title": "Июньский розыгрыш", "current": "Подарки"},
    ).json()["id"]

    inactive_response = client.post(
        f"/api/content/admin/giveaways/{giveaway_id}/items",
        headers=headers,
        json={
            "title": "Скрытый приз",
            "description": None,
            "image_url": None,
            "sort_order": 0,
            "is_active": False,
        },
    )
    assert inactive_response.status_code == 201

    second_response = client.post(
        f"/api/content/admin/giveaways/{giveaway_id}/items",
        headers=headers,
        json={"title": "Второй приз", "sort_order": 20},
    )
    first_response = client.post(
        f"/api/content/admin/giveaways/{giveaway_id}/items",
        headers=headers,
        json={
            "title": "Первый приз",
            "description": "Сертификат партнёра",
            "image_url": "https://example.com/prize.jpg",
            "sort_order": 10,
        },
    )
    assert second_response.status_code == 201
    assert first_response.status_code == 201
    first_item = first_response.json()
    first_item_id = first_item["id"]
    assert first_item["giveaway_id"] == giveaway_id
    assert first_item["description"] == "Сертификат партнёра"

    list_response = client.get(
        f"/api/content/admin/giveaways/{giveaway_id}/items", headers=headers
    )
    assert list_response.status_code == 200
    assert [item["title"] for item in list_response.json()] == [
        "Скрытый приз",
        "Первый приз",
        "Второй приз",
    ]

    read_response = client.get(
        f"/api/content/admin/giveaway-items/{first_item_id}", headers=headers
    )
    assert read_response.status_code == 200
    assert read_response.json()["title"] == "Первый приз"

    update_response = client.patch(
        f"/api/content/admin/giveaway-items/{first_item_id}",
        headers=headers,
        json={"title": "Главный приз"},
    )
    assert update_response.status_code == 200
    updated_item = update_response.json()
    assert updated_item["title"] == "Главный приз"
    assert updated_item["description"] == "Сертификат партнёра"
    assert updated_item["sort_order"] == 10

    public_response = client.get("/api/content/giveaways")
    assert public_response.status_code == 200
    assert [item["title"] for item in public_response.json()[0]["items"]] == [
        "Главный приз",
        "Второй приз",
    ]


def test_content_admin_giveaway_items_not_found_and_auth(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client
    headers = _auth_headers(token)
    giveaway_id = client.post(
        "/api/content/admin/giveaways", headers=headers, json={"title": "Июль"}
    ).json()["id"]

    assert (
        client.post(
            "/api/content/admin/giveaways/999999/items",
            headers=headers,
            json={"title": "Приз"},
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/api/content/admin/giveaway-items/999999", headers=headers
        ).status_code
        == 404
    )
    assert (
        client.patch(
            "/api/content/admin/giveaway-items/999999",
            headers=headers,
            json={"title": "Новый приз"},
        ).status_code
        == 404
    )
    assert (
        client.get(f"/api/content/admin/giveaways/{giveaway_id}/items").status_code
        == 401
    )

    original_token = settings.TELEGRAM_ADMIN_API_TOKEN
    object.__setattr__(
        settings, "TELEGRAM_ADMIN_API_TOKEN", "telegram-admin-test-token"
    )
    try:
        wrong_response = client.get(
            f"/api/content/admin/giveaways/{giveaway_id}/items",
            headers={"X-Telegram-Admin-Token": "wrong-token"},
        )
        bearer_response = client.post(
            f"/api/content/admin/giveaways/{giveaway_id}/items",
            headers={"Authorization": "Bearer telegram-admin-test-token"},
            json={"title": "Bearer prize"},
        )
        header_response = client.post(
            f"/api/content/admin/giveaways/{giveaway_id}/items",
            headers={"X-Telegram-Admin-Token": "telegram-admin-test-token"},
            json={"title": "Header prize"},
        )
    finally:
        object.__setattr__(settings, "TELEGRAM_ADMIN_API_TOKEN", original_token)

    assert wrong_response.status_code == 403
    assert bearer_response.status_code == 201
    assert header_response.status_code == 201


def test_content_admin_delete_partner_hard_deletes_related_records(
    content_admin_client: tuple[TestClient, str],
) -> None:
    client, token = content_admin_client
    headers = _auth_headers(token)

    city_id = client.post(
        "/api/content/admin/cities",
        headers=headers,
        json={"name": "Казань", "slug": "kazan"},
    ).json()["id"]
    category_id = client.post(
        "/api/content/admin/categories",
        headers=headers,
        json={"name": "Фитнес", "slug": "fitness"},
    ).json()["id"]
    partner_id = client.post(
        "/api/content/admin/partners",
        headers=headers,
        json={
            "city_id": city_id,
            "category_slug": "fitness",
            "category_ids": [category_id],
            "name": "Hard Delete Partner",
        },
    ).json()["id"]
    offer_id = client.post(
        f"/api/content/admin/partners/{partner_id}/offers",
        headers=headers,
        json={"title": "Trial", "benefit_text": "-10%"},
    ).json()["id"]
    partner_photo_id = client.post(
        f"/api/content/admin/partners/{partner_id}/photos",
        headers=headers,
        json={"url": "https://example.com/partner-hard-delete.jpg"},
    ).json()["id"]
    offer_photo_id = client.post(
        f"/api/content/admin/offers/{offer_id}/photos",
        headers=headers,
        json={"url": "https://example.com/offer-hard-delete.jpg"},
    ).json()["id"]

    delete_response = client.delete(
        f"/api/content/admin/partners/{partner_id}", headers=headers
    )

    assert delete_response.status_code == 204
    assert (
        client.get(f"/api/content/admin/partners/{partner_id}", headers=headers).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/content/admin/partners/{partner_id}/photos", headers=headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/content/admin/partners/{partner_id}/offers", headers=headers
        ).status_code
        == 404
    )
    assert (
        client.get(f"/api/content/admin/offers/{offer_id}", headers=headers).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/content/admin/offers/{offer_id}/photos", headers=headers
        ).status_code
        == 404
    )
    assert client.patch(
        f"/api/content/admin/partner-photos/{partner_photo_id}",
        headers=headers,
        json={"alt_text": "gone"},
    ).status_code == 404
    assert client.patch(
        f"/api/content/admin/offer-photos/{offer_photo_id}",
        headers=headers,
        json={"alt_text": "gone"},
    ).status_code == 404
    assert (
        client.delete(f"/api/content/admin/partners/{partner_id}", headers=headers).status_code
        == 404
    )
    partners = client.get("/api/content/admin/partners", headers=headers).json()
    assert partner_id not in {partner["id"] for partner in partners}
