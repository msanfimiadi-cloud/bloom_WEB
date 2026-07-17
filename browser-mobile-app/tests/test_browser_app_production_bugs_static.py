from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "src" / "App.tsx").read_text(encoding="utf-8")
CLIENT = (ROOT / "src" / "api" / "client.ts").read_text(encoding="utf-8")
ERROR_REPORTER = (ROOT / "src" / "diagnostics" / "clientErrorReporter.ts").read_text(encoding="utf-8")


def test_successful_login_code_auth_restores_state_without_full_page_reload() -> None:
    login_section = APP[APP.index("const submitLoginCode"):APP.index("const reloadSuccessfulBootstrapRecovery")]
    assert "storeAuthTokenFromResponse(loginResponse)" in login_section
    assert "await loadAppData(\"manual\", false);" in login_section
    for marker in ["location.reload", "location.replace", "location.href", "location.assign"]:
        assert marker not in login_section


def test_runtime_build_mismatch_diagnostic_never_replaces_browser_app_location() -> None:
    mismatch_section = ERROR_REPORTER[ERROR_REPORTER.index("export async function reloadWhenServerBuildDiffers"):]
    assert "frontend_build_mismatch_detected" in mismatch_section
    assert 'action: "no_reload"' in mismatch_section
    assert "window.location.replace" not in mismatch_section
    assert "window.location.reload" not in mismatch_section


def test_stored_invalid_and_guest_jwt_paths_are_explicit() -> None:
    startup_section = APP[APP.index("const storedAuthToken = authSnapshot.token;"):APP.index('traceMark("auth_finished"')]
    assert "await requestProfileAndSubscription()" in startup_section
    assert "clearStoredAuthToken();" in startup_section
    assert "setBrowserLoginRequired(!browserGuestMode);" in startup_section
    assert "setIsBootstrapDone(true);" in startup_section


def test_browser_app_uses_same_origin_api_proxy_for_web_catalog_on_app_domain() -> None:
    assert 'DEFAULT_API_BASE_URL = "/api/v1"' in CLIENT
    assert 'LEGACY_WEB_API_BASE_URL = "https://bloomclub.ru/api/v1"' in CLIENT
    assert 'window.location.hostname === "app.bloomclub.ru"' in CLIENT
    assert 'WEB_CATALOG_PARTNERS_PATH = "/clients/catalog/partners"' in CLIENT
    catalog_section = CLIENT[CLIENT.index("async function getPartnersAttempt"):CLIENT.index("export async function getPartners")]
    assert 'const apiBase = TG_LOCAL_CATALOG_ENABLED ? "tg" : "web";' in catalog_section


def test_catalog_failure_does_not_trigger_browser_app_reload() -> None:
    catalog_section = APP[APP.index("const loadPartners"):APP.index("const loadPartnerOffers")]
    for marker in ["location.reload", "location.replace", "location.href", "location.assign", "restartAppAfterStartupFailure"]:
        assert marker not in catalog_section
