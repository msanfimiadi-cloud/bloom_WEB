from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.landing import DEFAULT_GIVEAWAY_EMPTY_TEXT, LandingSettings
from app.models.partner import Partner
from app.models.user import User, UserRole
from app.models.verification import PrivilegeVerificationSession, PrivilegeVerificationStatus
from app.schemas.landing import GiveawayItem, PublicLandingStatsRead

LANDING_SETTINGS_ID = 1
CLIENT_MEMBER_ROLES = (UserRole.CLIENT.value, "member", "customer")


def normalize_giveaway_items(items: list[dict] | None) -> list[dict]:
    normalized: list[dict] = []
    source = items if isinstance(items, list) else []
    for index, item in enumerate(source):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        normalized.append(
            {
                "title": title,
                "description": str(item.get("description") or "").strip() or None,
                "is_active": bool(item.get("is_active", True)),
                "sort_order": int(item.get("sort_order") or index),
            }
        )
    return normalized


def get_or_create_landing_settings(db: Session) -> LandingSettings:
    settings = db.get(LandingSettings, LANDING_SETTINGS_ID)
    if settings is None:
        settings = LandingSettings(id=LANDING_SETTINGS_ID)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def calculate_real_members_count(db: Session) -> int:
    real_members_count = db.execute(
        select(func.count(User.id)).where(
            User.role.in_(CLIENT_MEMBER_ROLES),
            User.is_active.is_(True),
        )
    ).scalar_one()
    return int(real_members_count or 0)


def calculate_public_members_count(db: Session, settings: LandingSettings | None = None) -> int:
    landing_settings = settings or get_or_create_landing_settings(db)
    return int(landing_settings.members_count_base or 0) + calculate_real_members_count(db)


def calculate_active_partners_count(db: Session) -> int:
    active_partners_count = db.execute(
        select(func.count(Partner.id)).where(Partner.is_active.is_(True))
    ).scalar_one()
    return int(active_partners_count or 0)


def calculate_real_savings_total(db: Session) -> int:
    real_savings_total = db.execute(
        select(func.coalesce(func.sum(PrivilegeVerificationSession.saving_amount), 0)).where(
            PrivilegeVerificationSession.status == PrivilegeVerificationStatus.confirmed.value,
            PrivilegeVerificationSession.saving_amount.is_not(None),
        )
    ).scalar_one()
    if isinstance(real_savings_total, Decimal):
        return int(real_savings_total)
    return int(real_savings_total or 0)


def get_giveaway_empty_text(value: str | None) -> str:
    return str(value or "").strip() or DEFAULT_GIVEAWAY_EMPTY_TEXT


def get_primary_giveaway_title(items: list[dict], fallback: str = "") -> str:
    active_items = [item for item in normalize_giveaway_items(items) if item.get("is_active", True)]
    active_items.sort(key=lambda item: (int(item.get("sort_order") or 0), str(item.get("title") or "")))
    if not active_items:
        return ""
    return str(active_items[0].get("title") or fallback).strip()


def build_public_landing_stats(db: Session) -> PublicLandingStatsRead:
    settings = get_or_create_landing_settings(db)
    giveaway_items = normalize_giveaway_items(settings.giveaway_items)
    current = get_primary_giveaway_title(giveaway_items, settings.giveaway_current)
    members_count_base = int(settings.members_count_base or 0)
    members_count_real = calculate_real_members_count(db)
    partners_count_base = int(settings.partners_count_display or 0)
    partners_count_real = calculate_active_partners_count(db)
    savings_total_base = int(settings.savings_total or 0)
    savings_total_real = calculate_real_savings_total(db)
    return PublicLandingStatsRead(
        members_count=members_count_base + members_count_real,
        members_count_base=members_count_base,
        members_count_real=members_count_real,
        partners_count=partners_count_base + partners_count_real,
        partners_count_base=partners_count_base,
        partners_count_real=partners_count_real,
        savings_total=savings_total_base + savings_total_real,
        savings_total_base=savings_total_base,
        savings_total_real=savings_total_real,
        giveaway_title=settings.giveaway_title or "Розыгрыш месяца",
        giveaway_current=current,
        giveaway_subtitle=settings.giveaway_subtitle or "доступно участницам клуба",
        giveaway_empty_text=get_giveaway_empty_text(settings.giveaway_empty_text),
        giveaway_items=[GiveawayItem(**item) for item in giveaway_items],
    )


def build_admin_landing_settings_read(db: Session) -> dict:
    settings = get_or_create_landing_settings(db)
    public_stats = build_public_landing_stats(db)
    return {
        "id": settings.id,
        "members_count_base": int(settings.members_count_base or 0),
        "partners_count_display": int(settings.partners_count_display or 0),
        "partners_count_base": public_stats.partners_count_base,
        "savings_total": int(settings.savings_total or 0),
        "savings_total_base": public_stats.savings_total_base,
        "giveaway_title": settings.giveaway_title,
        "giveaway_current": settings.giveaway_current,
        "giveaway_subtitle": settings.giveaway_subtitle,
        "giveaway_empty_text": get_giveaway_empty_text(settings.giveaway_empty_text),
        "giveaway_items": [GiveawayItem(**item) for item in normalize_giveaway_items(settings.giveaway_items)],
        "updated_at": settings.updated_at,
        "members_count": public_stats.members_count,
        "members_count_real": public_stats.members_count_real,
        "partners_count": public_stats.partners_count,
        "partners_count_real": public_stats.partners_count_real,
        "savings_total_display": public_stats.savings_total,
        "savings_total_real": public_stats.savings_total_real,
    }
