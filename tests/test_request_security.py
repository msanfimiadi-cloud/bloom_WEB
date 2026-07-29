from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.request_security import (
    RateLimitRule,
    SlidingWindowRateLimiter,
    normalize_request_id,
    sanitize_client_error_payload,
)


def test_sliding_window_rate_limiter_blocks_and_recovers() -> None:
    limiter = SlidingWindowRateLimiter()
    rule = RateLimitRule(requests=2, window_seconds=10)

    assert limiter.check("client:/login", rule, now=100) == (True, 0)
    assert limiter.check("client:/login", rule, now=101) == (True, 0)
    assert limiter.check("client:/login", rule, now=102) == (False, 8)
    assert limiter.check("client:/login", rule, now=111) == (True, 0)


def test_client_error_payload_redacts_secrets_and_limits_shape() -> None:
    sanitized = sanitize_client_error_payload(
        {
            "message": "Authorization: Bearer top-secret-value",
            "access_token": "top-secret-value",
            "nested": {"password": "password-value"},
            "items": list(range(30)),
        }
    )

    assert "top-secret-value" not in repr(sanitized)
    assert "password-value" not in repr(sanitized)
    assert sanitized["access_token"] == "[redacted]"
    assert sanitized["nested"]["password"] == "[redacted]"
    assert len(sanitized["items"]) == 20


def test_request_id_rejects_log_injection() -> None:
    assert normalize_request_id("safe-id_123", "fallback") == "safe-id_123"
    assert normalize_request_id("bad\ninjected", "fallback") == "fallback"
    assert normalize_request_id("x" * 129, "fallback") == "fallback"


def _production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "ENV": "production",
        "JWT_SECRET_KEY": "j" * 48,
        "SECRET_KEY": "s" * 48,
        "BOT_SERVICE_TOKEN": "b" * 48,
        "JWT_ALGORITHM": "HS256",
        "BACKEND_CORS_ORIGINS": "https://bloomclub.ru,https://app.bloomclub.ru",
        "TRUSTED_HOSTS": "bloomclub.ru,app.bloomclub.ru",
    }
    values.update(overrides)
    return Settings(**values)


def test_production_security_configuration_accepts_strong_values() -> None:
    _production_settings().validate_security()


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("JWT_SECRET_KEY", "short"),
        ("SECRET_KEY", "change-me-in-production"),
        ("BOT_SERVICE_TOKEN", ""),
        ("JWT_ALGORITHM", "none"),
        ("BACKEND_CORS_ORIGINS", "http://localhost:5173"),
        ("TRUSTED_HOSTS", ""),
    ),
)
def test_production_security_configuration_rejects_unsafe_values(
    field: str,
    value: str,
) -> None:
    with pytest.raises(RuntimeError):
        _production_settings(**{field: value}).validate_security()
