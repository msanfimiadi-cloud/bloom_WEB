from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.browser_auth import BrowserLoginCodeCreateResponse
from app.services.browser_login_codes import BrowserLoginCodeService

OPEN_APP_URL = "https://app.bloomclub.ru"
LOGIN_CODE_MESSAGE = "Ваш код входа для Bloom Club.\n\nСкопируйте код из следующей строки одним тапом:\n`{code}`\n\nКод действует 5 минут.\n\nОткрыть приложение:\n{app_url}"


@dataclass(frozen=True)
class TelegramBotUserIdentity:
    telegram_user_id: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    photo_url: str | None = None

    @property
    def display_name(self) -> str | None:
        return " ".join(part for part in (self.first_name, self.last_name) if part) or None


class TelegramBotLoginCodeService:
    def __init__(self, *, session_factory=SessionLocal) -> None:
        self.session_factory = session_factory

    def create_browser_login_code(self, identity: TelegramBotUserIdentity) -> BrowserLoginCodeCreateResponse:
        with self.session_factory() as db:
            assert isinstance(db, Session)
            service = BrowserLoginCodeService(db)
            code, record = service.create_code(
                provider="telegram",
                provider_user_id=identity.telegram_user_id,
                display_name=identity.display_name,
                username=identity.username,
                photo_url=identity.photo_url,
                source="telegram_bot",
                created_by="telegram-bot",
            )
            db.commit()
            db.refresh(record)
            return BrowserLoginCodeCreateResponse(code=code, expires_at=record.expires_at, app_url=service.build_app_url())

    def build_login_code_message(self, response: BrowserLoginCodeCreateResponse) -> str:
        return LOGIN_CODE_MESSAGE.format(code=response.code, app_url=response.app_url or OPEN_APP_URL)
