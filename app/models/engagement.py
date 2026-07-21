from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PartnerBotAccess(Base):
    __tablename__ = "partner_bot_accesses"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_partner_bot_access_provider_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    activation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    partner: Mapped["Partner"] = relationship("Partner")


class PartnerCodeAttempt(Base):
    __tablename__ = "partner_code_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    access_id: Mapped[int] = mapped_column(ForeignKey("partner_bot_accesses.id", ondelete="CASCADE"), nullable=False, index=True)
    was_successful: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)


class BloomDailyTask(Base):
    __tablename__ = "bloom_daily_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    petals: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    starts_on: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    ends_on: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class BloomPetalEvent(Base):
    __tablename__ = "bloom_petal_events"
    __table_args__ = (
        UniqueConstraint("client_id", "idempotency_key", name="uq_bloom_petal_event_client_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("bloom_daily_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    month_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(96), nullable=False)
    petals: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    task: Mapped["BloomDailyTask | None"] = relationship("BloomDailyTask")


class BloomLeaderboardReward(Base):
    __tablename__ = "bloom_leaderboard_rewards"
    __table_args__ = (
        UniqueConstraint("month_start", "client_id", name="uq_bloom_leaderboard_reward_month_client"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    month_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    giveaway_id: Mapped[int] = mapped_column(ForeignKey("giveaways.id", ondelete="CASCADE"), nullable=False, index=True)
    place: Mapped[int] = mapped_column(Integer, nullable=False)
    entries_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
