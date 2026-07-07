from __future__ import annotations

from decimal import Decimal
from typing import TypeVar

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_content_admin
from app.db.content_session import get_content_db
from app.models.content import (
    ContentBanner,
    ContentBlock,
    ContentCategory,
    ContentCity,
    ContentGiveaway,
    ContentGiveawayItem,
    ContentOffer,
    ContentOfferPhoto,
    ContentPartner,
    ContentPartnerCategory,
    ContentPartnerPhoto,
)
from app.services.image_uploads import save_content_image_upload
from app.schemas.content import (
    ContentBannerCreate,
    ContentBannerRead,
    ContentBannerUpdate,
    ContentBlockCreate,
    ContentBlockRead,
    ContentBlockUpdate,
    ContentCategoryCreate,
    ContentCategoryRead,
    ContentCategoryUpdate,
    ContentCityCreate,
    ContentCityRead,
    ContentCityUpdate,
    ContentGiveawayCreate,
    ContentGiveawayItemCreate,
    ContentGiveawayItemRead,
    ContentGiveawayItemUpdate,
    ContentGiveawayPublicRead,
    ContentGiveawayRead,
    ContentGiveawayUpdate,
    ContentOfferCreate,
    ContentOfferPhotoCreate,
    ContentOfferPhotoRead,
    ContentOfferPhotoUpdate,
    ContentOfferRead,
    ContentOfferUpdate,
    ContentPartnerCreate,
    ContentPartnerPhotoCreate,
    ContentPartnerPhotoRead,
    ContentPartnerPhotoUpdate,
    ContentPartnerRead,
    ContentPartnerUpdate,
    ContentUploadRead,
)

router = APIRouter(prefix="/api/content", tags=["content"])
admin_router = APIRouter(
    prefix="/admin",
    tags=["content-admin"],
    dependencies=[Depends(require_content_admin)],
)

ModelT = TypeVar("ModelT")

PARTNER_FIELDS = (
    "city_id",
    "category_slug",
    "name",
    "description",
    "address",
    "phone",
    "website_url",
    "social_url",
    "instagram_url",
    "vk_url",
    "telegram_url",
    "whatsapp_url",
    "map_url",
    "working_hours",
    "logo_url",
    "cover_url",
    "is_active",
    "is_verified",
    "sort_order",
)


def _get_or_404(
    db: Session, model: type[ModelT], object_id: int, detail: str
) -> ModelT:
    item = db.get(model, object_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return item


def _commit_or_400(db: Session, duplicate_detail: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=duplicate_detail
        ) from None


def _apply_update(
    instance: object, payload: object, *, exclude: set[str] | None = None
) -> None:
    exclude = exclude or set()
    for field, value in payload.model_dump(exclude_unset=True, exclude=exclude).items():
        setattr(instance, field, value)


def _discount_percent_from_saving(
    regular_price: Decimal, saving: Decimal
) -> Decimal | None:
    if regular_price <= 0:
        return None
    return (saving / regular_price * Decimal("100")).quantize(Decimal("0.01"))


def _offer_payload_to_db_data(
    payload: ContentOfferCreate | ContentOfferUpdate,
    *,
    existing_offer: ContentOffer | None = None,
) -> dict[str, object]:
    fields_to_exclude = {"regular_price", "club_price", "saving", "terms"}
    data = payload.model_dump(exclude_unset=True, exclude=fields_to_exclude)

    if payload.regular_price is not None and "base_price" not in data:
        data["base_price"] = payload.regular_price

    regular_price = data.get(
        "base_price", existing_offer.base_price if existing_offer is not None else None
    )
    club_price = payload.club_price
    saving = payload.saving

    if regular_price is not None:
        regular_price = Decimal(str(regular_price))
        if club_price is not None:
            saving = regular_price - Decimal(str(club_price))
        if saving is not None:
            data["discount_percent"] = _discount_percent_from_saving(
                regular_price, Decimal(str(saving))
            )

    return data


def _partner_to_read(partner: ContentPartner) -> ContentPartnerRead:
    data = ContentPartnerRead.model_validate(partner).model_dump()
    data["category_ids"] = [link.category_id for link in partner.category_links]
    return ContentPartnerRead.model_validate(data)


def _giveaway_to_public_read(giveaway: ContentGiveaway) -> ContentGiveawayPublicRead:
    data = ContentGiveawayRead.model_validate(giveaway).model_dump()
    active_items = sorted(
        (item for item in giveaway.items if item.is_active),
        key=lambda item: (item.sort_order, item.id),
    )
    data["items"] = [
        ContentGiveawayItemRead.model_validate(item) for item in active_items
    ]
    return ContentGiveawayPublicRead.model_validate(data)


def _replace_partner_categories(
    db: Session, partner: ContentPartner, category_ids: list[int]
) -> None:
    unique_ids = list(dict.fromkeys(category_ids))
    if unique_ids:
        existing_ids = set(
            db.execute(
                select(ContentCategory.id).where(ContentCategory.id.in_(unique_ids))
            )
            .scalars()
            .all()
        )
        missing_ids = sorted(set(unique_ids) - existing_ids)
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content categories not found: {', '.join(str(category_id) for category_id in missing_ids)}",
            )
    db.query(ContentPartnerCategory).filter(
        ContentPartnerCategory.partner_id == partner.id
    ).delete()
    for category_id in unique_ids:
        db.add(ContentPartnerCategory(partner_id=partner.id, category_id=category_id))


@router.get("/health")
def content_health(_db: Session = Depends(get_content_db)) -> dict[str, str]:
    """Health endpoint for the isolated content API surface."""

    return {"status": "ok", "service": "content", "database": "configured"}


@router.post("/uploads", response_model=ContentUploadRead)
async def upload_content_image(
    file: UploadFile = File(...),
    _admin=Depends(require_content_admin),
) -> dict[str, object]:
    return await save_content_image_upload(file)


@router.get("/blocks", response_model=list[ContentBlockRead])
def list_content_blocks(
    block_type: str | None = Query(default=None, alias="type"),
    db: Session = Depends(get_content_db),
) -> list[ContentBlock]:
    statement = select(ContentBlock).where(ContentBlock.is_active.is_(True))
    if block_type is not None:
        statement = statement.where(ContentBlock.placement == block_type)
    return (
        db.execute(
            statement.order_by(
                ContentBlock.placement, ContentBlock.key, ContentBlock.locale
            )
        )
        .scalars()
        .all()
    )


@router.get("/cities", response_model=list[ContentCityRead])
def list_content_cities(db: Session = Depends(get_content_db)) -> list[ContentCity]:
    return (
        db.execute(
            select(ContentCity)
            .where(ContentCity.is_active.is_(True))
            .order_by(ContentCity.sort_order, ContentCity.name)
        )
        .scalars()
        .all()
    )


@router.get("/categories", response_model=list[ContentCategoryRead])
def list_content_categories(
    db: Session = Depends(get_content_db),
) -> list[ContentCategory]:
    return (
        db.execute(
            select(ContentCategory)
            .where(ContentCategory.is_active.is_(True))
            .order_by(ContentCategory.sort_order, ContentCategory.name)
        )
        .scalars()
        .all()
    )


@router.get("/partners", response_model=list[ContentPartnerRead])
def list_content_partners(
    db: Session = Depends(get_content_db),
) -> list[ContentPartnerRead]:
    partners = (
        db.execute(
            select(ContentPartner)
            .options(selectinload(ContentPartner.category_links))
            .where(ContentPartner.is_active.is_(True))
            .order_by(ContentPartner.sort_order, ContentPartner.name)
        )
        .scalars()
        .all()
    )
    return [_partner_to_read(partner) for partner in partners]


@router.get("/partners/{partner_id}", response_model=ContentPartnerRead)
def read_content_partner(
    partner_id: int, db: Session = Depends(get_content_db)
) -> ContentPartnerRead:
    partner = db.execute(
        select(ContentPartner)
        .options(selectinload(ContentPartner.category_links))
        .where(ContentPartner.id == partner_id, ContentPartner.is_active.is_(True))
    ).scalar_one_or_none()
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content partner not found"
        )
    return _partner_to_read(partner)


@router.get("/partners/{partner_id}/offers", response_model=list[ContentOfferRead])
def list_content_partner_offers(
    partner_id: int, db: Session = Depends(get_content_db)
) -> list[ContentOffer]:
    _get_or_404(db, ContentPartner, partner_id, "Content partner not found")
    return (
        db.execute(
            select(ContentOffer)
            .where(
                ContentOffer.partner_id == partner_id, ContentOffer.is_active.is_(True)
            )
            .order_by(ContentOffer.sort_order, ContentOffer.title)
        )
        .scalars()
        .all()
    )


@router.get("/giveaways", response_model=list[ContentGiveawayPublicRead])
def list_content_giveaways(
    db: Session = Depends(get_content_db),
) -> list[ContentGiveawayPublicRead]:
    giveaways = (
        db.execute(
            select(ContentGiveaway)
            .options(selectinload(ContentGiveaway.items))
            .where(ContentGiveaway.is_active.is_(True))
            .order_by(ContentGiveaway.sort_order, ContentGiveaway.id)
        )
        .scalars()
        .all()
    )
    return [_giveaway_to_public_read(giveaway) for giveaway in giveaways]


@router.get("/banners", response_model=list[ContentBannerRead])
def list_content_banners(db: Session = Depends(get_content_db)) -> list[ContentBanner]:
    return (
        db.execute(
            select(ContentBanner)
            .where(ContentBanner.is_active.is_(True))
            .order_by(ContentBanner.sort_order, ContentBanner.id)
        )
        .scalars()
        .all()
    )


@admin_router.post(
    "/blocks", response_model=ContentBlockRead, status_code=status.HTTP_201_CREATED
)
def admin_create_content_block(
    payload: ContentBlockCreate, db: Session = Depends(get_content_db)
) -> ContentBlock:
    block = ContentBlock(**payload.model_dump())
    db.add(block)
    _commit_or_400(db, "Content block with this key and locale already exists")
    db.refresh(block)
    return block


@admin_router.patch("/blocks/{key}", response_model=ContentBlockRead)
def admin_update_content_block(
    key: str, payload: ContentBlockUpdate, db: Session = Depends(get_content_db)
) -> ContentBlock:
    locale = payload.locale or "ru"
    block = db.execute(
        select(ContentBlock).where(
            ContentBlock.key == key, ContentBlock.locale == locale
        )
    ).scalar_one_or_none()
    if block is None:
        create_data = payload.model_dump(exclude_unset=True)
        create_data["key"] = key
        create_data["locale"] = locale
        create_data.setdefault("placement", "static_texts")
        block = ContentBlock(**create_data)
    else:
        _apply_update(block, payload)
    db.add(block)
    _commit_or_400(db, "Content block with this key and locale already exists")
    db.refresh(block)
    return block


@admin_router.get("/cities", response_model=list[ContentCityRead])
def admin_list_content_cities(
    db: Session = Depends(get_content_db),
) -> list[ContentCity]:
    return (
        db.execute(
            select(ContentCity).order_by(ContentCity.sort_order, ContentCity.name)
        )
        .scalars()
        .all()
    )


@admin_router.post(
    "/cities", response_model=ContentCityRead, status_code=status.HTTP_201_CREATED
)
def admin_create_content_city(
    payload: ContentCityCreate, db: Session = Depends(get_content_db)
) -> ContentCity:
    city = ContentCity(**payload.model_dump())
    db.add(city)
    _commit_or_400(db, "Content city with this slug or name already exists")
    db.refresh(city)
    return city


@admin_router.patch("/cities/{city_id}", response_model=ContentCityRead)
def admin_update_content_city(
    city_id: int, payload: ContentCityUpdate, db: Session = Depends(get_content_db)
) -> ContentCity:
    city = _get_or_404(db, ContentCity, city_id, "Content city not found")
    _apply_update(city, payload)
    db.add(city)
    _commit_or_400(db, "Content city with this slug or name already exists")
    db.refresh(city)
    return city


@admin_router.get("/categories", response_model=list[ContentCategoryRead])
def admin_list_content_categories(
    db: Session = Depends(get_content_db),
) -> list[ContentCategory]:
    return (
        db.execute(
            select(ContentCategory).order_by(
                ContentCategory.sort_order, ContentCategory.name
            )
        )
        .scalars()
        .all()
    )


@admin_router.post(
    "/categories",
    response_model=ContentCategoryRead,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_content_category(
    payload: ContentCategoryCreate, db: Session = Depends(get_content_db)
) -> ContentCategory:
    category = ContentCategory(**payload.model_dump())
    db.add(category)
    _commit_or_400(db, "Content category with this slug already exists")
    db.refresh(category)
    return category


@admin_router.patch("/categories/{category_id}", response_model=ContentCategoryRead)
def admin_update_content_category(
    category_id: int,
    payload: ContentCategoryUpdate,
    db: Session = Depends(get_content_db),
) -> ContentCategory:
    category = _get_or_404(
        db, ContentCategory, category_id, "Content category not found"
    )
    _apply_update(category, payload)
    db.add(category)
    _commit_or_400(db, "Content category with this slug already exists")
    db.refresh(category)
    return category


@admin_router.get("/partners", response_model=list[ContentPartnerRead])
def admin_list_content_partners(
    db: Session = Depends(get_content_db),
) -> list[ContentPartnerRead]:
    partners = (
        db.execute(
            select(ContentPartner)
            .options(selectinload(ContentPartner.category_links))
            .order_by(ContentPartner.sort_order, ContentPartner.name)
        )
        .scalars()
        .all()
    )
    return [_partner_to_read(partner) for partner in partners]


@admin_router.post(
    "/partners", response_model=ContentPartnerRead, status_code=status.HTTP_201_CREATED
)
def admin_create_content_partner(
    payload: ContentPartnerCreate, db: Session = Depends(get_content_db)
) -> ContentPartnerRead:
    _get_or_404(db, ContentCity, payload.city_id, "Content city not found")
    partner_data = {field: getattr(payload, field) for field in PARTNER_FIELDS}
    partner = ContentPartner(**partner_data)
    db.add(partner)
    db.flush()
    _replace_partner_categories(db, partner, payload.category_ids)
    _commit_or_400(db, "Content partner could not be created")
    partner = db.execute(
        select(ContentPartner)
        .options(selectinload(ContentPartner.category_links))
        .where(ContentPartner.id == partner.id)
    ).scalar_one()
    return _partner_to_read(partner)


@admin_router.get("/partners/{partner_id}", response_model=ContentPartnerRead)
def admin_read_content_partner(
    partner_id: int, db: Session = Depends(get_content_db)
) -> ContentPartnerRead:
    partner = db.execute(
        select(ContentPartner)
        .options(selectinload(ContentPartner.category_links))
        .where(ContentPartner.id == partner_id)
    ).scalar_one_or_none()
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content partner not found"
        )
    return _partner_to_read(partner)


@admin_router.patch("/partners/{partner_id}", response_model=ContentPartnerRead)
def admin_update_content_partner(
    partner_id: int,
    payload: ContentPartnerUpdate,
    db: Session = Depends(get_content_db),
) -> ContentPartnerRead:
    partner = db.execute(
        select(ContentPartner)
        .options(selectinload(ContentPartner.category_links))
        .where(ContentPartner.id == partner_id)
    ).scalar_one_or_none()
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content partner not found"
        )
    if payload.city_id is not None:
        _get_or_404(db, ContentCity, payload.city_id, "Content city not found")
    update_data = payload.model_dump(exclude_unset=True, exclude={"category_ids"})
    for field, value in update_data.items():
        setattr(partner, field, value)
    if "category_ids" in payload.model_fields_set and payload.category_ids is not None:
        _replace_partner_categories(db, partner, payload.category_ids)
    db.add(partner)
    _commit_or_400(db, "Content partner could not be updated")
    partner = db.execute(
        select(ContentPartner)
        .options(selectinload(ContentPartner.category_links))
        .where(ContentPartner.id == partner_id)
    ).scalar_one()
    return _partner_to_read(partner)


@admin_router.delete("/partners/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_content_partner(
    partner_id: int, db: Session = Depends(get_content_db)
) -> None:
    partner = db.execute(
        select(ContentPartner)
        .options(
            selectinload(ContentPartner.category_links),
            selectinload(ContentPartner.photos),
            selectinload(ContentPartner.offers).selectinload(ContentOffer.photos),
        )
        .where(ContentPartner.id == partner_id)
    ).scalar_one_or_none()
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content partner not found"
        )
    db.delete(partner)
    _commit_or_400(db, "Content partner could not be deleted")


@admin_router.get(
    "/partners/{partner_id}/offers", response_model=list[ContentOfferRead]
)
def admin_list_content_partner_offers(
    partner_id: int, db: Session = Depends(get_content_db)
) -> list[ContentOffer]:
    _get_or_404(db, ContentPartner, partner_id, "Content partner not found")
    return (
        db.execute(
            select(ContentOffer)
            .where(ContentOffer.partner_id == partner_id)
            .order_by(ContentOffer.sort_order, ContentOffer.title)
        )
        .scalars()
        .all()
    )


@admin_router.post(
    "/partners/{partner_id}/offers",
    response_model=ContentOfferRead,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_content_offer(
    partner_id: int, payload: ContentOfferCreate, db: Session = Depends(get_content_db)
) -> ContentOffer:
    _get_or_404(db, ContentPartner, partner_id, "Content partner not found")
    offer = ContentOffer(partner_id=partner_id, **_offer_payload_to_db_data(payload))
    db.add(offer)
    _commit_or_400(db, "Content offer could not be created")
    db.refresh(offer)
    return offer


@admin_router.get("/offers/{offer_id}", response_model=ContentOfferRead)
def admin_read_content_offer(
    offer_id: int, db: Session = Depends(get_content_db)
) -> ContentOffer:
    return _get_or_404(db, ContentOffer, offer_id, "Content offer not found")


@admin_router.patch("/offers/{offer_id}", response_model=ContentOfferRead)
def admin_update_content_offer(
    offer_id: int, payload: ContentOfferUpdate, db: Session = Depends(get_content_db)
) -> ContentOffer:
    offer = _get_or_404(db, ContentOffer, offer_id, "Content offer not found")
    offer_data = _offer_payload_to_db_data(payload, existing_offer=offer)
    for field, value in offer_data.items():
        setattr(offer, field, value)
    db.add(offer)
    _commit_or_400(db, "Content offer could not be updated")
    db.refresh(offer)
    return offer


@admin_router.get(
    "/partners/{partner_id}/photos", response_model=list[ContentPartnerPhotoRead]
)
def admin_list_content_partner_photos(
    partner_id: int, db: Session = Depends(get_content_db)
) -> list[ContentPartnerPhoto]:
    _get_or_404(db, ContentPartner, partner_id, "Content partner not found")
    return (
        db.execute(
            select(ContentPartnerPhoto)
            .where(ContentPartnerPhoto.partner_id == partner_id)
            .order_by(ContentPartnerPhoto.sort_order, ContentPartnerPhoto.id)
        )
        .scalars()
        .all()
    )


@admin_router.post(
    "/partners/{partner_id}/photos",
    response_model=ContentPartnerPhotoRead,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_content_partner_photo(
    partner_id: int,
    payload: ContentPartnerPhotoCreate,
    db: Session = Depends(get_content_db),
) -> ContentPartnerPhoto:
    _get_or_404(db, ContentPartner, partner_id, "Content partner not found")
    photo = ContentPartnerPhoto(partner_id=partner_id, **payload.model_dump())
    db.add(photo)
    _commit_or_400(db, "Content partner photo could not be created")
    db.refresh(photo)
    return photo


@admin_router.patch(
    "/partner-photos/{photo_id}", response_model=ContentPartnerPhotoRead
)
def admin_update_content_partner_photo(
    photo_id: int,
    payload: ContentPartnerPhotoUpdate,
    db: Session = Depends(get_content_db),
) -> ContentPartnerPhoto:
    photo = _get_or_404(
        db, ContentPartnerPhoto, photo_id, "Content partner photo not found"
    )
    _apply_update(photo, payload)
    db.add(photo)
    _commit_or_400(db, "Content partner photo could not be updated")
    db.refresh(photo)
    return photo


@admin_router.get(
    "/offers/{offer_id}/photos", response_model=list[ContentOfferPhotoRead]
)
def admin_list_content_offer_photos(
    offer_id: int, db: Session = Depends(get_content_db)
) -> list[ContentOfferPhoto]:
    _get_or_404(db, ContentOffer, offer_id, "Content offer not found")
    return (
        db.execute(
            select(ContentOfferPhoto)
            .where(ContentOfferPhoto.offer_id == offer_id)
            .order_by(ContentOfferPhoto.sort_order, ContentOfferPhoto.id)
        )
        .scalars()
        .all()
    )


@admin_router.post(
    "/offers/{offer_id}/photos",
    response_model=ContentOfferPhotoRead,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_content_offer_photo(
    offer_id: int,
    payload: ContentOfferPhotoCreate,
    db: Session = Depends(get_content_db),
) -> ContentOfferPhoto:
    _get_or_404(db, ContentOffer, offer_id, "Content offer not found")
    photo = ContentOfferPhoto(offer_id=offer_id, **payload.model_dump())
    db.add(photo)
    _commit_or_400(db, "Content offer photo could not be created")
    db.refresh(photo)
    return photo


@admin_router.patch("/offer-photos/{photo_id}", response_model=ContentOfferPhotoRead)
def admin_update_content_offer_photo(
    photo_id: int,
    payload: ContentOfferPhotoUpdate,
    db: Session = Depends(get_content_db),
) -> ContentOfferPhoto:
    photo = _get_or_404(
        db, ContentOfferPhoto, photo_id, "Content offer photo not found"
    )
    _apply_update(photo, payload)
    db.add(photo)
    _commit_or_400(db, "Content offer photo could not be updated")
    db.refresh(photo)
    return photo


@admin_router.get("/giveaways", response_model=list[ContentGiveawayRead])
def admin_list_content_giveaways(
    db: Session = Depends(get_content_db),
) -> list[ContentGiveaway]:
    return (
        db.execute(
            select(ContentGiveaway).order_by(
                ContentGiveaway.sort_order, ContentGiveaway.id
            )
        )
        .scalars()
        .all()
    )


@admin_router.post(
    "/giveaways",
    response_model=ContentGiveawayRead,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_content_giveaway(
    payload: ContentGiveawayCreate, db: Session = Depends(get_content_db)
) -> ContentGiveaway:
    giveaway = ContentGiveaway(**payload.model_dump())
    db.add(giveaway)
    _commit_or_400(db, "Content giveaway could not be created")
    db.refresh(giveaway)
    return giveaway


@admin_router.get("/giveaways/{giveaway_id}", response_model=ContentGiveawayRead)
def admin_read_content_giveaway(
    giveaway_id: int, db: Session = Depends(get_content_db)
) -> ContentGiveaway:
    return _get_or_404(db, ContentGiveaway, giveaway_id, "Content giveaway not found")


@admin_router.patch("/giveaways/{giveaway_id}", response_model=ContentGiveawayRead)
def admin_update_content_giveaway(
    giveaway_id: int,
    payload: ContentGiveawayUpdate,
    db: Session = Depends(get_content_db),
) -> ContentGiveaway:
    giveaway = _get_or_404(
        db, ContentGiveaway, giveaway_id, "Content giveaway not found"
    )
    _apply_update(giveaway, payload)
    db.add(giveaway)
    _commit_or_400(db, "Content giveaway could not be updated")
    db.refresh(giveaway)
    return giveaway


@admin_router.get(
    "/giveaways/{giveaway_id}/items", response_model=list[ContentGiveawayItemRead]
)
def admin_list_content_giveaway_items(
    giveaway_id: int, db: Session = Depends(get_content_db)
) -> list[ContentGiveawayItem]:
    _get_or_404(db, ContentGiveaway, giveaway_id, "Content giveaway not found")
    return (
        db.execute(
            select(ContentGiveawayItem)
            .where(ContentGiveawayItem.giveaway_id == giveaway_id)
            .order_by(ContentGiveawayItem.sort_order, ContentGiveawayItem.id)
        )
        .scalars()
        .all()
    )


@admin_router.post(
    "/giveaways/{giveaway_id}/items",
    response_model=ContentGiveawayItemRead,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_content_giveaway_item(
    giveaway_id: int,
    payload: ContentGiveawayItemCreate,
    db: Session = Depends(get_content_db),
) -> ContentGiveawayItem:
    _get_or_404(db, ContentGiveaway, giveaway_id, "Content giveaway not found")
    item = ContentGiveawayItem(giveaway_id=giveaway_id, **payload.model_dump())
    db.add(item)
    _commit_or_400(db, "Content giveaway item could not be created")
    db.refresh(item)
    return item


@admin_router.get("/giveaway-items/{item_id}", response_model=ContentGiveawayItemRead)
def admin_read_content_giveaway_item(
    item_id: int, db: Session = Depends(get_content_db)
) -> ContentGiveawayItem:
    return _get_or_404(
        db, ContentGiveawayItem, item_id, "Content giveaway item not found"
    )


@admin_router.patch("/giveaway-items/{item_id}", response_model=ContentGiveawayItemRead)
def admin_update_content_giveaway_item(
    item_id: int,
    payload: ContentGiveawayItemUpdate,
    db: Session = Depends(get_content_db),
) -> ContentGiveawayItem:
    item = _get_or_404(
        db, ContentGiveawayItem, item_id, "Content giveaway item not found"
    )
    _apply_update(item, payload)
    db.add(item)
    _commit_or_400(db, "Content giveaway item could not be updated")
    db.refresh(item)
    return item


@admin_router.get("/banners", response_model=list[ContentBannerRead])
def admin_list_content_banners(
    db: Session = Depends(get_content_db),
) -> list[ContentBanner]:
    return (
        db.execute(
            select(ContentBanner).order_by(ContentBanner.sort_order, ContentBanner.id)
        )
        .scalars()
        .all()
    )


@admin_router.post(
    "/banners", response_model=ContentBannerRead, status_code=status.HTTP_201_CREATED
)
def admin_create_content_banner(
    payload: ContentBannerCreate, db: Session = Depends(get_content_db)
) -> ContentBanner:
    banner = ContentBanner(**payload.model_dump())
    db.add(banner)
    _commit_or_400(db, "Content banner could not be created")
    db.refresh(banner)
    return banner


@admin_router.patch("/banners/{banner_id}", response_model=ContentBannerRead)
def admin_update_content_banner(
    banner_id: int, payload: ContentBannerUpdate, db: Session = Depends(get_content_db)
) -> ContentBanner:
    banner = _get_or_404(db, ContentBanner, banner_id, "Content banner not found")
    _apply_update(banner, payload)
    db.add(banner)
    _commit_or_400(db, "Content banner could not be updated")
    db.refresh(banner)
    return banner



# WEB backend client admin endpoints consumed by content/admin tools.
from datetime import datetime, timezone
from sqlalchemy import func
from app.db.session import get_db as get_main_db
from app.models.client import ClientProfile, ClientReferral, GiveawayEntry
from app.models.payment import Subscription, SubscriptionStatus
from app.models.user import User
from app.services.referrals import ensure_referral_code, referral_counts, referral_link


def _active_client_subscription(db: Session, client_id: int) -> Subscription | None:
    now = datetime.now(timezone.utc)
    return db.execute(
        select(Subscription)
        .where(Subscription.client_id == client_id, Subscription.status == SubscriptionStatus.active.value, Subscription.starts_at <= now, Subscription.ends_at > now)
        .order_by(Subscription.ends_at.desc(), Subscription.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _admin_client_payload(db: Session, client: ClientProfile) -> dict[str, object]:
    ensure_referral_code(db, client)
    subscription = _active_client_subscription(db, client.id)
    referrals_count, entries_count = referral_counts(db, client.id)
    user = client.user
    return {
        "id": client.id,
        "user_id": client.user_id,
        "telegram_user_id": client.telegram_user_id,
        "first_name": client.telegram_first_name,
        "last_name": client.telegram_last_name,
        "username": client.telegram_username,
        "phone": user.phone if user else None,
        "created_at": client.created_at,
        "updated_at": None,
        "subscription_status": subscription.status if subscription else "inactive",
        "subscription_until": subscription.ends_at if subscription else None,
        "trial_used": client.trial_subscription_used_at is not None,
        "trial_available": client.trial_subscription_used_at is None and subscription is None,
        "referral_code": client.referral_code,
        "referral_link": referral_link(client.referral_code),
        "referrals_count": referrals_count,
        "earned_giveaway_entries_count": entries_count,
    }


@admin_router.get("/clients")
def list_content_admin_clients(db: Session = Depends(get_main_db)) -> list[dict[str, object]]:
    clients = db.execute(select(ClientProfile).options(selectinload(ClientProfile.user)).order_by(ClientProfile.id.asc())).scalars().all()
    payload = [_admin_client_payload(db, client) for client in clients]
    db.commit()
    return payload


@admin_router.get("/clients/{client_id}")
def get_content_admin_client(client_id: int, db: Session = Depends(get_main_db)) -> dict[str, object]:
    client = db.execute(select(ClientProfile).options(selectinload(ClientProfile.user)).where(ClientProfile.id == client_id)).scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    payload = _admin_client_payload(db, client)
    payload["referrals"] = [
        {"id": r.id, "referred_client_id": r.referred_client_id, "reward_entries_count": r.reward_entries_count, "reward_granted_at": r.reward_granted_at, "created_at": r.created_at}
        for r in db.execute(select(ClientReferral).where(ClientReferral.referrer_client_id == client.id).order_by(ClientReferral.created_at.desc())).scalars().all()
    ]
    payload["giveaway_entries"] = [
        {"id": e.id, "client_id": e.client_id, "giveaway_id": e.giveaway_id, "source": e.source, "entries_count": e.entries_count, "related_referral_id": e.related_referral_id, "created_at": e.created_at}
        for e in db.execute(select(GiveawayEntry).where(GiveawayEntry.client_id == client.id).order_by(GiveawayEntry.created_at.desc())).scalars().all()
    ]
    payload["subscriptions"] = [
        {"id": s.id, "status": s.status, "starts_at": s.starts_at, "ends_at": s.ends_at, "source": s.source, "source_payment_request_id": s.source_payment_request_id, "created_at": s.created_at}
        for s in db.execute(select(Subscription).where(Subscription.client_id == client.id).order_by(Subscription.created_at.desc(), Subscription.id.desc())).scalars().all()
    ]
    db.commit()
    return payload


router.include_router(admin_router)
