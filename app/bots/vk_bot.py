from __future__ import annotations

import argparse
import logging
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.schemas.browser_auth import BrowserLoginCodeCreateResponse
from app.services.browser_login_codes import BrowserLoginCodeService

logger = logging.getLogger(__name__)

VK_API_URL = "https://api.vk.com/method"
VK_API_VERSION = "5.199"
USER_ERROR_TEXT = "Не удалось создать код входа. Попробуйте позже."
LINK_TEXT = "Код для привязки аккаунта к Bloom Club:\n\n{code}\n\nВведите его в разделе “Профиль → Связанные аккаунты”."
OPEN_TEXT = "Ваш код входа:\n\n{code}\n\nКод действует 5 минут.\n\nОткрыть приложение:\nhttps://app.bloomclub.ru"
OPEN_BUTTON_TEXT = "Открыть приложение"


@dataclass(frozen=True)
class VkUserIdentity:
    vk_user_id: str
    display_name: str | None = None
    username: str | None = None
    photo_url: str | None = None


class VkBotError(RuntimeError):
    """Expected VK bot runtime error safe to show in logs without secrets."""


class VkBotService:
    """VK Long Poll bot that sends temporary Bloom Club browser login codes."""

    def __init__(
        self,
        *,
        token: str | None = None,
        group_id: str | None = None,
        session_factory=SessionLocal,
        api_url: str = VK_API_URL,
        client: httpx.Client | None = None,
        poll_wait_seconds: int = 25,
    ) -> None:
        self.token = (token if token is not None else settings.VK_BOT_TOKEN).strip()
        self.group_id = (group_id if group_id is not None else settings.VK_BOT_GROUP_ID).strip()
        self.session_factory = session_factory
        self.api_url = api_url.rstrip("/")
        self.client = client or httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0))
        self.poll_wait_seconds = poll_wait_seconds

    def run_forever(self) -> None:
        self._ensure_configured()
        server = self._get_long_poll_server()
        logger.info("VK bot long poll started for group_id=%s", self.group_id)
        while True:
            try:
                response = self.client.get(
                    server["server"],
                    params={"act": "a_check", "key": server["key"], "ts": server["ts"], "wait": self.poll_wait_seconds},
                )
                response.raise_for_status()
                payload = response.json()
                if "failed" in payload:
                    server = self._recover_long_poll_server(payload, server)
                    continue
                server["ts"] = payload.get("ts", server["ts"])
                for update in payload.get("updates", []):
                    self.handle_update(update)
            except KeyboardInterrupt:
                raise
            except Exception as exc:  # noqa: BLE001 - keep bot alive after transient failures
                logger.warning("VK bot polling error: %s", exc)
                time.sleep(3)

    def handle_update(self, update: dict[str, Any]) -> None:
        if update.get("type") != "message_new":
            return
        message = update.get("object", {}).get("message", {})
        peer_id = message.get("peer_id")
        from_id = message.get("from_id")
        if not peer_id or not from_id or int(from_id) <= 0:
            return
        try:
            identity = self.get_user_identity(str(from_id))
            code_response = self.create_browser_login_code(identity)
            self.send_login_code(int(peer_id), code_response.code, code_response.app_url)
        except Exception as exc:  # noqa: BLE001 - answer user with stable text
            logger.warning("Failed to create VK browser login code for user_id=%s: %s", from_id, exc)
            self.send_text(int(peer_id), USER_ERROR_TEXT)

    def build_browser_login_payload(self, identity: VkUserIdentity, *, purpose: str = "login") -> dict[str, str]:
        payload = {
            "provider": "vk",
            "provider_user_id": identity.vk_user_id,
            "source": "vk_bot",
            "purpose": purpose,
        }
        if identity.display_name:
            payload["display_name"] = identity.display_name
        if identity.username:
            payload["username"] = identity.username
        if identity.photo_url:
            payload["photo_url"] = identity.photo_url
        return payload

    def create_browser_login_code(self, identity: VkUserIdentity, *, purpose: str = "login") -> BrowserLoginCodeCreateResponse:
        payload = self.build_browser_login_payload(identity, purpose=purpose)
        with self.session_factory() as db:
            assert isinstance(db, Session)
            service = BrowserLoginCodeService(db)
            code, record = service.create_code(**payload, created_by="vk-bot")
            db.commit()
            db.refresh(record)
            return BrowserLoginCodeCreateResponse(code=code, expires_at=record.expires_at, app_url=service.build_app_url())

    def create_browser_link_code(self, identity: VkUserIdentity) -> BrowserLoginCodeCreateResponse:
        return self.create_browser_login_code(identity, purpose="identity_link")

    def get_user_identity(self, vk_user_id: str) -> VkUserIdentity:
        try:
            data = self._vk_api("users.get", {"user_ids": vk_user_id, "fields": "screen_name,photo_100"})
            user = data[0] if data else {}
            first_name = (user.get("first_name") or "").strip()
            last_name = (user.get("last_name") or "").strip()
            display_name = " ".join(part for part in (first_name, last_name) if part) or None
            return VkUserIdentity(
                vk_user_id=vk_user_id,
                display_name=display_name,
                username=(user.get("screen_name") or None),
                photo_url=(user.get("photo_100") or None),
            )
        except Exception as exc:  # noqa: BLE001 - identity enrichment is optional
            logger.info("Could not load VK user profile for user_id=%s: %s", vk_user_id, exc)
            return VkUserIdentity(vk_user_id=vk_user_id)

    def send_login_code(self, peer_id: int, code: str, app_url: str) -> None:
        keyboard = {"inline": True, "buttons": [[{"action": {"type": "open_link", "link": app_url, "label": OPEN_BUTTON_TEXT}}]]}
        self._vk_api("messages.send", {"peer_id": peer_id, "message": OPEN_TEXT.format(code=code), "keyboard": keyboard, "random_id": random.randint(1, 2_147_483_647)})

    def send_text(self, peer_id: int, text: str) -> None:
        self._vk_api("messages.send", {"peer_id": peer_id, "message": text, "random_id": random.randint(1, 2_147_483_647)})

    def _get_long_poll_server(self) -> dict[str, Any]:
        data = self._vk_api("groups.getLongPollServer", {"group_id": self.group_id})
        return {"server": data["server"], "key": data["key"], "ts": data["ts"]}

    def _recover_long_poll_server(self, payload: dict[str, Any], server: dict[str, Any]) -> dict[str, Any]:
        failed = payload.get("failed")
        if failed == 1 and payload.get("ts"):
            server["ts"] = payload["ts"]
            return server
        return self._get_long_poll_server()

    def _vk_api(self, method: str, params: dict[str, Any]) -> Any:
        self._ensure_configured()
        request_params = {**params, "access_token": self.token, "v": VK_API_VERSION}
        response = self.client.post(f"{self.api_url}/{method}", json=request_params)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise VkBotError(f"VK API {method} failed: {payload['error'].get('error_msg', 'unknown error')}")
        return payload.get("response")

    def _ensure_configured(self) -> None:
        if not self.token:
            raise VkBotError("VK_BOT_TOKEN is not configured")
        if not self.group_id:
            raise VkBotError("VK_BOT_GROUP_ID is not configured")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Bloom Club VK bot")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    VkBotService().run_forever()


if __name__ == "__main__":
    main()
