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


def test_public_brand_block_is_static_not_clickable() -> None:
    source = _frontend_main()

    assert '<div class="brand" aria-label="Женский клуб">' in source
    assert not re.search(r'<a[^>]*class="brand"', source)
    assert not re.search(r'<button[^>]*class="brand"', source)
    assert not re.search(r'class="brand"[^>]*(href|type)=', source)


def test_public_header_does_not_render_admin_panel_action() -> None:
    source = _frontend_main()
    topbar_match = re.search(r'<div class="topbar-actions".*?</div>', source, re.S)

    assert topbar_match is not None
    assert "Панель" not in topbar_match.group(0)


def test_city_selector_uses_static_choice_chips() -> None:
    source = _frontend_main()
    city_selector_block = source.split('<section class="panel" aria-labelledby="login-title" id="login">')[0]

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
        "Подтверждения",
    ):
        assert tab_text in source


def test_frontend_contains_admin_search_filter_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "admin-search",
        "admin-search-input",
        "admin-toolbar",
        "admin-search-reset",
    ):
        assert expected in source or expected in styles

    for placeholder in (
        "Поиск по пользователям",
        "Поиск по городам",
        "Поиск по категориям",
        "Поиск по партнёрам",
        "Поиск по предложениям",
        "Поиск по QR",
        "Поиск по лидам",
        "Поиск по подтверждениям",
    ):
        assert placeholder in source

    for helper_marker in (
        "normalizeSearchText",
        "filterAdminRows",
        "data-admin-search",
        "data-admin-search-reset",
        "Ничего не найдено.",
    ):
        assert helper_marker in source


def test_frontend_contains_reusable_status_badges() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "renderStatusBadge",
        "status-badge",
        "status-badge--success",
        "status-badge--muted",
        "status-badge--warning",
        "status-badge--danger",
    ):
        assert expected in source or expected in styles

    for expected_label in (
        "Активен",
        "Неактивен",
        "Активна",
        "Неактивна",
        "Проверен",
        "Не проверен",
        "Подтверждено",
        "Истекло",
        "Отменено",
    ):
        assert expected_label in source

    for preserved_marker in (
        "Пользователи",
        "Города",
        "Категории",
        "Партнёры",
        "Предложения",
        "QR / лиды",
        "Подтверждения",
        "Личный кабинет",
        "Кабинет партнёра",
        "womenClubAdminAccessToken",
        "womenclub_partner_token",
        "womenclub_client_token",
        "dashboard-shell",
        "dashboard-topbar",
        "dashboard-sidebar",
        "dashboard-main",
        "Женский клуб",
        "Федеральный клуб привилегий для девушек",
        "Новосибирск",
        "Череповец",
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


def test_frontend_contains_human_readable_admin_labels() -> None:
    source = _frontend_main()

    for expected in (
        "Название города",
        "Порядок сортировки",
        "Владелец / аккаунт партнёра",
        "Название партнёра",
        "Ссылка на соцсеть / сайт",
        "Название предложения",
        "Базовая цена",
        "Скидка, %",
        "Целевая ссылка",
        "Подтверждено",
        "Email",
        "Телефон",
        "Роль",
        "Активен",
        "Действие",
        "Клиент",
        "Администратор",
    ):
        assert expected in source


def test_frontend_does_not_render_technical_admin_labels() -> None:
    source = _frontend_main()
    rendered_table_headers = "\n".join(re.findall(r"renderTable\(\[(.*?)\]", source, re.S))

    for forbidden_label in (
        "city_id",
        "owner_user_id",
        "category_slug",
        "sort_order",
        "is_active",
    ):
        assert f">{forbidden_label}<" not in source
        assert f">{forbidden_label}" not in source
        assert f"'{forbidden_label}'" not in rendered_table_headers
        assert f'"{forbidden_label}"' not in rendered_table_headers


def test_frontend_contains_admin_cabinet_tabs() -> None:
    source = _frontend_main()

    for tab_text in (
        "Панель администратора",
        "Главная",
        "Обзор",
        "Пользователи",
        "Города",
        "Категории",
        "Партнёры",
        "Предложения",
        "QR / лиды",
        "Подтверждения",
    ):
        assert tab_text in source



def test_frontend_contains_admin_payment_requests_ui_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Оплаты",
        "Заявки на оплату",
        "Проверяйте ручные оплаты",
        "Заявок на оплату пока нет",
        "Подтвердить",
        "Отклонить",
        "Ожидает отметки клиента",
        "Подписка продлена",
        "/api/v1/admin/payment-requests",
        "/approve",
        "/reject",
        "admin-payments",
        "admin-payment-card",
        "admin-payment-actions",
        "admin-payment-receipts",
        "custom-select",
        "data-custom-select",
        "custom-select:change",
    ):
        assert expected in source or expected in styles

    for preserved_marker in (
        "Партнёры",
        "Предложения",
        "На проверке",
        "Активность",
        "Аналитика",
        "Кабинет клуба",
        "Кабинет партнёра",
        "Личный кабинет",
        "setup-password",
        "landing",
        "reference-lotus-layer",
        "/assets/lotus-bg.png",
    ):
        if preserved_marker in ("reference-lotus-layer", "/assets/lotus-bg.png"):
            assert preserved_marker not in source
            assert preserved_marker not in styles
        else:
            assert preserved_marker in source or preserved_marker in styles

def test_frontend_contains_admin_cabinet_endpoint_strings() -> None:
    source = _frontend_main()

    for endpoint in (
        "/api/v1/admin/users",
        "/api/v1/admin/cities",
        "/api/v1/admin/categories",
        "/api/v1/admin/partners",
        "/api/v1/admin/leads/partners",
        "/api/v1/admin/verifications",
    ):
        assert endpoint in source


def test_admin_categories_support_create_edit_and_safe_toggle_ui() -> None:
    endpoints = _admin_endpoints()
    schemas = _admin_schemas()
    source = _frontend_main()

    assert '@router.get("/categories", response_model=list[CategoryRead])' in endpoints
    assert '@router.post("/categories", response_model=CategoryRead)' in endpoints
    assert '@router.patch("/categories/{category_id}", response_model=CategoryRead)' in endpoints
    assert '@router.delete("/categories/{category_id}"' not in endpoints
    assert 'class CategoryCreate' in schemas
    assert 'class CategoryUpdate' in schemas

    for marker in (
        "Новая категория",
        "Редактировать категорию",
        "Редактировать",
        "Деактивировать",
        "Активировать",
        "Название",
        "Slug",
        "Активна",
        "Порядок сортировки",
        "Отмена",
        "postJson('/api/v1/admin/categories'",
        "patchJson(`/api/v1/admin/categories/${categoryId}`",
        "data-admin-category-edit",
        "data-admin-category-active-toggle",
        "category_ids",
        "getPartnerCategories",
        "partner-multicategory",
        "category-chip",
    ):
        assert marker in source




def test_admin_partners_phase2_form_toggle_and_sections_markers() -> None:
    source = _frontend_main()

    for marker in (
        "adminState.partnerFormOpen",
        "data-admin-partner-create",
        "+ Добавить партнёра",
        "data-admin-partner-edit",
        "data-admin-partner-edit-cancel",
        "admin-partner-form-panel",
        "<h5 class=\"admin-form-section__title\">Основное</h5>",
        "<h5 class=\"admin-form-section__title\">Статусы</h5>",
        "<h5 class=\"admin-form-section__title\">Категории</h5>",
        "<h5 class=\"admin-form-section__title\">Контакты</h5>",
        "<h5 class=\"admin-form-section__title\">Описание</h5>",
        "<h5 class=\"admin-form-section__title\">Медиа</h5>",
        "admin-partners-layout",
        "admin-partners-table",
        "partnerFilters",
        "data-admin-partner-filter",
        "data-admin-partner-filter-reset",
        "data-admin-partner-filter-clear",
        "Найдено:",
        "По выбранным фильтрам партнёры не найдены.",
        "renderPartnersList(partners, adminState.partners)",
        "renderPartnerForm()",
        "adminState.partnerFormOpen = true;",
        "adminState.partnerFormOpen = false;",
    ):
        assert marker in source

    assert "adminState.partnerFormOpen ? '' : 'hidden'" in source
    assert 'class="admin-partner-form-panel is-open"' not in source



def test_admin_partners_phase21_filters_and_category_normalization_markers() -> None:
    source = _frontend_main()

    for marker in (
        "city: ''",
        "category: ''",
        "activity: 'all'",
        "photos: 'all'",
        "offers: 'all'",
        "getPartnerCategories(partner)",
        "name === '[object Object]'",
        "slug === '[object Object]'",
        "+ Добавить партнёра",
        "adminState.partnerFormOpen",
    ):
        assert marker in source
def test_frontend_category_admin_keeps_public_dashboard_and_removed_image_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for marker in (
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
        assert marker in source

    for removed_marker in (
        "reference-lotus-layer",
        "lotus-layer",
        "lotus-decor",
        "--user-lotus-reference-svg",
        "--lotus-reference-background",
        "/assets/lotus-bg.png",
    ):
        assert removed_marker not in source
        assert removed_marker not in styles


def test_frontend_contains_admin_user_role_options() -> None:
    source = _frontend_main()

    for role in ("client", "partner", "admin"):
        assert role in source


def test_frontend_contains_admin_users_management_ui_strings() -> None:
    source = _frontend_main()

    for expected in (
        "data-admin-form=\"user\"",
        "data-user-active-toggle",
        "Создать пользователя",
        "owner_user_id",
        "Без владельца",
        "owner_email",
    ):
        assert expected in source


def test_public_landing_copy_and_city_chips_remain_intact() -> None:
    source = _frontend_main()

    for public_copy in (
        "Женский клуб",
        "Федеральный клуб привилегий для девушек",
        "Новосибирск",
        "Череповец",
    ):
        assert public_copy in source


def test_frontend_contains_admin_city_edit_and_safe_deactivate_ui() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Редактировать город",
        "Редактировать",
        "Деактивировать",
        "Убрать город из активных?",
        "data-admin-city-edit",
        "data-admin-city-active-toggle",
        "Название",
        "Slug",
        "Активен",
        "Порядок сортировки",
        "Отмена",
        "POST",
        "PATCH",
        "/api/v1/admin/cities",
        "patchJson(`/api/v1/admin/cities/${cityId}`",
        "is_active: city.is_active ? false : true",
        "await loadCities();",
    ):
        assert expected in source or expected in styles


def test_frontend_city_management_keeps_required_landing_dashboard_and_negative_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

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

    for removed_marker in (
        "reference-lotus-layer",
        "lotus-layer",
        "lotus-decor",
        "--user-lotus-reference-svg",
        "--lotus-reference-background",
        "/assets/lotus-bg.png",
    ):
        assert removed_marker not in source
        assert removed_marker not in styles


def test_frontend_contains_admin_partner_edit_ui() -> None:
    source = _frontend_main()

    for expected in (
        "Редактирование партнёра",
        "Редактировать",
        "/api/v1/admin/partners/",
        "Город",
        "Категория",
        "Владелец",
        "Без владельца",
        "Название",
        "Описание",
        "Адрес",
        "Телефон",
        "Сайт",
        "Соцсеть",
        "Активен",
        "Проверен",
    ):
        assert expected in source


def test_frontend_contains_admin_offer_edit_ui() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Редактировать предложение",
        "Редактировать",
        "/api/v1/admin/offers/",
        "PATCH",
        "Название",
        "Описание",
        "Скидка / выгода",
        "Условия",
        "Активно",
        "Отмена",
        "POST",
        "/api/v1/admin/partners/",
        "/offers",
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


def test_frontend_contains_admin_qr_edit_ui() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Редактировать QR-ссылку",
        "Редактировать",
        "/api/v1/admin/qr-links/",
        "PATCH",
        "Slug",
        "Целевая ссылка",
        "Deep-link payload",
        "Активна",
        "Отмена",
        "POST",
        "/api/v1/admin/partners/",
        "/qr-links",
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


def test_frontend_keeps_landing_and_dashboard_markers_with_partner_edit() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

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


def test_frontend_login_modes_remain_available() -> None:
    source = _frontend_main()

    for expected in (
        "Администратор",
        "Партнёр",
        "Клиент",
    ):
        assert expected in source


def test_frontend_contains_partner_cabinet_foundation() -> None:
    source = _frontend_main()

    for expected in (
        "Кабинет партнёра",
        "Партнёр",
        "Профиль",
        "Предложения",
        "QR / лиды",
        "Подтверждения",
    ):
        assert expected in source


def test_frontend_contains_partner_endpoint_strings_and_separate_token() -> None:
    source = _frontend_main()

    for endpoint in (
        "/api/v1/auth/user-login",
        "/api/v1/auth/user-me",
        "/api/v1/partners/me",
        "/api/v1/partners/me/offers",
        "/api/v1/partners/me/qr-links",
        "/api/v1/partners/me/leads",
        "/api/v1/partners/me/verifications",
    ):
        assert endpoint in source

    assert "/api/v1/auth/login" in source
    assert "womenclub_partner_token" in source


def test_partner_cabinet_uses_human_readable_copy_statuses_and_empty_states() -> None:
    source = _frontend_main()

    for expected in (
        "Пока нет предложений.",
        "Добавьте первое предложение",
        "Пока нет QR-ссылок.",
        "Создайте QR-ссылку",
        "Пока нет лидов.",
        "Когда клиенты перейдут по QR-ссылке",
        "Пока нет подтверждений.",
        "Когда клиент покажет код привилегии",
        "Активен",
        "Неактивен",
        "Проверен",
        "Не проверен",
        "Активно",
        "Неактивно",
        "Активна",
        "Неактивна",
        "Подтверждено",
        "Истекло",
        "Отменено",
        "Название",
        "Краткая выгода",
        "Описание",
        "Условия",
        "Базовая цена",
        "Код ссылки",
        "Целевая ссылка",
        "Подтвердить привилегию",
    ):
        assert expected in source

    for marker in (
        "womenclub_partner_token",
        "womenclub_client_token",
        "womenClubAdminAccessToken",
        "dashboard-shell",
        "dashboard-topbar",
        "dashboard-sidebar",
        "dashboard-main",
        "Женский клуб",
        "Федеральный клуб привилегий для девушек",
        "Новосибирск",
        "Череповец",
    ):
        assert marker in source

    assert "renderStatusBadge(formatStatus(item.status))" in source
    assert "renderActiveStatusBadge(offer.is_active)" in source
    assert "renderActiveStatusFeminineBadge(link.is_active)" in source

def test_frontend_contains_client_cabinet_foundation() -> None:
    source = _frontend_main()

    for expected in (
        "Личный кабинет",
        "Клиент",
        "Профиль",
        "Каталог",
        "Моя подписка",
        "История",
    ):
        assert expected in source


def test_frontend_contains_client_endpoint_strings_and_separate_token() -> None:
    source = _frontend_main()

    for endpoint in (
        "/api/v1/auth/user-login",
        "/api/v1/auth/user-me",
        "/api/v1/clients/me",
        "/api/v1/clients/me/subscription",
        "/api/v1/clients/catalog/partners",
        "/api/v1/clients/partners/",
        "/api/v1/clients/me/verifications",
    ):
        assert endpoint in source

    assert "womenclub_client_token" in source
    assert "womenClubAdminAccessToken" in source
    assert "womenclub_partner_token" in source


def test_frontend_contains_client_vk_link_code_ui() -> None:
    source = _frontend_main()

    for expected in (
        "Привязка VK",
        "Создать код для VK",
        "/api/v1/clients/me/vk-link-codes",
        "Привязать",
    ):
        assert expected in source

    assert "womenclub_client_token" in source
    assert "womenClubAdminAccessToken" in source
    assert "womenclub_partner_token" in source

    for public_copy in (
        "Женский клуб",
        "Федеральный клуб привилегий для девушек",
        "Новосибирск",
        "Череповец",
    ):
        assert public_copy in source


def test_client_cabinet_uses_human_readable_profile_catalog_history_and_subscription_copy() -> None:
    source = _frontend_main()

    for forbidden in (
        "ID города не угадывается",
        "Город (ID)",
        "например, beauty",
        "Например, beauty",
        "ID из админки",
    ):
        assert forbidden not in source

    for expected in (
        "Выберите город",
        "Город помогает подобрать предложения рядом.",
        "Все категории",
        "Категория",
        "По выбранному городу",
        "Все города",
        "Название, описание, адрес",
        "Пока нет подтверждений.",
        "Активная подписка пока не найдена",
        "Когда подписка будет оформлена",
        "Активно",
        "Подтверждено",
        "Истекло",
        "Отменено",
    ):
        assert expected in source

    assert "selected_city_id: selectedCityId ? Number(selectedCityId) : null" in source
    assert "renderStatusBadge(formatStatus(item.status))" in source
    assert "getPartnerCategories(partner)" in source


def test_frontend_contains_vk_password_setup_flow_markers() -> None:
    source = _frontend_main()

    assert "setup_token" in source
    assert "client_login" in source
    assert "getPasswordSetupParams" in source
    assert "applyClientLoginPrefill" in source
    assert "Задайте пароль" in source
    assert "Новый пароль" in source
    assert "Повторите пароль" in source
    assert "Пароль установлен. Теперь войдите" in source
    assert "login prefill" in source
    assert "client login mode" in source
    assert "/api/v1/auth/password-setup/complete" in source
    assert "Ссылка недействительна или истекла" in source


def test_frontend_preserves_public_and_cabinet_contract_markers_after_password_setup() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Федеральный клуб привилегий для девушек",
        "data-login-form",
        'data-login-mode="admin"',
        'data-login-mode="partner"',
        'data-login-mode="client"',
        "/api/v1/auth/login",
        "/api/v1/auth/user-login",
        "Панель администратора",
        "partner-dashboard",
        "client-dashboard",
    ):
        assert expected in source

    for removed_marker in (
        "reference-lotus-layer",
        "lotus-layer",
        "lotus-decor",
        "--user-lotus-reference-svg",
        "--lotus-reference-background",
    ):
        assert removed_marker not in source
        assert removed_marker not in styles


def test_public_landing_contains_smm_hero_menu_directions_and_partner_modal() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "hero-card",
        "для себя",
        "Красота, забота и вдохновение",
        "Скидки, подарки и специальные предложения у партнёров клуба.",
        "formatPartnerBenefit",
        "Специальное предложение",
        "landing-menu",
        "landing-menu-toggle",
        "landing-menu-panel",
        "О клубе",
        "Привилегии",
        "Партнёры",
        "Направления",
        "Как вступить",
        "Города",
        "landing-about",
        "landing-benefits",
        "landing-partners",
        "landing-directions",
        "landing-join",
        "landing-cities",
        "landing-direction-button",
        "direction-card",
        "data-landing-category-slug",
        "selectedLandingDirection",
        "landingPartnerModalState",
        "/api/v1/public/landing/partners",
        "landing-partner-modal",
        "landing-partner-panel",
        "landing-partner-card",
        "landing-partner-cover",
        "landing-partner-cover--placeholder",
        "landing-carousel-button",
        "Партнёры этого направления скоро появятся.",
        "Закрыть",
    ):
        assert expected in source or expected in styles

    for expected_style in (
        ".hero-card",
        ".pill",
        ".landing-menu-panel",
        ".landing-direction-button",
        ".landing-partner-modal",
        ".landing-partner-card",
        ".landing-carousel-button",
    ):
        assert expected_style in styles

    topbar_block = _css_block(styles, ".topbar")
    landing_menu_block = _css_block(styles, ".landing-menu")
    landing_menu_panel_block = _css_block(styles, ".landing-menu-panel")
    hero_card_block = _css_block(styles, ".hero-card")

    assert "z-index: 20;" in topbar_block
    assert "z-index: 30;" in landing_menu_block
    assert "Keep landing dropdown above hero/glass cards." in landing_menu_panel_block
    assert "position: absolute;" in landing_menu_panel_block
    assert "z-index: 40;" in landing_menu_panel_block
    assert "pointer-events: auto;" in landing_menu_panel_block
    assert "right: 0;" in landing_menu_panel_block
    assert "z-index:" not in hero_card_block

    assert "Красота, забота и привилегии рядом с вами" not in source
    assert "hero-visual" not in source
    assert "hero-visual-image" not in styles
    assert "1E+1" not in source
    assert "-1E+1%" not in source


def test_public_landing_uses_safe_public_partner_fetches_and_images() -> None:
    source = _frontend_main()
    styles = _frontend_styles()
    public_landing_match = re.search(r"const renderPublicApp = \(\) => \{(.*?)const authTokenKey", source, re.S)
    assert public_landing_match is not None
    public_landing_source = public_landing_match.group(1)

    assert "/api/v1/public/landing/partners" in source
    assert "/api/v1/admin/partners" not in public_landing_source
    assert "/api/v1/clients/catalog/partners" not in public_landing_source
    assert "Красота, забота и привилегии рядом с вами" not in source
    assert "hero-visual" not in source
    assert "hero-visual-image" not in styles
    assert 'url("/assets/hero-woman.jpg")' not in styles
    assert "startsWith('/assets/')" in source
    assert "startsWith('/uploads/')" in source


def test_frontend_contains_partner_logo_cover_upload_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Загрузить логотип",
        "Загрузить обложку",
        "Фотографии профиля",
        "Изображения партнёра",
        "/api/v1/admin/partners/${partnerId}/images?kind=${kind}",
        "/api/v1/partners/me/images?kind=${kind}",
        "partner-image-uploader",
        "partner-image-preview",
        "data-partner-upload-kind=\"logo\"",
        "data-partner-upload-kind=\"cover\"",
        "type=\"file\"",
        "accept=\"image/jpeg,image/png,image/webp\"",
        "FormData",
        "input.value = \"\"",
        "partner-upload-status",
        "Загружаем изображение",
        "Изображение загружено",
        "Не удалось загрузить изображение",
        "/uploads/",
    ):
        assert expected in source or expected in styles


def test_frontend_contains_partner_marketplace_profile_preview() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "renderPartnerMarketplaceCard",
        "partner-marketplace-card",
        "partner-marketplace-cover",
        "partner-marketplace-logo",
        "partner-marketplace-body",
        "partner-marketplace-meta",
        "partner-marketplace-offer",
        "partner-profile-layout",
        "partner-profile-main",
        "partner-profile-side",
        "partner-side-stack",
        "partner-section",
        "partner-section--compact",
        "partner-section-header",
        "partner-section-description",
        "partner-combined-section",
        "partner-progress-card",
        "Контакты и график",
        "partner-missing-list",
        "partner-save-bar",
        "partner-save-status",
        "partner-empty-state",
        "partner-profile-preview",
        "partner-profile-settings",
        "partner-profile-hints",
        "partner-onboarding",
        "partner-onboarding-progress",
        "partner-onboarding-step",
        "partner-onboarding-action",
        "Настройте витрину за 4 шага",
        "Готовность профиля",
        "Заполните главное для понятной витрины",
        "Основная информация",
        "Фото и обложка",
        "Предложения",
        "Публикация и проверка",
        "Витрина готова к публикации",
        "Нужно заполнить",
        "Профиль партнёра",
        "Главные данные для витрины",
        "Preview для клиента",
        "Название, город, категорию и статусы обновляет администратор",
        "График работы",
        "Витрина партнёра",
        "Заполненность профиля",
        "Профиль заполнен на",
        "Нет логотипа",
        "Нет обложки",
        "Нет описания",
        "Нет предложений",
        "Есть несохранённые изменения",
        "Сохранение…",
        "Сохранено",
        "Например: Bloom Beauty Studio",
        "Новосибирск, ул. Ленина, 15",
        "+7 999 123-45-67",
        "Уютная студия красоты в центре города",
        "Добавьте 3–5 фото",
        "Добавьте первое предложение — именно оно мотивирует клиентку прийти.",
        "Загрузить логотип",
        "Загрузить обложку",
        "/api/v1/partners/me/images",
        "/api/v1/admin/partners/",
        "/images?kind=",
        "working_hours",
        "logo_url",
        "cover_url",
        "sort_order",
    ):
        assert expected in source or expected in styles

    assert "startsWith('/uploads/')" in source
    assert "startsWith('/assets/')" in source

def test_frontend_contains_offer_marketplace_cards() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "renderOfferMarketplaceCard",
        "offer-marketplace-card",
        "offer-marketplace-image",
        "offer-marketplace-benefit",
        "offer-marketplace-preview",
        "offer-card-grid",
        "offer-card-placeholder",
        "Предложения и привилегии",
        "Короткая выгода и условия для клиенток",
        "Preview для клиента",
        "Добавьте первое предложение",
        "URL изображения",
        "Базовая цена",
        "Скидка, %",
        "Получить привилегию",
        "Карточка привилегии партнёра",
        "Фото услуги",
        "Специальное предложение",
        "/uploads/offer.webp",
        "/assets/offer.webp",
    ):
        assert expected in source or expected in styles

    assert "startsWith('/uploads/')" in source
    assert "startsWith('/assets/')" in source
    assert "image_url: getOptionalText(formData, 'image_url')" in source
    assert "partner-marketplace-card" in source or "partner-marketplace-card" in styles
    assert "Загрузить логотип" in source
    assert "Загрузить обложку" in source
    assert "/api/v1/public/landing/partners" in source
    assert "landing-partner-card" in source or "landing-partner-card" in styles
    assert "data-landing-partner-modal" in source
    assert "setup_token" in source
    assert "womenClubAdminAccessToken" in source
    assert "womenclub_partner_token" in source
    assert "womenclub_client_token" in source

    for removed_marker in (
        "reference-lotus-layer",
        "lotus-layer",
        "lotus-decor",
        "--user-lotus-reference-svg",
        "--lotus-reference-background",
        "/assets/lotus-bg.png",
    ):
        assert removed_marker not in source
        assert removed_marker not in styles


def test_frontend_contains_safe_offer_image_upload_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Фото предложения",
        "Загрузить фото предложения",
        "Сначала сохраните, затем загрузите фото.",
        "/api/v1/admin/offers/",
        "/image",
        "/api/v1/partners/me/offers/",
        "offer-image-uploader",
        "offer-image-preview",
        "offer-image-upload-actions",
        "offer-image-status",
        "admin-offers-layout",
        "admin-offers-toolbar",
        "admin-offers-preview-panel",
        "admin-offers-table-panel",
        "admin-offers-form-panel",
        "admin-table-actions",
        "admin-action-button",
        "admin-table-action",
        "/uploads/",
        "renderOfferMarketplaceCard",
        "offer-marketplace-card",
        "offer-marketplace-image",
        "Загрузить логотип",
        "Загрузить обложку",
        "partner-image-uploader",
        "partner-image-preview",
        "/api/v1/public/landing/partners",
        "data-landing-partner-modal",
        "landing-directions",
        "setup_token",
        "womenClubAdminAccessToken",
        "womenclub_partner_token",
        "womenclub_client_token",
        "dashboard-shell",
        "dashboard-topbar",
        "dashboard-sidebar",
        "dashboard-main",
    ):
        assert expected in source or expected in styles

    assert "startsWith('/uploads/')" in source
    assert "startsWith('/assets/')" in source

    for removed_marker in (
        "reference-lotus-layer",
        "lotus-layer",
        "lotus-decor",
        "--user-lotus-reference-svg",
        "--lotus-reference-background",
        "/assets/lotus-bg.png",
    ):
        assert removed_marker not in source
        assert removed_marker not in styles


def test_frontend_contains_partner_gallery_photo_mvp_markers() -> None:
    source = FRONTEND_MAIN.read_text(encoding="utf-8")
    styles = FRONTEND_STYLES.read_text(encoding="utf-8")

    required_source_markers = [
        "Галерея партнёра",
        "Загрузить фото в галерею",
        "data-partner-gallery-upload",
        "Фото для клиентской витрины.",
        "Публикация после проверки.",
        "Фото загружено и отправлено на проверку.",
        "На проверке",
        "Ожидает активации.",
        "Скрыть фото",
        "partner-gallery",
        "partner-gallery-grid",
        "/api/v1/admin/partners/",
        "/photos",
        "/api/v1/partners/me/photos",
        "landing-partner-gallery",
        "/api/v1/partners/me/images?kind=${kind}",
        "/api/v1/admin/partners/${partnerId}/images?kind=${kind}",
        "/api/v1/partners/me/offers/${offerId}/image",
        "data-partner-offer-image-upload",
        "Сначала сохраните предложение",
        "/api/v1/admin/offers/${offerId}/image",
        "partner-marketplace-card",
        "offer-marketplace-card",
        "setup_token",
        "/api/v1/public/landing/partners",
        "startsWith('/uploads/')",
    ]
    for marker in required_source_markers:
        assert marker in source

    for marker in [
        ".partner-gallery",
        ".partner-gallery-grid",
        ".partner-gallery-item",
        ".partner-gallery-image",
        ".partner-gallery-actions",
        ".partner-gallery-upload",
        ".partner-gallery-empty",
        ".partner-gallery-status",
        ".partner-empty-state",
    ]:
        assert marker in styles

    forbidden_reference_markers = ["lotus", "Лотос", "remote image fetch"]
    for marker in forbidden_reference_markers:
        assert marker not in source


def test_frontend_contains_partner_content_moderation_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Публикация после проверки администратором.",
        "Предложение отправлено на проверку. После активации администратором оно появится у клиентов.",
        "Публикация после проверки.",
        "Фото загружено и отправлено на проверку.",
        "Ожидает активации.",
        "На проверке",
        "partner-gallery-status",
        "renderPartnerReviewStatusBadge",
        "Фото для клиентской витрины.",
        "partner-marketplace-card",
        "offer-marketplace-card",
        "/api/v1/partners/me/photos",
        "/api/v1/partners/me/offers",
        "/api/v1/partners/me/activity",
        "/api/v1/partners/me/analytics",
        "setup_token",
        "dashboard-shell",
        "womenclub_partner_token",
        "womenclub_client_token",
        "/api/v1/public/landing/partners",
    ):
        assert expected in source or expected in styles

    for removed_marker in (
        "reference-lotus-layer",
        "lotus-layer",
        "lotus-decor",
        "--user-lotus-reference-svg",
        "--lotus-reference-background",
        "/assets/lotus-bg.png",
    ):
        assert removed_marker not in source
        assert removed_marker not in styles


def test_frontend_contains_client_marketplace_partner_catalog_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "client-marketplace-grid",
        "client-partner-card",
        "client-partner-cover",
        "client-partner-logo",
        "client-partner-gallery",
        "client-partner-detail",
        "client-partner-offers",
        "client-partner-empty",
        "Партнёры пока не найдены",
        "Попробуйте выбрать другой город или категорию",
        "Предложения скоро появятся",
        "Открыть",
        "Получить привилегию",
        "Проверенный партнёр",
        "renderOfferMarketplaceCard",
        "offer-marketplace-card",
        "getActivePartnerGalleryPhotos(partner.photos)",
        "isSafePublicAssetUrl(partner.cover_url)",
        "isSafePublicAssetUrl(partner.logo_url)",
        "openClientPartnerMarketplace",
        "/api/v1/clients/partners/${partnerId}",
        "/api/v1/clients/partners/${partnerId}/offers",
        "partner-gallery",
        "partner-gallery-grid",
        "Загрузить фото в галерею",
        "setup_token",
        "womenClubAdminAccessToken",
        "womenclub_partner_token",
        "womenclub_client_token",
        "dashboard-shell",
        "dashboard-topbar",
        "dashboard-sidebar",
        "dashboard-main",
        "/api/v1/public/landing/partners",
        "data-landing-partner-modal",
        "renderClientPartnerModal",
        "renderClientPartnerModalGallery",
        "getPartnerGalleryImages",
        "selectedPartnerModalId",
        "selectedPartnerModalPartner",
        "selectedPartnerModalOffers",
        "partnerModalGalleryIndex",
        "data-client-partner-open",
        "data-partner-id",
        "data-client-partner-modal-close",
        "data-gallery-action",
        'role="dialog"',
        'aria-modal="true"',
        "client-partner-modal",
        "client-partner-modal__overlay",
        "client-partner-modal__panel",
        "client-partner-modal__gallery",
        "client-partner-modal__thumbs",
        "client-partner-modal__offers",
        "client-partner-card",
        "object-fit: contain",
        "object-fit: cover",
    ):
        assert expected in source or expected in styles

    assert "startsWith('/uploads/')" in source
    assert "startsWith('/assets/')" in source

    for removed_marker in (
        "reference-lotus-layer",
        "lotus-layer",
        "lotus-decor",
        "--user-lotus-reference-svg",
        "--lotus-reference-background",
        "/assets/lotus-bg.png",
    ):
        assert removed_marker not in source
        assert removed_marker not in styles



def test_frontend_contains_client_onboarding_checklist_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Как пользоваться клубом",
        "Пройдено",
        "Выберите город",
        "Откройте каталог",
        "Получите привилегию",
        "Покажите код партнёру",
        "Партнёр → код → визит",
        "Вы уже умеете пользоваться клубом",
        "client-onboarding",
        "client-onboarding-progress",
        "client-onboarding-step",
        "client-onboarding-action",
    ):
        assert expected in source or expected in styles


def test_frontend_contains_client_home_overview_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Мой клуб привилегий",
        "Смотреть партнёров",
        "Получить код у партнёра",
        "Мои коды",
        "Изменить город",
        "Ежемесячный розыгрыш",
        "VK привязан",
        "VK не привязан",
        "У вас есть активная привилегия",
        "Активных привилегий пока нет",
        "Выберите предложение в каталоге",
        "client-home",
        "client-home-hero",
        "client-home-stats",
        "client-quick-actions",
        "client-quick-action",
        "client-active-privilege",
        "client-active-code",
        "client-profile-home-only",
        "client-tab-header",
        "client-tab-title",
        "client-tab-description",
        "Каталог партнёров",
        "Выберите категорию, город или найдите партнёра",
        "Статус клубного доступа и срок действия",
        "Активные и использованные коды",
        "Ваши действия и изменения статусов",
    ):
        assert expected in source or expected in styles


def test_frontend_contains_privilege_marketplace_flow_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Привилегия активирована",
        "Покажите этот код партнёру перед оплатой/получением услуги.",
        "Мои привилегии",
        "Для получения привилегии нужна активная подписка.",
        "Предложение сейчас недоступно.",
        "Подтвердить привилегию",
        "data-privilege-success-panel",
        "data-client-privilege-card",
        "data-partner-confirmation-card",
        "privilege-success-panel",
        "client-privilege-card",
        "partner-confirmation-card",
        "/api/v1/clients/partners/${partnerId}/verify",
        "/api/v1/clients/me/verifications",
        "/api/v1/partners/me/verifications/${verificationId}/confirm",
        "renderOfferMarketplaceCard",
        "offer-marketplace-card",
        "partner-gallery",
        "setup_token",
        "/api/v1/public/landing/partners",
        "womenclub_client_token",
        "womenclub_partner_token",
    ):
        assert expected in source or expected in styles

    for expected_status in ("Активно", "Подтверждено", "Истекло", "Отменено"):
        assert expected_status in source

    assert "startsWith('/uploads/')" in source
    assert "startsWith('/assets/')" in source

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


def test_frontend_contains_partner_analytics_ui_markers() -> None:
    source = _frontend_main()
    styles = _frontend_styles()

    for expected in (
        "Аналитика",
        "Аналитика партнёра",
        "Переходы по QR",
        "Получено привилегий",
        "Подтверждено",
        "Активные привилегии",
        "Истекшие привилегии",
        "Конверсия в привилегию",
        "Процент подтверждения",
        "Данных пока нет",
        "Аналитика помогает понять",
        "/api/v1/partners/me/analytics",
        "/api/v1/admin/partners/",
        "/analytics",
        "renderAnalyticsCards",
        "partnerAnalyticsById",
        "selectedPartnerAnalytics",
        "analyticsLoading",
        "analyticsError",
    ):
        assert expected in source

    for expected_style in (
        "analytics-grid",
        "analytics-card",
        "analytics-value",
        "analytics-label",
        "analytics-hint",
        "analytics-empty",
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
        "setup_token",
        "/api/v1/public/landing/partners",
        "womenclub_partner_token",
        "womenclub_client_token",
        "dashboard-shell",
        "dashboard-topbar",
        "dashboard-sidebar",
        "dashboard-main",
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

def test_admin_partner_wizard_markers_present() -> None:
    source = _frontend_main()

    for marker in (
        "partnerFormStep",
        "basic",
        "status",
        "contacts",
        "description",
        "media",
                "Основное",
        "Категории",
        "Контакты",
        "Описание",
        "Медиа",
                        "Назад",
        "Сохранить",
                        "adminState.partnerFormOpen",
        "category_ids",
        "Партнёр может отображаться сразу в нескольких категориях.",
                "type=\"button\"",
        "data-admin-partner-wizard-form",
        "data-admin-partner-save-button",
        "partnerWizardFormId",
    ):
        assert marker in source


def test_admin_partner_wizard_uses_single_save_action_markers() -> None:
    source = _frontend_main()

    for marker in (
        'data-admin-partner-save-button',
        'form="${escapeHtml(partnerWizardFormId)}"',
        'data-admin-partner-step-jump',
        'adminState.partnerFormOpen = true;',
    ):
        assert marker in source

    assert 'data-admin-partner-step-next' not in source



def test_admin_partner_wizard_save_button_targets_edit_form_and_is_not_disabled() -> None:
    source = _frontend_main()
    form_block = source.split('const renderPartnerForm = () => {', 1)[1].split('const defaultPartnerFilters = () => ({', 1)[0]

    assert 'id="${escapeHtml(partnerWizardFormId)}"' in form_block
    assert 'data-admin-partner-wizard-form novalidate' in form_block
    assert 'type="submit" form="${escapeHtml(partnerWizardFormId)}" data-admin-partner-save-button' in form_block
    save_button_line = 'type="submit" form="${escapeHtml(partnerWizardFormId)}" data-admin-partner-save-button>Сохранить</button>'
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

def test_admin_partner_wizard_reset_and_category_review_normalization_markers() -> None:
    source = _frontend_main()

    for marker in (
        "adminState.partnerFormStep = 'basic';",
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


def test_admin_partner_category_uncheck_state_survives_wizard_rerender() -> None:
    source = _frontend_main()

    for marker in (
        "partnerFormCategoryIds",
        "captureAdminPartnerCategoryDraft",
        "getAdminPartnerSelectedCategoryIds",
        "input[name=\"category_ids\"]:checked",
        "[data-admin-partner-wizard-form] input[name=\"category_ids\"]",
        "captureAdminPartnerCategoryDraft(partnerStepJump.closest('[data-admin-partner-wizard-form]'))",
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
        'Для участниц клуба',
        'Выгода',
        'renderOfferPricingBlock(offer)',
        'offer_id',
        'saving_amount',
        'discount_percent',
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
    ):
        assert css_marker in styles


def test_landing_partner_filter_uses_categories_array_and_keeps_direction_markers() -> None:
    source = _frontend_main()

    for marker in (
        "selectedLandingDirection",
        "landingPartnerModalState",
        "data-landing-category-slug",
        "direction-card",
        "landing-direction-button",
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
    assert "cache: options.cache || 'no-store'" in source


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
