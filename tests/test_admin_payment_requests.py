from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all SQLAlchemy models for test metadata
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.client import ClientProfile
from app.models.city import City
from app.models.payment import (
    PaymentReceipt,
    PaymentRequest,
    PaymentRequestStatus,
    Subscription,
    SubscriptionStatus,
)
from app.models.user import AdminUser, User, UserRole


@dataclass
class AdminPaymentHarness:
    client: TestClient
    session_factory: sessionmaker[Session]


@pytest.fixture()
def admin_payment_harness() -> Generator[AdminPaymentHarness, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    Base.metadata.create_all(bind=engine)
    with session_factory() as session:
        session.add_all(
            [
                AdminUser(
                    email="admin@example.com",
                    password_hash=hash_password("AdminPassword123"),
                    role=UserRole.ADMIN.value,
                    is_active=True,
                ),
                AdminUser(
                    email="partner-admin-row@example.com",
                    password_hash=hash_password("PartnerPassword123"),
                    role=UserRole.PARTNER.value,
                    is_active=True,
                ),
                User(
                    email="vk_client@vk.local",
                    phone="+79990000001",
                    password_hash=hash_password("ClientPassword123"),
                    role=UserRole.CLIENT.value,
                    is_active=True,
                ),
                User(
                    email="other-client@example.com",
                    phone="+79990000002",
                    password_hash=hash_password("OtherClientPassword123"),
                    role=UserRole.CLIENT.value,
                    is_active=True,
                ),
            ]
        )
        session.flush()
        session.add_all(
            [
                City(name="Новосибирск", slug="novosibirsk", is_active=True),
                ClientProfile(
                    user_id=1,
                    full_name="Client One",
                    contact_email="client.one@mail.test",
                    selected_city_id=1,
                    vk_user_id="vk-client-one",
                    source="seed",
                    is_active=True,
                ),
                ClientProfile(
                    user_id=2,
                    contact_email="other-client@mail.test",
                    selected_city_id=1,
                    source="seed",
                    is_active=True,
                ),
            ]
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield AdminPaymentHarness(client=client, session_factory=session_factory)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_token(harness: AdminPaymentHarness) -> str:
    response = harness.client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPassword123"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _partner_admin_row_token(harness: AdminPaymentHarness) -> str:
    response = harness.client.post(
        "/api/v1/auth/login",
        json={
            "email": "partner-admin-row@example.com",
            "password": "PartnerPassword123",
        },
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _client_token(harness: AdminPaymentHarness) -> str:
    response = harness.client.post(
        "/api/v1/auth/user-login",
        json={"login": "vk_client@vk.local", "password": "ClientPassword123"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _create_payment_request(
    harness: AdminPaymentHarness,
    *,
    client_id: int = 1,
    status: str = PaymentRequestStatus.paid.value,
    amount: Decimal = Decimal("2990.00"),
    comment: str | None = None,
    with_receipt: bool = False,
) -> int:
    with harness.session_factory() as session:
        payment_request = PaymentRequest(
            client_id=client_id,
            amount=amount,
            status=status,
            source="manual",
            comment=comment,
        )
        session.add(payment_request)
        session.flush()
        if with_receipt:
            session.add(
                PaymentReceipt(
                    payment_request_id=payment_request.id,
                    file_url="https://example.com/receipt.jpg",
                    uploaded_via="web",
                )
            )
        session.commit()
        return payment_request.id


def _parse_dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def test_admin_payment_requests_without_token_returns_401(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    response = admin_payment_harness.client.get("/api/v1/admin/payment-requests")

    assert response.status_code == 401


def test_non_admin_cannot_access_admin_payment_requests(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    token = _partner_admin_row_token(admin_payment_harness)

    response = admin_payment_harness.client.get(
        "/api/v1/admin/payment-requests",
        headers=_auth_headers(token),
    )

    assert response.status_code == 403


def test_unified_client_token_cannot_access_admin_payment_requests(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    token = _client_token(admin_payment_harness)

    response = admin_payment_harness.client.get(
        "/api/v1/admin/payment-requests",
        headers=_auth_headers(token),
    )

    assert response.status_code == 401


def test_admin_can_list_all_payment_requests(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    older_id = _create_payment_request(
        admin_payment_harness, status=PaymentRequestStatus.pending.value
    )
    newer_id = _create_payment_request(
        admin_payment_harness, status=PaymentRequestStatus.paid.value, with_receipt=True
    )
    token = _admin_token(admin_payment_harness)

    response = admin_payment_harness.client.get(
        "/api/v1/admin/payment-requests", headers=_auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data] == [newer_id, older_id]
    assert data[0]["client_full_name"] == "Client One"
    assert data[0]["client_user_id"] == 1
    assert data[0]["client_vk_user_id"] == "vk-client-one"
    assert data[0]["user_email"] == "vk_client@vk.local"
    assert data[0]["user_phone"] == "+79990000001"
    assert data[0]["full_name"] == "Client One"
    assert data[0]["contact_email"] == "client.one@mail.test"
    assert data[0]["selected_city_name"] == "Новосибирск"
    assert data[0]["vk_user_id"] == "vk-client-one"
    assert data[0]["vk_url"] == "https://vk.com/idvk-client-one"
    assert data[0]["display_name"] == "Client One"
    assert data[0]["is_synthetic_email"] is True
    assert data[0]["receipts"][0]["file_url"] == "https://example.com/receipt.jpg"
    assert "password_hash" not in data[0]
    assert "temporary_password" not in data[0]


def test_admin_payment_request_status_filter_works(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    _create_payment_request(
        admin_payment_harness, status=PaymentRequestStatus.pending.value
    )
    paid_id = _create_payment_request(
        admin_payment_harness, status=PaymentRequestStatus.paid.value
    )
    token = _admin_token(admin_payment_harness)

    response = admin_payment_harness.client.get(
        "/api/v1/admin/payment-requests?status=paid",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data] == [paid_id]
    assert data[0]["status"] == PaymentRequestStatus.paid.value
    assert data[0]["vk_url"] == "https://vk.com/idvk-client-one"


def test_admin_payment_request_profile_fallbacks_and_vk_null(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(admin_payment_harness, client_id=2)
    token = _admin_token(admin_payment_harness)

    response = admin_payment_harness.client.get(
        f"/api/v1/admin/payment-requests/{payment_request_id}",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["vk_user_id"] is None
    assert data["vk_url"] is None
    assert data["full_name"] is None
    assert data["display_name"] == "other-client@mail.test"
    assert data["contact_email"] == "other-client@mail.test"
    assert data["selected_city_name"] == "Новосибирск"
    assert data["is_synthetic_email"] is False


def test_admin_can_read_payment_request_detail(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(
        admin_payment_harness, with_receipt=True
    )
    token = _admin_token(admin_payment_harness)

    response = admin_payment_harness.client.get(
        f"/api/v1/admin/payment-requests/{payment_request_id}",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == payment_request_id
    assert data["receipts"][0]["uploaded_via"] == "web"


def test_approve_paid_request_creates_subscription_and_sets_fields(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(admin_payment_harness)
    token = _admin_token(admin_payment_harness)

    response = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/approve",
        headers=_auth_headers(token),
        json={"comment": "Looks good"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == PaymentRequestStatus.approved.value
    assert data["approved_at"] is not None
    assert data["admin_user_id"] == 1
    assert data["access_until"] is not None
    assert "Admin approval comment: Looks good" in data["comment"]
    with admin_payment_harness.session_factory() as session:
        subscription = session.execute(select(Subscription)).scalar_one()
        assert subscription.client_id == 1
        assert subscription.status == SubscriptionStatus.active.value
        assert subscription.source_payment_request_id == payment_request_id
        assert _parse_dt(data["access_until"]) == _parse_dt(
            subscription.ends_at.isoformat()
        )


def test_approve_uses_default_30_days(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(admin_payment_harness)
    token = _admin_token(admin_payment_harness)
    before = datetime.now(timezone.utc)

    response = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/approve",
        headers=_auth_headers(token),
        json={},
    )
    after = datetime.now(timezone.utc)

    assert response.status_code == 200
    access_until = _parse_dt(response.json()["access_until"])
    assert before + timedelta(days=30) <= access_until <= after + timedelta(days=30)


def test_approve_with_custom_access_days(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(admin_payment_harness)
    token = _admin_token(admin_payment_harness)
    before = datetime.now(timezone.utc)

    response = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/approve",
        headers=_auth_headers(token),
        json={"access_days": 10},
    )
    after = datetime.now(timezone.utc)

    assert response.status_code == 200
    access_until = _parse_dt(response.json()["access_until"])
    assert before + timedelta(days=10) <= access_until <= after + timedelta(days=10)


def test_approve_with_custom_access_until(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(admin_payment_harness)
    token = _admin_token(admin_payment_harness)
    custom_until = datetime.now(timezone.utc) + timedelta(days=45)

    response = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/approve",
        headers=_auth_headers(token),
        json={"access_until": custom_until.isoformat()},
    )

    assert response.status_code == 200
    assert _parse_dt(response.json()["access_until"]) == custom_until


def test_approve_extends_from_existing_active_subscription(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(admin_payment_harness)
    token = _admin_token(admin_payment_harness)
    existing_ends_at = datetime.now(timezone.utc) + timedelta(days=5)
    with admin_payment_harness.session_factory() as session:
        session.add(
            Subscription(
                client_id=1,
                status=SubscriptionStatus.active.value,
                starts_at=datetime.now(timezone.utc) - timedelta(days=25),
                ends_at=existing_ends_at,
            )
        )
        session.commit()

    response = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/approve",
        headers=_auth_headers(token),
        json={"access_days": 10},
    )

    assert response.status_code == 200
    with admin_payment_harness.session_factory() as session:
        new_subscription = (
            session.execute(
                select(Subscription).order_by(
                    Subscription.ends_at.desc(), Subscription.id.desc()
                )
            )
            .scalars()
            .first()
        )
        assert new_subscription is not None
        assert _parse_dt(new_subscription.starts_at.isoformat()) == _parse_dt(
            existing_ends_at.isoformat()
        )
        assert _parse_dt(new_subscription.ends_at.isoformat()) == _parse_dt(
            (existing_ends_at + timedelta(days=10)).isoformat()
        )


def test_approve_pending_returns_400(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(
        admin_payment_harness, status=PaymentRequestStatus.pending.value
    )
    token = _admin_token(admin_payment_harness)

    response = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/approve",
        headers=_auth_headers(token),
        json={},
    )

    assert response.status_code == 400


def test_approve_rejected_returns_400(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(
        admin_payment_harness, status=PaymentRequestStatus.rejected.value
    )
    token = _admin_token(admin_payment_harness)

    response = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/approve",
        headers=_auth_headers(token),
        json={},
    )

    assert response.status_code == 400


def test_approve_approved_is_idempotent(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(admin_payment_harness)
    token = _admin_token(admin_payment_harness)
    first = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/approve",
        headers=_auth_headers(token),
        json={},
    )

    second = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/approve",
        headers=_auth_headers(token),
        json={"access_days": 60},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert _parse_dt(second.json()["access_until"]) == _parse_dt(
        first.json()["access_until"]
    )
    with admin_payment_harness.session_factory() as session:
        assert session.query(Subscription).count() == 1


def test_reject_paid_request_sets_fields_and_does_not_create_subscription(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(admin_payment_harness)
    token = _admin_token(admin_payment_harness)

    response = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/reject",
        headers=_auth_headers(token),
        json={"comment": "Cannot match receipt"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == PaymentRequestStatus.rejected.value
    assert data["rejected_at"] is not None
    assert data["admin_user_id"] == 1
    assert "Admin rejection comment: Cannot match receipt" in data["comment"]
    with admin_payment_harness.session_factory() as session:
        assert session.query(Subscription).count() == 0


def test_reject_pending_request_sets_rejected(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(
        admin_payment_harness, status=PaymentRequestStatus.pending.value
    )
    token = _admin_token(admin_payment_harness)

    response = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/reject",
        headers=_auth_headers(token),
        json={},
    )

    assert response.status_code == 200
    assert response.json()["status"] == PaymentRequestStatus.rejected.value


def test_reject_approved_returns_400(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(admin_payment_harness)
    token = _admin_token(admin_payment_harness)
    approved = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/approve",
        headers=_auth_headers(token),
        json={},
    )
    assert approved.status_code == 200

    response = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/reject",
        headers=_auth_headers(token),
        json={},
    )

    assert response.status_code == 400


def test_reject_rejected_is_idempotent(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(admin_payment_harness)
    token = _admin_token(admin_payment_harness)
    first = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/reject",
        headers=_auth_headers(token),
        json={"comment": "No receipt"},
    )

    second = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/reject",
        headers=_auth_headers(token),
        json={"comment": "Second comment ignored"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["comment"] == first.json()["comment"]
    with admin_payment_harness.session_factory() as session:
        assert session.query(Subscription).count() == 0


def test_client_subscription_returns_admin_approved_latest_subscription(
    admin_payment_harness: AdminPaymentHarness,
) -> None:
    payment_request_id = _create_payment_request(admin_payment_harness)
    admin_token = _admin_token(admin_payment_harness)
    client_token = _client_token(admin_payment_harness)
    with admin_payment_harness.session_factory() as session:
        session.add(
            Subscription(
                client_id=1,
                status=SubscriptionStatus.expired.value,
                starts_at=datetime.now(timezone.utc) - timedelta(days=60),
                ends_at=datetime.now(timezone.utc) - timedelta(days=30),
            )
        )
        session.commit()

    approve_response = admin_payment_harness.client.post(
        f"/api/v1/admin/payment-requests/{payment_request_id}/approve",
        headers=_auth_headers(admin_token),
        json={"access_days": 7},
    )
    subscription_response = admin_payment_harness.client.get(
        "/api/v1/clients/me/subscription",
        headers=_auth_headers(client_token),
    )

    assert approve_response.status_code == 200
    assert subscription_response.status_code == 200
    data = subscription_response.json()
    assert data["status"] == SubscriptionStatus.active.value
    assert data["source_payment_request_id"] == payment_request_id
