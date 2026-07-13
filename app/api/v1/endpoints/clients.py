from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
import logging
import hashlib
import hmac
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_optional_current_user, require_client
from app.core.categories import get_women_club_categories
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.city import City
from app.models.category import Category
from app.models.client import AccountLinkingChallenge, ClientIdentityLink, ClientProfile, ClientReferral, GiveawayEntry, VkLinkCode, VkLinkCodeStatus
from app.models.giveaway import Giveaway, GiveawayNumber
from app.models.partner import OfferPhoto, Partner, PartnerOffer, PartnerPhoto
from app.models.payment import PaymentReceipt, PaymentRequest, PaymentRequestStatus, Subscription, SubscriptionStatus
from app.models.verification import PrivilegeVerificationSession, PrivilegeVerificationStatus
from app.models.user import User
from app.schemas.activity import ActivityFeedRead
from app.schemas.browser_auth import BrowserLoginCodeRequest
from app.schemas.giveaway import GiveawayStateRead, PublicGiveawayRead, GiveawayPrizeRead, GiveawayNumberRead
from app.schemas.client import (
    ClientSiteCredentialsRead,
    ClientCityResponse,
    ClientLinkingConfirmRequest,
    ClientLinkingConfirmResponse,
    ClientLinkingStartRequest,
    ClientLinkingStartResponse,
    ClientLinkingStatusRead,
    ClientCreateVerificationRequest,
    ClientPartnerCatalogItem,
    ClientPartnerCategoryRead,
    ClientPartnerOfferRead,
    ClientPartnerPhotoRead,
    ClientProfileRead,
    ClientReferralSummaryItem,
    ClientReferralSummaryRead,
    ClientProfileUpdate,
    ClientSavingsItemRead,
    ClientSavingsPeriodRead,
    ClientSavingsRead,
    ClientVerificationRead,
    SubscriptionRead,
)
from app.schemas.payment import (
    PaymentReceiptCreate,
    PaymentReceiptRead,
    PaymentRequestCreate,
    PaymentRequestMarkPaid,
    PaymentRequestRead,
)
from app.schemas.vk import VkLinkCodeRead
from app.services.activity_feed import build_client_activity_feed
from app.services.browser_login_codes import BrowserLoginCodeService
from app.services.referrals import REWARD_ENTRIES_PER_REFERRAL, activated_referrals_count, ensure_referral_code, referral_counts, referral_link
from app.services.giveaways import ensure_user_numbers, get_active_giveaway
from app.services.offer_savings import calculate_offer_saving_snapshot
from app.services.site_credentials import (
    decrypt_site_password,
    ensure_client_site_credentials,
)
from app.services.privilege_verifications import (
    PRIVILEGE_VERIFICATION_TTL_SECONDS,
    apply_verification_status_filter,
    as_aware_utc,
    normalize_expired_verifications,
    ttl_seconds,
)

router = APIRouter(prefix="/clients", tags=["clients"])
logger = logging.getLogger(__name__)

CITY_NOT_FOUND_DETAIL = "City not found"
PARTNER_NOT_FOUND_DETAIL = "Partner not found"
OFFER_NOT_FOUND_DETAIL = "Offer not found"
OFFER_ID_CONFLICT_DETAIL = "offer_id and privilege_id must match"
ACTIVE_SUBSCRIPTION_REQUIRED_DETAIL = "Active subscription required"
VERIFICATION_CODE_ALPHABET = string.digits
PRIVILEGE_QR_PAYLOAD_PREFIX = "bloomclub:privilege:"
VK_LINK_CODE_TTL_SECONDS = 10 * 60
VK_LINK_CODE_LENGTH = 8
VK_LINK_CODE_ALPHABET = string.ascii_uppercase + string.digits
TRIAL_SUBSCRIPTION_DAYS = 15
TRIAL_SOURCE = "trial"
PAID_SOURCE = "paid"
LINKING_CHALLENGE_TTL_SECONDS = 600
LINKING_MAX_ATTEMPTS = 5
CATEGORY_DISPLAY_BY_SLUG = {item["slug"]: item["title"] for item in get_women_club_categories()}




@router.get("/me/linking-status", response_model=ClientLinkingStatusRead)
def read_client_linking_status(
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> ClientLinkingStatusRead:
    profile = _get_or_create_client_profile(db, current_user.id)
    has_vk_identity = bool(profile.vk_user_id)
    has_telegram_identity = bool(profile.telegram_user_id)
    has_site_login = bool(current_user.site_login or current_user.email or current_user.phone)
    is_linked = has_telegram_identity and (has_vk_identity or has_site_login)
    can_start_linking = has_telegram_identity and not is_linked
    return ClientLinkingStatusRead(
        has_vk_identity=has_vk_identity,
        has_telegram_identity=has_telegram_identity,
        has_site_login=has_site_login,
        is_linked=is_linked,
        can_start_linking=can_start_linking,
    )


@router.post("/me/linking/start", response_model=ClientLinkingStartResponse)
def start_client_account_linking(
    payload: ClientLinkingStartRequest,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> ClientLinkingStartResponse:
    current_profile = _get_or_create_client_profile(db, current_user.id)
    if not current_profile.telegram_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="telegram_identity_required")

    identifier_type, normalized_identifier = _normalize_linking_identifier(payload.identifier)
    candidates = _find_linking_candidates(db, current_profile.id, identifier_type, normalized_identifier)
    if not candidates:
        return ClientLinkingStartResponse(status="not_found")
    if len(candidates) > 1:
        return ClientLinkingStartResponse(status="multiple_matches")

    target_profile = candidates[0]
    now = datetime.now(timezone.utc)
    code = _generate_linking_code()
    challenge = AccountLinkingChallenge(
        id=secrets.token_urlsafe(24),
        current_client_profile_id=current_profile.id,
        target_client_profile_id=target_profile.id,
        identifier_type=identifier_type,
        identifier_hash=_linking_hash(f"{identifier_type}:{normalized_identifier}"),
        code_hash=_linking_hash(code),
        expires_at=now + timedelta(seconds=LINKING_CHALLENGE_TTL_SECONDS),
    )
    db.add(challenge)
    db.commit()
    response = ClientLinkingStartResponse(
        status="challenge_created",
        challenge_id=challenge.id,
        masked_identifier=_mask_linking_identifier(identifier_type, normalized_identifier),
        expires_in_seconds=LINKING_CHALLENGE_TTL_SECONDS,
    )
    if not settings.is_production:
        response.dev_code = code
    return response


@router.post("/me/linking/confirm", response_model=ClientLinkingConfirmResponse)
def confirm_client_account_linking(
    payload: ClientLinkingConfirmRequest,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> ClientLinkingConfirmResponse:
    current_profile = _get_or_create_client_profile(db, current_user.id)
    challenge = db.get(AccountLinkingChallenge, payload.challenge_id.strip())
    now = datetime.now(timezone.utc)
    if (
        challenge is None
        or challenge.current_client_profile_id != current_profile.id
        or challenge.consumed_at is not None
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_challenge")
    if as_aware_utc(challenge.expires_at) <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="expired_challenge")
    if challenge.attempts_count >= LINKING_MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="too_many_attempts")

    if not hmac.compare_digest(challenge.code_hash, _linking_hash(payload.code.strip())):
        challenge.attempts_count += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_code")

    target_profile = db.execute(
        select(ClientProfile).where(ClientProfile.id == challenge.target_client_profile_id)
    ).scalar_one_or_none()
    if target_profile is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="target_profile_not_found")
    if not current_profile.telegram_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="telegram_identity_required")
    if target_profile.telegram_user_id and target_profile.telegram_user_id != current_profile.telegram_user_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="target_has_another_telegram_identity")
    if _temporary_profile_has_activity(db, current_profile):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="temporary_profile_has_activity")

    telegram_user_id = current_profile.telegram_user_id
    telegram_fields = {
        field: getattr(current_profile, field)
        for field in ("telegram_username", "telegram_first_name", "telegram_last_name", "telegram_photo_url")
    }
    current_profile.telegram_user_id = None
    current_profile.telegram_username = None
    current_profile.telegram_first_name = None
    current_profile.telegram_last_name = None
    current_profile.telegram_photo_url = None
    current_profile.is_active = False
    db.flush()
    target_profile.telegram_user_id = telegram_user_id
    for field, value in telegram_fields.items():
        if value and not getattr(target_profile, field):
            setattr(target_profile, field, value)
    challenge.consumed_at = now
    challenge.attempts_count += 1

    existing_link = db.execute(
        select(ClientIdentityLink).where(
            ClientIdentityLink.provider == "telegram",
            ClientIdentityLink.provider_user_id == telegram_user_id,
        )
    ).scalar_one_or_none()
    if existing_link is None:
        db.add(
            ClientIdentityLink(
                provider="telegram",
                provider_user_id=telegram_user_id,
                client_profile_id=target_profile.id,
                linked_at=now,
                verified_at=now,
            )
        )
    else:
        existing_link.client_profile_id = target_profile.id
        existing_link.linked_at = existing_link.linked_at or now
        existing_link.verified_at = now

    db.commit()
    target_user = db.get(User, target_profile.user_id)
    if target_user is None or not target_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="target_user_inactive")
    db.refresh(target_profile)
    subscription = _get_current_active_subscription(db, target_profile.id, now)
    return ClientLinkingConfirmResponse(
        status="linked",
        access_token=create_access_token(f"user:{target_user.id}"),
        client=_client_profile_to_read(db, target_profile, target_user),
        subscription=_subscription_to_read(subscription, target_profile, now),
    )



@router.post("/me/linking/vk-login-code", response_model=ClientLinkingConfirmResponse)
def link_current_client_with_vk_login_code(
    payload: BrowserLoginCodeRequest,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> ClientLinkingConfirmResponse:
    current_profile = _get_or_create_client_profile(db, current_user.id)
    if not current_profile.telegram_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="telegram_identity_required")

    service = BrowserLoginCodeService(db)
    code_record = service.get_by_code(payload.code)
    if code_record is None:
        service.mark_failed_attempt(payload.code)
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="code_not_found")
    if code_record.provider != "vk":
        service.mark_failed_attempt(payload.code)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="vk_code_required")
    if service.is_expired(code_record):
        service.mark_failed_attempt(payload.code)
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="code_expired")
    if code_record.used_at is not None:
        service.mark_failed_attempt(payload.code)
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="code_already_used")

    now = datetime.now(timezone.utc)
    vk_user_id = code_record.provider_user_id
    target_profile = db.execute(select(ClientProfile).where(ClientProfile.vk_user_id == vk_user_id)).scalar_one_or_none()
    existing_vk_link = db.execute(select(ClientIdentityLink).where(ClientIdentityLink.provider == "vk", ClientIdentityLink.provider_user_id == vk_user_id)).scalar_one_or_none()
    if target_profile is None and existing_vk_link is not None:
        target_profile = db.get(ClientProfile, existing_vk_link.client_profile_id)

    telegram_user_id = current_profile.telegram_user_id
    target_profile = target_profile or current_profile
    if target_profile.id != current_profile.id:
        if target_profile.telegram_user_id and target_profile.telegram_user_id != telegram_user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="target_has_another_telegram_identity")
        if _temporary_profile_has_activity(db, current_profile):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="temporary_profile_has_activity")
        telegram_fields = {field: getattr(current_profile, field) for field in ("telegram_username", "telegram_first_name", "telegram_last_name", "telegram_photo_url")}
        current_profile.telegram_user_id = None
        current_profile.telegram_username = None
        current_profile.telegram_first_name = None
        current_profile.telegram_last_name = None
        current_profile.telegram_photo_url = None
        current_profile.is_active = False
        target_profile.telegram_user_id = telegram_user_id
        for field, value in telegram_fields.items():
            if value and not getattr(target_profile, field):
                setattr(target_profile, field, value)
    target_profile.vk_user_id = vk_user_id
    if code_record.username and hasattr(target_profile, "vk_username"):
        target_profile.vk_username = code_record.username
    ensure_referral_code(db, target_profile)

    for provider, provider_user_id in (("telegram", telegram_user_id), ("vk", vk_user_id)):
        link = db.execute(select(ClientIdentityLink).where(ClientIdentityLink.provider == provider, ClientIdentityLink.provider_user_id == provider_user_id)).scalar_one_or_none()
        if link is None:
            db.add(ClientIdentityLink(provider=provider, provider_user_id=provider_user_id, client_profile_id=target_profile.id, linked_at=now, verified_at=now))
        else:
            link.client_profile_id = target_profile.id
            link.linked_at = link.linked_at or now
            link.verified_at = now

    service.mark_used(code_record)
    db.commit()
    target_user = db.get(User, target_profile.user_id)
    if target_user is None or not target_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="target_user_inactive")
    db.refresh(target_profile)
    subscription = _get_current_active_subscription(db, target_profile.id, now)
    return ClientLinkingConfirmResponse(status="linked", access_token=create_access_token(f"user:{target_user.id}"), client=_client_profile_to_read(db, target_profile, target_user), subscription=_subscription_to_read(subscription, target_profile, now))

@router.get("/me", response_model=ClientProfileRead)
def read_client_me(
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> ClientProfileRead:
    profile = _get_or_create_client_profile(db, current_user.id)
    return _client_profile_to_read(db, profile, current_user)


@router.get("/me/referral", response_model=ClientReferralSummaryRead)
def read_client_referral(
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> ClientReferralSummaryRead:
    profile = _get_or_create_client_profile(db, current_user.id)
    code = ensure_referral_code(db, profile)
    db.commit()
    referrals_count, earned_entries_count = referral_counts(db, profile.id)
    rows = db.execute(
        select(ClientReferral, ClientProfile)
        .join(ClientProfile, ClientProfile.id == ClientReferral.referred_client_id)
        .where(ClientReferral.referrer_client_id == profile.id)
        .order_by(ClientReferral.created_at.desc(), ClientReferral.id.desc())
    ).all()
    return ClientReferralSummaryRead(
        referral_code=code,
        referral_link=referral_link(code) or "",
        referrals_count=referrals_count,
        activated_referrals_count=activated_referrals_count(db, profile.id),
        earned_entries_count=earned_entries_count,
        earned_giveaway_entries_count=earned_entries_count,
        reward_entries_per_referral=REWARD_ENTRIES_PER_REFERRAL,
        referrals=[ClientReferralSummaryItem(id=r.id, referred_client_id=r.referred_client_id, first_name=c.telegram_first_name, username=c.telegram_username, created_at=r.created_at, reward_entries_count=r.reward_entries_count) for r, c in rows],
    )


@router.get("/giveaway", response_model=GiveawayStateRead)
def read_client_giveaway(
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> GiveawayStateRead:
    giveaway = get_active_giveaway(db)
    if giveaway is None:
        return GiveawayStateRead(has_active_giveaway=False, message="no_active_giveaway")
    public = PublicGiveawayRead(
        id=giveaway.id,
        title=giveaway.title,
        description=giveaway.description,
        prizes=[GiveawayPrizeRead(id=p.id, place_number=p.place_number, prize_title=p.prize_title) for p in sorted(giveaway.prizes, key=lambda item: item.place_number)],
    )
    if current_user is None:
        return GiveawayStateRead(has_active_giveaway=True, giveaway=public, guest=True, message="login_required")
    profile = _get_or_create_client_profile(db, current_user.id)
    numbers = ensure_user_numbers(db, giveaway.id, profile.id)
    db.commit()
    return GiveawayStateRead(
        has_active_giveaway=True,
        giveaway=public,
        user_numbers_count=len(numbers),
        numbers=[GiveawayNumberRead(number=n.number, source=n.source) for n in numbers],
    )


@router.get("/me/site-credentials", response_model=ClientSiteCredentialsRead)
def read_client_site_credentials(
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> ClientSiteCredentialsRead:
    _get_or_create_client_profile(db, current_user.id)
    generated_credentials, plain_password = ensure_client_site_credentials(db, current_user)
    if generated_credentials:
        db.commit()
        db.refresh(current_user)
    if not current_user.site_login or (plain_password is None and not current_user.encrypted_site_password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site credentials are not available",
        )
    site_password = plain_password or decrypt_site_password(current_user.encrypted_site_password)
    return ClientSiteCredentialsRead(site_login=current_user.site_login, site_password=site_password)


@router.get("/cities", response_model=list[ClientCityResponse])
def list_client_cities(
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> list[City]:
    _ = current_user
    result = db.execute(
        select(City)
        .where(City.is_active.is_(True))
        .order_by(City.sort_order.asc(), City.name.asc(), City.id.asc())
    )
    return list(result.scalars().all())


@router.patch("/me", response_model=ClientProfileRead)
def update_client_me(
    payload: ClientProfileUpdate,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> ClientProfileRead:
    profile = _get_or_create_client_profile(db, current_user.id)
    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data and "full_name" not in update_data:
        update_data["full_name"] = update_data["name"]

    if "full_name" in update_data:
        profile.full_name = _normalize_required_name(update_data["full_name"])

    city_text = _normalize_optional_text(update_data.get("custom_city"))
    if city_text is None:
        city_text = _normalize_optional_text(update_data.get("city"))

    resolved_city_id = _resolve_city_for_profile_update(
        db,
        update_data.get("selected_city_id" if "selected_city_id" in update_data else "city_id"),
        update_data.get("city_slug"),
        keep_current=profile.selected_city_id,
    )
    if any(field in update_data for field in ("selected_city_id", "city_id", "city_slug")):
        profile.selected_city_id = resolved_city_id

    if city_text is not None:
        resolved_text_city_id = _resolve_city_id_by_name(db, city_text)
        profile.custom_city = city_text
        if resolved_text_city_id is not None:
            profile.selected_city_id = resolved_text_city_id
    elif any(field in update_data for field in ("city", "custom_city")):
        profile.custom_city = None

    if "phone" in update_data:
        normalized_phone = _normalize_phone(update_data["phone"])
        _ensure_unique_user_phone(db, normalized_phone, current_user.id)
        current_user.phone = normalized_phone

    if "contact_email" in update_data:
        profile.contact_email = _normalize_email(update_data["contact_email"])
    elif "email" in update_data:
        normalized_email = _normalize_email(update_data["email"])
        _ensure_unique_user_email(db, normalized_email, current_user.id)
        profile.contact_email = normalized_email
        current_user.email = normalized_email

    db.commit()
    db.refresh(profile)
    return _client_profile_to_read(db, profile, current_user)


@router.post("/me/vk-link-codes", response_model=VkLinkCodeRead)
def create_client_vk_link_code(
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> VkLinkCodeRead:
    profile = _get_or_create_client_profile(db, current_user.id)
    now = datetime.now(timezone.utc)
    active_codes = db.execute(
        select(VkLinkCode).where(
            VkLinkCode.client_id == profile.id,
            VkLinkCode.status == VkLinkCodeStatus.ACTIVE.value,
            VkLinkCode.expires_at > now,
        )
    ).scalars().all()
    for active_code in active_codes:
        active_code.status = VkLinkCodeStatus.CANCELLED.value

    link_code = VkLinkCode(
        client_id=profile.id,
        code=_generate_vk_link_code(db),
        status=VkLinkCodeStatus.ACTIVE.value,
        expires_at=now + timedelta(seconds=VK_LINK_CODE_TTL_SECONDS),
    )
    db.add(link_code)
    db.commit()
    db.refresh(link_code)
    return _vk_link_code_to_read(link_code)


@router.get("/me/activity", response_model=ActivityFeedRead)
def read_client_activity(
    limit: int = 30,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> ActivityFeedRead:
    profile = _get_or_create_client_profile(db, current_user.id)
    return build_client_activity_feed(db, profile.id, limit=limit)


@router.get("/me/subscription", response_model=SubscriptionRead)
def read_client_subscription(
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> SubscriptionRead:
    profile = _get_or_create_client_profile(db, current_user.id)
    now = datetime.now(timezone.utc)
    subscription = _get_current_active_subscription(db, profile.id, now)
    return _subscription_to_read(subscription, profile, now)


@router.post("/me/trial-subscription", response_model=SubscriptionRead)
def activate_client_trial_subscription(
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> SubscriptionRead:
    profile = _get_or_create_client_profile(db, current_user.id)
    now = datetime.now(timezone.utc)

    if profile.trial_subscription_used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trial subscription already activated",
        )

    trial_ends_at = now + timedelta(days=TRIAL_SUBSCRIPTION_DAYS)
    current_subscription = _get_current_active_subscription(db, profile.id, now)
    profile.trial_subscription_used_at = now

    if current_subscription is None or as_aware_utc(current_subscription.ends_at) < trial_ends_at:
        db.add(
            Subscription(
                client_id=profile.id,
                status=SubscriptionStatus.active.value,
                starts_at=now,
                ends_at=trial_ends_at,
                source=TRIAL_SOURCE,
            )
        )

    db.flush()
    active_giveaway = get_active_giveaway(db, now)
    base_number_created = False
    if active_giveaway is not None:
        had_base_number = db.execute(
            select(GiveawayNumber.id).where(
                GiveawayNumber.giveaway_id == active_giveaway.id,
                GiveawayNumber.client_id == profile.id,
                GiveawayNumber.source == "subscription",
            )
        ).scalar_one_or_none() is not None
        ensure_user_numbers(db, active_giveaway.id, profile.id)
        base_number_created = not had_base_number and db.execute(
            select(GiveawayNumber.id).where(
                GiveawayNumber.giveaway_id == active_giveaway.id,
                GiveawayNumber.client_id == profile.id,
                GiveawayNumber.source == "subscription",
            )
        ).scalar_one_or_none() is not None
    logger.info(
        "client_trial_activated",
        extra={
            "action": "client_trial_activated",
            "provider_user_id": profile.telegram_user_id or profile.vk_user_id,
            "client_id": profile.id,
            "trial_activated": True,
            "active_giveaway_id": active_giveaway.id if active_giveaway is not None else None,
            "base_giveaway_entry_created": base_number_created,
            "base_giveaway_entry_skip_reason": None if active_giveaway is not None else "no_active_giveaway",
        },
    )

    db.commit()
    db.refresh(profile)
    subscription = _get_current_active_subscription(db, profile.id, now)
    return _subscription_to_read(subscription, profile, now)


@router.post("/me/payment-requests", response_model=PaymentRequestRead, status_code=status.HTTP_201_CREATED)
def create_client_payment_request(
    payload: PaymentRequestCreate | None = None,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> PaymentRequestRead:
    profile = _get_current_client_profile_or_404(db, current_user)
    payload = payload or PaymentRequestCreate()
    payment_request = PaymentRequest(
        client_id=profile.id,
        amount=payload.amount if payload.amount is not None else Decimal("349.00"),
        status=PaymentRequestStatus.pending.value,
        source=_normalize_optional_text(payload.source) or "web",
        comment=_normalize_optional_text(payload.comment),
    )
    db.add(payment_request)
    db.commit()
    payment_request = _get_owned_payment_request_or_404(db, profile.id, payment_request.id)
    return PaymentRequestRead.model_validate(payment_request)


@router.get("/me/payment-requests", response_model=list[PaymentRequestRead])
def list_client_payment_requests(
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> list[PaymentRequestRead]:
    profile = _get_current_client_profile_or_404(db, current_user)
    payment_requests = db.execute(
        select(PaymentRequest)
        .options(selectinload(PaymentRequest.receipts))
        .where(PaymentRequest.client_id == profile.id)
        .order_by(PaymentRequest.created_at.desc(), PaymentRequest.id.desc())
    ).scalars().all()
    return [PaymentRequestRead.model_validate(payment_request) for payment_request in payment_requests]


@router.get("/me/payment-requests/{payment_request_id}", response_model=PaymentRequestRead)
def read_client_payment_request(
    payment_request_id: int,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> PaymentRequestRead:
    profile = _get_current_client_profile_or_404(db, current_user)
    payment_request = _get_owned_payment_request_or_404(db, profile.id, payment_request_id)
    return PaymentRequestRead.model_validate(payment_request)


@router.post("/me/payment-requests/{payment_request_id}/mark-paid", response_model=PaymentRequestRead)
def mark_client_payment_request_paid(
    payment_request_id: int,
    payload: PaymentRequestMarkPaid | None = None,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> PaymentRequestRead:
    profile = _get_current_client_profile_or_404(db, current_user)
    payment_request = _get_owned_payment_request_or_404(db, profile.id, payment_request_id)

    if payment_request.status == PaymentRequestStatus.pending.value:
        payment_request.status = PaymentRequestStatus.paid.value
        payment_request.updated_at = datetime.now(timezone.utc)
    elif payment_request.status == PaymentRequestStatus.paid.value:
        pass
    elif payment_request.status in {PaymentRequestStatus.approved.value, PaymentRequestStatus.rejected.value}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment request cannot be marked as paid",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported payment request status",
        )

    _append_payment_request_comment(payment_request, payload.comment if payload is not None else None)
    db.commit()
    payment_request = _get_owned_payment_request_or_404(db, profile.id, payment_request.id)
    return PaymentRequestRead.model_validate(payment_request)


@router.post(
    "/me/payment-requests/{payment_request_id}/receipts",
    response_model=PaymentReceiptRead,
    status_code=status.HTTP_201_CREATED,
)
def create_client_payment_receipt(
    payment_request_id: int,
    payload: PaymentReceiptCreate,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> PaymentReceiptRead:
    profile = _get_current_client_profile_or_404(db, current_user)
    _get_owned_payment_request_or_404(db, profile.id, payment_request_id)
    receipt = PaymentReceipt(
        payment_request_id=payment_request_id,
        file_url=payload.file_url,
        uploaded_via=_normalize_optional_text(payload.uploaded_via) or "web",
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return PaymentReceiptRead.model_validate(receipt)


@router.get("/catalog/partners", response_model=list[ClientPartnerCatalogItem])
def list_client_catalog_partners(
    city_id: int | None = None,
    city_slug: str | None = None,
    category_slug: str | None = None,
    q: str | None = None,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> list[ClientPartnerCatalogItem]:
    if current_user is not None and current_user.role == "client":
        profile = _get_or_create_client_profile(db, current_user.id)
        resolved_city_id = _resolve_catalog_city_id(db, profile, city_id, city_slug)
    else:
        resolved_city_id = _resolve_public_catalog_city_id(db, city_id, city_slug)
    normalized_category_slug = _normalize_optional_text(category_slug)
    normalized_query = _normalize_optional_text(q)

    statement = (
        select(Partner, City.name.label("city_name"))
        .join(City, Partner.city_id == City.id)
        .options(selectinload(Partner.categories))
        .where(Partner.is_active.is_(True))
        .order_by(Partner.sort_order.asc(), Partner.id.asc())
    )
    if resolved_city_id is not None:
        statement = statement.where(Partner.city_id == resolved_city_id)
    if normalized_category_slug is not None:
        statement = statement.where(
            Partner.categories.any(Category.slug == normalized_category_slug) | (Partner.category_slug == normalized_category_slug)
        )
    if normalized_query is not None:
        search = f"%{normalized_query}%"
        statement = statement.where(Partner.name.ilike(search))

    rows = db.execute(statement).all()
    partner_ids = [partner.id for partner, _city_name in rows]
    photos_by_partner = _active_photos_by_partner(db, partner_ids)
    return [
        _partner_to_catalog_item(
            partner,
            city_name,
            photos_by_partner.get(partner.id, []),
        )
        for partner, city_name in rows
    ]


@router.post("/partners/{partner_id}/verify", response_model=ClientVerificationRead)
def create_client_partner_verification(
    partner_id: int,
    payload: ClientCreateVerificationRequest | None = None,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> ClientVerificationRead:
    profile = _get_or_create_client_profile(db, current_user.id)
    partner, _city_name = _get_active_partner_row_or_404(db, partner_id)
    request_payload = payload or ClientCreateVerificationRequest()
    offer = _resolve_partner_offer_for_verification(db, partner.id, request_payload.offer_id, request_payload.privilege_id)

    now = datetime.now(timezone.utc)
    if not _has_active_subscription(db, profile.id, now):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ACTIVE_SUBSCRIPTION_REQUIRED_DETAIL,
        )

    normalize_expired_verifications(db, now=now, client_id=profile.id, partner_id=partner.id)

    session = PrivilegeVerificationSession(
        client_id=profile.id,
        partner_id=partner.id,
        offer_id=offer.id if offer is not None else None,
        code=_generate_verification_code(),
        token=_generate_unique_privilege_session_token(db),
        status=PrivilegeVerificationStatus.active.value,
        source=_normalize_optional_text(request_payload.source) or "web",
        expires_at=now + timedelta(seconds=PRIVILEGE_VERIFICATION_TTL_SECONDS),
        created_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _client_verification_to_read(session, partner.name, offer)


@router.get("/me/verifications", response_model=list[ClientVerificationRead])
def list_client_verifications(
    status: str | None = None,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> list[ClientVerificationRead]:
    profile = _get_or_create_client_profile(db, current_user.id)
    now = datetime.now(timezone.utc)
    normalize_expired_verifications(db, now=now, client_id=profile.id)
    statement = (
        select(PrivilegeVerificationSession, Partner.name.label("partner_name"), PartnerOffer)
        .join(Partner, PrivilegeVerificationSession.partner_id == Partner.id)
        .outerjoin(PartnerOffer, PrivilegeVerificationSession.offer_id == PartnerOffer.id)
        .where(PrivilegeVerificationSession.client_id == profile.id)
        .order_by(PrivilegeVerificationSession.created_at.desc(), PrivilegeVerificationSession.id.desc())
    )
    statement = apply_verification_status_filter(statement, status, now=now)

    return [
        _client_verification_to_read(session, partner_name, offer)
        for session, partner_name, offer in db.execute(statement).all()
    ]


@router.get("/me/savings", response_model=ClientSavingsRead)
def read_client_savings(
    from_date: date | None = None,
    to_date: date | None = None,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> ClientSavingsRead:
    profile = _get_or_create_client_profile(db, current_user.id)
    statement = (
        select(PrivilegeVerificationSession, Partner.name.label("partner_name"), PartnerOffer.title.label("offer_title"))
        .join(Partner, PrivilegeVerificationSession.partner_id == Partner.id)
        .outerjoin(PartnerOffer, PrivilegeVerificationSession.offer_id == PartnerOffer.id)
        .where(
            PrivilegeVerificationSession.client_id == profile.id,
            PrivilegeVerificationSession.status == PrivilegeVerificationStatus.confirmed.value,
        )
    )
    if from_date is not None:
        statement = statement.where(PrivilegeVerificationSession.confirmed_at >= datetime.combine(from_date, time.min, tzinfo=timezone.utc))
    if to_date is not None:
        statement = statement.where(PrivilegeVerificationSession.confirmed_at <= datetime.combine(to_date, time.max, tzinfo=timezone.utc))
    statement = statement.order_by(PrivilegeVerificationSession.confirmed_at.desc(), PrivilegeVerificationSession.id.desc())
    items: list[ClientSavingsItemRead] = []
    total = Decimal("0.00")
    for session, partner_name, offer_title in db.execute(statement).all():
        base_price = session.saving_base_price
        final_price = session.saving_final_price
        discount_percent = session.saving_discount_percent
        saving_amount = session.saving_amount
        used_at = session.saving_used_at or session.confirmed_at
        if saving_amount is None:
            base_price, final_price, discount_percent, saving_amount = _compute_saving_from_offer(session.offer)
        total += saving_amount
        items.append(ClientSavingsItemRead(
            id=session.id, used_at=used_at, partner_id=session.partner_id, partner_name=session.saving_partner_name or partner_name,
            offer_id=session.offer_id, offer_title=session.saving_offer_title or offer_title, base_price=base_price,
            final_price=final_price, discount_percent=discount_percent, saving_amount=saving_amount,
        ))
    return ClientSavingsRead(
        total_saving_amount=total,
        period=ClientSavingsPeriodRead(from_date=from_date.isoformat() if from_date else None, to_date=to_date.isoformat() if to_date else None),
        items=items,
    )


@router.get("/partners/{partner_id}", response_model=ClientPartnerCatalogItem)
def read_client_partner(
    partner_id: int,
    db: Session = Depends(get_db),
) -> ClientPartnerCatalogItem:
    partner, city_name = _get_active_partner_row_or_404(db, partner_id)
    return _partner_to_catalog_item(
        partner,
        city_name,
        _active_photos_by_partner(db, [partner.id]).get(partner.id, []),
    )


@router.get("/partners/{partner_id}/offers", response_model=list[ClientPartnerOfferRead])
def list_client_partner_offers(
    partner_id: int,
    db: Session = Depends(get_db),
) -> list[ClientPartnerOfferRead]:
    _get_active_partner_row_or_404(db, partner_id)
    offers = db.execute(
        select(PartnerOffer)
        .where(PartnerOffer.partner_id == partner_id, PartnerOffer.is_active.is_(True))
        .order_by(PartnerOffer.sort_order.asc(), PartnerOffer.id.asc())
    ).scalars().all()
    photos_by_offer = _active_photos_by_offer(db, [offer.id for offer in offers])
    return [_partner_offer_to_read(offer, photos_by_offer.get(offer.id, [])) for offer in offers]


def _get_current_client_profile_or_404(db: Session, current_user: User) -> ClientProfile:
    profile = db.execute(select(ClientProfile).where(ClientProfile.user_id == current_user.id)).scalar_one_or_none()
    if profile is not None:
        return profile
    return _get_or_create_client_profile(db, current_user.id)



def _normalize_linking_identifier(identifier: str) -> tuple[str, str]:
    value = (identifier or "").strip()
    if not value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="identifier_required")
    if "@" in value:
        normalized = value.lower()
        if "." not in normalized.split("@")[-1]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_email")
        return "email", normalized
    normalized_phone = "".join(ch for ch in value if ch.isdigit() or ch == "+")
    if len(normalized_phone.replace("+", "")) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_phone")
    return "phone", normalized_phone


def _linking_hash(value: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _generate_linking_code() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(6))


def _mask_linking_identifier(identifier_type: str, value: str) -> str:
    if identifier_type == "email":
        local, _, domain = value.partition("@")
        masked_local = (local[:1] + "***") if local else "***"
        return f"{masked_local}@{domain}"
    digits = "".join(ch for ch in value if ch.isdigit())
    suffix = digits[-4:] if len(digits) >= 4 else digits
    prefix = "+" if value.startswith("+") else ""
    return f"{prefix}***{suffix}" if suffix else "***"


def _find_linking_candidates(
    db: Session,
    current_profile_id: int,
    identifier_type: str,
    normalized_identifier: str,
) -> list[ClientProfile]:
    if identifier_type == "email":
        statement = (
            select(ClientProfile)
            .join(User, User.id == ClientProfile.user_id)
            .where(
                ClientProfile.id != current_profile_id,
                or_(
                    func.lower(User.email) == normalized_identifier,
                    func.lower(ClientProfile.contact_email) == normalized_identifier,
                ),
            )
        )
    else:
        statement = (
            select(ClientProfile)
            .join(User, User.id == ClientProfile.user_id)
            .where(
                ClientProfile.id != current_profile_id,
                User.phone == normalized_identifier,
            )
        )
    profiles = list(db.execute(statement).scalars().all())
    preferred = [profile for profile in profiles if profile.vk_user_id or profile.user.site_login or profile.user.email or profile.user.phone]
    return preferred or profiles


def _temporary_profile_has_activity(db: Session, profile: ClientProfile) -> bool:
    if profile.trial_subscription_used_at is not None:
        return True
    has_subscription = db.execute(select(Subscription.id).where(Subscription.client_id == profile.id).limit(1)).scalar_one_or_none()
    if has_subscription is not None:
        return True
    has_payment_request = db.execute(select(PaymentRequest.id).where(PaymentRequest.client_id == profile.id).limit(1)).scalar_one_or_none()
    if has_payment_request is not None:
        return True
    has_verification = db.execute(select(PrivilegeVerificationSession.id).where(PrivilegeVerificationSession.client_id == profile.id).limit(1)).scalar_one_or_none()
    return has_verification is not None

def _get_owned_payment_request_or_404(db: Session, client_id: int, payment_request_id: int) -> PaymentRequest:
    payment_request = db.execute(
        select(PaymentRequest)
        .options(selectinload(PaymentRequest.receipts))
        .where(PaymentRequest.id == payment_request_id, PaymentRequest.client_id == client_id)
    ).scalar_one_or_none()
    if payment_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment request not found")
    return payment_request


def _append_payment_request_comment(payment_request: PaymentRequest, comment: str | None) -> None:
    normalized_comment = _normalize_optional_text(comment)
    if normalized_comment is None:
        return
    if payment_request.comment:
        if payment_request.comment.strip() == normalized_comment:
            return
        payment_request.comment = f"{payment_request.comment}\n\nClient mark-paid comment: {normalized_comment}"
    else:
        payment_request.comment = normalized_comment
    payment_request.updated_at = datetime.now(timezone.utc)


def _get_or_create_client_profile(db: Session, user_id: int) -> ClientProfile:
    profile = db.execute(select(ClientProfile).where(ClientProfile.user_id == user_id)).scalar_one_or_none()
    if profile is not None:
        return profile

    profile = ClientProfile(user_id=user_id, is_active=True, source="web")
    db.add(profile)
    db.flush()
    ensure_referral_code(db, profile)
    db.commit()
    db.refresh(profile)
    return profile


def _compute_saving_from_offer(offer: PartnerOffer | None) -> tuple[Decimal | None, Decimal | None, Decimal | None, Decimal]:
    snapshot = calculate_offer_saving_snapshot(offer)
    return snapshot.regular_price, snapshot.club_price, snapshot.discount_percent, snapshot.saving_amount


def _client_profile_to_read(db: Session, profile: ClientProfile, user: User) -> ClientProfileRead:
    selected_city_name = None
    if profile.selected_city_id is not None:
        selected_city_name = db.execute(select(City.name).where(City.id == profile.selected_city_id)).scalar_one_or_none()
    city_name = profile.custom_city or selected_city_name
    ensure_referral_code(db, profile)
    now = datetime.now(timezone.utc)
    active_subscription = _get_current_active_subscription(db, profile.id, now)
    return ClientProfileRead.model_validate(
        {
            "id": profile.id,
            "user_id": profile.user_id,
            "email": user.email,
            "phone": user.phone,
            "contact_email": profile.contact_email,
            "full_name": profile.full_name,
            "selected_city_id": profile.selected_city_id,
            "selected_city_name": selected_city_name,
            "city": city_name,
            "custom_city": profile.custom_city,
            "city_name": city_name,
            "vk_user_id": profile.vk_user_id,
            "telegram_user_id": profile.telegram_user_id,
            "telegram_username": profile.telegram_username,
            "telegram_first_name": profile.telegram_first_name,
            "telegram_last_name": profile.telegram_last_name,
            "trial_used": profile.trial_subscription_used_at is not None,
            "trial_available": profile.trial_subscription_used_at is None and active_subscription is None,
            "referral_code": profile.referral_code,
            "referral_link": referral_link(profile.referral_code),
            "site_login": user.site_login,
            "site_password_masked": "*****" if user.encrypted_site_password else None,
            "site_password_available": bool(user.encrypted_site_password),
            "source": profile.source,
            "is_active": profile.is_active,
        }
    )


def _ensure_unique_user_phone(db: Session, phone: str | None, current_user_id: int) -> None:
    if phone is None:
        return
    existing_id = db.execute(select(User.id).where(User.phone == phone, User.id != current_user_id)).scalar_one_or_none()
    if existing_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone is already used")


def _ensure_unique_user_email(db: Session, email: str | None, current_user_id: int) -> None:
    if email is None:
        return
    existing_id = db.execute(
        select(User.id).where(func.lower(User.email) == email.lower(), User.id != current_user_id)
    ).scalar_one_or_none()
    if existing_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already used")


def _generate_vk_link_code(db: Session) -> str:
    for _ in range(20):
        code = "".join(secrets.choice(VK_LINK_CODE_ALPHABET) for _ in range(VK_LINK_CODE_LENGTH))
        exists = db.execute(select(VkLinkCode.id).where(VkLinkCode.code == code)).scalar_one_or_none()
        if exists is None:
            return code
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Could not generate VK link code",
    )


def _vk_link_code_to_read(link_code: VkLinkCode) -> VkLinkCodeRead:
    expires_at = as_aware_utc(link_code.expires_at)
    ttl_seconds = max(0, int((expires_at - datetime.now(timezone.utc)).total_seconds()))
    return VkLinkCodeRead(
        code=link_code.code,
        status=link_code.status,
        expires_at=expires_at,
        ttl_seconds=ttl_seconds,
    )


def _get_current_active_subscription(db: Session, client_id: int, now: datetime) -> Subscription | None:
    return db.execute(
        select(Subscription)
        .where(
            Subscription.client_id == client_id,
            Subscription.status == SubscriptionStatus.active.value,
            Subscription.starts_at <= now,
            Subscription.ends_at > now,
        )
        .order_by(Subscription.ends_at.desc(), Subscription.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _subscription_source(subscription: Subscription | None) -> str | None:
    if subscription is None:
        return None
    if subscription.source:
        return subscription.source
    if subscription.source_payment_request_id is not None:
        return PAID_SOURCE
    return None


def _is_trial_promo_available(now: datetime) -> bool:
    _ = now
    return True


def _subscription_to_read(
    subscription: Subscription | None,
    profile: ClientProfile,
    now: datetime,
) -> SubscriptionRead:
    trial_used = profile.trial_subscription_used_at is not None
    trial_available = not trial_used and subscription is None and _is_trial_promo_available(now)
    if subscription is None:
        return SubscriptionRead(
            status="inactive",
            is_active=False,
            subscription_active=False,
            expires_at=None,
            end_date=None,
            subscription_until=None,
            trial_available=trial_available,
            trial_used=trial_used,
            amount=Decimal("349.00"),
        )

    subscription_source = _subscription_source(subscription)
    return SubscriptionRead(
        id=subscription.id,
        client_id=subscription.client_id,
        status=SubscriptionStatus.active.value,
        starts_at=subscription.starts_at,
        ends_at=subscription.ends_at,
        source_payment_request_id=subscription.source_payment_request_id,
        source=subscription_source,
        type=subscription_source,
        is_active=True,
        subscription_active=True,
        expires_at=subscription.ends_at,
        end_date=subscription.ends_at,
        subscription_until=subscription.ends_at,
        trial_available=trial_available,
        trial_used=trial_used,
        amount=Decimal("349.00"),
    )


def _has_active_subscription(db: Session, client_id: int, now: datetime) -> bool:
    subscription = db.execute(
        select(Subscription.id)
        .where(
            Subscription.client_id == client_id,
            Subscription.status == SubscriptionStatus.active.value,
            Subscription.starts_at <= now,
            Subscription.ends_at > now,
        )
        .limit(1)
    ).scalar_one_or_none()
    return subscription is not None


def _get_active_city_or_404(db: Session, city_id: int) -> City:
    city = db.execute(select(City).where(City.id == city_id, City.is_active.is_(True))).scalar_one_or_none()
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CITY_NOT_FOUND_DETAIL)
    return city



def _resolve_public_catalog_city_id(
    db: Session,
    city_id: int | None,
    city_slug: str | None,
) -> int | None:
    if city_id is not None:
        return city_id

    normalized_city_slug = _normalize_optional_text(city_slug)
    if normalized_city_slug is not None:
        city = db.execute(select(City).where(City.slug == normalized_city_slug, City.is_active.is_(True))).scalar_one_or_none()
        if city is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CITY_NOT_FOUND_DETAIL)
        return city.id

    return None

def _resolve_catalog_city_id(
    db: Session,
    profile: ClientProfile,
    city_id: int | None,
    city_slug: str | None,
) -> int | None:
    if city_id is not None:
        return city_id

    normalized_city_slug = _normalize_optional_text(city_slug)
    if normalized_city_slug is not None:
        city = db.execute(
            select(City).where(City.slug == normalized_city_slug, City.is_active.is_(True))
        ).scalar_one_or_none()
        if city is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CITY_NOT_FOUND_DETAIL)
        return city.id

    return profile.selected_city_id


def _get_active_partner_row_or_404(
    db: Session,
    partner_id: int,
) -> tuple[Partner, str | None]:
    row = db.execute(
        select(Partner, City.name.label("city_name"))
        .join(City, Partner.city_id == City.id)
        .options(selectinload(Partner.categories))
        .where(Partner.id == partner_id, Partner.is_active.is_(True))
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PARTNER_NOT_FOUND_DETAIL)
    partner, city_name = row
    return partner, city_name


def _get_active_partner_offer_or_404(db: Session, partner_id: int, offer_id: int) -> PartnerOffer:
    offer = db.execute(
        select(PartnerOffer).where(
            PartnerOffer.id == offer_id,
            PartnerOffer.partner_id == partner_id,
            PartnerOffer.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=OFFER_NOT_FOUND_DETAIL)
    return offer


def _resolve_partner_offer_for_verification(
    db: Session,
    partner_id: int,
    offer_id: int | None,
    privilege_id: int | None,
) -> PartnerOffer | None:
    selected_offer_id = _selected_offer_id(offer_id, privilege_id)
    if selected_offer_id is not None:
        return _get_active_partner_offer_or_404(db, partner_id, selected_offer_id)
    return None


def _selected_offer_id(offer_id: int | None, privilege_id: int | None) -> int | None:
    if offer_id is not None and privilege_id is not None and offer_id != privilege_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=OFFER_ID_CONFLICT_DETAIL)
    return offer_id if offer_id is not None else privilege_id


def _generate_verification_code(length: int = 6) -> str:
    return "".join(secrets.choice(VERIFICATION_CODE_ALPHABET) for _ in range(length))


def _generate_unique_privilege_session_token(db: Session) -> str:
    for _ in range(20):
        token = secrets.token_urlsafe(32)
        exists = db.execute(
            select(PrivilegeVerificationSession.id).where(PrivilegeVerificationSession.token == token)
        ).scalar_one_or_none()
        if exists is None:
            return token
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Could not generate privilege session token",
    )


def _privilege_qr_payload(token: str | None) -> str | None:
    if not token:
        return None
    return f"{PRIVILEGE_QR_PAYLOAD_PREFIX}{token}"


def _client_verification_to_read(
    session: PrivilegeVerificationSession,
    partner_name: str | None,
    offer: PartnerOffer | str | None,
) -> ClientVerificationRead:
    offer_title = offer.title if isinstance(offer, PartnerOffer) else offer
    base_price, final_price, discount_percent, saving_amount = _client_verification_prices(session, offer)
    if session.status == PrivilegeVerificationStatus.confirmed.value:
        partner_name = session.saving_partner_name or partner_name
        offer_title = session.saving_offer_title or offer_title

    return ClientVerificationRead.model_validate(
        {
            "id": session.id,
            "session_id": session.id,
            "client_id": session.client_id,
            "partner_id": session.partner_id,
            "partner_name": partner_name,
            "offer_id": session.offer_id,
            "offer_title": offer_title,
            "code": session.code,
            "display_code": session.code,
            "token": session.token,
            "qr_payload": _privilege_qr_payload(session.token),
            "status": session.status,
            "source": session.source,
            "expires_at": session.expires_at,
            "confirmed_at": session.confirmed_at,
            "created_at": session.created_at,
            "ttl_seconds": ttl_seconds(session.expires_at),
            "regular_price": base_price,
            "club_price": final_price,
            "base_price": base_price,
            "final_price": final_price,
            "discount_percent": discount_percent,
            "saving_amount": saving_amount,
            "subscription_required": False,
        }
    )


def _client_verification_prices(
    session: PrivilegeVerificationSession,
    offer: PartnerOffer | str | None,
) -> tuple[Decimal | None, Decimal | None, Decimal | None, Decimal | None]:
    if session.status == PrivilegeVerificationStatus.confirmed.value:
        base_price = session.saving_base_price
        final_price = session.saving_final_price
        discount_percent = session.saving_discount_percent
        saving_amount = session.saving_amount
        if saving_amount is not None:
            return base_price, final_price, discount_percent, saving_amount

    if isinstance(offer, PartnerOffer):
        base_price, final_price, discount_percent, saving_amount = _compute_saving_from_offer(offer)
        return base_price, final_price, discount_percent, saving_amount

    if session.status == PrivilegeVerificationStatus.confirmed.value and session.saving_amount is not None:
        return session.saving_base_price, session.saving_final_price, session.saving_discount_percent, session.saving_amount

    return None, None, None, Decimal("0.00") if session.offer_id is None else None


def _active_photos_by_partner(db: Session, partner_ids: list[int]) -> dict[int, list[ClientPartnerPhotoRead]]:
    if not partner_ids:
        return {}
    photos = db.execute(
        select(PartnerPhoto)
        .where(PartnerPhoto.partner_id.in_(partner_ids), PartnerPhoto.is_active.is_(True))
        .order_by(PartnerPhoto.partner_id.asc(), PartnerPhoto.sort_order.asc(), PartnerPhoto.id.asc())
    ).scalars().all()
    result: dict[int, list[ClientPartnerPhotoRead]] = {}
    for photo in photos:
        result.setdefault(photo.partner_id, []).append(
            ClientPartnerPhotoRead.model_validate(
                {
                    "id": photo.id,
                    "url": photo.url,
                    "alt_text": photo.alt_text,
                    "sort_order": photo.sort_order,
                    "created_at": photo.created_at,
                }
            )
        )
    return result


def _partner_to_catalog_item(
    partner: Partner,
    city_name: str | None,
    photos: list[ClientPartnerPhotoRead] | None = None,
) -> ClientPartnerCatalogItem:
    active_categories = sorted(
        [category for category in partner.categories if category.is_active],
        key=lambda c: (c.sort_order, c.name.lower(), c.id),
    )
    first = active_categories[0] if active_categories else None
    photo_url = photos[0].url if photos else None
    image_url = photo_url or partner.cover_url or partner.logo_url
    return ClientPartnerCatalogItem.model_validate(
        {
            "id": partner.id,
            "city_id": partner.city_id,
            "city_name": _humanize_display_text(city_name),
            "category_id": first.id if first is not None else None,
            "category_name": _display_category_name(
                first.name if first is not None else None,
                first.slug if first is not None else partner.category_slug,
            ),
            "category_slug": first.slug if first is not None else partner.category_slug,
            "category": (
                ClientPartnerCategoryRead(
                    id=first.id,
                    name=_display_category_name(first.name, first.slug),
                    slug=first.slug,
                )
                if first is not None
                else None
            ),
            "categories": [
                ClientPartnerCategoryRead(id=c.id, name=_display_category_name(c.name, c.slug), slug=c.slug)
                for c in active_categories
            ],
            "category_ids": [c.id for c in active_categories],
            "category_slugs": [c.slug for c in active_categories],
            "name": partner.name,
            "description": partner.description,
            "address": partner.address,
            "phone": partner.phone,
            "website_url": partner.website_url,
            "social_url": partner.social_url,
            "instagram_url": partner.instagram_url,
            "vk_url": partner.vk_url,
            "telegram_url": partner.telegram_url,
            "whatsapp_url": partner.whatsapp_url,
            "map_url": partner.map_url,
            "working_hours": partner.working_hours,
            "logo_url": partner.logo_url,
            "cover_url": partner.cover_url,
            "image_url": image_url,
            "photo_url": photo_url,
            "is_verified": partner.is_verified,
            "photos": photos or [],
        }
    )


def _active_photos_by_offer(db: Session, offer_ids: list[int]) -> dict[int, list[dict[str, object]]]:
    if not offer_ids:
        return {}
    photos = db.execute(
        select(OfferPhoto)
        .where(OfferPhoto.offer_id.in_(offer_ids), OfferPhoto.is_active.is_(True))
        .order_by(OfferPhoto.offer_id.asc(), OfferPhoto.sort_order.asc(), OfferPhoto.id.asc())
    ).scalars().all()
    result: dict[int, list[dict[str, object]]] = {}
    for photo in photos:
        result.setdefault(photo.offer_id, []).append(
            {"id": photo.id, "url": photo.url, "alt_text": photo.alt_text, "sort_order": photo.sort_order}
        )
    return result


def _humanize_display_text(value: str | None) -> str | None:
    normalized = _normalize_optional_text(value)
    if normalized is None:
        return None
    return normalized[0].upper() + normalized[1:] if normalized else normalized


def _display_category_name(name: str | None, slug: str | None) -> str | None:
    normalized_slug = _normalize_optional_text(slug)
    if normalized_slug is not None and normalized_slug in CATEGORY_DISPLAY_BY_SLUG:
        return CATEGORY_DISPLAY_BY_SLUG[normalized_slug]
    return _humanize_display_text(name)


def _partner_offer_to_read(offer: PartnerOffer, photos: list[dict[str, object]] | None = None) -> ClientPartnerOfferRead:
    photos_payload = photos or []
    photo_url = str(photos_payload[0]["url"]) if photos_payload else None
    return ClientPartnerOfferRead.model_validate(
        {
            "id": offer.id,
            "partner_id": offer.partner_id,
            "title": offer.title,
            "description": offer.description,
            "benefit_text": offer.benefit_text,
            "conditions": offer.conditions,
            "base_price": offer.base_price,
            "discount_percent": offer.discount_percent,
            "image_url": offer.image_url,
            "photo_url": photo_url,
            "photos": photos_payload,
            "sort_order": offer.sort_order,
        }
    )




def _resolve_city_id_by_name(db: Session, city_name: str) -> int | None:
    normalized_city_name = _normalize_optional_text(city_name)
    if normalized_city_name is None:
        return None
    return db.execute(
        select(City.id).where(City.name.ilike(normalized_city_name), City.is_active.is_(True)).limit(1)
    ).scalar_one_or_none()

def _resolve_city_for_profile_update(
    db: Session,
    city_id: int | None,
    city_slug: str | None,
    keep_current: int | None,
) -> int | None:
    if city_id is not None:
        _get_active_city_or_404(db, city_id)
        return city_id
    normalized_slug = _normalize_optional_text(city_slug)
    if normalized_slug is not None:
        city = db.execute(select(City).where(City.slug == normalized_slug, City.is_active.is_(True))).scalar_one_or_none()
        if city is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CITY_NOT_FOUND_DETAIL)
        return city.id
    if city_slug is not None:
        return None
    return keep_current


def _normalize_email(value: str | None) -> str | None:
    normalized = _normalize_optional_text(value)
    if normalized is None:
        return None
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")
    return normalized.lower()


def _normalize_phone(value: str | None) -> str | None:
    normalized = _normalize_optional_text(value)
    if normalized is None:
        return None
    if normalized.startswith("8") and len(normalized) == 11 and normalized[1:].isdigit():
        normalized = "+7" + normalized[1:]
    if len(normalized) > 64:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone is too long")
    return normalized


def _normalize_required_name(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must not be empty")
    if len(normalized) > 255:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name is too long")
    return normalized

def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
