from __future__ import annotations

from datetime import datetime, timezone

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.security import (
    create_access_token,
    hash_password,
    hash_password_setup_token,
    verify_password,
)
from app.db.session import get_db
from app.models.client import ClientPasswordSetupToken
from app.models.client import ClientProfile
from app.schemas.browser_auth import BrowserLoginCodeRequest, BrowserTokenLoginRequest
from app.services.browser_identity_resolver import BrowserIdentityResolver
from app.services.browser_login_codes import BrowserLoginCodeService
from app.models.payment import Subscription, SubscriptionStatus
from app.models.user import AdminUser, User, UserRole
from app.services.site_credentials import ensure_vk_site_credentials
from app.services.referrals import REFERRAL_EXISTING_PROFILE_ERROR, ReferralError, apply_referral_on_new_client, ensure_referral_code, normalize_referral_code, validate_referral_for_new_client
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    PasswordSetupCompleteRequest,
    PasswordSetupCompleteResponse,
    TelegramMiniAppLoginResponse,
    TelegramMiniAppSubscriptionRead,
    TelegramMiniAppUserRead,
    UnifiedTokenResponse,
    UnifiedUserRead,
    UserLoginRequest,
    VkMiniAppLoginResponse,
)
from app.services.telegram_miniapp_auth import (
    TelegramMiniAppUser,
    extract_telegram_user,
    verify_telegram_init_data,
)
from app.services.vk_miniapp_auth import (
    extract_vk_user_id,
    parse_launch_params,
    validate_vk_ts_freshness,
    verify_vk_miniapp_signature,
)

router = APIRouter(prefix="/auth", tags=["auth"])


VK_MINIAPP_LOGIN_HANDLER = "vk-miniapp-login-v2"
VK_MINIAPP_ENTRYPOINT = "fed_women_club_WEB"
PASSWORD_SETUP_PURPOSE = "vk_onboarding_password_setup"


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    result = db.execute(select(AdminUser).where(AdminUser.email == payload.email.lower()))
    admin = result.scalar_one_or_none()

    if admin is None or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive admin user")

    token = create_access_token(str(admin.id))
    return LoginResponse(access_token=token, user=admin)


@router.post("/user-login", response_model=UnifiedTokenResponse)
def user_login(payload: UserLoginRequest, db: Session = Depends(get_db)) -> UnifiedTokenResponse:
    login_value = payload.login.strip()
    email_value = login_value.lower()
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect login or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    result = db.execute(
        select(User).where(
            or_(
                func.lower(User.email) == email_value,
                User.phone == login_value,
                func.lower(User.site_login) == email_value,
            )
        )
    )
    user = result.scalars().first()

    if user is None or not user.is_active or not user.password_hash:
        raise unauthorized
    if not verify_password(payload.password, user.password_hash):
        raise unauthorized

    token = create_access_token(f"user:{user.id}")
    return UnifiedTokenResponse(access_token=token, user=user)


def _missing_launch_params_response() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "launch_params are required",
            "handler": VK_MINIAPP_LOGIN_HANDLER,
            "entrypoint": VK_MINIAPP_ENTRYPOINT,
        },
    )


def _stringify_params(params: dict[str, Any]) -> dict[str, str]:
    return {key: str(value) for key, value in params.items() if value is not None}


def _extract_vk_miniapp_params(payload: Any) -> dict[str, str] | None:
    if not isinstance(payload, dict) or not payload:
        return None

    launch_params = payload.get("launch_params") or payload.get("launchParams")
    if isinstance(launch_params, str) and launch_params.strip():
        return parse_launch_params(launch_params)

    params = payload.get("params")
    if isinstance(params, dict) and params:
        return _stringify_params(params)

    if "sign" in payload and any(key.startswith("vk_") for key in payload):
        return _stringify_params(payload)

    return None


def _build_vk_miniapp_full_name(params: dict[str, str]) -> str | None:
    parts = [
        (params.get("vk_first_name") or params.get("first_name") or "").strip(),
        (params.get("vk_last_name") or params.get("last_name") or "").strip(),
    ]
    full_name = " ".join(part for part in parts if part)
    return full_name or None


def _get_or_create_vk_client_profile(
    db: Session,
    vk_user_id: str,
    params: dict[str, str],
) -> tuple[ClientProfile, bool, bool]:
    profile = db.execute(
        select(ClientProfile)
        .options(joinedload(ClientProfile.user))
        .where(ClientProfile.vk_user_id == vk_user_id)
    ).scalar_one_or_none()
    if profile is not None:
        if profile.user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Client user is inactive or invalid")
        generated_credentials, _ = ensure_vk_site_credentials(db, profile.user, vk_user_id)
        if generated_credentials:
            ensure_referral_code(db, profile)
            db.commit()
            db.refresh(profile)
        return profile, False, generated_credentials

    user = User(role=UserRole.CLIENT.value, is_active=True)
    db.add(user)
    db.flush()

    profile = ClientProfile(
        user_id=user.id,
        vk_user_id=vk_user_id,
        full_name=_build_vk_miniapp_full_name(params),
        source="vk-miniapp",
        is_active=True,
    )
    db.add(profile)
    db.flush()
    ensure_referral_code(db, profile)
    generated_credentials, _ = ensure_vk_site_credentials(db, user, vk_user_id)
    db.commit()
    db.refresh(profile)
    return profile, True, generated_credentials


def _build_telegram_full_name(telegram_user: TelegramMiniAppUser) -> str | None:
    full_name = " ".join(
        part for part in (telegram_user.first_name, telegram_user.last_name) if part
    ).strip()
    return full_name or None


def _sync_telegram_profile_fields(profile: ClientProfile, telegram_user: TelegramMiniAppUser) -> bool:
    changed = False
    updates = {
        "telegram_username": telegram_user.username,
        "telegram_first_name": telegram_user.first_name,
        "telegram_last_name": telegram_user.last_name,
        "telegram_photo_url": telegram_user.photo_url,
    }
    for field, value in updates.items():
        if getattr(profile, field) != value:
            setattr(profile, field, value)
            changed = True

    full_name = _build_telegram_full_name(telegram_user)
    if full_name and not profile.full_name:
        profile.full_name = full_name
        changed = True
    if profile.source != "telegram-miniapp":
        profile.source = "telegram-miniapp"
        changed = True
    if not profile.is_active:
        profile.is_active = True
        changed = True
    return changed


def _get_or_create_telegram_client_profile(
    db: Session,
    telegram_user: TelegramMiniAppUser,
    referral_code: str | None = None,
) -> tuple[ClientProfile, bool]:
    profile = db.execute(
        select(ClientProfile)
        .options(joinedload(ClientProfile.user))
        .where(ClientProfile.telegram_user_id == telegram_user.telegram_user_id)
    ).scalar_one_or_none()
    if profile is not None:
        if profile.user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Client user is inactive or invalid")
        changed = _sync_telegram_profile_fields(profile, telegram_user)
        ensure_referral_code(db, profile)
        if normalize_referral_code(referral_code):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=REFERRAL_EXISTING_PROFILE_ERROR)
        if changed or not profile.referral_code:
            db.commit()
            db.refresh(profile)
        return profile, False

    validate_referral_for_new_client(db, referral_code, provider="telegram", provider_user_id=telegram_user.telegram_user_id)

    user = User(role=UserRole.CLIENT.value, is_active=True)
    db.add(user)
    db.flush()

    profile = ClientProfile(
        user_id=user.id,
        telegram_user_id=telegram_user.telegram_user_id,
        telegram_username=telegram_user.username,
        telegram_first_name=telegram_user.first_name,
        telegram_last_name=telegram_user.last_name,
        telegram_photo_url=telegram_user.photo_url,
        full_name=_build_telegram_full_name(telegram_user),
        source="telegram-miniapp",
        is_active=True,
    )
    db.add(profile)
    db.flush()
    ensure_referral_code(db, profile)
    apply_referral_on_new_client(db, profile, referral_code)
    db.commit()
    db.refresh(profile)
    return profile, True


def _active_subscription_summary(db: Session, client_id: int) -> TelegramMiniAppSubscriptionRead:
    now = datetime.now(timezone.utc)
    subscription = db.execute(
        select(Subscription)
        .where(
            Subscription.client_id == client_id,
            Subscription.status == SubscriptionStatus.active.value,
            Subscription.starts_at <= now,
            Subscription.ends_at > now,
        )
        .order_by(Subscription.ends_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if subscription is None:
        return TelegramMiniAppSubscriptionRead(is_active=False, expires_at=None)
    return TelegramMiniAppSubscriptionRead(is_active=True, expires_at=subscription.ends_at)


def _telegram_user_read(user: User, profile: ClientProfile) -> TelegramMiniAppUserRead:
    return TelegramMiniAppUserRead(
        id=user.id,
        telegram_user_id=profile.telegram_user_id,
        first_name=profile.telegram_first_name,
        last_name=profile.telegram_last_name,
        username=profile.telegram_username,
        photo_url=profile.telegram_photo_url,
        role=UserRole.CLIENT.value,
    )


def _build_client_auth_response(db: Session, profile: ClientProfile) -> TelegramMiniAppLoginResponse:
    user = profile.user
    if user is None or not user.is_active or user.role != UserRole.CLIENT.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Client user is inactive or invalid")

    return TelegramMiniAppLoginResponse(
        access_token=create_access_token(f"user:{user.id}"),
        user=_telegram_user_read(user, profile),
        client=profile,
        subscription=_active_subscription_summary(db, profile.id),
    )


@router.post("/telegram-miniapp-login", response_model=TelegramMiniAppLoginResponse)
def telegram_miniapp_login(
    payload: Any = Body(default=None),
    db: Session = Depends(get_db),
) -> TelegramMiniAppLoginResponse:
    init_data = payload.get("init_data") if isinstance(payload, dict) else None
    if not isinstance(init_data, str) or not init_data.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_init_data")

    params = verify_telegram_init_data(init_data)
    telegram_user = extract_telegram_user(params)
    referral_code = None
    if isinstance(payload, dict):
        referral_code = payload.get("referral_code") or payload.get("start_param") or payload.get("startapp")
    if referral_code is None:
        referral_code = params.get("start_param") or params.get("startapp")
    try:
        profile, _ = _get_or_create_telegram_client_profile(db, telegram_user, referral_code=referral_code)
    except ReferralError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail) from exc
    return _build_client_auth_response(db, profile)


@router.post("/login-code", response_model=TelegramMiniAppLoginResponse)
def browser_login_code_login(
    payload: BrowserLoginCodeRequest,
    db: Session = Depends(get_db),
) -> TelegramMiniAppLoginResponse:
    service = BrowserLoginCodeService(db)
    code_record = service.get_by_code(payload.login_code or "")
    if code_record is None:
        service.mark_failed_attempt(payload.login_code or "")
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="code_not_found")
    if service.is_expired(code_record):
        service.mark_failed_attempt(payload.login_code or "")
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="code_expired")
    if code_record.used_at is not None:
        service.mark_failed_attempt(payload.login_code or "")
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="code_already_used")
    if payload.provider and code_record.provider != payload.provider.strip().lower():
        service.mark_failed_attempt(payload.login_code or "")
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="provider_mismatch")
    if getattr(code_record, "purpose", "login") != "login":
        service.mark_failed_attempt(payload.login_code or "")
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_code_purpose")

    try:
        resolved = BrowserIdentityResolver(db).resolve(
            provider=code_record.provider,
            provider_user_id=code_record.provider_user_id,
            display_name=code_record.display_name,
            username=code_record.username,
            photo_url=code_record.photo_url,
            referral_code=payload.referral_code or code_record.referral_code,
            source=code_record.source,
        )
    except ReferralError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail) from exc
    response = _build_client_auth_response(db, resolved.client_profile)
    service.mark_used(code_record)
    db.commit()
    return response


@router.post("/browser-token-login", response_model=TelegramMiniAppLoginResponse)
def browser_token_login(
    payload: BrowserTokenLoginRequest,
    db: Session = Depends(get_db),
) -> TelegramMiniAppLoginResponse:
    from app.services.browser_login_tokens import BrowserLoginTokenService

    service = BrowserLoginTokenService(db)
    token_record = service.get_by_token(payload.token.strip())
    if token_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="token_not_found")
    if token_record.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="token_revoked")
    if service.is_expired(token_record):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="token_expired")
    if token_record.used_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="token_already_used")

    try:
        resolved = BrowserIdentityResolver(db).resolve(
            provider=token_record.provider,
            provider_user_id=token_record.provider_user_id,
            display_name=token_record.display_name,
            username=token_record.username,
            photo_url=token_record.photo_url,
            referral_code=token_record.referral_code,
            source=token_record.source,
            create_if_missing=False,
        )
    except ReferralError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail) from exc
    if resolved.status == "not_found" or resolved.client_profile is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="profile_not_found")

    response = _build_client_auth_response(db, resolved.client_profile)
    service.mark_used(token_record)
    db.commit()
    return response


@router.post("/vk-miniapp-login", response_model=VkMiniAppLoginResponse)
def vk_miniapp_login(
    payload: Any = Body(default=None),
    db: Session = Depends(get_db),
) -> VkMiniAppLoginResponse | JSONResponse:
    params = _extract_vk_miniapp_params(payload)
    if params is None:
        return _missing_launch_params_response()

    verify_vk_miniapp_signature(params)
    validate_vk_ts_freshness(params)
    vk_user_id = extract_vk_user_id(params)

    profile, created_profile, generated_credentials = _get_or_create_vk_client_profile(db, vk_user_id, params)
    user = profile.user
    if user is None or not user.is_active or user.role != UserRole.CLIENT.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Client user is inactive or invalid")

    return VkMiniAppLoginResponse(
        access_token=create_access_token(f"user:{user.id}"),
        user=UnifiedUserRead.model_validate(user),
        client=profile,
        generated_account=created_profile or generated_credentials,
        profile_completed=_is_vk_profile_completed(profile, user),
        missing_fields=_vk_profile_missing_fields(profile, user),
    )


@router.post("/password-setup/complete", response_model=PasswordSetupCompleteResponse)
def complete_password_setup(
    payload: PasswordSetupCompleteRequest,
    db: Session = Depends(get_db),
) -> PasswordSetupCompleteResponse:
    token = payload.token.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password setup link",
        )
    if payload.password_confirm is not None and payload.password != payload.password_confirm:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least 8 characters",
        )

    now = datetime.now(timezone.utc)
    setup_token = db.execute(
        select(ClientPasswordSetupToken).where(
            ClientPasswordSetupToken.token_hash == hash_password_setup_token(token),
            ClientPasswordSetupToken.purpose == PASSWORD_SETUP_PURPOSE,
            ClientPasswordSetupToken.used_at.is_(None),
        )
    ).scalar_one_or_none()

    if setup_token is None or _ensure_aware_utc(setup_token.expires_at) <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password setup link",
        )

    user = db.get(User, setup_token.user_id)
    if user is None or not user.is_active or user.role != UserRole.CLIENT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password setup link",
        )

    user.password_hash = hash_password(payload.password)
    setup_token.used_at = now
    db.commit()

    return PasswordSetupCompleteResponse(
        ok=True,
        login=user.site_login or user.email or user.phone,
        message="Password has been set",
    )


@router.get("/user-me", response_model=UnifiedUserRead)
def read_user_me(user: User = Depends(get_current_user)) -> User:
    return user


def _ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _vk_profile_missing_fields(profile: ClientProfile, user: User) -> list[str]:
    missing: list[str] = []
    if not profile.full_name:
        missing.append("name")
    if not user.phone:
        missing.append("phone")
    if not (profile.contact_email or user.email):
        missing.append("email")
    if profile.selected_city_id is None and not profile.custom_city:
        missing.append("city")
    return missing


def _is_vk_profile_completed(profile: ClientProfile, user: User) -> bool:
    return not _vk_profile_missing_fields(profile, user)
