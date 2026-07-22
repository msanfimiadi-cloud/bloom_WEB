from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "browser-mobile-app" / "src"


def read(relative_path: str) -> str:
    return (APP / relative_path).read_text(encoding="utf-8")


def test_profile_uses_the_same_payment_card_as_subscription_page() -> None:
    profile = read("pages/ProfilePage.tsx")
    subscription = read("pages/SubscriptionPage.tsx")
    app = read("App.tsx")

    assert "<SubscriptionPaymentCard" in profile
    assert "<SubscriptionPaymentCard" in subscription
    assert "isCreatingPayment={isCreatingPayment}" in app
    assert "onCreatePayment={openPayment}" in app


def test_browser_app_legal_links_use_public_site_pages() -> None:
    payment_card = read("components/SubscriptionPaymentCard.tsx")
    app = read("App.tsx")

    for url in (
        "https://bloomclub.ru/privacy/",
        "https://bloomclub.ru/terms/",
        "https://bloomclub.ru/personal-data-consent/",
    ):
        assert url in payment_card
        assert url in app
    assert "https://bloomclub.ru/offer/" in payment_card


def test_mature_flower_has_joined_petals_and_no_scattered_daily_emoji() -> None:
    flower = read("components/FlowerGame.tsx")
    styles = read("styles.css")

    assert "flower-joining-petal" in flower
    assert "Добавить лепесток дня" in flower
    assert "flower-daily-petal" not in flower
    assert ".flower-illustration__petal {" in styles
    petal_rule = styles.split(".flower-illustration__petal {", 1)[1].split("}", 1)[0]
    assert "transform-box" not in petal_rule


def test_flower_has_five_thresholds_and_visible_growth_feedback() -> None:
    flower = read("components/FlowerGame.tsx")
    styles = read("styles.css")

    assert "const STAGE_STARTS = [0, 5, 12, 22, 35]" in flower
    assert "getStageProgress(state.petals, stage)" in flower
    assert "flower-illustration__seed-crack" in flower
    assert "flower-illustration__cotyledons" in flower
    assert "flower-stage-path" in flower
    assert "До стадии" in flower
    assert "is-stage-changing" in flower
    assert "@keyframes bloom-stage-rise" in styles
    assert "prefers-reduced-motion: reduce" in styles


def test_partner_detail_hero_uses_contain_in_final_override() -> None:
    styles = read("styles.css")
    final_rule = styles.rsplit(".partner-gallery__main .partner-detail__image {", 1)[1].split("}", 1)[0]

    assert "object-fit: contain" in final_rule
    assert "height: auto" in final_rule
    assert "min-height: 0" in final_rule
