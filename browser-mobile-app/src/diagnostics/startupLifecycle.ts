import { appBuildInfo } from "../buildInfo";
import { traceStartup } from "./startupTrace";

export type StartupPhase = "html_loaded" | "main_started" | "react_render_called" | "app_mounted" | "first_visible_paint" | "bootstrap_started" | "bootstrap_finished";

const IN_PROGRESS_KEY = "bloom_startup_in_progress";
const COMPLETED_KEY = "bloom_startup_completed";
const INTERRUPTED_KEY = "bloom_startup_interrupted";
const STALE_MS = 60_000;
const protectedAuthKeyPattern = /(auth|token|telegram_login|session|jwt|initdata)/i;
const temporaryStartupKeyPattern = /(startup|bootstrap|crash|recovery|build_mismatch|forced_reload|chunk|vite|asset|catalog_recovery)/i;

function now(): number { return Date.now(); }
function safeParse(raw: string | null): Record<string, unknown> | null { try { return raw ? JSON.parse(raw) as Record<string, unknown> : null; } catch { return null; } }
function buildId(): string { return appBuildInfo.buildHash || appBuildInfo.buildVersion || "unknown-build"; }

function getStartupLifecycleTraceContext(): Record<string, unknown> {
  if (typeof window === "undefined") return { startupPhase: undefined, inProgressTimestamp: undefined, completedTimestamp: undefined };
  try {
    const inProgress = safeParse(window.sessionStorage.getItem(IN_PROGRESS_KEY) || window.localStorage.getItem(IN_PROGRESS_KEY));
    const completed = safeParse(window.sessionStorage.getItem(COMPLETED_KEY) || window.localStorage.getItem(COMPLETED_KEY));
    return {
      startupPhase: window.__BLOOM_STARTUP_PHASE__,
      inProgressTimestamp: inProgress?.timestamp,
      completedTimestamp: completed?.timestamp,
      inProgressBuildId: inProgress?.buildId,
      completedBuildId: completed?.buildId,
    };
  } catch {
    return { startupPhase: window.__BLOOM_STARTUP_PHASE__, inProgressTimestamp: undefined, completedTimestamp: undefined, markerReadError: true };
  }
}

function traceStartupLifecycleFunction(event: string, payload: Record<string, unknown> = {}): void {
  traceStartup(`startup_lifecycle:${event}`, {
    ...getStartupLifecycleTraceContext(),
    ...payload,
  });
}

export function setStartupPhase(phase: StartupPhase, extra: Record<string, unknown> = {}): void {
  traceStartupLifecycleFunction("setStartupPhase:enter", { nextPhase: phase, extra });
  if (typeof window === "undefined") {
    traceStartupLifecycleFunction("setStartupPhase:exit", { nextPhase: phase, returnValue: undefined, skipped: "window_undefined" });
    return;
  }
  const marker = { phase, timestamp: now(), buildId: buildId(), ...extra };
  window.__BLOOM_STARTUP_PHASE__ = phase;
  try { window.sessionStorage.setItem(IN_PROGRESS_KEY, JSON.stringify(marker)); } catch { /* storage is best effort */ }
  traceStartupLifecycleFunction("setStartupPhase:exit", { nextPhase: phase, returnValue: undefined, markerTimestamp: marker.timestamp });
}

export function markFirstVisiblePaint(): void {
  traceStartupLifecycleFunction("markFirstVisiblePaint:enter");
  if (typeof window === "undefined") {
    traceStartupLifecycleFunction("markFirstVisiblePaint:exit", { returnValue: undefined, skipped: "window_undefined" });
    return;
  }
  const marker = { phase: "first_visible_paint", timestamp: now(), buildId: buildId() };
  window.__BLOOM_STARTUP_PHASE__ = "first_visible_paint";
  try {
    window.sessionStorage.setItem(COMPLETED_KEY, JSON.stringify(marker));
    window.localStorage.setItem(COMPLETED_KEY, JSON.stringify(marker));
    window.sessionStorage.removeItem(INTERRUPTED_KEY);
  } catch { /* storage is best effort */ }
  traceStartupLifecycleFunction("markFirstVisiblePaint:exit", { returnValue: undefined, markerTimestamp: marker.timestamp });
}

export function markBootstrapFinished(): void {
  traceStartupLifecycleFunction("markBootstrapFinished:enter");
  const returnValue = setStartupPhase("bootstrap_finished");
  traceStartupLifecycleFunction("markBootstrapFinished:exit", { returnValue });
  return returnValue;
}

export function detectInterruptedStartup(): boolean {
  traceStartupLifecycleFunction("detectInterruptedStartup:enter");
  if (typeof window === "undefined") {
    traceStartupLifecycleFunction("detectInterruptedStartup:exit", { returnValue: false, decisionReason: "window_undefined" });
    return false;
  }
  try {
    const inProgress = safeParse(window.sessionStorage.getItem(IN_PROGRESS_KEY) || window.localStorage.getItem(IN_PROGRESS_KEY));
    const completed = safeParse(window.sessionStorage.getItem(COMPLETED_KEY) || window.localStorage.getItem(COMPLETED_KEY));
    const currentBuildId = buildId();
    if (!inProgress) {
      traceStartupLifecycleFunction("detectInterruptedStartup:exit", { returnValue: false, decisionReason: "missing_in_progress_marker" });
      return false;
    }
    if (inProgress.buildId !== currentBuildId) {
      traceStartupLifecycleFunction("detectInterruptedStartup:exit", { returnValue: false, decisionReason: "in_progress_build_mismatch", currentBuildId });
      return false;
    }
    if (completed?.buildId === currentBuildId && typeof completed.timestamp === "number" && Number(completed.timestamp) >= Number(inProgress.timestamp || 0)) {
      traceStartupLifecycleFunction("detectInterruptedStartup:exit", { returnValue: false, decisionReason: "completed_marker_is_current", currentBuildId });
      return false;
    }
    const stale = typeof inProgress.timestamp === "number" && now() - Number(inProgress.timestamp) > STALE_MS;
    const returnValue = !completed || stale || completed.buildId !== inProgress.buildId;
    traceStartupLifecycleFunction("detectInterruptedStartup:exit", {
      returnValue,
      decisionReason: returnValue
        ? (!completed ? "missing_completed_marker" : stale ? "in_progress_marker_stale" : "completed_build_mismatch")
        : "not_interrupted",
      stale,
      currentBuildId,
    });
    return returnValue;
  } catch (caughtError) {
    traceStartupLifecycleFunction("detectInterruptedStartup:exit", { returnValue: false, decisionReason: "exception", error: caughtError });
    return false;
  }
}

export function clearInterruptedStartupTemporaryState(): void {
  if (typeof window === "undefined") return;
  try {
    [window.sessionStorage, window.localStorage].forEach((storage) => {
      Object.keys(storage).forEach((key) => {
        if (temporaryStartupKeyPattern.test(key) && !protectedAuthKeyPattern.test(key)) storage.removeItem(key);
      });
    });
    window.sessionStorage.setItem(INTERRUPTED_KEY, JSON.stringify({ timestamp: now(), buildId: buildId(), action: "temporary_state_cleaned" }));
  } catch { /* recovery must not break startup */ }
}

export function markStartupInterrupted(reason: string): void {
  if (typeof window === "undefined") return;
  try { window.sessionStorage.setItem(INTERRUPTED_KEY, JSON.stringify({ timestamp: now(), buildId: buildId(), reason })); } catch { /* noop */ }
}

export function getStartupMarkers(): Record<string, unknown> {
  if (typeof window === "undefined") return {};
  return { phase: window.__BLOOM_STARTUP_PHASE__, inProgress: safeParse(window.sessionStorage.getItem(IN_PROGRESS_KEY)), completed: safeParse(window.sessionStorage.getItem(COMPLETED_KEY)), interrupted: safeParse(window.sessionStorage.getItem(INTERRUPTED_KEY)) };
}
