from __future__ import annotations

import base64
import hmac
from datetime import datetime, timezone
from hashlib import sha256
from urllib.parse import parse_qsl, urlencode

from fastapi import HTTPException, status

from app.core.config import settings


def parse_launch_params(launch_params: str) -> dict[str, str]:
    raw = launch_params.strip()
    if raw.startswith("?"):
        raw = raw[1:]
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="launch_params must not be empty")
    return dict(parse_qsl(raw, keep_blank_values=True))


def verify_vk_miniapp_signature(params: dict[str, str]) -> None:
    sign = params.get("sign")
    if not sign:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid VK Mini App signature")

    app_secret = settings.VK_APP_SECRET.strip()
    if not app_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="VK_APP_SECRET is not configured",
        )

    app_id = params.get("vk_app_id")
    if not app_id or app_id != settings.VK_APP_ID.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid VK Mini App signature")

    data = {key: value for key, value in params.items() if key.startswith("vk_")}
    canonical = urlencode(sorted(data.items()), doseq=False)
    digest = hmac.new(app_secret.encode("utf-8"), canonical.encode("utf-8"), sha256).digest()
    expected_sign = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    if not hmac.compare_digest(expected_sign, sign):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid VK Mini App signature")


def extract_vk_user_id(params: dict[str, str]) -> str:
    vk_user_id = (params.get("vk_user_id") or "").strip()
    if not vk_user_id or not vk_user_id.isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid VK Mini App signature")
    return vk_user_id


def validate_vk_ts_freshness(params: dict[str, str]) -> None:
    vk_ts = (params.get("vk_ts") or "").strip()
    if not vk_ts.isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid VK Mini App signature")
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if now_ts - int(vk_ts) > settings.VK_MINIAPP_AUTH_MAX_AGE_SECONDS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="VK Mini App launch params expired")
