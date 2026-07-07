from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.landing import DEFAULT_GIVEAWAY_EMPTY_TEXT


class GiveawayItem(BaseModel):
    title: str = ""
    description: str | None = None
    is_active: bool = True
    sort_order: int = 0


class LandingSettingsBase(BaseModel):
    members_count_base: int = Field(default=125, ge=0)
    partners_count_display: int = Field(default=18, ge=0)
    partners_count_base: int = Field(default=18, ge=0)
    savings_total: int = Field(default=53500, ge=0)
    savings_total_base: int = Field(default=53500, ge=0)
    giveaway_title: str = "Розыгрыш месяца"
    giveaway_current: str = "Приз месяца"
    giveaway_subtitle: str = "доступно участницам клуба"
    giveaway_empty_text: str = DEFAULT_GIVEAWAY_EMPTY_TEXT
    giveaway_items: list[GiveawayItem] = Field(default_factory=list)


class LandingSettingsRead(LandingSettingsBase):
    id: int
    updated_at: datetime
    members_count: int = 125
    members_count_real: int = 0
    partners_count: int = 18
    partners_count_real: int = 0
    savings_total_display: int = 53500
    savings_total_real: int = 0

    model_config = {"from_attributes": True}


class LandingSettingsUpdate(BaseModel):
    members_count_base: int | None = Field(default=None, ge=0)
    partners_count_display: int | None = Field(default=None, ge=0)
    partners_count_base: int | None = Field(default=None, ge=0)
    savings_total: int | None = Field(default=None, ge=0)
    savings_total_base: int | None = Field(default=None, ge=0)
    giveaway_title: str | None = None
    giveaway_current: str | None = None
    giveaway_subtitle: str | None = None
    giveaway_empty_text: str | None = None
    giveaway_items: list[GiveawayItem] | None = None


class PublicLandingStatsRead(BaseModel):
    members_count: int
    members_count_base: int
    members_count_real: int
    partners_count: int
    partners_count_base: int
    partners_count_real: int
    savings_total: int
    savings_total_base: int
    savings_total_real: int
    giveaway_title: str
    giveaway_current: str
    giveaway_subtitle: str
    giveaway_empty_text: str
    giveaway_items: list[GiveawayItem]
