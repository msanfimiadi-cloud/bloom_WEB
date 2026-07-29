from __future__ import annotations

import math
import re
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import Any

from starlette.requests import Request


@dataclass(frozen=True)
class RateLimitRule:
    requests: int
    window_seconds: int


AUTH_RATE_LIMITS: dict[str, RateLimitRule] = {
    "/api/v1/auth/login": RateLimitRule(10, 300),
    "/api/v1/auth/user-login": RateLimitRule(15, 300),
    "/api/v1/auth/login-code": RateLimitRule(30, 300),
    "/api/v1/auth/browser-token-login": RateLimitRule(30, 300),
    "/api/v1/auth/password-setup/complete": RateLimitRule(10, 300),
    "/api/v1/partner/login": RateLimitRule(10, 300),
    "/api/v1/partner/code-login": RateLimitRule(10, 300),
    "/api/client-errors": RateLimitRule(30, 60),
}

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_SENSITIVE_KEY_PATTERN = re.compile(
    r"(authorization|cookie|credential|password|secret|signature|token|jwt|init[_-]?data|hash)",
    re.IGNORECASE,
)
_INLINE_SECRET_PATTERN = re.compile(
    r"(?i)(authorization|token|secret|password|signature|init[_-]?data)([\s\"':=]+)(?:Bearer\s+)?([^\s,\"'}]+)"
)


class SlidingWindowRateLimiter:
    def __init__(self, *, max_keys: int = 50_000) -> None:
        self._events: dict[str, deque[float]] = {}
        self._lock = Lock()
        self._max_keys = max_keys

    def check(
        self,
        key: str,
        rule: RateLimitRule,
        *,
        now: float | None = None,
    ) -> tuple[bool, int]:
        current = time.monotonic() if now is None else now
        cutoff = current - rule.window_seconds

        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= cutoff:
                events.popleft()

            if len(events) >= rule.requests:
                retry_after = max(1, math.ceil(events[0] + rule.window_seconds - current))
                return False, retry_after

            events.append(current)
            if len(self._events) > self._max_keys:
                self._prune(cutoff)
            return True, 0

    def _prune(self, cutoff: float) -> None:
        stale_keys = [
            key
            for key, events in self._events.items()
            if not events or events[-1] <= cutoff
        ]
        for key in stale_keys:
            self._events.pop(key, None)


def client_ip_for_rate_limit(request: Request) -> str:
    # Production Uvicorn only listens on loopback and Nginx overwrites X-Real-IP.
    forwarded = request.headers.get("x-real-ip", "").strip()
    if forwarded:
        return forwarded[:64]
    if request.client is not None and request.client.host:
        return request.client.host[:64]
    return "unknown"


def normalize_request_id(value: str | None, fallback: str) -> str:
    candidate = (value or "").strip()
    return candidate if _REQUEST_ID_PATTERN.fullmatch(candidate) else fallback


def sanitize_client_error_payload(value: Any, *, depth: int = 0) -> Any:
    if depth >= 4:
        return "[truncated]"
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 30:
                sanitized["_truncated"] = True
                break
            safe_key = str(key)[:80]
            sanitized[safe_key] = (
                "[redacted]"
                if _SENSITIVE_KEY_PATTERN.search(safe_key)
                else sanitize_client_error_payload(item, depth=depth + 1)
            )
        return sanitized
    if isinstance(value, list):
        return [
            sanitize_client_error_payload(item, depth=depth + 1)
            for item in value[:20]
        ]
    if isinstance(value, str):
        redacted = _INLINE_SECRET_PATTERN.sub(r"\1\2[redacted]", value)
        return redacted[:500]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return f"[{type(value).__name__}]"
