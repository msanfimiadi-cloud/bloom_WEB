from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.models.partner import PartnerOffer

MONEY_QUANT = Decimal("0.01")
PERCENT_QUANT = Decimal("0.01")
PERCENT_BASE = Decimal("100.00")
ZERO_MONEY = Decimal("0.00")
PERCENT_PATTERN = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d{1,2})?)\s*%")


@dataclass(frozen=True)
class OfferSavingSnapshot:
    regular_price: Decimal | None
    club_price: Decimal | None
    discount_percent: Decimal | None
    saving_amount: Decimal


def extract_discount_percent_from_text(*values: str | None) -> Decimal | None:
    """Extract an explicit percentage such as ``5%`` or ``5 %`` from offer text."""
    for value in values:
        if not value:
            continue
        for match in PERCENT_PATTERN.finditer(str(value)):
            try:
                percent = Decimal(match.group(1).replace(",", ".")).quantize(PERCENT_QUANT)
            except InvalidOperation:
                continue
            if ZERO_MONEY < percent <= PERCENT_BASE:
                return percent
    return None


def resolve_offer_discount_percent(offer: PartnerOffer | None) -> Decimal | None:
    """Prefer the structured discount field, with explicit percentage text as fallback."""
    if offer is None:
        return None

    explicit_percent = _decimal_or_none(offer.discount_percent)
    if explicit_percent is not None:
        return explicit_percent

    return extract_discount_percent_from_text(
        offer.benefit_text,
        offer.title,
        offer.description,
        offer.conditions,
    )


def calculate_offer_saving_snapshot(offer: PartnerOffer | None) -> OfferSavingSnapshot:
    """Calculate savings from backend offer pricing fields."""
    if offer is None:
        return OfferSavingSnapshot(None, None, None, ZERO_MONEY)
    return calculate_percentage_saving_snapshot(offer.base_price, resolve_offer_discount_percent(offer))


def calculate_percentage_saving_snapshot(
    order_amount: Decimal | int | str | None,
    discount_percent: Decimal | int | str | None,
) -> OfferSavingSnapshot:
    """Calculate a monetary snapshot for a percentage privilege."""
    regular_price = _money_or_none(order_amount)
    normalized_percent = _decimal_or_none(discount_percent)
    if regular_price is None:
        return OfferSavingSnapshot(None, None, normalized_percent, ZERO_MONEY)
    if normalized_percent is None:
        return OfferSavingSnapshot(regular_price, None, None, ZERO_MONEY)

    saving_amount = (regular_price * normalized_percent / PERCENT_BASE).quantize(MONEY_QUANT)
    saving_amount = max(saving_amount, ZERO_MONEY)
    club_price = max((regular_price - saving_amount).quantize(MONEY_QUANT), ZERO_MONEY)
    return OfferSavingSnapshot(regular_price, club_price, normalized_percent, saving_amount)


def offer_requires_order_amount(offer: PartnerOffer | None) -> bool:
    """Return True when a percentage offer has no fixed base price."""
    if offer is None or _money_or_none(offer.base_price) is not None:
        return False

    discount_percent = resolve_offer_discount_percent(offer)
    if discount_percent is None or discount_percent <= ZERO_MONEY or discount_percent > PERCENT_BASE:
        return False

    # Persist the normalized fallback during verification creation so the existing
    # calculation path and future catalog reads use the same structured value.
    if _decimal_or_none(offer.discount_percent) != discount_percent:
        offer.discount_percent = discount_percent
    return True


def calculate_offer_saving_amount(offer: PartnerOffer | None) -> Decimal:
    return calculate_offer_saving_snapshot(offer).saving_amount


def _money_or_none(value: Decimal | int | str | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value).quantize(MONEY_QUANT)


def _decimal_or_none(value: Decimal | int | str | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value)
