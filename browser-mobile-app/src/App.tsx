import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  activateTrialSubscription,
  loginWithCode,
  createPaymentRequest,
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
  | "subscription";
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
  privacy: '/docs/Политика%20Конфиденциальности.docx',
  agreement: '/docs/Пользовательское%20соглашение.docx',
  personalDataConsent: '/docs/Согласие%20на%20обработку%20персональных%20данных.docx',
};

const BROWSER_LOGIN_REQUIRED_MESSAGE =
  "Добро пожаловать в Bloom Club";
const LOGIN_CODE_HELP_MESSAGE =
  "Введите код, который прислал Telegram или VK бот.";
const TELEGRAM_IN_APP_BROWSER_HOST = "app.bloomclub.ru";


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
  backendDetail?: string;
  partnerIdMissingOrInvalid?: boolean;
}

declare global {
  interface Navigator {
    userAgentData?: {
      platform?: string;
    };
  }

  interface Window {
    TelegramWebviewProxy?: unknown;
    TelegramGameProxy?: unknown;
    __BLOOM_TG_CATALOG_BOOTSTRAP__?: {
      items?: Partner[];
      consumed?: boolean;
    };
    __BLOOM_LAST_CATALOG_ERROR__?: unknown;
  }
}

interface AppData {
  profile: ClientProfile | null;
  subscription: Subscription | null;
  partners: Partner[];
  verifications: Verification[];
  savings: SavingsSummary | null;
  cities: City[];
  linkingStatus: LinkingStatus | null;
  referralSummary: ReferralSummary | null;
  giveawayState: GiveawayState | null;
}

const emptyData: AppData = {
  profile: null,
  subscription: null,
  partners: [],
  verifications: [],
  savings: null,
  cities: [],
  linkingStatus: null,
  referralSummary: null,
  giveawayState: null,
};

function asObject<T extends object>(value: T | null | undefined): T | null {
  return value && typeof value === "object" ? value : null;
}

function asArray<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function normalizeAppData(data: Partial<AppData>): AppData {
  return {
    profile: asObject(data.profile),
    subscription: asObject(data.subscription),
    partners: sortPartnersForCatalog(asArray(data.partners)),
    verifications: asArray(data.verifications),
    savings: asObject(data.savings),
    cities: asArray(data.cities),
    linkingStatus: asObject(data.linkingStatus),
    referralSummary: asObject(data.referralSummary),
    giveawayState: asObject(data.giveawayState),
  };
}

function consumeCatalogBootstrap(): Partner[] | null {
  if (typeof window === "undefined") {
    traceMark("catalog_bootstrap_missing", { reason: "no_window" });
    return null;
  }

  const bootstrap = window.__BLOOM_TG_CATALOG_BOOTSTRAP__;
  if (
    !bootstrap ||
    bootstrap.consumed ||
    !Array.isArray(bootstrap.items) ||
    bootstrap.items.length === 0
  ) {
    traceMark("catalog_bootstrap_missing", {
      consumed: bootstrap?.consumed,
      hasItems: Array.isArray(bootstrap?.items),
      itemsCount: bootstrap?.items?.length ?? 0,
    });
    return null;
  }

  traceMark("catalog_bootstrap_available", {
    itemsCount: bootstrap.items.length,
  });
  bootstrap.consumed = true;
  traceMark("catalog_bootstrap_consumed", {
    itemsCount: bootstrap.items.length,
  });
  const items = bootstrap.items;
  window.__BLOOM_TG_CATALOG_BOOTSTRAP__ = { items: [], consumed: true };
  return items;
}

function normalizeOffersResponse(response: unknown): Offer[] {
  if (Array.isArray(response)) {
    return sortOffersForPartner(response as Offer[]);
  }

  if (!response || typeof response !== "object") {
    return [];
  }

  const body = response as Record<string, unknown>;
  const candidates = [body.items, body.offers, body.data, body.results];
  const offers = candidates.find(Array.isArray);
  return sortOffersForPartner(Array.isArray(offers) ? (offers as Offer[]) : []);
}

function extractTrialPayload(response: unknown): {
  subscription: Subscription | null;
  profile: ClientProfile | null;
} {
  if (!response || typeof response !== "object") {
    return { subscription: null, profile: null };
  }

  const body = response as Record<string, unknown>;
  const subscription = asObject((body.subscription ?? body) as Subscription);
  const profile = asObject((body.profile ?? body.client) as ClientProfile);

  return { subscription, profile };
}

function safeDiagnosticText(value: unknown): string | undefined {
  if (value === undefined || value === null) {
    return undefined;
  }

  const text = typeof value === "string" ? value : JSON.stringify(value);
  return text
    .replace(
      /(credential|signature|token)(["'\s:=]+)[^,"'\s}]+/gi,
      "$1$2[hidden]",
    )
    .slice(0, 500);
}

function logBootstrapDiagnostic(
  event: string,
  details: Record<string, unknown>,
): void {
  console.info(event, {
    ...details,
    errorMessageShort:
      "errorMessageShort" in details
        ? safeDiagnosticText(details.errorMessageShort)
        : undefined,
  });
}

function getLinkingDismissKey(profile: ClientProfile | null): string | null {
  const identity = profile?.telegram_user_id ?? profile?.id;
  return identity === undefined || identity === null
    ? null
    : `bloom_club_tma_linking_dismissed_${identity}`;
}

function isProfileLinked(status: LinkingStatus | null | undefined): boolean {
  if (!status || typeof status !== "object") {
    return false;
  }

  if (
    status.linked === true ||
    status.is_linked === true ||
    status.has_linked_account === true
  ) {
    return true;
  }

  if (status.needs_linking === true) {
    return false;
  }

  const statusText = String(status.status ?? "").toLowerCase();
  return (
    ["linked", "connected", "merged"].includes(statusText) ||
    Boolean(status.linked_profile_id)
  );
}

function shouldShowLinkingOnboarding(
  isTelegram: boolean,
  profile: ClientProfile | null,
  status: LinkingStatus | null,
  dismissedKey: string | null,
): boolean {
  if (
    !isTelegram ||
    !profile ||
    !status ||
    isProfileLinked(status) ||
    !dismissedKey
  ) {
    return false;
  }

  return window.localStorage.getItem(dismissedKey) !== "1";
}

function getStartupPage(): PageId {
  if (typeof window === "undefined") {
    return "home";
  }

  return window.location.hash === "#catalog" ? "catalog" : "home";
}

function isUnsafeStartupScreen(page: PageId): boolean {
  return page === "partner";
}

function isKnownPage(page: string): page is PageId {
  return [
    "home",
    "catalog",
    "partner",
    "privileges",
    "savings",
    "profile",
    "subscription",
  ].includes(page);
}

export default function App() {
  traceStartup("app_component_rendered");
  lifecycleTrace("app_render", {
    page:
      typeof window === "undefined"
        ? "unknown"
        : window.__BLOOM_PAGE_LIFECYCLE_PAGE_ID__,
  });
  const [page, setPage] = useState<PageId>(() => getStartupPage());
  const [data, setData] = useState<AppData>(emptyData);
  const [selectedPartner, setSelectedPartner] = useState<Partner | null>(null);
  const [partnerOffers, setPartnerOffers] = useState<Offer[]>([]);
  const [partnerOffersStatus, setPartnerOffersStatus] =
    useState<AsyncStatus>("idle");
  const [partnerOffersError, setPartnerOffersError] = useState("");
  const [partnerOffersDiagnostic, setPartnerOffersDiagnostic] =
    useState<PartnerOffersDiagnostic | null>(null);
  const [paymentRequest, setPaymentRequest] = useState<PaymentRequest | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<AppDiagnostic | null>(null);
  const [authRestoreStatus, setAuthRestoreStatus] = useState<AuthRestoreStatus>("unknown");
  const [lastAuthDecisionReason, setLastAuthDecisionReason] = useState("initial_unknown");
  const authSnapshotRef = useRef(getAuthTokenStorageSnapshot());
  const cleanupRanRef = useRef(false);
  const cleanupRemovedKeysRef = useRef<string[]>([]);
  const lastPagehideAtRef = useRef<string | null>(null);
  const lastPageshowAtRef = useRef<string | null>(null);
  const lastBootstrapAbortReasonRef = useRef<string | null>(null);
  const [browserLoginRequired, setBrowserLoginRequired] = useState(false);
  const [browserLoginExternalOpenRequired, setBrowserLoginExternalOpenRequired] = useState(false);
  const [isLoginCodeFormOpen, setIsLoginCodeFormOpen] = useState(false);
  const [loginCode, setLoginCode] = useState("");
  const [loginReferralCode, setLoginReferralCode] = useState("");
  const [loginCodeError, setLoginCodeError] = useState("");
  const [isLoginCodeSubmitting, setIsLoginCodeSubmitting] = useState(false);
  const [guestRestrictionMessage, setGuestRestrictionMessage] = useState(false);
  const [isCreatingPayment, setIsCreatingPayment] = useState(false);
  const [trialMessage, setTrialMessage] = useState<string | null>(null);
  const [paymentMessage, setPaymentMessage] = useState<string | null>(null);
  const [isPartnersLoading, setIsPartnersLoading] = useState(false);
  const [partnersError, setPartnersError] = useState("");
  const [partnersErrorTitle, setPartnersErrorTitle] = useState(
    "Не удалось загрузить каталог",
  );
  const [partnersErrorDetails, setPartnersErrorDetails] = useState<
    | Pick<
        CatalogErrorDiagnostic,
        | "source"
        | "requestUrl"
        | "requestUrlPath"
        | "requestOrigin"
        | "httpStatus"
        | "requestId"
        | "elapsedMs"
        | "attempt"
        | "fetchPhase"
        | "errorName"
        | "isAbortError"
      >
    | undefined
  >(undefined);
  const [catalogErrorCreatedAt, setCatalogErrorCreatedAt] = useState<
    string | undefined
  >(undefined);
  const [catalogLoadStartedAt, setCatalogLoadStartedAt] = useState<
    string | undefined
  >(undefined);
  const [catalogLoadRequestId, setCatalogLoadRequestId] = useState<
    number | undefined
  >(undefined);
  // Catalog diagnostic UI intentionally allows only safe request fields plus local freshness markers.
  const [hasPartnersLoaded, setHasPartnersLoaded] = useState(false);
  const [catalogRecoveryPending, setCatalogRecoveryPending] = useState(() => hasCatalogRecoveryFlag());
  const [shouldShowLinking, setShouldShowLinking] = useState(false);
  const [isTelegramApp, setIsTelegramApp] = useState(false);
  const isStartupDebugUiEnabledValue = useMemo(isStartupDebugUiEnabled, []);
  const [showStartupDiagnostics, setShowStartupDiagnostics] = useState(false);
  const [diagnosticOverlayReason, setDiagnosticOverlayReason] = useState<
    string | null
  >(null);
  const [previousCrashDump, setPreviousCrashDump] = useState<BloomCrashDump | null>(() => readCompatibleCrashDump());
  const debugTapCountRef = useRef(0);
  const debugTapTimerRef = useRef<number | undefined>(undefined);
  const [watchdogMessage, setWatchdogMessage] = useState<string | null>(null);
  const [showStartupRecovery, setShowStartupRecovery] = useState(false);
  const [isBootstrapDone, setIsBootstrapDone] = useState(false);
  const [hasRenderedPageContent, setHasRenderedPageContent] = useState(false);
  const partnersPromiseRef = useRef<Promise<void> | null>(null);
  const catalogAbortControllerRef = useRef<AbortController | null>(null);
  const catalogLoadSequenceRef = useRef(0);
  const pageRef = useRef<PageId>(page);
  const clearCatalogDiagnostic = setPartnersErrorDetails;
  const bootstrapPromiseRef = useRef<Promise<void> | null>(null);
  const bootstrapSequenceRef = useRef(0);
  const appActiveRef = useRef(true);
  const catalogLoadingRef = useRef(false);
  const mountedRef = useRef(false);
  const diagnosticSessionIdRef = useRef(
    `bootstrap-deadlock-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
  );
  const logBootstrapDeadlockDiagnostic = useCallback(
    (event: string, details: Record<string, unknown> = {}) => {
      console.info("bootstrap_deadlock_diagnostic", {
        event,
        sessionId: diagnosticSessionIdRef.current,
        visibilityState: document.visibilityState,
        performanceNow: performance.now(),
        bootstrapSequence: bootstrapSequenceRef.current,
        bootstrapPromiseExists: Boolean(bootstrapPromiseRef.current),
        mountedRef: mountedRef.current,
        appActive: appActiveRef.current,
        ...details,
      });
    },
    [],
  );

  useEffect(() => {
    const effectSpan = startupExecutionBegin("useEffect:page_transition", { page });
    lifecycleTrace("app_effect_page_start", {
      from: pageRef.current,
      to: page,
    });
    pageRef.current = page;
    setLifecyclePageId(page);
    lifecycleTrace("page_transition", { page });
    startupExecutionEnd(effectSpan, { page });
    return () => {
      const cleanupSpan = startupExecutionBegin("cleanup:page_transition", { page });
      lifecycleTrace("app_effect_page_cleanup", { page });
      startupExecutionEnd(cleanupSpan, { page });
    };
  }, [page]);

  useEffect(() => {
    const effectSpan = startupExecutionBegin("useEffect:modal_focus_observer");
    focusOpenModal();

    const observer = new MutationObserver(() => focusOpenModal());
    observer.observe(document.body, { childList: true, subtree: true });

    startupExecutionEnd(effectSpan);
    return () => {
      const cleanupSpan = startupExecutionBegin("cleanup:modal_focus_observer");
      observer.disconnect();
      startupExecutionEnd(cleanupSpan);
    };
  }, []);

  const clearBloomBootstrapRecoveryStorage = useCallback(() => {
    if (typeof window === "undefined") {
      return { localStorage: [] as string[], sessionStorage: [] as string[] };
    }

    const keyPattern = /^(bloom_club_tma_.*(?:bootstrap|build|recovery|startup|crash)|bloom_tma_.*(?:bootstrap|build|recovery|startup|crash)|bloomClubTma.*(?:Bootstrap|Build|Recovery|Startup|Crash)|bloom_(?:last_startup_error|forced_reload_count|recovery|recovery_ts|reload_build|reload_ts))/i;
    const clearMatchingStorageKeys = (storage: Storage): string[] => {
      const removed: string[] = [];
      for (let index = storage.length - 1; index >= 0; index -= 1) {
        const key = storage.key(index);
        if (key && keyPattern.test(key)) {
          storage.removeItem(key);
          removed.push(key);
        }
      }
      return removed;
    };

    try {
      return {
        localStorage: clearMatchingStorageKeys(window.localStorage),
        sessionStorage: clearMatchingStorageKeys(window.sessionStorage),
      };
    } catch {
      return { localStorage: [], sessionStorage: [] };
    }
  }, []);

  const invalidateBootstrapForInactiveWebView = useCallback((eventName: string) => {
    appActiveRef.current = false;
    bootstrapSequenceRef.current += 1;
    const hadBootstrapPromise = Boolean(bootstrapPromiseRef.current);
    bootstrapPromiseRef.current = null;
    resetTelegramLoginInFlight();
    lastBootstrapAbortReasonRef.current = eventName;
    setAuthRestoreStatus((current) => current === "authenticated" ? current : "restoring");
    setLastAuthDecisionReason("bootstrap_aborted_neutral");
    const removedStorage = clearBloomBootstrapRecoveryStorage();
    logBootstrapDeadlockDiagnostic("webview_inactive_bootstrap_invalidated", {
      lifecycleEvent: eventName,
      hadBootstrapPromise,
      invalidatedSequence: bootstrapSequenceRef.current,
      removedLocalStorageKeys: removedStorage.localStorage,
      removedSessionStorageKeys: removedStorage.sessionStorage,
    });
  }, [clearBloomBootstrapRecoveryStorage, logBootstrapDeadlockDiagnostic]);

  const resetStaleBootstrapForActiveWebView = useCallback((eventName: string) => {
    appActiveRef.current = true;
    if (bootstrapPromiseRef.current) {
      logBootstrapDeadlockDiagnostic("bootstrapPromiseRef_cleared", {
        reason: "webview_resume",
        lifecycleEvent: eventName,
      });
    }
    bootstrapPromiseRef.current = null;
    bootstrapSequenceRef.current += 1;
    resetTelegramLoginInFlight();
    setIsBootstrapDone(false);
    setShowStartupRecovery(false);
    setWatchdogMessage(null);
    setError(null);
    logBootstrapDeadlockDiagnostic("webview_active_bootstrap_reset", {
      lifecycleEvent: eventName,
      invalidatedSequence: bootstrapSequenceRef.current,
    });
  }, [logBootstrapDeadlockDiagnostic]);

  const resetCatalogStateForForceReload = useCallback(() => {
    catalogAbortControllerRef.current?.abort("catalog_force_reload");
    catalogAbortControllerRef.current = null;
    partnersPromiseRef.current = null;
    setPartnersError("");
    clearCatalogDiagnostic(undefined);
    setCatalogErrorCreatedAt(undefined);
    setCatalogLoadStartedAt(undefined);
    setCatalogLoadRequestId(undefined);
    setHasPartnersLoaded(false);
    catalogLoadingRef.current = false;
    setIsPartnersLoading(false);
  }, [logBootstrapDeadlockDiagnostic]);


  const abortInFlightCatalogLoad = useCallback((reason: string) => {
    const hadCatalogPromise = Boolean(partnersPromiseRef.current);
    catalogAbortControllerRef.current?.abort(reason);
    catalogAbortControllerRef.current = null;
    partnersPromiseRef.current = null;
    catalogLoadingRef.current = false;
    setIsPartnersLoading(false);
    console.info("catalog_load_aborted_for_lifecycle", {
      reason,
      hadCatalogPromise,
      page: pageRef.current,
    });
  }, []);

  useEffect(() => {
    const effectSpan = startupExecutionBegin("useEffect:closing_confirmation", { isLoading, isPartnersLoading });
    const webApp = getTelegramWebApp();
    const shouldConfirmClosing = isLoading || isPartnersLoading;
    try {
      if (shouldConfirmClosing) {
        webApp?.enableClosingConfirmation?.();
        console.info("closing_confirmation_enabled", { isLoading, isPartnersLoading });
        traceStartup("closing_confirmation_enabled", { isLoading, isPartnersLoading });
      } else {
        webApp?.disableClosingConfirmation?.();
        console.info("closing_confirmation_disabled", { isLoading, isPartnersLoading });
        traceStartup("closing_confirmation_disabled", { isLoading, isPartnersLoading });
      }
    } catch (caughtError) {
      traceStartup("closing_confirmation_error", { error: caughtError });
    }
    startupExecutionEnd(effectSpan, { isLoading, isPartnersLoading });
    return () => {
      const cleanupSpan = startupExecutionBegin("cleanup:closing_confirmation");
      try { webApp?.disableClosingConfirmation?.(); } catch { /* ignore */ }
      startupExecutionEnd(cleanupSpan);
    };
  }, [isLoading, isPartnersLoading]);

  useEffect(() => {
    const effectSpan = startupExecutionBegin("useEffect:open_diagnostics_listener");
    window.__BLOOM_OPEN_DIAGNOSTICS__ = (reason = "external_open") => {
      enableBloomDebug();
      setDiagnosticOverlayReason(reason);
      setShowStartupDiagnostics(true);
    };
    startupExecutionEnd(effectSpan);
    return () => {
      const cleanupSpan = startupExecutionBegin("cleanup:open_diagnostics_listener");
      window.__BLOOM_OPEN_DIAGNOSTICS__ = undefined;
      startupExecutionEnd(cleanupSpan);
    };
  }, []);

  useEffect(() => {
    const effectSpan = startupExecutionBegin("useEffect:app_component_mount", { page });
    console.info("app_component_mount_start");
    logBootstrapDeadlockDiagnostic("react_mount");
    markReactMounted(true);
    lifecycleTrace("app_mount", { page });
    setStartupPhase("app_mounted", { page });
    traceStartup("app_mounted", { page });
    traceStartup("app_component_mounted", { page });
    traceMark("ui_mounted", { page });
    traceMark("app_component_mount");
    traceMark("app_initial_state", {
      page,
      isLoading,
      hasError: Boolean(error),
    });
    mountedRef.current = true;
    traceStartup("remove_fallback_started", { page });
    removeEntryFallbackOverlay();
    traceStartup("remove_fallback_done", { page });
    startupExecutionMark("requestAnimationFrame scheduled:first_visible_shell_committed", { page });
    requestAnimationFrame(() => {
      const rafSpan = startupExecutionBegin("requestAnimationFrame:first_visible_shell_committed", { page: pageRef.current });
      traceStartup("first_visible_shell_committed", { page: pageRef.current });
      setStartupPhase("first_visible_paint", { page: pageRef.current });
      markFirstVisiblePaint();
      startupExecutionEnd(rafSpan, { page: pageRef.current });
    });
    startupExecutionEnd(effectSpan, { page });

    return () => {
      lifecycleTrace("app_unmount", { page: pageRef.current });
      logBootstrapDeadlockDiagnostic("react_unmount_before_mountedRef_false", {
        page: pageRef.current,
      });
      markReactMounted(false);
      mountedRef.current = false;
      logBootstrapDeadlockDiagnostic("react_unmount_after_mountedRef_false", {
        page: pageRef.current,
      });
    };
  }, [logBootstrapDeadlockDiagnostic]);

  useEffect(() => {
    const effectSpan = startupExecutionBegin("useEffect:startup_recovery_watchdog", { hasRenderedPageContent });
    lifecycleTrace("app_effect_startup_recovery_start", { page: pageRef.current });
    if (detectInterruptedStartup()) {
      traceStartup("interrupted_startup_detected", { markers: getStartupMarkers() });
      clearInterruptedStartupTemporaryState();
      cleanupRanRef.current = true;
      cleanupRemovedKeysRef.current = ["temporary_startup_state_only"];
    }

    startupExecutionMark("setTimeout scheduled:startup_recovery_watchdog_8s", { delayMs: 8000, outsideFirstFiveSeconds: true });
    const startupRecoveryTimer = window.setTimeout(() => {
      const timerSpan = startupExecutionBegin("setTimeout:startup_recovery_watchdog_8s", { hasRenderedPageContent });
      if (!hasRenderedPageContent) {
        traceMark("startup_watchdog_8s", { page: pageRef.current });
        saveCrashDump("react_app_ready_timeout", { reactAppReady: false, page: pageRef.current });
        setWatchdogMessage("Запуск не завершился за 8 секунд.");
        setShowStartupRecovery(true);
        traceMark("startup_recovery_screen_requested", { page: pageRef.current });
      }
      startupExecutionEnd(timerSpan, { hasRenderedPageContent });
    }, 8000);

    startupExecutionEnd(effectSpan, { hasRenderedPageContent });
    return () => {
      const cleanupSpan = startupExecutionBegin("cleanup:startup_recovery_watchdog");
      lifecycleTrace("app_effect_startup_recovery_cleanup", { page: pageRef.current });
      window.clearTimeout(startupRecoveryTimer);
      startupExecutionEnd(cleanupSpan);
    };
  }, [hasRenderedPageContent]);

  const resetPartnerFlowState = useCallback((nextPage: PageId = "catalog") => {
    setSelectedPartner(null);
    setPartnerOffers([]);
    setPartnerOffersStatus("idle");
    setPartnerOffersError("");
    setPartnerOffersDiagnostic(null);
    setPage(isUnsafeStartupScreen(nextPage) ? "catalog" : nextPage);
  }, []);

  const loadAppData = useCallback(
    (reason: BootstrapReason = "initial", options: boolean | { forceRefresh?: boolean; forceNewIdentity?: boolean } = false) => {
      const forceRefresh = typeof options === "boolean" ? options : Boolean(options.forceRefresh);
      const forceNewIdentity = typeof options === "boolean" ? false : Boolean(options.forceNewIdentity);
      const forceNew = forceRefresh || forceNewIdentity;
      traceStartupRecovery("loadAppData:enter", { reason, forceNew, forceRefresh, forceNewIdentity });
      if (forceNew) {
        if (bootstrapPromiseRef.current) {
          logBootstrapDeadlockDiagnostic("bootstrapPromiseRef_cleared", {
            reason: forceNewIdentity ? "forceNewIdentity" : "forceRefresh",
          });
        }
        bootstrapPromiseRef.current = null;
        if (forceNewIdentity) {
          resetTelegramLoginInFlight();
        }
      } else if (bootstrapPromiseRef.current) {
        traceStartupRecovery("loadAppData:exit", {
          reason,
          forceNew,
          returnValue: "existing_bootstrap_promise",
        });
        return bootstrapPromiseRef.current;
      }

      const sequenceId = bootstrapSequenceRef.current + 1;
      bootstrapSequenceRef.current = sequenceId;
      logBootstrapDeadlockDiagnostic("bootstrapSequenceRef_updated", {
        sequenceId,
        reason,
        forceNew,
      });
      const isActive = () =>
        mountedRef.current && appActiveRef.current && bootstrapSequenceRef.current === sequenceId;

      if (isActive()) {
        setIsLoading(true);
        setError(null);
        setBrowserLoginRequired(false);
        setBrowserLoginExternalOpenRequired(false);
      }

      let bootstrapPromise: Promise<void> | undefined;
      bootstrapPromise = (async () => {
        let stage: AppStage = "telegram_runtime_check";
        const startedAt = performance.now();

        setStartupPhase("bootstrap_started", { reason, forceNew, sequenceId });
        lifecycleTrace("bootstrap_start", { reason, forceNew, sequenceId });
        setAuthRestoreStatus("restoring");
        setLastAuthDecisionReason("restore_started");
        traceMark("auth_started", { reason, sequenceId });
        traceStartup("loadAppData_called", { reason, forceNew, sequenceId });
        traceStart("loadAppData_started", { reason, forceNew, sequenceId });
        traceStartup("bootstrap_promise_created", { reason, forceNew, sequenceId });
        logBootstrapDiagnostic("app_bootstrap_start", {
          reason,
          forceNew,
          sequenceId,
        });

        const hardTimeoutId = window.setTimeout(() => {
          if (bootstrapPromiseRef.current === bootstrapPromise) {
            bootstrapPromiseRef.current = null;
            bootstrapSequenceRef.current += 1;
            resetTelegramLoginInFlight();
            setAuthRestoreStatus((current) => current === "authenticated" ? current : "restoring");
            setLastAuthDecisionReason("bootstrap_hard_timeout_neutral");
            setIsLoading(false);
            setWatchdogMessage(CONNECTION_PROBLEM_DESCRIPTION);
            setShowStartupRecovery(true);
            traceStartup("bootstrap_hard_timeout", { sequenceId, timeoutMs: BOOTSTRAP_HARD_TIMEOUT_MS });
            logBootstrapDeadlockDiagnostic("bootstrap_hard_timeout", {
              sequenceId,
              timeoutMs: BOOTSTRAP_HARD_TIMEOUT_MS,
            });
          }
        }, BOOTSTRAP_HARD_TIMEOUT_MS);

        try {
          let isTelegram = false;

          {
            lifecycleTrace("telegram_ready_start");
            lifecycleTrace("telegram_expand_start");
            traceStart("telegram_prepare_start");
            try {
              traceStartup("prepareTelegramViewport_started", { sequenceId });
              await traceStartupStep("prepareTelegramViewport", () => prepareTelegramViewport(), { sequenceId });
              traceStartup("prepareTelegramViewport_done", { sequenceId });
              lifecycleTrace("telegram_ready_ok");
              lifecycleTrace("telegram_expand_ok");
              traceOk("telegram_prepare_ok");
            } catch (prepareError) {
              lifecycleTrace("telegram_ready_fail", prepareError);
              lifecycleTrace("telegram_expand_fail", prepareError);
              traceFail("telegram_prepare_fail", prepareError);
              throw prepareError;
            }
            traceStart("telegram_runtime_check_start");
            isTelegram = await traceStartupStep("prepareTelegram:isTelegramRuntime", () => isTelegramRuntime(), { sequenceId });
            traceOk("telegram_runtime_check_ok", { isTelegram });
            if (isActive()) {
              setIsTelegramApp(isTelegram);
            }
          }

          const requestProfileAndSubscription = async () => {
            stage = "profile_request";
            traceStartup("loadAppData_profile_started");
            traceStartup("loadAppData_subscription_started");
            traceStart("stored_token_profile_start");
            traceStart("stored_token_subscription_start");
            const nextProfile = await traceStartupStep("restoreSession:getProfile", getProfile, { sequenceId });
            const nextSubscription = await traceStartupStep("restoreSession:getSubscription", getSubscription, { sequenceId });
            traceStartup("loadAppData_profile_success");
            traceOk("stored_token_profile_ok", {
              hasProfile: Boolean(nextProfile),
            });
            traceStartup("loadAppData_subscription_success");
            traceOk("stored_token_subscription_ok", {
              hasSubscription: Boolean(nextSubscription),
            });
            stage = "subscription_request";
            return { profile: nextProfile, subscription: nextSubscription };
          };

          const loginWithTelegramPayload = async (): Promise<boolean> => {
            stage = "init_data_read";
            traceStart("launch_payload_read_start");
            const telegramLaunchPayload =
              await getTelegramLaunchPayloadWithRetry();
            const hasValidInitData = hasValidTelegramMiniAppInitData(telegramLaunchPayload);
            traceStartupRecovery("loadAppData:telegram_payload_read", {
              reason,
              forceNew,
              sequenceId,
              hasTelegramPayload: Boolean(telegramLaunchPayload),
              hasValidTelegramPayload: hasValidInitData,
            });
            traceOk("launch_payload_read_ok", {
              hasPayload: Boolean(telegramLaunchPayload),
              hasValidInitData,
            });

            if (!hasValidInitData) {
              traceOk("telegram_login_skipped", {
                reason: telegramLaunchPayload
                  ? "invalid_init_data"
                  : "empty_init_data_browser_app",
                hasTelegramWebApp: Boolean(getTelegramWebApp()),
              });
              return false;
            }

            {
              stage = "telegram_login_prefetch";
              lifecycleTrace("login_start", { reason, sequenceId });
              traceStartup("loadAppData_login_started", { reason, sequenceId });
              traceStart("telegram_login_start", { reason, sequenceId });
              const telegramStartParam = getTelegramStartParam();
              const referralCode = getReferralCodeFromStartParam(telegramStartParam);
              const telegramRuntimeDiagnostics = getTelegramRuntimeDiagnostics();
              traceOk("telegram_start_param_sources", {
                sourceNames: telegramRuntimeDiagnostics.startParamSourceNames,
                initDataHasStartParamKey: telegramRuntimeDiagnostics.initDataHasStartParamKey,
                locationHasStartParamKey: telegramRuntimeDiagnostics.locationHasStartParamKey,
                locationSearchHasStartParamKey: telegramRuntimeDiagnostics.locationSearchHasStartParamKey,
                locationHashHasStartParamKey: telegramRuntimeDiagnostics.locationHashHasStartParamKey,
                retrieveLaunchParamsHasStartParam: telegramRuntimeDiagnostics.retrieveLaunchParamsHasStartParam,
                retrieveLaunchParamsHasInitDataRaw: telegramRuntimeDiagnostics.retrieveLaunchParamsHasInitDataRaw,
                hasStartParam: telegramStartParam.length > 0,
                startParamLength: telegramStartParam.length,
                hasReferralCode: Boolean(referralCode),
                referralCodeLength: referralCode?.length ?? 0,
              });
              await traceStartupStep("restoreSession:loginWithTelegram", () => loginWithTelegram(telegramLaunchPayload, {
                reason,
                bootstrapAttemptId: sequenceId,
                forceNew: true,
                referralCode,
                startParam: telegramStartParam || referralCode,
              }), { sequenceId });
              stage = "telegram_login_request";
              lifecycleTrace("login_ok", { sequenceId });
              traceStartup("loadAppData_login_success", { sequenceId });
              traceOk("telegram_login_ok");
              return true;
            }
          };

          let profile: ClientProfile;
          let subscription: Subscription;
          lifecycleTrace("stored_token_auth_start", { forceNew, forceRefresh, forceNewIdentity });
          traceStart("stored_token_check_start");
          traceStartup("storage_read_started", { key: AUTH_STORAGE_KEY });
          const authSnapshot = getAuthTokenStorageSnapshot();
          authSnapshotRef.current = authSnapshot;
          // Deterministic replacement for legacy startup read: const storedAuthToken = getStoredAuthToken();
          const storedAuthToken = authSnapshot.token;
          traceStartupRecovery("loadAppData:auth_snapshot", {
            reason,
            forceNew,
            sequenceId,
            hasStoredAuthToken: Boolean(storedAuthToken),
            tokenSource: authSnapshot.tokenSource,
          });
          if (authSnapshot.storageReadError) {
            setAuthRestoreStatus("invalid");
            setLastAuthDecisionReason("storage_read_failed");
            reportClientError("auth_storage_read_failed", new Error(authSnapshot.storageReadError), { authRestoreStatus: "invalid", tokenSource: authSnapshot.tokenSource });
            throw new Error("auth_storage_read_failed");
          }
          traceStartup("storage_read_done", { key: AUTH_STORAGE_KEY, hasStoredToken: Boolean(storedAuthToken), tokenSource: authSnapshot.tokenSource });
          traceResumeAuthDiagnostic("startup_auth_check", {
            startupReason: reason,
            hasStoredToken: Boolean(storedAuthToken),
            tokenStorageKey: AUTH_STORAGE_KEY,
            authCheckStatus: "started",
          });
          lifecycleTrace("stored_token_auth_ok", {
            hasStoredAuthToken: Boolean(storedAuthToken),
            forceNew,
            forceRefresh,
            forceNewIdentity,
          });
          traceOk("stored_token_check_ok", {
            hasStoredAuthToken: Boolean(storedAuthToken),
            forceNew,
            forceRefresh,
            forceNewIdentity,
          });

          // Resume and refresh flows must always prefer the existing stored token.
          // Only explicit identity replacement flows may bypass stored-token auth.
          if (storedAuthToken && !forceNewIdentity) {
            try {
              ({ profile, subscription } =
                await requestProfileAndSubscription());
            } catch (caughtError) {
              if (!isAuthInvalidStatus(caughtError)) {
                traceResumeAuthDiagnostic("stored_token_auth_check_non_auth_error", {
                  startupReason: reason,
                  hasStoredToken: true,
                  tokenStorageKey: AUTH_STORAGE_KEY,
                  authCheckStatus: isApiError(caughtError) ? caughtError.status : "network_or_unknown",
                  authClearedReason: null,
                });
                throw caughtError;
              }

              const authFailureStatus = isApiError(caughtError) ? caughtError.status : undefined;
              lifecycleTrace("stored_token_auth_fail", caughtError);
              traceFail("stored_token_profile_fail", caughtError);
              traceFail("stored_token_subscription_fail", caughtError);
              traceResumeAuthDiagnostic("stored_token_auth_cleared", {
                startupReason: reason,
                hasStoredToken: true,
                tokenStorageKey: AUTH_STORAGE_KEY,
                authCheckStatus: authFailureStatus,
                authClearedReason: "auth_check_401_403",
              });
              clearStoredAuthToken();
              setAuthRestoreStatus("invalid");
              setLastAuthDecisionReason("auth_check_401_403");
              // Stale JWT still attempts Telegram Mini App auth when valid initData exists: await loginWithTelegramPayload();
              if (!(await loginWithTelegramPayload())) {
                setAuthRestoreStatus("unauthenticated");
                setLastAuthDecisionReason("no_valid_token_no_telegram_payload_after_401");
                setBrowserLoginRequired(true);
                setIsBootstrapDone(true);
                await loadPartners(true).catch(() => undefined);
                traceStartupRecovery("loadAppData:exit", { reason, forceNew, sequenceId, returnValue: "unauthenticated_after_invalid_stored_token" });
                return;
              }
              traceStart("fresh_profile_start");
              traceStart("fresh_subscription_start");
              ({ profile, subscription } =
                await requestProfileAndSubscription());
              traceOk("fresh_profile_ok", { hasProfile: Boolean(profile) });
              traceOk("fresh_subscription_ok", {
                hasSubscription: Boolean(subscription),
              });
            }
          } else {
            if (!(await loginWithTelegramPayload())) {
              setAuthRestoreStatus("unauthenticated");
              setLastAuthDecisionReason("no_token_no_telegram_payload_restore_complete");
              setBrowserLoginRequired(true);
              setIsBootstrapDone(true);
              await loadPartners(true).catch(() => undefined);
              traceStartupRecovery("loadAppData:exit", { reason, forceNew, sequenceId, returnValue: "unauthenticated_no_token_or_payload" });
              return;
            }
            traceStart("fresh_profile_start");
            traceStart("fresh_subscription_start");
            ({ profile, subscription } = await requestProfileAndSubscription());
            traceOk("fresh_profile_ok", { hasProfile: Boolean(profile) });
            traceOk("fresh_subscription_ok", {
              hasSubscription: Boolean(subscription),
            });
          }

          setAuthRestoreStatus("authenticated");
          setLastAuthDecisionReason("authenticated_profile_loaded");
          traceMark("auth_finished", { sequenceId });
          const postAuthMounted = mountedRef.current;
          const postAuthBootstrapSequence = bootstrapSequenceRef.current;
          const postAuthIsActive = isActive();

          traceStartup("loadAppData_before_post_auth_isActive_guard", {
            sequenceId,
            mounted: postAuthMounted,
            bootstrapSequence: postAuthBootstrapSequence,
            isActive: postAuthIsActive,
          });

          if (!isActive()) {
            traceStartup("loadAppData_post_auth_isActive_guard_return", {
              sequenceId,
              mounted: postAuthMounted,
              bootstrapSequence: postAuthBootstrapSequence,
              reason: !postAuthMounted
                ? "mountedRef_false"
                : postAuthBootstrapSequence !== sequenceId
                  ? "sequence_mismatch"
                  : "unknown",
            });
            traceStartupRecovery("loadAppData:exit", { reason, forceNew, sequenceId, returnValue: "inactive_after_auth" });
            return;
          }

          traceStart("stale_state_cleanup_start");
          resetCatalogStateForForceReload();
          clearStaleAppState();
          traceOk("stale_state_cleanup_ok");
          traceStart("partner_flow_reset_start");
          resetPartnerFlowState(getStartupPage() === "catalog" ? "catalog" : "home");
          traceOk("partner_flow_reset_ok");

          traceStart("app_data_set_start");
          traceStartup("first_setState_after_mount", { sequenceId });
          setData(
            normalizeAppData({
              profile,
              subscription,
              partners: [],
              verifications: [],
              savings: null,
              cities: [],
              linkingStatus: null,
              giveawayState: null,
            }),
          );

          traceOk("app_data_set_ok", { page: pageRef.current });
          setIsLoading(false);

          if (hasCatalogRecoveryFlag()) {
            console.info("catalog_recovery_flag_detected", { sequenceId, page: pageRef.current });
            traceStartup("catalog_recovery_flag_detected", { sequenceId, page: pageRef.current });
            setCatalogRecoveryPending(true);
            setPage("catalog");
            setPartnersErrorTitle("Загрузка клуба прервана");
            setPartnersError(CATALOG_RECOVERY_MESSAGE);
          } else if (pageRef.current === "catalog") {
            console.info("catalog_reload_after_bootstrap", {
              sequenceId,
              page: pageRef.current,
              reason: "startup_core_catalog_load",
            });
            traceStartup("loadAppData_core_catalog_requested", { sequenceId });
            startupExecutionMark("setTimeout removed:startup_core_catalog_load_serial", { sequenceId });
            await traceStartupStep("catalog bootstrap:loadPartners", () => loadPartners(true), { sequenceId, source: "startup_core_catalog_load" });
          }

          traceStartup("loadAppData_optional_requests_started", { sequenceId });
          traceStart("secondary_requests_start");
          traceStart("verifications_start");
          traceStart("savings_start");
          traceStart("cities_start");
          traceStart("linking_status_start");
          const settleStartupStep = async <T,>(label: string, fn: () => Promise<T>) => {
            try {
              return { status: "fulfilled" as const, value: await traceStartupStep(label, fn, { sequenceId }) };
            } catch (reason) {
              return { status: "rejected" as const, reason };
            }
          };
          const verificationsResult = await settleStartupStep("secondary:getVerifications", getVerifications);
          const savingsResult = await settleStartupStep("secondary:getSavings", getSavings);
          const citiesResult = await settleStartupStep("secondary:getCities", getCities);
          const linkingStatusResult = await settleStartupStep("secondary:getLinkingStatus", getLinkingStatus);
          const giveawayStateResult = await settleStartupStep("secondary:getGiveawayState", getGiveawayState);

          traceStartup("loadAppData_before_post_optional_isActive_guard", {
            sequenceId,
            mounted: mountedRef.current,
            bootstrapSequence: bootstrapSequenceRef.current,
            isActive: isActive(),
          });

          if (!isActive()) {
            traceStartup("loadAppData_post_optional_isActive_guard_return", {
              sequenceId,
              mounted: mountedRef.current,
              bootstrapSequence: bootstrapSequenceRef.current,
              reason: !mountedRef.current
                ? "mountedRef_false"
                : bootstrapSequenceRef.current !== sequenceId
                  ? "sequence_mismatch"
                  : "unknown",
            });
            traceStartupRecovery("loadAppData:exit", { reason, forceNew, sequenceId, returnValue: "inactive_after_optional_requests" });
            return;
          }

          lifecycleTrace("secondary_requests_ok", { sequenceId });
          traceStartup("loadAppData_optional_requests_finished", { sequenceId });
          traceMark("secondary_requests_done", {
            verifications: verificationsResult.status,
            savings: savingsResult.status,
            cities: citiesResult.status,
            linkingStatus: linkingStatusResult.status,
            giveawayState: giveawayStateResult.status,
          });
          verificationsResult.status === "fulfilled"
            ? traceOk("verifications_ok")
            : traceFail("verifications_fail", verificationsResult.reason);
          savingsResult.status === "fulfilled"
            ? traceOk("savings_ok")
            : traceFail("savings_fail", savingsResult.reason);
          citiesResult.status === "fulfilled"
            ? traceOk("cities_ok")
            : traceFail("cities_fail", citiesResult.reason);
          linkingStatusResult.status === "fulfilled"
            ? traceOk("linking_status_ok")
            : traceFail("linking_status_fail", linkingStatusResult.reason);
          giveawayStateResult.status === "fulfilled"
            ? traceOk("giveaway_state_ok")
            : traceFail("giveaway_state_fail", giveawayStateResult.reason);

          const nextLinkingStatus =
            linkingStatusResult.status === "fulfilled"
              ? linkingStatusResult.value
              : null;

          setData((current) =>
            normalizeAppData({
              ...current,
              verifications:
                verificationsResult.status === "fulfilled"
                  ? verificationsResult.value
                  : current.verifications,
              savings:
                savingsResult.status === "fulfilled"
                  ? savingsResult.value
                  : current.savings,
              cities:
                citiesResult.status === "fulfilled"
                  ? citiesResult.value
                  : current.cities,
              linkingStatus: nextLinkingStatus ?? current.linkingStatus,
              giveawayState:
                giveawayStateResult.status === "fulfilled"
                  ? giveawayStateResult.value
                  : current.giveawayState,
            }),
          );

          const dismissedKey = getLinkingDismissKey(profile);
          setShouldShowLinking(
            shouldShowLinkingOnboarding(
              isTelegram,
              profile,
              nextLinkingStatus,
              dismissedKey,
            ),
          );

          setIsBootstrapDone(true);
          lifecycleTrace("bootstrap_ok", { sequenceId, page: pageRef.current });
          traceStartup("loadAppData_finished", { sequenceId, page: pageRef.current });
          traceOk("bootstrap_done", { sequenceId, page: pageRef.current });
          traceOk("startup_completed_successfully", { sequenceId, page: pageRef.current });
          markBootstrapFinished();
          markStartupCompletedSuccessfully();
          traceStartupRecovery("loadAppData:exit", { reason, forceNew, sequenceId, returnValue: "bootstrap_success" });
          setPreviousCrashDump(null);
          logBootstrapDiagnostic("app_bootstrap_success", {
            sequenceId,
            elapsedMs: Math.max(0, Math.round(performance.now() - startedAt)),
            hasProfile: Boolean(profile),
            hasSubscription: Boolean(subscription),
            secondaryRequests: {
              verifications: verificationsResult.status,
              savings: savingsResult.status,
              cities: citiesResult.status,
              linkingStatus: linkingStatusResult.status,
            },
          });
        } catch (caughtError) {
          const error = caughtError instanceof Error ? caughtError : null;
          traceMark("auth_finished", { sequenceId, failed: true, stage });
          lifecycleTrace("bootstrap_fail", { stage, error: caughtError });
          traceStartup("loadAppData_failed", { stage, error: caughtError });
          traceFail(`${stage}_fail`, caughtError);
          saveCrashDump("fatal_startup_error", { stage });
          logBootstrapDiagnostic("app_bootstrap_error", {
            sequenceId,
            stage,
            errorName: safeDiagnosticText(error?.name),
            errorMessageShort: safeDiagnosticText(
              error?.message ?? caughtError,
            ),
            elapsedMs: Math.max(0, Math.round(performance.now() - startedAt)),
          });
          if (isActive()) {
            setError(createDiagnostic(stage, caughtError));
          }
          traceStartupRecovery("loadAppData:exit", { reason, forceNew, sequenceId, returnValue: "bootstrap_failed", stage });
        } finally {
          window.clearTimeout(hardTimeoutId);
          if (isActive()) {
            setIsLoading(false);
          }

          if (bootstrapPromiseRef.current === bootstrapPromise) {
            bootstrapPromiseRef.current = null;
            logBootstrapDeadlockDiagnostic("bootstrapPromiseRef_cleared", {
              reason: "finally",
              sequenceId,
            });
          }
        }
      })();

      bootstrapPromiseRef.current = bootstrapPromise;
      logBootstrapDeadlockDiagnostic("bootstrapPromiseRef_created", {
        sequenceId,
        reason,
        forceNew,
      });
      traceStartupRecovery("loadAppData:exit", {
        reason,
        forceNew,
        sequenceId,
        returnValue: "new_bootstrap_promise",
      });
      return bootstrapPromise;
    },
    [logBootstrapDeadlockDiagnostic, resetCatalogStateForForceReload, resetPartnerFlowState],
  );

  useEffect(() => {
    const effectSpan = startupExecutionBegin("useEffect:bootstrap_loadAppData");
    void traceStartupStep("bootstrap()", () => loadAppData(), { reason: "initial" }).finally(() => {
      startupExecutionEnd(effectSpan);
    });
  }, [loadAppData, logBootstrapDeadlockDiagnostic]);

  useEffect(() => {
    const effectSpan = startupExecutionBegin("useEffect:lifecycle_listeners");
    const refreshAfterWebViewResume = (event: PageTransitionEvent | Event) => {
      const listenerSpan = startupExecutionBegin("lifecycle_listener:refreshAfterWebViewResume", { eventType: event.type });
      lifecycleTrace("webview_resume_prepare_start", {
        eventType: event.type,
        persisted:
          event instanceof PageTransitionEvent ? event.persisted : undefined,
        visibilityState: document.visibilityState,
      });
      try {
        traceStartup("telegram_viewport_prepare_called", { eventType: event.type });
        prepareTelegramViewport();
        traceStartup("telegram_viewport_prepare_finished", { eventType: event.type });
        lifecycleTrace("webview_resume_prepare_ok", { eventType: event.type });
      } catch (caughtError) {
        lifecycleTrace("webview_resume_prepare_fail", caughtError);
        startupExecutionFail(listenerSpan, caughtError);
        return;
      }
      startupExecutionEnd(listenerSpan, { eventType: event.type });
    };

    const resumeWithoutAuthReset = (event: PageTransitionEvent | Event) => {
      traceStartupRecovery("resumeWithoutAuthReset:enter", { eventType: event.type });
      const listenerSpan = startupExecutionBegin("lifecycle_listener:resumeWithoutAuthReset", { eventType: event.type });
      const pageshowPersisted =
        event instanceof PageTransitionEvent ? event.persisted : undefined;
      logBootstrapDeadlockDiagnostic("webview_resume", {
        lifecycleEvent: event.type,
        persisted: pageshowPersisted,
      });
      traceResumeAuthDiagnostic("resume_event", {
        startupReason: "resume",
        hasStoredToken: Boolean(getStoredAuthToken()),
        tokenStorageKey: AUTH_STORAGE_KEY,
        authCheckStatus: "not_run_on_resume",
        authClearedReason: null,
        pageshowPersisted,
        visibilityState: document.visibilityState,
        resumeEvent: event.type,
        didForceReload: false,
      });
      refreshAfterWebViewResume(event);
      startupExecutionEnd(listenerSpan, { eventType: event.type });
      traceStartupRecovery("resumeWithoutAuthReset:exit", { eventType: event.type, returnValue: undefined });
    };

    const markInactive = (event: Event) => {
      const listenerSpan = startupExecutionBegin("lifecycle_listener:markInactive", { eventType: event.type });
      logBootstrapDeadlockDiagnostic("webview_inactive", { lifecycleEvent: event.type });
      traceStartup("webview_inactive", { eventType: event.type });
      if (catalogLoadingRef.current || partnersPromiseRef.current) {
        setCatalogRecoveryFlag();
        console.info("catalog_load_aborted_on_hide", { eventType: event.type, page: pageRef.current });
        traceStartup("catalog_load_aborted_on_hide", { eventType: event.type, page: pageRef.current });
      }
      if (!window.__BLOOM_STARTUP_PHASE__ || !["first_visible_paint", "bootstrap_finished"].includes(String(window.__BLOOM_STARTUP_PHASE__))) {
        markStartupInterrupted(event.type);
      }
      abortInFlightCatalogLoad(event.type);
      invalidateBootstrapForInactiveWebView(event.type);
      startupExecutionEnd(listenerSpan, { eventType: event.type });
    };

    const onPageShow = (event: PageTransitionEvent) => {
      traceStartupRecovery("pageshow:enter", { persisted: event.persisted });
      lastPageshowAtRef.current = new Date().toISOString();
      traceStartup("pageshow", { persisted: event.persisted });
      resumeWithoutAuthReset(event);
      const interruptedStartup = detectInterruptedStartup();
      traceStartupRecovery("pageshow:detectInterruptedStartup_return", {
        persisted: event.persisted,
        returnValue: interruptedStartup,
      });
      // Startup recovery refreshes app data but must preserve stored-token auth on PWA resume.
      if (interruptedStartup) { void loadAppData("resume", false); }
      traceStartupRecovery("pageshow:exit", { persisted: event.persisted, returnValue: undefined });
    };
    const onPageHide = (event: PageTransitionEvent) => { lastPagehideAtRef.current = new Date().toISOString(); markInactive(event); };
    const onResume = (event: Event) => resumeWithoutAuthReset(event);
    const onFocus = (event: Event) => {
      traceStartup("focus");
      resumeWithoutAuthReset(event);
    };
    const onBlur = (event: Event) => markInactive(event);
    const onVisibilityChange = (event: Event) => {
      traceStartup("visibilitychange", { visibilityState: document.visibilityState });
      if (document.visibilityState === "visible") {
        resumeWithoutAuthReset(event);
      } else if (document.visibilityState === "hidden") {
        markInactive(event);
      }
    };

    window.addEventListener("pageshow", onPageShow);
    window.addEventListener("pagehide", onPageHide);
    window.addEventListener("focus", onFocus);
    window.addEventListener("blur", onBlur);
    document.addEventListener("resume", onResume);
    document.addEventListener("visibilitychange", onVisibilityChange);

    const telegramWebApp = window.Telegram?.WebApp;
    const onTelegramActivated = () => resumeWithoutAuthReset(new Event("telegram_activated"));
    const onTelegramDeactivated = () => markInactive(new Event("telegram_deactivated"));
    telegramWebApp?.onEvent?.("activated" as never, onTelegramActivated);
    telegramWebApp?.onEvent?.("deactivated" as never, onTelegramDeactivated);
    startupExecutionEnd(effectSpan);

    return () => {
      const cleanupSpan = startupExecutionBegin("cleanup:lifecycle_listeners");
      window.removeEventListener("pageshow", onPageShow);
      window.removeEventListener("pagehide", onPageHide);
      window.removeEventListener("focus", onFocus);
      window.removeEventListener("blur", onBlur);
      document.removeEventListener("resume", onResume);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      telegramWebApp?.offEvent?.("activated" as never, onTelegramActivated);
      telegramWebApp?.offEvent?.("deactivated" as never, onTelegramDeactivated);
      startupExecutionEnd(cleanupSpan);
    };
  }, [abortInFlightCatalogLoad, invalidateBootstrapForInactiveWebView, loadAppData, logBootstrapDeadlockDiagnostic, resetStaleBootstrapForActiveWebView]);

  const loadPartners = useCallback(
    (forceRetry = true) => {
      const logCatalogReturn = (reason: string) => {
        console.info("catalog_return", {
          reason,
          force: forceRetry,
          catalogLoaded: hasPartnersLoaded,
          catalogLoading: isPartnersLoading,
          hasInflight: Boolean(partnersPromiseRef.current),
          partnersCount: data.partners.length,
          hasError: Boolean(partnersError),
          hasDiagnostic: Boolean(partnersErrorDetails),
        });
      };

      if (forceRetry) {
        resetCatalogStateForForceReload();
      } else if (partnersPromiseRef.current) {
        console.info("catalog_load_skipped_with_reason", {
          reason: "inflight",
          forceRetry,
        });
        logCatalogReturn("inflight");
        return partnersPromiseRef.current;
      }

      const localRequestId = catalogLoadSequenceRef.current + 1;
      catalogLoadSequenceRef.current = localRequestId;
      const startedAtIso = new Date().toISOString();
      const catalogAbortController = new AbortController();
      catalogAbortControllerRef.current = catalogAbortController;

      let promise: Promise<void>;
      promise = (async () => {
        const catalogSpan = startupExecutionBegin("catalog bootstrap:loadPartners body", { forceRetry, localRequestId });
        catalogTrace("catalog requested", { forceRetry, localRequestId });
        traceStartup("loadPartners_called", { forceRetry, localRequestId });
        console.info("catalog_diagnostic_loadPartners_entered", { forceRetry, localRequestId });
        catalogTrace("loadPartners entered", { forceRetry, localRequestId });
        traceStartup("loadPartners_entered", { forceRetry, localRequestId });
        traceStart("catalog_load_start", { forceRetry, localRequestId });
        console.info("catalog_load_started", {
          forceRetry,
          localRequestId,
          startedAtIso,
        });
        catalogLoadingRef.current = true;
        setIsPartnersLoading(true);
        setPartnersError("");
        setPartnersErrorDetails(undefined);
        setCatalogErrorCreatedAt(undefined);
        setCatalogLoadStartedAt(startedAtIso);
        setCatalogLoadRequestId(localRequestId);

        try {
          const bootstrapPartners = forceRetry ? null : consumeCatalogBootstrap();
          traceStartup("loadPartners_before_getPartners", { localRequestId });
          console.info("catalog_diagnostic_loadPartners_before_getPartners_await", { localRequestId });
          catalogTrace("getPartners entered", { localRequestId });
          // Regression anchor: previous code used `const partners = await getPartners();`;
          // keep catalog fetch non-bootstrap-blocking while allowing lifecycle aborts.
          const partners = await getPartners({ signal: catalogAbortController.signal });
          traceStartup("loadPartners_after_getPartners", { localRequestId, partnersCount: partners.length });
          console.info("catalog_diagnostic_loadPartners_after_getPartners_await", { localRequestId, partnersCount: partners.length });
          if (catalogAbortController.signal.aborted) {
            traceStartup("loadPartners_aborted_before_state_update", { localRequestId });
            return;
          }
          if (bootstrapPartners && partners.length === 0) {
            console.info("catalog_bootstrap_replaced_by_empty_fetch", {
              bootstrapCount: bootstrapPartners.length,
              localRequestId,
            });
          }
          traceStartup("loadPartners_before_setPartners", { localRequestId, partnersCount: partners.length });
          console.info("catalog_diagnostic_loadPartners_before_setPartners", { localRequestId, partnersCount: partners.length });
          setData((current) => normalizeAppData({ ...current, partners }));
          traceStartup("loadPartners_after_setPartners", { localRequestId, partnersCount: partners.length });
          console.info("catalog_diagnostic_loadPartners_after_setPartners", { localRequestId, partnersCount: partners.length });
          setHasPartnersLoaded(true);
          lifecycleTrace("catalog_load_ok", {
            partnersCount: partners.length,
            source: "fetch",
            hadBootstrap: Boolean(bootstrapPartners),
          });
          catalogTrace("catalog rendered", { localRequestId, partnersCount: partners.length });
          traceStartup("loadPartners_success", { localRequestId, partnersCount: partners.length });
          traceOk("catalog_load_ok", {
            partnersCount: partners.length,
            source: "fetch",
            hadBootstrap: Boolean(bootstrapPartners),
          });
          console.info("catalog_load_success", {
            partnersCount: partners.length,
            localRequestId,
            source: "fetch",
            hadBootstrap: Boolean(bootstrapPartners),
          });
        } catch (caughtError) {
          const diagnostic = isCatalogLoadError(caughtError)
            ? caughtError.diagnostic
            : undefined;
          lifecycleTrace("catalog_load_fail", caughtError);
          catalogTrace("fetch rejected", { localRequestId, error: caughtError });
          traceStartup("loadPartners_error", { localRequestId, error: caughtError });
          traceFail("catalog_load_fail", caughtError);
          saveCrashDump("catalog_load_interrupted", { localRequestId });
          if (typeof window !== "undefined") {
            window.__BLOOM_LAST_CATALOG_ERROR__ = diagnostic ?? caughtError;
          }
          console.info(
            "catalog_load_failed",
            diagnostic ?? {
              errorName:
                caughtError instanceof Error ? caughtError.name : undefined,
              errorMessage:
                caughtError instanceof Error
                  ? safeDiagnosticText(caughtError.message)
                  : undefined,
            },
          );
          if (catalogAbortController.signal.aborted) {
            traceStartup("loadPartners_aborted", { localRequestId, reason: String(catalogAbortController.signal.reason ?? "") });
            return;
          }
          setCatalogErrorCreatedAt(new Date().toISOString());
          setPartnersErrorTitle(
            TG_LOCAL_CATALOG_ENABLED
              ? "Не удалось загрузить каталог Telegram"
              : "Не удалось загрузить каталог",
          );
          setPartnersError(
            diagnostic?.abortSource === "timeout"
              ? "Загрузка каталога заняла слишком много времени. Закройте этот экран или попробуйте ещё раз."
              : TG_LOCAL_CATALOG_ENABLED
                ? "Проверьте подключение и попробуйте снова."
                : "Не удалось загрузить каталог",
          );
          setPartnersErrorDetails(
            diagnostic
              ? {
                  source: diagnostic.source,
                  requestUrl: diagnostic.requestUrl,
                  requestUrlPath: diagnostic.requestUrlPath,
                  requestOrigin: diagnostic.requestOrigin,
                  httpStatus: diagnostic.httpStatus,
                  requestId: diagnostic.requestId,
                  elapsedMs: diagnostic.elapsedMs,
                  attempt: diagnostic.attempt,
                  fetchPhase: diagnostic.fetchPhase,
                  errorName: diagnostic.errorName,
                  isAbortError: diagnostic.isAbortError,
                }
              : undefined,
          );
        } finally {
          traceStartup("loadPartners_finally", { localRequestId, signalAborted: catalogAbortController.signal.aborted });
          console.info("catalog_diagnostic_loadPartners_finally", {
            localRequestId,
            signalAborted: catalogAbortController.signal.aborted,
            abortReason: String(catalogAbortController.signal.reason ?? ""),
          });
          catalogLoadingRef.current = false;
          setIsPartnersLoading(false);
          partnersPromiseRef.current = null;
          if (!hasCatalogRecoveryFlag()) clearCatalogRecoveryFlag();
          startupExecutionEnd(catalogSpan, { localRequestId });
        }
      })();

      partnersPromiseRef.current = promise;
      logCatalogReturn("started");
      return promise;
    },
    [
      data.partners.length,
      hasPartnersLoaded,
      isPartnersLoading,
      partnersError,
      partnersErrorDetails,
      resetCatalogStateForForceReload,
    ],
  );

  const openCatalog = useCallback(() => {
    lifecycleTrace("catalog_open", { forceReload: false });
    console.info("catalog_open_requested", {
      catalogLoaded: hasPartnersLoaded,
      catalogLoading: isPartnersLoading,
      partnersCount: data.partners.length,
      hasCatalogError: Boolean(partnersError),
      hasCatalogDiagnostic: Boolean(partnersErrorDetails),
      forceReload: false,
    });

    setSelectedPartner(null);
    setPartnerOffers([]);
    setPartnerOffersStatus("idle");
    setPartnerOffersError("");
    setPartnerOffersDiagnostic(null);
    scrollAppToTop();
    setPage("catalog");
    if (hasCatalogRecoveryFlag() || catalogRecoveryPending) {
      console.info("catalog_recovery_flag_detected", { source: "openCatalog" });
      traceStartup("catalog_recovery_flag_detected", { source: "openCatalog" });
      setCatalogRecoveryPending(true);
      setPartnersErrorTitle("Загрузка клуба прервана");
      setPartnersError(CATALOG_RECOVERY_MESSAGE);
      return;
    }
    startupExecutionMark("setTimeout removed:openCatalog_loadPartners_serial");
    void traceStartupStep("catalog open:loadPartners", () => loadPartners(false), { forceRetry: false });
  }, [
    data.partners.length,
    hasPartnersLoaded,
    isPartnersLoading,
    loadPartners,
    partnersError,
    partnersErrorDetails,
    catalogRecoveryPending,
  ]);

  const navigate = useCallback(
    (nextPage: PageId) => {
      if (nextPage === "catalog") {
        openCatalog();
        return;
      }

      lifecycleTrace("page_transition_request", { nextPage });
      scrollAppToTop();
      setPage(nextPage);
    },
    [openCatalog],
  );

  const cancelCatalogLoad = useCallback(() => {
    lifecycleTrace("recovery_action", { action: "cancel_catalog_load" });
    console.info("catalog_load_cancelled_by_user", { page: pageRef.current });
    abortInFlightCatalogLoad("user_cancel_catalog");
    clearCatalogRecoveryFlag();
    setCatalogRecoveryPending(false);
    setPartnersError("");
    setPartnersErrorDetails(undefined);
    setCatalogErrorCreatedAt(undefined);
    setPage("home");
  }, [abortInFlightCatalogLoad]);

  const retryCatalogAfterRecovery = useCallback(() => {
    clearCatalogRecoveryFlag();
    setCatalogRecoveryPending(false);
    setPartnersError("");
    setPartnersErrorDetails(undefined);
    void loadPartners(true);
  }, [loadPartners]);

  const loadPartnerOffers = useCallback(async (partner: Partner) => {
    const resolved = resolveNumericPartnerId(partner);

    setPartnerOffers([]);
    setPartnerOffersError("");
    setPartnerOffersDiagnostic(null);
    lifecycleTrace("offers_load_start", { hasPartner: Boolean(partner) });
    traceStart("offers_load_start", { hasPartner: Boolean(partner) });
    setPartnerOffersStatus("loading");

    if (!resolved) {
      traceFail("offers_load_fail", { reason: "missing_numeric_partner_id" });
      setPartnerOffersStatus("error");
      setPartnerOffersError("Не удалось загрузить предложения партнёра");
      setPartnerOffersDiagnostic({
        partnerIdSource: "partner.id",
        partnerIdMissingOrInvalid: true,
        backendDetail:
          "partner.id отсутствует или не является numeric Partner.id.",
      });
      return;
    }

    const offersUrlPath = getPartnerOffersPath(resolved.numericPartnerId);
    const baseDiagnostic: PartnerOffersDiagnostic = {
      numericPartnerId: resolved.numericPartnerId,
      partnerIdSource: resolved.source,
      offersUrlPath,
      source: TG_LOCAL_CATALOG_ENABLED
        ? "tg_local_catalog"
        : "web_legacy_catalog",
    };

    try {
      const response = await getPartnerOffers(resolved.numericPartnerId);
      const safeOffers = normalizeOffersResponse(response);
      setPartnerOffers(safeOffers);
      setPartnerOffersStatus(safeOffers.length ? "success" : "empty");
      lifecycleTrace("offers_load_ok", { offersCount: safeOffers.length });
      traceOk("offers_load_ok", { offersCount: safeOffers.length });
    } catch (caughtError) {
      lifecycleTrace("offers_load_fail", caughtError);
      traceFail("offers_load_fail", caughtError);
      setPartnerOffers([]);
      setPartnerOffersDiagnostic({
        ...baseDiagnostic,
        httpStatus: isApiError(caughtError) ? caughtError.status : undefined,
        backendDetail: isApiError(caughtError)
          ? safeDiagnosticText(caughtError.detail)
          : undefined,
      });

      if (isTimeoutError(caughtError)) {
        setPartnerOffersStatus("timeout");
        setPartnerOffersError("Не удалось загрузить предложения партнёра");
      } else if (isApiError(caughtError) && caughtError.status === 401) {
        setPartnerOffersStatus("error");
        setPartnerOffersError("Сессия истекла, откройте приложение заново");
      } else {
        setPartnerOffersStatus("error");
        setPartnerOffersError("Не удалось загрузить предложения партнёра");
      }
    } finally {
      setPartnerOffersStatus((current) =>
        current === "loading" ? "error" : current,
      );
    }
  }, []);

  const openPartner = useCallback(
    (partner: Partner) => {
      lifecycleTrace("partner_open", { hasPartner: Boolean(partner) });
      traceStart("partner_open_start", { hasPartner: Boolean(partner) });
      setSelectedPartner(partner);
      setPage("partner");
      void loadPartnerOffers(partner);
    },
    [loadPartnerOffers],
  );

  const retryPartnerOffers = useCallback(() => {
    lifecycleTrace("recovery_action", { action: "retry_partner_offers" });
    if (selectedPartner) {
      void loadPartnerOffers(selectedPartner);
    }
  }, [loadPartnerOffers, selectedPartner]);

  const refreshProfileAndSubscription = useCallback(async () => {
    const profile = await traceStartupStep("action:refreshProfile.getProfile", getProfile);
    const subscription = await traceStartupStep("action:refreshProfile.getSubscription", getSubscription);
    setData((current) =>
      normalizeAppData({ ...current, profile, subscription }),
    );
    return { profile, subscription };
  }, []);

  const saveProfile = useCallback(async (payload: ClientProfilePatch) => {
    try {
      await updateProfile(payload);
      const profile = await getProfile();
      setData((current) => normalizeAppData({ ...current, profile }));
      return profile;
    } catch (caughtError) {
      throw caughtError;
    }
  }, []);


  const requireRegisteredUser = useCallback(() => {
    if (!data.profile) {
      setGuestRestrictionMessage(true);
      return true;
    }
    return false;
  }, [data.profile]);

  const activateTrial = useCallback(async () => {
    if (requireRegisteredUser()) throw new Error("registration_required");
    setTrialMessage(null);

    try {
      const trialResponse = await activateTrialSubscription();
      const trialPayload = extractTrialPayload(trialResponse);
      const subscription = trialPayload.subscription || trialResponse;
      setData((current) =>
        normalizeAppData({
          ...current,
          profile: trialPayload.profile || current.profile,
          subscription,
        }),
      );
      const refreshed = await refreshProfileAndSubscription().catch(() => null);
      const referralSummary = await traceStartupStep("action:activateTrial.getReferralSummary", getReferralSummary).catch(() => null);
      const giveawayState = await traceStartupStep("action:activateTrial.getGiveawayState", getGiveawayState).catch(() => null);
      if (referralSummary || giveawayState) {
        setData((current) => normalizeAppData({ ...current, referralSummary: referralSummary ?? current.referralSummary, giveawayState: giveawayState ?? current.giveawayState }));
      }
      const updatedSubscription = refreshed?.subscription || subscription;
      setTrialMessage(null);
      return updatedSubscription;
    } catch (caughtError) {
      throw caughtError;
    }
  }, [refreshProfileAndSubscription, requireRegisteredUser]);

  const createVerification = useCallback(
    async (partnerId: string | number, offerId: string | number) => {
      try {
        const verification = await verifyPartnerOffer(partnerId, offerId);
        setData((current) =>
          normalizeAppData({
            ...current,
            verifications: [
              verification,
              ...current.verifications.filter(
                (item) => item.id !== verification.id,
              ),
            ],
          }),
        );

        const refreshedVerifications = await getVerifications().catch(
          () => null,
        );
        if (refreshedVerifications) {
          setData((current) =>
            normalizeAppData({
              ...current,
              verifications: refreshedVerifications,
            }),
          );
        }

        return verification;
      } catch (caughtError) {
        throw caughtError;
      }
    },
    [],
  );

  const openPayment = useCallback(async () => {
    if (requireRegisteredUser()) return;
    setIsCreatingPayment(true);
    setPaymentMessage(null);

    try {
      const request = await createPaymentRequest();
      setPaymentRequest(request);
      setPaymentMessage("Запрос на продление создан.");
    } catch (caughtError) {
      setPaymentMessage(
        isTimeoutError(caughtError)
          ? RETRYABLE_LOAD_ERROR_MESSAGE
          : "Не удалось подготовить продление. Попробуйте ещё раз.",
      );
    } finally {
      setIsCreatingPayment(false);
    }
  }, [requireRegisteredUser]);

  const refreshAfterLinking = useCallback(async () => {
    const profile = await traceStartupStep("action:refreshAfterLinking.getProfile", getProfile);
    const subscription = await traceStartupStep("action:refreshAfterLinking.getSubscription", getSubscription);
    const linkingStatus = await traceStartupStep("action:refreshAfterLinking.getLinkingStatus", getLinkingStatus).catch(() => null);
    const referralSummary = await traceStartupStep("action:refreshAfterLinking.getReferralSummary", getReferralSummary).catch(() => null);
    const giveawayState = await traceStartupStep("action:refreshAfterLinking.getGiveawayState", getGiveawayState).catch(() => null);

    setData((current) =>
      normalizeAppData({
        ...current,
        profile,
        subscription,
        linkingStatus: linkingStatus ?? current.linkingStatus,
        referralSummary: referralSummary ?? current.referralSummary,
        giveawayState: giveawayState ?? current.giveawayState,
      }),
    );
  }, []);

  const dismissLinkingOnboarding = useCallback(() => {
    const key = getLinkingDismissKey(data.profile);
    if (key) {
      window.localStorage.setItem(key, "1");
    }
    setShouldShowLinking(false);
  }, [data.profile]);

  useEffect(() => {
    if (!isLoading && !error) {
      lifecycleTrace(`page_render_${page}`, { page });
      traceStart("render_page_start", { page });
      traceOk("render_page_ok", { page });
      traceMark("app_interactive", { page });
      window.__BLOOM_APP_INTERACTIVE__ = true;
      setHasRenderedPageContent(true);
      setShowStartupRecovery(false);
    }
  }, [error, isLoading, page]);

  const activeNavPage = useMemo<PageId>(() => {
    if (page === "partner") {
      return "catalog";
    }

    if (page === "subscription") {
      return "profile";
    }

    return page;
  }, [page]);

  const safeData = normalizeAppData(data);
  const hasValidSelectedPartner = selectedPartner !== null;
  const activePage = isKnownPage(page)
    ? page === "partner" && !hasValidSelectedPartner
      ? "catalog"
      : page
    : "home";
  const unknownStateDiagnostic = !isKnownPage(page)
    ? createUnknownStateDiagnostic(`Unknown page: ${page}`)
    : page === "partner" && !hasValidSelectedPartner
      ? createUnknownStateDiagnostic(
          "Stale partner screen without selected partner",
        )
      : null;


  const openDiagnosticsByHiddenGesture = useCallback(() => {
    debugTapCountRef.current += 1;
    if (debugTapTimerRef.current !== undefined) window.clearTimeout(debugTapTimerRef.current);
    debugTapTimerRef.current = window.setTimeout(() => { debugTapCountRef.current = 0; }, 2500);
    if (debugTapCountRef.current >= 7) {
      debugTapCountRef.current = 0;
      enableBloomDebug();
      lifecycleTrace("diagnostic_overlay_hidden_gesture_open", { page: activePage });
      setDiagnosticOverlayReason("Диагностика открыта скрытым жестом: 7 тапов.");
      setShowStartupDiagnostics(true);
    }
  }, [activePage]);

  const logout = useCallback(() => {
    const confirmed = window.confirm("Вы уверены, что хотите выйти?");
    if (!confirmed) {
      return;
    }

    clearStoredAuthToken();
    resetTelegramLoginInFlight();
    setData(emptyData);
    setSelectedPartner(null);
    setPartnerOffers([]);
    setPartnerOffersStatus("idle");
    setPartnerOffersError("");
    setPartnerOffersDiagnostic(null);
    setPaymentRequest(null);
    setPaymentMessage(null);
    setTrialMessage(null);
    setGuestRestrictionMessage(false);
    setShouldShowLinking(false);
    setPage("home");
    setBrowserLoginRequired(true);
    setIsLoginCodeFormOpen(false);
    setLoginCode("");
    setLoginReferralCode("");
    setLoginCodeError("");
  }, []);

  const submitLoginCode = useCallback(async () => {
    setLoginCodeError("");
    setIsLoginCodeSubmitting(true);
    try {
      const loginResponse = await loginWithCode(loginCode, loginReferralCode);
      if (!storeAuthTokenFromResponse(loginResponse)) {
        throw new Error("invalid_login_code_response");
      }
      setBrowserLoginRequired(false);
      setIsLoginCodeFormOpen(false);
      setLoginCode("");
      setLoginReferralCode("");
      await loadAppData("manual", false);
    } catch (error) {
      const backendDetail = isApiError(error) && typeof error.detail === "string" ? error.detail : "";
      setLoginCodeError(backendDetail || "Код недействителен или устарел. Получите новый код в боте.");
    } finally {
      setIsLoginCodeSubmitting(false);
    }
  }, [loadAppData, loginCode, loginReferralCode]);

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

  if (browserLoginExternalOpenRequired) {
    return <BrowserLoginExternalOpenRequiredScreen />;
  }

  if (browserLoginRequired && !canRenderLogin) {
    return <LoadingState title={hasAnyAuthTokenForLoginGuard ? "Проверяем вход..." : "Загружаем данные клуба"} />;
  }

  if (canRenderLogin) {
    return (
      <div className="state" role="status">
        <h1>{BROWSER_LOGIN_REQUIRED_MESSAGE}</h1>
        {isLoginCodeFormOpen ? (
          <>
            <p>{LOGIN_CODE_HELP_MESSAGE}</p>
            <input
              aria-label="Код входа"
              value={loginCode}
              placeholder="BC-XXXXXX"
              onChange={(event) => setLoginCode(event.target.value.toUpperCase())}
            />
            <input
              aria-label="Реферальный код"
              value={loginReferralCode}
              placeholder="Реферальный код"
              onChange={(event) => setLoginReferralCode(event.target.value.toUpperCase())}
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
            <button className="button button--primary" type="button" onClick={() => setIsLoginCodeFormOpen(true)}>Войти по коду</button>
            <button className="button button--secondary" type="button" onClick={() => setBrowserLoginRequired(false)}>Продолжить без регистрации</button>
          </>
        )}
      </div>
    );
  }

  if (isLoading) {
    return <LoadingState title="Загружаем данные клуба" />;
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
            onOpenCatalog={openCatalog}
            onOpenSubscription={() => setPage("subscription")}
            onActivateTrial={activateTrial}
            referralSummary={safeData.referralSummary}
            giveawayState={safeData.giveawayState}
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
              <button className="button button--primary" type="button" onClick={() => { setGuestRestrictionMessage(false); setBrowserLoginRequired(true); setIsLoginCodeFormOpen(true); }}>Ввести код</button>
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
