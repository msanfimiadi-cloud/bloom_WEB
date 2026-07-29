from __future__ import annotations

import os
from dataclasses import dataclass

from pydantic import SecretStr


_ENV = os.getenv("ENV", "test")
_DEFAULT_JWT_SECRET = "change-me-test-jwt-secret" if _ENV.lower() in {"test", "testing"} else ""
_IS_PRODUCTION_ENV = _ENV.lower() in {"production", "prod"}
_DEFAULT_TRUSTED_HOSTS = (
    "bloomclub.ru,www.bloomclub.ru,app.bloomclub.ru"
    if _IS_PRODUCTION_ENV
    else "bloomclub.ru,www.bloomclub.ru,app.bloomclub.ru,localhost,127.0.0.1,testserver"
)
_DEFAULT_CORS_ORIGINS = (
    "https://bloomclub.ru,https://www.bloomclub.ru,https://app.bloomclub.ru,"
    "https://m.vk.ru,https://m.vk.com,https://vk.com,https://vk.ru,"
    "https://kosmos327-fed-women-club-mini-app-3f15.twc1.net"
    if _IS_PRODUCTION_ENV
    else
    "https://bloomclub.ru,https://www.bloomclub.ru,https://app.bloomclub.ru,"
    "https://m.vk.ru,https://m.vk.com,https://vk.com,https://vk.ru,"
    "https://kosmos327-fed-women-club-mini-app-3f15.twc1.net,"
    "http://localhost:5173,http://127.0.0.1:5173"
)


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
    ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    PARTNER_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("PARTNER_ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    AUTH_RATE_LIMIT_ENABLED: bool = os.getenv(
        "AUTH_RATE_LIMIT_ENABLED",
        "true" if _ENV.lower() in {"production", "prod"} else "false",
    ).lower() in {"1", "true", "yes", "on"}
    TRUSTED_HOSTS: str = os.getenv(
        "TRUSTED_HOSTS",
        _DEFAULT_TRUSTED_HOSTS,
    )
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
        _DEFAULT_CORS_ORIGINS,
    )
    WEB_PUBLIC_URL: str = os.getenv("WEB_PUBLIC_URL", "https://women-club.example")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    PUBLIC_UPLOADS_PATH: str = os.getenv("PUBLIC_UPLOADS_PATH", "/uploads")
    WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED: bool = os.getenv("WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    TOCHKA_PAYMENTS_ENABLED: bool = os.getenv("TOCHKA_PAYMENTS_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    TOCHKA_API_BASE_URL: str = os.getenv("TOCHKA_API_BASE_URL", "https://enter.tochka.com/uapi")
    TOCHKA_JWT_TOKEN: SecretStr = SecretStr(os.getenv("TOCHKA_JWT_TOKEN", ""))
    TOCHKA_CLIENT_ID: str = os.getenv("TOCHKA_CLIENT_ID", "")
    TOCHKA_CUSTOMER_CODE: str = os.getenv("TOCHKA_CUSTOMER_CODE", "")
    TOCHKA_MERCHANT_ID: str = os.getenv("TOCHKA_MERCHANT_ID", "")
    TOCHKA_TERMINAL_ID: str = os.getenv("TOCHKA_TERMINAL_ID", "")
    TOCHKA_PAYMENT_MODES: str = os.getenv("TOCHKA_PAYMENT_MODES", "sbp,card")
    TOCHKA_PAYMENT_LINK_TTL_MINUTES: int = int(os.getenv("TOCHKA_PAYMENT_LINK_TTL_MINUTES", "60"))
    TOCHKA_WEBHOOK_PUBLIC_KEY: SecretStr = SecretStr(os.getenv("TOCHKA_WEBHOOK_PUBLIC_KEY", ""))
    TOCHKA_WEBHOOK_URL: str = os.getenv("TOCHKA_WEBHOOK_URL", "https://bloomclub.ru/api/v1/payments/tochka/webhook")
    TOCHKA_SUCCESS_REDIRECT_URL: str = os.getenv("TOCHKA_SUCCESS_REDIRECT_URL", "https://app.bloomclub.ru/payment/success")
    TOCHKA_FAIL_REDIRECT_URL: str = os.getenv("TOCHKA_FAIL_REDIRECT_URL", "https://app.bloomclub.ru/payment/fail")
    TOCHKA_REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("TOCHKA_REQUEST_TIMEOUT_SECONDS", "15"))
    TOCHKA_RECONCILIATION_ENABLED: bool = os.getenv("TOCHKA_RECONCILIATION_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    TOCHKA_RECONCILIATION_INTERVAL_MINUTES: int = int(os.getenv("TOCHKA_RECONCILIATION_INTERVAL_MINUTES", "5"))
    TOCHKA_TAX_SYSTEM_CODE: str = os.getenv("TOCHKA_TAX_SYSTEM_CODE", "")
    TOCHKA_VAT_TYPE: str = os.getenv("TOCHKA_VAT_TYPE", "none")
    TOCHKA_PAYMENT_METHOD: str = os.getenv("TOCHKA_PAYMENT_METHOD", "full_payment")
    TOCHKA_PAYMENT_OBJECT: str = os.getenv("TOCHKA_PAYMENT_OBJECT", "service")

    @property
    def backend_cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def trusted_hosts_list(self) -> list[str]:
        return [host.strip() for host in self.TRUSTED_HOSTS.split(",") if host.strip()]

    @property
    def visitor_cookie_secure(self) -> bool:
        return self.ENV.lower() in {"production", "prod", "staging"}

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() in {"production", "prod"}

    @property
    def tochka_payment_modes_list(self) -> list[str]:
        return [mode.strip().lower() for mode in self.TOCHKA_PAYMENT_MODES.split(",") if mode.strip()]

    @property
    def tochka_configured(self) -> bool:
        required = (
            self.TOCHKA_JWT_TOKEN.get_secret_value(),
            self.TOCHKA_CUSTOMER_CODE,
            self.TOCHKA_MERCHANT_ID,
            self.TOCHKA_SUCCESS_REDIRECT_URL,
            self.TOCHKA_FAIL_REDIRECT_URL,
            self.TOCHKA_WEBHOOK_PUBLIC_KEY.get_secret_value(),
        )
        return all(value.strip() for value in required)

    def validate_tochka(self) -> None:
        if self.TOCHKA_PAYMENTS_ENABLED and not self.tochka_configured:
            raise RuntimeError("Tochka payments are enabled but required backend settings are missing")


    def validate_security(self) -> None:
        if not self.is_production:
            return

        required_secrets = {
            "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
            "SECRET_KEY": self.SECRET_KEY,
            "BOT_SERVICE_TOKEN": self.BOT_SERVICE_TOKEN,
        }
        for name, value in required_secrets.items():
            normalized = value.strip()
            if len(normalized) < 32 or normalized.lower().startswith("change-me"):
                raise RuntimeError(f"{name} must be a unique production secret of at least 32 characters")

        if self.JWT_ALGORITHM != "HS256":
            raise RuntimeError("JWT_ALGORITHM must be HS256")

        if not self.trusted_hosts_list:
            raise RuntimeError("TRUSTED_HOSTS must contain at least one production host")

        for origin in self.backend_cors_origins_list:
            if origin == "*" or origin.startswith("http://"):
                raise RuntimeError("Production CORS origins must be explicit HTTPS origins")


settings = Settings()
settings.validate_security()
settings.validate_tochka()
