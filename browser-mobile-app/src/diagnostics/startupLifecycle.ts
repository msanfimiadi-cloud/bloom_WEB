import { appBuildInfo } from "../buildInfo";

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

export function setStartupPhase(phase: StartupPhase, extra: Record<string, unknown> = {}): void {
  if (typeof window === "undefined") return;
  const marker = { phase, timestamp: now(), buildId: buildId(), ...extra };
  window.__BLOOM_STARTUP_PHASE__ = phase;
  try { window.sessionStorage.setItem(IN_PROGRESS_KEY, JSON.stringify(marker)); } catch { /* storage is best effort */ }
}

export function markFirstVisiblePaint(): void {
  if (typeof window === "undefined") return;
  const marker = { phase: "first_visible_paint", timestamp: now(), buildId: buildId() };
  window.__BLOOM_STARTUP_PHASE__ = "first_visible_paint";
  try {
    window.sessionStorage.setItem(COMPLETED_KEY, JSON.stringify(marker));
    window.localStorage.setItem(COMPLETED_KEY, JSON.stringify(marker));
    window.sessionStorage.removeItem(INTERRUPTED_KEY);
  } catch { /* storage is best effort */ }
}

export function markBootstrapFinished(): void { setStartupPhase("bootstrap_finished"); }

export function detectInterruptedStartup(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const inProgress = safeParse(window.sessionStorage.getItem(IN_PROGRESS_KEY) || window.localStorage.getItem(IN_PROGRESS_KEY));
    const completed = safeParse(window.sessionStorage.getItem(COMPLETED_KEY) || window.localStorage.getItem(COMPLETED_KEY));
    if (!inProgress || inProgress.buildId !== buildId()) return false;
    if (completed?.buildId === buildId() && typeof completed.timestamp === "number" && Number(completed.timestamp) >= Number(inProgress.timestamp || 0)) return false;
    const stale = typeof inProgress.timestamp === "number" && now() - Number(inProgress.timestamp) > STALE_MS;
    return !completed || stale || completed.buildId !== inProgress.buildId;
  } catch { return false; }
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
