from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    PARTNER = "partner"
    CLIENT = "client"

    # Backward-compatible aliases for pre-existing lowercase member access.
    admin = ADMIN
    partner = PARTNER
    client = CLIENT


class User(Base):
    """Future unified account model for partner/client/admin roles.

    The existing AdminUser authentication flow intentionally remains separate
    in this PR and continues to use the admin_users table.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    phone_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    site_login: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    encrypted_site_password: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    site_credentials_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default=UserRole.CLIENT.value)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    client_profile: Mapped["ClientProfile | None"] = relationship(
        "ClientProfile",
        back_populates="user",
        uselist=False,
    )
    owned_partners: Mapped[list["Partner"]] = relationship("Partner", back_populates="owner_user")
    password_setup_tokens: Mapped[list["ClientPasswordSetupToken"]] = relationship(
        "ClientPasswordSetupToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default=UserRole.ADMIN.value)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
