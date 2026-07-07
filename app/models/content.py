from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.content_base import ContentBase


class ContentCity(ContentBase):
    __tablename__ = "content_cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    partners: Mapped[list["ContentPartner"]] = relationship("ContentPartner", back_populates="city")


class ContentCategory(ContentBase):
    __tablename__ = "content_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    partner_links: Mapped[list["ContentPartnerCategory"]] = relationship(
        "ContentPartnerCategory", back_populates="category"
    )
    partners: Mapped[list["ContentPartner"]] = relationship(
        "ContentPartner", secondary="content_partner_categories", back_populates="categories", viewonly=True
    )

    @property
    def title(self) -> str:
        return self.name


class ContentPartner(ContentBase):
    __tablename__ = "content_partners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("content_cities.id"), nullable=False, index=True)
    category_slug: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    social_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    vk_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    telegram_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    whatsapp_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    map_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    working_hours: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    city: Mapped["ContentCity"] = relationship("ContentCity", back_populates="partners")
    category_links: Mapped[list["ContentPartnerCategory"]] = relationship(
        "ContentPartnerCategory", back_populates="partner", cascade="all, delete-orphan"
    )
    categories: Mapped[list["ContentCategory"]] = relationship(
        "ContentCategory", secondary="content_partner_categories", back_populates="partners", viewonly=True
    )
    photos: Mapped[list["ContentPartnerPhoto"]] = relationship(
        "ContentPartnerPhoto", back_populates="partner", cascade="all, delete-orphan"
    )
    offers: Mapped[list["ContentOffer"]] = relationship(
        "ContentOffer", back_populates="partner", cascade="all, delete-orphan"
    )


class ContentPartnerCategory(ContentBase):
    __tablename__ = "content_partner_categories"
    __table_args__ = (UniqueConstraint("partner_id", "category_id", name="uq_content_partner_categories_pair"),)

    partner_id: Mapped[int] = mapped_column(ForeignKey("content_partners.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("content_categories.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    partner: Mapped["ContentPartner"] = relationship("ContentPartner", back_populates="category_links")
    category: Mapped["ContentCategory"] = relationship("ContentCategory", back_populates="partner_links")


class ContentPartnerPhoto(ContentBase):
    __tablename__ = "content_partner_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("content_partners.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    partner: Mapped["ContentPartner"] = relationship("ContentPartner", back_populates="photos")


class ContentOffer(ContentBase):
    __tablename__ = "content_offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("content_partners.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefit_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


    @property
    def regular_price(self) -> Decimal | None:
        return self.base_price

    @property
    def saving(self) -> Decimal | None:
        if self.base_price is None or self.discount_percent is None:
            return None
        return (
            self.base_price * self.discount_percent / Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def club_price(self) -> Decimal | None:
        if self.base_price is None:
            return None
        saving = self.saving
        if saving is None:
            return None
        return (self.base_price - saving).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @property
    def terms(self) -> str | None:
        return self.conditions

    partner: Mapped["ContentPartner"] = relationship("ContentPartner", back_populates="offers")
    photos: Mapped[list["ContentOfferPhoto"]] = relationship(
        "ContentOfferPhoto", back_populates="offer", cascade="all, delete-orphan"
    )


class ContentOfferPhoto(ContentBase):
    __tablename__ = "content_offer_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("content_offers.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    offer: Mapped["ContentOffer"] = relationship("ContentOffer", back_populates="photos")


class ContentGiveaway(ContentBase):
    __tablename__ = "content_giveaways"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    current: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subtitle: Mapped[str | None] = mapped_column(String(512), nullable=True)
    empty_text: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["ContentGiveawayItem"]] = relationship("ContentGiveawayItem", back_populates="giveaway")


class ContentGiveawayItem(ContentBase):
    __tablename__ = "content_giveaway_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    giveaway_id: Mapped[int] = mapped_column(ForeignKey("content_giveaways.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    giveaway: Mapped["ContentGiveaway"] = relationship("ContentGiveaway", back_populates="items")


class ContentBanner(ContentBase):
    __tablename__ = "content_banners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mobile_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    link_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cta_text: Mapped[str | None] = mapped_column(String(120), nullable=True)
    placement: Mapped[str] = mapped_column(String(120), nullable=False, default="landing")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ContentBlock(ContentBase):
    __tablename__ = "content_blocks"
    __table_args__ = (UniqueConstraint("key", "locale", name="uq_content_blocks_key_locale"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    placement: Mapped[str] = mapped_column(String(120), nullable=False, default="static_texts", index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="ru", index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
