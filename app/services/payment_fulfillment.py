from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.acquiring import Payment, PaymentEvent, PaymentStatus, SubscriptionPlan
from app.models.giveaway import GiveawayNumber
from app.models.payment import Subscription, SubscriptionStatus
from app.services.giveaways import ensure_user_numbers, get_active_giveaway


logger = logging.getLogger("app.payments.fulfillment")

PROVIDER_STATUS_MAP = {
    "CREATED": PaymentStatus.created.value,
    "AUTHORIZED": PaymentStatus.authorized.value,
    "APPROVED": PaymentStatus.approved.value,
    "ON-REFUND": PaymentStatus.refund_pending.value,
    "REFUNDED_PARTIALLY": PaymentStatus.partially_refunded.value,
    "REFUNDED": PaymentStatus.refunded.value,
    "EXPIRED": PaymentStatus.expired.value,
    "WAIT_FULL_PAYMENT": PaymentStatus.pending.value,
}


def aware(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)


def payload_hash(value: str | bytes) -> str:
    raw = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def add_payment_event(
    db: Session, *, payment: Payment | None, source: str, event_type: str,
    provider_status: str | None, payload: dict[str, Any], raw_hash: str,
    signature_verified: bool, provider_event_id: str | None = None,
) -> PaymentEvent:
    event = PaymentEvent(
        payment_id=payment.id if payment else None,
        provider="tochka",
        event_type=event_type,
        provider_event_id=provider_event_id or f"{source}:{uuid4().hex}",
        provider_status=provider_status,
        source=source,
        signature_verified=signature_verified,
        raw_body_hash=raw_hash,
        payload_json=payload,
        processing_status="received",
    )
    db.add(event)
    db.flush()
    return event


def apply_provider_state(payment: Payment, payload: dict[str, Any], *, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    data = payload.get("Data") or payload.get("data") or payload
    provider_status = str(data.get("status") or "").upper()
    payment.provider_status = provider_status or payment.provider_status
    payment.payment_method = data.get("paymentType") or data.get("paymentMode") or payment.payment_method
    payment.last_synced_at = now
    payment.updated_at = now
    mapped = PROVIDER_STATUS_MAP.get(provider_status)
    if mapped is None:
        logger.warning("unknown_tochka_status payment_public_id=%s provider_status=%s", payment.public_id, provider_status)
        return
    payment.status = mapped
    if mapped == PaymentStatus.authorized.value:
        payment.authorized_at = now
    elif mapped == PaymentStatus.approved.value:
        payment.paid_at = payment.paid_at or now
        payment.approved_at = payment.approved_at or now
    elif mapped == PaymentStatus.expired.value:
        payment.expired_at = payment.expired_at or now
    elif mapped == PaymentStatus.refunded.value:
        payment.refunded_at = payment.refunded_at or now


class PaymentFulfillmentService:
    def __init__(self, db: Session):
        self.db = db

    def fulfill_approved_payment(self, payment_id: int) -> Payment:
        payment = self.db.execute(
            select(Payment).where(Payment.id == payment_id).with_for_update()
        ).scalar_one()
        if payment.fulfilled_at is not None:
            logger.info("payment_fulfillment_skipped payment_public_id=%s", payment.public_id)
            return payment
        if payment.status != PaymentStatus.approved.value:
            raise ValueError("Payment is not approved")
        plan = self.db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == payment.subscription_plan_id)).scalar_one()
        if payment.amount != plan.price or payment.currency != plan.currency:
            raise ValueError("Payment amount or currency does not match subscription plan")
        now = datetime.now(timezone.utc)
        current = self.db.execute(
            select(Subscription)
            .where(Subscription.client_id == payment.client_profile_id, Subscription.status == SubscriptionStatus.active.value)
            .order_by(Subscription.ends_at.desc(), Subscription.id.desc())
            .with_for_update()
            .limit(1)
        ).scalar_one_or_none()
        if current is not None and aware(current.ends_at) and aware(current.ends_at) > now:
            current.ends_at = aware(current.ends_at) + timedelta(days=plan.duration_days)
            subscription = current
        else:
            subscription = Subscription(
                client_id=payment.client_profile_id,
                status=SubscriptionStatus.active.value,
                starts_at=now,
                ends_at=now + timedelta(days=plan.duration_days),
                source="tochka",
            )
            self.db.add(subscription)
            self.db.flush()
        payment.subscription_id = subscription.id
        payment.fulfilled_at = now
        active_giveaway = get_active_giveaway(self.db, now)
        if active_giveaway is not None:
            ensure_user_numbers(self.db, active_giveaway.id, payment.client_profile_id)
        logger.info("payment_fulfillment_completed payment_public_id=%s subscription_id=%s", payment.public_id, subscription.id)
        return payment
