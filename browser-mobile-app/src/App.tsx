import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  activateTrialSubscription,
  loginWithCode,
  createAcquiringPayment,
  getCities,
  getLinkingStatus,
  getReferralSummary,
  getGiveawayState,
  AUTH_STORAGE_KEY,
  clearStoredAuthToken,
  getPartnerOffersPath,
  getPartnerOffers,
  getPartners,
  getProfile,
  getAuthTokenStorageSnapshot,
  getStoredAuthToken,
  storeAuthTokenFromResponse,
  getSavings,
  getSubscription,
  getVerifications,
  isApiError,
  isCatalogLoadError,
  isTimeoutError,
  loginWithTelegram,
  resetTelegramLoginInFlight,
  TG_LOCAL_CATALOG_ENABLED,
  updateProfile,
  verifyPartnerOffer,
} from "./api/client";
import type { CatalogErrorDiagnostic } from "./api/client";
import type {
  ApiId,
  City,
  ClientProfile,
  ClientProfilePatch,
  Offer,
  Partner,
  PaymentRequest,
  LinkingStatus,
  ReferralSummary,
  GiveawayState,
  SavingsSummary,
  Subscription,
  Verification,
} from "./api/types";
import { AccountLinkingOnboarding } from "./components/AccountLinkingOnboarding";
import { AppShell } from "./components/AppShell";
import { ErrorState } from "./components/ErrorState";
import { LoadingState } from "./components/LoadingState";
import { DiagnosticOverlay } from "./components/DiagnosticOverlay";
import { CatalogPage } from "./pages/CatalogPage";
import { HomePage } from "./pages/HomePage";
import { PartnerPage } from "./pages/PartnerPage";
import { PrivilegesPage } from "./pages/PrivilegesPage";
import { ProfilePage } from "./pages/ProfilePage";
import { SavingsPage } from "./pages/SavingsPage";
import { SubscriptionPage } from "./pages/SubscriptionPage";
import { PaymentResultScreen } from "./components/PaymentResultScreen";
import { ContentProvider } from "./content/ContentContext";
import {
  createDiagnostic,
  createUnknownStateDiagnostic,
  type AppDiagnostic,
  type AppStage,
} from "./diagnostics";
import {
  lifecycleTrace,
  markReactMounted,
  setLifecyclePageId,
} from "./diagnostics/lifecycleTrace";
import {
  getStartupTrace,
  type StartupTraceEvent,
  traceFail,
  traceMark,
  traceOk,
  traceStart,
  traceStartup,
} from "./diagnostics/startupTrace";
import { catalogTrace, enableBloomDebug, isBloomDebugEnabled } from "./diagnostics/productionDebug";
import { clearCrashDump, markStartupCompletedSuccessfully, readCompatibleCrashDump, saveCrashDump, type BloomCrashDump } from "./diagnostics/crashDump";
import { clearInterruptedStartupTemporaryState, detectInterruptedStartup, getStartupMarkers, markBootstrapFinished, markFirstVisiblePaint, markStartupInterrupted, setStartupPhase } from "./diagnostics/startupLifecycle";
import { resolveNumericPartnerId, sortOffersForPartner, sortPartnersForCatalog } from "./utils/partnerDisplay";
import {
  getReferralCodeFromStartParam,
  getTelegramStartParam,
  getTelegramRuntimeDiagnostics,
  getTelegramLaunchPayload,
  getTelegramLaunchPayloadWithRetry,
  hasValidTelegramMiniAppInitData,
  isTelegramRuntime,
  getTelegramWebApp,
  prepareTelegramViewport,
} from "./telegram/webapp";
import { clearStaleAppState } from "./stateRecovery";
import { removeEntryFallbackOverlay } from "./main";
import { reportClientError } from "./diagnostics/clientErrorReporter";
import { startupExecutionBegin, startupExecutionEnd, startupExecutionFail, startupExecutionMark, traceStartupStep } from "./diagnostics/startupExecutionTrace";

export type PageId =
  | "home"
  | "catalog"
  | "partner"
  | "privileges"
  | "savings"
  | "profile"
  | "subscription"
  | "payment-result";
type AsyncStatus =
  | "idle"
  | "loading"
  | "success"
  | "empty"
  | "error"
  | "timeout";
type BootstrapReason = "initial" | "retry" | "manual" | "resume";
type AuthRestoreStatus = "unknown" | "restoring" | "authenticated" | "unauthenticated" | "invalid";

const BOOTSTRAP_HARD_TIMEOUT_MS = 9_000;

const RESUME_AUTH_DIAGNOSTICS_ENABLED =
  import.meta.env.DEV || import.meta.env.MODE === "test";

function traceResumeAuthDiagnostic(
  event: string,
  details: Record<string, unknown> = {},
): void {
  if (!RESUME_AUTH_DIAGNOSTICS_ENABLED) {
    return;
  }

  console.info("browser_app_resume_auth_diagnostic", { event, ...details });
}

function isAuthInvalidStatus(error: unknown): boolean {
  return isApiError(error) && (error.status === 401 || error.status === 403);
}

const CATALOG_CLOSED_DURING_LOAD_KEY = "bloom_catalog_closed_during_load";
const CATALOG_RECOVERY_MESSAGE = "Загрузка клуба была прервана. Нажмите, чтобы попробовать снова.";

const RETRYABLE_LOAD_ERROR_MESSAGE =
  "Проверьте интернет или VPN и попробуйте снова.";
const CONNECTION_PROBLEM_TITLE = "Проблемы с соединением";
const CONNECTION_PROBLEM_DESCRIPTION =
  "Проверьте интернет или VPN и попробуйте снова.";


const LEGAL_DOCUMENT_LINKS = {
  privacy: 'https://bloomclub.ru/privacy/',
  agreement: 'https://bloomclub.ru/terms/',
  personalDataConsent: 'https://bloomclub.ru/personal-data-consent/',
};

const BROWSER_LOGIN_REQUIRED_MESSAGE =
  "Добро пожаловать в Bloom Club";
const LOGIN_CODE_HELP_MESSAGE =
  "Введите код, который прислал Telegram или VK бот.";
const TELEGRAM_IN_APP_BROWSER_HOST = "app.bloomclub.ru";

const TELEGRAM_LOGIN_CODE_DRAFT_STORAGE_KEY = "bloom.telegramLoginCodeDraft";
const VK_LOGIN_CODE_DRAFT_STORAGE_KEY = "bloom.vkLoginCodeDraft";
const REFERRAL_CODE_DRAFT_STORAGE_KEY = "bloom.referralCodeDraft";
const GUEST_MODE_STORAGE_KEY = "bloom.browserGuestMode";
const TELEGRAM_BOT_LINK = import.meta.env.VITE_TELEGRAM_BOT_LINK || "";
const VK_BOT_LINK = import.meta.env.VITE_VK_BOT_LINK || "";

function hasStoredBrowserLoginDraft(): boolean {
  return Boolean(
    readLoginCodeDraft(TELEGRAM_LOGIN_CODE_DRAFT_STORAGE_KEY) ||
      readLoginCodeDraft(VK_LOGIN_CODE_DRAFT_STORAGE_KEY) ||
      readLoginCodeDraft(REFERRAL_CODE_DRAFT_STORAGE_KEY),
  );
}

function getLoginDraftStorage(): Storage | null {
  if (typeof window === "undefined") return null;

  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

function readLoginCodeDraft(key: string): string {
  try {
    return getLoginDraftStorage()?.getItem(key) ?? "";
  } catch {
    return "";
  }
}

function writeLoginCodeDraft(key: string, value: string): void {
  try {
    const storage = getLoginDraftStorage();
    if (!storage) return;

    if (value) {
      storage.setItem(key, value);
    } else {
      storage.removeItem(key);
    }
  } catch {
    // Storage can be unavailable in private mode or restricted embedded browsers.
  }
}

function clearLoginCodeDrafts(): void {
  writeLoginCodeDraft(TELEGRAM_LOGIN_CODE_DRAFT_STORAGE_KEY, "");
  writeLoginCodeDraft(VK_LOGIN_CODE_DRAFT_STORAGE_KEY, "");
  writeLoginCodeDraft(REFERRAL_CODE_DRAFT_STORAGE_KEY, "");
}

function readBrowserGuestMode(): boolean {
  try {
    return getLoginDraftStorage()?.getItem(GUEST_MODE_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

function writeBrowserGuestMode(enabled: boolean): void {
  try {
    const storage = getLoginDraftStorage();
    if (!storage) return;
    if (enabled) {
      storage.setItem(GUEST_MODE_STORAGE_KEY, "1");
    } else {
      storage.removeItem(GUEST_MODE_STORAGE_KEY);
    }
  } catch {
    // Storage can be unavailable in private mode or restricted embedded browsers.
  }
}


function getStartupRecoveryTraceContext(): Record<string, unknown> {
  const markers = getStartupMarkers();
  const inProgress = markers.inProgress as { timestamp?: unknown } | null | undefined;
  const completed = markers.completed as { timestamp?: unknown } | null | undefined;
  const launchPayload = getTelegramLaunchPayload();
  return {
    startupPhase: markers.phase,
    inProgressTimestamp: inProgress?.timestamp,
    completedTimestamp: completed?.timestamp,
    hasStoredAuthToken: Boolean(getStoredAuthToken()),
    hasTelegramPayload: Boolean(launchPayload),
    hasValidTelegramPayload: hasValidTelegramMiniAppInitData(launchPayload),
  };
}

function traceStartupRecovery(event: string, payload: Record<string, unknown> = {}): void {
  traceStartup(`startup_recovery:${event}`, {
    ...getStartupRecoveryTraceContext(),
    ...payload,
  });
}

function getBrowserPlatform(): string {
  if (typeof navigator === "undefined") return "";

  return String(navigator.userAgentData?.platform || navigator.platform || "");
}

function isDesktopBrowser(userAgent: string, platform: string): boolean {
  const normalizedUserAgent = userAgent.toLowerCase();
  const normalizedPlatform = platform.toLowerCase();

  return (
    /windows|win32|win64|macintosh|macintel|linux x86_64|x11|cros/.test(normalizedPlatform) ||
    /windows nt|macintosh|x11|cros|linux x86_64|telegramdesktop|telegram desktop/.test(normalizedUserAgent) ||
    (!/mobile|iphone|ipad|ipod|android|tablet/.test(normalizedUserAgent) &&
      /chrome|safari|edg|firefox/.test(normalizedUserAgent))
  );
}

function getBrowserLoginEnvironmentDiagnostics(browserLoginToken: string) {
  const userAgent = typeof navigator === "undefined" ? "" : navigator.userAgent || "";
  const platform = getBrowserPlatform();
  const hasTelegramWebApp = Boolean(getTelegramWebApp());
  const launchPayload = getTelegramLaunchPayload();
  const telegramDiagnostics = getTelegramRuntimeDiagnostics();
  const hasValidTelegramInitData = hasValidTelegramMiniAppInitData(launchPayload);
  const isIOS = /iphone|ipad|ipod/i.test(userAgent) || /iphone|ipad|ipod/i.test(platform);
  const isAndroid = /android/i.test(userAgent);
  const isDesktop = isDesktopBrowser(userAgent, platform);
  const isMobile = !isDesktop && (
    isIOS ||
    isAndroid ||
    /mobile|tablet/i.test(userAgent) ||
    (typeof navigator !== "undefined" && navigator.maxTouchPoints > 1 && /arm|aarch|mobile/i.test(platform))
  );
  const hasTelegramUserAgentEvidence = /telegram(?!desktop)|telegrambot|tgwebview/i.test(userAgent);
  const hasTelegramBridgeEvidence = Boolean(window.TelegramWebviewProxy || window.TelegramGameProxy);
  const hasTelegramMobileEvidence = hasTelegramUserAgentEvidence || hasTelegramBridgeEvidence;
  const isExternalIOSBrowser = isIOS && /safari/i.test(userAgent) && !hasTelegramUserAgentEvidence;
  const isExternalAndroidBrowser = isAndroid && /chrome|crios|firefox|edg|samsungbrowser/i.test(userAgent) && !hasTelegramUserAgentEvidence;
  const isTelegramInAppBrowser = (
    isMobile &&
    !isDesktop &&
    !isExternalIOSBrowser &&
    !isExternalAndroidBrowser &&
    hasTelegramMobileEvidence
  );
  const shouldShowExternalOpenRequired = (
    Boolean(browserLoginToken) &&
    window.location.host === TELEGRAM_IN_APP_BROWSER_HOST &&
    isMobile &&
    !isDesktop &&
    !hasValidTelegramInitData &&
    isTelegramInAppBrowser
  );

  return {
    userAgent,
    platform,
    isMobile,
    isIOS,
    isAndroid,
    isDesktop,
    hasTelegramWebApp,
    hasValidTelegramInitData,
    telegramLaunchPayloadLength: telegramDiagnostics.launchPayloadLength,
    isTelegramInAppBrowser,
    shouldShowExternalOpenRequired,
  };
}

function logBrowserLoginGuardDiagnostics(diagnostics: ReturnType<typeof getBrowserLoginEnvironmentDiagnostics>): void {
  if (!import.meta.env.DEV && !import.meta.env.TEST) return;

  console.info("browser_login_telegram_in_app_guard", diagnostics);
}

function shouldRequireExternalBrowserForTelegramInAppBrowser(browserLoginToken: string): boolean {
  if (typeof window === "undefined") return false;

  const diagnostics = getBrowserLoginEnvironmentDiagnostics(browserLoginToken);
  logBrowserLoginGuardDiagnostics(diagnostics);

  return diagnostics.shouldShowExternalOpenRequired;
}

function getBrowserLoginTokenFromUrl(): string {
  if (typeof window === "undefined") return "";

  const readFromParams = (text: string): string => {
    const normalized = text.startsWith("?") || text.startsWith("#") ? text.slice(1) : text;
    return (new URLSearchParams(normalized).get("t") || "").trim();
  };

  const readFromHash = (hash: string): string => {
    const normalized = hash.startsWith("#") ? hash.slice(1) : hash;
    const queryStart = normalized.indexOf("?");
    return readFromParams(normalized) || (queryStart >= 0 ? readFromParams(normalized.slice(queryStart)) : "");
  };

  return readFromParams(window.location.search) || readFromHash(window.location.hash);
}

const BROWSER_LOGIN_SUCCESS_PATH = "/";

function focusOpenModal(): void {
  if (typeof document === "undefined") return;

  const modal = document.querySelector<HTMLElement>(
    '[role="dialog"][aria-modal="true"], .modal, .lightbox, .linking-modal',
  );

  if (!modal) return;

  if (!modal.hasAttribute("tabindex")) {
    modal.setAttribute("tabindex", "-1");
  }

  modal.scrollIntoView({ block: "center", inline: "center" });
  modal.focus({ preventScroll: true });
}

function scrollAppToTop(): void {
  if (typeof window === "undefined") return;

  window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  document.documentElement.scrollTop = 0;
  document.body.scrollTop = 0;
}

function clearBrowserLoginTokenFromUrl(): void {
  if (typeof window === "undefined") return;

  window.history.replaceState(
    window.history.state,
    document.title,
    BROWSER_LOGIN_SUCCESS_PATH,
  );
}

function getBrowserLoginProfile(response: { user?: unknown; client?: unknown }): ClientProfile | null {
  const client = asObject(response.client as ClientProfile | null | undefined);
  return client ?? asObject(response.user as ClientProfile | null | undefined);
}

function getBrowserLoginSubscription(response: { subscription?: unknown }): Subscription | null {
  return asObject(response.subscription as Subscription | null | undefined);
}


function hasCatalogRecoveryFlag(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.sessionStorage.getItem(CATALOG_CLOSED_DURING_LOAD_KEY) === "true" ||
      window.localStorage.getItem(CATALOG_CLOSED_DURING_LOAD_KEY) === "true";
  } catch {
    return false;
  }
}

function setCatalogRecoveryFlag(): void {
  if (typeof window === "undefined") return;
  try { window.sessionStorage.setItem(CATALOG_CLOSED_DURING_LOAD_KEY, "true"); } catch { /* ignore */ }
  try { window.localStorage.setItem(CATALOG_CLOSED_DURING_LOAD_KEY, "true"); } catch { /* ignore */ }
  console.info("catalog_closed_during_load_flag_set", { key: CATALOG_CLOSED_DURING_LOAD_KEY });
  traceStartup("catalog_closed_during_load_flag_set", { key: CATALOG_CLOSED_DURING_LOAD_KEY });
}

function clearCatalogRecoveryFlag(): void {
  if (typeof window === "undefined") return;
  try { window.sessionStorage.removeItem(CATALOG_CLOSED_DURING_LOAD_KEY); } catch { /* ignore */ }
  try { window.localStorage.removeItem(CATALOG_CLOSED_DURING_LOAD_KEY); } catch { /* ignore */ }
}

function clearStartupRecoveryStorage(): void {
  const keyPattern = /(bootstrap|build|crash|startup|telegram_login|recovery|reload)/i;
  try {
    [window.sessionStorage, window.localStorage].forEach((storage) => {
      Object.keys(storage).forEach((key) => {
        if (keyPattern.test(key)) storage.removeItem(key);
      });
    });
  } catch {
    // Recovery must work even when storage is blocked.
  }
}

function restartAppAfterStartupFailure(): void {
  clearStartupRecoveryStorage();
  const url = new URL(window.location.href);
  url.searchParams.set("bloom_recovery", "app_watchdog");
  url.searchParams.set("bloom_recovery_ts", String(Date.now()));
  window.location.replace(url.toString());
}

function copyTextToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(text);
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();

  try {
    document.execCommand("copy");
    return Promise.resolve();
  } finally {
    document.body.removeChild(textarea);
  }
}

function BrowserLoginExternalOpenRequiredScreen(): React.ReactElement {
  const [copyStatus, setCopyStatus] = useState<"idle" | "success" | "error">("idle");

  const copyCurrentLink = async () => {
    try {
      await copyTextToClipboard(window.location.href);
      setCopyStatus("success");
    } catch {
      setCopyStatus("error");
    }
  };

  return (
    <main className="state" role="status">
      <h1>Откройте в браузере</h1>
      <p>Эта ссылка открылась внутри Telegram. Чтобы войти в Bloom Club, откройте её во внешнем браузере Safari/Chrome.</p>
      <p>Нажмите значок Safari/браузера внизу экрана или зажмите ссылку в чате и выберите «Открыть в браузере».</p>
      <button className="button button--primary" type="button" onClick={copyCurrentLink}>
        Скопировать ссылку
      </button>
      {copyStatus === "success" ? <p>Ссылка скопирована.</p> : null}
      {copyStatus === "error" ? <p>Не удалось скопировать ссылку автоматически. Скопируйте адрес из строки браузера.</p> : null}
    </main>
  );
}

function StartupRecoveryScreen({ message }: { message: string | null }): React.ReactElement {
  return (
    <main className="startup-recovery-screen" role="alert">
      <h1>{CONNECTION_PROBLEM_TITLE}</h1>
      <p>{message ?? CONNECTION_PROBLEM_DESCRIPTION}</p>
      <button className="button button--primary" type="button" onClick={restartAppAfterStartupFailure}>
        Повторить
      </button>
    </main>
  );
}


function SuccessfulBootstrapRecoveryScreen({ onReload }: { onReload: () => void }): React.ReactElement {
  return (
    <main className="startup-recovery-screen" role="alert">
      <h1>Восстанавливаем интерфейс</h1>
      <p>Вход выполнен и данные загружены, но экран приложения не отобразился. Нажмите кнопку, чтобы перезапустить интерфейс без выхода из аккаунта.</p>
      <button className="button button--primary" type="button" onClick={onReload}>
        Обновить экран
      </button>
    </main>
  );
}

function getLastLifecycleEventName(): string | null {
  if (typeof window === "undefined") return null;
  const events = window.__BLOOM_PAGE_LIFECYCLE__ ?? [];
  return events.length ? events[events.length - 1]?.event ?? null : null;
}

function getVisibleElementCount(container: HTMLElement | null): number {
  if (!container) return 0;
  const elements = [container, ...Array.from(container.querySelectorAll<HTMLElement>("*"))];
  return elements.filter((element) => {
    const style = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return (
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      Number(style.opacity || "1") > 0 &&
      rect.width > 0 &&
      rect.height > 0
    );
  }).length;
}

function hasSuccessfulApiBootstrap(trace: StartupTraceEvent[]): boolean {
  return trace.some((event) => event.step === "bootstrap_done" || event.step === "startup_completed_successfully");
}

function isStartupDebugUiEnabled(): boolean {
  if (import.meta.env.DEV) {
    return true;
  }

  if (typeof window === "undefined") {
    return false;
  }

  try {
    return isBloomDebugEnabled() || new URLSearchParams(window.location.search).get("debug") === "1";
  } catch {
    return false;
  }
}
export interface PartnerOffersDiagnostic {
  numericPartnerId?: number;
  partnerIdSource?: "partner.id";
  offersUrlPath?: string;
  source?: "tg_local_catalog" | "web_legacy_catalog";
  httpStatus?: number;
  backendDetail?: strin…22472 tokens truncated…     const backendDetail = isApiError(error) && typeof error.detail === "string" ? error.detail : "";
      setLoginCodeError(backendDetail || "Код недействителен или устарел. Получите новый код в боте.");
    } finally {
      setIsLoginCodeSubmitting(false);
    }
  }, [loadAppData, telegramLoginCode, vkLoginCode, loginReferralCode]);

  const reloadSuccessfulBootstrapRecovery = useCallback(() => {
    setShowSuccessfulBootstrapRecovery(false);
    resetPartnerFlowState("home");
    removeEntryFallbackOverlay();
  }, [resetPartnerFlowState]);

  const hasAnyAuthTokenForLoginGuard = Boolean(authSnapshotRef.current.token || getStoredAuthToken());
  const canRenderLogin = browserLoginRequired && authRestoreStatus === "unauthenticated" && !isLoading && !bootstrapPromiseRef.current;

  useEffect(() => {
    if (browserLoginRequired && hasAnyAuthTokenForLoginGuard) {
      reportClientError("unexpected_login_screen_with_token", new Error("unexpected_login_screen_with_token"), {
        authRestoreStatus,
        hasStoredToken: hasAnyAuthTokenForLoginGuard,
        tokenSource: authSnapshotRef.current.tokenSource,
        lastAuthDecisionReason,
        startupInterrupted: Boolean(getStartupMarkers().interrupted),
        startupCompleted: isBootstrapDone,
        cleanupRan: cleanupRanRef.current,
        cleanupRemovedKeys: cleanupRemovedKeysRef.current,
        cleanupRemovedKeysCount: cleanupRemovedKeysRef.current.length,
        lastPagehideAt: lastPagehideAtRef.current,
        lastPageshowAt: lastPageshowAtRef.current,
        lastBootstrapAbortReason: lastBootstrapAbortReasonRef.current,
        currentRouteHash: `${window.location.pathname}${window.location.search}${window.location.hash}`,
        appMounted: mountedRef.current,
        firstVisiblePaint: window.__BLOOM_STARTUP_PHASE__ === "first_visible_paint",
      });
    }
  }, [authRestoreStatus, browserLoginRequired, hasAnyAuthTokenForLoginGuard, isBootstrapDone, lastAuthDecisionReason]);


  if (showStartupRecovery) {
    return <StartupRecoveryScreen message={watchdogMessage} />;
  }

  if (showSuccessfulBootstrapRecovery) {
    return <SuccessfulBootstrapRecoveryScreen onReload={reloadSuccessfulBootstrapRecovery} />;
  }

  const designPreviewHome = import.meta.env.DEV && new URLSearchParams(window.location.search).get("design_preview") === "home";

  if (designPreviewHome) {
    const previewProfile: ClientProfile = { id: 248, first_name: "Мария", city: "Новосибирск" };
    const previewSubscription: Subscription = { status: "active", active: true, ends_at: "2026-12-31T23:59:59+07:00" };

    return (
      <ContentProvider>
        <AppShell activePage="home" onNavigate={() => undefined} profile={previewProfile} subscription={previewSubscription} onOpenSubscription={() => undefined}>
          <HomePage
            profile={previewProfile}
            subscription={previewSubscription}
            cities={[{ id: 1, name: "Новосибирск" }]}
            partners={[]}
            isPartnersLoading={false}
            hasPartnersLoaded={true}
            onOpenCatalog={() => undefined}
            onOpenSubscription={() => undefined}
            onActivateTrial={async () => previewSubscription}
            referralSummary={null}
            giveawayState={{ guest: false, has_active_giveaway: false }}
            isGiveawayLoading={false}
          />
        </AppShell>
      </ContentProvider>
    );
  }

  if (browserLoginExternalOpenRequired) {
    return <BrowserLoginExternalOpenRequiredScreen />;
  }

  if (browserLoginRequired && !canRenderLogin) {
    return <LoadingState title={hasAnyAuthTokenForLoginGuard ? "Проверяем вход..." : "Загружаем Bloom Club..."} />;
  }

  if (canRenderLogin) {
    return (
      <div className="welcome-auth-screen" role="status">
        <div className="welcome-auth-screen__background" aria-hidden="true" />
        <div className="welcome-auth-screen__overlay" aria-hidden="true" />
        <div className="state welcome-auth-screen__card">
          <div className="welcome-auth-screen__brand" aria-label="Bloom Club">
            <strong>BLOOM CLUB</strong>
            <span>Женский клуб · НСК</span>
          </div>
          <h1>{BROWSER_LOGIN_REQUIRED_MESSAGE}</h1>
          {isLoginCodeFormOpen ? (
            <>
              <p>{LOGIN_CODE_HELP_MESSAGE}</p>
              <input
                aria-label="Код для входа из Telegram"
                className="auth-code-input"
                value={telegramLoginCode}
                placeholder="Код из Telegram"
                inputMode="text"
                autoCapitalize="characters"
                autoCorrect="off"
                spellCheck={false}
                onChange={(event) => updateTelegramLoginCodeDraft(event.target.value)}
              />
              <div className="login-code-legal-text">или</div>
              <input
                aria-label="Код для входа из VK"
                className="auth-code-input"
                value={vkLoginCode}
                placeholder="Код из VK"
                inputMode="text"
                autoCapitalize="characters"
                autoCorrect="off"
                spellCheck={false}
                onChange={(event) => updateVkLoginCodeDraft(event.target.value)}
              />
              <p className="login-code-legal-text">Получите код у нашего бота в Telegram или VK</p>
              <div className="auth-actions">
                {TELEGRAM_BOT_LINK ? <a className="button button--secondary" href={TELEGRAM_BOT_LINK}>Получить код в Telegram</a> : null}
                {VK_BOT_LINK ? <a className="button button--secondary" href={VK_BOT_LINK}>Получить код во VK</a> : null}
              </div>
              <input
                aria-label="Реферальный код — необязательно"
                className="auth-code-input"
                value={loginReferralCode}
                placeholder="Реферальный код — необязательно"
                inputMode="text"
                autoCapitalize="characters"
                autoCorrect="off"
                spellCheck={false}
                onChange={(event) => updateReferralCodeDraft(event.target.value)}
              />
              {loginCodeError ? <p className="error-text">{loginCodeError}</p> : null}
              <button className="button button--primary" type="button" onClick={submitLoginCode} disabled={isLoginCodeSubmitting}>
                {isLoginCodeSubmitting ? "Входим…" : "Войти"}
              </button>
              <p className="login-code-legal-text">
                Нажимая «Войти», вы принимаете условия{' '}
                <a href={LEGAL_DOCUMENT_LINKS.agreement} target="_blank" rel="noopener noreferrer">Пользовательского соглашения</a>
                ,{' '}
                <a href={LEGAL_DOCUMENT_LINKS.privacy} target="_blank" rel="noopener noreferrer">Политики конфиденциальности</a>
                {' '}и даёте согласие на{' '}
                <a href={LEGAL_DOCUMENT_LINKS.personalDataConsent} target="_blank" rel="noopener noreferrer">обработку персональных данных</a>.
              </p>
            </>
          ) : (
            <>
              <button className="button button--primary" type="button" onClick={() => { writeBrowserGuestMode(false); setBrowserGuestMode(false); pendingBrowserLoginRef.current = true; setIsLoginCodeFormOpen(true); }}>Войти по коду</button>
              <button className="button button--secondary" type="button" onClick={() => { pendingBrowserLoginRef.current = false; writeBrowserGuestMode(true); setBrowserGuestMode(true); setBrowserLoginRequired(false); setAuthRestoreStatus("unauthenticated"); setLastAuthDecisionReason("guest_mode_selected"); setIsBootstrapDone(true); setIsLoading(false); resetPartnerFlowState("home"); loadPartners(true).catch(() => undefined); }}>Продолжить без регистрации</button>
            </>
          )}
        </div>
      </div>
    );
  }

  if (isLoading) {
    return <LoadingState title="Загружаем Bloom Club..." />;
  }

  if (error) {
    return (
      <ErrorState
        title={CONNECTION_PROBLEM_TITLE}
        description={CONNECTION_PROBLEM_DESCRIPTION}
        diagnostic={error}
        onRetry={() => loadAppData("manual", true)}
        startupContext={{
          currentPage: page,
          bootstrapStatus: isBootstrapDone ? "done" : "pending",
          catalogStatus: isPartnersLoading
            ? "loading"
            : hasPartnersLoaded
              ? "loaded"
              : partnersError
                ? "error"
                : "idle",
          offersStatus: partnerOffersStatus,
        }}
      />
    );
  }


  if (!isKnownPage(page) && unknownStateDiagnostic) {
    return (
      <ContentProvider>
        <AppShell activePage="home" onNavigate={setPage}>
          <ErrorState
            title="Не удалось определить раздел приложения"
            description="Откройте главный экран или повторите запуск Mini App."
            diagnostic={unknownStateDiagnostic}
            onRetry={() => setPage("home")}
            startupContext={{
              currentPage: page,
              bootstrapStatus: isBootstrapDone ? "done" : "pending",
              catalogStatus: hasPartnersLoaded ? "loaded" : "idle",
              offersStatus: partnerOffersStatus,
            }}
          />
        </AppShell>
      </ContentProvider>
    );
  }


  const catalogStatus = isPartnersLoading
    ? "loading"
    : hasPartnersLoaded
      ? "loaded"
      : partnersError
        ? "error"
        : "idle";
  const latestCatalogTrace = getStartupTrace();
  const diagnosticFlags = {
    catalogLoadRequested: catalogLoadRequestId !== undefined,
    fetchStarted: latestCatalogTrace.some((event) => event.step === "getPartners_fetch_started"),
    timeoutStarted: latestCatalogTrace.some((event) => event.step === "catalog_timeout_created"),
    activePage,
    currentPath: typeof window === "undefined" ? "" : `${window.location.pathname}${window.location.search}${window.location.hash}`,
    hasToken: Boolean(getStoredAuthToken()),
    hasProfile: Boolean(safeData.profile),
    hasSubscription: Boolean(safeData.subscription),
    partnerCount: safeData.partners.length,
    catalogStatus,
  };



  const startupDiagnostics = showStartupDiagnostics ? (
    <div className="startup-diagnostic-panel" role="status">
      <button
        className="button button--secondary"
        type="button"
        onClick={() => setShowStartupDiagnostics(false)}
      >
        Скрыть диагностику запуска
      </button>
      <h2>Диагностика запуска</h2>
      {watchdogMessage ? <p>{watchdogMessage}</p> : null}
      <pre>{JSON.stringify(getStartupTrace().slice(-30), null, 2)}</pre>
    </div>
  ) : null;

  return (
    <ContentProvider>
      <AppShell activePage={activeNavPage} onNavigate={navigate} onHiddenDiagnosticsGesture={openDiagnosticsByHiddenGesture} profile={safeData.profile} subscription={safeData.subscription} onOpenSubscription={() => setPage("subscription")}>
        {activePage === "home" ? (
          <HomePage
            profile={safeData.profile}
            subscription={safeData.subscription}
            cities={safeData.cities}
            partners={safeData.partners}
            isPartnersLoading={isPartnersLoading}
            hasPartnersLoaded={hasPartnersLoaded}
            onOpenCatalog={openCatalog}
            onOpenSubscription={() => setPage("subscription")}
            onActivateTrial={activateTrial}
            referralSummary={safeData.referralSummary}
            giveawayState={safeData.giveawayState}
            isGiveawayLoading={isGiveawayLoading}
          />
        ) : null}

        {activePage === "catalog" && unknownStateDiagnostic ? (
          <ErrorState
            title="Не удалось восстановить карточку партнёра"
            description="Откройте каталог и выберите партнёра заново."
            diagnostic={unknownStateDiagnostic}
            onRetry={openCatalog}
            startupContext={{
              currentPage: page,
              bootstrapStatus: isBootstrapDone ? "done" : "pending",
              catalogStatus: hasPartnersLoaded ? "loaded" : "idle",
              offersStatus: partnerOffersStatus,
            }}
          />
        ) : null}

        {activePage === "catalog" && !unknownStateDiagnostic ? (
          <CatalogPage
            partners={safeData.partners}
            isLoading={isPartnersLoading}
            error={partnersError}
            errorTitle={partnersErrorTitle}
            errorDetails={partnersErrorDetails}
            errorCreatedAt={catalogErrorCreatedAt}
            loadStartedAt={catalogLoadStartedAt}
            loadRequestId={catalogLoadRequestId}
            onRetry={catalogRecoveryPending ? retryCatalogAfterRecovery : () => void loadPartners(true)}
            onCancel={cancelCatalogLoad}
            isRecovery={catalogRecoveryPending}
            onOpenPartner={openPartner}
          />
        ) : null}
        {activePage === "partner" ? (
          <PartnerPage
            partner={selectedPartner}
            profile={safeData.profile}
            offers={partnerOffers}
            offersStatus={partnerOffersStatus}
            offersError={partnerOffersError}
            offersDiagnostic={partnerOffersDiagnostic}
            subscription={safeData.subscription}
            onBack={openCatalog}
            onVerifyOffer={createVerification}
            onOpenSubscription={() => setPage("subscription")}
            onActivateTrial={activateTrial}
            onRetryOffers={retryPartnerOffers}
          />
        ) : null}
        {activePage === "privileges" ? (
          <PrivilegesPage
            verifications={safeData.verifications}
            emptyTitle={
              TG_LOCAL_CATALOG_ENABLED
                ? "Привилегии Telegram-каталога скоро появятся."
                : undefined
            }
            emptyDescription={
              TG_LOCAL_CATALOG_ENABLED
                ? "Выберите партнёра в Telegram-каталоге и получите код, когда выдача кодов будет подключена."
                : undefined
            }
          />
        ) : null}
        {activePage === "savings" ? (
          <SavingsPage
            savings={safeData.savings}
            emptyTitle={
              TG_LOCAL_CATALOG_ENABLED
                ? "Экономия Telegram-каталога скоро появится."
                : undefined
            }
            emptyDescription={
              TG_LOCAL_CATALOG_ENABLED
                ? "История экономии появится после подключения пользовательского контекста Telegram-каталога."
                : undefined
            }
          />
        ) : null}
        {activePage === "profile" ? (
          <ProfilePage
            profile={safeData.profile}
            subscription={safeData.subscription}
            cities={safeData.cities}
            onOpenSubscription={() => setPage("subscription")}
            onActivateTrial={activateTrial}
            isCreatingPayment={isCreatingPayment}
            onCreatePayment={openPayment}
            onSaveProfile={saveProfile}
            referralSummary={safeData.referralSummary}
            onLogout={logout}
          />
        ) : null}
        {activePage === "subscription" ? (
          <SubscriptionPage
            profile={safeData.profile}
            subscription={safeData.subscription}
            paymentRequest={paymentRequest}
            isCreatingPayment={isCreatingPayment}
            onCreatePayment={openPayment}
            onActivateTrial={activateTrial}
            onBack={() => setPage("profile")}
          />
        ) : null}
        {activePage === "payment-result" ? (
          <PaymentResultScreen
            onDone={async () => { await refreshProfileAndSubscription(); }}
            onBack={() => { window.history.replaceState({}, '', '/'); setPage('profile'); }}
          />
        ) : null}

        {shouldShowLinking && isTelegramApp ? (
          <AccountLinkingOnboarding
            onDismiss={dismissLinkingOnboarding}
            onLinked={async () => {
              await refreshAfterLinking();
              setShouldShowLinking(false);
            }}
          />
        ) : null}

        {guestRestrictionMessage ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <div className="modal-card">
              <h2>Требуется регистрация</h2>
              <p>Чтобы воспользоваться возможностями Bloom Club, войдите по коду, который прислал Telegram или VK бот.</p>
              <button className="button button--primary" type="button" onClick={() => { setGuestRestrictionMessage(false); writeBrowserGuestMode(false); setBrowserGuestMode(false); setBrowserLoginRequired(true); setIsLoginCodeFormOpen(true); }}>Ввести код</button>
              <button className="button button--secondary" type="button" onClick={() => setGuestRestrictionMessage(false)}>Позже</button>
            </div>
          </div>
        ) : null}
        {previousCrashDump ? (
          <div className="crash-dump-banner" role="status">
            <p>Обнаружена диагностика предыдущего неудачного запуска</p>
            <div>
              <button
                className="button button--primary"
                type="button"
                onClick={() => {
                  setDiagnosticOverlayReason("Диагностика предыдущего неудачного запуска.");
                  setShowStartupDiagnostics(true);
                }}
              >
                Открыть диагностику
              </button>
              <button
                className="button button--secondary"
                type="button"
                onClick={() => {
                  clearCrashDump("user_clear_previous_crash_dump");
                  setPreviousCrashDump(null);
                }}
              >
                Очистить
              </button>
            </div>
          </div>
        ) : null}
        {isStartupDebugUiEnabledValue ? (
          <>
            <button
              className="startup-diagnostic-button"
              type="button"
              onClick={() => {
                lifecycleTrace("diagnostic_overlay_manual_open", {
                  page: activePage,
                });
                setDiagnosticOverlayReason("Диагностика открыта вручную.");
                setShowStartupDiagnostics(true);
              }}
            >
              Открыть debug диагностику
            </button>
            {startupDiagnostics}
          </>
        ) : null}
        {Boolean(diagnosticOverlayReason) ? (
          <DiagnosticOverlay
            open={Boolean(diagnosticOverlayReason)}
            reason={diagnosticOverlayReason}
            onClose={() => setDiagnosticOverlayReason(null)}
            currentFlags={{ ...diagnosticFlags, previousCrashDump }}
          />
        ) : null}
      </AppShell>
    </ContentProvider>
  );
}
