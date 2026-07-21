from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class PartnerBotAccessWrite(BaseModel):
    partner_id: int
    provider: str
    provider_user_id: str
    username: str | None = None
    display_name: str
    is_active: bool = True

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"telegram", "vk"}:
            raise ValueError("provider must be telegram or vk")
        return normalized


class PartnerBotAccessPatch(BaseModel):
    partner_id: int | None = None
    username: str | None = None
    display_name: str | None = None
    is_active: bool | None = None


class PartnerBotAccessRead(BaseModel):
    id: int
    partner_id: int
    partner_name: str
    provider: str
    provider_user_id: str
    username: str | None
    display_name: str
    is_active: bool
    activation_count: int
    last_activity_at: datetime | None
    created_at: datetime


class InternalPartnerIdentityRequest(BaseModel):
    provider: str
    provider_user_id: str


class InternalPartnerCodeCheckRequest(InternalPartnerIdentityRequest):
    code: str = Field(min_length=4, max_length=16)


class InternalPartnerCodeConfirmRequest(InternalPartnerIdentityRequest):
    session_id: int


class InternalPartnerAccessStatusRead(BaseModel):
    is_partner: bool
    partner_id: int | None = None
    partner_name: str | None = None
    employee_name: str | None = None


class InternalPartnerCodeRead(BaseModel):
    session_id: int
    code: str
    partner_name: str
    privilege_title: str | None
    saving_amount: Decimal
    expires_at: datetime


class InternalPartnerCodeConfirmationRead(BaseModel):
    status: str
    saving_amount: Decimal
    giveaway_number_awarded: bool
    giveaway_number: str | None = None


class BloomTaskWrite(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    petals: int = Field(default=3, ge=1, le=100)
    is_active: bool = True
    starts_on: date | None = None
    ends_on: date | None = None
    sort_order: int = 0


class BloomTaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    petals: int | None = Field(default=None, ge=1, le=100)
    is_active: bool | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    sort_order: int | None = None


class BloomTaskRead(BloomTaskWrite):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FlowerTaskStateRead(BaseModel):
    id: int
    title: str
    description: str | None
    petals: int
    completed_today: bool


class FlowerLeaderboardItemRead(BaseModel):
    place: int
    client_id: int
    display_name: str
    petals: int
    is_current_user: bool


class FlowerStateRead(BaseModel):
    month: str
    petals: int
    streak: int
    stage: int
    stage_count: int
    checked_in_today: bool
    days_grown: int
    days_in_month: int
    rank: int | None
    tasks: list[FlowerTaskStateRead]
    leaderboard: list[FlowerLeaderboardItemRead]


class FlowerActionRead(BaseModel):
    awarded: bool
    state: FlowerStateRead


class FlowerLeaderboardSettleRequest(BaseModel):
    month: date
    giveaway_id: int


class FlowerLeaderboardRewardRead(BaseModel):
    client_id: int
    place: int
    entries_count: int
