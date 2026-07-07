from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


class AuthPayload(TypedDict, total=False):
    data: dict[str, Any]


class LoginRequest(BaseModel):
    email: str
    password: str


class AdminUserRead(BaseModel):
    id: int
    email: str
    role: str
    legacy_content_write_enabled: bool = True

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AdminUserRead


class UserLoginRequest(BaseModel):
    login: str
    password: str


class UnifiedUserRead(BaseModel):
    id: int
    email: str | None
    phone: str | None
    role: Literal["admin", "partner", "client"]

    model_config = {"from_attributes": True}


class UnifiedTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UnifiedUserRead


class VkMiniAppLoginRequest(BaseModel):
    launch_params: str | None = None
    launchParams: str | None = None
    params: dict[str, str] | None = None


class TelegramMiniAppLoginRequest(BaseModel):
    init_data: str | None = None


class TelegramMiniAppUserRead(BaseModel):
    id: int
    telegram_user_id: str | None
    first_name: str | None
    last_name: str | None
    username: str | None
    photo_url: str | None
    role: Literal["client"]


class TelegramMiniAppSubscriptionRead(BaseModel):
    is_active: bool = False
    expires_at: Any | None = None


class TelegramMiniAppClientRead(BaseModel):
    id: int
    user_id: int
    telegram_user_id: str | None
    telegram_username: str | None
    telegram_first_name: str | None
    telegram_last_name: str | None
    telegram_photo_url: str | None
    full_name: str | None
    selected_city_id: int | None
    source: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class TelegramMiniAppLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: TelegramMiniAppUserRead
    client: TelegramMiniAppClientRead
    subscription: TelegramMiniAppSubscriptionRead


class VkMiniAppLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UnifiedUserRead
    client: "VkMiniAppClientRead"
    generated_account: bool = False
    profile_completed: bool = False
    missing_fields: list[str] = Field(default_factory=list)


class VkMiniAppClientRead(BaseModel):
    id: int
    user_id: int
    vk_user_id: str | None
    full_name: str | None
    selected_city_id: int | None
    source: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class PasswordSetupCompleteRequest(BaseModel):
    token: str
    password: str
    password_confirm: str | None = None


class PasswordSetupCompleteResponse(BaseModel):
    ok: bool
    login: str | None = None
    message: str | None = None
