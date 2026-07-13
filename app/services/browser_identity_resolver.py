from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.client import ClientIdentityLink, ClientProfile
from app.models.user import User, UserRole
from app.services.referrals import REFERRAL_EXISTING_PROFILE_ERROR, ReferralError, apply_referral_on_new_client, ensure_referral_code, normalize_referral_code, validate_referral_for_new_client

logger = logging.getLogger(__name__)

BrowserIdentityResolveStatus = Literal["linked", "legacy_linked", "created", "not_found"]


@dataclass(frozen=True)
class BrowserIdentityResolveResult:
    status: BrowserIdentityResolveStatus
    provider: str
    provider_user_id: str
    client_profile: ClientProfile | None = None
    identity_link: ClientIdentityLink | None = None
    created_identity_link: bool = False
    created_client_profile: bool = False


class BrowserIdentityResolver:
    """Resolve browser login provider identities to client profiles.

    Login-code/browser-token authentication is a real user login flow, so an
    unknown provider identity creates a normal client ``User`` +
    ``ClientProfile`` and links it through ``client_identity_links``. Existing
    identity links and legacy provider fields are reused to avoid duplicates.
    """

    LEGACY_PROVIDER_FIELDS = {
        "telegram": ClientProfile.telegram_user_id,
        "vk": ClientProfile.vk_user_id,
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    def resolve(
        self,
        *,
        provider: str,
        provider_user_id: str,
        display_name: str | None = None,
        username: str | None = None,
        photo_url: str | None = None,
        referral_code: str | None = None,
        source: str | None = None,
        create_if_missing: bool = True,
    ) -> BrowserIdentityResolveResult:
        normalized_provider = provider.strip().lower()
        normalized_provider_user_id = provider_user_id.strip()
        normalized_username = self._clean(username)
        normalized_display_name = self._clean(display_name)
        normalized_source = self._clean(source) or f"{normalized_provider}_login_code"
        now = datetime.now(timezone.utc)

        normalized_referral_code = normalize_referral_code(referral_code)

        identity_link = self._get_identity_link(normalized_provider, normalized_provider_user_id)
        if identity_link is not None:
            profile = identity_link.client_profile
            self._sync_profile_metadata(profile, normalized_provider, normalized_provider_user_id, normalized_display_name, normalized_username, self._clean(photo_url), normalized_source)
            ensure_referral_code(self.db, profile)
            if normalized_referral_code:
                logger.info("browser_identity_referral_rejected", extra={"action": "browser_identity_referral_rejected", "provider_user_id": normalized_provider_user_id, "client_id": profile.id, "reason": "existing_identity_link"})
                raise ReferralError(REFERRAL_EXISTING_PROFILE_ERROR)
            logger.info("browser_identity_resolved", extra={"action": "browser_identity_resolved", "provider_user_id": normalized_provider_user_id, "client_id": profile.id, "status": "reused", "existing_deleted_client": False})
            return BrowserIdentityResolveResult("linked", normalized_provider, normalized_provider_user_id, profile, identity_link)

        profile = self._get_legacy_profile(normalized_provider, normalized_provider_user_id)
        status: BrowserIdentityResolveStatus = "legacy_linked"
        created_profile = False
        if profile is not None and normalized_referral_code:
            logger.info("browser_identity_referral_rejected", extra={"action": "browser_identity_referral_rejected", "provider_user_id": normalized_provider_user_id, "client_id": profile.id, "reason": "existing_legacy_profile"})
            raise ReferralError(REFERRAL_EXISTING_PROFILE_ERROR)
        if profile is None and not create_if_missing:
            return BrowserIdentityResolveResult("not_found", normalized_provider, normalized_provider_user_id)
        if profile is None:
            validate_referral_for_new_client(self.db, normalized_referral_code, provider=normalized_provider, provider_user_id=normalized_provider_user_id)
            user = User(role=UserRole.CLIENT.value, is_active=True)
            self.db.add(user)
            self.db.flush()
            profile = ClientProfile(user_id=user.id, is_active=True)
            self.db.add(profile)
            self.db.flush()
            created_profile = True
            status = "created"

        self._sync_profile_metadata(profile, normalized_provider, normalized_provider_user_id, normalized_display_name, normalized_username, self._clean(photo_url), normalized_source)
        ensure_referral_code(self.db, profile)
        if created_profile:
            referral = apply_referral_on_new_client(self.db, profile, normalized_referral_code)
            logger.info(
                "browser_identity_referral_applied",
                extra={
                    "action": "browser_identity_referral_applied",
                    "provider_user_id": normalized_provider_user_id,
                    "client_id": profile.id,
                    "referral_code_present": normalized_referral_code is not None,
                    "referral_relation_created": referral is not None,
                    "skip_reason": None if normalized_referral_code and referral is not None else ("no_referral_code" if not normalized_referral_code else "referral_not_created"),
                },
            )

        identity_link = ClientIdentityLink(
            client_profile_id=profile.id,
            provider=normalized_provider,
            provider_user_id=normalized_provider_user_id,
            linked_at=now,
            verified_at=now,
        )
        self.db.add(identity_link)
        self.db.flush()
        logger.info("browser_identity_resolved", extra={"action": "browser_identity_resolved", "provider_user_id": normalized_provider_user_id, "client_id": profile.id, "status": "created" if created_profile else "legacy_linked", "existing_deleted_client": False})
        return BrowserIdentityResolveResult(status, normalized_provider, normalized_provider_user_id, profile, identity_link, True, created_profile)

    def _sync_profile_metadata(self, profile: ClientProfile, provider: str, provider_user_id: str, display_name: str | None, username: str | None, photo_url: str | None, source: str | None) -> None:
        if display_name and profile.full_name != display_name:
            profile.full_name = display_name
        if source and not profile.source:
            profile.source = source
        if not profile.is_active:
            profile.is_active = True
        if provider == "telegram":
            profile.telegram_user_id = provider_user_id
            profile.telegram_username = username
            profile.telegram_photo_url = photo_url
            if display_name:
                first, _, last = display_name.partition(" ")
                profile.telegram_first_name = first or None
                profile.telegram_last_name = last or None
        elif provider == "vk":
            profile.vk_user_id = provider_user_id
            if hasattr(profile, "vk_username"):
                profile.vk_username = username

    @staticmethod
    def _clean(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def _get_identity_link(self, provider: str, provider_user_id: str) -> ClientIdentityLink | None:
        return self.db.execute(
            select(ClientIdentityLink)
            .options(joinedload(ClientIdentityLink.client_profile).joinedload(ClientProfile.user))
            .where(ClientIdentityLink.provider == provider, ClientIdentityLink.provider_user_id == provider_user_id)
        ).scalar_one_or_none()

    def _get_legacy_profile(self, provider: str, provider_user_id: str) -> ClientProfile | None:
        legacy_field = self.LEGACY_PROVIDER_FIELDS.get(provider)
        if legacy_field is None:
            return None
        return self.db.execute(
            select(ClientProfile).options(joinedload(ClientProfile.user)).where(legacy_field == provider_user_id)
        ).scalar_one_or_none()
