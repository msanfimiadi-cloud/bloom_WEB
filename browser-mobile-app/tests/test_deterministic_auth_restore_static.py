from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "src" / "App.tsx").read_text(encoding="utf-8")
CLIENT = (ROOT / "src" / "api" / "client.ts").read_text(encoding="utf-8")
LIFECYCLE = (ROOT / "src" / "diagnostics" / "startupLifecycle.ts").read_text(encoding="utf-8")


def test_auth_restore_status_starts_unknown_and_gates_login() -> None:
    assert 'type AuthRestoreStatus = "unknown" | "restoring" | "authenticated" | "unauthenticated" | "invalid"' in APP
    assert 'useState<AuthRestoreStatus>("unknown")' in APP
    assert 'const canRenderLogin = browserLoginRequired && authRestoreStatus === "unauthenticated"' in APP
    assert 'if (browserLoginRequired && !canRenderLogin)' in APP


def test_token_present_or_pending_profile_shows_restore_loading_not_login() -> None:
    assert 'setAuthRestoreStatus("restoring")' in APP
    assert 'const storedAuthToken = authSnapshot.token;' in APP
    assert 'await requestProfileAndSubscription()' in APP
    assert 'Проверяем вход...' in APP


def test_network_timeout_and_abort_are_neutral_not_unauthenticated() -> None:
    non_auth_section = APP[APP.index('if (!isAuthInvalidStatus(caughtError))'):APP.index('lifecycleTrace("stored_token_auth_fail"')]
    assert 'throw caughtError;' in non_auth_section
    assert 'setAuthRestoreStatus("unauthenticated")' not in non_auth_section
    assert 'setLastAuthDecisionReason("bootstrap_aborted_neutral")' in APP
    assert 'lastBootstrapAbortReasonRef.current = eventName' in APP


def test_interrupted_startup_cleanup_preserves_auth_keys() -> None:
    assert 'protectedAuthKeyPattern' in LIFECYCLE
    assert 'auth|token|telegram_login|session|jwt|initdata' in LIFECYCLE
    assert 'temporaryStartupKeyPattern.test(key) && !protectedAuthKeyPattern.test(key)' in LIFECYCLE


def test_unexpected_login_screen_with_token_diagnostic() -> None:
    assert 'unexpected_login_screen_with_token' in APP
    for field in [
        'authRestoreStatus', 'hasStoredToken', 'tokenSource', 'lastAuthDecisionReason',
        'startupInterrupted', 'startupCompleted', 'cleanupRan', 'cleanupRemovedKeysCount',
        'lastPagehideAt', 'lastPageshowAt', 'lastBootstrapAbortReason', 'currentRouteHash',
        'appMounted', 'firstVisiblePaint',
    ]:
        assert field in APP


def test_next_launch_reads_stable_storage_snapshot_not_stale_bootstrap() -> None:
    assert 'getAuthTokenStorageSnapshot' in CLIENT
    assert 'tokenSource: "local"' in CLIENT
    assert 'sessionToken ? "session"' in CLIENT
    assert 'if (detectInterruptedStartup()) { void loadAppData("resume", true); }' in APP
    assert 'bootstrapPromiseRef.current = null;' in APP
