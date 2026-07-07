from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.lead import LeadClick
from app.models.partner import Partner, PartnerQrLink
from app.models.verification import PrivilegeVerificationSession, PrivilegeVerificationStatus
from app.schemas.partner import PartnerAnalyticsRead


def build_partner_analytics(db: Session, partner: Partner) -> PartnerAnalyticsRead:
    now = datetime.now(timezone.utc)

    qr_links_count = _count(
        db,
        select(func.count()).select_from(PartnerQrLink).where(PartnerQrLink.partner_id == partner.id),
    )
    lead_clicks_count = _count(
        db,
        select(func.count()).select_from(LeadClick).where(LeadClick.partner_id == partner.id),
    )
    privileges_created_count = _count(
        db,
        select(func.count())
        .select_from(PrivilegeVerificationSession)
        .where(PrivilegeVerificationSession.partner_id == partner.id),
    )
    privileges_confirmed_count = _count(
        db,
        select(func.count())
        .select_from(PrivilegeVerificationSession)
        .where(
            PrivilegeVerificationSession.partner_id == partner.id,
            PrivilegeVerificationSession.status == PrivilegeVerificationStatus.confirmed.value,
        ),
    )
    active_privileges_count = _count(
        db,
        select(func.count())
        .select_from(PrivilegeVerificationSession)
        .where(
            PrivilegeVerificationSession.partner_id == partner.id,
            PrivilegeVerificationSession.status == PrivilegeVerificationStatus.active.value,
            PrivilegeVerificationSession.expires_at > now,
        ),
    )
    expired_privileges_count = _count(
        db,
        select(func.count())
        .select_from(PrivilegeVerificationSession)
        .where(
            PrivilegeVerificationSession.partner_id == partner.id,
            or_(
                PrivilegeVerificationSession.status == PrivilegeVerificationStatus.expired.value,
                (
                    (PrivilegeVerificationSession.status == PrivilegeVerificationStatus.active.value)
                    & (PrivilegeVerificationSession.expires_at <= now)
                ),
            ),
        ),
    )

    conversion_to_privilege_percent = (
        round(privileges_created_count / lead_clicks_count * 100, 1) if lead_clicks_count > 0 else 0.0
    )
    confirmation_rate_percent = (
        round(privileges_confirmed_count / privileges_created_count * 100, 1)
        if privileges_created_count > 0
        else 0.0
    )

    return PartnerAnalyticsRead(
        partner_id=partner.id,
        partner_name=partner.name,
        qr_links_count=qr_links_count,
        lead_clicks_count=lead_clicks_count,
        privileges_created_count=privileges_created_count,
        privileges_confirmed_count=privileges_confirmed_count,
        active_privileges_count=active_privileges_count,
        expired_privileges_count=expired_privileges_count,
        conversion_to_privilege_percent=conversion_to_privilege_percent,
        confirmation_rate_percent=confirmation_rate_percent,
    )


def _count(db: Session, statement) -> int:
    return int(db.execute(statement).scalar_one())
