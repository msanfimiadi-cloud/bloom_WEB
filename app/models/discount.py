from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DiscountCodeStatus(str, Enum):
    active = "active"
    used = "used"
    expired = "expired"


@dataclass(slots=True)
class DiscountCode:
    id: int | None
    code: str
    client_user_id: int
    partner_id: int
    status: DiscountCodeStatus
    expires_at: datetime | None = None
