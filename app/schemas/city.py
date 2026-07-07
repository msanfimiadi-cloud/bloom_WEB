from __future__ import annotations

from typing import TypedDict


class CityPayload(TypedDict, total=False):
    id: int
    name: str
    slug: str
    is_active: bool
    sort_order: int
