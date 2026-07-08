from fastapi.testclient import TestClient

from app.main import app


def test_client_errors_returns_204_for_any_json() -> None:
    response = TestClient(app).post("/api/client-errors", json={"anything": {"nested": True}})
    assert response.status_code == 204
    assert response.content == b""


def test_runtime_config_returns_200_no_store_json() -> None:
    response = TestClient(app).get("/api/runtime-config")
    assert response.status_code == 200
    assert response.headers["cache-control"].startswith("no-store")
    assert response.json()["service"] == "womenclub"
