from __future__ import annotations

from typing import NotRequired, TypedDict


class HealthResponse(TypedDict):
    status: str
    service: str
    version: NotRequired[str]


class DatabaseHealthResponse(TypedDict):
    status: str
    service: str
    database: str
