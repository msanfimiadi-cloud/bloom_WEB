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
