from __future__ import annotations

from typing import Any, TypedDict


class DiscountPayload(TypedDict, total=False):
    data: dict[str, Any]
