from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Table, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

partner_categories = Table(
    "partner_categories",
    Base.metadata,
    Column("partner_id", ForeignKey("partners.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("partner_id", "category_id", name="uq_partner_categories_partner_category"),
)


class Partner(Base):
    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False, index=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    city: Mapped["City"] = relationship("City", back_populates="partners")
    owner_user: Mapped["User | None"] = relationship("User", back_populates="owned_partners")
    offers: Mapped[list["PartnerOffer"]] = relationship("PartnerOffer", back_populates="partner")
    photos: Mapped[list["PartnerPhoto"]] = relationship("PartnerPhoto", back_populates="partner")
    qr_links: Mapped[list["PartnerQrLink"]] = relationship("PartnerQrLink", back_populates="partner")
    lead_clicks: Mapped[list["LeadClick"]] = relationship("LeadClick", back_populates="partner")
    verification_sessions: Mapped[list["PrivilegeVerificationSession"]] = relationship(
        "PrivilegeVerificationSession",
        back_populates="partner",
        foreign_keys="PrivilegeVerificationSession.partner_id",
    )
    categories: Mapped[list["Category"]] = relationship(
        "Category",
        secondary=partner_categories,
        back_populates="partners",
    )


class PartnerPhoto(Base):
    __tablename__ = "partner_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    partner: Mapped["Partner"] = relationship("Partner", back_populates="photos")


class PartnerOffer(Base):
    __tablename__ = "partner_offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefit_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    partner: Mapped["Partner"] = relationship("Partner", back_populates="offers")
    photos: Mapped[list["OfferPhoto"]] = relationship("OfferPhoto", back_populates="offer")
    verification_sessions: Mapped[list["PrivilegeVerificationSession"]] = relationship(
        "PrivilegeVerificationSession",
        back_populates="offer",
    )


class OfferPhoto(Base):
    __tablename__ = "offer_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("partner_offers.id"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    offer: Mapped["PartnerOffer"] = relationship("PartnerOffer", back_populates="photos")


class PartnerQrLink(Base):
    __tablename__ = "partner_qr_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    deep_link_payload: Mapped[str | None] = mapped_column(String(512), nullable=True)
    target_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    partner: Mapped["Partner"] = relationship("Partner", back_populates="qr_links")
    lead_clicks: Mapped[list["LeadClick"]] = relationship("LeadClick", back_populates="qr_link")
