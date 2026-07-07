from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, TypedDict

from pydantic import BaseModel, Field


class PaymentPayload(TypedDict, total=False):
    data: dict[str, Any]


class PaymentReceiptCreate(BaseModel):
    file_url: str
    uploaded_via: str = "web"


class PaymentReceiptRead(BaseModel):
    id: int
    payment_request_id: int
    file_url: str
    uploaded_via: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentRequestCreate(BaseModel):
    amount: Decimal | None = Decimal("349.00")
    source: str = "web"
    comment: str | None = None


class PaymentRequestMarkPaid(BaseModel):
    comment: str | None = None


class PaymentRequestApprove(BaseModel):
    access_days: int | None = Field(default=None, gt=0)
    access_until: datetime | None = None
    comment: str | None = None


class PaymentRequestReject(BaseModel):
    comment: str | None = None


class PaymentRequestRead(BaseModel):
    id: int
    client_id: int
    amount: Decimal
    status: str
    source: str | None
    comment: str | None
    created_at: datetime
    updated_at: datetime | None
    approved_at: datetime | None
    rejected_at: datetime | None
    admin_user_id: int | None
    access_until: datetime | None
    receipts: list[PaymentReceiptRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class AdminPaymentRequestRead(PaymentRequestRead):
    client_name: str | None = None
    client_full_name: str | None = None
    client_user_id: int | None = None
    client_vk_user_id: str | None = None
    user_id: int | None = None
    user_email: str | None = None
    user_login: str | None = None
    user_phone: str | None = None
    full_name: str | None = None
    contact_email: str | None = None
    selected_city_name: str | None = None
    vk_user_id: str | None = None
    vk_url: str | None = None
    display_name: str | None = None
    is_synthetic_email: bool = False
