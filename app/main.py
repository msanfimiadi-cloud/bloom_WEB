from __future__ import annotations

import logging
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError, SQLAlchemyError, TimeoutError as SQLAlchemyTimeoutError

from app.api.v1.endpoints.auth import router as root_auth_router, telegram_miniapp_login, vk_miniapp_login
from app.api.v1.endpoints.content import router as content_router
from app.api.v1.endpoints.public import router as public_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import SessionLocal


logger = logging.getLogger("app.request")
vk_logger = logging.getLogger("app.auth_cors")
db_logger = logging.getLogger("app.database")

VK_MINIAPP_AUTH_LOG_PATHS = {"/api/v1/auth/vk-miniapp-login", "/auth/vk-miniapp-login"}
SERVICE_NAME = "womenclub"
APP_VERSION = "0.1.0"


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins_list,
    allow_origin_regex=r"https://([a-z0-9-]+\.)*(vk\.ru|vk\.com|bloomclub\.ru)$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)

upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount(settings.PUBLIC_UPLOADS_PATH, StaticFiles(directory=upload_dir), name="uploads")

vk_mini_app_dir = Path("app/static/vk-mini-app")


def _vk_mini_app_path(relative_path: str) -> Path:
    candidate = (vk_mini_app_dir / relative_path).resolve()
    base = vk_mini_app_dir.resolve()
    if base not in candidate.parents and candidate != base:
        raise HTTPException(status_code=404, detail="Not found")
    return candidate


def _vk_mini_app_index() -> FileResponse:
    index_path = vk_mini_app_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(
            status_code=503,
            detail="VK Mini App build is not deployed. Place build files into app/static/vk-mini-app/",
        )
    return FileResponse(index_path)


def _health_payload() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME, "version": APP_VERSION}


def _database_health_payload() -> dict[str, str]:
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return {"status": "ok", "service": SERVICE_NAME, "database": "ok"}


@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    db_logger.exception("database operational error path=%s request_id=%s", request.url.path, request_id)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database temporarily unavailable", "request_id": request_id},
    )


@app.exception_handler(SQLAlchemyTimeoutError)
async def sqlalchemy_timeout_handler(request: Request, exc: SQLAlchemyTimeoutError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    db_logger.exception("database pool timeout path=%s request_id=%s", request.url.path, request_id)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database temporarily unavailable", "request_id": request_id},
    )


@app.exception_handler(DBAPIError)
async def dbapi_error_handler(request: Request, exc: DBAPIError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    db_logger.exception("database error path=%s request_id=%s", request.url.path, request_id)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error", "request_id": request_id},
    )


@app.get("/vk-mini-app/")
async def vk_mini_app_entrypoint() -> FileResponse:
    return _vk_mini_app_index()


@app.get("/vk-mini-app/{full_path:path}")
async def vk_mini_app_static(full_path: str) -> FileResponse:
    if not full_path:
        return _vk_mini_app_index()

    file_path = _vk_mini_app_path(full_path)
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)

    return _vk_mini_app_index()


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return _health_payload()


@app.get("/api/v1/health", tags=["health"])
async def api_health_check() -> dict[str, str]:
    return _health_payload()


@app.get("/health/db", tags=["health"], response_model=None)
async def database_health_check():
    try:
        return _database_health_payload()
    except SQLAlchemyError:
        db_logger.exception("database health check failed")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "service": SERVICE_NAME, "database": "unavailable"},
        )


app.include_router(public_router)
app.include_router(content_router)
app.include_router(api_router)
app.include_router(root_auth_router)

# Keep auth contract routes visible to route-introspection tests and legacy clients.
app.add_api_route("/api/v1/auth/vk-miniapp-login", vk_miniapp_login, methods=["POST"], response_model=None, include_in_schema=False)
app.add_api_route("/auth/vk-miniapp-login", vk_miniapp_login, methods=["POST"], response_model=None, include_in_schema=False)
app.add_api_route("/api/v1/auth/telegram-miniapp-login", telegram_miniapp_login, methods=["POST"], response_model=None, include_in_schema=False)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    started_at = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "request method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            request_id,
        )
        if "response" in locals():
            response.headers["X-Request-ID"] = request_id


@app.middleware("http")
async def log_vk_miniapp_auth_cors_debug(request: Request, call_next):
    path = request.url.path
    if path not in VK_MINIAPP_AUTH_LOG_PATHS:
        return await call_next(request)

    method = request.method
    origin = request.headers.get("origin", "")
    acr_method = request.headers.get("access-control-request-method", "")
    acr_headers = request.headers.get("access-control-request-headers", "")
    user_agent = request.headers.get("user-agent", "")[:120]

    response = await call_next(request)
    vk_logger.info(
        "vk-miniapp-login method=%s path=%s origin=%s acr_method=%s acr_headers=%s status=%s ua=%s",
        method,
        path,
        origin,
        acr_method,
        acr_headers,
        response.status_code,
        user_agent,
    )
    return response
