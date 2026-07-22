from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_admin, require_client
from app.core.config import settings
from app.db.session import get_db
from app.models.acquiring import Payment, PaymentEvent, PaymentRefund, PaymentStatus, SubscriptionPlan
from app.models.client import ClientProfile
from app.models.user import AdminUser, User
from app.schemas.acquiring import (
    AdminPaymentRead,
    PaymentCreate,
    PaymentRead,
    RefundCreate,
    SubscriptionPlanRead,
    SubscriptionPlanUpdate,
)
from app.services.payment_fulfillment import PaymentFulfillmentService, add_payment_event, apply_provider_state, payload_hash
from app.services.payments import create_payment, payment_read, refresh_payment
from app.services.tochka_payments import TochkaError, TochkaPaymentsClient, TochkaWebhookSignatureError, verify_webhook


logger = logging.getLogger("app.payments.api")
router = APIRouter()
_refresh_timestamps: dict[str, datetime] = {}
_create_timestamps: dict[int, datetime] = {}


def _profile(db: Session, user_id: int) -> ClientProfile:
    profile = db.execute(select(ClientProfile).where(ClientProfile.user_id == user_id)).scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Client profile not found")
    return profile


def _owned(db: Session, public_id: str, user_id: int) -> Payment:
    payment = db.execute(select(Payment).where(Payment.public_id == public_id, Payment.user_id == user_id)).scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


def _plan_read(plan: SubscriptionPlan) -> SubscriptionPlanRead:
    return SubscriptionPlanRead(
        id=plan.id,
        code=plan.code,
        name=plan.name,
        price=plan.price,
        currency=plan.currency,
        duration_days=plan.duration_days,
        is_active=plan.is_active,
        updated_at=plan.updated_at,
    )


@router.get("/clients/subscription-plans", response_model=list[SubscriptionPlanRead], tags=["client-payments"])
def list_client_subscription_plans(
    current_user: User = Depends(require_client), db: Session = Depends(get_db),
):
    _ = current_user
    plans = db.execute(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.id)
    ).scalars().all()
    return [_plan_read(plan) for plan in plans]


@router.post("/clients/payments", response_model=PaymentRead, status_code=201, tags=["client-payments"])
async def create_client_payment(payload: PaymentCreate, current_user: User = Depends(require_client), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    last = _create_timestamps.get(current_user.id)
    if last and now - last < timedelta(seconds=3):
        raise HTTPException(status_code=429, detail="Слишком много запросов. Попробуйте ещё раз.")
    _create_timestamps[current_user.id] = now
    try:
        payment = await create_payment(db, user_id=current_user.id, profile=_profile(db, current_user.id), request=payload)
        return payment_read(payment)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Тариф не найден") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (RuntimeError, TochkaError) as exc:
        logger.warning("payment_create_failed user_id=%s error_type=%s", current_user.id, type(exc).__name__)
        raise HTTPException(status_code=503, detail="Не удалось создать оплату. Попробуйте ещё раз.") from exc


@router.get("/clients/payments/{payment_public_id}", response_model=PaymentRead, tags=["client-payments"])
def read_client_payment(payment_public_id: str, current_user: User = Depends(require_client), db: Session = Depends(get_db)):
    return payment_read(_owned(db, payment_public_id, current_user.id))


@router.post("/clients/payments/{payment_public_id}/refresh", response_model=PaymentRead, tags=["client-payments"])
async def refresh_client_payment(payment_public_id: str, current_user: User = Depends(require_client), db: Session = Depends(get_db)):
    payment = _owned(db, payment_public_id, current_user.id)
    now = datetime.now(timezone.utc)
    last = _refresh_timestamps.get(payment_public_id)
    if last and now - last < timedelta(seconds=12):
        raise HTTPException(status_code=429, detail="Платёж уже проверяется")
    _refresh_timestamps[payment_public_id] = now
    try:
        return payment_read(await refresh_payment(db, payment))
    except TochkaError as exc:
        raise HTTPException(status_code=503, detail="Не удалось проверить оплату") from exc


@router.post("/payments/tochka/webhook", tags=["payments-webhook"])
async def tochka_webhook(request: Request, db: Session = Depends(get_db)) -> Response:
    raw = (await request.body()).decode("utf-8", errors="strict").strip()
    try:
        payload = verify_webhook(raw)
    except (UnicodeError, TochkaWebhookSignatureError) as exc:
        logger.warning("tochka_webhook_rejected reason=%s", type(exc).__name__)
        raise HTTPException(status_code=401, detail="Invalid webhook") from exc
    data = payload.model_dump(mode="json")
    event_id = f"{payload.operationId}:{payload.status}:{payload.paymentLinkId}"
    existing = db.execute(select(PaymentEvent.id).where(PaymentEvent.provider == "tochka", PaymentEvent.provider_event_id == event_id)).scalar_one_or_none()
    if existing is not None:
        return Response(status_code=200)
    payment = db.execute(select(Payment).where(Payment.provider == "tochka", Payment.provider_operation_id == payload.operationId)).scalar_one_or_none()
    event = add_payment_event(db, payment=payment, source="webhook", event_type=payload.webhookType, provider_status=payload.status, payload=data, raw_hash=payload_hash(raw), signature_verified=True, provider_event_id=event_id)
    if payment is None:
        event.processing_status = "ignored"
        event.processing_error = "unknown_operation"
        event.processed_at = datetime.now(timezone.utc)
        db.commit()
        return Response(status_code=200)
    conflicts = []
    if payload.paymentLinkId != payment.payment_link_id: conflicts.append("payment_link_id")
    if Decimal(payload.amount) != payment.amount: conflicts.append("amount")
    if payload.merchantId != payment.merchant_id: conflicts.append("merchant_id")
    if payload.customerCode and payload.customerCode != payment.customer_code: conflicts.append("customer_code")
    if payload.webhookType != "acquiringInternetPayment": conflicts.append("webhook_type")
    if conflicts:
        event.processing_status = "conflict"
        event.processing_error = ",".join(conflicts)
        event.processed_at = datetime.now(timezone.utc)
        logger.error("tochka_webhook_conflict payment_public_id=%s fields=%s", payment.public_id, conflicts)
        db.commit()
        return Response(status_code=200)
    try:
        apply_provider_state(payment, data)
        if payment.status == PaymentStatus.approved.value:
            PaymentFulfillmentService(db).fulfill_approved_payment(payment.id)
        event.processing_status = "processed"
        event.processed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("tochka_webhook_processing_failed operation_id=%s", payload.operationId)
        raise HTTPException(status_code=500, detail="Webhook processing failed") from exc
    return Response(status_code=200)


def _admin_read(payment: Payment) -> AdminPaymentRead:
    profile = payment_metadata_profile = getattr(payment, "_admin_profile", None)
    return AdminPaymentRead(
        id=payment.id, public_id=payment.public_id, user_id=payment.user_id, client_profile_id=payment.client_profile_id,
        client_name=getattr(profile, "full_name", None), telegram_user_id=getattr(profile, "telegram_user_id", None), vk_user_id=getattr(profile, "vk_user_id", None),
        plan_name=payment.plan.name, amount=payment.amount, currency=payment.currency, status=payment.status,
        provider_status=payment.provider_status, payment_method=payment.payment_method, provider_operation_id=payment.provider_operation_id,
        payment_link_id=payment.payment_link_id, paid_at=payment.paid_at, subscription_id=payment.subscription_id,
        refunded_amount=payment.refunded_amount, created_at=payment.created_at,
    )


@router.get("/admin/subscription-plans", response_model=list[SubscriptionPlanRead], tags=["admin-payments"])
def list_admin_subscription_plans(
    admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db),
):
    _ = admin
    plans = db.execute(select(SubscriptionPlan).order_by(SubscriptionPlan.id)).scalars().all()
    return [_plan_read(plan) for plan in plans]


@router.patch("/admin/subscription-plans/{plan_id}", response_model=SubscriptionPlanRead, tags=["admin-payments"])
def update_admin_subscription_plan(
    plan_id: int,
    payload: SubscriptionPlanUpdate,
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    plan = db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id).with_for_update()
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    old_price = plan.price
    plan.price = payload.price.quantize(Decimal("0.01"))
    plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plan)
    logger.info(
        "subscription_plan_price_updated admin_id=%s plan_id=%s old_price=%s new_price=%s",
        admin.id,
        plan.id,
        old_price,
        plan.price,
    )
    return _plan_read(plan)


@router.get("/admin/payments", response_model=list[AdminPaymentRead], tags=["admin-payments"])
def list_admin_payments(
    payment_status: str | None = Query(None, alias="status"), operation_id: str | None = None,
    payment_link_id: str | None = None, user_id: int | None = None, payment_method: str | None = None,
    amount: Decimal | None = None, from_date: datetime | None = None, to_date: datetime | None = None,
    admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db),
):
    _ = admin
    query = select(Payment).options(selectinload(Payment.plan)).order_by(Payment.created_at.desc()).limit(500)
    if payment_status: query = query.where(Payment.status == payment_status)
    if operation_id: query = query.where(Payment.provider_operation_id == operation_id)
    if payment_link_id: query = query.where(Payment.payment_link_id == payment_link_id)
    if user_id: query = query.where(Payment.user_id == user_id)
    if payment_method: query = query.where(Payment.payment_method == payment_method)
    if amount is not None: query = query.where(Payment.amount == amount)
    if from_date: query = query.where(Payment.created_at >= from_date)
    if to_date: query = query.where(Payment.created_at <= to_date)
    payments = db.execute(query).scalars().all()
    profiles = {p.id: p for p in db.execute(select(ClientProfile).where(ClientProfile.id.in_([x.client_profile_id for x in payments]))).scalars().all()} if payments else {}
    for payment in payments: payment._admin_profile = profiles.get(payment.client_profile_id)
    return [_admin_read(payment) for payment in payments]


@router.get("/admin/payments/{payment_id}", tags=["admin-payments"])
def read_admin_payment(payment_id: int, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)):
    _ = admin
    payment = db.execute(select(Payment).options(selectinload(Payment.plan), selectinload(Payment.events), selectinload(Payment.refunds)).where(Payment.id == payment_id)).scalar_one_or_none()
    if payment is None: raise HTTPException(status_code=404, detail="Payment not found")
    payment._admin_profile = db.get(ClientProfile, payment.client_profile_id)
    return {"payment": _admin_read(payment).model_dump(mode="json"), "events": [{"id": e.id, "source": e.source, "event_type": e.event_type, "provider_status": e.provider_status, "processing_status": e.processing_status, "processing_error": e.processing_error, "received_at": e.received_at} for e in payment.events], "refunds": [{"id": r.id, "amount": r.amount, "status": r.status, "reason": r.reason, "created_at": r.created_at} for r in payment.refunds]}


@router.post("/admin/payments/{payment_id}/sync", response_model=AdminPaymentRead, tags=["admin-payments"])
async def sync_admin_payment(payment_id: int, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)):
    _ = admin
    payment = db.execute(select(Payment).options(selectinload(Payment.plan)).where(Payment.id == payment_id)).scalar_one_or_none()
    if payment is None: raise HTTPException(status_code=404, detail="Payment not found")
    payment = await refresh_payment(db, payment, source="manual_sync")
    payment._admin_profile = db.get(ClientProfile, payment.client_profile_id)
    return _admin_read(payment)


@router.post("/admin/payments/{payment_id}/refund", tags=["admin-payments"])
async def refund_admin_payment(payment_id: int, payload: RefundCreate, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)):
    payment = db.execute(select(Payment).where(Payment.id == payment_id).with_for_update()).scalar_one_or_none()
    if payment is None: raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status not in {PaymentStatus.approved.value, PaymentStatus.partially_refunded.value}: raise HTTPException(status_code=409, detail="Payment cannot be refunded")
    available = payment.amount - payment.refunded_amount
    if payload.amount > available: raise HTTPException(status_code=422, detail="Refund exceeds available amount")
    if not payment.provider_operation_id: raise HTTPException(status_code=409, detail="Provider operation is missing")
    refund = PaymentRefund(payment_id=payment.id, public_id=str(uuid4()), amount=payload.amount, reason=payload.reason, requested_by_admin_id=admin.id)
    db.add(refund); payment.status = PaymentStatus.refund_pending.value; db.commit(); db.refresh(refund)
    try:
        async with TochkaPaymentsClient() as client:
            result = await client.refund_payment(payment.provider_operation_id, f"{payload.amount:.2f}")
    except TochkaError as exc:
        refund.status = "failed"; payment.status = PaymentStatus.approved.value; db.commit()
        raise HTTPException(status_code=503, detail="Refund provider request failed") from exc
    refund.status = "completed"; refund.completed_at = datetime.now(timezone.utc)
    payment.refunded_amount += payload.amount
    payment.status = PaymentStatus.refunded.value if payment.refunded_amount == payment.amount else PaymentStatus.partially_refunded.value
    if payment.status == PaymentStatus.refunded.value: payment.refunded_at = refund.completed_at
    add_payment_event(db, payment=payment, source="refund_response", event_type="refund", provider_status=payment.provider_status, payload={"refund_id": refund.public_id, "amount": str(payload.amount)}, raw_hash=payload_hash(str(result)), signature_verified=False)
    db.commit()
    return {"refund_id": refund.public_id, "status": refund.status, "amount": str(refund.amount), "payment_status": payment.status}
