from __future__ import annotations

from datetime import datetime, timezone
import secrets
import string
from urllib.parse import quote

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.client import ClientProfile, ClientReferral, GiveawayEntry
from app.models.giveaway import Giveaway, GiveawayNumber
from app.models.payment import Subscription, SubscriptionStatus

REFERRAL_EXISTING_PROFILE_ERROR = "Личный кабинет уже был создан ранее. Реферальный код можно использовать только при первом входе."
REFERRAL_INVALID_ERROR = "Реферальный код не найден или недействителен."
REFERRAL_SELF_ERROR = "Нельзя использовать собственный реферальный код."


class ReferralError(ValueError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


REWARD_ENTRIES_PER_REFERRAL = 5
REFERRAL_SOURCE = "referral"
_REFERRAL_CODE_ALPHABET = string.ascii_uppercase + string.digits


def referral_link(code: str | None) -> str | None:
    if not code:
        return None
    base = (settings.WEB_PUBLIC_URL or "https://bloomclub.ru").rstrip("/")
    return f"{base}/?startapp={quote(code)}"


def ensure_referral_code(db: Session, client: ClientProfile) -> str:
    if client.referral_code:
        return client.referral_code
    for _ in range(30):
        code = "".join(secrets.choice(_REFERRAL_CODE_ALPHABET) for _ in range(8))
        exists = db.execute(select(ClientProfile.id).where(ClientProfile.referral_code == code)).scalar_one_or_none()
        if exists is None:
            client.referral_code = code
            db.flush()
            return code
    raise RuntimeError("Could not generate referral code")


def _referral_owner_filter(db: Session, client_id: int):
    referral_code_value = db.execute(select(ClientProfile.referral_code).where(ClientProfile.id == client_id)).scalar_one_or_none()
    criteria = [ClientReferral.referrer_client_id == client_id]
    if referral_code_value:
        criteria.append(ClientReferral.referral_code == referral_code_value)
    return or_(*criteria)


def _active_giveaway_id(db: Session, now: datetime | None = None) -> int | None:
    now = now or datetime.now(timezone.utc)
    return db.execute(
        select(Giveaway.id)
        .where(
            Giveaway.is_active.is_(True),
            or_(Giveaway.starts_at.is_(None), Giveaway.starts_at <= now),
            or_(Giveaway.ends_at.is_(None), Giveaway.ends_at >= now),
        )
        .order_by(Giveaway.starts_at.desc().nullslast(), Giveaway.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def referral_counts(db: Session, client_id: int) -> tuple[int, int]:
    criteria = _referral_owner_filter(db, client_id)
    referrals_count = db.execute(select(func.count(func.distinct(ClientReferral.referred_client_id))).where(criteria)).scalar_one()
    earned_entries_count = db.execute(
        select(func.coalesce(func.sum(GiveawayEntry.entries_count), 0)).where(
            GiveawayEntry.client_id == client_id,
            GiveawayEntry.source == REFERRAL_SOURCE,
        )
    ).scalar_one()
    active_giveaway_id = _active_giveaway_id(db)
    referral_numbers_count = 0
    if active_giveaway_id is not None:
        referral_numbers_count = int(
            db.execute(
                select(func.count(GiveawayNumber.id)).where(
                    GiveawayNumber.giveaway_id == active_giveaway_id,
                    GiveawayNumber.client_id == client_id,
                    GiveawayNumber.source == REFERRAL_SOURCE,
                )
            ).scalar_one()
            or 0
        )
    return int(referrals_count or 0), max(int(earned_entries_count or 0), referral_numbers_count)


def activated_referrals_count(db: Session, client_id: int, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    criteria = _referral_owner_filter(db, client_id)
    return int(
        db.execute(
            select(func.count(func.distinct(ClientReferral.referred_client_id)))
            .join(ClientProfile, ClientProfile.id == ClientReferral.referred_client_id)
            .join(Subscription, Subscription.client_id == ClientProfile.id)
            .where(
                criteria,
                Subscription.status == SubscriptionStatus.active.value,
                Subscription.starts_at <= now,
                Subscription.ends_at >= now,
            )
        ).scalar_one()
        or 0
    )


def normalize_referral_code(referral_code_value: str | None) -> str | None:
    code = (referral_code_value or "").strip()
    return code or None


def get_referrer_by_code(db: Session, referral_code_value: str | None) -> ClientProfile | None:
    code = normalize_referral_code(referral_code_value)
    if not code:
        return None
    return db.execute(select(ClientProfile).where(ClientProfile.referral_code == code)).scalar_one_or_none()


def validate_referral_for_new_client(db: Session, referral_code_value: str | None, *, provider: str | None = None, provider_user_id: str | None = None, new_client: ClientProfile | None = None) -> ClientProfile | None:
    code = normalize_referral_code(referral_code_value)
    if not code:
        return None
    referrer = get_referrer_by_code(db, code)
    if referrer is None:
        raise ReferralError(REFERRAL_INVALID_ERROR)
    if new_client is not None and referrer.id == new_client.id:
        raise ReferralError(REFERRAL_SELF_ERROR)
    if provider and provider_user_id:
        normalized_provider = provider.strip().lower()
        normalized_provider_user_id = provider_user_id.strip()
        if (normalized_provider == "telegram" and referrer.telegram_user_id == normalized_provider_user_id) or (normalized_provider == "vk" and referrer.vk_user_id == normalized_provider_user_id):
            raise ReferralError(REFERRAL_SELF_ERROR)
    return referrer


def apply_referral_on_new_client(db: Session, new_client: ClientProfile, referral_code_value: str | None) -> ClientReferral | None:
    code = normalize_referral_code(referral_code_value)
    if not code:
        return None
    referrer = validate_referral_for_new_client(db, code, new_client=new_client)
    if referrer is None:
        return None
    existing = db.execute(select(ClientReferral).where(ClientReferral.referred_client_id == new_client.id)).scalar_one_or_none()
    if existing is not None:
        return existing
    now = datetime.now(timezone.utc)
    referral = ClientReferral(referrer_client_id=referrer.id, referred_client_id=new_client.id, referral_code=code, reward_entries_count=REWARD_ENTRIES_PER_REFERRAL, reward_granted_at=now)
    db.add(referral)
    db.flush()
    new_client.referred_by_referral_id = referral.id
    db.add(GiveawayEntry(client_id=referrer.id, source=REFERRAL_SOURCE, entries_count=REWARD_ENTRIES_PER_REFERRAL, related_referral_id=referral.id))
    return referral
