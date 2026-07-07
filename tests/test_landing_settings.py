from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

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
from app.models.partner import Partner
from app.models.user import AdminUser, User, UserRole
from app.models.verification import PrivilegeVerificationSession, PrivilegeVerificationStatus

DEFAULT_GIVEAWAY_EMPTY_TEXT = "Информация о призах появится после настройки розыгрыша."


@pytest.fixture()
def landing_client() -> Generator[TestClient, None, None]:
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


def _auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "StrongPassword123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_public_landing_stats_returns_start_values(landing_client: TestClient) -> None:
    response = landing_client.get("/api/v1/public/landing/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["members_count"] == 125
    assert data["members_count_base"] == 125
    assert data["members_count_real"] == 0
    assert data["partners_count"] == 18
    assert data["partners_count_base"] == 18
    assert data["partners_count_real"] == 0
    assert data["savings_total"] == 53500
    assert data["savings_total_base"] == 53500
    assert data["savings_total_real"] == 0
    assert data["giveaway_title"] == "Розыгрыш месяца"
    assert data["giveaway_empty_text"] == DEFAULT_GIVEAWAY_EMPTY_TEXT


def test_public_members_count_grows_when_client_user_appears(landing_client: TestClient) -> None:
    with next(app.dependency_overrides[get_db]()) as session:
        session.add(User(email="client@example.com", role=UserRole.CLIENT.value, is_active=True))
        session.commit()

    response = landing_client.get("/api/v1/public/landing/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["members_count"] == 126
    assert data["members_count_base"] == 125
    assert data["members_count_real"] == 1


def test_public_landing_stats_counts_base_plus_active_partners(landing_client: TestClient) -> None:
    with next(app.dependency_overrides[get_db]()) as session:
        city = City(name="Новосибирск", slug="novosibirsk", is_active=True)
        session.add(city)
        session.flush()
        session.add_all(
            [
                Partner(city_id=city.id, name="Active partner 1", is_active=True),
                Partner(city_id=city.id, name="Active partner 2", is_active=True),
                Partner(city_id=city.id, name="Inactive partner", is_active=False),
            ]
        )
        session.commit()

    response = landing_client.get("/api/v1/public/landing/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["partners_count"] == 20
    assert data["partners_count_base"] == 18
    assert data["partners_count_real"] == 2


def test_public_landing_alias_returns_dynamic_stats(landing_client: TestClient) -> None:
    response = landing_client.get("/api/v1/public/landing")

    assert response.status_code == 200
    data = response.json()
    assert data["partners_count_base"] == 18
    assert data["savings_total_base"] == 53500


def test_public_landing_stats_uses_real_savings_helper(landing_client: TestClient) -> None:
    response = landing_client.get("/api/v1/public/landing/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["savings_total"] == 53500
    assert data["savings_total_base"] == 53500
    assert data["savings_total_real"] == 0


def test_public_landing_stats_adds_confirmed_real_savings(landing_client: TestClient) -> None:
    with next(app.dependency_overrides[get_db]()) as session:
        city = City(name="Омск", slug="omsk", is_active=True)
        user = User(email="savings-client@example.com", role=UserRole.CLIENT.value, is_active=True)
        session.add_all([city, user])
        session.flush()
        client = ClientProfile(user_id=user.id, selected_city_id=city.id, is_active=True)
        partner = Partner(city_id=city.id, name="Savings partner", is_active=True)
        session.add_all([client, partner])
        session.flush()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session.add_all(
            [
                PrivilegeVerificationSession(
                    client_id=client.id,
                    partner_id=partner.id,
                    code="SAVE01",
                    status=PrivilegeVerificationStatus.confirmed.value,
                    expires_at=expires_at,
                    confirmed_at=datetime.now(timezone.utc),
                    saving_amount=Decimal("1500.00"),
                ),
                PrivilegeVerificationSession(
                    client_id=client.id,
                    partner_id=partner.id,
                    code="DRAFT1",
                    status=PrivilegeVerificationStatus.active.value,
                    expires_at=expires_at,
                    saving_amount=Decimal("9000.00"),
                ),
            ]
        )
        session.commit()

    response = landing_client.get("/api/v1/public/landing/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["savings_total"] == 55000
    assert data["savings_total_base"] == 53500
    assert data["savings_total_real"] == 1500


def test_admin_landing_settings_patch_saves_public_stats_and_giveaway(landing_client: TestClient) -> None:
    response = landing_client.patch(
        "/api/v1/admin/landing-settings",
        headers=_auth_headers(landing_client),
        json={
            "partners_count_display": 24,
            "savings_total": 75000,
            "giveaway_title": "Розыгрыш месяца",
            "giveaway_current": "Сертификат в SPA",
            "giveaway_subtitle": "для активных участниц",
            "giveaway_empty_text": "Скоро расскажем о призах месяца.",
            "giveaway_items": [
                {"title": "Сертификат в SPA", "description": "Главный приз", "is_active": True, "sort_order": 10},
                {"title": "Beauty box", "description": "Дополнительный приз", "is_active": True, "sort_order": 20},
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["partners_count_display"] == 24
    assert data["savings_total"] == 75000
    assert data["giveaway_current"] == "Сертификат в SPA"
    assert data["giveaway_empty_text"] == "Скоро расскажем о призах месяца."
    assert [item["title"] for item in data["giveaway_items"]] == ["Сертификат в SPA", "Beauty box"]


def test_admin_landing_settings_patch_updates_giveaway_empty_text(landing_client: TestClient) -> None:
    response = landing_client.patch(
        "/api/v1/admin/landing-settings",
        headers=_auth_headers(landing_client),
        json={"giveaway_empty_text": "Призы появятся после запуска нового розыгрыша."},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["giveaway_empty_text"] == "Призы появятся после запуска нового розыгрыша."


def test_public_landing_stats_returns_configured_giveaway_empty_text(landing_client: TestClient) -> None:
    headers = _auth_headers(landing_client)
    response = landing_client.patch(
        "/api/v1/admin/landing-settings",
        headers=headers,
        json={"giveaway_empty_text": "Итоги и призы опубликуем в этом разделе.", "giveaway_items": []},
    )
    assert response.status_code == 200

    public_response = landing_client.get("/api/v1/public/landing/stats")

    assert public_response.status_code == 200
    data = public_response.json()
    assert data["giveaway_empty_text"] == "Итоги и призы опубликуем в этом разделе."
    assert data["giveaway_current"] == ""
    assert data["giveaway_items"] == []


def test_admin_landing_settings_patch_updates_bases_used_by_public_stats(landing_client: TestClient) -> None:
    with next(app.dependency_overrides[get_db]()) as session:
        city = City(name="Томск", slug="tomsk", is_active=True)
        session.add(city)
        session.flush()
        session.add(Partner(city_id=city.id, name="Active partner", is_active=True))
        session.commit()

    response = landing_client.patch(
        "/api/v1/admin/landing-settings",
        headers=_auth_headers(landing_client),
        json={"partners_count_base": 30, "savings_total_base": 90000},
    )

    assert response.status_code == 200
    admin_data = response.json()
    assert admin_data["partners_count_display"] == 30
    assert admin_data["partners_count_base"] == 30
    assert admin_data["partners_count"] == 31
    assert admin_data["savings_total"] == 90000
    assert admin_data["savings_total_base"] == 90000
    assert admin_data["savings_total_display"] == 90000

    public_response = landing_client.get("/api/v1/public/landing/stats")

    assert public_response.status_code == 200
    public_data = public_response.json()
    assert public_data["partners_count"] == 31
    assert public_data["partners_count_base"] == 30
    assert public_data["partners_count_real"] == 1
    assert public_data["savings_total"] == 90000
    assert public_data["savings_total_base"] == 90000
    assert public_data["savings_total_real"] == 0


def test_public_landing_stats_returns_updated_giveaway(landing_client: TestClient) -> None:
    headers = _auth_headers(landing_client)
    response = landing_client.patch(
        "/api/v1/admin/landing-settings",
        headers=headers,
        json={
            "giveaway_current": "Fallback prize",
            "giveaway_items": [
                {"title": "Неактивный приз", "is_active": False, "sort_order": 0},
                {"title": "Главный активный приз", "is_active": True, "sort_order": 1},
            ],
        },
    )
    assert response.status_code == 200

    public_response = landing_client.get("/api/v1/public/landing/stats")

    assert public_response.status_code == 200
    data = public_response.json()
    assert data["giveaway_current"] == "Главный активный приз"
    assert data["giveaway_empty_text"] == DEFAULT_GIVEAWAY_EMPTY_TEXT
    assert data["giveaway_items"][0]["title"] == "Неактивный приз"


def test_frontend_landing_hero_stats_do_not_use_legacy_hardcodes() -> None:
    text = Path("frontend/src/main.js").read_text(encoding="utf-8")

    assert "327" not in text
    assert "50+" not in text
    assert "183 000 ₽" not in text
    assert "Dyson" not in text


def test_frontend_landing_settings_copy_marks_partner_and_savings_values_as_base() -> None:
    text = Path("frontend/src/main.js").read_text(encoding="utf-8")

    assert "Ручное значение на главной" not in text
    for expected_text in (
        "Базовое число партнёров",
        "Базовая сумма экономии",
        "База + активные партнёры",
        "База + реальная экономия",
        "Текст, если призы ещё не заполнены",
        "Показывается на главной, когда призы розыгрыша ещё не настроены.",
    ):
        assert expected_text in text
