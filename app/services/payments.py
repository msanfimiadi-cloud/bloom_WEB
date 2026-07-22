from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.acquiring import Payment, PaymentStatus, SubscriptionPlan
from app.models.client import ClientProfile
from app.schemas.acquiring import PaymentCreate, PaymentRead
from app.services.payment_fulfillment import PaymentFulfillmentService, add_payment_event, apply_provider_state, payload_hash
from app.services.tochka_payments import TochkaPaymentsClient


def _redirect(base: str, public_id: str) -> str:
    parts = urlsplit(base)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["payment"] = public_id
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def payment_read(payment: Payment) -> PaymentRead:
    return PaymentRead(
        payment_id=payment.public_id,
        status=payment.status,
        provider_status=payment.provider_status,
        amount=payment.amount,
        currency=payment.currency,
        payment_url=payment.provider_payment_url,
        expires_at=payment.expired_at,
        paid_at=payment.paid_at,
        subscription_activated=payment.fulfilled_at is not None,
    )


async def create_payment(db: Session, *, user_id: int, profile: ClientProfile, request: PaymentCreate) -> Payment:
    if not settings.TOCHKA_PAYMENTS_ENABLED:
        raise RuntimeError("Payments are temporarily unavailable")
    settings.validate_tochka()
    if not settings.TOCHKA_TAX_SYSTEM_CODE.strip():
        raise RuntimeError("Receipt tax system is not configured")
    if profile.status != "active" or profile.merged_into_client_id is not None:
        raise ValueError("Client profile is not available for payments")
    plan = db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == request.subscription_plan_id, SubscriptionPlan.is_active.is_(True))).scalar_one_or_none()
    if plan is None:
        raise LookupError("Subscription plan not found")
    if plan.currency != "RUB":
        raise ValueError("Unsupported subscription currency")
    recent_since = datetime.now(timezone.utc) - timedelta(minutes=5)
    duplicate = db.execute(
        select(Payment).where(
            Payment.client_profile_id == profile.id,
            Payment.subscription_plan_id == plan.id,
            Payment.status.in_([PaymentStatus.created.value, PaymentStatus.pending.value, PaymentStatus.authorized.value]),
            Payment.created_at >= recent_since,
        ).order_by(Payment.id.desc()).limit(1)
    ).scalar_one_or_none()
    if duplicate is not None:
        return duplicate
    configured_modes = settings.tochka_payment_modes_list
    requested_modes = request.payment_modes or configured_modes
    modes = [mode for mode in requested_modes if mode in configured_modes and mode in {"sbp", "card"}]
    if not modes:
        raise ValueError("No supported payment mode selected")
    public_id = str(uuid4())
    link_id = f"blm-{public_id.replace('-', '')[:26]}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.TOCHKA_PAYMENT_LINK_TTL_MINUTES)
    payment = Payment(
        public_id=public_id, user_id=user_id, client_profile_id=profile.id, subscription_plan_id=plan.id,
        payment_link_id=link_id, amount=plan.price, currency=plan.currency, purpose=plan.name[:140],
        status=PaymentStatus.created.value, payment_modes=modes, customer_code=settings.TOCHKA_CUSTOMER_CODE,
        merchant_id=settings.TOCHKA_MERCHANT_ID, terminal_id=settings.TOCHKA_TERMINAL_ID or None,
        receipt_email=request.receipt_email, receipt_phone=request.receipt_phone, expired_at=expires_at,
        metadata_json={"duration_days": plan.duration_days},
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    body = {
        "customerCode": payment.customer_code,
        "merchantId": payment.merchant_id,
        "amount": float(payment.amount),
        "purpose": payment.purpose,
        "paymentLinkId": payment.payment_link_id,
        "paymentMode": modes,
        "redirectUrl": _redirect(settings.TOCHKA_SUCCESS_REDIRECT_URL, payment.public_id),
        "failRedirectUrl": _redirect(settings.TOCHKA_FAIL_REDIRECT_URL, payment.public_id),
        "preAuthorization": False,
        "ttl": settings.TOCHKA_PAYMENT_LINK_TTL_MINUTES,
        "taxSystemCode": settings.TOCHKA_TAX_SYSTEM_CODE,
        "Client": {"name": profile.full_name or "Клиент Bloom Club", "email": payment.receipt_email, **({"phone": payment.receipt_phone} if payment.receipt_phone else {})},
        "Items": [{"name": payment.purpose, "amount": float(payment.amount), "quantity": 1, "vatType": settings.TOCHKA_VAT_TYPE, "paymentMethod": settings.TOCHKA_PAYMENT_METHOD, "paymentObject": settings.TOCHKA_PAYMENT_OBJECT, "measure": "шт."}],
    }
    try:
        async with TochkaPaymentsClient() as client:
            result = await client.create_payment_with_receipt(body)
    except Exception:
        payment.status = PaymentStatus.pending.value
        payment.failure_message = "Payment creation outcome requires reconciliation"
        payment.updated_at = datetime.now(timezone.utc)
        db.commit()
        raise
    payment.provider_operation_id = result.operation_id
    payment.provider_payment_url = result.payment_url
    payment.provider_status = result.status or "CREATED"
    payment.status = PaymentStatus.created.value
    payment.provider_created_at = datetime.now(timezone.utc)
    payment.updated_at = payment.provider_created_at
    safe = {"operationId": result.operation_id, "paymentLinkId": payment.payment_link_id, "status": result.status}
    add_payment_event(db, payment=payment, source="create_response", event_type="payment_created", provider_status=payment.provider_status, payload=safe, raw_hash=payload_hash(str(safe)), signature_verified=False)
    db.commit()
    db.refresh(payment)
    return payment


async def refresh_payment(db: Session, payment: Payment, *, source: str = "manual_sync") -> Payment:
    if not payment.provider_operation_id:
        return payment
    async with TochkaPaymentsClient() as client:
        payload = await client.get_payment_info(payment.provider_operation_id)
    apply_provider_state(payment, payload)
    add_payment_event(db, payment=payment, source=source, event_type="payment_status", provider_status=payment.provider_status, payload=payload, raw_hash=payload_hash(str(payload)), signature_verified=False)
    if payment.status == PaymentStatus.approved.value:
        PaymentFulfillmentService(db).fulfill_approved_payment(payment.id)
    db.commit()
    db.refresh(payment)
    return payment
