from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.models.acquiring import Payment, PaymentStatus, SubscriptionPlan
from app.models.client import ClientProfile
from app.models.payment import Subscription
from app.models.user import User, UserRole
from app.services.payment_fulfillment import PaymentFulfillmentService, apply_provider_state
from app.schemas.acquiring import SubscriptionPlanUpdate
from app.services.tochka_payments import TochkaWebhookSignatureError, verify_webhook


def test_provider_status_mapping_does_not_approve_unknown_status():
    payment = Payment(provider_status=None, status=PaymentStatus.created.value)
    apply_provider_state(payment, {"Data": {"status": "NEW_UNKNOWN_STATUS"}})
    assert payment.status == PaymentStatus.created.value
    assert payment.provider_status == "NEW_UNKNOWN_STATUS"


def test_webhook_rejects_non_rs256_algorithm():
    token = jwt.encode({"webhookType": "acquiringInternetPayment"}, "generated-test-key", algorithm="HS256")
    with pytest.raises(TochkaWebhookSignatureError, match="Unsupported"):
        verify_webhook(token)


def test_fulfillment_is_idempotent_and_uses_database_plan_price():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        user = User(email="payment-user@example.test", role=UserRole.CLIENT.value, is_active=True)
        db.add(user); db.flush()
        profile = ClientProfile(user_id=user.id, full_name="Payment User", is_active=True)
        plan = SubscriptionPlan(code="monthly-test", name="Подписка Bloom Club на 30 дней", price=Decimal("349.00"), currency="RUB", duration_days=30, is_active=True)
        db.add_all([profile, plan]); db.flush()
        payment = Payment(
            public_id="00000000-0000-4000-8000-000000000001", user_id=user.id, client_profile_id=profile.id,
            subscription_plan_id=plan.id, provider="tochka", provider_operation_id="operation-generated-1",
            payment_link_id="blm-generated-1", amount=Decimal("349.00"), currency="RUB",
            purpose=plan.name, status=PaymentStatus.approved.value, provider_status="APPROVED",
            payment_modes=["sbp", "card"], customer_code="customer-test", merchant_id="200000000000001",
            receipt_email="payment-user@example.test", approved_at=datetime.now(timezone.utc), metadata_json={},
        )
        db.add(payment); db.flush()
        service = PaymentFulfillmentService(db)
        first = service.fulfill_approved_payment(payment.id)
        subscription_id = first.subscription_id
        second = service.fulfill_approved_payment(payment.id)
        assert second.subscription_id == subscription_id
        assert db.query(Subscription).count() == 1
        assert second.fulfilled_at is not None


def test_subscription_plan_price_validation():
    assert SubscriptionPlanUpdate(price=Decimal("499.90")).price == Decimal("499.90")
    with pytest.raises(ValueError):
        SubscriptionPlanUpdate(price=Decimal("0"))
    with pytest.raises(ValueError):
        SubscriptionPlanUpdate(price=Decimal("349.999"))
