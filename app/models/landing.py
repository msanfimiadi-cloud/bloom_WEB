from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


DEFAULT_GIVEAWAY_EMPTY_TEXT = "Информация о призах появится после настройки розыгрыша."

DEFAULT_GIVEAWAY_ITEMS = [
    {"title": "Приз месяца", "is_active": True, "sort_order": 0},
]


class LandingSettings(Base):
    __tablename__ = "landing_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    members_count_base: Mapped[int] = mapped_column(Integer, nullable=False, default=20, server_default="20")
    partners_count_display: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    savings_total: Mapped[int] = mapped_column(Integer, nullable=False, default=8200, server_default="8200")
    bloom_map_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    giveaway_title: Mapped[str] = mapped_column(String(255), nullable=False, default="Розыгрыш месяца", server_default="Розыгрыш месяца")
    giveaway_current: Mapped[str] = mapped_column(String(255), nullable=False, default="Приз месяца", server_default="Приз месяца")
    giveaway_subtitle: Mapped[str] = mapped_column(String(512), nullable=False, default="доступно участницам клуба", server_default="доступно участницам клуба")
    giveaway_empty_text: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default=DEFAULT_GIVEAWAY_EMPTY_TEXT,
        server_default=DEFAULT_GIVEAWAY_EMPTY_TEXT,
    )
    giveaway_items: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=lambda: [item.copy() for item in DEFAULT_GIVEAWAY_ITEMS])
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
