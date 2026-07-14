import { useMemo, useState } from "react";
import { checkSocialSubscription, getGiveawayState, isApiError, isTimeoutError } from "../api/client";
import { AppImage } from "../components/AppImage";
import { PartnerCatalogCard } from "../components/PartnerCatalogCard";
import type { City, ClientProfile, GiveawayState, Partner, ReferralSummary, Subscription } from "../api/types";
import { isSubscriptionActive, isTrialEligible } from "../utils/subscription";
import { useContent, useContentText } from "../content/ContentContext";
import type { HomeBlock } from "../content/clientContentApi";
import { getPartnerName } from "../utils/partnerDisplay";
import { toText } from "../utils/text";
import { sanitizeCmsHtml } from "../utils/sanitizeCmsHtml";
import { resolveHomeCtaAction } from "../utils/homeCta";

interface HomePageProps {
  profile: ClientProfile | null;
  subscription: Subscription | null;
  cities?: City[] | null;
  partners?: Partner[] | null;
  isPartnersLoading?: boolean;
  hasPartnersLoaded?: boolean;
  onOpenCatalog: () => void;
  onOpenSubscription: () => void;
  onActivateTrial: () => Promise<Subscription>;
  referralSummary?: ReferralSummary | null;
  giveawayState?: GiveawayState | null;
  isGiveawayLoading?: boolean;
}

function getCityName(city: unknown): string {
  return toText(city);
}

function hasVisibleHomeBlockContent(block: HomeBlock): boolean {
  return Boolean(
    block.title?.trim() ||
      block.subtitle?.trim() ||
      block.body?.trim() ||
      block.image_url?.trim() ||
      block.cta_text?.trim() ||
      (block.type === "giveaway" &&
        typeof block.metadata_json.prize === "string" &&
        block.metadata_json.prize.trim()),
  );
}

export function HomePage({
  profile,
  subscription,
  cities,
  partners,
  isPartnersLoading = false,
  hasPartnersLoaded = false,
  onOpenCatalog,
  onOpenSubscription,
  onActivateTrial,
  referralSummary,
  giveawayState,
  isGiveawayLoading = false,
}: HomePageProps) {
  const safeCities = Array.isArray(cities) ? cities : [];
  const safePartners = Array.isArray(partners) ? partners : [];
  const [isActivatingTrial, setIsActivatingTrial] = useState(false);
  const [localTrialMessage, setLocalTrialMessage] = useState<string | null>(null);
  const { homeBlocks } = useContent();

  const hasAccess = isSubscriptionActive(subscription);
  const trialAvailable = isTrialEligible(profile, subscription);
  const selectedCity = safeCities[0] ? getCityName(safeCities[0]) : "Новосибирск";
  const firstName = profile?.first_name || profile?.name || "участница";
  const visibleHomeBlocks = useMemo(
    () => homeBlocks.filter((block) => block.is_active !== false && hasVisibleHomeBlockContent(block)),
    [homeBlocks],
  );

  const catalogCta = useContentText("home.hero.catalog_cta", "Найти привилегии");
  const subscriptionLabel = useContentText("home.hero.subscription_cta", "Оформить доступ");
  const manageSubscriptionLabel = useContentText("home.hero.manage_subscription_cta", "Моя подписка");
  const trialCta = useContentText("home.trial.cta", "Подключить пробный период 15 дней");
  const heroEyebrow = useContentText("home.hero.eyebrow", "Bloom Club · Женский клуб НСК");
  const heroTitle = useContentText("home.hero.title", `Добро пожаловать, ${firstName}`);
  const heroSubtitle = useContentText(
    "home.hero.subtitle",
    "Закрытый клуб привилегий у партнёров города: красота, здоровье, стиль, отдых и забота о себе.",
  );
  const cityTitle = useContentText("home.city.title", "Город");
  const trialTitle = useContentText("home.trial.title", "Попробуйте клуб бесплатно");
  const trialDescription = useContentText("home.trial.description", "Откройте 15 дней доступа к привилегиям Bloom Club.");
  const referralCode = toText(referralSummary?.referral_code || profile?.referral_code);
  const [referralCopyMessage, setReferralCopyMessage] = useState('');
  const [isGiveawayModalOpen, setGiveawayModalOpen] = useState(false);
  const [socialStatuses, setSocialStatuses] = useState<Record<string, string>>({});
  const partnersTitle = useContentText("home.partners.title", "Партнёры клуба");
  const partnersDescription = useContentText(
    "home.partners.description",
    "Открывайте каталог и выбирайте привилегии у партнёров Bloom Club.",
  );
  const visiblePartners = safePartners.slice(0, 6);

  async function copyReferralCode() {
    if (!referralCode) {
      return;
    }

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(referralCode);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = referralCode;
        textarea.setAttribute('readonly', '');
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }
      setReferralCopyMessage('Код скопирован');
      window.setTimeout(() => setReferralCopyMessage(''), 2200);
    } catch {
      setReferralCopyMessage('Скопируйте код вручную');
    }
  }

  async function handleActivateTrial() {
    setIsActivatingTrial(true);
    setLocalTrialMessage(null);

    try {
      await onActivateTrial();
      setLocalTrialMessage(null);
    } catch (caughtError) {
      if (isTimeoutError(caughtError)) {
        setLocalTrialMessage("Не удалось загрузить данные. Проверьте соединение и повторите попытку.");
      } else if (isApiError(caughtError) && [400, 403, 409, 422].includes(caughtError.status || 0)) {
        setLocalTrialMessage("Пробный период уже использован");
      } else {
        setLocalTrialMessage("Не удалось активировать тестовый период. Попробуйте позже.");
      }
    } finally {
      setIsActivatingTrial(false);
    }
  }

  function runCta(action?: string) {
    const normalized = String(action || "").trim().toLowerCase();

    if (!normalized || normalized === "catalog" || normalized === "partners") {
      onOpenCatalog();
      return;
    }

    if (normalized === "subscription" || normalized === "profile") {
      onOpenSubscription();
      return;
    }

    if (normalized === "trial") {
      void handleActivateTrial();
      return;
    }

    if (/^https?:\/\//i.test(action || "")) {
      window.open(action, "_blank", "noopener,noreferrer");
    }
  }

  function renderCta(block: HomeBlock) {
    return block.cta_text ? (
      <button className="button button--primary" type="button" onClick={() => runCta(resolveHomeCtaAction(block))}>
        {block.cta_text}
      </button>
    ) : null;
  }

  function renderHomeBlock(block: HomeBlock) {
    const key = String(block.id);

    if (block.type === "hero") {
      return (
        <div className="hero-card" key={key}>
          {block.subtitle ? <p className="eyebrow">{block.subtitle}</p> : null}
          <h1>{block.title}</h1>
          {block.body ? <p>{block.body}</p> : null}
          <AppImage src={block.image_url} className="home-builder-image" alt={block.title} shellClassName="home-builder-image-shell" placeholderClassName="home-builder-image image-placeholder image-placeholder--wide" loading="eager" />
          <div className="hero-card__actions">{renderCta(block)}</div>
        </div>
      );
    }

    if (block.type === "partners_carousel") {
      return (
        <div className="info-panel" key={key}>
          <strong>{block.title}</strong>
          {block.body ? <p>{block.body}</p> : null}
          <div className="home-partners-carousel" aria-label="Партнёры клуба">
            {isPartnersLoading || !hasPartnersLoaded ? (
              <div className="home-empty-state">
                <strong>Загружаем партнёров</strong>
                <p>Каталог Bloom Club уже обновляется.</p>
              </div>
            ) : safePartners.length ? safePartners.slice(0, 8).map((partner) => (
              <button
                className="home-partner-card"
                type="button"
                onClick={onOpenCatalog}
                key={String(partner.id ?? getPartnerName(partner))}
              >
                <span>{getPartnerName(partner)}</span>
                <small>{toText(partner.category) || "Партнёр Bloom Club"}</small>
              </button>
            )) : (
              <div className="home-empty-state">
                <strong>Партнёров пока нет</strong>
                <p>Каталог Bloom Club наполняется.</p>
              </div>
            )}
          </div>
          {renderCta(block)}
        </div>
      );
    }

    if (block.type === "html_text") {
      return (
        <div className="info-panel home-html-text" key={key}>
          {block.title ? <strong>{block.title}</strong> : null}
          {block.body ? <p>{sanitizeCmsHtml(block.body)}</p> : null}
          {renderCta(block)}
        </div>
      );
    }

    if (block.type === "image") {
      return (
        <figure className="info-panel home-image-block" key={key}>
          <AppImage src={block.image_url} className="home-builder-image" alt={block.title || block.subtitle} shellClassName="home-builder-image-shell" placeholderClassName="home-builder-image image-placeholder image-placeholder--wide" />
          <figcaption>
            {block.title ? <strong>{block.title}</strong> : null}
            {block.body ? <p>{block.body}</p> : null}
          </figcaption>
          {renderCta(block)}
        </figure>
      );
    }

    return (
      <div
        className={
          block.type === "custom_cta" || block.type === "banner" || block.type === "giveaway"
            ? "info-panel info-panel--soft"
            : "info-panel"
        }
        key={key}
      >
        <AppImage src={block.image_url} className="home-builder-image" alt={block.title} shellClassName="home-builder-image-shell" placeholderClassName="home-builder-image image-placeholder image-placeholder--wide" />
        {block.subtitle ? <p className="eyebrow">{block.subtitle}</p> : null}
        {block.title ? <strong>{block.title}</strong> : null}
        {block.body ? <p>{block.body}</p> : null}
        {block.type === "giveaway" && typeof block.metadata_json.prize === "string" ? (
          <p className="success-text">Приз: {block.metadata_json.prize}</p>
        ) : null}
        {renderCta(block)}
      </div>
    );
  }



  function renderReferralBanner() {
    return (
      <div className="info-panel info-panel--soft referral-banner">
        <p className="eyebrow">Реферальная программа</p>
        <strong>Реферальный код</strong>
        <p>Отправьте ваш код тому, кого хотите пригласить.</p>
        {referralCode ? (
          <button className="button button--primary referral-code-button" type="button" onClick={() => void copyReferralCode()}>
            {referralCode}
          </button>
        ) : (
          <p>Реферальный код скоро появится</p>
        )}
        {referralCopyMessage ? <p className="success-text">{referralCopyMessage}</p> : null}
        <div className="referral-banner__stats" aria-label="Статистика реферальной программы">
          <span>Приглашено: {referralSummary?.invited_count ?? referralSummary?.referrals_count ?? 0}</span>
          <span>Активировали тестовый период: {referralSummary?.activated_count ?? referralSummary?.activated_referrals_count ?? 0}</span>
          <span>Дополнительных номеров в розыгрыше: {referralSummary?.earned_giveaway_entries_count ?? referralSummary?.earned_entries_count ?? 0}</span>
        </div>
      </div>
    );
  }


  async function handleSocialCheck(platform: "telegram" | "vk") {
    setSocialStatuses((current) => ({ ...current, [platform]: "Проверяем…" }));
    try {
      const result = await checkSocialSubscription(platform);
      setSocialStatuses((current) => ({ ...current, [platform]: String(result.message || "Проверка завершена") }));
      await getGiveawayState().catch(() => null);
      window.dispatchEvent(new CustomEvent("bloom:refresh"));
    } catch {
      setSocialStatuses((current) => ({ ...current, [platform]: "Проверка временно недоступна" }));
    }
  }

  function renderSocialTasks() {
    const tasks = giveawayState?.social_tasks || {};
    const rows = (["telegram", "vk"] as const).filter((platform) => tasks[platform]?.enabled && tasks[platform]?.community_url);
    if (giveawayState?.guest || rows.length === 0) return null;
    return <div className="giveaway-social-tasks"><strong>Получите дополнительные номера</strong>{rows.map((platform) => {
      const isTelegram = platform === "telegram";
      const url = String(tasks[platform]?.community_url || "");
      return <div className="giveaway-social-task" key={platform}>
        <div><b>{isTelegram ? "Telegram" : "VK"}</b><p>{isTelegram ? "Подпишитесь на наш Telegram-канал и получите 1 дополнительный номер" : "Подпишитесь на наше сообщество VK и получите 1 дополнительный номер"}</p></div>
        <a className="button button--secondary" href={url} target="_blank" rel="noopener noreferrer">{isTelegram ? "Подписаться на Telegram" : "Подписаться на VK"}</a>
        <button className="button" type="button" onClick={() => handleSocialCheck(platform)}>{isTelegram ? "Проверить подписку" : "Проверить подписку"}</button>
        {socialStatuses[platform] ? <small>{socialStatuses[platform]}</small> : null}
      </div>;
    })}</div>;
  }

  function renderGiveawayBlock() {
    const giveaway = giveawayState?.giveaway;
    const prizes = Array.isArray(giveaway?.prizes) ? giveaway?.prizes ?? [] : [];
    if (isGiveawayLoading || giveawayState == null) {
      return (
        <div className="info-panel info-panel--soft giveaway-panel">
          <p className="eyebrow">Розыгрыш</p>
          <strong>Загружаем активный розыгрыш</strong>
          <p>Проверяем ваши номера участия.</p>
        </div>
      );
    }
    if (!giveawayState.has_active_giveaway) {
      return (
        <div className="info-panel info-panel--soft giveaway-panel">
          <p className="eyebrow">Розыгрыш</p>
          <strong>Скоро объявим новый розыгрыш</strong>
          <p>Новый розыгрыш появится в ближайшее время.</p>
        </div>
      );
    }
    if (!giveaway) {
      return (
        <div className="info-panel info-panel--soft giveaway-panel">
          <p className="eyebrow">Розыгрыш</p>
          <strong>Активный розыгрыш</strong>
          <p>Данные розыгрыша обновляются. Попробуйте открыть приложение ещё раз.</p>
        </div>
      );
    }
    return (
      <div className="info-panel info-panel--soft giveaway-panel">
        <p className="eyebrow">Розыгрыш</p>
        <strong>{toText(giveaway.title)}</strong>
        {toText(giveaway.description) ? <p>{toText(giveaway.description)}</p> : null}
        <ul className="giveaway-panel__prizes">
          {prizes.map((prize, index) => (
            <li key={`${prize.place_number || index}-${toText(prize.prize_title)}`}>{prize.place_number || index + 1} место — {toText(prize.prize_title)}</li>
          ))}
        </ul>
        {giveawayState.guest ? (
          <p>Войдите, чтобы получить номера для участия.</p>
        ) : (
          <>
            <p>Ваших номеров в розыгрыше: {giveawayState.user_numbers_count ?? 0}</p>
            <button className="button button--secondary" type="button" onClick={() => setGiveawayModalOpen(true)}>Открыть список моих номеров</button>
            {renderSocialTasks()}
          </>
        )}
        {isGiveawayModalOpen ? (
          <div className="giveaway-modal" role="dialog" aria-modal="true" aria-label="Мои номера в розыгрыше">
            <div className="giveaway-modal__card">
              <button className="giveaway-modal__close" type="button" aria-label="Закрыть" onClick={() => setGiveawayModalOpen(false)}>×</button>
              <strong>Мои номера</strong>
              <ul>{(giveawayState.numbers ?? []).map((item) => <li key={`${toText(item.number)}-${toText(item.source)}`}>{toText(item.number)} — {toText(item.source) === 'referral' ? 'реферал' : toText(item.source) === 'telegram_subscription' ? 'Telegram' : toText(item.source) === 'vk_subscription' ? 'VK' : 'подписка'}</li>)}</ul>
            </div>
          </div>
        ) : null}
      </div>
    );
  }

  function renderTrialCta() {
    if (!trialAvailable) {
      return null;
    }

    return (
      <div className="info-panel info-panel--soft trial-cta-panel">
        <strong>{trialTitle}</strong>
        <p>{trialDescription}</p>
        <button className="button button--primary" type="button" onClick={() => void handleActivateTrial()} disabled={isActivatingTrial}>
          {isActivatingTrial ? "Активируем…" : trialCta}
        </button>
      </div>
    );
  }

  function renderLegacyHome() {
    return (
      <>
        <div className="hero-card home-hero">
          <p className="eyebrow">{heroEyebrow}</p>
          <h1>{heroTitle}</h1>
          <p>{heroSubtitle}</p>
          <div className="home-hero__benefits" aria-label="Преимущества Bloom Club">
            <span>Красота</span>
            <span>Здоровье</span>
            <span>Стиль</span>
          </div>
          <div className="hero-card__actions">
            <button className="button button--primary" type="button" onClick={onOpenCatalog}>
              {catalogCta}
            </button>
            <button className="button button--ghost" type="button" onClick={onOpenSubscription}>
              {hasAccess ? manageSubscriptionLabel : subscriptionLabel}
            </button>
          </div>
        </div>

        {safeCities.length ? (
          <div className="info-panel">
            <strong>{cityTitle}</strong>
            <p>
              {selectedCity
                ? `Сейчас показываем партнёров города: ${selectedCity}.`
                : "Выберите город в профиле, чтобы видеть актуальные предложения."}
            </p>
          </div>
        ) : null}

        <section className="home-partners-section" aria-labelledby="home-partners-title">
          <div className="home-section-heading">
            <div>
              <p className="eyebrow">Каталог привилегий</p>
              <h2 id="home-partners-title">{partnersTitle}</h2>
              <p>{partnersDescription}</p>
            </div>
            <button className="link-button" type="button" onClick={onOpenCatalog}>
              Все
            </button>
          </div>

          {visiblePartners.length ? (
            <div className="home-partners-grid">
              {visiblePartners.map((partner) => (
                <PartnerCatalogCard
                  partner={partner}
                  onOpen={onOpenCatalog}
                  diagnosticContext="home"
                  key={String(partner.id ?? getPartnerName(partner))}
                />
              ))}
            </div>
          ) : isPartnersLoading || !hasPartnersLoaded ? (
            <div className="home-empty-state">
              <span aria-hidden="true">♡</span>
              <strong>Загружаем партнёров</strong>
              <p>Каталог Bloom Club уже обновляется и скоро появится на главном экране.</p>
            </div>
          ) : (
            <div className="home-empty-state">
              <span aria-hidden="true">♡</span>
              <strong>Скоро добавим партнёров</strong>
              <p>Команда Bloom Club готовит новые места для красоты, отдыха и заботы о себе. Загляните в каталог чуть позже.</p>
              <button className="button button--primary" type="button" onClick={onOpenCatalog}>
                Открыть каталог
              </button>
            </div>
          )}
        </section>
      </>
    );
  }

  return (
    <section className="page">
      {visibleHomeBlocks.length ? (
        <>
          {visibleHomeBlocks.map(renderHomeBlock)}
          {renderTrialCta()}
          {renderReferralBanner()}
        {renderGiveawayBlock()}
        </>
      ) : (
        <>
          {renderTrialCta()}
          {renderReferralBanner()}
        {renderGiveawayBlock()}
          {renderLegacyHome()}
        </>
      )}
      {localTrialMessage ? <p className="error-text">{localTrialMessage}</p> : null}
    </section>
  );
}
