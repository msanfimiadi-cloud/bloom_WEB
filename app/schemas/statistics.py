from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ClientAnalyticsEventCreate(BaseModel):
    event_type: Literal["partner_view", "offer_view", "offer_select", "contact_click"]
    partner_id: int = Field(gt=0)
    offer_id: int | None = Field(default=None, gt=0)
    target: str | None = Field(default=None, max_length=128)
