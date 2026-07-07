from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LeadClick(Base):
    __tablename__ = "lead_clicks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int | None] = mapped_column(ForeignKey("partners.id"), nullable=True, index=True)
    qr_link_id: Mapped[int | None] = mapped_column(ForeignKey("partner_qr_links.id"), nullable=True, index=True)
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    ip_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referer: Mapped[str | None] = mapped_column(String(512), nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    partner: Mapped["Partner | None"] = relationship("Partner", back_populates="lead_clicks")
    qr_link: Mapped["PartnerQrLink | None"] = relationship("PartnerQrLink", back_populates="lead_clicks")
    city: Mapped["City | None"] = relationship("City", back_populates="lead_clicks")
