from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.services.giveaways import GIVEAWAY_DRAW_DAY, is_giveaway_draw_day


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
    telegram_community_url: str | None = None
    telegram_chat_id: str | None = None
    telegram_reward_enabled: bool = False
    telegram_reward_numbers: int = 1
    vk_community_url: str | None = None
    vk_group_id: str | None = None
    vk_reward_enabled: bool = False
    vk_reward_numbers: int = 1


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

    @model_validator(mode="after")
    def validate_draw_schedule(self) -> "GiveawayWrite":
        if self.ends_at is not None and not is_giveaway_draw_day(self.ends_at):
            raise ValueError(f"Розыгрыш должен проводиться {GIVEAWAY_DRAW_DAY}-го числа месяца")
        if self.starts_at is not None and self.ends_at is not None and self.starts_at >= self.ends_at:
            raise ValueError("Дата начала розыгрыша должна быть раньше даты проведения")
        return self


class SocialGiveawaySettingsWrite(BaseModel):
    telegram_community_url: str | None = None
    telegram_chat_id: str | None = None
    telegram_reward_enabled: bool = False
    telegram_reward_numbers: int = Field(default=1, ge=1, le=1)
    vk_community_url: str | None = None
    vk_group_id: str | None = None
    vk_reward_enabled: bool = False
    vk_reward_numbers: int = Field(default=1, ge=1, le=1)

    @model_validator(mode="after")
    def validate_social_reward_requirements(self) -> "SocialGiveawaySettingsWrite":
        if self.telegram_reward_enabled and not (
            (self.telegram_community_url or "").strip()
            and (self.telegram_chat_id or "").strip()
        ):
            raise ValueError("Для номера за Telegram заполните ссылку на канал и Chat ID")
        if self.vk_reward_enabled and not (
            (self.vk_community_url or "").strip()
            and (self.vk_group_id or "").strip()
        ):
            raise ValueError("Для номера за VK заполните ссылку на сообщество и ID группы")
        return self


class GiveawayNumberRead(BaseModel):
    number: str
    source: str
    status: str = "active"
    is_active: bool = True


class SocialTaskRead(BaseModel):
    enabled: bool = False
    community_url: str | None = None
    reward_numbers: int = 1


class SocialSubscriptionCheckRead(BaseModel):
    platform: str
    subscribed: bool
    entry_active: bool
    entry_number: str | None = None
    message: str
    status: str = "ok"


class PublicGiveawayRead(BaseModel):
    id: int
    title: str
    description: str | None = None
    draws_at: datetime | None = None
    prizes: list[GiveawayPrizeRead] = Field(default_factory=list)


class GiveawayStateRead(BaseModel):
    has_active_giveaway: bool
    giveaway: PublicGiveawayRead | None = None
    user_numbers_count: int = 0
    numbers: list[GiveawayNumberRead] = Field(default_factory=list)
    guest: bool = False
    message: str | None = None
    social_tasks: dict[str, SocialTaskRead] = Field(default_factory=dict)
