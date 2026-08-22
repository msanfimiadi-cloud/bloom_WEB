from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.analytics import ClientAnalyticsEvent
from app.models.category import Category
from app.models.client import ClientProfile
from app.models.partner import Partner, PartnerOffer
from app.models.payment import Subscription, SubscriptionStatus
from app.models.verification import PrivilegeVerificationSession, PrivilegeVerificationStatus


CLUB_TIMEZONE = ZoneInfo("Asia/Novosibirsk")
EVENT_LABELS = {
    "partner_view": "Просмотр карточки партнёра",
    "offer_view": "Просмотр услуги",
    "offer_select": "Выбор услуги",
    "contact_click": "Переход по ссылке партнёра",
}


def resolve_statistics_period(
    period: str,
    date_from: date | None,
    date_to: date | None,
    *,
    now: datetime | None = None,
) -> tuple[datetime, datetime, date, date]:
    current = (now or datetime.now(timezone.utc)).astimezone(CLUB_TIMEZONE).date()
    if period == "today":
        first_day = last_day = current
    elif period == "yesterday":
        first_day = last_day = current - timedelta(days=1)
    elif period == "week":
        first_day, last_day = current - timedelta(days=6), current
    elif period == "month":
        first_day, last_day = current - timedelta(days=29), current
    else:
        first_day = date_from or current - timedelta(days=29)
        last_day = date_to or current
    if first_day > last_day:
        raise ValueError("Дата начала не может быть позже даты окончания.")
    start_at = datetime.combine(first_day, time.min, CLUB_TIMEZONE).astimezone(timezone.utc)
    end_at = datetime.combine(last_day + timedelta(days=1), time.min, CLUB_TIMEZONE).astimezone(timezone.utc)
    return start_at, end_at, first_day, last_day


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _percentage(value: int, total: int) -> float:
    return round(value / total * 100, 1) if total else 0.0


def _count(db: Session, statement: Any) -> int:
    return int(db.execute(statement).scalar_one() or 0)


def build_admin_statistics(
    db: Session,
    *,
    period: str,
    date_from: date | None,
    date_to: date | None,
    partner_id: int | None,
    city_id: int | None,
    category_slug: str | None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    start_at, end_at, first_day, last_day = resolve_statistics_period(period, date_from, date_to, now=now)

    partners_statement = select(Partner).options(selectinload(Partner.city), selectinload(Partner.categories))
    if partner_id is not None:
        partners_statement = partners_statement.where(Partner.id == partner_id)
    if city_id is not None:
        partners_statement = partners_statement.where(Partner.city_id == city_id)
    if category_slug:
        partners_statement = partners_statement.where(
            or_(Partner.category_slug == category_slug, Partner.categories.any(Category.slug == category_slug))
        )
    partners = list(db.execute(partners_statement.order_by(Partner.name)).scalars().all())
    partner_ids = [partner.id for partner in partners]

    event_rows: list[ClientAnalyticsEvent] = []
    created_sessions: list[PrivilegeVerificationSession] = []
    confirmed_sessions: list[PrivilegeVerificationSession] = []
    offers: list[PartnerOffer] = []
    if partner_ids:
        event_rows = list(
            db.execute(
                select(ClientAnalyticsEvent)
                .options(selectinload(ClientAnalyticsEvent.client))
                .where(
                    ClientAnalyticsEvent.partner_id.in_(partner_ids),
                    ClientAnalyticsEvent.created_at >= start_at,
                    ClientAnalyticsEvent.created_at < end_at,
                )
                .order_by(ClientAnalyticsEvent.created_at.desc())
            ).scalars().all()
        )
        offers = list(
            db.execute(select(PartnerOffer).where(PartnerOffer.partner_id.in_(partner_ids))).scalars().all()
        )
        created_sessions = list(
            db.execute(
                select(PrivilegeVerificationSession).where(
                    PrivilegeVerificationSession.partner_id.in_(partner_ids),
                    PrivilegeVerificationSession.created_at >= start_at,
                    PrivilegeVerificationSession.created_at < end_at,
                )
            ).scalars().all()
        )
        confirmed_sessions = list(
            db.execute(
                select(PrivilegeVerificationSession).where(
                    PrivilegeVerificationSession.partner_id.in_(partner_ids),
                    PrivilegeVerificationSession.status == PrivilegeVerificationStatus.confirmed.value,
                    PrivilegeVerificationSession.confirmed_at >= start_at,
                    PrivilegeVerificationSession.confirmed_at < end_at,
                )
            ).scalars().all()
        )

    client_conditions = [ClientProfile.status == "active"]
    if city_id is not None:
        client_conditions.append(ClientProfile.selected_city_id == city_id)
    total_users = _count(db, select(func.count()).select_from(ClientProfile).where(*client_conditions))
    new_users = _count(
        db,
        select(func.count()).select_from(ClientProfile).where(
            *client_conditions, ClientProfile.created_at >= start_at, ClientProfile.created_at < end_at
        ),
    )

    subscription_statement = select(Subscription).join(ClientProfile).where(
        *client_conditions,
        Subscription.status == SubscriptionStatus.active.value,
        Subscription.starts_at <= now,
        Subscription.ends_at > now,
    )
    active_subscriptions = list(db.execute(subscription_statement).scalars().all())
    active_trial_users = {subscription.client_id for subscription in active_subscriptions if subscription.source == "trial"}
    active_paid_users = {subscription.client_id for subscription in active_subscriptions if subscription.source != "trial"}

    trial_users = set(
        db.execute(
            select(Subscription.client_id).join(ClientProfile).where(
                *client_conditions,
                Subscription.source == "trial",
                Subscription.created_at >= start_at,
                Subscription.created_at < end_at,
            )
        ).scalars().all()
    )
    converted_trial_users = set()
    if trial_users:
        converted_trial_users = set(
            db.execute(
                select(Subscription.client_id).where(
                    Subscription.client_id.in_(trial_users),
                    Subscription.source.is_not(None),
                    Subscription.source != "trial",
                )
            ).scalars().all()
        )

    events_by_partner: dict[int, list[ClientAnalyticsEvent]] = {item.id: [] for item in partners}
    events_by_offer: dict[int, list[ClientAnalyticsEvent]] = {}
    for event in event_rows:
        events_by_partner.setdefault(event.partner_id, []).append(event)
        if event.offer_id is not None:
            events_by_offer.setdefault(event.offer_id, []).append(event)

    created_by_partner = Counter(item.partner_id for item in created_sessions)
    confirmed_by_partner = Counter(item.partner_id for item in confirmed_sessions)
    created_by_offer = Counter(item.offer_id for item in created_sessions if item.offer_id is not None)
    confirmed_by_offer = Counter(item.offer_id for item in confirmed_sessions if item.offer_id is not None)
    partner_by_id = {item.id: item for item in partners}

    partner_rows = []
    for partner in partners:
        items = events_by_partner.get(partner.id, [])
        views = [event for event in items if event.event_type == "partner_view"]
        clicks = [event for event in items if event.event_type == "contact_click"]
        issued = created_by_partner[partner.id]
        used = confirmed_by_partner[partner.id]
        partner_rows.append(
            {
                "partner_id": partner.id,
                "partner_name": partner.name,
                "city_name": partner.city.name if partner.city is not None else None,
                "category_names": [item.name for item in partner.categories],
                "category_slug": partner.category_slug,
                "views": len(views),
                "unique_viewers": len({event.client_id for event in views if event.client_id is not None}),
                "offer_views": sum(event.event_type == "offer_view" for event in items),
                "offer_selections": sum(event.event_type == "offer_select" for event in items),
                "contact_clicks": len(clicks),
                "contact_click_breakdown": dict(Counter(event.target or "Другое" for event in clicks)),
                "codes_issued": issued,
                "codes_used": used,
                "view_to_code_percent": _percentage(issued, len(views)),
                "code_usage_percent": _percentage(used, issued),
                "last_viewed_at": views[0].created_at if views else None,
            }
        )
    partner_rows.sort(key=lambda item: (-item["views"], -item["codes_issued"], item["partner_name"].lower()))

    offer_rows = []
    for offer in offers:
        items = events_by_offer.get(offer.id, [])
        views = sum(event.event_type == "offer_view" for event in items)
        selected = sum(event.event_type == "offer_select" for event in items)
        issued = created_by_offer[offer.id]
        used = confirmed_by_offer[offer.id]
        offer_rows.append(
            {
                "offer_id": offer.id,
                "offer_title": offer.title,
                "partner_id": offer.partner_id,
                "partner_name": partner_by_id[offer.partner_id].name,
                "views": views,
                "selections": selected,
                "codes_issued": issued,
                "codes_used": used,
                "selection_percent": _percentage(selected, views),
                "code_usage_percent": _percentage(used, issued),
                "is_active": offer.is_active and offer.deleted_at is None,
            }
        )
    offer_rows.sort(key=lambda item: (-item["selections"], -item["views"], -item["codes_issued"]))

    hourly_counter = Counter(
        _as_utc(event.created_at).astimezone(CLUB_TIMEZONE).hour
        for event in event_rows
        if event.event_type == "partner_view"
    )
    category_counter: Counter[str] = Counter()
    for item in partner_rows:
        labels = item["category_names"] or ([item["category_slug"]] if item["category_slug"] else ["Без категории"])
        for label in labels:
            category_counter[label] += item["views"]

    event_type_counts = Counter(event.event_type for event in event_rows)
    recent_events = []
    offer_by_id = {offer.id: offer for offer in offers}
    for event in event_rows[:50]:
        profile = event.client
        recent_events.append(
            {
                "event_type": event.event_type,
                "event_label": EVENT_LABELS.get(event.event_type, event.event_type),
                "partner_id": event.partner_id,
                "partner_name": partner_by_id[event.partner_id].name,
                "offer_title": offer_by_id[event.offer_id].title if event.offer_id in offer_by_id else None,
                "client_name": (
                    profile.full_name
                    or " ".join(filter(None, [profile.telegram_first_name, profile.telegram_last_name]))
                    or (f"@{profile.telegram_username}" if profile.telegram_username else None)
                    if profile is not None
                    else None
                ),
                "target": event.target,
                "created_at": event.created_at,
            }
        )

    return {
        "period": {"key": period, "date_from": first_day, "date_to": last_day, "timezone": "Asia/Novosibirsk"},
        "summary": {
            "total_users": total_users,
            "new_users": new_users,
            "active_subscriptions": len(active_trial_users | active_paid_users),
            "active_trial_subscriptions": len(active_trial_users - active_paid_users),
            "active_paid_subscriptions": len(active_paid_users),
            "trial_users": len(trial_users),
            "trial_to_paid_users": len(converted_trial_users),
            "trial_to_paid_percent": _percentage(len(converted_trial_users), len(trial_users)),
            "partner_views": event_type_counts["partner_view"],
            "unique_partner_viewers": len(
                {event.client_id for event in event_rows if event.event_type == "partner_view" and event.client_id is not None}
            ),
            "offer_views": event_type_counts["offer_view"],
            "offer_selections": event_type_counts["offer_select"],
            "contact_clicks": event_type_counts["contact_click"],
            "codes_issued": len(created_sessions),
            "codes_used": len(confirmed_sessions),
            "partners_without_views": sum(item["views"] == 0 for item in partner_rows),
            "partners_without_codes": sum(item["views"] > 0 and item["codes_issued"] == 0 for item in partner_rows),
        },
        "partners": partner_rows,
        "offers": offer_rows,
        "popular_hours": [{"hour": hour, "views": hourly_counter[hour]} for hour in range(24)],
        "popular_categories": [
            {"category_name": name, "views": count} for name, count in category_counter.most_common()
        ],
        "recent_events": recent_events,
    }
