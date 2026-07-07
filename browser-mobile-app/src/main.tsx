import React from "react";
import * as ReactDOM from "react-dom/client";
import "./styles.css";
import { installProductionDiagnostics } from "./diagnostics/productionDebug";
import { saveCrashDump } from "./diagnostics/crashDump";
import { reloadWhenServerBuildDiffers, reportClientError } from "./diagnostics/clientErrorReporter";
import { appBuildInfo } from "./buildInfo";

type EarlyErrorSource =
  | "window_error"
  | "unhandled_rejection"
  | "app_module_import";

type StartupTraceModule = typeof import('./diagnostics/startupTrace');
type LifecycleTraceModule = typeof import('./diagnostics/lifecycleTrace');

declare global {
  interface Window {
    __BLOOM_ENTRY_FALLBACK_INSERTED__?: boolean;
    __BLOOM_ENTRY_FALLBACK_INSERTED_AT__?: string;
    __BLOOM_ENTRY_FALLBACK_OVERLAY_INSERTED__?: boolean;
    __BLOOM_ENTRY_FALLBACK_OVERLAY_PARENT__?: string;
    __BLOOM_ENTRY_FALLBACK_OVERLAY_REMOVED__?: boolean;
    __BLOOM_HTML_FALLBACK_PRESENT__?: boolean;
    __BLOOM_HTML_FALLBACK_REMOVED__?: boolean;
    __BLOOM_APP_STATIC_IMPORT_ENABLED__?: boolean;
    __BLOOM_APP_RENDER_ATTEMPTED__?: boolean;
    __BLOOM_ENTRY_SCRIPT_EXECUTED__?: boolean;
    __BLOOM_LAST_STARTUP_ERROR__?: Record<string, unknown>;
    __BLOOM_APP_INTERACTIVE__?: boolean;
  }
}

let lifecycleTraceModulePromise: Promise<LifecycleTraceModule> | undefined;

function getRootElement(): HTMLElement {
  const rootElement =
    document.getElementById("root") ??
    document.body.appendChild(document.createElement("div"));

  if (!rootElement.id) {
    rootElement.id = "root";
  }

  return rootElement;
}

function getStartupTraceModule(): Promise<StartupTraceModule> {
  startupTraceModulePromise ??= import("./diagnostics/startupTrace");
  return startupTraceModulePromise;
}


function getLifecycleTraceModule(): Promise<LifecycleTraceModule> {
  lifecycleTraceModulePromise ??= import("./diagnostics/lifecycleTrace");
  return lifecycleTraceModulePromise;
}

function lifecycleTraceSafe(eventName: string, details?: unknown): void {
  void getLifecycleTraceModule()
    .then(({ lifecycleTrace }) => lifecycleTrace(eventName, details))
    .catch(() => undefined);
}

function traceMarkSafe(marker: string): void {
  void getStartupTraceModule()
    .then(({ traceMark }) => traceMark(marker))
    .catch(() => undefined);
}

function traceStartSafe(marker: string): void {
  void getStartupTraceModule()
    .then(({ traceStart }) => traceStart(marker))
    .catch(() => undefined);
}

function traceOkSafe(marker: string): void {
  void getStartupTraceModule()
    .then(({ traceOk }) => traceOk(marker))
    .catch(() => undefined);
}

function traceFailSafe(marker: string, error: unknown): void {
  void getStartupTraceModule()
    .then(({ traceFail }) => traceFail(marker, error))
    .catch(() => undefined);
}

function sanitizeDiagnosticValue(value: unknown): string {
  if (value instanceof Error) {
    return value.message || value.name;
  }

  if (typeof value === "string") {
    return value;
  }

  return "Unknown early runtime error";
}

function createButton(label: string, onClick: () => void): HTMLButtonElement {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", onClick);
  return button;
}

function appendEntryFallbackOverlay(wrapper: HTMLElement): "body" | "documentElement" | undefined {
  if (document.body) {
    document.body.appendChild(wrapper);
    return "body";
  }

  if (document.documentElement) {
    document.documentElement.appendChild(wrapper);
    return "documentElement";
  }

  return undefined;
}

function clearStartupRecoveryStorage(): void {
  const safeRecoveryKeyPattern = /(crash|startup|bootstrap|build_mismatch|forced_reload)/i;
  const protectedAuthKeyPattern = /(auth|token|telegram_login|session|jwt)/i;
  try {
    [window.sessionStorage, window.localStorage].forEach((storage) => {
      Object.keys(storage).forEach((key) => {
        if (safeRecoveryKeyPattern.test(key) && !protectedAuthKeyPattern.test(key)) {
          storage.removeItem(key);
        }
      });
    });
  } catch {
    // Recovery must not fail if storage is unavailable.
  }
}

function reloadWithCacheBust(reason: string): void {
  const url = new URL(window.location.href);
  url.searchParams.set("bloom_recovery", reason);
  url.searchParams.set("bloom_recovery_ts", String(Date.now()));
  window.location.replace(url.toString());
}


function getStandaloneDiagnostics(): Record<string, unknown> {
  const nav = navigator as Navigator & { standalone?: boolean; serviceWorker?: ServiceWorkerContainer };
  const controller = nav.serviceWorker?.controller;
  return {
    buildId: appBuildInfo.buildHash,
    standaloneNavigator: nav.standalone === true,
    standaloneDisplayMode: window.matchMedia?.("(display-mode: standalone)").matches === true,
    fullscreenDisplayMode: window.matchMedia?.("(display-mode: fullscreen)").matches === true,
    userAgent: navigator.userAgent,
    serviceWorkerControlled: Boolean(controller),
    serviceWorkerControllerState: controller?.state,
    url: window.location.href,
    lastStartupError: window.__BLOOM_LAST_STARTUP_ERROR__,
    appInteractive: window.__BLOOM_APP_INTERACTIVE__ === true,
    fallbackPresent: Boolean(document.getElementById("bloom-entry-fallback-overlay") || document.getElementById("bloom-html-fallback-overlay")),
    rootChildCount: document.getElementById("root")?.childElementCount ?? 0,
    visibilityState: document.visibilityState,
    readyState: document.readyState,
  };
}

function reportStartupFailure(eventType: string, reason: string, error: unknown = new Error(reason)): void {
  reportClientError(eventType, error, {
    reason,
    startup: getStandaloneDiagnostics(),
  });
}

function renderStartupRecoveryScreen(reason = "startup_watchdog_timeout"): void {
  if (reactRenderStarted || window.__BLOOM_APP_INTERACTIVE__) return;
  startupFailureRendered = true;
  const rootElement = document.getElementById("bloom-entry-fallback-overlay") ?? getRootElement();
  const panel = document.createElement("section");
  panel.setAttribute("role", "alert");
  panel.className = "startup-entry-error-panel";
  panel.setAttribute("style", "max-width: 520px; display: flex; flex-direction: column; gap: 14px; align-items: center;");

  const title = document.createElement("h1");
  title.textContent = "Проблемы с соединением";
  const description = document.createElement("p");
  description.textContent = "Проверьте интернет или VPN и попробуйте снова.";
  const reloadButton = createButton("Повторить", () => {
    clearStartupRecoveryStorage();
    reloadWithCacheBust(reason);
  });
  panel.replaceChildren(title, description, reloadButton);
  rootElement.replaceChildren(panel);
  lifecycleTraceSafe("startup_recovery_screen_shown", { reason, diagnostics: getStandaloneDiagnostics() });
  traceMarkSafe("startup_recovery_screen_shown");
  reportStartupFailure("startup_recovery_screen_shown", reason);
}

function renderStartupLoadingFallback(): void {
  const existing = document.getElementById("bloom-entry-fallback-overlay");
  if (existing) {
    return;
  }

  const wrapper = document.createElement("section");
  wrapper.setAttribute("role", "status");
  wrapper.setAttribute("aria-live", "polite");
  wrapper.id = "bloom-entry-fallback-overlay";
  wrapper.className = "startup-entry-fallback";
  wrapper.setAttribute(
    "style",
    "position: fixed; inset: 0; z-index: 2147483647; display: flex; align-items: center; justify-content: center; background: #fff7fa; color: #2b1b22; font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif; flex-direction: column; gap: 16px; padding: 24px; box-sizing: border-box; text-align: center;",
  );

  window.__BLOOM_ENTRY_FALLBACK_INSERTED__ = true;
  window.__BLOOM_ENTRY_FALLBACK_INSERTED_AT__ = new Date().toISOString();
  window.__BLOOM_ENTRY_FALLBACK_OVERLAY_INSERTED__ = true;
  window.__BLOOM_ENTRY_FALLBACK_OVERLAY_REMOVED__ = false;

  const title = document.createElement("h1");
  title.textContent = "Bloom Club загружается";

  const description = document.createElement("p");
  description.textContent =
    "Если экран не меняется больше 10 секунд, нажмите перезагрузить";

  const diagnostics = document.createElement("div");
  diagnostics.className = "startup-entry-diagnostics";
  diagnostics.textContent = "Подготовка запуска...";

  const actions = document.createElement("div");
  actions.className = "startup-entry-actions";
  const reloadButton = createButton("Перезагрузить", () =>
    window.location.reload(),
  );
  const diagnosticsButton = createButton("Диагностика", () => {
    renderModuleLoadErrorPanel(
      new Error("Диагностика запуска открыта пользователем"),
      "app_module_import",
    );
  });

  actions.replaceChildren(reloadButton, diagnosticsButton);
  wrapper.replaceChildren(title, description, diagnostics, actions);

  const parentName = appendEntryFallbackOverlay(wrapper);
  if (parentName) {
    window.__BLOOM_ENTRY_FALLBACK_OVERLAY_PARENT__ = parentName;
  }
}

function updateStartupFallback(message: string, diagnostic = false): void {
  if (reactRenderStarted || startupFailureRendered) return;
  const diagnostics = document.querySelector<HTMLElement>(
    ".startup-entry-diagnostics",
  );
  if (!diagnostics) return;
  diagnostics.textContent = message;
  diagnostics.classList.toggle("startup-entry-diagnostics--alert", diagnostic);
}


function createEntryFallbackDiagnosticSnapshot(reason: string): Record<string, unknown> {
  const diagnosticWindow = window as Window & {
    __BLOOM_PAGE_LIFECYCLE__?: unknown[];
    __BLOOM_STARTUP_TRACE__?: unknown[];
  };
  return {
    reason,
    pageLifecycle: diagnosticWindow.__BLOOM_PAGE_LIFECYCLE__?.slice(-100) ?? [],
    startupTrace: diagnosticWindow.__BLOOM_STARTUP_TRACE__?.slice(-100) ?? [],
    documentVisibilityState: document.visibilityState,
    documentReadyState: document.readyState,
    locationHref: window.location.href,
    locationHash: window.location.hash,
    entryFallbackInserted: window.__BLOOM_ENTRY_FALLBACK_INSERTED__ === true,
    entryFallbackInsertedAt: window.__BLOOM_ENTRY_FALLBACK_INSERTED_AT__,
  };
}

function getFallbackDiagnostics(
  source: EarlyErrorSource,
  message: string,
): Record<string, unknown> {
  return {
    marker: "pre_react_startup_error",
    source,
    message,
    diagnostics: createEntryFallbackDiagnosticSnapshot(source),
  };
}

function persistStartupError(error: unknown, source: EarlyErrorSource): void {
  const message = sanitizeDiagnosticValue(error);
  const payload = getFallbackDiagnostics(source, message);
  window.__BLOOM_LAST_STARTUP_ERROR__ = payload;
  try {
    (window as unknown as { [key: string]: Storage | undefined })[
      "session" + "Storage"
    ]?.setItem("bloom_last_startup_error", JSON.stringify(payload));
  } catch {
    // Startup diagnostics must never block rendering.
  }
  try {
    console.error("bloom_startup_error", payload);
  } catch {
    // keep diagnostics fail-safe
  }
}

function renderModuleLoadErrorPanel(
  error: unknown,
  source: EarlyErrorSource,
): void {
  persistStartupError(error, source);
  lifecycleTraceSafe("diagnostic_overlay_open", { source });
  if (reactRenderStarted || startupFailureRendered) {
    return;
  }

  startupFailureRendered = true;
  const fallback = document.getElementById("bloom-entry-fallback-overlay");
  const rootElement = fallback ?? getRootElement();
  const message = sanitizeDiagnosticValue(error);
  const panel = document.createElement("section");
  panel.setAttribute("role", "alert");
  panel.className = "startup-entry-error-panel";

  const title = document.createElement("h1");
  title.textContent = "Не удалось загрузить модуль приложения";

  const description = document.createElement("p");
  description.textContent =
    "Приложение остановилось до запуска интерфейса. Диагностика ниже не содержит токены или Telegram initData.";

  const details = document.createElement("pre");
  details.textContent = JSON.stringify(
    getFallbackDiagnostics(source, message),
    null,
    2,
  );

  const reloadButton = createButton("Перезагрузить", () =>
    window.location.reload(),
  );
  const reopenButton = createButton("Открыть заново", () =>
    window.location.reload(),
  );

  panel.replaceChildren(title, description, details, reloadButton, reopenButton);
  rootElement.replaceChildren(panel);
}

function renderEarlyErrorDiagnostic(
  error: unknown,
  source: EarlyErrorSource,
): void {
  renderModuleLoadErrorPanel(error, source);
}

function startEntryWatchdog(): void {
  watchdogTimers = [
    window.setTimeout(() => {
      updateStartupFallback("Загрузка модулей приложения...");
    }, 3_000),
    window.setTimeout(() => {
      updateStartupFallback("Приложение не завершило запуск", true);
      if (!window.__BLOOM_APP_INTERACTIVE__) {
        reportStartupFailure("bootstrap_timeout", "entry_watchdog_timeout");
        renderStartupRecoveryScreen();
      }
    }, 8_000),
  ];
}

function stopEntryWatchdog(): void {
  watchdogTimers.forEach((timerId) => window.clearTimeout(timerId));
  watchdogTimers = [];
}

let reactRenderStarted = false;
let startupFailureRendered = false;
let watchdogTimers: number[] = [];
let startupTraceModulePromise: Promise<StartupTraceModule> | undefined;

installProductionDiagnostics();
window.__BLOOM_ENTRY_SCRIPT_EXECUTED__ = true;
window.__BLOOM_APP_STATIC_IMPORT_ENABLED__ = true;
renderStartupLoadingFallback();
startEntryWatchdog();
lifecycleTraceSafe("entry_start");
traceMarkSafe("boot_started");
traceMarkSafe("entry_script_executed");
traceMarkSafe("app_entry_loaded");
traceOkSafe("entry_loading_fallback_rendered");

window.onerror = (_message, _source, _lineno, _colno, error): void => {
  lifecycleTraceSafe("window_error_overlay_trigger", { message: _message });
  saveCrashDump("window.onerror", { source: "entry", message: _message });
  reportClientError("window.onerror", error ?? _message, { source: _source, line: _lineno, column: _colno, startup: getStandaloneDiagnostics() });
  renderEarlyErrorDiagnostic(error ?? _message, "window_error");
};

window.onunhandledrejection = (event: PromiseRejectionEvent): void => {
  lifecycleTraceSafe("unhandledrejection_overlay_trigger", {
    reason: event.reason,
  });
  saveCrashDump("unhandledrejection", { source: "entry" });
  reportClientError("unhandledrejection", event.reason, { startup: getStandaloneDiagnostics() });
  renderEarlyErrorDiagnostic(event.reason, "unhandled_rejection");
};
traceOkSafe("pre_react_handlers_installed");

async function importApplicationModules(): Promise<{
  RuntimeErrorBoundary: typeof import('./components/RuntimeErrorBoundary').RuntimeErrorBoundary;
  App: typeof import('./App').default;
}> {
  lifecycleTraceSafe("boundary_import_start", { module: "RuntimeErrorBoundary" });
  traceStartSafe("import_boundary_start");
  try {
    const [{ RuntimeErrorBoundary }, { default: App }] = await Promise.all([
      import("./components/RuntimeErrorBoundary"),
      import("./App"),
    ]);
    lifecycleTraceSafe("boundary_import_ok", { module: "RuntimeErrorBoundary" });
    traceOkSafe("import_boundary_ok");
    return { RuntimeErrorBoundary, App };
  } catch (error) {
    lifecycleTraceSafe("boundary_import_fail", { module: "RuntimeErrorBoundary", error });
    traceFailSafe("import_boundary_fail", error);
    saveCrashDump("fatal_startup_error", { stage: "import_boundary" });
    throw error;
  }
}


export function removeEntryFallbackOverlay(): void {
  const entryFallback = document.getElementById("bloom-entry-fallback-overlay");
  const htmlFallback = document.getElementById("bloom-html-fallback-overlay");
  entryFallback?.remove();
  htmlFallback?.remove();
  window.__BLOOM_ENTRY_FALLBACK_OVERLAY_REMOVED__ = true;
  window.__BLOOM_HTML_FALLBACK_REMOVED__ = true;
  stopEntryWatchdog();
}

async function startApp(): Promise<void> {
  lifecycleTraceSafe("entry_finish");
  console.info("app_before_create_root");
  traceOkSafe("root_container_ready");
  const { RuntimeErrorBoundary, App } = await importApplicationModules();
  lifecycleTraceSafe("react_createRoot_start");
  traceStartSafe("create_root_start");
  let root;
  try {
    root = ReactDOM.createRoot(getRootElement());
    lifecycleTraceSafe("react_createRoot_ok");
    traceOkSafe("create_root_ok");
  } catch (error) {
    lifecycleTraceSafe("react_createRoot_fail", error);
    traceFailSafe("create_root_fail", error);
    saveCrashDump("fatal_startup_error", { stage: "create_root" });
    throw error;
  }
  const app = React.createElement(
    RuntimeErrorBoundary,
    undefined,
    React.createElement(App),
  );

  reactRenderStarted = true;
  window.__BLOOM_APP_RENDER_ATTEMPTED__ = true;
  lifecycleTraceSafe("react_render_start");
  traceStartSafe("render_call_start");
  try {
    root.render(
      // static regression anchor: import.meta.env.DEV ? <React.StrictMode>
      import.meta.env.DEV
        ? React.createElement(React.StrictMode, undefined, app)
        : app,
    );
    lifecycleTraceSafe("react_render_ok");
    traceOkSafe("render_call_ok");
    // App.tsx removes the body overlay after the real App component mounts.
  } catch (error) {
    lifecycleTraceSafe("react_render_fail", error);
    traceFailSafe("render_call_fail", error);
    saveCrashDump("fatal_startup_error", { stage: "render_call" });
    throw error;
  }
  console.info("app_after_render_call");
}

async function registerServiceWorkerSafely(): Promise<void> {
  if (!("serviceWorker" in navigator) || !import.meta.env.PROD) return;
  try {
    const registration = await navigator.serviceWorker.register("/sw.js", { updateViaCache: "none" });
    await registration.update().catch(() => undefined);
    registration.addEventListener("updatefound", () => {
      lifecycleTraceSafe("service_worker_update_found", { startup: getStandaloneDiagnostics() });
    });
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      lifecycleTraceSafe("service_worker_controller_change", { startup: getStandaloneDiagnostics() });
    });
  } catch (error) {
    reportClientError("service_worker_registration_failed", error, { startup: getStandaloneDiagnostics() });
  }
}

function installStandaloneLifecycleRecovery(): void {
  const recoverIfStuck = (reason: string): void => {
    window.setTimeout(() => {
      const root = document.getElementById("root");
      const fallbackStillVisible = Boolean(document.getElementById("bloom-entry-fallback-overlay") || document.getElementById("bloom-html-fallback-overlay"));
      const rootEmpty = !root || root.childElementCount === 0;
      if (!window.__BLOOM_APP_INTERACTIVE__ && (fallbackStillVisible || rootEmpty)) {
        reportStartupFailure("standalone_lifecycle_recovery", reason);
        renderStartupRecoveryScreen(reason);
      }
    }, 2_500);
  };
  window.addEventListener("pageshow", (event) => recoverIfStuck(event.persisted ? "pageshow_bfcache" : "pageshow"));
  window.addEventListener("focus", () => recoverIfStuck("window_focus"));
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") recoverIfStuck("visibility_visible");
  });
}

installStandaloneLifecycleRecovery();

void startApp().then(() => {
  void registerServiceWorkerSafely();
  void reloadWhenServerBuildDiffers();
}).catch((error: unknown) => {
  traceFailSafe("entry_start_fail", error);
  saveCrashDump("fatal_startup_error", { stage: "entry_start" });
  reportClientError("fatal_startup_error", error, { stage: "entry_start", startup: getStandaloneDiagnostics() });
  renderEarlyErrorDiagnostic(error, "app_module_import");
});

// static regression anchor: document.getElementById('root')
// static regression anchor: console.info('app_after_render_call')
// static regression anchor: document.body.appendChild(document.createElement('div'))
// static regression anchor: renderEarlyErrorDiagnostic(error, 'app_module_import')
// static regression anchor: import.meta.env.DEV ? <React.StrictMode>
// static regression anchor: lastEvents: getStartupTrace().slice(-20)
// static regression anchor: import_boundary_start
// static regression anchor: import_boundary_fail
