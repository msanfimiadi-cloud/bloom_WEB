from __future__ import annotations

import hashlib
import re

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import settings
from app.db.session import get_db
from app.models.category import Category
from app.models.city import City
from app.models.lead import LeadClick
from app.models.partner import Partner, PartnerOffer, PartnerPhoto, PartnerQrLink
from app.schemas.landing import PublicLandingStatsRead
from app.schemas.partner import (
    PublicLandingPartnerCard,
    PublicLandingPartnerListResponse,
    PublicLandingPartnerOffer,
    PublicLandingPartnerPhoto,
    PublicLandingPartnerCategory,
)

from app.services.landing_settings import build_public_landing_stats

router = APIRouter(tags=["public"])


def _hash_visitor_value(value: str | None) -> str | None:
    if not value:
        return None
    salt = settings.JWT_SECRET_KEY or "womenclub"
    return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()


def _normalize_optional_query_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_slug_query_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


_SCIENTIFIC_NOTATION_PATTERN = re.compile(r"[+-]?\d+(?:[.,]\d+)?e[+-]?\d+%?", re.IGNORECASE)
PUBLIC_OFFER_BENEFIT_FALLBACK = "Специальное предложение"


def _has_scientific_notation(value: str | None) -> bool:
    return bool(value and _SCIENTIFIC_NOTATION_PATTERN.search(value.strip()))


def _format_discount_percent(value: Decimal | None) -> str | None:
    if value is None:
        return None
    normalized = value.copy_abs().normalize()
    formatted = format(normalized, "f")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return f"-{formatted}%" if formatted else None


def format_public_offer_benefit(benefit_text: str | None, discount_percent: Decimal | None) -> str:
    normalized_benefit = (benefit_text or "").strip()
    if normalized_benefit and not _has_scientific_notation(normalized_benefit):
        return normalized_benefit
    return _format_discount_percent(discount_percent) or PUBLIC_OFFER_BENEFIT_FALLBACK


def _public_landing_offer_to_read(offer: PartnerOffer) -> PublicLandingPartnerOffer:
    return PublicLandingPartnerOffer(
        title=offer.title,
        discount_text=format_public_offer_benefit(offer.benefit_text, offer.discount_percent),
        description=offer.description,
        terms=offer.conditions,
    )


def _public_landing_photo_to_read(photo: PartnerPhoto) -> PublicLandingPartnerPhoto:
    return PublicLandingPartnerPhoto(
        id=photo.id,
        url=photo.url,
        alt_text=photo.alt_text,
        sort_order=photo.sort_order,
    )


def _public_landing_category_to_read(category: Category) -> PublicLandingPartnerCategory:
    return PublicLandingPartnerCategory(
        id=category.id,
        name=category.name,
        title=category.title,
        slug=category.slug,
    )


def _public_landing_partner_to_read(
    partner: Partner,
    city: City,
    selected_category_slug: str | None,
    legacy_categories_by_slug: dict[str, Category],
    offers: list[PartnerOffer],
    photos: list[PartnerPhoto],
) -> PublicLandingPartnerCard:
    active_categories = sorted(
        [category for category in partner.categories if category.is_active],
        key=lambda c: (c.sort_order, c.name.lower(), c.id),
    )
    legacy_category = legacy_categories_by_slug.get(partner.category_slug or "")
    if selected_category_slug is not None:
        selected_category = next((category for category in active_categories if category.slug == selected_category_slug), None)
        if selected_category is None and legacy_category is not None and legacy_category.slug == selected_category_slug:
            selected_category = legacy_category
    else:
        selected_category = None
    primary_category = selected_category or (active_categories[0] if active_categories else None)
    display_category = primary_category or legacy_category
    if display_category is None:
        # The public endpoint only selects partners with an active related category or
        # active backward-compatible category_slug, so this guard is for type safety.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    category_payloads = [_public_landing_category_to_read(category) for category in active_categories]
    if not category_payloads and legacy_category is not None:
        category_payloads = [_public_landing_category_to_read(legacy_category)]

    return PublicLandingPartnerCard(
        id=partner.id,
        name=partner.name,
        address=partner.address,
        city_name=city.name,
        city_slug=city.slug,
        category_title=display_category.title,
        category_slug=display_category.slug,
        category=_public_landing_category_to_read(display_category),
        categories=category_payloads,
        category_ids=[category.id for category in active_categories] or ([legacy_category.id] if legacy_category else []),
        category_slugs=[category.slug for category in active_categories] or ([legacy_category.slug] if legacy_category else []),
        logo_url=partner.logo_url,
        cover_url=partner.cover_url,
        offers=[_public_landing_offer_to_read(offer) for offer in offers],
        photos=[_public_landing_photo_to_read(photo) for photo in photos],
    )


@router.get("/r/p/{slug}")
def redirect_partner_qr_link(
    slug: str,
    request: Request,
    session_id: str | None = None,
    utm_source: str | None = None,
    utm_medium: str | None = None,
    utm_campaign: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    qr_link = db.execute(
        select(PartnerQrLink)
        .options(joinedload(PartnerQrLink.partner))
        .where(PartnerQrLink.slug == slug, PartnerQrLink.is_active.is_(True))
    ).scalar_one_or_none()
    if qr_link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR link not found")

    client_host = request.client.host if request.client is not None else None
    lead_click = LeadClick(
        partner_id=qr_link.partner_id,
        qr_link_id=qr_link.id,
        city_id=qr_link.partner.city_id if qr_link.partner is not None else None,
        source="web_qr",
        session_id=_normalize_optional_query_value(session_id),
        ip_hash=_hash_visitor_value(client_host),
        user_agent_hash=_hash_visitor_value(request.headers.get("user-agent")),
        referer=_normalize_optional_query_value(request.headers.get("referer")),
        utm_source=_normalize_optional_query_value(utm_source),
        utm_medium=_normalize_optional_query_value(utm_medium),
        utm_campaign=_normalize_optional_query_value(utm_campaign),
    )
    db.add(lead_click)
    db.commit()

    target_url = qr_link.target_url or qr_link.deep_link_payload or f"{settings.WEB_PUBLIC_URL.rstrip('/')}/"
    return RedirectResponse(url=target_url, status_code=status.HTTP_302_FOUND)


@router.get("/api/v1/public/landing", response_model=PublicLandingStatsRead)
@router.get("/api/v1/public/landing/stats", response_model=PublicLandingStatsRead)
def read_public_landing_stats(db: Session = Depends(get_db)) -> PublicLandingStatsRead:
    return build_public_landing_stats(db)


@router.get("/api/v1/public/landing/partners", response_model=PublicLandingPartnerListResponse)
def list_public_landing_partners(
    category_slug: str | None = None,
    city_slug: str | None = None,
    limit: int = Query(default=12, ge=1),
    db: Session = Depends(get_db),
) -> PublicLandingPartnerListResponse:
    normalized_category_slug = _normalize_slug_query_value(category_slug)
    normalized_city_slug = _normalize_slug_query_value(city_slug)
    safe_limit = min(limit, 30)

    if category_slug is not None:
        category_exists = db.execute(
            select(Category.id).where(
                Category.slug == normalized_category_slug,
                Category.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if category_exists is None:
            return PublicLandingPartnerListResponse(items=[])

    if city_slug is not None:
        city_exists = db.execute(
            select(City.id).where(
                City.slug == normalized_city_slug,
                City.is_active.is_(True),
            )
        ).scalar_one_or_none()
        if city_exists is None:
            return PublicLandingPartnerListResponse(items=[])

    active_category_condition = or_(
        Partner.categories.any(Category.is_active.is_(True)),
        Partner.category_slug.in_(select(Category.slug).where(Category.is_active.is_(True))),
    )
    statement = (
        select(Partner, City)
        .join(City, Partner.city_id == City.id)
        .options(selectinload(Partner.categories))
        .where(
            Partner.is_active.is_(True),
            Partner.is_verified.is_(True),
            City.is_active.is_(True),
            active_category_condition,
        )
        .order_by(Partner.sort_order.asc(), Partner.id.asc())
        .limit(safe_limit)
    )

    if normalized_category_slug is not None:
        statement = statement.where(
            or_(
                Partner.categories.any(
                    and_(Category.slug == normalized_category_slug, Category.is_active.is_(True))
                ),
                Partner.category_slug == normalized_category_slug,
            )
        )
    if normalized_city_slug is not None:
        statement = statement.where(City.slug == normalized_city_slug)

    rows = db.execute(statement).all()
    partner_ids = [partner.id for partner, _city in rows]
    offers_by_partner: dict[int, list[PartnerOffer]] = {partner_id: [] for partner_id in partner_ids}
    photos_by_partner: dict[int, list[PartnerPhoto]] = {partner_id: [] for partner_id in partner_ids}
    if partner_ids:
        offers = db.execute(
            select(PartnerOffer)
            .where(
                PartnerOffer.partner_id.in_(partner_ids),
                PartnerOffer.is_active.is_(True),
            )
            .order_by(PartnerOffer.sort_order.asc(), PartnerOffer.id.asc())
        ).scalars().all()
        for offer in offers:
            offers_by_partner.setdefault(offer.partner_id, []).append(offer)
        photos = db.execute(
            select(PartnerPhoto)
            .where(
                PartnerPhoto.partner_id.in_(partner_ids),
                PartnerPhoto.is_active.is_(True),
            )
            .order_by(PartnerPhoto.sort_order.asc(), PartnerPhoto.created_at.asc())
        ).scalars().all()
        for photo in photos:
            photos_by_partner.setdefault(photo.partner_id, []).append(photo)

    legacy_slugs = {partner.category_slug for partner, _city in rows if partner.category_slug}
    legacy_categories_by_slug = {
        category.slug: category
        for category in db.execute(
            select(Category).where(Category.slug.in_(legacy_slugs), Category.is_active.is_(True))
        ).scalars().all()
    } if legacy_slugs else {}

    return PublicLandingPartnerListResponse(
        items=[
            _public_landing_partner_to_read(
                partner,
                city,
                normalized_category_slug,
                legacy_categories_by_slug,
                offers_by_partner.get(partner.id, []),
                photos_by_partner.get(partner.id, []),
            )
            for partner, city in rows
        ]
    )
