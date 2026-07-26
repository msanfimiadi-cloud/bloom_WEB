from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_active_subscription_plan_catalog_is_public_for_guest_checkout() -> None:
    source = (ROOT / "app" / "api" / "v1" / "endpoints" / "payments.py").read_text(encoding="utf-8")
    start = source.index('@router.get("/clients/subscription-plans"')
    end = source.index('@router.post("/clients/payments"', start)
    handler = source[start:end]

    assert "Depends(get_db)" in handler
    assert "Depends(require_client)" not in handler
