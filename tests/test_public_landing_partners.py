from __future__ import annotations

from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all SQLAlchemy models for test metadata
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.category import Category
from app.models.city import City
from app.models.partner import Partner, PartnerOffer, PartnerPhoto
from app.models.user import User, UserRole


@pytest.fixture()
def public_client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    Base.metadata.create_all(bind=engine)
    with session_factory() as session:
        active_city = City(name="Новосибирск", slug="novosibirsk", is_active=True, sort_order=10)
        other_city = City(name="Череповец", slug="cherepovets", is_active=True, sort_order=20)
        inactive_city = City(name="Скрытый город", slug="hidden-city", is_active=False, sort_order=30)
        active_category = Category(name="Красота", slug="krasota", is_active=True, sort_order=10)
        other_category = Category(name="Фитнес / йога", slug="fitnes-yoga", is_active=True, sort_order=20)
        inactive_category = Category(name="Скрытая", slug="hidden-category", is_active=False, sort_order=30)
        owner = User(email="owner@example.com", role=UserRole.PARTNER.value, is_active=True)
        session.add_all([active_city, other_city, inactive_city, active_category, other_category, inactive_category, owner])
        session.flush()

        partners = [
            Partner(
                city_id=active_city.id,
                owner_user_id=owner.id,
                category_slug="krasota",
                name="Beauty Studio Sakura",
                address="ул. Примерная, 10",
                phone="+79990000000",
                social_url="https://example.com/sakura",
                logo_url="/assets/partners/sakura-logo.jpg",
                cover_url="/assets/partners/sakura-cover.jpg",
                is_active=True,
                is_verified=True,
                sort_order=10,
            ),
            Partner(city_id=active_city.id, category_slug="krasota", name="Inactive", is_active=False, is_verified=True),
            Partner(city_id=active_city.id, category_slug="krasota", name="Unverified", is_active=True, is_verified=False),
            Partner(city_id=inactive_city.id, category_slug="krasota", name="Hidden City", is_active=True, is_verified=True),
            Partner(city_id=active_city.id, category_slug="hidden-category", name="Hidden Category", is_active=True, is_verified=True),
            Partner(city_id=other_city.id, category_slug="fitnes-yoga", name="Yoga Active", is_active=True, is_verified=True),
        ]
        partners[0].categories = [active_category]
        partners[5].categories = [other_category]
        session.add_all(partners)
        session.flush()
        session.add_all(
            [
                PartnerPhoto(
                    partner_id=partners[0].id,
                    url="/uploads/partners/1/photos/photo-visible.webp",
                    alt_text="Живое фото",
                    is_active=True,
                    sort_order=5,
                ),
                PartnerPhoto(
                    partner_id=partners[0].id,
                    url="/uploads/partners/1/photos/photo-hidden.webp",
                    alt_text="Скрытое фото",
                    is_active=False,
                    sort_order=1,
                ),
                PartnerOffer(
                    partner_id=partners[0].id,
                    title="Скидка на первый визит",
                    benefit_text="-15%",
                    description="На первую процедуру для участниц клуба",
                    conditions="По предварительной записи",
                    is_active=True,
                    sort_order=10,
                ),
                PartnerOffer(
                    partner_id=partners[0].id,
                    title="Скрытая скидка",
                    discount_percent=Decimal("20"),
                    is_active=False,
                    sort_order=20,
                ),
                PartnerOffer(
                    partner_id=partners[5].id,
                    title="Пробная тренировка",
                    benefit_text="-1E+1%",
                    discount_percent=Decimal("10"),
                    is_active=True,
                    sort_order=10,
                ),
                PartnerOffer(
                    partner_id=partners[5].id,
                    title="Подарок клуба",
                    benefit_text="Подарок",
                    is_active=True,
                    sort_order=20,
                ),
                PartnerOffer(
                    partner_id=partners[5].id,
                    title="Особые условия",
                    benefit_text="2E+1",
                    is_active=True,
                    sort_order=30,
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


def test_public_landing_partners_returns_only_safe_active_public_data(public_client: TestClient) -> None:
    response = public_client.get("/api/v1/public/landing/partners?category_slug=krasota&city_slug=novosibirsk")

    assert response.status_code == 200
    data = response.json()
    assert [item["name"] for item in data["items"]] == ["Beauty Studio Sakura"]
    item = data["items"][0]
    assert item == {
        "id": item["id"],
        "name": "Beauty Studio Sakura",
        "address": "ул. Примерная, 10",
        "city_name": "Новосибирск",
        "city_slug": "novosibirsk",
        "category_title": "Красота",
        "category_slug": "krasota",
        "category": {"id": item["category"]["id"], "name": "Красота", "title": "Красота", "slug": "krasota"},
        "categories": [{"id": item["categories"][0]["id"], "name": "Красота", "title": "Красота", "slug": "krasota"}],
        "category_ids": [item["categories"][0]["id"]],
        "category_slugs": ["krasota"],
        "logo_url": "/assets/partners/sakura-logo.jpg",
        "cover_url": "/assets/partners/sakura-cover.jpg",
        "offers": [
            {
                "title": "Скидка на первый визит",
                "discount_text": "-15%",
                "description": "На первую процедуру для участниц клуба",
                "terms": "По предварительной записи",
            }
        ],
        "photos": [
            {
                "id": item["photos"][0]["id"],
                "url": "/uploads/partners/1/photos/photo-visible.webp",
                "alt_text": "Живое фото",
                "sort_order": 5,
            }
        ],
    }
    serialized = str(item)
    for forbidden_key in ("owner_user_id", "owner_email", "phone", "social_url"):
        assert forbidden_key not in serialized


def test_public_landing_partners_formats_offer_benefits_without_scientific_notation(public_client: TestClient) -> None:
    response = public_client.get("/api/v1/public/landing/partners?category_slug=fitnes-yoga&city_slug=cherepovets")

    assert response.status_code == 200
    data = response.json()
    assert [item["name"] for item in data["items"]] == ["Yoga Active"]
    assert data["items"][0]["photos"] == []
    offers = data["items"][0]["offers"]
    assert offers == [
        {
            "title": "Пробная тренировка",
            "discount_text": "-10%",
            "description": None,
            "terms": None,
        },
        {
            "title": "Подарок клуба",
            "discount_text": "Подарок",
            "description": None,
            "terms": None,
        },
        {
            "title": "Особые условия",
            "discount_text": "Специальное предложение",
            "description": None,
            "terms": None,
        },
    ]
    serialized = str(data)
    assert "1E+1" not in serialized
    assert "-1E+1%" not in serialized


def test_public_landing_partners_excludes_inactive_unverified_and_inactive_relations(public_client: TestClient) -> None:
    response = public_client.get("/api/v1/public/landing/partners")

    assert response.status_code == 200
    names = {item["name"] for item in response.json()["items"]}
    assert names == {"Beauty Studio Sakura", "Yoga Active"}
    assert "Inactive" not in names
    assert "Unverified" not in names
    assert "Hidden City" not in names
    assert "Hidden Category" not in names
    sakura = next(item for item in response.json()["items"] if item["name"] == "Beauty Studio Sakura")
    assert [offer["title"] for offer in sakura["offers"]] == ["Скидка на первый визит"]
    assert [photo["url"] for photo in sakura["photos"]] == ["/uploads/partners/1/photos/photo-visible.webp"]


def test_public_landing_category_and_city_filters_work(public_client: TestClient) -> None:
    category_response = public_client.get("/api/v1/public/landing/partners?category_slug= FITNES-YOGA ")
    city_response = public_client.get("/api/v1/public/landing/partners?city_slug= cherepovets ")

    assert category_response.status_code == 200
    assert [item["name"] for item in category_response.json()["items"]] == ["Yoga Active"]
    assert city_response.status_code == 200
    assert [item["name"] for item in city_response.json()["items"]] == ["Yoga Active"]


def test_public_landing_missing_or_inactive_category_and_city_return_empty(public_client: TestClient) -> None:
    paths = [
        "/api/v1/public/landing/partners?category_slug=missing",
        "/api/v1/public/landing/partners?category_slug=hidden-category",
        "/api/v1/public/landing/partners?city_slug=missing",
        "/api/v1/public/landing/partners?city_slug=hidden-city",
    ]

    for path in paths:
        response = public_client.get(path)
        assert response.status_code == 200
        assert response.json() == {"items": []}


def test_public_landing_limit_is_capped(public_client: TestClient) -> None:
    response = public_client.get("/api/v1/public/landing/partners?limit=300")

    assert response.status_code == 200
    assert len(response.json()["items"]) <= 30


def test_public_landing_partners_returns_multi_category_partner_in_each_category(public_client: TestClient) -> None:
    response = public_client.get("/api/v1/public/landing/partners?category_slug=krasota")
    assert response.status_code == 200
    sakura = next(item for item in response.json()["items"] if item["name"] == "Beauty Studio Sakura")
    partner_id = sakura["id"]

    manicure = Category(name="Маникюр / педикюр", slug="manikyur-pedikyur", is_active=True, sort_order=2)
    brows = Category(name="Брови / ресницы", slug="brovi-resnitsy", is_active=True, sort_order=4)
    cosmetology = Category(name="Косметология", slug="kosmetologiya", is_active=True, sort_order=5)

    session_gen = app.dependency_overrides[get_db]()
    session = next(session_gen)
    try:
        partner = session.get(Partner, partner_id)
        assert partner is not None
        partner.categories.extend([manicure, brows, cosmetology])
        session.add(partner)
        session.commit()
    finally:
        session.close()
        session_gen.close()

    requested_slugs = ["krasota", "manikyur-pedikyur", "brovi-resnitsy", "kosmetologiya"]
    expected_category_slugs = ["manikyur-pedikyur", "brovi-resnitsy", "kosmetologiya", "krasota"]
    for slug in requested_slugs:
        category_response = public_client.get(f"/api/v1/public/landing/partners?category_slug={slug}&limit=12")
        assert category_response.status_code == 200
        partner = next(item for item in category_response.json()["items"] if item["name"] == "Beauty Studio Sakura")
        assert partner["category_slug"] == slug
        assert isinstance(partner["categories"], list)
        assert [category["slug"] for category in partner["categories"]] == expected_category_slugs
        assert partner["category_slugs"] == expected_category_slugs
        assert partner["category"]["slug"] == slug


def test_public_landing_partners_unfiltered_response_contains_categories_array(public_client: TestClient) -> None:
    response = public_client.get("/api/v1/public/landing/partners?limit=12")

    assert response.status_code == 200
    partner = next(item for item in response.json()["items"] if item["name"] == "Beauty Studio Sakura")
    assert partner["category_slug"] == "krasota"
    assert isinstance(partner["categories"], list)
    assert [category["slug"] for category in partner["categories"]] == ["krasota"]
