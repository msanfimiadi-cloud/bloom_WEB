const root = document.querySelector('#root');

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
        <a class="editorial-button editorial-button--small" href="https://app.bloomclub.ru/">Стать участницей</a>
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
          <a class="editorial-button" href="https://app.bloomclub.ru/">Стать участницей <span aria-hidden="true">→</span></a>
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
        <p>Доступ к привилегиям, подаркам, закрытым предложениям и розыгрышам у партнёров клуба.</p>
        <div class="editorial-price" aria-label="349 ₽ на 30 дней"><strong>349 ₽</strong><span>на 30 дней</span></div>
        <ul>
          <li>Пробный период 15 дней, если он доступен для аккаунта</li>
          <li>Автоматического продления и повторных списаний нет</li>
          <li>Продление выполняется вручную</li>
        </ul>
        <div class="editorial-subscription__actions">
          <a class="editorial-button" href="https://app.bloomclub.ru/">Оформить подписку <span aria-hidden="true">→</span></a>
        </div>
      </div>
    </section>

    <section class="editorial-access" id="login" aria-labelledby="login-title">
      <span class="landing-anchor" id="landing-join" aria-hidden="true"></span>
      <div>
        <p class="editorial-kicker">Уже с нами?</p>
        <h2 id="login-title">Личный кабинет</h2>
        <p>Войдите как участница или партнёр клуба — все привычные функции остаются на месте.</p>
      </div>
      <div class="editorial-login-card">
        <div class="login-quick-access" aria-label="Быстрый вход" data-login-quick-card>
          <p class="login-quick-access__title">Выберите кабинет</p>
          <div class="login-quick-access__actions">
            <button class="login-quick-access__button" type="button" data-login-expand-mode="client">Я участница</button>
            <button class="login-quick-access__button" type="button" data-login-expand-mode="partner">Я партнёр</button>
          </div>
        </div>
        <div class="login-details" data-login-details hidden>
          <div class="login-mode-switch" role="tablist" aria-label="Тип входа">
            <button class="login-mode-button is-active" type="button" data-login-mode="admin" role="tab" aria-selected="true">Администратор</button>
            <button class="login-mode-button" type="button" data-login-mode="partner" role="tab" aria-selected="false">Партнёр</button>
            <button class="login-mode-button" type="button" data-login-mode="client" role="tab" aria-selected="false">Клиент</button>
          </div>
          <form class="login-form" data-login-form>
            <label>Логин<input type="text" name="email" autocomplete="username" placeholder="Email, телефон или логин" required /></label>
            <label>Пароль<input type="password" name="password" autocomplete="current-password" placeholder="Введите пароль" required /></label>
            <button type="submit">Войти</button>
            <p class="login-message" data-login-message role="status" aria-live="polite"></p>
          </form>
        </div>
        <div class="admin-dashboard" data-admin-dashboard hidden><h3>Админ-панель</h3><p>Вы вошли как: <strong data-admin-email></strong></p><button type="button" data-logout-button>Выйти</button></div>
        <div class="admin-dashboard partner-dashboard" data-partner-dashboard hidden></div>
        <div class="admin-dashboard client-dashboard" data-client-dashboard hidden></div>
      </div>
    </section>

    <section class="editorial-cities" id="landing-cities" aria-labelledby="city-selector-title">
      <div><p class="editorial-kicker">География клуба</p><h2 id="city-selector-title">Выберите город</h2><p class="editorial-cities__note">Чем больше мы растём, тем больше городов подключаем. Скоро появятся новые города.</p></div>
      <div class="city-choice-grid" role="radiogroup" aria-labelledby="city-selector-title">
        ${cities.map((city, index) => `<button class="city-choice${index === 0 ? ' is-active' : ''}" type="button" role="radio" aria-checked="${index === 0 ? 'true' : 'false'}" data-city-choice><span class="city-choice-title">${city}</span><span class="city-choice-meta">${city === 'Новосибирск' ? `${escapeHtml(landingStats.partners_count)} партнёров` : 'скоро открытие'}</span></button>`).join('')}
      </div>
    </section>

    <footer class="editorial-footer" id="landing-contacts" aria-labelledby="business-info-title">
      <div class="editorial-footer__brand"><span class="editorial-brand__name">Bloom Club</span><p>Федеральный клуб привилегий для девушек.</p></div>
      <div><h2 id="business-info-title">Поддержка и контакты</h2><p>Время работы: 09:00–18:00<br>по новосибирскому времени (UTC+7)</p><a href="mailto:danka1948@mail.ru">danka1948@mail.ru</a></div>
      <div><h2>Мы на связи</h2><a href="https://t.me/Wo_ClubNSK" target="_blank" rel="noopener noreferrer">Telegram-канал</a><a href="https://t.me/app_bloom_club_bot" target="_blank" rel="noopener noreferrer">Telegram-бот</a><a href="https://vk.ru/club238169934" target="_blank" rel="noopener noreferrer">ВКонтакте</a></div>
      <div><h2>Документы</h2>${renderLegalDocumentLinks('legal-links editorial-footer__links')}</div>
      <p class="editorial-footer__operator">© Bloom Club · ИП Глущенко Анастасия Дмитриевна · ИНН 541007956565 · ОГРНИП 323547600049744</p>
    </footer>
  </main>
`;
  bindPublicElements();
};




const authTokenKey = 'womenClubAdminAccessToken';
const partnerTokenKey = 'womenclub_partner_token';
const clientTokenKey = 'womenclub_client_token';
let activeLoginMode = 'admin';
const adminTabs = [
  { id: 'overview', label: 'Главная', group: 'Обзор' },
  { id: 'partners', label: 'Партнёры', group: 'Ежедневная работа' },
  { id: 'contentReview', label: 'На проверке', group: 'Ежедневная работа' },
  { id: 'payments', label: 'Платежи', group: 'Ежедневная работа' },
  { id: 'paymentRequests', label: 'Ручные заявки', group: 'Ежедневная работа' },
  { id: 'verifications', label: 'Подтверждения', group: 'Ежедневная работа' },
  { id: 'partnerAccess', label: 'Партнёрский доступ', group: 'Ежедневная работа' },
  { id: 'offers', label: 'Привилегии', group: 'Продвижение' },
  { id: 'qr', label: 'QR и лиды', group: 'Продвижение' },
  { id: 'giveaways', label: 'Розыгрыши', group: 'Продвижение' },
  { id: 'flower', label: 'Сад Bloom', group: 'Продвижение' },
  { id: 'users', label: 'Пользователи', group: 'Данные' },
  { id: 'activity', label: 'Журнал событий', group: 'Данные' },
  { id: 'cities', label: 'Города', group: 'Настройки' },
  { id: 'categories', label: 'Категории', group: 'Настройки' },
];

const adminState = {
  activeTab: 'overview',
  user: null,
  legacyContentWriteEnabled: true,
  users: [],
  cities: [],
  categories: [],
  partners: [],
  partnerPhotosByPartner: {},
  partnerAnalyticsById: {},
  selectedPartnerAnalytics: null,
  partnerAnalyticsLoading: false,
  partnerAnalyticsError: '',
  offers: [],
  contentReview: { offers: [], photos: [] },
  qrLinks: [],
  leads: [],
  verifications: [],
  partnerAccesses: [],
  flowerTasks: [],
  flowerSettings: { placement_mode: 'random', manual_position: 'top_right', daily_petals: 1 },
  flowerSpecialTasks: [],
  flowerAnalytics: null,
  flowerCalendarMonth: new Date().toISOString().slice(0, 7),
  paymentRequests: [],
  acquiringPayments: [],
  subscriptionPlans: [],
  acquiringPaymentStatusFilter: '',
  selectedAcquiringPayment: null,
  paymentRequestsLoading: false,
  paymentRequestsError: '',
  paymentRequestsStatusFilter: '',
  selectedPaymentRequest: null,
  paymentApprovalDays: 30,
  paymentActionStatus: '',
  paymentActionError: '',
  selectedPartnerIdForOffers: '',
  selectedPartnerIdForQr: '',
  selectedQrLinkIdForEdit: '',
  selectedPartnerIdForEdit: '',
  partnerFormOpen: false,
  partnerFormStep: 'basic',
  partnerFormInlineError: '',
  partnerFormCategoryIds: {},
  selectedCityIdForEdit: '',
  selectedCategoryIdForEdit: '',
  selectedOfferIdForEdit: '',
  panelMessage: '',
  formMessages: {},
  overviewPartialError: false,
  partnerFilters: {
    city: '',
    category: '',
    activity: 'all',
    photos: 'all',
    offers: 'all',
    verification: 'all',
  },
  search: {
    users: '',
    cities: '',
    categories: '',
    partners: '',
    offers: '',
    contentReview: '',
    qr: '',
    leads: '',
    verifications: '',
    partnerAccesses: '',
    paymentRequests: '',
  },
  activityItems: [],
  activityLoading: false,
  activityError: '',
  activityEventType: '',
  selectedPartnerIdForActivity: '',
  landingSettings: null,
  giveawayDrawerOpen: false,
  landingSettingsSaving: false,
  giveawaySaving: false,
  giveawayEntries: null,
  giveawayEntriesLoading: false,
  giveawayRecheckResult: null,
  giveaways: [],
  selectedGiveawayIdForEdit: '',
  selectedGiveawayIdForEntries: '',
  selectedGiveawayIdForEntriesManual: '',
};

const adminPartnerWizardSteps = [
  { key: 'basic', label: 'Основное' },
  { key: 'status', label: 'Категории' },
  { key: 'contacts', label: 'Контакты' },
  { key: 'description', label: 'Описание' },
  { key: 'media', label: 'Медиа' },
];

const getPartnerWizardStepIndex = (key) => adminPartnerWizardSteps.findIndex((step) => step.key === key);

const normalizeSearchText = (value) => String(value ?? '').trim().toLowerCase();

const getSearchableValue = (row, field) => {
  if (typeof field === 'function') {
    return field(row);
  }

  return row?.[field];
};

const filterAdminRows = (rows, query, fields) => {
  const normalizedQuery = normalizeSearchText(query);
  if (!normalizedQuery) {
    return rows;
  }

  return rows.filter((row) => fields.some((field) => normalizeSearchText(getSearchableValue(row, field)).includes(normalizedQuery)));
};

const searchableBool = (value) => `${formatBool(value)} ${value ? 'active активен активна активно да true' : 'inactive неактивен неактивна неактивно нет false'}`;

const partnerTabs = [
  { id: 'overview', label: 'Обзор', icon: '◎' },
  { id: 'profile', label: 'Профиль', icon: '♡' },
  { id: 'contacts', label: 'Контакты', icon: '☎' },
  { id: 'media', label: 'Медиа', icon: '🖼' },
  { id: 'services', label: 'Услуги', icon: '%' },
  { id: 'preview', label: 'Предпросмотр', icon: '◧' },
];

const partnerState = {
  activeTab: 'overview',
  user: null,
  profile: null,
  photos: [],
  offers: [],
  qrLinks: [],
  leads: [],
  verifications: [],
  analytics: null,
  analyticsLoading: false,
  analyticsError: '',
  activityItems: [],
  activityLoading: false,
  activityError: '',
  panelMessage: '',
  formMessages: {},
  selectedOfferIdForEdit: '',
  selectedOfferIdForGallery: '',
  offerPhotosByOfferId: {},
  isProfileDirty: false,
  profileSaveStatus: 'saved',
  uploadStatuses: {},
};

const toastState = {
  timeoutId: null,
};

const clientTabs = [
  { id: 'savings', label: 'Моя экономия', icon: '₽' },
  { id: 'profile', label: 'Профиль', icon: '♡' },
  { id: 'catalog', label: 'Каталог', icon: '✦' },
  { id: 'subscription', label: 'Моя подписка', icon: '₽' },
  { id: 'history', label: 'Мои привилегии', legacyLabel: 'История', icon: '↺' },
  { id: 'activity', label: 'Активность', icon: '•' },
  { id: 'giveaways', label: 'Розыгрыши', icon: '🎁' },
];

const clientState = {
  activeTab: 'profile',
  user: null,
  profile: null,
  subscription: null,
  partners: [],
  catalogLoaded: false,
  offersByPartner: {},
  selectedPartner: null,
  selectedPartnerId: '',
  selectedPartnerModalId: '',
  selectedPartnerModalPartner: null,
  selectedPartnerModalOffers: [],
  partnerModalGalleryIndex: 0,
  partnerModalOfferGalleryId: '',
  partnerModalOfferGalleryIndex: 0,
  partnerModalLoading: false,
  partnerModalError: '',
  latestVerification: null,
  vkLinkCode: null,
  vkLinkStatus: '',
  vkLinkMessage: '',
  verifications: [],
  activityItems: [],
  savings: null,
  savingsLoading: false,
  savingsError: '',
  savingsFilterMode: 'all',
  savingsFilterFromDate: '',
  savingsFilterToDate: '',
  savingsFilterUiError: '',
  activityLoading: false,
  activityError: '',
  catalogFilters: {
    q: '',
    category_slug: '',
    city_slug: '',
  },
  panelMessage: '',
  formMessages: {},
};

let loginForm = null;
let loginModeButtons = [];
let loginMessage = null;
let adminDashboard = null;
let partnerDashboard = null;
let clientDashboard = null;
let isLoginExpanded = false;

const bindPublicElements = () => {
  loginForm = document.querySelector('[data-login-form]');
  loginModeButtons = document.querySelectorAll('[data-login-mode]');
  loginMessage = document.querySelector('[data-login-message]');
  adminDashboard = document.querySelector('[data-admin-dashboard]');
  partnerDashboard = document.querySelector('[data-partner-dashboard]');
  clientDashboard = document.querySelector('[data-client-dashboard]');
  syncLoginPanelState();
  setLoginMode(activeLoginMode);
};

const setLoginExpanded = (expanded, mode = '') => {
  isLoginExpanded = expanded;
  const loginDetails = document.querySelector('[data-login-details]');
  const quickCard = document.querySelector('[data-login-quick-card]');
  const actionButtons = document.querySelectorAll('[data-login-expand-mode]');

  if (loginDetails) {
    loginDetails.hidden = !expanded;
  }
  if (quickCard) {
    quickCard.classList.toggle('is-compact', expanded);
  }
  actionButtons.forEach((button) => {
    if (!expanded) {
      button.classList.remove('is-selected');
      return;
    }
    button.classList.toggle('is-selected', mode && button.dataset.loginExpandMode === mode);
  });
};

const syncLoginPanelState = () => {
  setLoginExpanded(isLoginExpanded);
};

const bindDashboardElements = () => {
  loginForm = null;
  loginModeButtons = [];
  loginMessage = null;
  adminDashboard = document.querySelector('[data-admin-dashboard]');
  partnerDashboard = document.querySelector('[data-partner-dashboard]');
  clientDashboard = document.querySelector('[data-client-dashboard]');
};

const escapeHtml = (value) => String(value ?? '')
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#039;');

const renderHtmlAttributes = (attributes = {}) => Object.entries(attributes)
  .filter(([, value]) => value !== undefined && value !== null && value !== false)
  .map(([key, value]) => (value === true ? ` ${key}` : ` ${key}="${escapeHtml(value)}"`))
  .join('');

const renderCustomSelect = ({
  id,
  name = '',
  value = '',
  options = [],
  placeholder = 'Выберите',
  label = '',
  disabled = false,
  required = false,
  className = '',
  data = {},
  ariaLabel = '',
  size = '',
} = {}) => {
  const selectId = id || `custom-select-${name || 'field'}`;
  const triggerId = `${selectId}-trigger`;
  const menuId = `${selectId}-menu`;
  const selectedOption = options.find((option) => String(option.value) === String(value) && !option.disabled);
  const selectedLabel = selectedOption?.label || placeholder;
  const modifierClass = size ? ` custom-select--${escapeHtml(size)}` : '';
  const wrapperClass = ['custom-select', disabled ? 'custom-select--disabled' : '', className]
    .filter(Boolean)
    .join(' ');
  const dataAttributes = Object.fromEntries(
    Object.entries(data).map(([key, dataValue]) => [`data-${key.replace(/[A-Z]/g, (match) => `-${match.toLowerCase()}`)}`, dataValue]),
  );

  return `
    <div class="${escapeHtml(wrapperClass)}${modifierClass}" data-custom-select data-custom-select-name="${escapeHtml(name)}" data-custom-select-value="${escapeHtml(value)}"${required ? ' data-custom-select-required="true"' : ''}${renderHtmlAttributes(dataAttributes)}>
      ${name ? `<input type="hidden" id="${escapeHtml(selectId)}" name="${escapeHtml(name)}" value="${escapeHtml(value)}" data-custom-select-input>` : ''}
      <button
        type="button"
        id="${escapeHtml(triggerId)}"
        class="custom-select-trigger"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded="false"
        aria-controls="${escapeHtml(menuId)}"
        ${label ? `aria-labelledby="${escapeHtml(`${selectId}-label`)} ${escapeHtml(triggerId)}"` : `aria-label="${escapeHtml(ariaLabel || placeholder)}"`}
        ${disabled ? 'disabled aria-disabled="true"' : ''}
      >
        ${label ? `<span class="sr-only" id="${escapeHtml(`${selectId}-label`)}">${escapeHtml(label)}</span>` : ''}
        <span class="custom-select-value">${escapeHtml(selectedLabel)}</span>
        <span class="custom-select-arrow" aria-hidden="true"></span>
      </button>
      <div class="custom-select-menu" id="${escapeHtml(menuId)}" role="listbox" aria-labelledby="${escapeHtml(triggerId)}" data-custom-select-menu>
        ${options.map((option, index) => {
          const isSelected = String(option.value) === String(value);
          const isDisabled = Boolean(option.disabled);
          const optionClassName = [
            'custom-select-option',
            isSelected ? 'custom-select-option--selected' : '',
            isDisabled ? 'custom-select-option--disabled' : '',
          ].filter(Boolean).join(' ');
          return `<button type="button" class="${optionClassName}" role="option" aria-selected="${String(isSelected)}" data-custom-select-option data-custom-select-option-index="${index}" data-custom-select-option-value="${escapeHtml(option.value)}" ${isDisabled ? 'disabled aria-disabled="true"' : ''}>${escapeHtml(option.label)}</button>`;
        }).join('')}
      </div>
    </div>
  `;
};

const getCustomSelectParts = (select) => ({
  trigger: select?.querySelector('.custom-select-trigger'),
  value: select?.querySelector('.custom-select-value'),
  menu: select?.querySelector('.custom-select-menu'),
  input: select?.querySelector('[data-custom-select-input]'),
  options: Array.from(select?.querySelectorAll('[data-custom-select-option]') || []),
});

const getEnabledCustomSelectOptions = (select) => getCustomSelectParts(select)
  .options
  .filter((option) => !option.disabled && !option.classList.contains('custom-select-option--disabled'));

const setCustomSelectExpanded = (select, expanded) => {
  if (!select) {
    return;
  }
  const { trigger } = getCustomSelectParts(select);
  select.classList.toggle('custom-select--open', expanded);
  if (trigger) {
    trigger.setAttribute('aria-expanded', String(expanded));
  }
};

const setCustomSelectActiveOption = (select, option) => {
  const { options } = getCustomSelectParts(select);
  options.forEach((item) => item.classList.toggle('custom-select-option--active', item === option));
  option?.scrollIntoView({ block: 'nearest' });
};

const closeCustomSelect = (select) => {
  setCustomSelectExpanded(select, false);
  setCustomSelectActiveOption(select, null);
};

const closeCustomSelects = (except = null) => {
  document.querySelectorAll('[data-custom-select]').forEach((select) => {
    if (select !== except) {
      closeCustomSelect(select);
    }
  });
};

const openCustomSelect = (select) => {
  if (!select || select.classList.contains('custom-select--disabled')) {
    return;
  }
  closeCustomSelects(select);
  setCustomSelectExpanded(select, true);
  const { options } = getCustomSelectParts(select);
  const selectedOption = options.find((option) => option.getAttribute('aria-selected') === 'true');
  setCustomSelectActiveOption(select, selectedOption || getEnabledCustomSelectOptions(select)[0] || null);
};

const selectCustomSelectOption = (option) => {
  if (!option || option.disabled || option.classList.contains('custom-select-option--disabled')) {
    return;
  }
  const select = option.closest('[data-custom-select]');
  const { value: valueNode, input, options } = getCustomSelectParts(select);
  const nextValue = option.dataset.customSelectOptionValue || '';

  options.forEach((item) => {
    const isSelected = item === option;
    item.classList.toggle('custom-select-option--selected', isSelected);
    item.setAttribute('aria-selected', String(isSelected));
  });

  if (valueNode) {
    valueNode.textContent = option.textContent.trim();
  }
  if (input) {
    input.value = nextValue;
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  select.dataset.customSelectValue = nextValue;
  select.classList.remove('custom-select--invalid');
  getCustomSelectParts(select).trigger?.setAttribute('aria-invalid', 'false');
  select.dispatchEvent(new CustomEvent('custom-select:change', {
    bubbles: true,
    detail: {
      id: input?.id || '',
      name: select.dataset.customSelectName || input?.name || '',
      value: nextValue,
      input,
    },
  }));
  closeCustomSelect(select);
  getCustomSelectParts(select).trigger?.focus();
};


const validateRequiredCustomSelects = (form) => {
  const emptyRequiredSelect = Array.from(form.querySelectorAll('[data-custom-select-required="true"]'))
    .find((select) => !String(select.dataset.customSelectValue || '').trim());

  form.querySelectorAll('[data-custom-select-required="true"]').forEach((select) => {
    const isEmpty = !String(select.dataset.customSelectValue || '').trim();
    const { trigger } = getCustomSelectParts(select);
    select.classList.toggle('custom-select--invalid', isEmpty);
    if (trigger) {
      trigger.setAttribute('aria-invalid', String(isEmpty));
    }
  });

  if (!emptyRequiredSelect) {
    return true;
  }

  const fieldLabel = getCustomSelectParts(emptyRequiredSelect).trigger?.textContent?.trim() || 'обязательное поле';
  const message = `Заполните обязательное поле: ${fieldLabel}.`;
  const formType = form?.dataset?.adminForm || '';
  if (formType === 'partner' || formType === 'partnerEdit') {
    adminState.partnerFormInlineError = message;
    setFormMessage(formType, message);
    const messageNode = form.querySelector(`[data-form-message="${formType}"]`);
    if (messageNode) {
      messageNode.textContent = message;
    }
    const inlineErrorNode = form.querySelector('.admin-form-inline-error');
    if (inlineErrorNode) {
      inlineErrorNode.textContent = message;
    }
  }
  openCustomSelect(emptyRequiredSelect);
  getCustomSelectParts(emptyRequiredSelect).trigger?.focus();
  return false;
};

const moveCustomSelectActiveOption = (select, direction) => {
  const enabledOptions = getEnabledCustomSelectOptions(select);
  if (!enabledOptions.length) {
    return;
  }
  const activeOption = select.querySelector('.custom-select-option--active');
  const currentIndex = enabledOptions.indexOf(activeOption);
  const nextIndex = currentIndex === -1
    ? (direction > 0 ? 0 : enabledOptions.length - 1)
    : (currentIndex + direction + enabledOptions.length) % enabledOptions.length;
  setCustomSelectActiveOption(select, enabledOptions[nextIndex]);
};

const formatBool = (value) => (value ? 'Активен' : 'Неактивен');
const formatActiveStatus = (value) => (value ? 'Активно' : 'Неактивно');
const formatActiveStatusFeminine = (value) => (value ? 'Активна' : 'Неактивна');
const formatVerifiedStatus = (value) => (value ? 'Проверен' : 'Не проверен');

const statusBadgeMappings = {
  'активен': { label: 'Активен', tone: 'success' },
  'активно': { label: 'Активно', tone: 'success' },
  'активна': { label: 'Активна', tone: 'success' },
  'неактивен': { label: 'Неактивен', tone: 'muted' },
  'неактивно': { label: 'Неактивно', tone: 'muted' },
  'неактивна': { label: 'Неактивна', tone: 'muted' },
  'на проверке': { label: 'На проверке', tone: 'warning' },
  'проверен': { label: 'Проверен', tone: 'success' },
  'не проверен': { label: 'Не проверен', tone: 'warning' },
  'подтверждено': { label: 'Подтверждено', tone: 'success' },
  'истекло': { label: 'Истекло', tone: 'warning' },
  'отменено': { label: 'Отменено', tone: 'danger' },
  'active': { label: 'Активно', tone: 'success' },
  'confirmed': { label: 'Использовано', tone: 'success' },
  'expired': { label: 'Истекло', tone: 'warning' },
  'cancelled': { label: 'Отменено', tone: 'danger' },
  'canceled': { label: 'Отменено', tone: 'danger' },
  'pending': { label: 'Ожидает', tone: 'warning' },
  'paid': { label: 'Оплачено / на проверке', tone: 'warning' },
  'approved': { label: 'Подтверждено', tone: 'success' },
  'rejected': { label: 'Отклонено', tone: 'danger' },
  'waiting': { label: 'waiting', tone: 'warning' },
  'error': { label: 'Ошибка', tone: 'danger' },
};

const getStatusBadgeMeta = (value, tone = '') => {
  const normalized = String(value || '').trim().toLowerCase();
  if (!normalized || normalized === '—') {
    return null;
  }

  const mapped = statusBadgeMappings[normalized] || { label: value, tone: tone || 'info' };
  return {
    label: mapped.label,
    tone: tone || mapped.tone || 'info',
  };
};

const renderStatusBadge = (label, tone = '') => {
  const meta = getStatusBadgeMeta(label, tone);
  if (!meta) {
    return '—';
  }

  return `<span class="status-badge ui-badge ui-badge--${escapeHtml(meta.tone)} status-badge--${escapeHtml(meta.tone)}">${escapeHtml(meta.label)}</span>`;
};

const renderBoolStatusBadge = (value) => renderStatusBadge(formatBool(value));
const renderActiveStatusBadge = (value) => renderStatusBadge(formatActiveStatus(value));
const renderPartnerReviewStatusBadge = (value) => (value ? renderActiveStatusBadge(value) : renderStatusBadge('На проверке'));
const renderActiveStatusFeminineBadge = (value) => renderStatusBadge(formatActiveStatusFeminine(value));
const renderVerifiedStatusBadge = (value) => renderStatusBadge(formatVerifiedStatus(value));
const formatRole = (role) => ({
  client: 'Клиент',
  partner: 'Партнёр',
  admin: 'Администратор',
}[role] || role);
const formatValue = (value) => {
  if (value === null || value === undefined || value === '') return '—';
  return escapeHtml(value);
};
const hasScientificNotation = (value) => /[+-]?\d+(?:[.,]\d+)?e[+-]?\d+%?/i.test(String(value || ''));
const formatPartnerBenefit = (offer) => {
  const pricing = getOfferPricingView(offer || {});
  if (pricing.hasSaving) {
    return `Экономия ${formatMoneyLabel(pricing.savingAmount)}`;
  }
  const benefitText = String(offer?.benefit_text || offer?.discount_text || '').trim();
  const looksLikeDiscount = /%|скидк/i.test(benefitText);
  if (benefitText && !hasScientificNotation(benefitText) && !looksLikeDiscount) {
    return benefitText;
  }
  return 'Клубная привилегия';
};

const formatOfferBasePrice = (value) => {
  if (value === null || value === undefined || value === '') return 'Цена уточняется';
  const rawValue = String(value).trim();
  if (!rawValue || hasScientificNotation(rawValue)) return 'Цена уточняется';
  const normalized = Number(rawValue.replace(',', '.'));
  if (!Number.isFinite(normalized)) return rawValue;
  return `${normalized.toLocaleString('ru-RU', {
    maximumFractionDigits: 2,
  })} ₽`;
};

const formatPrice = (value) => {
  if (value === null || value === undefined || value === '') return '—';
  const rawValue = String(value).trim();
  if (!rawValue || hasScientificNotation(rawValue)) return '—';
  const normalized = Number(rawValue.replace(',', '.'));
  if (!Number.isFinite(normalized)) return '—';
  return `${normalized.toLocaleString('ru-RU', {
    maximumFractionDigits: 2,
  })} ₽`;
};


const parseMoneyValue = (value) => {
  if (value === null || value === undefined || value === '') return null;
  if (typeof value === 'object') return null;
  const rawValue = String(value).trim();
  if (!rawValue || hasScientificNotation(rawValue)) return null;
  const normalized = Number(rawValue.replace(',', '.'));
  if (!Number.isFinite(normalized)) return null;
  return normalized;
};

const formatMoneyLabel = (value) => {
  if (!Number.isFinite(value)) return '';
  return `${value.toLocaleString('ru-RU', { maximumFractionDigits: 2 })} ₽`;
};

const getOfferPricingView = (offer = {}) => {
  let basePrice = [offer.base_price, offer.regular_price, offer.price, offer.old_price]
    .map(parseMoneyValue)
    .find((value) => Number.isFinite(value));

  let memberPrice = [offer.final_price, offer.member_price, offer.club_price, offer.discounted_price, offer.price_with_discount]
    .map(parseMoneyValue)
    .find((value) => Number.isFinite(value));

  const directSavingAmount = [offer.saving_amount, offer.saving]
    .map(parseMoneyValue)
    .find((value) => Number.isFinite(value) && value > 0);

  if (!Number.isFinite(memberPrice) && Number.isFinite(basePrice) && Number.isFinite(directSavingAmount)) {
    memberPrice = Math.max(basePrice - directSavingAmount, 0);
  }

  if (!Number.isFinite(basePrice) && Number.isFinite(memberPrice) && Number.isFinite(directSavingAmount)) {
    basePrice = memberPrice + directSavingAmount;
  }

  if (!Number.isFinite(memberPrice) && Number.isFinite(basePrice)) {
    const discountPercent = parseMoneyValue(offer.discount_percent);
    if (Number.isFinite(discountPercent)) {
      memberPrice = basePrice * (1 - (discountPercent / 100));
    }
  }

  const hasBasePrice = Number.isFinite(basePrice);
  const hasMemberPrice = Number.isFinite(memberPrice);
  const calculatedSavingAmount = hasBasePrice && hasMemberPrice ? basePrice - memberPrice : null;
  const savingAmount = Number.isFinite(directSavingAmount) ? directSavingAmount : calculatedSavingAmount;
  const hasSaving = Number.isFinite(savingAmount) && savingAmount > 0;

  return {
    basePrice: hasBasePrice ? basePrice : null,
    memberPrice: hasMemberPrice ? memberPrice : null,
    savingAmount: hasSaving ? savingAmount : null,
    hasBasePrice,
    hasMemberPrice,
    hasSaving,
    basePriceLabel: hasBasePrice ? formatMoneyLabel(basePrice) : '',
    memberPriceLabel: hasMemberPrice ? formatMoneyLabel(memberPrice) : '',
    savingLabel: hasSaving ? `−${formatMoneyLabel(savingAmount)}` : '',
  };
};

const renderOfferPricingBlock = (offer, options = {}) => {
  const pricing = getOfferPricingView(offer);
  const fallbackLabel = options.fallbackLabel || 'Цена уточняется';

  if (pricing.hasBasePrice && pricing.hasMemberPrice) {
    return `
      <div class="offer-pricing">
        <div class="offer-pricing__row"><span class="offer-pricing__label">Обычная цена</span><span class="offer-pricing__value offer-pricing__value--base">${escapeHtml(pricing.basePriceLabel)}</span></div>
        <div class="offer-pricing__row"><span class="offer-pricing__label">Цена участницы</span><span class="offer-pricing__value offer-pricing__value--member">${escapeHtml(pricing.memberPriceLabel)}</span></div>
        ${pricing.hasSaving ? `<div class="offer-pricing__saving">Экономия ${escapeHtml(pricing.savingLabel.replace(/^−/, ''))}</div>` : ''}
      </div>
    `;
  }

  if (pricing.hasBasePrice) {
    return `<div class="offer-pricing"><div class="offer-pricing__fallback">Цена: ${escapeHtml(pricing.basePriceLabel)}</div></div>`;
  }

  if (pricing.hasMemberPrice) {
    return `<div class="offer-pricing"><div class="offer-pricing__fallback">Цена участницы: ${escapeHtml(pricing.memberPriceLabel)}</div></div>`;
  }

  return `<div class="offer-pricing"><div class="offer-pricing__fallback">${escapeHtml(fallbackLabel)}</div></div>`;
};

const formatPrivilegeErrorMessage = (message) => ({
  'Active subscription required': 'Для получения привилегии нужна активная подписка.',
  'Offer not found': 'Предложение сейчас недоступно.',
  'Partner not found': 'Партнёр сейчас недоступен.',
  'Verification session is not active': 'Эта привилегия уже не активна.',
  'Verification session expired': 'Срок действия кода истёк.',
  'Verification session not found': 'Код не найден для вашего кабинета.',
  'Privilege limit per partner reached for current month': 'Вы уже получили привилегию у этого партнёра в этом месяце. Новую можно будет получить в следующем месяце.',
}[String(message || '').trim()] || message || 'Не удалось выполнить действие. Попробуйте позже.');

const getOfferPhotos = (offer = {}) => {
  const photos = Array.isArray(offer.photos) ? offer.photos : [];
  const list = photos
    .filter((photo) => photo?.is_active !== false)
    .map((photo) => ({
      url: [photo?.url, photo?.photo_url, photo?.image_url].find(isSafePublicAssetUrl) || '',
      alt_text: photo?.alt_text || offer.title || 'Фото услуги',
    }))
    .filter((photo) => photo.url);
  if (!list.length && isSafePublicAssetUrl(offer.photo_url)) {
    list.push({ url: offer.photo_url, alt_text: offer.title || 'Фото услуги' });
  }
  return list;
};

const formatPrivilegeStatus = (status) => getStatusBadgeMeta(status)?.label || 'Активно';

const renderOfferMarketplaceCard = (offer = {}, options = {}) => {
  const offerPhotos = getOfferPhotos(offer);
  const imageUrl = offerPhotos[0]?.url || (isSafePublicAssetUrl(offer.image_url) ? offer.image_url : '');
  const rawTitle = String(offer.title || '').trim();
  const rawDescription = String(offer.description || '').trim();
  const rawConditions = String(offer.conditions || offer.terms || '').trim();
  const allowFallbacks = options.showFallbackPlaceholders !== false;
  const title = rawTitle || (allowFallbacks ? 'Название предложения' : '');
  const description = rawDescription || (allowFallbacks ? 'Короткое описание услуги.' : '');
  const conditions = rawConditions || (allowFallbacks ? 'Условия появятся здесь.' : '');
  const benefit = formatPartnerBenefit(offer);
  const basePrice = formatOfferBasePrice(offer.base_price);
  const ctaText = options.cta || 'Получить привилегию';
  const note = options.note || 'Preview для клиента';
  const actionHtml = options.actionHtml || `<button type="button" disabled>${escapeHtml(ctaText)}</button>`;
  const isPartnerCabinetCard = options.layout === 'partner-cabinet';

  return `
    <article class="offer-marketplace-card ${options.compact ? 'offer-marketplace-card--compact' : ''} ${isPartnerCabinetCard ? 'partner-offer-card partner-offer-card--partner-cabinet' : ''}" ${isPartnerCabinetCard ? 'data-layout="partner-cabinet"' : ''}>
      ${imageUrl
        ? `<div class="offer-marketplace-image partner-media ${isPartnerCabinetCard ? 'partner-offer-card__media' : ''}" role="img" aria-label="${escapeHtml(title)}"><div class="partner-media__bg" style="background-image: url('${escapeHtml(imageUrl)}')"></div><img class="partner-media__img" src="${escapeHtml(imageUrl)}" alt="${escapeHtml(title)}" loading="lazy"></div>`
        : `<div class="offer-marketplace-image offer-card-placeholder partner-media partner-media--placeholder ${isPartnerCabinetCard ? 'partner-offer-card__media' : ''}" aria-label="Фото услуги"><span>Фото услуги</span></div>`}
      <div class="offer-marketplace-body ${isPartnerCabinetCard ? 'partner-offer-card__body' : ''}">
        <div class="offer-marketplace-heading ${isPartnerCabinetCard ? 'partner-offer-card__header' : ''}">
          <span class="offer-marketplace-benefit">${escapeHtml(benefit)}</span>
          ${offer.is_active === undefined ? '' : renderActiveStatusBadge(offer.is_active)}
        </div>
        ${title ? `<h4 class="card-title">${escapeHtml(title)}</h4>` : ''}
        ${description ? `<p class="card-description compact-copy ${isPartnerCabinetCard ? 'partner-offer-card__description' : ''}">${escapeHtml(description)}</p>` : ''}
        <dl class="offer-marketplace-meta ${isPartnerCabinetCard ? 'partner-offer-card__details' : ''}">
          ${conditions ? `<div><dt>Условия</dt><dd>${escapeHtml(conditions)}</dd></div>` : ''}
          <div><dd>${renderOfferPricingBlock(offer)}</dd></div>
        </dl>
        <div class="${isPartnerCabinetCard ? 'partner-offer-card__actions' : 'offer-marketplace-preview offer-marketplace-preview__actions'}">
          ${isPartnerCabinetCard ? '' : `<span class="helper-text">${escapeHtml(note)}</span>`}
          ${actionHtml}
        </div>
      </div>
    </article>
  `;
};

const renderDisplayValue = (value) => String(value || '').startsWith('<span class="status-badge') ? value : formatValue(value);
const formatDate = (value) => (value ? new Date(value).toLocaleString('ru-RU') : '—');
const formatDateTime = (value) => {
  if (value === null || value === undefined || value === '') return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';

  const pad = (part) => String(part).padStart(2, '0');
  return `${pad(date.getDate())}.${pad(date.getMonth() + 1)}.${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
};
const formatDateRu = (value) => {
  if (!value) return '—';
  const [year, month, day] = String(value).split('-');
  if (!year || !month || !day) return formatDate(value);
  return `${day}.${month}.${year}`;
};

const activityEventMeta = {
  privilege_created: { label: 'Привилегия', icon: '♡', tone: 'privilege' },
  privilege_confirmed: { label: 'Подтверждение', icon: '✓', tone: 'confirmed' },
  privilege_expired: { label: 'Истекло', icon: '⌛', tone: 'expired' },
  qr_clicked: { label: 'QR-переход', icon: 'QR', tone: 'qr' },
  partner_created: { label: 'Партнёр', icon: '✦', tone: 'partner' },
  offer_created: { label: 'Предложение', icon: '%', tone: 'privilege' },
  qr_link_created: { label: 'QR-ссылка', icon: '⌁', tone: 'qr' },
  payment_request_created: { label: 'Оплата', icon: '₽', tone: 'partner' },
  payment_approved: { label: 'Оплата подтверждена', icon: '✓', tone: 'confirmed' },
  subscription_activated: { label: 'Подписка', icon: '★', tone: 'privilege' },
};

const activityEventFilters = [
  { value: '', label: 'Все события' },
  { value: 'privilege_created', label: 'Привилегии' },
  { value: 'privilege_confirmed', label: 'Подтверждения' },
  { value: 'privilege_expired', label: 'Истекшие' },
  { value: 'qr_clicked', label: 'QR-переходы' },
  { value: 'partner_created', label: 'Партнёры' },
  { value: 'offer_created', label: 'Предложения' },
  { value: 'qr_link_created', label: 'QR-ссылки' },
];

const formatActivityDate = (value) => formatDate(value);

const getActivityEventMeta = (eventType) => activityEventMeta[eventType] || {
  label: 'Событие',
  icon: '•',
  tone: 'privilege',
};

const renderActivityItem = (item = {}) => {
  const eventMeta = getActivityEventMeta(item.event_type);
  const metaItems = [
    item.partner_name ? `Партнёр: ${item.partner_name}` : '',
    item.offer_title ? `Предложение: ${item.offer_title}` : '',
    item.qr_slug ? `QR: ${item.qr_slug}` : '',
  ].filter(Boolean);

  return `
    <article class="activity-item">
      <span class="activity-badge activity-badge--${escapeHtml(eventMeta.tone)}" title="${escapeHtml(eventMeta.label)}" aria-label="${escapeHtml(eventMeta.label)}">${escapeHtml(eventMeta.icon)}</span>
      <div class="activity-item__body">
        <div class="activity-item__heading">
          <div>
            <h4>${formatValue(item.title || eventMeta.label)}</h4>
            <p>${formatValue(item.description || 'Подробности события появятся здесь.')}</p>
          </div>
          <time datetime="${escapeHtml(item.occurred_at || '')}">${escapeHtml(formatActivityDate(item.occurred_at))}</time>
        </div>
        ${(metaItems.length || item.status) ? `
          <div class="activity-meta">
            ${metaItems.map((meta) => `<span>${escapeHtml(meta)}</span>`).join('')}
            ${item.status ? renderStatusBadge(formatStatus(item.status)) : ''}
          </div>
        ` : ''}
      </div>
    </article>
  `;
};

const renderActivityFeed = (items = [], options = {}) => {
  if (options.loading) {
    return '<div class="activity-empty" role="status">Загружаем события…</div>';
  }

  if (options.error) {
    return '<div class="activity-empty activity-empty--error" role="alert">Не удалось загрузить события.</div>';
  }

  if (!Array.isArray(items) || !items.length) {
    return '<div class="activity-empty">Событий пока нет.</div>';
  }

  return `<div class="activity-feed">${items.map(renderActivityItem).join('')}</div>`;
};

const statusLabels = {
  active: 'Активно',
  confirmed: 'Использовано',
  expired: 'Истекло',
  cancelled: 'Отменено',
  canceled: 'Отменено',
  paused: 'Приостановлено',
  pending: 'Ожидает',
  paid: 'Оплачено / на проверке',
  approved: 'Подтверждено',
  rejected: 'Отклонено',
};

const formatStatus = (status) => {
  const normalized = String(status || '').trim().toLowerCase();
  if (!normalized) return '—';
  return statusLabels[normalized] || status;
};

const getClientCityOptions = () => {
  const stateCities = Array.isArray(adminState.cities) && adminState.cities.length
    ? adminState.cities.filter((city) => city.is_active !== false)
    : [];
  const baseCities = stateCities.length ? stateCities : fallbackClientCities;
  const profile = clientState.profile || {};
  const hasSelectedCity = profile.selected_city_id
    && !baseCities.some((city) => String(city.id) === String(profile.selected_city_id));

  return [
    ...baseCities,
    ...(hasSelectedCity ? [{ id: profile.selected_city_id, slug: '', name: profile.selected_city_name || 'Выбранный город' }] : []),
  ];
};

const getClientCategoryOptions = () => {
  const fromPartners = new Map();
  (Array.isArray(clientState.partners) ? clientState.partners : []).forEach((partner) => {
    getPartnerCategories(partner).forEach((category) => {
      const key = category.slug || category.name.toLowerCase();
      if (!key) return;
      if (!fromPartners.has(key)) fromPartners.set(key, { slug: category.slug || '', title: category.name, name: category.name, sort_order: Number.MAX_SAFE_INTEGER });
    });
  });
  const stateCategories = Array.isArray(adminState.categories) && adminState.categories.length ? adminState.categories.filter((category) => category.is_active !== false) : [];
  const base = stateCategories.length ? stateCategories : fallbackClientCategories;
  base.forEach((category) => fromPartners.set(category.slug || category.name.toLowerCase(), { ...category, title: category.title || category.name }));
  return Array.from(fromPartners.values()).sort((a, b) => Number(a.sort_order ?? Number.MAX_SAFE_INTEGER) - Number(b.sort_order ?? Number.MAX_SAFE_INTEGER) || String(a.name || a.title || '').localeCompare(String(b.name || b.title || ''), 'ru') || String(a.slug || '').localeCompare(String(b.slug || '')));
};

const formatClientCategory = (slug) => {
  const category = getClientCategoryOptions().find((item) => item.slug === slug);
  return category?.title || slug || '—';
};

const normalizeCategoryName = (value) => String(value || '').trim();

const getPartnerCategories = (partner = {}) => {
  const result = [];
  const seen = new Set();
  const addCategory = (item = {}) => {
    const name = normalizeCategoryName(item.name || item.title || item.slug);
    const slug = normalizeCategoryName(item.slug);
    const id = Number.isFinite(Number(item.id)) ? Number(item.id) : undefined;
    if (!name) return;
    if (name === '[object Object]' || slug === '[object Object]') return;
    const key = `${slug.toLowerCase()}::${name.toLowerCase()}`;
    if (seen.has(key)) return;
    seen.add(key);
    result.push({ ...(id ? { id } : {}), name, ...(slug ? { slug } : {}) });
  };
  const categories = Array.isArray(partner.categories) ? partner.categories : [];
  categories.forEach((category) => {
    if (!category) return;
    if (typeof category === 'string') {
      addCategory({ name: category });
      return;
    }
    if (typeof category === 'object') addCategory(category);
  });
  if (!result.length && Array.isArray(partner.category_slugs)) {
    partner.category_slugs.forEach((slug) => addCategory({ slug, name: formatClientCategory(slug) }));
  }
  if (!result.length) {
    [partner.category, partner.category_name, partner.category_slug, partner.type, partner.service_category]
      .forEach((fallback) => addCategory(typeof fallback === 'string' ? { name: fallback, slug: fallback } : {}));
  }
  return result;
};


const getPartnerCategoryIdStrings = (partner = {}, activeCategories = []) => getPartnerCategories(partner)
  .map((item) => {
    if (item.id) return String(item.id);
    const match = activeCategories.find((category) => category.slug === item.slug);
    return match ? String(match.id) : '';
  })
  .filter(Boolean);

const getAdminPartnerDraftKey = (partnerId) => (partnerId ? String(partnerId) : '__new__');

const getAdminPartnerSelectedCategoryIds = (partner = null, activeCategories = []) => {
  const draftKey = getAdminPartnerDraftKey(partner?.id || adminState.selectedPartnerIdForEdit || '');
  const draftCategoryIds = adminState.partnerFormCategoryIds[draftKey];
  if (Array.isArray(draftCategoryIds)) {
    return new Set(draftCategoryIds.map(String));
  }
  return new Set(partner ? getPartnerCategoryIdStrings(partner, activeCategories) : []);
};

const captureAdminPartnerCategoryDraft = (form) => {
  if (!form) return [];
  const draftKey = getAdminPartnerDraftKey(form.dataset.partnerId || '');
  const selectedIds = Array.from(form.querySelectorAll('input[name="category_ids"]:checked'))
    .map((input) => String(input.value || '').trim())
    .filter(Boolean);
  adminState.partnerFormCategoryIds[draftKey] = selectedIds;
  return selectedIds;
};

const resetAdminPartnerCategoryDraft = (partnerId = '') => {
  delete adminState.partnerFormCategoryIds[getAdminPartnerDraftKey(partnerId)];
};

const formatPartnerCategory = (partner) => getPartnerCategories(partner).map((item) => item.name).join(', ') || '—';
const partnerMatchesLandingCategory = (partner, categorySlug) => {
  const normalizedCategorySlug = String(categorySlug || '').trim().toLowerCase();
  if (!normalizedCategorySlug) return true;
  const categories = Array.isArray(partner?.categories) ? partner.categories : [];
  if (categories.some((category) => String(category?.slug || category).trim().toLowerCase() === normalizedCategorySlug)) {
    return true;
  }
  return getPartnerCategories(partner).some((category) => String(category.slug || '').trim().toLowerCase() === normalizedCategorySlug);
};


const renderEmptyState = (title, text, icon = '♡') => `
  <article class="client-empty-state ui-empty-state">
    <span class="client-empty-state__icon" aria-hidden="true">${escapeHtml(icon)}</span>
    <h4 class="ui-card__title">${escapeHtml(title)}</h4>
    <p class="ui-card__meta">${escapeHtml(text)}</p>
  </article>
`;


const analyticsCardDefinitions = [
  ['qr_links_count', 'QR-ссылки', 'count'],
  ['lead_clicks_count', 'Переходы по QR', 'count'],
  ['privileges_created_count', 'Получено привилегий', 'count'],
  ['privileges_confirmed_count', 'Подтверждено', 'count'],
  ['active_privileges_count', 'Активные привилегии', 'count'],
  ['expired_privileges_count', 'Истекшие привилегии', 'count'],
  ['conversion_to_privilege_percent', 'Конверсия в привилегию', 'percent'],
  ['confirmation_rate_percent', 'Процент подтверждения', 'percent'],
];

const formatAnalyticsCount = (value) => {
  const numberValue = Number(value || 0);
  return Number.isFinite(numberValue) ? String(numberValue) : '0';
};

const formatAnalyticsPercent = (value) => {
  const numberValue = Number(value || 0);
  if (!Number.isFinite(numberValue)) return '0%';
  const rounded = Math.round(numberValue * 10) / 10;
  return `${Number.isInteger(rounded) ? rounded.toFixed(0) : rounded.toFixed(1)}%`;
};

const isAnalyticsEmpty = (analytics = {}) => analyticsCardDefinitions.every(([key]) => Number(analytics?.[key] || 0) === 0);

const renderAnalyticsCards = (analytics = {}) => `
  <div class="analytics-grid">
    ${analyticsCardDefinitions.map(([key, label, type]) => `
      <article class="analytics-card">
        <strong class="analytics-value">${escapeHtml(type === 'percent' ? formatAnalyticsPercent(analytics?.[key]) : formatAnalyticsCount(analytics?.[key]))}</strong>
        <span class="analytics-label">${escapeHtml(label)}</span>
      </article>
    `).join('')}
  </div>
`;

const renderAnalyticsSection = (analytics, options = {}) => {
  const title = options.title || 'Аналитика';
  const loading = options.loading || false;
  const error = options.error || '';

  if (loading) {
    return `
      <section class="analytics-panel" aria-live="polite">
        <div class="admin-section-heading"><h4>${escapeHtml(title)}</h4><p class="analytics-hint">Аналитика помогает понять, сколько клиентов пришли из клуба и сколько привилегий реально использовали.</p></div>
        <p class="analytics-hint">Загружаем аналитику…</p>
      </section>
    `;
  }

  if (error) {
    return `
      <section class="analytics-panel" aria-live="polite">
        <div class="admin-section-heading"><h4>${escapeHtml(title)}</h4><p class="analytics-hint">Аналитика помогает понять, сколько клиентов пришли из клуба и сколько привилегий реально использовали.</p></div>
        <p class="analytics-empty">${escapeHtml(error)}</p>
      </section>
    `;
  }

  if (!analytics) {
    return `
      <section class="analytics-panel" aria-live="polite">
        <div class="admin-section-heading"><h4>${escapeHtml(title)}</h4><p class="analytics-hint">Аналитика помогает понять, сколько клиентов пришли из клуба и сколько привилегий реально использовали.</p></div>
        <p class="analytics-empty">Выберите партнёра, чтобы увидеть аналитику.</p>
      </section>
    `;
  }

  return `
    <section class="analytics-panel" aria-live="polite">
      <div class="admin-section-heading"><h4>${escapeHtml(title)}</h4><p class="analytics-hint">Аналитика помогает понять, сколько клиентов пришли из клуба и сколько привилегий реально использовали.</p></div>
      ${renderAnalyticsCards(analytics)}
      ${isAnalyticsEmpty(analytics) ? '<p class="analytics-empty">Данных пока нет. Разместите QR-код и добавьте предложения, чтобы начать получать статистику.</p>' : ''}
    </section>
  `;
};

const renderClientEmptyState = (title, text) => renderEmptyState(title, text);
const renderPartnerEmptyState = (title, text) => renderEmptyState(title, text, '✦');

const getToken = () => localStorage.getItem(authTokenKey);
const getPartnerToken = () => localStorage.getItem(partnerTokenKey);
const getClientToken = () => localStorage.getItem(clientTokenKey);

const setLoginMessage = (message = '') => {
  if (loginMessage) {
    loginMessage.textContent = message;
  }
};

const setFormMessage = (formType, message = '') => {
  adminState.formMessages[formType] = message;
};

const setPanelMessage = (message = '', type = 'info') => {
  adminState.panelMessage = message
    ? `<div class="admin-status admin-status--${type}" role="status">${escapeHtml(message)}</div>`
    : '';
};

const clearToken = () => {
  localStorage.removeItem(authTokenKey);
};

const clearPartnerToken = () => {
  localStorage.removeItem(partnerTokenKey);
};

const clearClientToken = () => {
  localStorage.removeItem(clientTokenKey);
};

const setLoginMode = (mode) => {
  activeLoginMode = mode;
  loginModeButtons.forEach((button) => {
    const isActive = button.dataset.loginMode === mode;
    button.classList.toggle('is-active', isActive);
    button.setAttribute('aria-selected', String(isActive));
  });
};

const getRoleUser = (role) => {
  if (role === 'admin') return adminState.user;
  if (role === 'partner') return partnerState.user;
  return clientState.user;
};

const getRoleTitle = (role) => ({
  admin: 'Панель администратора',
  partner: 'Кабинет партнёра',
  client: 'Личный кабинет',
}[role]);

const getRoleTabs = (role) => ({
  admin: adminTabs,
  partner: partnerTabs,
  client: clientTabs,
}[role]);

const getActiveTab = (role) => ({
  admin: adminState.activeTab,
  partner: partnerState.activeTab,
  client: clientState.activeTab,
}[role]);

const getDashboardDataAttr = (role) => ({
  admin: 'data-admin-dashboard',
  partner: 'data-partner-dashboard',
  client: 'data-client-dashboard',
}[role]);

const getTabDataAttr = (role) => ({
  admin: 'data-admin-tab',
  partner: 'data-partner-tab',
  client: 'data-client-tab',
}[role]);

const getLogoutAttr = (role) => ({
  admin: 'data-logout-button',
  partner: 'data-partner-logout-button',
  client: 'data-client-logout-button',
}[role]);

const getRoleCaption = (role) => ({
  admin: 'Управление клубом, партнёрами и подтверждениями',
  partner: 'Рабочее место партнёра клуба',
  client: 'Персональный аккаунт с привилегиями',
}[role]);

const renderDashboardNavigation = (role, tabs, activeTab, tabAttr) => {
  if (role !== 'admin') {
    return tabs.map((tab) => `
      <button class="dashboard-nav-button${activeTab === tab.id ? ' is-active' : ''}" type="button" ${tabAttr}="${tab.id}">
        <span>${tab.label}</span>
      </button>
    `).join('');
  }

  const groups = tabs.reduce((result, tab) => {
    const group = tab.group || 'Разделы';
    if (!result.has(group)) result.set(group, []);
    result.get(group).push(tab);
    return result;
  }, new Map());

  return `
    <div class="dashboard-primary-actions">
      <button class="ui-button ui-button--primary" type="button" data-admin-global-partner-create>Добавить партнёра</button>
      <button class="ui-button ui-button--secondary" type="button" data-admin-global-giveaway-create>Создать розыгрыш</button>
    </div>
    ${Array.from(groups.entries()).map(([group, items]) => `
      <section class="dashboard-nav-group" aria-label="${escapeHtml(group)}">
        <p class="dashboard-nav-group__title">${escapeHtml(group)}</p>
        ${items.map((tab) => `
          <button class="dashboard-nav-button${activeTab === tab.id ? ' is-active' : ''}" type="button" ${tabAttr}="${tab.id}">
            <span>${tab.label}</span>
          </button>
        `).join('')}
      </section>
    `).join('')}
  `;
};

const renderDashboardApp = (role) => {
  const user = getRoleUser(role) || {};
  const roleTitle = getRoleTitle(role);
  const roleCaption = getRoleCaption(role);
  const contact = user.email || user.phone || 'пользователь клуба';
  const dashboardAttr = getDashboardDataAttr(role);
  const tabAttr = getTabDataAttr(role);
  const logoutAttr = getLogoutAttr(role);
  const activeTab = getActiveTab(role);

  document.body.classList.add('is-dashboard');
  document.body.classList.remove('is-editorial-landing');
  root.innerHTML = `
    <div class="dashboard-shell" data-dashboard-role="${role}">
      ${renderCabinetAmbientLayer()}
      <header class="dashboard-topbar">
        <div class="dashboard-brand" aria-label="Женский клуб">
          <span class="brand-mark" aria-hidden="true">
            <img class="brand-mark__image" src="${clubAvatarSrc}" alt="" loading="lazy" onerror="this.hidden=true;this.nextElementSibling.hidden=false;" />
            <span class="brand-mark__fallback" hidden>ЖК</span>
          </span>
          <span>
            <span class="brand-name">Женский клуб</span>
            <span class="brand-caption">Федеральный клуб привилегий для девушек</span>
          </span>
        </div>
        <div class="dashboard-title-block">
          <p class="section-kicker">Кабинет клуба</p>
          <h1>${roleTitle}</h1>
          <p class="dashboard-role-caption">${roleCaption}</p>
        </div>
        <div class="dashboard-user-block">
          <span>${escapeHtml(contact)}</span>
          <button type="button" ${logoutAttr}>Выйти</button>
        </div>
      </header>
      <div class="dashboard-layout">
        <aside class="dashboard-sidebar" aria-label="Разделы кабинета">
          <div class="dashboard-sidebar-heading">
            <span>Навигация</span>
            <strong>${roleTitle}</strong>
          </div>
          <nav class="dashboard-nav" aria-label="Меню кабинета">
            ${renderDashboardNavigation(role, getRoleTabs(role), activeTab, tabAttr)}
          </nav>
        </aside>
        <main class="dashboard-main">
          <div class="admin-dashboard ${role}-dashboard" ${dashboardAttr}></div>
        </main>
      </div>
    </div>
    <div class="ui-toast" data-ui-toast role="status" aria-live="polite"></div>
  `;
  bindDashboardElements();
};

const showLoginForm = () => {
  adminState.user = null;
  partnerState.user = null;
  clientState.user = null;
  renderPublicApp();
  applyClientLoginPrefill();
  setLoginMessage();
};

const buildErrorMessage = async (response) => {
  try {
    const data = await response.json();
    if (typeof data.detail === 'string') {
      return data.detail;
    }
    if (Array.isArray(data.detail)) {
      return 'Проверьте заполнение полей и повторите попытку.';
    }
  } catch (error) {
    // response body is not JSON
  }
  return `Ошибка ${response.status}`;
};

const getLandingDirectionBySlug = (slug) => categoryDirections.find((category) => category.slug === slug) || null;

const isSafePublicAssetUrl = (value) => {
  const url = String(value || '').trim();
  return (url.startsWith('/assets/') || url.startsWith('/uploads/')) && !/[\s'"()]/.test(url);
};

const getActivePartnerGalleryPhotos = (photos = []) => (Array.isArray(photos) ? photos : [])
  .filter((photo) => photo?.is_active !== false && isSafePublicAssetUrl(photo?.url))
  .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0) || Number(left.id || 0) - Number(right.id || 0));

const renderLandingPartnerImage = (partner, activePhotoIndex = 0) => {
  const photos = getPartnerGalleryImages(partner || {});
  if (photos.length) {
    const safePhotoIndex = Math.min(Math.max(Number(activePhotoIndex || 0), 0), photos.length - 1);
    const currentPhoto = photos[safePhotoIndex];
    return `
      <div class="landing-partner-cover landing-partner-gallery" aria-label="Галерея партнёра">
        <div class="landing-partner-gallery-main">
          <span class="landing-partner-gallery-backdrop" style="background-image: url('${escapeHtml(currentPhoto.url)}')" aria-hidden="true"></span>
          <img class="landing-partner-gallery-image" src="${escapeHtml(currentPhoto.url)}" alt="${escapeHtml(currentPhoto.alt_text || partner?.name || 'Фото партнёра')}" loading="lazy" />
          ${photos.length > 1 ? '<button class=\"landing-gallery-nav landing-gallery-nav--prev\" type=\"button\" data-landing-photo-prev aria-label=\"Предыдущее фото\">←</button>' : ''}
          ${photos.length > 1 ? '<button class=\"landing-gallery-nav landing-gallery-nav--next\" type=\"button\" data-landing-photo-next aria-label=\"Следующее фото\">→</button>' : ''}
          <span class=\"landing-gallery-counter\">Фото ${safePhotoIndex + 1} / ${photos.length}</span>
        </div>
        ${photos.length > 1 ? `<div class="landing-partner-gallery-thumbs">${photos.slice(0, 6).map((photo, index) => `<button type="button" class="landing-partner-gallery-thumb ${index === safePhotoIndex ? 'landing-partner-gallery-thumb--active' : ''}" data-landing-photo-index="${escapeHtml(index)}" aria-label="Показать фото ${escapeHtml(index + 1)}"><img src="${escapeHtml(photo.url)}" alt="" loading="lazy" /></button>`).join('')}</div>` : ''}
      </div>
    `;
  }
  const coverUrl = isSafePublicAssetUrl(partner?.cover_url) ? partner.cover_url : '';
  if (!coverUrl) {
    return '<div class="landing-partner-cover landing-partner-cover--placeholder" aria-hidden="true">♡</div>';
  }
  return `<div class="landing-partner-cover landing-partner-gallery-main"><span class="landing-partner-gallery-backdrop" style="background-image: url('${escapeHtml(coverUrl)}')" aria-hidden="true"></span><img class="landing-partner-gallery-image" src="${escapeHtml(coverUrl)}" alt="${escapeHtml(partner?.name || 'Фото партнёра')}" loading="lazy" /></div>`;
};

const renderSafePartnerImagePreview = (url, kind, label) => {
  const safeUrl = isSafePublicAssetUrl(url) ? url : '';
  const modifier = kind === 'cover' ? 'partner-image-preview--cover' : 'partner-image-preview--logo';
  return safeUrl
    ? `<div class="partner-image-preview ${modifier}" style="background-image: url('${escapeHtml(safeUrl)}')" role="img" aria-label="${escapeHtml(label)}"></div>`
    : `<div class="partner-image-preview ${modifier} partner-image-preview--placeholder" aria-label="${escapeHtml(label)}">${kind === 'cover' ? 'Обложка' : 'Лого'}</div>`;
};


const getPartnerUploadStatus = (key) => partnerState.uploadStatuses[key] || { state: '', message: '' };

const setPartnerUploadStatus = (key, state = '', message = '') => {
  if (!key) return;
  if (!state && !message) {
    delete partnerState.uploadStatuses[key];
    return;
  }
  partnerState.uploadStatuses[key] = { state, message };
};

const isPartnerUploadLoading = (key) => getPartnerUploadStatus(key).state === 'loading';

const renderPartnerUploadStatus = (key) => {
  const status = getPartnerUploadStatus(key);
  const stateClass = status.state ? ` partner-upload-status--${escapeHtml(status.state)}` : '';
  return `<p class="helper-text form-message partner-upload-status${stateClass}" data-partner-upload-status="${escapeHtml(key)}">${escapeHtml(status.message || '')}</p>`;
};

const getSafeUploadErrorMessage = (error, fallback = 'Не удалось загрузить изображение') => {
  console.error('Partner image upload failed', {
    name: error?.name || 'Error',
  });
  return fallback;
};

const renderPartnerUploadButton = ({ label, trigger, inputAttr, inputSelector, statusKey, kind = '', disabled = false, disabledMessage = '' }) => {
  const isLoading = isPartnerUploadLoading(statusKey);
  const buttonClass = `admin-inline-action admin-action-button partner-upload-button${isLoading ? ' partner-upload-button--loading' : ''}`;
  const disabledAttr = disabled || isLoading ? ' disabled' : '';
  const inputMarkup = inputAttr
    ? `<input type="file" accept="image/jpeg,image/png,image/webp" ${inputAttr} />`
    : '';
  return `
    <button class="${buttonClass}" type="button" data-partner-upload-trigger="${escapeHtml(trigger)}"${kind ? ` data-partner-upload-kind="${escapeHtml(kind)}"` : ''}${inputSelector ? ` data-partner-upload-input="${escapeHtml(inputSelector)}"` : ''}${disabled && disabledMessage ? ` data-partner-upload-disabled-message="${escapeHtml(disabledMessage)}"` : ''}${disabledAttr}>${isLoading ? 'Загружаем изображение…' : escapeHtml(label)}</button>
    ${inputMarkup}
  `;
};

const renderSafeOfferImagePreview = (url, label = 'Фото предложения') => {
  const safeUrl = isSafePublicAssetUrl(url) ? url : '';
  return safeUrl
    ? `<div class="offer-image-preview" style="background-image: url('${escapeHtml(safeUrl)}')" role="img" aria-label="${escapeHtml(label)}"></div>`
    : `<div class="offer-image-preview offer-image-preview--placeholder" aria-label="${escapeHtml(label)}">Фото услуги</div>`;
};

const renderOfferImageUploader = (offer, scope) => {
  const isAdmin = scope === 'admin';
  const offerId = offer?.id;
  const messageKey = isAdmin ? 'offerImage' : 'offerImage';
  const message = isAdmin ? (adminState.formMessages[messageKey] || '') : (partnerState.formMessages[messageKey] || '');
  const statusKey = offerId ? `offerImage:${offerId}` : 'offerImage:new';
  const inputAttr = isAdmin
    ? `data-admin-offer-image-upload data-offer-id="${escapeHtml(offerId || '')}"`
    : `data-partner-offer-image-upload data-partner-upload-kind="offer" data-offer-id="${escapeHtml(offerId || '')}"`;
  return `
    <section class="offer-image-uploader">
      <div class="admin-section-heading text-stack"><h4 class="section-title">Фото предложения</h4><p class="helper-text compact-copy">JPG, PNG или WEBP до 5 МБ.</p></div>
      ${renderSafeOfferImagePreview(offer?.image_url, 'Фото предложения')}
      <div class="offer-image-upload-actions">
        ${isAdmin
          ? (offerId
            ? `<label class="admin-inline-action ui-button ui-button--secondary">Загрузить фото предложения<input type="file" accept="image/jpeg,image/png,image/webp" ${inputAttr} /></label>`
            : '<p class="helper-text form-message compact-copy">Сначала сохраните предложение, затем загрузите фото.</p>')
          : renderPartnerUploadButton({
            label: 'Загрузить фото предложения',
            trigger: 'offer-image',
            inputAttr: offerId ? inputAttr : '',
            inputSelector: offerId ? '[data-partner-offer-image-upload]' : '',
            statusKey,
            kind: 'offer',
            disabled: !offerId,
            disabledMessage: 'Сначала сохраните предложение, затем загрузите фото',
          })}
      </div>
      ${!isAdmin && offer?.id && offer?.image_url ? `<button class="admin-inline-action ui-button ui-button--danger admin-inline-action--danger" type="button" data-partner-offer-image-clear="${escapeHtml(offer.id)}">Удалить фото услуги</button>` : ''}
      <p class="helper-text compact-copy">Рекомендуемый формат: горизонтальное фото 16:9 или 4:3. Важные элементы размещайте ближе к центру.</p>
      ${!isAdmin && !offerId ? '<p class="helper-text form-message compact-copy">Сначала сохраните предложение, затем загрузите фото</p>' : ''}
      ${isAdmin ? `<p class="form-message offer-image-status" data-form-message="${messageKey}">${escapeHtml(message)}</p>` : renderPartnerUploadStatus(statusKey)}
      ${!isAdmin ? `<p class="form-message offer-image-status" data-partner-form-message="${messageKey}">${escapeHtml(message)}</p>` : ''}
    </section>
  `;
};

const renderPartnerImageUploader = (partner, scope) => {
  const isAdmin = scope === 'admin';
  const logoInputAttr = isAdmin
    ? `data-admin-partner-image-upload="logo" data-partner-id="${escapeHtml(partner.id)}"`
    : 'data-partner-image-upload="logo" data-partner-upload-kind="logo"';
  const coverInputAttr = isAdmin
    ? `data-admin-partner-image-upload="cover" data-partner-id="${escapeHtml(partner.id)}"`
    : 'data-partner-image-upload="cover" data-partner-upload-kind="cover"';
  return `
    <section class="partner-image-uploader">
      <div class="admin-section-heading text-stack"><h4 class="section-title">${isAdmin ? 'Изображения партнёра' : 'Фотографии профиля'}</h4><p class="helper-text compact-copy">JPG, PNG или WEBP до 5 МБ.</p></div>
      <div class="partner-image-grid">
        <article>
          <span>Логотип</span>
          ${renderSafePartnerImagePreview(partner.logo_url, 'logo', 'Логотип партнёра')}
          <div class="partner-upload-actions">
            ${isAdmin
              ? `<label class="admin-inline-action ui-button ui-button--secondary">Загрузить логотип<input type="file" accept="image/jpeg,image/png,image/webp" ${logoInputAttr} /></label>`
              : `${renderPartnerUploadButton({ label: partner.logo_url ? 'Заменить логотип' : 'Загрузить логотип', trigger: 'profile-image', inputAttr: logoInputAttr, inputSelector: '[data-partner-image-upload="logo"]', statusKey: 'profileImages:logo', kind: 'logo' })}${partner.logo_url ? '<button class="admin-inline-action ui-button ui-button--danger admin-inline-action--danger" type="button" data-partner-image-clear="logo">Удалить логотип</button>' : ''}`}
          </div>
          <p class="helper-text compact-copy">Рекомендуемый формат: квадратное фото 1:1.</p>
          ${!isAdmin ? renderPartnerUploadStatus('profileImages:logo') : ''}
        </article>
        <article>
          <span>Обложка</span>
          ${renderSafePartnerImagePreview(partner.cover_url, 'cover', 'Обложка партнёра')}
          <div class="partner-upload-actions">
            ${isAdmin
              ? `<label class="admin-inline-action ui-button ui-button--secondary">Загрузить обложку<input type="file" accept="image/jpeg,image/png,image/webp" ${coverInputAttr} /></label>`
              : `${renderPartnerUploadButton({ label: partner.cover_url ? 'Заменить обложку' : 'Загрузить обложку', trigger: 'profile-image', inputAttr: coverInputAttr, inputSelector: '[data-partner-image-upload="cover"]', statusKey: 'profileImages:cover', kind: 'cover' })}${partner.cover_url ? '<button class="admin-inline-action ui-button ui-button--danger admin-inline-action--danger" type="button" data-partner-image-clear="cover">Удалить обложку</button>' : ''}`}
          </div>
          <p class="helper-text compact-copy">Рекомендуемый формат: горизонтальное фото 16:9 или 4:3. Важные элементы размещайте ближе к центру.</p>
          ${!isAdmin ? renderPartnerUploadStatus('profileImages:cover') : ''}
        </article>
      </div>
      <p class="helper-text form-message upload-status" data-${isAdmin ? 'form-message="partnerImage"' : 'partner-form-message="profileImages"'}>${escapeHtml(isAdmin ? (adminState.formMessages.partnerImage || '') : (partnerState.formMessages.profileImages || ''))}</p>
    </section>
  `;
};

const renderPartnerGallery = (partner, photos = [], scope = 'partner') => {
  const isAdmin = scope === 'admin';
  const partnerId = partner?.id || '';
  const messageKey = isAdmin ? 'partnerGallery' : 'partnerGallery';
  const message = isAdmin ? (adminState.formMessages[messageKey] || '') : (partnerState.formMessages[messageKey] || '');
  const uploadAttr = isAdmin
    ? `data-admin-partner-photo-upload data-partner-id="${escapeHtml(partnerId)}"`
    : 'data-partner-photo-upload data-partner-gallery-upload data-partner-upload-kind="gallery"';
  const visiblePhotos = Array.isArray(photos) ? photos : [];
  return `
    <section class="partner-gallery">
      <div class="admin-section-heading text-stack">
        <h4 class="section-title">Фото карточки партнёра</h4>
        <span class="sr-only">Галерея партнёра</span>
        <p class="section-description compact-copy">Эти фотографии клиент видит в карточке партнёра и в общей галерее. Фото для клиентской витрины. Публикация после проверки.</p>
      </div>
      <div class="partner-gallery-upload partner-gallery-upload-card">
        <h5>Добавить фото</h5>
        ${partnerId ? (isAdmin
          ? `<label class="admin-inline-action ui-button ui-button--secondary">Загрузить фото в галерею<input type="file" accept="image/jpeg,image/png,image/webp" ${uploadAttr} /></label>`
          : renderPartnerUploadButton({ label: 'Загрузить фото в галерею', trigger: 'gallery-photo', inputAttr: uploadAttr, inputSelector: '[data-partner-gallery-upload]', statusKey: 'partnerGallery', kind: 'gallery' })) : '<p class="form-message">Сначала сохраните партнёра, затем загрузите фото.</p>'}
        <p class="helper-text compact-copy">Поддерживаются JPG, PNG, WebP. Лучше использовать вертикальные или квадратные фото хорошего качества.</p>
      </div>
      ${!isAdmin ? renderPartnerUploadStatus('partnerGallery') : ''}
      ${visiblePhotos.length ? `
        <div class="partner-gallery-grid">
          ${visiblePhotos.map((photo) => {
            const safeUrl = isSafePublicAssetUrl(photo.url) ? photo.url : '';
            return `
              <article class="partner-gallery-item partner-gallery-card ${photo.is_active ? '' : 'is-muted'}">
                ${safeUrl ? `<div class="partner-gallery-media" role="img" aria-label="${escapeHtml(photo.alt_text || 'Фото партнёра')}"><div class="partner-gallery-media__bg" style="background-image: url('${escapeHtml(safeUrl)}')"></div><img class="partner-gallery-media__img" src="${escapeHtml(safeUrl)}" alt="${escapeHtml(photo.alt_text || 'Фото партнёра')}" loading="lazy"></div>` : '<div class="partner-gallery-media partner-gallery-empty">Фото скрыто</div>'}
                <form class="partner-gallery-actions ui-card-actions ui-action-row ui-action-row--stack-mobile" data-${isAdmin ? 'admin' : 'partner'}-gallery-form="photo" data-photo-id="${escapeHtml(photo.id)}">
                  <div class="partner-gallery-row"><span class="status-badge ${photo.is_active ? 'status-badge--success' : 'status-badge--warning'}">${photo.is_active ? 'Показывается' : 'Скрыто'}</span></div>
                  <label class="partner-gallery-order">Порядок<input name="sort_order" type="number" value="${escapeHtml(photo.sort_order || 0)}" /></label>
                  <input name="is_active" type="hidden" value="${photo.is_active ? 'true' : 'false'}" />
                  <div class="admin-form-actions">
                    <button class="admin-inline-action ui-button ui-button--primary admin-inline-action--primary" type="submit"${isAdmin ? legacyContentDisabledAttr() : ''}>Сохранить</button>
                    <button class="admin-inline-action ui-button ui-button--secondary admin-inline-action--secondary" type="button" data-${isAdmin ? 'admin' : 'partner'}-photo-hide="${escapeHtml(photo.id)}">${photo.is_active ? 'Скрыть фото' : 'Показать фото'}</button>
                    ${!isAdmin ? `<button class="admin-inline-action ui-button ui-button--danger admin-inline-action--danger" type="button" data-partner-photo-delete="${escapeHtml(photo.id)}">Удалить</button>` : ''}
                  </div>
                </form>
              </article>
            `;
          }).join('')}
        </div>
      ` : '<div class="partner-gallery-empty partner-empty-state compact-copy"><strong>Фото пока не добавлены.</strong><span>Загрузите первое фото, чтобы клиенты увидели ваши работы.</span><small>Добавьте 3–5 фото для доверия.</small></div>'}
      <p class="helper-text form-message" data-${isAdmin ? 'form-message' : 'partner-form-message'}="${messageKey}">${escapeHtml(message)}</p>
    </section>
  `;
};


const getPartnerPrimaryOffer = (partner, options = {}) => {
  if (options.primaryOffer) {
    return options.primaryOffer;
  }
  if (Array.isArray(options.offers) && options.offers.length) {
    return options.offers[0];
  }
  if (Array.isArray(partner?.offers) && partner.offers.length) {
    return partner.offers[0];
  }
  if (partner?.primary_offer || partner?.benefit_text || partner?.discount_text) {
    return {
      title: partner.primary_offer || 'Главная привилегия',
      benefit_text: partner.benefit_text || partner.discount_text,
      description: partner.offer_description,
    };
  }
  return null;
};

const getPartnerMarketplaceCompleteness = (partner, options = {}) => {
  const primaryOffer = getPartnerPrimaryOffer(partner, options);
  const contactFilled = Boolean(String(partner?.phone || partner?.website_url || partner?.social_url || '').trim());
  const items = [
    ['Обложка', isSafePublicAssetUrl(partner?.cover_url), 'Нет обложки'],
    ['Логотип', isSafePublicAssetUrl(partner?.logo_url), 'Нет логотипа'],
    ['Описание', Boolean(String(partner?.description || '').trim()), 'Нет описания'],
    ['Адрес', Boolean(String(partner?.address || '').trim()), 'Нет адреса'],
    ['График', Boolean(String(partner?.working_hours || '').trim()), 'Нет графика работы'],
    ['Контакты', contactFilled, 'Нет контактов'],
    ['Предложения', Boolean(primaryOffer), 'Нет предложений'],
  ];
  const filled = items.filter(([, value]) => value).length;
  const total = items.length;
  return {
    items,
    filled,
    total,
    percent: total ? Math.round((filled / total) * 100) : 0,
    recommendations: items.filter(([, value]) => !value).map(([, , recommendation]) => recommendation),
  };
};

const renderPartnerProfileHints = (partner, options = {}) => {
  const completeness = getPartnerMarketplaceCompleteness(partner, options);
  const missingItems = completeness.recommendations.length ? completeness.recommendations : ['Все ключевые элементы заполнены'];
  return `
    <section class="partner-profile-hints partner-progress-card">
      <div>
        <span class="section-eyebrow section-kicker">Заполненность профиля</span>
        <h4>Профиль заполнен на ${escapeHtml(completeness.percent)}%</h4>
      </div>
      <div class="partner-progress-track" aria-hidden="true"><span style="width: ${escapeHtml(completeness.percent)}%"></span></div>
      <p class="helper-text form-message">Заполните ключевые поля — это помогает решиться на визит.</p>
      <ul class="partner-missing-list">
        ${missingItems.map((item) => `
          <li class="${completeness.recommendations.length ? '' : 'is-complete'}">
            <span>${completeness.recommendations.length ? '＋' : '✓'}</span>
            ${escapeHtml(item)}
          </li>
        `).join('')}
      </ul>
    </section>
  `;
};

const getPartnerOnboardingSteps = (partner = {}, options = {}) => {
  const contactFilled = Boolean(String(partner.phone || partner.website_url || partner.social_url || '').trim());
  return [
    {
      title: 'Основная информация',
      isComplete: Boolean(
        String(partner.description || '').trim()
        && String(partner.address || '').trim()
        && contactFilled
        && String(partner.working_hours || '').trim()
      ),
      action: 'Заполнить профиль',
      tab: 'contacts',
    },
    {
      title: 'Фото и обложка',
      isComplete: Boolean(String(partner.logo_url || '').trim() && String(partner.cover_url || '').trim()),
      action: 'Загрузить изображения',
      tab: 'media',
    },
    {
      title: 'Предложения',
      isComplete: Array.isArray(options.offers) && options.offers.length > 0,
      action: 'Добавить услугу',
      tab: 'services',
    },
    {
      title: 'Публикация и проверка',
      isComplete: Boolean(partner.is_active) && Boolean(partner.is_verified),
      action: 'Проверить статус',
      tab: 'overview',
    },
  ];
};

const renderPartnerOnboardingChecklist = (partner, options = {}) => {
  const steps = getPartnerOnboardingSteps(partner, options);
  const completedCount = steps.filter((step) => step.isComplete).length;
  const isReady = completedCount === steps.length;
  const readinessPercent = steps.length ? Math.round((completedCount / steps.length) * 100) : 0;

  return `
    <section class="partner-onboarding" aria-labelledby="partner-onboarding-title">
      <div class="partner-onboarding-header">
        <div>
          <span class="section-eyebrow section-kicker">Onboarding</span>
          <h4 class="section-title" id="partner-onboarding-title">Настройте витрину за 4 шага</h4>
          <p class="section-description compact-copy">Заполните главное для понятной витрины.</p>
        </div>
        <div class="partner-onboarding-progress" aria-live="polite">
          <strong>Готовность витрины: ${escapeHtml(readinessPercent)}% (${escapeHtml(completedCount)} из ${escapeHtml(steps.length)} шагов)</strong>
          ${isReady ? '<span>Витрина готова к публикации</span>' : '<span>Продолжайте настройку витрины</span>'}
          <div class="partner-onboarding-progressbar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${escapeHtml(readinessPercent)}"><span style="width: ${escapeHtml(readinessPercent)}%"></span></div>
        </div>
      </div>
      <div class="partner-onboarding-steps">
        ${steps.map((step, index) => `
          <article class="partner-onboarding-step ${step.isComplete ? 'partner-onboarding-step--done' : 'partner-onboarding-step--todo'}">
            <div>
              <span class="partner-onboarding-step-number">${escapeHtml(index + 1)}</span>
              <h5>${escapeHtml(step.title)}</h5>
            </div>
            <p class="helper-text">${step.isComplete ? '✅ Готово' : 'Нужно заполнить'}</p>
            ${step.isComplete ? '' : `<button class="partner-onboarding-action" type="button" data-partner-onboarding-tab="${escapeHtml(step.tab)}">${escapeHtml(step.action)}</button>`}
          </article>
        `).join('')}
      </div>
    </section>
  `;
};

const renderPartnerMarketplaceCard = (partner = {}, options = {}) => {
  const galleryPhotos = getActivePartnerGalleryPhotos(options.photos || partner.photos);
  const coverUrl = galleryPhotos[0]?.url || (isSafePublicAssetUrl(partner.cover_url) ? partner.cover_url : '');
  const logoUrl = isSafePublicAssetUrl(partner.logo_url) ? partner.logo_url : '';
  const primaryOffer = getPartnerPrimaryOffer(partner, options);
  const cityAddress = [partner.city_name || partner.city, partner.address].filter(Boolean).join(' · ');
  const socialValue = String(partner.social_url || '').trim();
  const siteValue = String(partner.website_url || '').trim();
  const socialLabel = socialValue ? (socialValue.includes('t.me') || socialValue.includes('telegram') ? 'Telegram' : 'Открыть соцсеть') : '';
  const contactItems = [
    ['Телефон', partner.phone],
    ['Соцсеть', socialValue ? `<a href="${escapeHtml(socialValue)}" target="_blank" rel="noopener noreferrer">${escapeHtml(socialLabel || socialValue)}</a>` : ''],
    ['Сайт', siteValue ? `<a href="${escapeHtml(siteValue)}" target="_blank" rel="noopener noreferrer">Открыть сайт</a>` : ''],
  ].filter(([, value]) => String(value || '').trim());

  return `
    <article class="partner-marketplace-card partner-profile-preview-card">
      <div class="partner-marketplace-cover partner-profile-preview__media partner-media ${coverUrl ? '' : 'partner-marketplace-cover--placeholder partner-media--placeholder'}" ${coverUrl ? `role="img" aria-label="${escapeHtml(partner.name || 'Фото партнёра')}"` : 'aria-label="Фото партнёра"'}>
        ${coverUrl ? `<div class="partner-media__bg partner-profile-preview__media-bg" style="background-image: url('${escapeHtml(coverUrl)}')"></div><img class="partner-media__img partner-profile-preview__media-img" src="${escapeHtml(coverUrl)}" alt="${escapeHtml(partner.name || 'Фото партнёра')}" loading="lazy" onerror="this.closest('.partner-profile-preview__media')?.classList.add('partner-media--placeholder');this.remove();">` : '<span>Фото партнёра</span>'}
      </div>
      <div class="partner-marketplace-body partner-profile-preview__body">
        <div class="partner-marketplace-heading partner-profile-preview__identity">
          <div class="partner-marketplace-logo ${logoUrl ? '' : 'partner-marketplace-logo--placeholder'}" ${logoUrl ? `style="background-image: url('${escapeHtml(logoUrl)}')"` : ''} aria-hidden="true">${logoUrl ? '' : '♡'}</div>
          <div>
            <h3>${escapeHtml(partner.name || 'Название партнёра')}</h3>
            <div class="partner-marketplace-category">${categories.length ? categories.map((category) => `<span class="category-chip">${escapeHtml(category.name)}</span>`).join('') : '<span class="category-chip">—</span>'}</div>
            <div class="partner-marketplace-badges">
              ${partner.is_verified === undefined ? '' : renderVerifiedStatusBadge(partner.is_verified)}
            </div>
          </div>
        </div>
        <p class="partner-marketplace-description">${escapeHtml(partner.description || 'Коротко расскажите, чем вы полезны участницам клуба и какую атмосферу получит клиент.')}</p>
        <dl class="partner-marketplace-meta partner-profile-preview__info-grid">
          <div><dt>Город и адрес</dt><dd>${cityAddress ? escapeHtml(cityAddress) : 'Адрес появится в карточке'}</dd></div>
          <div><dt>График работы</dt><dd>${escapeHtml(partner.working_hours || 'График работы появится после заполнения')}</dd></div>
          ${contactItems.map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd>${value}</dd></div>`).join('')}
        </dl>
        <div class="partner-marketplace-offer">
          <span>Главная выгода</span>
          <strong>${escapeHtml(primaryOffer ? formatPartnerBenefit(primaryOffer) : 'Добавьте предложение')}</strong>
          <small class="card-description">${escapeHtml(primaryOffer?.title || primaryOffer?.description || 'Коротко о привилегии.')}</small>
        </div>
      </div>
    </article>
  `;
};

const renderLandingPartnerCard = (partner, activePhotoIndex = 0) => {
  const offers = Array.isArray(partner?.offers) ? partner.offers : [];
  const firstOffer = offers[0] || null;
  const logoUrl = isSafePublicAssetUrl(partner?.logo_url) ? partner.logo_url : '';
  return `
    <article class="landing-partner-card">
      ${renderLandingPartnerImage(partner, activePhotoIndex)}
      <div class="landing-partner-card-body">
        <div class="landing-partner-card-heading">
          ${logoUrl ? `<span class="landing-partner-logo" style="background-image: url('${escapeHtml(logoUrl)}')" aria-hidden="true"></span>` : '<span class="landing-partner-logo landing-partner-logo--placeholder" aria-hidden="true">ЖК</span>'}
          <div>
            <p class="section-kicker">${escapeHtml(partner?.city_name || 'Город клуба')}</p>
            <h3>${escapeHtml(partner?.name || 'Партнёр клуба')}</h3>
          </div>
        </div>
        <p>${escapeHtml(partner?.address || 'Адрес появится в карточке партнёра')}</p>
        ${firstOffer ? `
          <div class="landing-partner-offer">
            <strong>${escapeHtml(formatPartnerBenefit(firstOffer))}</strong>
            <span>${escapeHtml(firstOffer.title)}</span>
            <p>${escapeHtml(firstOffer.description || 'Подробности привилегии уточняйте у партнёра.')}</p>
            ${firstOffer.terms ? `<small>${escapeHtml(firstOffer.terms)}</small>` : ''}
          </div>
        ` : '<div class="landing-partner-offer"><strong>Привилегия скоро появится</strong><p>Партнёр готовит специальное предложение для участниц клуба.</p></div>'}
      </div>
    </article>
  `;
};

const renderLandingPartnerModal = () => {
  const modal = document.querySelector('[data-landing-partner-modal]');
  if (!modal) {
    return;
  }

  if (!landingPartnerModalState.isOpen || !landingPartnerModalState.selectedLandingDirection) {
    modal.hidden = true;
    modal.innerHTML = '';
    return;
  }

  const { selectedLandingDirection, partners, selectedPartnerIndex, activePhotoIndex, loading, error } = landingPartnerModalState;
  const hasPartners = partners.length > 0;
  const safePartnerIndex = hasPartners ? Math.min(selectedPartnerIndex, partners.length - 1) : 0;
  landingPartnerModalState.selectedPartnerIndex = safePartnerIndex;
  const selectedPartner = hasPartners ? partners[safePartnerIndex] : null;
  const selectedPartnerPhotos = selectedPartner ? getPartnerGalleryImages(selectedPartner) : [];
  const safePhotoIndex = selectedPartnerPhotos.length ? Math.min(Math.max(activePhotoIndex, 0), selectedPartnerPhotos.length - 1) : 0;
  landingPartnerModalState.activePhotoIndex = safePhotoIndex;

  modal.hidden = false;
  modal.innerHTML = `
    <div class="landing-partner-panel" role="dialog" aria-modal="false" aria-labelledby="landing-partner-modal-title">
      <div class="landing-partner-panel-header">
        <div>
          <p class="section-kicker">Партнёры клуба</p>
          <h2 id="landing-partner-modal-title">${escapeHtml(selectedLandingDirection.title)}</h2>
        </div>
        <button class="landing-partner-close" type="button" data-landing-partner-close>Закрыть</button>
      </div>
      <div class="landing-partner-carousel">
        ${loading ? '<p class="landing-partner-status">Загружаем партнёров направления…</p>' : ''}
        ${error ? `<p class="landing-partner-status">${escapeHtml(error)}</p>` : ''}
        ${!loading && !error && hasPartners ? renderLandingPartnerCard(selectedPartner, safePhotoIndex) : ''}
        ${!loading && !error && !hasPartners ? '<p class="landing-partner-empty">Партнёры этого направления скоро появятся.</p>' : ''}
      </div>
      <div class="landing-partner-panel-actions">
        <div class="landing-partner-switcher">
          <button class="landing-carousel-button" type="button" data-landing-carousel-prev ${partners.length > 1 ? '' : 'disabled'}>←</button>
          <span>Партнёр ${hasPartners ? safePartnerIndex + 1 : 0} / ${hasPartners ? partners.length : 0}</span>
          <button class="landing-carousel-button" type="button" data-landing-carousel-next ${partners.length > 1 ? '' : 'disabled'}>→</button>
        </div>
        <a class="primary-button" href="https://app.bloomclub.ru/" data-landing-modal-cta>${hasPartners ? 'Получить привилегию' : 'Вступить в клуб'}</a>
      </div>
    </div>
  `;
};

const openLandingDirection = async (slug) => {
  const direction = getLandingDirectionBySlug(slug);
  if (!direction) {
    return;
  }

  landingPartnerModalState.isOpen = true;
  landingPartnerModalState.selectedLandingDirection = direction;
  landingPartnerModalState.selectedPartnerIndex = 0;
  landingPartnerModalState.activePhotoIndex = 0;
  landingPartnerModalState.error = '';
  landingPartnerModalState.partners = landingPartnerModalState.cache[slug] || [];
  landingPartnerModalState.loading = !landingPartnerModalState.cache[slug];
  renderLandingPartnerModal();

  if (landingPartnerModalState.cache[slug]) {
    return;
  }

  try {
    const response = await fetch(`/api/v1/public/landing/partners?category_slug=${encodeURIComponent(slug)}&limit=12`);
    if (!response.ok) {
      throw new Error(await buildErrorMessage(response));
    }
    const data = await response.json();
    const partners = Array.isArray(data.items) ? data.items : [];
    landingPartnerModalState.cache[slug] = partners.filter((partner) => partnerMatchesLandingCategory(partner, slug));
    landingPartnerModalState.partners = landingPartnerModalState.cache[slug];
  } catch (error) {
    landingPartnerModalState.error = 'Не удалось загрузить партнёров. Попробуйте позже.';
  } finally {
    landingPartnerModalState.loading = false;
    renderLandingPartnerModal();
  }
};

const closeLandingPartnerModal = () => {
  landingPartnerModalState.isOpen = false;
  landingPartnerModalState.selectedLandingDirection = null;
  landingPartnerModalState.partners = [];
  landingPartnerModalState.selectedPartnerIndex = 0;
  landingPartnerModalState.activePhotoIndex = 0;
  landingPartnerModalState.loading = false;
  landingPartnerModalState.error = '';
  renderLandingPartnerModal();
};

const moveLandingPhotoCarousel = (step) => {
  const partner = landingPartnerModalState.partners[landingPartnerModalState.selectedPartnerIndex];
  const total = partner ? getPartnerGalleryImages(partner).length : 0;
  if (total < 2) {
    return;
  }
  landingPartnerModalState.activePhotoIndex = (landingPartnerModalState.activePhotoIndex + step + total) % total;
  renderLandingPartnerModal();
};

const moveLandingPartnerCarousel = (step) => {
  const total = landingPartnerModalState.partners.length;
  if (total < 2) {
    return;
  }
  landingPartnerModalState.selectedPartnerIndex = (landingPartnerModalState.selectedPartnerIndex + step + total) % total;
  landingPartnerModalState.activePhotoIndex = 0;
  renderLandingPartnerModal();
};

const selectLandingModalPartner = (index) => {
  const total = landingPartnerModalState.partners.length;
  if (!total) return;
  landingPartnerModalState.selectedPartnerIndex = Math.min(Math.max(index, 0), total - 1);
  landingPartnerModalState.activePhotoIndex = 0;
  renderLandingPartnerModal();
};

const selectLandingModalPhoto = (index) => {
  const partner = landingPartnerModalState.partners[landingPartnerModalState.selectedPartnerIndex];
  const total = partner ? getPartnerGalleryImages(partner).length : 0;
  if (!total) return;
  landingPartnerModalState.activePhotoIndex = Math.min(Math.max(index, 0), total - 1);
  renderLandingPartnerModal();
};

const apiFetchResponse = async (path, options = {}) => {
  const { timeoutMs: timeoutOption, ...fetchOptions } = options;
  const token = getToken();
  const headers = new Headers(fetchOptions.headers || {});
  const timeoutMs = Number(timeoutOption ?? 30000);
  const timeoutController = !fetchOptions.signal && timeoutMs > 0 ? new AbortController() : null;
  const timeoutId = timeoutController
    ? setTimeout(() => timeoutController.abort(), timeoutMs)
    : null;

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (fetchOptions.body && !(fetchOptions.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let response;
  try {
    response = await fetch(path, {
      cache: fetchOptions.cache || 'no-store',
      ...fetchOptions,
      signal: fetchOptions.signal || timeoutController?.signal,
      headers,
    });
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new Error('Сервер не ответил вовремя. Проверьте соединение и повторите попытку.');
    }
    throw error;
  } finally {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  }

  if (response.status === 401 || response.status === 403) {
    clearToken();
    showLoginForm();
    throw new Error('Сессия истекла. Войдите снова.');
  }

  if (!response.ok) {
    throw new Error(await buildErrorMessage(response));
  }

  return response;
};

const apiFetch = async (path, options = {}) => {
  const response = await apiFetchResponse(path, options);

  if (response.status === 204) {
    return null;
  }

  return response.json();
};


const setPartnerPanelMessage = (message = '', type = 'info') => {
  const toastNode = document.querySelector('[data-ui-toast]');
  if (!message) {
    if (toastState.timeoutId) {
      clearTimeout(toastState.timeoutId);
      toastState.timeoutId = null;
    }
    if (toastNode) {
      toastNode.classList.remove('is-visible');
      toastNode.textContent = '';
    }
    return;
  }
  if (!toastNode) {
    return;
  }
  toastNode.className = `ui-toast ui-toast--${type} is-visible`;
  toastNode.textContent = message;
  if (toastState.timeoutId) {
    clearTimeout(toastState.timeoutId);
  }
  toastState.timeoutId = setTimeout(() => {
    toastNode.classList.remove('is-visible');
    toastNode.textContent = '';
  }, 2500);
};

const setPartnerFormMessage = (formType, message = '') => {
  partnerState.formMessages[formType] = message;
};

const partnerApiFetch = async (path, options = {}) => {
  const token = getPartnerToken();
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (fetchOptions.body && !(fetchOptions.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });

  if (response.status === 401 || response.status === 403) {
    clearPartnerToken();
    showLoginForm();
    setLoginMode('partner');
    throw new Error('Сессия партнёра истекла. Войдите снова.');
  }

  if (!response.ok) {
    throw new Error(await buildErrorMessage(response));
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
};

const partnerPatchJson = (path, payload) => partnerApiFetch(path, {
  method: 'PATCH',
  body: JSON.stringify(payload),
});

const partnerPostJson = (path, payload = {}) => partnerApiFetch(path, {
  method: 'POST',
  body: JSON.stringify(payload),
});

const setClientPanelMessage = (message = '', type = 'info') => {
  clientState.panelMessage = message
    ? `<div class="admin-status admin-status--${type}" role="status">${escapeHtml(message)}</div>`
    : '';
};

const setClientFormMessage = (formType, message = '') => {
  clientState.formMessages[formType] = message;
};

const clientApiFetch = async (path, options = {}) => {
  const token = getClientToken();
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });

  if (response.status === 401 || response.status === 403) {
    clearClientToken();
    showLoginForm();
    setLoginMode('client');
    throw new Error('Сессия клиента истекла. Войдите снова.');
  }

  if (!response.ok) {
    throw new Error(await buildErrorMessage(response));
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
};

const clientPatchJson = (path, payload) => clientApiFetch(path, {
  method: 'PATCH',
  body: JSON.stringify(payload),
});

const clientPostJson = (path, payload = {}) => clientApiFetch(path, {
  method: 'POST',
  body: JSON.stringify(payload),
});

const requestPartnerUserMe = () => partnerApiFetch('/api/v1/auth/user-me');
const mergePartnerProfilePreservingFilledFields = (currentProfile, incomingProfile) => {
  const base = { ...(currentProfile || {}) };
  const incoming = incomingProfile || {};
  Object.entries(incoming).forEach(([key, value]) => {
    if (value !== null && value !== undefined) {
      base[key] = value;
    }
  });
  return base;
};

const loadPartnerProfile = async () => {
  const profile = await partnerApiFetch('/api/v1/partners/me');
  partnerState.profile = mergePartnerProfilePreservingFilledFields(partnerState.profile, profile);
};
const loadPartnerPhotos = async () => { partnerState.photos = await partnerApiFetch('/api/v1/partners/me/photos'); };
const loadPartnerOffers = async () => {
  partnerState.offers = await partnerApiFetch('/api/v1/partners/me/offers');
  if (partnerState.selectedOfferIdForEdit && !partnerState.offers.some((offer) => String(offer.id) === String(partnerState.selectedOfferIdForEdit))) {
    partnerState.selectedOfferIdForEdit = '';
  }
  if (partnerState.selectedOfferIdForGallery && !partnerState.offers.some((offer) => String(offer.id) === String(partnerState.selectedOfferIdForGallery))) {
    partnerState.selectedOfferIdForGallery = '';
  }
  if (!partnerState.selectedOfferIdForGallery && partnerState.offers.length) {
    partnerState.selectedOfferIdForGallery = String(partnerState.offers[0].id);
  }
};
const loadPartnerOfferPhotos = async (offerId) => {
  if (!offerId) return [];
  const photos = await partnerApiFetch(`/api/v1/partners/me/offers/${offerId}/photos`);
  partnerState.offerPhotosByOfferId[String(offerId)] = Array.isArray(photos) ? photos : [];
  return partnerState.offerPhotosByOfferId[String(offerId)];
};
const loadPartnerQrLinks = async () => { partnerState.qrLinks = await partnerApiFetch('/api/v1/partners/me/qr-links'); };
const loadPartnerLeads = async () => { partnerState.leads = await partnerApiFetch('/api/v1/partners/me/leads'); };
const loadPartnerVerifications = async () => { partnerState.verifications = await partnerApiFetch('/api/v1/partners/me/verifications'); };
const loadPartnerActivity = async () => {
  partnerState.activityLoading = true;
  partnerState.activityError = '';
  try {
    const data = await partnerApiFetch('/api/v1/partners/me/activity');
    partnerState.activityItems = Array.isArray(data?.items) ? data.items : [];
  } catch (error) {
    if (!getPartnerToken()) throw error;
    partnerState.activityError = error.message || 'Не удалось загрузить события.';
  } finally {
    partnerState.activityLoading = false;
  }
};
const loadPartnerAnalytics = async () => {
  partnerState.analyticsLoading = true;
  partnerState.analyticsError = '';
  try {
    partnerState.analytics = await partnerApiFetch('/api/v1/partners/me/analytics');
  } catch (error) {
    partnerState.analyticsError = error.message || 'Не удалось загрузить аналитику.';
  } finally {
    partnerState.analyticsLoading = false;
  }
};

const requestClientUserMe = () => clientApiFetch('/api/v1/auth/user-me');
const loadClientProfile = async () => { clientState.profile = await clientApiFetch('/api/v1/clients/me'); };
const loadClientSubscription = async () => { clientState.subscription = await clientApiFetch('/api/v1/clients/me/subscription'); };
const loadClientVerifications = async () => { clientState.verifications = await clientApiFetch('/api/v1/clients/me/verifications'); };
const loadClientActivity = async () => {
  clientState.activityLoading = true;
  clientState.activityError = '';
  try {
    const data = await clientApiFetch('/api/v1/clients/me/activity');
    clientState.activityItems = Array.isArray(data?.items) ? data.items : [];
  } catch (error) {
    if (!getClientToken()) throw error;
    clientState.activityError = error.message || 'Не удалось загрузить события.';
  } finally {
    clientState.activityLoading = false;
  }
};
const buildClientSavingsPath = ({ fromDate = '', toDate = '' } = {}) => {
  const params = new URLSearchParams();
  if (fromDate) params.set('from_date', fromDate);
  if (toDate) params.set('to_date', toDate);
  const query = params.toString();
  return `/api/v1/clients/me/savings${query ? `?${query}` : ''}`;
};

const loadClientSavings = async ({ fromDate = '', toDate = '' } = {}) => {
  clientState.savingsLoading = true;
  clientState.savingsError = '';
  try {
    clientState.savings = await clientApiFetch(buildClientSavingsPath({ fromDate, toDate }));
  } catch (error) {
    if (!getClientToken()) throw error;
    clientState.savingsError = error.message || 'Не удалось загрузить экономию.';
  } finally {
    clientState.savingsLoading = false;
  }
};

const buildClientCatalogPath = () => {
  const params = new URLSearchParams();
  const { q, category_slug: categorySlug, city_slug: citySlug } = clientState.catalogFilters;
  if (q) params.set('q', q);
  if (categorySlug) params.set('category_slug', categorySlug);
  if (citySlug && citySlug !== '__all__') params.set('city_slug', citySlug);
  if (!citySlug && clientState.profile?.selected_city_id) {
    params.set('city_id', clientState.profile.selected_city_id);
  }
  const query = params.toString();
  return `/api/v1/clients/catalog/partners${query ? `?${query}` : ''}`;
};

const loadClientCatalog = async () => {
  if (!clientState.profile) {
    await loadClientProfile();
  }
  clientState.partners = await clientApiFetch(buildClientCatalogPath());
  clientState.catalogLoaded = true;
  if (clientState.selectedPartnerId && !clientState.partners.some((partner) => String(partner.id) === clientState.selectedPartnerId)) {
    clientState.selectedPartner = null;
    clientState.selectedPartnerId = '';
  }
};

const loadClientPartnerDetail = async (partnerId) => {
  clientState.selectedPartner = await clientApiFetch(`/api/v1/clients/partners/${partnerId}`);
  clientState.selectedPartnerId = String(partnerId);
};

const loadClientPartnerOffers = async (partnerId) => {
  clientState.offersByPartner[partnerId] = await clientApiFetch(`/api/v1/clients/partners/${partnerId}/offers`);
};

const resetClientPartnerModalState = () => {
  clientState.selectedPartnerModalId = '';
  clientState.selectedPartnerModalPartner = null;
  clientState.selectedPartnerModalOffers = [];
  clientState.partnerModalGalleryIndex = 0;
  clientState.partnerModalOfferGalleryId = '';
  clientState.partnerModalOfferGalleryIndex = 0;
  clientState.partnerModalLoading = false;
  clientState.partnerModalError = '';
  document.body.classList.remove('client-partner-modal-open');
};

const syncClientPartnerModalScrollLock = () => {
  document.body.classList.toggle('client-partner-modal-open', Boolean(clientState.selectedPartnerModalId));
};

const openClientPartnerModal = async (partnerId) => {
  const normalizedPartnerId = String(partnerId || '');
  if (!normalizedPartnerId) return;

  const catalogPartner = clientState.partners.find((partner) => String(partner.id) === normalizedPartnerId) || null;
  clientState.selectedPartnerModalId = normalizedPartnerId;
  clientState.selectedPartnerModalPartner = catalogPartner;
  clientState.selectedPartnerModalOffers = clientState.offersByPartner[normalizedPartnerId] || [];
  clientState.partnerModalGalleryIndex = 0;
  clientState.partnerModalOfferGalleryId = '';
  clientState.partnerModalOfferGalleryIndex = 0;
  clientState.partnerModalLoading = true;
  clientState.partnerModalError = '';
  renderClientLayout();

  try {
    const [partnerDetail, offers] = await Promise.all([
      clientApiFetch(`/api/v1/clients/partners/${normalizedPartnerId}`),
      clientState.offersByPartner[normalizedPartnerId]
        ? Promise.resolve(clientState.offersByPartner[normalizedPartnerId])
        : clientApiFetch(`/api/v1/clients/partners/${normalizedPartnerId}/offers`),
    ]);
    clientState.selectedPartnerModalPartner = partnerDetail || catalogPartner;
    clientState.selectedPartnerModalOffers = Array.isArray(offers) ? offers : [];
    clientState.offersByPartner[normalizedPartnerId] = clientState.selectedPartnerModalOffers;
  } catch (error) {
    clientState.partnerModalError = error.message || 'Не удалось загрузить витрину партнёра.';
  } finally {
    clientState.partnerModalLoading = false;
    renderClientLayout();
  }
};

const openClientPartnerMarketplace = async (partnerId) => {
  await Promise.all([loadClientPartnerDetail(partnerId), loadClientPartnerOffers(partnerId)]);
};

const renderClientLayout = () => {
  renderDashboardApp('client');
  const profileHome = clientState.activeTab === 'profile'
    ? `<div class="client-profile-home-only">${renderClientHome()}${renderClientOnboarding()}</div>`
    : '';
  clientDashboard.innerHTML = `
    ${clientState.panelMessage}
    ${profileHome}
    <section class="admin-tab-panel">${renderClientTabContent()}</section>
    ${renderClientPartnerModal()}
  `;
  syncClientPartnerModalScrollLock();
};

const getClientVerificationStats = () => {
  const verifications = Array.isArray(clientState.verifications) ? clientState.verifications : [];
  const active = verifications.filter((item) => String(item.status || '').toLowerCase() === 'active');
  const confirmed = verifications.filter((item) => String(item.status || '').toLowerCase() === 'confirmed' || item.confirmed_at);

  return { active, confirmed, verifications };
};

const getClientSelectedCityName = () => {
  const profile = clientState.profile || {};
  if (profile.selected_city_name || profile.city) {
    return profile.selected_city_name || profile.city;
  }

  const selectedCity = getClientCityOptions().find((city) => String(city.id) === String(profile.selected_city_id || ''));
  return selectedCity?.name || 'Город не выбран';
};

const getClientActiveVerification = () => {
  const { active } = getClientVerificationStats();
  return active[0] || null;
};

const isClientSubscriptionActive = () => {
  const subscription = clientState.subscription || {};
  const status = String(subscription.status || '').toLowerCase();
  return status === 'active' || status === 'paid' || status === 'approved';
};

const isClientProfileCompleted = () => {
  const profile = clientState.profile || {};
  return Boolean(String(profile.full_name || '').trim() && String(profile.phone || '').trim() && String(profile.email || '').trim());
};

const renderClientActivityPreview = () => {
  const items = Array.isArray(clientState.activityItems) ? clientState.activityItems.slice(0, 3) : [];
  if (clientState.activityLoading) {
    return '<div class="activity-empty" role="status">Загружаем последние события клуба…</div>';
  }
  if (clientState.activityError) {
    return '<div class="activity-empty activity-empty--error" role="alert">Не удалось загрузить события. Откройте вкладку «Активность» чуть позже.</div>';
  }
  if (!items.length) {
    return `
      <div class="activity-empty activity-empty--friendly" role="status">
        <strong>Пока тихо, но клуб уже готов</strong>
        <p>Откройте каталог партнёров, получите первую привилегию — и здесь появится ваша активность.</p>
      </div>
    `;
  }
  return renderActivityFeed(items);
};

const renderClientActivePrivilege = () => {
  const activeVerification = getClientActiveVerification();

  if (!activeVerification) {
    return `
      <article class="client-active-privilege client-active-privilege--empty">
        <p class="section-eyebrow section-kicker">Активная привилегия</p>
        <h4 class="card-title">Активных привилегий пока нет</h4>
        <p class="card-description compact-copy">Выберите предложение в каталоге.</p>
        <button type="button" data-client-tab="catalog">Открыть каталог</button>
      </article>
    `;
  }

  return `
    <article class="client-active-privilege">
      <div>
        <p class="section-eyebrow section-kicker">Активная привилегия</p>
        <h4 class="card-title">У вас есть активная привилегия</h4>
        <p class="card-description compact-copy">${formatValue(activeVerification.partner_name)} · ${formatValue(activeVerification.offer_title || 'Клубная привилегия партнёра')}</p>
      </div>
      <div class="client-active-code" aria-label="Код активной привилегии">${formatValue(activeVerification.code)}</div>
      <dl class="client-card-details">
        <div><dt>Истекает</dt><dd>${formatValue(formatDate(activeVerification.expires_at))}</dd></div>
      </dl>
      <button type="button" data-client-tab="history">Мои привилегии</button>
    </article>
  `;
};

const renderClientHome = () => {
  const profile = clientState.profile || {};
  const cityName = getClientSelectedCityName();
  const { active } = getClientVerificationStats();
  const isVkBound = Boolean(profile.is_vk_bound || profile.vk_user_id);
  const vkUrl = String(profile.vk_url || '').trim() || (profile.vk_user_id ? `https://vk.com/id${profile.vk_user_id}` : '');
  const hasActiveSubscription = isClientSubscriptionActive();
  const activeSubscriptionUntil = formatDate(clientState.subscription?.ends_at);
  const subscriptionSubtitle = hasActiveSubscription
    ? `Подписка активна до ${formatValue(activeSubscriptionUntil)}`
    : 'Оформите подписку, чтобы получать привилегии у партнёров';
  const hasProfileContacts = isClientProfileCompleted();
  const quickActions = [
    { title: 'Смотреть партнёров', text: 'Каталог по городу и категории.', tab: 'catalog' },
    { title: 'Получить код у партнёра', text: 'Откройте предложение и получите код.', tab: 'catalog' },
    { title: 'Мои коды', text: 'Активные и прошлые коды.', tab: 'history' },
    { title: 'Изменить город', text: 'Уточнить выдачу каталога.', tab: 'profile' },
  ];

  return `
    <section class="client-home" aria-labelledby="client-home-title">
      <div class="client-home-hero">
        <div>
          <p class="section-eyebrow section-kicker">Клиентский кабинет</p>
          <h2 class="section-title" id="client-home-title">Мой клуб привилегий</h2>
          <p class="section-description compact-copy">${escapeHtml(subscriptionSubtitle)}</p>
          <div class="client-home-actions">
            <button type="button" data-client-tab="${hasActiveSubscription ? 'catalog' : 'subscription'}">${hasActiveSubscription ? 'Смотреть партнёров' : 'Оформить подписку'}</button>
            <button type="button" class="admin-inline-action ui-button ui-button--secondary" data-client-tab="${hasActiveSubscription ? 'history' : 'catalog'}">${hasActiveSubscription ? 'Мои привилегии' : 'Посмотреть партнёров'}</button>
          </div>
        </div>
        <div class="client-home-stats text-stack" aria-label="Сводка клиента">
          <div class="client-home-stat"><span>Город</span><strong>${escapeHtml(cityName)}</strong></div>
          <div class="client-home-stat"><span>VK</span><strong>${isVkBound ? 'VK привязан' : 'VK не привязан'}</strong></div>
          ${active.length ? `<div class="client-home-stat"><span>Активные коды</span><strong>${active.length}</strong></div>` : ''}
        </div>
      </div>
      <div class="client-quick-actions" aria-label="Быстрые действия">
        ${quickActions.map((action) => `
          <button type="button" class="client-quick-action" data-client-tab="${escapeHtml(action.tab)}">
            <strong class="card-title">${escapeHtml(action.title)}</strong>
            <span class="card-description compact-copy">${escapeHtml(action.text)}</span>
          </button>
        `).join('')}
      </div>
      <section class="client-vk-link-card" aria-labelledby="client-home-vk-title">
        <div class="client-vk-link-header">
          <div>
            <h4 id="client-home-vk-title">VK</h4>
            <p class="helper-text compact-copy">${isVkBound ? 'VK уже привязан' : 'Подключите VK, чтобы получать коды через бота клуба.'}</p>
          </div>
          ${isVkBound
            ? (vkUrl ? `<a class="admin-inline-action ui-button ui-button--secondary" href="${escapeHtml(vkUrl)}" target="_blank" rel="noopener noreferrer">Открыть VK</a>` : '')
            : '<button type="button" data-client-create-vk-code>Создать код для VK</button>'}
        </div>
        ${isVkBound ? '' : renderClientVkLinkCode()}
      </section>
      <section class="summary-card client-raffle-card" aria-labelledby="client-raffle-title">
        <h4 id="client-raffle-title">Ежемесячный розыгрыш</h4>
        <p class="compact-copy">${hasProfileContacts ? 'Контакты заполнены. Вы участвуете в розыгрышах клуба.' : 'Заполните имя, телефон и email, чтобы мы могли связаться с вами при победе.'}</p>
        ${hasProfileContacts ? '' : '<button type="button" class="admin-inline-action ui-button ui-button--secondary" data-client-tab="profile">Заполнить профиль</button>'}
      </section>
      <section class="client-activity-preview" aria-labelledby="client-activity-preview-title">
        <div class="client-tab-header admin-section-heading text-stack">
          <h4 class="client-tab-title section-title" id="client-activity-preview-title">Последняя активность</h4>
          <p class="client-tab-description section-description compact-copy">2–3 последних события по вашим привилегиям.</p>
        </div>
        ${renderClientActivityPreview()}
        <button type="button" class="admin-inline-action ui-button ui-button--secondary" data-client-tab="activity">Вся активность</button>
      </section>
      ${renderClientActivePrivilege()}
    </section>
  `;
};

const getClientOnboardingSteps = () => {
  const profile = clientState.profile || {};
  const verifications = Array.isArray(clientState.verifications) ? clientState.verifications : [];
  const hasSelectedCity = Boolean(profile.selected_city_id || profile.city || profile.selected_city_name);
  const hasCatalogOpened = clientState.activeTab === 'catalog' || clientState.catalogLoaded;
  const hasVerification = verifications.length > 0;
  const hasConfirmedVerification = verifications.some((item) => String(item.status || '').toLowerCase() === 'confirmed' || item.confirmed_at);
  const hasActiveVerification = verifications.some((item) => String(item.status || '').toLowerCase() === 'active');

  return [
    {
      title: 'Выберите город',
      text: 'Сохраните город в профиле — каталог покажет партнёров рядом с вами.',
      done: hasSelectedCity,
      action: 'Выбрать город',
      tab: 'profile',
    },
    {
      title: 'Откройте каталог',
      text: 'Перейдите в каталог, чтобы выбрать партнёра, категорию или конкретное предложение.',
      done: hasCatalogOpened,
      action: 'Открыть каталог',
      tab: 'catalog',
    },
    {
      title: 'Получите привилегию',
      text: 'Нажмите «Получить привилегию» в карточке партнёра или предложения.',
      done: hasVerification,
      action: 'Открыть каталог',
      tab: 'catalog',
    },
    {
      title: 'Покажите код партнёру',
      text: 'Откройте «Мои привилегии» и покажите активный код сотруднику перед оплатой.',
      done: hasConfirmedVerification,
      active: hasActiveVerification && !hasConfirmedVerification,
      action: 'Мои привилегии',
      tab: 'history',
    },
  ];
};

const renderClientOnboarding = () => {
  const steps = getClientOnboardingSteps();
  const completedCount = steps.filter((step) => step.done).length;
  const nextTodoIndex = steps.findIndex((step) => !step.done);
  const isComplete = completedCount === steps.length;

  return `
    <section class="client-onboarding" aria-labelledby="client-onboarding-title">
      <div class="client-onboarding-header">
        <div>
          <p class="section-eyebrow section-kicker">Онбординг клиента</p>
          <h4 class="section-title" id="client-onboarding-title">Как пользоваться клубом</h4>
          <p class="section-description compact-copy">Партнёр → код → визит.</p>
        </div>
        <div class="client-onboarding-progress" aria-label="Прогресс онбординга">
          <strong>Пройдено ${completedCount} из ${steps.length}</strong>
          <span>${isComplete ? 'Вы уже умеете пользоваться клубом' : 'Следующий шаг отмечен ниже'}</span>
        </div>
      </div>
      <div class="client-onboarding-steps">
        ${steps.map((step, index) => {
          const isCurrent = !step.done && (index === nextTodoIndex || step.active);
          const stateLabel = step.done ? '✅ Готово' : 'Следующий шаг';
          return `
            <article class="client-onboarding-step client-onboarding-step--${step.done ? 'done' : 'todo'}${step.active && !step.done ? ' client-onboarding-step--active' : ''}">
              <span class="client-onboarding-step__status">${stateLabel}</span>
              <h5 class="card-title">${escapeHtml(step.title)}</h5>
              <p class="card-description compact-copy">${escapeHtml(step.text)}</p>
              ${isCurrent ? `<button type="button" class="client-onboarding-action" data-client-tab="${escapeHtml(step.tab)}">${escapeHtml(step.action)}</button>` : ''}
            </article>
          `;
        }).join('')}
      </div>
    </section>
  `;
};

const renderClientTabHeader = (title, description) => `
  <div class="client-tab-header admin-section-heading text-stack">
    <h4 class="client-tab-title section-title">${escapeHtml(title)}</h4>
    <p class="client-tab-description section-description compact-copy">${escapeHtml(description)}</p>
  </div>
`;

const renderClientTabContent = () => {
  if (clientState.activeTab === 'savings') {
    return renderClientSavingsTab();
  }
  if (clientState.activeTab === 'catalog') {
    return renderClientCatalogTab();
  }
  if (clientState.activeTab === 'subscription') {
    return renderClientSubscriptionTab();
  }
  if (clientState.activeTab === 'history') {
    return renderClientHistoryTab();
  }
  if (clientState.activeTab === 'activity') {
    return renderClientActivityTab();
  }
  return renderClientProfileTab();
};

const renderClientSavingsTab = () => {
  const isPeriodMode = clientState.savingsFilterMode === 'period';
  const activePeriodLabel = isPeriodMode
    ? `За период: ${formatDateRu(clientState.savingsFilterFromDate)} — ${formatDateRu(clientState.savingsFilterToDate)}`
    : 'За всё время';
  if (clientState.savingsLoading) {
    return `${renderClientTabHeader('Моя экономия', 'По использованным привилегиям.')}
      <section class="client-savings-filter">
        <div class="client-savings-filter__modes">
          <button type="button" class="ui-button ${!isPeriodMode ? 'ui-button--primary' : 'ui-button--secondary'}" data-client-savings-filter-mode="all">За всё время</button>
          <button type="button" class="ui-button ${isPeriodMode ? 'ui-button--primary' : 'ui-button--secondary'}" data-client-savings-filter-mode="period">Период</button>
        </div>
      </section>
      <div class="activity-empty" role="status">Загружаем экономию…</div>`;
  }
  if (clientState.savingsError) {
    return `${renderClientTabHeader('Моя экономия', 'По использованным привилегиям.')}<div class="activity-empty activity-empty--error" role="alert">${escapeHtml(clientState.savingsError)}</div>`;
  }
  const data = clientState.savings || { total_saving_amount: 0, items: [] };
  return `
    ${renderClientTabHeader('Моя экономия', 'По использованным привилегиям.')}
    <section class="client-savings-filter">
      <div class="client-savings-filter__modes">
        <button type="button" class="ui-button ${!isPeriodMode ? 'ui-button--primary' : 'ui-button--secondary'}" data-client-savings-filter-mode="all">За всё время</button>
        <button type="button" class="ui-button ${isPeriodMode ? 'ui-button--primary' : 'ui-button--secondary'}" data-client-savings-filter-mode="period">Период</button>
      </div>
      ${isPeriodMode ? `
        <div class="client-savings-filter__fields">
          <label>От<input type="date" name="from_date" value="${escapeHtml(clientState.savingsFilterFromDate)}" data-client-savings-date="from" /></label>
          <label>До<input type="date" name="to_date" value="${escapeHtml(clientState.savingsFilterToDate)}" data-client-savings-date="to" /></label>
        </div>
        <div class="client-savings-filter__actions">
          <button type="button" class="ui-button ui-button--primary" data-client-savings-apply>Применить</button>
          <button type="button" class="ui-button ui-button--ghost" data-client-savings-reset>Сбросить</button>
        </div>
      ` : ''}
      ${clientState.savingsFilterUiError ? `<p class="form-message" role="alert">${escapeHtml(clientState.savingsFilterUiError)}</p>` : ''}
    </section>
    <article class="summary-card"><span>Активный период</span><strong>${escapeHtml(activePeriodLabel)}</strong></article>
    <article class="summary-card"><span>Вы сэкономили</span><strong>${formatPrice(data.total_saving_amount)}</strong><small>По использованным привилегиям</small></article>
    ${Array.isArray(data.items) && data.items.length ? data.items.map((item) => `
      <article class="client-privilege-card">
        <h4>${formatValue(item.partner_name)}</h4>
        <p>${formatValue(item.offer_title)}</p>
        <p>${formatValue(formatDate(item.used_at))}</p>
        <p>Обычная цена: ${formatPrice(item.base_price)}</p>
        <p>Цена участницы: ${formatPrice(item.final_price)}</p>
        <p>Экономия: ${formatPrice(item.saving_amount)}</p>
      </article>
    `).join('') : '<div class="activity-empty" role="status"><strong>Пока нет использованных привилегий.</strong><p>Получайте коды у партнёров — экономия появится здесь после использования.</p></div>'}
  `;
};

const renderClientProfileTab = () => {
  const profile = clientState.profile || {};
  const isVkBound = Boolean(profile.is_vk_bound || profile.vk_user_id);
  const vkUrl = String(profile.vk_url || '').trim() || (profile.vk_user_id ? `https://vk.com/id${profile.vk_user_id}` : '');
  const cityOptions = getClientCityOptions();
  return `
    ${renderClientTabHeader('Профиль', 'Город помогает подобрать предложения рядом.')}
    <div class="partner-profile-grid">
      ${[
        ['Email', profile.email],
        ['Телефон', profile.phone],
        ['Имя', profile.full_name],
        ['Город', profile.selected_city_name || 'Выберите город'],
        ['Источник', profile.source],
        ['Активность', renderBoolStatusBadge(profile.is_active)],
      ].map(([label, value]) => `
        <div class="summary-card"><span>${label}</span><strong>${renderDisplayValue(value)}</strong></div>
      `).join('')}
    </div>
    <section class="client-vk-link-card" aria-labelledby="client-vk-link-title">
      <div class="client-vk-link-header">
        <div>
          <h4 id="client-vk-link-title">${isVkBound ? 'VK привязан' : 'Привязка VK'}</h4>
          <p class="helper-text compact-copy">${isVkBound ? 'Ваш VK уже связан с WEB-кабинетом.' : 'Создайте код и отправьте VK-боту: Привязать КОД'}</p>
        </div>
        ${isVkBound
          ? (vkUrl ? `<a class="admin-inline-action ui-button ui-button--secondary" href="${escapeHtml(vkUrl)}" target="_blank" rel="noopener noreferrer">Открыть VK</a>` : '')
          : '<button type="button" data-client-create-vk-code>Создать код для VK</button>'}
      </div>
      ${isVkBound ? '' : renderClientVkLinkCode()}
    </section>
    <form class="admin-form admin-form--inline" data-client-form="profile">
      <h4>Обновить профиль</h4>
      <label>Имя<input name="full_name" value="${escapeHtml(profile.full_name || '')}" /></label>
      <label>Город
        ${renderCustomSelect({
          name: 'selected_city_id',
          value: profile.selected_city_id || '',
          options: [
            { value: '', label: 'Выберите город' },
            ...cityOptions.map((city) => ({ value: city.id, label: city.name })),
          ],
          placeholder: 'Выберите город',
          label: 'Город',
          data: { clientProfileCity: true },
        })}
      </label>
      <p class="helper-text form-message compact-copy">Город уточняет каталог.</p>
      <button type="submit">Сохранить</button>
      <p class="form-message" data-client-form-message="profile">${escapeHtml(clientState.formMessages.profile || '')}</p>
    </form>
  `;
};

const renderClientVkLinkCode = () => {
  const statusClass = clientState.vkLinkStatus ? ` client-vk-link-message--${clientState.vkLinkStatus}` : '';
  const message = clientState.vkLinkMessage
    ? `<p class="client-vk-link-message${statusClass}">${escapeHtml(clientState.vkLinkMessage)}</p>`
    : '';

  if (!clientState.vkLinkCode) {
    return message;
  }

  const { code, expires_at: expiresAt, ttl_seconds: ttlSeconds } = clientState.vkLinkCode;
  return `
    <div class="client-vk-link-result">
      <span class="client-vk-link-code">${escapeHtml(code)}</span>
      <dl class="client-vk-link-meta">
        <div><dt>Истекает</dt><dd>${formatValue(formatDate(expiresAt))}</dd></div>
        <div><dt>TTL, сек.</dt><dd>${formatValue(ttlSeconds)}</dd></div>
      </dl>
      <p>Скопируйте код и отправьте VK-боту: <strong>Привязать ${escapeHtml(code)}</strong></p>
      <p class="client-warning">Код действует 10 минут. Новый код отменяет предыдущий.</p>
      ${message}
    </div>
  `;
};

const renderClientSubscriptionTab = () => {
  const subscription = clientState.subscription;
  if (!subscription) {
    return `
      ${renderClientTabHeader('Моя подписка', 'Статус клубного доступа и срок действия.')}
      ${renderClientEmptyState('Активная подписка пока не найдена', 'Когда подписка будет оформлена, здесь появится срок действия и статус.')}
    `;
  }

  return `
    ${renderClientTabHeader('Моя подписка', 'Статус клубного доступа и срок действия.')}
    <div class="summary-grid">
      <div class="summary-card"><span>Статус</span><strong>${renderStatusBadge(formatStatus(subscription.status))}</strong></div>
      <div class="summary-card"><span>Начало</span><strong>${formatValue(formatDate(subscription.starts_at))}</strong></div>
      <div class="summary-card"><span>Окончание</span><strong>${formatValue(formatDate(subscription.ends_at))}</strong></div>
    </div>
  `;
};

const renderClientCatalogTab = () => {
  const cityOptions = getClientCityOptions();
  const categoryOptions = getClientCategoryOptions();
  return `
    ${renderClientTabHeader('Каталог партнёров', 'Выберите категорию, город или найдите партнёра по названию.')}
    <form class="admin-form client-catalog-filter" data-client-form="catalog">
      <label>Поиск<input name="q" value="${escapeHtml(clientState.catalogFilters.q)}" placeholder="Название, описание, адрес" /></label>
      <label>Категория
        ${renderCustomSelect({
          name: 'category_slug',
          value: clientState.catalogFilters.category_slug,
          options: [
            { value: '', label: 'Все категории' },
            ...categoryOptions.map((category) => ({ value: category.slug, label: category.title })),
          ],
          placeholder: 'Все категории',
          label: 'Категория',
          data: { clientCatalogFilter: 'category' },
        })}
      </label>
      <label>Город
        ${renderCustomSelect({
          name: 'city_slug',
          value: clientState.catalogFilters.city_slug,
          options: [
            { value: '', label: 'По выбранному городу' },
            { value: '__all__', label: 'Все города' },
            ...cityOptions.filter((city) => city.slug).map((city) => ({ value: city.slug, label: city.name })),
          ],
          placeholder: 'По выбранному городу',
          label: 'Город',
          data: { clientCatalogFilter: 'city' },
        })}
      </label>
      <button type="submit">Найти</button>
    </form>
    ${clientState.latestVerification ? renderClientVerificationResult(clientState.latestVerification) : ''}
    <div class="client-marketplace-grid client-catalog-grid">
      ${clientState.partners.length ? clientState.partners.map(renderClientPartnerCard).join('') : renderClientEmptyState('Партнёры пока не найдены', 'Попробуйте выбрать другой город или категорию.')}
    </div>
  `;
};

const getClientPartnerVisuals = (partner = {}) => {
  const photos = getActivePartnerGalleryPhotos(partner.photos);
  const coverFromPartner = [partner.cover_url, partner.main_image_url, partner.image_url].find(isSafePublicAssetUrl) || '';
  const previewUrl = coverFromPartner || photos[0]?.url || (isSafePublicAssetUrl(partner.logo_url) ? partner.logo_url : '');
  return {
    photos,
    coverUrl: previewUrl,
    logoUrl: isSafePublicAssetUrl(partner.logo_url) ? partner.logo_url : '',
  };
};

const renderClientPartnerCover = (partner = {}, className = 'client-partner-cover') => {
  const { coverUrl } = getClientPartnerVisuals(partner);
  return `
    <div class="${className} ${coverUrl ? '' : `${className}--placeholder`}" ${coverUrl ? `style="background-image: url('${escapeHtml(coverUrl)}')" role="img" aria-label="${escapeHtml(partner.name || 'Партнёр')}"` : 'aria-hidden="true"'}>
      ${coverUrl ? '' : '<span>Фото витрины</span>'}
    </div>
  `;
};

const renderClientPartnerLogo = (partner = {}) => {
  const { logoUrl } = getClientPartnerVisuals(partner);
  return `<div class="client-partner-logo ${logoUrl ? '' : 'client-partner-logo--placeholder'}" ${logoUrl ? `style="background-image: url('${escapeHtml(logoUrl)}')"` : ''} aria-hidden="true">${logoUrl ? '' : '♡'}</div>`;
};

const renderClientPartnerGallery = (partner = {}) => {
  const { photos } = getClientPartnerVisuals(partner);
  if (!photos.length) {
    return renderClientPartnerCover(partner, 'client-partner-gallery-main');
  }
  return `
    <div class="client-partner-gallery" aria-label="Галерея партнёра">
      <div class="client-partner-gallery-main" style="background-image: url('${escapeHtml(photos[0].url)}')" role="img" aria-label="${escapeHtml(photos[0].alt_text || partner.name || 'Фото партнёра')}"></div>
      ${photos.length > 1 ? `<div class="client-partner-gallery-thumbs">${photos.slice(0, 6).map((photo) => `<span style="background-image: url('${escapeHtml(photo.url)}')" aria-hidden="true"></span>`).join('')}</div>` : ''}
    </div>
  `;
};

const getPartnerGalleryImages = (partner = {}) => {
  const photos = Array.isArray(partner.photos) ? partner.photos : [];
  const activePhotos = photos
    .filter((photo) => photo?.is_active !== false)
    .map((photo) => ({
      url: [photo?.image_url, photo?.photo_url, photo?.url].find(isSafePublicAssetUrl) || '',
      alt_text: photo?.alt_text || partner.name || 'Фото партнёра',
      sort_order: photo?.sort_order,
      id: photo?.id,
    }))
    .filter((photo) => photo.url)
    .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0) || Number(left.id || 0) - Number(right.id || 0));

  const galleryImages = [];
  const seen = new Set();
  const pushUnique = (url, altText) => {
    if (!isSafePublicAssetUrl(url) || seen.has(url)) return;
    seen.add(url);
    galleryImages.push({ url, alt_text: altText || partner.name || 'Фото партнёра' });
  };
  pushUnique([partner.cover_url, partner.main_image_url, partner.image_url].find(isSafePublicAssetUrl) || '', partner.name || 'Обложка партнёра');
  activePhotos.forEach((photo) => pushUnique(photo.url, photo.alt_text));
  if (!galleryImages.length) {
    pushUnique(partner.logo_url, partner.name || 'Логотип партнёра');
  }
  return galleryImages;
};

const renderClientPartnerModalGallery = (partner = {}) => {
  const images = getPartnerGalleryImages(partner);
  if (!images.length) {
    return `
      <section class="client-partner-modal__gallery" aria-label="Галерея партнёра">
        <div class="client-partner-modal__main-image client-partner-modal__placeholder">Фото партнёра</div>
      </section>
    `;
  }

  const safeIndex = Math.min(Math.max(Number(clientState.partnerModalGalleryIndex || 0), 0), images.length - 1);
  const currentImage = images[safeIndex];
  const hasMany = images.length > 1;

  return `
    <section class="client-partner-modal__gallery" aria-label="Галерея партнёра">
      <div class="client-partner-modal__main-image">
        <img class="client-partner-modal__image" src="${escapeHtml(currentImage.url)}" alt="${escapeHtml(currentImage.alt_text || partner.name || 'Фото партнёра')}" loading="lazy" />
        <span class="client-partner-modal__counter">${safeIndex + 1} / ${images.length}</span>
        ${hasMany ? `
          <button class="client-partner-modal__nav client-partner-modal__nav--prev" type="button" data-gallery-action="prev" aria-label="Предыдущее фото">‹</button>
          <button class="client-partner-modal__nav client-partner-modal__nav--next" type="button" data-gallery-action="next" aria-label="Следующее фото">›</button>
        ` : ''}
      </div>
      ${hasMany ? `
        <div class="client-partner-modal__thumbs">
          ${images.map((image, index) => `<button class="client-partner-modal__thumb ${index === safeIndex ? 'client-partner-modal__thumb--active' : ''}" type="button" data-gallery-action="select" data-gallery-index="${escapeHtml(index)}" aria-label="Показать фото ${escapeHtml(index + 1)}"><img src="${escapeHtml(image.url)}" alt="" loading="lazy" /></button>`).join('')}
        </div>
      ` : ''}
    </section>
  `;
};

const renderClientPartnerCard = (partner) => {
  const partnerId = partner.id;
  const cityAddress = [partner.city_name || partner.city, partner.address].filter(Boolean).join(' · ');
  const { coverUrl, logoUrl } = getClientPartnerVisuals(partner);
  const categories = getPartnerCategories(partner);
  return `
    <article class="client-partner-card" data-partner-id="${escapeHtml(partnerId)}">
      <div class="client-partner-card__cover ${coverUrl ? '' : 'client-partner-card__cover--placeholder'}" ${coverUrl ? `style="background-image: url('${escapeHtml(coverUrl)}')" role="img" aria-label="${escapeHtml(partner.name || 'Партнёр')}"` : 'aria-hidden="true"'}>${coverUrl ? '' : '<span>Фото партнёра</span>'}</div>
      <div class="client-partner-card-body">
        <h4>${formatValue(partner.name)}</h4>
        <div class="client-card-topline">
          <div class="client-partner-card__avatar ${logoUrl ? '' : 'client-partner-card__avatar--placeholder'}" ${logoUrl ? `style="background-image: url('${escapeHtml(logoUrl)}')"` : ''} aria-hidden="true">${logoUrl ? '' : '♡'}</div>
          <div>
            <span>${formatValue(categories.map((item) => item.name).join(' · '))}</span>
            ${partner.is_verified ? '<span class="status-badge status-badge--success">Проверенный партнёр</span>' : ''}
          </div>
        </div>
        <p>${formatValue(partner.description || 'Витрина услуг партнёра скоро пополнится подробностями.')}</p>
        <div class="client-card-location">${formatValue(cityAddress)}</div>
        <div class="client-partner-card__actions client-card-actions ui-card-actions ui-action-row ui-action-row--stack-mobile">
          <button type="button" data-client-partner-open data-partner-id="${escapeHtml(partnerId)}">Открыть</button>
          <button type="button" data-client-verify-partner="${escapeHtml(partnerId)}">Получить привилегию</button>
        </div>
      </div>
    </article>
  `;
};

const renderClientPartnerDetail = (partner = {}) => {
  const partnerId = partner.id;
  const offers = clientState.offersByPartner[partnerId] || [];
  const cityAddress = [partner.city_name, partner.address].filter(Boolean).join(' · ');
  const contacts = [
    ['Телефон', partner.phone],
    ['Сайт', partner.website_url],
    ['Соцсети', partner.social_url],
  ].filter(([, value]) => String(value || '').trim());
  return `
    <section class="client-partner-detail">
      <div class="client-partner-detail-hero">
        ${renderClientPartnerGallery(partner)}
        <div class="client-partner-detail-info">
          <div class="client-card-topline">
            ${renderClientPartnerLogo(partner)}
            <div>
              <span>${formatValue(categories.map((item) => item.name).join(' · '))}</span>
              ${partner.is_verified ? '<span class="status-badge status-badge--success">Проверенный партнёр</span>' : ''}
            </div>
          </div>
          <h3>${formatValue(partner.name)}</h3>
          <p>${formatValue(partner.description || 'Описание партнёра скоро появится.')}</p>
          <dl class="client-card-details">
            <div><dt>Город и адрес</dt><dd>${formatValue(cityAddress)}</dd></div>
            <div><dt>График работы</dt><dd>${formatValue(partner.working_hours)}</dd></div>
            ${contacts.length ? contacts.map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`).join('') : ''}
          </dl>
          <button type="button" data-client-verify-partner="${escapeHtml(partnerId)}">Получить привилегию</button>
        </div>
      </div>
      <div class="client-partner-offers">
        <div class="admin-section-heading"><h4>Предложения партнёра</h4><p>Выберите услугу и получите клубную привилегию.</p></div>
        ${offers.length ? offers.map((offer) => renderClientOffer(partnerId, offer)).join('') : '<div class="client-partner-empty">Предложения скоро появятся.</div>'}
      </div>
    </section>
  `;
};

const renderClientPartnerModalOffer = (partnerId, offer) => `
  <div class="client-partner-modal__offer">
    ${renderClientOffer(partnerId, offer)}
    ${getOfferPhotos(offer).length ? `<button type="button" class="admin-inline-action ui-button ui-button--secondary" data-client-offer-gallery-open="${escapeHtml(offer.id)}">Посмотреть работы</button>` : ''}
  </div>
`;

const renderClientPartnerModal = () => {
  const partnerId = clientState.selectedPartnerModalId;
  if (!partnerId) return '';

  const partner = clientState.selectedPartnerModalPartner
    || clientState.partners.find((item) => String(item.id) === String(partnerId))
    || {};
  const offers = Array.isArray(clientState.selectedPartnerModalOffers) ? clientState.selectedPartnerModalOffers : [];
  const activeOfferGalleryId = String(clientState.partnerModalOfferGalleryId || '');
  const activeOffer = offers.find((offer) => String(offer.id) === activeOfferGalleryId);
  const offerPhotos = activeOffer ? getOfferPhotos(activeOffer) : [];
  const offerPhotoIndex = Math.min(Math.max(Number(clientState.partnerModalOfferGalleryIndex || 0), 0), Math.max(offerPhotos.length - 1, 0));
  const cityAddress = [partner.city_name || partner.city, partner.address].filter(Boolean).join(' · ');
  const categories = getPartnerCategories(partner);
  const contacts = [
    ['Город и адрес', cityAddress],
    ['График работы', partner.working_hours],
    ['Телефон', partner.phone],
    ['Сайт', partner.website_url],
    ['Соцсети', partner.social_url],
  ].filter(([, value]) => String(value || '').trim());
  const { logoUrl } = getClientPartnerVisuals(partner);
  const titleId = 'client-partner-modal-title';

  return `
    <div class="client-partner-modal" data-client-partner-modal>
      <div class="client-partner-modal__overlay" data-client-partner-modal-close></div>
      <section class="client-partner-modal__panel" role="dialog" aria-modal="true" aria-labelledby="${titleId}">
        <header class="client-partner-modal__header">
          <div>
            <span class="section-kicker">Витрина партнёра</span>
            <h3 id="${titleId}">${formatValue(partner.name || 'Партнёр клуба')}</h3>
          </div>
          <button class="client-partner-modal__close" type="button" data-client-partner-modal-close aria-label="Закрыть витрину партнёра">×</button>
        </header>
        <div class="client-partner-modal__body">
          ${clientState.partnerModalLoading ? '<div class="client-partner-modal__empty">Загружаем витрину партнёра…</div>' : ''}
          ${clientState.partnerModalError ? `<div class="client-partner-modal__empty">${escapeHtml(clientState.partnerModalError)}</div>` : ''}
          <div class="client-partner-modal__hero">
            ${renderClientPartnerModalGallery(partner)}
            <aside class="client-partner-modal__info">
              <div class="client-card-topline">
                <div class="client-partner-card__avatar ${logoUrl ? '' : 'client-partner-card__avatar--placeholder'}" ${logoUrl ? `style="background-image: url('${escapeHtml(logoUrl)}')"` : ''} aria-hidden="true">${logoUrl ? '' : '♡'}</div>
                <div>
                  <span>${formatValue(categories.map((item) => item.name).join(' · '))}</span>
                  ${partner.is_verified ? '<span class="status-badge status-badge--success">Проверенный партнёр</span>' : ''}
                </div>
              </div>
              <p>${formatValue(partner.description || 'Описание партнёра скоро появится.')}</p>
              <dl class="client-card-details">
                ${contacts.length ? contacts.map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`).join('') : '<div><dt>Контакты</dt><dd>Партнёр скоро добавит контакты.</dd></div>'}
              </dl>
              <button type="button" data-client-verify-partner="${escapeHtml(partnerId)}">Получить привилегию</button>
            </aside>
          </div>
          <section class="client-partner-modal__offers" aria-label="Предложения партнёра">
            <div class="admin-section-heading"><h4>Предложения</h4><p>Выберите услугу и получите клубную привилегию.</p></div>
            ${offers.length ? offers.map((offer) => renderClientPartnerModalOffer(partnerId, offer)).join('') : '<div class="client-partner-modal__empty">Пока нет активных предложений</div>'}
          </section>
          ${activeOffer && offerPhotos.length ? `
            <section class="client-partner-modal__offers client-partner-modal__offer-gallery" aria-label="Галерея работ услуги">
              <div class="admin-section-heading"><h4>Работы: ${escapeHtml(activeOffer.title || 'Услуга')}</h4></div>
              <div class="client-partner-modal__main-image">
                <img class="client-partner-modal__image" src="${escapeHtml(offerPhotos[offerPhotoIndex].url)}" alt="${escapeHtml(offerPhotos[offerPhotoIndex].alt_text)}" loading="lazy" />
                <span class="client-partner-modal__counter">${offerPhotoIndex + 1} / ${offerPhotos.length}</span>
                ${offerPhotos.length > 1 ? `<button class="client-partner-modal__nav client-partner-modal__nav--prev" type="button" data-offer-gallery-action="prev" aria-label="Предыдущее фото">‹</button><button class="client-partner-modal__nav client-partner-modal__nav--next" type="button" data-offer-gallery-action="next" aria-label="Следующее фото">›</button>` : ''}
              </div>
            </section>` : ''}
        </div>
      </section>
    </div>
  `;
};

const renderClientOffer = (partnerId, offer) => renderOfferMarketplaceCard(offer, {
  cta: 'Получить привилегию',
  note: 'Карточка привилегии партнёра',
  actionHtml: `<button type="button" data-client-verify-offer="${escapeHtml(partnerId)}" data-offer-id="${escapeHtml(offer.id)}">Получить привилегию</button>`,
});

const renderClientVerificationResult = (verification) => `
  <div class="client-verification-result privilege-success-panel" role="status" data-privilege-success-panel>
    <p class="section-kicker">Привилегия активирована</p>
    <div class="privilege-success-panel__heading">
      <div>
        <h4>${formatValue(verification.partner_name)}</h4>
        <p>${formatValue(verification.offer_title || 'Клубная привилегия партнёра')}</p>
      </div>
      ${renderStatusBadge(formatPrivilegeStatus(verification.status))}
    </div>
    <div class="privilege-code" aria-label="Код подтверждения">${formatValue(verification.code)}</div>
    <p class="client-warning">Покажите этот код партнёру перед оплатой/получением услуги.</p>
    <dl class="client-card-details privilege-success-panel__meta">
      <div><dt>Срок действия</dt><dd>${formatValue(formatDate(verification.expires_at))}</dd></div>
      <div><dt>Создано</dt><dd>${formatValue(formatDate(verification.created_at))}</dd></div>
    </dl>
    <div class="client-card-actions ui-card-actions ui-action-row ui-action-row--stack-mobile">
      <button type="button" data-client-dismiss-privilege>Понятно</button>
      <button type="button" class="admin-inline-action ui-button ui-button--secondary" data-client-open-privileges>Мои привилегии</button>
    </div>
  </div>
`;

const renderClientPrivilegeCard = (item) => `
  <article class="client-privilege-card" data-client-privilege-card>
    <div class="client-card-topline">
      ${renderStatusBadge(formatPrivilegeStatus(item.status))}
      <span>${escapeHtml(formatDate(item.created_at) || 'Дата создания не указана')}</span>
    </div>
    <h4>${formatValue(item.partner_name)}</h4>
    <p>${formatValue(item.offer_title || 'Клубная привилегия партнёра')}</p>
    <div class="privilege-code privilege-code--card" aria-label="Код подтверждения">${formatValue(item.code)}</div>
    <dl class="client-card-details">
      <div><dt>Срок действия</dt><dd>${formatValue(formatDate(item.expires_at))}</dd></div>
      <div><dt>Подтверждено</dt><dd>${formatValue(formatDate(item.confirmed_at))}</dd></div>
    </dl>
  </article>
`;

const renderClientHistoryTab = () => `
  ${renderClientTabHeader('Мои привилегии', 'Активные и использованные коды партнёрских предложений.')}
  ${clientState.verifications.length
    ? `<div class="client-privilege-card-grid">${clientState.verifications.map(renderClientPrivilegeCard).join('')}</div>`
    : renderClientEmptyState('Пока нет привилегий', 'Выберите оффер в каталоге и нажмите «Получить привилегию».')}
`;

const renderClientActivityTab = () => `
  ${renderClientTabHeader('Активность', 'Ваши действия и изменения статусов привилегий.')}
  <p hidden>Здесь появятся ваши действия и статусы привилегий.</p>
  ${renderActivityFeed(clientState.activityItems, { loading: clientState.activityLoading, error: clientState.activityError })}
`;

const renderPartnerLayout = () => {
  renderDashboardApp('partner');
  partnerDashboard.innerHTML = `
    <section class="admin-tab-panel">${renderPartnerTabContent()}</section>
  `;
};

const renderPartnerTabContent = () => {
  if (partnerState.activeTab === 'overview') {
    return renderPartnerOverviewTab();
  }
  if (partnerState.activeTab === 'contacts') {
    return renderPartnerContactsTab();
  }
  if (partnerState.activeTab === 'media') {
    return renderPartnerMediaTab();
  }
  if (partnerState.activeTab === 'services') {
    return renderPartnerOffersTab();
  }
  if (partnerState.activeTab === 'preview') {
    return renderPartnerPreviewTab();
  }
  return renderPartnerProfileTab();
};

const isRequiredProfileFieldEmpty = (profile, field) => !String(profile?.[field] || '').trim();

const getPartnerSaveStatusLabel = () => {
  if (partnerState.profileSaveStatus === 'saving') return 'Сохранение…';
  if (partnerState.isProfileDirty) return 'Есть несохранённые изменения';
  return '';
};

const renderPartnerSectionHeader = (title, description) => `
  <div class="partner-section-header text-stack">
    <h4 class="section-title">${escapeHtml(title)}</h4>
    <p class="partner-section-description section-description compact-copy">${escapeHtml(description)}</p>
  </div>
`;

const renderPartnerOffersTeaser = () => `
  <div class="offer-card-grid">
    ${partnerState.offers.length ? partnerState.offers.map((offer) => renderOfferMarketplaceCard(offer, {
      note: offer.is_active ? 'Preview для клиента' : 'Ожидает активации.',
      actionHtml: renderPartnerOfferAction(offer),
    })).join('') : `
      <div class="partner-empty-state offer-card-placeholder">
        <strong>Добавьте первое предложение — именно оно мотивирует клиентку прийти.</strong>
        <button class="admin-inline-action ui-button ui-button--secondary" type="button" data-partner-onboarding-tab="offers">Добавить предложение</button>
      </div>
    `}
  </div>
`;

const renderPartnerOverviewTab = () => {
  const profile = partnerState.profile || {};
  return `
    <div class="admin-section-heading text-stack">
      <p class="section-eyebrow section-kicker">Обзор кабинета</p>
      <h4 class="section-title">Статус и готовность профиля</h4>
      <p class="section-description compact-copy">Проверьте готовность и перейдите к нужной вкладке в один клик.</p>
    </div>
    ${renderPartnerOnboardingChecklist(profile, { offers: partnerState.offers, photos: partnerState.photos })}
    <section class="panel-card">
      ${renderPartnerProfileHints(profile, { offers: partnerState.offers })}
    </section>
  `;
};

const renderPartnerProfileTab = () => {
  const profile = partnerState.profile || {};
  const descriptionLength = String(profile.description || '').length;
  return `
    <div class="admin-section-heading text-stack">
      <p class="section-eyebrow section-kicker">Кабинет партнёра</p>
      <h4 class="section-title">Профиль партнёра</h4>
      <p class="section-description compact-copy">Главные данные для витрины.</p>
    </div>
    <div class="partner-profile-layout partner-profile-top-grid">
      <form class="admin-form partner-profile-form" id="partner-profile-form" data-partner-form="profile">
        <main class="partner-profile-main partner-profile-settings">
          <section class="partner-section partner-section--compact">
            ${renderPartnerSectionHeader('Основные данные', 'Название, город, категория.')}
            <div class="partner-profile-grid">
              <label>Название<input name="name" value="${escapeHtml(profile.name || '')}" readonly placeholder="Например: Bloom Beauty Studio" /></label>
              <label>Город<input name="city_name" value="${escapeHtml(profile.city_name || '')}" readonly placeholder="Новосибирск" /></label>
              <label>Категория<input name="category" value="${escapeHtml(formatPartnerCategory(profile) || '')}" readonly placeholder="Красота" /></label>
              <article class="summary-card"><span>Активность</span><strong>${renderBoolStatusBadge(profile.is_active)}</strong></article>
              <article class="summary-card"><span>Проверка</span><strong>${renderVerifiedStatusBadge(profile.is_verified)}</strong></article>
            </div>
            <p class="helper-text form-message partner-profile-admin-note compact-copy">Название, город, категорию и статусы обновляет администратор.</p>
          </section>

          <section class="partner-section partner-section--compact">
            ${renderPartnerSectionHeader('Описание', 'Коротко о вашем сервисе.')}
            <label>Описание<textarea class="partner-description-textarea ${isRequiredProfileFieldEmpty(profile, 'description') ? 'partner-required-empty' : ''}" name="description" required placeholder="Уютная студия красоты в центре города…">${escapeHtml(profile.description || '')}</textarea></label>
            <p class="helper-text form-message partner-textarea-hint compact-copy">${escapeHtml(descriptionLength)} символов. Рекомендация: 200–500 символов.</p>
          </section>
        </main>

        <aside class="partner-profile-side">
          <div class="partner-side-stack">
            <section class="partner-section partner-profile-preview partner-section--compact">
              ${renderPartnerSectionHeader('Витрина партнёра', 'Preview карточки.')}
              <span class="section-eyebrow section-kicker">Так клиент увидит вашу карточку</span>
              ${renderPartnerMarketplaceCard(profile, { offers: partnerState.offers, note: 'Preview для клиента', photos: partnerState.photos })}
            </section>

          </div>
        </aside>
        <div class="partner-profile-fullwidth-sections">
          <section class="partner-section partner-progress-card partner-section--compact">
            ${renderPartnerSectionHeader('Готовность профиля', 'Заполнено и осталось.')}
            ${renderPartnerProfileHints(profile, { offers: partnerState.offers })}
            <div class="partner-side-tips">
              <strong>Ключевые элементы</strong>
              <span>Проверьте обязательные поля и добавьте хотя бы одно предложение с фото.</span>
            </div>
          </section>

          <section class="partner-section partner-combined-section partner-section--compact">
            ${renderPartnerSectionHeader('Фотографии профиля', 'Добавьте качественные фото для доверия.')}
            ${renderPartnerImageUploader(profile, 'partner')}
            <div class="partner-gallery-compact">
              ${renderPartnerSectionHeader('Галерея', 'Фото атмосферы и работ.')}
              ${renderPartnerGallery(profile, partnerState.photos, 'partner')}
            </div>
          </section>
        </div>

        <section class="partner-section partner-section--compact partner-profile-save-section">
          ${renderPartnerSectionHeader('Сохранить профиль', 'Проверьте и сохраните профильные поля.')}
          ${getPartnerSaveStatusLabel() ? `<div class="partner-save-status" role="status">${escapeHtml(getPartnerSaveStatusLabel())}</div>` : ''}
          <div class="ui-action-row ui-action-row--right ui-action-row--stack-mobile"><button class="ui-button ui-button--primary" type="submit">Сохранить</button></div>
          <p class="form-message" data-partner-form-message="profile">${escapeHtml(partnerState.formMessages.profile || '')}</p>
        </section>
      </form>
    </div>
    <div class="partner-save-bar" role="status" ${partnerState.isProfileDirty ? '' : 'hidden'}>
      <span>Есть несохранённые изменения</span>
      <button type="submit" form="partner-profile-form">Сохранить</button>
    </div>
  `;
};

const renderPartnerContactsTab = () => {
  const profile = partnerState.profile || {};
  return `
    <div class="admin-section-heading text-stack"><p class="section-eyebrow section-kicker">Контакты</p><h4 class="section-title">Связь и ссылки</h4></div>
    <form class="admin-form partner-profile-form" data-partner-form="contacts">
      <section class="partner-section partner-section--compact partner-combined-section">
        ${renderPartnerSectionHeader('Контакты и график', 'Контактные ссылки и каналы связи для клиенток.')}
        <div class="partner-profile-grid partner-contact-grid partner-form-grid">
          <label>Адрес<input class="${isRequiredProfileFieldEmpty(profile, 'address') ? 'partner-required-empty' : ''}" name="address" required value="${escapeHtml(profile.address || '')}" placeholder="Новосибирск, ул. Ленина, 15" /></label>
          <label>График работы<input class="${isRequiredProfileFieldEmpty(profile, 'working_hours') ? 'partner-required-empty' : ''}" name="working_hours" required value="${escapeHtml(profile.working_hours || '')}" placeholder="Пн–Пт 10:00–20:00, Сб 11:00–18:00" /></label>
          <label>Телефон<input name="phone" autocomplete="tel" value="${escapeHtml(profile.phone || '')}" placeholder="+7 999 123-45-67" /></label>
          <label>Ссылка на соцсеть / сайт<input name="website_url" value="${escapeHtml(profile.website_url || '')}" placeholder="https://example.ru" /></label>
          <label>Instagram<input name="instagram_url" value="${escapeHtml(profile.instagram_url || '')}" placeholder="https://instagram.com/your_brand" /></label>
          <label>VK<input name="vk_url" value="${escapeHtml(profile.vk_url || profile.social_url || '')}" placeholder="https://vk.com/your_brand" /></label>
          <label>Telegram<input name="telegram_url" value="${escapeHtml(profile.telegram_url || '')}" placeholder="https://t.me/your_brand" /></label>
          <label>WhatsApp<input name="whatsapp_url" value="${escapeHtml(profile.whatsapp_url || '')}" placeholder="https://wa.me/79991234567" /></label>
          <label>Карта / маршрут<input name="map_url" value="${escapeHtml(profile.map_url || '')}" placeholder="https://yandex.ru/maps/..." /></label>
          <label>Общая соцссылка (legacy)<input name="social_url" value="${escapeHtml(profile.social_url || '')}" placeholder="https://vk.com/bloom_beauty" /></label>
        </div>
      </section>
      <div class="ui-action-row ui-action-row--right"><button class="ui-button ui-button--primary" type="submit">Сохранить</button></div>
      <p class="form-message" data-partner-form-message="contacts">${escapeHtml(partnerState.formMessages.contacts || '')}</p>
    </form>
  `;
};

const renderPartnerMediaTab = () => `
  <div class="stack">
    <div class="admin-section-heading text-stack"><p class="section-eyebrow section-kicker">Медиа</p><h4 class="section-title">Логотип, обложка и галерея</h4><p class="section-description compact-copy">Логотип — квадрат, обложка — горизонтальная, галерея — фото работ и интерьера.</p></div>
    <section class="panel-card">${renderPartnerImageUploader(partnerState.profile || {}, 'partner')}</section>
    ${renderPartnerGalleryTab()}
  </div>
`;

const renderPartnerPreviewTab = () => `
  <div class="stack">
    <div class="admin-section-heading text-stack"><p class="section-eyebrow section-kicker">Предпросмотр</p><h4 class="section-title">Как карточка выглядит в Mini App</h4><p class="section-description compact-copy">Компактный read-only preview на основе текущих данных.</p></div>
    <section class="panel-card">${renderPartnerMarketplaceCard(partnerState.profile || {}, { offers: partnerState.offers, note: 'Read-only preview', photos: partnerState.photos })}</section>
    <section class="panel-card">${renderPartnerOffersTeaser()}</section>
  </div>
`;

const renderPartnerOfferAction = (offer) => `
  <button class="admin-inline-action ui-button ui-button--secondary admin-inline-action--primary" type="button" data-partner-offer-edit="${escapeHtml(offer.id)}">Редактировать</button>
  ${offer.is_active
    ? `<button class="admin-inline-action ui-button ui-button--secondary admin-inline-action--secondary" type="button" data-partner-offer-toggle="${escapeHtml(offer.id)}">Скрыть</button>`
    : '<button class="admin-inline-action ui-button ui-button--secondary admin-inline-action--secondary" type="button" disabled>На проверке</button>'}
  ${offer.image_url ? `<button class="admin-inline-action ui-button ui-button--danger admin-inline-action--danger" type="button" data-partner-offer-image-clear="${escapeHtml(offer.id)}">Удалить фото</button>` : ''}
`;

const renderPartnerOfferForm = () => {
  const offer = partnerState.offers.find((item) => String(item.id) === String(partnerState.selectedOfferIdForEdit));
  const isEdit = Boolean(offer);
  const previewOffer = isEdit ? offer : { is_active: false };
  const hasPreviewData = Boolean(
    String(previewOffer?.title || '').trim()
    || String(previewOffer?.benefit_text || '').trim()
    || String(previewOffer?.description || '').trim()
    || String(previewOffer?.conditions || previewOffer?.terms || '').trim()
    || String(previewOffer?.base_price || '').trim()
    || isSafePublicAssetUrl(previewOffer?.image_url),
  );

  return `
    <section class="offer-marketplace-preview">
      <span class="section-eyebrow section-kicker">Preview предложения</span>
      ${hasPreviewData
    ? renderOfferMarketplaceCard(previewOffer, { note: 'Preview для клиента', showFallbackPlaceholders: false })
    : '<div class="partner-offer-preview-empty">Заполните услугу, чтобы увидеть предпросмотр</div>'}
    </section>
    <form class="admin-form admin-form--inline" data-partner-form="${isEdit ? 'offerEdit' : 'offer'}" ${isEdit ? `data-offer-id="${escapeHtml(offer.id)}"` : ''}>
      <h4>${isEdit ? 'Редактировать услугу' : 'Новая услуга'}</h4>
      <p class="helper-text form-message compact-copy">Публикация после проверки администратором.</p>
      ${isEdit && offer?.is_active === false ? '<p class="helper-text form-message compact-copy">Ожидает активации.</p>' : ''}
      <label>Название<input name="title" required value="${escapeHtml(offer?.title || '')}" /></label>
      <label>Краткая выгода<input name="benefit_text" value="${escapeHtml(offer?.benefit_text || '')}" /></label>
      <label>Описание<textarea name="description" rows="3">${escapeHtml(offer?.description || '')}</textarea></label>
      <label>Условия<textarea name="conditions" rows="3">${escapeHtml(offer?.conditions || '')}</textarea></label>
      <div class="partner-offer-form-numeric-row">
        <label>Обычная цена<input class="partner-input-compact" name="base_price" type="number" step="0.01" inputmode="decimal" value="${escapeHtml(offer?.base_price || '')}" /></label>
        <label>Цена участницы<input class="partner-input-compact" name="member_price" type="number" step="0.01" inputmode="decimal" value="${escapeHtml(getOfferPricingView(offer || {}).memberPrice || '')}" /></label>
        <label>Экономия<input class="partner-input-compact" name="saving_amount" type="number" step="0.01" inputmode="decimal" value="${escapeHtml(getOfferPricingView(offer || {}).savingAmount || '')}" readonly /></label>
      </div>
      ${renderOfferImageUploader(offer, 'partner')}
      <details class="partner-profile-advanced">
        <summary>URL изображения предложения</summary>
        <p class="helper-text form-message compact-copy">URL сохраняется для проверки.</p>
        <label>URL изображения<input name="image_url" value="${escapeHtml(offer?.image_url || '')}" readonly placeholder="/uploads/offer.webp или /assets/offer.webp" /></label>
      </details>
      ${isEdit ? `<label class="checkbox-row"><input name="is_active" type="checkbox" ${offer?.is_active === false ? '' : 'checked'} ${offer?.is_active === false ? 'disabled' : ''} /> Активно</label>` : ''}
      <label>Порядок сортировки<input class="partner-input-compact" name="sort_order" type="number" value="${escapeHtml(offer?.sort_order || 0)}" /></label>
      <div class="admin-form-actions">
        <button type="submit">${isEdit ? 'Сохранить услугу' : 'Добавить услугу'}</button>
        ${isEdit ? '<button class="admin-inline-action ui-button ui-button--ghost" type="button" data-partner-offer-edit-cancel>Отмена</button>' : ''}
      </div>
      <p class="form-message" data-partner-form-message="${isEdit ? 'offerEdit' : 'offer'}">${escapeHtml(partnerState.formMessages[isEdit ? 'offerEdit' : 'offer'] || '')}</p>
    </form>
  `;
};

const renderPartnerOffersTab = () => `
  <div class="partner-cabinet-offers">
    <div class="admin-section-heading text-stack"><p class="section-eyebrow section-kicker">Услуги</p><h4 class="section-title">Предложения и привилегии</h4><p class="section-description compact-copy">Короткая выгода и условия для клиенток</p></div>
    ${partnerState.offers.length ? `
    <div class="offer-card-grid">
      ${partnerState.offers.map((offer) => renderOfferMarketplaceCard(offer, {
        layout: 'partner-cabinet',
        note: offer.is_active ? 'Preview для клиента' : 'Ожидает активации.',
        actionHtml: `${renderPartnerOfferAction(offer)}<button type="button" disabled>Получить привилегию</button>`,
      })).join('')}
    </div>
    ${renderTable(
      ['Название', 'Краткая выгода', 'Описание', 'Условия', 'Обычная цена', 'Цена участницы', 'Активно', 'Порядок сортировки', 'Действие'],
      partnerState.offers.map((offer) => [
        formatValue(offer.title),
        formatValue(formatPartnerBenefit(offer)),
        formatValue(offer.description),
        formatValue(offer.conditions),
        formatValue(getOfferPricingView(offer).basePriceLabel || '—'),
        formatValue(getOfferPricingView(offer).memberPriceLabel || '—'),
        renderPartnerReviewStatusBadge(offer.is_active),
        formatValue(offer.sort_order),
        renderPartnerOfferAction(offer),
      ]),
      true,
    )}
  ` : renderPartnerEmptyState('Пока нет предложений.', 'Добавьте первое предложение, чтобы клиент мог получить привилегию.')}
    ${renderPartnerOfferForm()}
  </div>
`;

const renderPartnerGalleryTab = () => {
  const offers = Array.isArray(partnerState.offers) ? partnerState.offers : [];
  const selectedOfferId = String(partnerState.selectedOfferIdForGallery || '');
  const offerPhotos = selectedOfferId ? (partnerState.offerPhotosByOfferId[selectedOfferId] || []) : [];
  return `
    <div class="stack">
      <div class="admin-section-heading text-stack"><p class="section-eyebrow section-kicker">Галерея</p><h4 class="section-title">Управление галереей</h4><p class="section-description compact-copy">Разделите фото карточки партнёра и фото работ по услугам.</p></div>
      <section class="panel-card">${renderPartnerGallery(partnerState.profile || {}, partnerState.photos, 'partner')}</section>
      <section class="panel-card">
        <h4 class="section-title">Фото работ по услугам</h4>
        <p class="section-description compact-copy">Выберите услугу и добавьте фотографии работ. Клиент увидит их по кнопке «Фото работ».</p>
        ${!offers.length ? '<p class="helper-text">Сначала создайте услугу, затем добавьте к ней фотографии работ.</p>' : `
          <label class="field"><span>Выберите услугу</span><select data-partner-offer-gallery-select>${offers.map((offer) => `<option value="${escapeHtml(offer.id)}" ${String(offer.id) === selectedOfferId ? 'selected' : ''}>${escapeHtml(offer.title || `Услуга #${offer.id}`)}</option>`).join('')}</select></label>
          <p class="helper-text compact-copy">Выберите услугу, к которой хотите добавить фотографии работ.</p>
          <label class="field"><span>Добавить фото</span><input type="file" accept="image/*" data-partner-offer-photo-upload data-offer-id="${escapeHtml(selectedOfferId)}" ${selectedOfferId ? '' : 'disabled'}></label>
          <p class="form-message" data-partner-form-message="offerPhoto">${escapeHtml(partnerState.formMessages.offerPhoto || '')}</p>
          ${offerPhotos.length ? `<div class="partner-gallery-grid">${offerPhotos.map((photo) => `<article class="partner-gallery-item partner-gallery-card ${photo.is_active ? '' : 'is-muted'}">
            ${photo.url ? `<div class="partner-gallery-media" role="img" aria-label="${escapeHtml(photo.alt_text || 'Фото услуги')}"><div class="partner-gallery-media__bg" style="background-image: url('${escapeHtml(photo.url)}')"></div><img class="partner-gallery-media__img" src="${escapeHtml(photo.url)}" alt="${escapeHtml(photo.alt_text || 'Фото услуги')}" loading="lazy"></div>` : '<div class="partner-gallery-media partner-gallery-empty">Фото скрыто</div>'}
            <form class="partner-gallery-actions ui-card-actions ui-action-row ui-action-row--stack-mobile" data-partner-offer-photo-form data-offer-id="${escapeHtml(selectedOfferId)}" data-photo-id="${escapeHtml(photo.id)}">
              <div class="partner-gallery-row"><span class="status-badge ${photo.is_active ? 'status-badge--success' : 'status-badge--warning'}">${photo.is_active ? 'Показывается' : 'Скрыто'}</span></div>
              <input type="hidden" name="is_active" value="${photo.is_active ? 'true' : 'false'}">
              <div class="partner-gallery-controls-row">
                <label class="partner-gallery-order"><span>Порядок</span><input type="number" name="sort_order" value="${escapeHtml(photo.sort_order ?? 0)}"></label>
                <button class="admin-inline-action ui-button ui-button--primary admin-inline-action--primary" type="submit">Сохранить</button>
                <button class="admin-inline-action ui-button ui-button--secondary admin-inline-action--secondary" type="button" data-partner-offer-photo-visibility="${escapeHtml(photo.id)}" data-offer-id="${escapeHtml(selectedOfferId)}" data-next-active="${photo.is_active ? 'false' : 'true'}">${photo.is_active ? 'Скрыть' : 'Показать'}</button>
                <button class="admin-inline-action ui-button ui-button--danger admin-inline-action--danger" type="button" data-partner-offer-photo-delete="${escapeHtml(photo.id)}" data-offer-id="${escapeHtml(selectedOfferId)}">Удалить</button>
              </div>
            </form>
          </article>`).join('')}</div>` : '<div class="partner-gallery-empty partner-empty-state compact-copy"><strong>Фото пока не добавлены.</strong><span>Загрузите первое фото, чтобы клиенты увидели ваши работы.</span></div>'}
        `}
      </section>
    </div>
  `;
};

const renderPartnerQrTab = () => `
  <div class="admin-section-heading"><h4>QR / лиды</h4><p>QR-ссылки создаёт администратор. Партнёр видит ссылки и статистику переходов.</p></div>
  ${partnerState.qrLinks.length ? renderTable(
    ['Код ссылки', 'QR-ссылка', 'Целевая ссылка', 'Deep-link payload', 'Активна'],
    partnerState.qrLinks.map((link) => [
      formatValue(link.slug),
      link.qr_url ? `<a href="${escapeHtml(link.qr_url)}" target="_blank" rel="noreferrer">${escapeHtml(link.qr_url)}</a>` : '—',
      link.target_url ? `<a href="${escapeHtml(link.target_url)}" target="_blank" rel="noreferrer">${escapeHtml(link.target_url)}</a>` : '—',
      formatValue(link.deep_link_payload),
      renderActiveStatusFeminineBadge(link.is_active),
    ]),
    true,
  ) : renderPartnerEmptyState('Пока нет QR-ссылок.', 'Создайте QR-ссылку, чтобы отслеживать переходы от клиентов.')}
  <h4 class="table-title">Лиды</h4>
  ${partnerState.leads.length ? renderTable(
    ['Код ссылки', 'Лиды / переходы'],
    partnerState.leads.map((lead) => [formatValue(lead.qr_slug), formatValue(lead.total_clicks)]),
    true,
  ) : renderPartnerEmptyState('Пока нет лидов.', 'Когда клиенты перейдут по QR-ссылке, они появятся здесь.')}
`;

const renderPartnerVerificationAction = (verification) => verification.status === 'active'
  ? `<button class="admin-inline-action ui-button ui-button--secondary" type="button" data-partner-confirm-verification="${escapeHtml(verification.id)}">Подтвердить привилегию</button>`
  : '';

const renderPartnerConfirmationCard = (item) => `
  <article class="partner-confirmation-card" data-partner-confirmation-card>
    <div class="client-card-topline">
      ${renderStatusBadge(formatPrivilegeStatus(item.status))}
      <span>${escapeHtml(formatDate(item.created_at) || 'Новый код')}</span>
    </div>
    <h4>${formatValue(item.offer_title || 'Клубная привилегия')}</h4>
    <p>Партнёр: <strong>${formatValue(item.partner_name)}</strong></p>
    <div class="privilege-code privilege-code--card" aria-label="Код клиента">${formatValue(item.code)}</div>
    <dl class="client-card-details">
      <div><dt>Клиент</dt><dd>${formatValue(item.client_name || 'Клиент клуба')}</dd></div>
      <div><dt>Истекает</dt><dd>${formatValue(formatDate(item.expires_at))}</dd></div>
      <div><dt>Подтверждено</dt><dd>${formatValue(formatDate(item.confirmed_at))}</dd></div>
    </dl>
    ${renderPartnerVerificationAction(item) ? `<div class="client-card-actions ui-card-actions ui-action-row ui-action-row--stack-mobile">${renderPartnerVerificationAction(item)}</div>` : ''}
  </article>
`;

const renderPartnerVerificationsTab = () => `
  <div class="admin-section-heading"><h4>Подтверждения</h4><p>Подтверждайте активные клиентские коды до окончания срока действия.</p></div>
  ${partnerState.verifications.length
    ? `<div class="partner-confirmation-card-grid">${partnerState.verifications.map(renderPartnerConfirmationCard).join('')}</div>`
    : renderPartnerEmptyState('Пока нет подтверждений.', 'Когда клиент покажет код привилегии, подтверждение появится здесь.')}
`;

const renderPartnerAnalyticsTab = () => renderAnalyticsSection(partnerState.analytics, {
  title: 'Аналитика',
  loading: partnerState.analyticsLoading,
  error: partnerState.analyticsError,
});

const renderPartnerActivityTab = () => `
  <div class="admin-section-heading admin-page-heading">
    <p class="section-eyebrow section-kicker">Activity feed</p>
    <h4>Активность</h4>
    <p>Лента помогает быстро видеть, что происходит с клиентами, QR и привилегиями.</p>
  </div>
  ${renderActivityFeed(partnerState.activityItems, { loading: partnerState.activityLoading, error: partnerState.activityError })}
`;

const requestAdminMe = async () => {
  const me = await apiFetch('/api/v1/admin/me');
  adminState.legacyContentWriteEnabled = me?.legacy_content_write_enabled !== false;
  return me;
};

const buildAdminPaymentRequestsPath = (status = adminState.paymentRequestsStatusFilter) => {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  const query = params.toString();
  return `/api/v1/admin/payment-requests${query ? `?${query}` : ''}`;
};

const postJson = (path, payload) => apiFetch(path, {
  method: 'POST',
  body: JSON.stringify(payload),
});

const patchJson = (path, payload) => apiFetch(path, {
  method: 'PATCH',
  body: JSON.stringify(payload),
});

const deleteJson = (path) => apiFetch(path, {
  method: 'DELETE',
});

const loadAdminPaymentRequests = async (status = adminState.paymentRequestsStatusFilter) => {
  adminState.paymentRequestsLoading = true;
  adminState.paymentRequestsError = '';
  try {
    const data = await apiFetch(buildAdminPaymentRequestsPath(status));
    adminState.paymentRequests = Array.isArray(data) ? data : Array.isArray(data?.items) ? data.items : [];
    if (adminState.selectedPaymentRequest && !adminState.paymentRequests.some((request) => String(getPaymentRequestId(request)) === String(getPaymentRequestId(adminState.selectedPaymentRequest)))) {
      adminState.selectedPaymentRequest = null;
    }
  } catch (error) {
    adminState.paymentRequests = [];
    adminState.paymentRequestsError = error.message || 'Не удалось загрузить заявки на оплату.';
  } finally {
    adminState.paymentRequestsLoading = false;
  }
};

const loadAdminPaymentRequest = (id) => apiFetch(`/api/v1/admin/payment-requests/${id}`);

const approveAdminPaymentRequest = (id, accessDays) => postJson(`/api/v1/admin/payment-requests/${id}/approve`, {
  access_days: Number(accessDays) || 30,
});

const rejectAdminPaymentRequest = (id, comment = 'Отклонено администратором') => postJson(`/api/v1/admin/payment-requests/${id}/reject`, { comment });

const loadUsers = async () => {
  adminState.users = await apiFetch('/api/v1/admin/users');
};

const loadCities = async () => {
  adminState.cities = await apiFetch('/api/v1/admin/cities');
  if (adminState.selectedCityIdForEdit && !adminState.cities.some((city) => String(city.id) === String(adminState.selectedCityIdForEdit))) {
    adminState.selectedCityIdForEdit = '';
  }
};

const loadCategories = async () => {
  adminState.categories = await apiFetch('/api/v1/admin/categories');
  if (adminState.selectedCategoryIdForEdit && !adminState.categories.some((category) => String(category.id) === String(adminState.selectedCategoryIdForEdit))) {
    adminState.selectedCategoryIdForEdit = '';
  }
};

const loadPartners = async () => {
  adminState.partners = await apiFetch('/api/v1/admin/partners');
};

const loadAdminLandingSettings = async () => {
  adminState.landingSettings = await apiFetch('/api/v1/admin/landing-settings');
};

const loadAdminPartnerPhotos = async (partnerId) => {
  if (!partnerId) return;
  adminState.partnerPhotosByPartner[partnerId] = await apiFetch(`/api/v1/admin/partners/${partnerId}/photos`);
};

const loadAdminPartnerAnalytics = async (partnerId) => {
  if (!partnerId) return;
  adminState.partnerAnalyticsLoading = true;
  adminState.partnerAnalyticsError = '';
  adminState.selectedPartnerAnalytics = adminState.partnerAnalyticsById[partnerId] || null;
  try {
    const analytics = await apiFetch(`/api/v1/admin/partners/${partnerId}/analytics`);
    adminState.partnerAnalyticsById[partnerId] = analytics;
    adminState.selectedPartnerAnalytics = analytics;
  } catch (error) {
    adminState.partnerAnalyticsError = error.message || 'Не удалось загрузить аналитику партнёра.';
  } finally {
    adminState.partnerAnalyticsLoading = false;
  }
};

const loadLeads = async () => {
  adminState.leads = await apiFetch('/api/v1/admin/leads/partners');
};

const loadVerifications = async () => {
  adminState.verifications = await apiFetch('/api/v1/admin/verifications');
};

const buildAdminActivityPath = () => {
  const params = new URLSearchParams();
  if (adminState.activityEventType) params.set('event_type', adminState.activityEventType);
  if (adminState.selectedPartnerIdForActivity) params.set('partner_id', adminState.selectedPartnerIdForActivity);
  params.set('limit', '50');
  return `/api/v1/admin/activity?${params.toString()}`;
};

const loadAdminActivity = async () => {
  adminState.activityLoading = true;
  adminState.activityError = '';
  try {
    const data = await apiFetch(buildAdminActivityPath());
    adminState.activityItems = Array.isArray(data?.items) ? data.items : [];
  } catch (error) {
    if (!getToken()) throw error;
    adminState.activityError = error.message || 'Не удалось загрузить события.';
  } finally {
    adminState.activityLoading = false;
  }
};

const loadOffers = async () => {
  if (!adminState.selectedPartnerIdForOffers) {
    adminState.offers = [];
    adminState.selectedOfferIdForEdit = '';
    return;
  }
  adminState.offers = await apiFetch(`/api/v1/admin/partners/${adminState.selectedPartnerIdForOffers}/offers`);
  if (adminState.selectedOfferIdForEdit && !adminState.offers.some((offer) => String(offer.id) === String(adminState.selectedOfferIdForEdit))) {
    adminState.selectedOfferIdForEdit = '';
  }
};

const loadContentReview = async () => {
  const data = await apiFetch('/api/v1/admin/content-review');
  adminState.contentReview = {
    offers: Array.isArray(data?.offers) ? data.offers : [],
    photos: Array.isArray(data?.photos) ? data.photos : [],
  };
};

const loadQrLinks = async () => {
  if (!adminState.selectedPartnerIdForQr) {
    adminState.qrLinks = [];
    adminState.selectedQrLinkIdForEdit = '';
    return;
  }
  adminState.qrLinks = await apiFetch(`/api/v1/admin/partners/${adminState.selectedPartnerIdForQr}/qr-links`);
  if (adminState.selectedQrLinkIdForEdit && !adminState.qrLinks.some((link) => String(link.id) === String(adminState.selectedQrLinkIdForEdit))) {
    adminState.selectedQrLinkIdForEdit = '';
  }
};

const legacyContentReadOnlyMessage = 'Редактирование контента перенесено в Telegram Admin Bot. Этот раздел доступен только для просмотра.';
const isLegacyContentReadOnly = () => adminState.legacyContentWriteEnabled === false;
const legacyContentDisabledAttr = () => isLegacyContentReadOnly() ? ` disabled title="${escapeHtml(legacyContentReadOnlyMessage)}" aria-disabled="true"` : '';
const renderLegacyContentNotice = () => isLegacyContentReadOnly() ? `<div class="admin-readonly-notice" role="status"><strong>Read-only режим</strong><span>${escapeHtml(legacyContentReadOnlyMessage)}</span></div>` : '';
const guardLegacyContentWrite = () => {
  if (!isLegacyContentReadOnly()) return false;
  setPanelMessage(legacyContentReadOnlyMessage, 'info');
  renderAdminLayout();
  return true;
};

const ensureAdminDictionaries = async () => {
  await Promise.all([
    adminState.users.length ? Promise.resolve() : loadUsers(),
    adminState.cities.length ? Promise.resolve() : loadCities(),
    adminState.categories.length ? Promise.resolve() : loadCategories(),
    adminState.partners.length ? Promise.resolve() : loadPartners(),
  ]);
};

const renderAdminLayout = () => {
  renderDashboardApp('admin');
  const content = renderAdminTabContent();
  adminDashboard.innerHTML = `
    ${adminState.panelMessage}
    ${['overview', 'cities', 'categories', 'partners', 'offers', 'contentReview'].includes(adminState.activeTab) ? renderLegacyContentNotice() : ''}
    <section class="admin-tab-panel">${content}</section>
  `;
  if (isLegacyContentReadOnly()) {
    adminDashboard.querySelectorAll('[data-legacy-content-form] input, [data-legacy-content-form] textarea, [data-legacy-content-form] select, [data-legacy-content-form] button[type=\"submit\"]').forEach((el) => { el.disabled = true; });
  }
};

const renderAdminTabContent = () => {
  switch (adminState.activeTab) {
    case 'users':
      return renderUsersTab();
    case 'cities':
      return renderCitiesTab();
    case 'categories':
      return renderCategoriesTab();
    case 'partners':
      return renderPartnersTab();
    case 'offers':
      return renderOffersTab();
    case 'contentReview':
      return renderContentReviewTab();
    case 'paymentRequests':
      return renderAdminPaymentRequestsTab();
    case 'payments':
      return renderAcquiringPaymentsTab();
    case 'qr':
      return renderQrTab();
    case 'verifications':
      return renderVerificationsTab();
    case 'partnerAccess':
      return renderPartnerAccessTab();
    case 'activity':
      return renderAdminActivityTab();
    case 'giveaways':
      return renderGiveawaysTab();
    case 'flower':
      return renderFlowerAdminTab();
    default:
      return renderOverviewTab();
  }
};


const loadGiveaways = async () => {
  adminState.giveaways = await apiFetch('/api/v1/admin/giveaways');
};

const loadAcquiringPayments = async () => {
  const query = adminState.acquiringPaymentStatusFilter ? `?status=${encodeURIComponent(adminState.acquiringPaymentStatusFilter)}` : '';
  adminState.acquiringPayments = await apiFetch(`/api/v1/admin/payments${query}`);
};

const loadSubscriptionPlans = async () => {
  adminState.subscriptionPlans = await apiFetch('/api/v1/admin/subscription-plans');
};

const renderAcquiringPaymentsTab = () => {
  const rows = adminState.acquiringPayments.map((item) => [
    formatDate(item.created_at),
    `${escapeHtml(item.client_name || `Клиент #${item.client_profile_id}`)}<br><small>${item.telegram_user_id ? `TG ${escapeHtml(item.telegram_user_id)}` : ''} ${item.vk_user_id ? `VK ${escapeHtml(item.vk_user_id)}` : ''}</small>`,
    escapeHtml(item.plan_name),
    `${formatValue(item.amount)} ${escapeHtml(item.currency)}`,
    `<strong>${escapeHtml(item.status)}</strong><br><small>${escapeHtml(item.provider_status || '—')}</small>`,
    escapeHtml(item.payment_method || '—'),
    `<small>${escapeHtml(item.provider_operation_id || '—')}<br>${escapeHtml(item.payment_link_id)}</small>`,
    item.paid_at ? formatDate(item.paid_at) : '—',
    item.subscription_id ? `#${formatValue(item.subscription_id)}` : '—',
    `<button type="button" class="ui-button ui-button--secondary" data-payment-details="${escapeHtml(item.id)}">История</button><button type="button" class="ui-button ui-button--secondary" data-payment-sync="${escapeHtml(item.id)}">Проверить статус</button><form class="admin-form admin-form--inline" data-admin-form="paymentRefund"><input type="hidden" name="payment_id" value="${escapeHtml(item.id)}"><input name="amount" type="number" min="0.01" step="0.01" max="${escapeHtml(Number(item.amount) - Number(item.refunded_amount || 0))}" placeholder="Сумма" required><input name="reason" minlength="3" placeholder="Причина возврата" required><button type="submit" ${['approved','partially_refunded'].includes(item.status) ? '' : 'disabled'}>Вернуть</button></form>`,
  ]);
  const planCards = adminState.subscriptionPlans.map((plan) => `
    <form class="admin-form admin-form--inline ui-card" data-admin-form="subscriptionPlanPrice">
      <input type="hidden" name="plan_id" value="${escapeHtml(plan.id)}">
      <div>
        <p class="section-eyebrow section-kicker">Тариф подписки</p>
        <h4>${escapeHtml(plan.name)}</h4>
        <p>${escapeHtml(plan.duration_days)} дней · ${plan.is_active ? 'активен' : 'неактивен'}</p>
      </div>
      <label>Цена, ₽
        <input name="price" type="number" min="0.01" max="1000000" step="0.01" value="${escapeHtml(Number(plan.price).toFixed(2))}" required>
      </label>
      <button type="submit">Сохранить цену</button>
      <p class="form-message" data-form-message="subscriptionPlanPrice">${escapeHtml(adminState.formMessages.subscriptionPlanPrice || '')}</p>
    </form>
  `).join('');
  const planSettingsHtml = `<section class="stack"><div class="admin-section-heading"><div><h4>Стоимость подписки</h4><p>Новая цена применяется только к новым платежам. Уже созданные платежи сохраняют прежнюю сумму.</p></div></div>${planCards || '<p>Тарифы пока не созданы.</p>'}</section>`;
  const detail = adminState.selectedAcquiringPayment;
  const detailHtml = detail ? `<section class="ui-card"><div class="admin-section-heading"><h4>История платежа #${escapeHtml(detail.payment.id)}</h4><p>${escapeHtml(detail.payment.public_id)}</p></div>${renderTable(['Источник','Событие','Статус Точки','Обработка','Получено'], (detail.events || []).map((event) => [escapeHtml(event.source), escapeHtml(event.event_type), escapeHtml(event.provider_status || '—'), `${escapeHtml(event.processing_status)}${event.processing_error ? `<br><small>${escapeHtml(event.processing_error)}</small>` : ''}`, formatDate(event.received_at)]), true, '', 'Событий пока нет.')}</section>` : '';
  return `<div class="stack"><div class="admin-section-heading admin-page-heading"><div><p class="section-eyebrow section-kicker">Точка Банк</p><h3>Платежи</h3><p>Эквайринг, статусы, связанные подписки и возвраты.</p></div><label>Статус<select data-acquiring-payment-status><option value="">Все</option>${['created','pending','authorized','approved','failed','expired','refund_pending','partially_refunded','refunded','cancelled'].map((value) => `<option value="${value}" ${adminState.acquiringPaymentStatusFilter === value ? 'selected' : ''}>${value}</option>`).join('')}</select></label></div>${planSettingsHtml}${renderTable(['Дата','Пользователь','Тариф','Сумма','Статус','Способ','Operation / Link ID','Оплата','Подписка','Действия'], rows, true, '', 'Платежей пока нет.')}${detailHtml}</div>`;
};

const loadPartnerAccesses = async () => {
  adminState.partnerAccesses = await apiFetch('/api/v1/admin/partner-accesses');
};

const loadFlowerTasks = async () => {
  adminState.flowerTasks = await apiFetch('/api/v1/admin/flower/tasks');
};

const loadFlowerGarden = async () => {
  const [settings, specialTasks] = await Promise.all([
    apiFetch('/api/v1/admin/flower/settings'),
    apiFetch('/api/v1/admin/flower/special-tasks'),
  ]);
  adminState.flowerSettings = settings;
  adminState.flowerSpecialTasks = specialTasks;
};

const renderPartnerAccessTab = () => {
  const rows = filterAdminRows(adminState.partnerAccesses, adminState.search.partnerAccesses, ['display_name', 'partner_name', 'provider', 'provider_user_id', 'username']);
  return `<div class="partner-access-page stack">
    <div class="admin-section-heading admin-page-heading"><p class="section-eyebrow section-kicker">Боты партнёров</p><h3>Партнёрский доступ</h3><p>Добавьте постоянный Telegram или VK ID сотрудника. Ник используется только как подпись и не даёт доступ.</p></div>
    <form class="admin-form admin-form--inline ui-card" data-admin-form="partnerAccess">
      <h4>Добавить сотрудника партнёра</h4>
      <label>Партнёр${renderPartnerPicker('partnerAccess', '')}</label>
      <label>Бот<select name="provider" required><option value="vk">VK</option><option value="telegram">Telegram</option></select></label>
      <label>Постоянный ID<input name="provider_user_id" required placeholder="Например, 123456789" /></label>
      <label>Имя сотрудника<input name="display_name" required placeholder="Например, Анна · кассир" /></label>
      <label>Ник, необязательно<input name="username" placeholder="Например, anna_shop" /></label>
      <button type="submit">Добавить доступ</button><p class="form-message" data-form-message="partnerAccess">${escapeHtml(adminState.formMessages.partnerAccess || '')}</p>
    </form>
    <section class="ui-card"><div class="admin-section-heading"><h4>Сотрудники</h4><p>Доступ можно выключить без удаления истории активаций.</p></div>${renderAdminSearch('partnerAccesses', 'Поиск по сотрудникам и партнёрам')}
      ${renderTable(['Сотрудник', 'Партнёр', 'Бот', 'Постоянный ID', 'Активаций', 'Последняя активность', 'Доступ'], rows.map((item) => [formatValue(item.display_name), formatValue(item.partner_name), item.provider === 'telegram' ? 'Telegram' : 'VK', formatValue(item.provider_user_id), formatValue(item.activation_count), formatValue(formatDate(item.last_activity_at)), `<button class="admin-inline-action ui-button ${item.is_active ? 'ui-button--danger' : 'ui-button--secondary'}" type="button" data-partner-access-toggle="${escapeHtml(item.id)}" data-next-active="${item.is_active ? 'false' : 'true'}">${item.is_active ? 'Отключить' : 'Включить'}</button>`]), true, '', 'Сотрудники пока не добавлены.')}
    </section>
  </div>`;
};

const bloomPositionLabels = { top_left: 'Сверху слева', top_right: 'Сверху справа', middle_left: 'По центру слева', middle_right: 'По центру справа', bottom_left: 'Снизу слева', bottom_right: 'Снизу справа' };

const renderBloomCalendar = () => {
  const [year, month] = adminState.flowerCalendarMonth.split('-').map(Number);
  const first = new Date(Date.UTC(year, month - 1, 1));
  const days = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const offset = (first.getUTCDay() + 6) % 7;
  const cells = Array.from({ length: offset }, () => '<span class="bloom-calendar__day is-empty"></span>');
  for (let day = 1; day <= days; day += 1) {
    const iso = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const tasks = adminState.flowerSpecialTasks.filter((task) => task.starts_on <= iso && task.ends_on >= iso);
    cells.push(`<span class="bloom-calendar__day"><strong>${day}</strong>${tasks.map((task) => `<small title="${escapeHtml(task.title)}">${escapeHtml(task.title)}</small>`).join('')}</span>`);
  }
  return `<div class="bloom-calendar"><div class="bloom-calendar__weekdays">${['Пн','Вт','Ср','Чт','Пт','Сб','Вс'].map((day) => `<b>${day}</b>`).join('')}</div><div class="bloom-calendar__grid">${cells.join('')}</div></div>`;
};

const bloomChartColors = ['#d46b9c', '#8b74c7', '#72a88b', '#e2a75f', '#6e9fc7', '#cf7a70'];
const renderBloomAnalytics = () => {
  const data = adminState.flowerAnalytics;
  if (!data) return '';
  const questions = data.questions.map((question) => {
    let cursor = 0;
    const stops = question.options.map((option, index) => { const start = cursor; cursor += Number(option.percent || 0); return `${bloomChartColors[index % bloomChartColors.length]} ${start}% ${cursor}%`; });
    return `<article class="bloom-analytics__question"><h5>${escapeHtml(question.prompt)}</h5><div class="bloom-chart-row"><div class="bloom-pie" style="background:conic-gradient(${stops.length ? stops.join(',') : '#eee 0 100%'})" role="img" aria-label="Распределение ответов"></div><ul>${question.options.map((option, index) => `<li><i style="background:${bloomChartColors[index % bloomChartColors.length]}"></i><span>${escapeHtml(option.label)}</span><strong>${formatValue(option.percent)}% · ${formatValue(option.count)}</strong></li>`).join('')}</ul></div></article>`;
  }).join('');
  const rows = data.submissions.map((item) => [
    `#${formatValue(item.client_id)}`,
    [item.full_name, item.email, item.phone, item.telegram_username ? `TG: @${item.telegram_username}` : '', item.vk_username ? `VK: ${item.vk_username}` : ''].filter(Boolean).map(escapeHtml).join('<br>') || '—',
    formatDate(item.completed_at),
    item.answers.map(escapeHtml).join('<br>'),
  ]);
  return `<section class="ui-card bloom-analytics"><div class="admin-section-heading"><h4>Ответы: ${escapeHtml(data.title)}</h4><p>Заполнили: ${formatValue(data.submissions_count)}</p></div>${questions}${renderTable(['ID', 'Участница и контакты', 'Дата', 'Ответы'], rows, true, '', 'Ответов пока нет.')}</section>`;
};

const renderFlowerAdminTab = () => {
  const settings = adminState.flowerSettings || {};
  const clientUsers = adminState.users.filter((item) => item.role === 'client');
  const clientOptions = clientUsers.map((item) => {
    const contact = item.phone || item.contact_email || item.email || '';
    const label = [item.display_name || item.full_name || `Пользователь #${item.id}`, contact, `ID ${item.id}`].filter(Boolean).join(' · ');
    return `<option value="${escapeHtml(item.id)}">${escapeHtml(label)}</option>`;
  }).join('');
  const taskCards = adminState.flowerSpecialTasks.map((task) => `<article class="ui-card bloom-survey-card">
    <div class="admin-section-heading"><div><h4>${escapeHtml(task.title)}</h4><p>${formatDate(task.starts_on)} — ${formatDate(task.ends_on)} · +${formatValue(task.petals)} лепестков · ответов: ${formatValue(task.submissions_count)}</p></div><div class="admin-inline-actions"><button class="admin-inline-action ui-button ${task.is_active ? 'ui-button--danger' : 'ui-button--secondary'}" type="button" data-special-task-toggle="${escapeHtml(task.id)}" data-next-active="${task.is_active ? 'false' : 'true'}">${task.is_active ? 'Остановить' : 'Запустить'}</button><button class="admin-inline-action ui-button ui-button--danger admin-inline-action--danger" type="button" data-special-task-delete="${escapeHtml(task.id)}" data-task-title="${escapeHtml(task.title)}" data-submissions-count="${escapeHtml(task.submissions_count)}">Удалить</button></div></div>
    ${task.description ? `<p>${escapeHtml(task.description)}</p>` : ''}
    <ol class="bloom-question-list">${task.questions.map((question) => `<li><strong>${escapeHtml(question.prompt)}</strong><small>${question.options.map((option) => escapeHtml(option.label)).join(' · ')}</small></li>`).join('') || '<li>Добавьте первый вопрос.</li>'}</ol>
    <form class="admin-form admin-form--inline bloom-question-form" data-admin-form="flowerSpecialQuestion"><input type="hidden" name="task_id" value="${escapeHtml(task.id)}"><label>Новый вопрос<input name="prompt" required placeholder="Текст вопроса"></label><label>Варианты ответа<textarea name="options" rows="3" required placeholder="Каждый вариант с новой строки"></textarea></label><button type="submit">Добавить вопрос</button></form>
    <button type="button" class="ui-button ui-button--secondary" data-special-task-analytics="${escapeHtml(task.id)}">Показать ответы и графики</button>
  </article>`).join('');
  return `<div class="flower-admin-page stack">
    <div class="admin-section-heading admin-page-heading"><p class="section-eyebrow section-kicker">Ежедневная и недельная активность</p><h3>Сад Bloom</h3><p>Здесь настраивается игровой лепесток и специальные опросники. Эти настройки, календарь и ответы видны только администраторам.</p></div>
    <form class="admin-form admin-form--inline ui-card" data-admin-form="flowerPetalAward"><h4>Начислить лепестки участнице</h4><p class="helper-text">Ручное начисление сразу попадёт в цветок и рейтинг текущего месяца. Операция сохранится в истории вместе с причиной.</p><label>Участница<select name="user_id" required><option value="">Выберите участницу</option>${clientOptions}</select></label><label>Количество<input name="petals" type="number" min="1" max="1000" value="1" required></label><label>Причина<textarea name="note" rows="2" minlength="2" maxlength="1000" required placeholder="Например, победа в активности клуба"></textarea></label><button type="submit" ${clientUsers.length ? '' : 'disabled'}>Начислить</button><p class="form-message" data-form-message="flowerPetalAward">${escapeHtml(adminState.formMessages.flowerPetalAward || '')}</p></form>
    <form class="admin-form admin-form--inline ui-card" data-admin-form="flowerPetalRevoke"><h4>Забрать лепестки у участницы</h4><p class="helper-text">Списание уменьшит цветок и рейтинг текущего месяца. Баланс не может стать отрицательным, причина сохранится в истории.</p><label>Участница<select name="user_id" required><option value="">Выберите участницу</option>${clientOptions}</select></label><label>Количество<input name="petals" type="number" min="1" max="1000" value="1" required></label><label>Причина<textarea name="note" rows="2" minlength="2" maxlength="1000" required placeholder="Например, ошибочное начисление"></textarea></label><button class="ui-button ui-button--danger" type="submit" ${clientUsers.length ? '' : 'disabled'}>Забрать</button><p class="form-message" data-form-message="flowerPetalRevoke">${escapeHtml(adminState.formMessages.flowerPetalRevoke || '')}</p></form>
    <form class="admin-form admin-form--inline ui-card" data-admin-form="flowerGardenSettings"><h4>Задание дня — найти лепесток</h4><p class="helper-text">Участница находит лепесток в карточке сада и нажимает на него один раз в день.</p><label>Размещение<select name="placement_mode"><option value="random" ${settings.placement_mode === 'random' ? 'selected' : ''}>Случайное каждый день</option><option value="manual" ${settings.placement_mode === 'manual' ? 'selected' : ''}>Выбранное администратором</option></select></label><label>Место<select name="manual_position">${Object.entries(bloomPositionLabels).map(([value,label]) => `<option value="${value}" ${settings.manual_position === value ? 'selected' : ''}>${label}</option>`).join('')}</select></label><label>Лепестков за находку<input name="daily_petals" type="number" min="1" max="20" value="${escapeHtml(settings.daily_petals || 1)}"></label><button type="submit">Сохранить</button></form>
    <form class="admin-form admin-form--inline ui-card" data-admin-form="flowerSpecialTask"><h4>Новое специальное задание клуба</h4><label>Название<input name="title" required placeholder="Опрос недели"></label><label>Описание<textarea name="description" rows="2"></textarea></label><label>Лепестки<input name="petals" type="number" min="1" max="100" value="5" required></label><label>Начало недели<input name="starts_on" type="date" required></label><label>Окончание<input name="ends_on" type="date" required></label><button type="submit">Создать опросник</button></form>
    <section class="ui-card"><div class="admin-section-heading"><div><h4>Календарь опросников</h4><p>По дням видно, в какую неделю действовал каждый опросник.</p></div><label>Месяц<input type="month" value="${escapeHtml(adminState.flowerCalendarMonth)}" data-bloom-calendar-month></label></div>${renderBloomCalendar()}</section>
    <section class="stack"><div class="admin-section-heading"><h4>Специальные задания</h4><p>Кнопка появляется у участниц только в указанный период и после добавления вопросов.</p></div>${taskCards || '<div class="ui-card"><p>Опросников пока нет.</p></div>'}</section>
    ${renderBloomAnalytics()}
    <form class="admin-form admin-form--inline ui-card" data-admin-form="flowerSettle"><h4>Подвести итоги месяца</h4><p class="helper-text">При равном количестве лепестков участницы делят место; на границе топ-10 проводится фиксируемая системная жеребьёвка.</p><label>Месяц<input name="month" type="month" required /></label><label>Розыгрыш<select name="giveaway_id" required><option value="">Выберите розыгрыш</option>${adminState.giveaways.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(getGiveawayTitle(item))}</option>`).join('')}</select></label><button type="submit">Начислить номерки топ-10</button><p class="form-message" data-form-message="flowerSettle">${escapeHtml(adminState.formMessages.flowerSettle || '')}</p></form>
  </div>`;
};

const getGiveawayTitle = (giveaway = {}) => giveaway.title || `Розыгрыш #${giveaway.id}`;

const resolveGiveawayForEntries = () => {
  const giveaways = Array.isArray(adminState.giveaways) ? adminState.giveaways : [];
  const editing = giveaways.find((item) => String(item.id) === String(adminState.selectedGiveawayIdForEdit));
  if (editing) return { giveaway: editing, source: 'editing' };

  const manual = giveaways.find((item) => String(item.id) === String(adminState.selectedGiveawayIdForEntriesManual));
  if (manual) return { giveaway: manual, source: 'manual' };

  const active = giveaways.find((item) => item.is_active);
  if (active) return { giveaway: active, source: 'active' };

  if (giveaways.length === 1) return { giveaway: giveaways[0], source: 'single' };

  return { giveaway: null, source: 'manual' };
};

const logSelectedGiveawayForEntries = ({ giveaway, source }) => {
  console.info('[BLOOM_ADMIN_GIVEAWAY_ENTRIES] selected giveaway', {
    source,
    giveawayId: giveaway?.id || null,
  });
};

const syncGiveawayEntriesSelection = async ({ force = false } = {}) => {
  const selection = resolveGiveawayForEntries();
  const selectedId = selection.giveaway?.id ? String(selection.giveaway.id) : '';
  const previousId = String(adminState.selectedGiveawayIdForEntries || '');
  adminState.selectedGiveawayIdForEntries = selectedId;
  logSelectedGiveawayForEntries(selection);

  if (!selectedId) {
    adminState.giveawayEntries = null;
    adminState.giveawayEntriesLoading = false;
    return null;
  }

  if (!force && adminState.giveawayEntries && previousId === selectedId) {
    return adminState.giveawayEntries;
  }

  adminState.giveawayEntries = null;
  adminState.giveawayRecheckResult = null;
  return loadGiveawayEntries(selectedId);
};

const getGiveawayExportFilename = (giveawayId, response) => {
  const disposition = response.headers.get('Content-Disposition') || '';
  const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
  const plainMatch = disposition.match(/filename=\"?([^\";]+)\"?/i);
  const rawFilename = utf8Match?.[1] || plainMatch?.[1] || `giveaway-${giveawayId}-entries.xlsx`;

  try {
    return decodeURIComponent(rawFilename).replace(/[\\/]/g, '-');
  } catch (error) {
    return rawFilename.replace(/[\\/]/g, '-');
  }
};

const downloadBlob = (blob, filename) => {
  const blobUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(blobUrl), 0);
};

const downloadGiveawayEntriesExcel = async (giveawayId) => {
  if (!giveawayId) return;
  const response = await apiFetchResponse(`/api/v1/admin/giveaways/${encodeURIComponent(giveawayId)}/entries/export.xlsx`, {
    headers: {
      Accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    },
    timeoutMs: 60000,
  });
  const blob = await response.blob();
  downloadBlob(blob, getGiveawayExportFilename(giveawayId, response));
};

const loadGiveawayEntries = async (giveawayId) => {
  if (!giveawayId) {
    adminState.giveawayEntries = null;
    adminState.giveawayEntriesLoading = false;
    return null;
  }
  const endpoint = `/api/v1/admin/giveaways/${giveawayId}/entries`;
  console.info('[BLOOM_ADMIN_GIVEAWAY_ENTRIES] request', { giveawayId, endpoint });
  adminState.giveawayEntriesLoading = true;
  let responseStatus = 'error';
  try {
    const headers = new Headers();
    const token = getToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    const response = await fetch(endpoint, { cache: 'no-store', headers });
    responseStatus = response.status;
    if (response.status === 401 || response.status === 403) {
      clearToken();
      showLoginForm();
      throw new Error('Сессия истекла. Войдите снова.');
    }
    if (!response.ok) {
      throw new Error(await buildErrorMessage(response));
    }
    const data = response.status === 204 ? null : await response.json();
    const rowsCount = Array.isArray(data?.items) ? data.items.length : 0;
    const summary = data?.summary || {};
    console.info('[BLOOM_ADMIN_GIVEAWAY_ENTRIES] response', {
      status: responseStatus,
      rowsCount,
      total: summary.total_numbers || 0,
      active: summary.active_numbers || 0,
      uniqueParticipants: summary.unique_participants || 0,
    });
    adminState.giveawayEntries = data;
    return data;
  } catch (error) {
    console.info('[BLOOM_ADMIN_GIVEAWAY_ENTRIES] response', {
      status: responseStatus,
      rowsCount: 0,
      total: 0,
      active: 0,
      uniqueParticipants: 0,
    });
    throw error;
  } finally {
    adminState.giveawayEntriesLoading = false;
  }
};

const renderGiveawayPlaceRows = (giveaway = {}) => {
  const count = Number(giveaway.winners_count || 1);
  const prizes = Array.isArray(giveaway.prizes) ? giveaway.prizes : [];
  return Array.from({ length: Math.max(0, count) }, (_, index) => {
    const place = prizes[index] || { place_number: index + 1 };
    return `<fieldset class="giveaway-prize-row" data-admin-giveaway-place-row>
      <legend>${index + 1}-е место</legend>
      <input name="place_number" type="hidden" value="${escapeHtml(place.place_number || index + 1)}" />
      <label>Приз<input name="prize_title" value="${escapeHtml(place.prize_title || '')}" /></label>
      <details class="giveaway-winner-details" ${place.winner_provider || place.winner_provider_user_id || place.winning_number ? 'open' : ''}>
        <summary>Заполнить победителя после розыгрыша</summary>
        <div class="admin-form-grid">
          <label>Платформа<select name="winner_provider"><option value="">Не выбран</option><option value="telegram" ${place.winner_provider === 'telegram' ? 'selected' : ''}>Telegram</option><option value="vk" ${place.winner_provider === 'vk' ? 'selected' : ''}>VK</option></select></label>
          <label>ID победителя<input name="winner_provider_user_id" value="${escapeHtml(place.winner_provider_user_id || '')}" /></label>
          <label>Победный номер<input name="winning_number" value="${escapeHtml(place.winning_number || '')}" /></label>
        </div>
      </details>
    </fieldset>`;
  }).join('');
};

const renderGiveawayForm = (giveaway = {}) => `<form class="admin-form admin-giveaway-form" data-admin-giveaway-form data-giveaway-id="${escapeHtml(giveaway.id || '')}">
  <section class="admin-form-section"><div class="admin-form-section-heading"><span>1</span><div><h4>Основное</h4><p>Название, описание и период проведения.</p></div></div>
    <label>Название<input name="title" value="${escapeHtml(giveaway.title || '')}" placeholder="Например, Тест2" required /></label>
    <label>Описание<textarea name="description" rows="3">${escapeHtml(giveaway.description || '')}</textarea></label>
    <div class="admin-form-grid"><label>Начало<input name="starts_at" type="datetime-local" value="${escapeHtml(String(giveaway.starts_at || '').slice(0, 16))}" /></label><label>Окончание<input name="ends_at" type="datetime-local" value="${escapeHtml(String(giveaway.ends_at || '').slice(0, 16))}" /></label><label>Количество победителей<input name="winners_count" type="number" min="0" max="100" value="${escapeHtml(giveaway.winners_count || 1)}" data-admin-giveaway-winners-count /></label></div>
  </section>
  <section class="admin-form-section"><div class="admin-form-section-heading"><span>2</span><div><h4>Призы</h4><p>Количество строк меняется вместе с количеством победителей.</p></div></div><div data-admin-giveaway-place-list>${renderGiveawayPlaceRows(giveaway)}</div></section>
  <details class="admin-form-section admin-giveaway-social" ${giveaway.telegram_reward_enabled || giveaway.vk_reward_enabled ? 'open' : ''}><summary>Дополнительные номера за подписки</summary><p class="helper-text">Откройте этот блок, только если хотите начислять номера за Telegram или VK.</p>
    <div class="admin-giveaway-social-grid"><fieldset><legend>Telegram</legend><label>Ссылка на канал<input name="telegram_community_url" value="${escapeHtml(giveaway.telegram_community_url || '')}" /></label><label>Chat ID<input name="telegram_chat_id" value="${escapeHtml(giveaway.telegram_chat_id || '')}" /></label><label class="checkbox-row"><input name="telegram_reward_enabled" type="checkbox" ${giveaway.telegram_reward_enabled ? 'checked' : ''} /> Начислять номер</label><input name="telegram_reward_numbers" type="hidden" value="1" /></fieldset><fieldset><legend>ВКонтакте</legend><label>Ссылка на сообщество<input name="vk_community_url" value="${escapeHtml(giveaway.vk_community_url || '')}" /></label><label>ID группы<input name="vk_group_id" value="${escapeHtml(giveaway.vk_group_id || '')}" /></label><label class="checkbox-row"><input name="vk_reward_enabled" type="checkbox" ${giveaway.vk_reward_enabled ? 'checked' : ''} /> Начислять номер</label><input name="vk_reward_numbers" type="hidden" value="1" /></fieldset></div>
  </details>
  <section class="admin-form-section admin-form-section--publish"><div class="admin-form-section-heading"><span>3</span><div><h4>Публикация</h4><p>Новый розыгрыш сохраняется неактивным, пока вы его не включите.</p></div></div><label class="checkbox-row"><input name="is_active" type="checkbox" ${giveaway.is_active ? 'checked' : ''} /> Показывать розыгрыш участницам</label></section>
  <div class="admin-form-actions"><button class="ui-button ui-button--primary" type="submit" ${adminState.giveawaySaving ? 'disabled' : ''}>${adminState.giveawaySaving ? 'Сохранение…' : 'Сохранить розыгрыш'}</button>${giveaway.id ? '<button class="ui-button ui-button--ghost" type="button" data-admin-giveaway-create>Отмена</button>' : ''}</div>
  <p class="form-message" data-form-message="giveaway">${escapeHtml(adminState.formMessages.giveaway || '')}</p>
</form>`;

const renderGiveawayEntriesSelector = (selected) => {
  const giveaways = Array.isArray(adminState.giveaways) ? adminState.giveaways : [];
  if (giveaways.length < 2) return '';
  return `<label class="field admin-giveaway-entries-picker"><span>Розыгрыш для участников</span><select data-admin-giveaway-entries-select>${giveaways.map((giveaway) => `<option value="${escapeHtml(giveaway.id)}" ${String(giveaway.id) === String(selected?.id) ? 'selected' : ''}>${escapeHtml(getGiveawayTitle(giveaway))}${giveaway.is_active ? ' — активный' : ''}</option>`).join('')}</select></label>`;
};


const giveawayEntryStatusMeta = {
  active: { label: '● Активен', tone: 'success' },
  inactive: { label: '● Неактивен', tone: 'muted' },
  revoked: { label: '● Отозван', tone: 'danger' },
  verification_error: { label: '● Ошибка проверки', tone: 'warning' },
};

const renderGiveawayEntryStatusBadge = (status) => {
  const normalized = String(status || '').trim().toLowerCase();
  const meta = giveawayEntryStatusMeta[normalized] || { label: status || '—', tone: 'info' };
  if (!status) return '—';
  return `<span class="status-badge ui-badge ui-badge--${escapeHtml(meta.tone)} status-badge--${escapeHtml(meta.tone)}">${escapeHtml(meta.label)}</span>`;
};

const giveawayEntrySourceMeta = {
  subscription: { label: '🟣 Bloom', tone: 'bloom' },
  referral: { label: '🟢 Реферал', tone: 'referral' },
  telegram_subscription: { label: '🔵 Telegram', tone: 'telegram' },
  vk_subscription: { label: '🔷 VK', tone: 'vk' },
  manual: { label: '🟡 Ручной', tone: 'manual' },
};

const renderGiveawayEntrySourceBadge = (source, fullLabel) => {
  const normalized = String(source || '').trim().toLowerCase();
  const meta = giveawayEntrySourceMeta[normalized] || { label: fullLabel || source || '—', tone: 'unknown' };
  if (!source && !fullLabel) return '—';
  const title = fullLabel || source || meta.label;
  return `<span class="giveaway-source-badge giveaway-source-badge--${escapeHtml(meta.tone)}" title="${escapeHtml(title)}">${escapeHtml(meta.label)}</span>`;
};

const renderGiveawayEntriesSection = (selected) => {
  const hasGiveaways = Array.isArray(adminState.giveaways) && adminState.giveaways.length > 0;
  if (!hasGiveaways) return `<section class="ui-card giveaway-participants-section"><div class="admin-section-heading"><h4>Участники и номера</h4><p>Сначала создайте и сохраните розыгрыш.</p></div></section>`;
  if (!selected) return `<section class="ui-card giveaway-participants-section"><div class="admin-section-heading"><h4>Участники и номера</h4><p>Выберите розыгрыш, чтобы открыть список участников.</p></div>${renderGiveawayEntriesSelector(selected)}</section>`;
  const data = adminState.giveawayEntries;
  const rows = Array.isArray(data?.items) ? data.items : [];
  const summary = data?.summary || {};
  return `<section class="ui-card giveaway-participants-section"><div class="admin-section-heading"><h4>Участники и номера — ${escapeHtml(getGiveawayTitle(selected))}</h4><p>Каждый номер показан отдельной строкой. Excel выгружает весь выбранный розыгрыш.</p></div>
    ${renderGiveawayEntriesSelector(selected)}
    <div class="admin-toolbar"><button class="ui-button ui-button--secondary" type="button" data-admin-giveaway-export="${escapeHtml(selected.id)}">Выгрузить в Excel (весь розыгрыш)</button><button class="ui-button" type="button" data-admin-giveaway-recheck="${escapeHtml(selected.id)}">Перепроверить подписки</button></div>
    ${adminState.giveawayRecheckResult ? `<p class="form-message">Проверено: ${escapeHtml(adminState.giveawayRecheckResult.checked || 0)}, активных: ${escapeHtml(adminState.giveawayRecheckResult.active || 0)}, деактивировано: ${escapeHtml(adminState.giveawayRecheckResult.deactivated || 0)}, повторно активировано: ${escapeHtml(adminState.giveawayRecheckResult.reactivated || 0)}, ошибок: ${escapeHtml(adminState.giveawayRecheckResult.errors || 0)}</p>` : ''}
    <div class="giveaway-entry-stats"><article><span>Всего номеров</span><strong>${escapeHtml(summary.total_numbers || 0)}</strong></article><article><span>Активных</span><strong>${escapeHtml(summary.active_numbers || 0)}</strong></article><article><span>Участников</span><strong>${escapeHtml(summary.unique_participants || 0)}</strong></article><article><span>Bloom</span><strong>${escapeHtml(summary.subscription_numbers || 0)}</strong></article><article><span>Рефералы</span><strong>${escapeHtml(summary.referral_numbers || 0)}</strong></article><article><span>Telegram</span><strong>${escapeHtml(summary.telegram_numbers || 0)}</strong></article><article><span>VK</span><strong>${escapeHtml(summary.vk_numbers || 0)}</strong></article></div>
    ${renderTable(['Номер','Статус','Источник','ФИО','Client ID','Telegram ID','Telegram username','VK ID','Телефон','Email','Дата начисления','Причина неактивности'], rows.map((i) => [formatValue(i.number), renderGiveawayEntryStatusBadge(i.status), renderGiveawayEntrySourceBadge(i.source, i.source_label), formatValue(i.owner_name), formatValue(i.client_id), formatValue(i.telegram_id), formatValue(i.telegram_username), formatValue(i.vk_id), formatValue(i.phone), formatValue(i.email), formatValue(formatDateTime(i.created_at)), formatValue(i.deactivation_reason)]), true, 'admin-table--compact admin-table--giveaway-entries', adminState.giveawayEntriesLoading ? 'Загрузка…' : 'В этом розыгрыше пока нет номеров')}
  </section>`;
};

const renderGiveawaysTab = () => {
  const selected = adminState.giveaways.find((item) => String(item.id) === String(adminState.selectedGiveawayIdForEdit));
  const entriesSelection = resolveGiveawayForEntries();
  return `<div class="giveaways-page"><div class="admin-section-heading admin-page-heading admin-page-heading--actions"><div><p class="section-eyebrow section-kicker">Розыгрыши</p><h3>Розыгрыши клуба</h3><p>Создание розыгрыша, призы, участники и выгрузка результатов — в одном разделе.</p></div><button class="ui-button ui-button--primary" type="button" data-admin-giveaway-create>Новый розыгрыш</button></div>
  <section class="ui-card giveaway-section"><h4>${selected ? `Редактирование: ${escapeHtml(getGiveawayTitle(selected))}` : 'Новый розыгрыш'}</h4>${renderGiveawayForm(selected || {})}</section>
  <section class="ui-card giveaway-section"><h4>Все розыгрыши</h4>${renderTable(
    ['ID', 'Название', 'Статус', 'Победителей', 'Действия'],
    adminState.giveaways.map((g) => [
      formatValue(g.id),
      formatValue(g.title),
      renderActiveStatusBadge(g.is_active),
      formatValue(g.winners_count),
      renderAdminTableActions(`<button class="admin-inline-action ui-button ui-button--secondary admin-table-action" type="button" data-admin-giveaway-edit="${escapeHtml(g.id)}">Редактировать</button>`),
    ]),
    true,
    'admin-table--compact',
    'Розыгрышей пока нет.',
  )}</section>${renderGiveawayEntriesSection(entriesSelection.giveaway)}</div>`;
};

const buildGiveawayPayload = (form) => {
  const fd = new FormData(form);
  return {
    title: String(fd.get('title') || '').trim(),
    description: String(fd.get('description') || '').trim(),
    is_active: fd.get('is_active') === 'on',
    starts_at: fd.get('starts_at') ? new Date(String(fd.get('starts_at'))).toISOString() : null,
    ends_at: fd.get('ends_at') ? new Date(String(fd.get('ends_at'))).toISOString() : null,
    winners_count: Number(fd.get('winners_count') || 0),
    telegram_community_url: String(fd.get('telegram_community_url') || '').trim() || null,
    telegram_chat_id: String(fd.get('telegram_chat_id') || '').trim() || null,
    telegram_reward_enabled: fd.get('telegram_reward_enabled') === 'on',
    telegram_reward_numbers: Number(fd.get('telegram_reward_numbers') || 1),
    vk_community_url: String(fd.get('vk_community_url') || '').trim() || null,
    vk_group_id: String(fd.get('vk_group_id') || '').trim() || null,
    vk_reward_enabled: fd.get('vk_reward_enabled') === 'on',
    vk_reward_numbers: Number(fd.get('vk_reward_numbers') || 1),
    prizes: Array.from(form.querySelectorAll('[data-admin-giveaway-place-row]')).map((row, index) => ({
      place_number: index + 1,
      prize_title: String(row.querySelector('[name="prize_title"]')?.value || '').trim(),
      winner_provider: String(row.querySelector('[name="winner_provider"]')?.value || '').trim() || null,
      winner_provider_user_id: String(row.querySelector('[name="winner_provider_user_id"]')?.value || '').trim() || null,
      winning_number: String(row.querySelector('[name="winning_number"]')?.value || '').trim() || null,
    })),
  };
};

const renderAdminActivityTab = () => `
  <div class="admin-section-heading admin-page-heading">
    <p class="section-eyebrow section-kicker">Activity feed</p>
    <h4>Активность</h4>
    <p>Общая лента событий по привилегиям, QR, партнёрам и предложениям.</p>
  </div>
  <form class="activity-filter" data-admin-activity-filter>
    <label>Тип события
      ${renderCustomSelect({
        id: 'admin-activity-event-type',
        name: 'event_type',
        value: adminState.activityEventType,
        options: activityEventFilters,
        placeholder: 'Все события',
        label: 'Тип события',
        data: { adminActivityEventType: true },
        ariaLabel: 'Тип события',
      })}
    </label>
  </form>
  ${renderActivityFeed(adminState.activityItems, { loading: adminState.activityLoading, error: adminState.activityError })}
`;


const getAdminLandingSettings = () => ({
  members_count_base: 125,
  partners_count_display: 18,
  partners_count_base: 18,
  partners_count: 18,
  partners_count_real: 0,
  savings_total: 53500,
  savings_total_base: 53500,
  savings_total_display: 53500,
  savings_total_real: 0,
  giveaway_title: 'Розыгрыш месяца',
  giveaway_current: 'Приз месяца',
  giveaway_subtitle: 'доступно участницам клуба',
  giveaway_empty_text: 'Информация о призах появится после настройки розыгрыша.',
  giveaway_items: [{ title: 'Приз месяца', description: '', is_active: true, sort_order: 0 }],
  ...(adminState.landingSettings || {}),
});

const renderAdminGiveawayItems = (items = []) => {
  const list = Array.isArray(items) && items.length ? items : [{ title: '', description: '', is_active: true, sort_order: 0 }];
  return list.map((item, index) => `
    <article class="giveaway-prize-row" data-giveaway-prize-row>
      <label>Приз<input name="giveaway_item_title" value="${escapeHtml(item.title || '')}" placeholder="Название приза" /></label>
      <label>Описание<input name="giveaway_item_description" value="${escapeHtml(item.description || '')}" placeholder="Короткое описание" /></label>
      <label>Порядок<input name="giveaway_item_sort_order" type="number" value="${escapeHtml(item.sort_order ?? index)}" /></label>
      <label class="checkbox-row"><input name="giveaway_item_is_active_${index}" type="checkbox" ${item.is_active === false ? '' : 'checked'} /> Активен</label>
      <button class="admin-inline-action ui-button ui-button--danger" type="button" data-admin-giveaway-remove-prize${legacyContentDisabledAttr()}>Удалить</button>
    </article>
  `).join('');
};

const renderLandingSettingsCard = () => {
  const settings = getAdminLandingSettings();
  const partnersCountBase = Number(settings.partners_count_base ?? settings.partners_count_display ?? 0);
  const partnersCountPreview = Number(settings.partners_count ?? partnersCountBase + Number(settings.partners_count_real || 0));
  const savingsTotalBase = Number(settings.savings_total_base ?? settings.savings_total ?? 0);
  const savingsTotalPreview = Number(settings.savings_total_display ?? savingsTotalBase + Number(settings.savings_total_real || 0));
  return `
    <section class="quick-actions-panel admin-landing-settings" aria-labelledby="landing-settings-title">
      <div class="admin-section-heading">
        <h4 id="landing-settings-title">Настройки главной</h4>
        <p>Управляйте публичными показателями hero mini-cards и розыгрышем месяца.</p>
      </div>
      <form class="admin-form admin-form--inline" data-admin-form="landingSettings" data-legacy-content-form>
        <label>Базовое число девушек<input name="members_count_base" type="number" min="0" value="${escapeHtml(settings.members_count_base)}" required /></label>
        <label>Базовое число партнёров<input name="partners_count_display" type="number" min="0" value="${escapeHtml(partnersCountBase)}" required /></label>
        <label>Базовая сумма экономии<input name="savings_total" type="number" min="0" value="${escapeHtml(savingsTotalBase)}" required /></label>
        <div class="admin-form-actions">
          <button class="ui-button ui-button--primary" type="submit"${legacyContentDisabledAttr()}>Сохранить показатели</button>
          <button class="ui-button ui-button--secondary" type="button" data-admin-giveaway-open${legacyContentDisabledAttr()}>Розыгрыш месяца</button>
        </div>
        <p class="form-message" data-form-message="landingSettings">${escapeHtml(adminState.formMessages.landingSettings || '')}</p>
      </form>
      <div class="summary-grid summary-grid--compact">
        <article class="summary-card"><span>Девушек внутри</span><strong>${escapeHtml(settings.members_count_base)} + клиентки</strong><small>База плюс реальные client/member/customer</small></article>
        <article class="summary-card"><span>Партнёров</span><strong>${escapeHtml(partnersCountPreview)}</strong><small>База + активные партнёры</small></article>
        <article class="summary-card"><span>Экономия</span><strong>${escapeHtml(formatMoneyLabel(savingsTotalPreview))}</strong><small>База + реальная экономия</small></article>
        <article class="summary-card"><span>${escapeHtml(settings.giveaway_title)}</span><strong>${escapeHtml(settings.giveaway_current)}</strong><small>${escapeHtml(settings.giveaway_subtitle)}</small></article>
      </div>
      ${adminState.giveawayDrawerOpen ? renderGiveawayDrawer(settings) : ''}
    </section>
  `;
};

const renderGiveawayDrawer = (settings) => `
  <aside class="admin-side-drawer admin-giveaway-drawer" aria-label="Розыгрыш месяца">
    <form class="admin-form" data-admin-form="landingGiveaway" data-legacy-content-form>
      <div class="admin-section-heading">
        <h4>Розыгрыш месяца</h4>
        <p>Первый активный приз с меньшим порядком сортировки показывается на главной.</p>
      </div>
      <label>Название блока<input name="giveaway_title" value="${escapeHtml(settings.giveaway_title || '')}" required /></label>
      <label>Название текущего розыгрыша<input name="giveaway_current" value="${escapeHtml(settings.giveaway_current || '')}" required /></label>
      <label>Описание<textarea name="giveaway_subtitle" rows="3" required>${escapeHtml(settings.giveaway_subtitle || '')}</textarea></label>
      <label>Текст, если призы ещё не заполнены<textarea name="giveaway_empty_text" rows="3">${escapeHtml(settings.giveaway_empty_text || '')}</textarea><small>Показывается на главной, когда призы розыгрыша ещё не настроены.</small></label>
      <div class="giveaway-prize-list" data-admin-giveaway-prize-list>
        ${renderAdminGiveawayItems(settings.giveaway_items)}
      </div>
      <button class="admin-inline-action ui-button ui-button--secondary" type="button" data-admin-giveaway-add-prize${legacyContentDisabledAttr()}>Добавить приз</button>
      <div class="admin-form-actions">
        <button class="ui-button ui-button--primary" type="submit"${legacyContentDisabledAttr()}>Сохранить</button>
        <button class="ui-button ui-button--ghost" type="button" data-admin-giveaway-cancel>Отмена</button>
      </div>
      <p class="form-message" data-form-message="landingGiveaway">${escapeHtml(adminState.formMessages.landingGiveaway || (adminState.landingSettingsSaving ? 'Сохранение…' : ''))}</p>
    </form>
  </aside>
`;

const renderOverviewTab = () => {
  const cards = [
    ['Пользователи', adminState.users.length, 'Аккаунты всех ролей'],
    ['Города', adminState.cities.length, 'Активная география'],
    ['Категории', adminState.categories.length, 'Направления каталога'],
    ['Партнёры', adminState.partners.length, 'CRM-база клуба'],
    ['Подтверждения', adminState.verifications.length, 'Сессии привилегий'],
    ['Оплаты', adminState.paymentRequests.length, 'Ручные заявки на оплату'],
    ['Лиды', adminState.leads.reduce((sum, lead) => sum + Number(lead.total_clicks || 0), 0), 'Переходы по QR'],
  ];
  const quickActions = [
    ['users', 'Пользователи', 'Создать или активировать аккаунт'],
    ['partners', 'Партнёры', 'Добавить партнёра и владельца'],
    ['cities', 'Города', 'Настроить географию клуба'],
    ['contentReview', 'На проверке', 'Активировать новые материалы партнёров'],
    ['paymentRequests', 'Оплаты', 'Проверить ручные оплаты'],
    ['qr', 'QR / лиды', 'Посмотреть QR-ссылки и лиды'],
  ];

  return `
    <div class="admin-section-heading admin-page-heading">
      <p class="section-kicker">Панель управления</p>
      <h4>Обзор</h4>
      <p>${adminState.overviewPartialError ? 'Не удалось загрузить часть данных.' : 'Короткая сводка по справочникам и активности.'}</p>
    </div>
    <div class="summary-grid">
      ${cards.map(([label, value, caption]) => `
        <article class="summary-card">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
          <small>${escapeHtml(caption)}</small>
        </article>
      `).join('')}
    </div>
    ${renderLandingSettingsCard()}
    <section class="quick-actions-panel" aria-labelledby="quick-actions-title">
      <div class="admin-section-heading">
        <h4 id="quick-actions-title">Быстрые действия</h4>
        <p>Самые частые административные разделы в один клик.</p>
      </div>
      <div class="quick-actions-grid">
        ${quickActions.map(([tab, label, caption]) => `
          <button class="quick-action-card" type="button" data-admin-tab="${tab}">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(caption)}</strong>
          </button>
        `).join('')}
      </div>
    </section>
  `;
};

const renderAdminTableActions = (content) => `
  <div class="admin-table-actions admin-actions-stack">
    ${content}
  </div>
`;

const renderUserActionButton = (user) => renderAdminTableActions(`
  <button class="admin-inline-action ui-button ui-button--secondary admin-table-action" type="button" data-user-active-toggle="${escapeHtml(user.id)}">
    ${user.is_active ? 'Заблокировать' : 'Активировать'}
  </button>
  <button class="admin-inline-action ui-button ui-button--danger admin-table-action admin-inline-action--danger" type="button" data-user-delete="${escapeHtml(user.id)}">
    Удалить
  </button>
`);

const renderAdminSearch = (scope, placeholder) => {
  const value = adminState.search?.[scope] || '';
  return `
    <div class="admin-toolbar">
      <label class="admin-search">
        <span class="visually-hidden">${escapeHtml(placeholder)}</span>
        <input class="admin-search-input" data-admin-search="${escapeHtml(scope)}" value="${escapeHtml(value)}" placeholder="${escapeHtml(placeholder)}" />
      </label>
      ${value ? `<button class="admin-search-reset" type="button" data-admin-search-reset="${escapeHtml(scope)}">Сбросить</button>` : ''}
    </div>
  `;
};

const renderUsersTab = () => {
  const users = filterAdminRows(adminState.users, adminState.search.users, [
    'email',
    'contact_email',
    'phone',
    'full_name',
    'selected_city_name',
    'vk_user_id',
    'vk_username',
    'telegram_user_id',
    'telegram_username',
    'trial_status',
    'paid_subscription_status',
    'active_subscription_type',
    'role',
    (item) => item.display_name,
    (item) => formatRole(item.role),
    (item) => searchableBool(item.is_active),
  ]);
  return `
    <div class="admin-two-column admin-two-column--wide">
      <div>
        <div class="admin-section-heading"><h4>Пользователи</h4><p>Unified users для клиентских, партнёрских и административных кабинетов.</p></div>
        ${renderAdminSearch('users', 'Поиск по пользователям')}
        ${renderTable(
          ['Пользователь', 'Контакты', 'Роль', 'Статус', 'Подписка', 'Действия'],
          users.map((item) => [
            `<strong>${formatValue(item.display_name || item.full_name)}</strong><br><small class="muted-text">ID: ${formatValue(item.id)}</small>${item.selected_city_name ? `<br><small class="muted-text">${formatValue(item.selected_city_name)}</small>` : ''}`,
            `<div><strong>Login:</strong> ${item.is_synthetic_email ? `<span class="muted-text">${formatValue(item.email)}</span>` : formatValue(item.email)}</div><div><strong>Email:</strong> ${formatValue(item.contact_email)}</div><div><strong>Телефон:</strong> ${formatValue(item.phone)}</div><div><strong>VK:</strong> ${item.vk_url ? `<a href="${escapeHtml(item.vk_url)}" target="_blank" rel="noopener noreferrer">Открыть</a>${item.vk_user_id ? ` <small class="muted-text">(id: ${escapeHtml(item.vk_user_id)})</small>` : ''}${item.vk_username ? ` <small class="muted-text">@${escapeHtml(item.vk_username)}</small>` : ''}` : (item.vk_user_id ? `ID: ${escapeHtml(item.vk_user_id)}${item.vk_username ? ` <small class="muted-text">@${escapeHtml(item.vk_username)}</small>` : ''}` : '—')}</div><div><strong>TG:</strong> ${item.telegram_url ? `<a href="${escapeHtml(item.telegram_url)}" target="_blank" rel="noopener noreferrer">Открыть</a>${item.telegram_user_id ? ` <small class="muted-text">(id: ${escapeHtml(item.telegram_user_id)})</small>` : ''}` : (item.telegram_user_id ? `ID: ${escapeHtml(item.telegram_user_id)} <small class="muted-text">(username не указан)</small>` : '—')}</div>`,
            formatValue(formatRole(item.role)),
            renderBoolStatusBadge(item.is_active),
            `<div><strong>Trial:</strong> ${formatValue(item.trial_status)}</div><div><strong>Платная:</strong> ${formatValue(item.paid_subscription_status)}</div><div><strong>Тип:</strong> ${formatValue(item.active_subscription_type)}</div><div><strong>До:</strong> ${formatDateTime(item.subscription_active_until ?? item.active_subscription_until)}</div>`,
            renderUserActionButton(item),
          ]),
          true,
          'admin-table--compact',
          adminState.search.users ? 'Ничего не найдено.' : 'Пока нет данных.',
        )}
      </div>
      <form class="admin-form" data-admin-form="user">
        <h4>Новый пользователь</h4>
        <label>Логин<input name="email" type="text" autocomplete="username" placeholder="Введите логин" /><small class="helper-text">Логин — email, телефон или технический логин.</small></label>
        <label>Телефон<input name="phone" autocomplete="tel" /></label>
        <label>Пароль<input name="password" type="password" autocomplete="new-password" required /></label>
        <label>Роль${renderSelect('role', [['client', 'Клиент'], ['partner', 'Партнёр'], ['admin', 'Администратор']], true, 'client', null, { label: 'Роль', data: { adminUserRole: true } })}</label>
        <label class="checkbox-row"><input name="is_active" type="checkbox" checked /> Активен</label>
        <button type="submit">Создать пользователя</button>
        <p class="form-message" data-form-message="user">${escapeHtml(adminState.formMessages.user || '')}</p>
      </form>
    </div>
  `;
};

const renderCityActionButtons = (city) => renderAdminTableActions(`
  <button class="admin-inline-action ui-button ui-button--secondary admin-table-action" type="button" data-admin-city-edit="${escapeHtml(city.id)}"${legacyContentDisabledAttr()}>Редактировать</button>
  <button class="admin-inline-action ui-button ui-button--secondary admin-table-action" type="button" data-admin-city-active-toggle="${escapeHtml(city.id)}"${legacyContentDisabledAttr()}>
    ${city.is_active ? 'Деактивировать' : 'Активировать'}
  </button>
`);

const renderCityCreateForm = () => `
  <form class="admin-form" data-admin-form="city" data-legacy-content-form>
    <h4>Новый город</h4>
    <label>Название города<input name="name" required /></label>
    <label>Слаг / код города<input name="slug" required /></label>
    <label>Порядок сортировки<input name="sort_order" type="number" value="0" /></label>
    <label class="checkbox-row"><input name="is_active" type="checkbox" checked /> Активен</label>
    <button type="submit"${legacyContentDisabledAttr()}>Создать город</button>
    <p class="form-message" data-form-message="city">${escapeHtml(adminState.formMessages.city || '')}</p>
  </form>
`;

const renderCityEditForm = () => {
  const city = adminState.cities.find((item) => String(item.id) === String(adminState.selectedCityIdForEdit));
  if (!city) {
    return '';
  }

  return `
    <form class="admin-form" data-admin-form="cityEdit" data-legacy-content-form data-city-id="${escapeHtml(city.id)}">
      <h4>Редактировать город</h4>
      <label>Название<input name="name" value="${escapeHtml(city.name || '')}" required /></label>
      <label>Slug<input name="slug" value="${escapeHtml(city.slug || '')}" required /></label>
      <label>Порядок сортировки<input name="sort_order" type="number" value="${escapeHtml(city.sort_order ?? 0)}" /></label>
      <label class="checkbox-row"><input name="is_active" type="checkbox" ${city.is_active ? 'checked' : ''} /> Активен</label>
      <div class="admin-form-actions">
        <div class="ui-action-row ui-action-row--right ui-action-row--stack-mobile"><button class="ui-button ui-button--primary" type="submit">Сохранить изменения</button></div>
        <button class="admin-inline-action ui-button ui-button--ghost" type="button" data-admin-city-edit-cancel>Отмена</button>
      </div>
      <p class="form-message" data-form-message="cityEdit">${escapeHtml(adminState.formMessages.cityEdit || '')}</p>
    </form>
  `;
};

const renderCitiesTab = () => {
  const cities = filterAdminRows(adminState.cities, adminState.search.cities, ['name', 'slug', (city) => searchableBool(city.is_active)]);
  return `
    <div class="admin-two-column">
      <div>
        <div class="admin-section-heading"><h4>Города</h4><p>Список городов для управления каталогом.</p></div>
        ${renderAdminSearch('cities', 'Поиск по городам')}
        ${renderTable(
          ['Город', 'Слаг', 'Активен', 'Сортировка', 'Действие'],
          cities.map((city) => [
            formatValue(city.name),
            formatValue(city.slug),
            renderBoolStatusBadge(city.is_active),
            formatValue(city.sort_order),
            renderCityActionButtons(city),
          ]),
          true,
          'admin-table--compact',
          adminState.search.cities ? 'Ничего не найдено.' : 'Пока нет данных.',
        )}
      </div>
      ${adminState.selectedCityIdForEdit ? renderCityEditForm() : renderCityCreateForm()}
    </div>
  `;
};

const getCategoryName = (category) => category.name || category.title || '';

const renderCategoryActionButtons = (category) => renderAdminTableActions(`
  <button class="admin-inline-action ui-button ui-button--secondary admin-table-action" type="button" data-admin-category-edit="${escapeHtml(category.id)}"${legacyContentDisabledAttr()}>Редактировать</button>
  <button class="admin-inline-action ui-button ui-button--secondary admin-table-action" type="button" data-admin-category-active-toggle="${escapeHtml(category.id)}"${legacyContentDisabledAttr()}>
    ${category.is_active ? 'Деактивировать' : 'Активировать'}
  </button>
`);

const renderCategoryCreateForm = () => `
  <form class="admin-form" data-admin-form="category" data-legacy-content-form>
    <h4>Новая категория</h4>
    <label>Название партнёра<input name="name" required /></label>
    <label>Slug<input name="slug" required /></label>
    <label>Порядок сортировки<input name="sort_order" type="number" value="0" /></label>
    <label class="checkbox-row"><input name="is_active" type="checkbox" checked /> Активна</label>
    <button type="submit"${legacyContentDisabledAttr()}>Создать категорию</button>
    <p class="form-message" data-form-message="category">${escapeHtml(adminState.formMessages.category || '')}</p>
  </form>
`;

const renderCategoryEditForm = () => {
  const category = adminState.categories.find((item) => String(item.id) === String(adminState.selectedCategoryIdForEdit));
  if (!category) {
    return '';
  }

  return `
    <form class="admin-form" data-admin-form="categoryEdit" data-legacy-content-form data-category-id="${escapeHtml(category.id)}">
      <h4>Редактировать категорию</h4>
      <label>Название<input name="name" value="${escapeHtml(getCategoryName(category))}" required /></label>
      <label>Slug<input name="slug" value="${escapeHtml(category.slug || '')}" required /></label>
      <label>Порядок сортировки<input name="sort_order" type="number" value="${escapeHtml(category.sort_order ?? 0)}" /></label>
      <label class="checkbox-row"><input name="is_active" type="checkbox" ${category.is_active ? 'checked' : ''} /> Активна</label>
      <div class="admin-form-actions">
        <div class="ui-action-row ui-action-row--right ui-action-row--stack-mobile"><button class="ui-button ui-button--primary" type="submit">Сохранить изменения</button></div>
        <button class="admin-inline-action ui-button ui-button--ghost" type="button" data-admin-category-edit-cancel>Отмена</button>
      </div>
      <p class="form-message" data-form-message="categoryEdit">${escapeHtml(adminState.formMessages.categoryEdit || '')}</p>
    </form>
  `;
};

const renderCategoriesTab = () => {
  const categories = filterAdminRows(adminState.categories, adminState.search.categories, ['name', 'title', 'slug', (category) => searchableBool(category.is_active)]);
  return `
    <div class="admin-two-column">
      <div>
        <div class="admin-section-heading"><h4>Категории</h4><p>Справочник категорий партнёров с безопасной деактивацией.</p></div>
        ${renderAdminSearch('categories', 'Поиск по категориям')}
        ${renderTable(
          ['Категория', 'Слаг', 'Активна', 'Сортировка', 'Действие'],
          categories.map((category) => [
            formatValue(getCategoryName(category)),
            formatValue(category.slug),
            renderActiveStatusFeminineBadge(category.is_active),
            formatValue(category.sort_order),
            renderCategoryActionButtons(category),
          ]),
          true,
          'admin-table--compact',
          adminState.search.categories ? 'Ничего не найдено.' : 'Пока нет данных.',
        )}
      </div>
      ${adminState.selectedCategoryIdForEdit ? renderCategoryEditForm() : renderCategoryCreateForm()}
    </div>
  `;
};

const renderAdminPartnerAction = (partner) => renderAdminTableActions(`
  <button class="admin-inline-action ui-button ui-button--secondary admin-table-action" type="button" data-admin-partner-edit="${escapeHtml(partner.id)}"${legacyContentDisabledAttr()}>Редактировать</button>
`);

const getAdminLoadedOffersForPartner = (partner) => {
  const partnerId = String(partner?.id || '');
  const inlineOffers = Array.isArray(partner?.offers) ? partner.offers : [];
  const selectedOffers = String(adminState.selectedPartnerIdForOffers || '') === partnerId ? adminState.offers : [];
  const relatedLoadedOffers = adminState.offers.filter((offer) => offer?.partner_id && String(offer.partner_id) === partnerId);
  return [...inlineOffers, ...selectedOffers, ...relatedLoadedOffers];
};

const renderPublishReadinessItem = (label, isOk) => `
  <li class="publish-readiness-item publish-readiness-item--${isOk ? 'ok' : 'warn'}">
    <span aria-hidden="true">${isOk ? '✅' : '⚠️'}</span>
    <span>${label}</span>
  </li>
`;

const renderPublishReadiness = (partner) => {
  const loadedOffers = getAdminLoadedOffersForPartner(partner);
  const checks = [
    ['Обложка добавлена', Boolean(partner.cover_url)],
    ['Логотип добавлен', Boolean(partner.logo_url)],
    ['Описание заполнено', Boolean(partner.description)],
    ['Адрес заполнен', Boolean(partner.address)],
    ['График работы заполнен', Boolean(partner.working_hours)],
    ['Есть активное предложение', loadedOffers.some((offer) => offer?.is_active === true)],
    ['Партнёр активен', partner.is_active === true],
    ['Партнёр проверен', partner.is_verified === true],
  ];
  const isReady = partner.is_active === true
    && partner.is_verified === true
    && Boolean(partner.description)
    && Boolean(partner.address)
    && loadedOffers.some((offer) => offer?.is_active === true)
    && (Boolean(partner.cover_url) || Boolean(partner.logo_url));

  return `
    <section class="publish-readiness" aria-label="Готовность к публикации">
      <div class="admin-section-heading">
        <h4>Готовность к публикации</h4>
        <p>Проверьте базовые элементы витрины перед публикацией партнёра.</p>
      </div>
      <div class="publish-readiness-status">${isReady ? 'Готов к публикации' : 'Нужно доработать'}</div>
      <ul class="publish-readiness-checklist">
        ${checks.map(([label, isOk]) => renderPublishReadinessItem(label, isOk)).join('')}
      </ul>
    </section>
  `;
};

const renderPartnerEditForm = () => {
  const partner = adminState.partners.find((item) => String(item.id) === String(adminState.selectedPartnerIdForEdit));
  const photos = adminState.partnerPhotosByPartner[adminState.selectedPartnerIdForEdit] || [];
  if (!partner) {
    return '';
  }

  const activeCategories = adminState.categories.filter((category) => category.is_active !== false);
  const isEditMode = Boolean(partner);
  const selectedCategoryIds = getAdminPartnerSelectedCategoryIds(isEditMode ? partner : null, activeCategories);
  return `
    <section class="admin-partner-detail">
      <div class="admin-partner-detail-header">
        <button class="admin-back-button" type="button" data-admin-partner-edit-cancel>← Назад к списку партнёров</button>
        <div class="admin-partner-detail-title">
          <p class="section-eyebrow section-kicker">Партнёры</p>
          <h4 class="section-title">Редактирование партнёра</h4>
          <strong>${escapeHtml(partner.name || 'Партнёр без названия')}</strong>
        </div>
        <div class="admin-partner-detail-badges" aria-label="Статусы партнёра">
          ${renderBoolStatusBadge(partner.is_active)}
          ${renderVerifiedStatusBadge(partner.is_verified)}
        </div>
      </div>
      <div class="admin-partner-detail-grid">
        <div class="admin-partner-detail-main">
          <section class="admin-partner-detail-section">
            <form class="admin-form partner-profile-settings" data-admin-form="partnerEdit" data-legacy-content-form data-partner-id="${escapeHtml(partner.id)}">
              <div class="admin-section-heading text-stack"><h4 class="section-title">Основные данные</h4><p class="section-description compact-copy">Профиль, контакты и статусы для каталога.</p></div>
              <label>Город${renderSelect('city_id', adminState.cities.map((city) => [city.id, city.name]), true, partner.city_id, null, { label: 'Город', data: { adminPartnerField: 'city' } })}</label>
              <fieldset class="partner-multicategory"><legend>Категории</legend><div class="partner-category-chips">${activeCategories.map((category) => `<label class="checkbox-row"><input type="checkbox" name="category_ids" value="${escapeHtml(category.id)}" data-category-id="${escapeHtml(category.id)}" data-category-slug="${escapeHtml(category.slug || '')}" data-category-title="${escapeHtml(category.title || category.name || '')}" ${selectedCategoryIds.has(String(category.id)) ? 'checked' : ''}/> ${escapeHtml(category.title)}</label>`).join('')}</div></fieldset>
              <label>Владелец / аккаунт партнёра${renderSelect('owner_user_id', adminState.users.filter((item) => item.role === 'partner').map((item) => [item.id, item.email || item.phone || `Партнёр #${item.id}`]), false, partner.owner_user_id || '', 'Без владельца', { label: 'Владелец', data: { adminPartnerField: 'owner' } })}</label>
              <label>Название<input name="name" required value="${escapeHtml(partner.name || '')}" /></label>
              <label>Описание<textarea name="description" rows="3">${escapeHtml(partner.description || '')}</textarea></label>
              <label>Адрес<input name="address" value="${escapeHtml(partner.address || '')}" /></label>
              <label>Телефон<input name="phone" value="${escapeHtml(partner.phone || '')}" /></label>
              <label>Сайт<input name="website_url" value="${escapeHtml(partner.website_url || '')}" /></label>
              <label>Соцсеть<input name="social_url" value="${escapeHtml(partner.social_url || '')}" /></label>
              <label>ВКонтакте<input name="vk_url" value="${escapeHtml(partner.vk_url || '')}" /></label>
              <label>Telegram<input name="telegram_url" value="${escapeHtml(partner.telegram_url || '')}" /></label>
              <label>WhatsApp<input name="whatsapp_url" value="${escapeHtml(partner.whatsapp_url || '')}" /></label>
              <label>Instagram<input name="instagram_url" value="${escapeHtml(partner.instagram_url || '')}" /></label>
              <label>Ссылка на карту<input name="map_url" value="${escapeHtml(partner.map_url || '')}" /></label>
              <label>График работы<input name="working_hours" value="${escapeHtml(partner.working_hours || '')}" /></label>
              <label>Порядок сортировки<input name="sort_order" type="number" value="${escapeHtml(partner.sort_order ?? 0)}" /></label>
              <label class="checkbox-row"><input name="is_active" type="checkbox" ${partner.is_active ? 'checked' : ''} /> Активен</label>
              <label class="checkbox-row"><input name="is_verified" type="checkbox" ${partner.is_verified ? 'checked' : ''} /> Проверен</label>
              <details class="partner-profile-advanced">
                <summary>URL изображения</summary>
                <p class="helper-text form-message compact-copy">URL — дополнительное поле для /uploads/ и /assets/.</p>
                <label>Логотип URL<input name="logo_url" value="${escapeHtml(partner.logo_url || '')}" /></label>
                <label>Обложка URL<input name="cover_url" value="${escapeHtml(partner.cover_url || '')}" /></label>
              </details>
              <div class="admin-partner-detail-actions admin-form-actions">
                <div class="ui-action-row ui-action-row--right ui-action-row--stack-mobile"><button class="ui-button ui-button--primary" type="submit">Сохранить изменения</button></div>
                <button class="admin-inline-action ui-button ui-button--ghost" type="button" data-admin-partner-edit-cancel>Отмена</button>
              </div>
              <p class="form-message" data-form-message="partnerEdit">${escapeHtml(adminState.formMessages.partnerEdit || '')}</p>
            </form>
          </section>
          <section class="admin-partner-detail-section">
            ${renderPartnerImageUploader(partner, 'admin')}
          </section>
          <section class="admin-partner-detail-section">
            ${renderPartnerGallery(partner, photos, 'admin')}
          </section>
        </div>
        <aside class="admin-partner-detail-side">
          <section class="admin-partner-detail-section admin-partner-next-actions">
            <div class="admin-section-heading text-stack"><h4 class="section-title">Следующие шаги</h4><p class="section-description compact-copy">Продолжайте настройку этого партнёра без повторного поиска.</p></div>
            <button class="ui-button ui-button--primary" type="button" data-admin-partner-open-offers="${escapeHtml(partner.id)}">Добавить привилегию</button>
            <button class="ui-button ui-button--secondary" type="button" data-admin-partner-open-qr="${escapeHtml(partner.id)}">Настроить QR</button>
          </section>
          <section class="admin-partner-detail-section">
            <div class="admin-section-heading text-stack"><h4 class="section-title">Витрина партнёра</h4><p class="section-description compact-copy">Preview для клиентского каталога.</p></div>
            ${renderPartnerMarketplaceCard(partner, { note: 'Preview для клиента', photos })}
            ${renderPartnerProfileHints(partner)}
          </section>
          <section class="admin-partner-detail-section">
            ${renderPublishReadiness(partner)}
          </section>
          <section class="admin-partner-detail-section">
            ${renderAnalyticsSection(adminState.selectedPartnerAnalytics, {
              title: 'Аналитика партнёра',
              loading: adminState.partnerAnalyticsLoading,
              error: adminState.partnerAnalyticsError,
            })}
          </section>
        </aside>
      </div>
    </section>
  `;
};

const renderPartnerForm = () => {
  const activeCategories = adminState.categories.filter((category) => category.is_active !== false);
  return `
    <section class="admin-partner-create-page">
      <header class="admin-partner-create-header">
        <button class="admin-back-button" type="button" data-admin-partner-edit-cancel>← Назад к партнёрам</button>
        <div>
          <p class="section-eyebrow section-kicker">Новый партнёр</p>
          <h3>Добавить партнёра</h3>
          <p>Сначала сохраните карточку. Фото, привилегии и QR можно добавить сразу после этого.</p>
        </div>
        <span class="ui-badge ui-badge--muted">Черновик</span>
      </header>
      <form id="admin-partner-create-form" class="admin-form admin-partner-create-form" data-admin-form="partner" data-admin-partner-wizard-form>
        <section class="admin-form-section">
          <div class="admin-form-section-heading"><span>1</span><div><h4>Основная информация</h4><p>Поля, по которым партнёра найдут в каталоге.</p></div></div>
          <div class="admin-form-grid">
            <label>Название партнёра<input name="name" required autofocus placeholder="Например, Тест1" /></label>
            <label>Город${renderSelect('city_id', adminState.cities.filter((city) => city.is_active !== false).map((city) => [city.id, city.name]), true, '', null, { label: 'Город', data: { adminPartnerField: 'city' } })}</label>
          </div>
          <fieldset class="partner-multicategory"><legend>Категории</legend><p class="helper-text">Можно выбрать несколько.</p><div class="partner-category-chips admin-partner-chips">${activeCategories.map((category) => `<label class="checkbox-row"><input type="checkbox" name="category_ids" value="${escapeHtml(category.id)}" /> ${escapeHtml(category.title || category.name)}</label>`).join('')}</div></fieldset>
          <label>Короткое описание<textarea name="description" rows="4" placeholder="Чем занимается партнёр и какую пользу получает участница"></textarea></label>
        </section>
        <section class="admin-form-section">
          <div class="admin-form-section-heading"><span>2</span><div><h4>Контакты</h4><p>Показываются клиентке в карточке партнёра.</p></div></div>
          <div class="admin-form-grid">
            <label>Адрес<input name="address" placeholder="Город, улица, дом" /></label>
            <label>Телефон<input name="phone" autocomplete="tel" placeholder="+7 900 000-00-00" /></label>
            <label>График работы<input name="working_hours" placeholder="Пн–Вс, 10:00–21:00" /></label>
            <label>Ссылка на карту<input name="map_url" type="url" placeholder="https://…" /></label>
          </div>
        </section>
        <section class="admin-form-section">
          <div class="admin-form-section-heading"><span>3</span><div><h4>Сайт и соцсети</h4><p>Заполняйте только те каналы, которыми партнёр пользуется.</p></div></div>
          <div class="admin-form-grid">
            <label>Сайт<input name="website_url" type="url" placeholder="https://…" /></label>
            <label>ВКонтакте<input name="vk_url" type="url" placeholder="https://vk.com/…" /></label>
            <label>Telegram<input name="telegram_url" type="url" placeholder="https://t.me/…" /></label>
            <label>WhatsApp<input name="whatsapp_url" type="url" placeholder="https://wa.me/…" /></label>
            <label>Instagram<input name="instagram_url" type="url" placeholder="https://instagram.com/…" /></label>
            <label>Другая ссылка<input name="social_url" type="url" placeholder="https://…" /></label>
          </div>
        </section>
        <section class="admin-form-section admin-form-section--publish">
          <div class="admin-form-section-heading"><span>4</span><div><h4>Доступ и публикация</h4><p>Новый партнёр по умолчанию сохраняется скрытым — его можно спокойно заполнить и проверить.</p></div></div>
          <div class="admin-form-grid">
            <label>Аккаунт владельца${renderSelect('owner_user_id', adminState.users.filter((item) => item.role === 'partner').map((item) => [item.id, item.email || item.phone || `Партнёр #${item.id}`]), false, '', 'Подключить позже', { label: 'Аккаунт владельца', data: { adminPartnerField: 'owner' } })}<small class="helper-text">Если аккаунта ещё нет, сохраните карточку и создайте его позже в разделе «Пользователи».</small></label>
            <label>Порядок в каталоге<input name="sort_order" type="number" value="0" /></label>
          </div>
          <div class="admin-publish-options">
            <label class="checkbox-row"><input name="is_active" type="checkbox" /> Показывать партнёра клиенткам</label>
            <label class="checkbox-row"><input name="is_verified" type="checkbox" /> Данные проверены администратором</label>
          </div>
        </section>
        <div class="admin-partner-create-actions">
          <p>После сохранения откроется карточка, где можно загрузить фотографии и добавить привилегию.</p>
          <div class="ui-action-row ui-action-row--right ui-action-row--stack-mobile">
            <button class="ui-button ui-button--ghost" type="button" data-admin-partner-edit-cancel>Отмена</button>
            <button class="ui-button ui-button--primary" type="submit">Сохранить партнёра</button>
          </div>
          <p class="form-message" data-form-message="partner">${escapeHtml(adminState.formMessages.partner || '')}</p>
        </div>
      </form>
    </section>
  `;
};


const defaultPartnerFilters = () => ({
  city: '',
  category: '',
  activity: 'all',
  photos: 'all',
  offers: 'all',
  verification: 'all',
});

const hasVerificationData = (partners) => partners.some((partner) => partner?.is_verified !== undefined && partner?.is_verified !== null);

const getPartnerFilterOptions = (partners) => {
  const cityMap = new Map();
  adminState.cities.forEach((city) => {
    const name = String(city?.name || '').trim();
    if (name) cityMap.set(name.toLowerCase(), name);
  });
  partners.forEach((partner) => {
    const name = String(partner?.city_name || '').trim();
    if (name) cityMap.set(name.toLowerCase(), name);
  });

  const categoryMap = new Map();
  adminState.categories.forEach((category) => {
    const title = String(category?.title || category?.name || '').trim();
    if (title) categoryMap.set(title.toLowerCase(), title);
  });
  partners.forEach((partner) => {
    getPartnerCategories(partner).forEach((category) => {
      const title = String(category?.name || category?.title || '').trim();
      if (title) categoryMap.set(title.toLowerCase(), title);
    });
  });

  return {
    cities: Array.from(cityMap.values()).sort((a, b) => a.localeCompare(b, 'ru')),
    categories: Array.from(categoryMap.values()).sort((a, b) => a.localeCompare(b, 'ru')),
  };
};

const filterPartnersRegistry = (partners) => {
  const filters = { ...defaultPartnerFilters(), ...(adminState.partnerFilters || {}) };
  return partners.filter((partner) => {
    const cityName = String(partner.city_name || '').trim();
    if (filters.city && cityName !== filters.city) return false;

    const categories = getPartnerCategories(partner).map((category) => String(category.name || '').trim());
    if (filters.category && !categories.includes(filters.category)) return false;

    if (filters.activity === 'active' && partner.is_active !== true) return false;
    if (filters.activity === 'inactive' && partner.is_active === true) return false;

    const photosCount = Number(partner.photos_count ?? adminState.partnerPhotosByPartner[String(partner.id)]?.length ?? 0);
    const hasPhoto = Boolean(partner.cover_url || partner.logo_url || photosCount > 0);
    if (filters.photos === 'with' && !hasPhoto) return false;
    if (filters.photos === 'without' && hasPhoto) return false;

    const offersCount = getAdminLoadedOffersForPartner(partner).length;
    if (filters.offers === 'with' && offersCount <= 0) return false;
    if (filters.offers === 'without' && offersCount > 0) return false;

    if (filters.verification === 'verified' && partner.is_verified !== true) return false;
    if (filters.verification === 'unverified' && partner.is_verified === true) return false;

    return true;
  });
};

const hasActivePartnerFilters = () => {
  const filters = { ...defaultPartnerFilters(), ...(adminState.partnerFilters || {}) };
  return Boolean(filters.city || filters.category || filters.activity !== 'all' || filters.photos !== 'all' || filters.offers !== 'all' || filters.verification !== 'all' || adminState.search.partners);
};

const renderPartnersList = (partners, totalPartners) => {
  const filterOptions = getPartnerFilterOptions(totalPartners);
  const filters = { ...defaultPartnerFilters(), ...(adminState.partnerFilters || {}) };
  const showVerificationFilter = hasVerificationData(totalPartners);
  const activeChips = [
    filters.city ? ['city', `Город: ${filters.city}`] : null,
    filters.category ? ['category', `Категория: ${filters.category}`] : null,
    filters.activity === 'active' ? ['activity', 'Активные'] : null,
    filters.activity === 'inactive' ? ['activity', 'Скрытые / неактивные'] : null,
    filters.photos === 'with' ? ['photos', 'Есть фото'] : null,
    filters.photos === 'without' ? ['photos', 'Без фото'] : null,
    filters.offers === 'with' ? ['offers', 'Есть услуги'] : null,
    filters.offers === 'without' ? ['offers', 'Без услуг'] : null,
    filters.verification === 'verified' ? ['verification', 'Проверенные'] : null,
    filters.verification === 'unverified' ? ['verification', 'Требуют проверки'] : null,
  ].filter(Boolean);

  const rows = partners.map((partner) => {
    const cats = getPartnerCategories(partner).map((c) => c.title || c.name || c.slug).filter(Boolean);
    const offersCount = getAdminLoadedOffersForPartner(partner).length;
    const photosCount = (partner.photos_count ?? adminState.partnerPhotosByPartner[String(partner.id)]?.length ?? 0);
    return [
      `<div><strong>${escapeHtml(partner.name || '—')}</strong><div class="muted">${escapeHtml(partner.city_name || '—')}</div><div class="muted">${escapeHtml(partner.owner_email || partner.phone || '—')}</div></div>`,
      cats.length ? `<div class="admin-partner-chips">${cats.map((c) => `<span class="status-badge">${escapeHtml(c)}</span>`).join('')}</div>` : '—',
      `${renderBoolStatusBadge(partner.is_active)} ${renderVerifiedStatusBadge(partner.is_verified)}`,
      `${partner.cover_url || partner.logo_url ? 'Есть фото' : 'Нет фото'} · ${photosCount || 0}`,
      String(offersCount || 0),
      formatValue(partner.updated_at || partner.created_at || '—'),
      `<div class="admin-table-actions">${renderAdminPartnerAction(partner)}</div>`,
    ];
  });

  const hasAnyPartners = totalPartners.length > 0;
  const noResults = hasAnyPartners && partners.length === 0;

  return `
  <section>
    <header class="admin-page-header"><h3>Партнёры</h3><p>Управление партнёрами клуба, категориями, статусами и витриной.</p></header>
    <div class="admin-page-toolbar">
      <div class="ui-toolbar-actions">
        <button class="ui-button ui-button--primary" type="button" data-admin-partner-create${legacyContentDisabledAttr()}>+ Добавить партнёра</button>
      </div>
      ${renderAdminSearch('partners', 'Поиск по партнёрам, городам, email, телефону и категориям')}
      ${hasActivePartnerFilters() ? '<button class="ui-button ui-button--ghost" type="button" data-admin-partner-filter-clear>Сбросить</button>' : ''}
    </div>
    <div class="admin-filter-panel">
      <div class="admin-filter-grid">
        <label class="admin-filter-field">Город${renderSelect('partner_filter_city', [['', 'Все города'], ...filterOptions.cities.map((city) => [city, city])], false, filters.city, null, { data: { adminPartnerFilter: 'city' } })}</label>
        <label class="admin-filter-field">Категория${renderSelect('partner_filter_category', [['', 'Все категории'], ...filterOptions.categories.map((category) => [category, category])], false, filters.category, null, { data: { adminPartnerFilter: 'category' } })}</label>
        <label class="admin-filter-field">Активность${renderSelect('partner_filter_activity', [['all', 'Все'], ['active', 'Активные'], ['inactive', 'Скрытые / неактивные']], false, filters.activity, null, { data: { adminPartnerFilter: 'activity' } })}</label>
        <label class="admin-filter-field">Фото${renderSelect('partner_filter_photos', [['all', 'Все'], ['with', 'Есть фото'], ['without', 'Нет фото']], false, filters.photos, null, { data: { adminPartnerFilter: 'photos' } })}</label>
        <label class="admin-filter-field">Услуги${renderSelect('partner_filter_offers', [['all', 'Все'], ['with', 'Есть услуги'], ['without', 'Нет услуг']], false, filters.offers, null, { data: { adminPartnerFilter: 'offers' } })}</label>
        ${showVerificationFilter ? `<label class="admin-filter-field">Проверка${renderSelect('partner_filter_verification', [['all', 'Все'], ['verified', 'Проверенные'], ['unverified', 'Требуют проверки']], false, filters.verification, null, { data: { adminPartnerFilter: 'verification' } })}</label>` : ''}
      </div>
      ${activeChips.length ? `<div class="admin-filter-chips">${activeChips.map(([key, label]) => `<span class="admin-filter-chip">${escapeHtml(label)}<button class="ui-button ui-button--ghost" type="button" data-admin-partner-filter-reset="${escapeHtml(key)}">×</button></span>`).join('')}<button class="ui-button ui-button--ghost" type="button" data-admin-partner-filter-clear>Сбросить всё</button></div>` : ''}
    </div>
    <div class="admin-summary-strip">Найдено: <strong>${partners.length}</strong> из ${totalPartners.length}</div>
    ${!hasAnyPartners ? `<div class="admin-empty-state"><p>Партнёры пока не добавлены.</p><button class="ui-button ui-button--primary" type="button" data-admin-partner-create${legacyContentDisabledAttr()}>+ Добавить партнёра</button></div>` : ''}
    ${noResults ? `<div class="admin-empty-state"><p>По выбранным фильтрам партнёры не найдены.</p><button class="ui-button ui-button--ghost" type="button" data-admin-partner-filter-clear>Сбросить фильтры</button></div>` : ''}
    ${!noResults && hasAnyPartners ? renderTable(['Партнёр', 'Категории', 'Статус', 'Витрина', 'Услуги', 'Обновлено', 'Действия'], rows, true, 'admin-table--compact admin-table--partners admin-partners-table') : ''}
  </section>
`;
};

const renderPartnersTab = () => {
  if (adminState.selectedPartnerIdForEdit) {
    return renderPartnerEditForm();
  }
  if (adminState.partnerFormOpen) {
    return renderPartnerForm();
  }

  const searchedPartners = filterAdminRows(adminState.partners, adminState.search.partners, [
    'name',
    'city_name',
    'category_slug',
    'category_name',
    'owner_email',
    'phone',
    (partner) => getPartnerCategories(partner).map((category) => `${category.name} ${category.slug || ''}`).join(' '),
    (partner) => searchableBool(partner.is_active),
    (partner) => (partner.is_verified ? 'verified проверен проверенный true' : 'unverified не проверен непроверенный false'),
  ]);

  const partners = filterPartnersRegistry(searchedPartners);

  return `<div class="admin-partners-layout">${renderPartnersList(partners, adminState.partners)}</div>`;
};

const renderAdminOfferAction = (offer) => renderAdminTableActions(`
  <button class="admin-inline-action ui-button ui-button--secondary admin-table-action" type="button" data-admin-offer-edit="${escapeHtml(offer.id)}"${legacyContentDisabledAttr()}>Редактировать</button>
  <label class="admin-inline-action ui-button ui-button--secondary admin-table-action">Загрузить фото<input type="file" accept="image/jpeg,image/png,image/webp" data-admin-offer-image-upload data-offer-id="${escapeHtml(offer.id)}" ${legacyContentDisabledAttr()} /></label>
`);

const renderOfferEditForm = () => {
  const offer = adminState.offers.find((item) => String(item.id) === String(adminState.selectedOfferIdForEdit));
  if (!offer) {
    return '';
  }

  return `
    <form class="admin-form admin-form--inline admin-offer-form" data-admin-form="offerEdit" data-legacy-content-form data-offer-id="${escapeHtml(offer.id)}">
      <h4>Редактировать предложение</h4>
      <label>Название<input name="title" required value="${escapeHtml(offer.title || '')}" /></label>
      <label>Краткая выгода<input name="benefit_text" value="${escapeHtml(offer.benefit_text || '')}" /></label>
      <label>Описание<textarea name="description" rows="3">${escapeHtml(offer.description || '')}</textarea></label>
      <label>Условия<textarea name="conditions" rows="3">${escapeHtml(offer.conditions || '')}</textarea></label>
      <label>Обычная цена<input name="base_price" type="number" step="0.01" value="${escapeHtml(offer.base_price || '')}" /></label>
      <label>Цена участницы<input name="member_price" type="number" step="0.01" value="${escapeHtml(getOfferPricingView(offer).memberPrice || '')}" /></label>
      <label>Экономия<input name="saving_amount" type="number" step="0.01" value="${escapeHtml(getOfferPricingView(offer).savingAmount || '')}" readonly /></label>
      ${renderOfferImageUploader(offer, 'admin')}
      <details class="partner-profile-advanced">
        <summary>URL изображения предложения</summary>
        <p class="helper-text form-message compact-copy">URL сохраняется для проверки.</p>
        <label>URL изображения<input name="image_url" value="${escapeHtml(offer.image_url || '')}" readonly placeholder="/uploads/offer.webp или /assets/offer.webp" /></label>
      </details>
      <label class="checkbox-row"><input name="is_active" type="checkbox" ${offer.is_active ? 'checked' : ''} /> Активно</label>
      <label>Порядок сортировки<input name="sort_order" type="number" value="${escapeHtml(offer.sort_order || 0)}" /></label>
      <div class="admin-form-actions">
        <div class="ui-action-row ui-action-row--right ui-action-row--stack-mobile"><button class="ui-button ui-button--primary" type="submit">Сохранить изменения</button></div>
        <button class="admin-inline-action ui-button ui-button--ghost" type="button" data-admin-offer-edit-cancel>Отмена</button>
      </div>
      <p class="form-message" data-form-message="offerEdit">${escapeHtml(adminState.formMessages.offerEdit || '')}</p>
    </form>
  `;
};

const renderOfferCreateForm = () => `
  <form class="admin-form admin-form--inline admin-offer-form" data-admin-form="offer" data-legacy-content-form>
    <h4>Новое предложение</h4>
    <label>Название предложения<input name="title" required /></label>
    <label>Краткая выгода<input name="benefit_text" /></label>
    <label>Описание<textarea name="description" rows="3"></textarea></label>
    <label>Условия<textarea name="conditions" rows="3"></textarea></label>
    <label>Обычная цена<input name="base_price" type="number" step="0.01" /></label>
    <label>Цена участницы<input name="member_price" type="number" step="0.01" /></label>
    <label>Экономия<input name="saving_amount" type="number" step="0.01" readonly /></label>
    <p class="helper-text form-message compact-copy">Экономия рассчитывается автоматически из обычной цены и цены участницы.</p>
    ${renderOfferImageUploader(null, 'admin')}
    <details class="partner-profile-advanced">
      <summary>URL изображения предложения</summary>
      <p class="helper-text form-message compact-copy">Сначала сохраните, затем загрузите фото.</p>
      <label>URL изображения<input name="image_url" readonly placeholder="/uploads/offer.webp или /assets/offer.webp" /></label>
    </details>
    <label class="checkbox-row"><input name="is_active" type="checkbox" checked /> Активен</label>
    <label>Порядок сортировки<input name="sort_order" type="number" value="0" /></label>
    <button type="submit">Создать предложение</button>
    <p class="form-message" data-form-message="offer">${escapeHtml(adminState.formMessages.offer || '')}</p>
  </form>
`;

const renderOffersPreviewPanel = (offers) => {
  const selectedOffer = adminState.selectedOfferIdForEdit
    ? offers.find((offer) => String(offer.id) === String(adminState.selectedOfferIdForEdit))
    : offers[0];
  const previewOffer = selectedOffer || { is_active: true };
  return `
    <section class="admin-offers-preview-panel">
      <div class="admin-section-heading text-stack"><h4 class="section-title">Предпросмотр привилегии</h4><p class="section-description compact-copy">Компактный вид для клиентки.</p></div>
      ${renderOfferMarketplaceCard(previewOffer, {
        compact: true,
        note: selectedOffer ? 'Preview для клиента' : 'Добавьте первое предложение',
        actionHtml: selectedOffer ? `${renderAdminOfferAction(selectedOffer)}<button type="button" disabled>Получить привилегию</button>` : '<button type="button" disabled>Получить привилегию</button>',
      })}
    </section>
  `;
};

const renderOffersTab = () => {
  const offers = filterAdminRows(adminState.offers, adminState.search.offers, ['title', 'description', 'benefit_text', 'discount_text', 'terms', 'conditions', (offer) => searchableBool(offer.is_active)]);
  return `
    <div class="admin-offers-layout">
      <div class="admin-section-heading text-stack"><p class="section-eyebrow section-kicker">Привилегии</p><h4 class="section-title">Привилегии партнёров</h4><p class="section-description compact-copy">Настройка и предпросмотр предложений для участниц клуба.</p></div>
      <section class="admin-offers-toolbar">
        <label class="admin-select-label">Партнёр${renderPartnerPicker('offers', adminState.selectedPartnerIdForOffers)}</label>
        ${adminState.selectedPartnerIdForOffers ? renderAdminSearch('offers', 'Поиск по предложениям') : ''}
      </section>
      ${adminState.selectedPartnerIdForOffers ? `
        ${renderOffersPreviewPanel(offers)}
        <section class="admin-offers-table-panel">
          <div class="admin-section-heading text-stack"><h4 class="section-title">Таблица предложений</h4><p class="helper-text compact-copy">Кнопки действий собраны справа.</p></div>
          ${renderTable(
            ['Название предложения', 'Краткая выгода', 'Обычная цена', 'Цена участницы', 'Активно', 'Сортировка', 'Действие'],
            offers.map((offer) => [formatValue(offer.title), formatValue(formatPartnerBenefit(offer)), formatValue(getOfferPricingView(offer).basePriceLabel || '—'), formatValue(getOfferPricingView(offer).memberPriceLabel || '—'), renderActiveStatusBadge(offer.is_active), formatValue(offer.sort_order), renderAdminOfferAction(offer)]),
            true,
            'admin-table--compact admin-table--offers',
            adminState.search.offers ? 'Ничего не найдено.' : 'Пока нет данных.',
          )}
        </section>
        <section class="admin-offers-form-panel">
          <div class="admin-section-heading text-stack"><h4 class="section-title">${adminState.selectedOfferIdForEdit ? 'Редактирование' : 'Создание'}</h4><p class="helper-text compact-copy">Поля и фото разделены.</p></div>
          ${adminState.selectedOfferIdForEdit ? renderOfferEditForm() : renderOfferCreateForm()}
        </section>
      ` : '<p class="empty-note">Сначала выберите партнёра.</p>'}
    </div>
  `;
};


const renderContentReviewOfferCard = (offer) => renderOfferMarketplaceCard(
  { ...offer, is_active: false },
  {
    note: `Партнёр: ${offer.partner_name || '—'}`,
    actionHtml: `
      <button class="ui-button ui-button--success" type="button" data-content-review-offer-activate="${escapeHtml(offer.id)}"${legacyContentDisabledAttr()}>Активировать</button>
      <button class="admin-inline-action ui-button ui-button--secondary" type="button" data-content-review-partner-open="${escapeHtml(offer.partner_id)}">Открыть партнёра</button>
    `,
  },
);

const renderContentReviewPhotoCard = (photo) => {
  const safeUrl = isSafePublicAssetUrl(photo.url) ? photo.url : '';
  return `
    <article class="content-review-card">
      <div class="content-review-preview ${safeUrl ? '' : 'content-review-preview--placeholder'}" ${safeUrl ? `style="background-image: url('${escapeHtml(safeUrl)}')" role="img" aria-label="${escapeHtml(photo.alt_text || 'Фото галереи')}"` : 'aria-hidden="true"'}>
        ${safeUrl ? '' : '<span>Фото галереи</span>'}
      </div>
      <div class="content-review-body">
        <span class="section-eyebrow section-kicker">Фото галереи</span>
        <h4>${escapeHtml(photo.partner_name || 'Партнёр')}</h4>
        <dl class="offer-marketplace-meta">
          <div><dt>Alt</dt><dd>${formatValue(photo.alt_text)}</dd></div>
          <div><dt>Сортировка</dt><dd>${formatValue(photo.sort_order)}</dd></div>
          <div><dt>Создано</dt><dd>${formatValue(formatDate(photo.created_at))}</dd></div>
        </dl>
        <div class="content-review-actions ui-card-actions ui-action-row ui-action-row--stack-mobile">
          <button class="ui-button ui-button--success" type="button" data-content-review-photo-activate="${escapeHtml(photo.id)}"${legacyContentDisabledAttr()}>Активировать</button>
          <button class="admin-inline-action ui-button ui-button--secondary" type="button" data-content-review-partner-open="${escapeHtml(photo.partner_id)}">Открыть партнёра</button>
        </div>
      </div>
    </article>
  `;
};

const renderContentReviewSection = (title, items, renderer) => `
  <section class="content-review-section">
    <div class="admin-section-heading text-stack">
      <h4 class="section-title">${escapeHtml(title)}</h4>
      <p class="helper-text compact-copy">${items.length ? `Ожидают проверки: ${items.length}` : 'Новых материалов нет.'}</p>
    </div>
    ${items.length ? `<div class="content-review-grid">${items.map(renderer).join('')}</div>` : '<div class="content-review-empty ui-empty-state">Партнёров на проверке нет.</div>'}
  </section>
`;

const renderContentReviewTab = () => {
  const offers = adminState.contentReview.offers || [];
  const photos = adminState.contentReview.photos || [];
  return `
    <div class="content-review">
      <div class="admin-section-heading admin-page-heading">
        <p class="section-eyebrow section-kicker">Модерация</p>
        <h4 class="section-title">На проверке</h4>
        <p class="section-description compact-copy">Новые предложения и фото перед публикацией.</p>
      </div>
      ${!offers.length && !photos.length ? '<div class="content-review-empty ui-empty-state">Партнёров на проверке нет.</div>' : ''}
      ${renderContentReviewSection('Предложения', offers, renderContentReviewOfferCard)}
      ${renderContentReviewSection('Фото галереи', photos, renderContentReviewPhotoCard)}
      <p class="form-message" data-form-message="contentReview">${escapeHtml(adminState.formMessages.contentReview || '')}</p>
    </div>
  `;
};

const renderAdminQrAction = (link) => renderAdminTableActions(`
  <button class="admin-inline-action ui-button ui-button--secondary admin-table-action" type="button" data-admin-qr-edit="${escapeHtml(link.id)}">Редактировать</button>
`);

const renderQrCreateForm = () => `
  <form class="admin-form admin-form--inline" data-admin-form="qr">
    <h4>Новая QR-ссылка</h4>
    <label>Код ссылки<input name="slug" /></label>
    <label>Целевая ссылка<input name="target_url" /></label>
    <label>Deep link payload / payload<input name="deep_link_payload" /></label>
    <label class="checkbox-row"><input name="is_active" type="checkbox" checked /> Активен</label>
    <button type="submit">Создать QR</button>
    <p class="form-message" data-form-message="qr">${escapeHtml(adminState.formMessages.qr || '')}</p>
  </form>
`;

const renderQrEditForm = () => {
  const link = adminState.qrLinks.find((item) => String(item.id) === String(adminState.selectedQrLinkIdForEdit));
  if (!link) {
    return '';
  }

  return `
    <form class="admin-form admin-form--inline" data-admin-form="qrEdit" data-qr-link-id="${escapeHtml(link.id)}">
      <h4>Редактировать QR-ссылку</h4>
      <label>Slug<input name="slug" value="${escapeHtml(link.slug || '')}" /></label>
      <label>Целевая ссылка<input name="target_url" value="${escapeHtml(link.target_url || '')}" /></label>
      <label>Deep-link payload<input name="deep_link_payload" value="${escapeHtml(link.deep_link_payload || '')}" /></label>
      <label class="checkbox-row"><input name="is_active" type="checkbox" ${link.is_active ? 'checked' : ''} /> Активна</label>
      <div class="admin-form-actions">
        <div class="ui-action-row ui-action-row--right ui-action-row--stack-mobile"><button class="ui-button ui-button--primary" type="submit">Сохранить изменения</button></div>
        <button class="admin-inline-action ui-button ui-button--ghost" type="button" data-admin-qr-edit-cancel>Отмена</button>
      </div>
      <p class="form-message" data-form-message="qrEdit">${escapeHtml(adminState.formMessages.qrEdit || '')}</p>
    </form>
  `;
};


const adminPaymentStatusOptions = [
  { value: '', label: 'Все' },
  { value: 'pending', label: 'Ожидает' },
  { value: 'paid', label: 'Оплачено / на проверке' },
  { value: 'approved', label: 'Подтверждено' },
  { value: 'rejected', label: 'Отклонено' },
];

const getPaymentRequestId = (request) => request?.id ?? request?.payment_request_id ?? request?.request_id;

const getPaymentClientLabel = (request) => {
  const name = request?.display_name || request?.full_name || request?.client_full_name || request?.client_name || request?.client?.full_name || request?.client?.name;
  const userId = request?.client_user_id || request?.user_id || request?.client_id || request?.client?.id;
  return [name, userId ? `user ${userId}` : ''].filter(Boolean).join(' · ') || 'Клиент не указан';
};

const getPaymentAmountLabel = (request) => {
  const amount = request?.amount ?? request?.amount_rub ?? request?.price ?? request?.total_amount;
  const currency = request?.currency || '₽';
  if (amount === null || amount === undefined || amount === '') return '—';
  return `${amount} ${currency}`;
};

const renderAdminPaymentMetaItem = (label, value, trusted = false) => `
  <div><dt>${escapeHtml(label)}</dt><dd>${trusted ? value : formatValue(value)}</dd></div>
`;

const renderAdminPaymentReceipts = (request) => {
  const receipts = Array.isArray(request?.receipts) ? request.receipts : Array.isArray(request?.receipt_urls) ? request.receipt_urls : [];
  if (!receipts.length && !request?.receipt_url) {
    return '<div class="admin-payment-receipts"><strong>Чеки</strong><span>Чеки не приложены.</span></div>';
  }
  const normalizedReceipts = receipts.length ? receipts : [request.receipt_url];
  return `
    <div class="admin-payment-receipts">
      <strong>Чеки</strong>
      <ul>
        ${normalizedReceipts.map((receipt, index) => {
          const url = typeof receipt === 'string' ? receipt : (receipt?.url || receipt?.file_url || receipt?.href || '');
          const label = typeof receipt === 'string' ? `Чек ${index + 1}` : (receipt?.title || receipt?.filename || `Чек ${index + 1}`);
          return url
            ? `<li><a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a></li>`
            : `<li>${formatValue(label)}</li>`;
        }).join('')}
      </ul>
    </div>
  `;
};

const renderAdminPaymentActions = (request) => {
  const status = String(request?.status || '').toLowerCase();
  const requestId = getPaymentRequestId(request);
  if (status === 'paid') {
    return `
      <div class="admin-payment-actions ui-action-row ui-action-row--stack-mobile">
        <label>Дней доступа
          <input type="number" min="1" step="1" value="${escapeHtml(adminState.paymentApprovalDays)}" data-admin-payment-access-days>
        </label>
        <button type="button" class="ui-button ui-button--success" data-admin-payment-approve="${escapeHtml(requestId)}">Подтвердить</button>
        <button type="button" class="admin-inline-action ui-button ui-button--danger admin-inline-action--danger" data-admin-payment-reject="${escapeHtml(requestId)}">Отклонить</button>
      </div>
    `;
  }
  if (status === 'pending') {
    return `
      <div class="admin-payment-actions admin-payment-actions--note ui-action-row ui-action-row--stack-mobile">
        <p>Ожидает отметки клиента “Я оплатил”</p>
        <button type="button" class="admin-inline-action ui-button ui-button--danger admin-inline-action--danger" data-admin-payment-reject="${escapeHtml(requestId)}">Отклонить</button>
      </div>
    `;
  }
  if (status === 'approved') {
    return `<div class="admin-payment-actions admin-payment-actions--note ui-action-row ui-action-row--stack-mobile"><p>Подписка продлена до ${formatValue(formatDate(request?.access_until || request?.subscription_ends_at || request?.ends_at))}</p></div>`;
  }
  if (status === 'rejected') {
    return '<div class="admin-payment-actions admin-payment-actions--note ui-action-row ui-action-row--stack-mobile"><p>Отклонена</p></div>';
  }
  return '<div class="admin-payment-actions admin-payment-actions--note ui-action-row ui-action-row--stack-mobile"><p>Действия недоступны для текущего статуса.</p></div>';
};

const renderAdminPaymentCard = (request) => {
  const requestId = getPaymentRequestId(request);
  const displayName = request?.display_name || request?.full_name || request?.client_full_name || request?.client_name;
  const userId = request?.user_id || request?.client_user_id || request?.client_id;
  const login = request?.user_login || request?.user_email;
  const contactEmail = request?.contact_email;
  const vkUrl = request?.vk_url;
  const vkUserId = request?.vk_user_id || request?.client_vk_user_id;
  return `
    <article class="admin-payment-card ui-card" data-admin-payment-request="${escapeHtml(requestId || '')}">
      <div class="admin-payment-card__header ui-card__header">
        <div>
          <p class="section-kicker">ID ${formatValue(requestId)}</p>
          <h4>${formatValue(getPaymentClientLabel(request))}</h4>
        </div>
        <div class="admin-payment-status">${renderStatusBadge(formatStatus(request?.status))}</div>
      </div>
      <dl class="admin-payment-meta">
        ${renderAdminPaymentMetaItem('Клиент', `${displayName || '—'}${userId ? `\nuser ${userId}` : ''}`)}
        ${renderAdminPaymentMetaItem('Контакты', `${request?.user_phone || '—'}\n${contactEmail || '—'}`)}
        ${renderAdminPaymentMetaItem('VK', vkUrl ? `<a href="${escapeHtml(vkUrl)}" target="_blank" rel="noopener noreferrer">Открыть VK</a>${vkUserId ? `<br><small class="muted-text">id: ${escapeHtml(vkUserId)}</small>` : ''}` : '—', true)}
        ${renderAdminPaymentMetaItem('Login', login || '—')}
        ${renderAdminPaymentMetaItem('Сумма / статус', `${getPaymentAmountLabel(request)}\n${formatStatus(request?.status)}`)}
        ${renderAdminPaymentMetaItem('Город', request?.selected_city_name || '—')}
        ${renderAdminPaymentMetaItem('Создано', formatDate(request?.created_at))}
        ${renderAdminPaymentMetaItem('Обновлено', formatDate(request?.updated_at))}
        ${renderAdminPaymentMetaItem('Подтверждено', formatDate(request?.approved_at))}
        ${renderAdminPaymentMetaItem('Отклонено', formatDate(request?.rejected_at))}
        ${renderAdminPaymentMetaItem('Доступ до', formatDate(request?.access_until || request?.subscription_ends_at || request?.ends_at))}
        ${renderAdminPaymentMetaItem('Комментарий', request?.comment || request?.admin_comment)}
      </dl>
      ${renderAdminPaymentReceipts(request)}
      <div class="admin-payment-actions ui-action-row ui-action-row--stack-mobile"><button type="button" class="admin-inline-action ui-button ui-button--secondary" data-admin-payment-open="${escapeHtml(requestId)}">Открыть детали</button></div>
      ${renderAdminPaymentActions(request)}
    </article>
  `;
};

const renderAdminPaymentRequestsTab = () => `
  <section class="admin-payments">
    <div class="admin-section-heading admin-page-heading">
      <p class="section-eyebrow section-kicker">Оплаты</p>
      <h4>Заявки на оплату</h4>
      <p>Проверяйте ручные оплаты и продлевайте доступ после подтверждения.</p>
    </div>
    <div class="admin-payments-toolbar admin-toolbar">
      <label class="admin-select-label">Статус
        ${renderCustomSelect({
          id: 'admin-payment-status-filter',
          name: 'payment_status',
          value: adminState.paymentRequestsStatusFilter,
          options: adminPaymentStatusOptions,
          placeholder: 'Все',
          label: 'Статус оплаты',
          data: { adminPaymentStatusFilter: true },
          ariaLabel: 'Статус оплаты',
          size: 'compact',
        })}
      </label>
      <button type="button" class="admin-inline-action ui-button ui-button--ghost" data-admin-payment-refresh>Обновить</button>
    </div>
    ${adminState.paymentActionStatus ? `<div class="admin-status admin-status--success" role="status">${escapeHtml(adminState.paymentActionStatus)}</div>` : ''}
    ${adminState.paymentActionError ? `<div class="admin-status admin-status--error" role="alert">${escapeHtml(adminState.paymentActionError)}</div>` : ''}
    ${adminState.selectedPaymentRequest ? `<section class="admin-payment-card ui-card admin-payment-card--details"><div class="admin-section-heading"><h4>Детали заявки ${formatValue(getPaymentRequestId(adminState.selectedPaymentRequest))}</h4><p>Данные загружены через GET /api/v1/admin/payment-requests/{payment_request_id}.</p></div>${renderAdminPaymentCard(adminState.selectedPaymentRequest)}</section>` : ''}
    ${adminState.paymentRequestsLoading ? '<div class="admin-payment-empty">Загружаем заявки на оплату…</div>' : ''}
    ${adminState.paymentRequestsError ? `<div class="admin-payment-empty admin-payment-empty--error">${escapeHtml(adminState.paymentRequestsError)}</div>` : ''}
    ${!adminState.paymentRequestsLoading && !adminState.paymentRequestsError ? (
      adminState.paymentRequests.length
        ? `<div class="admin-payment-grid">${adminState.paymentRequests.map(renderAdminPaymentCard).join('')}</div>`
        : '<div class="admin-payment-empty ui-empty-state">Заявок на оплату пока нет.</div>'
    ) : ''}
  </section>
`;

const renderQrTab = () => {
  const qrLinks = filterAdminRows(adminState.qrLinks, adminState.search.qr, ['slug', 'target_url', 'deep_link_payload', (link) => searchableBool(link.is_active)]);
  const leads = filterAdminRows(adminState.leads, adminState.search.leads, ['partner_name', 'city_name', 'qr_slug', 'target_url', 'deep_link_payload', 'total_clicks']);
  return `
    <div class="admin-section-heading"><h4>QR / лиды</h4><p>QR-ссылки партнёров и агрегированные переходы.</p></div>
    <label class="admin-select-label">Партнёр${renderPartnerPicker('qr', adminState.selectedPartnerIdForQr)}</label>
    ${adminState.selectedPartnerIdForQr ? `
      ${renderAdminSearch('qr', 'Поиск по QR')}
      ${renderTable(
        ['Код ссылки', 'QR-ссылка', 'Целевая ссылка', 'Активна', 'Действие'],
        qrLinks.map((link) => [formatValue(link.slug), link.qr_url ? `<a href="${escapeHtml(link.qr_url)}" target="_blank" rel="noreferrer">${escapeHtml(link.qr_url)}</a>` : '—', formatValue(link.target_url), renderActiveStatusFeminineBadge(link.is_active), renderAdminQrAction(link)]),
        true,
        'admin-table--compact',
        adminState.search.qr ? 'Ничего не найдено.' : 'Пока нет данных.',
      )}
      ${adminState.selectedQrLinkIdForEdit ? renderQrEditForm() : renderQrCreateForm()}
    ` : '<p class="empty-note">Сначала выберите партнёра.</p>'}
    <h4 class="table-title">Лиды партнёров</h4>
    ${renderAdminSearch('leads', 'Поиск по лидам')}
    ${renderTable(['Партнёр', 'Город', 'Код ссылки', 'Лиды / переходы'], leads.map((lead) => [lead.partner_name, lead.city_name, lead.qr_slug, lead.total_clicks]), false, 'admin-table--compact', adminState.search.leads ? 'Ничего не найдено.' : 'Пока нет данных.')}
  `;
};

const renderVerificationsTab = () => {
  const verifications = filterAdminRows(adminState.verifications, adminState.search.verifications, [
    'status',
    'code',
    'partner_name',
    'client_name',
    'client_id',
    'offer_title',
    'created_at',
    'expires_at',
    'confirmed_at',
    (item) => formatDate(item.created_at),
    (item) => formatDate(item.expires_at),
    (item) => formatDate(item.confirmed_at),
  ]);
  return `
    <div class="admin-section-heading"><h4>Подтверждения</h4><p>Последние сессии подтверждения привилегий.</p></div>
    ${renderAdminSearch('verifications', 'Поиск по подтверждениям')}
    ${renderTable(
      ['Статус', 'Код', 'Партнёр', 'Клиент', 'Название предложения', 'Создано', 'Истекает', 'Подтверждено'],
      verifications.map((item) => [renderStatusBadge(formatStatus(item.status)), formatValue(item.code), formatValue(item.partner_name), formatValue(`${item.client_name || '—'} / ${item.client_id}`), formatValue(item.offer_title), formatValue(formatDate(item.created_at)), formatValue(formatDate(item.expires_at)), formatValue(formatDate(item.confirmed_at))]),
      true,
      'admin-table--compact',
      adminState.search.verifications ? 'Ничего не найдено.' : 'Подтверждений пока нет.',
    )}
  `;
};

const getAdminTableCellClass = (header) => {
  if (header === 'Действие') {
    return 'admin-table-cell--actions';
  }

  if (['Описание', 'Название предложения', 'Партнёр', 'Email', 'Телефон', 'Владелец', 'QR-ссылка', 'Целевая ссылка', 'Клиент'].includes(header)) {
    return 'admin-table-cell--wrap';
  }

  return 'admin-table-cell--truncate';
};

const renderTable = (headers, rows, trustedHtml = false, tableModifier = '', emptyMessage = 'Пока нет данных.') => {
  if (!rows.length) {
    return `<div class="empty-note">${escapeHtml(emptyMessage)}</div>`;
  }

  const isGiveawayEntriesTable = tableModifier.split(/\s+/).includes('admin-table--giveaway-entries');
  const tableClassName = ['admin-table', isGiveawayEntriesTable ? 'giveaway-participants-table' : '', tableModifier].filter(Boolean).join(' ');
  const wrapperClassName = ['admin-table-wrap', isGiveawayEntriesTable ? 'giveaway-participants-table-wrapper' : ''].filter(Boolean).join(' ');

  return `
    <div class="${wrapperClassName}">
      <table class="${tableClassName}">
        <thead><tr>${headers.map((header) => `<th class="${getAdminTableCellClass(header)}">${escapeHtml(header)}</th>`).join('')}</tr></thead>
        <tbody>
          ${rows.map((row) => `<tr>${row.map((cell, index) => `<td class="${getAdminTableCellClass(headers[index])}">${trustedHtml ? cell : formatValue(cell)}</td>`).join('')}</tr>`).join('')}
        </tbody>
      </table>
    </div>
  `;
};

const renderSelect = (name, options, required = false, selectedValue = '', emptyLabel = null, config = {}) => renderCustomSelect({
  id: config.id,
  name,
  value: selectedValue,
  options: [
    { value: '', label: emptyLabel || (required ? 'Выберите' : 'Без категории') },
    ...options.map(([value, label]) => ({ value, label })),
  ],
  placeholder: emptyLabel || (required ? 'Выберите' : 'Без категории'),
  label: config.label || name,
  required,
  className: config.className || '',
  data: config.data || {},
  ariaLabel: config.ariaLabel || config.label || name,
});

const renderPartnerPicker = (scope, selectedValue) => renderCustomSelect({
  id: `admin-${scope}-partner-picker`,
  name: 'partner_id',
  value: selectedValue,
  options: [
    { value: '', label: 'Выберите партнёра' },
    ...adminState.partners.map((partner) => ({ value: partner.id, label: partner.name })),
  ],
  placeholder: 'Выберите партнёра',
  label: 'Партнёр',
  data: { partnerPicker: scope },
});

const showAdminDashboard = async (user) => {
  adminState.user = user;
  setLoginMessage();
  setPanelMessage();
  renderAdminLayout();
  await loadActiveTabData();
};

const showPartnerDashboard = async (user) => {
  partnerState.user = user;
  setLoginMessage();
  setPartnerPanelMessage();
  renderPartnerLayout();
  await loadActivePartnerTabData();
};

const showClientDashboard = async (user) => {
  clientState.user = user;
  setLoginMessage();
  setClientPanelMessage();
  renderClientLayout();
  await loadActiveClientTabData();
};

const loadOverview = async () => {
  adminState.overviewPartialError = false;
  const tasks = [loadUsers, loadCities, loadCategories, loadPartners, loadVerifications, loadLeads, loadAdminLandingSettings];
  const results = await Promise.allSettled(tasks.map((task) => task()));
  adminState.overviewPartialError = results.some((result) => result.status === 'rejected');
};

const loadActiveTabData = async () => {
  setPanelMessage();
  renderAdminLayout();

  try {
    if (adminState.activeTab === 'overview') {
      await loadOverview();
    } else if (adminState.activeTab === 'users') {
      await loadUsers();
    } else if (adminState.activeTab === 'cities') {
      await loadCities();
    } else if (adminState.activeTab === 'categories') {
      await loadCategories();
    } else if (adminState.activeTab === 'partners') {
      await ensureAdminDictionaries();
    } else if (adminState.activeTab === 'offers') {
      await ensureAdminDictionaries();
      if (!adminState.selectedPartnerIdForOffers && adminState.partners[0]) {
        adminState.selectedPartnerIdForOffers = String(adminState.partners[0].id);
      }
      await loadOffers();
    } else if (adminState.activeTab === 'contentReview') {
      await Promise.all([ensureAdminDictionaries(), loadContentReview()]);
    } else if (adminState.activeTab === 'paymentRequests') {
      await loadAdminPaymentRequests();
    } else if (adminState.activeTab === 'payments') {
      await Promise.all([loadSubscriptionPlans(), loadAcquiringPayments()]);
    } else if (adminState.activeTab === 'qr') {
      await Promise.all([ensureAdminDictionaries(), loadLeads()]);
      if (!adminState.selectedPartnerIdForQr && adminState.partners[0]) {
        adminState.selectedPartnerIdForQr = String(adminState.partners[0].id);
      }
      await loadQrLinks();
    } else if (adminState.activeTab === 'verifications') {
      await loadVerifications();
    } else if (adminState.activeTab === 'partnerAccess') {
      await Promise.all([ensureAdminDictionaries(), loadPartnerAccesses()]);
    } else if (adminState.activeTab === 'giveaways') {
      await loadGiveaways();
      await syncGiveawayEntriesSelection({ force: true });
    } else if (adminState.activeTab === 'flower') {
      await Promise.all([loadFlowerGarden(), loadGiveaways(), loadUsers()]);
    } else if (adminState.activeTab === 'activity') {
      adminState.activityLoading = true;
      adminState.activityError = '';
      renderAdminLayout();
      await loadAdminActivity();
    }
  } catch (error) {
    if (!getToken()) {
      return;
    }
    setPanelMessage(error.message || 'Не удалось загрузить данные.', 'error');
  }

  renderAdminLayout();
};


const loadActivePartnerTabData = async () => {
  setPartnerPanelMessage();
  renderPartnerLayout();

  try {
    if (partnerState.activeTab === 'overview' || partnerState.activeTab === 'profile' || partnerState.activeTab === 'contacts' || partnerState.activeTab === 'preview') {
      await Promise.all([loadPartnerProfile(), loadPartnerOffers(), loadPartnerPhotos()]);
    } else if (partnerState.activeTab === 'services') {
      await loadPartnerOffers();
    } else if (partnerState.activeTab === 'media') {
      await Promise.all([loadPartnerProfile(), loadPartnerOffers(), loadPartnerPhotos()]);
      if (partnerState.selectedOfferIdForGallery) {
        await loadPartnerOfferPhotos(partnerState.selectedOfferIdForGallery);
      }
    }
  } catch (error) {
    if (!getPartnerToken()) {
      return;
    }
    setPartnerPanelMessage(error.message || 'Не удалось загрузить данные.', 'error');
  }

  renderPartnerLayout();
};

const loadActiveClientTabData = async () => {
  setClientPanelMessage();
  renderClientLayout();

  try {
    if (clientState.activeTab === 'profile') {
      await loadClientProfile();
    } else if (clientState.activeTab === 'catalog') {
      await loadClientCatalog();
    } else if (clientState.activeTab === 'subscription') {
      await loadClientSubscription();
    } else if (clientState.activeTab === 'history') {
      await loadClientVerifications();
    } else if (clientState.activeTab === 'activity') {
      clientState.activityLoading = true;
      clientState.activityError = '';
      renderClientLayout();
      await loadClientActivity();
    } else if (clientState.activeTab === 'savings') {
      await loadClientSavings();
    }
  } catch (error) {
    if (!getClientToken()) {
      return;
    }
    setClientPanelMessage(error.message || 'Не удалось загрузить данные.', 'error');
  }

  renderClientLayout();
};

const buildPartnerProfilePayload = (formData, section = 'profile') => {
  const payload = {};

  if (section === 'profile') {
    payload.description = getOptionalText(formData, 'description');
  }

  if (section === 'contacts') {
    payload.address = getOptionalText(formData, 'address');
    payload.phone = getOptionalText(formData, 'phone');
    payload.website_url = getOptionalText(formData, 'website_url');
    payload.social_url = getOptionalText(formData, 'social_url');
    payload.instagram_url = getOptionalText(formData, 'instagram_url');
    payload.vk_url = getOptionalText(formData, 'vk_url');
    payload.telegram_url = getOptionalText(formData, 'telegram_url');
    payload.whatsapp_url = getOptionalText(formData, 'whatsapp_url');
    payload.map_url = getOptionalText(formData, 'map_url');
    payload.working_hours = getOptionalText(formData, 'working_hours');
  }

  return payload;
};

const submitPartnerProfile = async (form) => {
  const formData = new FormData(form);
  const payload = buildPartnerProfilePayload(formData, 'profile');
  partnerState.profileSaveStatus = 'saving';
  renderPartnerLayout();
  console.debug('[partner-profile] PATCH /api/v1/partners/me payload', payload);
  const updatedProfile = await partnerPatchJson('/api/v1/partners/me', payload);
  console.debug('[partner-profile] PATCH /api/v1/partners/me response', updatedProfile);
  partnerState.profile = mergePartnerProfilePreservingFilledFields(partnerState.profile, updatedProfile);
  await loadPartnerPhotos();
  partnerState.isProfileDirty = false;
  partnerState.profileSaveStatus = 'saved';
};

const submitPartnerContacts = async (form) => {
  const formData = new FormData(form);
  const payload = buildPartnerProfilePayload(formData, 'contacts');
  console.debug('[partner-contacts] PATCH /api/v1/partners/me payload', payload);
  const updatedProfile = await partnerPatchJson('/api/v1/partners/me', payload);
  console.debug('[partner-contacts] PATCH /api/v1/partners/me response', updatedProfile);
  partnerState.profile = mergePartnerProfilePreservingFilledFields(partnerState.profile, updatedProfile);
};


const calculateDiscountPercentFromPrices = (formData) => {
  const basePrice = parseMoneyValue(formData.get('base_price'));
  const memberPrice = parseMoneyValue(formData.get('member_price'));
  if (!Number.isFinite(basePrice) || !Number.isFinite(memberPrice) || basePrice <= 0 || memberPrice < 0 || memberPrice >= basePrice) return null;
  return ((basePrice - memberPrice) / basePrice * 100).toFixed(2);
};

const buildPartnerOfferPayload = (formData) => ({
  title: getOptionalText(formData, 'title'),
  benefit_text: getOptionalText(formData, 'benefit_text'),
  description: getOptionalText(formData, 'description'),
  conditions: getOptionalText(formData, 'conditions'),
  base_price: decimalOrNull(formData, 'base_price'),
  discount_percent: calculateDiscountPercentFromPrices(formData),
  image_url: getOptionalText(formData, 'image_url'),
  is_active: formData.has('is_active'),
  sort_order: Number(formData.get('sort_order') || 0),
});

const submitPartnerOffer = async (form) => {
  const formData = new FormData(form);
  await partnerPostJson('/api/v1/partners/me/offers', buildPartnerOfferPayload(formData));
  setPartnerFormMessage('offer', 'Предложение отправлено на проверку. После активации администратором оно появится у клиентов.');
  setPartnerPanelMessage('Предложение отправлено на проверку. После активации администратором оно появится у клиентов.', 'success');
  form.reset();
  await loadPartnerOffers();
};

const submitPartnerOfferEdit = async (form) => {
  const formData = new FormData(form);
  await partnerPatchJson(`/api/v1/partners/me/offers/${form.dataset.offerId}`, buildPartnerOfferPayload(formData));
  partnerState.selectedOfferIdForEdit = '';
  await loadPartnerOffers();
};

const handlePartnerFormSubmit = async (form) => {
  const formType = form.dataset.partnerForm;
  const shouldRestoreScroll = ['profile', 'contacts', 'offer', 'offerEdit'].includes(formType);
  const preservedScrollY = shouldRestoreScroll ? window.scrollY : null;
  setPartnerFormMessage(formType);

  try {
    if (formType === 'profile') {
      await submitPartnerProfile(form);
    } else if (formType === 'contacts') {
      await submitPartnerContacts(form);
    } else if (formType === 'offer') {
      await submitPartnerOffer(form);
    } else if (formType === 'offerEdit') {
      await submitPartnerOfferEdit(form);
    }
    if (formType !== 'offer') {
      setPartnerFormMessage(formType, 'Сохранено.');
      setPartnerPanelMessage('Сохранено.', 'success');
    }
  } catch (error) {
    if (formType === 'profile') {
      partnerState.profileSaveStatus = 'dirty';
    }
    setPartnerFormMessage(formType, error.message || 'Не удалось сохранить.');
    setPartnerPanelMessage(error.message || 'Не удалось сохранить.', 'error');
  }

  renderPartnerLayout();
  if (shouldRestoreScroll && Number.isFinite(preservedScrollY)) {
    requestAnimationFrame(() => window.scrollTo({ top: preservedScrollY, behavior: 'auto' }));
  }
};

const submitClientProfile = async (form) => {
  const formData = new FormData(form);
  const selectedCityId = String(formData.get('selected_city_id') || '').trim();
  await clientPatchJson('/api/v1/clients/me', {
    full_name: getOptionalText(formData, 'full_name'),
    selected_city_id: selectedCityId ? Number(selectedCityId) : null,
  });
  await loadClientProfile();
};

const submitClientCatalogFilters = async (form) => {
  const formData = new FormData(form);
  clientState.catalogFilters = {
    q: String(formData.get('q') || '').trim(),
    category_slug: String(formData.get('category_slug') || '').trim(),
    city_slug: String(formData.get('city_slug') || '').trim(),
  };
  await loadClientCatalog();
};

const handleClientFormSubmit = async (form) => {
  const formType = form.dataset.clientForm;
  setClientFormMessage(formType);

  try {
    if (formType === 'profile') {
      await submitClientProfile(form);
    } else if (formType === 'catalog') {
      await submitClientCatalogFilters(form);
    }
    setClientFormMessage(formType, 'Сохранено.');
    setClientPanelMessage(formType === 'catalog' ? 'Каталог обновлён.' : 'Сохранено.', 'success');
  } catch (error) {
    setClientFormMessage(formType, error.message || 'Не удалось сохранить.');
    setClientPanelMessage(error.message || 'Не удалось сохранить.', 'error');
  }

  renderClientLayout();
};

const createClientVerification = async (partnerId, offerId = null) => {
  try {
    clientState.latestVerification = await clientPostJson(`/api/v1/clients/partners/${partnerId}/verify`, {
      ...(offerId ? { offer_id: Number(offerId) } : {}),
      source: 'web',
    });
    setClientPanelMessage('Привилегия активирована. Покажите код партнёру.', 'success');
    resetClientPartnerModalState();
  } catch (error) {
    setClientPanelMessage(formatPrivilegeErrorMessage(error.message), 'error');
  }

  renderClientLayout();
};

const createClientVkLinkCode = async () => {
  clientState.vkLinkStatus = '';
  clientState.vkLinkMessage = '';

  try {
    clientState.vkLinkCode = await clientPostJson('/api/v1/clients/me/vk-link-codes');
    clientState.vkLinkStatus = 'success';
    clientState.vkLinkMessage = 'Код VK создан.';
  } catch (error) {
    if (error.message === 'Сессия клиента истекла. Войдите снова.') {
      return;
    }
    clientState.vkLinkStatus = 'error';
    clientState.vkLinkMessage = 'Не удалось создать код VK. Попробуйте позже.';
  }

  renderClientLayout();
};

const togglePartnerOffer = async (offerId) => {
  const offer = partnerState.offers.find((item) => String(item.id) === String(offerId));
  if (!offer) {
    return;
  }

  try {
    await partnerPatchJson(`/api/v1/partners/me/offers/${offerId}`, { is_active: !offer.is_active });
    await loadPartnerOffers();
    setPartnerPanelMessage(offer.is_active ? 'Предложение скрыто.' : 'Ожидает активации администратором.', 'success');
  } catch (error) {
    setPartnerPanelMessage(error.message || 'Не удалось обновить предложение.', 'error');
  }

  renderPartnerLayout();
};

const confirmPartnerVerification = async (verificationId) => {
  try {
    await partnerPostJson(`/api/v1/partners/me/verifications/${verificationId}/confirm`);
    await loadPartnerVerifications();
    setPartnerPanelMessage('Подтверждение выполнено.', 'success');
  } catch (error) {
    setPartnerPanelMessage(formatPrivilegeErrorMessage(error.message), 'error');
  }

  renderPartnerLayout();
};

const getOptionalText = (formData, name) => {
  const value = String(formData.get(name) || '').trim();
  return value || null;
};

const buildCityPayload = (formData) => ({
  name: getOptionalText(formData, 'name'),
  slug: getOptionalText(formData, 'slug'),
  sort_order: Number(formData.get('sort_order') || 0),
  is_active: formData.has('is_active'),
});

const buildCategoryPayload = (formData) => ({
  name: getOptionalText(formData, 'name'),
  slug: getOptionalText(formData, 'slug'),
  sort_order: Number(formData.get('sort_order') || 0),
  is_active: formData.has('is_active'),
});

const submitCity = async (form) => {
  if (guardLegacyContentWrite()) return;
  const formData = new FormData(form);
  await postJson('/api/v1/admin/cities', buildCityPayload(formData));
  form.reset();
  await loadCities();
};

const submitCityEdit = async (form) => {
  if (guardLegacyContentWrite()) return;
  const cityId = form.dataset.cityId;
  const formData = new FormData(form);
  await patchJson(`/api/v1/admin/cities/${cityId}`, buildCityPayload(formData));
  await loadCities();
};

const submitCategory = async (form) => {
  if (guardLegacyContentWrite()) return;
  const formData = new FormData(form);
  await postJson('/api/v1/admin/categories', buildCategoryPayload(formData));
  form.reset();
  await loadCategories();
};

const submitCategoryEdit = async (form) => {
  if (guardLegacyContentWrite()) return;
  const categoryId = form.dataset.categoryId;
  const formData = new FormData(form);
  await patchJson(`/api/v1/admin/categories/${categoryId}`, buildCategoryPayload(formData));
  await loadCategories();
};

const toggleCategoryActive = async (categoryId) => {
  if (guardLegacyContentWrite()) return;
  const category = adminState.categories.find((item) => String(item.id) === String(categoryId));
  if (!category) {
    return;
  }

  const confirmationText = category.is_active ? 'Деактивировать категорию?' : 'Активировать категорию?';
  if (!window.confirm(confirmationText)) {
    return;
  }

  try {
    await patchJson(`/api/v1/admin/categories/${categoryId}`, { is_active: category.is_active ? false : true });
    await loadCategories();
    setPanelMessage(category.is_active ? 'Категория деактивирована.' : 'Категория активирована.', 'success');
  } catch (error) {
    setPanelMessage(error.message || 'Не удалось обновить категорию.', 'error');
  }

  renderAdminLayout();
};

const toggleCityActive = async (cityId) => {
  if (guardLegacyContentWrite()) return;
  const city = adminState.cities.find((item) => String(item.id) === String(cityId));
  if (!city) {
    return;
  }

  const confirmationText = city.is_active ? 'Убрать город из активных?' : 'Активировать город?';
  if (!window.confirm(confirmationText)) {
    return;
  }

  try {
    await patchJson(`/api/v1/admin/cities/${cityId}`, { is_active: city.is_active ? false : true });
    await loadCities();
    setPanelMessage(city.is_active ? 'Город деактивирован.' : 'Город активирован.', 'success');
  } catch (error) {
    setPanelMessage(error.message || 'Не удалось обновить город.', 'error');
  }

  renderAdminLayout();
};

const submitUser = async (form) => {
  const formData = new FormData(form);
  await postJson('/api/v1/admin/users', {
    email: getOptionalText(formData, 'email'),
    phone: getOptionalText(formData, 'phone'),
    password: String(formData.get('password') || ''),
    role: getOptionalText(formData, 'role'),
    is_active: formData.has('is_active'),
  });
  form.reset();
  await loadUsers();
};

const toggleUserActive = async (userId) => {
  const currentUser = adminState.users.find((item) => String(item.id) === String(userId));
  if (!currentUser) {
    return;
  }

  try {
    await patchJson(`/api/v1/admin/users/${userId}`, {
      is_active: !currentUser.is_active,
    });
    await loadUsers();
    setPanelMessage(currentUser.is_active ? 'Пользователь заблокирован.' : 'Пользователь активирован.', 'success');
  } catch (error) {
    setPanelMessage(error.message || 'Не удалось обновить пользователя.', 'error');
  }

  renderAdminLayout();
};


const deleteUser = async (userId) => {
  const confirmationText = 'Вы уверены? Будет удалена вся информация по выбранному пользователю. Действие нельзя отменить.';
  if (!window.confirm(confirmationText)) {
    return;
  }

  try {
    await deleteJson(`/api/v1/admin/users/${userId}`);
    adminState.users = adminState.users.filter((item) => String(item.id) !== String(userId));
    setPanelMessage('Пользователь удалён.', 'success');
  } catch (error) {
    setPanelMessage(error.message || 'Не удалось удалить пользователя. Попробуйте позже.', 'error');
  }

  renderAdminLayout();
};

const getAdminPartnerPayloadCategoryIds = (formData, selectedCategoryIds = null) => {
  const rawCategoryIds = Array.isArray(selectedCategoryIds) ? selectedCategoryIds : formData.getAll('category_ids');
  return rawCategoryIds
    .map((id) => Number(String(id || '').trim()))
    .filter((id) => Number.isInteger(id) && id > 0);
};

const buildAdminPartnerPayload = (formData, selectedCategoryIds = null) => ({
  city_id: Number(formData.get('city_id')),
  category_slug: getOptionalText(formData, 'category_slug'),
  owner_user_id: formData.get('owner_user_id') ? Number(formData.get('owner_user_id')) : null,
  name: getOptionalText(formData, 'name'),
  description: getOptionalText(formData, 'description'),
  address: getOptionalText(formData, 'address'),
  phone: getOptionalText(formData, 'phone'),
  website_url: getOptionalText(formData, 'website_url'),
  social_url: getOptionalText(formData, 'social_url'),
  instagram_url: getOptionalText(formData, 'instagram_url'),
  vk_url: getOptionalText(formData, 'vk_url'),
  telegram_url: getOptionalText(formData, 'telegram_url'),
  whatsapp_url: getOptionalText(formData, 'whatsapp_url'),
  map_url: getOptionalText(formData, 'map_url'),
  working_hours: getOptionalText(formData, 'working_hours'),
  logo_url: getOptionalText(formData, 'logo_url'),
  cover_url: getOptionalText(formData, 'cover_url'),
  is_active: formData.has('is_active'),
  is_verified: formData.has('is_verified'),
  sort_order: Number(formData.get('sort_order') || 0),
  category_ids: getAdminPartnerPayloadCategoryIds(formData, selectedCategoryIds),
});

const submitPartner = async (form) => {
  if (guardLegacyContentWrite()) return;
  const selectedCategoryIds = captureAdminPartnerCategoryDraft(form);
  const formData = new FormData(form);
  const createdPartner = await postJson('/api/v1/admin/partners', buildAdminPartnerPayload(formData, selectedCategoryIds));
  resetAdminPartnerCategoryDraft('');
  await loadPartners();
  return createdPartner;
};

const submitPartnerEdit = async (form) => {
  if (guardLegacyContentWrite()) return;
  const partnerId = form.dataset.partnerId;
  const selectedCategoryIds = captureAdminPartnerCategoryDraft(form);
  const formData = new FormData(form);
  const updatedPartner = await patchJson(`/api/v1/admin/partners/${partnerId}`, buildAdminPartnerPayload(formData, selectedCategoryIds));
  adminState.partners = adminState.partners.map((partner) => String(partner.id) === String(partnerId) ? updatedPartner : partner);
  resetAdminPartnerCategoryDraft(partnerId);
  await loadPartners();
};

const decimalOrNull = (formData, name) => {
  const value = String(formData.get(name) || '').trim();
  return value || null;
};

const buildOfferTextPayload = (formData) => ({
  title: getOptionalText(formData, 'title'),
  benefit_text: getOptionalText(formData, 'benefit_text'),
  description: getOptionalText(formData, 'description'),
  conditions: getOptionalText(formData, 'conditions'),
  base_price: decimalOrNull(formData, 'base_price'),
  discount_percent: calculateDiscountPercentFromPrices(formData),
  image_url: getOptionalText(formData, 'image_url'),
  sort_order: Number(formData.get('sort_order') || 0),
  is_active: formData.has('is_active'),
});

const submitOffer = async (form) => {
  if (guardLegacyContentWrite()) return;
  const formData = new FormData(form);
  await postJson(`/api/v1/admin/partners/${adminState.selectedPartnerIdForOffers}/offers`, buildOfferTextPayload(formData));
  form.reset();
  await loadOffers();
};

const submitOfferEdit = async (form) => {
  if (guardLegacyContentWrite()) return;
  const offerId = form.dataset.offerId;
  const formData = new FormData(form);
  await patchJson(`/api/v1/admin/offers/${offerId}`, buildOfferTextPayload(formData));
  await loadOffers();
};

const buildQrPayload = (formData) => ({
  slug: getOptionalText(formData, 'slug'),
  target_url: getOptionalText(formData, 'target_url'),
  deep_link_payload: getOptionalText(formData, 'deep_link_payload'),
  is_active: formData.has('is_active'),
});

const submitQr = async (form) => {
  const formData = new FormData(form);
  await postJson(`/api/v1/admin/partners/${adminState.selectedPartnerIdForQr}/qr-links`, buildQrPayload(formData));
  form.reset();
  await loadQrLinks();
  await loadLeads();
};

const submitQrEdit = async (form) => {
  const qrLinkId = form.dataset.qrLinkId;
  const formData = new FormData(form);
  await patchJson(`/api/v1/admin/qr-links/${qrLinkId}`, buildQrPayload(formData));
  await loadQrLinks();
  await loadLeads();
};

const uploadAdminPartnerPhoto = async (partnerId, file) => {
  if (guardLegacyContentWrite()) return;
  const body = new FormData();
  body.append('file', file);
  const response = await apiFetch(`/api/v1/admin/partners/${partnerId}/photos`, { method: 'POST', body });
  await loadAdminPartnerPhotos(partnerId);
  return response;
};

const uploadPartnerPhoto = async (file) => {
  const body = new FormData();
  body.append('file', file);
  const response = await partnerApiFetch('/api/v1/partners/me/photos', { method: 'POST', body });
  await loadPartnerPhotos();
  return response;
};

const buildPartnerPhotoPayload = (formData) => ({
  alt_text: getOptionalText(formData, 'alt_text'),
  sort_order: Number(formData.get('sort_order') || 0),
  is_active: formData.has('is_active'),
});

const submitAdminPartnerPhoto = async (form) => {
  if (guardLegacyContentWrite()) return;
  await patchJson(`/api/v1/admin/partner-photos/${form.dataset.photoId}`, buildPartnerPhotoPayload(new FormData(form)));
  await loadAdminPartnerPhotos(adminState.selectedPartnerIdForEdit);
};

const submitPartnerPhoto = async (form) => {
  await partnerPatchJson(`/api/v1/partners/me/photos/${form.dataset.photoId}`, buildPartnerPhotoPayload(new FormData(form)));
  await loadPartnerPhotos();
};

const hideAdminPartnerPhoto = async (photoId) => {
  if (guardLegacyContentWrite()) return;
  await patchJson(`/api/v1/admin/partner-photos/${photoId}`, { is_active: false });
  await loadAdminPartnerPhotos(adminState.selectedPartnerIdForEdit);
};

const hidePartnerPhoto = async (photoId) => {
  await partnerPatchJson(`/api/v1/partners/me/photos/${photoId}`, { is_active: false });
  await loadPartnerPhotos();
};

const clearPartnerProfileImage = async (kind) => {
  const response = await partnerApiFetch(`/api/v1/partners/me/images/${kind}`, { method: 'DELETE' });
  if (partnerState.profile) partnerState.profile[`${kind}_url`] = null;
  await loadPartnerProfile();
  return response;
};

const deletePartnerPhoto = async (photoId) => {
  await partnerApiFetch(`/api/v1/partners/me/photos/${photoId}`, { method: 'DELETE' });
  await loadPartnerPhotos();
};
const uploadPartnerOfferPhoto = async (offerId, file) => {
  const body = new FormData();
  body.append('file', file);
  const response = await partnerApiFetch(`/api/v1/partners/me/offers/${offerId}/photos`, { method: 'POST', body });
  await loadPartnerOfferPhotos(offerId);
  await loadPartnerOffers();
  return response;
};
const updatePartnerOfferPhoto = async (offerId, photoId, payload) => {
  await partnerPatchJson(`/api/v1/partners/me/offers/${offerId}/photos/${photoId}`, payload);
  await loadPartnerOfferPhotos(offerId);
  await loadPartnerOffers();
};
const deletePartnerOfferPhoto = async (offerId, photoId) => {
  await partnerApiFetch(`/api/v1/partners/me/offers/${offerId}/photos/${photoId}`, { method: 'DELETE' });
  await loadPartnerOfferPhotos(offerId);
  await loadPartnerOffers();
};

const clearPartnerOfferImage = async (offerId) => {
  const response = await partnerApiFetch(`/api/v1/partners/me/offers/${offerId}/image`, { method: 'DELETE' });
  await loadPartnerOffers();
  return response;
};


const activateContentReviewOffer = async (offerId) => {
  if (guardLegacyContentWrite()) return;
  await patchJson(`/api/v1/admin/offers/${offerId}`, { is_active: true });
  await loadContentReview();
  if (adminState.selectedPartnerIdForOffers) {
    await loadOffers();
  }
};

const activateContentReviewPhoto = async (photoId) => {
  if (guardLegacyContentWrite()) return;
  await patchJson(`/api/v1/admin/partner-photos/${photoId}`, { is_active: true });
  await loadContentReview();
  if (adminState.selectedPartnerIdForEdit) {
    await loadAdminPartnerPhotos(adminState.selectedPartnerIdForEdit);
  }
};

const uploadAdminPartnerImage = async (partnerId, kind, file) => {
  if (guardLegacyContentWrite()) return;
  const body = new FormData();
  body.append('file', file);
  const response = await apiFetch(`/api/v1/admin/partners/${partnerId}/images?kind=${kind}`, {
    method: 'POST',
    body,
  });
  await loadPartners();
  const selectedPartner = adminState.partners.find((item) => String(item.id) === String(partnerId));
  if (selectedPartner && response?.url) {
    selectedPartner[`${kind}_url`] = response.url;
  }
  return response;
};

const uploadPartnerProfileImage = async (kind, file) => {
  const body = new FormData();
  body.append('file', file);
  const response = await partnerApiFetch(`/api/v1/partners/me/images?kind=${kind}`, {
    method: 'POST',
    body,
  });
  if (partnerState.profile && response?.url) {
    partnerState.profile[`${kind}_url`] = response.url;
  }
  await loadPartnerProfile();
  return response;
};
const uploadAdminOfferImage = async (offerId, file) => {
  if (guardLegacyContentWrite()) return;
  const body = new FormData();
  body.append('file', file);
  const response = await apiFetch(`/api/v1/admin/offers/${offerId}/image`, {
    method: 'POST',
    body,
  });
  if (response?.url) {
    const offer = adminState.offers.find((item) => String(item.id) === String(offerId));
    if (offer) {
      offer.image_url = response.url;
    }
  }
  await loadOffers();
  return response;
};

const uploadPartnerOfferImage = async (offerId, file) => {
  const body = new FormData();
  body.append('file', file);
  const response = await partnerApiFetch(`/api/v1/partners/me/offers/${offerId}/image`, {
    method: 'POST',
    body,
  });
  if (response?.url) {
    const offer = partnerState.offers.find((item) => String(item.id) === String(offerId));
    if (offer) {
      offer.image_url = response.url;
    }
  }
  await loadPartnerOffers();
  return response;
};



const buildLandingSettingsPayload = (formData) => ({
  members_count_base: Number(formData.get('members_count_base') || 0),
  partners_count_display: Number(formData.get('partners_count_display') || 0),
  savings_total: Number(formData.get('savings_total') || 0),
});

const getGiveawayItemsFromForm = (form) => Array.from(form.querySelectorAll('[data-giveaway-prize-row]')).map((row, index) => ({
  title: String(row.querySelector('[name="giveaway_item_title"]')?.value || '').trim(),
  description: String(row.querySelector('[name="giveaway_item_description"]')?.value || '').trim(),
  sort_order: Number(row.querySelector('[name="giveaway_item_sort_order"]')?.value || index),
  is_active: row.querySelector('input[type="checkbox"]')?.checked !== false,
})).filter((item) => item.title);

const submitLandingSettings = async (form) => {
  const formData = new FormData(form);
  adminState.landingSettingsSaving = true;
  adminState.landingSettings = await patchJson('/api/v1/admin/landing-settings', buildLandingSettingsPayload(formData));
  adminState.landingSettingsSaving = false;
};

const submitLandingGiveaway = async (form) => {
  const formData = new FormData(form);
  adminState.landingSettingsSaving = true;
  adminState.formMessages.landingGiveaway = 'Сохранение…';
  renderAdminLayout();
  adminState.landingSettings = await patchJson('/api/v1/admin/landing-settings', {
    giveaway_title: getOptionalText(formData, 'giveaway_title'),
    giveaway_current: getOptionalText(formData, 'giveaway_current'),
    giveaway_subtitle: getOptionalText(formData, 'giveaway_subtitle'),
    giveaway_empty_text: getOptionalText(formData, 'giveaway_empty_text'),
    giveaway_items: getGiveawayItemsFromForm(form),
  });
  adminState.landingSettingsSaving = false;
  adminState.formMessages.landingGiveaway = 'Сохранено.';
};

const handleAdminFormSubmit = async (form) => {
  const formType = form.dataset.adminForm;
  let savedEntity = null;
  let successMessage = 'Сохранено.';
  const message = form.querySelector(`[data-form-message="${formType}"]`);
  setFormMessage(formType);
  if (message) {
    message.textContent = '';
  }

  try {
    if (formType === 'user') {
      await submitUser(form);
    } else if (formType === 'city') {
      await submitCity(form);
    } else if (formType === 'cityEdit') {
      await submitCityEdit(form);
    } else if (formType === 'category') {
      await submitCategory(form);
    } else if (formType === 'categoryEdit') {
      await submitCategoryEdit(form);
    } else if (formType === 'partner') {
      savedEntity = await submitPartner(form);
    } else if (formType === 'partnerEdit') {
      await submitPartnerEdit(form);
    } else if (formType === 'offer') {
      await submitOffer(form);
    } else if (formType === 'offerEdit') {
      await submitOfferEdit(form);
    } else if (formType === 'qr') {
      await submitQr(form);
    } else if (formType === 'qrEdit') {
      await submitQrEdit(form);
    } else if (formType === 'landingSettings') {
      await submitLandingSettings(form);
    } else if (formType === 'landingGiveaway') {
      await submitLandingGiveaway(form);
    } else if (formType === 'partnerAccess') {
      const data = new FormData(form);
      await postJson('/api/v1/admin/partner-accesses', {
        partner_id: Number(data.get('partner_id')),
        provider: String(data.get('provider') || ''),
        provider_user_id: String(data.get('provider_user_id') || '').trim(),
        display_name: String(data.get('display_name') || '').trim(),
        username: getOptionalText(data, 'username'),
        is_active: true,
      });
      await loadPartnerAccesses();
      form.reset();
    } else if (formType === 'paymentRefund') {
      const data = new FormData(form);
      const amount = Number(data.get('amount'));
      const reason = String(data.get('reason') || '').trim();
      if (!window.confirm(`Вернуть ${amount} ₽? Причина: ${reason}`)) return;
      await postJson(`/api/v1/admin/payments/${Number(data.get('payment_id'))}/refund`, { amount, reason });
      await loadAcquiringPayments();
      successMessage = 'Возврат отправлен в Точку и записан в аудит.';
    } else if (formType === 'subscriptionPlanPrice') {
      const data = new FormData(form);
      const planId = Number(data.get('plan_id'));
      const price = Number(data.get('price'));
      if (!Number.isFinite(price) || price <= 0) {
        throw new Error('Укажите цену больше 0 ₽.');
      }
      await patchJson(`/api/v1/admin/subscription-plans/${planId}`, { price });
      await loadSubscriptionPlans();
      successMessage = `Цена подписки изменена на ${price.toLocaleString('ru-RU', { maximumFractionDigits: 2 })} ₽.`;
    } else if (formType === 'flowerGardenSettings') {
      const data = new FormData(form);
      adminState.flowerSettings = await patchJson('/api/v1/admin/flower/settings', {
        placement_mode: String(data.get('placement_mode') || 'random'), manual_position: String(data.get('manual_position') || 'top_right'), daily_petals: Number(data.get('daily_petals') || 1),
      });
    } else if (formType === 'flowerPetalAward') {
      const data = new FormData(form);
      const result = await postJson('/api/v1/admin/flower/petals/award', {
        user_id: Number(data.get('user_id')),
        petals: Number(data.get('petals')),
        note: String(data.get('note') || '').trim(),
      });
      form.reset();
      successMessage = `Начислено ${result.petals}. Теперь у участницы ${result.total_petals} лепестков в этом месяце.`;
    } else if (formType === 'flowerPetalRevoke') {
      const data = new FormData(form);
      const petals = Number(data.get('petals'));
      const userLabel = form.querySelector('[name="user_id"] option:checked')?.textContent || 'выбранной участницы';
      if (!window.confirm(`Забрать ${petals} лепестков у ${userLabel}?`)) return;
      const result = await postJson('/api/v1/admin/flower/petals/revoke', {
        user_id: Number(data.get('user_id')),
        petals,
        note: String(data.get('note') || '').trim(),
      });
      form.reset();
      successMessage = `Списано ${result.petals_removed}. Теперь у участницы ${result.total_petals} лепестков в этом месяце.`;
    } else if (formType === 'flowerSpecialTask') {
      const data = new FormData(form);
      await postJson('/api/v1/admin/flower/special-tasks', { title: String(data.get('title') || '').trim(), description: getOptionalText(data, 'description'), petals: Number(data.get('petals') || 5), starts_on: String(data.get('starts_on') || ''), ends_on: String(data.get('ends_on') || ''), is_active: true });
      await loadFlowerGarden();
      form.reset();
    } else if (formType === 'flowerSpecialQuestion') {
      const data = new FormData(form);
      const taskId = Number(data.get('task_id'));
      const options = String(data.get('options') || '').split('\n').map((item) => item.trim()).filter(Boolean);
      await postJson(`/api/v1/admin/flower/special-tasks/${taskId}/questions`, { prompt: String(data.get('prompt') || '').trim(), options });
      await loadFlowerGarden();
    } else if (formType === 'flowerSettle') {
      const data = new FormData(form);
      const rewards = await postJson('/api/v1/admin/flower/settle', { month: `${data.get('month')}-01`, giveaway_id: Number(data.get('giveaway_id')) });
      successMessage = `Готово. Награды начислены: ${Array.isArray(rewards) ? rewards.length : 0}.`;
    }
    setFormMessage(formType, successMessage);
    if (formType === 'partner' || formType === 'partnerEdit') {
      if (formType === 'partner') {
        if (savedEntity?.id) adminState.selectedPartnerIdForEdit = String(savedEntity.id);
      }
      adminState.partnerFormOpen = false;
      adminState.partnerFormInlineError = '';
    }
    setPanelMessage(successMessage, 'success');
    renderAdminLayout();
  } catch (error) {
    setFormMessage(formType, error.message || 'Не удалось сохранить.');
    if (message) {
      message.textContent = adminState.formMessages[formType];
    }
    setPanelMessage(error.message || 'Не удалось сохранить.', 'error');
  }

  renderAdminLayout();
};


const handlePasswordSetupSubmit = async (form) => {
  const message = document.querySelector('[data-password-setup-message]');
  if (message) {
    message.textContent = '';
  }
  const { setupToken, login } = getPasswordSetupParams();
  const formData = new FormData(form);
  const password = String(formData.get('password') || '');
  const passwordConfirm = String(formData.get('password_confirm') || '');

  try {
    const response = await fetch('/api/v1/auth/password-setup/complete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token: setupToken,
        password,
        password_confirm: passwordConfirm,
      }),
    });

    if (!response.ok) {
      throw new Error('Password setup failed');
    }

    await response.json();
    form.reset();
    if (message) {
      message.textContent = 'Пароль установлен. Теперь войдите в личный кабинет.';
    }
    const nextUrl = new URL(window.location.href);
    nextUrl.searchParams.delete('setup_token');
    window.history.replaceState({}, '', `${nextUrl.pathname}${nextUrl.search}${nextUrl.hash}`);
    renderPublicApp();
    setLoginMode('client');
    const loginInput = document.querySelector('[data-login-form] input[name="email"]');
    if (loginInput && login) {
      loginInput.value = login;
    }
    setLoginMessage('Пароль установлен. Теперь войдите в личный кабинет.');
  } catch (error) {
    if (message) {
      message.textContent = 'Ссылка недействительна или истекла. Запросите новую ссылку в VK-боте.';
    }
  }
};

const handleLoginSubmit = async (form) => {
  setLoginMessage();

  const formData = new FormData(form);
  const loginValue = String(formData.get('email') || '').trim();
  const password = String(formData.get('password') || '');

  try {
    if (activeLoginMode === 'partner' || activeLoginMode === 'client') {
      const response = await fetch('/api/v1/auth/user-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ login: loginValue, password }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      const expectedRole = activeLoginMode;
      const tokenKey = expectedRole === 'partner' ? partnerTokenKey : clientTokenKey;
      localStorage.setItem(tokenKey, data.access_token);

      if (data.user?.role !== expectedRole) {
        if (expectedRole === 'partner') {
          clearPartnerToken();
        } else {
          clearClientToken();
        }
        showLoginForm();
        setLoginMode(expectedRole);
        setLoginMessage(expectedRole === 'partner' ? 'Этот вход доступен только партнёрам' : 'Этот вход доступен только клиентам');
        return;
      }

      form.reset();
      if (expectedRole === 'partner') {
        await showPartnerDashboard(data.user);
      } else {
        await showClientDashboard(data.user);
      }
      return;
    }

    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: loginValue, password }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    localStorage.setItem(authTokenKey, data.access_token);
    form.reset();
    await showAdminDashboard(data.user);
  } catch (error) {
    if (activeLoginMode === 'partner') {
      clearPartnerToken();
      showLoginForm();
      setLoginMode('partner');
    } else if (activeLoginMode === 'client') {
      clearClientToken();
      showLoginForm();
      setLoginMode('client');
    } else {
      clearToken();
      showLoginForm();
      setLoginMode('admin');
    }
    setLoginMessage('Неверный логин или пароль');
  }
};


const triggerPartnerUploadInput = (button) => {
  const disabledMessage = button.dataset.partnerUploadDisabledMessage;
  if (button.disabled) {
    if (disabledMessage) {
      const statusKey = button.dataset.partnerUploadKind === 'offer'
        ? 'offerImage:new'
        : button.dataset.partnerUploadKind || '';
      setPartnerUploadStatus(statusKey, 'error', disabledMessage);
      setPartnerFormMessage('offerImage', disabledMessage);
      renderPartnerLayout();
    }
    return;
  }
  const container = button.closest('.partner-image-uploader, .partner-gallery, .offer-image-uploader');
  const selector = button.dataset.partnerUploadInput;
  const input = selector ? container?.querySelector(selector) : null;
  if (input) {
    input.click();
  }
};

root.addEventListener('click', async (event) => {

  const giveawayEdit = event.target.closest('[data-admin-giveaway-edit]');
  if (giveawayEdit) {
    event.preventDefault();
    const giveawayId = giveawayEdit.dataset.adminGiveawayEdit;
    adminState.selectedGiveawayIdForEdit = giveawayId;
    adminState.selectedGiveawayIdForEntriesManual = '';
    adminState.giveawayEntries = null;
    adminState.giveawayRecheckResult = null;
    renderAdminLayout();
    syncGiveawayEntriesSelection({ force: true }).then(() => renderAdminLayout()).catch((error) => { setFormMessage('giveaway', error.message || 'Не удалось загрузить номера розыгрыша'); renderAdminLayout(); });
    return;
  }
  const customSelectOption = event.target.closest('[data-custom-select-option]');
  if (customSelectOption) {
    event.preventDefault();
    selectCustomSelectOption(customSelectOption);
    return;
  }

  const customSelectTrigger = event.target.closest('.custom-select-trigger');
  if (customSelectTrigger) {
    event.preventDefault();
    const customSelect = customSelectTrigger.closest('[data-custom-select]');
    if (customSelect?.classList.contains('custom-select--open')) {
      closeCustomSelect(customSelect);
    } else {
      openCustomSelect(customSelect);
    }
    return;
  }

  if (event.target.closest('[data-custom-select]')) {
    return;
  }


  const giveawayExport = event.target.closest('[data-admin-giveaway-export]');
  if (giveawayExport) {
    event.preventDefault();
    const id = giveawayExport.dataset.adminGiveawayExport;
    giveawayExport.disabled = true;
    try {
      await downloadGiveawayEntriesExcel(id);
      setPartnerPanelMessage('Excel-файл розыгрыша скачан.', 'success');
    } catch (error) {
      setPartnerPanelMessage(error.message || 'Не удалось выгрузить Excel.', 'error');
    } finally {
      giveawayExport.disabled = false;
    }
    return;
  }

  const giveawayRecheck = event.target.closest('[data-admin-giveaway-recheck]');
  if (giveawayRecheck) {
    const id = giveawayRecheck.dataset.adminGiveawayRecheck;
    postJson(`/api/v1/admin/giveaways/${id}/social-subscriptions/recheck`, {}).then((data) => { adminState.giveawayRecheckResult = data; return loadGiveawayEntries(id); }).then(() => { render(); }).catch((error) => { setFormMessage('giveaway', error.message || 'Не удалось перепроверить подписки'); render(); });
    return;
  }

  const giveawayOpen = event.target.closest('[data-admin-giveaway-open]');
  if (giveawayOpen) {
    event.preventDefault();
    adminState.giveawayDrawerOpen = true;
    setFormMessage('landingGiveaway');
    renderAdminLayout();
    return;
  }

  const giveawayCancel = event.target.closest('[data-admin-giveaway-cancel]');
  if (giveawayCancel) {
    event.preventDefault();
    adminState.giveawayDrawerOpen = false;
    setFormMessage('landingGiveaway');
    renderAdminLayout();
    return;
  }

  const giveawayAddPrize = event.target.closest('[data-admin-giveaway-add-prize]');
  if (giveawayAddPrize) {
    event.preventDefault();
    const list = root.querySelector('[data-admin-giveaway-prize-list]');
    const index = list ? list.querySelectorAll('[data-giveaway-prize-row]').length : 0;
    if (list) {
      list.insertAdjacentHTML('beforeend', renderAdminGiveawayItems([{ title: '', description: '', is_active: true, sort_order: index }]));
    }
    return;
  }

  const giveawayRemovePrize = event.target.closest('[data-admin-giveaway-remove-prize]');
  if (giveawayRemovePrize) {
    event.preventDefault();
    const row = giveawayRemovePrize.closest('[data-giveaway-prize-row]');
    if (row) row.remove();
    return;
  }

  const partnerUploadTrigger = event.target.closest('[data-partner-upload-trigger]');
  if (partnerUploadTrigger) {
    event.preventDefault();
    event.stopPropagation();
    triggerPartnerUploadInput(partnerUploadTrigger);
    return;
  }

  if (event.target.closest('[data-client-partner-modal]')) {
    const closePartnerModalButton = event.target.closest('[data-client-partner-modal-close]');
    if (closePartnerModalButton) {
      event.preventDefault();
      event.stopPropagation();
      resetClientPartnerModalState();
      renderClientLayout();
      return;
    }

    const galleryButton = event.target.closest('[data-gallery-action]');
    if (galleryButton) {
      event.preventDefault();
      event.stopPropagation();
      const images = getPartnerGalleryImages(clientState.selectedPartnerModalPartner || {});
      const total = images.length;
      if (total) {
        if (galleryButton.dataset.galleryAction === 'prev') {
          clientState.partnerModalGalleryIndex = (clientState.partnerModalGalleryIndex - 1 + total) % total;
        } else if (galleryButton.dataset.galleryAction === 'next') {
          clientState.partnerModalGalleryIndex = (clientState.partnerModalGalleryIndex + 1) % total;
        } else if (galleryButton.dataset.galleryAction === 'select') {
          const nextIndex = Number(galleryButton.dataset.galleryIndex || 0);
          clientState.partnerModalGalleryIndex = Math.min(Math.max(nextIndex, 0), total - 1);
        }
        renderClientLayout();
      }
      return;
    }

    const offerGalleryButton = event.target.closest('[data-client-offer-gallery-open]');
    if (offerGalleryButton) {
      event.preventDefault();
      event.stopPropagation();
      clientState.partnerModalOfferGalleryId = offerGalleryButton.dataset.clientOfferGalleryOpen;
      clientState.partnerModalOfferGalleryIndex = 0;
      renderClientLayout();
      return;
    }
    const offerGalleryNavButton = event.target.closest('[data-offer-gallery-action]');
    if (offerGalleryNavButton) {
      event.preventDefault();
      event.stopPropagation();
      const offers = Array.isArray(clientState.selectedPartnerModalOffers) ? clientState.selectedPartnerModalOffers : [];
      const activeOffer = offers.find((offer) => String(offer.id) === String(clientState.partnerModalOfferGalleryId || ''));
      const photos = getOfferPhotos(activeOffer || {});
      if (photos.length > 1) {
        if (offerGalleryNavButton.dataset.offerGalleryAction === 'prev') clientState.partnerModalOfferGalleryIndex = (clientState.partnerModalOfferGalleryIndex - 1 + photos.length) % photos.length;
        if (offerGalleryNavButton.dataset.offerGalleryAction === 'next') clientState.partnerModalOfferGalleryIndex = (clientState.partnerModalOfferGalleryIndex + 1) % photos.length;
      }
      renderClientLayout();
      return;
    }
  }

  const openPartnerModalButton = event.target.closest('[data-client-partner-open]');
  if (openPartnerModalButton) {
    event.preventDefault();
    event.stopPropagation();
    await openClientPartnerModal(openPartnerModalButton.dataset.partnerId);
    return;
  }

  const menuToggle = event.target.closest('[data-landing-menu-toggle]');
  if (menuToggle) {
    const panel = document.querySelector('[data-landing-menu-panel]');
    const isExpanded = menuToggle.getAttribute('aria-expanded') === 'true';
    menuToggle.setAttribute('aria-expanded', String(!isExpanded));
    if (panel) {
      panel.hidden = isExpanded;
    }
    return;
  }

  const menuLink = event.target.closest('[data-landing-menu-link]');
  if (menuLink) {
    const menuButton = document.querySelector('[data-landing-menu-toggle]');
    const panel = document.querySelector('[data-landing-menu-panel]');
    if (menuButton) {
      menuButton.setAttribute('aria-expanded', 'false');
    }
    if (panel) {
      panel.hidden = true;
    }
    return;
  }

  const directionButton = event.target.closest('[data-landing-category-slug]');
  if (directionButton) {
    await openLandingDirection(directionButton.dataset.landingCategorySlug);
    return;
  }

  if (event.target.closest('[data-landing-partner-close]')) {
    closeLandingPartnerModal();
    return;
  }

  const landingPartnerPicker = event.target.closest('[data-landing-partner-index]');
  if (landingPartnerPicker) {
    selectLandingModalPartner(Number(landingPartnerPicker.dataset.landingPartnerIndex || 0));
    return;
  }

  const landingPhotoPicker = event.target.closest('[data-landing-photo-index]');
  if (landingPhotoPicker) {
    selectLandingModalPhoto(Number(landingPhotoPicker.dataset.landingPhotoIndex || 0));
    return;
  }

  if (event.target.closest('[data-landing-photo-prev]')) {
    moveLandingPhotoCarousel(-1);
    return;
  }

  if (event.target.closest('[data-landing-photo-next]')) {
    moveLandingPhotoCarousel(1);
    return;
  }

  if (event.target.closest('[data-landing-carousel-prev]')) {
    moveLandingPartnerCarousel(-1);
    return;
  }

  if (event.target.closest('[data-landing-carousel-next]')) {
    moveLandingPartnerCarousel(1);
    return;
  }

  if (event.target.closest('[data-landing-modal-cta]')) {
    closeLandingPartnerModal();
    return;
  }

  const loginExpandButton = event.target.closest('[data-login-expand-mode]');
  if (loginExpandButton) {
    setLoginExpanded(true, loginExpandButton.dataset.loginExpandMode || '');
    setLoginMode(loginExpandButton.dataset.loginExpandMode || 'client');
    return;
  }

  const cityChoice = event.target.closest('[data-city-choice]');
  if (cityChoice) {
    document.querySelectorAll('[data-city-choice]').forEach((choice) => {
      const isSelected = choice === cityChoice;
      choice.classList.toggle('is-active', isSelected);
      choice.setAttribute('aria-checked', String(isSelected));
    });
    return;
  }

  const loginModeButton = event.target.closest('[data-login-mode]');
  if (loginModeButton) {
    setLoginMode(loginModeButton.dataset.loginMode);
    setLoginMessage();
    return;
  }

  const adminSearchReset = event.target.closest('[data-admin-search-reset]');
  if (adminSearchReset) {
    adminState.search[adminSearchReset.dataset.adminSearchReset] = '';
    renderAdminLayout();
    return;
  }

  const partnerFilterReset = event.target.closest('[data-admin-partner-filter-reset]');
  if (partnerFilterReset) {
    adminState.partnerFilters = { ...defaultPartnerFilters(), ...(adminState.partnerFilters || {}), [partnerFilterReset.dataset.adminPartnerFilterReset]: defaultPartnerFilters()[partnerFilterReset.dataset.adminPartnerFilterReset] ?? '' };
    renderAdminLayout();
    return;
  }

  const partnerAccessToggle = event.target.closest('[data-partner-access-toggle]');
  if (partnerAccessToggle) {
    try {
      await patchJson(`/api/v1/admin/partner-accesses/${partnerAccessToggle.dataset.partnerAccessToggle}`, { is_active: partnerAccessToggle.dataset.nextActive === 'true' });
      await loadPartnerAccesses();
      setPanelMessage('Партнёрский доступ обновлён.', 'success');
    } catch (error) { setPanelMessage(error.message || 'Не удалось обновить доступ.', 'error'); }
    renderAdminLayout(); return;
  }

  const paymentSync = event.target.closest('[data-payment-sync]');
  if (paymentSync) {
    try {
      await postJson(`/api/v1/admin/payments/${paymentSync.dataset.paymentSync}/sync`, {});
      await loadAcquiringPayments();
      setPanelMessage('Статус платежа обновлён.', 'success');
    } catch (error) { setPanelMessage(error.message || 'Не удалось проверить платёж.', 'error'); }
    renderAdminLayout(); return;
  }

  const paymentDetails = event.target.closest('[data-payment-details]');
  if (paymentDetails) {
    try { adminState.selectedAcquiringPayment = await apiFetch(`/api/v1/admin/payments/${paymentDetails.dataset.paymentDetails}`); }
    catch (error) { setPanelMessage(error.message || 'Не удалось загрузить историю платежа.', 'error'); }
    renderAdminLayout(); return;
  }

  const flowerTaskToggle = event.target.closest('[data-flower-task-toggle]');
  if (flowerTaskToggle) {
    try {
      await patchJson(`/api/v1/admin/flower/tasks/${flowerTaskToggle.dataset.flowerTaskToggle}`, { is_active: flowerTaskToggle.dataset.nextActive === 'true' });
      await loadFlowerTasks();
      setPanelMessage('Задание обновлено.', 'success');
    } catch (error) { setPanelMessage(error.message || 'Не удалось обновить задание.', 'error'); }
    renderAdminLayout(); return;
  }

  const specialTaskToggle = event.target.closest('[data-special-task-toggle]');
  if (specialTaskToggle) {
    try {
      await patchJson(`/api/v1/admin/flower/special-tasks/${specialTaskToggle.dataset.specialTaskToggle}`, { is_active: specialTaskToggle.dataset.nextActive === 'true' });
      await loadFlowerGarden();
      setPanelMessage('Специальное задание обновлено.', 'success');
    } catch (error) { setPanelMessage(error.message || 'Не удалось обновить задание.', 'error'); }
    renderAdminLayout(); return;
  }

  const specialTaskDelete = event.target.closest('[data-special-task-delete]');
  if (specialTaskDelete) {
    const title = specialTaskDelete.dataset.taskTitle || 'это задание';
    const submissionsCount = Number(specialTaskDelete.dataset.submissionsCount || 0);
    const answersWarning = submissionsCount ? ` Вместе с ним будут удалены ответы участниц: ${submissionsCount}.` : '';
    if (!window.confirm(`Удалить «${title}»?${answersWarning} Действие нельзя отменить.`)) return;
    try {
      await deleteJson(`/api/v1/admin/flower/special-tasks/${specialTaskDelete.dataset.specialTaskDelete}`);
      if (String(adminState.flowerAnalytics?.task_id) === String(specialTaskDelete.dataset.specialTaskDelete)) adminState.flowerAnalytics = null;
      await loadFlowerGarden();
      setPanelMessage('Специальное задание удалено.', 'success');
    } catch (error) { setPanelMessage(error.message || 'Не удалось удалить задание.', 'error'); }
    renderAdminLayout(); return;
  }

  const specialTaskAnalytics = event.target.closest('[data-special-task-analytics]');
  if (specialTaskAnalytics) {
    try {
      adminState.flowerAnalytics = await apiFetch(`/api/v1/admin/flower/special-tasks/${specialTaskAnalytics.dataset.specialTaskAnalytics}/analytics`);
    } catch (error) { setPanelMessage(error.message || 'Не удалось загрузить ответы.', 'error'); }
    renderAdminLayout(); return;
  }

  const partnerFilterClear = event.target.closest('[data-admin-partner-filter-clear]');
  if (partnerFilterClear) {
    adminState.partnerFilters = defaultPartnerFilters();
    adminState.search.partners = '';
    renderAdminLayout();
    return;
  }

  const userToggle = event.target.closest('[data-user-active-toggle]');
  if (userToggle) {
    toggleUserActive(userToggle.dataset.userActiveToggle);
    return;
  }

  const userDeleteButton = event.target.closest('[data-user-delete]');
  if (userDeleteButton) {
    deleteUser(userDeleteButton.dataset.userDelete);
    return;
  }

  const cityEditButton = event.target.closest('[data-admin-city-edit]');
  if (cityEditButton) {
    adminState.selectedCityIdForEdit = cityEditButton.dataset.adminCityEdit;
    setFormMessage('cityEdit');
    renderAdminLayout();
    return;
  }

  const cityEditCancel = event.target.closest('[data-admin-city-edit-cancel]');
  if (cityEditCancel) {
    adminState.selectedCityIdForEdit = '';
    setFormMessage('cityEdit');
    renderAdminLayout();
    return;
  }

  const cityActiveToggle = event.target.closest('[data-admin-city-active-toggle]');
  if (cityActiveToggle) {
    toggleCityActive(cityActiveToggle.dataset.adminCityActiveToggle);
    return;
  }

  const categoryEditButton = event.target.closest('[data-admin-category-edit]');
  if (categoryEditButton) {
    adminState.selectedCategoryIdForEdit = categoryEditButton.dataset.adminCategoryEdit;
    setFormMessage('categoryEdit');
    renderAdminLayout();
    return;
  }

  const categoryEditCancel = event.target.closest('[data-admin-category-edit-cancel]');
  if (categoryEditCancel) {
    adminState.selectedCategoryIdForEdit = '';
    setFormMessage('categoryEdit');
    renderAdminLayout();
    return;
  }

  const categoryActiveToggle = event.target.closest('[data-admin-category-active-toggle]');
  if (categoryActiveToggle) {
    toggleCategoryActive(categoryActiveToggle.dataset.adminCategoryActiveToggle);
    return;
  }

  const partnerCreateButton = event.target.closest('[data-admin-partner-create]');
  if (partnerCreateButton) {
    adminState.selectedPartnerIdForEdit = '';
    resetAdminPartnerCategoryDraft('');
    adminState.partnerFormOpen = true;
    adminState.partnerFormStep = 'basic';
    adminState.partnerFormInlineError = '';
    setFormMessage('partner');
    renderAdminLayout();
    return;
  }

  const partnerEditButton = event.target.closest('[data-admin-partner-edit]');
  if (partnerEditButton) {
    adminState.selectedPartnerIdForEdit = partnerEditButton.dataset.adminPartnerEdit;
    resetAdminPartnerCategoryDraft(adminState.selectedPartnerIdForEdit);
    adminState.partnerFormOpen = true;
    adminState.partnerFormStep = 'basic';
    adminState.partnerFormInlineError = '';
    setFormMessage('partnerEdit');
    setFormMessage('partnerGallery');
    adminState.selectedPartnerAnalytics = adminState.partnerAnalyticsById[adminState.selectedPartnerIdForEdit] || null;
    adminState.partnerAnalyticsError = '';
    try {
      await Promise.all([
        loadAdminPartnerPhotos(adminState.selectedPartnerIdForEdit),
        loadAdminPartnerAnalytics(adminState.selectedPartnerIdForEdit),
      ]);
    } catch (error) {
      setFormMessage('partnerGallery', error.message || 'Не удалось загрузить галерею.');
    }
    renderAdminLayout();
    return;
  }

  const partnerEditCancel = event.target.closest('[data-admin-partner-edit-cancel]');
  if (partnerEditCancel) {
    resetAdminPartnerCategoryDraft(partnerEditCancel.dataset.partnerId || adminState.selectedPartnerIdForEdit || '');
    adminState.selectedPartnerIdForEdit = '';
    adminState.selectedPartnerAnalytics = null;
    adminState.partnerAnalyticsError = '';
    adminState.partnerAnalyticsLoading = false;
    adminState.partnerFormOpen = false;
    adminState.partnerFormStep = 'basic';
    adminState.partnerFormInlineError = '';
    setFormMessage('partnerEdit');
    renderAdminLayout();
    return;
  }

  const partnerStepJump = event.target.closest('[data-admin-partner-step-jump]');
  if (partnerStepJump) {
    captureAdminPartnerCategoryDraft(partnerStepJump.closest('[data-admin-partner-wizard-form]'));
    const stepKey = partnerStepJump.dataset.adminPartnerStepJump;
    if (getPartnerWizardStepIndex(stepKey) >= 0) {
      adminState.partnerFormStep = stepKey;
      adminState.partnerFormInlineError = '';
      renderAdminLayout();
    }
    return;
  }

  const contentReviewOfferActivate = event.target.closest('[data-content-review-offer-activate]');
  if (contentReviewOfferActivate) {
    setFormMessage('contentReview');
    try {
      await activateContentReviewOffer(contentReviewOfferActivate.dataset.contentReviewOfferActivate);
      setFormMessage('contentReview', 'Предложение активировано.');
      setPanelMessage('Предложение активировано и стало видно клиентам.', 'success');
    } catch (error) {
      setFormMessage('contentReview', error.message || 'Не удалось активировать предложение.');
      setPanelMessage(error.message || 'Не удалось активировать предложение.', 'error');
    }
    renderAdminLayout();
    return;
  }

  const contentReviewPhotoActivate = event.target.closest('[data-content-review-photo-activate]');
  if (contentReviewPhotoActivate) {
    setFormMessage('contentReview');
    try {
      await activateContentReviewPhoto(contentReviewPhotoActivate.dataset.contentReviewPhotoActivate);
      setFormMessage('contentReview', 'Фото активировано.');
      setPanelMessage('Фото активировано и стало видно клиентам.', 'success');
    } catch (error) {
      setFormMessage('contentReview', error.message || 'Не удалось активировать фото.');
      setPanelMessage(error.message || 'Не удалось активировать фото.', 'error');
    }
    renderAdminLayout();
    return;
  }

  const contentReviewPartnerOpen = event.target.closest('[data-content-review-partner-open]');
  if (contentReviewPartnerOpen) {
    adminState.activeTab = 'partners';
    adminState.selectedPartnerIdForEdit = contentReviewPartnerOpen.dataset.contentReviewPartnerOpen;
    setFormMessage('partnerEdit');
    await ensureAdminDictionaries();
    await Promise.all([
      loadAdminPartnerPhotos(adminState.selectedPartnerIdForEdit),
      loadAdminPartnerAnalytics(adminState.selectedPartnerIdForEdit),
    ]);
    renderAdminLayout();
    return;
  }

  const offerEditButton = event.target.closest('[data-admin-offer-edit]');
  if (offerEditButton) {
    adminState.selectedOfferIdForEdit = offerEditButton.dataset.adminOfferEdit;
    setFormMessage('offerEdit');
    renderAdminLayout();
    return;
  }

  const offerEditCancel = event.target.closest('[data-admin-offer-edit-cancel]');
  if (offerEditCancel) {
    adminState.selectedOfferIdForEdit = '';
    setFormMessage('offerEdit');
    renderAdminLayout();
    return;
  }

  const qrEditButton = event.target.closest('[data-admin-qr-edit]');
  if (qrEditButton) {
    adminState.selectedQrLinkIdForEdit = qrEditButton.dataset.adminQrEdit;
    setFormMessage('qrEdit');
    renderAdminLayout();
    return;
  }

  const qrEditCancel = event.target.closest('[data-admin-qr-edit-cancel]');
  if (qrEditCancel) {
    adminState.selectedQrLinkIdForEdit = '';
    setFormMessage('qrEdit');
    renderAdminLayout();
    return;
  }

  const adminPhotoHide = event.target.closest('[data-admin-photo-hide]');
  if (adminPhotoHide) {
    setFormMessage('partnerGallery');
    try {
      await hideAdminPartnerPhoto(adminPhotoHide.dataset.adminPhotoHide);
      setFormMessage('partnerGallery', 'Фото скрыто.');
      setPanelMessage('Фото скрыто без удаления файла.', 'success');
    } catch (error) {
      setFormMessage('partnerGallery', error.message || 'Не удалось скрыть фото.');
      setPanelMessage(error.message || 'Не удалось скрыть фото.', 'error');
    }
    renderAdminLayout();
    return;
  }

  const partnerPhotoHide = event.target.closest('[data-partner-photo-hide]');
  if (partnerPhotoHide) {
    setPartnerFormMessage('partnerGallery');
    try {
      await hidePartnerPhoto(partnerPhotoHide.dataset.partnerPhotoHide);
      setPartnerFormMessage('partnerGallery', 'Фото скрыто.');
      setPartnerPanelMessage('Фото скрыто без удаления файла.', 'success');
    } catch (error) {
      setPartnerFormMessage('partnerGallery', error.message || 'Не удалось скрыть фото.');
      setPartnerPanelMessage(error.message || 'Не удалось скрыть фото.', 'error');
    }
    renderPartnerLayout();
    return;
  }

  const partnerImageClear = event.target.closest('[data-partner-image-clear]');
  if (partnerImageClear) {
    if (!window.confirm('Удалить это фото? Действие нельзя отменить.')) return;
    partnerImageClear.disabled = true;
    setPartnerFormMessage('profileImages');
    try {
      await clearPartnerProfileImage(partnerImageClear.dataset.partnerImageClear);
      setPartnerFormMessage('profileImages', 'Изображение удалено.');
      setPartnerPanelMessage('Удалена связь с изображением в профиле.', 'success');
    } catch (error) {
      setPartnerFormMessage('profileImages', error.message || 'Не удалось удалить изображение.');
      setPartnerPanelMessage(error.message || 'Не удалось удалить изображение.', 'error');
    }
    renderPartnerLayout();
    return;
  }

  const partnerPhotoDelete = event.target.closest('[data-partner-photo-delete]');
  if (partnerPhotoDelete) {
    if (!window.confirm('Удалить это фото? Действие нельзя отменить.')) return;
    partnerPhotoDelete.disabled = true;
    setPartnerFormMessage('partnerGallery');
    try {
      await deletePartnerPhoto(partnerPhotoDelete.dataset.partnerPhotoDelete);
      setPartnerFormMessage('partnerGallery', 'Фото удалено.');
      setPartnerPanelMessage('Фото удалено из галереи.', 'success');
    } catch (error) {
      setPartnerFormMessage('partnerGallery', error.message || 'Не удалось удалить фото.');
      setPartnerPanelMessage(error.message || 'Не удалось удалить фото.', 'error');
    }
    renderPartnerLayout();
    return;
  }
  const partnerOfferPhotoDelete = event.target.closest('[data-partner-offer-photo-delete]');
  if (partnerOfferPhotoDelete) {
    if (!window.confirm('Удалить это фото? Действие нельзя отменить.')) return;
    setPartnerFormMessage('offerPhoto');
    try {
      await deletePartnerOfferPhoto(partnerOfferPhotoDelete.dataset.offerId, partnerOfferPhotoDelete.dataset.partnerOfferPhotoDelete);
      setPartnerFormMessage('offerPhoto', 'Фото услуги удалено.');
      setPartnerPanelMessage('Фото услуги удалено.', 'success');
    } catch (error) {
      setPartnerFormMessage('offerPhoto', error.message || 'Не удалось удалить фото услуги.');
      setPartnerPanelMessage(error.message || 'Не удалось удалить фото услуги.', 'error');
    }
    renderPartnerLayout();
    return;
  }
  const partnerOfferPhotoVisibility = event.target.closest('[data-partner-offer-photo-visibility]');
  if (partnerOfferPhotoVisibility) {
    setPartnerFormMessage('offerPhoto');
    try {
      await updatePartnerOfferPhoto(
        partnerOfferPhotoVisibility.dataset.offerId,
        partnerOfferPhotoVisibility.dataset.partnerOfferPhotoVisibility,
        { is_active: partnerOfferPhotoVisibility.dataset.nextActive === 'true' },
      );
      setPartnerFormMessage('offerPhoto', 'Статус фото обновлён.');
      setPartnerPanelMessage('Статус фото услуги обновлён.', 'success');
    } catch (error) {
      setPartnerFormMessage('offerPhoto', error.message || 'Не удалось обновить статус фото услуги.');
      setPartnerPanelMessage(error.message || 'Не удалось обновить статус фото услуги.', 'error');
    }
    renderPartnerLayout();
    return;
  }

  const partnerOfferImageClear = event.target.closest('[data-partner-offer-image-clear]');
  if (partnerOfferImageClear) {
    if (!window.confirm('Удалить это фото? Действие нельзя отменить.')) return;
    partnerOfferImageClear.disabled = true;
    setPartnerFormMessage('offerEdit');
    try {
      await clearPartnerOfferImage(partnerOfferImageClear.dataset.partnerOfferImageClear);
      setPartnerFormMessage('offerEdit', 'Фото услуги удалено.');
      setPartnerPanelMessage('Фото услуги удалено из предложения.', 'success');
    } catch (error) {
      setPartnerFormMessage('offerEdit', error.message || 'Не удалось удалить фото услуги.');
      setPartnerPanelMessage(error.message || 'Не удалось удалить фото услуги.', 'error');
    }
    renderPartnerLayout();
    return;
  }

  const adminPaymentRefresh = event.target.closest('[data-admin-payment-refresh]');
  if (adminPaymentRefresh) {
    adminState.paymentActionStatus = '';
    adminState.paymentActionError = '';
    loadActiveTabData();
    return;
  }

  const adminPaymentOpen = event.target.closest('[data-admin-payment-open]');
  if (adminPaymentOpen) {
    await handleAdminPaymentOpen(adminPaymentOpen.dataset.adminPaymentOpen);
    return;
  }

  const adminPaymentApprove = event.target.closest('[data-admin-payment-approve]');
  if (adminPaymentApprove) {
    await handleAdminPaymentApprove(adminPaymentApprove.dataset.adminPaymentApprove);
    return;
  }

  const adminPaymentReject = event.target.closest('[data-admin-payment-reject]');
  if (adminPaymentReject) {
    await handleAdminPaymentReject(adminPaymentReject.dataset.adminPaymentReject);
    return;
  }

  const adminLogout = event.target.closest('[data-logout-button]');
  if (adminLogout) {
    clearToken();
    showLoginForm();
    setLoginMode('admin');
    return;
  }

  const globalPartnerCreate = event.target.closest('[data-admin-global-partner-create]');
  if (globalPartnerCreate) {
    adminState.activeTab = 'partners';
    adminState.selectedPartnerIdForEdit = '';
    adminState.partnerFormOpen = true;
    setFormMessage('partner');
    await ensureAdminDictionaries();
    renderAdminLayout();
    return;
  }

  const globalGiveawayCreate = event.target.closest('[data-admin-global-giveaway-create]');
  if (globalGiveawayCreate) {
    adminState.activeTab = 'giveaways';
    adminState.selectedGiveawayIdForEdit = '';
    await loadGiveaways();
    renderAdminLayout();
    return;
  }

  const partnerOpenOffers = event.target.closest('[data-admin-partner-open-offers]');
  if (partnerOpenOffers) {
    adminState.activeTab = 'offers';
    adminState.selectedPartnerIdForOffers = partnerOpenOffers.dataset.adminPartnerOpenOffers;
    adminState.selectedOfferIdForEdit = '';
    await loadActiveTabData();
    return;
  }

  const partnerOpenQr = event.target.closest('[data-admin-partner-open-qr]');
  if (partnerOpenQr) {
    adminState.activeTab = 'qr';
    adminState.selectedPartnerIdForQr = partnerOpenQr.dataset.adminPartnerOpenQr;
    adminState.selectedQrLinkIdForEdit = '';
    await loadActiveTabData();
    return;
  }

  const giveawayCreate = event.target.closest('[data-admin-giveaway-create]');
  if (giveawayCreate) {
    adminState.selectedGiveawayIdForEdit = '';
    setFormMessage('giveaway');
    renderAdminLayout();
    return;
  }

  const adminTabButton = event.target.closest('[data-admin-tab]');
  if (adminTabButton) {
    adminState.activeTab = adminTabButton.dataset.adminTab;
    loadActiveTabData();
    return;
  }

  const partnerOfferEditButton = event.target.closest('[data-partner-offer-edit]');
  if (partnerOfferEditButton) {
    partnerState.selectedOfferIdForEdit = partnerOfferEditButton.dataset.partnerOfferEdit;
    setPartnerFormMessage('offerEdit');
    renderPartnerLayout();
    return;
  }

  const partnerOfferEditCancel = event.target.closest('[data-partner-offer-edit-cancel]');
  if (partnerOfferEditCancel) {
    partnerState.selectedOfferIdForEdit = '';
    setPartnerFormMessage('offerEdit');
    renderPartnerLayout();
    return;
  }

  const partnerOfferToggle = event.target.closest('[data-partner-offer-toggle]');
  if (partnerOfferToggle) {
    togglePartnerOffer(partnerOfferToggle.dataset.partnerOfferToggle);
    return;
  }

  const partnerConfirmButton = event.target.closest('[data-partner-confirm-verification]');
  if (partnerConfirmButton) {
    confirmPartnerVerification(partnerConfirmButton.dataset.partnerConfirmVerification);
    return;
  }

  const partnerLogout = event.target.closest('[data-partner-logout-button]');
  if (partnerLogout) {
    clearPartnerToken();
    showLoginForm();
    setLoginMode('partner');
    return;
  }

  const partnerOnboardingTabButton = event.target.closest('[data-partner-onboarding-tab]');
  if (partnerOnboardingTabButton) {
    partnerState.activeTab = partnerOnboardingTabButton.dataset.partnerOnboardingTab;
    loadActivePartnerTabData();
    return;
  }

  const partnerTabButton = event.target.closest('[data-partner-tab]');
  if (partnerTabButton) {
    partnerState.activeTab = partnerTabButton.dataset.partnerTab;
    loadActivePartnerTabData();
    return;
  }

  const clientLogout = event.target.closest('[data-client-logout-button]');
  if (clientLogout) {
    clearClientToken();
    showLoginForm();
    setLoginMode('client');
    return;
  }

  const clientTabButton = event.target.closest('[data-client-tab]');
  if (clientTabButton) {
    clientState.activeTab = clientTabButton.dataset.clientTab;
    await loadActiveClientTabData();
    return;
  }

  const savingsModeButton = event.target.closest('[data-client-savings-filter-mode]');
  if (savingsModeButton) {
    const mode = savingsModeButton.dataset.clientSavingsFilterMode === 'period' ? 'period' : 'all';
    clientState.savingsFilterMode = mode;
    clientState.savingsFilterUiError = '';
    if (mode === 'all') {
      clientState.savingsFilterFromDate = '';
      clientState.savingsFilterToDate = '';
      await loadClientSavings();
    }
    renderClientLayout();
    return;
  }

  const savingsApplyButton = event.target.closest('[data-client-savings-apply]');
  if (savingsApplyButton) {
    clientState.savingsFilterUiError = '';
    const { savingsFilterFromDate: fromDate, savingsFilterToDate: toDate } = clientState;
    if (fromDate && toDate && fromDate > toDate) {
      clientState.savingsFilterUiError = 'Дата начала не может быть позже даты окончания.';
      renderClientLayout();
      return;
    }
    await loadClientSavings({ fromDate, toDate });
    renderClientLayout();
    return;
  }

  const savingsResetButton = event.target.closest('[data-client-savings-reset]');
  if (savingsResetButton) {
    clientState.savingsFilterMode = 'all';
    clientState.savingsFilterFromDate = '';
    clientState.savingsFilterToDate = '';
    clientState.savingsFilterUiError = '';
    await loadClientSavings();
    renderClientLayout();
    return;
  }

  const createVkCodeButton = event.target.closest('[data-client-create-vk-code]');
  if (createVkCodeButton) {
    await createClientVkLinkCode();
    return;
  }

  const dismissPrivilegeButton = event.target.closest('[data-client-dismiss-privilege]');
  if (dismissPrivilegeButton) {
    clientState.latestVerification = null;
    renderClientLayout();
    return;
  }

  const openPrivilegesButton = event.target.closest('[data-client-open-privileges]');
  if (openPrivilegesButton) {
    clientState.latestVerification = null;
    clientState.activeTab = 'history';
    await loadActiveClientTabData();
    return;
  }

  const loadOffersButton = event.target.closest('[data-client-load-offers]');
  if (loadOffersButton) {
    try {
      await openClientPartnerMarketplace(loadOffersButton.dataset.clientLoadOffers);
      setClientPanelMessage('Партнёр и предложения открыты.', 'success');
    } catch (error) {
      setClientPanelMessage(error.message || 'Не удалось загрузить предложения.', 'error');
    }
    renderClientLayout();
    return;
  }

  const verifyOfferButton = event.target.closest('[data-client-verify-offer]');
  if (verifyOfferButton) {
    await createClientVerification(verifyOfferButton.dataset.clientVerifyOffer, verifyOfferButton.dataset.offerId);
    return;
  }

  const verifyPartnerButton = event.target.closest('[data-client-verify-partner]');
  if (verifyPartnerButton) {
    await createClientVerification(verifyPartnerButton.dataset.clientVerifyPartner);
  }
});

root.addEventListener('input', (event) => {
  const partnerProfileInput = event.target.closest('[data-partner-form="profile"] input, [data-partner-form="profile"] textarea');
  if (partnerProfileInput && !partnerProfileInput.readOnly) {
    if (partnerState.profile && partnerProfileInput.name) {
      partnerState.profile[partnerProfileInput.name] = partnerProfileInput.value;
    }
    partnerState.isProfileDirty = true;
    partnerState.profileSaveStatus = 'dirty';

    const saveStatusNode = root.querySelector('.partner-save-status');
    if (saveStatusNode) {
      saveStatusNode.textContent = getPartnerSaveStatusLabel();
    }

    const dirtyBar = root.querySelector('.partner-save-bar');
    if (dirtyBar) {
      dirtyBar.hidden = false;
    }

    if (partnerProfileInput.classList.contains('partner-required-empty') && String(partnerProfileInput.value || '').trim()) {
      partnerProfileInput.classList.remove('partner-required-empty');
    }

    if (partnerProfileInput.matches('textarea[name="description"]')) {
      const hint = partnerProfileInput.closest('section')?.querySelector('.partner-textarea-hint');
      if (hint) {
        hint.textContent = `${partnerProfileInput.value.length} символов. Рекомендация: 200–500 символов.`;
      }
    }
    return;
  }


  const paymentAccessDaysInput = event.target.closest('[data-admin-payment-access-days]');
  if (paymentAccessDaysInput) {
    adminState.paymentApprovalDays = Math.max(1, Number(paymentAccessDaysInput.value) || 30);
    return;
  }

  const partnerFilterInput = event.target.closest('[data-admin-partner-filter]');
  if (partnerFilterInput) {
    const filterKey = partnerFilterInput.dataset.adminPartnerFilter;
    adminState.partnerFilters = { ...defaultPartnerFilters(), ...(adminState.partnerFilters || {}), [filterKey]: partnerFilterInput.value };
    renderAdminLayout();
    return;
  }

  const searchInput = event.target.closest('[data-admin-search]');
  const savingsDateInput = event.target.closest('[data-client-savings-date]');
  if (savingsDateInput) {
    if (savingsDateInput.dataset.clientSavingsDate === 'from') {
      clientState.savingsFilterFromDate = savingsDateInput.value;
    } else {
      clientState.savingsFilterToDate = savingsDateInput.value;
    }
    clientState.savingsFilterUiError = '';
    return;
  }

  if (!searchInput) {
    return;
  }

  const searchScope = searchInput.dataset.adminSearch;
  adminState.search[searchScope] = searchInput.value;
  renderAdminLayout();
  requestAnimationFrame(() => {
    const updatedInput = root.querySelector(`[data-admin-search="${searchScope}"]`);
    if (updatedInput) {
      updatedInput.focus();
      updatedInput.setSelectionRange(updatedInput.value.length, updatedInput.value.length);
    }
  });
});


const handleAdminPartnerPhotoInput = async (input) => {
  const file = input.files?.[0];
  if (!file) return;
  const partnerId = input.dataset.partnerId;
  setFormMessage('partnerGallery');
  try {
    await uploadAdminPartnerPhoto(partnerId, file);
    setFormMessage('partnerGallery', 'Фото добавлено в галерею.');
    setPanelMessage('Фото добавлено в галерею партнёра.', 'success');
  } catch (error) {
    setFormMessage('partnerGallery', error.message || 'Не удалось загрузить фото в галерею.');
    setPanelMessage(error.message || 'Не удалось загрузить фото в галерею.', 'error');
  }
  renderAdminLayout();
};

const handlePartnerPhotoInput = async (input) => {
  const file = input.files?.[0];
  if (!file) return;
  const statusKey = 'partnerGallery';
  setPartnerFormMessage('partnerGallery');
  setPartnerUploadStatus(statusKey, 'loading', 'Загружаем изображение…');
  renderPartnerLayout();
  try {
    await uploadPartnerPhoto(file);
    const successMessage = 'Изображение загружено. Фото загружено и отправлено на проверку. Фото появится после проверки/активации администратором.';
    setPartnerUploadStatus(statusKey, 'success', successMessage);
    setPartnerFormMessage('partnerGallery', successMessage);
    setPartnerPanelMessage(successMessage, 'success');
  } catch (error) {
    const errorMessage = getSafeUploadErrorMessage(error);
    setPartnerUploadStatus(statusKey, 'error', errorMessage);
    setPartnerFormMessage('partnerGallery', errorMessage);
    setPartnerPanelMessage(errorMessage, 'error');
  } finally {
    input.value = "";
    renderPartnerLayout();
  }
};

const handleAdminGalleryFormSubmit = async (form) => {
  setFormMessage('partnerGallery');
  try {
    await submitAdminPartnerPhoto(form);
    setFormMessage('partnerGallery', 'Фото обновлено.');
    setPanelMessage('Настройки фото сохранены.', 'success');
  } catch (error) {
    setFormMessage('partnerGallery', error.message || 'Не удалось сохранить фото.');
    setPanelMessage(error.message || 'Не удалось сохранить фото.', 'error');
  }
  renderAdminLayout();
};

const handlePartnerGalleryFormSubmit = async (form) => {
  setPartnerFormMessage('partnerGallery');
  try {
    await submitPartnerPhoto(form);
    setPartnerFormMessage('partnerGallery', 'Фото обновлено.');
    setPartnerPanelMessage('Настройки фото сохранены.', 'success');
  } catch (error) {
    setPartnerFormMessage('partnerGallery', error.message || 'Не удалось сохранить фото.');
    setPartnerPanelMessage(error.message || 'Не удалось сохранить фото.', 'error');
  }
  renderPartnerLayout();
};


const handleAdminPaymentOpen = async (requestId) => {
  adminState.paymentActionStatus = '';
  adminState.paymentActionError = '';
  renderAdminLayout();
  try {
    adminState.selectedPaymentRequest = await loadAdminPaymentRequest(requestId);
  } catch (error) {
    adminState.paymentActionError = error.message || 'Не удалось открыть детали заявки.';
  }
  renderAdminLayout();
};

const handleAdminPaymentApprove = async (requestId) => {
  adminState.paymentActionStatus = '';
  adminState.paymentActionError = '';
  renderAdminLayout();
  try {
    await approveAdminPaymentRequest(requestId, adminState.paymentApprovalDays);
    adminState.paymentActionStatus = 'Оплата подтверждена. Подписка продлена.';
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
