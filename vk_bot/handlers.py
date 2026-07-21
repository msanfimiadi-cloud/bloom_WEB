from __future__ import annotations

import asyncio
import json
import re
import logging
from typing import Any

import httpx

from .client import InternalApiClient, VkApiClient
from .keyboards import NEW_CODE_LABEL, REPEAT_CODE_LABEL, login_keyboard, partner_confirmation_keyboard
from .settings import VkBotSettings

logger = logging.getLogger(__name__)
LOGIN_INTRO_MESSAGE = "🌸 Добро пожаловать в Bloom Club!\n\nВаш код для входа:"
LOGIN_INSTRUCTION_MESSAGE = "Откройте приложение Bloom Club и введите этот код."
LINK_INTRO_MESSAGE = "🔗 Код для привязки аккаунта"
LINK_INSTRUCTION_MESSAGE = "Введите этот код в разделе\n\nПрофиль → Связанные аккаунты"
LOGIN_MESSAGE = f"{LOGIN_INTRO_MESSAGE}\n\n{{code}}\n\n{LOGIN_INSTRUCTION_MESSAGE}"
ERROR_MESSAGE = "Сервис временно недоступен. Попробуйте получить код ещё раз через несколько минут."
SUPPORTED_TEXTS = {"начать", "start", "/start", "получить код", "получить код повторно", REPEAT_CODE_LABEL.lower(), NEW_CODE_LABEL.lower()}
PARTNER_COMMANDS = {"/partner", "partner", "партнёр", "партнер"}
PARTNER_CODE_PATTERN = re.compile(r"^[A-Za-z0-9-]{4,16}$")


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
        raw_text = (message.get("text") or "").strip()
        text = raw_text.lower()
        payload = self._parse_payload(message.get("payload"))
        logger.info("message_received", extra={"event": "message_received", "vk_user_id": str(from_id)})
        if payload.get("command") == "confirm_partner_code":
            await self.confirm_partner_code(int(peer_id), str(from_id), payload.get("session_id"))
            return
        if payload.get("command") == "cancel_partner_code":
            await self.vk.send_message(int(peer_id), "Активация отменена. Код не использован.")
            return
        if text in PARTNER_COMMANDS:
            await self.open_partner_mode(int(peer_id), str(from_id))
            return
        if raw_text and PARTNER_CODE_PATTERN.fullmatch(raw_text):
            status_data = await self._partner_status(str(from_id))
            if status_data.get("is_partner"):
                await self.check_partner_code(int(peer_id), str(from_id), raw_text)
                return
        await self.send_code(int(peer_id), str(from_id))

    @staticmethod
    def _parse_payload(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if not value:
            return {}
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, ValueError):
            return {}

    async def _partner_status(self, user_id: str) -> dict[str, Any]:
        try:
            return await self.internal.partner_status(user_id)
        except httpx.HTTPError:
            return {"is_partner": False}

    async def open_partner_mode(self, peer_id: int, user_id: str) -> None:
        try:
            data = await self.internal.partner_status(user_id)
            if not data.get("is_partner"):
                await self.vk.send_message(peer_id, f"Партнёрский доступ не найден.\n\nВаш VK ID: {user_id}\n\nПередайте этот ID администратору Bloom Club.")
                return
            await self.vk.send_message(peer_id, f"Партнёрский режим активирован\n\nПартнёр: {data.get('partner_name')}\nСотрудник: {data.get('employee_name')}\n\nОтправьте код, который показала клиентка.")
        except httpx.HTTPError:
            await self._safe_error(peer_id)

    async def check_partner_code(self, peer_id: int, user_id: str, code: str) -> None:
        try:
            data = await self.internal.check_partner_code(user_id, code)
            title = data.get("privilege_title") or "Привилегия Bloom Club"
            saving = data.get("saving_amount") or 0
            message = f"✅ Код актуален\n\nПартнёр: {data.get('partner_name')}\nПривилегия: {title}\nЭкономия: {saving} ₽\n\nАктивировать код?"
            await self.vk.send_message(peer_id, message, partner_confirmation_keyboard(int(data["session_id"])))
        except httpx.HTTPStatusError as exc:
            details = self._backend_detail(exc)
            messages = {
                "code_not_found": "Код не найден. Проверьте цифры и попробуйте ещё раз.",
                "code_for_another_partner": "Этот код выдан для другого партнёра.",
                "code_already_activated": "Этот код уже был активирован.",
                "code_expired": "Срок действия кода истёк. Попросите клиентку получить новый код.",
                "too_many_code_attempts": "Слишком много попыток. Подождите несколько минут и попробуйте снова.",
                "client_inactive": "Аккаунт клиентки неактивен. Код нельзя использовать.",
                "subscription_inactive": "Подписка клиентки уже неактивна. Попросите её обновить доступ.",
            }
            await self.vk.send_message(peer_id, messages.get(details, ERROR_MESSAGE))
        except (httpx.HTTPError, KeyError, ValueError):
            await self._safe_error(peer_id)

    async def confirm_partner_code(self, peer_id: int, user_id: str, session_id: Any) -> None:
        try:
            data = await self.internal.confirm_partner_code(user_id, int(session_id))
            number_text = " Клиентке начислен 1 номерок текущего розыгрыша." if data.get("giveaway_number_awarded") else " Активного розыгрыша сейчас нет, поэтому номерок не начислялся."
            await self.vk.send_message(peer_id, f"✅ Код активирован\n\nЭкономия {data.get('saving_amount') or 0} ₽ учтена.{number_text}")
        except httpx.HTTPStatusError as exc:
            detail = self._backend_detail(exc)
            message = "Этот код уже был активирован." if detail == "code_already_activated" else ERROR_MESSAGE
            await self.vk.send_message(peer_id, message)
        except (httpx.HTTPError, TypeError, ValueError):
            await self._safe_error(peer_id)

    @staticmethod
    def _backend_detail(exc: httpx.HTTPStatusError) -> str:
        try:
            return str(exc.response.json().get("detail") or "")
        except (TypeError, ValueError):
            return ""

    async def send_code(self, peer_id: int, user_id: str) -> None:
        try:
            profile = await self.vk.get_profile(user_id)
            data = await self.internal.create_login_code(profile)
            code = data["login_code"]
            await self.send_login_code_messages(peer_id, code)
        except (httpx.HTTPError, KeyError) as exc:
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            logger.warning("backend_error", extra={"event": "backend_error", "vk_user_id": user_id, "status_code": status})
            await self._safe_error(peer_id)

    async def send_login_code_messages(self, peer_id: int, code: str) -> None:
        await self.vk.send_message(peer_id, LOGIN_INTRO_MESSAGE)
        await self.vk.send_message(peer_id, code)
        await self.vk.send_message(peer_id, LOGIN_INSTRUCTION_MESSAGE, login_keyboard(self.settings.browser_app_url))

    async def send_link_code_messages(self, peer_id: int, code: str) -> None:
        await self.vk.send_message(peer_id, LINK_INTRO_MESSAGE)
        await self.vk.send_message(peer_id, code)
        await self.vk.send_message(peer_id, LINK_INSTRUCTION_MESSAGE, login_keyboard(self.settings.browser_app_url, repeat_label=NEW_CODE_LABEL))

    async def _safe_error(self, peer_id: int) -> None:
        try:
            await self.vk.send_message(peer_id, ERROR_MESSAGE, login_keyboard(self.settings.browser_app_url))
        except Exception as exc:  # noqa: BLE001
            logger.warning("vk_api_error", extra={"event": "vk_api_error", "peer_id": peer_id, "error": type(exc).__name__})


async def backoff_sleep(delay: float) -> float:
    await asyncio.sleep(delay)
    return min(delay * 2, 60.0)
