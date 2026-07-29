from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased, selectinload

from app.api.deps import require_admin
from app.core.categories import WOMEN_CLUB_CATEGORY_SLUGS
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import get_db
from app.models.category import Category
from app.models.city import City
from app.models.client import ClientProfile, ClientReferral
from app.models.giveaway import Giveaway, GiveawayNumber, GiveawayPrize
from app.models.engagement import (
    BloomDailyTask,
    BloomGardenSettings,
    BloomSpecialAnswer,
    BloomSpecialOption,
    BloomSpecialQuestion,
    BloomSpecialSubmission,
    BloomSpecialTask,
    BloomPetalEvent,
    PartnerBotAccess,
)
from app.models.lead import LeadClick
from app.models.landing import LandingSettings
from app.models.partner import Partner, PartnerOffer, PartnerPhoto, PartnerQrLink
from app.models.payment import PaymentRequest, PaymentRequestStatus, Subscription, SubscriptionStatus
from app.models.user import AdminUser, User, UserRole
from app.models.verification import PrivilegeVerificationSession
from app.services.referral_subscription_rewards import process_paid_referral_reward
from app.schemas.activity import ActivityFeedRead
from app.schemas.admin import (
    AdminManagedUserCreate,
    AdminManagedUserRead,
    AdminManagedUserUpdate,
    AdminSubscriptionDaysAdjustRead,
    AdminSubscriptionDaysAdjustRequest,
    AdminDeleteUserResponse,
    AdminVerificationRead,
    ContentReviewOfferRead,
    ContentReviewPhotoRead,
    ContentReviewRead,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    CityCreate,
    CityRead,
    CityUpdate,
    LeadStatsRead,
    PartnerCreate,
    PartnerOfferCreate,
    PartnerOfferRead,
    PartnerOfferUpdate,
    PartnerPhotoRead,
    PartnerPhotoUpdate,
    PartnerPhotoUploadResponse,
    PartnerQrLinkCreate,
    PartnerQrLinkRead,
    PartnerQrLinkUpdate,
    PartnerRead,
    PartnerUpdate,
)
from app.schemas.auth import AdminUserRead
from app.schemas.giveaway import GiveawayRead, GiveawayWrite, GiveawayPrizeRead, GiveawayPrizeWrite
from app.schemas.engagement import (
    AdminPetalAwardRead,
    AdminPetalAwardWrite,
    AdminPetalRevokeRead,
    AdminPetalRevokeWrite,
    BloomTaskPatch,
    BloomTaskRead,
    BloomTaskWrite,
    BloomGardenSettingsPatch,
    BloomGardenSettingsRead,
    BloomSpecialAnalyticsRead,
    BloomSpecialOptionAnalyticsRead,
    BloomSpecialQuestionAnalyticsRead,
    BloomSpecialQuestionWrite,
    BloomSpecialSubmissionRead,
    BloomSpecialTaskPatch,
    BloomSpecialTaskRead,
    BloomSpecialTaskWrite,
    FlowerLeaderboardRewardRead,
    FlowerLeaderboardSettleRequest,
    PartnerBotAccessPatch,
    PartnerBotAccessRead,
    PartnerBotAccessWrite,
)
from app.schemas.landing import LandingSettingsRead, LandingSettingsUpdate
from app.schemas.partner import PartnerAnalyticsRead
from app.schemas.payment import AdminPaymentRequestRead, PaymentRequestApprove, PaymentRequestReject
from app.services.activity_feed import build_admin_activity_feed
from app.services.admin_user_delete_service import delete_user_with_relations
from app.services.landing_settings import build_admin_landing_settings_read, get_or_create_landing_settings, normalize_giveaway_items
from app.services.image_uploads import save_partner_image_upload, save_partner_offer_image_upload, save_partner_photo_image_upload, validate_image_kind
from app.services.partner_analytics import build_partner_analytics
from app.services.partner_access_codes import prepare_partner_access_code
from app.services.privilege_verifications import (
    apply_verification_status_filter,
    as_aware_utc,
    normalize_expired_verifications,
    ttl_seconds,
)
from app.services.social_subscriptions import recheck_giveaway_social_subscriptions, is_number_active
from app.services.engagement import club_today, garden_settings, settle_flower_leaderboard
from app.services.engagement import month_start_for
from app.services.qr_links import (
    generate_qr_slug,
    is_valid_qr_slug,
    normalize_qr_slug,
    qr_link_to_read,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _partner_access_read(access: PartnerBotAccess) -> PartnerBotAccessRead:
    return PartnerBotAccessRead(
        id=access.id,
        partner_id=access.partner_id,
        partner_name=access.partner.name,
        provider=access.provider,
        provider_user_id=access.provider_user_id,
        username=access.username,
        display_name=access.display_name,
        is_active=access.is_active,
        activation_count=access.activation_count,
        last_activity_at=access.last_activity_at,
        created_at=access.created_at,
    )


@router.get("/partner-accesses", response_model=list[PartnerBotAccessRead])
def list_partner_accesses(admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> list[PartnerBotAccessRead]:
    _ = admin
    rows = db.execute(select(PartnerBotAccess).options(selectinload(PartnerBotAccess.partner)).order_by(PartnerBotAccess.created_at.desc())).scalars().all()
    return [_partner_access_read(row) for row in rows]


@router.post("/partner-accesses", response_model=PartnerBotAccessRead, status_code=status.HTTP_201_CREATED)
def create_partner_access(payload: PartnerBotAccessWrite, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> PartnerBotAccessRead:
    _ = admin
    partner = db.get(Partner, payload.partner_id)
    if partner is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    access = PartnerBotAccess(**payload.model_dump())
    access.provider_user_id = access.provider_user_id.strip()
    access.display_name = access.display_name.strip()
    access.username = (access.username or "").strip() or None
    db.add(access)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This bot account already has partner access") from None
    db.refresh(access)
    access.partner = partner
    return _partner_access_read(access)


@router.patch("/partner-accesses/{access_id}", response_model=PartnerBotAccessRead)
def update_partner_access(access_id: int, payload: PartnerBotAccessPatch, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> PartnerBotAccessRead:
    _ = admin
    access = db.get(PartnerBotAccess, access_id)
    if access is None:
        raise HTTPException(status_code=404, detail="Partner access not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "partner_id" and db.get(Partner, value) is None:
            raise HTTPException(status_code=404, detail="Partner not found")
        setattr(access, field, value.strip() if isinstance(value, str) else value)
    db.commit()
    access = db.execute(select(PartnerBotAccess).options(selectinload(PartnerBotAccess.partner)).where(PartnerBotAccess.id == access_id)).scalar_one()
    return _partner_access_read(access)


@router.get("/flower/tasks", response_model=list[BloomTaskRead])
def list_flower_tasks(admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> list[BloomTaskRead]:
    _ = admin
    return list(db.execute(select(BloomDailyTask).order_by(BloomDailyTask.sort_order, BloomDailyTask.id)).scalars().all())


@router.post("/flower/tasks", response_model=BloomTaskRead, status_code=status.HTTP_201_CREATED)
def create_flower_task(payload: BloomTaskWrite, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> BloomTaskRead:
    _ = admin
    task = BloomDailyTask(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/flower/tasks/{task_id}", response_model=BloomTaskRead)
def update_flower_task(task_id: int, payload: BloomTaskPatch, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> BloomTaskRead:
    _ = admin
    task = db.get(BloomDailyTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Flower task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/flower/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flower_task(task_id: int, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> None:
    _ = admin
    task = db.get(BloomDailyTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Flower task not found")
    db.execute(update(BloomPetalEvent).where(BloomPetalEvent.task_id == task_id).values(task_id=None))
    db.delete(task)
    db.commit()


@router.get("/flower/settings", response_model=BloomGardenSettingsRead)
def read_flower_settings(admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> BloomGardenSettingsRead:
    _ = admin
    settings_row = garden_settings(db)
    if settings_row not in db:
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return BloomGardenSettingsRead.model_validate(settings_row, from_attributes=True)


@router.patch("/flower/settings", response_model=BloomGardenSettingsRead)
def update_flower_settings(payload: BloomGardenSettingsPatch, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> BloomGardenSettingsRead:
    _ = admin
    settings_row = garden_settings(db)
    if settings_row not in db:
        db.add(settings_row)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings_row, field, value)
    db.commit()
    db.refresh(settings_row)
    return BloomGardenSettingsRead.model_validate(settings_row, from_attributes=True)


@router.post("/flower/petals/award", response_model=AdminPetalAwardRead, status_code=status.HTTP_201_CREATED)
def award_flower_petals(
    payload: AdminPetalAwardWrite,
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminPetalAwardRead:
    profile = db.execute(
        select(ClientProfile).where(ClientProfile.user_id == payload.user_id)
    ).scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Client profile not found")

    today = club_today()
    month_start = month_start_for(today)
    event = BloomPetalEvent(
        client_id=profile.id,
        event_date=today,
        month_start=month_start,
        source="admin",
        idempotency_key=f"admin:{admin.id}:{uuid4().hex}",
        petals=payload.petals,
        awarded_by_admin_id=admin.id,
        note=payload.note,
    )
    db.add(event)
    db.flush()
    total_petals = db.execute(
        select(func.coalesce(func.sum(BloomPetalEvent.petals), 0)).where(
            BloomPetalEvent.client_id == profile.id,
            BloomPetalEvent.month_start == month_start,
        )
    ).scalar_one()
    db.commit()
    db.refresh(event)
    return AdminPetalAwardRead(
        event_id=event.id,
        user_id=payload.user_id,
        client_id=profile.id,
        petals=event.petals,
        total_petals=int(total_petals or 0),
        note=event.note or "",
        created_at=event.created_at,
    )


@router.post("/flower/petals/revoke", response_model=AdminPetalRevokeRead, status_code=status.HTTP_201_CREATED)
def revoke_flower_petals(
    payload: AdminPetalRevokeWrite,
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminPetalRevokeRead:
    profile = db.execute(
        select(ClientProfile).where(ClientProfile.user_id == payload.user_id).with_for_update()
    ).scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Client profile not found")

    today = club_today()
    month_start = month_start_for(today)
    total_petals = int(db.execute(
        select(func.coalesce(func.sum(BloomPetalEvent.petals), 0)).where(
            BloomPetalEvent.client_id == profile.id,
            BloomPetalEvent.month_start == month_start,
        )
    ).scalar_one() or 0)
    if payload.petals > total_petals:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Нельзя забрать {payload.petals} лепестков: у участницы только {total_petals}",
        )

    event = BloomPetalEvent(
        client_id=profile.id,
        event_date=today,
        month_start=month_start,
        source="admin_revoke",
        idempotency_key=f"admin-revoke:{admin.id}:{uuid4().hex}",
        petals=-payload.petals,
        awarded_by_admin_id=admin.id,
        note=payload.note,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return AdminPetalRevokeRead(
        event_id=event.id,
        user_id=payload.user_id,
        client_id=profile.id,
        petals_removed=payload.petals,
        total_petals=total_petals - payload.petals,
        note=event.note or "",
        created_at=event.created_at,
    )


def _special_task_read(db: Session, task: BloomSpecialTask) -> BloomSpecialTaskRead:
    count = db.execute(select(func.count(BloomSpecialSubmission.id)).where(BloomSpecialSubmission.task_id == task.id)).scalar_one()
    result = BloomSpecialTaskRead.model_validate(task, from_attributes=True)
    return result.model_copy(update={"submissions_count": int(count or 0)})


def _ensure_no_special_task_overlap(db: Session, starts_on: date, ends_on: date, *, exclude_id: int | None = None) -> None:
    query = select(BloomSpecialTask.id).where(
        BloomSpecialTask.is_active.is_(True),
        BloomSpecialTask.starts_on <= ends_on,
        BloomSpecialTask.ends_on >= starts_on,
    )
    if exclude_id is not None:
        query = query.where(BloomSpecialTask.id != exclude_id)
    if db.execute(query).scalars().first() is not None:
        raise HTTPException(status_code=409, detail="Another active special task overlaps this period")


@router.get("/flower/special-tasks", response_model=list[BloomSpecialTaskRead])
def list_special_tasks(admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> list[BloomSpecialTaskRead]:
    _ = admin
    tasks = db.execute(
        select(BloomSpecialTask)
        .options(selectinload(BloomSpecialTask.questions).selectinload(BloomSpecialQuestion.options))
        .order_by(BloomSpecialTask.starts_on.desc(), BloomSpecialTask.id.desc())
    ).scalars().all()
    return [_special_task_read(db, task) for task in tasks]


@router.post("/flower/special-tasks", response_model=BloomSpecialTaskRead, status_code=status.HTTP_201_CREATED)
def create_special_task(payload: BloomSpecialTaskWrite, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> BloomSpecialTaskRead:
    _ = admin
    if payload.ends_on < payload.starts_on:
        raise HTTPException(status_code=422, detail="ends_on must not be before starts_on")
    if payload.is_active:
        _ensure_no_special_task_overlap(db, payload.starts_on, payload.ends_on)
    task = BloomSpecialTask(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return _special_task_read(db, task)


@router.patch("/flower/special-tasks/{task_id}", response_model=BloomSpecialTaskRead)
def update_special_task(task_id: int, payload: BloomSpecialTaskPatch, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> BloomSpecialTaskRead:
    _ = admin
    task = db.execute(select(BloomSpecialTask).options(selectinload(BloomSpecialTask.questions).selectinload(BloomSpecialQuestion.options)).where(BloomSpecialTask.id == task_id)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Special task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    if task.ends_on < task.starts_on:
        raise HTTPException(status_code=422, detail="ends_on must not be before starts_on")
    if task.is_active:
        _ensure_no_special_task_overlap(db, task.starts_on, task.ends_on, exclude_id=task.id)
    db.commit()
    db.refresh(task)
    return _special_task_read(db, task)


@router.delete("/flower/special-tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_special_task(task_id: int, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> None:
    _ = admin
    if db.get(BloomSpecialTask, task_id) is None:
        raise HTTPException(status_code=404, detail="Special task not found")

    submission_ids = select(BloomSpecialSubmission.id).where(BloomSpecialSubmission.task_id == task_id)
    question_ids = select(BloomSpecialQuestion.id).where(BloomSpecialQuestion.task_id == task_id)
    db.execute(delete(BloomSpecialAnswer).where(BloomSpecialAnswer.submission_id.in_(submission_ids)))
    db.execute(delete(BloomSpecialSubmission).where(BloomSpecialSubmission.task_id == task_id))
    db.execute(delete(BloomSpecialOption).where(BloomSpecialOption.question_id.in_(question_ids)))
    db.execute(delete(BloomSpecialQuestion).where(BloomSpecialQuestion.task_id == task_id))
    db.execute(delete(BloomSpecialTask).where(BloomSpecialTask.id == task_id))
    db.commit()


@router.post("/flower/special-tasks/{task_id}/questions", response_model=BloomSpecialTaskRead, status_code=status.HTTP_201_CREATED)
def add_special_question(task_id: int, payload: BloomSpecialQuestionWrite, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> BloomSpecialTaskRead:
    _ = admin
    task = db.get(BloomSpecialTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Special task not found")
    sort_order = int(db.execute(select(func.count(BloomSpecialQuestion.id)).where(BloomSpecialQuestion.task_id == task_id)).scalar_one() or 0)
    question = BloomSpecialQuestion(task_id=task_id, prompt=payload.prompt.strip(), sort_order=sort_order)
    db.add(question)
    db.flush()
    for index, label in enumerate(payload.options):
        db.add(BloomSpecialOption(question_id=question.id, label=label, sort_order=index))
    db.commit()
    task = db.execute(select(BloomSpecialTask).options(selectinload(BloomSpecialTask.questions).selectinload(BloomSpecialQuestion.options)).where(BloomSpecialTask.id == task_id)).scalar_one()
    return _special_task_read(db, task)


@router.get("/flower/special-tasks/{task_id}/analytics", response_model=BloomSpecialAnalyticsRead)
def special_task_analytics(task_id: int, admin: AdminUser = Depends(require_admin), db: Session = Depends(get_db)) -> BloomSpecialAnalyticsRead:
    _ = admin
    task = db.execute(select(BloomSpecialTask).options(selectinload(BloomSpecialTask.questions).selectinload(BloomSpecialQuestion.options)).where(BloomSpecialTask.id == task_id)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Special task not found")
    submissions = db.execute(
        select(BloomSpecialSubmission)
        .options(selectinload(BloomSpecialSubmission.answers))
        .where(BloomS…18106 tokens truncated…mp(exclude_unset=True)
    _validate_offer_amounts(
        update_data.get("base_price", offer.base_price),
        update_data.get("discount_percent", offer.discount_percent),
        update_data.get("requires_order_amount", offer.requires_order_amount),
    )

    if "title" in update_data:
        offer.title = _strip_offer_title(update_data["title"])
    for field in PARTNER_OFFER_TEXT_FIELDS:
        if field in update_data:
            setattr(offer, field, _normalize_optional_text(update_data[field]))
    for field in ("base_price", "discount_percent", "requires_order_amount", "is_active", "sort_order"):
        if field in update_data:
            setattr(offer, field, update_data[field])

    db.commit()
    db.refresh(offer)
    return _get_partner_offer_read_or_404(db, offer.id)


def _admin_verification_to_read(
    session: PrivilegeVerificationSession,
    client_name: str | None,
    partner_name: str | None,
    city_id: int | None,
    city_name: str | None,
    offer_title: str | None,
) -> AdminVerificationRead:
    return AdminVerificationRead.model_validate(
        {
            "id": session.id,
            "client_id": session.client_id,
            "client_name": client_name,
            "partner_id": session.partner_id,
            "partner_name": partner_name,
            "city_id": city_id,
            "city_name": city_name,
            "offer_id": session.offer_id,
            "offer_title": offer_title,
            "code": session.code,
            "status": session.status,
            "source": session.source,
            "expires_at": session.expires_at,
            "confirmed_at": session.confirmed_at,
            "created_at": session.created_at,
            "ttl_seconds": ttl_seconds(session.expires_at),
        }
    )


def _get_admin_payment_request_or_404(db: Session, payment_request_id: int) -> PaymentRequest:
    payment_request = db.execute(
        select(PaymentRequest)
        .options(
            selectinload(PaymentRequest.receipts),
            selectinload(PaymentRequest.client).selectinload(ClientProfile.user),
            selectinload(PaymentRequest.client).selectinload(ClientProfile.selected_city),
        )
        .where(PaymentRequest.id == payment_request_id)
    ).scalar_one_or_none()
    if payment_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment request not found")
    return payment_request


def _admin_payment_request_to_read(payment_request: PaymentRequest) -> AdminPaymentRequestRead:
    client = payment_request.client
    user = client.user if client is not None else None
    city = client.selected_city if client is not None else None
    client_full_name = client.full_name if client is not None else None
    user_email = user.email if user is not None else None
    is_synthetic_email = bool(user_email and user_email.endswith("@vk.local"))
    vk_user_id = client.vk_user_id if client is not None else None
    vk_url = f"https://vk.com/id{vk_user_id}" if vk_user_id else None
    display_name = client_full_name or (client.contact_email if client is not None else None) or user_email
    if display_name is None and client is not None:
        display_name = f"Пользователь #{client.id}"
    return AdminPaymentRequestRead.model_validate(
        {
            "id": payment_request.id,
            "client_id": payment_request.client_id,
            "amount": payment_request.amount,
            "status": payment_request.status,
            "source": payment_request.source,
            "comment": payment_request.comment,
            "created_at": payment_request.created_at,
            "updated_at": payment_request.updated_at,
            "approved_at": payment_request.approved_at,
            "rejected_at": payment_request.rejected_at,
            "admin_user_id": payment_request.admin_user_id,
            "access_until": payment_request.access_until,
            "receipts": payment_request.receipts,
            "client_name": client_full_name,
            "client_full_name": client_full_name,
            "client_user_id": client.user_id if client is not None else None,
            "client_vk_user_id": vk_user_id,
            "user_id": client.user_id if client is not None else None,
            "user_email": user_email,
            "user_login": user_email,
            "user_phone": user.phone if user is not None else None,
            "full_name": client_full_name,
            "contact_email": client.contact_email if client is not None else None,
            "selected_city_name": city.name if city is not None else None,
            "vk_user_id": vk_user_id,
            "vk_url": vk_url,
            "display_name": display_name,
            "is_synthetic_email": is_synthetic_email,
        }
    )


def _append_admin_payment_request_comment(payment_request: PaymentRequest, comment: str | None, *, prefix: str) -> None:
    normalized_comment = _normalize_optional_text(comment)
    if normalized_comment is None:
        return
    comment_line = f"{prefix}: {normalized_comment}"
    if payment_request.comment:
        if comment_line in payment_request.comment:
            return
        payment_request.comment = f"{payment_request.comment}\n\n{comment_line}"
    else:
        payment_request.comment = comment_line


def _normalize_user_email(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


def _normalize_user_phone(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _ensure_user_contact_present(email: str | None, phone: str | None) -> None:
    if email is None and phone is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or phone is required",
        )


def _normalize_user_role(value: str | None) -> str:
    normalized = value.strip().lower() if value is not None else ""
    if normalized not in ALLOWED_USER_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user role")
    return normalized


def _normalize_user_password(value: str) -> str:
    normalized = value.strip()
    if len(normalized) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    return normalized


def _ensure_unique_user_identity(
    db: Session,
    *,
    email: str | None,
    phone: str | None,
    exclude_user_id: int | None = None,
) -> None:
    conditions = []
    if email is not None:
        conditions.append(User.email == email)
    if phone is not None:
        conditions.append(User.phone == phone)
    if not conditions:
        return

    statement = select(User.id).where(or_(*conditions))
    if exclude_user_id is not None:
        statement = statement.where(User.id != exclude_user_id)
    duplicate_id = db.execute(statement.limit(1)).scalar_one_or_none()
    if duplicate_id is not None:
        raise _user_duplicate_error()


def _user_duplicate_error() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=USER_DUPLICATE_DETAIL)


def _qr_slug_duplicate_error() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="QR slug already exists")


def _invalid_qr_slug_error() -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid QR slug")


def _ensure_unique_qr_slug(db: Session, slug: str, exclude_qr_link_id: int | None = None) -> None:
    statement = select(PartnerQrLink.id).where(PartnerQrLink.slug == slug)
    if exclude_qr_link_id is not None:
        statement = statement.where(PartnerQrLink.id != exclude_qr_link_id)
    duplicate_id = db.execute(statement.limit(1)).scalar_one_or_none()
    if duplicate_id is not None:
        raise _qr_slug_duplicate_error()


def _normalize_existing_qr_slug(
    db: Session,
    slug: str | None,
    *,
    exclude_qr_link_id: int | None = None,
) -> str:
    normalized = normalize_qr_slug(slug)
    if not is_valid_qr_slug(normalized):
        raise _invalid_qr_slug_error()
    assert normalized is not None
    _ensure_unique_qr_slug(db, normalized, exclude_qr_link_id=exclude_qr_link_id)
    return normalized


def _normalize_or_generate_qr_slug(db: Session, partner_id: int, slug: str | None) -> str:
    if slug is not None:
        return _normalize_existing_qr_slug(db, slug)
    for _ in range(5):
        generated = generate_qr_slug(partner_id)
        if is_valid_qr_slug(generated):
            existing_id = db.execute(
                select(PartnerQrLink.id).where(PartnerQrLink.slug == generated).limit(1)
            ).scalar_one_or_none()
            if existing_id is None:
                return generated
    raise _qr_slug_duplicate_error()


def _strip_required(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"City {field_name} must not be empty",
        )
    return normalized


def _ensure_unique_city_identity(
    db: Session,
    *,
    name: str,
    slug: str,
    exclude_city_id: int | None = None,
) -> None:
    statement = select(City.id).where(or_(City.name == name, City.slug == slug))
    if exclude_city_id is not None:
        statement = statement.where(City.id != exclude_city_id)
    duplicate_id = db.execute(statement.limit(1)).scalar_one_or_none()
    if duplicate_id is not None:
        raise _city_duplicate_error()


def _city_duplicate_error() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=CITY_DUPLICATE_DETAIL)


def _ensure_city_exists(db: Session, city_id: int) -> City:
    city = db.get(City, city_id)
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
    return city


def _get_partner_owner(db: Session, owner_user_id: int) -> User:
    owner = db.get(User, owner_user_id)
    if owner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner user not found")
    if owner.role != UserRole.PARTNER.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner user must have partner role",
        )
    return owner


def _strip_partner_name(value: str | None) -> str:
    normalized = value.strip() if value is not None else ""
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Partner name must not be empty",
        )
    return normalized


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _strip_category_required(value: str | None, field_name: str) -> str:
    normalized = value.strip() if value is not None else ""
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category {field_name} must not be empty",
        )
    return normalized


def _ensure_unique_category_slug(
    db: Session,
    *,
    slug: str,
    exclude_category_id: int | None = None,
) -> None:
    statement = select(Category.id).where(Category.slug == slug)
    if exclude_category_id is not None:
        statement = statement.where(Category.id != exclude_category_id)
    duplicate_id = db.execute(statement.limit(1)).scalar_one_or_none()
    if duplicate_id is not None:
        raise _category_duplicate_error()


def _category_duplicate_error() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=CATEGORY_DUPLICATE_DETAIL)


def _normalize_category_slug(db: Session, value: str | None) -> str | None:
    normalized = _normalize_optional_text(value)
    if normalized is None:
        return None
    category_count = db.execute(select(func.count()).select_from(Category)).scalar_one()
    if category_count == 0:
        if normalized not in WOMEN_CLUB_CATEGORY_SLUGS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown category slug")
        return normalized

    category_id = db.execute(
        select(Category.id).where(Category.slug == normalized, Category.is_active.is_(True)).limit(1)
    ).scalar_one_or_none()
    if category_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown category slug")
    return normalized


def _ensure_partner_exists(db: Session, partner_id: int) -> Partner:
    partner = db.get(Partner, partner_id)
    if partner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
    return partner


def _strip_offer_title(value: str | None) -> str:
    normalized = value.strip() if value is not None else ""
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offer title must not be empty",
        )
    return normalized


def _validate_offer_amounts(
    base_price: Decimal | None = None,
    discount_percent: Decimal | None = None,
    requires_order_amount: bool = False,
) -> None:
    if base_price is not None and base_price < Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="base_price must be greater than or equal to 0",
        )
    if discount_percent is not None and (
        discount_percent < Decimal("0") or discount_percent > Decimal("100")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="discount_percent must be between 0 and 100",
        )
    if requires_order_amount and (
        discount_percent is None or discount_percent <= Decimal("0")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="discount_percent is required when requires_order_amount is true",
        )


def _get_partner_offer_read_or_404(db: Session, offer_id: int) -> PartnerOfferRead:
    statement = (
        select(PartnerOffer, Partner.name.label("partner_name"))
        .join(Partner, PartnerOffer.partner_id == Partner.id)
        .where(PartnerOffer.id == offer_id)
    )
    row = db.execute(statement).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    offer, partner_name = row
    return _partner_offer_to_read(offer, partner_name=partner_name)


def _partner_offer_to_read(offer: PartnerOffer, partner_name: str | None) -> PartnerOfferRead:
    return PartnerOfferRead.model_validate(
        {
            "id": offer.id,
            "partner_id": offer.partner_id,
            "title": offer.title,
            "description": offer.description,
            "benefit_text": offer.benefit_text,
            "conditions": offer.conditions,
            "base_price": offer.base_price,
            "discount_percent": offer.discount_percent,
            "requires_order_amount": offer.requires_order_amount,
            "image_url": offer.image_url,
            "is_active": offer.is_active,
            "sort_order": offer.sort_order,
            "partner_name": partner_name,
        }
    )


def _get_partner_read_or_404(db: Session, partner_id: int) -> PartnerRead:
    statement = (
        select(Partner, City.name.label("city_name"), User.email.label("owner_email"))
        .join(City, Partner.city_id == City.id)
        .outerjoin(User, Partner.owner_user_id == User.id)
        .options(selectinload(Partner.categories))
        .where(Partner.id == partner_id)
    )
    row = db.execute(statement).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
    partner, city_name, owner_email = row
    return _partner_to_read(partner, city_name, owner_email)


def _category_to_api_payload(category: Category | None) -> dict[str, object] | None:
    if category is None:
        return None
    name = getattr(category, "name", None) or getattr(category, "title", None) or getattr(category, "slug", None)
    title = getattr(category, "title", None) or name
    return {
        "id": getattr(category, "id", None),
        "title": title,
        "name": name,
        "slug": getattr(category, "slug", None),
        "sort_order": getattr(category, "sort_order", 0) or 0,
        "is_active": bool(getattr(category, "is_active", True)),
    }


def _partner_to_read(partner: Partner, city_name: str | None, owner_email: str | None) -> PartnerRead:
    categories = sorted(partner.categories, key=lambda c: (c.sort_order, c.name.lower(), c.id))
    first = categories[0] if categories else None
    legacy_slug = partner.category_slug
    first_category_payload = _category_to_api_payload(first)
    first_name = str(first_category_payload["name"]) if first_category_payload is not None else None
    first_slug = str(first_category_payload["slug"]) if first_category_payload is not None else None
    categories_payload = [_category_to_api_payload(category) for category in categories]
    normalized_categories_payload = [item for item in categories_payload if item is not None]
    return PartnerRead.model_validate(
        {
            "id": partner.id,
            "city_id": partner.city_id,
            "owner_user_id": partner.owner_user_id,
            "category_slug": first_slug or legacy_slug,
            "category_id": first.id if first is not None else None,
            "category_name": first_name,
            "category": first_category_payload,
            "categories": normalized_categories_payload,
            "category_ids": [c.id for c in categories],
            "category_slugs": [c.slug for c in categories],
            "name": partner.name,
            "description": partner.description,
            "address": partner.address,
            "phone": partner.phone,
            "website_url": partner.website_url,
            "social_url": partner.social_url,
            "instagram_url": partner.instagram_url,
            "vk_url": partner.vk_url,
            "telegram_url": partner.telegram_url,
            "whatsapp_url": partner.whatsapp_url,
            "map_url": partner.map_url,
            "working_hours": partner.working_hours,
            "logo_url": partner.logo_url,
            "cover_url": partner.cover_url,
            "is_active": partner.is_active,
            "is_verified": partner.is_verified,
            "sort_order": partner.sort_order,
            "city_name": city_name,
            "owner_email": owner_email,
            "access_code_configured": bool(partner.access_code_hash),
        }
    )


def _get_categories_by_ids_or_400(db: Session, category_ids: list[int]) -> list[Category]:
    if not category_ids:
        return []
    categories = db.execute(select(Category).where(Category.id.in_(category_ids))).scalars().all()
    by_id = {category.id: category for category in categories}
    if len(by_id) != len(set(category_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")
    return [by_id[category_id] for category_id in dict.fromkeys(category_ids)]

