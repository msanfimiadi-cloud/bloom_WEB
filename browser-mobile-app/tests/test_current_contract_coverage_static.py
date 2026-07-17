from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
APP = (ROOT / "src/App.tsx").read_text(encoding="utf-8")
SERVER = (ROOT / "server/production-server.js").read_text(encoding="utf-8")
CATALOG = (ROOT / "src/pages/CatalogPage.tsx").read_text(encoding="utf-8")
PARTNER = (ROOT / "src/pages/PartnerPage.tsx").read_text(encoding="utf-8")
PROFILE = (ROOT / "src/pages/ProfilePage.tsx").read_text(encoding="utf-8")


def test_guest_mode_contract_remains_covered() -> None:
    assert "GUEST_MODE_STORAGE_KEY" in APP
    assert "writeBrowserGuestMode(true)" in APP
    assert "Продолжить без регистрации" in APP


def test_welcome_loop_prevention_contract_remains_covered() -> None:
    assert "setBrowserLoginRequired(!browserGuestMode)" in APP
    assert "guest_mode_selected" in APP
    assert "setIsBootstrapDone(true)" in APP


def test_protected_action_login_modal_contract_remains_covered() -> None:
    assert "requireRegisteredUser" in APP
    assert "Требуется регистрация" in APP
    assert "setIsLoginCodeFormOpen(true)" in APP


def test_catalog_screen_contract_remains_covered() -> None:
    assert "catalog-search" in CATALOG
    assert "filterPartnersByCategory" in CATALOG
    assert "catalog-empty-state" in CATALOG


def test_partner_card_and_offers_contract_remains_covered() -> None:
    assert "partner-detail__hero" in PARTNER
    assert "offer-card" in PARTNER
    assert "onVerifyOffer" in PARTNER


def test_legal_documents_contract_remains_covered() -> None:
    for name in ["Политика%20Конфиденциальности.docx", "Пользовательское%20соглашение.docx", "Согласие%20на%20обработку%20персональных%20данных.docx"]:
        assert name in APP or name in PROFILE
    assert "serveDocument" in SERVER
    assert ".docx" in SERVER


def test_client_api_proxy_contract_remains_covered() -> None:
    assert "CLIENT_API_PROXY_ROUTES" in SERVER
    assert "clients\\/catalog\\/partners" in SERVER
    assert "clients\\/partners" in SERVER
    assert "X-Correlation-ID" in SERVER


def test_unknown_api_json_404_contract_remains_covered() -> None:
    assert "pathname.startsWith('/api/')" in SERVER
    assert "sendJson(response, 404, { detail: 'not_found' })" in SERVER


def test_versioned_spa_paths_contract_remains_covered() -> None:
    assert "isVersionedFrontendRoute" in SERVER
    assert "pathname.startsWith('/app-v')" in SERVER
    assert "serveFrontend" in SERVER


def test_admin_bot_scope_is_documented() -> None:
    doc = (REPO_ROOT / "docs/admin-bot-and-vk-mini-app-scope.md").read_text(encoding="utf-8")
    assert "Browser Mobile App does not embed" in doc
    assert "admin_bot/admin_bot/__main__.py" in doc


def test_vk_mini_app_scope_is_documented_separately() -> None:
    doc = (REPO_ROOT / "docs/admin-bot-and-vk-mini-app-scope.md").read_text(encoding="utf-8")
    hosting = (REPO_ROOT / "docs/VK_MINI_APP_HOSTING.md").read_text(encoding="utf-8")
    assert "VK Mini App hosting" in doc
    assert "app/static/vk-mini-app/index.html" in doc
    assert "app/static/vk-mini-app/index.html" in hosting


def test_playwright_e2e_scenarios_are_listed_for_ci() -> None:
    doc = (REPO_ROOT / "docs/deploy_checklist.md").read_text(encoding="utf-8")
    for marker in ["guest", "catalog", "partner", "docs", "protected"]:
        assert marker in doc.lower()


def test_runtime_config_build_id_contract_remains_covered() -> None:
    assert "SERVER_BUILD_ID" in SERVER
    assert "buildId" in SERVER
    assert "/api/runtime-config" in SERVER
