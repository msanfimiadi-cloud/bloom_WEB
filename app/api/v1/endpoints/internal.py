from __future__ import annotations

from hmac import compare_digest

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import bearer_scheme
from app.core.config import settings
from app.db.session import get_db
from app.schemas.browser_auth import (
    BrowserLoginCodeCreateRequest,
    BrowserLoginCodeInternalResponse,
    BrowserLoginTokenCreateRequest,
    BrowserLoginTokenCreateResponse,
)
from app.schemas.engagement import (
    InternalPartnerAccessStatusRead,
    InternalPartnerCodeCheckRequest,
    InternalPartnerCodeConfirmRequest,
    InternalPartnerCodeConfirmationRead,
    InternalPartnerCodeRead,
    InternalPartnerIdentityRequest,
)
from app.services.engagement import check_partner_code, confirm_verification, get_partner_bot_access
from app.services.offer_savings import calculate_offer_saving_snapshot
from app.services.browser_login_codes import LOGIN_CODE_TTL_SECONDS, BrowserLoginCodeService
from app.services.browser_login_tokens import BrowserLoginTokenService

router = APIRouter(prefix="/internal", tags=["internal"])


def require_internal_service_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    if not settings.BOT_SERVICE_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if not compare_digest(credentials.credentials, settings.BOT_SERVICE_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


@router.post("/partner-access/status", response_model=InternalPartnerAccessStatusRead)
def read_partner_access_status(
    payload: InternalPartnerIdentityRequest,
    _: None = Depends(require_internal_service_token),
    db: Session = Depends(get_db),
) -> InternalPartnerAccessStatusRead:
    access = get_partner_bot_access(db, payload.provider, payload.provider_user_id)
    if access is None or not access.partner.is_active:
        return InternalPartnerAccessStatusRead(is_partner=False)
    return InternalPartnerAccessStatusRead(
        is_partner=True,
        partner_id=access.partner_id,
        partner_name=access.partner.name,
        employee_name=access.display_name,
    )


@router.post("/partner-code/check", response_model=InternalPartnerCodeRead)
def check_internal_partner_code(
    payload: InternalPartnerCodeCheckRequest,
    _: None = Depends(require_internal_service_token),
    db: Session = Depends(get_db),
) -> InternalPartnerCodeRead:
    access = get_partner_bot_access(db, payload.provider, payload.provider_user_id)
    if access is None or not access.partner.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="partner_access_required")
    try:
        session = check_partner_code(db, access, payload.code)
        saving = calculate_offer_saving_snapshot(session.offer)
        result = InternalPartnerCodeRead(
            session_id=session.id,
            code=session.code,
            partner_name=access.partner.name,
            privilege_title=session.offer.title if session.offer is not None else None,
            saving_amount=saving.saving_amount,
            expires_at=session.expires_at,
        )
        db.commit()
        return result
    except HTTPException:
        db.commit()
        raise


@router.post("/partner-code/confirm", response_model=InternalPartnerCodeConfirmationRead)
def confirm_internal_partner_code(
    payload: InternalPartnerCodeConfirmRequest,
    _: None = Depends(require_internal_service_token),
    db: Session = Depends(get_db),
) -> InternalPartnerCodeConfirmationRead:
    access = get_partner_bot_access(db, payload.provider, payload.provider_user_id)
    if access is None or not access.partner.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="partner_access_required")
    from app.models.verification import PrivilegeVerificationSession

    session = db.get(PrivilegeVerificationSession, payload.session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="code_not_found")
    confirmed, number = confirm_verification(db, session, partner=access.partner, bot_access=access)
    return InternalPartnerCodeConfirmationRead(
        status=confirmed.status,
        saving_amount=confirmed.saving_amount or 0,
        giveaway_number_awarded=number is not None,
        giveaway_number=number.number if number is not None else None,
    )

@router.post("/login-code", response_model=BrowserLoginCodeInternalResponse)
def create_browser_login_code(
    payload: BrowserLoginCodeCreateRequest,
    _: None = Depends(require_internal_service_token),
    db: Session = Depends(get_db),
) -> BrowserLoginCodeInternalResponse:
    provider = payload.provider.strip().lower()
    provider_user_id = payload.provider_user_id.strip()
    if provider not in {"telegram", "vk"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="unsupported_provider")
    if not provider_user_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="provider_user_id_required")

    service = BrowserLoginCodeService(db)
    login_code, _ = service.create_code(
        provider=provider,
        provider_user_id=provider_user_id,
        display_name=_build_display_name(payload.first_name, payload.last_name),
        username=_normalize_optional(payload.username),
        photo_url=_normalize_optional(payload.photo_url),
        referral_code=_normalize_optional(payload.referral_code),
        source=_normalize_optional(payload.source),
        created_by="internal-api",
        purpose=payload.purpose,
    )
    db.commit()
    return BrowserLoginCodeInternalResponse(login_code=login_code, expires_in=LOGIN_CODE_TTL_SECONDS)


@router.post("/browser-login-token", response_model=BrowserLoginTokenCreateResponse)
def create_browser_login_token(
    payload: BrowserLoginTokenCreateRequest,
    _: None = Depends(require_internal_service_token),
    db: Session = Depends(get_db),
) -> BrowserLoginTokenCreateResponse:
    service = BrowserLoginTokenService(db)
    token, token_record = service.create_token(
        provider=payload.provider.strip(),
        provider_user_id=payload.provider_user_id.strip(),
        display_name=_normalize_optional(payload.display_name),
        username=_normalize_optional(payload.username),
        photo_url=_normalize_optional(payload.photo_url),
        referral_code=_normalize_optional(payload.referral_code),
        source=_normalize_optional(payload.source),
        created_by="internal-api",
    )
    db.commit()
    db.refresh(token_record)
    return BrowserLoginTokenCreateResponse(
        token=token,
        expires_at=token_record.expires_at,
        login_url=service.build_login_url(token),
    )


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _build_display_name(first_name: str | None, last_name: str | None) -> str | None:
    parts = [part for part in (_normalize_optional(first_name), _normalize_optional(last_name)) if part]
    return " ".join(parts) or None
