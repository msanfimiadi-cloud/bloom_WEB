from __future__ import annotations

import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from urllib.parse import parse_qsl

from fastapi import HTTPException, status

from app.core.config import settings


@dataclass(frozen=True)
class TelegramMiniAppUser:
    telegram_user_id: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    photo_url: str | None = None


def _auth_error(detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED) -> HTTPException:
    return HTTPException(status_code=status_code, detail=detail)


def parse_telegram_init_data(init_data: str) -> dict[str, str]:
    raw = init_data.strip()
    if not raw:
        raise _auth_error("missing_init_data", status.HTTP_400_BAD_REQUEST)
    return dict(parse_qsl(raw, keep_blank_values=True, strict_parsing=False))


def verify_telegram_init_data(init_data: str) -> dict[str, str]:
    params = parse_telegram_init_data(init_data)
    actual_hash = (params.get("hash") or "").strip()
    if not actual_hash:
        raise _auth_error("invalid_hash")

    bot_token = settings.TELEGRAM_BOT_TOKEN.strip()
    if not bot_token:
        raise _auth_error("missing_telegram_bot_token", status.HTTP_500_INTERNAL_SERVER_ERROR)

    signed_pairs = [(key, value) for key, value in params.items() if key != "hash"]
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(signed_pairs))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, actual_hash):
        raise _auth_error("invalid_hash")

    validate_telegram_auth_date(params)
    return params


def validate_telegram_auth_date(params: dict[str, str]) -> None:
    auth_date = (params.get("auth_date") or "").strip()
    if not auth_date.isdigit():
        raise _auth_error("expired_auth_date")
    now_ts = int(datetime.now(timezone.utc).timestamp())
    auth_ts = int(auth_date)
    if auth_ts > now_ts + 60 or now_ts - auth_ts > settings.TELEGRAM_MINIAPP_AUTH_MAX_AGE_SECONDS:
        raise _auth_error("expired_auth_date")


def extract_telegram_user(params: dict[str, str]) -> TelegramMiniAppUser:
    raw_user = params.get("user")
    if not raw_user:
        raise _auth_error("invalid_user_payload", status.HTTP_400_BAD_REQUEST)
    try:
        user_payload: Any = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise _auth_error("invalid_user_payload", status.HTTP_400_BAD_REQUEST) from exc
    if not isinstance(user_payload, dict):
        raise _auth_error("invalid_user_payload", status.HTTP_400_BAD_REQUEST)

    telegram_user_id = str(user_payload.get("id") or "").strip()
    if not telegram_user_id or not telegram_user_id.isdigit():
        raise _auth_error("invalid_user_payload", status.HTTP_400_BAD_REQUEST)

    return TelegramMiniAppUser(
        telegram_user_id=telegram_user_id,
        username=_optional_str(user_payload.get("username")),
        first_name=_optional_str(user_payload.get("first_name")),
        last_name=_optional_str(user_payload.get("last_name")),
        photo_url=_optional_str(user_payload.get("photo_url")),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
