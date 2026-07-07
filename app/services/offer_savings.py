from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.models.partner import PartnerOffer

MONEY_QUANT = Decimal("0.01")
PERCENT_BASE = Decimal("100.00")
ZERO_MONEY = Decimal("0.00")


@dataclass(frozen=True)
class OfferSavingSnapshot:
    regular_price: Decimal | None
    club_price: Decimal | None
    discount_percent: Decimal | None
    saving_amount: Decimal


def calculate_offer_saving_snapshot(offer: PartnerOffer | None) -> OfferSavingSnapshot:
    """Calculate savings from backend offer pricing fields.

    PartnerOffer currently stores a regular/base price in ``base_price`` and the
    member price is derived from ``discount_percent``. Missing price data yields
    a zero saving amount.
    """
    if offer is None:
        return OfferSavingSnapshot(None, None, None, ZERO_MONEY)

    regular_price = _money_or_none(offer.base_price)
    discount_percent = _decimal_or_none(offer.discount_percent)
    if regular_price is None:
        return OfferSavingSnapshot(None, None, discount_percent, ZERO_MONEY)
    if discount_percent is None:
        return OfferSavingSnapshot(regular_price, None, discount_percent, ZERO_MONEY)

    saving_amount = (regular_price * discount_percent / PERCENT_BASE).quantize(MONEY_QUANT)
    saving_amount = max(saving_amount, ZERO_MONEY)
    club_price = max((regular_price - saving_amount).quantize(MONEY_QUANT), ZERO_MONEY)
    return OfferSavingSnapshot(regular_price, club_price, discount_percent, saving_amount)


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
