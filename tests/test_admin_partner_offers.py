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
from app.models.partner import Partner, PartnerOffer
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
                    title="Later offer",
                    benefit_text="Later benefit",
                    is_active=True,
                    sort_order=20,
                ),
                PartnerOffer(
                    partner_id=partner.id,
                    title="First same sort",
                    is_active=True,
                    sort_order=10,
                ),
                PartnerOffer(
                    partner_id=partner.id,
                    title="Second same sort inactive",
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


def _offer_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "  Скидка на уход  ",
        "description": "  Подробное описание  ",
        "benefit_text": "  -15% для клуба  ",
        "conditions": "  По записи  ",
        "base_price": "1000.00",
        "discount_percent": "15.50",
        "image_url": "  https://example.com/offer.png  ",
        "is_active": True,
        "sort_order": 5,
    }
    payload.update(overrides)
    return payload


def test_admin_partner_offers_returns_401_without_token(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/admin/partners/1/offers")

    assert response.status_code == 401


def test_admin_partner_offers_missing_partner_returns_404(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/partners/9999/offers", headers=_auth_headers(admin_token))

    assert response.status_code == 404
    assert response.json()["detail"] == "Partner not found"


def test_admin_partner_offer_create_for_existing_partner(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/offers",
        headers=_auth_headers(admin_token),
        json=_offer_payload(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"]
    assert data["partner_id"] == 1
    assert data["partner_name"] == "Alpha Beauty"
    assert data["title"] == "Скидка на уход"
    assert data["description"] == "Подробное описание"
    assert data["benefit_text"] == "-15% для клуба"
    assert data["conditions"] == "По записи"
    assert data["base_price"] in ("1000.00", 1000.0)
    assert data["discount_percent"] in ("15.50", 15.5)
    assert data["image_url"] == "https://example.com/offer.png"
    assert data["is_active"] is True
    assert data["sort_order"] == 5


def test_admin_created_offer_can_be_active_as_before(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/offers",
        headers=_auth_headers(admin_token),
        json=_offer_payload(is_active=True),
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_admin_partner_offer_create_empty_title_returns_400(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/offers",
        headers=_auth_headers(admin_token),
        json=_offer_payload(title="   "),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Offer title must not be empty"


def test_admin_partner_offer_create_negative_base_price_returns_400(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/offers",
        headers=_auth_headers(admin_token),
        json=_offer_payload(base_price="-0.01"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "base_price must be greater than or equal to 0"


def test_admin_partner_offer_create_discount_percent_below_zero_returns_400(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/offers",
        headers=_auth_headers(admin_token),
        json=_offer_payload(discount_percent="-0.01"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "discount_percent must be between 0 and 100"


def test_admin_partner_offer_create_discount_percent_above_100_returns_400(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_client.post(
        "/api/v1/admin/partners/1/offers",
        headers=_auth_headers(admin_token),
        json=_offer_payload(discount_percent="100.01"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "discount_percent must be between 0 and 100"


def test_admin_partner_offers_list_ordered_and_includes_partner_name(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_client.get("/api/v1/admin/partners/1/offers", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert [offer["title"] for offer in data] == [
        "First same sort",
        "Second same sort inactive",
        "Later offer",
    ]
    assert [offer["sort_order"] for offer in data] == [10, 10, 20]
    assert [offer["partner_name"] for offer in data] == ["Alpha Beauty", "Alpha Beauty", "Alpha Beauty"]


def test_admin_partner_offers_list_supports_is_active_filter(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_client.get(
        "/api/v1/admin/partners/1/offers?is_active=false",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.json()
    assert [offer["title"] for offer in data] == ["Second same sort inactive"]
    assert data[0]["is_active"] is False


def test_admin_partner_offer_get_returns_offer(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.get("/api/v1/admin/offers/1", headers=_auth_headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Later offer"
    assert data["partner_id"] == 1
    assert data["partner_name"] == "Alpha Beauty"


def test_admin_partner_offer_get_missing_offer_returns_404(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_client.get("/api/v1/admin/offers/9999", headers=_auth_headers(admin_token))

    assert response.status_code == 404
    assert response.json()["detail"] == "Offer not found"


def test_admin_partner_offer_patch_updates_fields(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.patch(
        "/api/v1/admin/offers/1",
        headers=_auth_headers(admin_token),
        json={
            "title": "  Обновленная скидка  ",
            "benefit_text": "  Новый бонус  ",
            "is_active": False,
            "sort_order": 1,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Обновленная скидка"
    assert data["benefit_text"] == "Новый бонус"
    assert data["is_active"] is False
    assert data["sort_order"] == 1
    assert data["partner_name"] == "Alpha Beauty"


def test_admin_partner_offer_patch_clears_optional_text_with_empty_string(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_client.patch(
        "/api/v1/admin/offers/1",
        headers=_auth_headers(admin_token),
        json={"benefit_text": "   ", "description": "   ", "conditions": "", "image_url": "   "},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["benefit_text"] is None
    assert data["description"] is None
    assert data["conditions"] is None
    assert data["image_url"] is None


@pytest.mark.parametrize(
    ("payload", "detail"),
    [
        ({"base_price": "-1"}, "base_price must be greater than or equal to 0"),
        ({"discount_percent": "-1"}, "discount_percent must be between 0 and 100"),
        ({"discount_percent": "101"}, "discount_percent must be between 0 and 100"),
    ],
)
def test_admin_partner_offer_patch_invalid_numeric_values_return_400(
    admin_client: TestClient,
    admin_token: str,
    payload: dict[str, str],
    detail: str,
) -> None:
    response = admin_client.patch(
        "/api/v1/admin/offers/1",
        headers=_auth_headers(admin_token),
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == detail

TINY_OFFER_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\x9cc``\x00\x00"
    b"\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _upload_file(content: bytes, filename: str, content_type: str) -> dict[str, tuple[str, bytes, str]]:
    return {"file": (filename, content, content_type)}


def test_admin_uploads_valid_image_for_offer_updates_image_url(
    admin_client: TestClient,
    admin_token: str,
) -> None:
    response = admin_client.post(
        "/api/v1/admin/offers/1/image",
        headers=_auth_headers(admin_token),
        files=_upload_file(TINY_OFFER_PNG_BYTES, "ignored-original-name.png", "image/png"),
    )

    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"url"}
    assert data["url"].startswith("/uploads/partners/1/offers/1/offer-")
    assert data["url"].endswith(".png")

    offer_response = admin_client.get("/api/v1/admin/offers/1", headers=_auth_headers(admin_token))
    assert offer_response.json()["image_url"] == data["url"]


def test_admin_offer_upload_rejects_invalid_file_type(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/offers/1/image",
        headers=_auth_headers(admin_token),
        files=_upload_file(b"<svg></svg>", "offer.svg", "image/svg+xml"),
    )

    assert response.status_code == 400


def test_admin_offer_upload_rejects_invalid_image_bytes(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/offers/1/image",
        headers=_auth_headers(admin_token),
        files=_upload_file(b"not an image", "offer.png", "image/png"),
    )

    assert response.status_code == 400


def test_admin_offer_upload_rejects_too_large_file(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/offers/1/image",
        headers=_auth_headers(admin_token),
        files=_upload_file(b"\x89PNG\r\n\x1a\n" + (b"0" * (5 * 1024 * 1024)), "offer.png", "image/png"),
    )

    assert response.status_code == 400


def test_admin_offer_upload_rejects_unauthorized_request(admin_client: TestClient) -> None:
    response = admin_client.post(
        "/api/v1/admin/offers/1/image",
        files=_upload_file(TINY_OFFER_PNG_BYTES, "offer.png", "image/png"),
    )

    assert response.status_code == 401


def test_admin_offer_upload_missing_offer_returns_404(admin_client: TestClient, admin_token: str) -> None:
    response = admin_client.post(
        "/api/v1/admin/offers/9999/image",
        headers=_auth_headers(admin_token),
        files=_upload_file(TINY_OFFER_PNG_BYTES, "offer.png", "image/png"),
    )

    assert response.status_code == 404
