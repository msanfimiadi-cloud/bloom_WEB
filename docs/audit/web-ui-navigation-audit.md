## Phase 1 implementation notes

- Introduced unified button system classes: `.ui-button`, modifier variants (`--primary`, `--secondary`, `--ghost`, `--danger`, `--success`, `--disabled`), and size modifiers (`--sm`, `--md`, `--lg`, `--full`).
- Introduced shared action layout groups: `.ui-action-row`, `.ui-action-row--right`, `.ui-action-row--between`, `.ui-action-row--stack-mobile`, `.ui-card-actions`, `.ui-form-actions`, `.ui-toolbar-actions`.
- Backward compatibility aliases retained for admin inline actions: `.admin-inline-action--primary`, `.admin-inline-action--secondary`, `.admin-inline-action--danger` and `.admin-action-button` mapped visually to new UI button semantics.
- Action groups normalized in Admin/Partner/Client cards and media sections, including payment request cards and content review cards, by applying `ui-card-actions` / `ui-action-row` wrappers.
- Phase 2 TODO: deeper semantic review for ambiguous neutral actions (for example “Открыть партнёра” context priority) and broader refactor of legacy component-specific button selectors.

## Phase 2 implementation notes — Admin Partners

- Экран **Admin → Партнёры** переведён в формат реестра: список отображается в таблице с ключевыми колонками (партнёр, категории, статусы, витрина, услуги, обновление, действия).
- Форма создания/редактирования партнёра теперь **скрыта по умолчанию** и открывается по явному действию: кнопка «+ Добавить партнёра» или «Редактировать» в строке реестра.
- Форма структурирована по секциям: **Основное**, **Статусы**, **Категории**, **Контакты**, **Описание**, **Медиа**.
- Действия, существовавшие в бизнес-логике, сохранены без изменения API: редактирование, загрузка медиа и текущие submit-потоки create/edit.
- Для Phase 3 остаются: углублённые фильтры реестра, дополнительные массовые операции и расширенные сценарии аналитики/публикации в рамках отдельного UX-цикла.

## Phase 2.1 implementation notes — Admin Partners filters

- Добавлены frontend-only фильтры в Admin → Партнёры: город, категория, активность, фото, услуги и (условно) проверка, если в данных есть поле `is_verified`.
- Фильтрация выполняется только на уже загруженном наборе `adminState.partners` (без новых backend endpoint/API параметров).
- Multi-category filtering работает через существующую нормализацию `getPartnerCategories(...)`: партнёр с несколькими категориями участвует в каждой из них.
- Добавлены chips активных фильтров с точечным сбросом и кнопкой «Сбросить всё».
- Добавлена summary-строка «Найдено: N из TOTAL».
- Добавлены пустые состояния:
  - «Партнёры пока не добавлены.» с CTA «+ Добавить партнёра»;
  - «По выбранным фильтрам партнёры не найдены.» с CTA «Сбросить фильтры».
- На Phase 3 остаются архитектурные улучшения (drawer/сохранение фильтров между сессиями/расширенная аналитика по проблемным карточкам).

## Phase 3 implementation notes — Admin Partner wizard

- В админ-форму партнёра добавлен пошаговый wizard с шагами: `basic`, `status`, `contacts`, `description`, `media`, `review`.
- Для create/edit используется общий drawer и единый state `adminState.partnerFormStep`; при открытии create/edit шаг сбрасывается на `basic`, при cancel/успешном submit форма закрывается и шаг также сбрасывается.
- Submit партнёра выполняется только на последнем шаге (`review`); кнопка «Далее» всегда `type="button"`, а Enter до финального шага перехватывается для предотвращения ранней отправки.
- На шаге `review` добавлен frontend summary по текущим данным формы/партнёра (название, город, категории, активность, описание, фото, контакты).
- Backend/API/migrations не менялись: используются текущие payload и endpoints создания/редактирования партнёра.
- Следующая фаза: более детальная field-level валидация и автофокус/прокрутка к ошибкам по шагам.
