from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_bot_api_token
from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_password_setup_token,
    generate_temporary_password,
    hash_password,
    hash_password_setup_token,
)
from app.db.session import get_db
from app.models.city import City
from app.models.client import (
    ClientPasswordSetupToken,
    ClientProfile,
    VkLinkCode,
    VkLinkCodeStatus,
)
from app.models.user import User, UserRole
from app.schemas.auth import UnifiedUserRead
from app.schemas.vk import (
    VkExchangeLinkCodeRequest,
    VkExchangeTokenResponse,
    VkOnboardClientProfileRead,
    VkOnboardClientRequest,
    VkOnboardClientResponse,
    VkOnboardClientUserRead,
    VkTokenRequest,
)

router = APIRouter(prefix="/bot/vk", tags=["bot-vk"])

PASSWORD_SETUP_PURPOSE = "vk_onboarding_password_setup"
PASSWORD_SETUP_TTL_SECONDS = 60 * 60


@router.post("/exchange-link-code", response_model=VkExchangeTokenResponse)
def exchange_vk_link_code(
    payload: VkExchangeLinkCodeRequest,
    _: None = Depends(require_bot_api_token),
    db: Session = Depends(get_db),
) -> VkExchangeTokenResponse:
    vk_user_id = _normalize_required(payload.vk_user_id, "VK user ID is required")
    code_value = payload.code.strip().upper()
    if not code_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link code not found"
        )

    link_code = db.execute(
        select(VkLinkCode).where(VkLinkCode.code == code_value)
    ).scalar_one_or_none()
    if link_code is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link code not found"
        )
    if link_code.status == VkLinkCodeStatus.USED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Link code already used"
        )
    if link_code.status != VkLinkCodeStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Link code is not active"
        )

    now = datetime.now(timezone.utc)
    if _ensure_aware_utc(link_code.expires_at) <= now:
        link_code.status = VkLinkCodeStatus.EXPIRED.value
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Link code expired"
        )

    profile = db.execute(
        select(ClientProfile)
        .options(joinedload(ClientProfile.user))
        .where(ClientProfile.id == link_code.client_id)
    ).scalar_one_or_none()
    if profile is None or profile.user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client user not found"
        )
    user = profile.user
    if not user.is_active or user.role != UserRole.CLIENT.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client user not found"
        )

    if profile.vk_user_id is not None and profile.vk_user_id != vk_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client profile is already linked",
        )

    existing_profile_id = db.execute(
        select(ClientProfile.id).where(
            ClientProfile.vk_user_id == vk_user_id,
            ClientProfile.id != profile.id,
        )
    ).scalar_one_or_none()
    if existing_profile_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="VK user is already linked"
        )

    profile.vk_user_id = vk_user_id
    link_code.status = VkLinkCodeStatus.USED.value
    link_code.used_at = now
    db.commit()
    db.refresh(user)
    return _token_response(user)


@router.post("/token", response_model=VkExchangeTokenResponse)
def create_vk_user_token(
    payload: VkTokenRequest,
    _: None = Depends(require_bot_api_token),
    db: Session = Depends(get_db),
) -> VkExchangeTokenResponse:
    vk_user_id = _normalize_required(payload.vk_user_id, "VK user ID is required")
    profile = db.execute(
        select(ClientProfile)
        .options(joinedload(ClientProfile.user))
        .where(ClientProfile.vk_user_id == vk_user_id)
    ).scalar_one_or_none()
    if profile is None or profile.user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VK user is not linked"
        )
    user = profile.user
    if not user.is_active or user.role != UserRole.CLIENT.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="VK user is not linked"
        )
    return _token_response(user)


@router.post("/onboard-client", response_model=VkOnboardClientResponse)
def onboard_vk_client(
    payload: VkOnboardClientRequest,
    _: None = Depends(require_bot_api_token),
    db: Session = Depends(get_db),
) -> VkOnboardClientResponse:
    vk_user_id = _normalize_required(payload.vk_user_id, "vk_user_id must not be empty")
    selected_city_id = _resolve_selected_city_id(db, payload.selected_city_slug)

    profile = _find_vk_profile(db, vk_user_id)
    if profile is not None:
        user = profile.user
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client user not found"
            )
        if user.role != UserRole.CLIENT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Linked user is not a client",
            )
        if selected_city_id is not None:
            profile.selected_city_id = selected_city_id
        _sync_optional_contact(user, payload.email, payload.phone)
        _ensure_vk_login(user, vk_user_id)
        setup_data = _prepare_password_setup(db, user, vk_user_id)
        db.commit()
        db.refresh(profile)
        db.refresh(user)
        return _onboard_response(user, profile, is_new=False, setup_data=setup_data)

    synthetic_profile = _find_synthetic_vk_profile(db, vk_user_id)
    if synthetic_profile is not None:
        user = synthetic_profile.user
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client user not found"
            )
        synthetic_profile.vk_user_id = vk_user_id
        if selected_city_id is not None:
            synthetic_profile.selected_city_id = selected_city_id
        _sync_optional_contact(user, payload.email, payload.phone)
        setup_data = _prepare_password_setup(db, user, vk_user_id)
        db.commit()
        db.refresh(user)
        db.refresh(synthetic_profile)
        return _onboard_response(user, synthetic_profile, is_new=False, setup_data=setup_data)

    normalized_email = _normalize_optional_email(payload.email)
    normalized_phone = _normalize_optional_text(payload.phone)
    temporary_password = generate_temporary_password()
    user = User(
        email=normalized_email or _synthetic_vk_email(vk_user_id),
        phone=normalized_phone,
        password_hash=hash_password(temporary_password),
        role=UserRole.CLIENT.value,
        is_active=True,
    )
    db.add(user)
    db.flush()

    profile = ClientProfile(
        user_id=user.id,
        vk_user_id=vk_user_id,
        selected_city_id=selected_city_id,
        full_name=_normalize_optional_text(payload.full_name),
        source=_normalize_optional_text(payload.source) or "vk",
        is_active=True,
    )
    db.add(profile)
    setup_data = _prepare_password_setup(db, user, vk_user_id)
    db.commit()
    db.refresh(user)
    db.refresh(profile)
    return _onboard_response(
        user,
        profile,
        is_new=True,
        setup_data=setup_data,
        temporary_password=temporary_password,
    )


def _token_response(user: User) -> VkExchangeTokenResponse:
    auth_payload = _build_vk_auth_payload(user)
    return VkExchangeTokenResponse(
        access_token=auth_payload["access_token"],
        user=UnifiedUserRead.model_validate(user),
    )


def _onboard_response(
    user: User,
    profile: ClientProfile,
    is_new: bool,
    setup_data: dict[str, object] | None = None,
    temporary_password: str | None = None,
) -> VkOnboardClientResponse:
    login = _user_login_value(user)
    return VkOnboardClientResponse(
        access_token=_build_vk_auth_payload(user)["access_token"],
        user=VkOnboardClientUserRead.model_validate(user),
        client=VkOnboardClientProfileRead.model_validate(profile),
        is_new=is_new,
        password_setup_required=setup_data is not None,
        password_setup_url=str(setup_data["url"]) if setup_data else None,
        login=login,
        password_setup_expires_at=setup_data["expires_at"] if setup_data else None,
        password_setup_ttl_seconds=PASSWORD_SETUP_TTL_SECONDS if setup_data else None,
        web_login_url=_web_login_url(login),
        temporary_password=temporary_password,
    )


def _find_vk_profile(db: Session, vk_user_id: str) -> ClientProfile | None:
    return db.execute(
        select(ClientProfile)
        .options(joinedload(ClientProfile.user))
        .where(ClientProfile.vk_user_id == vk_user_id)
    ).scalar_one_or_none()


def _find_synthetic_vk_profile(db: Session, vk_user_id: str) -> ClientProfile | None:
    synthetic_login = _synthetic_vk_email(vk_user_id)
    return db.execute(
        select(ClientProfile)
        .options(joinedload(ClientProfile.user))
        .join(User, ClientProfile.user_id == User.id)
        .where(
            ClientProfile.vk_user_id.is_(None),
            User.email == synthetic_login,
            User.role == UserRole.CLIENT.value,
            User.is_active.is_(True),
        )
    ).scalar_one_or_none()


def _build_vk_auth_payload(user: User) -> dict[str, str]:
    return {"access_token": create_access_token(f"user:{user.id}")}

def _prepare_password_setup(
    db: Session, user: User, vk_user_id: str
) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    active_tokens = (
        db.execute(
            select(ClientPasswordSetupToken).where(
                ClientPasswordSetupToken.user_id == user.id,
                ClientPasswordSetupToken.purpose == PASSWORD_SETUP_PURPOSE,
                ClientPasswordSetupToken.used_at.is_(None),
            )
        )
        .scalars()
        .all()
    )
    for setup_token in active_tokens:
        if _ensure_aware_utc(setup_token.expires_at) > now:
            setup_token.used_at = now

    plain_token = generate_password_setup_token()
    expires_at = now + timedelta(seconds=PASSWORD_SETUP_TTL_SECONDS)
    db.add(
        ClientPasswordSetupToken(
            user_id=user.id,
            token_hash=hash_password_setup_token(plain_token),
            purpose=PASSWORD_SETUP_PURPOSE,
            expires_at=expires_at,
            source="vk",
            vk_user_id=vk_user_id,
        )
    )

    query_params = {"setup_token": plain_token}
    login = _user_login_value(user)
    if login is not None:
        query_params["login"] = login
    public_url = settings.WEB_PUBLIC_URL.rstrip("/")
    return {"url": f"{public_url}/?{urlencode(query_params)}", "expires_at": expires_at}


def _sync_optional_contact(user: User, email: str | None, phone: str | None) -> None:
    normalized_email = _normalize_optional_email(email)
    normalized_phone = _normalize_optional_text(phone)
    if user.email is None and normalized_email is not None:
        user.email = normalized_email
    if user.phone is None and normalized_phone is not None:
        user.phone = normalized_phone


def _ensure_vk_login(user: User, vk_user_id: str) -> None:
    if _user_login_value(user) is None:
        user.email = _synthetic_vk_email(vk_user_id)


def _user_login_value(user: User) -> str | None:
    return user.email or user.phone


def _web_login_url(login: str | None) -> str | None:
    if login is None:
        return None
    public_url = settings.WEB_PUBLIC_URL.rstrip("/")
    return f"{public_url}/?{urlencode({'client_login': login})}"


def _synthetic_vk_email(vk_user_id: str) -> str:
    """Return a stable technical login for VK onboarding users without real contact data.

    The vk.local domain is intentionally non-customer-facing and should not be
    treated as the client's real email address.
    """
    digest = hashlib.sha256(vk_user_id.encode("utf-8")).hexdigest()[:32]
    return f"vk_{digest}@vk.local"


def _normalize_optional_email(value: str | None) -> str | None:
    normalized = _normalize_optional_text(value)
    return normalized.lower() if normalized is not None else None


def _resolve_selected_city_id(
    db: Session, selected_city_slug: str | None
) -> int | None:
    normalized_slug = _normalize_optional_text(selected_city_slug)
    if normalized_slug is None:
        return None
    city_id = db.execute(
        select(City.id).where(City.slug == normalized_slug, City.is_active.is_(True))
    ).scalar_one_or_none()
    if city_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="City not found"
        )
    return int(city_id)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_required(value: str, detail: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    return normalized


def _ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
