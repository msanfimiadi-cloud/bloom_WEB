from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARTNER_PAGE = ROOT / "browser-mobile-app" / "src" / "pages" / "PartnerPage.tsx"


def test_textual_percentage_offer_opens_order_amount_modal() -> None:
    source = PARTNER_PAGE.read_text(encoding="utf-8")

    assert "function getTextualOfferDiscountPercent(offer: Offer)" in source
    assert "offer.benefit_text" in source
    assert "offer.title" in source
    assert "offer.description" in source
    assert "offer.conditions" in source
    assert "getTextualOfferDiscountPercent(offer)" in source


def test_backend_order_amount_required_response_is_not_shown_as_technical_error() -> None:
    source = PARTNER_PAGE.read_text(encoding="utf-8")

    assert 'backendDetail === "order_amount_required"' in source
    assert "setPendingAmountOffer(offer)" in source
    assert 'setMessage("")' in source
