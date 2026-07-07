from __future__ import annotations

from datetime import datetime, timezone
import secrets
import string
from urllib.parse import quote

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.client import ClientProfile, ClientReferral, GiveawayEntry

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


def referral_counts(db: Session, client_id: int) -> tuple[int, int]:
    referrals_count = db.execute(select(func.count(ClientReferral.id)).where(ClientReferral.referrer_client_id == client_id)).scalar_one()
    entries_count = db.execute(select(func.coalesce(func.sum(GiveawayEntry.entries_count), 0)).where(GiveawayEntry.client_id == client_id)).scalar_one()
    return int(referrals_count or 0), int(entries_count or 0)


def apply_referral_on_new_client(db: Session, new_client: ClientProfile, referral_code_value: str | None) -> ClientReferral | None:
    code = (referral_code_value or "").strip()
    if not code:
        return None
    referrer = db.execute(select(ClientProfile).where(ClientProfile.referral_code == code)).scalar_one_or_none()
    if referrer is None or referrer.id == new_client.id:
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
