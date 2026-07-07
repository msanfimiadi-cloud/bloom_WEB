from __future__ import annotations

from typing import TypedDict

WOMEN_CLUB_CATEGORIES: tuple[str, ...] = (
    "Красота",
    "Маникюр / педикюр",
    "Волосы / окрашивание",
    "Брови / ресницы",
    "Косметология",
    "Массаж / SPA",
    "Фитнес / йога",
    "Здоровье",
    "Психология",
    "Одежда / аксессуары",
    "Кафе / рестораны",
    "Обучение / мастер-классы",
    "Фотосессии",
    "Цветы / подарки",
    "Другое",
)

WOMEN_CLUB_CATEGORY_SLUGS: tuple[str, ...] = (
    "krasota",
    "manikyur-pedikyur",
    "volosy-okrashivanie",
    "brovi-resnitsy",
    "kosmetologiya",
    "massazh-spa",
    "fitnes-yoga",
    "zdorove",
    "psihologiya",
    "odezhda-aksessuary",
    "kafe-restorany",
    "obuchenie-master-klassy",
    "fotosessii",
    "cvety-podarki",
    "drugoe",
)


class WomenClubCategory(TypedDict):
    slug: str
    title: str
    is_active: bool
    sort_order: int


def get_women_club_categories() -> list[WomenClubCategory]:
    """Return stable Women Club category metadata for read-only APIs."""
    return [
        {
            "slug": slug,
            "title": title,
            "is_active": True,
            "sort_order": index,
        }
        for index, (slug, title) in enumerate(
            zip(WOMEN_CLUB_CATEGORY_SLUGS, WOMEN_CLUB_CATEGORIES, strict=True),
            start=1,
        )
    ]
