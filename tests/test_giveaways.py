from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.giveaway import Giveaway, GiveawayPrize, GiveawayNumber
from app.models.client import ClientProfile, ClientReferral
from app.models.payment import Subscription, SubscriptionStatus
from app.models.user import User, UserRole
from app.services.giveaways import get_active_giveaway, ensure_user_numbers


def _session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _client(db: Session, email: str) -> ClientProfile:
    user = User(email=email, role=UserRole.CLIENT.value, is_active=True)
    db.add(user)
    db.flush()
    profile = ClientProfile(user_id=user.id, is_active=True, referral_code=email.split("@")[0])
    db.add(profile)
    db.flush()
    return profile


def _active_subscription(db: Session, client_id: int) -> None:
    now = datetime.now(timezone.utc)
    db.add(Subscription(client_id=client_id, status=SubscriptionStatus.active.value, starts_at=now - timedelta(days=1), ends_at=now + timedelta(days=30)))
    db.flush()


def test_giveaway_creation_model_migration_shape() -> None:
    db = _session()
    giveaway = Giveaway(title="Розыгрыш месяца", is_active=True, winners_count=1, prizes=[GiveawayPrize(place_number=1, prize_title="Фен Dyson", winner_provider="telegram", winner_provider_user_id="123", winning_number="000001")])
    db.add(giveaway)
    db.commit()
    assert giveaway.id is not None
    assert giveaway.prizes[0].prize_title == "Фен Dyson"


def test_only_active_giveaway_returned() -> None:
    db = _session()
    db.add_all([Giveaway(title="old", is_active=False, winners_count=1), Giveaway(title="active", is_active=True, winners_count=1)])
    db.commit()
    assert get_active_giveaway(db).title == "active"


def test_user_with_active_subscription_gets_one_base_number() -> None:
    db = _session()
    client = _client(db, "client@example.com")
    _active_subscription(db, client.id)
    giveaway = Giveaway(title="active", is_active=True, winners_count=1)
    db.add(giveaway)
    db.commit()
    numbers = ensure_user_numbers(db, giveaway.id, client.id)
    assert [(n.number, n.source) for n in numbers] == [("000001", "subscription")]


def test_user_with_one_activated_referral_gets_two_numbers_total() -> None:
    db = _session()
    referrer = _client(db, "referrer@example.com")
    referred = _client(db, "referred@example.com")
    _active_subscription(db, referrer.id)
    _active_subscription(db, referred.id)
    db.add(ClientReferral(referrer_client_id=referrer.id, referred_client_id=referred.id, referral_code="referrer", reward_entries_count=1))
    giveaway = Giveaway(title="active", is_active=True, winners_count=1)
    db.add(giveaway)
    db.commit()
    numbers = ensure_user_numbers(db, giveaway.id, referrer.id)
    assert len(numbers) == 2
    assert [n.source for n in numbers].count("referral") == 1


def test_legacy_extra_referral_numbers_are_revoked_under_one_number_rule() -> None:
    db = _session()
    referrer = _client(db, "legacy-referrer@example.com")
    referred = _client(db, "legacy-referred@example.com")
    _active_subscription(db, referrer.id)
    _active_subscription(db, referred.id)
    db.add(ClientReferral(referrer_client_id=referrer.id, referred_client_id=referred.id, referral_code="legacy", reward_entries_count=1))
    giveaway = Giveaway(title="active", is_active=True, winners_count=1)
    db.add(giveaway)
    db.flush()
    db.add_all(
        [
            GiveawayNumber(giveaway_id=giveaway.id, client_id=referrer.id, number=f"{index:06d}", source="referral")
            for index in range(1, 6)
        ]
    )
    db.commit()

    numbers = ensure_user_numbers(db, giveaway.id, referrer.id)

    assert [number.source for number in numbers].count("referral") == 1
    revoked = db.query(GiveawayNumber).filter_by(source="referral", status="revoked").all()
    assert len(revoked) == 4
    assert all(number.deactivation_reason == "referral_reward_rule_reduced" for number in revoked)


def test_numbers_are_not_duplicated_on_repeated_requests() -> None:
    db = _session()
    client = _client(db, "client@example.com")
    _active_subscription(db, client.id)
    giveaway = Giveaway(title="active", is_active=True, winners_count=1)
    db.add(giveaway)
    db.commit()
    first = ensure_user_numbers(db, giveaway.id, client.id)
    second = ensure_user_numbers(db, giveaway.id, client.id)
    assert [n.number for n in first] == [n.number for n in second]
    assert db.query(GiveawayNumber).count() == 1


def test_guest_response_contract_does_not_require_numbers() -> None:
    db = _session()
    giveaway = Giveaway(title="active", is_active=True, winners_count=1)
    db.add(giveaway)
    db.commit()
    assert get_active_giveaway(db).title == "active"
    assert db.query(GiveawayNumber).count() == 0


def test_admin_giveaway_prizes_are_upserted_by_place_number() -> None:
    from app.api.v1.endpoints.admin import _apply_giveaway_payload
    from app.schemas.giveaway import GiveawayPrizeWrite, GiveawayWrite

    db = _session()
    giveaway = Giveaway(title="Июль", is_active=True, winners_count=1)
    db.add(giveaway)
    _apply_giveaway_payload(
        giveaway,
        GiveawayWrite(
            title="Июль",
            is_active=True,
            winners_count=1,
            prizes=[GiveawayPrizeWrite(place_number=1, prize_title="Старый приз")],
        ),
    )
    db.commit()

    _apply_giveaway_payload(
        giveaway,
        GiveawayWrite(
            title="Июль обновлён",
            is_active=True,
            winners_count=1,
            prizes=[GiveawayPrizeWrite(place_number=1, prize_title="Новый приз")],
        ),
    )
    db.commit()
    db.refresh(giveaway)

    assert db.query(GiveawayPrize).filter_by(giveaway_id=giveaway.id).count() == 1
    assert giveaway.prizes[0].place_number == 1
    assert giveaway.prizes[0].prize_title == "Новый приз"


def test_admin_giveaway_prizes_add_and_remove_places_without_duplicates() -> None:
    from app.api.v1.endpoints.admin import _apply_giveaway_payload
    from app.schemas.giveaway import GiveawayPrizeWrite, GiveawayWrite

    db = _session()
    giveaway = Giveaway(title="Июль", is_active=True, winners_count=1)
    db.add(giveaway)
    db.flush()

    _apply_giveaway_payload(
        giveaway,
        GiveawayWrite(
            title="Июль",
            is_active=True,
            winners_count=3,
            prizes=[
                GiveawayPrizeWrite(place_number=1, prize_title="Первый"),
                GiveawayPrizeWrite(place_number=2, prize_title="Второй"),
                GiveawayPrizeWrite(place_number=3, prize_title="Третий"),
            ],
        ),
    )
    db.commit()
    assert db.query(GiveawayPrize).filter_by(giveaway_id=giveaway.id).count() == 3

    _apply_giveaway_payload(
        giveaway,
        GiveawayWrite(
            title="Июль",
            is_active=True,
            winners_count=1,
            prizes=[GiveawayPrizeWrite(place_number=1, prize_title="Первый обновлён")],
        ),
    )
    db.commit()

    prizes = db.query(GiveawayPrize).filter_by(giveaway_id=giveaway.id).order_by(GiveawayPrize.place_number).all()
    assert [(prize.place_number, prize.prize_title) for prize in prizes] == [(1, "Первый обновлён")]

    _apply_giveaway_payload(
        giveaway,
        GiveawayWrite(
            title="Июль",
            is_active=True,
            winners_count=1,
            prizes=[GiveawayPrizeWrite(place_number=1, prize_title="Первый обновлён")],
        ),
    )
    db.commit()

    assert db.query(GiveawayPrize).filter_by(giveaway_id=giveaway.id).count() == 1



def test_active_giveaway_subscriptions_are_grouped_by_participant() -> None:
    from app.api.v1.endpoints.admin import _active_subscriptions_by_client

    db = _session()
    paid_client = _client(db, "paid@example.com")
    trial_client = _client(db, "trial@example.com")
    inactive_client = _client(db, "inactive@example.com")
    now = datetime.now(timezone.utc)
    db.add_all(
        [
            Subscription(
                client_id=paid_client.id,
                status=SubscriptionStatus.active.value,
                starts_at=now - timedelta(days=1),
                ends_at=now + timedelta(days=30),
                source="tochka",
            ),
            Subscription(
                client_id=trial_client.id,
                status=SubscriptionStatus.active.value,
                starts_at=now - timedelta(days=1),
                ends_at=now + timedelta(days=14),
                source="trial",
            ),
            Subscription(
                client_id=inactive_client.id,
                status=SubscriptionStatus.expired.value,
                starts_at=now - timedelta(days=30),
                ends_at=now - timedelta(days=1),
                source="tochka",
            ),
        ]
    )
    db.commit()

    active = _active_subscriptions_by_client(
        db,
        {paid_client.id, trial_client.id, inactive_client.id},
        now=now,
    )

    assert set(active) == {paid_client.id, trial_client.id}
    assert active[paid_client.id].source == "tochka"
    assert active[trial_client.id].source == "trial"


def test_deleting_giveaway_removes_prizes_and_numbers() -> None:
    from app.api.v1.endpoints.admin import delete_admin_giveaway

    db = _session()
    client = _client(db, "delete-giveaway@example.com")
    giveaway = Giveaway(
        title="Удаляемый розыгрыш",
        is_active=False,
        winners_count=1,
        prizes=[GiveawayPrize(place_number=1, prize_title="Приз")],
    )
    db.add(giveaway)
    db.flush()
    db.add(
        GiveawayNumber(
            giveaway_id=giveaway.id,
            client_id=client.id,
            number="000001",
            source="manual",
        )
    )
    db.commit()
    giveaway_id = giveaway.id

    result = delete_admin_giveaway(giveaway_id, admin=None, db=db)

    assert result["deleted"]["id"] == giveaway_id
    assert result["deleted"]["prizes"] == 1
    assert result["deleted"]["numbers"] == 1
    assert db.get(Giveaway, giveaway_id) is None
    assert db.query(GiveawayPrize).filter_by(giveaway_id=giveaway_id).count() == 0
    assert db.query(GiveawayNumber).filter_by(giveaway_id=giveaway_id).count() == 0
