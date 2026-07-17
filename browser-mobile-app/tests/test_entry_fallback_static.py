from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "src/main.tsx").read_text(encoding="utf-8")
APP = (ROOT / "src/App.tsx").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
LIFECYCLE = (ROOT / "src/diagnostics/lifecycleTrace.ts").read_text(encoding="utf-8")


def test_entry_uses_dynamic_app_import_with_early_fallback_and_error_panel() -> None:
    assert 'import React from "react";' in MAIN
    assert 'import * as ReactDOM from "react-dom/client";' in MAIN
    assert 'import("./App")' in MAIN
    assert "renderStartupLoadingFallback();" in MAIN
    assert "renderEarlyErrorDiagnostic(error, 'app_module_import')" in MAIN
    assert "MODULE_IMPORT_TIMEOUT_MS" not in MAIN
    assert "Promise.race" not in MAIN


def test_entry_watchdog_status_updates_exist_without_module_timeout() -> None:
    for marker in ["startEntryWatchdog", "3_000", "8_000", "Загрузка модулей приложения", "Приложение не завершило запуск"]:
        assert marker in MAIN


def test_storage_cleanup_is_scoped_and_preserves_auth_before_fallback() -> None:
    before_fallback = MAIN[: MAIN.index("renderStartupLoadingFallback();")]
    assert "window.Telegram" not in before_fallback
    assert "protectedAuthKeyPattern" in before_fallback
    assert "storage.removeItem(key)" in before_fallback


def test_lifecycle_trace_listener_setup_is_fail_safe() -> None:
    assert "try {\n  installLifecycleTraceListeners();" in LIFECYCLE
    assert "listener setup must not break entry startup" in LIFECYCLE
    assert "function sanitizeValue" in LIFECYCLE
    assert "return \"[unserializable]\"" in LIFECYCLE


def test_entry_fallback_insertion_precedes_runtime_boundary_import() -> None:
    assert MAIN.index("renderStartupLoadingFallback();") < MAIN.index('import("./components/RuntimeErrorBoundary")')


def test_entry_fallback_overlay_uses_body_or_document_element_not_root() -> None:
    assert 'wrapper.id = "bloom-entry-fallback-overlay"' in MAIN
    assert "document.body.appendChild(wrapper)" in MAIN
    assert "document.documentElement.appendChild(wrapper)" in MAIN
    assert "rootElement.replaceChildren(wrapper)" not in MAIN


def test_app_removes_entry_fallback_overlay_after_mount() -> None:
    assert 'import { removeEntryFallbackOverlay } from "./main";' in APP
    assert APP.index('lifecycleTrace("app_mount"') < APP.index("removeEntryFallbackOverlay();")


def test_remove_entry_fallback_overlay_removes_entry_and_html_fallbacks() -> None:
    remove_block = MAIN[MAIN.index("export function removeEntryFallbackOverlay()") : MAIN.index("async function startApp()")]
    assert 'document.getElementById("bloom-entry-fallback-overlay")' in remove_block
    assert 'document.getElementById("bloom-html-fallback-overlay")' in remove_block
    assert "fadeAndRemove(entryFallback);" in remove_block
    assert "fadeAndRemove(htmlFallback);" in remove_block


def test_index_contains_visible_html_startup_fallback_overlay() -> None:
    assert 'id="bloom-html-fallback-overlay"' in INDEX
    assert "Bloom Club загружается" in INDEX
    assert "Диагностика появится после запуска приложения" in INDEX
    assert INDEX.index('id="bloom-html-fallback-overlay"') < INDEX.index('id="root"') < INDEX.index('type="module" src="/src/main.tsx"')


def test_startup_loader_video_is_component_owned_asset() -> None:
    loading_state = (ROOT / 'src/components/LoadingState.tsx').read_text(encoding='utf-8')
    assert 'spinner' in loading_state
    assert 'role="status"' in loading_state


def test_telegram_sdk_loads_lazily_after_app_needs_it() -> None:
    webapp = (ROOT / "src/telegram/webapp.ts").read_text(encoding="utf-8")
    for marker in ["document.createElement('script')", "script.async = true", "await loadTelegramSdk();", "preloadTelegramSdkInBackground();"]:
        assert marker in webapp
