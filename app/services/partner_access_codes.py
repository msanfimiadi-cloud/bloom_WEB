from __future__ import annotations

from hashlib import sha256

from app.core.security import hash_password, verify_password


MIN_PARTNER_ACCESS_CODE_LENGTH = 8
MAX_PARTNER_ACCESS_CODE_LENGTH = 64


def normalize_partner_access_code(value: str) -> str:
    normalized = value.strip().upper()
    if not MIN_PARTNER_ACCESS_CODE_LENGTH <= len(normalized) <= MAX_PARTNER_ACCESS_CODE_LENGTH:
        raise ValueError("Partner access code must contain from 8 to 64 characters")
    return normalized


def partner_access_code_digest(value: str) -> str:
    normalized = normalize_partner_access_code(value)
    return sha256(normalized.encode("utf-8")).hexdigest()


def prepare_partner_access_code(value: str) -> tuple[str, str]:
    normalized = normalize_partner_access_code(value)
    return partner_access_code_digest(normalized), hash_password(normalized)


def verify_partner_access_code(value: str, password_hash: str) -> bool:
    try:
        normalized = normalize_partner_access_code(value)
    except ValueError:
        return False
    return verify_password(normalized, password_hash)
