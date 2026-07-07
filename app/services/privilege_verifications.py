from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Select, update
from sqlalchemy.orm import Session

from app.models.verification import PrivilegeVerificationSession, PrivilegeVerificationStatus

PRIVILEGE_VERIFICATION_TTL_SECONDS = 15 * 60
PRIVILEGE_VERIFICATION_USED_STATUS = "used"
PRIVILEGE_VERIFICATION_FINAL_STATUSES = {
    PrivilegeVerificationStatus.confirmed.value,
    PRIVILEGE_VERIFICATION_USED_STATUS,
}


def as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def ttl_seconds(expires_at: datetime, *, now: datetime | None = None) -> int:
    current_time = now or datetime.now(timezone.utc)
    seconds = int((as_aware_utc(expires_at) - current_time).total_seconds())
    return max(seconds, 0)


def is_final_verification_status(status: str) -> bool:
    return status in PRIVILEGE_VERIFICATION_FINAL_STATUSES


def normalize_expired_verifications(
    db: Session,
    *,
    now: datetime | None = None,
    client_id: int | None = None,
    partner_id: int | None = None,
) -> int:
    """Mark active/pending privilege verification sessions as expired once their 15-minute TTL is over."""

    current_time = now or datetime.now(timezone.utc)
    statement = (
        update(PrivilegeVerificationSession)
        .where(
            PrivilegeVerificationSession.status.in_(
                [PrivilegeVerificationStatus.active.value, PrivilegeVerificationStatus.pending.value]
            ),
            PrivilegeVerificationSession.expires_at < current_time,
        )
        .values(status=PrivilegeVerificationStatus.expired.value)
        .execution_options(synchronize_session=False)
    )
    if client_id is not None:
        statement = statement.where(PrivilegeVerificationSession.client_id == client_id)
    if partner_id is not None:
        statement = statement.where(PrivilegeVerificationSession.partner_id == partner_id)

    result = db.execute(statement)
    expired_count = int(result.rowcount or 0)
    if expired_count > 0:
        db.commit()
    return expired_count


def apply_verification_status_filter(
    statement: Select,
    requested_status: str | None,
    *,
    now: datetime | None = None,
) -> Select:
    normalized_status = requested_status.strip().lower() if requested_status is not None else None
    if normalized_status is None or normalized_status == "all":
        return statement

    current_time = now or datetime.now(timezone.utc)
    if normalized_status == PrivilegeVerificationStatus.active.value:
        return statement.where(
            PrivilegeVerificationSession.status == PrivilegeVerificationStatus.active.value,
            PrivilegeVerificationSession.expires_at >= current_time,
        )
    if normalized_status == PrivilegeVerificationStatus.expired.value:
        return statement.where(PrivilegeVerificationSession.status == PrivilegeVerificationStatus.expired.value)
    if normalized_status in PRIVILEGE_VERIFICATION_FINAL_STATUSES:
        return statement.where(PrivilegeVerificationSession.status.in_(PRIVILEGE_VERIFICATION_FINAL_STATUSES))

    return statement.where(PrivilegeVerificationSession.status == normalized_status)
