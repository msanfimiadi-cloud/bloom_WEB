from __future__ import annotations

from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.main import app


def test_uploads_static_files_are_mounted() -> None:
    route = next((route for route in app.routes if getattr(route, "path", None) == settings.PUBLIC_UPLOADS_PATH), None)

    assert route is not None
    assert isinstance(getattr(route, "app", None), StaticFiles)
