from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.client import ClientProfile, ClientReferral
from app.models.giveaway import Giveaway, GiveawayNumber
from app.models.user import User
from app.services.social_subscriptions import is_number_active
from app.models.payment import Subscription, SubscriptionStatus


def aware(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def get_active_giveaway(db: Session, now: datetime | None = None) -> Giveaway | None:
    now = now or datetime.now(timezone.utc)
    rows = db.execute(select(Giveaway).options(selectinload(Giveaway.prizes)).where(Giveaway.is_active.is_(True)).order_by(Giveaway.starts_at.desc().nullslast(), Giveaway.id.desc())).scalars().all()
    for giveaway in rows:
        if giveaway.starts_at and aware(giveaway.starts_at) > now:
            continue
        if giveaway.ends_at and aware(giveaway.ends_at) < now:
            continue
        return giveaway
    return rows[0] if rows else None


def has_active_access(db: Session, client_id: int, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    return db.execute(select(Subscription.id).where(Subscription.client_id == client_id, Subscription.status == SubscriptionStatus.active.value, Subscription.starts_at <= now, Subscription.ends_at >= now)).scalar_one_or_none() is not None


def is_client_excluded_from_giveaways(db: Session, client_id: int) -> bool:
    return bool(
        db.execute(
            select(User.exclude_from_giveaways)
            .join(ClientProfile, ClientProfile.user_id == User.id)
            .where(ClientProfile.id == client_id)
        ).scalar_one_or_none()
    )


def activated_referrals_count(db: Session, client_id: int, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    return int(db.execute(select(func.count(ClientReferral.id)).join(ClientProfile, ClientProfile.id == ClientReferral.referred_client_id).join(Subscription, Subscription.client_id == ClientProfile.id).where(ClientReferral.referrer_client_id == client_id, Subscription.status == SubscriptionStatus.active.value, Subscription.starts_at <= now, Subscription.ends_at >= now)).scalar_one() or 0)


def desired_number_sources(db: Session, client_id: int, now: datetime | None = None) -> list[str]:
    sources: list[str] = []
    if has_active_access(db, client_id, now):
        sources.append("subscription")
    sources.extend(["referral"] * activated_referrals_count(db, client_id, now))
    return sources


def ensure_user_numbers(db: Session, giveaway_id: int, client_id: int) -> list[GiveawayNumber]:
    if is_client_excluded_from_giveaways(db, client_id):
        return []
    sources = desired_number_sources(db, client_id)
    existing = db.execute(select(GiveawayNumber).where(GiveawayNumber.giveaway_id == giveaway_id, GiveawayNumber.client_id == client_id).order_by(GiveawayNumber.id)).scalars().all()
    managed_existing = [number for number in existing if number.source in {"subscription", "referral"}]
    desired_counts = Counter(sources)
    now = datetime.now(timezone.utc)

    for source in ("subscription", "referral"):
        source_numbers = [number for number in managed_existing if number.source == source]
        active_numbers = [number for number in source_numbers if is_number_active(number)]
        inactive_numbers = [number for number in source_numbers if not is_number_active(number)]
        target_count = desired_counts[source]

        while len(active_numbers) < target_count and inactive_numbers:
            number = inactive_numbers.pop(0)
            number.is_active = True
            number.status = "active"
            number.deactivated_at = None
            number.deactivation_reason = None
            number.reactivated_at = now
            active_numbers.append(number)

        while len(active_numbers) < target_count:
            created = create_bonus_number(
                db,
                giveaway_id=giveaway_id,
                client_id=client_id,
                source=source,
            )
            if created is None:
                break
            active_numbers.append(created)

        for number in active_numbers[target_count:]:
            number.is_active = False
            number.status = "revoked"
            number.deactivated_at = now
            number.deactivation_reason = (
                "referral_reward_rule_reduced"
                if source == "referral"
                else "subscription_access_not_active"
            )

    db.flush()
    existing = db.execute(select(GiveawayNumber).where(GiveawayNumber.giveaway_id == giveaway_id, GiveawayNumber.client_id == client_id).order_by(GiveawayNumber.id)).scalars().all()
    return [n for n in existing if is_number_active(n)]


def create_bonus_number(
    db: Session,
    *,
    giveaway_id: int,
    client_id: int,
    source: str,
    source_reference: str | None = None,
) -> GiveawayNumber | None:
    if is_client_excluded_from_giveaways(db, client_id):
        return None
    if source_reference:
        existing = db.execute(
            select(GiveawayNumber).where(
                GiveawayNumber.giveaway_id == giveaway_id,
                GiveawayNumber.source == source,
                GiveawayNumber.source_reference == source_reference,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing

    values = db.execute(
        select(GiveawayNumber.number).where(GiveawayNumber.giveaway_id == giveaway_id)
    ).scalars().all()
    numeric_values = [int(value) for value in values if str(value).isdigit()]
    next_number = max(numeric_values, default=0) + 1
    number = GiveawayNumber(
        giveaway_id=giveaway_id,
        client_id=client_id,
        number=f"{next_number:06d}",
        source=source,
        source_reference=source_reference,
    )
    db.add(number)
    db.flush()
    return number
