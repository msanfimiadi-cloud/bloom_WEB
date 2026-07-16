from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VkLinkCodeStatus(str, Enum):
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class BrowserLoginCode(Base):
    __tablename__ = "browser_login_codes"
    __table_args__ = (
        UniqueConstraint("login_code", name="uq_browser_login_codes_login_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    login_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False, default="login", server_default="login", index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    referral_code: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class BrowserLoginToken(Base):
    __tablename__ = "browser_login_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_browser_login_tokens_token_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    referral_code: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    selected_city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    custom_city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vk_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    vk_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trial_subscription_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    referral_code: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True, index=True)
    referred_by_referral_id: Mapped[int | None] = mapped_column(ForeignKey("client_referrals.id"), nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active", index=True)
    merged_into_client_id: Mapped[int | None] = mapped_column(ForeignKey("client_profiles.id"), nullable=True, index=True)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship("User", back_populates="client_profile")
    selected_city: Mapped["City | None"] = relationship("City", back_populates="client_profiles")
    payment_requests: Mapped[list["PaymentRequest"]] = relationship("PaymentRequest", back_populates="client")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="client")
    verification_sessions: Mapped[list["PrivilegeVerificationSession"]] = relationship(
        "PrivilegeVerificationSession",
        back_populates="client",
    )
    vk_link_codes: Mapped[list["VkLinkCode"]] = relationship("VkLinkCode", back_populates="client")
    referrals_made: Mapped[list["ClientReferral"]] = relationship("ClientReferral", foreign_keys="ClientReferral.referrer_client_id", back_populates="referrer")
    referral_joined: Mapped["ClientReferral | None"] = relationship("ClientReferral", foreign_keys=[referred_by_referral_id], post_update=True)
    giveaway_entries: Mapped[list["GiveawayEntry"]] = relationship("GiveawayEntry", back_populates="client")
    identity_links: Mapped[list["ClientIdentityLink"]] = relationship(
        "ClientIdentityLink",
        back_populates="client_profile",
        cascade="all, delete-orphan",
    )
    outgoing_linking_challenges: Mapped[list["AccountLinkingChallenge"]] = relationship(
        "AccountLinkingChallenge",
        foreign_keys="AccountLinkingChallenge.current_client_profile_id",
        back_populates="current_client_profile",
    )
    incoming_linking_challenges: Mapped[list["AccountLinkingChallenge"]] = relationship(
        "AccountLinkingChallenge",
        foreign_keys="AccountLinkingChallenge.target_client_profile_id",
        back_populates="target_client_profile",
    )


class AccountLinkingChallenge(Base):
    __tablename__ = "account_linking_challenges"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    current_client_profile_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), nullable=False, index=True)
    target_client_profile_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), nullable=False, index=True)
    identifier_type: Mapped[str] = mapped_column(String(16), nullable=False)
    identifier_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    current_client_profile: Mapped["ClientProfile"] = relationship(
        "ClientProfile",
        foreign_keys=[current_client_profile_id],
        back_populates="outgoing_linking_challenges",
    )
    target_client_profile: Mapped["ClientProfile"] = relationship(
        "ClientProfile",
        foreign_keys=[target_client_profile_id],
        back_populates="incoming_linking_challenges",
    )


class ClientIdentityLink(Base):
    __tablename__ = "client_identity_links"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_client_identity_links_provider_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_profile_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    linked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    client_profile: Mapped["ClientProfile"] = relationship("ClientProfile", back_populates="identity_links")


class VkLinkCode(Base):
    __tablename__ = "vk_link_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=VkLinkCodeStatus.ACTIVE.value)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    client: Mapped["ClientProfile"] = relationship("ClientProfile", back_populates="vk_link_codes")


class ClientPasswordSetupToken(Base):
    __tablename__ = "client_password_setup_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    purpose: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="vk_onboarding_password_setup",
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    source: Mapped[str | None] = mapped_column(String(64), nullable=True, default="vk")
    vk_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="password_setup_tokens")


class ClientReferral(Base):
    __tablename__ = "client_referrals"
    __table_args__ = (
        UniqueConstraint("referred_client_id", name="uq_client_referrals_referred_client_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referrer_client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), nullable=False, index=True)
    referred_client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), nullable=False, unique=True, index=True)
    referral_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    reward_entries_count: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    reward_granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    referrer: Mapped["ClientProfile"] = relationship("ClientProfile", foreign_keys=[referrer_client_id], back_populates="referrals_made")
    referred: Mapped["ClientProfile"] = relationship("ClientProfile", foreign_keys=[referred_client_id])
    giveaway_entry: Mapped["GiveawayEntry | None"] = relationship("GiveawayEntry", back_populates="related_referral", uselist=False)


class GiveawayEntry(Base):
    __tablename__ = "giveaway_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client_profiles.id"), nullable=False, index=True)
    giveaway_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="other", index=True)
    entries_count: Mapped[int] = mapped_column(Integer, nullable=False)
    related_referral_id: Mapped[int | None] = mapped_column(ForeignKey("client_referrals.id"), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    client: Mapped["ClientProfile"] = relationship("ClientProfile", back_populates="giveaway_entries")
    related_referral: Mapped["ClientReferral | None"] = relationship("ClientReferral", back_populates="giveaway_entry")
