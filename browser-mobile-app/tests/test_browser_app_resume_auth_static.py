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
    assert 'if (storedAuthToken && !forceNewIdentity)' in startup_section
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


def test_pageshow_interrupted_startup_resume_preserves_stored_token_auth() -> None:
    pageshow_section = APP[APP.index('const onPageShow = (event: PageTransitionEvent) => {'):APP.index('const onPageHide', APP.index('const onPageShow = (event: PageTransitionEvent) => {'))]
    assert 'detectInterruptedStartup()' in pageshow_section
    assert 'void loadAppData("resume", false);' in pageshow_section
    assert 'void loadAppData("resume", true);' not in pageshow_section
    startup_section = APP[APP.index('const storedAuthToken = getStoredAuthToken();'):APP.index('traceMark("auth_finished"')]
    assert 'const forceNewIdentity = typeof options === "boolean" ? false : Boolean(options.forceNewIdentity);' in APP
    assert 'if (storedAuthToken && !forceNewIdentity)' in startup_section
    assert startup_section.index('if (storedAuthToken && !forceNewIdentity)') < startup_section.index('if (!(await loginWithTelegramPayload()))')


def test_force_refresh_with_stored_token_does_not_mark_unauthenticated() -> None:
    startup_section = APP[APP.index('const forceRefresh ='):APP.index('traceMark("auth_finished"')]
    stored_token_branch = startup_section[startup_section.index('if (storedAuthToken && !forceNewIdentity)'):startup_section.index('} else {', startup_section.index('if (storedAuthToken && !forceNewIdentity)'))]
    assert 'await requestProfileAndSubscription()' in stored_token_branch
    before_invalid_auth_clear = stored_token_branch.split('clearStoredAuthToken();')[0]
    assert 'setAuthRestoreStatus("unauthenticated")' not in before_invalid_auth_clear
    assert 'setBrowserLoginRequired(true);' not in before_invalid_auth_clear


def test_browser_pwa_without_telegram_payload_keeps_valid_stored_token_restoring_or_authenticated() -> None:
    startup_section = APP[APP.index('const storedAuthToken = getStoredAuthToken();'):APP.index('traceMark("auth_finished"')]
    stored_token_branch = startup_section[startup_section.index('if (storedAuthToken && !forceNewIdentity)'):startup_section.index('} else {', startup_section.index('if (storedAuthToken && !forceNewIdentity)'))]
    assert 'await loginWithTelegramPayload()' not in stored_token_branch.split('} catch (caughtError)')[0]
    assert 'setAuthRestoreStatus("authenticated")' in APP
    no_token_branch = startup_section[startup_section.index('} else {', startup_section.index('if (storedAuthToken && !forceNewIdentity)')):]
    assert 'setAuthRestoreStatus("unauthenticated")' in no_token_branch


def test_unauthenticated_requires_no_stored_token_or_confirmed_auth_clear() -> None:
    invalid_token_clear = APP.index('clearStoredAuthToken();')
    no_token_else = APP.index('} else {', APP.index('if (storedAuthToken && !forceNewIdentity)'))
    for marker in [i for i in range(len(APP)) if APP.startswith('setAuthRestoreStatus("unauthenticated")', i)]:
        assert marker > invalid_token_clear or marker > no_token_else
    assert 'authClearedReason: "auth_check_401_403"' in APP


def test_unexpected_login_screen_with_token_not_reachable_from_resume_stored_token_branch() -> None:
    assert 'unexpected_login_screen_with_token' in APP
    pageshow_section = APP[APP.index('const onPageShow = (event: PageTransitionEvent) => {'):APP.index('const onPageHide', APP.index('const onPageShow = (event: PageTransitionEvent) => {'))]
    assert 'loadAppData("resume", false)' in pageshow_section
    assert 'loadAppData("resume", true)' not in pageshow_section
    login_guard_section = APP[APP.index('if (browserLoginRequired && !canRenderLogin)'):APP.index('if (canRenderLogin)')]
    assert 'Проверяем вход...' in login_guard_section


def test_manual_logout_finishes_auth_locally_without_bootstrap_or_draft_clear() -> None:
    logout_section = APP[APP.index('const logout = useCallback(() => {'):APP.index('const submitLoginCode', APP.index('const logout = useCallback(() => {'))]
    assert 'clearStoredAuthToken();' in logout_section
    assert 'authSnapshotRef.current = getAuthTokenStorageSnapshot();' in logout_section
    assert 'resetTelegramLoginInFlight();' in logout_section
    assert 'setAuthRestoreStatus("unauthenticated");' in logout_section
    assert 'setLastAuthDecisionReason("manual_logout_local_clear");' in logout_section
    assert 'setIsLoading(false);' in logout_section
    assert 'setIsBootstrapDone(true);' in logout_section
    assert 'setBrowserLoginRequired(true);' in logout_section
    assert 'bootstrapPromiseRef.current = null;' in logout_section
    assert 'loadAppData(' not in logout_section
    assert 'clearLoginCodeDrafts();' not in logout_section
    assert 'setLoginCode("");' not in logout_section
    assert 'setLoginReferralCode("");' not in logout_section
