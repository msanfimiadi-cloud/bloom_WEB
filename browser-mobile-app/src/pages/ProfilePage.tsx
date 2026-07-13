import { isTimeoutError } from '../api/client';
import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { AppImage } from '../components/AppImage';
import { ContentText } from '../components/ContentText';
import { useContentText } from '../content/ContentContext';
import { useAddToHomeScreen } from '../utils/pwaInstall';
import type { City, ClientProfile, ClientProfilePatch, ReferralSummary, Subscription } from '../api/types';
import { pickText, toText } from '../utils/text';


const legalDocuments = [
  {
    label: 'Политика конфиденциальности',
    href: '/docs/Политика%20Конфиденциальности.docx',
  },
  {
    label: 'Пользовательское соглашение',
    href: '/docs/Пользовательское%20соглашение.docx',
  },
  {
    label: 'Согласие на обработку персональных данных',
    href: '/docs/Согласие%20на%20обработку%20персональных%20данных.docx',
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
  onSaveProfile: (payload: ClientProfilePatch) => Promise<ClientProfile>;
  referralSummary?: ReferralSummary | null;
  onLogout: () => void;
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

export function ProfilePage({ profile, cities, onSaveProfile, referralSummary, onLogout }: ProfilePageProps) {
  const safeCities = useMemo(() => (Array.isArray(cities) ? cities : []), [cities]);
  const initialName = getProfileDisplayName(profile);
  const initialCity = getCityName(profile?.city);
  const [name, setName] = useState(initialName);
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
  const [copyMessage, setCopyMessage] = useState('');
  const addToHomeScreen = useAddToHomeScreen();

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
      </div>

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
