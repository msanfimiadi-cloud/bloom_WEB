from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all SQLAlchemy models for test metadata
from app.api.deps import require_partner
from app.core.security import decode_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import AdminUser, User, UserRole


@pytest.fixture()
def unified_auth_client() -> Generator[TestClient, None, None]:
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
        session.add_all(
            [
                User(
                    email="partner@example.com",
                    phone="+79990000001",
                    password_hash=hash_password("PartnerPassword123"),
                    role=UserRole.PARTNER.value,
                    is_active=True,
                ),
                User(
                    email="client@example.com",
                    phone="+79990000002",
                    password_hash=hash_password("ClientPassword123"),
                    role=UserRole.CLIENT.value,
                    is_active=True,
                ),
                User(
                    email="inactive@example.com",
                    phone="+79990000003",
                    password_hash=hash_password("InactivePassword123"),
                    role=UserRole.PARTNER.value,
                    is_active=False,
                ),
                User(
                    email="nopassword@example.com",
                    phone="+79990000004",
                    password_hash=None,
                    role=UserRole.PARTNER.value,
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


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_login(client: TestClient, login: str, password: str) -> str:
    response = client.post("/api/v1/auth/user-login", json={"login": login, "password": password})
    assert response.status_code == 200
    return str(response.json()["access_token"])


def test_admin_login_still_authenticates_admin_user(unified_auth_client: TestClient) -> None:
    response = unified_auth_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"] == {"id": 1, "email": "admin@example.com", "role": "admin"}
    assert decode_access_token(data["access_token"])["sub"] == "1"


def test_user_login_with_partner_email_returns_token_and_role(unified_auth_client: TestClient) -> None:
    response = unified_auth_client.post(
        "/api/v1/auth/user-login",
        json={"login": "  PARTNER@example.com  ", "password": "PartnerPassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"] == {
        "id": 1,
        "email": "partner@example.com",
        "phone": "+79990000001",
        "role": "partner",
    }
    assert decode_access_token(data["access_token"])["sub"] == "user:1"


def test_user_login_with_phone_returns_token(unified_auth_client: TestClient) -> None:
    response = unified_auth_client.post(
        "/api/v1/auth/user-login",
        json={"login": "+79990000001", "password": "PartnerPassword123"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "partner"


def test_user_login_rejects_wrong_password(unified_auth_client: TestClient) -> None:
    response = unified_auth_client.post(
        "/api/v1/auth/user-login",
        json={"login": "partner@example.com", "password": "WrongPassword"},
    )

    assert response.status_code == 401


def test_user_login_rejects_inactive_user(unified_auth_client: TestClient) -> None:
    response = unified_auth_client.post(
        "/api/v1/auth/user-login",
        json={"login": "inactive@example.com", "password": "InactivePassword123"},
    )

    assert response.status_code == 401


def test_user_login_rejects_user_without_password_hash(unified_auth_client: TestClient) -> None:
    response = unified_auth_client.post(
        "/api/v1/auth/user-login",
        json={"login": "nopassword@example.com", "password": "AnyPassword123"},
    )

    assert response.status_code == 401


def test_user_me_with_unified_user_token_returns_user(unified_auth_client: TestClient) -> None:
    token = _user_login(unified_auth_client, "partner@example.com", "PartnerPassword123")

    response = unified_auth_client.get("/api/v1/auth/user-me", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "email": "partner@example.com",
        "phone": "+79990000001",
        "role": "partner",
    }


def test_user_me_with_admin_user_token_returns_401(unified_auth_client: TestClient) -> None:
    login_response = unified_auth_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPassword123"},
    )
    token = login_response.json()["access_token"]

    response = unified_auth_client.get("/api/v1/auth/user-me", headers=_auth_headers(token))

    assert response.status_code == 401


def test_require_partner_allows_partner_role() -> None:
    partner = User(id=1, email="partner@example.com", role=UserRole.PARTNER.value, is_active=True)

    assert require_partner(partner) is partner


def test_require_partner_rejects_client_role() -> None:
    client = User(id=2, email="client@example.com", role=UserRole.CLIENT.value, is_active=True)

    with pytest.raises(HTTPException) as exc_info:
        require_partner(client)

    assert exc_info.value.status_code == 403


def test_admin_endpoints_do_not_accept_unified_user_token(unified_auth_client: TestClient) -> None:
    token = _user_login(unified_auth_client, "partner@example.com", "PartnerPassword123")

    response = unified_auth_client.get("/api/v1/admin/me", headers=_auth_headers(token))

    assert response.status_code == 401
