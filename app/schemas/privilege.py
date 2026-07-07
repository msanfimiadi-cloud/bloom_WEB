from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PrivilegeSessionCreateRequest(BaseModel):
    partner_id: int
    offer_id: int | None = None
    privilege_id: int | None = None


class PrivilegeSessionPartnerRead(BaseModel):
    id: int
    name: str


class PrivilegeSessionPrivilegeRead(BaseModel):
    id: int
    title: str


class PrivilegeSessionCreateResponse(BaseModel):
    session_id: int
    token: str
    qr_payload: str
    expires_at: datetime
    partner: PrivilegeSessionPartnerRead
    privilege: PrivilegeSessionPrivilegeRead | None = None
    display_code: str | None = None
    status: str
