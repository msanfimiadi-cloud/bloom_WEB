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


class BloomGardenSettings(Base):
    __tablename__ = "bloom_garden_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    placement_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="random")
    manual_position: Mapped[str] = mapped_column(String(32), nullable=False, default="top_right")
    daily_petals: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class BloomSpecialTask(Base):
    __tablename__ = "bloom_special_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    petals: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    questions: Mapped[list["BloomSpecialQuestion"]] = relationship(
        "BloomSpecialQuestion", back_populates="task", cascade="all, delete-orphan", order_by="BloomSpecialQuestion.sort_order"
    )


class BloomSpecialQuestion(Base):
    __tablename__ = "bloom_special_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("bloom_special_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    task: Mapped["BloomSpecialTask"] = relationship("BloomSpecialTask", back_populates="questions")
    options: Mapped[list["BloomSpecialOption"]] = relationship(
        "BloomSpecialOption", back_populates="question", cascade="all, delete-orphan", order_by="BloomSpecialOption.sort_order"
    )


class BloomSpecialOption(Base):
    __tablename__ = "bloom_special_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("bloom_special_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    question: Mapped["BloomSpecialQuestion"] = relationship("BloomSpecialQuestion", back_populates="options")


class BloomSpecialSubmission(Base):
    __tablename__ = "bloom_special_submissions"
    __table_args__ = (UniqueConstraint("task_id", "client_id", name="uq_bloom_special_submission_task_client"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("bloom_special_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    answers: Mapped[list["BloomSpecialAnswer"]] = relationship("BloomSpecialAnswer", cascade="all, delete-orphan")


class BloomSpecialAnswer(Base):
    __tablename__ = "bloom_special_answers"
    __table_args__ = (UniqueConstraint("submission_id", "question_id", name="uq_bloom_special_answer_submission_question"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("bloom_special_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("bloom_special_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("bloom_special_options.id", ondelete="RESTRICT"), nullable=False, index=True)


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
    awarded_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
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
