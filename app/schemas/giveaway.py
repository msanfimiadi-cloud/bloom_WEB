from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GiveawayPrizeRead(BaseModel):
    id: int | None = None
    place_number: int
    prize_title: str
    winner_provider: str | None = None
    winner_provider_user_id: str | None = None
    winning_number: str | None = None


class GiveawayRead(BaseModel):
    id: int
    title: str
    description: str | None = None
    is_active: bool = False
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    winners_count: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    prizes: list[GiveawayPrizeRead] = Field(default_factory=list)


class GiveawayPrizeWrite(BaseModel):
    place_number: int
    prize_title: str = ""
    winner_provider: str | None = None
    winner_provider_user_id: str | None = None
    winning_number: str | None = None


class GiveawayWrite(BaseModel):
    title: str
    description: str | None = None
    is_active: bool = False
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    winners_count: int = Field(default=1, ge=0, le=100)
    prizes: list[GiveawayPrizeWrite] = Field(default_factory=list)


class GiveawayNumberRead(BaseModel):
    number: str
    source: str


class PublicGiveawayRead(BaseModel):
    id: int
    title: str
    description: str | None = None
    prizes: list[GiveawayPrizeRead] = Field(default_factory=list)


class GiveawayStateRead(BaseModel):
    has_active_giveaway: bool
    giveaway: PublicGiveawayRead | None = None
    user_numbers_count: int = 0
    numbers: list[GiveawayNumberRead] = Field(default_factory=list)
    guest: bool = False
    message: str | None = None
