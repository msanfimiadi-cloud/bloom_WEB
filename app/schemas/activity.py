from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ActivityItemRead(BaseModel):
    id: str
    event_type: str
    occurred_at: datetime
    title: str
    description: str | None = None
    partner_id: int | None = None
    partner_name: str | None = None
    client_id: int | None = None
    client_name: str | None = None
    offer_id: int | None = None
    offer_title: str | None = None
    qr_link_id: int | None = None
    qr_slug: str | None = None
    source: str | None = None
    status: str | None = None


class ActivityFeedRead(BaseModel):
    items: list[ActivityItemRead] = Field(default_factory=list)
