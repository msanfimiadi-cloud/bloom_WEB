from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .settings import VkBotSettings

logger = logging.getLogger(__name__)
VK_API_URL = "https://api.vk.com/method"


class VkApiError(RuntimeError):
    def __init__(self, method: str, message: str, *, code: int | None = None) -> None:
        super().__init__(f"VK API {method} failed: {message}")
        self.method = method
        self.code = code


@dataclass(frozen=True)
class VkProfile:
    user_id: str
    username: str
    first_name: str | None = None
    last_name: str | None = None


class VkApiClient:
    def __init__(self, settings: VkBotSettings, http: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self.http = http or httpx.AsyncClient(timeout=httpx.Timeout(35.0, connect=10.0))
        self._owns_http = http is None
        self._profile_cache: dict[str, tuple[float, VkProfile]] = {}

    async def close(self) -> None:
        if self._owns_http:
            await self.http.aclose()

    async def api(self, method: str, params: dict[str, Any]) -> Any:
        safe_params = {**params, "access_token": self.settings.vk_bot_token, "v": self.settings.vk_api_version}
        response = await self.http.post(f"{VK_API_URL}/{method}", data=safe_params)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            error = payload["error"]
            raise VkApiError(method, error.get("error_msg", "unknown"), code=error.get("error_code"))
        return payload.get("response")

    async def get_longpoll_server(self) -> dict[str, Any]:
        data = await self.api("groups.getLongPollServer", {"group_id": self.settings.vk_group_id})
        logger.info("longpoll_connected", extra={"event": "longpoll_connected"})
        return {"server": data["server"], "key": data["key"], "ts": data["ts"]}

    async def poll(self, server: dict[str, Any]) -> dict[str, Any]:
        response = await self.http.get(
            server["server"],
            params={
                "act": "a_check",
                "key": server["key"],
                "ts": server["ts"],
                "wait": self.settings.vk_longpoll_wait,
                "mode": self.settings.vk_longpoll_mode,
                "version": self.settings.vk_longpoll_version,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_profile(self, user_id: str) -> VkProfile:
        cached = self._profile_cache.get(user_id)
        now = time.monotonic()
        if cached and cached[0] > now:
            return cached[1]
        data = await self.api("users.get", {"user_ids": user_id, "fields": "screen_name"})
        user = data[0] if data else {}
        first_name = (user.get("first_name") or "").strip() or None
        last_name = (user.get("last_name") or "").strip() or None
        screen_name = (user.get("screen_name") or "").strip() or None
        username = screen_name or " ".join(part for part in (first_name, last_name) if part) or user_id
        profile = VkProfile(user_id=user_id, username=username, first_name=first_name, last_name=last_name)
        self._profile_cache[user_id] = (now + self.settings.profile_cache_ttl_seconds, profile)
        return profile

    async def send_message(self, peer_id: int, message: str, keyboard: str | None = None) -> None:
        params: dict[str, Any] = {"peer_id": peer_id, "message": message, "random_id": random.randint(1, 2_147_483_647)}
        if keyboard:
            params["keyboard"] = keyboard
        await self.api("messages.send", params)
        logger.info("reply_sent", extra={"event": "reply_sent", "peer_id": peer_id})


class InternalApiClient:
    def __init__(self, settings: VkBotSettings, http: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self.http = http or httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0))
        self._owns_http = http is None

    async def close(self) -> None:
        if self._owns_http:
            await self.http.aclose()

    async def create_login_code(self, profile: VkProfile) -> dict[str, Any]:
        payload = {"provider": "vk", "provider_user_id": profile.user_id, "username": profile.username, "first_name": profile.first_name, "last_name": profile.last_name, "source": "vk_bot"}
        logger.info("login_code_requested", extra={"event": "login_code_requested", "vk_user_id": profile.user_id})
        response = await self.http.post(
            f"{self.settings.internal_api_base_url.rstrip('/')}/api/v1/internal/login-code",
            json=payload,
            headers={"Authorization": f"Bearer {self.settings.internal_api_key}"},
        )
        if response.status_code >= 500 or response.status_code == 429:
            await asyncio.sleep(0.5)
            response = await self.http.post(
                f"{self.settings.internal_api_base_url.rstrip('/')}/api/v1/internal/login-code",
                json=payload,
                headers={"Authorization": f"Bearer {self.settings.internal_api_key}"},
            )
        response.raise_for_status()
        return response.json()
