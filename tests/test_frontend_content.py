from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"
FRONTEND_INDEX = FRONTEND_DIR / "index.html"
FRONTEND_MAIN = FRONTEND_DIR / "src" / "main.js"
FRONTEND_STYLES = FRONTEND_DIR / "src" / "styles.css"
ADMIN_ENDPOINTS = REPO_ROOT / "app" / "api" / "v1" / "endpoints" / "admin.py"
ADMIN_SCHEMAS = REPO_ROOT / "app" / "schemas" / "admin.py"

EXPECTED_TITLE = "Женский клуб — федеральный клуб привилегий для девушек"
FORBIDDEN_PUBLIC_COPY = (
    "skeleton",
    "ADMIN / PARTNER SHELL",
    "Панель администратора и кабинет партнёра сохраняют",
)
REQUIRED_PUBLIC_BLOCKS = (
    "Женский клуб",
    "Категории партнёров",
    "Выберите город",
)


def _frontend_index() -> str:
    return FRONTEND_INDEX.read_text(encoding="utf-8")


def _frontend_main() -> str:
    return FRONTEND_MAIN.read_text(encoding="utf-8")


def _frontend_styles() -> str:
    return FRONTEND_STYLES.read_text(encoding="utf-8")


def _admin_endpoints() -> str:
    return ADMIN_ENDPOINTS.read_text(encoding="utf-8")


def _admin_schemas() -> str:
    return ADMIN_SCHEMAS.read_text(encoding="utf-8")


def _frontend_public_sources() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in (FRONTEND_INDEX, FRONTEND_MAIN)
    )


def _css_block(styles: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*{{(.*?)\n}}", styles, re.S)
    assert match is not None
    return match.group(1)


def _city_options() -> list[str]:
    source = _frontend_main()
    match = re.search(r"const cities = \[(.*?)\];", source, re.S)
    assert match is not None
    return re.findall(r"'([^']+)'", match.group(1))



def test_frontend_contains_cabinet_text_hierarchy_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()
    combined = source + "\n" + styles

    for marker in (
        "section-eyebrow",
        "section-title",
        "section-description",
        "helper-text",
        "card-title",
        "card-description",
        "muted-text",
        "compact-copy",
    ):
        assert marker in combined

def test_frontend_title_targets_girls() -> None:
    assert f"<title>{EXPECTED_TITLE}</title>" in _frontend_index()


def test_public_frontend_does_not_render_technical_shell_copy() -> None:
    source = _frontend_public_sources()

    for forbidden_copy in FORBIDDEN_PUBLIC_COPY:
        assert forbidden_copy not in source


def test_public_frontend_keeps_core_blocks() -> None:
    source = _frontend_main()

    for public_block in REQUIRED_PUBLIC_BLOCKS:
        assert public_block in source


def test_public_frontend_contains_css_only_sakura_layer() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        'class="sakura-layer" aria-hidden="true"',
        "sakura-petal",
        "sakura-petal--1",
    ):
        assert expected in source or expected in styles

    assert "Array.from({ length: 68 }" in source
    assert "sakura-petal--68" in styles
    for sakura_color in (
        "rgba(244, 167, 185",
        "rgba(247, 182, 200",
        "rgba(242, 191, 208",
        "rgba(233, 150, 173",
    ):
        assert sakura_color in styles

    assert "--petal-vein" in styles
    assert "filter: blur(0.25px);" in styles
    assert "@keyframes sakuraFall" in styles
    assert "translate3d(" in styles
    assert "animation-duration:" in styles
    assert "animation-delay:" in styles
    assert "--fall-duration:" in styles
    assert "--fall-delay:" in styles
    assert "prefers-reduced-motion: reduce" in styles
    assert "animation: none !important;" in styles
    assert "position: fixed;" in styles
    assert "pointer-events: none;" in styles
    assert "z-index: 0;" in styles
    assert ".app-shell" in styles
    assert "z-index: 1;" in styles

def test_dashboard_cabinets_include_ambient_sakura_layer() -> None:
    source = _frontend_main()
    styles = _frontend_styles()
    combined = source + "\n" + styles

    for marker in (
        "cabinet-ambient",
        "cabinet-ambient__glow",
        "cabinet-petals",
        "cabinet-petal",
        "cabinet-petal--near",
        "cabinet-petal--far",
        "cabinet-petal-fall",
        "prefers-reduced-motion",
        'aria-hidden="true"',
        "pointer-events: none",
        "translate3d",
    ):
        assert marker in combined

    assert "renderCabinetAmbientLayer()" in source
    assert "Array.from({ length: 18 }" in source
    assert "pointer-events: none;" in _css_block(styles, ".cabinet-ambient")
    assert "z-index: 0;" in _css_block(styles, ".cabinet-ambient")
    assert "z-index: 1;" in _css_block(styles, ".dashboard-topbar,\n.dashboard-layout")
    assert "animation: none !important;" in styles


def test_public_landing_cards_use_frosted_translucent_backgrounds() -> None:
    styles = _frontend_styles()

    assert "body:not(.is-dashboard) .hero" in styles
    assert "body:not(.is-dashboard) .panel" in styles

    for selector in (
        "body:not(.is-dashboard) .hero",
        "body:not(.is-dashboard) .panel",
        ".hero-card",
        ".feature-card",
        ".city-select-card",
    ):
        block = _css_block(styles, selector)
        assert "background:" in block
        assert re.search(r"background:[^;]*(rgba|hsla)\(", block, re.S)
        assert "backdrop-filter: blur(10px) saturate(1.05);" in block
        assert "-webkit-backdrop-filter: blur(10px) saturate(1.05);" in block
        assert not re.search(r"(^|\s)opacity\s*:", block)


def test_frontend_selects_use_rose_glass_native_styling() -> None:
    styles = _frontend_styles()

    for expected_marker in (
        "Rose glass native select styling",
        ".form-select",
        ".app-select",
        ".select-field",
        "select option",
        "select:focus",
        "select:disabled",
    ):
        assert expected_marker in styles

    select_block = styles.split("/* Rose glass native select styling", 1)[1].split("\n}\n", 1)[0]
    for expected_style in (
        "min-height: 46px;",
        "border-radius: 16px;",
        "rgba(255, 250, 248, 0.92)",
        "background-image:",
        "data:image/svg+xml",
        "appearance: none;",
        "var(--color-text)",
    ):
        assert expected_style in select_block

    focus_block = _css_block(styles, "select:focus-visible")
    assert "border-color: var(--color-rose);" in focus_block
    assert "0 0 0 4px rgba(246, 216, 210, 0.7)" in focus_block

    disabled_block = _css_block(styles, "select:disabled")
    assert "cursor: not-allowed;" in disabled_block
    assert "opacity: 1;" in disabled_block

    option_block = _css_block(styles, "select option")
    assert "background: #fffaf8;" in option_block
    assert "color: var(--color-text);" in option_block


def test_frontend_contains_reusable_custom_select_component() -> None:
    source = _frontend_main()
    styles = _frontend_styles()
    combined = source + "\n" + styles

    for marker in (
        "renderCustomSelect",
        "custom-select",
        "custom-select--open",
        "custom-select-trigger",
        "custom-select-menu",
        "custom-select-option",
        "custom-select-option--selected",
        "custom-select-option--active",
        "custom-select-option--disabled",
        'role="combobox"',
        'role="listbox"',
        'role="option"',
        "aria-expanded",
        "aria-selected",
        "data-custom-select",
    ):
        assert marker in combined


def test_client_savings_tab_contains_date_filter_controls() -> None:
    source = _frontend_main()

    for marker in (
        "data-client-savings-filter-mode=\"all\"",
        "data-client-savings-filter-mode=\"period\"",
        "data-client-savings-date=\"from\"",
        "data-client-savings-date=\"to\"",
        "data-client-savings-apply",
        "data-client-savings-reset",
        "Дата начала не может быть позже даты окончания.",
        "За всё время",
        "За период:",
        "from_date",
        "to_date",
    ):
        assert marker in source

    for behavior_marker in (
        "openCustomSelect",
        "closeCustomSelects",
        "selectCustomSelectOption",
        "custom-select:change",
        "ArrowDown",
        "ArrowUp",
        "Escape",
        "scrollIntoView",
        "data-custom-select-input",
    ):
        assert behavior_marker in source


def test_client_savings_uses_defined_price_formatter() -> None:
    source = _frontend_main()
    assert "const formatPrice = (value) => {" in source
    assert "formatPrice(data.total_saving_amount)" in source


def test_admin_users_subscription_date_uses_safe_datetime_formatter() -> None:
    source = _frontend_main()
    users_block = source.split("const renderUsersTab = () => {", 1)[1].split("const renderCityActionButtons", 1)[0]

    assert "const formatDateTime = (value) => {" in source
    assert "if (value === null || value === undefined || value === '') return '—';" in source
    assert "if (Number.isNaN(date.getTime())) return '—';" in source
    assert "formatDateTime(item.subscription_active_until ?? item.active_subscription_until)" in users_block


def test_admin_users_can_add_and_remove_subscription_days() -> None:
    source = _frontend_main()
    users_block = source.split("const renderUserActionButton = (user) =>", 1)[1].split("const renderAdminSearch", 1)[0]

    assert "Добавить дни" in users_block
    assert "Убрать дни" in users_block
    assert "data-user-subscription-adjust" in users_block
    assert "data-subscription-operation" in users_block
    assert "const adjustUserSubscriptionDays = async" in source
    assert "/subscription-days" in source
    assert "days < 1 || days > 3650" in source


def test_frontend_applies_custom_selects_to_client_catalog_filters() -> None:
    source = _frontend_main()
    catalog_block = source.split("const renderClientCatalogTab = () => {", 1)[1].split("const renderClientPartnerCard", 1)[0]

    assert "renderCustomSelect" in catalog_block
    assert "name: 'category_slug'" in catalog_block
    assert "name: 'city_slug'" in catalog_block
    assert "clientCatalogFilter: 'category'" in catalog_block
    assert "clientCatalogFilter: 'city'" in catalog_block
    assert '<select name="category_slug"' not in catalog_block
    assert '<select name="city_slug"' not in catalog_block


def test_frontend_applies_custom_selects_to_admin_partner_edit_fields() -> None:
    source = _frontend_main()
    partner_edit_block = source.split("const renderPartnerEditForm = () => {", 1)[1].split("const renderPartnerCreateForm", 1)[0]

    assert "renderSelect('city_id'" in partner_edit_block
    assert "name=\"category_ids\"" in partner_edit_block
    assert "renderSelect('owner_user_id'" in partner_edit_block
    assert "adminPartnerField: 'city'" in partner_edit_block
    assert "adminPartnerField: 'owner'" in partner_edit_block
    assert '<select name="city_id"' not in partner_edit_block
    assert '<select name="category_slug"' not in partner_edit_block
    assert '<select name="owner_user_id"' not in partner_edit_block


def test_frontend_applies_custom_selects_to_admin_role_offer_and_activity_filters() -> None:
    source = _frontend_main()

    users_block = source.split("const renderUsersTab = () => {", 1)[1].split("const renderCityActionButtons", 1)[0]
    assert "renderSelect('role'" in users_block
    assert "adminUserRole: true" in users_block

    partner_picker_block = source.split("const renderPartnerPicker = (scope, selectedValue) =>", 1)[1].split("const showAdminDashboard", 1)[0]
    assert "renderCustomSelect" in partner_picker_block
    assert "name: 'partner_id'" in partner_picker_block
    assert "data: { partnerPicker: scope }" in partner_picker_block

    activity_block = source.split("const renderAdminActivityTab = () =>", 1)[1].split("const renderOverviewTab", 1)[0]
    assert "renderCustomSelect" in activity_block
    assert "name: 'event_type'" in activity_block
    assert "data: { adminActivityEventType: true }" in activity_block

    assert "data-custom-select-name" in source
    assert "custom-select:change" in source


def test_frontend_preserves_native_select_fallback_styles() -> None:
    styles = _frontend_styles()

    for expected_marker in (
        "Rose glass native select styling",
        ".form-select",
        ".app-select",
        ".select-field",
        "select option",
        "select:focus-visible",
        "select:disabled",
    ):
        assert expected_marker in styles


def test_frontend_adds_subtle_center_sakura_motion() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    assert "Array.from({ length: 20 }" in source
    assert "sakura-petal--center" in source
    assert "sakura-petal--center-${index + 1}" in source
    assert "sakura-petal--center-1" in styles
    assert "sakura-petal--center-20" in styles
    assert "--center-left: 35%" in styles
    assert "--center-left: 65%" in styles
    assert "--center-opacity: 0.22" in styles
    assert "--center-opacity: 0.38" in styles
    assert "will-change: transform;" in _css_block(styles, ".sakura-petal--center")

def test_brand_copy_targets_girls() -> None:
    source = _frontend_main()

    assert "Федеральный клуб привилегий для девушек" in source
    assert "Федеральный клуб привилегий для женщин" not in source


def test_public_brand_block_links_back_to_landing_top() -> None:
    source = _frontend_main()

    assert 'class="editorial-brand" href="#landing-about"' in source
    assert 'aria-label="Bloom Club — на главную"' in source


def test_public_header_does_not_render_admin_panel_action() -> None:
    source = _frontend_main()
    topbar_match = re.search(r'<header class="editorial-header".*?</header>', source, re.S)

    assert topbar_match is not None
    assert "Панель" not in topbar_match.group(0)


def test_city_selector_uses_static_choice_chips() -> None:
    source = _frontend_main()
    city_selector_block = source.split('<footer class="editorial-footer"')[0]

    for forbidden_tag in ("<select", "<option", "<details", "<summary"):
        assert forbidden_tag not in city_selector_block

    assert 'class="city-choice-grid"' in source
    assert "city-choice${index === 0 ? ' is-active' : ''}" in source
    assert _city_options() == ["Новосибирск", "Череповец"]
    assert "Новосибирск" in source
    assert "Череповец" in source


def test_frontend_city_selector_options_are_limited_to_active_cities() -> None:
    assert _city_options() == ["Новосибирск", "Череповец"]


def test_removed_cities_are_not_in_frontend_city_selector() -> None:
    source = _frontend_main()
    cities = _city_options()

    for removed_city in ("Москва", "Санкт-Петербург", "Екатеринбург", "Казань"):
        assert removed_city not in cities
        assert removed_city not in source


def test_city_growth_note_is_present() -> None:
    assert (
        "Чем больше мы растём, тем больше городов подключаем. "
        "Скоро появятся новые города."
    ) in _frontend_main()


def test_frontend_contains_real_login_form_and_dashboard_strings() -> None:
    source = _frontend_main()

    assert 'data-login-form' in source
    assert 'name="email"' in source
    assert 'name="password"' in source
    assert '/api/v1/auth/login' in source
    assert '/api/v1/admin/me' in source
    assert 'Панель администратора' in source
    assert 'Неверный логин или пароль' in source
    assert 'localStorage.setItem(authTokenKey, data.access_token)' in source


def test_frontend_contains_dashboard_shell_classes() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "dashboard-shell",
        "dashboard-layout",
        "dashboard-sidebar",
        "dashboard-main",
        "dashboard-topbar",
        "Быстрые действия",
    ):
        assert expected in source or expected in styles

    assert "--dashboard-width: min(1680px, calc(100vw - 48px));" in styles
    assert "grid-template-columns: 260px minmax(0, 1fr);" in styles
    assert ".dashboard-main" in styles
    assert "min-width: 0;" in styles


def test_frontend_removes_broken_lotus_background() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for removed_lotus_marker in (
        "reference-lotus-layer",
        "lotus-layer",
        "lotus-decor",
        "--user-lotus-reference-svg",
        "--lotus-reference-background",
        "--lotus-left-composition",
        "--lotus-right-composition",
        "--lotus-swirl-line",
        "--lotus-line-art",
        "--lotus-botanical-line-art",
        "--lotus-botanical-composition",
    ):
        assert removed_lotus_marker not in source
        assert removed_lotus_marker not in styles

    assert ".hero::before" not in styles
    assert "body:not(.is-dashboard)::before" not in styles
    assert "/assets/lotus-bg.png" not in source
    assert "/assets/lotus-bg.png" not in styles

    for expected in (
        "Женский клуб",
        "Федеральный клуб привилегий для девушек",
        "Новосибирск",
        "Череповец",
        "dashboard-shell",
        "dashboard-topbar",
        "dashboard-sidebar",
        "dashboard-main",
        "womenClubAdminAccessToken",
        "womenclub_partner_token",
        "womenclub_client_token",
    ):
        assert expected in source or expected in styles


def test_frontend_keeps_required_public_role_nav_and_token_copy() -> None:
    source = _frontend_main()

    for expected in (
        "Женский клуб",
        "Федеральный клуб привилегий для девушек",
        "Новосибирск",
        "Череповец",
        "Панель администратора",
        "Кабинет партнёра",
        "Личный кабинет",
        "Главная",
        "Пользователи",
        "Города",
        "Категории",
        "Партнёры",
        "Предложения",
        "QR / лиды",
        "Подтверждения",
        "womenClubAdminAccessToken",
        "womenclub_partner_token",
        "womenclub_client_token",
    ):
        assert expected in source





def test_frontend_contains_compact_admin_table_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "admin-table-action",
        "admin-table--compact",
        "admin-table-cell--actions",
        "text-overflow: ellipsis",
        "overflow-wrap",
        "table-layout",
    ):
        assert expected in source or expected in styles

    for tab_text in (
        "Пользователи",
        "Города",
        "Категории",
        "Партнёры",
        "Предложения",
        "QR / лиды",
        "Подтв…13055 tokens truncated… marker in source or marker in styles


def test_frontend_contains_derived_activity_feed_ui_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Активность",
        "Событий пока нет.",
        "Загружаем события",
        "Не удалось загрузить события",
        "Здесь появятся ваши действия",
        "Лента помогает быстро видеть",
        "Все события",
        "QR-переходы",
        "/api/v1/clients/me/activity",
        "/api/v1/partners/me/activity",
        "/api/v1/admin/activity",
        "renderActivityFeed",
        "renderActivityItem",
        "formatActivityDate",
        "privilege_created",
        "privilege_confirmed",
        "privilege_expired",
        "qr_clicked",
        "partner_created",
        "offer_created",
        "qr_link_created",
    ):
        assert expected in source

    for expected_style in (
        "activity-feed",
        "activity-item",
        "activity-badge",
        "activity-badge--privilege",
        "activity-badge--confirmed",
        "activity-badge--expired",
        "activity-badge--qr",
        "activity-badge--partner",
        "activity-meta",
        "activity-empty",
        "activity-filter",
    ):
        assert expected_style in source or expected_style in styles

    for preserved_marker in (
        "partner-marketplace-card",
        "offer-marketplace-card",
        "partner-gallery",
        "partner-gallery-grid",
        "data-privilege-success-panel",
        "data-client-privilege-card",
        "data-partner-confirmation-card",
        "analytics-grid",
        "analytics-card",
        "analyticsLoading",
        "setup_token",
        "/api/v1/auth/password-setup/complete",
        "/api/v1/public/landing/partners",
        "/api/v1/clients/catalog/partners",
        "dashboard-shell",
        "dashboard-topbar",
        "dashboard-sidebar",
        "dashboard-main",
        "womenclub_partner_token",
        "womenclub_client_token",
        "womenClubAdminAccessToken",
        "startsWith('/uploads/')",
    ):
        assert preserved_marker in source or preserved_marker in styles

    for removed_lotus_marker in (
        "reference-lotus-layer",
        "lotus-layer",
        "lotus-decor",
        "--user-lotus-reference-svg",
        "--lotus-reference-background",
        "/assets/lotus-bg.png",
    ):
        assert removed_lotus_marker not in source
        assert removed_lotus_marker not in styles


def test_frontend_contains_admin_partner_detail_screen_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Назад к списку партнёров",
        "Редактирование партнёра",
        "Основные данные",
        "Изображения партнёра",
        "Галерея партнёра",
        "Preview для клиентского каталога",
    ):
        assert expected in source

    for expected_style in (
        "admin-partner-detail",
        "admin-partner-detail-header",
        "admin-partner-detail-grid",
        "admin-partner-detail-main",
        "admin-partner-detail-side",
        "admin-partner-detail-section",
        "admin-back-button",
    ):
        assert expected_style in source or expected_style in styles

    for preserved_marker in (
        "partner-marketplace-card",
        "publish-readiness",
        "partner-gallery",
        "partner-image-uploader",
        "content-review",
        "content-review-preview",
        "analytics-grid",
        "analytics-card",
        "offer-image-uploader",
        "setup_token",
        "/api/v1/public/landing/partners",
    ):
        assert preserved_marker in source or preserved_marker in styles


def test_frontend_contains_admin_publish_readiness_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Готовность к публикации",
        "Готов к публикации",
        "Нужно доработать",
        "Проверьте базовые элементы витрины",
        "Обложка добавлена",
        "Логотип добавлен",
        "Описание заполнено",
        "Адрес заполнен",
        "График работы заполнен",
        "Есть активное предложение",
        "Партнёр активен",
        "Партнёр проверен",
        "renderPublishReadiness",
        "getAdminLoadedOffersForPartner",
    ):
        assert expected in source

    for expected_style in (
        "publish-readiness",
        "publish-readiness-checklist",
        "publish-readiness-item--ok",
        "publish-readiness-item--warn",
    ):
        assert expected_style in source or expected_style in styles

    for preserved_marker in (
        "content-review",
        "content-review-card",
        "content-review-preview",
        "/api/v1/admin/content-review",
        "offer-image-uploader",
        "partner-image-uploader",
        "partner-gallery",
        "partner-gallery-grid",
        "offer-marketplace-card",
        "partner-marketplace-card",
        "analytics-grid",
        "analytics-card",
        "analyticsLoading",
        "/api/v1/admin/activity",
        "activity-feed",
        "data-privilege-success-panel",
        "data-client-privilege-card",
        "data-partner-confirmation-card",
        "setup_token",
        "/api/v1/auth/password-setup/complete",
        "/api/v1/public/landing/partners",
        "/api/v1/clients/catalog/partners",
        "womenclub_partner_token",
        "womenclub_client_token",
        "womenClubAdminAccessToken",
        "startsWith('/uploads/')",
    ):
        assert preserved_marker in source or preserved_marker in styles

    for removed_lotus_marker in (
        "reference-lotus-layer",
        "lotus-layer",
        "lotus-decor",
        "--user-lotus-reference-svg",
        "--lotus-reference-background",
        "/assets/lotus-bg.png",
    ):
        assert removed_lotus_marker not in source
        assert removed_lotus_marker not in styles


def test_frontend_contains_admin_content_review_queue_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()
    admin_endpoints = _admin_endpoints()

    for expected in (
        "На проверке",
        "Партнёров на проверке нет.",
        "Новые предложения и фото перед публикацией",
        "Активировать",
        "Фото галереи",
        "content-review",
        "content-review-card",
        "content-review-preview",
        "/api/v1/admin/content-review",
        "/api/v1/admin/offers/${offerId}",
        "/api/v1/admin/offers/",
        "/api/v1/admin/partner-photos/${photoId}",
        "/api/v1/admin/partner-photos/",
    ):
        assert expected in source or expected in styles or expected in admin_endpoints

    for expected_style in (
        ".content-review",
        ".content-review-section",
        ".content-review-card",
        ".content-review-preview",
        ".content-review-actions",
        ".content-review-empty",
    ):
        assert expected_style in styles

    for preserved_marker in (
        "Публикация после проверки администратором.",
        "Предложение отправлено на проверку. После активации администратором оно появится у клиентов.",
        "Публикация после проверки.",
        "Фото загружено и отправлено на проверку.",
        "Ожидает активации.",
        "/api/v1/partners/me/activity",
        "/api/v1/partners/me/analytics",
        "/api/v1/admin/activity",
        "offer-image-uploader",
        "partner-image-uploader",
        "partner-gallery",
        "partner-gallery-grid",
        "offer-marketplace-card",
        "partner-marketplace-card",
        "data-privilege-success-panel",
        "data-client-privilege-card",
        "setup_token",
        "/api/v1/auth/password-setup/complete",
        "/api/v1/public/landing/partners",
        "/api/v1/clients/catalog/partners",
        "womenclub_partner_token",
        "womenclub_client_token",
        "womenClubAdminAccessToken",
    ):
        assert preserved_marker in source or preserved_marker in styles

    for removed_lotus_marker in (
        "reference-lotus-layer",
        "lotus-layer",
        "lotus-decor",
        "--user-lotus-reference-svg",
        "--lotus-reference-background",
        "/assets/lotus-bg.png",
    ):
        assert removed_lotus_marker not in source
        assert removed_lotus_marker not in styles


def test_frontend_dist_build_points_to_assets_bundle() -> None:
    dist_index = FRONTEND_DIR / "dist" / "index.html"
    dist_assets = FRONTEND_DIR / "dist" / "assets"

    assert dist_index.exists(), "Expected frontend/dist/index.html after npm run build"
    assert dist_assets.exists(), "Expected frontend/dist/assets after npm run build"

    dist_html = dist_index.read_text(encoding="utf-8")
    assert "/src/main.js" not in dist_html
    assert "/src/styles.css" not in dist_html

    assert '/assets/styles.css' in dist_html
    assert '/assets/main.js' in dist_html

    assert any(path.suffix == ".js" for path in dist_assets.iterdir())
    assert any(path.suffix == ".css" for path in dist_assets.iterdir())

def test_admin_partner_create_page_markers_present() -> None:
    source = _frontend_main()

    for marker in (
        "admin-partner-create-page",
        "Основная информация",
        "Категории",
        "Контакты",
        "Сайт и соцсети",
        "Доступ и публикация",
        "Назад к партнёрам",
        "Сохранить партнёра",
        "adminState.partnerFormOpen",
        "category_ids",
        "Можно выбрать несколько.",
        "type=\"button\"",
        "data-admin-partner-wizard-form",
        "admin-partner-create-form",
    ):
        assert marker in source


def test_admin_partner_create_page_uses_single_save_action_markers() -> None:
    source = _frontend_main()

    for marker in (
        'data-admin-form="partner"',
        'type="submit">Сохранить партнёра</button>',
        'data-admin-partner-edit-cancel',
        'adminState.partnerFormOpen = true;',
    ):
        assert marker in source

    form_block = source.split('const renderPartnerForm = () => {', 1)[1].split('const defaultPartnerFilters = () => ({', 1)[0]
    assert 'data-admin-partner-step-jump' not in form_block



def test_admin_partner_create_save_button_is_native_and_not_disabled() -> None:
    source = _frontend_main()
    form_block = source.split('const renderPartnerForm = () => {', 1)[1].split('const defaultPartnerFilters = () => ({', 1)[0]

    assert 'id="admin-partner-create-form"' in form_block
    assert 'data-admin-partner-wizard-form' in form_block
    save_button_line = 'type="submit">Сохранить партнёра</button>'
    assert save_button_line in form_block
    assert 'disabled' not in save_button_line


def test_admin_partner_category_only_save_still_posts_patch_payload() -> None:
    source = _frontend_main()
    edit_block = source.split('const submitPartnerEdit = async (form) => {', 1)[1].split('const decimalOrNull', 1)[0]
    payload_block = source.split('const buildAdminPartnerPayload = (formData, selectedCategoryIds = null) => ({', 1)[1].split('const submitPartner = async', 1)[0]

    assert 'const selectedCategoryIds = captureAdminPartnerCategoryDraft(form);' in edit_block
    assert 'const formData = new FormData(form);' in edit_block
    assert 'patchJson(`/api/v1/admin/partners/${partnerId}`, buildAdminPartnerPayload(formData, selectedCategoryIds))' in edit_block
    assert 'category_ids: getAdminPartnerPayloadCategoryIds(formData, selectedCategoryIds)' in payload_block
    assert "formData.getAll('category_ids')" in source


def test_admin_partner_validation_block_shows_visible_message() -> None:
    source = _frontend_main()
    validation_block = source.split('const validateRequiredCustomSelects = (form) => {', 1)[1].split('const moveCustomSelectActiveOption', 1)[0]

    assert 'Заполните обязательное поле:' in validation_block
    assert 'adminState.partnerFormInlineError = message;' in validation_block
    assert 'setFormMessage(formType, message);' in validation_block
    assert 'messageNode.textContent = message;' in validation_block
    assert 'inlineErrorNode.textContent = message;' in validation_block

def test_admin_partner_create_reset_and_category_edit_markers() -> None:
    source = _frontend_main()

    for marker in (
        "adminState.partnerFormInlineError = '';",
        "adminState.selectedPartnerIdForEdit = '';",
        "name=\"category_ids\"",
        "selectedCategoryIds.has(String(category.id)) ? 'checked' : ''",
    ):
        assert marker in source



def test_admin_partner_category_payload_uses_current_checkbox_state_and_refreshes_row() -> None:
    source = _frontend_main()
    payload_block = source.split("const buildAdminPartnerPayload = (formData, selectedCategoryIds = null) => ({", 1)[1].split("const submitPartner = async", 1)[0]
    edit_block = source.split("const submitPartnerEdit = async (form) => {", 1)[1].split("const decimalOrNull", 1)[0]

    assert "category_ids: getAdminPartnerPayloadCategoryIds(formData, selectedCategoryIds)" in payload_block
    assert "const selectedCategoryIds = captureAdminPartnerCategoryDraft(form);" in edit_block
    assert "const updatedPartner = await patchJson(`/api/v1/admin/partners/${partnerId}`, buildAdminPartnerPayload(formData, selectedCategoryIds));" in edit_block
    assert "adminState.partners = adminState.partners.map" in edit_block
    assert "await loadPartners();" in edit_block


def test_admin_partner_category_state_is_captured_on_submit_and_edit() -> None:
    source = _frontend_main()

    for marker in (
        "partnerFormCategoryIds",
        "captureAdminPartnerCategoryDraft",
        "getAdminPartnerSelectedCategoryIds",
        "input[name=\"category_ids\"]:checked",
        "selectedCategoryIds.has(String(category.id)) ? 'checked' : ''",
    ):
        assert marker in source

def test_offer_pricing_helpers_and_copy_present() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for marker in (
        'const getOfferPricingView = (offer = {}) =>',
        'const renderOfferPricingBlock = (offer, options = {}) =>',
        'Обычная цена',
        'Цена участницы',
        'Экономия',
        'renderOfferPricingBlock(offer)',
        'offer_id',
        'saving_amount',
        'discount_percent',
        'Экономия ${formatMoneyLabel(pricing.savingAmount)}',
        'Привилегии у партнёров',
        'Доступ к привилегиям, подаркам',
        'Обычная цена:',
    ):
        assert marker in source

    for css_marker in (
        '.offer-pricing',
        '.offer-pricing__row',
        '.offer-pricing__label',
        '.offer-pricing__value',
        '.offer-pricing__value--base',
        '.offer-pricing__value--member',
        '.offer-pricing__saving',
        '.offer-pricing__fallback',
        '.landing-partner-gallery-backdrop',
        '.landing-partner-gallery-image',
        'object-fit: contain',
    ):
        assert css_marker in styles


def test_landing_partner_filter_uses_categories_array_and_keeps_direction_markers() -> None:
    source = _frontend_main()

    for marker in (
        "selectedLandingDirection",
        "landingPartnerModalState",
        "data-landing-category-slug",
        "editorial-category-card",
        "editorial-directions",
        "/api/v1/public/landing/partners",
    ):
        assert marker in source

    assert "partnerMatchesLandingCategory" in source
    assert "Array.isArray(partner?.categories) ? partner.categories : []" in source
    assert "categories.some((category)" in source
    assert "partners.filter((partner) => partnerMatchesLandingCategory(partner, slug))" in source


def test_admin_partner_category_payload_uses_captured_checked_ids_not_initial_partner_categories() -> None:
    source = _frontend_main()

    assert "const selectedCategoryIds = captureAdminPartnerCategoryDraft(form);" in source
    assert "buildAdminPartnerPayload(formData, selectedCategoryIds)" in source
    assert "category_ids: getAdminPartnerPayloadCategoryIds(formData, selectedCategoryIds)" in source
    assert "formData.getAll('category_ids').map((id) => Number(id)).filter((id) => Number.isFinite(id))" not in source


def test_admin_partner_manicure_checkbox_uses_category_id_value_with_slug_title_diagnostics() -> None:
    source = _frontend_main()

    assert "{ slug: 'manikyur-pedikyur', title: 'Маникюр / педикюр' }" in source
    assert 'name="category_ids" value="${escapeHtml(category.id)}"' in source
    assert 'data-category-id="${escapeHtml(category.id)}"' in source
    assert 'data-category-slug="${escapeHtml(category.slug || \'\')}"' in source
    assert 'data-category-title="${escapeHtml(category.title || category.name || \'\')}"' in source
    assert 'value="${escapeHtml(category.slug)}"' not in source
    assert 'value="${escapeHtml(category.title)}"' not in source


def test_admin_partner_save_updates_table_from_patch_response_then_uncached_refetch() -> None:
    source = _frontend_main()

    submit_edit = re.search(r"const submitPartnerEdit = async \(form\) => \{(.*?)\n\};", source, re.S)
    assert submit_edit is not None
    submit_edit_body = submit_edit.group(1)
    assert "const updatedPartner = await patchJson" in submit_edit_body
    assert "adminState.partners = adminState.partners.map" in submit_edit_body
    assert "? updatedPartner : partner" in submit_edit_body
    assert "await loadPartners();" in submit_edit_body
    assert "cache: fetchOptions.cache || 'no-store'" in source


def test_admin_partner_reopening_drawer_uses_updated_partner_category_ids() -> None:
    source = _frontend_main()

    assert "const selectedCategoryIds = getAdminPartnerSelectedCategoryIds(isEditMode ? partner : null, activeCategories);" in source
    assert "return new Set(partner ? getPartnerCategoryIdStrings(partner, activeCategories) : []);" in source
    assert "resetAdminPartnerCategoryDraft(partnerId);" in source


def test_admin_legacy_content_readonly_notice_and_flag_handling_present() -> None:
    source = _frontend_main()
    styles = FRONTEND_STYLES.read_text(encoding="utf-8")

    assert "legacy_content_write_enabled" in source
    assert "legacyContentWriteEnabled" in source
    assert "Редактирование контента перенесено в Telegram Admin Bot" in source
    assert "renderLegacyContentNotice" in source
    assert "guardLegacyContentWrite" in source
    assert "data-legacy-content-form" in source
    assert "admin-readonly-notice" in styles

