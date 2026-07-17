from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "src/App.tsx").read_text(encoding="utf-8")
MAIN = (ROOT / "src/main.tsx").read_text(encoding="utf-8")
WEBAPP = (ROOT / "src/telegram/webapp.ts").read_text(encoding="utf-8")
SERVER = (ROOT / "server/production-server.js").read_text(encoding="utf-8")


def test_bfcache_pageshow_preserves_auth_session_without_forced_bootstrap() -> None:
    assert 'window.addEventListener("pageshow", onPageShow)' in APP
    on_pageshow = APP[APP.index('const onPageShow = (event: PageTransitionEvent) => {'):APP.index('const onResume =', APP.index('const onPageShow = (event: PageTransitionEvent) => {'))]
    assert 'resumeWithoutAuthReset(event);' in on_pageshow
    assert 'loadAppData("retry", true)' not in on_pageshow
    assert 'resetStaleBootstrapForActiveWebView' not in on_pageshow


def test_webview_resume_events_reprepare_viewport_idempotently() -> None:
    assert 'document.addEventListener("resume", onResume)' in APP
    assert 'document.addEventListener("visibilitychange", onVisibilityChange)' in APP
    assert 'document.visibilityState === "visible"' in APP
    assert 'lifecycleTrace("webview_resume_prepare_start"' in APP
    assert 'lifecycleTrace("webview_resume_prepare_ok"' in APP


def test_repeated_prepare_telegram_viewport_cleans_previous_listeners_first() -> None:
    prepare_index = WEBAPP.index("export function prepareTelegramViewport")
    cleanup_index = WEBAPP.index("cleanupTelegramViewportListeners?.();", prepare_index)
    ready_index = WEBAPP.index("webApp.ready?.();", prepare_index)
    on_event_index = WEBAPP.index("webApp.onEvent?.('viewportChanged'", prepare_index)
    assert cleanup_index < ready_index < on_event_index
    assert "cleanupTelegramViewportListeners = null;" in WEBAPP
    assert "__BLOOM_TG_VIEWPORT_PREPARE_COUNT__" in WEBAPP
    assert "__BLOOM_TG_VIEWPORT_CLEANUP_COUNT__" in WEBAPP


def test_fallback_removed_after_successful_mount_and_cannot_cover_ready_app() -> None:
    assert 'export function removeEntryFallbackOverlay()' in MAIN
    assert 'fadeAndRemove(entryFallback);' in MAIN
    assert 'fadeAndRemove(htmlFallback);' in MAIN
    assert 'removeEntryFallbackOverlay();' in APP
    assert APP.index('lifecycleTrace("app_mount"') < APP.index('removeEntryFallbackOverlay();')


def test_startup_errors_are_visible_without_backend_endpoint() -> None:
    assert "function persistStartupError" in MAIN
    assert "window.__BLOOM_LAST_STARTUP_ERROR__" in MAIN
    assert '"session" + "Storage"' in MAIN
    assert '?.setItem("bloom_last_startup_error"' in MAIN
    assert 'console.error("bloom_startup_error"' in MAIN
    assert "fetch(" not in MAIN[MAIN.index("function persistStartupError") : MAIN.index("function renderModuleLoadErrorPanel")]


def test_production_html_is_no_store_and_assets_are_immutable() -> None:
    assert "const HTML_NO_STORE_CACHE_CONTROL = 'no-store, no-cache, max-age=0, must-revalidate'" in SERVER
    assert "'cache-control': HTML_NO_STORE_CACHE_CONTROL" in SERVER
    assert "pragma: 'no-cache'" in SERVER
    assert "expires: '0'" in SERVER
    assert "const ASSET_IMMUTABLE_CACHE_CONTROL = 'public, max-age=31536000, immutable'" in SERVER
    assert "'cache-control': ASSET_IMMUTABLE_CACHE_CONTROL" in SERVER


def test_production_static_serving_logs_safe_index_and_asset_events() -> None:
    assert "frontend_index_served" in SERVER
    assert "frontend_asset_served" in SERVER
    assert "frontend_asset_missing" in SERVER
    assert "cacheControlType" in SERVER
    assert "isTelegramUserAgent" in SERVER
    assert "contentLength" in SERVER
    assert "injectedCatalogBootstrap" in SERVER


def test_app_static_import_is_preserved() -> None:
    assert 'importApplicationModules' in MAIN
    assert 'import("./App")' in MAIN


def test_html_fallback_reports_js_entry_not_executed_without_backend_endpoint() -> None:
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "__BLOOM_ENTRY_SCRIPT_EXECUTED__ = false" in index
    assert "bloomHtmlEntryWatchdog" in index
    assert "JS entry не выполнен" in index
    assert "устаревшего HTML" in index
    assert "fetch(" not in index[index.index("bloomHtmlEntryWatchdog") : index.index("</script>", index.index("bloomHtmlEntryWatchdog"))]
    assert "__BLOOM_ENTRY_SCRIPT_EXECUTED__ = true" in MAIN


def test_missing_assets_are_not_spa_fallbacks() -> None:
    asset_section = SERVER[SERVER.index("async function serveAsset") : SERVER.index("async function serveUpload")]
    assert "sendText(response, 404, 'Not found')" in asset_section
    assert "serveFrontend" not in asset_section
    assert "frontend_asset_missing" in asset_section


def test_all_versioned_paths_use_current_index_handler_without_redirect() -> None:
    route_section = SERVER[SERVER.index("function isVersionedFrontendRoute") : SERVER.index("const REQUEST_LOG_WINDOW_MS")]
    assert "pathname.startsWith('/app-v')" in route_section
    request_section = SERVER[SERVER.index("if (isVersionedFrontendRoute(pathname))") : SERVER.index("sendText(response, 404, 'Not found');", SERVER.index("if (isVersionedFrontendRoute(pathname))"))]
    assert "serveFrontend" in request_section
    assert "writeHead(30" not in request_section


def test_pageshow_and_focus_do_not_force_retry_or_reset_auth() -> None:
    lifecycle_section = APP[APP.index('const onPageShow = (event: PageTransitionEvent) => {'):APP.index('window.addEventListener("pageshow", onPageShow)')]
    assert 'resumeWithoutAuthReset(event);' in lifecycle_section
    assert 'void loadAppData("retry", true);' not in lifecycle_section
    assert 'resetStaleBootstrapForActiveWebView' not in lifecycle_section
    assert 'clearStoredAuthToken' not in lifecycle_section


def test_visibilitychange_resume_focus_behavior_unchanged() -> None:
    assert 'const onResume = (event: Event) => resumeWithoutAuthReset(event);' in APP
    assert 'const onFocus = (event: Event) => {' in APP
    assert 'const onBlur = (event: Event) => markInactive(event);' in APP
    assert 'document.visibilityState === "visible"' in APP
    assert 'resumeWithoutAuthReset(event);' in APP[APP.index('const onVisibilityChange'):APP.index('window.addEventListener("pageshow", onPageShow)')]
