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
    assert "/assets/garden/stage-${stage}.jpeg" in flower
    assert "/assets/garden/bloom-flower-loop.mp4" in flower
    assert "flower-stage-media--stage-${stage}" in flower
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


def test_flower_month_progress_counts_down_after_the_current_day() -> None:
    flower = read("components/FlowerGame.tsx")

    assert "state.days_in_month, new Date().getDate()" in flower
    assert "safeDaysInMonth - elapsedDays" in flower
    assert "До конца месяца осталось" in flower
    assert "Сегодня последний день месяца" in flower
    assert "state.days_grown} из {state.days_in_month}" not in flower


def test_partner_catalog_card_renders_partner_information_only_once() -> None:
    card = read("components/PartnerCatalogCard.tsx")
    styles = read("styles.css")

    assert card.count('className="home-partner-tile__body"') == 1
    final_card_rule = styles.rsplit(".partner-catalog-card {", 1)[1].split("}", 1)[0]
    assert "height: auto" in final_card_rule
    assert "min-height: 172px" in final_card_rule


def test_home_promotes_catalog_without_duplicating_partner_cards() -> None:
    home = read("pages/HomePage.tsx")

    assert "Открыть каталог партнёров" in home
    assert "PartnerCatalogCard" not in home
    assert "visiblePartners.map" not in home
    assert "safePartners.slice(0, 8).map" not in home


def test_flower_garden_explains_actions_and_giveaway_rewards() -> None:
    flower = read("components/FlowerGame.tsx")

    assert "Как работает Сад Bloom" in flower
    assert "Заходите каждый день" in flower
    assert "Пользуйтесь привилегиями партнёров" in flower
    assert "первую десятку рейтинга" in flower
    assert "дополнительные номера для розыгрыша" in flower
