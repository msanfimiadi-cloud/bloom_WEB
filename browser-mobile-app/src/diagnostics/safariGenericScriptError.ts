export interface SafariGenericScriptErrorLike {
  message?: unknown;
  filename?: unknown;
  lineno?: unknown;
  colno?: unknown;
}

export function hasReachedFirstVisiblePaint(): boolean {
  if (typeof window === "undefined") return false;
  return (
    window.__BLOOM_APP_INTERACTIVE__ === true ||
    window.__BLOOM_STARTUP_PHASE__ === "first_visible_paint" ||
    window.__BLOOM_STARTUP_PHASE__ === "bootstrap_finished"
  );
}

export function isGenericSafariScriptError(
  message: unknown,
  filename: unknown,
  line: unknown,
  column: unknown,
): boolean {
  return (
    message === "Script error." &&
    (filename === "" || filename === undefined || filename === null) &&
    Number(line ?? 0) === 0 &&
    Number(column ?? 0) === 0
  );
}

export function isGenericSafariScriptErrorEvent(event: SafariGenericScriptErrorLike): boolean {
  return isGenericSafariScriptError(
    event.message,
    event.filename,
    event.lineno,
    event.colno,
  );
}

export function shouldIgnoreGenericSafariScriptErrorAfterRender(
  message: unknown,
  filename: unknown,
  line: unknown,
  column: unknown,
): boolean {
  return isGenericSafariScriptError(message, filename, line, column) && hasReachedFirstVisiblePaint();
}
