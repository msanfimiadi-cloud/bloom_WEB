from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_client
from app.db.session import get_db
from app.models.city import City
from app.models.client import ClientProfile
from app.models.partner import Partner, PartnerOffer
from app.models.payment import Subscription, SubscriptionStatus
from app.models.user import User
from app.models.verification import PrivilegeVerificationSession, PrivilegeVerificationStatus
from app.schemas.privilege import (
    PrivilegeSessionCreateRequest,
    PrivilegeSessionCreateResponse,
    PrivilegeSessionPartnerRead,
    PrivilegeSessionPrivilegeRead,
)
from app.services.privilege_verifications import PRIVILEGE_VERIFICATION_TTL_SECONDS, normalize_expired_verifications

router = APIRouter(prefix="/privileges", tags=["privileges"])

ACTIVE_SUBSCRIPTION_REQUIRED_DETAIL = "Active subscription required"
PARTNER_NOT_FOUND_DETAIL = "Partner not found"
OFFER_NOT_FOUND_DETAIL = "Offer not found"
OFFER_ID_CONFLICT_DETAIL = "offer_id and privilege_id must match"
PRIVILEGE_QR_PAYLOAD_PREFIX = "bloomclub:privilege:"
VERIFICATION_CODE_ALPHABET = string.digits


@router.post("/sessions", response_model=PrivilegeSessionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_privilege_qr_session(
    payload: PrivilegeSessionCreateRequest,
    current_user: User = Depends(require_client),
    db: Session = Depends(get_db),
) -> PrivilegeSessionCreateResponse:
    profile = _get_or_create_client_profile(db, current_user.id)
    now = datetime.now(timezone.utc)
    if not _has_active_subscription(db, profile.id, now):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ACTIVE_SUBSCRIPTION_REQUIRED_DETAIL,
        )

    partner = _get_active_partner_or_404(db, payload.partner_id)
    privilege = _resolve_partner_privilege(db, partner.id, payload.offer_id, payload.privilege_id)

    normalize_expired_verifications(db, now=now, client_id=profile.id, partner_id=partner.id)

    token = _generate_unique_privilege_token(db)
    session = PrivilegeVerificationSession(
        client_id=profile.id,
        partner_id=partner.id,
        offer_id=privilege.id if privilege is not None else None,
        code=_generate_display_code(),
        token=token,
        status=PrivilegeVerificationStatus.pending.value,
        source="qr",
        expires_at=now + timedelta(seconds=PRIVILEGE_VERIFICATION_TTL_SECONDS),
        created_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return _privilege_session_to_response(session, partner, privilege)


def _get_or_create_client_profile(db: Session, user_id: int) -> ClientProfile:
    profile = db.execute(select(ClientProfile).where(ClientProfile.user_id == user_id)).scalar_one_or_none()
    if profile is not None:
        return profile
    profile = ClientProfile(user_id=user_id, source="web", is_active=True)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _has_active_subscription(db: Session, client_id: int, now: datetime) -> bool:
    subscription_id = db.execute(
        select(Subscription.id)
        .where(
            Subscription.client_id == client_id,
            Subscription.status == SubscriptionStatus.active.value,
            Subscription.starts_at <= now,
            Subscription.ends_at > now,
        )
        .limit(1)
    ).scalar_one_or_none()
    return subscription_id is not None


def _get_active_partner_or_404(db: Session, partner_id: int) -> Partner:
    partner = db.execute(
        select(Partner)
        .join(City, Partner.city_id == City.id)
        .options(selectinload(Partner.categories))
        .where(Partner.id == partner_id, Partner.is_active.is_(True), City.is_active.is_(True))
    ).scalar_one_or_none()
    if partner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PARTNER_NOT_FOUND_DETAIL)
    return partner


def _resolve_partner_privilege(
    db: Session,
    partner_id: int,
    offer_id: int | None,
    privilege_id: int | None,
) -> PartnerOffer | None:
    selected_offer_id = _selected_offer_id(offer_id, privilege_id)
    if selected_offer_id is None:
        return None
    privilege = db.execute(
        select(PartnerOffer).where(
            PartnerOffer.id == selected_offer_id,
            PartnerOffer.partner_id == partner_id,
            PartnerOffer.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if privilege is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=OFFER_NOT_FOUND_DETAIL)
    return privilege


def _selected_offer_id(offer_id: int | None, privilege_id: int | None) -> int | None:
    if offer_id is not None and privilege_id is not None and offer_id != privilege_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=OFFER_ID_CONFLICT_DETAIL)
    return offer_id if offer_id is not None else privilege_id


def _generate_display_code(length: int = 6) -> str:
    return "".join(secrets.choice(VERIFICATION_CODE_ALPHABET) for _ in range(length))


def _generate_unique_privilege_token(db: Session) -> str:
    for _ in range(20):
        token = secrets.token_urlsafe(32)
        exists = db.execute(
            select(PrivilegeVerificationSession.id).where(PrivilegeVerificationSession.token == token)
        ).scalar_one_or_none()
        if exists is None:
            return token
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Could not generate privilege session token",
    )


def _privilege_qr_payload(token: str) -> str:
    return f"{PRIVILEGE_QR_PAYLOAD_PREFIX}{token}"


def _privilege_session_to_response(
    session: PrivilegeVerificationSession,
    partner: Partner,
    privilege: PartnerOffer | None,
) -> PrivilegeSessionCreateResponse:
    token = session.token
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Privilege session token is not available",
        )
    return PrivilegeSessionCreateResponse(
        session_id=session.id,
        token=token,
        qr_payload=_privilege_qr_payload(token),
        expires_at=session.expires_at,
        partner=PrivilegeSessionPartnerRead(id=partner.id, name=partner.name),
        privilege=(
            PrivilegeSessionPrivilegeRead(id=privilege.id, title=privilege.title)
            if privilege is not None
            else None
        ),
        display_code=session.code,
        status=session.status,
    )
