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
    preserve_start = APP.index('const preservePendingBrowserLoginFlow = useCallback')
    preserve_end = APP.index('const updateLoginCodeDraft')
    for marker in [i for i in range(len(APP)) if APP.startswith('setAuthRestoreStatus("unauthenticated")', i)]:
        assert (preserve_start < marker < preserve_end) or marker > invalid_token_clear or marker > no_token_else
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


def test_manual_logout_blocks_lifecycle_bootstrap_and_renders_auth_screen() -> None:
    assert 'const manualLogoutInProgressRef = useRef(false);' in APP
    assert 'const logoutGenerationRef = useRef(0);' in APP
    logout_section = APP[APP.index('const logout = useCallback(() => {'):APP.index('const submitLoginCode', APP.index('const logout = useCallback(() => {'))]
    assert 'manualLogoutInProgressRef.current = true;' in logout_section
    assert 'logoutGenerationRef.current += 1;' in logout_section
    assert 'setAuthRestoreStatus("unauthenticated");' in logout_section
    assert 'setIsLoading(false);' in logout_section
    assert 'setIsBootstrapDone(true);' in logout_section
    assert 'setBrowserLoginRequired(true);' in logout_section
    assert 'setData(emptyData);' in logout_section
    assert 'loadAppData(' not in logout_section

    load_app_data_guard = APP[APP.index('traceStartupRecovery("loadAppData:enter"'):APP.index('if (forceNew) {')]
    assert 'manualLogoutInProgressRef.current' in load_app_data_guard
    assert 'manual_logout_bootstrap_blocked' in load_app_data_guard
    assert 'setIsLoading(true);' not in load_app_data_guard

    pageshow_section = APP[APP.index('const onPageShow = (event: PageTransitionEvent) => {'):APP.index('const onPageHide', APP.index('const onPageShow = (event: PageTransitionEvent) => {'))]
    assert 'interruptedStartup && !manualLogoutInProgressRef.current' in pageshow_section

    home_catalog_effect = APP[APP.rfind('useEffect(() => {', 0, APP.index('home bootstrap:loadPartners')):APP.index('const openCatalog = useCallback')]
    assert 'manualLogoutInProgressRef.current' in home_catalog_effect
    assert 'browserLoginRequired' in home_catalog_effect
    assert 'authRestoreStatus !== "authenticated"' in home_catalog_effect

    render_section = APP[APP.index('const canRenderLogin ='):APP.index('if (error) {')]
    assert 'const canRenderLogin = browserLoginRequired && authRestoreStatus === "unauthenticated" && !isLoading && !bootstrapPromiseRef.current;' in render_section
    assert 'if (canRenderLogin)' in render_section
    assert 'welcome-auth-screen' in render_section
    assert render_section.index('if (canRenderLogin)') < render_section.index('if (isLoading)')


def test_profile_logout_button_uses_app_logout_callback_with_trace() -> None:
    profile = (ROOT / "src" / "pages" / "ProfilePage.tsx").read_text(encoding="utf-8")
    button_section = profile[profile.index('profile-logout-button'):profile.index('Выйти из профиля')]
    assert '[BLOOM_LOGOUT_TRACE] logout_button_clicked' in button_section
    assert 'onLogout();' in button_section


def test_pending_browser_login_draft_resume_does_not_bootstrap_or_show_loader() -> None:
    assert 'const pendingBrowserLoginRef = useRef(false);' in APP
    assert 'function hasStoredBrowserLoginDraft(): boolean' in APP
    assert 'const hasPendingBrowserLoginDraft = useCallback' in APP
    assert 'const preservePendingBrowserLoginFlow = useCallback' in APP

    preserve_section = APP[APP.index('const preservePendingBrowserLoginFlow = useCallback'):APP.index('const updateLoginCodeDraft')]
    assert 'pendingBrowserLoginRef.current = true;' in preserve_section
    assert 'restoreLoginCodeDrafts();' in preserve_section
    assert 'setIsLoading(false);' in preserve_section
    assert 'setAuthRestoreStatus("unauthenticated");' in preserve_section
    assert 'setBrowserLoginRequired(true);' in preserve_section
    assert 'setBrowserLoginExternalOpenRequired(false);' in preserve_section
    assert 'loadAppData(' not in preserve_section

    load_app_data_guard = APP[APP.index('traceStartupRecovery("loadAppData:enter"'):APP.index('if (forceNew) {')]
    assert 'reason === "resume" && preservePendingBrowserLoginFlow("loadAppData:resume")' in load_app_data_guard
    assert 'pending_browser_login_bootstrap_blocked' in load_app_data_guard
    assert 'setIsLoading(true);' not in load_app_data_guard
    assert 'setAuthRestoreStatus("restoring")' not in load_app_data_guard

    pageshow_section = APP[APP.index('const onPageShow = (event: PageTransitionEvent) => {'):APP.index('const onPageHide', APP.index('const onPageShow = (event: PageTransitionEvent) => {'))]
    assert 'interruptedStartup && !manualLogoutInProgressRef.current && !hasPendingBrowserLoginDraft()' in pageshow_section
    assert 'void loadAppData("resume", false);' in pageshow_section

    mark_inactive_section = APP[APP.index('const markInactive = (event: Event) => {'):APP.index('const onPageShow = (event: PageTransitionEvent) => {')]
    assert '!hasPendingBrowserLoginDraft() &&' in mark_inactive_section
    assert 'markStartupInterrupted(event.type);' in mark_inactive_section


def test_pending_browser_login_guard_clears_after_successful_code_login() -> None:
    submit_section = APP[APP.index('const submitLoginCode = useCallback(async () => {'):APP.index('const reloadSuccessfulBootstrapRecovery')]
    assert 'pendingBrowserLoginRef.current = false;' in submit_section
    assert 'setBrowserLoginRequired(false);' in submit_section
    assert 'clearLoginCodeDrafts();' in submit_section
    assert 'await loadAppData("manual", false);' in submit_section

    pageshow_section = APP[APP.index('const onPageShow = (event: PageTransitionEvent) => {'):APP.index('const onPageHide', APP.index('const onPageShow = (event: PageTransitionEvent) => {'))]
    assert 'void loadAppData("resume", false);' in pageshow_section
    assert 'hasPendingBrowserLoginDraft()' in pageshow_section
