from __future__ import annotations

import os
from dataclasses import dataclass


_ENV = os.getenv("ENV", "test")
_DEFAULT_JWT_SECRET = "change-me-test-jwt-secret" if _ENV.lower() in {"test", "testing"} else ""


@dataclass(frozen=True)
class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Federal Women Club WEB")
    ENV: str = _ENV
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    CONTENT_DATABASE_URL: str = os.getenv("CONTENT_DATABASE_URL", "sqlite+aiosqlite:///./content.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-test-secret")
    SITE_CREDENTIALS_SECRET: str | None = os.getenv("SITE_CREDENTIALS_SECRET")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", _DEFAULT_JWT_SECRET)
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    BOT_API_TOKEN: str = os.getenv("BOT_API_TOKEN", "")
    TELEGRAM_ADMIN_API_TOKEN: str = os.getenv("TELEGRAM_ADMIN_API_TOKEN", "")
    BOT_SERVICE_TOKEN: str = os.getenv("BOT_SERVICE_TOKEN", "change-me-test-token")
    BROWSER_LOGIN_TOKEN_TTL_SECONDS: int = int(os.getenv("BROWSER_LOGIN_TOKEN_TTL_SECONDS", "900"))
    BROWSER_APP_PUBLIC_URL: str = os.getenv("BROWSER_APP_PUBLIC_URL", "https://app.bloomclub.ru")
    VK_APP_ID: str = os.getenv("VK_APP_ID", "")
    VK_APP_SECRET: str = os.getenv("VK_APP_SECRET", "")
    VK_BOT_TOKEN: str = os.getenv("VK_BOT_TOKEN", "")
    VK_BOT_GROUP_ID: str = os.getenv("VK_BOT_GROUP_ID", "")
    VK_BOT_CONFIRMATION_CODE: str = os.getenv("VK_BOT_CONFIRMATION_CODE", "")
    VK_BOT_SECRET: str = os.getenv("VK_BOT_SECRET", "")
    VK_SERVICE_TOKEN: str = os.getenv("VK_SERVICE_TOKEN", "")
    VK_MINIAPP_AUTH_MAX_AGE_SECONDS: int = int(os.getenv("VK_MINIAPP_AUTH_MAX_AGE_SECONDS", "86400"))
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_MINIAPP_AUTH_MAX_AGE_SECONDS: int = int(os.getenv("TELEGRAM_MINIAPP_AUTH_MAX_AGE_SECONDS", "86400"))
    LEAD_HASH_SALT: str = os.getenv("LEAD_HASH_SALT", "change-me-test-salt")
    BACKEND_CORS_ORIGINS: str = os.getenv(
        "BACKEND_CORS_ORIGINS",
        "https://bloomclub.ru,https://www.bloomclub.ru,https://m.vk.ru,https://m.vk.com,https://vk.com,https://vk.ru,https://kosmos327-fed-women-club-mini-app-3f15.twc1.net,http://localhost:5173,http://127.0.0.1:5173",
    )
    WEB_PUBLIC_URL: str = os.getenv("WEB_PUBLIC_URL", "https://women-club.example")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    PUBLIC_UPLOADS_PATH: str = os.getenv("PUBLIC_UPLOADS_PATH", "/uploads")
    WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED: bool = os.getenv("WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED", "true").lower() in {"1", "true", "yes", "on"}

    @property
    def backend_cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def visitor_cookie_secure(self) -> bool:
        return self.ENV.lower() in {"production", "prod", "staging"}

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() in {"production", "prod"}


settings = Settings()
