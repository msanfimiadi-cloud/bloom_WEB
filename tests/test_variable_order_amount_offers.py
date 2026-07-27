from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.admin import _validate_offer_amounts as validate_admin_offer_amounts
from app.models.partner import PartnerOffer
from app.services.offer_savings import offer_requires_order_amount


ROOT = Path(__file__).resolve().parents[1]
WEB_ADMIN = ROOT / "frontend" / "src" / "main.js"
BROWSER_TYPES = ROOT / "browser-mobile-app" / "src" / "api" / "types.ts"
PARTNER_PAGE = ROOT / "browser-mobile-app" / "src" / "pages" / "PartnerPage.tsx"


def test_offer_requires_amount_only_when_explicitly_enabled() -> None:
    enabled = PartnerOffer(
        partner_id=1,
        title="Горячие напитки",
        discount_percent=Decimal("5.00"),
        requires_order_amount=True,
    )
    disabled = PartnerOffer(
        partner_id=1,
        title="Горячие напитки 5%",
        benefit_text="Скидка 5% на горячие напитки",
        requires_order_amount=False,
    )

    assert offer_requires_order_amount(enabled) is True
    assert offer_requires_order_amount(disabled) is False


def test_variable_amount_offer_requires_positive_discount_percent() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_admin_offer_amounts(
            base_price=None,
            discount_percent=None,
            requires_order_amount=True,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "discount_percent is required when requires_order_amount is true"
    )

    validate_admin_offer_amounts(
        base_price=None,
        discount_percent=Decimal("5.00"),
        requires_order_amount=True,
    )


def test_web_admin_exposes_explicit_variable_amount_controls() -> None:
    source = WEB_ADMIN.read_text(encoding="utf-8")

    assert "Клиент должен сам указать сумму заказа" in source
    assert 'name="requires_order_amount"' in source
    assert 'name="variable_discount_percent"' in source
    assert "requires_order_amount: requiresOrderAmount" in source
    assert "discount_percent: requiresOrderAmount" in source


def test_browser_app_prefers_explicit_variable_amount_setting() -> None:
    page_source = PARTNER_PAGE.read_text(encoding="utf-8")
    types_source = BROWSER_TYPES.read_text(encoding="utf-8")

    assert "requires_order_amount?: boolean | string | number" in types_source
    assert "function getExplicitOrderAmountSetting(offer: Offer)" in page_source
    assert "if (explicitSetting === true)" in page_source
    assert "if (explicitSetting === false)" in page_source
    assert 'backendDetail === "order_amount_required"' in page_source
    assert "Для этой привилегии не настроен процент" in page_source
