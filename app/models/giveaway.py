from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Giveaway(Base):
    __tablename__ = "giveaways"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    winners_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    prizes: Mapped[list["GiveawayPrize"]] = relationship("GiveawayPrize", back_populates="giveaway", cascade="all, delete-orphan")
    numbers: Mapped[list["GiveawayNumber"]] = relationship("GiveawayNumber", back_populates="giveaway", cascade="all, delete-orphan")


class GiveawayPrize(Base):
    __tablename__ = "giveaway_prizes"
    __table_args__ = (UniqueConstraint("giveaway_id", "place_number", name="uq_giveaway_prizes_giveaway_place"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    giveaway_id: Mapped[int] = mapped_column(ForeignKey("giveaways.id", ondelete="CASCADE"), nullable=False, index=True)
    place_number: Mapped[int] = mapped_column(Integer, nullable=False)
    prize_title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    winner_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    winner_provider_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    winning_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    giveaway: Mapped["Giveaway"] = relationship("Giveaway", back_populates="prizes")


class GiveawayNumber(Base):
    __tablename__ = "giveaway_numbers"
    __table_args__ = (
        UniqueConstraint("giveaway_id", "number", name="uq_giveaway_numbers_giveaway_number"),
        UniqueConstraint("giveaway_id", "client_id", "number", name="uq_giveaway_numbers_client_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    giveaway_id: Mapped[int] = mapped_column(ForeignKey("giveaways.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="subscription")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    giveaway: Mapped["Giveaway"] = relationship("Giveaway", back_populates="numbers")
