from decimal import Decimal

from app.models.partner import PartnerOffer
from app.schemas.partner import PartnerOfferRead
from app.services.offer_savings import (
    calculate_percentage_saving_snapshot,
    extract_discount_percent_from_text,
    offer_requires_order_amount,
    resolve_offer_discount_percent,
)


def _offer(**overrides) -> PartnerOffer:
    values = {
        "id": 101,
        "partner_id": 7,
        "title": "Горячие напитки",
        "description": None,
        "benefit_text": "Скидка 5% на любые горячие напитки",
        "conditions": None,
        "base_price": None,
        "discount_percent": None,
        "image_url": None,
        "is_active": True,
        "sort_order": 0,
    }
    values.update(overrides)
    return PartnerOffer(**values)


def test_extracts_explicit_percentage_from_russian_offer_text() -> None:
    assert extract_discount_percent_from_text("скидка 5% на напитки") == Decimal("5.00")
    assert extract_discount_percent_from_text("Привилегия 7,5 % на заказ") == Decimal("7.50")
    assert extract_discount_percent_from_text("Заказ от 1000 рублей") is None


def test_textual_percentage_without_price_requires_order_amount() -> None:
    offer = _offer()

    assert resolve_offer_discount_percent(offer) == Decimal("5.00")
    assert offer_requires_order_amount(offer) is True
    assert offer.discount_percent == Decimal("5.00")

    saving = calculate_percentage_saving_snapshot(Decimal("1000.00"), offer.discount_percent)
    assert saving.regular_price == Decimal("1000.00")
    assert saving.club_price == Decimal("950.00")
    assert saving.saving_amount == Decimal("50.00")


def test_catalog_schema_exposes_textual_percentage_to_browser_app() -> None:
    payload = PartnerOfferRead.model_validate(_offer())

    assert payload.discount_percent == Decimal("5.00")
    assert payload.base_price is None


def test_structured_percentage_wins_over_text_and_fixed_price_skips_prompt() -> None:
    structured = _offer(discount_percent=Decimal("10.00"))
    fixed_price = _offer(base_price=Decimal("300.00"))

    assert resolve_offer_discount_percent(structured) == Decimal("10.00")
    assert offer_requires_order_amount(fixed_price) is False
