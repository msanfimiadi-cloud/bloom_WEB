export type StartupExecutionStatus = "begin" | "end" | "fail" | "skip";

type StartupExecutionEvent = {
  id: number;
  parentId: number | null;
  status: StartupExecutionStatus;
  label: string;
  ts: string;
  t: number;
  elapsedMs?: number;
  details?: unknown;
};

declare global {
  interface Window {
    __BLOOM_STARTUP_EXECUTION_TRACE__?: StartupExecutionEvent[];
    __BLOOM_STARTUP_EXECUTION_TRACE_STARTED_AT__?: number;
    __BLOOM_STARTUP_EXECUTION_TRACE_LAST_ID__?: number;
    __BLOOM_STARTUP_EXECUTION_TRACE_STACK__?: number[];
  }
}

const FIRST_RENDER_WINDOW_MS = 5_000;

function now(): number {
  return typeof performance !== "undefined" ? performance.now() : Date.now();
}

function ensureStarted(): number {
  if (typeof window === "undefined") return now();
  window.__BLOOM_STARTUP_EXECUTION_TRACE_STARTED_AT__ ??= now();
  window.__BLOOM_STARTUP_EXECUTION_TRACE__ ??= [];
  window.__BLOOM_STARTUP_EXECUTION_TRACE_STACK__ ??= [];
  window.__BLOOM_STARTUP_EXECUTION_TRACE_LAST_ID__ ??= 0;
  return window.__BLOOM_STARTUP_EXECUTION_TRACE_STARTED_AT__;
}

function isWithinStartupWindow(): boolean {
  return now() - ensureStarted() <= FIRST_RENDER_WINDOW_MS;
}

function push(status: StartupExecutionStatus, label: string, id: number, startedAt?: number, details?: unknown): void {
  if (typeof window === "undefined" || !isWithinStartupWindow()) return;
  const event: StartupExecutionEvent = {
    id,
    parentId: (() => { const stack = window.__BLOOM_STARTUP_EXECUTION_TRACE_STACK__; return stack && stack.length > 0 ? stack[stack.length - 1] : null; })(),
    status,
    label,
    ts: new Date().toISOString(),
    t: Math.round(now() * 100) / 100,
    details,
  };
  if (typeof startedAt === "number") event.elapsedMs = Math.round((now() - startedAt) * 100) / 100;
  window.__BLOOM_STARTUP_EXECUTION_TRACE__?.push(event);
  console.info("startup_execution_trace", event);
}

export function markFirstReactRenderForExecutionTrace(details?: unknown): void {
  if (typeof window === "undefined") return;
  window.__BLOOM_STARTUP_EXECUTION_TRACE_STARTED_AT__ = now();
  window.__BLOOM_STARTUP_EXECUTION_TRACE__ = [];
  window.__BLOOM_STARTUP_EXECUTION_TRACE_STACK__ = [];
  window.__BLOOM_STARTUP_EXECUTION_TRACE_LAST_ID__ = 0;
  startupExecutionMark("first_react_render", details);
}

export function startupExecutionMark(label: string, details?: unknown): void {
  if (typeof window === "undefined" || !isWithinStartupWindow()) return;
  const id = (window.__BLOOM_STARTUP_EXECUTION_TRACE_LAST_ID__ ?? 0) + 1;
  window.__BLOOM_STARTUP_EXECUTION_TRACE_LAST_ID__ = id;
  push("end", label, id, undefined, details);
}

export function startupExecutionBegin(label: string, details?: unknown): { id: number; startedAt: number; label: string } | null {
  if (typeof window === "undefined" || !isWithinStartupWindow()) return null;
  const id = (window.__BLOOM_STARTUP_EXECUTION_TRACE_LAST_ID__ ?? 0) + 1;
  window.__BLOOM_STARTUP_EXECUTION_TRACE_LAST_ID__ = id;
  const startedAt = now();
  push("begin", label, id, undefined, details);
  window.__BLOOM_STARTUP_EXECUTION_TRACE_STACK__?.push(id);
  return { id, startedAt, label };
}

export function startupExecutionEnd(span: { id: number; startedAt: number; label: string } | null, details?: unknown): void {
  if (!span || typeof window === "undefined") return;
  const stack = window.__BLOOM_STARTUP_EXECUTION_TRACE_STACK__;
  if (stack && stack.length > 0 && stack[stack.length - 1] === span.id) stack.pop();
  push("end", span.label, span.id, span.startedAt, details);
}

export function startupExecutionFail(span: { id: number; startedAt: number; label: string } | null, error: unknown): void {
  if (!span || typeof window === "undefined") return;
  const stack = window.__BLOOM_STARTUP_EXECUTION_TRACE_STACK__;
  if (stack && stack.length > 0 && stack[stack.length - 1] === span.id) stack.pop();
  push("fail", span.label, span.id, span.startedAt, error);
}

export async function traceStartupStep<T>(label: string, fn: () => Promise<T> | T, details?: unknown): Promise<T> {
  const span = startupExecutionBegin(label, details);
  try {
    const value = await fn();
    startupExecutionEnd(span);
    return value;
  } catch (error) {
    startupExecutionFail(span, error);
    throw error;
  }
}
