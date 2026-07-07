from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "src" / "App.tsx").read_text(encoding="utf-8")
CLIENT = (ROOT / "src" / "api" / "client.ts").read_text(encoding="utf-8")


def test_after_login_code_success_jwt_is_stored_in_local_storage() -> None:
    assert 'export const AUTH_STORAGE_KEY = "bloom_club_tma_auth"' in CLIENT
    assert 'window.localStorage.setItem(AUTH_STORAGE_KEY, token);' in CLIENT
    assert 'storeAuthTokenFromResponse(loginResponse)' in APP


def test_resume_lifecycle_events_do_not_clear_jwt() -> None:
    resume_section = APP[APP.index('const resumeWithoutAuthReset'):APP.index('const markInactive')]
    forbidden = ['clearStoredAuthToken', 'localStorage.removeItem(AUTH_STORAGE_KEY)', 'sessionStorage.removeItem(AUTH_SESSION_STORAGE_KEY)', 'loadAppData("resume"', 'location.reload', 'location.replace']
    for marker in forbidden:
        assert marker not in resume_section
    assert 'authCheckStatus: "not_run_on_resume"' in resume_section


def test_app_startup_with_stored_jwt_loads_authenticated_app_before_login_code() -> None:
    startup_section = APP[APP.index('const storedAuthToken = getStoredAuthToken();'):APP.index('traceMark("auth_finished"')]
    assert 'if (storedAuthToken && !forceNew)' in startup_section
    assert 'await requestProfileAndSubscription()' in startup_section
    assert startup_section.index('await requestProfileAndSubscription()') < startup_section.index('setBrowserLoginRequired(true);')


def test_missing_telegram_init_data_on_resume_does_not_clear_jwt() -> None:
    resume_section = APP[APP.index('const resumeWithoutAuthReset'):APP.index('const markInactive')]
    assert 'getTelegramLaunchPayloadWithRetry' not in resume_section
    assert 'loginWithTelegramPayload' not in resume_section
    assert 'clearStoredAuthToken' not in resume_section


def test_catalog_and_network_errors_do_not_clear_jwt() -> None:
    auth_error_section = APP[APP.index('if (!isAuthInvalidStatus(caughtError))'):APP.index('lifecycleTrace("stored_token_auth_fail"')]
    assert 'throw caughtError;' in auth_error_section
    assert 'clearStoredAuthToken' not in auth_error_section


def test_only_401_403_auth_response_clears_jwt() -> None:
    assert 'return isApiError(error) && (error.status === 401 || error.status === 403);' in APP
    clear_section = APP[APP.index('traceResumeAuthDiagnostic("stored_token_auth_cleared"'):APP.index('// Stale JWT still attempts Telegram Mini App auth')]
    assert 'authClearedReason: "auth_check_401_403"' in clear_section
    assert 'clearStoredAuthToken();' in clear_section


def test_no_resume_handler_calls_location_reload_or_replace() -> None:
    lifecycle_section = APP[APP.index('const resumeWithoutAuthReset'):APP.index('window.addEventListener("pageshow", onPageShow)')]
    assert 'location.reload' not in lifecycle_section
    assert 'location.replace' not in lifecycle_section
    assert 'didForceReload: false' in lifecycle_section
