from __future__ import annotations

from datetime import datetime, timezone


import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
import app.models  # noqa: F401
from app.bots.telegram_bot import TelegramBotLoginCodeService, TelegramBotUserIdentity
from app.bots.vk_bot import VkBotService, VkUserIdentity
from app.models.client import BrowserLoginCode, ClientProfile, ClientReferral
from app.models.user import User, UserRole
from app.services.browser_login_codes import BrowserLoginCodeService
from app.services.referrals import ReferralError, validate_referral_for_new_client


@pytest.fixture()
def session_factory():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    yield factory
    engine.dispose()


@pytest.fixture()
def db_session(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


def _create_profile(db_session, *, telegram_user_id: str | None = None, vk_user_id: str | None = None) -> ClientProfile:
    user = User(role=UserRole.CLIENT.value, is_active=True)
    db_session.add(user)
    db_session.flush()
    profile = ClientProfile(user_id=user.id, telegram_user_id=telegram_user_id, vk_user_id=vk_user_id, is_active=True)
    db_session.add(profile)
    db_session.flush()
    return profile


def test_login_code_success_returns_jwt_and_is_single_use(client, db_session):
    profile = _create_profile(db_session, telegram_user_id="tg-code")
    code, record = BrowserLoginCodeService(db_session).create_code(provider="telegram", provider_user_id="tg-code")
    db_session.commit()

    response = client.post("/api/v1/auth/login-code", json={"code": code.lower()})

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["client"]["id"] == profile.id
    db_session.refresh(record)
    assert record.used_at is not None
    second = client.post("/api/v1/auth/login-code", json={"code": code})
    assert second.status_code == 403
    assert second.json()["detail"] == "code_already_used"


def test_login_code_expired_and_invalid_rejected(client, db_session):
    _create_profile(db_session, telegram_user_id="tg-expired-code")
    code, _ = BrowserLoginCodeService(db_session).create_code(provider="telegram", provider_user_id="tg-expired-code")
    record = db_session.query(BrowserLoginCode).filter_by(login_code=code).one()
    record.expires_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    db_session.commit()

    assert client.post("/api/v1/auth/login-code", json={"code": code}).status_code == 403
    assert client.post("/api/v1/auth/login-code", json={"code": "BC-NOPE99"}).status_code == 404


def test_new_login_code_invalidates_previous_unused_code(db_session):
    service = BrowserLoginCodeService(db_session)
    first, first_record = service.create_code(provider="vk", provider_user_id="vk-1")
    second, second_record = service.create_code(provider="vk", provider_user_id="vk-1")
    db_session.commit()

    assert first != second
    db_session.refresh(first_record)
    db_session.refresh(second_record)
    assert first_record.used_at is not None
    assert second_record.used_at is None


def test_telegram_bot_generates_login_code(session_factory):
    bot = TelegramBotLoginCodeService(session_factory=session_factory)
    response = bot.create_browser_login_code(TelegramBotUserIdentity(telegram_user_id="123", username="bloom"))

    assert response.code.startswith("BC-")
    assert response.app_url == "https://app.bloomclub.ru"
    with session_factory() as db:
        record = db.query(BrowserLoginCode).one()
        assert record.provider == "telegram"
        assert record.provider_user_id == "123"
        assert record.source == "telegram_bot"


def test_vk_bot_generates_login_code(session_factory):
    bot = VkBotService(token="vk-token", group_id="42", session_factory=session_factory)
    response = bot.create_browser_login_code(VkUserIdentity(vk_user_id="456", display_name="Bloom User"))

    assert response.code.startswith("BC-")
    assert response.app_url == "https://app.bloomclub.ru"
    with session_factory() as db:
        record = db.query(BrowserLoginCode).one()
        assert record.provider == "vk"
        assert record.provider_user_id == "456"
        assert record.display_name == "Bloom User"
        assert record.source == "vk_bot"


def _internal_login_code_payload(provider: str = "telegram", provider_user_id: str = "tg-internal") -> dict[str, str]:
    return {
        "provider": provider,
        "provider_user_id": provider_user_id,
        "source": f"{provider}_bot",
        "username": "username",
        "first_name": "First",
        "last_name": "Last",
    }


def test_internal_login_code_requires_bot_service_token(client):
    response = client.post("/api/v1/internal/login-code", json=_internal_login_code_payload())

    assert response.status_code in {401, 403}


def test_internal_login_code_with_valid_bot_service_token_returns_code(client, db_session):
    from app.core.config import settings

    response = client.post(
        "/api/v1/internal/login-code",
        headers={"Authorization": f"Bearer {settings.BOT_SERVICE_TOKEN}"},
        json=_internal_login_code_payload(provider_user_id="tg-internal-ok"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["login_code"].startswith("BC-")
    assert payload["expires_in"] == 300
    record = db_session.query(BrowserLoginCode).filter_by(login_code=payload["login_code"]).one()
    assert record.provider == "telegram"
    assert record.provider_user_id == "tg-internal-ok"
    assert record.username == "username"
    assert record.display_name == "First Last"
    assert record.source == "telegram_bot"


def test_internal_login_code_can_be_used_by_auth_login_code(client, db_session):
    from app.core.config import settings

    profile = _create_profile(db_session, telegram_user_id="tg-internal-auth")
    response = client.post(
        "/api/v1/internal/login-code",
        headers={"Authorization": f"Bearer {settings.BOT_SERVICE_TOKEN}"},
        json=_internal_login_code_payload(provider_user_id="tg-internal-auth"),
    )
    assert response.status_code == 200

    auth_response = client.post("/api/v1/auth/login-code", json={"code": response.json()["login_code"]})

    assert auth_response.status_code == 200
    auth_payload = auth_response.json()
    assert auth_payload["access_token"]
    assert auth_payload["client"]["id"] == profile.id


def test_internal_login_code_second_code_invalidates_first(client):
    from app.core.config import settings

    headers = {"Authorization": f"Bearer {settings.BOT_SERVICE_TOKEN}"}
    first = client.post(
        "/api/v1/internal/login-code",
        headers=headers,
        json=_internal_login_code_payload(provider="telegram", provider_user_id="tg-reissue"),
    )
    second = client.post(
        "/api/v1/internal/login-code",
        headers=headers,
        json=_internal_login_code_payload(provider="telegram", provider_user_id="tg-reissue"),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["login_code"] != second.json()["login_code"]
    assert client.post("/api/v1/auth/login-code", json={"code": first.json()["login_code"]}).status_code == 403


def test_internal_login_code_supports_telegram_and_vk(client, db_session):
    from app.core.config import settings

    headers = {"Authorization": f"Bearer {settings.BOT_SERVICE_TOKEN}"}
    telegram = client.post(
        "/api/v1/internal/login-code",
        headers=headers,
        json=_internal_login_code_payload(provider="telegram", provider_user_id="tg-provider"),
    )
    vk = client.post(
        "/api/v1/internal/login-code",
        headers=headers,
        json=_internal_login_code_payload(provider="vk", provider_user_id="vk-provider"),
    )

    assert telegram.status_code == 200
    assert vk.status_code == 200
    records = {record.provider: record for record in db_session.query(BrowserLoginCode).all()}
    assert records["telegram"].provider_user_id == "tg-provider"
    assert records["vk"].provider_user_id == "vk-provider"


def test_telegram_login_code_redemption_creates_visible_client(client, db_session):
    code, _ = BrowserLoginCodeService(db_session).create_code(
        provider="telegram",
        provider_user_id="tg-new-visible",
        display_name="Visible Telegram",
        username="visible_tg",
        source="telegram_bot",
    )
    db_session.commit()

    response = client.post("/api/v1/auth/login-code", json={"code": code})

    assert response.status_code == 200
    profile = db_session.query(ClientProfile).filter_by(telegram_user_id="tg-new-visible").one()
    assert profile.user.role == UserRole.CLIENT.value
    assert profile.telegram_username == "visible_tg"
    assert profile.identity_links[0].provider == "telegram"


def test_vk_login_code_redemption_creates_visible_client(client, db_session):
    code, _ = BrowserLoginCodeService(db_session).create_code(
        provider="vk",
        provider_user_id="vk-new-visible",
        display_name="Visible VK",
        username="vk_domain",
        source="vk_bot",
    )
    db_session.commit()

    response = client.post("/api/v1/auth/login-code", json={"code": code})

    assert response.status_code == 200
    profile = db_session.query(ClientProfile).filter_by(vk_user_id="vk-new-visible").one()
    assert profile.user.role == UserRole.CLIENT.value
    assert profile.vk_username == "vk_domain"
    assert profile.identity_links[0].provider == "vk"


def test_repeated_telegram_login_code_reuses_same_client(client, db_session):
    first_code, _ = BrowserLoginCodeService(db_session).create_code(provider="telegram", provider_user_id="tg-repeat-visible", username="first")
    db_session.commit()
    first = client.post("/api/v1/auth/login-code", json={"code": first_code})
    assert first.status_code == 200
    first_client_id = first.json()["client"]["id"]

    second_code, _ = BrowserLoginCodeService(db_session).create_code(provider="telegram", provider_user_id="tg-repeat-visible", username="second")
    db_session.commit()
    second = client.post("/api/v1/auth/login-code", json={"code": second_code})

    assert second.status_code == 200
    assert second.json()["client"]["id"] == first_client_id
    assert db_session.query(ClientProfile).filter_by(telegram_user_id="tg-repeat-visible").count() == 1
    assert db_session.query(ClientProfile).filter_by(telegram_user_id="tg-repeat-visible").one().telegram_username == "second"



def test_existing_telegram_login_code_user_with_referral_returns_first_login_error(client, db_session):
    existing = _create_profile(db_session, telegram_user_id="tg-existing-ref")
    referrer = _create_profile(db_session, telegram_user_id="tg-referrer")
    referrer.referral_code = "REF12345"
    code, _ = BrowserLoginCodeService(db_session).create_code(provider="telegram", provider_user_id="tg-existing-ref")
    db_session.commit()

    response = client.post("/api/v1/auth/login-code", json={"code": code, "referral_code": "REF12345"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Личный кабинет уже был создан ранее. Реферальный код можно использовать только при первом входе."
    assert db_session.query(ClientProfile).filter_by(telegram_user_id="tg-existing-ref").count() == 1
    assert db_session.get(ClientProfile, existing.id).referred_by_referral_id is None


def test_new_telegram_login_code_user_with_valid_referral_preserves_telegram_data(client, db_session):
    referrer = _create_profile(db_session, telegram_user_id="tg-referrer-valid")
    referrer.referral_code = "VALID123"
    code, _ = BrowserLoginCodeService(db_session).create_code(
        provider="telegram",
        provider_user_id="tg-new-ref",
        display_name="Telegram New",
        username="new_tg",
        photo_url="https://example.com/avatar.jpg",
    )
    db_session.commit()

    response = client.post("/api/v1/auth/login-code", json={"code": code, "referral_code": "VALID123"})

    assert response.status_code == 200
    profile = db_session.query(ClientProfile).filter_by(telegram_user_id="tg-new-ref").one()
    assert profile.telegram_username == "new_tg"
    assert profile.telegram_first_name == "Telegram"
    assert profile.telegram_last_name == "New"
    assert profile.telegram_photo_url == "https://example.com/avatar.jpg"
    referral = db_session.query(ClientReferral).filter_by(referred_client_id=profile.id).one()
    assert referral.referrer_client_id == referrer.id
    assert profile.referred_by_referral_id == referral.id


def test_new_telegram_login_code_user_with_invalid_referral_does_not_create_profile(client, db_session):
    code, _ = BrowserLoginCodeService(db_session).create_code(provider="telegram", provider_user_id="tg-invalid-ref")
    db_session.commit()

    response = client.post("/api/v1/auth/login-code", json={"code": code, "referral_code": "NOPE1234"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Реферальный код не найден или недействителен."
    assert db_session.query(ClientProfile).filter_by(telegram_user_id="tg-invalid-ref").count() == 0


def test_new_telegram_login_code_user_with_own_referral_does_not_create_profile(client, db_session):
    owner = _create_profile(db_session, telegram_user_id="tg-own-ref")
    owner.referral_code = "OWN12345"
    # Simulate a missing identity link path; legacy provider lookup still identifies self before creation.
    owner.telegram_user_id = None
    db_session.flush()
    owner.telegram_user_id = "tg-own-ref"
    code, _ = BrowserLoginCodeService(db_session).create_code(provider="telegram", provider_user_id="tg-own-ref")
    db_session.commit()

    response = client.post("/api/v1/auth/login-code", json={"code": code, "referral_code": "OWN12345"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Личный кабинет уже был создан ранее. Реферальный код можно использовать только при первом входе."
    assert db_session.query(ClientProfile).filter_by(telegram_user_id="tg-own-ref").count() == 1


def test_relogin_after_referral_was_applied_does_not_overwrite_referral(client, db_session):
    first_referrer = _create_profile(db_session, telegram_user_id="tg-first-referrer")
    first_referrer.referral_code = "FIRST123"
    second_referrer = _create_profile(db_session, telegram_user_id="tg-second-referrer")
    second_referrer.referral_code = "SECOND12"
    code, _ = BrowserLoginCodeService(db_session).create_code(provider="telegram", provider_user_id="tg-relogin-ref")
    db_session.commit()
    first = client.post("/api/v1/auth/login-code", json={"code": code, "referral_code": "FIRST123"})
    assert first.status_code == 200
    profile_id = first.json()["client"]["id"]
    original_referral_id = db_session.get(ClientProfile, profile_id).referred_by_referral_id

    second_code, _ = BrowserLoginCodeService(db_session).create_code(provider="telegram", provider_user_id="tg-relogin-ref")
    db_session.commit()
    second = client.post("/api/v1/auth/login-code", json={"code": second_code, "referral_code": "SECOND12"})

    assert second.status_code == 400
    assert db_session.get(ClientProfile, profile_id).referred_by_referral_id == original_referral_id
    assert db_session.query(ClientReferral).filter_by(referred_client_id=profile_id).count() == 1


def test_no_duplicate_client_profile_for_same_provider_user_id(client, db_session):
    first_code, _ = BrowserLoginCodeService(db_session).create_code(provider="telegram", provider_user_id="tg-no-dupe")
    db_session.commit()
    assert client.post("/api/v1/auth/login-code", json={"code": first_code}).status_code == 200
    second_code, _ = BrowserLoginCodeService(db_session).create_code(provider="telegram", provider_user_id="tg-no-dupe")
    db_session.commit()
    assert client.post("/api/v1/auth/login-code", json={"code": second_code}).status_code == 200

    assert db_session.query(ClientProfile).filter_by(telegram_user_id="tg-no-dupe").count() == 1



def test_referral_validation_rejects_same_provider_user_id_before_creation(db_session):
    owner = _create_profile(db_session, telegram_user_id="tg-self-validation")
    owner.referral_code = "SELFVAL1"
    db_session.commit()

    with pytest.raises(ReferralError) as exc_info:
        validate_referral_for_new_client(
            db_session,
            "SELFVAL1",
            provider="telegram",
            provider_user_id="tg-self-validation",
        )

    assert exc_info.value.detail == "Нельзя использовать собственный реферальный код."
