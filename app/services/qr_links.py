from __future__ import annotations

import re
import secrets

from app.core.config import settings
from app.models.partner import PartnerQrLink

_SAFE_SLUG_RE = re.compile(r"^[a-z0-9_-]+$")


def build_qr_url(slug: str) -> str:
    return f"{settings.WEB_PUBLIC_URL.rstrip('/')}/r/p/{slug}"


def normalize_qr_slug(slug: str | None) -> str | None:
    if slug is None:
        return None
    return slug.strip().lower()


def is_valid_qr_slug(slug: str | None) -> bool:
    return bool(slug and _SAFE_SLUG_RE.fullmatch(slug))


def generate_qr_slug(partner_id: int) -> str:
    token = secrets.token_urlsafe(6).rstrip("=").lower()
    return f"partner-{partner_id}-{token}"


def qr_link_to_read(qr_link: PartnerQrLink, *, partner_name: str | None = None) -> dict[str, object]:
    return {
        "id": qr_link.id,
        "partner_id": qr_link.partner_id,
        "slug": qr_link.slug,
        "deep_link_payload": qr_link.deep_link_payload,
        "target_url": qr_link.target_url,
        "is_active": qr_link.is_active,
        "qr_url": build_qr_url(qr_link.slug),
        "partner_name": partner_name,
    }
