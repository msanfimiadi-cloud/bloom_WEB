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


def _example_openapi_path(path: str) -> str:
    return path.replace("{giveaway_id}", "1").replace("{partner_id}", "1").replace("{client_id}", "1").replace("{city_id}", "1").replace("{category_id}", "1").replace("{offer_id}", "1").replace("{verification_id}", "1")


def test_cors_preflight_all_openapi_methods_are_allowed() -> None:
    schema = client.get("/openapi.json").json()
    checked_methods: set[str] = set()

    for raw_path, operations in schema["paths"].items():
        path = _example_openapi_path(raw_path)
        for method in operations:
            method_upper = method.upper()
            if method_upper in {"HEAD", "OPTIONS", "TRACE"}:
                continue

            checked_methods.add(method_upper)
            response = client.options(
                path,
                headers={
                    "Origin": "https://bloomclub.ru",
                    "Access-Control-Request-Method": method_upper,
                    "Access-Control-Request-Headers": "Authorization, Content-Type, Accept, X-Request-ID",
                },
            )
            assert response.status_code in {200, 204}, f"{method_upper} {raw_path} failed CORS preflight"
            assert method_upper in response.headers.get("access-control-allow-methods", "")

    assert "PUT" in checked_methods
