from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientProfile
from app.models.lead import LeadClick
from app.models.payment import PaymentRequest, PaymentRequestStatus, Subscription, SubscriptionStatus
from app.models.partner import Partner, PartnerOffer, PartnerQrLink
from app.models.verification import PrivilegeVerificationSession, PrivilegeVerificationStatus
from app.schemas.activity import ActivityFeedRead, ActivityItemRead

DEFAULT_ACTIVITY_LIMIT = 30
MAX_ACTIVITY_LIMIT = 100

PRIVILEGE_CREATED = "privilege_created"
PRIVILEGE_CONFIRMED = "privilege_confirmed"
PRIVILEGE_EXPIRED = "privilege_expired"
QR_CLICKED = "qr_clicked"
PARTNER_CREATED = "partner_created"
OFFER_CREATED = "offer_created"
QR_LINK_CREATED = "qr_link_created"
PAYMENT_REQUEST_CREATED = "payment_request_created"
PAYMENT_APPROVED = "payment_approved"
SUBSCRIPTION_ACTIVATED = "subscription_activated"

SUPPORTED_EVENT_TYPES = {
    PRIVILEGE_CREATED,
    PRIVILEGE_CONFIRMED,
    PRIVILEGE_EXPIRED,
    QR_CLICKED,
    PARTNER_CREATED,
    OFFER_CREATED,
    QR_LINK_CREATED,
}


def build_client_activity_feed(db: Session, client_id: int, limit: int = DEFAULT_ACTIVITY_LIMIT) -> ActivityFeedRead:
    items = [
        *_client_payment_items(db, client_id=client_id),
        *_client_subscription_items(db, client_id=client_id),
        *_privilege_items(db, client_id=client_id),
    ]
    return _feed(items, limit)


def build_partner_activity_feed(db: Session, partner_id: int, limit: int = DEFAULT_ACTIVITY_LIMIT) -> ActivityFeedRead:
    items = [
        *_privilege_items(db, partner_id=partner_id),
        *_qr_clicked_items(db, partner_id=partner_id),
        *_offer_created_items(db, partner_id=partner_id),
    ]
    return _feed(items, limit)


def build_admin_activity_feed(
    db: Session,
    limit: int = DEFAULT_ACTIVITY_LIMIT,
    event_type: str | None = None,
    partner_id: int | None = None,
) -> ActivityFeedRead:
    items = [
        *_partner_created_items(db, partner_id=partner_id),
        *_offer_created_items(db, partner_id=partner_id),
        *_qr_link_created_items(db, partner_id=partner_id),
        *_qr_clicked_items(db, partner_id=partner_id),
        *_privilege_items(db, partner_id=partner_id),
    ]
    if event_type is not None:
        items = [item for item in items if item.event_type == event_type]
    return _feed(items, limit)


def normalize_activity_limit(limit: int) -> int:
    if limit < 1:
        return DEFAULT_ACTIVITY_LIMIT
    return min(limit, MAX_ACTIVITY_LIMIT)


def _feed(items: list[ActivityItemRead], limit: int) -> ActivityFeedRead:
    normalized_limit = normalize_activity_limit(limit)
    sorted_items = sorted(items, key=lambda item: (_sort_datetime(item.occurred_at), item.id), reverse=True)
    return ActivityFeedRead(items=sorted_items[:normalized_limit])


def _sort_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _privilege_items(
    db: Session,
    *,
    client_id: int | None = None,
    partner_id: int | None = None,
) -> list[ActivityItemRead]:
    statement = (
        select(
            PrivilegeVerificationSession,
            ClientProfile.full_name.label("client_name"),
            Partner.name.label("partner_name"),
            PartnerOffer.title.label("offer_title"),
        )
        .join(ClientProfile, PrivilegeVerificationSession.client_id == ClientProfile.id)
        .join(Partner, PrivilegeVerificationSession.partner_id == Partner.id)
        .outerjoin(PartnerOffer, PrivilegeVerificationSession.offer_id == PartnerOffer.id)
    )
    if client_id is not None:
        statement = statement.where(PrivilegeVerificationSession.client_id == client_id)
    if partner_id is not None:
        statement = statement.where(PrivilegeVerificationSession.partner_id == partner_id)

    now = datetime.now(timezone.utc)
    items: list[ActivityItemRead] = []
    for session, client_name, partner_name, offer_title in db.execute(statement).all():
        items.append(
            _privilege_item(
                event_type=PRIVILEGE_CREATED,
                session=session,
                occurred_at=session.created_at,
                title="Клиент получил привилегию",
                client_name=client_name,
                partner_name=partner_name,
                offer_title=offer_title,
            )
        )
        if session.status == PrivilegeVerificationStatus.confirmed.value and session.confirmed_at is not None:
            items.append(
                _privilege_item(
                    event_type=PRIVILEGE_CONFIRMED,
                    session=session,
                    occurred_at=session.confirmed_at,
                    title="Привилегия подтверждена",
                    client_name=client_name,
                    partner_name=partner_name,
                    offer_title=offer_title,
                )
            )
        if _is_expired_privilege(session, now):
            items.append(
                _privilege_item(
                    event_type=PRIVILEGE_EXPIRED,
                    session=session,
                    occurred_at=session.expires_at,
                    title="Привилегия истекла",
                    client_name=client_name,
                    partner_name=partner_name,
                    offer_title=offer_title,
                )
            )
    return items


def _privilege_item(
    *,
    event_type: str,
    session: PrivilegeVerificationSession,
    occurred_at: datetime,
    title: str,
    client_name: str | None,
    partner_name: str | None,
    offer_title: str | None,
) -> ActivityItemRead:
    description = _join_description(client_name, partner_name, offer_title)
    return ActivityItemRead(
        id=f"{event_type}:{session.id}",
        event_type=event_type,
        occurred_at=occurred_at,
        title=title,
        description=description,
        partner_id=session.partner_id,
        partner_name=partner_name,
        client_id=session.client_id,
        client_name=client_name,
        offer_id=session.offer_id,
        offer_title=offer_title,
        source=session.source,
        status=session.status,
    )


def _is_expired_privilege(session: PrivilegeVerificationSession, now: datetime) -> bool:
    if session.status == PrivilegeVerificationStatus.expired.value:
        return True
    expires_at = _sort_datetime(session.expires_at)
    return session.status == PrivilegeVerificationStatus.active.value and expires_at <= now


def _qr_clicked_items(db: Session, *, partner_id: int | None = None) -> list[ActivityItemRead]:
    statement = (
        select(LeadClick, Partner.name.label("partner_name"), PartnerQrLink.slug.label("qr_slug"))
        .outerjoin(Partner, LeadClick.partner_id == Partner.id)
        .outerjoin(PartnerQrLink, LeadClick.qr_link_id == PartnerQrLink.id)
    )
    if partner_id is not None:
        statement = statement.where(LeadClick.partner_id == partner_id)

    return [
        ActivityItemRead(
            id=f"{QR_CLICKED}:{click.id}",
            event_type=QR_CLICKED,
            occurred_at=click.created_at,
            title="Переход по QR",
            description=_join_description(partner_name, qr_slug),
            partner_id=click.partner_id,
            partner_name=partner_name,
            qr_link_id=click.qr_link_id,
            qr_slug=qr_slug,
            source=click.source,
        )
        for click, partner_name, qr_slug in db.execute(statement).all()
    ]


def _client_payment_items(db: Session, *, client_id: int) -> list[ActivityItemRead]:
    requests = db.execute(select(PaymentRequest).where(PaymentRequest.client_id == client_id)).scalars().all()
    items: list[ActivityItemRead] = []
    for request in requests:
        amount_text = f"{request.amount} ₽"
        items.append(
            ActivityItemRead(
                id=f"{PAYMENT_REQUEST_CREATED}:{request.id}",
                event_type=PAYMENT_REQUEST_CREATED,
                occurred_at=request.created_at,
                title="Запрос на оплату создан",
                description=f"Сумма: {amount_text}",
                client_id=request.client_id,
                source=request.source,
                status=request.status,
            )
        )
        if request.status == PaymentRequestStatus.approved.value and request.approved_at is not None:
            items.append(
                ActivityItemRead(
                    id=f"{PAYMENT_APPROVED}:{request.id}",
                    event_type=PAYMENT_APPROVED,
                    occurred_at=request.approved_at,
                    title="Оплата подтверждена",
                    description=f"Сумма: {amount_text}",
                    client_id=request.client_id,
                    source=request.source,
                    status=request.status,
                )
            )
    return items


def _client_subscription_items(db: Session, *, client_id: int) -> list[ActivityItemRead]:
    subscriptions = db.execute(select(Subscription).where(Subscription.client_id == client_id)).scalars().all()
    return [
        ActivityItemRead(
            id=f"{SUBSCRIPTION_ACTIVATED}:{subscription.id}",
            event_type=SUBSCRIPTION_ACTIVATED,
            occurred_at=subscription.created_at,
            title="Подписка активирована",
            description=f"Действует до {subscription.ends_at.strftime('%d.%m.%Y')}",
            client_id=subscription.client_id,
            status=subscription.status,
            source="payment_request" if subscription.source_payment_request_id else None,
        )
        for subscription in subscriptions
        if subscription.status in {SubscriptionStatus.active.value, SubscriptionStatus.expired.value}
    ]


def _partner_created_items(db: Session, *, partner_id: int | None = None) -> list[ActivityItemRead]:
    statement = select(Partner)
    if partner_id is not None:
        statement = statement.where(Partner.id == partner_id)
    return [
        ActivityItemRead(
            id=f"{PARTNER_CREATED}:{partner.id}",
            event_type=PARTNER_CREATED,
            occurred_at=partner.created_at,
            title="Добавлен партнёр",
            description=partner.name,
            partner_id=partner.id,
            partner_name=partner.name,
        )
        for partner in db.execute(statement).scalars().all()
    ]


def _offer_created_items(db: Session, *, partner_id: int | None = None) -> list[ActivityItemRead]:
    statement = select(PartnerOffer, Partner.name.label("partner_name")).join(Partner, PartnerOffer.partner_id == Partner.id)
    if partner_id is not None:
        statement = statement.where(PartnerOffer.partner_id == partner_id)
    return [
        ActivityItemRead(
            id=f"{OFFER_CREATED}:{offer.id}",
            event_type=OFFER_CREATED,
            occurred_at=offer.created_at,
            title="Добавлено предложение",
            description=_join_description(partner_name, offer.title),
            partner_id=offer.partner_id,
            partner_name=partner_name,
            offer_id=offer.id,
            offer_title=offer.title,
        )
        for offer, partner_name in db.execute(statement).all()
    ]


def _qr_link_created_items(db: Session, *, partner_id: int | None = None) -> list[ActivityItemRead]:
    statement = select(PartnerQrLink, Partner.name.label("partner_name")).join(Partner, PartnerQrLink.partner_id == Partner.id)
    if partner_id is not None:
        statement = statement.where(PartnerQrLink.partner_id == partner_id)
    return [
        ActivityItemRead(
            id=f"{QR_LINK_CREATED}:{link.id}",
            event_type=QR_LINK_CREATED,
            occurred_at=link.created_at,
            title="Создана QR-ссылка",
            description=_join_description(part=partner_name, extra=link.slug),
            partner_id=link.partner_id,
            partner_name=partner_name,
            qr_link_id=link.id,
            qr_slug=link.slug,
        )
        for link, partner_name in db.execute(statement).all()
    ]


def _join_description(*parts: str | None, part: str | None = None, extra: str | None = None) -> str | None:
    values = [*parts]
    if part is not None:
        values.append(part)
    if extra is not None:
        values.append(extra)
    cleaned = [value for value in values if value]
    if not cleaned:
        return None
    return " · ".join(cleaned)
