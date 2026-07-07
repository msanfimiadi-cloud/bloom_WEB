from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

import app.main as main
from app.main import app


client = TestClient(app)


def test_app_is_fastapi_asgi_application() -> None:
    assert isinstance(app, FastAPI)
    assert callable(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "womenclub"


def test_api_health_check() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "womenclub"


def test_health_checks_do_not_require_auth() -> None:
    for path in ("/health", "/api/v1/health", "/health/db"):
        response = client.get(path)

        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_database_health_check() -> None:
    response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "womenclub", "database": "ok"}


def test_database_health_check_failure_is_controlled(monkeypatch) -> None:
    class BrokenSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, statement):
            raise OperationalError("SELECT 1", {}, Exception("db unavailable"))

    class BrokenSessionLocal:
        def __call__(self):
            return BrokenSession()

    monkeypatch.setattr(main, "SessionLocal", BrokenSessionLocal())

    response = client.get("/health/db")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "service": "womenclub", "database": "unavailable"}
