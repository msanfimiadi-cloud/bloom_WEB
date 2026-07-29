const root = document.querySelector('#root');
const browserAppUrl = (() => {
  const url = new URL('https://app.bloomclub.ru/');
  const currentParams = new URLSearchParams(window.location.search);
  ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'startapp', 'ref', 'referral', 'referral_code'].forEach((field) => {
    const value = currentParams.get(field);
    if (value) url.searchParams.set(field, value);
  });
  return url.toString();
})();

const cities = [
  'Новосибирск',
  'Череповец',
];

const categoryDirections = [
  { slug: 'krasota', title: 'Красота' },
  { slug: 'manikyur-pedikyur', title: 'Маникюр / педикюр' },
  { slug: 'volosy-okrashivanie', title: 'Волосы / окрашивание' },
  { slug: 'brovi-resnitsy', title: 'Брови / ресницы' },
  { slug: 'kosmetologiya', title: 'Косметология' },
  { slug: 'massazh-spa', title: 'Массаж / SPA' },
  { slug: 'fitnes-yoga', title: 'Фитнес / йога' },
  { slug: 'zdorove', title: 'Здоровье' },
  { slug: 'psihologiya', title: 'Психология' },
  { slug: 'odezhda-aksessuary', title: 'Одежда / аксессуары' },
  { slug: 'kafe-restorany', title: 'Кафе / рестораны' },
  { slug: 'obuchenie-master-klassy', title: 'Обучение / мастер-классы' },
  { slug: 'fotosessii', title: 'Фотосессии' },
  { slug: 'cvety-podarki', title: 'Цветы / подарки' },
  { slug: 'drugoe', title: 'Другое' },
];

const categories = categoryDirections.map((category) => category.title);

const landingMenuLinks = [
  { href: '#landing-about', label: 'О клубе' },
  { href: '#landing-how', label: 'Как это работает' },
  { href: '#landing-partners', label: 'Партнёры' },
  { href: '#landing-subscription', label: 'Подписка' },
  { href: '#landing-contacts', label: 'Контакты' },
];

const editorialFeaturedCategories = [
  { slug: 'krasota', title: 'Красота', text: 'Салоны и уход', image: '/assets/editorial/category-beauty.webp' },
  { slug: 'manikyur-pedikyur', title: 'Маникюр', text: 'Студии и мастера', image: '/assets/editorial/category-manicure.webp' },
  { slug: 'massazh-spa', title: 'Массаж & SPA', text: 'Отдых и восстановление', image: '/assets/editorial/category-spa.webp' },
  { slug: 'fitnes-yoga', title: 'Фитнес & йога', text: 'Движение и баланс', image: '/assets/editorial/category-yoga.webp' },
  { slug: 'kafe-restorany', title: 'Кафе', text: 'Встречи и впечатления', image: '/assets/editorial/category-cafe.webp' },
  { slug: 'cvety-podarki', title: 'Цветы & подарки', text: 'Особенные поводы', image: '/assets/editorial/category-flowers.webp' },
];

// The previous sakura wallpaper and animated petals are deliberately preserved.
// Switch this flag to true to restore the former public landing treatment.
const publicLandingLegacyEffectsEnabled = false;

const landingStatsFallback = {
  members_count: 125,
  partners_count: 18,
  savings_total: 53500,
  giveaway_title: 'Розыгрыш месяца',
  giveaway_current: 'Приз месяца',
  giveaway_subtitle: 'доступно участницам клуба',
  giveaway_empty_text: 'Информация о призах появится после настройки розыгрыша.',
  giveaway_items: [
    { title: 'Приз месяца', is_active: true, sort_order: 0 },
  ],
};

const landingStatsState = {
  data: { ...landingStatsFallback },
  loaded: false,
  loading: false,
  error: '',
};

const landingPartnerModalState = {
  isOpen: false,
  selectedLandingDirection: null,
  partners: [],
  cache: {},
  selectedPartnerIndex: 0,
  activePhotoIndex: 0,
  loading: false,
  error: '',
};


const fallbackClientCities = [
  { id: 1, slug: 'novosibirsk', name: 'Новосибирск' },
  { id: 2, slug: 'cherepovets', name: 'Череповец' },
];

const fallbackClientCategories = [
  { slug: 'krasota', title: 'Красота' },
  { slug: 'manikyur-pedikyur', title: 'Маникюр / педикюр' },
  { slug: 'volosy-okrashivanie', title: 'Волосы / окрашивание' },
  { slug: 'brovi-resnitsy', title: 'Брови / ресницы' },
  { slug: 'kosmetologiya', title: 'Косметология' },
  { slug: 'massazh-spa', title: 'Массаж / SPA' },
  { slug: 'fitnes-yoga', title: 'Фитнес / йога' },
  { slug: 'zdorove', title: 'Здоровье' },
  { slug: 'psihologiya', title: 'Психология' },
  { slug: 'odezhda-aksessuary', title: 'Одежда / аксессуары' },
  { slug: 'kafe-restorany', title: 'Кафе / рестораны' },
  { slug: 'obuchenie-master-klassy', title: 'Обучение / мастер-классы' },
  { slug: 'fotosessii', title: 'Фотосессии' },
  { slug: 'cvety-podarki', title: 'Цветы / подарки' },
  { slug: 'drugoe', title: 'Другое' },
];

const featureCards = [
  {
    title: 'Привилегии у партнёров',
    text: 'Салоны, кафе, SPA, фитнес и lifestyle-сервисы города.',
  },
  {
    title: 'Подарки и розыгрыши',
    text: 'Каждый месяц — новые призы, beauty-боксы и сертификаты.',
  },
  {
    title: 'Код привилегии',
    text: 'Покажите короткий код партнёру — он подтвердит использование в боте.',
  },
  {
    title: 'Ваш город',
    text: 'Выбирайте город и открывайте актуальные предложения рядом.',
  },
];

const clubAvatarSrc = '/assets/club-avatar.png';

const legalDocuments = [
  {
    label: 'Публичная оферта',
    href: '/offer/',
  },
  {
    label: 'Политика конфиденциальности',
    href: '/privacy/',
  },
  {
    label: 'Пользовательское соглашение',
    href: '/terms/',
  },
  {
    label: 'Согласие на обработку персональных данных',
    href: '/personal-data-consent/',
  },
];

const renderLegalDocumentLinks = (className = 'legal-links') => `
  <ul class="${className}">
    ${legalDocuments.map((document) => `
      <li><a href="${document.href}" target="_blank" rel="noopener">${document.label}</a></li>
    `).join('')}
  </ul>
`;


const sakuraEdgePetalMarkup = Array.from({ length: 68 }, (_, index) => (
  `<span class="sakura-petal sakura-petal--${index + 1}"></span>`
)).join('');

const sakuraCenterPetalMarkup = Array.from({ length: 20 }, (_, index) => (
  `<span class="sakura-petal sakura-petal--center sakura-petal--center-${index + 1}"></span>`
)).join('');

const sakuraPetalMarkup = `${sakuraEdgePetalMarkup}${sakuraCenterPetalMarkup}`;

const renderLegacyPublicLandingEffects = () => (publicLandingLegacyEffectsEnabled ? `
  <div class="sakura-layer sakura-layer--landing" aria-hidden="true">
    <div class="sakura-landing-backdrop"></div>
    ${sakuraPetalMarkup}
  </div>
` : '');

const cabinetPetalMarkup = Array.from({ length: 18 }, (_, index) => {
  const depthClass = index % 3 === 0 ? 'cabinet-petal--near' : 'cabinet-petal--far';

  return `<span class="cabinet-petal ${depthClass} cabinet-petal--${index + 1}"></span>`;
}).join('');

const renderCabinetAmbientLayer = () => `
  <div class="cabinet-ambient" aria-hidden="true">
    <span class="cabinet-ambient__glow cabinet-ambient__glow--rose"></span>
    <span class="cabinet-ambient__glow cabinet-ambient__glow--cream"></span>
    <span class="cabinet-ambient__glow cabinet-ambient__glow--blush"></span>
    <div class="cabinet-petals">
      ${cabinetPetalMarkup}
    </div>
  </div>
`;


const getPasswordSetupParams = () => {
  const params = new URLSearchParams(window.location.search);
  const setupToken = params.get('setup_token');
  return {
    setupToken: setupToken ? setupToken.trim() : '',
    login: (params.get('login') || '').trim(),
  };
};

const getClientLoginPrefillParams = () => {
  const params = new URLSearchParams(window.location.search);
  const clientLogin = (params.get('client_login') || params.get('login') || '').trim();
  return {
    clientLogin,
  };
};

const applyClientLoginPrefill = () => {
  const { clientLogin } = getClientLoginPrefillParams();
  if (!clientLogin || getPasswordSetupParams().setupToken) {
    return;
  }

  // client_login opens client login mode and uses login prefill for VK onboarding links.
  setLoginMode('client');
  const loginInput = document.querySelector('[data-login-form] input[name="email"]');
  if (loginInput) {
    loginInput.value = clientLogin;
    loginInput.focus();
  }
};

const renderPasswordSetupApp = () => {
  const { login } = getPasswordSetupParams();
  document.body.classList.remove('is-dashboard');
  document.body.classList.remove('is-editorial-landing');
  root.innerHTML = `
    <div class="sakura-layer" aria-hidden="true">
      ${sakuraPetalMarkup}
    </div>
    <main class="app-shell setup-password-shell">
      <section class="panel setup-password-panel" aria-labelledby="setup-password-title">
        <p class="section-kicker">VK onboarding</p>
        <h1 id="setup-password-title">Задайте пароль</h1>
        <p>Придумайте пароль для входа в личный кабинет клуба.</p>
        <form class="login-form setup-password-form" data-password-setup-form>
          <label>
            Логин
            <input type="text" name="login" autocomplete="username" value="${escapeHtml(login)}" readonly placeholder="Логин появится после установки, если VK-бот не передал email или телефон" />
          </label>
          <label>
            Новый пароль
            <input type="password" name="password" autocomplete="new-password" placeholder="Минимум 8 символов" required />
          </label>
          <label>
            Повторите пароль
            <input type="password" name="password_confirm" autocomplete="new-password" placeholder="Повторите пароль" required />
          </label>
          <button type="submit">Сохранить пароль</button>
          <p class="login-message" data-password-setup-message role="status" aria-live="polite"></p>
        </form>
      </section>
    </main>
  `;
};


const normalizeLandingStats = (data = {}) => {
  const items = Array.isArray(data.giveaway_items) ? data.giveaway_items : landingStatsFallback.giveaway_items;
  return {
    members_count: Number.isFinite(Number(data.members_count)) ? Number(data.members_count) : landingStatsFallback.members_count,
    partners_count: Number.isFinite(Number(data.partners_count)) ? Number(data.partners_count) : landingStatsFallback.partners_count,
    savings_total: Number.isFinite(Number(data.savings_total)) ? Number(data.savings_total) : landingStatsFallback.savings_total,
    giveaway_title: String(data.giveaway_title || landingStatsFallback.giveaway_title).trim(),
    giveaway_current: String(data.giveaway_current || landingStatsFallback.giveaway_current).trim(),
    giveaway_subtitle: String(data.giveaway_subtitle || landingStatsFallback.giveaway_subtitle).trim(),
    giveaway_empty_text: String(data.giveaway_empty_text || landingStatsFallback.giveaway_empty_text).trim(),
    giveaway_items: items.map((item, index) => ({
      title: String(item?.title || '').trim(),
      description: String(item?.description || '').trim(),
      is_active: item?.is_active !== false,
      sort_order: Number.isFinite(Number(item?.sort_order)) ? Number(item.sort_order) : index,
    })).filter((item) => item.title),
  };
};

const getLandingStats = () => normalizeLandingStats(landingStatsState.data);

const loadLandingStats = async () => {
  if (landingStatsState.loading || landingStatsState.loaded) return;
  landingStatsState.loading = true;
  landingStatsState.error = '';
  try {
    const response = await fetch('/api/v1/public/landing/stats');
    if (!response.ok) {
      throw new Error(await buildErrorMessage(response));
    }
    landingStatsState.data = normalizeLandingStats(await response.json());
    landingStatsState.loaded = true;
  } catch (error) {
    landingStatsState.data = { ...landingStatsFallback };
    landingStatsState.loaded = true;
    landingStatsState.error = error.message || 'Не удалось загрузить показатели.';
  } finally {
    landingStatsState.loading = false;
    if (!adminState.user && !partnerState.user && !clientState.user && root.querySelector('.hero-proof-grid')) {
      renderPublicApp();
      applyClientLoginPrefill();
    }
  }
};

const renderPublicApp = () => {
  const landingStats = getLandingStats();
  document.body.classList.remove('is-dashboard');
  document.body.classList.add('is-editorial-landing');
  root.innerHTML = `
  ${renderLegacyPublicLandingEffects()}
  <main class="editorial-landing">
    <header class="editorial-header" id="landing-about">
      <a class="editorial-brand" href="#landing-about" aria-label="Bloom Club — на главную">
        <span class="editorial-brand__name">Bloom Club</span>
        <span class="editorial-brand__caption">Клуб привилегий для девушек</span>
      </a>
      <nav class="editorial-nav" aria-label="Основная навигация">
        ${landingMenuLinks.map((link) => `<a href="${link.href}" data-landing-menu-link>${link.label}</a>`).join('')}
      </nav>
      <div class="editorial-header__actions">
        <a class="editorial-login-link" href="#login">Войти</a>
        <a class="editorial-button editorial-button--small" href="${browserAppUrl}">Стать участницей</a>
        <div class="landing-menu editorial-mobile-menu">
          <button class="landing-menu-toggle" type="button" data-landing-menu-toggle aria-expanded="false" aria-controls="landing-menu-panel">Меню</button>
          <div class="landing-menu-panel" id="landing-menu-panel" data-landing-menu-panel hidden>
            ${landingMenuLinks.map((link) => `<a href="${link.href}" data-landing-menu-link>${link.label}</a>`).join('')}
            <a href="#login" data-landing-menu-link>Войти</a>
          </div>
        </div>
      </div>
    </header>

    <section class="editorial-hero" aria-labelledby="hero-title">
      <div class="editorial-hero__copy">
        <p class="editorial-kicker">Твой мир привилегий</p>
        <h1 id="hero-title">Выгодные<br><em>привилегии</em></h1>
        <p class="editorial-hero__lead">Красота, забота, отдых и вдохновение — специальные предложения у лучших партнёров города.</p>
        <div class="editorial-hero__actions">
          <a class="editorial-button" href="${browserAppUrl}">Стать участницей <span aria-hidden="true">→</span></a>
          <a class="editorial-text-link" href="#landing-partners">Смотреть партнёров</a>
        </div>
        <dl class="editorial-stats hero-proof-grid" aria-label="Показатели клуба">
          <div><dt>${escapeHtml(landingStats.members_count)}+</dt><dd>участниц</dd></div>
          <div><dt>${escapeHtml(landingStats.partners_count)}+</dt><dd>партнёров</dd></div>
          <div><dt>${escapeHtml(formatMoneyLabel(Number(landingStats.savings_total)))}</dt><dd>общая экономия</dd></div>
        </dl>
      </div>
      <div class="editorial-hero__visual">
        <img src="/assets/editorial/hero-blossoms.webp" alt="Цветущая ветка в мягком весеннем свете" fetchpriority="high" />
        <article class="editorial-testimonial">
          <img src="/assets/editorial/member-anna.webp" alt="Анна, участница Bloom Club" />
          <div>
            <p>«Открыла для себя любимые места и уже сэкономила больше стоимости подписки»</p>
            <span>Анна · участница клуба</span>
          </div>
        </article>
      </div>
    </section>

    <section class="editorial-how" id="landing-how" aria-labelledby="landing-how-title">
      <div class="editorial-section-heading">
        <p class="editorial-kicker">Всё очень просто</p>
        <h2 id="landing-how-title">Как это работает</h2>
      </div>
      <ol class="editorial-steps">
        <li><span class="editorial-step__number">01</span><img src="/assets/icons/user-plus.svg" alt="" /><h3>Вступи в клуб</h3><p>Оформи доступ за пару минут в приложении.</p></li>
        <li><span class="editorial-step__number">02</span><img src="/assets/icons/storefront.svg" alt="" /><h3>Выбери партнёра</h3><p>Найди место и предложение, которое тебе подходит.</p></li>
        <li><span class="editorial-step__number">03</span><img src="/assets/icons/gift.svg" alt="" /><h3>Получи привилегию</h3><p>Покажи код партнёру — после подтверждения экономия и номерок появятся в приложении.</p></li>
      </ol>
    </section>

    <section class="editorial-partners" id="landing-partners" aria-labelledby="categories-title">
      <div class="editorial-section-heading editorial-section-heading--row">
        <div><p class="editorial-kicker">Выбирай своё</p><h2 id="categories-title">Партнёры клуба</h2></div>
        <p>Нажми на категорию, чтобы посмотреть актуальных партнёров и их предложения.</p>
      </div>
      <div class="editorial-category-grid">
        ${editorialFeaturedCategories.map((category) => `
          <button class="editorial-category-card" type="button" data-landing-category-slug="${category.slug}">
            <img src="${category.image}" alt="${category.title}" loading="lazy" />
            <span class="editorial-category-card__overlay"><strong>${category.title}</strong><small>${category.text}</small></span>
          </button>
        `).join('')}
      </div>
      <div class="editorial-directions" id="landing-directions" aria-label="Категории партнёров">
        ${categoryDirections.map((category) => `<button type="button" data-landing-category-slug="${category.slug}">${category.title}</button>`).join('')}
      </div>
    </section>

    <section class="landing-partner-modal" data-landing-partner-modal aria-live="polite" hidden></section>

    <section class="editorial-subscription" id="landing-subscription" aria-labelledby="subscription-offer-title">
      <img class="editorial-subscription__image" src="/assets/editorial/subscription-still-life.webp" alt="Цветущие ветки в вазе и чашка на светлом столе" loading="lazy" />
      <div class="editorial-subscription__content">
        <p class="editorial-kicker">Одна подписка — много возможностей</p>
        <h2 id="subscription-offer-title">Всё лучшее<br><em>для тебя</em></h2>
        <p>Доступ к привилегиям, подаркам, закрытым …107565 tokens truncated…paymentActionStatus = 'Оплата подтверждена. Подписка продлена.';
    await loadAdminPaymentRequests();
  } catch (error) {
    adminState.paymentActionError = error.message || 'Не удалось подтвердить оплату.';
  }
  renderAdminLayout();
};

const handleAdminPaymentReject = async (requestId) => {
  adminState.paymentActionStatus = '';
  adminState.paymentActionError = '';
  renderAdminLayout();
  try {
    await rejectAdminPaymentRequest(requestId, 'Отклонено администратором');
    adminState.paymentActionStatus = 'Заявка отклонена.';
    await loadAdminPaymentRequests();
  } catch (error) {
    adminState.paymentActionError = error.message || 'Не удалось отклонить заявку.';
  }
  renderAdminLayout();
};

const handleAdminPartnerImageInput = async (input) => {
  const file = input.files?.[0];
  if (!file) return;
  const kind = input.dataset.adminPartnerImageUpload;
  const partnerId = input.dataset.partnerId;
  setFormMessage('partnerImage');
  try {
    await uploadAdminPartnerImage(partnerId, kind, file);
    setFormMessage('partnerImage', 'Фото обновлено.');
    setPanelMessage('Фото партнёра обновлено.', 'success');
  } catch (error) {
    setFormMessage('partnerImage', error.message || 'Не удалось загрузить фото.');
    setPanelMessage(error.message || 'Не удалось загрузить фото.', 'error');
  }
  renderAdminLayout();
};

const handlePartnerProfileImageInput = async (input) => {
  const file = input.files?.[0];
  if (!file) return;
  const kind = input.dataset.partnerImageUpload;
  const statusKey = `profileImages:${kind}`;
  setPartnerFormMessage('profileImages');
  setPartnerUploadStatus(statusKey, 'loading', 'Загружаем изображение…');
  renderPartnerLayout();
  try {
    await uploadPartnerProfileImage(kind, file);
    const successMessage = 'Изображение загружено';
    setPartnerUploadStatus(statusKey, 'success', successMessage);
    setPartnerFormMessage('profileImages', successMessage);
    setPartnerPanelMessage(successMessage, 'success');
  } catch (error) {
    const errorMessage = getSafeUploadErrorMessage(error);
    setPartnerUploadStatus(statusKey, 'error', errorMessage);
    setPartnerFormMessage('profileImages', errorMessage);
    setPartnerPanelMessage(errorMessage, 'error');
  } finally {
    input.value = "";
    renderPartnerLayout();
  }
};

const handleAdminOfferImageInput = async (input) => {
  const file = input.files?.[0];
  if (!file) return;
  const offerId = input.dataset.offerId;
  setFormMessage('offerImage');
  try {
    await uploadAdminOfferImage(offerId, file);
    setFormMessage('offerImage', 'Фото предложения обновлено.');
    setPanelMessage('Фото предложения обновлено.', 'success');
  } catch (error) {
    setFormMessage('offerImage', error.message || 'Не удалось загрузить фото предложения.');
    setPanelMessage(error.message || 'Не удалось загрузить фото предложения.', 'error');
  }
  renderAdminLayout();
};

const handlePartnerOfferImageInput = async (input) => {
  const file = input.files?.[0];
  if (!file) return;
  const offerId = input.dataset.offerId;
  const statusKey = offerId ? `offerImage:${offerId}` : 'offerImage:new';
  if (!offerId) {
    const saveFirstMessage = 'Сначала сохраните предложение, затем загрузите фото';
    setPartnerUploadStatus(statusKey, 'error', saveFirstMessage);
    setPartnerFormMessage('offerImage', saveFirstMessage);
    input.value = "";
    renderPartnerLayout();
    return;
  }
  setPartnerFormMessage('offerImage');
  setPartnerUploadStatus(statusKey, 'loading', 'Загружаем изображение…');
  renderPartnerLayout();
  try {
    await uploadPartnerOfferImage(offerId, file);
    const successMessage = 'Изображение загружено';
    setPartnerUploadStatus(statusKey, 'success', successMessage);
    setPartnerFormMessage('offerImage', successMessage);
    setPartnerPanelMessage(successMessage, 'success');
  } catch (error) {
    const errorMessage = getSafeUploadErrorMessage(error);
    setPartnerUploadStatus(statusKey, 'error', errorMessage);
    setPartnerFormMessage('offerImage', errorMessage);
    setPartnerPanelMessage(errorMessage, 'error');
  } finally {
    input.value = "";
    renderPartnerLayout();
  }
};

const handlePartnerOfferPhotoInput = async (input) => {
  const file = input.files?.[0];
  const offerId = input.dataset.offerId;
  if (!file || !offerId) return;
  setPartnerFormMessage('offerPhoto');
  try {
    await uploadPartnerOfferPhoto(offerId, file);
    setPartnerFormMessage('offerPhoto', 'Фото услуги загружено.');
    setPartnerPanelMessage('Фото услуги добавлено в галерею.', 'success');
  } catch (error) {
    setPartnerFormMessage('offerPhoto', error.message || 'Не удалось загрузить фото услуги.');
    setPartnerPanelMessage(error.message || 'Не удалось загрузить фото услуги.', 'error');
  } finally {
    input.value = '';
    renderPartnerLayout();
  }
};

const handlePartnerOfferPhotoFormSubmit = async (form) => {
  const formData = new FormData(form);
  const offerId = form.dataset.offerId;
  const photoId = form.dataset.photoId;
  setPartnerFormMessage('offerPhoto');
  try {
    await updatePartnerOfferPhoto(offerId, photoId, {
      alt_text: getOptionalText(formData, 'alt_text'),
      sort_order: Number(formData.get('sort_order') || 0),
      is_active: formData.has('is_active'),
    });
    setPartnerFormMessage('offerPhoto', 'Фото услуги обновлено.');
    setPartnerPanelMessage('Изменения сохранены.', 'success');
  } catch (error) {
    setPartnerFormMessage('offerPhoto', error.message || 'Не удалось обновить фото услуги.');
    setPartnerPanelMessage(error.message || 'Не удалось обновить фото услуги.', 'error');
  }
  renderPartnerLayout();
};

root.addEventListener('change', (event) => {
  const orderAmountToggle = event.target.closest('[data-order-amount-toggle]');
  if (orderAmountToggle) {
    const form = orderAmountToggle.closest('form');
    const requiresOrderAmount = orderAmountToggle.checked;
    const percentSection = form?.querySelector('[data-order-amount-percent]');
    const percentInput = percentSection?.querySelector('input[name="variable_discount_percent"]');
    const fixedPricing = form?.querySelector('[data-fixed-offer-pricing]');

    if (percentSection) percentSection.hidden = !requiresOrderAmount;
    if (percentInput) {
      percentInput.disabled = !requiresOrderAmount;
      percentInput.required = requiresOrderAmount;
      if (requiresOrderAmount) percentInput.focus();
    }
    if (fixedPricing) {
      fixedPricing.hidden = requiresOrderAmount;
      fixedPricing.querySelectorAll('input').forEach((input) => {
        input.disabled = requiresOrderAmount;
      });
    }
    return;
  }
  const acquiringPaymentStatus = event.target.closest('[data-acquiring-payment-status]');
  if (acquiringPaymentStatus) {
    adminState.acquiringPaymentStatusFilter = acquiringPaymentStatus.value || '';
    void loadAcquiringPayments().then(renderAdminLayout).catch((error) => { setPanelMessage(error.message || 'Не удалось загрузить платежи.', 'error'); renderAdminLayout(); });
    return;
  }
  const bloomCalendarMonth = event.target.closest('[data-bloom-calendar-month]');
  if (bloomCalendarMonth) {
    adminState.flowerCalendarMonth = bloomCalendarMonth.value || new Date().toISOString().slice(0, 7);
    renderAdminLayout();
    return;
  }

  const adminPartnerCategoryInput = event.target.closest('[data-admin-partner-wizard-form] input[name="category_ids"]');
  if (adminPartnerCategoryInput) {
    captureAdminPartnerCategoryDraft(adminPartnerCategoryInput.closest('[data-admin-partner-wizard-form]'));
    return;
  }

  const adminPhotoInput = event.target.closest('[data-admin-partner-photo-upload]');
  if (adminPhotoInput) {
    handleAdminPartnerPhotoInput(adminPhotoInput);
    return;
  }

  const partnerPhotoInput = event.target.closest('[data-partner-photo-upload]');
  if (partnerPhotoInput) {
    handlePartnerPhotoInput(partnerPhotoInput);
    return;
  }

  const adminImageInput = event.target.closest('[data-admin-partner-image-upload]');
  if (adminImageInput) {
    handleAdminPartnerImageInput(adminImageInput);
    return;
  }

  const partnerImageInput = event.target.closest('[data-partner-image-upload]');
  if (partnerImageInput) {
    handlePartnerProfileImageInput(partnerImageInput);
    return;
  }

  const adminOfferImageInput = event.target.closest('[data-admin-offer-image-upload]');
  if (adminOfferImageInput) {
    handleAdminOfferImageInput(adminOfferImageInput);
    return;
  }

  const partnerOfferImageInput = event.target.closest('[data-partner-offer-image-upload]');
  if (partnerOfferImageInput) {
    handlePartnerOfferImageInput(partnerOfferImageInput);
    return;
  }
  const partnerOfferPhotoInput = event.target.closest('[data-partner-offer-photo-upload]');
  if (partnerOfferPhotoInput) {
    handlePartnerOfferPhotoInput(partnerOfferPhotoInput);
    return;
  }
  const partnerOfferGallerySelect = event.target.closest('[data-partner-offer-gallery-select]');
  if (partnerOfferGallerySelect) {
    partnerState.selectedOfferIdForGallery = partnerOfferGallerySelect.value;
    loadPartnerOfferPhotos(partnerState.selectedOfferIdForGallery).then(renderPartnerLayout);
    return;
  }


  const giveawayEntriesSelect = event.target.closest('[data-admin-giveaway-entries-select]');
  if (giveawayEntriesSelect) {
    adminState.selectedGiveawayIdForEntriesManual = giveawayEntriesSelect.value;
    adminState.selectedGiveawayIdForEdit = '';
    adminState.giveawayEntries = null;
    adminState.giveawayRecheckResult = null;
    adminState.giveawayParticipantSubscriptionResult = null;
    renderAdminLayout();
    syncGiveawayEntriesSelection({ force: true }).then(() => renderAdminLayout()).catch((error) => { setFormMessage('giveaway', error.message || 'Не удалось загрузить номера розыгрыша'); renderAdminLayout(); });
    return;
  }

  const paymentAccessDaysInput = event.target.closest('[data-admin-payment-access-days]');
  if (paymentAccessDaysInput) {
    adminState.paymentApprovalDays = Math.max(1, Number(paymentAccessDaysInput.value) || 30);
    return;
  }

  const paymentStatusFilter = event.target.closest('[data-admin-payment-status-filter]');
  if (paymentStatusFilter) {
    adminState.paymentRequestsStatusFilter = paymentStatusFilter.value;
    adminState.paymentActionStatus = '';
    adminState.paymentActionError = '';
    loadActiveTabData();
    return;
  }

  const activityEventSelect = event.target.closest('[data-admin-activity-event-type]');
  if (activityEventSelect) {
    adminState.activityEventType = activityEventSelect.value;
    loadActiveTabData();
    return;
  }

  const picker = event.target.closest('[data-partner-picker]');
  if (!picker) {
    return;
  }

  if (picker.dataset.partnerPicker === 'offers') {
    adminState.selectedPartnerIdForOffers = picker.value;
    adminState.selectedOfferIdForEdit = '';
    setFormMessage('offerEdit');
  } else if (picker.dataset.partnerPicker === 'qr') {
    adminState.selectedPartnerIdForQr = picker.value;
    adminState.selectedQrLinkIdForEdit = '';
    setFormMessage('qrEdit');
  }

  loadActiveTabData();
});

root.addEventListener('custom-select:change', (event) => {
  const customSelect = event.target.closest('[data-custom-select]');
  if (!customSelect) {
    return;
  }

  if (customSelect.matches('[data-admin-payment-status-filter]')) {
    adminState.paymentRequestsStatusFilter = event.detail.value;
    adminState.paymentActionStatus = '';
    adminState.paymentActionError = '';
    loadActiveTabData();
    return;
  }

  if (customSelect.matches('[data-admin-activity-event-type]')) {
    adminState.activityEventType = event.detail.value;
    loadActiveTabData();
    return;
  }

  if (customSelect.matches('[data-partner-picker]')) {
    if (customSelect.dataset.partnerPicker === 'offers') {
      adminState.selectedPartnerIdForOffers = event.detail.value;
      adminState.selectedOfferIdForEdit = '';
      setFormMessage('offerEdit');
    } else if (customSelect.dataset.partnerPicker === 'qr') {
      adminState.selectedPartnerIdForQr = event.detail.value;
      adminState.selectedQrLinkIdForEdit = '';
      setFormMessage('qrEdit');
    }

    loadActiveTabData();
  }
});

document.addEventListener('click', (event) => {
  if (!event.target.closest('[data-custom-select]')) {
    closeCustomSelects();
  }
});

document.addEventListener('keydown', (event) => {
  const partnerWizardForm = event.target.closest?.('[data-admin-partner-wizard-form]');
  if (event.key === 'Escape' && clientState.selectedPartnerModalId) {
    event.preventDefault();
    resetClientPartnerModalState();
    renderClientLayout();
    return;
  }

  const trigger = event.target.closest?.('.custom-select-trigger');
  const openSelect = document.querySelector('[data-custom-select].custom-select--open');
  const activeSelect = trigger?.closest('[data-custom-select]') || openSelect;

  if (!activeSelect) {
    return;
  }

  if (event.key === 'Escape') {
    event.preventDefault();
    closeCustomSelect(activeSelect);
    getCustomSelectParts(activeSelect).trigger?.focus();
    return;
  }

  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault();
    if (!activeSelect.classList.contains('custom-select--open')) {
      openCustomSelect(activeSelect);
      return;
    }
    moveCustomSelectActiveOption(activeSelect, event.key === 'ArrowDown' ? 1 : -1);
    return;
  }

  if (event.key === 'Enter') {
    if (activeSelect.classList.contains('custom-select--open')) {
      event.preventDefault();
      selectCustomSelectOption(activeSelect.querySelector('.custom-select-option--active'));
    }
    return;
  }

  if (event.key === ' ' && trigger) {
    event.preventDefault();
    if (activeSelect.classList.contains('custom-select--open')) {
      selectCustomSelectOption(activeSelect.querySelector('.custom-select-option--active'));
    } else {
      openCustomSelect(activeSelect);
    }
  }
});

const handleGiveawayFormSubmit = async (form) => {
  const id = form.dataset.giveawayId;
  const payload = buildGiveawayPayload(form);
  adminState.giveawaySaving = true;
  setFormMessage('giveaway', 'Сохранение…');
  setPanelMessage();
  renderAdminLayout();

  try {
    const savedGiveaway = id
      ? await apiFetch(`/api/v1/admin/giveaways/${id}`, { method: 'PUT', body: JSON.stringify(payload), timeoutMs: 30000 })
      : await postJson('/api/v1/admin/giveaways', payload);
    const savedGiveawayId = savedGiveaway?.id || id;
    adminState.selectedGiveawayIdForEdit = savedGiveawayId ? String(savedGiveawayId) : '';
    await loadGiveaways();
    if (savedGiveawayId) {
      await syncGiveawayEntriesSelection({ force: true });
    }
    setFormMessage('giveaway', 'Розыгрыш сохранён.');
    setPanelMessage('Розыгрыш сохранён', 'success');
  } catch (error) {
    const message = error?.message || 'Не удалось сохранить розыгрыш.';
    setFormMessage('giveaway', message);
    setPanelMessage(message, 'error');
  } finally {
    adminState.giveawaySaving = false;
    renderAdminLayout();
  }
};

root.addEventListener('input', (event) => {
  const countInput = event.target.closest('[data-admin-giveaway-winners-count]');
  if (!countInput) return;
  const form = countInput.closest('[data-admin-giveaway-form]');
  const list = form?.querySelector('[data-admin-giveaway-place-list]');
  if (list) list.innerHTML = renderGiveawayPlaceRows({ winners_count: Number(countInput.value || 0), prizes: [] });
});

root.addEventListener('submit', (event) => {
  const submittedForm = event.target.closest('form');
  if (submittedForm && !validateRequiredCustomSelects(submittedForm)) {
    event.preventDefault();
    return;
  }

  const passwordSetup = event.target.closest('[data-password-setup-form]');
  if (passwordSetup) {
    event.preventDefault();
    handlePasswordSetupSubmit(passwordSetup);
    return;
  }

  const login = event.target.closest('[data-login-form]');
  if (login) {
    event.preventDefault();
    handleLoginSubmit(login);
    return;
  }

  const adminGalleryForm = event.target.closest('[data-admin-gallery-form]');
  if (adminGalleryForm) {
    event.preventDefault();
    handleAdminGalleryFormSubmit(adminGalleryForm);
    return;
  }

  const partnerGalleryForm = event.target.closest('[data-partner-gallery-form]');
  if (partnerGalleryForm) {
    event.preventDefault();
    handlePartnerGalleryFormSubmit(partnerGalleryForm);
    return;
  }
  const partnerOfferPhotoForm = event.target.closest('[data-partner-offer-photo-form]');
  if (partnerOfferPhotoForm) {
    event.preventDefault();
    handlePartnerOfferPhotoFormSubmit(partnerOfferPhotoForm);
    return;
  }

  const giveawayForm = event.target.closest('[data-admin-giveaway-form]');
  if (giveawayForm) {
    event.preventDefault();
    handleGiveawayFormSubmit(giveawayForm);
    return;
  }

  const adminForm = event.target.closest('[data-admin-form]');
  if (adminForm) {
    event.preventDefault();
    handleAdminFormSubmit(adminForm);
    return;
  }

  const partnerForm = event.target.closest('[data-partner-form]');
  if (partnerForm) {
    event.preventDefault();
    handlePartnerFormSubmit(partnerForm);
    return;
  }

  const clientForm = event.target.closest('[data-client-form]');
  if (clientForm) {
    event.preventDefault();
    handleClientFormSubmit(clientForm);
  }
});

const restoreClientSession = async () => {
  const token = getClientToken();
  if (!token) {
    showLoginForm();
    return;
  }

  try {
    const user = await requestClientUserMe();
    if (user.role !== 'client') {
      clearClientToken();
      showLoginForm();
      return;
    }
    setLoginMode('client');
    await showClientDashboard(user);
  } catch (error) {
    clearClientToken();
    showLoginForm();
  }
};

const restorePartnerSession = async () => {
  const token = getPartnerToken();
  if (!token) {
    await restoreClientSession();
    return;
  }

  try {
    const user = await requestPartnerUserMe();
    if (user.role !== 'partner') {
      clearPartnerToken();
      await restoreClientSession();
      return;
    }
    setLoginMode('partner');
    await showPartnerDashboard(user);
  } catch (error) {
    clearPartnerToken();
    await restoreClientSession();
  }
};

const restoreAdminSession = async () => {
  const token = getToken();
  if (!token) {
    await restorePartnerSession();
    return;
  }

  try {
    const user = await requestAdminMe();
    await showAdminDashboard(user);
  } catch (error) {
    clearToken();
    await restorePartnerSession();
  }
};

if (getPasswordSetupParams().setupToken) {
  renderPasswordSetupApp();
} else {
  restoreAdminSession();
}

