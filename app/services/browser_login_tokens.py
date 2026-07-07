from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.client import BrowserLoginToken

TOKEN_BYTES = 32


def generate_browser_login_token() -> str:
    """Generate an opaque one-time browser login token for client delivery only."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_browser_login_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class BrowserLoginTokenService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_token(
        self,
        *,
        provider: str,
        provider_user_id: str,
        display_name: str | None = None,
        username: str | None = None,
        photo_url: str | None = None,
        referral_code: str | None = None,
        source: str | None = None,
        ttl_seconds: int | None = None,
        created_by: str | None = None,
    ) -> tuple[str, BrowserLoginToken]:
        token = generate_browser_login_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=ttl_seconds or settings.BROWSER_LOGIN_TOKEN_TTL_SECONDS
        )
        record = BrowserLoginToken(
            token_hash=hash_browser_login_token(token),
            provider=provider,
            provider_user_id=provider_user_id,
            display_name=display_name,
            username=username,
            photo_url=photo_url,
            referral_code=referral_code,
            source=source,
            expires_at=expires_at,
            created_by=created_by,
        )
        self.db.add(record)
        self.db.flush()
        return token, record

    def get_by_token(self, token: str) -> BrowserLoginToken | None:
        token_hash = hash_browser_login_token(token)
        return self.db.execute(
            select(BrowserLoginToken).where(BrowserLoginToken.token_hash == token_hash)
        ).scalar_one_or_none()

    def is_expired(self, token_record: BrowserLoginToken, *, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        return ensure_aware_utc(token_record.expires_at) <= ensure_aware_utc(current)

    def mark_used(self, token_record: BrowserLoginToken, *, now: datetime | None = None) -> BrowserLoginToken:
        token_record.used_at = now or datetime.now(timezone.utc)
        self.db.flush()
        return token_record

    def revoke(self, token_record: BrowserLoginToken, *, now: datetime | None = None) -> BrowserLoginToken:
        token_record.revoked_at = now or datetime.now(timezone.utc)
        self.db.flush()
        return token_record

    def build_login_url(self, token: str) -> str:
        base_url = settings.BROWSER_APP_PUBLIC_URL.rstrip("/")
        return f"{base_url}/login?{urlencode({'t': token})}"
