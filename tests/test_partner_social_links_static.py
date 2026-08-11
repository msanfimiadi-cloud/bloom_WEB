from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARTNER_PAGE = (ROOT / "browser-mobile-app/src/pages/PartnerPage.tsx").read_text(encoding="utf-8")
TYPES = (ROOT / "browser-mobile-app/src/api/types.ts").read_text(encoding="utf-8")
STYLES = (ROOT / "browser-mobile-app/src/styles.css").read_text(encoding="utf-8")


def test_partner_card_exposes_configured_social_links() -> None:
    for field in ("social_url", "instagram_url", "vk_url", "telegram_url", "whatsapp_url", "booking_url"):
        assert f"{field}?: BackendText;" in TYPES
        assert f"partner.{field}" in PARTNER_PAGE

    for label in ("Запись онлайн", "Instagram", "ВКонтакте", "Telegram", "WhatsApp"):
        assert f'label: "{label}"' in PARTNER_PAGE

    assert 'className="partner-contact-card__social-links"' in PARTNER_PAGE
    assert 'target="_blank"' in PARTNER_PAGE
    assert 'rel="noopener noreferrer"' in PARTNER_PAGE


def test_partner_social_links_are_safe_and_mobile_friendly() -> None:
    assert 'url.protocol === "http:" || url.protocol === "https:"' in PARTNER_PAGE
    assert "seen.has(href)" in PARTNER_PAGE
    assert 'rawValue.startsWith("@")' in PARTNER_PAGE
    assert 'return `https://wa.me/${phone}`' in PARTNER_PAGE
    assert "firstFilledPartnerValue(partner.website_url, partner.website, partner.site, partner.url)" in PARTNER_PAGE
    assert ".partner-contact-card__social-links" in STYLES
    assert "min-height: 44px;" in STYLES
    assert "flex: 1 1 128px;" in STYLES
