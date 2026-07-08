from fastapi.testclient import TestClient

from app.main import BROWSER_BUILD_ID_PATH, app


def test_runtime_config_build_id_matches_browser_mobile_hash(tmp_path, monkeypatch) -> None:
    build_file = tmp_path / "build-id.txt"
    build_file.write_text("4d1b56d91bd8\n", encoding="utf-8")
    monkeypatch.setattr("app.main.BROWSER_BUILD_ID_PATH", build_file)

    response = TestClient(app).get("/api/runtime-config?clientBuildId=4d1b56d91bd8")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "0.1.0"
    assert payload["buildId"] == "4d1b56d91bd8"
    assert payload["clientBuildId"] == "4d1b56d91bd8"


def test_runtime_config_missing_build_id_mirrors_client_to_avoid_false_mismatch(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("app.main.BROWSER_BUILD_ID_PATH", tmp_path / "missing-build-id.txt")

    payload = TestClient(app).get("/api/runtime-config?clientBuildId=clienthash123").json()

    assert payload["version"] == "0.1.0"
    assert payload["buildId"] == "clienthash123"
