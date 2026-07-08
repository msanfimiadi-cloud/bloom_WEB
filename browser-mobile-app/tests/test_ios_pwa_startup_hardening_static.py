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
