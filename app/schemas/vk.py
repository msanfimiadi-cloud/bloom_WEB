from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.auth import UnifiedUserRead


class VkLinkCodeRead(BaseModel):
    code: str
    status: str
    expires_at: datetime
    ttl_seconds: int


class VkExchangeLinkCodeRequest(BaseModel):
    vk_user_id: str
    code: str


class VkTokenRequest(BaseModel):
    vk_user_id: str


class VkExchangeTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UnifiedUserRead


class VkOnboardClientRequest(BaseModel):
    vk_user_id: str
    source: str | None = "vk"
    selected_city_slug: str | None = None
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None


class VkOnboardClientUserRead(BaseModel):
    id: int
    email: str | None
    phone: str | None
    role: Literal["client"]

    model_config = {"from_attributes": True}


class VkOnboardClientProfileRead(BaseModel):
    id: int
    vk_user_id: str
    selected_city_id: int | None
    full_name: str | None
    source: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class VkOnboardClientResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: VkOnboardClientUserRead
    client: VkOnboardClientProfileRead
    is_new: bool
    password_setup_required: bool = True
    password_setup_url: str | None = None
    login: str | None = None
    password_setup_expires_at: datetime | None = None
    password_setup_ttl_seconds: int | None = None
    web_login_url: str | None = None
    temporary_password: str | None = None
