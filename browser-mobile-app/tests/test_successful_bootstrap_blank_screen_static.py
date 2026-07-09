from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "src/App.tsx").read_text(encoding="utf-8")
CONTENT = (ROOT / "src/content/ContentContext.tsx").read_text(encoding="utf-8")
BOUNDARY = (ROOT / "src/components/RuntimeErrorBoundary.tsx").read_text(encoding="utf-8")


def test_successful_bootstrap_blank_screen_diagnostic_payload_present():
    assert '"blank_screen_after_successful_bootstrap"' in APP
    for field in [
        "authRestoreStatus",
        "isBootstrapDone",
        "isLoading",
        "browserLoginRequired",
        "currentPage",
        "currentTab",
        "selectedPartnerId",
        "partnersCount",
        "staticTextsLoaded",
        "contentBlocksLoaded",
        "rootChildCount",
        "appContainerTextLength",
        "visibleElementCount",
        "lastLifecycleEvent",
        "lastPageshowAt",
        "lastPagehideAt",
        "lastBootstrapAbortReason",
    ]:
        assert field in APP


def test_authenticated_bootstrap_done_checks_visible_app_shell():
    assert 'authRestoreStatus !== "authenticated"' in APP
    assert 'hasSuccessfulApiBootstrap(startupTrace)' in APP
    assert 'document.querySelector<HTMLElement>(".app-shell")' in APP
    assert 'getVisibleElementCount(appContainer)' in APP
    assert 'setShowSuccessfulBootstrapRecovery(true)' in APP


def test_invalid_route_after_successful_bootstrap_falls_back_to_safe_default():
    assert 'invalid_page_after_successful_bootstrap' in APP
    assert 'resetPartnerFlowState("home")' in APP
    assert 'missing_partner_after_successful_bootstrap' in APP
    assert 'resetPartnerFlowState("catalog")' in APP
    assert 'return isKnownPage(String(page)) ? page : "home"' in APP


def test_loaded_data_without_route_has_visible_recovery_screen():
    assert 'function SuccessfulBootstrapRecoveryScreen' in APP
    assert 'Обновить экран' in APP
    assert 'setShowSuccessfulBootstrapRecovery(false)' in APP
    assert 'removeEntryFallbackOverlay()' in APP


def test_content_loaded_flags_support_blank_screen_diagnostics():
    assert '__BLOOM_CONTENT_STATIC_TEXTS_LOADED__ = false' in CONTENT
    assert '__BLOOM_CONTENT_BLOCKS_LOADED__ = false' in CONTENT
    assert '__BLOOM_CONTENT_STATIC_TEXTS_LOADED__ = true' in CONTENT
    assert '__BLOOM_CONTENT_BLOCKS_LOADED__ = true' in CONTENT


def test_nonfatal_safari_script_error_does_not_blank_ui():
    assert 'safari_generic_script_error_after_render' in BOUNDARY
    assert 'nonfatal: true' in BOUNDARY
    assert 'event.preventDefault()' in BOUNDARY
