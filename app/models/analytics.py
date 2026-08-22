from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ClientAnalyticsEvent(Base):
    __tablename__ = "client_analytics_events"
    __table_args__ = (
        Index("ix_client_analytics_events_partner_type_created", "partner_id", "event_type", "created_at"),
        Index("ix_client_analytics_events_offer_type_created", "offer_id", "event_type", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("client_profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    partner_id: Mapped[int] = mapped_column(
        ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    offer_id: Mapped[int | None] = mapped_column(
        ForeignKey("partner_offers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    target: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    client: Mapped["ClientProfile | None"] = relationship("ClientProfile")
    partner: Mapped["Partner"] = relationship("Partner")
    offer: Mapped["PartnerOffer | None"] = relationship("PartnerOffer")
