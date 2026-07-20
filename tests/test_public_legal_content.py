from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND = REPO_ROOT / "frontend"
PUBLIC = FRONTEND / "public"
MAIN_JS = FRONTEND / "src" / "main.js"
INDEX_HTML = FRONTEND / "index.html"

LEGAL_PAGES = {
    "offer": PUBLIC / "offer" / "index.html",
    "privacy": PUBLIC / "privacy" / "index.html",
    "terms": PUBLIC / "terms" / "index.html",
    "consent": PUBLIC / "personal-data-consent" / "index.html",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_public_landing_discloses_subscription_price_and_terms() -> None:
    source = _read(MAIN_JS)

    for marker in (
        "349 ₽ на 30 дней",
        "Автоматического продления и повторных списаний нет",
        "https://app.bloomclub.ru/",
        "/offer/",
    ):
        assert marker in source


def test_public_landing_discloses_operator_and_support_contacts() -> None:
    source = _read(MAIN_JS)

    for marker in (
        "ИП Глущенко Анастасия Дмитриевна",
        "541007956565",
        "323547600049744",
        "danka1948@mail.ru",
        "https://t.me/Wo_ClubNSK",
        "https://t.me/app_bloom_club_bot",
        "https://vk.ru/club238169934",
    ):
        assert marker in source

    assert "Поддержка и контакты" in source
    assert 'class="business-info__details"' not in source
    assert "Юридический адрес" not in source


def test_legal_pages_are_readable_html_with_cross_links() -> None:
    for page_name, path in LEGAL_PAGES.items():
        assert path.is_file(), page_name
        source = _read(path)
        assert '<html lang="ru">' in source
        assert 'href="/legal.css"' in source
        assert 'href="/"' in source
        assert "ИП Глущенко Анастасия Дмитриевна" in source
        assert "danka1948@mail.ru" in source
        assert "давай дальше" not in source.lower()
        assert "конец части" not in source.lower()


def test_offer_contains_complete_payment_and_bank_details() -> None:
    source = _read(LEGAL_PAGES["offer"])

    for marker in (
        "349 (триста сорок девять) рублей",
        "30 календарных дней",
        "Автоматическое продление не используется",
        "40802810220000007083",
        "ООО «Банк Точка»",
        "044525104",
        "30101810745374525104",
    ):
        assert marker in source


def test_offer_describes_refund_for_unused_subscription_period() -> None:
    source = _read(LEGAL_PAGES["offer"])

    for marker in (
        "Возврат возможен за неиспользованный период подписки",
        "полных неиспользованных дней доступа",
        "фактически понесённых Исполнителем и документально подтверждённых расходов",
        "Если доступ не был предоставлен по вине Исполнителя",
        "тем же способом, которым была совершена оплата",
    ):
        assert marker in source

    assert "Автоматические безусловные возвраты" not in source


def test_index_has_search_and_social_metadata() -> None:
    source = _read(INDEX_HTML)

    assert '<meta name="description"' in source
    assert '<meta property="og:title"' in source
    assert '<link rel="canonical" href="https://bloomclub.ru/"' in source
