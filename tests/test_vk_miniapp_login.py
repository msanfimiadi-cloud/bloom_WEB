from __future__ import annotations

import base64
import hmac
from collections.abc import Generator
from datetime import datetime, timezone
from hashlib import sha256
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import settings
from app.core.security import decode_access_token, hash_password, verify_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.client import ClientProfile
from app.models.user import User, UserRole
from app.services.site_credentials import decrypt_site_password
from app.services.vk_miniapp_auth import (
    extract_vk_user_id,
    parse_launch_params,
    validate_vk_ts_freshness,
    verify_vk_miniapp_signature,
)


@pytest.fixture()
def vk_miniapp_client() -> Generator[TestClient, None, None]:
    original_app_id = settings.VK_APP_ID
    original_secret = settings.VK_APP_SECRET
    original_max_age = settings.VK_MINIAPP_AUTH_MAX_AGE_SECONDS
    object.__setattr__(settings, "VK_APP_ID", "54600832")
    object.__setattr__(settings, "VK_APP_SECRET", "test-miniapp-secret")
    object.__setattr__(settings, "VK_MINIAPP_AUTH_MAX_AGE_SECONDS", 86400)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    with session_factory() as session:
        user = User(
            email="client@example.com",
            phone="+79990001234",
            password_hash=hash_password("ClientPass123"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        session.add(user)
        session.flush()
        session.add(ClientProfile(user_id=user.id, vk_user_id="123456789", is_active=True, source="vk"))
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
        object.__setattr__(settings, "VK_APP_ID", original_app_id)
        object.__setattr__(settings, "VK_APP_SECRET", original_secret)
        object.__setattr__(settings, "VK_MINIAPP_AUTH_MAX_AGE_SECONDS", original_max_age)
        engine.dispose()


def _build_launch_params(vk_user_id: str = "123456789", vk_ts: int | None = None, vk_app_id: str = "54600832") -> str:
    ts = vk_ts or int(datetime.now(timezone.utc).timestamp())
    params = {"vk_app_id": vk_app_id, "vk_platform": "desktop_web", "vk_ts": str(ts), "vk_user_id": vk_user_id}
    canonical = urlencode(sorted(params.items()))
    digest = hmac.new(settings.VK_APP_SECRET.encode("utf-8"), canonical.encode("utf-8"), sha256).digest()
    sign = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return f"{canonical}&sign={sign}"


def test_service_valid_signed_launch_params_ok() -> None:
    object.__setattr__(settings, "VK_APP_ID", "54600832")
    object.__setattr__(settings, "VK_APP_SECRET", "test-miniapp-secret")
    params = parse_launch_params(_build_launch_params())
    verify_vk_miniapp_signature(params)
    assert extract_vk_user_id(params) == "123456789"


def test_service_invalid_sign_rejected() -> None:
    params = parse_launch_params(_build_launch_params() + "bad")
    with pytest.raises(Exception):
        verify_vk_miniapp_signature(params)


def test_service_tampered_vk_user_id_rejected() -> None:
    good = _build_launch_params(vk_user_id="123456789")
    tampered = good.replace("vk_user_id=123456789", "vk_user_id=987654321")
    params = parse_launch_params(tampered)
    with pytest.raises(Exception):
        verify_vk_miniapp_signature(params)


def test_service_missing_sign_rejected() -> None:
    params = parse_launch_params(_build_launch_params().rsplit("&sign=", 1)[0])
    with pytest.raises(Exception):
        verify_vk_miniapp_signature(params)


def test_service_missing_vk_user_id_rejected() -> None:
    params = parse_launch_params(_build_launch_params().replace("&vk_user_id=123456789", ""))
    with pytest.raises(Exception):
        verify_vk_miniapp_signature(params)


def test_service_stale_vk_ts_rejected() -> None:
    stale_ts = int(datetime.now(timezone.utc).timestamp()) - (settings.VK_MINIAPP_AUTH_MAX_AGE_SECONDS + 5)
    params = parse_launch_params(_build_launch_params(vk_ts=stale_ts))
    verify_vk_miniapp_signature(params)
    with pytest.raises(Exception):
        validate_vk_ts_freshness(params)


def test_service_wrong_vk_app_id_rejected() -> None:
    params = parse_launch_params(_build_launch_params(vk_app_id="00000000"))
    with pytest.raises(Exception):
        verify_vk_miniapp_signature(params)


def test_service_non_numeric_vk_user_id_rejected() -> None:
    params = parse_launch_params(_build_launch_params(vk_user_id="not_numeric"))
    verify_vk_miniapp_signature(params)
    with pytest.raises(Exception):
        extract_vk_user_id(params)


def test_service_empty_launch_params_rejected() -> None:
    with pytest.raises(Exception):
        parse_launch_params("")


def test_vk_miniapp_login_success(vk_miniapp_client: TestClient) -> None:
    response = vk_miniapp_client.post("/api/v1/auth/vk-miniapp-login", json={"launch_params": _build_launch_params()})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["client"]["vk_user_id"] == "123456789"


def test_vk_miniapp_login_unknown_vk_user_creates_client(vk_miniapp_client: TestClient) -> None:
    response = vk_miniapp_client.post(
        "/api/v1/auth/vk-miniapp-login",
        json={"launch_params": _build_launch_params(vk_user_id="999000")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["client"]["vk_user_id"] == "999000"
    assert body["client"]["source"] == "vk-miniapp"
    assert body["user"]["role"] == UserRole.CLIENT.value


def test_vk_miniapp_login_stale_vk_ts_returns_401(vk_miniapp_client: TestClient) -> None:
    stale_ts = int(datetime.now(timezone.utc).timestamp()) - (settings.VK_MINIAPP_AUTH_MAX_AGE_SECONDS + 10)
    response = vk_miniapp_client.post(
        "/api/v1/auth/vk-miniapp-login",
        json={"launch_params": _build_launch_params(vk_ts=stale_ts)},
    )
    assert response.status_code == 401


def test_vk_miniapp_login_wrong_vk_app_id_returns_401(vk_miniapp_client: TestClient) -> None:
    response = vk_miniapp_client.post(
        "/api/v1/auth/vk-miniapp-login",
        json={"launch_params": _build_launch_params(vk_app_id="00000000")},
    )
    assert response.status_code == 401


def test_vk_miniapp_login_missing_sign_returns_401(vk_miniapp_client: TestClient) -> None:
    response = vk_miniapp_client.post(
        "/api/v1/auth/vk-miniapp-login",
        json={"launch_params": _build_launch_params().rsplit("&sign=", 1)[0]},
    )
    assert response.status_code == 401


def test_vk_miniapp_login_tampered_vk_user_id_returns_401(vk_miniapp_client: TestClient) -> None:
    launch_params = _build_launch_params(vk_user_id="123456789")
    tampered = launch_params.replace("vk_user_id=123456789", "vk_user_id=123456780")
    response = vk_miniapp_client.post("/api/v1/auth/vk-miniapp-login", json={"launch_params": tampered})
    assert response.status_code == 401


def test_vk_miniapp_login_inactive_linked_user_rejected(vk_miniapp_client: TestClient) -> None:
    session_gen = app.dependency_overrides[get_db]()
    session = next(session_gen)
    try:
        user = session.execute(select(User).where(User.email == "client@example.com")).scalar_one()
        user.is_active = False
        session.commit()
    finally:
        session_gen.close()
    response = vk_miniapp_client.post("/api/v1/auth/vk-miniapp-login", json={"launch_params": _build_launch_params()})
    assert response.status_code in (401, 403)


def test_vk_miniapp_login_wrong_role_linked_user_rejected(vk_miniapp_client: TestClient) -> None:
    session_gen = app.dependency_overrides[get_db]()
    session = next(session_gen)
    try:
        user = session.execute(select(User).where(User.email == "client@example.com")).scalar_one()
        user.role = UserRole.PARTNER.value
        session.commit()
    finally:
        session_gen.close()
    response = vk_miniapp_client.post("/api/v1/auth/vk-miniapp-login", json={"launch_params": _build_launch_params()})
    assert response.status_code in (401, 403)


def test_vk_miniapp_login_missing_vk_app_secret_returns_500(vk_miniapp_client: TestClient) -> None:
    object.__setattr__(settings, "VK_APP_SECRET", "")
    response = vk_miniapp_client.post("/api/v1/auth/vk-miniapp-login", json={"launch_params": _build_launch_params()})
    assert response.status_code == 500
    assert "VK_APP_SECRET" in response.json()["detail"]
    assert "access_token" not in response.json()


def test_vk_miniapp_login_without_body_returns_controlled_400(vk_miniapp_client: TestClient) -> None:
    response = vk_miniapp_client.post("/api/v1/auth/vk-miniapp-login")
    assert response.status_code == 400
    assert response.json() == {
        "detail": "launch_params are required",
        "handler": "vk-miniapp-login-v2",
        "entrypoint": "fed_women_club_WEB",
    }


def test_vk_miniapp_login_empty_json_returns_controlled_400(vk_miniapp_client: TestClient) -> None:
    response = vk_miniapp_client.post("/api/v1/auth/vk-miniapp-login", json={})
    assert response.status_code == 400
    assert response.json() == {
        "detail": "launch_params are required",
        "handler": "vk-miniapp-login-v2",
        "entrypoint": "fed_women_club_WEB",
    }


def test_vk_miniapp_login_params_object_path_works(vk_miniapp_client: TestClient) -> None:
    params = parse_launch_params(_build_launch_params())
    response = vk_miniapp_client.post("/api/v1/auth/vk-miniapp-login", json={"params": params})
    assert response.status_code == 200
    assert response.json()["client"]["vk_user_id"] == "123456789"


def test_vk_miniapp_login_launch_params_camel_case_path_works(vk_miniapp_client: TestClient) -> None:
    response = vk_miniapp_client.post(
        "/api/v1/auth/vk-miniapp-login",
        json={"launchParams": _build_launch_params()},
    )
    assert response.status_code == 200
    assert response.json()["client"]["vk_user_id"] == "123456789"


def test_vk_miniapp_login_raw_vk_object_path_works(vk_miniapp_client: TestClient) -> None:
    params = parse_launch_params(_build_launch_params())
    response = vk_miniapp_client.post("/api/v1/auth/vk-miniapp-login", json=params)
    assert response.status_code == 200
    assert response.json()["client"]["vk_user_id"] == "123456789"


def test_vk_miniapp_login_preflight_returns_cors_headers(vk_miniapp_client: TestClient) -> None:
    origin = "https://kosmos327-fed-women-club-mini-app-3f15.twc1.net"
    response = vk_miniapp_client.options(
        "/api/v1/auth/vk-miniapp-login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type, Accept",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "POST" in response.headers["access-control-allow-methods"]
    allow_headers = response.headers["access-control-allow-headers"].lower()
    assert "authorization" in allow_headers
    assert "content-type" in allow_headers
    assert "accept" in allow_headers


def test_vk_miniapp_login_invalid_payload_is_not_404(vk_miniapp_client: TestClient) -> None:
    response = vk_miniapp_client.post("/api/v1/auth/vk-miniapp-login", json={"launch_params": {}})
    assert response.status_code != 404


@pytest.mark.parametrize(
    "origin",
    [
        "https://m.vk.ru",
        "https://m.vk.com",
        "https://vk.com",
        "https://vk.ru",
        "https://bloomclub.ru",
    ],
)
def test_vk_miniapp_login_preflight_vk_origin_returns_cors_headers(
    vk_miniapp_client: TestClient,
    origin: str,
) -> None:
    response = vk_miniapp_client.options(
        "/api/v1/auth/vk-miniapp-login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()


def test_api_v1_auth_vk_miniapp_login_route_is_registered() -> None:
    target = "/api/v1/auth/vk-miniapp-login"
    post_routes = {route.path for route in app.router.routes if "POST" in getattr(route, "methods", set())}
    assert target in post_routes


def test_runtime_info_returns_vk_miniapp_handler_marker(vk_miniapp_client: TestClient) -> None:
    response = vk_miniapp_client.get("/api/v1/runtime-info")
    assert response.status_code == 200
    assert response.json() == {
        "app": "fed_women_club_WEB",
        "handler": "vk-miniapp-login-v2",
        "endpoint": "/api/v1/auth/vk-miniapp-login",
    }



def test_vk_miniapp_first_login_creates_site_credentials(vk_miniapp_client: TestClient) -> None:
    response = vk_miniapp_client.post(
        "/api/v1/auth/vk-miniapp-login",
        json={"launch_params": _build_launch_params(vk_user_id="555001")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["generated_account"] is True
    assert body["client"]["vk_user_id"] == "555001"
    assert "site_password" not in body
    assert "site_password" not in body["user"]
    assert body["access_token"]

    payload = decode_access_token(body["access_token"])
    assert "site_password" not in payload

    session_gen = app.dependency_overrides[get_db]()
    session = next(session_gen)
    try:
        profile = session.execute(select(ClientProfile).where(ClientProfile.vk_user_id == "555001")).scalar_one()
        user = session.get(User, profile.user_id)
        assert user is not None
        assert user.site_login == "bloom_vk_555001"
        assert user.password_hash is not None
        assert user.encrypted_site_password is not None
        assert user.site_credentials_created_at is not None
        plain_password = decrypt_site_password(user.encrypted_site_password)
        assert plain_password != user.password_hash
        assert verify_password(plain_password, user.password_hash)
    finally:
        session_gen.close()


def test_vk_miniapp_repeated_login_reuses_same_account_and_credentials(vk_miniapp_client: TestClient) -> None:
    launch_params = _build_launch_params(vk_user_id="555002")
    first = vk_miniapp_client.post("/api/v1/auth/vk-miniapp-login", json={"launch_params": launch_params})
    assert first.status_code == 200

    session_gen = app.dependency_overrides[get_db]()
    session = next(session_gen)
    try:
        profile = session.execute(select(ClientProfile).where(ClientProfile.vk_user_id == "555002")).scalar_one()
        user = session.get(User, profile.user_id)
        first_user_id = user.id
        first_profile_id = profile.id
        first_site_login = user.site_login
        first_password_hash = user.password_hash
        first_encrypted_password = user.encrypted_site_password
    finally:
        session_gen.close()

    second = vk_miniapp_client.post("/api/v1/auth/vk-miniapp-login", json={"launch_params": launch_params})
    assert second.status_code == 200
    assert second.json()["generated_account"] is False

    session_gen = app.dependency_overrides[get_db]()
    session = next(session_gen)
    try:
        profiles = session.execute(select(ClientProfile).where(ClientProfile.vk_user_id == "555002")).scalars().all()
        assert len(profiles) == 1
        user_count = session.query(User).count()
        assert user_count == 2
        profile = profiles[0]
        user = session.get(User, profile.user_id)
        assert profile.id == first_profile_id
        assert user.id == first_user_id
        assert user.site_login == first_site_login
        assert user.password_hash == first_password_hash
        assert user.encrypted_site_password == first_encrypted_password
    finally:
        session_gen.close()


def test_vk_miniapp_generated_site_login_works_for_user_login(vk_miniapp_client: TestClient) -> None:
    login_response = vk_miniapp_client.post(
        "/api/v1/auth/vk-miniapp-login",
        json={"launch_params": _build_launch_params(vk_user_id="555003")},
    )
    token = login_response.json()["access_token"]
    credentials_response = vk_miniapp_client.get(
        "/api/v1/clients/me/site-credentials",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert credentials_response.status_code == 200
    credentials = credentials_response.json()

    response = vk_miniapp_client.post(
        "/api/v1/auth/user-login",
        json={"login": credentials["site_login"], "password": credentials["site_password"]},
    )
    assert response.status_code == 200
    assert response.json()["user"]["role"] == UserRole.CLIENT.value


def test_client_profile_exposes_masked_site_credentials_only(vk_miniapp_client: TestClient) -> None:
    login_response = vk_miniapp_client.post(
        "/api/v1/auth/vk-miniapp-login",
        json={"launch_params": _build_launch_params(vk_user_id="555004")},
    )
    token = login_response.json()["access_token"]

    response = vk_miniapp_client.get("/api/v1/clients/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["site_login"] == "bloom_vk_555004"
    assert body["site_password_masked"] == "*****"
    assert body["site_password_available"] is True
    assert "site_password" not in body


def test_site_credentials_endpoint_requires_auth(vk_miniapp_client: TestClient) -> None:
    response = vk_miniapp_client.get("/api/v1/clients/me/site-credentials")

    assert response.status_code == 401


def test_site_credentials_endpoint_returns_only_current_client_credentials(vk_miniapp_client: TestClient) -> None:
    first = vk_miniapp_client.post(
        "/api/v1/auth/vk-miniapp-login",
        json={"launch_params": _build_launch_params(vk_user_id="555005")},
    ).json()
    second = vk_miniapp_client.post(
        "/api/v1/auth/vk-miniapp-login",
        json={"launch_params": _build_launch_params(vk_user_id="555006")},
    ).json()

    first_credentials = vk_miniapp_client.get(
        "/api/v1/clients/me/site-credentials",
        headers={"Authorization": f"Bearer {first['access_token']}"},
    ).json()
    second_credentials = vk_miniapp_client.get(
        "/api/v1/clients/me/site-credentials",
        headers={"Authorization": f"Bearer {second['access_token']}"},
    ).json()

    assert first_credentials["site_login"] == "bloom_vk_555005"
    assert second_credentials["site_login"] == "bloom_vk_555006"
    assert first_credentials["site_password"] != second_credentials["site_password"]


def test_client_profile_patch_updates_profile_fields_without_changing_credentials(vk_miniapp_client: TestClient) -> None:
    login_response = vk_miniapp_client.post(
        "/api/v1/auth/vk-miniapp-login",
        json={"launch_params": _build_launch_params(vk_user_id="555007")},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    before = vk_miniapp_client.get("/api/v1/clients/me/site-credentials", headers=headers).json()

    response = vk_miniapp_client.patch(
        "/api/v1/clients/me",
        headers=headers,
        json={
            "name": "Анна Клиент",
            "phone": "+79995550707",
            "email": "anna.client@example.com",
            "city": "Новосибирск",
        },
    )

    assert response.status_code == 200
    profile = response.json()
    assert profile["full_name"] == "Анна Клиент"
    assert profile["phone"] == "+79995550707"
    assert profile["email"] == "anna.client@example.com"
    assert profile["contact_email"] == "anna.client@example.com"
    assert profile["city"] == "Новосибирск"
    after = vk_miniapp_client.get("/api/v1/clients/me/site-credentials", headers=headers).json()
    assert after == before


def test_documented_risk_vk_login_uses_vk_user_id_only_not_existing_phone_or_email(
    vk_miniapp_client: TestClient,
) -> None:
    """Documentation regression: VK login must not silently merge by unverified phone/email today."""
    session_gen = app.dependency_overrides[get_db]()
    session = next(session_gen)
    try:
        existing_user = User(
            email="same-person@example.com",
            phone="+79990007777",
            password_hash=hash_password("ClientPass123"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        session.add(existing_user)
        session.flush()
        existing_profile = ClientProfile(
            user_id=existing_user.id,
            contact_email="same-person@example.com",
            is_active=True,
            source="web",
        )
        session.add(existing_profile)
        session.commit()
        existing_user_id = existing_user.id
        existing_profile_id = existing_profile.id
    finally:
        session_gen.close()

    response = vk_miniapp_client.post(
        "/api/v1/auth/vk-miniapp-login",
        json={"launch_params": _build_launch_params(vk_user_id="777777")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["client"]["vk_user_id"] == "777777"
    assert body["client"]["id"] != existing_profile_id
    assert body["user"]["id"] != existing_user_id

    session_gen = app.dependency_overrides[get_db]()
    session = next(session_gen)
    try:
        original_profile = session.get(ClientProfile, existing_profile_id)
        new_profile = session.execute(select(ClientProfile).where(ClientProfile.vk_user_id == "777777")).scalar_one()
        assert original_profile is not None
        assert original_profile.vk_user_id is None
        assert new_profile.user_id != existing_user_id
    finally:
        session_gen.close()
