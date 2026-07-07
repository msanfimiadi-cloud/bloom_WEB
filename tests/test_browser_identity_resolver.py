from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register all SQLAlchemy models for test metadata
from app.db.base import Base
from app.models.client import ClientIdentityLink, ClientProfile
from app.models.user import User, UserRole
from app.services.browser_identity_resolver import BrowserIdentityResolver


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    with session_factory() as session:
        yield session
    engine.dispose()


def _create_profile(db_session, *, telegram_user_id: str | None = None, vk_user_id: str | None = None) -> ClientProfile:
    user = User(role=UserRole.CLIENT.value, is_active=True)
    db_session.add(user)
    db_session.flush()
    profile = ClientProfile(
        user_id=user.id,
        telegram_user_id=telegram_user_id,
        vk_user_id=vk_user_id,
        source="test",
        is_active=True,
    )
    db_session.add(profile)
    db_session.flush()
    return profile


def _create_identity_link(db_session, *, profile: ClientProfile, provider: str, provider_user_id: str) -> ClientIdentityLink:
    link = ClientIdentityLink(
        client_profile_id=profile.id,
        provider=provider,
        provider_user_id=provider_user_id,
    )
    db_session.add(link)
    db_session.flush()
    return link


def test_telegram_provider_finds_profile_through_identity_link(db_session) -> None:
    profile = _create_profile(db_session, telegram_user_id="legacy-tg")
    link = _create_identity_link(db_session, profile=profile, provider="telegram", provider_user_id="tg-123")

    result = BrowserIdentityResolver(db_session).resolve(provider="telegram", provider_user_id="tg-123")

    assert result.status == "linked"
    assert result.client_profile.id == profile.id
    assert result.identity_link.id == link.id
    assert result.created_identity_link is False


def test_vk_provider_finds_profile_through_identity_link(db_session) -> None:
    profile = _create_profile(db_session, vk_user_id="legacy-vk")
    link = _create_identity_link(db_session, profile=profile, provider="vk", provider_user_id="vk-123")

    result = BrowserIdentityResolver(db_session).resolve(provider="vk", provider_user_id="vk-123")

    assert result.status == "linked"
    assert result.client_profile.id == profile.id
    assert result.identity_link.id == link.id
    assert result.created_identity_link is False


def test_telegram_provider_finds_legacy_user_id_and_creates_identity_link(db_session) -> None:
    profile = _create_profile(db_session, telegram_user_id="tg-legacy")

    result = BrowserIdentityResolver(db_session).resolve(provider="telegram", provider_user_id="tg-legacy")

    assert result.status == "legacy_linked"
    assert result.client_profile.id == profile.id
    assert result.identity_link.provider == "telegram"
    assert result.identity_link.provider_user_id == "tg-legacy"
    assert result.identity_link.client_profile_id == profile.id
    assert result.created_identity_link is True


def test_vk_provider_finds_legacy_user_id_and_creates_identity_link(db_session) -> None:
    profile = _create_profile(db_session, vk_user_id="vk-legacy")

    result = BrowserIdentityResolver(db_session).resolve(provider="vk", provider_user_id="vk-legacy")

    assert result.status == "legacy_linked"
    assert result.client_profile.id == profile.id
    assert result.identity_link.provider == "vk"
    assert result.identity_link.provider_user_id == "vk-legacy"
    assert result.identity_link.client_profile_id == profile.id
    assert result.created_identity_link is True


def test_unknown_provider_user_id_creates_client_profile(db_session) -> None:
    _create_profile(db_session, telegram_user_id="known")

    result = BrowserIdentityResolver(db_session).resolve(
        provider="telegram",
        provider_user_id="unknown",
        display_name="New User",
        username="new_user",
        photo_url="https://example.test/avatar.jpg",
        referral_code="REF123",
        source="telegram_bot",
    )

    assert result.status == "created"
    assert result.client_profile is not None
    assert result.client_profile.telegram_user_id == "unknown"
    assert result.client_profile.telegram_username == "new_user"
    assert result.identity_link is not None
    assert result.identity_link.provider_user_id == "unknown"
    assert result.created_identity_link is True


def test_repeated_resolve_does_not_create_duplicate_identity_link(db_session) -> None:
    profile = _create_profile(db_session, telegram_user_id="tg-repeat")
    resolver = BrowserIdentityResolver(db_session)

    first = resolver.resolve(provider="telegram", provider_user_id="tg-repeat")
    second = resolver.resolve(provider="telegram", provider_user_id="tg-repeat")

    links = db_session.execute(
        select(ClientIdentityLink).where(
            ClientIdentityLink.provider == "telegram",
            ClientIdentityLink.provider_user_id == "tg-repeat",
        )
    ).scalars().all()
    assert first.status == "legacy_linked"
    assert first.created_identity_link is True
    assert second.status == "linked"
    assert second.client_profile.id == profile.id
    assert second.created_identity_link is False
    assert len(links) == 1
