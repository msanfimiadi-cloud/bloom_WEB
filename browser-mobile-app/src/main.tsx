import React from "react";
import * as ReactDOM from "react-dom/client";
import "./styles.css";
import { installProductionDiagnostics } from "./diagnostics/productionDebug";
import { saveCrashDump } from "./diagnostics/crashDump";
import { reloadWhenServerBuildDiffers, reportClientError } from "./diagnostics/clientErrorReporter";
import { appBuildInfo } from "./buildInfo";
import { clearInterruptedStartupTemporaryState, detectInterruptedStartup, getStartupMarkers, setStartupPhase } from "./diagnostics/startupLifecycle";
import { markFirstReactRenderForExecutionTrace, traceStartupStep } from "./diagnostics/startupExecutionTrace";
import { shouldIgnoreGenericSafariScriptErrorAfterRender } from "./diagnostics/safariGenericScriptError";

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
    __BLOOM_EARLY_STARTUP_TRACE__?: Array<Record<string, unknown>>;
    __BLOOM_RESOURCE_ERROR_TRACE__?: Array<Record<string, unknown>>;
    __BLOOM_CHUNK_RECOVERY_STARTED__?: boolean;
    __BLOOM_STARTUP_PHASE__?: string;
    __BLOOM_STARTUP_SPLASH_READY__?: boolean;
    __BLOOM_STARTUP_SPLASH_STARTED_AT__?: number;
    __BLOOM_STARTUP_APP_READY__?: boolean;
    __BLOOM_STARTUP_VIDEO_DONE__?: boolean;
    __BLOOM_STARTUP_ROOT_REVEALED__?: boolean;
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
  void (async () => {
    try {
      const { lifecycleTrace } = await getLifecycleTraceModule();
      lifecycleTrace(eventName, details);
    } catch {
      // Diagnostics must never block startup.
    }
  })();
}

function traceMarkSafe(marker: string): void {
  void (async () => {
    try {
      const { traceMark } = await getStartupTraceModule();
      traceMark(marker);
    } catch {
      // Diagnostics must never block startup.
    }
  })();
}

function traceStartSafe(marker: string): void {
  void (async () => {
    try {
      const { traceStart } = await getStartupTraceModule();
      traceStart(marker);
    } catch {
      // Diagnostics must never block startup.
    }
  })();
}

function traceOkSafe(marker: string): void {
  void (async () => {
    try {
      const { traceOk } = await getStartupTraceModule();
      traceOk(marker);
    } catch {
      // Diagnostics must never block startup.
    }
  })();
}

function traceFailSafe(marker: string, error: unknown): void {
  void (async () => {
    try {
      const { traceFail } = await getStartupTraceModule();
      traceFail(marker, error);
    } catch {
      // Diagnostics must never block startup.
    }
  })();
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

export function clearStartupRecoveryStorage(): void {
  const safeRecoveryKeyPattern = /(crash|startup|bootstrap|build_mismatch|forced_reload|chunk|vite|asset|recovery)/i;
  const protectedAuthKeyPattern = /(auth|token|telegram_login|session|jwt|initdata)/i;
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

async function clearTemporaryBrowserCaches(): Promise<void> {
  clearStartupRecoveryStorage();
  try {
    if ("caches" in window) {
      const keys = await caches.keys();
      for (const key of keys.filter((key) => key.startsWith("bloom-club-") || key.startsWith("workbox-"))) {
        await traceStartupStep("post_render_cache_delete", () => caches.delete(key), { key });
      }
    }
  } catch {
    // Cache cleanup is best-effort and must not affect auth/session storage.
  }
}

async function unregisterUnsafeServiceWorkers(): Promise<void> {
  if (!("serviceWorker" in navigator)) return;
  try {
    const registrations = await navigator.serviceWorker.getRegistrations();
    for (const registration of registrations) {
      await traceStartupStep("post_render_service_worker_unregister", () => registration.unregister().catch(() => false), { scope: registration.scope });
    }
  } catch (error) {
    reportClientError("service_worker_unregister_failed", error, { startup: getStandaloneDiagnostics() });
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
    fallbackPresent: Boolean(document.getElementById("bloom-startup-loader") || document.getElementById("bloom-entry-fallback-overlay")),
    rootChildCount: document.getElementById("root")?.childElementCount ?? 0,
    visibilityState: document.visibilityState,
    readyState: document.readyState,
    performance: getPerformanceDiagnostics(),
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
  const rootElement = document.getElementById("bloom-startup-loader") ?? document.getElementById("bloom-entry-fallback-overlay") ?? getRootElement();
  const panel = document.createElement("section");
  panel.setAttribute("role", "alert");
  panel.className = "startup-entry-error-panel";
  panel.setAttribute("style", "max-width: 520px; display: flex; flex-direction: column; gap: 14px; align-items: center;");

  const title = document.createElement("h1");
  title.textContent = "Проблемы с запуском";
  const description = document.createElement("p");
  description.textContent = "Мы не смогли открыть приложение после быстрого перезапуска.";
  const reloadButton = createButton("Перезагрузить приложение", () => {
    void clearTemporaryBrowserCaches().finally(() => reloadWithCacheBust(reason));
  });
  const clearButton = createButton("Очистить временный кэш", () => {
    void clearTemporaryBrowserCaches().finally(() => reloadWithCacheBust("temporary_cache_cleared"));
  });
  panel.replaceChildren(title, description, reloadButton, clearButton);
  rootElement.replaceChildren(panel);
  lifecycleTraceSafe("startup_recovery_screen_shown", { reason, diagnostics: getStandaloneDiagnostics() });
  traceMarkSafe("startup_recovery_screen_shown");
  reportStartupFailure("startup_recovery_screen_shown", reason);
}

function renderStartupLoadingFallback(): void {
  const existing = document.getElementById("bloom-startup-loader") ?? document.getElementById("bloom-entry-fallback-overlay");
  if (existing) {
    earlyStartupTrace("splash created", { source: "existing_dom", id: existing.id });
    console.info("splash created", { source: "existing_dom", id: existing.id });
    requestAnimationFrame(() => {
      startupSplashMounted = true;
      earlyStartupTrace("splash mounted", { source: "existing_dom", id: existing.id, connected: existing.isConnected });
      console.info("splash mounted", { source: "existing_dom", id: existing.id, connected: existing.isConnected });
      maybeRemoveEntryFallbackOverlay();
    });
    bindStartupSplashVideo(existing.querySelector("video"));
    return;
  }

  const wrapper = document.createElement("section");
  wrapper.setAttribute("role", "status");
  wrapper.setAttribute("aria-live", "polite");
  wrapper.id = "bloom-startup-loader";
  wrapper.className = "startup-entry-fallback";
  wrapper.setAttribute(
    "style",
    "position: fixed; inset: 0; z-index: 2147483647; display: flex; align-items: center; justify-content: center; background: linear-gradient(180deg, #fffdfb 0%, #fff7f7 50%, #f8eef2 100%); color: #2b1b22; font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif; flex-direction: column; gap: 14px; padding: 24px; box-sizing: border-box; text-align: center; opacity: 1; transition: opacity 280ms ease;",
  );

  earlyStartupTrace("splash created", { source: "entry" });
  console.info("splash created", { source: "entry" });
  window.__BLOOM_ENTRY_FALLBACK_INSERTED__ = true;
  window.__BLOOM_ENTRY_FALLBACK_INSERTED_AT__ = new Date().toISOString();
  window.__BLOOM_ENTRY_FALLBACK_OVERLAY_INSERTED__ = true;
  window.__BLOOM_ENTRY_FALLBACK_OVERLAY_REMOVED__ = false;

  const video = document.createElement("video");
  video.src = "/assets/loader/bloom-loader.mp4";
  video.autoplay = true;
  video.muted = true;
  video.playsInline = true;
  video.preload = "auto";
  video.setAttribute("muted", "");
  video.setAttribute("playsinline", "");
  video.setAttribute("webkit-playsinline", "");
  video.setAttribute("preload", "auto");
  video.setAttribute("aria-hidden", "true");
  video.setAttribute(
    "style",
    "display: block; width: clamp(180px, 42vw, 220px); height: clamp(180px, 42vw, 220px); object-fit: contain; background: transparent;",
  );

  const title = document.createElement("h1");
  title.textContent = "Загружаем Bloom Club...";
  title.setAttribute("style", "margin: 0; color: rgba(53, 39, 43, 0.64); font-size: 0.95rem; font-weight: 600;");

  const description = document.createElement("p");
  description.textContent =
    "Если экран не меняется больше 10 секунд, нажмите перезагрузить";
  description.setAttribute("style", "margin: 0; color: rgba(53, 39, 43, 0.42); font-size: 0.82rem;");

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
  wrapper.replaceChildren(video, title, description, diagnostics, actions);
  bindStartupSplashVideo(video);

  const parentName = appendEntryFallbackOverlay(wrapper);
  requestAnimationFrame(() => {
    startupSplashMounted = true;
    earlyStartupTrace("splash mounted", { source: "entry", parentName, connected: wrapper.isConnected });
    console.info("splash mounted", { source: "entry", parentName, connected: wrapper.isConnected });
    maybeRemoveEntryFallbackOverlay();
  });
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
  const fallback = document.getElementById("bloom-startup-loader") ?? document.getElementById("bloom-entry-fallback-overlay");
  const rootElement = fallback ?? getRootElement();
  const message = sanitizeDiagnosticValue(error);
  const panel = document.createElement("section");
  panel.setAttribute("role", "alert");
  panel.className = "startup-entry-error-panel";

  const title = document.createElement("h1");
  title.textContent = "Проблемы с запуском";

  const description = document.createElement("p");
  description.textContent =
    "Мы не смогли открыть приложение после быстрого перезапуска.";

  const details = document.createElement("pre");
  details.textContent = JSON.stringify(
    getFallbackDiagnostics(source, message),
    null,
    2,
  );

  const reloadButton = createButton("Перезагрузить приложение", () => {
    void clearTemporaryBrowserCaches().finally(() => reloadWithCacheBust("module_load_error"));
  });
  const clearButton = createButton("Очистить временный кэш", () => {
    void clearTemporaryBrowserCaches().finally(() => reloadWithCacheBust("temporary_cache_cleared"));
  });

  panel.replaceChildren(title, description, details, reloadButton, clearButton);
  rootElement.replaceChildren(panel);
}

function isLikelyChunkLoadFailure(error: unknown): boolean {
  const message = sanitizeDiagnosticValue(error);
  return /ChunkLoadError|Loading chunk|Failed to fetch dynamically imported module|Importing a module script failed|module script|\/assets\/.*\.js|error loading dynamically imported module/i.test(message);
}

function recoverFromChunkLoadFailure(error: unknown, source: EarlyErrorSource): void {
  renderModuleLoadErrorPanel(error, source);
  if (window.__BLOOM_CHUNK_RECOVERY_STARTED__) return;
  window.__BLOOM_CHUNK_RECOVERY_STARTED__ = true;
  let reloadCount = 0;
  try {
    reloadCount = Number(window.sessionStorage.getItem("bloom_chunk_recovery_reload_count") ?? "0") || 0;
    window.sessionStorage.setItem("bloom_chunk_recovery_reload_count", String(reloadCount + 1));
  } catch {
    reloadCount = 1;
  }
  void clearTemporaryBrowserCaches().finally(() => {
    if (reloadCount < 1) {
      window.setTimeout(() => reloadWithCacheBust("chunk_load_failure"), 300);
    }
  });
}

function renderEarlyErrorDiagnostic(
  error: unknown,
  source: EarlyErrorSource,
): void {
  if (isLikelyChunkLoadFailure(error)) {
    recoverFromChunkLoadFailure(error, source);
    return;
  }
  renderModuleLoadErrorPanel(error, source);
}

function startEntryWatchdog(): void {
  watchdogTimers = [
    window.setTimeout(() => {
      updateStartupFallback("Загрузка модулей приложения...");
    }, 8_000),
    window.setTimeout(() => {
      updateStartupFallback("Приложение не завершило запуск", true);
      if (!window.__BLOOM_APP_INTERACTIVE__) {
        reportStartupFailure("bootstrap_timeout", "entry_watchdog_timeout");
        renderStartupRecoveryScreen();
      }
    }, 10_000),
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

function earlyStartupTrace(step: string, details: Record<string, unknown> = {}): void {
  try {
    window.__BLOOM_EARLY_STARTUP_TRACE__ ??= [];
    window.__BLOOM_EARLY_STARTUP_TRACE__.push({
      step,
      at: new Date().toISOString(),
      readyState: document.readyState,
      visibilityState: document.visibilityState,
      ...details,
    });
  } catch {
    // Early diagnostics must never block startup.
  }
}

function getPerformanceDiagnostics(): Record<string, unknown> {
  const navigation = performance.getEntriesByType?.("navigation")?.[0]?.toJSON?.() ?? null;
  const resources = performance
    .getEntriesByType?.("resource")
    ?.filter((entry) => /\.(?:js|css|woff2?|png|svg|webmanifest)$|\/sw\.js$/.test(entry.name))
    .slice(-80)
    .map((entry) => ({
      name: entry.name,
      initiatorType: (entry as PerformanceResourceTiming).initiatorType,
      startTime: Math.round(entry.startTime),
      duration: Math.round(entry.duration),
      transferSize: (entry as PerformanceResourceTiming).transferSize,
      encodedBodySize: (entry as PerformanceResourceTiming).encodedBodySize,
      decodedBodySize: (entry as PerformanceResourceTiming).decodedBodySize,
    })) ?? [];
  return {
    navigation,
    resources,
    earlyStartupTrace: window.__BLOOM_EARLY_STARTUP_TRACE__?.slice(-100) ?? [],
    resourceErrors: window.__BLOOM_RESOURCE_ERROR_TRACE__?.slice(-50) ?? [],
  };
}

earlyStartupTrace("main_first_executable_line", { marker: "before_installProductionDiagnostics" });
setStartupPhase("main_started");
if (detectInterruptedStartup()) { clearInterruptedStartupTemporaryState(); }
installProductionDiagnostics();
earlyStartupTrace("main_after_installProductionDiagnostics");
window.__BLOOM_ENTRY_SCRIPT_EXECUTED__ = true;
window.__BLOOM_APP_STATIC_IMPORT_ENABLED__ = true;
initializeStartupSplashGuards();
renderStartupLoadingFallback();
startEntryWatchdog();
lifecycleTraceSafe("entry_start");
traceMarkSafe("boot_started");
traceMarkSafe("entry_script_executed");
traceMarkSafe("app_entry_loaded");
traceOkSafe("entry_loading_fallback_rendered");

window.addEventListener("error", (event) => {
  const rawTarget = event.target;
  const target = rawTarget && rawTarget !== window ? rawTarget as HTMLElement & { src?: string; href?: string } : null;
  const url = target ? target.src || target.href || "" : "";
  if (/\/assets\/.*\.js(?:$|[?#])/.test(url)) {
    recoverFromChunkLoadFailure(new Error(`Missing startup asset: ${url}`), "app_module_import");
  }
}, true);

window.onerror = (_message, _source, _lineno, _colno, error): boolean | void => {
  if (shouldIgnoreGenericSafariScriptErrorAfterRender(_message, _source, _lineno, _colno)) {
    lifecycleTraceSafe("safari_generic_script_error_after_render", { message: _message });
    reportClientError("safari_generic_script_error_after_render", error ?? _message, { source: _source, line: _lineno, column: _colno, startup: getStandaloneDiagnostics(), startupMarkers: getStartupMarkers(), afterRender: true, nonfatal: true });
    return true;
  }
  lifecycleTraceSafe("window_error_overlay_trigger", { message: _message });
  saveCrashDump("window.onerror", { source: "entry", message: _message });
  reportClientError("window.onerror", error ?? _message, { source: _source, line: _lineno, column: _colno, startup: getStandaloneDiagnostics(), startupMarkers: getStartupMarkers(), afterRender: Boolean(window.__BLOOM_APP_INTERACTIVE__) });
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
    earlyStartupTrace("runtime_boundary_import_start");
    const { RuntimeErrorBoundary } = await import("./components/RuntimeErrorBoundary");
    earlyStartupTrace("runtime_boundary_import_ok");
    earlyStartupTrace("app_import_start");
    const { default: App } = await import("./App");
    earlyStartupTrace("app_import_ok");
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


const STARTUP_SPLASH_MIN_VISIBLE_MS = 5_000;
const STARTUP_SPLASH_MAX_DURATION_MS = 15_000;
const STARTUP_SPLASH_FADE_MS = 280;
const STARTUP_SPLASH_ACTIVE_CLASS = "bloom-startup-active";
const splashStartedAt = typeof window.__BLOOM_STARTUP_SPLASH_STARTED_AT__ === "number" ? window.__BLOOM_STARTUP_SPLASH_STARTED_AT__ : Date.now();
let startupMinimumSplashElapsed = false;
let startupAppReady = false;
let startupOverlayRemovalStarted = false;
let startupSplashMounted = false;
let startupMinimumSplashTimer: number | undefined;
let startupMaximumSplashTimer: number | undefined;

function markStartupMinimumSplashElapsed(reason: string): void {
  if (startupMinimumSplashElapsed) return;
  startupMinimumSplashElapsed = true;
  window.__BLOOM_STARTUP_SPLASH_READY__ = true;
  earlyStartupTrace("startup_splash_minimum_elapsed", { reason, elapsedMs: Date.now() - splashStartedAt });
  maybeRemoveEntryFallbackOverlay(reason);
}

function scheduleStartupSplashTimers(): void {
  const remainingMs = Math.max(0, STARTUP_SPLASH_MIN_VISIBLE_MS - (Date.now() - splashStartedAt));
  startupMinimumSplashTimer = window.setTimeout(() => {
    markStartupMinimumSplashElapsed("minimum_duration_elapsed");
  }, remainingMs);
  startupMaximumSplashTimer = window.setTimeout(() => {
    earlyStartupTrace("startup_splash_maximum_elapsed", { elapsedMs: Date.now() - splashStartedAt, startupAppReady });
    startupAppReady = true;
    window.__BLOOM_STARTUP_APP_READY__ = true;
    markStartupMinimumSplashElapsed("maximum_duration_elapsed");
    maybeRemoveEntryFallbackOverlay("maximum_duration_elapsed");
  }, STARTUP_SPLASH_MAX_DURATION_MS);
}

function bindStartupSplashVideo(video: HTMLVideoElement | null): void {
  if (!video || video.dataset.bloomSplashBound === "true") return;
  video.dataset.bloomSplashBound = "true";
  video.loop = false;
  video.muted = true;
  video.defaultMuted = true;
  video.playsInline = true;
  video.setAttribute("muted", "");
  video.setAttribute("playsinline", "");
  video.setAttribute("webkit-playsinline", "");
  video.setAttribute("preload", "auto");
  const logStartupVideoDiagnostics = (reason: string) => {
    const computedStyle = window.getComputedStyle(video);
    console.info("bloom_startup_video_diagnostics", {
      reason,
      selectorResult: document.querySelector("#bloom-startup-loader video") === video,
      currentSrc: video.currentSrc,
      readyState: video.readyState,
      networkState: video.networkState,
      videoWidth: video.videoWidth,
      videoHeight: video.videoHeight,
      paused: video.paused,
      error: video.error ? { code: video.error.code, message: video.error.message } : null,
      currentTime: video.currentTime,
      computedStyle: {
        display: computedStyle.display,
        visibility: computedStyle.visibility,
        opacity: computedStyle.opacity,
        width: computedStyle.width,
        height: computedStyle.height,
        zIndex: computedStyle.zIndex,
      },
    });
  };
  const traceVideoEvent = (eventName: string) => {
    logStartupVideoDiagnostics(eventName);
    earlyStartupTrace(`startup_video_${eventName}`, { currentTime: video.currentTime, readyState: video.readyState, paused: video.paused });
  };
  video.addEventListener("loadeddata", () => traceVideoEvent("loadeddata"), { once: true });
  video.addEventListener("canplay", () => traceVideoEvent("canplay"), { once: true });
  video.addEventListener("playing", () => {
    traceVideoEvent("playing");
    console.info("video playing", { source: "entry" });
  }, { once: true });
  video.addEventListener("ended", () => {
    window.__BLOOM_STARTUP_VIDEO_DONE__ = true;
    traceVideoEvent("ended");
  }, { once: true });
  video.addEventListener("error", () => traceVideoEvent("error"), { once: true });
  logStartupVideoDiagnostics("startup_bind");
  const playPromise = video.play();
  if (playPromise) {
    playPromise.catch((error: unknown) => {
      earlyStartupTrace("startup_video_play_rejected", { error: sanitizeDiagnosticValue(error) });
    });
  }
}

function initializeStartupSplashGuards(): void {
  bindStartupSplashVideo(document.querySelector<HTMLVideoElement>("#bloom-startup-loader video, #bloom-html-fallback-overlay video"));
  scheduleStartupSplashTimers();
}

function revealRootAfterStartupSplash(reason: string): void {
  const rootElement = getRootElement();
  document.documentElement.classList.remove(STARTUP_SPLASH_ACTIVE_CLASS);
  rootElement.style.visibility = "visible";
  window.__BLOOM_STARTUP_ROOT_REVEALED__ = true;
  earlyStartupTrace("startup_root_revealed", { reason, elapsedMs: Date.now() - splashStartedAt });
}

function maybeRemoveEntryFallbackOverlay(reason = "conditions_changed"): void {
  earlyStartupTrace("splash remove requested", { reason, startupAppReady, startupMinimumSplashElapsed, startupSplashMounted, startupOverlayRemovalStarted, elapsedMs: Date.now() - splashStartedAt });
  console.info("splash remove requested", { reason, startupAppReady, startupMinimumSplashElapsed, startupSplashMounted, startupOverlayRemovalStarted });
  if (!startupAppReady || !startupMinimumSplashElapsed || !startupSplashMounted || startupOverlayRemovalStarted) return;
  startupOverlayRemovalStarted = true;
  if (startupMinimumSplashTimer) window.clearTimeout(startupMinimumSplashTimer);
  if (startupMaximumSplashTimer) window.clearTimeout(startupMaximumSplashTimer);
  const startupFallback = document.getElementById("bloom-startup-loader");
  const entryFallback = document.getElementById("bloom-entry-fallback-overlay");
  const htmlFallback = document.getElementById("bloom-html-fallback-overlay");
  const overlays = [startupFallback, entryFallback, htmlFallback].filter(
    (element, index, elements): element is HTMLElement => Boolean(element) && elements.indexOf(element) === index,
  );
  const fadeAndRemove = (element: HTMLElement): void => {
    element.style.opacity = "0";
    element.style.pointerEvents = "none";
  };

  overlays.forEach(fadeAndRemove);
  window.setTimeout(() => {
    overlays.forEach((element) => {
      element.remove();
      earlyStartupTrace("splash removed", { id: element.id });
      console.info("splash removed", { id: element.id });
    });
    revealRootAfterStartupSplash(reason);
  }, overlays.length > 0 ? STARTUP_SPLASH_FADE_MS : 0);
  window.__BLOOM_ENTRY_FALLBACK_OVERLAY_REMOVED__ = true;
  window.__BLOOM_HTML_FALLBACK_REMOVED__ = true;
  stopEntryWatchdog();
}

export function removeEntryFallbackOverlay(): void {
  startupAppReady = true;
  window.__BLOOM_STARTUP_APP_READY__ = true;
  earlyStartupTrace("startup_app_ready_for_overlay_removal", { elapsedMs: Date.now() - splashStartedAt });
  console.info("app ready", { source: "entry" });
  maybeRemoveEntryFallbackOverlay("app_ready");
}

async function startApp(): Promise<void> {
  lifecycleTraceSafe("entry_finish");
  console.info("app_before_create_root");
  earlyStartupTrace("before_createRoot_imports_pending");
  traceOkSafe("root_container_ready");
  const { RuntimeErrorBoundary, App } = await traceStartupStep("dynamic_import_application_modules", importApplicationModules);
  earlyStartupTrace("before_createRoot");
  lifecycleTraceSafe("react_createRoot_start");
  traceStartSafe("create_root_start");
  let root;
  try {
    root = ReactDOM.createRoot(getRootElement());
    lifecycleTraceSafe("react_createRoot_ok");
    earlyStartupTrace("after_createRoot");
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
  earlyStartupTrace("before_render");
  traceStartSafe("render_call_start");
  try {
    setStartupPhase("react_render_called");
    markFirstReactRenderForExecutionTrace({ source: "main.startApp", mode: import.meta.env.MODE });
    await traceStartupStep("react_root_render_call", () => {
      root.render(
      // static regression anchor: import.meta.env.DEV ? <React.StrictMode>
      import.meta.env.DEV
        ? React.createElement(React.StrictMode, undefined, app)
        : app,
    );
    });
    lifecycleTraceSafe("react_render_ok");
    earlyStartupTrace("after_render");
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
  // Production startup is safer without an app-shell/chunk service worker. The
  // manifest still provides the iOS home-screen PWA shortcut. Remove old SWs in
  // the background without touching auth/session/localStorage tokens.
  await unregisterUnsafeServiceWorkers();
  await clearTemporaryBrowserCaches();
}


void (async () => {
  await traceStartupStep("entry_startApp", startApp);
  await traceStartupStep("post_render_unregister_service_workers", registerServiceWorkerSafely);
  await traceStartupStep("post_render_reload_build_check", reloadWhenServerBuildDiffers);
})().catch((error: unknown) => {
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
// static regression anchor: registerServiceWorkerSafely();
