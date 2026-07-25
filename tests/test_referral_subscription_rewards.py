from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.models.client import ClientProfile, ClientReferral, ReferralSubscriptionReward
from app.models.payment import Subscription, SubscriptionStatus
from app.models.user import User, UserRole
from app.services.referral_subscription_rewards import process_paid_referral_reward


def _session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _client(db: Session, index: int) -> ClientProfile:
    user = User(email=f"referral-reward-{index}@example.test", role=UserRole.CLIENT.value, is_active=True)
    db.add(user)
    db.flush()
    profile = ClientProfile(user_id=user.id, is_active=True, referral_code=f"REWARD{index:02d}")
    db.add(profile)
    db.flush()
    return profile


def test_every_five_qualifying_paid_referrals_extend_subscription_once() -> None:
    db = _session()
    now = datetime.now(timezone.utc)
    referrer = _client(db, 0)
    current = Subscription(
        client_id=referrer.id,
        status=SubscriptionStatus.active.value,
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=10),
        source="tochka",
    )
    db.add(current)
    referred_clients = []
    for index in range(1, 11):
        referred = _client(db, index)
        referred_clients.append(referred)
        db.add(
            ClientReferral(
                referrer_client_id=referrer.id,
                referred_client_id=referred.id,
                referral_code=referrer.referral_code,
                reward_entries_count=1,
            )
        )
    db.commit()
    original_end = current.ends_at

    for index, referred in enumerate(referred_clients[:4], start=1):
        rewards = process_paid_referral_reward(
            db,
            referred_client_id=referred.id,
            paid_amount=Decimal("349.00"),
            qualification_source=f"tochka:{index}",
            now=now,
        )
        assert rewards == []

    rewards = process_paid_referral_reward(
        db,
        referred_client_id=referred_clients[4].id,
        paid_amount=Decimal("349.00"),
        qualification_source="tochka:5",
        now=now,
    )
    db.flush()

    assert len(rewards) == 1
    assert current.ends_at == original_end + timedelta(days=30)
    assert db.query(ReferralSubscriptionReward).count() == 1

    duplicate = process_paid_referral_reward(
        db,
        referred_client_id=referred_clients[4].id,
        paid_amount=Decimal("349.00"),
        qualification_source="tochka:5",
        now=now,
    )
    assert duplicate == []
    assert current.ends_at == original_end + timedelta(days=30)
    assert db.query(ReferralSubscriptionReward).count() == 1

    for index, referred in enumerate(referred_clients[5:], start=6):
        process_paid_referral_reward(
            db,
            referred_client_id=referred.id,
            paid_amount=Decimal("349.00"),
            qualification_source=f"tochka:{index}",
            now=now,
        )
    db.flush()
    assert current.ends_at == original_end + timedelta(days=60)
    assert db.query(ReferralSubscriptionReward).count() == 2


def test_one_ruble_payment_does_not_qualify_referral() -> None:
    db = _session()
    referrer = _client(db, 10)
    referred = _client(db, 11)
    relation = ClientReferral(
        referrer_client_id=referrer.id,
        referred_client_id=referred.id,
        referral_code=referrer.referral_code,
        reward_entries_count=1,
    )
    db.add(relation)
    db.commit()

    rewards = process_paid_referral_reward(
        db,
        referred_client_id=referred.id,
        paid_amount=Decimal("1.00"),
        qualification_source="tochka:test-one-ruble",
    )

    assert rewards == []
    assert relation.paid_qualified_at is None
    assert db.query(ReferralSubscriptionReward).count() == 0
