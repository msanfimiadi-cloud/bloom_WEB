from __future__ import annotations

from typing import Any, TypedDict


class SubscriptionPayload(TypedDict, total=False):
    data: dict[str, Any]
