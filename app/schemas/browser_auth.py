from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class BrowserLoginTokenCreateRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=32)
    provider_user_id: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    photo_url: str | None = Field(default=None, max_length=512)
    referral_code: str | None = Field(default=None, max_length=32)
    source: str | None = Field(default=None, max_length=64)


class BrowserLoginCodeCreateRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=32)
    provider_user_id: str = Field(min_length=1, max_length=255)
    source: str | None = Field(default=None, max_length=64)
    username: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    photo_url: str | None = Field(default=None, max_length=512)
    referral_code: str | None = Field(default=None, max_length=32)
    purpose: str = Field(default="login", max_length=32)


class BrowserLoginCodeInternalResponse(BaseModel):
    login_code: str
    expires_in: int


class BrowserTokenLoginRequest(BaseModel):
    token: str = Field(min_length=1)


class BrowserLoginTokenCreateResponse(BaseModel):
    token: str
    expires_at: datetime
    login_url: str


class BrowserLoginCodeCreateResponse(BaseModel):
    code: str
    expires_at: datetime
    app_url: str


class BrowserLoginCodeRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=32)
    login_code: str | None = Field(default=None, min_length=1, max_length=32)
    provider: str | None = Field(default=None, max_length=32)
    referral_code: str | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def normalize_code(self) -> "BrowserLoginCodeRequest":
        if self.login_code is None and self.code is not None:
            self.login_code = self.code
        if self.code is None and self.login_code is not None:
            self.code = self.login_code
        return self


class ProviderIdentityLinkRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=32)
    login_code: str | None = Field(default=None, min_length=1, max_length=32)
    link_code: str | None = Field(default=None, min_length=1, max_length=32)

    @model_validator(mode="after")
    def normalize_link_code(self) -> "ProviderIdentityLinkRequest":
        if self.login_code is None and self.link_code is not None:
            self.login_code = self.link_code
        if self.link_code is None and self.login_code is not None:
            self.link_code = self.login_code
        return self
