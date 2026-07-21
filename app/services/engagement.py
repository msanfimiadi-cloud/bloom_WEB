from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from random import Random
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.client import ClientProfile
from app.models.engagement import (
    BloomDailyTask,
    BloomGardenSettings,
    BloomLeaderboardReward,
    BloomPetalEvent,
    BloomSpecialSubmission,
    BloomSpecialQuestion,
    BloomSpecialTask,
    PartnerBotAccess,
    PartnerCodeAttempt,
)
from app.models.giveaway import Giveaway, GiveawayNumber
from app.models.partner import Partner
from app.models.verification import PrivilegeVerificationSession, PrivilegeVerificationStatus
from app.services.giveaways import create_bonus_number, get_active_giveaway, has_active_access
from app.services.offer_savings import calculate_offer_saving_snapshot
from app.services.privilege_verifications import as_aware_utc

PARTNER_CODE_ATTEMPT_WINDOW_MINUTES = 5
PARTNER_CODE_ATTEMPT_LIMIT = 10
FLOWER_CHECKIN_PETALS = 1
FLOWER_PRIVILEGE_PETALS = 5
FLOWER_STAGE_THRESHOLDS = (0, 5, 12, 22, 35)
FLOWER_RANK_REWARDS = {1: 10, 2: 8, 3: 6, 4: 4, 5: 4, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2}
CLUB_TIMEZONE = ZoneInfo("Asia/Novosibirsk")
FLOWER_PETAL_POSITIONS = ("top_left", "top_right", "middle_left", "middle_right", "bottom_left", "bottom_right")


def club_today() -> date:
    return datetime.now(CLUB_TIMEZONE).date()


def garden_settings(db: Session) -> BloomGardenSettings:
    return db.get(BloomGardenSettings, 1) or BloomGardenSettings(
        id=1, placement_mode="random", manual_position="top_right", daily_petals=FLOWER_CHECKIN_PETALS
    )


def daily_petal_position(settings: BloomGardenSettings, today: date) -> str:
    if settings.placement_mode == "manual" and settings.manual_position in FLOWER_PETAL_POSITIONS:
        return settings.manual_position
    seed = int.from_bytes(sha256(f"bloom-petal:{today.isoformat()}".encode()).digest()[:8], "big")
    return Random(seed).choice(FLOWER_PETAL_POSITIONS)


def get_partner_bot_access(db: Session, provider: str, provider_user_id: str, *, active_only: bool = True) -> PartnerBotAccess | None:
    conditions = [
        PartnerBotAccess.provider == provider.strip().lower(),
        PartnerBotAccess.provider_user_id == provider_user_id.strip(),
    ]
    if active_only:
        conditions.append(PartnerBotAccess.is_active.is_(True))
    return db.execute(
        select(PartnerBotAccess).options(selectinload(PartnerBotAccess.partner)).where(*conditions)
    ).scalar_one_or_none()


def check_partner_code(db: Session, access: PartnerBotAccess, code: str, *, now: datetime | None = None) -> PrivilegeVerificationSession:
    now = now or datetime.now(timezone.utc)
    recent_attempts = db.execute(
        select(func.count(PartnerCodeAttempt.id)).where(
            PartnerCodeAttempt.access_id == access.id,
            PartnerCodeAttempt.attempted_at >= now - timedelta(minutes=PARTNER_CODE_ATTEMPT_WINDOW_MINUTES),
        )
    ).scalar_one()
    if int(recent_attempts or 0) >= PARTNER_CODE_ATTEMPT_LIMIT:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too_many_code_attempts")

    normalized_code = "".join(character for character in code.strip().upper() if character.isalnum())
    session = db.execute(
        select(PrivilegeVerificationSession)
        .options(
            selectinload(PrivilegeVerificationSession.client),
            selectinload(PrivilegeVerificationSession.partner),
            selectinload(PrivilegeVerificationSession.offer),
        )
        .where(
            PrivilegeVerificationSession.code == normalized_code,
            PrivilegeVerificationSession.partner_id == access.partner_id,
        )
        .order_by(PrivilegeVerificationSession.created_at.desc(), PrivilegeVerificationSession.id.desc())
    ).scalars().first()
    success = session is not None
    db.add(PartnerCodeAttempt(access_id=access.id, was_successful=success, attempted_at=now))
    access.last_activity_at = now
    db.flush()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="code_not_found")
    if session.confirmed_at is not None or session.status == PrivilegeVerificationStatus.confirmed.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="code_already_activated")
    if session.status == PrivilegeVerificationStatus.expired.value or as_aware_utc(session.expires_at) < now:
        session.status = PrivilegeVerificationStatus.expired.value
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="code_expired")
    if session.status not in {PrivilegeVerificationStatus.active.value, PrivilegeVerificationStatus.pending.value}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="code_not_active")
    if session.client is None or not session.client.is_active or session.client.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="client_inactive")
    if not has_active_access(db, session.client_id, now):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="subscription_inactive")
    return session


def confirm_verification(
    db: Session,
    session: PrivilegeVerificationSession,
    *,
    partner: Partner,
    bot_access: PartnerBotAccess | None = None,
    now: datetime | None = None,
) -> tuple[PrivilegeVerificationSession, GiveawayNumber | None]:
    now = now or datetime.now(timezone.utc)
    locked = db.execute(
        select(PrivilegeVerificationSession)
        .options(
            selectinload(PrivilegeVerificationSession.client),
            selectinload(PrivilegeVerificationSession.partner),
            selectinload(PrivilegeVerificationSession.offer),
        )
        .where(PrivilegeVerificationSession.id == session.id)
        .with_for_update()
    ).scalar_one()
    if locked.partner_id != partner.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="code_for_another_partner")
    if locked.confirmed_at is not None or locked.status == PrivilegeVerificationStatus.confirmed.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="code_already_activated")
    if as_aware_utc(locked.expires_at) < now:
        locked.status = PrivilegeVerificationStatus.expired.value
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="code_expired")
    if locked.client is None or not locked.client.is_active or locked.client.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="client_inactive")
    if not has_active_access(db, locked.client_id, now):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="subscription_inactive")

    saving = calculate_offer_saving_snapshot(locked.offer)
    locked.status = PrivilegeVerificationStatus.confirmed.value
    locked.confirmed_at = now
    locked.confirmed_by_partner_id = partner.id
    locked.confirmed_by_bot_access_id = bot_access.id if bot_access is not None else None
    locked.saving_base_price = saving.regular_price
    locked.saving_final_price = saving.club_price
    locked.saving_discount_percent = saving.discount_percent
    locked.saving_amount = saving.saving_amount
    locked.saving_partner_name = locked.partner.name if locked.partner is not None else partner.name
    locked.saving_offer_title = locked.offer.title if locked.offer is not None else None
    locked.saving_used_at = now

    event_day = now.astimezone(CLUB_TIMEZONE).date()
    db.add(BloomPetalEvent(
        client_id=locked.client_id,
        event_date=event_day,
        month_start=month_start_for(event_day),
        source="privilege",
        idempotency_key=f"privilege:{locked.id}",
        petals=FLOWER_PRIVILEGE_PETALS,
    ))

    giveaway = get_active_giveaway(db, now)
    bonus_number = None
    if giveaway is not None:
        db.execute(select(Giveaway).where(Giveaway.id == giveaway.id).with_for_update()).scalar_one()
        bonus_number = create_bonus_number(
            db,
            giveaway_id=giveaway.id,
            client_id=locked.client_id,
            source="privilege_activation",
            source_reference=f"verification:{locked.id}",
        )
    if bot_access is not None:
        bot_access.activation_count += 1
        bot_access.last_activity_at = now
    db.commit()
    db.refresh(locked)
    return locked, bonus_number


def month_start_for(day: date) -> date:
    return day.replace(day=1)


def flower_state(db: Session, client_id: int, *, today: date | None = None) -> dict[str, object]:
    today = today or club_today()
    month_start = month_start_for(today)
    settings = garden_settings(db)
    tasks = db.execute(
        select(BloomDailyTask).where(
            BloomDailyTask.is_active.is_(True),
            (BloomDailyTask.starts_on.is_(None) | (BloomDailyTask.starts_on <= today)),
            (BloomDailyTask.ends_on.is_(None) | (BloomDailyTask.ends_on >= today)),
        ).order_by(BloomDailyTask.sort_order, BloomDailyTask.id)
    ).scalars().all()
    events = db.execute(
        select(BloomPetalEvent).where(
            BloomPetalEvent.client_id == client_id,
            BloomPetalEvent.month_start == month_start,
        ).order_by(BloomPetalEvent.event_date)
    ).scalars().all()
    completed_keys = {event.idempotency_key for event in events}
    petals = sum(event.petals for event in events)
    checkin_dates = {event.event_date for event in events if event.source == "checkin"}
    streak = 0
    cursor = today if today in checkin_dates else today - timedelta(days=1)
    while cursor in checkin_dates:
        streak += 1
        cursor -= timedelta(days=1)

    leaderboard_rows = db.execute(
        select(BloomPetalEvent.client_id, func.sum(BloomPetalEvent.petals).label("petals"))
        .where(BloomPetalEvent.month_start == month_start)
        .group_by(BloomPetalEvent.client_id)
        .order_by(func.sum(BloomPetalEvent.petals).desc(), BloomPetalEvent.client_id.asc())
    ).all()
    ranked_rows: list[tuple[int, object]] = []
    previous_petals = None
    current_rank = 0
    for index, row in enumerate(leaderboard_rows, 1):
        if previous_petals != int(row.petals or 0):
            current_rank = index
            previous_petals = int(row.petals or 0)
        ranked_rows.append((current_rank, row))
    rank = next((place for place, row in ranked_rows if row.client_id == client_id), None)
    visible_rows = [(place, row) for place, row in ranked_rows if place <= 10]
    client_ids = [row.client_id for _, row in visible_rows]
    profiles = {
        profile.id: profile
        for profile in db.execute(select(ClientProfile).where(ClientProfile.id.in_(client_ids))).scalars().all()
    } if client_ids else {}
    special_task = db.execute(
        select(BloomSpecialTask)
        .options(selectinload(BloomSpecialTask.questions).selectinload(BloomSpecialQuestion.options))
        .where(
            BloomSpecialTask.is_active.is_(True),
            BloomSpecialTask.starts_on <= today,
            BloomSpecialTask.ends_on >= today,
        )
        .order_by(BloomSpecialTask.starts_on.desc(), BloomSpecialTask.id.desc())
    ).scalars().first()
    special_completed = False
    if special_task is not None:
        special_completed = db.execute(select(BloomSpecialSubmission.id).where(
            BloomSpecialSubmission.task_id == special_task.id,
            BloomSpecialSubmission.client_id == client_id,
        )).scalar_one_or_none() is not None
    days_in_month = monthrange(today.year, today.month)[1]
    return {
        "month": month_start.isoformat(),
        "petals": petals,
        "streak": streak,
        "stage": max(index for index, threshold in enumerate(FLOWER_STAGE_THRESHOLDS) if petals >= threshold),
        "stage_count": len(FLOWER_STAGE_THRESHOLDS),
        "checked_in_today": today in checkin_dates,
        "petal_position": daily_petal_position(settings, today),
        "petal_reward": settings.daily_petals,
        "days_grown": len(checkin_dates),
        "days_in_month": days_in_month,
        "rank": rank,
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "petals": task.petals,
                "completed_today": f"task:{task.id}:{today.isoformat()}" in completed_keys,
            }
            for task in tasks
        ],
        "special_task": {
            "id": special_task.id,
            "title": special_task.title,
            "description": special_task.description,
            "petals": special_task.petals,
            "starts_on": special_task.starts_on,
            "ends_on": special_task.ends_on,
            "completed": special_completed,
            "questions": special_task.questions,
        } if special_task is not None and special_task.questions else None,
        "leaderboard": [
            {
                "place": place,
                "client_id": row.client_id,
                "display_name": (profiles.get(row.client_id).full_name if profiles.get(row.client_id) else None) or f"Участница {row.client_id}",
                "petals": int(row.petals or 0),
                "is_current_user": row.client_id == client_id,
            }
            for place, row in visible_rows
        ],
    }


def award_petals(db: Session, client_id: int, *, source: str, task: BloomDailyTask | None = None, today: date | None = None) -> bool:
    today = today or club_today()
    key = f"checkin:{today.isoformat()}" if source == "checkin" else f"task:{task.id}:{today.isoformat()}"
    petals = garden_settings(db).daily_petals if source == "checkin" else int(task.petals)
    db.add(BloomPetalEvent(client_id=client_id, task_id=task.id if task else None, event_date=today, month_start=month_start_for(today), source=source, idempotency_key=key, petals=petals))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return False
    if source == "checkin":
        dates = set(db.execute(select(BloomPetalEvent.event_date).where(
            BloomPetalEvent.client_id == client_id,
            BloomPetalEvent.source == "checkin",
            BloomPetalEvent.event_date <= today,
        )).scalars().all())
        streak = 0
        cursor = today
        while cursor in dates:
            streak += 1
            cursor -= timedelta(days=1)
        bonuses: list[tuple[str, int]] = []
        if streak % 7 == 0:
            bonuses.append((f"streak7:{today.isoformat()}", 3))
        if streak % 30 == 0:
            bonuses.append((f"streak30:{today.isoformat()}", 10))
        for bonus_key, bonus_petals in bonuses:
            db.add(BloomPetalEvent(client_id=client_id, event_date=today, month_start=month_start_for(today), source="streak", idempotency_key=bonus_key, petals=bonus_petals))
    db.commit()
    return True


def settle_flower_leaderboard(db: Session, month_start: date, giveaway: Giveaway) -> list[BloomLeaderboardReward]:
    rows = db.execute(
        select(BloomPetalEvent.client_id, func.sum(BloomPetalEvent.petals).label("petals"))
        .where(BloomPetalEvent.month_start == month_start)
        .group_by(BloomPetalEvent.client_id)
        .order_by(func.sum(BloomPetalEvent.petals).desc(), BloomPetalEvent.client_id.asc())
    ).all()
    selected: list[tuple[int, object]] = []
    cursor = 0
    while cursor < len(rows) and len(selected) < 10:
        group_petals = int(rows[cursor].petals or 0)
        group: list[object] = []
        while cursor < len(rows) and int(rows[cursor].petals or 0) == group_petals:
            group.append(rows[cursor])
            cursor += 1
        place = len(selected) + 1
        slots = 10 - len(selected)
        if len(group) > slots:
            seed = int.from_bytes(sha256(f"bloom-rank:{month_start.isoformat()}:{giveaway.id}:{group_petals}".encode()).digest()[:8], "big")
            group = Random(seed).sample(group, slots)
            group.sort(key=lambda row: row.client_id)
        selected.extend((place, row) for row in group)
    rewards: list[BloomLeaderboardReward] = []
    for place, row in selected:
        existing = db.execute(select(BloomLeaderboardReward).where(BloomLeaderboardReward.month_start == month_start, BloomLeaderboardReward.client_id == row.client_id)).scalar_one_or_none()
        if existing is not None:
            rewards.append(existing)
            continue
        count = FLOWER_RANK_REWARDS[place]
        reward = BloomLeaderboardReward(month_start=month_start, client_id=row.client_id, giveaway_id=giveaway.id, place=place, entries_count=count)
        db.add(reward)
        db.flush()
        for index in range(1, count + 1):
            create_bonus_number(db, giveaway_id=giveaway.id, client_id=row.client_id, source="flower_rank", source_reference=f"{month_start.isoformat()}:{row.client_id}:{index}")
        rewards.append(reward)
    db.commit()
    return rewards
