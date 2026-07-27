from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import bearer_scheme
from app.api.v1.endpoints.partner import _require_partner_from_credentials
from app.api.v1.endpoints.partners import (
    PARTNER_OFFER_TEXT_FIELDS,
    PARTNER_PROFILE_TEXT_FIELDS,
    _get_owned_offer_or_404,
    _get_partner_profile_read,
    _normalize_optional_text,
    _partner_offer_to_read,
    _strip_offer_title,
    _validate_offer_amounts,
)
from app.db.session import get_db
from app.models.partner import PartnerOffer, PartnerPhoto
from app.schemas.partner import (
    PartnerOfferCreate,
    PartnerOfferRead,
    PartnerOfferUpdate,
    PartnerPhotoRead,
    PartnerPhotoUploadResponse,
    PartnerProfileRead,
    PartnerProfileUpdate,
)
from app.services.image_uploads import (
    save_partner_image_upload,
    save_partner_offer_image_upload,
    save_partner_photo_image_upload,
    validate_image_kind,
)

router = APIRouter(prefix="/partner", tags=["partner-content"])


@router.get("/profile", response_model=PartnerProfileRead)
def read_partner_profile(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> PartnerProfileRead:
    partner = _require_partner_from_credentials(db, credentials)
    return _get_partner_profile_read(db, partner.id)


@router.patch("/profile", response_model=PartnerProfileRead)
def update_partner_profile(
    payload: PartnerProfileUpdate,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> PartnerProfileRead:
    partner = _require_partner_from_credentials(db, credentials)
    update_data = payload.model_dump(exclude_unset=True)
    for field in PARTNER_PROFILE_TEXT_FIELDS:
        if field in update_data:
            setattr(partner, field, _normalize_optional_text(update_data[field]))
    db.commit()
    return _get_partner_profile_read(db, partner.id)


@router.post("/profile/images")
async def upload_partner_profile_image(
    kind: str,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    partner = _require_partner_from_credentials(db, credentials)
    normalized_kind = validate_image_kind(kind)
    image_url = await save_partner_image_upload(partner.id, normalized_kind, file)
    setattr(partner, f"{normalized_kind}_url", image_url)
    db.commit()
    return {"url": image_url, "kind": normalized_kind}


@router.delete("/profile/images/{kind}", response_model=PartnerProfileRead)
def clear_partner_profile_image(
    kind: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> PartnerProfileRead:
    partner = _require_partner_from_credentials(db, credentials)
    normalized_kind = validate_image_kind(kind)
    setattr(partner, f"{normalized_kind}_url", None)
    db.commit()
    return _get_partner_profile_read(db, partner.id)


@router.get("/photos", response_model=list[PartnerPhotoRead])
def list_partner_photos(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> list[PartnerPhoto]:
    partner = _require_partner_from_credentials(db, credentials)
    return list(
        db.execute(
            select(PartnerPhoto)
            .where(PartnerPhoto.partner_id == partner.id)
            .order_by(PartnerPhoto.sort_order.asc(), PartnerPhoto.created_at.asc())
        ).scalars().all()
    )


@router.post("/photos", response_model=PartnerPhotoUploadResponse)
async def upload_partner_gallery_photo(
    file: UploadFile = File(...),
    alt_text: str | None = Form(default=None),
    sort_order: int = Form(default=0),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> PartnerPhoto:
    partner = _require_partner_from_credentials(db, credentials)
    photo_url = await save_partner_photo_image_upload(partner.id, file)
    photo = PartnerPhoto(
        partner_id=partner.id,
        url=photo_url,
        alt_text=_normalize_optional_text(alt_text),
        sort_order=sort_order,
        is_active=False,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


@router.delete("/photos/{photo_id}")
def delete_partner_gallery_photo(
    photo_id: int,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    partner = _require_partner_from_credentials(db, credentials)
    photo = db.execute(
        select(PartnerPhoto).where(
            PartnerPhoto.id == photo_id,
            PartnerPhoto.partner_id == partner.id,
        )
    ).scalar_one_or_none()
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner photo not found")
    db.delete(photo)
    db.commit()
    return {"ok": True}


@router.get("/offers", response_model=list[PartnerOfferRead])
def list_partner_offers(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> list[PartnerOfferRead]:
    partner = _require_partner_from_credentials(db, credentials)
    offers = db.execute(
        select(PartnerOffer)
        .where(PartnerOffer.partner_id == partner.id)
        .order_by(PartnerOffer.sort_order.asc(), PartnerOffer.id.asc())
    ).scalars().all()
    return [_partner_offer_to_read(offer) for offer in offers]


@router.post("/offers", response_model=PartnerOfferRead)
def create_partner_offer(
    payload: PartnerOfferCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> PartnerOfferRead:
    partner = _require_partner_from_credentials(db, credentials)
    _validate_offer_amounts(payload.base_price, payload.discount_percent, payload.requires_order_amount)
    offer = PartnerOffer(
        partner_id=partner.id,
        title=_strip_offer_title(payload.title),
        base_price=None if payload.requires_order_amount else payload.base_price,
        discount_percent=payload.discount_percent,
        requires_order_amount=payload.requires_order_amount,
        is_active=False,
        sort_order=payload.sort_order,
    )
    for field in PARTNER_OFFER_TEXT_FIELDS:
        setattr(offer, field, _normalize_optional_text(getattr(payload, field)))
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return _partner_offer_to_read(offer)


@router.patch("/offers/{offer_id}", response_model=PartnerOfferRead)
def update_partner_offer(
    offer_id: int,
    payload: PartnerOfferUpdate,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> PartnerOfferRead:
    partner = _require_partner_from_credentials(db, credentials)
    offer = _get_owned_offer_or_404(db, partner.id, offer_id)
    update_data = payload.model_dump(exclude_unset=True)
    requires_order_amount = update_data.get("requires_order_amount", offer.requires_order_amount)
    base_price = update_data.get("base_price", offer.base_price)
    discount_percent = update_data.get("discount_percent", offer.discount_percent)
    _validate_offer_amounts(base_price, discount_percent, requires_order_amount)

    if "title" in update_data:
        offer.title = _strip_offer_title(update_data["title"])
    for field in PARTNER_OFFER_TEXT_FIELDS:
        if field in update_data:
            setattr(offer, field, _normalize_optional_text(update_data[field]))
    for field in ("base_price", "discount_percent", "requires_order_amount", "sort_order"):
        if field in update_data:
            setattr(offer, field, update_data[field])
    if requires_order_amount:
        offer.base_price = None
    # Any partner-authored change is reviewed before it becomes visible again.
    offer.is_active = False
    db.commit()
    db.refresh(offer)
    return _partner_offer_to_read(offer)


@router.post("/offers/{offer_id}/image")
async def upload_partner_offer_image(
    offer_id: int,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    partner = _require_partner_from_credentials(db, credentials)
    offer = _get_owned_offer_or_404(db, partner.id, offer_id)
    image_url = await save_partner_offer_image_upload(partner.id, offer.id, file)
    offer.image_url = image_url
    offer.is_active = False
    db.commit()
    return {"url": image_url}


@router.delete("/offers/{offer_id}/image", response_model=PartnerOfferRead)
def clear_partner_offer_image(
    offer_id: int,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> PartnerOfferRead:
    partner = _require_partner_from_credentials(db, credentials)
    offer = _get_owned_offer_or_404(db, partner.id, offer_id)
    offer.image_url = None
    offer.is_active = False
    db.commit()
    db.refresh(offer)
    return _partner_offer_to_read(offer)

