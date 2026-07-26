import { useCallback, useEffect, useState, type FormEvent } from "react";

import { removeEntryFallbackOverlay } from "./main";

const PARTNER_TOKEN_STORAGE_KEY = "bloom.partnerAccessToken";

type PartnerStats = {
  confirmed_today: number;
  confirmed_month: number;
  confirmed_total: number;
  unique_clients_total: number;
  savings_month: string | number;
};

type PartnerSummary = {
  id: number;
  name: string;
  display_name: string;
  is_active: boolean;
};

type PartnerSession = {
  access_token: string;
  partner: PartnerSummary;
  stats: PartnerStats;
};

type PartnerMe = {
  is_partner: boolean;
  partner: PartnerSummary | null;
  stats: PartnerStats | null;
};

type PrivilegeScan = {
  session_id: number;
  status: string;
  can_confirm: boolean;
  estimated_saving_amount: string | number | null;
  regular_price: string | number | null;
  club_price: string | number | null;
  client: { display_name: string | null; subscription_active: boolean };
  partner: { id: number; name: string };
  privilege: { id: number; title: string } | null;
  expires_at: string;
};

class PartnerApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function getStoredPartnerToken(): string {
  try {
    return localStorage.getItem(PARTNER_TOKEN_STORAGE_KEY) || "";
  } catch {
    return "";
  }
}

function storePartnerToken(token: string): void {
  try {
    if (token) localStorage.setItem(PARTNER_TOKEN_STORAGE_KEY, token);
    else localStorage.removeItem(PARTNER_TOKEN_STORAGE_KEY);
  } catch {
    // The cabinet still works for the current view if storage is unavailable.
  }
}

async function partnerRequest<T>(path: string, init: RequestInit = {}, token = getStoredPartnerToken()): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`/api/v1/partner${path}`, { ...init, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof payload?.detail === "string" ? payload.detail : "Не удалось выполнить запрос";
    throw new PartnerApiError(detail, response.status);
  }
  return payload as T;
}

function money(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "Не указана";
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return "Не указана";
  return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(parsed)} ₽`;
}

function partnerErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof PartnerApiError) {
    if (error.status === 401) return "Неверный код. Проверьте его и попробуйте ещё раз.";
    if (error.status === 404) return "Код привилегии не найден.";
    if (error.status === 409) return "Этот код уже использован или больше не действует.";
    return error.message || fallback;
  }
  return fallback;
}

export default function PartnerPortalApp() {
  const [partner, setPartner] = useState<PartnerSummary | null>(null);
  const [stats, setStats] = useState<PartnerStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loginCode, setLoginCode] = useState("");
  const [clientCode, setClientCode] = useState("");
  const [scan, setScan] = useState<PrivilegeScan | null>(null);
  const [showConfirmForm, setShowConfirmForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    const token = getStoredPartnerToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const response = await partnerRequest<PartnerMe>("/me", {}, token);
      if (!response.is_partner || !response.partner || !response.stats) {
        throw new PartnerApiError("Partner access required", 401);
      }
      setPartner(response.partner);
      setStats(response.stats);
    } catch (caughtError) {
      storePartnerToken("");
      setPartner(null);
      setStats(null);
      if (!(caughtError instanceof PartnerApiError && caughtError.status === 401)) {
        setError("Не удалось загрузить кабинет. Проверьте интернет и попробуйте снова.");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    removeEntryFallbackOverlay();
    void loadDashboard();
  }, [loadDashboard]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    setIsSubmitting(true);
    try {
      const response = await partnerRequest<PartnerSession>(
        "/code-login",
        { method: "POST", body: JSON.stringify({ code: loginCode.trim() }) },
        "",
      );
      storePartnerToken(response.access_token);
      setPartner(response.partner);
      setStats(response.stats);
      setLoginCode("");
    } catch (caughtError) {
      setError(partnerErrorMessage(caughtError, "Не удалось войти в кабинет."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleScan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    setScan(null);
    setIsSubmitting(true);
    try {
      const response = await partnerRequest<PrivilegeScan>("/privileges/scan", {
        method: "POST",
        body: JSON.stringify({ code: clientCode.trim() }),
      });
      setScan(response);
    } catch (caughtError) {
      setError(partnerErrorMessage(caughtError, "Не удалось проверить код привилегии."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function finishPrivilege(action: "confirm" | "reject") {
    if (!scan) return;
    setError("");
    setMessage("");
    setIsSubmitting(true);
    try {
      await partnerRequest(`/privileges/${action}`, {
        method: "POST",
        body: JSON.stringify({ session_id: scan.session_id }),
      });
      setMessage(action === "confirm" ? "Привилегия подтверждена." : "Привилегия отклонена. Клиент сможет выбрать нужную услугу заново.");
      setScan(null);
      setClientCode("");
      setShowConfirmForm(false);
      const response = await partnerRequest<PartnerMe>("/me");
      if (response.stats) setStats(response.stats);
    } catch (caughtError) {
      setError(partnerErrorMessage(caughtError, "Не удалось завершить проверку."));
    } finally {
      setIsSubmitting(false);
    }
  }

  function logout() {
    storePartnerToken("");
    setPartner(null);
    setStats(null);
    setScan(null);
    setMessage("");
    setError("");
  }

  if (isLoading) {
    return <main className="partner-portal partner-portal--center"><div className="partner-portal__loader">Загружаем кабинет…</div></main>;
  }

  if (!partner) {
    return (
      <main className="partner-portal partner-portal--center">
        <section className="partner-login-card" aria-labelledby="partner-login-title">
          <div className="partner-portal__brand">Bloom Club</div>
          <p className="partner-portal__eyebrow">Кабинет партнёра</p>
          <h1 id="partner-login-title">Вход по коду</h1>
          <p>Введите постоянный код, который вы получили от Bloom Club.</p>
          <form className="partner-login-form" onSubmit={handleLogin}>
            <label>
              <span>Код партнёра</span>
              <input value={loginCode} onChange={(event) => setLoginCode(event.target.value)} autoComplete="off" autoCapitalize="characters" spellCheck={false} placeholder="Например, BLOOM-CAFE-01" minLength={8} maxLength={64} required />
            </label>
            {error ? <p className="partner-portal__error" role="alert">{error}</p> : null}
            <button className="partner-portal__primary" type="submit" disabled={isSubmitting}>{isSubmitting ? "Проверяем…" : "Войти в кабинет"}</button>
          </form>
          <a className="partner-portal__client-link" href="/">Вернуться в приложение для участниц</a>
        </section>
      </main>
    );
  }

  return (
    <main className="partner-portal">
      <header className="partner-portal__header">
        <div><p className="partner-portal__eyebrow">Кабинет партнёра</p><h1>{partner.display_name}</h1></div>
        <button className="partner-portal__logout" type="button" onClick={logout}>Выйти</button>
      </header>
      <section className="partner-confirm-hero">
        <p>Клиентка показывает код в приложении Bloom Club</p>
        <button className="partner-confirm-hero__button" type="button" onClick={() => { setShowConfirmForm(true); setMessage(""); setError(""); }}>Подтвердить привилегию</button>
      </section>
      {showConfirmForm ? (
        <section className="partner-code-card" aria-labelledby="partner-code-title">
          <div className="partner-code-card__heading"><div><p className="partner-portal__eyebrow">Проверка</p><h2 id="partner-code-title">Введите код клиента</h2></div><button type="button" onClick={() => { setShowConfirmForm(false); setScan(null); setError(""); }}>Закрыть</button></div>
          <form className="partner-code-form" onSubmit={handleScan}>
            <input value={clientCode} onChange={(event) => setClientCode(event.target.value.replace(/\s/g, ""))} inputMode="numeric" autoComplete="one-time-code" placeholder="Код привилегии" maxLength={12} required />
            <button type="submit" disabled={isSubmitting}>{isSubmitting ? "Проверяем…" : "Проверить код"}</button>
          </form>
          {error ? <p className="partner-portal__error" role="alert">{error}</p> : null}
          {scan ? (
            <article className="partner-privilege-review">
              <p className="partner-privilege-review__client">Клиент: <strong>{scan.client.display_name || "Участница Bloom Club"}</strong></p>
              <h3>{scan.privilege?.title || "Привилегия партнёра"}</h3>
              <dl>
                <div><dt>Сумма без экономии</dt><dd>{money(scan.regular_price)}</dd></div>
                <div className="partner-privilege-review__total"><dt>Сумма с экономией</dt><dd>{money(scan.club_price)}</dd></div>
                <div><dt>Экономия клиентки</dt><dd>{money(scan.estimated_saving_amount)}</dd></div>
              </dl>
              <div className="partner-privilege-review__actions">
                <button className="partner-portal__primary" type="button" onClick={() => void finishPrivilege("confirm")} disabled={isSubmitting}>Подтвердить</button>
                <button className="partner-portal__danger" type="button" onClick={() => void finishPrivilege("reject")} disabled={isSubmitting}>Отказать</button>
              </div>
            </article>
          ) : null}
        </section>
      ) : null}
      {message ? <p className="partner-portal__success" role="status">{message}</p> : null}
      {!showConfirmForm && error ? <p className="partner-portal__error" role="alert">{error}</p> : null}
      <section className="partner-stats" aria-labelledby="partner-stats-title">
        <div className="partner-stats__heading"><p className="partner-portal__eyebrow">Статистика</p><h2 id="partner-stats-title">Использование привилегий</h2></div>
        <div className="partner-stats__grid">
          <article><strong>{stats?.unique_clients_total ?? 0}</strong><span>клиентов пришло</span></article>
          <article><strong>{stats?.confirmed_total ?? 0}</strong><span>привилегий использовано</span></article>
          <article><strong>{stats?.confirmed_today ?? 0}</strong><span>подтверждено сегодня</span></article>
          <article><strong>{stats?.confirmed_month ?? 0}</strong><span>за текущий месяц</span></article>
        </div>
        <div className="partner-stats__saving"><span>Экономия участниц за месяц</span><strong>{money(stats?.savings_month)}</strong></div>
      </section>
    </main>
  );
}
