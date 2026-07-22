from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentStatus(str, Enum):
    created = "created"
    pending = "pending"
    authorized = "authorized"
    approved = "approved"
    failed = "failed"
    expired = "expired"
    refund_pending = "refund_pending"
    partially_refunded = "partially_refunded"
    refunded = "refunded"
    cancelled = "cancelled"


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB", server_default="RUB")
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("public_id", name="uq_payments_public_id"),
        UniqueConstraint("provider", "provider_operation_id", name="uq_payments_provider_operation"),
        UniqueConstraint("provider", "payment_link_id", name="uq_payments_provider_link"),
        Index("ix_payments_user_id", "user_id"),
        Index("ix_payments_client_profile_id", "client_profile_id"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_created_at", "created_at"),
        Index("ix_payments_paid_at", "paid_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    client_profile_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), nullable=False)
    subscription_plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plans.id"), nullable=False)
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="tochka", server_default="tochka")
    provider_operation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payment_link_id: Mapped[str] = mapped_column(String(45), nullable=False)
    provider_payment_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB", server_default="RUB")
    purpose: Mapped[str] = mapped_column(String(140), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=PaymentStatus.created.value)
    provider_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payment_modes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    payment_type: Mapped[str] = mapped_column(String(32), nullable=False, default="subscription", server_default="subscription")
    recurring: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    subscription_provider_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    customer_code: Mapped[str] = mapped_column(String(64), nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    terminal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    receipt_email: Mapped[str] = mapped_column(String(320), nullable=False)
    receipt_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    provider_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"), server_default="0")
    failure_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan")
    subscription: Mapped["Subscription | None"] = relationship("Subscription")
    events: Mapped[list["PaymentEvent"]] = relationship("PaymentEvent", back_populates="payment", cascade="all, delete-orphan")
    refunds: Mapped[list["PaymentRefund"]] = relationship("PaymentRefund", back_populates="payment", cascade="all, delete-orphan")


class PaymentEvent(Base):
    __tablename__ = "payment_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_payment_events_provider_event"),
        Index("ix_payment_events_payment_id", "payment_id"),
        Index("ix_payment_events_received_at", "received_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="tochka")
    event_type: Mapped[str] = mapped_column(String(96), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(160), nullable=False)
    provider_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    signature_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_body_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False, default="received")
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    payment: Mapped["Payment | None"] = relationship("Payment", back_populates="events")


class PaymentRefund(Base):
    __tablename__ = "payment_refunds"
    __table_args__ = (Index("ix_payment_refunds_payment_id", "payment_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    provider_refund_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    requested_by_admin_id: Mapped[int] = mapped_column(ForeignKey("admin_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    payment: Mapped["Payment"] = relationship("Payment", back_populates="refunds")
