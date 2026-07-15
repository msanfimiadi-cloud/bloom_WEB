from __future__ import annotations

import logging
import secrets
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.client import BrowserLoginCode

logger = logging.getLogger(__name__)
LOGIN_CODE_TTL_SECONDS = 5 * 60
LOGIN_CODE_ALPHABET = string.ascii_uppercase + string.digits


def normalize_login_code(code: str) -> str:
    return code.strip().upper().replace(" ", "").replace("-", "")


def format_login_code(raw: str) -> str:
    normalized = normalize_login_code(raw)
    if normalized.startswith("BC"):
        normalized = normalized[2:]
    return f"BC-{normalized}"


def generate_login_code() -> str:
    suffix = "".join(secrets.choice(LOGIN_CODE_ALPHABET) for _ in range(6))
    return f"BC-{suffix}"


def ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class BrowserLoginCodeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_code(self, *, provider: str, provider_user_id: str, display_name: str | None = None, username: str | None = None, photo_url: str | None = None, referral_code: str | None = None, source: str | None = None, created_by: str | None = None) -> tuple[str, BrowserLoginCode]:
        normalized_provider = provider.strip().lower()
        normalized_provider_user_id = provider_user_id.strip()
        now = datetime.now(timezone.utc)
        active_code = self.db.execute(
            select(BrowserLoginCode)
            .where(
                BrowserLoginCode.provider == normalized_provider,
                BrowserLoginCode.provider_user_id == normalized_provider_user_id,
                BrowserLoginCode.used_at.is_(None),
                BrowserLoginCode.expires_at > now,
            )
            .order_by(BrowserLoginCode.created_at.desc(), BrowserLoginCode.id.desc())
        ).scalar_one_or_none()
        if active_code is not None:
            return active_code.login_code, active_code
        code = generate_login_code()
        record = BrowserLoginCode(
            provider=normalized_provider,
            provider_user_id=normalized_provider_user_id,
            login_code=code,
            display_name=display_name,
            username=username,
            photo_url=photo_url,
            referral_code=referral_code,
            source=source,
            expires_at=now + timedelta(seconds=LOGIN_CODE_TTL_SECONDS),
            created_by=created_by,
        )
        self.db.add(record)
        self.db.flush()
        return code, record

    def get_by_code(self, code: str) -> BrowserLoginCode | None:
        normalized = format_login_code(code)
        return self.db.execute(select(BrowserLoginCode).where(BrowserLoginCode.login_code == normalized)).scalar_one_or_none()

    def is_expired(self, record: BrowserLoginCode, *, now: datetime | None = None) -> bool:
        return ensure_aware_utc(record.expires_at) <= ensure_aware_utc(now or datetime.now(timezone.utc))

    def mark_failed_attempt(self, code: str) -> None:
        record = self.get_by_code(code)
        if record is not None:
            record.attempts_count += 1
            self.db.flush()
        logger.warning("Browser login code verification failed")

    def mark_used(self, record: BrowserLoginCode, *, now: datetime | None = None) -> BrowserLoginCode:
        record.used_at = now or datetime.now(timezone.utc)
        self.db.flush()
        return record

    def build_app_url(self) -> str:
        return settings.BROWSER_APP_PUBLIC_URL.rstrip("/")
