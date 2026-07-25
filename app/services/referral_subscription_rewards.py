from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client import ClientReferral, ReferralSubscriptionReward
from app.models.payment import Subscription, SubscriptionStatus


PAID_REFERRALS_PER_REWARD = 5
REFERRAL_REWARD_DAYS = 30
MINIMUM_QUALIFYING_PAYMENT = Decimal("349.00")


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _grant_reward_subscription(db: Session, referrer_client_id: int, now: datetime) -> Subscription:
    current = db.execute(
        select(Subscription)
        .where(
            Subscription.client_id == referrer_client_id,
            Subscription.status == SubscriptionStatus.active.value,
        )
        .order_by(Subscription.ends_at.desc(), Subscription.id.desc())
        .with_for_update()
        .limit(1)
    ).scalar_one_or_none()
    if current is not None and _aware(current.ends_at) > now:
        current.ends_at = _aware(current.ends_at) + timedelta(days=REFERRAL_REWARD_DAYS)
        return current

    subscription = Subscription(
        client_id=referrer_client_id,
        status=SubscriptionStatus.active.value,
        starts_at=now,
        ends_at=now + timedelta(days=REFERRAL_REWARD_DAYS),
        source="referral_reward",
    )
    db.add(subscription)
    db.flush()
    return subscription


def process_paid_referral_reward(
    db: Session,
    *,
    referred_client_id: int,
    paid_amount: Decimal,
    qualification_source: str,
    now: datetime | None = None,
) -> list[ReferralSubscriptionReward]:
    if paid_amount < MINIMUM_QUALIFYING_PAYMENT:
        return []

    now = now or datetime.now(timezone.utc)
    referral = db.execute(
        select(ClientReferral)
        .where(ClientReferral.referred_client_id == referred_client_id)
        .with_for_update()
    ).scalar_one_or_none()
    if referral is None:
        return []
    if referral.paid_qualified_at is None:
        referral.paid_qualified_at = now
        referral.paid_qualification_source = qualification_source
        db.flush()

    qualified_count = int(
        db.execute(
            select(func.count(ClientReferral.id)).where(
                ClientReferral.referrer_client_id == referral.referrer_client_id,
                ClientReferral.paid_qualified_at.is_not(None),
            )
        ).scalar_one()
        or 0
    )
    earned_periods = qualified_count // PAID_REFERRALS_PER_REWARD
    granted_periods = int(
        db.execute(
            select(func.count(ReferralSubscriptionReward.id)).where(
                ReferralSubscriptionReward.referrer_client_id == referral.referrer_client_id
            )
        ).scalar_one()
        or 0
    )

    rewards: list[ReferralSubscriptionReward] = []
    for reward_period in range(granted_periods + 1, earned_periods + 1):
        subscription = _grant_reward_subscription(db, referral.referrer_client_id, now)
        reward = ReferralSubscriptionReward(
            referrer_client_id=referral.referrer_client_id,
            reward_period=reward_period,
            qualified_referrals_count=reward_period * PAID_REFERRALS_PER_REWARD,
            reward_days=REFERRAL_REWARD_DAYS,
            subscription_id=subscription.id,
            granted_at=now,
        )
        db.add(reward)
        db.flush()
        rewards.append(reward)
    return rewards
