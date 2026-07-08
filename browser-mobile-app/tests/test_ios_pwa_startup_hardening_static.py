from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
MAIN = (ROOT / "src/main.tsx").read_text(encoding="utf-8")
SW = (ROOT / "public/sw.js").read_text(encoding="utf-8")
CLIENT = (ROOT / "src/api/client.ts").read_text(encoding="utf-8")
SERVER = (ROOT / "server/production-server.js").read_text(encoding="utf-8")


def test_no_parser_blocking_telegram_script_in_index() -> None:
    assert "telegram-web-app.js" not in INDEX
    assert "https://telegram.org" not in INDEX


def test_service_worker_never_caches_app_shell_or_js_chunks() -> None:
    assert "caches.open" not in SW
    assert "cache.put" not in SW
    assert "caches.match" not in SW
    assert "url.pathname.startsWith('/assets/')" in SW
    assert "fetch(request, { cache: 'no-store' })" in SW


def test_chunk_recovery_preserves_auth_and_reloads_once() -> None:
    assert "isLikelyChunkLoadFailure" in MAIN
    assert "recoverFromChunkLoadFailure" in MAIN
    assert "bloom_chunk_recovery_reload_count" in MAIN
    assert "protectedAuthKeyPattern" in MAIN
    assert "auth|token|telegram_login|session|jwt|initdata" in MAIN


def test_recovery_screen_has_required_copy_and_safe_cache_cleanup() -> None:
    assert "Проблемы с запуском" in MAIN
    assert "Мы не смогли открыть приложение после быстрого перезапуска." in MAIN
    assert "Перезагрузить приложение" in MAIN
    assert "Очистить временный кэш" in MAIN
    assert "clearTemporaryBrowserCaches" in MAIN


def test_corrupted_auth_session_storage_does_not_crash() -> None:
    assert "JSON.parse(rawSession)" in CLIENT
    assert "catch" in CLIENT[CLIENT.index("function readSessionAuthToken") : CLIENT.index("export function getStoredAuthToken")]


def test_runtime_critical_files_are_no_store_on_node_server() -> None:
    assert "serveStartupCriticalFile" in SERVER
    assert "'/sw.js'" in SERVER
    assert "'/manifest.webmanifest'" in SERVER
    assert "'/runtime-config.json'" in SERVER
    assert "'cache-control': HTML_NO_STORE_CACHE_CONTROL" in SERVER


def test_startup_path_has_single_resume_handler_set_and_no_entry_lifecycle_duplicate() -> None:
    assert "installStandaloneLifecycleRecovery" not in MAIN
    assert "standalone_lifecycle_recovery" not in MAIN
    assert MAIN.count("registerServiceWorkerSafely();") == 1


def test_startup_does_not_prefetch_catalog_from_home_or_html_shell() -> None:
    assert "home_prefetch" not in (ROOT / "src/App.tsx").read_text(encoding="utf-8")
    assert "const items = await fetchPublicCatalogPartners();" not in SERVER[SERVER.index("async function serveFrontend") : SERVER.index("async function handleRequest")]
    assert "injectedCatalogBootstrap: false" in SERVER

LIFECYCLE = (ROOT / "src/diagnostics/startupLifecycle.ts").read_text(encoding="utf-8")
APP = (ROOT / "src/App.tsx").read_text(encoding="utf-8")
REPORTER = (ROOT / "src/diagnostics/clientErrorReporter.ts").read_text(encoding="utf-8")


def test_interrupted_startup_marker_detected_and_auth_preserved() -> None:
    assert "bloom_startup_in_progress" in LIFECYCLE
    assert "detectInterruptedStartup" in LIFECYCLE
    assert "clearInterruptedStartupTemporaryState" in LIFECYCLE
    assert "protectedAuthKeyPattern" in LIFECYCLE
    assert "auth|token|telegram_login|session|jwt|initdata" in LIFECYCLE


def test_first_visible_shell_is_marked_before_bootstrap_finishes() -> None:
    assert "first_visible_paint" in LIFECYCLE
    assert "markFirstVisiblePaint" in APP
    assert APP.index("markFirstVisiblePaint") < APP.index("void loadAppData")


def test_pagehide_before_completion_marks_interrupted_startup() -> None:
    assert "markStartupInterrupted(event.type)" in APP
    assert "invalidateBootstrapForInactiveWebView(event.type)" in APP


def test_frontend_build_mismatch_ignores_version_field() -> None:
    assert "config.buildId && config.buildId !== config.version" in REPORTER
    assert "frontend_build_mismatch_detected" in REPORTER


def test_dotfile_env_paths_do_not_fall_through_to_index() -> None:
    assert "isForbiddenSpaFallbackPath" in SERVER
    assert r"\.env" in SERVER
    assert r"\.git" in SERVER
    assert "'/package.json'" in SERVER
    assert "sendText(response, 404, 'not found'" in SERVER


def test_generic_safari_script_error_after_first_visible_paint_is_nonfatal() -> None:
    boundary = (ROOT / "src/components/RuntimeErrorBoundary.tsx").read_text(encoding="utf-8")
    safari = (ROOT / "src/diagnostics/safariGenericScriptError.ts").read_text(encoding="utf-8")
    assert "shouldIgnoreGenericSafariScriptErrorAfterRender" in MAIN
    assert "safari_generic_script_error_after_render" in MAIN
    assert "return true" in MAIN[MAIN.index("window.onerror") : MAIN.index("window.onunhandledrejection")]
    assert "renderEarlyErrorDiagnostic(error ?? _message, \"window_error\")" in MAIN
    assert MAIN.index("shouldIgnoreGenericSafariScriptErrorAfterRender") < MAIN.index("renderEarlyErrorDiagnostic(error ?? _message, \"window_error\")")
    assert "isGenericSafariScriptErrorEvent(event) && hasReachedFirstVisiblePaint()" in boundary
    assert "event.preventDefault()" in boundary
    assert "this.setState" in boundary[boundary.index("private handleWindowError") :]
    assert "message === \"Script error.\"" in safari
    assert "window.__BLOOM_STARTUP_PHASE__ === \"first_visible_paint\"" in safari
    assert "window.__BLOOM_APP_INTERACTIVE__ === true" in safari


def test_generic_safari_script_error_before_render_still_triggers_recovery_diagnostics() -> None:
    assert "message === \"Script error.\"" in (ROOT / "src/diagnostics/safariGenericScriptError.ts").read_text(encoding="utf-8")
    onerror_block = MAIN[MAIN.index("window.onerror") : MAIN.index("window.onunhandledrejection")]
    assert "shouldIgnoreGenericSafariScriptErrorAfterRender" in onerror_block
    assert "renderEarlyErrorDiagnostic(error ?? _message, \"window_error\")" in onerror_block
    assert "renderModuleLoadErrorPanel(error, source)" in MAIN[MAIN.index("function renderEarlyErrorDiagnostic") : MAIN.index("function startEntryWatchdog")]


def test_real_react_errors_and_chunk_failures_remain_fatal_recovery_paths() -> None:
    boundary = (ROOT / "src/components/RuntimeErrorBoundary.tsx").read_text(encoding="utf-8")
    assert "static getDerivedStateFromError" in boundary
    assert "componentDidCatch" in boundary
    assert "createRuntimeErrorDiagnostic(error, errorInfo.componentStack)" in boundary
    assert "ReactErrorBoundary" in boundary
    assert "isLikelyChunkLoadFailure" in MAIN
    assert "recoverFromChunkLoadFailure(error, source)" in MAIN
    assert "Missing startup asset" in MAIN


def test_pwa_root_icon_fallbacks_reuse_existing_docs_icons_and_not_spa_fallbacks() -> None:
    assert not (ROOT / "public/apple-touch-icon.png").exists()
    assert not (ROOT / "public/apple-touch-icon-precomposed.png").exists()
    assert not (ROOT / "public/favicon.ico").exists()
    assert (ROOT / "public/docs/icons/apple-touch-icon.png").read_bytes().startswith(b"\x89PNG")
    assert (ROOT / "public/docs/icons/favicon-32.png").read_bytes().startswith(b"\x89PNG")
    assert "STARTUP_CRITICAL_FILE_ALIASES" in SERVER
    assert "['/apple-touch-icon.png', 'docs/icons/apple-touch-icon.png']" in SERVER
    assert "['/apple-touch-icon-precomposed.png', 'docs/icons/apple-touch-icon.png']" in SERVER
    assert "['/favicon.ico', 'docs/icons/favicon-32.png']" in SERVER
    assert "pathname === '/favicon.ico' ? 'image/png'" in SERVER
