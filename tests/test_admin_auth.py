from __future__ import annotations

from collections.abc import Generator
from datetime import timedelta
from time import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import AdminUser, UserRole


@pytest.fixture()
def client_with_admin_db() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    Base.metadata.create_all(bind=engine)
    with session_factory() as session:
        session.add_all(
            [
                AdminUser(
                    email="admin@example.com",
                    password_hash=hash_password("StrongPassword123"),
                    role=UserRole.ADMIN.value,
                    is_active=True,
                ),
                AdminUser(
                    email="inactive@example.com",
                    password_hash=hash_password("StrongPassword123"),
                    role=UserRole.ADMIN.value,
                    is_active=False,
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


def test_password_hash_verify_works() -> None:
    password_hash = hash_password("StrongPassword123")

    assert password_hash != "StrongPassword123"
    assert verify_password("StrongPassword123", password_hash) is True
    assert verify_password("WrongPassword", password_hash) is False


def test_user_role_admin_serializes_to_string_value() -> None:
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.ADMIN == "admin"


def test_access_token_round_trip_uses_python310_compatible_timezone() -> None:
    token = create_access_token("admin@example.com", expires_delta=timedelta(minutes=5))

    assert isinstance(token, str)
    payload = decode_access_token(token)

    assert payload["sub"] == "admin@example.com"
    assert isinstance(payload["exp"], int)
    assert payload["exp"] > int(time())


def test_admin_login_succeeds_with_correct_password(client_with_admin_db: TestClient) -> None:
    response = client_with_admin_db.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "StrongPassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"] == {"id": 1, "email": "admin@example.com", "role": "admin"}


def test_admin_login_returns_401_with_wrong_password(client_with_admin_db: TestClient) -> None:
    response = client_with_admin_db.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "WrongPassword"},
    )

    assert response.status_code == 401


def test_admin_me_works_with_valid_bearer_token(client_with_admin_db: TestClient) -> None:
    login_response = client_with_admin_db.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "StrongPassword123"},
    )
    token = login_response.json()["access_token"]

    response = client_with_admin_db.get(
        "/api/v1/admin/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"id": 1, "email": "admin@example.com", "role": "admin"}


def test_admin_me_returns_401_without_token(client_with_admin_db: TestClient) -> None:
    response = client_with_admin_db.get("/api/v1/admin/me")

    assert response.status_code == 401


def test_inactive_admin_cannot_login(client_with_admin_db: TestClient) -> None:
    response = client_with_admin_db.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "StrongPassword123"},
    )

    assert response.status_code == 403
