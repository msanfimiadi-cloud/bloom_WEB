from __future__ import annotations

import logging
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.bots.vk_bot import OPEN_BUTTON_TEXT, USER_ERROR_TEXT, VkBotService, VkUserIdentity
from app.db.base import Base
from app.models.client import BrowserLoginCode
from app.schemas.browser_auth import BrowserLoginCodeCreateResponse


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def test_vk_bot_builds_browser_login_code_payload():
    bot = VkBotService(token="vk-token", group_id="42")

    payload = bot.build_browser_login_payload(
        VkUserIdentity(
            vk_user_id="123",
            display_name="Bloom User",
            username="bloom_user",
            photo_url="https://example.test/photo.jpg",
        )
    )

    assert payload == {
        "provider": "vk",
        "provider_user_id": "123",
        "display_name": "Bloom User",
        "username": "bloom_user",
        "photo_url": "https://example.test/photo.jpg",
        "source": "vk_bot",
    }


def test_vk_bot_creates_browser_login_code_response(session_factory):
    bot = VkBotService(token="vk-token", group_id="42", session_factory=session_factory)

    response = bot.create_browser_login_code(VkUserIdentity(vk_user_id="123", display_name="Bloom User"))

    assert response.code.startswith("BC-")
    assert response.app_url == "https://app.bloomclub.ru"
    with session_factory() as db:
        record = db.execute(select(BrowserLoginCode)).scalar_one()
        assert record.provider == "vk"
        assert record.provider_user_id == "123"
        assert record.display_name == "Bloom User"
        assert record.source == "vk_bot"
        assert record.created_by == "vk-bot"
        assert record.login_code == response.code


def test_vk_bot_handles_backend_error_with_user_message(monkeypatch):
    sent_texts = []
    bot = VkBotService(token="vk-token", group_id="42")
    monkeypatch.setattr(bot, "get_user_identity", lambda user_id: VkUserIdentity(vk_user_id=user_id))
    monkeypatch.setattr(bot, "create_browser_login_code", lambda identity: (_ for _ in ()).throw(RuntimeError("backend down")))
    monkeypatch.setattr(bot, "send_text", lambda peer_id, text: sent_texts.append((peer_id, text)))
    monkeypatch.setattr(bot, "send_login_code", lambda peer_id, code, app_url: pytest.fail("must not send login code"))

    bot.handle_update({"type": "message_new", "object": {"message": {"peer_id": 777, "from_id": 123, "text": "начать"}}})

    assert sent_texts == [(777, USER_ERROR_TEXT)]


def test_vk_bot_sends_button_with_app_url(monkeypatch):
    calls = []
    bot = VkBotService(token="vk-token", group_id="42")
    monkeypatch.setattr(bot, "_vk_api", lambda method, params: calls.append((method, params)))

    bot.send_login_code(777, "BC-7K4P9Q", "https://app.bloomclub.ru")

    assert calls[0][0] == "messages.send"
    params = calls[0][1]
    assert "BC-7K4P9Q" in params["message"]
    button = params["keyboard"]["buttons"][0][0]["action"]
    assert button["type"] == "open_link"
    assert button["link"] == "https://app.bloomclub.ru"
    assert button["label"] == OPEN_BUTTON_TEXT


def test_vk_bot_does_not_log_plain_code_on_success(monkeypatch, caplog):
    plain_code = "BC-SECRET"
    sent_codes = []
    bot = VkBotService(token="vk-token", group_id="42")
    monkeypatch.setattr(bot, "get_user_identity", lambda user_id: VkUserIdentity(vk_user_id=user_id))
    monkeypatch.setattr(
        bot,
        "create_browser_login_code",
        lambda identity: BrowserLoginCodeCreateResponse(
            code=plain_code,
            expires_at=datetime.now(timezone.utc),
            app_url="https://app.bloomclub.ru",
        ),
    )
    monkeypatch.setattr(bot, "send_login_code", lambda peer_id, code, app_url: sent_codes.append(code))

    with caplog.at_level(logging.INFO):
        bot.handle_update({"type": "message_new", "object": {"message": {"peer_id": 777, "from_id": 123}}})

    assert sent_codes == [plain_code]
    assert plain_code not in caplog.text
