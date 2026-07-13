from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.models.client import (
    AccountLinkingChallenge,
    ClientIdentityLink,
    ClientPasswordSetupToken,
    ClientProfile,
    ClientReferral,
    GiveawayEntry,
    VkLinkCode,
)
from app.models.lead import LeadClick
from app.models.partner import OfferPhoto, Partner, PartnerOffer, PartnerPhoto, PartnerQrLink, partner_categories
from app.models.payment import PaymentReceipt, PaymentRequest, Subscription
from app.models.user import AdminUser, User, UserRole
from app.models.verification import PrivilegeVerificationSession

logger = logging.getLogger(__name__)

SYSTEM_ADMIN_EMAILS = {"admin@example.com", "root@example.com"}


def delete_user_with_relations(*, db: Session, admin: AdminUser, user_id: int) -> dict[str, object]:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.email and user.email.lower() == admin.email.lower():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить самого себя")

    if user.role == UserRole.ADMIN.value:
        admin_count = db.execute(select(func.count(User.id)).where(User.role == UserRole.ADMIN.value)).scalar_one()
        if admin_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить последнего администратора")
        if user.email and user.email.lower() in SYSTEM_ADMIN_EMAILS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить системного администратора")

    deleted: dict[str, int] = {
        "account_linking_challenges": 0,
        "client_identity_links": 0,
        "client_password_setup_tokens": 0,
        "client_referrals": 0,
        "giveaway_entries": 0,
        "client_profile": 0,
        "partner_profile": 0,
        "payment_requests": 0,
        "payment_receipts": 0,
        "subscriptions": 0,
        "verifications": 0,
        "vk_link_codes": 0,
        "offer_photos": 0,
        "partner_categories": 0,
        "partner_offers": 0,
        "partner_photos": 0,
        "partner_qr_links": 0,
        "partner_lead_clicks": 0,
        "user": 0,
    }

    try:
        deleted["client_password_setup_tokens"] += db.execute(
            delete(ClientPasswordSetupToken).where(ClientPasswordSetupToken.user_id == user.id)
        ).rowcount or 0

        client = db.execute(select(ClientProfile).where(ClientProfile.user_id == user.id)).scalar_one_or_none()
        if client is not None:
            deleted["verifications"] += db.execute(
                delete(PrivilegeVerificationSession).where(PrivilegeVerificationSession.client_id == client.id)
            ).rowcount or 0
            deleted["account_linking_challenges"] += db.execute(
                delete(AccountLinkingChallenge).where(
                    or_(
                        AccountLinkingChallenge.current_client_profile_id == client.id,
                        AccountLinkingChallenge.target_client_profile_id == client.id,
                    )
                )
            ).rowcount or 0
            deleted["client_identity_links"] += db.execute(
                delete(ClientIdentityLink).where(ClientIdentityLink.client_profile_id == client.id)
            ).rowcount or 0
            deleted["vk_link_codes"] += db.execute(delete(VkLinkCode).where(VkLinkCode.client_id == client.id)).rowcount or 0

            referral_ids = db.execute(
                select(ClientReferral.id).where(
                    or_(ClientReferral.referrer_client_id == client.id, ClientReferral.referred_client_id == client.id)
                )
            ).scalars().all()
            if referral_ids:
                db.execute(
                    update(ClientProfile)
                    .where(ClientProfile.referred_by_referral_id.in_(referral_ids))
                    .values(referred_by_referral_id=None)
                )
                # Keep already granted giveaway rewards on the inviter account.
                # Detach them from the deleted referral rows so the old reward
                # numbers remain visible and the same Telegram ID can register
                # again as a brand-new client with a brand-new referral relation.
                db.execute(
                    update(GiveawayEntry)
                    .where(GiveawayEntry.related_referral_id.in_(referral_ids), GiveawayEntry.client_id != client.id)
                    .values(related_referral_id=None)
                )
                deleted["giveaway_entries"] += db.execute(
                    delete(GiveawayEntry).where(GiveawayEntry.related_referral_id.in_(referral_ids))
                ).rowcount or 0
                deleted["client_referrals"] += db.execute(
                    delete(ClientReferral).where(ClientReferral.id.in_(referral_ids))
                ).rowcount or 0
            deleted["giveaway_entries"] += db.execute(
                delete(GiveawayEntry).where(GiveawayEntry.client_id == client.id)
            ).rowcount or 0

            payment_request_ids = db.execute(
                select(PaymentRequest.id).where(PaymentRequest.client_id == client.id)
            ).scalars().all()
            if payment_request_ids:
                deleted["payment_receipts"] += db.execute(
                    delete(PaymentReceipt).where(PaymentReceipt.payment_request_id.in_(payment_request_ids))
                ).rowcount or 0
            deleted["subscriptions"] += db.execute(delete(Subscription).where(Subscription.client_id == client.id)).rowcount or 0
            deleted["payment_requests"] += db.execute(
                delete(PaymentRequest).where(PaymentRequest.client_id == client.id)
            ).rowcount or 0
            deleted["client_profile"] += db.execute(delete(ClientProfile).where(ClientProfile.id == client.id)).rowcount or 0

        partner_ids = db.execute(select(Partner.id).where(Partner.owner_user_id == user.id)).scalars().all()
        for partner_id in partner_ids:
            deleted["verifications"] += db.execute(
                delete(PrivilegeVerificationSession).where(
                    or_(
                        PrivilegeVerificationSession.partner_id == partner_id,
                        PrivilegeVerificationSession.confirmed_by_partner_id == partner_id,
                    )
                )
            ).rowcount or 0
            offer_ids = db.execute(select(PartnerOffer.id).where(PartnerOffer.partner_id == partner_id)).scalars().all()
            if offer_ids:
                deleted["offer_photos"] += db.execute(delete(OfferPhoto).where(OfferPhoto.offer_id.in_(offer_ids))).rowcount or 0
            deleted["partner_offers"] += db.execute(delete(PartnerOffer).where(PartnerOffer.partner_id == partner_id)).rowcount or 0
            deleted["partner_photos"] += db.execute(delete(PartnerPhoto).where(PartnerPhoto.partner_id == partner_id)).rowcount or 0
            qr_ids = db.execute(select(PartnerQrLink.id).where(PartnerQrLink.partner_id == partner_id)).scalars().all()
            if qr_ids:
                deleted["partner_lead_clicks"] += db.execute(delete(LeadClick).where(LeadClick.qr_link_id.in_(qr_ids))).rowcount or 0
            deleted["partner_lead_clicks"] += db.execute(
                delete(LeadClick).where(LeadClick.partner_id == partner_id)
            ).rowcount or 0
            deleted["partner_qr_links"] += db.execute(delete(PartnerQrLink).where(PartnerQrLink.partner_id == partner_id)).rowcount or 0
            deleted["partner_categories"] += db.execute(
                delete(partner_categories).where(partner_categories.c.partner_id == partner_id)
            ).rowcount or 0
            deleted["partner_profile"] += db.execute(delete(Partner).where(Partner.id == partner_id)).rowcount or 0

        deleted["user"] = db.execute(delete(User).where(User.id == user.id)).rowcount or 0
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "admin_delete_user_failed",
            extra={"action": "admin_delete_user_failed", "admin_user_id": admin.id, "deleted_user_id": user_id, "counts": deleted},
        )
        raise

    logger.info(
        "admin_delete_user",
        extra={"action": "admin_delete_user", "admin_user_id": admin.id, "deleted_user_id": user_id, "counts": deleted},
    )
    return {"ok": True, "deleted_user_id": user_id, "deleted": deleted}
