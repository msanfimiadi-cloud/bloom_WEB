from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from .client import InternalApiClient, VkApiClient
from .keyboards import REPEAT_CODE_LABEL, login_keyboard
from .settings import VkBotSettings

logger = logging.getLogger(__name__)
LOGIN_MESSAGE = "Добро пожаловать в Bloom Club 🌸\n\nВаш код для входа:\n\n{code}\n\nОткройте приложение и введите этот код."
ERROR_MESSAGE = "Сервис временно недоступен. Попробуйте получить код ещё раз через несколько минут."
SUPPORTED_TEXTS = {"начать", "start", "/start", "получить код", "получить код повторно", REPEAT_CODE_LABEL.lower()}


class VkBotHandler:
    def __init__(self, vk: VkApiClient, internal: InternalApiClient, settings: VkBotSettings) -> None:
        self.vk = vk
        self.internal = internal
        self.settings = settings

    async def handle_update(self, update: dict[str, Any]) -> None:
        if update.get("type") != "message_new":
            return
        message = update.get("object", {}).get("message", {})
        peer_id = message.get("peer_id")
        from_id = message.get("from_id")
        if not peer_id or not from_id or int(from_id) <= 0:
            return
        text = (message.get("text") or "").strip().lower()
        logger.info("message_received", extra={"event": "message_received", "vk_user_id": str(from_id)})
        # Unknown texts intentionally show the same code flow: the bot has only one job.
        if text and text not in SUPPORTED_TEXTS:
            logger.info("unknown_text_as_code_request", extra={"event": "message_received", "vk_user_id": str(from_id)})
        await self.send_code(int(peer_id), str(from_id))

    async def send_code(self, peer_id: int, user_id: str) -> None:
        try:
            profile = await self.vk.get_profile(user_id)
            data = await self.internal.create_login_code(profile)
            code = data["login_code"]
            await self.vk.send_message(peer_id, LOGIN_MESSAGE.format(code=code), login_keyboard(self.settings.browser_app_url))
        except (httpx.HTTPError, KeyError) as exc:
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            logger.warning("backend_error", extra={"event": "backend_error", "vk_user_id": user_id, "status_code": status})
            await self._safe_error(peer_id)

    async def _safe_error(self, peer_id: int) -> None:
        try:
            await self.vk.send_message(peer_id, ERROR_MESSAGE, login_keyboard(self.settings.browser_app_url))
        except Exception as exc:  # noqa: BLE001
            logger.warning("vk_api_error", extra={"event": "vk_api_error", "peer_id": peer_id, "error": type(exc).__name__})


async def backoff_sleep(delay: float) -> float:
    await asyncio.sleep(delay)
    return min(delay * 2, 60.0)
