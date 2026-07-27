import {
  useCallback,
  useEffect,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";

import { removeEntryFallbackOverlay } from "./main";
import "./PartnerPortal.css";

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

type PartnerProfile = {
  id: number;
  name: string;
  city_name: string | null;
  description: string | null;
  address: string | null;
  phone: string | null;
  website_url: string | null;
  vk_url: string | null;
  telegram_url: string | null;
  whatsapp_url: string | null;
  map_url: string | null;
  working_hours: string | null;
  logo_url: string | null;
  cover_url: string | null;
};

type PartnerPhoto = {
  id: number;
  url: string;
  alt_text: string | null;
  is_active: boolean;
};

type PartnerOffer = {
  id: number;
  title: string;
  description: string | null;
  benefit_text: string | null;
  conditions: string | null;
  base_price: string | number | null;
  discount_percent: string | number | null;
  requires_order_amount: boolean;
  image_url: string | null;
  is_active: boolean;
  sort_order: number;
};

type OfferDraft = {
  id?: number;
  title: string;
  description: string;
  benefit_text: string;
  conditions: string;
  base_price: string;
  discount_percent: string;
  requires_order_amount: boolean;
  image_url: string | null;
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

type CabinetTab = "dashboard" | "card" | "services";

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

async function partnerRequest<T>(
  path: string,
  init: RequestInit = {},
  token = getStoredPartnerToken(),
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
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
    if (error.status === 404) return "Запись не найдена или больше недоступна.";
    if (error.status === 409) return "Этот код уже использован или больше не действует.";
    if (error.status === 413) return "Файл слишком большой. Выберите фотографию меньшего размера.";
    if (error.status === 422) return "Проверьте заполненные поля и попробуйте ещё раз.";
    return error.message || fallback;
  }
  return fallback;
}

function emptyOfferDraft(): OfferDraft {
  return {
    title: "",
    description: "",
    benefit_text: "",
    conditions: "",
    base_price: "",
    discount_percent: "",
    requires_order_amount: false,
    image_url: null,
  };
}

function draftFromOffer(offer: PartnerOffer): OfferDraft {
  return {
    id: offer.id,
    title: offer.title,
    description: offer.description || "",
    benefit_text: offer.benefit_text || "",
    conditions: offer.conditions || "",
    base_price: offer.base_price === null ? "" : String(offer.base_price),
    discount_percent: offer.discount_percent === null ? "" : String(offer.discount_percent),
    requires_order_amount: Boolean(offer.requires_order_amount),
    image_url: offer.image_url,
  };
}

export default function PartnerPortalApp() {
  const [partner, setPartner] = useState<PartnerSummary | null>(null);
  const [stats, setStats] = useState<PartnerStats | null>(null);
  const [profile, setProfile] = useState<PartnerProfile | null>(null);
  const [photos, setPhotos] = useState<PartnerPhoto[]>([]);
  const [offers, setOffers] = useState<PartnerOffer[]>([]);
  const [activeTab, setActiveTab] = useState<CabinetTab>("dashboard");
  const [isLoading, setIsLoading] = useState(true);
  const [isContentLoading, setIsContentLoading] = useState(false);
  const [loginCode, setLoginCode] = useState("");
  const [clientCode, setClientCode] = useState("");
  const [scan, setScan] = useState<PrivilegeScan | null>(null);
  const [showConfirmForm, setShowConfirmForm] = useState(false);
  const [offerDraft, setOfferDraft] = useState<OfferDraft | null>(null);
  const [offerImage, setOfferImage] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadContent = useCallback(async () => {
    setIsContentLoading(true);
    try {
      const [profileResponse, photosResponse, offersResponse] = await Promise.all([
        partnerRequest<PartnerProfile>("/profile"),
        partnerRequest<PartnerPhoto[]>("/photos"),
        partnerRequest<PartnerOffer[]>("/offers"),
      ]);
      setProfile(profileResponse);
      setPhotos(photosResponse);
      setOffers(offersResponse);
    } catch (caughtError) {
      setError(partnerErrorMessage(caughtError, "Не удалось загрузить данные карточки."));
    } finally {
      setIsContentLoading(false);
    }
  }, []);

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
      await loadContent();
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
  }, [loadContent]);

  useEffect(() => {
    removeEntryFallbackOverlay();
    void loadDashboard();
  }, [loadDashboard]);

  function clearNotices() {
    setMessage("");
    setError("");
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearNotices();
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
      await loadContent();
    } catch (caughtError) {
      setError(partnerErrorMessage(caughtError, "Не удалось войти в кабинет."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleScan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    clearNotices();
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
    clearNotices();
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

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profile) return;
    clearNotices();
    setIsSubmitting(true);
    const form = new FormData(event.currentTarget);
    const fields = [
      "description",
      "address",
      "phone",
      "working_hours",
      "website_url",
      "map_url",
      "vk_url",
      "telegram_url",
      "whatsapp_url",
    ];
    const payload = Object.fromEntries(fields.map((field) => [field, String(form.get(field) || "").trim() || null]));
    try {
      const response = await partnerRequest<PartnerProfile>("/profile", {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      setProfile(response);
      setMessage("Карточка партнёра обновлена.");
    } catch (caughtError) {
      setError(partnerErrorMessage(caughtError, "Не удалось сохранить карточку."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function uploadProfileImage(kind: "logo" | "cover", file: File | undefined) {
    if (!file) return;
    clearNotices();
    setIsSubmitting(true);
    const body = new FormData();
    body.append("file", file);
    try {
      const response = await partnerRequest<{ url: string }>(`/profile/images?kind=${kind}`, {
        method: "POST",
        body,
      });
      setProfile((current) => current ? { ...current, [`${kind}_url`]: response.url } : current);
      setMessage(kind === "logo" ? "Логотип обновлён." : "Обложка обновлена.");
    } catch (caughtError) {
      setError(partnerErrorMessage(caughtError, "Не удалось загрузить изображение."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function uploadGalleryPhoto(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    clearNotices();
    setIsSubmitting(true);
    const body = new FormData();
    body.append("file", file);
    body.append("alt_text", `${profile?.name || "Партнёр Bloom Club"} — фотография`);
    try {
      const response = await partnerRequest<PartnerPhoto>("/photos", { method: "POST", body });
      setPhotos((current) => [...current, response]);
      setMessage("Фотография добавлена и отправлена на проверку.");
    } catch (caughtError) {
      setError(partnerErrorMessage(caughtError, "Не удалось добавить фотографию."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function deleteGalleryPhoto(photoId: number) {
    clearNotices();
    setIsSubmitting(true);
    try {
      await partnerRequest(`/photos/${photoId}`, { method: "DELETE" });
      setPhotos((current) => current.filter((photo) => photo.id !== photoId));
      setMessage("Фотография удалена.");
    } catch (caughtError) {
      setError(partnerErrorMessage(caughtError, "Не удалось удалить фотографию."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function saveOffer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!offerDraft) return;
    clearNotices();
    setIsSubmitting(true);
    const payload = {
      title: offerDraft.title.trim(),
      description: offerDraft.description.trim() || null,
      benefit_text: offerDraft.benefit_text.trim() || null,
      conditions: offerDraft.conditions.trim() || null,
      base_price: offerDraft.requires_order_amount || !offerDraft.base_price ? null : offerDraft.base_price,
      discount_percent: offerDraft.discount_percent || null,
      requires_order_amount: offerDraft.requires_order_amount,
    };
    try {
      let saved = await partnerRequest<PartnerOffer>(
        offerDraft.id ? `/offers/${offerDraft.id}` : "/offers",
        {
          method: offerDraft.id ? "PATCH" : "POST",
          body: JSON.stringify(payload),
        },
      );
      if (offerImage) {
        const body = new FormData();
        body.append("file", offerImage);
        const image = await partnerRequest<{ url: string }>(`/offers/${saved.id}/image`, {
          method: "POST",
          body,
        });
        saved = { ...saved, image_url: image.url };
      }
      setOffers((current) => {
        const exists = current.some((offer) => offer.id === saved.id);
        return exists ? current.map((offer) => offer.id === saved.id ? saved : offer) : [...current, saved];
      });
      setOfferDraft(null);
      setOfferImage(null);
      setMessage("Услуга сохранена и отправлена администратору на проверку.");
    } catch (caughtError) {
      setError(partnerErrorMessage(caughtError, "Не удалось сохранить услугу."));
    } finally {
      setIsSubmitting(false);
    }
  }

  function logout() {
    storePartnerToken("");
    setPartner(null);
    setStats(null);
    setProfile(null);
    setPhotos([]);
    setOffers([]);
    setScan(null);
    clearNotices();
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
        <div>
          <p className="partner-portal__eyebrow">Кабинет партнёра</p>
          <h1>{partner.display_name}</h1>
        </div>
        <button className="partner-portal__logout" type="button" onClick={logout}>Выйти</button>
      </header>

      <section className="partner-confirm-hero">
        <p>Клиентка показывает код в приложении Bloom Club</p>
        <button className="partner-confirm-hero__button" type="button" onClick={() => { setShowConfirmForm(true); clearNotices(); }}>Подтвердить привилегию</button>
      </section>

      {showConfirmForm ? (
        <section className="partner-code-card" aria-labelledby="partner-code-title">
          <div className="partner-code-card__heading">
            <div><p className="partner-portal__eyebrow">Проверка</p><h2 id="partner-code-title">Введите код клиента</h2></div>
            <button type="button" onClick={() => { setShowConfirmForm(false); setScan(null); setError(""); }}>Закрыть</button>
          </div>
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

      <nav className="partner-cabinet-tabs" aria-label="Разделы кабинета">
        {([
          ["dashboard", "Статистика"],
          ["card", "Моя карточка"],
          ["services", "Услуги"],
        ] as const).map(([tab, label]) => (
          <button key={tab} type="button" className={activeTab === tab ? "is-active" : ""} onClick={() => { setActiveTab(tab); clearNotices(); }}>{label}</button>
        ))}
      </nav>

      {message ? <p className="partner-portal__success" role="status">{message}</p> : null}
      {!showConfirmForm && error ? <p className="partner-portal__error" role="alert">{error}</p> : null}

      {activeTab === "dashboard" ? (
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
      ) : null}

      {activeTab === "card" ? (
        <section className="partner-management-card" aria-labelledby="partner-profile-title">
          <div className="partner-management-heading">
            <div><p className="partner-portal__eyebrow">Как вас видят клиентки</p><h2 id="partner-profile-title">Моя карточка</h2></div>
            <span>{profile?.city_name || "Bloom Club"}</span>
          </div>
          {isContentLoading || !profile ? <p className="partner-portal__loader">Загружаем карточку…</p> : (
            <>
              <div className="partner-media-editor">
                <div className="partner-cover-preview" style={profile.cover_url ? { backgroundImage: `url("${profile.cover_url}")` } : undefined}>
                  <label className="partner-media-action">Изменить обложку<input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => void uploadProfileImage("cover", event.target.files?.[0])} /></label>
                </div>
                <div className="partner-logo-row">
                  <div className="partner-logo-preview">{profile.logo_url ? <img src={profile.logo_url} alt="" /> : <span>{profile.name.slice(0, 1)}</span>}</div>
                  <div><strong>{profile.name}</strong><label className="partner-text-action">Загрузить логотип<input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => void uploadProfileImage("logo", event.target.files?.[0])} /></label></div>
                </div>
              </div>
              <form className="partner-edit-form" onSubmit={saveProfile}>
                <label className="partner-field partner-field--wide"><span>Описание</span><textarea name="description" rows={4} defaultValue={profile.description || ""} placeholder="Коротко расскажите, чем вы занимаетесь и почему стоит прийти именно к вам." /></label>
                <label className="partner-field"><span>Адрес</span><input name="address" defaultValue={profile.address || ""} /></label>
                <label className="partner-field"><span>Телефон</span><input name="phone" inputMode="tel" defaultValue={profile.phone || ""} /></label>
                <label className="partner-field partner-field--wide"><span>Режим работы</span><input name="working_hours" defaultValue={profile.working_hours || ""} placeholder="Пн–Вс, 10:00–21:00" /></label>
                <label className="partner-field"><span>Сайт</span><input name="website_url" inputMode="url" defaultValue={profile.website_url || ""} placeholder="https://…" /></label>
                <label className="partner-field"><span>Ссылка на карту</span><input name="map_url" inputMode="url" defaultValue={profile.map_url || ""} placeholder="Яндекс Карты или 2ГИС" /></label>
                <label className="partner-field"><span>ВКонтакте</span><input name="vk_url" inputMode="url" defaultValue={profile.vk_url || ""} /></label>
                <label className="partner-field"><span>Telegram</span><input name="telegram_url" inputMode="url" defaultValue={profile.telegram_url || ""} /></label>
                <label className="partner-field partner-field--wide"><span>WhatsApp</span><input name="whatsapp_url" inputMode="url" defaultValue={profile.whatsapp_url || ""} /></label>
                <button className="partner-portal__primary partner-form-submit" type="submit" disabled={isSubmitting}>{isSubmitting ? "Сохраняем…" : "Сохранить карточку"}</button>
              </form>
              <div className="partner-gallery-editor">
                <div className="partner-management-heading">
                  <div><p className="partner-portal__eyebrow">Атмосфера и работы</p><h3>Фотографии</h3></div>
                  <label className="partner-add-button">Добавить фото<input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => void uploadGalleryPhoto(event)} /></label>
                </div>
                <p className="partner-review-note">Новые фотографии появятся в приложении после проверки администратором.</p>
                <div className="partner-photo-grid">
                  {photos.map((photo) => (
                    <article key={photo.id}>
                      <img src={photo.url} alt={photo.alt_text || "Фотография партнёра"} />
                      <span className={photo.is_active ? "is-published" : ""}>{photo.is_active ? "Опубликовано" : "На проверке"}</span>
                      <button type="button" onClick={() => void deleteGalleryPhoto(photo.id)} disabled={isSubmitting}>Удалить</button>
                    </article>
                  ))}
                  {!photos.length ? <p className="partner-empty-state">Добавьте несколько качественных фотографий — так карточка будет выглядеть живее и убедительнее.</p> : null}
                </div>
              </div>
            </>
          )}
        </section>
      ) : null}

      {activeTab === "services" ? (
        <section className="partner-management-card" aria-labelledby="partner-services-title">
          <div className="partner-management-heading">
            <div><p className="partner-portal__eyebrow">Привилегии для участниц</p><h2 id="partner-services-title">Услуги</h2></div>
            <button className="partner-add-button" type="button" onClick={() => { setOfferDraft(emptyOfferDraft()); setOfferImage(null); clearNotices(); }}>Добавить</button>
          </div>
          <p className="partner-review-note">Новая или изменённая услуга отправляется администратору на проверку перед публикацией.</p>
          {isContentLoading ? <p className="partner-portal__loader">Загружаем услуги…</p> : (
            <div className="partner-offer-list">
              {offers.map((offer) => (
                <article className="partner-offer-item" key={offer.id}>
                  {offer.image_url ? <img src={offer.image_url} alt="" /> : <div className="partner-offer-item__placeholder" />}
                  <div>
                    <span className={offer.is_active ? "is-published" : ""}>{offer.is_active ? "Опубликовано" : "На проверке"}</span>
                    <h3>{offer.title}</h3>
                    <p>{offer.benefit_text || (offer.requires_order_amount ? `Скидка ${offer.discount_percent || 0}% от суммы` : "Привилегия Bloom Club")}</p>
                  </div>
                  <button type="button" onClick={() => { setOfferDraft(draftFromOffer(offer)); setOfferImage(null); clearNotices(); }}>Редактировать</button>
                </article>
              ))}
              {!offers.length ? <p className="partner-empty-state">Услуг пока нет. Добавьте первую привилегию для участниц Bloom Club.</p> : null}
            </div>
          )}
        </section>
      ) : null}

      {offerDraft ? (
        <div className="partner-sheet-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setOfferDraft(null); }}>
          <section className="partner-offer-sheet" role="dialog" aria-modal="true" aria-labelledby="partner-offer-form-title">
            <div className="partner-code-card__heading">
              <div><p className="partner-portal__eyebrow">{offerDraft.id ? "Редактирование" : "Новая услуга"}</p><h2 id="partner-offer-form-title">{offerDraft.id ? "Изменить услугу" : "Добавить услугу"}</h2></div>
              <button type="button" onClick={() => setOfferDraft(null)}>Закрыть</button>
            </div>
            <form className="partner-edit-form partner-offer-form" onSubmit={saveOffer}>
              <label className="partner-field partner-field--wide"><span>Название услуги</span><input value={offerDraft.title} onChange={(event) => setOfferDraft({ ...offerDraft, title: event.target.value })} required /></label>
              <label className="partner-field partner-field--wide"><span>Краткая выгода</span><input value={offerDraft.benefit_text} onChange={(event) => setOfferDraft({ ...offerDraft, benefit_text: event.target.value })} placeholder="Например, скидка 10% на горячие напитки" /></label>
              <label className="partner-field partner-field--wide"><span>Описание</span><textarea rows={3} value={offerDraft.description} onChange={(event) => setOfferDraft({ ...offerDraft, description: event.target.value })} /></label>
              <label className="partner-field partner-field--wide"><span>Условия</span><textarea rows={3} value={offerDraft.conditions} onChange={(event) => setOfferDraft({ ...offerDraft, conditions: event.target.value })} /></label>
              <label className="partner-choice partner-field--wide"><input type="checkbox" checked={offerDraft.requires_order_amount} onChange={(event) => setOfferDraft({ ...offerDraft, requires_order_amount: event.target.checked, base_price: event.target.checked ? "" : offerDraft.base_price })} /><span><strong>Клиент указывает сумму заказа</strong><small>Подходит для скидки на весь чек или категорию товаров.</small></span></label>
              {!offerDraft.requires_order_amount ? <label className="partner-field"><span>Обычная цена, ₽</span><input type="number" min="0" step="0.01" inputMode="decimal" value={offerDraft.base_price} onChange={(event) => setOfferDraft({ ...offerDraft, base_price: event.target.value })} /></label> : null}
              <label className="partner-field"><span>Скидка, %</span><input type="number" min="0.01" max="100" step="0.01" inputMode="decimal" value={offerDraft.discount_percent} onChange={(event) => setOfferDraft({ ...offerDraft, discount_percent: event.target.value })} required={offerDraft.requires_order_amount} /></label>
              <label className="partner-upload-field partner-field--wide"><span>Фотография услуги</span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setOfferImage(event.target.files?.[0] || null)} /><small>{offerImage?.name || (offerDraft.image_url ? "Текущая фотография сохранится" : "Можно добавить после заполнения услуги")}</small></label>
              <button className="partner-portal__primary partner-form-submit" type="submit" disabled={isSubmitting}>{isSubmitting ? "Сохраняем…" : "Сохранить и отправить на проверку"}</button>
            </form>
          </section>
        </div>
      ) : null}
    </main>
  );
}

