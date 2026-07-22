from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class PaymentCreate(BaseModel):
    subscription_plan_id: int
    receipt_email: str
    receipt_phone: str | None = None
    payment_modes: list[Literal["sbp", "card"]] | None = None

    @field_validator("payment_modes")
    @classmethod
    def unique_modes(cls, value):
        return list(dict.fromkeys(value)) if value else value

    @field_validator("receipt_email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or len(normalized) > 320:
            raise ValueError("Valid receipt email is required")
        return normalized


class PaymentRead(BaseModel):
    payment_id: str
    status: str
    provider_status: str | None = None
    amount: Decimal
    currency: str
    payment_url: str | None = None
    expires_at: datetime | None = None
    paid_at: datetime | None = None
    subscription_activated: bool = False


class RefundCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=3, max_length=500)


class SubscriptionPlanRead(BaseModel):
    id: int
    code: str
    name: str
    price: Decimal
    currency: str
    duration_days: int
    is_active: bool
    updated_at: datetime | None = None


class SubscriptionPlanUpdate(BaseModel):
    price: Decimal = Field(gt=0, le=1_000_000, decimal_places=2)


class AdminPaymentRead(BaseModel):
    id: int
    public_id: str
    user_id: int
    client_profile_id: int
    client_name: str | None = None
    telegram_user_id: str | None = None
    vk_user_id: str | None = None
    plan_name: str
    amount: Decimal
    currency: str
    status: str
    provider_status: str | None
    payment_method: str | None
    provider_operation_id: str | None
    payment_link_id: str
    paid_at: datetime | None
    subscription_id: int | None
    refunded_amount: Decimal
    created_at: datetime


class TochkaWebhookPayload(BaseModel):
    webhookType: str
    operationId: str
    paymentLinkId: str
    amount: Decimal
    status: str
    merchantId: str
    customerCode: str | None = None
    paymentType: str | None = None

    model_config = {"extra": "allow"}


class ProviderResult(BaseModel):
    operation_id: str | None = None
    payment_url: str | None = None
    status: str | None = None
    payment_link_id: str | None = None
    raw: dict[str, Any]
