# Telegram admin bot → WEB Content Admin API

Документ фиксирует серверный API WEB backend, который может использовать новая Telegram bot админка Bloom Club. Telegram Mini App больше не должен выступать админкой: бот обращается к backend напрямую, поэтому CORS для этого клиента не нужен.

## Base URL

```text
https://bloomclub.ru/api/content
```

## Авторизация

Предпочтительный способ для Telegram admin bot:

```http
Authorization: Bearer <TELEGRAM_ADMIN_API_TOKEN>
```

Дополнительно backend принимает совместимый заголовок:

```http
X-Telegram-Admin-Token: <TELEGRAM_ADMIN_API_TOKEN>
```

Все endpoints с префиксом `/admin` и `POST /uploads` требуют admin token. Токен не возвращается в ответах и не должен логироваться клиентом.

Примеры ошибок:

```json
{"detail":"Not authenticated"}
```

```json
{"detail":"Admin role required"}
```


## Разделение с legacy WEB admin

Content Admin API остаётся основной поверхностью редактирования контента для Telegram Admin Bot. Для безопасного отключения старого редактирования контента в WEB admin добавлен feature flag `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED`: по умолчанию старые write endpoints работают, но при значении `false` legacy WEB admin больше не может изменять партнёров, услуги, фото, города, категории и landing settings; чтение и новый `/api/content/admin/*` остаются доступными.

При `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=false` legacy WEB admin показывает read-only notice для content-разделов: редактирование контента перенесено в Telegram Admin Bot, списки и карточки остаются доступными для просмотра, а создание/редактирование/загрузка/активация legacy content отключены. Флаг отдается в `GET /api/v1/admin/me` только как безопасный boolean `legacy_content_write_enabled`; секреты и токены не раскрываются.

Основная поверхность редактирования контента — Content Admin API `/api/content/admin/*`, которым пользуется Telegram Admin Bot для cities/categories/partners/offers/photos/giveaways/banners/blocks. Legacy WEB admin write endpoints `/api/v1/admin/landing-settings`, `/api/v1/admin/cities`, `/api/v1/admin/categories`, `/api/v1/admin/partners`, `/api/v1/admin/partners/{id}/images`, `/api/v1/admin/partners/{id}/photos`, `/api/v1/admin/partner-photos/{id}`, `/api/v1/admin/partners/{id}/offers` и `/api/v1/admin/offers/{id}`/`/image` должны возвращать 403 при выключенном флаге.

Проверка на staging:

1. Установить `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=false` и перезапустить WEB backend/frontend.
2. Войти в WEB admin и открыть «Города», «Категории», «Партнёры», «Предложения», «На проверке» и настройки главной: должен быть notice о переносе редактирования в Telegram Admin Bot, данные должны читаться, write-кнопки и upload-контролы должны быть недоступны.
3. Проверить `GET /api/v1/admin/me`: поле `legacy_content_write_enabled` должно быть `false`.
4. Проверить, что users/payments/subscriptions/support/admin-сценарии не заблокированы флагом: «Пользователи», «Оплаты», «Подтверждения», «QR / лиды» остаются рабочими в части не-content операций.
5. Проверить Telegram Admin Bot через `/api/content/admin/*`: `TELEGRAM_ADMIN_API_TOKEN` auth и content writes должны работать независимо от legacy WEB флага.

## Health

Публичный endpoint, без admin token:

```http
GET /api/content/health
```

Пример ответа:

```json
{"status":"ok","service":"content","database":"configured"}
```

## Upload

```http
POST /api/content/uploads
Content-Type: multipart/form-data
Authorization: Bearer <TELEGRAM_ADMIN_API_TOKEN>
```

Назначение: загрузка изображений для админского контента. Поддерживаются `jpg/jpeg`, `png`, `webp`; максимальный размер — 10 MB. Файл сохраняется в текущую директорию загрузок backend без изменения существующей схемы хранения.

Пример curl:

```bash
curl -X POST "https://bloomclub.ru/api/content/uploads" \
  -H "Authorization: Bearer $TELEGRAM_ADMIN_API_TOKEN" \
  -F "file=@./image.webp;type=image/webp"
```

Пример успешного ответа:

```json
{
  "url": "https://bloomclub.ru/uploads/content/9b8c7d6e-0000-4000-9000-123456789abc.webp",
  "path": "/uploads/content/9b8c7d6e-0000-4000-9000-123456789abc.webp",
  "filename": "9b8c7d6e-0000-4000-9000-123456789abc.webp",
  "content_type": "image/webp",
  "size": 34567
}
```

Пример ошибки формата:

```json
{"detail":"Invalid image content type"}
```

## Cities / Categories

```http
GET /api/content/admin/cities
GET /api/content/admin/categories
```

Эти endpoints нужны боту для выбора города и категории при создании или редактировании партнёра.

Пример ответа `GET /admin/cities`:

```json
[
  {"id":1,"name":"Новосибирск","slug":"novosibirsk","is_active":true,"sort_order":0,"created_at":"2026-06-11T00:00:00Z","updated_at":"2026-06-11T00:00:00Z"}
]
```

## Partners

```http
GET /api/content/admin/partners
POST /api/content/admin/partners
GET /api/content/admin/partners/{id}
PATCH /api/content/admin/partners/{id}
```

Payload создания:

```json
{
  "city_id": 1,
  "category_slug": "beauty",
  "category_ids": [1, 2],
  "name": "Bloom Spa",
  "description": "Спа-партнёр клуба",
  "address": "Красный проспект, 1",
  "phone": "+79990000000",
  "website_url": "https://example.com",
  "telegram_url": "https://t.me/example",
  "whatsapp_url": "https://wa.me/79990000000",
  "map_url": "https://maps.example/point",
  "working_hours": "10:00–20:00",
  "logo_url": "/uploads/content/logo.webp",
  "cover_url": "/uploads/content/cover.webp",
  "is_active": true,
  "is_verified": false,
  "sort_order": 0
}
```

Payload обновления может содержать любое подмножество полей, например для скрытия без hard delete:

```json
{"is_active":false}
```

Пример ответа:

```json
{
  "id": 10,
  "city_id": 1,
  "category_slug": "beauty",
  "category_ids": [1, 2],
  "name": "Bloom Spa",
  "description": "Спа-партнёр клуба",
  "address": "Красный проспект, 1",
  "phone": "+79990000000",
  "website_url": "https://example.com",
  "social_url": null,
  "instagram_url": null,
  "vk_url": null,
  "telegram_url": "https://t.me/example",
  "whatsapp_url": "https://wa.me/79990000000",
  "map_url": "https://maps.example/point",
  "working_hours": "10:00–20:00",
  "logo_url": "/uploads/content/logo.webp",
  "cover_url": "/uploads/content/cover.webp",
  "is_active": true,
  "is_verified": false,
  "sort_order": 0,
  "created_at": "2026-06-11T00:00:00Z",
  "updated_at": "2026-06-11T00:00:00Z"
}
```

## Partner photos

```http
GET /api/content/admin/partners/{id}/photos
POST /api/content/admin/partners/{id}/photos
PATCH /api/content/admin/partner-photos/{photo_id}
```

Payload создания:

```json
{"url":"/uploads/content/interior.webp","alt_text":"Интерьер","sort_order":0,"is_active":true}
```

Payload обновления:

```json
{"alt_text":"Главное фото партнёра","sort_order":10,"is_active":false}
```

Пример ответа:

```json
{"id":5,"partner_id":10,"url":"/uploads/content/interior.webp","alt_text":"Интерьер","sort_order":0,"is_active":true,"created_at":"2026-06-11T00:00:00Z","updated_at":"2026-06-11T00:00:00Z"}
```

Поле `is_main` в текущей content-модели отсутствует; для главного фото используйте `sort_order` и/или отдельное поле партнёра `cover_url`.

## Offers / Services

```http
GET /api/content/admin/partners/{id}/offers
POST /api/content/admin/partners/{id}/offers
GET /api/content/admin/offers/{id}
PATCH /api/content/admin/offers/{id}
```

Текущая схема БД хранит `base_price` и `discount_percent`. Для удобства бота API также принимает совместимые поля `regular_price`, `club_price`, `saving`, `terms` и возвращает их как вычисляемые значения.

Payload создания услуги:

```json
{
  "title": "Массаж",
  "description": "60 минут",
  "benefit_text": "Скидка для участниц клуба",
  "terms": "По предварительной записи",
  "regular_price": "5000.00",
  "club_price": "3500.00",
  "image_url": "/uploads/content/massage.webp",
  "is_active": true,
  "sort_order": 0
}
```

Backend пересчитает экономию безопасно:

```text
saving = regular_price - club_price = 5000.00 - 3500.00 = 1500.00
```

и сохранит эквивалентный `discount_percent`.

Payload обновления:

```json
{"club_price":"4000.00","is_active":true}
```

Пример ответа:

```json
{
  "id": 20,
  "partner_id": 10,
  "title": "Массаж",
  "description": "60 минут",
  "benefit_text": "Скидка для участниц клуба",
  "conditions": "По предварительной записи",
  "base_price": "5000.00",
  "discount_percent": "30.00",
  "regular_price": "5000.00",
  "club_price": "3500.00",
  "saving": "1500.00",
  "terms": "По предварительной записи",
  "image_url": "/uploads/content/massage.webp",
  "is_active": true,
  "sort_order": 0,
  "created_at": "2026-06-11T00:00:00Z",
  "updated_at": "2026-06-11T00:00:00Z"
}
```

## Offer photos

```http
GET /api/content/admin/offers/{id}/photos
POST /api/content/admin/offers/{id}/photos
PATCH /api/content/admin/offer-photos/{photo_id}
```

Payload создания:

```json
{"url":"/uploads/content/offer.webp","alt_text":"Фото услуги","sort_order":0,"is_active":true}
```

Пример ответа:

```json
{"id":7,"offer_id":20,"url":"/uploads/content/offer.webp","alt_text":"Фото услуги","is_active":true,"sort_order":0,"created_at":"2026-06-11T00:00:00Z","updated_at":"2026-06-11T00:00:00Z"}
```

## Giveaways

Розыгрыши реализованы на уровне `content_giveaways`:

```http
GET /api/content/admin/giveaways
POST /api/content/admin/giveaways
GET /api/content/admin/giveaways/{id}
PATCH /api/content/admin/giveaways/{id}
```

Payload:

```json
{
  "title": "Розыгрыш июня",
  "current": "Сертификат Bloom Spa",
  "subtitle": "Для активных участниц клуба",
  "empty_text": "Скоро объявим новый приз",
  "is_active": true,
  "sort_order": 0,
  "starts_at": "2026-06-01T00:00:00Z",
  "ends_at": "2026-06-30T23:59:59Z"
}
```

### Giveaway items / prizes

Telegram Admin Bot должен использовать эти endpoints для управления призами внутри розыгрыша (`content_giveaway_items`). Auth такой же, как у остальных Content Admin endpoints: `Authorization: Bearer <TELEGRAM_ADMIN_API_TOKEN>` или совместимый заголовок `X-Telegram-Admin-Token: <TELEGRAM_ADMIN_API_TOKEN>`.

```http
GET /api/content/admin/giveaways/{giveaway_id}/items
POST /api/content/admin/giveaways/{giveaway_id}/items
GET /api/content/admin/giveaway-items/{item_id}
PATCH /api/content/admin/giveaway-items/{item_id}
```

Create payload:

```json
{
  "title": "Сертификат Bloom Spa",
  "description": "Главный приз розыгрыша",
  "image_url": "/uploads/content/prize.webp",
  "sort_order": 10,
  "is_active": true
}
```

Create/read response:

```json
{
  "id": 15,
  "giveaway_id": 3,
  "title": "Сертификат Bloom Spa",
  "description": "Главный приз розыгрыша",
  "image_url": "/uploads/content/prize.webp",
  "is_active": true,
  "sort_order": 10,
  "created_at": "2026-06-22T00:00:00Z",
  "updated_at": "2026-06-22T00:00:00Z"
}
```

Update payload меняет только переданные поля:

```json
{"title":"Обновлённый приз","is_active":false}
```

List response сортируется по `sort_order`, затем `id`:

```json
[
  {"id":15,"giveaway_id":3,"title":"Сертификат Bloom Spa","description":"Главный приз розыгрыша","image_url":"/uploads/content/prize.webp","is_active":true,"sort_order":10,"created_at":"2026-06-22T00:00:00Z","updated_at":"2026-06-22T00:00:00Z"}
]
```

Если розыгрыш или приз не найден, API возвращает `404`. Физическое удаление не добавлено; для скрытия приза используйте `PATCH /api/content/admin/giveaway-items/{item_id}` с `{"is_active": false}`. Публичный `GET /api/content/giveaways` отдаёт только активные items, отсортированные по `sort_order`, затем `id`.

## Home / content blocks

Публичный endpoint для клиентов сохранён:

```http
GET /api/content/blocks
GET /api/content/blocks?type=static_texts
```

Admin endpoints уже есть и могут использоваться осторожно:

```http
POST /api/content/admin/blocks
PATCH /api/content/admin/blocks/{key}
```

Полноценная CMS главной для bot Stage 1 не реализована. Если в боте нужен раздел “Главная”, рекомендуется на первом этапе показывать заглушку “Управление главной будет добавлено позже”.

## Публичные Content API endpoints, которые нельзя ломать

```http
GET /api/content/health
GET /api/content/blocks
GET /api/content/cities
GET /api/content/categories
GET /api/content/partners
GET /api/content/partners/{id}
GET /api/content/partners/{id}/offers
GET /api/content/giveaways
GET /api/content/banners
```

## Endpoints, которых пока не хватает для полного бота

- Явное поле `is_main` для фото партнёра/услуги, если бизнес-логика потребует не только сортировку.
- Полноценные admin `GET` endpoints для просмотра content blocks по ключу/списком перед редактированием; сейчас есть публичный список активных блоков, `POST` и upsert через `PATCH`.
- Hard delete намеренно не добавлен. Для Stage 1 используйте `PATCH is_active=false`.

## Риски после деплоя

- Убедиться, что переменная окружения `TELEGRAM_ADMIN_API_TOKEN` задана только на WEB backend и сервере Telegram bot.
- Проверить, что production `WEB_PUBLIC_URL` указывает на `https://bloomclub.ru`, чтобы upload возвращал корректные абсолютные URL.
- Не расширять CORS ради Telegram bot: бот не браузерный клиент.
