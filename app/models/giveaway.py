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
    telegram_community_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_reward_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    telegram_reward_numbers: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    vk_community_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    vk_group_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vk_reward_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vk_reward_numbers: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

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
        UniqueConstraint("giveaway_id", "source", "source_reference", name="uq_giveaway_numbers_source_reference"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    giveaway_id: Mapped[int] = mapped_column(ForeignKey("giveaways.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="subscription")
    source_reference: Mapped[str | None] = mapped_column(String(96), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deactivation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_platform: Mapped[str | None] = mapped_column(String(32), nullable=True)
    external_community_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    giveaway: Mapped["Giveaway"] = relationship("Giveaway", back_populates="numbers")
