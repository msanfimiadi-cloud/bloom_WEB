from __future__ import annotations

from datetime import datetime
from enum import Enum

from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PrivilegeVerificationStatus(str, Enum):
    pending = "pending"
    active = "active"
    confirmed = "confirmed"
    expired = "expired"
    cancelled = "cancelled"


class PrivilegeVerificationSession(Base):
    __tablename__ = "privilege_verification_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), nullable=False, index=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id"), nullable=False, index=True)
    offer_id: Mapped[int | None] = mapped_column(ForeignKey("partner_offers.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    token: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=PrivilegeVerificationStatus.active.value)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_by_partner_id: Mapped[int | None] = mapped_column(ForeignKey("partners.id"), nullable=True, index=True)
    saving_base_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    saving_final_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    saving_discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    saving_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    saving_partner_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    saving_offer_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    saving_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    client: Mapped["ClientProfile"] = relationship("ClientProfile", back_populates="verification_sessions")
    partner: Mapped["Partner"] = relationship("Partner", back_populates="verification_sessions", foreign_keys=[partner_id])
    offer: Mapped["PartnerOffer | None"] = relationship("PartnerOffer", back_populates="verification_sessions")
    confirmed_by_partner: Mapped["Partner | None"] = relationship("Partner", foreign_keys=[confirmed_by_partner_id])
