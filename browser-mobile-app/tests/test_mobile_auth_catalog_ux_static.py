from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "src" / "App.tsx").read_text(encoding="utf-8")
CATALOG = (ROOT / "src" / "pages" / "CatalogPage.tsx").read_text(encoding="utf-8")
CATEGORIES = (ROOT / "src" / "utils" / "catalogCategories.ts").read_text(encoding="utf-8")
STYLES = (ROOT / "src" / "styles.css").read_text(encoding="utf-8")


def test_partner_detail_scrolls_after_the_partner_view_is_rendered() -> None:
    effect = APP[
        APP.index('if (page !== "partner" || !selectedPartner)')
        : APP.index("const retryPartnerOffers")
    ]
    assert "requestAnimationFrame(scrollAppToTop)" in effect
    assert "[page, selectedPartner]" in effect


def test_catalog_uses_api_categories_and_deduplicates_normalized_names() -> None:
    assert "LIFESTYLE_CATEGORIES" not in CATALOG
    assert "buildCatalogCategories(safePartners)" in CATALOG
    assert "normalizeCategoryKey" in CATEGORIES
    assert "toLocaleLowerCase('ru-RU')" in CATEGORIES
    assert "new Map<string, string>()" in CATEGORIES


def test_mobile_auth_fields_keep_ios_safe_font_size_and_centered_layout() -> None:
    final_guardrails = STYLES[STYLES.index("/* Mobile auth and safe-area guardrails.") :]
    assert "font-size: 16px" in final_guardrails
    assert "justify-content: center" in final_guardrails
    assert "text-align: center" in final_guardrails
    assert "100svh" in final_guardrails


def test_app_content_reserves_navigation_and_safe_area_space() -> None:
    final_guardrails = STYLES[STYLES.index("/* Mobile auth and safe-area guardrails.") :]
    assert "var(--bottom-nav-reserved-height, 98px)" in final_guardrails
    assert "env(safe-area-inset-bottom)" in final_guardrails
    assert "scroll-padding-bottom" in final_guardrails
