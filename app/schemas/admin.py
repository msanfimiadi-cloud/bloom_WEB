from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import AliasChoices, BaseModel, Field


class CityRead(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool
    sort_order: int

    model_config = {"from_attributes": True}


class CityCreate(BaseModel):
    name: str
    slug: str
    is_active: bool = True
    sort_order: int = 0


class CityUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class AdminManagedUserRead(BaseModel):
    id: int
    email: str | None
    phone: str | None
    role: str
    is_active: bool
    full_name: str | None = None
    contact_email: str | None = None
    selected_city_id: int | None = None
    selected_city_name: str | None = None
    vk_user_id: str | None = None
    vk_username: str | None = None
    vk_url: str | None = None
    telegram_user_id: str | None = None
    telegram_username: str | None = None
    telegram_url: str | None = None
    trial_status: str | None = None
    paid_subscription_status: str | None = None
    subscription_active_until: datetime | None = None
    active_subscription_type: str | None = None
    display_name: str | None = None
    is_synthetic_email: bool = False

    model_config = {"from_attributes": True}


class AdminManagedUserCreate(BaseModel):
    email: str | None = None
    phone: str | None = None
    password: str
    role: str
    is_active: bool = True


class AdminManagedUserUpdate(BaseModel):
    email: str | None = None
    phone: str | None = None
    password: str | None = None
    role: str | None = None
    is_active: bool | None = None


class CategoryRead(BaseModel):
    id: int
    name: str
    slug: str
    title: str
    is_active: bool = True
    sort_order: int

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str
    slug: str
    is_active: bool = True
    sort_order: int | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class PartnerRead(BaseModel):
    id: int
    city_id: int
    owner_user_id: int | None
    category_slug: str | None
    category_id: int | None = None
    category_name: str | None = None
    category: CategoryRead | None = None
    categories: list[CategoryRead] = Field(default_factory=list)
    category_ids: list[int] = Field(default_factory=list)
    category_slugs: list[str] = Field(default_factory=list)
    name: str
    description: str | None
    address: str | None
    phone: str | None
    website_url: str | None
    social_url: str | None
    instagram_url: str | None
    vk_url: str | None
    telegram_url: str | None
    whatsapp_url: str | None
    map_url: str | None
    working_hours: str | None
    logo_url: str | None
    cover_url: str | None
    is_active: bool
    is_verified: bool
    sort_order: int
    city_name: str | None = None
    owner_email: str | None = None

    model_config = {"from_attributes": True}


class PartnerCreate(BaseModel):
    city_id: int
    owner_user_id: int | None = None
    category_slug: str | None = None
    category_ids: list[int] | None = Field(default=None, validation_alias=AliasChoices("category_ids", "categories"))
    name: str
    description: str | None = None
    address: str | None = None
    phone: str | None = None
    website_url: str | None = None
    social_url: str | None = None
    instagram_url: str | None = None
    vk_url: str | None = None
    telegram_url: str | None = None
    whatsapp_url: str | None = None
    map_url: str | None = None
    working_hours: str | None = None
    logo_url: str | None = None
    cover_url: str | None = None
    is_active: bool = True
    is_verified: bool = False
    sort_order: int = 0


class PartnerUpdate(BaseModel):
    city_id: int | None = None
    owner_user_id: int | None = None
    category_slug: str | None = None
    category_ids: list[int] | None = Field(default=None, validation_alias=AliasChoices("category_ids", "categories"))
    name: str | None = None
    description: str | None = None
    address: str | None = None
    phone: str | None = None
    website_url: str | None = None
    social_url: str | None = None
    instagram_url: str | None = None
    vk_url: str | None = None
    telegram_url: str | None = None
    whatsapp_url: str | None = None
    map_url: str | None = None
    working_hours: str | None = None
    logo_url: str | None = None
    cover_url: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    sort_order: int | None = None


class PartnerOfferRead(BaseModel):
    id: int
    partner_id: int
    title: str
    description: str | None
    benefit_text: str | None
    conditions: str | None
    base_price: Decimal | None
    discount_percent: Decimal | None
    image_url: str | None
    is_active: bool
    sort_order: int
    partner_name: str | None = None

    model_config = {"from_attributes": True}


class PartnerOfferCreate(BaseModel):
    title: str
    description: str | None = None
    benefit_text: str | None = None
    conditions: str | None = None
    base_price: Decimal | None = None
    discount_percent: Decimal | None = None
    image_url: str | None = None
    is_active: bool = True
    sort_order: int = 0


class PartnerOfferUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    benefit_text: str | None = None
    conditions: str | None = None
    base_price: Decimal | None = None
    discount_percent: Decimal | None = None
    image_url: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class PartnerPhotoRead(BaseModel):
    id: int
    partner_id: int
    url: str
    alt_text: str | None
    sort_order: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PartnerPhotoUpdate(BaseModel):
    alt_text: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ContentReviewOfferRead(BaseModel):
    id: int
    partner_id: int
    partner_name: str
    title: str
    benefit_text: str | None
    description: str | None
    image_url: str | None
    created_at: datetime


class ContentReviewPhotoRead(BaseModel):
    id: int
    partner_id: int
    partner_name: str
    url: str
    alt_text: str | None
    sort_order: int
    created_at: datetime


class ContentReviewRead(BaseModel):
    offers: list[ContentReviewOfferRead]
    photos: list[ContentReviewPhotoRead]


class PartnerPhotoUploadResponse(PartnerPhotoRead):
    pass


class AdminVerificationRead(BaseModel):
    id: int
    client_id: int
    client_name: str | None
    partner_id: int
    partner_name: str | None
    city_id: int | None
    city_name: str | None
    offer_id: int | None
    offer_title: str | None
    code: str
    status: str
    source: str | None
    expires_at: datetime
    confirmed_at: datetime | None
    created_at: datetime
    ttl_seconds: int | None


class PartnerQrLinkRead(BaseModel):
    id: int
    partner_id: int
    slug: str
    deep_link_payload: str | None
    target_url: str | None
    is_active: bool
    qr_url: str
    partner_name: str | None = None

    model_config = {"from_attributes": True}


class PartnerQrLinkCreate(BaseModel):
    slug: str | None = None
    deep_link_payload: str | None = None
    target_url: str | None = None
    is_active: bool = True


class PartnerQrLinkUpdate(BaseModel):
    slug: str | None = None
    deep_link_payload: str | None = None
    target_url: str | None = None
    is_active: bool | None = None


class LeadStatsRead(BaseModel):
    partner_id: int
    partner_name: str
    city_id: int | None
    city_name: str | None
    qr_link_id: int | None
    qr_slug: str | None
    total_clicks: int


class AdminDeleteUserResponse(BaseModel):
    ok: bool
    deleted_user_id: int
    deleted: dict[str, int]
