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


class BloomGardenSettingsPatch(BaseModel):
    placement_mode: str | None = None
    manual_position: str | None = None
    daily_petals: int | None = Field(default=None, ge=1, le=20)

    @field_validator("placement_mode")
    @classmethod
    def validate_mode(cls, value: str | None) -> str | None:
        if value is not None and value not in {"random", "manual"}:
            raise ValueError("placement_mode must be random or manual")
        return value

    @field_validator("manual_position")
    @classmethod
    def validate_position(cls, value: str | None) -> str | None:
        allowed = {"top_left", "top_right", "middle_left", "middle_right", "bottom_left", "bottom_right"}
        if value is not None and value not in allowed:
            raise ValueError("unknown petal position")
        return value


class BloomGardenSettingsRead(BaseModel):
    placement_mode: str
    manual_position: str
    daily_petals: int


class BloomSpecialOptionRead(BaseModel):
    id: int
    label: str
    sort_order: int
    model_config = {"from_attributes": True}


class BloomSpecialQuestionRead(BaseModel):
    id: int
    prompt: str
    sort_order: int
    options: list[BloomSpecialOptionRead]
    model_config = {"from_attributes": True}


class BloomSpecialTaskWrite(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    petals: int = Field(default=5, ge=1, le=100)
    starts_on: date
    ends_on: date
    is_active: bool = True


class BloomSpecialTaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    petals: int | None = Field(default=None, ge=1, le=100)
    starts_on: date | None = None
    ends_on: date | None = None
    is_active: bool | None = None


class BloomSpecialQuestionWrite(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    options: list[str] = Field(min_length=2, max_length=10)

    @field_validator("options")
    @classmethod
    def validate_options(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values if value.strip()]
        if len(normalized) < 2:
            raise ValueError("at least two non-empty options are required")
        return normalized


class BloomSpecialTaskRead(BloomSpecialTaskWrite):
    id: int
    created_at: datetime
    questions: list[BloomSpecialQuestionRead]
    submissions_count: int = 0
    model_config = {"from_attributes": True}


class BloomSpecialAnswerWrite(BaseModel):
    question_id: int
    option_id: int


class BloomSpecialSubmissionWrite(BaseModel):
    answers: list[BloomSpecialAnswerWrite]


class BloomSpecialTaskClientRead(BaseModel):
    id: int
    title: str
    description: str | None
    petals: int
    starts_on: date
    ends_on: date
    completed: bool
    questions: list[BloomSpecialQuestionRead]


class BloomSpecialOptionAnalyticsRead(BaseModel):
    option_id: int
    label: str
    count: int
    percent: float


class BloomSpecialQuestionAnalyticsRead(BaseModel):
    question_id: int
    prompt: str
    options: list[BloomSpecialOptionAnalyticsRead]


class BloomSpecialSubmissionRead(BaseModel):
    client_id: int
    full_name: str | None
    email: str | None
    phone: str | None
    telegram_username: str | None
    vk_username: str | None
    completed_at: datetime
    answers: list[str]


class BloomSpecialAnalyticsRead(BaseModel):
    task_id: int
    title: str
    submissions_count: int
    questions: list[BloomSpecialQuestionAnalyticsRead]
    submissions: list[BloomSpecialSubmissionRead]


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
    petal_position: str
    petal_reward: int
    days_grown: int
    days_in_month: int
    rank: int | None
    tasks: list[FlowerTaskStateRead]
    special_task: BloomSpecialTaskClientRead | None = None
    leaderboard: list[FlowerLeaderboardItemRead]


class FlowerActionRead(BaseModel):
    awarded: bool
    state: FlowerStateRead


class AdminPetalAwardWrite(BaseModel):
    user_id: int = Field(gt=0)
    petals: int = Field(ge=1, le=1000)
    note: str = Field(min_length=2, max_length=1000)

    @field_validator("note", mode="before")
    @classmethod
    def normalize_note(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AdminPetalAwardRead(BaseModel):
    event_id: int
    user_id: int
    client_id: int
    petals: int
    total_petals: int
    note: str
    created_at: datetime


class FlowerLeaderboardSettleRequest(BaseModel):
    month: date
    giveaway_id: int


class FlowerLeaderboardRewardRead(BaseModel):
    client_id: int
    place: int
    entries_count: int
