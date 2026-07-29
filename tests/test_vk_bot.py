import json

import pytest
import httpx

from vk_bot.client import InternalApiClient, VkApiClient
from vk_bot.handlers import ERROR_MESSAGE, LOGIN_MESSAGE, VkBotHandler, backoff_sleep
from vk_bot.keyboards import OPEN_APP_LABEL
from vk_bot.settings import VkBotSettings


class FakeVk:
    def __init__(self, *, profile=None, send_error=None):
        self.profile = profile
        self.messages = []
        self.send_error = send_error

    async def get_profile(self, user_id):
        return self.profile

    async def send_message(self, peer_id, message, keyboard=None):
        if self.send_error:
            raise self.send_error
        self.messages.append((peer_id, message, keyboard))


class FakeInternal:
    def __init__(self, data=None, error=None):
        self.data = data or {"login_code": "BC-ABC123", "expires_in": 300}
        self.error = error
        self.calls = []

    async def create_login_code(self, profile):
        self.calls.append(profile)
        if self.error:
            raise self.error
        return self.data


@pytest.mark.asyncio
async def test_first_message_requests_internal_api_and_sends_keyboard():
    settings = VkBotSettings(browser_app_url="https://app.bloomclub.ru")
    vk_client = VkApiClient(settings, http=httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"response": [{"id": 1, "screen_name": "bloom_user"}]}))))
    profile = await vk_client.get_profile("1")
    fake_vk = FakeVk(profile=profile)
    internal = FakeInternal()
    handler = VkBotHandler(fake_vk, internal, settings)

    await handler.handle_update({"type": "message_new", "object": {"message": {"peer_id": 10, "from_id": 1, "text": "Начать"}}})

    assert internal.calls[0].user_id == "1"
    assert [message for _, message, _ in fake_vk.messages] == [LOGIN_MESSAGE.format(code="BC-ABC123")]
    keyboard = json.loads(fake_vk.messages[0][2])
    assert keyboard["inline"] is False
    assert keyboard["one_time"] is False
    assert len(keyboard["buttons"]) == 1
    assert len(keyboard["buttons"][0]) == 1
    assert keyboard["buttons"][0][0]["action"] == {
        "type": "open_link",
        "link": "https://app.bloomclub.ru",
        "label": OPEN_APP_LABEL,
    }


@pytest.mark.asyncio
async def test_repeat_code_uses_same_internal_flow():
    from vk_bot.client import VkProfile
    settings = VkBotSettings()
    profile = VkProfile(user_id="42", username="screen")
    fake_vk = FakeVk(profile=profile)
    internal = FakeInternal()
    handler = VkBotHandler(fake_vk, internal, settings)

    await handler.handle_update({"type": "message_new", "object": {"message": {"peer_id": 10, "from_id": 42, "text": "Получить код повторно"}}})

    assert len(internal.calls) == 1
    assert internal.calls[0] is profile
    assert [message for _, message, _ in fake_vk.messages] == [LOGIN_MESSAGE.format(code="BC-ABC123")]


@pytest.mark.asyncio
async def test_backend_unavailable_sends_clear_message():
    from vk_bot.client import VkProfile
    request = httpx.Request("POST", "http://test")
    error = httpx.ConnectError("down", request=request)
    fake_vk = FakeVk(profile=VkProfile(user_id="1", username="u"))
    handler = VkBotHandler(fake_vk, FakeInternal(error=error), VkBotSettings())

    await handler.handle_update({"type": "message_new", "object": {"message": {"peer_id": 10, "from_id": 1, "text": "x"}}})

    assert fake_vk.messages[0][1] == ERROR_MESSAGE


@pytest.mark.asyncio
async def test_backoff_caps_delay(monkeypatch):
    async def noop(delay):
        return None
    monkeypatch.setattr("asyncio.sleep", noop)
    assert await backoff_sleep(40) == 60.0


@pytest.mark.asyncio
async def test_users_get_fallback_username():
    async def handler(request):
        return httpx.Response(200, json={"response": [{"id": 7, "first_name": "Ира", "last_name": "Цветкова"}]})
    client = VkApiClient(VkBotSettings(), http=httpx.AsyncClient(transport=httpx.MockTransport(handler)))

    profile = await client.get_profile("7")

    assert profile.username == "Ира Цветкова"


@pytest.mark.asyncio
async def test_old_vk_bot_menu_and_partner_mode_are_removed():
    from vk_bot.client import VkProfile

    fake_vk = FakeVk(profile=VkProfile(user_id="7", username="screen"))
    handler = VkBotHandler(fake_vk, FakeInternal(), VkBotSettings())

    await handler.handle_update({"type": "message_new", "object": {"message": {"peer_id": 10, "from_id": 7, "text": "/partner"}}})

    assert len(handler.internal.calls) == 1
    keyboard = fake_vk.messages[0][2]
    for removed_text in (
        "Получить код повторно",
        "Получить новый код",
        "Подписка",
        "Партнёры и скидки",
        "Присоединиться к клубу",
        "Установить новый пароль",
        "Открыть WEB-кабинет",
        "Да, активировать",
    ):
        assert removed_text not in keyboard
