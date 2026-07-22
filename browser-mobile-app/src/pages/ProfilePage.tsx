import { isTimeoutError, linkProviderIdentity, mergeProviderIdentity, previewProviderIdentityMerge } from '../api/client';
import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { AppImage } from '../components/AppImage';
import { ContentText } from '../components/ContentText';
import { LEGAL_DOCUMENT_URLS, SubscriptionPaymentCard } from '../components/SubscriptionPaymentCard';
import { useContentText } from '../content/ContentContext';
import { useAddToHomeScreen } from '../utils/pwaInstall';
import type { AcquiringPayment, City, ClientProfile, ClientProfilePatch, ReferralSummary, Subscription } from '../api/types';
import { pickText, toText } from '../utils/text';


const legalDocuments = [
  {
    label: 'Политика конфиденциальности',
    href: LEGAL_DOCUMENT_URLS.privacy,
  },
  {
    label: 'Пользовательское соглашение',
    href: LEGAL_DOCUMENT_URLS.agreement,
  },
  {
    label: 'Согласие на обработку персональных данных',
    href: LEGAL_DOCUMENT_URLS.personalDataConsent,
  },
];

type TextChangeEvent = { target?: { value?: string } | null; currentTarget?: { value?: string } | null } | null | undefined;

function readChangeValue(event: TextChangeEvent): string {
  return event?.currentTarget?.value ?? event?.target?.value ?? "";
}

interface ProfilePageProps {
  profile: ClientProfile | null;
  subscription: Subscription | null;
  cities?: City[] | null;
  onOpenSubscription: () => void;
  onActivateTrial: () => Promise<Subscription>;
  isCreatingPayment: boolean;
  onCreatePayment: (email: string, subscriptionPlanId: number) => Promise<AcquiringPayment | null>;
  onSaveProfile: (payload: ClientProfilePatch) => Promise<ClientProfile>;
  referralSummary?: ReferralSummary | null;
  onLogout: () => void;
  onLinkedProvider?: () => Promise<void> | void;
}

function isValidPhone(value: string): boolean {
  if (!value.trim()) {
    return true;
  }

  return /^\+?[\d\s()\-]{10,20}$/.test(value.trim());
}

function isValidEmail(value: string): boolean {
  if (!value.trim()) {
    return true;
  }

  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

function getCityName(city: unknown): string {
  return toText(city);
}


function getProfileDisplayName(profile: ClientProfile | null | undefined): string {
  return pickText(
    profile?.full_name,
    profile?.name,
    profile?.user?.full_name,
    profile?.user?.name,
    [profile?.telegram_first_name, profile?.telegram_last_name],
    [profile?.first_name, profile?.last_name],
    [profile?.user?.first_name, profile?.user?.last_name],
  ) || '';
}

export function ProfilePage({ profile, subscription, cities, onOpenSubscription, onActivateTrial, isCreatingPayment, onCreatePayment, onSaveProfile, referralSummary, onLogout, onLinkedProvider }: ProfilePageProps) {
  const safeCities = useMemo(() => (Array.isArray(cities) ? cities : []), [cities]);
  const initialName = getProfileDisplayName(profile);
  const initialCity = getCityName(profile?.city);
  const [name, setName] = useState(initialName);
  const [linkProvider, setLinkProvider] = useState<"telegram" | "vk" | null>(null);
  const [telegramLinkCode, setTelegramLinkCode] = useState(() => sessionStorage.getItem("bloom.telegramLinkCodeDraft") || "");
  const [vkLinkCode, setVkLinkCode] = useState(() => sessionStorage.getItem("bloom.vkLinkCodeDraft") || "");
  const [linkMessage, setLinkMessage] = useState("");
  const [isLinking, setIsLinking] = useState(false);
  const [mergePrompt, setMergePrompt] = useState<{ provider: "telegram" | "vk"; code: string; source?: { has_subscription?: boolean; subscription_active?: boolean; giveaway_entries?: number; referrals?: number; linked_providers?: string[] } | null } | null>(null);

  const [phone, setPhone] = useState(toText(profile?.phone));
  const [email, setEmail] = useState(toText(profile?.email));
  const [city, setCity] = useState(initialCity);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const avatarUrl = toText(profile?.avatar_url);
  const defaultProfileName = useContentText('profile.default_name', 'Участница Bloom Club');
  const defaultProfileCity = useContentText('profile.default_city', 'Город можно указать ниже.');
  const referralCode = toText(referralSummary?.referral_code || profile?.referral_code);
  const invited = referralSummary?.invited_count ?? referralSummary?.referrals_count ?? 0;
  const activated = referralSummary?.activated_count ?? referralSummary?.activated_referrals_count ?? 0;
  const additionalEntries = referralSummary?.earned_giveaway_entries_count ?? referralSummary?.earned_entries_count ?? 0;
  const [copyMessage, setCopyMessage] = useState('');
  const addToHomeScreen = useAddToHomeScreen();


  const submitProviderLink = async (provider: "telegram" | "vk") => {
    const code = provider === "telegram" ? telegramLinkCode : vkLinkCode;
    setLinkMessage("");
    setIsLinking(true);
    try {
      const preview = await previewProviderIdentityMerge(provider, code);
      if (preview.merge_required) {
        setMergePrompt({ provider, code, source: preview.source_client });
        setLinkMessage("");
        return;
      }
      await linkProviderIdentity(provider, code);
      sessionStorage.removeItem(provider === "telegram" ? "bloom.telegramLinkCodeDraft" : "bloom.vkLinkCodeDraft");
      if (provider === "telegram") setTelegramLinkCode(""); else setVkLinkCode("");
      setLinkProvider(null);
      setLinkMessage("Аккаунт привязан");
      await onLinkedProvider?.();
    } catch (error) {
      const detail = typeof (error as { detail?: unknown }).detail === "string" ? String((error as { detail?: unknown }).detail) : "Не удалось привязать аккаунт";
      setLinkMessage(detail);
    } finally {
      setIsLinking(false);
    }
  };

  const confirmMerge = async () => {
    if (!mergePrompt) return;
    setIsLinking(true);
    try {
      await mergeProviderIdentity(mergePrompt.provider, mergePrompt.code);
      sessionStorage.removeItem(mergePrompt.provider === "telegram" ? "bloom.telegramLinkCodeDraft" : "bloom.vkLinkCodeDraft");
      if (mergePrompt.provider === "telegram") setTelegramLinkCode(""); else setVkLinkCode("");
      setMergePrompt(null);
      setLinkProvider(null);
      setLinkMessage("Аккаунты объединены");
      await onLinkedProvider?.();
    } catch (error) {
      const detail = typeof (error as { detail?: unknown }).detail === "string" ? String((error as { detail?: unknown }).detail) : "Не удалось объединить аккаунты";
      setLinkMessage(detail);
    } finally {
      setIsLinking(false);
    }
  };

  useEffect(() => {
    setName(initialName);
    setPhone(toText(profile?.phone));
    setEmail(toText(profile?.email));
    setCity(initialCity);
  }, [initialName, initialCity, profile?.phone, profile?.email]);


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
      setCopyMessage('Код скопирован');
      window.setTimeout(() => setCopyMessage(''), 2200);
    } catch {
      setCopyMessage('Скопируйте код вручную');
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setMessage('');

    if (!isValidPhone(phone)) {
      setError('Введите корректный номер телефона');
      return;
    }

    if (!isValidEmail(email)) {
      setError('Введите корректный email');
      return;
    }

    setIsSaving(true);

    try {
      await onSaveProfile({
        full_name: name.trim(),
        name: name.trim(),
        phone: phone.trim(),
        email: email.trim(),
        contact_email: email.trim(),
        custom_city: city.trim(),
        city: city.trim(),
      });
      setMessage('Данные сохранены');
    } catch (caughtError) {
      setError(isTimeoutError(caughtError) ? 'Загрузка заняла слишком много времени. Данные не сохранены, попробуйте ещё раз.' : 'Не удалось сохранить данные. Попробуйте ещё раз.');
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="page">
      <div className="profile-card">
        <div className="profile-card__avatar"><AppImage src={avatarUrl} alt="" placeholder="♡" placeholderClassName="profile-card__avatar-placeholder image-placeholder" /></div>
        <h1>{name || defaultProfileName}</h1>
        <p>{city || defaultProfileCity}</p>
      </div>

      <section className="profile-subscription-section" aria-label="Оплата подписки">
        <SubscriptionPaymentCard
          profile={profile}
          subscription={subscription}
          isCreatingPayment={isCreatingPayment}
          onCreatePayment={onCreatePayment}
          onActivateTrial={onActivateTrial}
        />
        <button className="link-button profile-subscription-section__details" type="button" onClick={onOpenSubscription}>
          Посмотреть условия подписки
        </button>
      </section>

      <form className="profile-form" onSubmit={(event: FormEvent<HTMLFormElement>) => void handleSubmit(event)}>
        <div>
          <ContentText as="h2" textKey="profile.title" fallback="Профиль" />
          <ContentText as="p" textKey="profile.description" fallback="Пожалуйста, заполните данные ниже. Они могут понадобиться для связи с вами в случае вашей победы в ежемесячном розыгрыше." multiline />
        </div>
        <label>
          Имя
          <input value={name} onChange={(event: { target: { value: string } }) => setName(readChangeValue(event))} placeholder="Ваше имя" />
        </label>
        <label>
          Телефон
          <input value={phone} onChange={(event: { target: { value: string } }) => setPhone(readChangeValue(event))} placeholder="+7 999 000-00-00" inputMode="tel" />
        </label>
        <label>
          Email
          <input value={email} onChange={(event: { target: { value: string } }) => setEmail(readChangeValue(event))} placeholder="name@example.com" inputMode="email" />
        </label>
        <label>
          Город
          <input value={city} onChange={(event: { target: { value: string } }) => setCity(readChangeValue(event))} list="club-cities" placeholder="Новосибирск" />
          <datalist id="club-cities">
            {safeCities.map((item) => {
              const cityName = getCityName(item);
              return cityName ? <option value={cityName} key={item.id ?? cityName} /> : null;
            })}
          </datalist>
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        {message ? <p className="success-text">{message}</p> : null}
        <button className="button button--primary" type="submit" disabled={isSaving}>
          {isSaving ? 'Сохраняем…' : 'Сохранить данные'}
        </button>
      </form>

      {addToHomeScreen.canShow ? (
        <div className="info-panel info-panel--soft add-to-phone-panel">
          <div className="add-to-phone-panel__icon" aria-hidden="true">📲</div>
          <div className="add-to-phone-panel__content">
            <strong>📲 Добавить на экран телефона</strong>
            {addToHomeScreen.mode === 'telegram' ? (
              <p>Чтобы добавить Bloom Club на экран телефона, сначала откройте приложение в Safari или Chrome.</p>
            ) : (
              <p>Добавьте Bloom Club на экран телефона, чтобы открывать приложение в один клик.</p>
            )}
          </div>
          {addToHomeScreen.mode === 'telegram' ? (
            <button className="button button--primary" type="button" onClick={addToHomeScreen.openInSystemBrowser}>
              Открыть в браузере
            </button>
          ) : (
            <button className="button button--primary" type="button" onClick={() => void addToHomeScreen.addToHomeScreen()}>
              Добавить
            </button>
          )}
        </div>
      ) : null}

      {addToHomeScreen.showIosInstructions ? (
        <div className="add-to-phone-modal" role="dialog" aria-modal="true" aria-labelledby="add-to-phone-title">
          <div className="add-to-phone-modal__card">
            <button className="add-to-phone-modal__close" type="button" aria-label="Закрыть" onClick={addToHomeScreen.closeIosInstructions}>
              ×
            </button>
            <div className="add-to-phone-modal__hero" aria-hidden="true">📲</div>
            <h2 id="add-to-phone-title">📲 Добавить на экран телефона</h2>
            <p>Чтобы добавить Bloom Club на экран телефона:</p>
            <ol className="add-to-phone-steps">
              <li><span aria-hidden="true">↗️</span><span>Нажмите кнопку «Поделиться».</span></li>
              <li><span aria-hidden="true">🏠</span><span>Выберите пункт<br />«На экран Домой».</span></li>
              <li><span aria-hidden="true">✨</span><span>Нажмите «Добавить».</span></li>
            </ol>
          </div>
        </div>
      ) : null}

      <div className="info-panel info-panel--soft referral-profile-card">
        <ContentText as="strong" textKey="profile.referral.title" fallback="Реферальный код" />
        <p>Отправьте ваш код тому, кого хотите пригласить.</p>
        {referralCode ? (
          <button className="button button--primary referral-code-button" type="button" onClick={() => void copyReferralCode()}>
            {referralCode}
          </button>
        ) : (
          <p>Реферальный код скоро появится</p>
        )}
        {copyMessage ? <p className="success-text">{copyMessage}</p> : null}
        <div className="referral-stats" aria-label="Реферальная программа">
          <span>Приглашено: {invited}</span>
          <span>Активировали тестовый период: {activated}</span>
          <span>Дополнительных номеров в розыгрыше: {additionalEntries}</span>
        </div>
      </div>


      <section className="profile-section glass-card">
        <h2>Связанные аккаунты</h2>
        {(["telegram", "vk"] as const).map((provider) => {
          const identity = profile?.provider_identities?.[provider];
          const linked = Boolean(identity?.linked || (provider === "telegram" ? profile?.telegram_user_id : profile?.vk_user_id));
          const label = provider === "telegram" ? "Telegram" : "VK";
          const code = provider === "telegram" ? telegramLinkCode : vkLinkCode;
          return (
            <div className="profile-linked-account" key={provider}>
              <strong>{label}</strong>
              <span>{linked ? "Привязан" : "Не привязан"}</span>
              {linked ? <span>{toText(identity?.username) || toText(identity?.provider_user_id_masked) || "Аккаунт Bloom Club"}</span> : null}
              {identity?.linked_at ? <small>{toText(identity.linked_at)}</small> : null}
              {!linked ? <button className="button button--secondary" type="button" onClick={() => setLinkProvider(provider)}>Привязать {label}</button> : null}
              {linkProvider === provider ? (
                <div>
                  <p>Введите код, полученный у {label}-бота</p>
                  <input
                    className="auth-code-input"
                    value={code}
                    onChange={(event) => {
                      const value = event.target.value.toUpperCase();
                      if (provider === "telegram") { setTelegramLinkCode(value); } else { setVkLinkCode(value); }
                      sessionStorage.setItem(provider === "telegram" ? "bloom.telegramLinkCodeDraft" : "bloom.vkLinkCodeDraft", value);
                    }}
                  />
                  <button className="button button--primary" type="button" disabled={isLinking || !code.trim()} onClick={() => submitProviderLink(provider)}>Привязать</button>
                </div>
              ) : null}
            </div>
          );
        })}
        {linkMessage ? <p className="profile-form__message">{linkMessage}</p> : null}
      </section>


      {mergePrompt ? (
        <div className="profile-merge-dialog glass-card" role="dialog" aria-modal="true">
          <h2>Найден ещё один аккаунт Bloom Club.</h2>
          <p>После объединения будут объединены:</p>
          <ul>
            <li>✅ подписка{mergePrompt.source?.subscription_active ? " (активна)" : ""}</li>
            <li>✅ участие в розыгрышах{typeof mergePrompt.source?.giveaway_entries === "number" ? `: ${mergePrompt.source.giveaway_entries}` : ""}</li>
            <li>✅ рефералы{typeof mergePrompt.source?.referrals === "number" ? `: ${mergePrompt.source.referrals}` : ""}</li>
            <li>✅ связанные аккаунты{mergePrompt.source?.linked_providers?.length ? `: ${mergePrompt.source.linked_providers.join(", ")}` : ""}</li>
          </ul>
          <p><strong>Это действие нельзя отменить.</strong></p>
          <div className="profile-merge-dialog__actions">
            <button className="button button--secondary" type="button" disabled={isLinking} onClick={() => setMergePrompt(null)}>Отмена</button>
            <button className="button button--primary" type="button" disabled={isLinking} onClick={confirmMerge}>Объединить аккаунты</button>
          </div>
        </div>
      ) : null}

      <button className="button button--ghost profile-logout-button" type="button" onClick={() => { console.info("[BLOOM_LOGOUT_TRACE] logout_button_clicked"); onLogout(); }}>
        Выйти из профиля
      </button>

      <div className="info-panel legal-documents-panel">
        <strong>Документы</strong>
        <ul className="legal-document-list">
          {legalDocuments.map((document) => (
            <li key={document.href}>
              <a href={document.href} target="_blank" rel="noopener noreferrer">
                {document.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
