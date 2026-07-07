from __future__ import annotations

from collections.abc import Callable
from hmac import compare_digest

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import AdminUser, User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def require_role(*roles: str):
    def dependency() -> tuple[str, ...]:
        return roles

    return dependency


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_bot_api_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    unauthorized = _unauthorized()
    if not settings.BOT_API_TOKEN:
        raise unauthorized
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized
    if credentials.credentials != settings.BOT_API_TOKEN:
        raise unauthorized


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    unauthorized = _unauthorized()
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
        admin_id = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        raise unauthorized from None

    result = db.execute(select(AdminUser).where(AdminUser.id == admin_id))
    admin = result.scalar_one_or_none()
    if admin is None:
        raise unauthorized
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive admin user"
        )
    if admin.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required"
        )
    return admin


def require_content_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_telegram_admin_token: str | None = Header(
        default=None, alias="X-Telegram-Admin-Token"
    ),
    db: Session = Depends(get_db),
) -> AdminUser | None:
    """Authorize Content Admin API callers.

    Prefer the server-to-server TELEGRAM_ADMIN_API_TOKEN in an Authorization
    Bearer header for the Telegram admin bot. Keep the legacy AdminUser JWT
    path so the existing web admin and tests continue to work. The optional
    X-Telegram-Admin-Token header is accepted for compatibility only.
    """

    unauthorized = _unauthorized()
    configured_token = settings.TELEGRAM_ADMIN_API_TOKEN
    bearer_token = (
        credentials.credentials
        if credentials is not None and credentials.scheme.lower() == "bearer"
        else None
    )

    for candidate in (bearer_token, x_telegram_admin_token):
        if (
            configured_token
            and candidate
            and compare_digest(candidate, configured_token)
        ):
            return None

    if bearer_token is None:
        if configured_token and x_telegram_admin_token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid content admin token")
        raise unauthorized

    try:
        payload = decode_access_token(bearer_token)
        admin_id = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        if configured_token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid content admin token") from None
        raise unauthorized from None

    result = db.execute(select(AdminUser).where(AdminUser.id == admin_id))
    admin = result.scalar_one_or_none()
    if admin is None:
        raise unauthorized
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive admin user"
        )
    if admin.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required"
        )
    return admin


def require_admin(admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
    return admin


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = _unauthorized()
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.startswith("user:"):
            raise ValueError("Unified user token subject required")
        user_id = int(subject.removeprefix("user:"))
    except (TypeError, ValueError):
        raise unauthorized from None

    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise unauthorized
    return user



def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.startswith("user:"):
            return None
        user_id = int(subject.removeprefix("user:"))
    except (TypeError, ValueError):
        return None
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    return user

def require_user_role(*roles: UserRole) -> Callable[[User], User]:
    allowed_roles = tuple(role.value for role in roles)

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User role required")
        return user

    return dependency


require_partner = require_user_role(UserRole.PARTNER)
require_client = require_user_role(UserRole.CLIENT)
require_unified_admin = require_user_role(UserRole.ADMIN)
