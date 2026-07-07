from app.core.config import Settings


def test_cors_origins_are_split() -> None:
    settings = Settings(BACKEND_CORS_ORIGINS="http://localhost:5173, https://bloomclub.ru")

    origins = settings.backend_cors_origins_list

    assert "http://localhost:5173" in origins
    assert "https://bloomclub.ru" in origins
    assert origins == ["http://localhost:5173", "https://bloomclub.ru"]
