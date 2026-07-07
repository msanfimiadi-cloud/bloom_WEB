from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import AliasChoices, BaseModel, Field


class ContentBaseRead(BaseModel):
    model_config = {"from_attributes": True}


class ContentUploadRead(BaseModel):
    url: str
    path: str
    filename: str
    content_type: str
    size: int


class ContentBlockCreate(BaseModel):
    key: str
    placement: str = "static_texts"
    locale: str = "ru"
    title: str | None = None
    body: str | None = None
    metadata_json: dict[str, object] | None = None
    is_active: bool = True


class ContentBlockUpdate(BaseModel):
    placement: str | None = None
    locale: str | None = None
    title: str | None = None
    body: str | None = None
    metadata_json: dict[str, object] | None = None
    is_active: bool | None = None


class ContentBlockRead(ContentBaseRead):
    key: str
    placement: str
    locale: str
    title: str | None
    body: str | None
    metadata_json: dict[str, object] | None
    is_active: bool


class ContentCityCreate(BaseModel):
    name: str
    slug: str
    is_active: bool = True
    sort_order: int = 0


class ContentCityUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class ContentCityRead(ContentBaseRead):
    id: int
    name: str
    slug: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ContentCategoryCreate(BaseModel):
    name: str
    slug: str
    is_active: bool = True
    sort_order: int = 0


class ContentCategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class ContentCategoryRead(ContentBaseRead):
    id: int
    name: str
    slug: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ContentPartnerCreate(BaseModel):
    city_id: int
    category_slug: str | None = None
    category_ids: list[int] = Field(default_factory=list)
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


class ContentPartnerUpdate(BaseModel):
    city_id: int | None = None
    category_slug: str | None = None
    category_ids: list[int] | None = None
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


class ContentPartnerRead(ContentBaseRead):
    id: int
    city_id: int
    category_slug: str | None
    category_ids: list[int] = Field(default_factory=list)
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
    created_at: datetime
    updated_at: datetime


class ContentOfferCreate(BaseModel):
    title: str
    description: str | None = None
    benefit_text: str | None = None
    conditions: str | None = Field(
        default=None, validation_alias=AliasChoices("conditions", "terms")
    )
    base_price: Decimal | None = None
    discount_percent: Decimal | None = None
    regular_price: Decimal | None = None
    club_price: Decimal | None = None
    saving: Decimal | None = None
    terms: str | None = None
    image_url: str | None = None
    is_active: bool = True
    sort_order: int = 0


class ContentOfferUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    benefit_text: str | None = None
    conditions: str | None = Field(
        default=None, validation_alias=AliasChoices("conditions", "terms")
    )
    base_price: Decimal | None = None
    discount_percent: Decimal | None = None
    regular_price: Decimal | None = None
    club_price: Decimal | None = None
    saving: Decimal | None = None
    terms: str | None = None
    image_url: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class ContentOfferRead(ContentBaseRead):
    id: int
    partner_id: int
    title: str
    description: str | None
    benefit_text: str | None
    conditions: str | None
    base_price: Decimal | None
    discount_percent: Decimal | None
    regular_price: Decimal | None
    club_price: Decimal | None
    saving: Decimal | None
    terms: str | None
    image_url: str | None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ContentPartnerPhotoCreate(BaseModel):
    url: str
    alt_text: str | None = None
    sort_order: int = 0
    is_active: bool = True


class ContentPartnerPhotoUpdate(BaseModel):
    url: str | None = None
    alt_text: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ContentPartnerPhotoRead(ContentBaseRead):
    id: int
    partner_id: int
    url: str
    alt_text: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ContentOfferPhotoCreate(BaseModel):
    url: str
    alt_text: str | None = None
    is_active: bool = True
    sort_order: int = 0


class ContentOfferPhotoUpdate(BaseModel):
    url: str | None = None
    alt_text: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class ContentOfferPhotoRead(ContentBaseRead):
    id: int
    offer_id: int
    url: str
    alt_text: str | None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ContentGiveawayItemCreate(BaseModel):
    title: str
    description: str | None = None
    image_url: str | None = None
    is_active: bool = True
    sort_order: int = 0


class ContentGiveawayItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class ContentGiveawayItemRead(ContentBaseRead):
    id: int
    giveaway_id: int
    title: str
    description: str | None
    image_url: str | None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ContentGiveawayCreate(BaseModel):
    title: str
    current: str | None = None
    subtitle: str | None = None
    empty_text: str | None = None
    is_active: bool = True
    sort_order: int = 0
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class ContentGiveawayUpdate(BaseModel):
    title: str | None = None
    current: str | None = None
    subtitle: str | None = None
    empty_text: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class ContentGiveawayRead(ContentBaseRead):
    id: int
    title: str
    current: str | None
    subtitle: str | None
    empty_text: str | None
    is_active: bool
    sort_order: int
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ContentGiveawayPublicRead(ContentGiveawayRead):
    items: list[ContentGiveawayItemRead] = Field(default_factory=list)


class ContentBannerCreate(BaseModel):
    title: str
    subtitle: str | None = None
    description: str | None = None
    image_url: str | None = None
    mobile_image_url: str | None = None
    link_url: str | None = None
    cta_text: str | None = None
    placement: str = "landing"
    is_active: bool = True
    sort_order: int = 0
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class ContentBannerUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    description: str | None = None
    image_url: str | None = None
    mobile_image_url: str | None = None
    link_url: str | None = None
    cta_text: str | None = None
    placement: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class ContentBannerRead(ContentBaseRead):
    id: int
    title: str
    subtitle: str | None
    description: str | None
    image_url: str | None
    mobile_image_url: str | None
    link_url: str | None
    cta_text: str | None
    placement: str
    is_active: bool
    sort_order: int
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime
    updated_at: datetime
