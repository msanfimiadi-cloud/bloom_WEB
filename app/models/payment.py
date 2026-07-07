from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PaymentRequestStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    approved = "approved"
    rejected = "rejected"


class SubscriptionStatus(str, Enum):
    active = "active"
    expired = "expired"
    paused = "paused"
    blocked = "blocked"


class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=PaymentRequestStatus.pending.value)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    admin_user_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id"), nullable=True)
    access_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    client: Mapped["ClientProfile"] = relationship("ClientProfile", back_populates="payment_requests")
    admin_user: Mapped["AdminUser | None"] = relationship("AdminUser")
    receipts: Mapped[list["PaymentReceipt"]] = relationship("PaymentReceipt", back_populates="payment_request")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="source_payment_request")


class PaymentReceipt(Base):
    __tablename__ = "payment_receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_request_id: Mapped[int] = mapped_column(ForeignKey("payment_requests.id"), nullable=False, index=True)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_via: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    payment_request: Mapped["PaymentRequest"] = relationship("PaymentRequest", back_populates="receipts")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=SubscriptionStatus.active.value)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_payment_request_id: Mapped[int | None] = mapped_column(ForeignKey("payment_requests.id"), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    client: Mapped["ClientProfile"] = relationship("ClientProfile", back_populates="subscriptions")
    source_payment_request: Mapped["PaymentRequest | None"] = relationship(
        "PaymentRequest",
        back_populates="subscriptions",
    )
