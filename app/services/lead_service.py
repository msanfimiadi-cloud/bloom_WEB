from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class LeadClick:
    qr_link_id: int | None
    session_id: str
    created_at: datetime


async def record_lead_click(*, db, qr_link, request, session_id: str) -> LeadClick:
    """Record a lead click in the MVP flow.

    The concrete persistence implementation is intentionally left to the copied
    backend skeleton/migrations and should not be rebranded in this PR.
    """
    return LeadClick(
        qr_link_id=getattr(qr_link, "id", None),
        session_id=session_id,
        created_at=datetime.now(timezone.utc),
    )
