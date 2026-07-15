from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class VkBotSettings:
    vk_bot_token: str = os.getenv("VK_BOT_TOKEN", "")
    vk_group_id: str = os.getenv("VK_GROUP_ID", os.getenv("VK_BOT_GROUP_ID", ""))
    vk_api_version: str = os.getenv("VK_API_VERSION", "5.199")
    vk_longpoll_wait: int = int(os.getenv("VK_LONGPOLL_WAIT", "25"))
    vk_longpoll_mode: int = int(os.getenv("VK_LONGPOLL_MODE", "2"))
    vk_longpoll_version: int = int(os.getenv("VK_LONGPOLL_VERSION", "3"))
    internal_api_base_url: str = os.getenv("INTERNAL_API_BASE_URL", "http://127.0.0.1:8000")
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", os.getenv("BOT_SERVICE_TOKEN", ""))
    browser_app_url: str = os.getenv("BROWSER_APP_URL", os.getenv("BROWSER_APP_PUBLIC_URL", "https://app.bloomclub.ru"))
    profile_cache_ttl_seconds: int = int(os.getenv("VK_PROFILE_CACHE_TTL_SECONDS", "300"))

    def validate(self) -> None:
        missing = []
        if not self.vk_bot_token:
            missing.append("VK_BOT_TOKEN")
        if not self.vk_group_id:
            missing.append("VK_GROUP_ID")
        if not self.internal_api_key:
            missing.append("INTERNAL_API_KEY")
        if missing:
            raise RuntimeError(f"missing_required_env: {', '.join(missing)}")


settings = VkBotSettings()
