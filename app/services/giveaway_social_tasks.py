from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client import ClientProfile
from app.models.giveaway import Giveaway, GiveawayNumber, GiveawaySocialTask
from app.models.user import User
from app.services.social_subscriptions import (
    TELEGRAM_SOURCE,
    VK_SOURCE,
    SOCIAL_SOURCES,
    check_telegram_membership,
    check_vk_membership,
    is_number_active,
)

logger = logging.getLogger(__name__)


@dataclass
class GiveawayTaskCheckResult:
    task_id: int | None
    platform: str
    subscribed: bool
    entry_active: bool
    entry_number: str | None
    message: str
    status: str = "ok"


def next_number(db: Session, giveaway_id: int) -> str:
    count = int(
        db.execute(
            select(func.count(GiveawayNumber.id)).where(
                GiveawayNumber.giveaway_id == giveaway_id
            )
        ).scalar_one()
        or 0
    )
    return f"{count + 1:06d}"


def build_legacy_social_tasks(giveaway: Giveaway) -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    if giveaway.telegram_reward_enabled and giveaway.telegram_community_url and giveaway.telegram_chat_id:
        tasks.append(
            {
                "id": None,
                "platform": "telegram",
                "task_type": "subscription",
                "title": "Подписаться на Telegram-канал",
                "description": "Подпишитесь на Telegram-канал и получите дополнительный номерок.",
                "community_url": giveaway.telegram_community_url,
                "external_id": giveaway.telegram_chat_id,
                "reward_numbers": giveaway.telegram_reward_numbers or 1,
                "enabled": True,
                "sort_order": 0,
                "source": TELEGRAM_SOURCE,
                "source_reference": "legacy:telegram",
            }
        )
    if giveaway.vk_reward_enabled and giveaway.vk_community_url and giveaway.vk_group_id:
        tasks.append(
            {
                "id": None,
                "platform": "vk",
                "task_type": "subscription",
                "title": "Подписаться на VK-сообщество",
                "description": "Подпишитесь на VK-сообщество и получите дополнительный номерок.",
                "community_url": giveaway.vk_community_url,
                "external_id": giveaway.vk_group_id,
                "reward_numbers": giveaway.vk_reward_numbers or 1,
                "enabled": True,
                "sort_order": 1,
                "source": VK_SOURCE,
                "source_reference": "legacy:vk",
            }
        )
    return tasks


def serialize_social_tasks(
    giveaway: Giveaway | None,
    *,
    db: Session | None = None,
    client_id: int | None = None,
) -> list[dict[str, object]]:
    if giveaway is None:
        return []

    if giveaway.social_tasks:
        tasks = [
            {
                "id": task.id,
                "platform": task.platform,
                "task_type": task.task_type,
                "title": task.title,
                "description": task.description,
                "community_url": task.community_url,
                "external_id": task.external_id,
                "reward_numbers": task.reward_numbers or 1,
                "enabled": bool(task.is_active and task.community_url and task.external_id),
                "sort_order": task.sort_order,
                "source": TELEGRAM_SOURCE if task.platform == "telegram" else VK_SOURCE,
                "source_reference": f"task:{task.id}",
            }
            for task in giveaway.social_tasks
        ]
    else:
        tasks = build_legacy_social_tasks(giveaway)

    if db is None or client_id is None:
        for task in tasks:
            task["completed"] = False
            task["entry_number"] = None
        return tasks

    rows = db.execute(
        select(
            GiveawayNumber.source,
            GiveawayNumber.source_reference,
            GiveawayNumber.number,
            GiveawayNumber.is_active,
            GiveawayNumber.status,
        ).where(
            GiveawayNumber.giveaway_id == giveaway.id,
            GiveawayNumber.client_id == client_id,
            GiveawayNumber.source.in_(SOCIAL_SOURCES),
        )
    ).all()
    completion_map = {
        (source, source_reference): number
        for source, source_reference, number, is_active, status in rows
        if is_active and status == "active"
    }
    for task in tasks:
        number = completion_map.get((task["source"], task["source_reference"]))
        task["completed"] = bool(number)
        task["entry_number"] = number
    return tasks


def apply_social_task_payload(giveaway: Giveaway, tasks_payload: list[object]) -> None:
    existing_by_id = {task.id: task for task in giveaway.social_tasks}
    requested_ids = {
        int(item.id)
        for item in tasks_payload
        if getattr(item, "id", None) is not None
    }

    for existing in list(giveaway.social_tasks):
        if existing.id not in requested_ids:
            giveaway.social_tasks.remove(existing)

    for index, item in enumerate(tasks_payload):
        task = existing_by_id.get(getattr(item, "id", None))
        if task is None:
            task = GiveawaySocialTask()
            giveaway.social_tasks.append(task)
        task.platform = item.platform
        task.task_type = item.task_type
        task.title = item.title.strip()
        task.description = (item.description or "").strip() or None
        task.community_url = (item.community_url or "").strip() or None
        task.external_id = (item.external_id or "").strip() or None
        task.reward_numbers = item.reward_numbers
        task.is_active = bool(item.is_active)
        task.sort_order = index


def sync_legacy_social_fields_from_tasks(giveaway: Giveaway) -> None:
    telegram_task = next(
        (
            task
            for task in giveaway.social_tasks
            if task.platform == "telegram" and task.is_active and task.community_url and task.external_id
        ),
        None,
    )
    vk_task = next(
        (
            task
            for task in giveaway.social_tasks
            if task.platform == "vk" and task.is_active and task.community_url and task.external_id
        ),
        None,
    )

    giveaway.telegram_community_url = telegram_task.community_url if telegram_task else None
    giveaway.telegram_chat_id = telegram_task.external_id if telegram_task else None
    giveaway.telegram_reward_enabled = telegram_task is not None
    giveaway.telegram_reward_numbers = 1

    giveaway.vk_community_url = vk_task.community_url if vk_task else None
    giveaway.vk_group_id = vk_task.external_id if vk_task else None
    giveaway.vk_reward_enabled = vk_task is not None
    giveaway.vk_reward_numbers = 1


def _resolve_task(giveaway: Giveaway, *, task_id: int | None = None, platform: str | None = None) -> GiveawaySocialTask | dict[str, object] | None:
    if task_id is not None:
        for task in giveaway.social_tasks:
            if task.id == task_id:
                return task
        return None
    if platform is None:
        return None
    if giveaway.social_tasks:
        for task in giveaway.social_tasks:
            if task.platform == platform and task.is_active:
                return task
    for task in build_legacy_social_tasks(giveaway):
        if task["platform"] == platform:
            return task
    return None


def _source_for_platform(platform: str) -> str:
    return TELEGRAM_SOURCE if platform == "telegram" else VK_SOURCE


def _reference_for_task(task: GiveawaySocialTask | dict[str, object]) -> str:
    if isinstance(task, GiveawaySocialTask):
        return f"task:{task.id}"
    return str(task.get("source_reference") or "")


def _community_id_for_task(task: GiveawaySocialTask | dict[str, object]) -> str | None:
    if isinstance(task, GiveawaySocialTask):
        return task.external_id
    return str(task.get("external_id") or "") or None


def upsert_task_number(
    db: Session,
    *,
    giveaway_id: int,
    client_id: int,
    source: str,
    source_reference: str,
    subscribed: bool,
    platform: str,
    community_id: str | None,
) -> GiveawayNumber | None:
    excluded = db.execute(
        select(User.exclude_from_giveaways)
        .join(ClientProfile, ClientProfile.user_id == User.id)
        .where(ClientProfile.id == client_id)
    ).scalar_one_or_none()
    if excluded:
        return None

    now = datetime.now(timezone.utc)
    number = db.execute(
        select(GiveawayNumber).where(
            GiveawayNumber.giveaway_id == giveaway_id,
            GiveawayNumber.client_id == client_id,
            GiveawayNumber.source == source,
            GiveawayNumber.source_reference == source_reference,
        )
    ).scalar_one_or_none()

    if subscribed:
        if number is None:
            number = GiveawayNumber(
                giveaway_id=giveaway_id,
                client_id=client_id,
                number=next_number(db, giveaway_id),
                source=source,
                source_reference=source_reference,
            )
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


def check_social_task(
    db: Session,
    giveaway: Giveaway,
    client: ClientProfile,
    *,
    task_id: int | None = None,
    platform: str | None = None,
) -> GiveawayTaskCheckResult:
    task = _resolve_task(giveaway, task_id=task_id, platform=platform)
    if task is None:
        return GiveawayTaskCheckResult(task_id, platform or "unknown", False, False, None, "Задание не настроено.", "not_configured")

    resolved_platform = task.platform if isinstance(task, GiveawaySocialTask) else str(task.get("platform") or platform or "")
    community_id = _community_id_for_task(task)
    source = _source_for_platform(resolved_platform)
    source_reference = _reference_for_task(task)

    if resolved_platform == "telegram":
        if not client.telegram_user_id:
            return GiveawayTaskCheckResult(getattr(task, "id", None), resolved_platform, False, False, None, "Для проверки нужно привязать Telegram.", "identity_required")
        try:
            subscribed = check_telegram_membership(str(community_id), client.telegram_user_id)
        except Exception as exc:
            logger.warning("Telegram subscription check failed: %s", exc)
            return GiveawayTaskCheckResult(getattr(task, "id", None), resolved_platform, False, False, None, "Проверка Telegram временно недоступна.", "verification_error")
    elif resolved_platform == "vk":
        if not client.vk_user_id:
            return GiveawayTaskCheckResult(getattr(task, "id", None), resolved_platform, False, False, None, "Для автоматической проверки нужно привязать VK.", "identity_required")
        try:
            subscribed = check_vk_membership(str(community_id), client.vk_user_id)
        except Exception as exc:
            logger.warning("VK subscription check failed: %s", exc)
            return GiveawayTaskCheckResult(getattr(task, "id", None), resolved_platform, False, False, None, "Проверка VK временно недоступна.", "verification_error")
    else:
        return GiveawayTaskCheckResult(getattr(task, "id", None), resolved_platform, False, False, None, "Неподдерживаемый тип задания.", "not_supported")

    number = upsert_task_number(
        db,
        giveaway_id=giveaway.id,
        client_id=client.id,
        source=source,
        source_reference=source_reference,
        subscribed=subscribed,
        platform=resolved_platform,
        community_id=community_id,
    )
    if subscribed and number is not None:
        return GiveawayTaskCheckResult(getattr(task, "id", None), resolved_platform, True, True, number.number, "Номерок зачислен. Проверьте его в списке ваших номеров.")
    return GiveawayTaskCheckResult(
        getattr(task, "id", None),
        resolved_platform,
        False,
        False,
        number.number if number else None,
        "Подписка не найдена. Номерок не зачислен." if number else "Подписка не найдена.",
    )


def recheck_social_tasks(db: Session, giveaway: Giveaway) -> dict[str, int]:
    stats = {"checked": 0, "active": 0, "deactivated": 0, "reactivated": 0, "errors": 0}
    rows = db.execute(
        select(GiveawayNumber)
        .join(ClientProfile, ClientProfile.id == GiveawayNumber.client_id)
        .join(User, User.id == ClientProfile.user_id)
        .where(
            GiveawayNumber.giveaway_id == giveaway.id,
            GiveawayNumber.source.in_(SOCIAL_SOURCES),
            User.exclude_from_giveaways.is_(False),
        )
    ).scalars().all()
    for number in rows:
        before = is_number_active(number)
        client = db.get(ClientProfile, number.client_id)
        if client is None or not client.is_active:
            if before:
                number.is_active = False
                number.status = "revoked"
                number.deactivated_at = datetime.now(timezone.utc)
                number.deactivation_reason = "client_inactive_or_deleted"
                stats["deactivated"] += 1
            continue

        task_id = None
        if (number.source_reference or "").startswith("task:"):
            try:
                task_id = int((number.source_reference or "").split(":", 1)[1])
            except ValueError:
                task_id = None
        platform = "telegram" if number.source == TELEGRAM_SOURCE else "vk"
        result = check_social_task(db, giveaway, client, task_id=task_id, platform=platform)
        stats["checked"] += 1
        if result.status == "verification_error":
            stats["errors"] += 1
        after_number = db.get(GiveawayNumber, number.id)
        after = bool(after_number and is_number_active(after_number))
        if after:
            stats["active"] += 1
        if before and not after:
            stats["deactivated"] += 1
        if not before and after:
            stats["reactivated"] += 1
    db.flush()
    return stats
