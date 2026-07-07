from __future__ import annotations

import base64
import hashlib
import hmac
import importlib.util
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import Settings, settings

JWT_SECRET_PLACEHOLDER = "change-me-in-production"
_PASSWORD_SCHEME = "pbkdf2_sha256"
_PASSWORD_ITERATIONS = 260_000


def validate_jwt_secret(config: Settings = settings) -> str:
    secret = config.JWT_SECRET_KEY.strip()
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY must be set")
    if config.is_production and secret == JWT_SECRET_PLACEHOLDER:
        raise RuntimeError("JWT_SECRET_KEY must be changed for production")
    return secret


def _hash_password_stdlib(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PASSWORD_ITERATIONS
    )
    return "$".join(
        [
            _PASSWORD_SCHEME,
            str(_PASSWORD_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        ]
    )


def _verify_password_stdlib(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations, salt_value, digest_value = password_hash.split("$", 3)
        if scheme != _PASSWORD_SCHEME:
            return False
        salt = base64.urlsafe_b64decode(salt_value.encode("ascii"))
        expected_digest = base64.urlsafe_b64decode(digest_value.encode("ascii"))
        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual_digest, expected_digest)


def hash_password(password: str) -> str:
    if importlib.util.find_spec("bcrypt") is not None:
        import bcrypt

        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return _hash_password_stdlib(password)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith(f"{_PASSWORD_SCHEME}$"):
        return _verify_password_stdlib(password, password_hash)
    if importlib.util.find_spec("bcrypt") is not None:
        import bcrypt

        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except ValueError:
            return False
    return False


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}".encode("ascii"))


def _encode_jwt_stdlib(payload: dict[str, Any]) -> str:
    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}
    header_segment = _base64url_encode(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    payload_segment = _base64url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    signature = hmac.new(
        validate_jwt_secret().encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    return f"{header_segment}.{payload_segment}.{_base64url_encode(signature)}"


def _decode_jwt_stdlib(token: str) -> dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        expected_signature = hmac.new(
            validate_jwt_secret().encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        actual_signature = _base64url_decode(signature_segment)
        if not hmac.compare_digest(actual_signature, expected_signature):
            raise ValueError("Invalid token signature")
        header = json.loads(_base64url_decode(header_segment))
        if header.get("alg") != settings.JWT_ALGORITHM:
            raise ValueError("Invalid token algorithm")
        payload = json.loads(_base64url_decode(payload_segment))
        exp = payload.get("exp")
        if exp is not None and datetime.now(timezone.utc).timestamp() > float(exp):
            raise ValueError("Token expired")
        return payload
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid token") from exc


def generate_password_setup_token() -> str:
    return secrets.token_urlsafe(48)


def generate_temporary_password() -> str:
    return secrets.token_urlsafe(18)


def hash_password_setup_token(token: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {"sub": subject, "exp": int(expire.timestamp())}
    if additional_claims is not None:
        payload.update(additional_claims)
    if importlib.util.find_spec("jose") is not None:
        from jose import jwt

        return jwt.encode(
            payload, validate_jwt_secret(), algorithm=settings.JWT_ALGORITHM
        )
    return _encode_jwt_stdlib(payload)


def decode_access_token(token: str) -> dict[str, Any]:
    if importlib.util.find_spec("jose") is not None:
        from jose import JWTError, jwt

        try:
            return jwt.decode(
                token, validate_jwt_secret(), algorithms=[settings.JWT_ALGORITHM]
            )
        except JWTError as exc:
            raise ValueError("Invalid token") from exc
    return _decode_jwt_stdlib(token)
