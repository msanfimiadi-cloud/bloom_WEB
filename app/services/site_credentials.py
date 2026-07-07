from __future__ import annotations

import base64
import hashlib
import secrets
import string
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User

SITE_LOGIN_PREFIX = "bloom_vk_"
SITE_PASSWORD_LENGTH = 16
_SITE_PASSWORD_ALPHABET = string.ascii_letters + string.digits


def _credentials_secret() -> str:
    return getattr(settings, "SITE_CREDENTIALS_SECRET", None) or settings.SECRET_KEY


def _fernet() -> Fernet:
    secret = _credentials_secret()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Site credentials encryption secret is not configured",
        )
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_site_password(password: str) -> str:
    return _fernet().encrypt(password.encode("utf-8")).decode("ascii")


def decrypt_site_password(encrypted_password: str) -> str:
    try:
        return _fernet().decrypt(encrypted_password.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Site credentials could not be decrypted",
        ) from exc


def generate_site_password() -> str:
    # Include a mixed-case alphanumeric alphabet to be accepted by regular site login forms.
    return "".join(secrets.choice(_SITE_PASSWORD_ALPHABET) for _ in range(SITE_PASSWORD_LENGTH))


def generate_unique_client_site_login(db: Session, user_id: int) -> str:
    base_login = f"bloom_client_{user_id}"
    if _site_login_available(db, base_login):
        return base_login

    for _ in range(20):
        candidate = f"{base_login}_{secrets.token_hex(3)}"
        if _site_login_available(db, candidate):
            return candidate

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Could not generate site login",
    )


def generate_unique_vk_site_login(db: Session, vk_user_id: str) -> str:
    base_login = f"{SITE_LOGIN_PREFIX}{vk_user_id}"
    if _site_login_available(db, base_login):
        return base_login

    for _ in range(20):
        candidate = f"{base_login}_{secrets.token_hex(3)}"
        if _site_login_available(db, candidate):
            return candidate

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Could not generate site login",
    )


def ensure_client_site_credentials(db: Session, user: User, site_login: str | None = None) -> tuple[bool, str | None]:
    """Ensure a VK client has stable site credentials.

    Returns (changed_now, plain_password_if_generated). The plain password is intentionally
    returned only to immediate callers that need to encrypt or test it before the request ends;
    API responses must not include it except the dedicated credentials endpoint.
    """
    changed = False
    generated_plain_password: str | None = None

    if not user.site_login:
        user.site_login = site_login or generate_unique_client_site_login(db, user.id)
        changed = True

    if not user.encrypted_site_password and not user.password_hash:
        generated_plain_password = generate_site_password()
        user.password_hash = hash_password(generated_plain_password)
        user.encrypted_site_password = encrypt_site_password(generated_plain_password)
        user.site_credentials_created_at = datetime.now(timezone.utc)
        changed = True
    elif user.encrypted_site_password and not user.site_credentials_created_at:
        user.site_credentials_created_at = datetime.now(timezone.utc)
        changed = True

    if changed:
        db.flush()

    return changed, generated_plain_password


def ensure_vk_site_credentials(db: Session, user: User, vk_user_id: str) -> tuple[bool, str | None]:
    site_login = user.site_login or generate_unique_vk_site_login(db, vk_user_id)
    return ensure_client_site_credentials(db, user, site_login=site_login)


def get_decrypted_site_password(user: User) -> str:
    if not user.encrypted_site_password:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site credentials are not available",
        )
    return decrypt_site_password(user.encrypted_site_password)


def _site_login_available(db: Session, site_login: str) -> bool:
    existing_id = db.execute(
        select(User.id).where(func.lower(User.site_login) == site_login.lower())
    ).scalar_one_or_none()
    return existing_id is None
