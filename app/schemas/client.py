from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ClientProfileRead(BaseModel):
    id: int
    user_id: int
    email: str | None
    phone: str | None
    contact_email: str | None
    full_name: str | None
    selected_city_id: int | None
    selected_city_name: str | None
    city: str | None = None
    custom_city: str | None = None
    city_name: str | None = None
    vk_user_id: str | None
    site_login: str | None = None
    site_password_masked: str | None = None
    site_password_available: bool = False
    source: str | None
    is_active: bool
    telegram_user_id: str | None = None
    telegram_username: str | None = None
    telegram_first_name: str | None = None
    telegram_last_name: str | None = None
    trial_used: bool = False
    trial_available: bool = False
    referral_code: str | None = None
    referral_link: str | None = None

    model_config = {"from_attributes": True}


class ClientSiteCredentialsRead(BaseModel):
    site_login: str
    site_password: str


class ClientProfileUpdate(BaseModel):
    name: str | None = None
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    contact_email: str | None = None
    city_id: int | None = None
    city_slug: str | None = None
    selected_city_id: int | None = None
    city: str | None = None
    custom_city: str | None = None


class ClientCityResponse(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class SubscriptionRead(BaseModel):
    id: int | None = None
    client_id: int | None = None
    status: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    source_payment_request_id: int | None = None
    source: str | None = None
    type: str | None = None
    is_active: bool
    subscription_active: bool | None = None
    expires_at: datetime | None = None
    end_date: datetime | None = None
    subscription_until: datetime | None = None
    trial_available: bool = False
    trial_used: bool = False
    amount: Decimal = Decimal("349.00")

    model_config = {"from_attributes": True}


class ClientLinkingStatusRead(BaseModel):
    has_vk_identity: bool
    has_telegram_identity: bool
    has_site_login: bool
    is_linked: bool
    can_start_linking: bool


class ClientLinkingStartRequest(BaseModel):
    identifier: str


class ClientLinkingStartResponse(BaseModel):
    status: str
    challenge_id: str | None = None
    masked_identifier: str | None = None
    expires_in_seconds: int | None = None
    dev_code: str | None = None


class ClientLinkingConfirmRequest(BaseModel):
    challenge_id: str
    code: str


class ClientLinkingConfirmResponse(BaseModel):
    status: str
    access_token: str | None = None
    token_type: str = "bearer"
    client: ClientProfileRead | None = None
    subscription: SubscriptionRead | None = None
    detail: str | None = None


class ClientPartnerPhotoRead(BaseModel):
    id: int
    url: str
    alt_text: str | None
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ClientPartnerCatalogItem(BaseModel):
    id: int
    city_id: int
    city_name: str | None
    category_id: int | None = None
    category_name: str | None = None
    category_slug: str | None
    category: "ClientPartnerCategoryRead | None" = None
    categories: list["ClientPartnerCategoryRead"] = Field(default_factory=list)
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
    image_url: str | None = None
    photo_url: str | None = None
    is_verified: bool
    photos: list[ClientPartnerPhotoRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ClientPartnerCategoryRead(BaseModel):
    id: int
    name: str
    slug: str


class ClientCreateVerificationRequest(BaseModel):
    offer_id: int | None = None
    privilege_id: int | None = None
    source: str | None = "web"


class ClientVerificationRead(BaseModel):
    id: int
    session_id: int | None = None
    client_id: int
    partner_id: int
    partner_name: str | None
    offer_id: int | None
    offer_title: str | None
    code: str
    display_code: str | None = None
    token: str | None = None
    qr_payload: str | None = None
    status: str
    source: str | None
    expires_at: datetime
    confirmed_at: datetime | None
    created_at: datetime
    ttl_seconds: int | None
    regular_price: Decimal | None = None
    club_price: Decimal | None = None
    base_price: Decimal | None = None
    final_price: Decimal | None = None
    discount_percent: Decimal | None = None
    saving_amount: Decimal | None = None
    subscription_required: bool = False


class ClientPartnerOfferRead(BaseModel):
    id: int
    partner_id: int
    title: str
    description: str | None
    benefit_text: str | None
    conditions: str | None
    base_price: Decimal | None
    discount_percent: Decimal | None
    image_url: str | None
    photo_url: str | None = None
    photos: list["ClientOfferPhotoRead"] = Field(default_factory=list)
    sort_order: int

    model_config = {"from_attributes": True}


class ClientOfferPhotoRead(BaseModel):
    id: int
    url: str
    alt_text: str | None
    sort_order: int


class ClientSavingsItemRead(BaseModel):
    id: int
    used_at: datetime | None
    partner_id: int
    partner_name: str | None
    offer_id: int | None
    offer_title: str | None
    base_price: Decimal | None
    final_price: Decimal | None
    discount_percent: Decimal | None
    saving_amount: Decimal


class ClientSavingsPeriodRead(BaseModel):
    from_date: str | None
    to_date: str | None


class ClientSavingsRead(BaseModel):
    total_saving_amount: Decimal
    currency: str = "RUB"
    period: ClientSavingsPeriodRead
    items: list[ClientSavingsItemRead]


class ClientReferralSummaryItem(BaseModel):
    id: int
    referred_client_id: int
    first_name: str | None = None
    username: str | None = None
    created_at: datetime
    reward_entries_count: int


class ClientReferralSummaryRead(BaseModel):
    referral_code: str
    referral_link: str
    referrals_count: int
    activated_referrals_count: int = 0
    earned_entries_count: int
    earned_giveaway_entries_count: int = 0
    reward_entries_per_referral: int = 5
    referrals: list[ClientReferralSummaryItem] = Field(default_factory=list)
