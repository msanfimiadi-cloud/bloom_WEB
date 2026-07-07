from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password, verify_password
from app.db.base import Base
from app.models.user import AdminUser, UserRole
from scripts import create_admin as create_admin_script


@pytest.fixture()
def admin_session_factory(monkeypatch: pytest.MonkeyPatch) -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(create_admin_script, "SessionLocal", session_factory)
    try:
        yield session_factory
    finally:
        engine.dispose()


def get_admin(session_factory: sessionmaker[Session], email: str) -> AdminUser:
    with session_factory() as session:
        admin = session.execute(select(AdminUser).where(AdminUser.email == email)).scalar_one()
        session.expunge(admin)
        return admin


def test_create_admin_creates_new_admin_user(
    admin_session_factory: sessionmaker[Session],
    capsys: pytest.CaptureFixture[str],
) -> None:
    created = create_admin_script.create_admin(" NewAdmin@Example.com ", "FirstPassword123")

    assert created is True
    admin = get_admin(admin_session_factory, "newadmin@example.com")
    assert admin.email == "newadmin@example.com"
    assert admin.role == UserRole.ADMIN.value
    assert admin.is_active is True
    assert verify_password("FirstPassword123", admin.password_hash) is True
    assert "Admin user newadmin@example.com created." in capsys.readouterr().out


def test_create_admin_without_update_password_keeps_existing_hash(
    admin_session_factory: sessionmaker[Session],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with admin_session_factory() as session:
        session.add(
            AdminUser(
                email="admin@example.com",
                password_hash=hash_password("OriginalPassword123"),
                role=UserRole.ADMIN.value,
                is_active=True,
            )
        )
        session.commit()
    original_hash = get_admin(admin_session_factory, "admin@example.com").password_hash

    created = create_admin_script.create_admin("admin@example.com", "NewPassword123")

    assert created is False
    admin = get_admin(admin_session_factory, "admin@example.com")
    assert admin.password_hash == original_hash
    assert verify_password("OriginalPassword123", admin.password_hash) is True
    assert verify_password("NewPassword123", admin.password_hash) is False
    assert "Admin user admin@example.com already exists; no duplicate was created." in capsys.readouterr().out


def test_create_admin_with_update_password_changes_existing_hash(
    admin_session_factory: sessionmaker[Session],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with admin_session_factory() as session:
        session.add(
            AdminUser(
                email="admin@example.com",
                password_hash=hash_password("OriginalPassword123"),
                role=UserRole.PARTNER.value,
                is_active=False,
            )
        )
        session.commit()
    original_hash = get_admin(admin_session_factory, "admin@example.com").password_hash

    updated = create_admin_script.create_admin(
        "admin@example.com",
        "NewPassword123",
        update_password=True,
    )

    assert updated is True
    admin = get_admin(admin_session_factory, "admin@example.com")
    assert admin.password_hash != original_hash
    assert verify_password("NewPassword123", admin.password_hash) is True
    assert verify_password("OriginalPassword123", admin.password_hash) is False
    assert admin.is_active is True
    assert admin.role == UserRole.ADMIN.value
    assert "Admin user admin@example.com password updated." in capsys.readouterr().out
