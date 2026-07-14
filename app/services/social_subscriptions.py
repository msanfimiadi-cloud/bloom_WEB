from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.client import ClientProfile
from app.models.giveaway import Giveaway, GiveawayNumber

logger = logging.getLogger(__name__)

TELEGRAM_SOURCE = "telegram_subscription"
VK_SOURCE = "vk_subscription"
SOCIAL_SOURCES = {TELEGRAM_SOURCE, VK_SOURCE}


@dataclass
class SocialCheckResult:
    platform: str
    subscribed: bool
    entry_active: bool
    entry_number: str | None
    message: str
    status: str = "ok"


def social_task_settings(giveaway: Giveaway | None) -> dict[str, dict[str, object]]:
    if giveaway is None:
        return {"telegram": {"enabled": False}, "vk": {"enabled": False}}
    return {
        "telegram": {
            "enabled": bool(giveaway.telegram_reward_enabled and giveaway.telegram_community_url and giveaway.telegram_chat_id),
            "community_url": giveaway.telegram_community_url,
            "reward_numbers": giveaway.telegram_reward_numbers or 1,
        },
        "vk": {
            "enabled": bool(giveaway.vk_reward_enabled and giveaway.vk_community_url and giveaway.vk_group_id),
            "community_url": giveaway.vk_community_url,
            "reward_numbers": giveaway.vk_reward_numbers or 1,
        },
    }


def is_number_active(number: GiveawayNumber) -> bool:
    return bool(number.is_active and number.status == "active")


def next_number(db: Session, giveaway_id: int) -> str:
    count = int(db.execute(select(func.count(GiveawayNumber.id)).where(GiveawayNumber.giveaway_id == giveaway_id)).scalar_one() or 0)
    return f"{count + 1:06d}"


def upsert_social_number(db: Session, giveaway_id: int, client_id: int, source: str, subscribed: bool, platform: str, community_id: str | None) -> GiveawayNumber | None:
    now = datetime.now(timezone.utc)
    number = db.execute(select(GiveawayNumber).where(GiveawayNumber.giveaway_id == giveaway_id, GiveawayNumber.client_id == client_id, GiveawayNumber.source == source)).scalar_one_or_none()
    if subscribed:
        if number is None:
            number = GiveawayNumber(giveaway_id=giveaway_id, client_id=client_id, number=next_number(db, giveaway_id), source=source)
            db.add(number)
            db.flush()
        elif not is_number_active(number):
            number.reactivated_at = now
        number.is_active = True
        number.status = "active"
        number.deactivated_at = None
        number.deactivation_reason = None
        number.verified_at = now
        number.verification_platform = platform
        number.external_community_id = community_id
        db.add(number)
        return number
    if number is not None and is_number_active(number):
        number.is_active = False
        number.status = "revoked"
        number.deactivated_at = now
        number.deactivation_reason = f"{platform}_subscription_not_found"
        number.verified_at = now
        number.verification_platform = platform
        number.external_community_id = community_id
        db.add(number)
    return number


def _telegram_member_from_payload(payload: dict) -> bool:
    result = payload.get("result") or {}
    status = result.get("status")
    if status in {"creator", "administrator", "member"}:
        return True
    if status == "restricted":
        return bool(result.get("is_member"))
    return False


def check_telegram_membership(chat_id: str, user_id: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("telegram_bot_token_not_configured")
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getChatMember"
    with httpx.Client(timeout=10) as client:
        response = client.get(url, params={"chat_id": chat_id, "user_id": user_id})
    data = response.json()
    if response.status_code >= 400 or not data.get("ok"):
        raise RuntimeError(str(data.get("description") or "telegram_api_error"))
    return _telegram_member_from_payload(data)


def check_vk_membership(group_id: str, user_id: str) -> bool:
    token = settings.VK_SERVICE_TOKEN or settings.VK_BOT_TOKEN
    if not token:
        raise RuntimeError("vk_token_not_configured")
    with httpx.Client(timeout=10) as client:
        response = client.get("https://api.vk.com/method/groups.isMember", params={"group_id": group_id, "user_id": user_id, "access_token": token, "v": "5.199"})
    data = response.json()
    if response.status_code >= 400 or data.get("error"):
        raise RuntimeError(str((data.get("error") or {}).get("error_msg") or "vk_api_error"))
    return bool(int(data.get("response") or 0))


def check_and_apply(db: Session, giveaway: Giveaway, client: ClientProfile, platform: str) -> SocialCheckResult:
    if platform == "telegram":
        source = TELEGRAM_SOURCE
        if not (giveaway.telegram_reward_enabled and giveaway.telegram_chat_id and giveaway.telegram_community_url):
            return SocialCheckResult(platform, False, False, None, "Задание Telegram не настроено.", "not_configured")
        if not client.telegram_user_id:
            return SocialCheckResult(platform, False, False, None, "Для проверки нужно привязать Telegram.", "identity_required")
        try:
            subscribed = check_telegram_membership(giveaway.telegram_chat_id, client.telegram_user_id)
        except Exception as exc:
            logger.warning("Telegram subscription check failed: %s", exc)
            return SocialCheckResult(platform, False, False, None, "Проверка Telegram временно недоступна.", "verification_error")
        community_id = giveaway.telegram_chat_id
    elif platform == "vk":
        source = VK_SOURCE
        if not (giveaway.vk_reward_enabled and giveaway.vk_group_id and giveaway.vk_community_url):
            return SocialCheckResult(platform, False, False, None, "Задание VK не настроено.", "not_configured")
        if not client.vk_user_id:
            return SocialCheckResult(platform, False, False, None, "Для автоматической проверки нужно привязать VK.", "identity_required")
        try:
            subscribed = check_vk_membership(giveaway.vk_group_id, client.vk_user_id)
        except Exception as exc:
            logger.warning("VK subscription check failed: %s", exc)
            return SocialCheckResult(platform, False, False, None, "Проверка VK временно недоступна.", "verification_error")
        community_id = giveaway.vk_group_id
    else:
        raise ValueError("unsupported platform")
    number = upsert_social_number(db, giveaway.id, client.id, source, subscribed, platform, community_id)
    if subscribed and number is not None:
        return SocialCheckResult(platform, True, True, number.number, "Подписка подтверждена. Номер начислен.")
    return SocialCheckResult(platform, False, False, number.number if number else None, "Подписка не найдена. Номер не участвует." if number else "Подписка не найдена.")


def recheck_giveaway_social_subscriptions(db: Session, giveaway: Giveaway) -> dict[str, int]:
    stats = {"checked": 0, "active": 0, "deactivated": 0, "reactivated": 0, "errors": 0}
    rows = db.execute(select(GiveawayNumber).where(GiveawayNumber.giveaway_id == giveaway.id, GiveawayNumber.source.in_(SOCIAL_SOURCES))).scalars().all()
    for number in rows:
        before = is_number_active(number)
        client = db.get(ClientProfile, number.client_id)
        if client is None or not client.is_active:
            if before:
                number.is_active = False; number.status = "revoked"; number.deactivated_at = datetime.now(timezone.utc); number.deactivation_reason = "client_inactive_or_deleted"; stats["deactivated"] += 1
            continue
        result = check_and_apply(db, giveaway, client, "telegram" if number.source == TELEGRAM_SOURCE else "vk")
        stats["checked"] += 1
        if result.status == "verification_error": stats["errors"] += 1
        after_number = db.get(GiveawayNumber, number.id)
        after = bool(after_number and is_number_active(after_number))
        if after: stats["active"] += 1
        if before and not after: stats["deactivated"] += 1
        if not before and after: stats["reactivated"] += 1
    db.flush()
    return stats
