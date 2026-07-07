# Legacy WEB content admin read-only rollout

Этот runbook нужен для безопасного staging/prod включения `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=false` в WEB backend Bloom Club. Он не меняет Telegram Admin Bot, Telegram Mini App и не удаляет legacy WEB admin: флаг только переводит старые WEB content write endpoints в read-only режим, пока Content Admin API остаётся основной поверхностью редактирования контента.

## A. Что делает флаг

- `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=true` — значение по умолчанию; legacy WEB admin content writes работают как раньше.
- `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=false` — legacy WEB admin продолжает читать данные, но content write endpoints отвечают `403 Forbidden`.
- `GET /api/v1/admin/me` возвращает безопасное boolean-поле `legacy_content_write_enabled`, чтобы frontend мог показать read-only notice и отключить content controls.
- Content Admin API `/api/content/admin/*` не зависит от этого флага и продолжает работать по `TELEGRAM_ADMIN_API_TOKEN`.

## B. Какие legacy WEB endpoints блокируются

При `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=false` должны возвращать `403` следующие legacy WEB content write endpoints:

| Метод | Endpoint |
| --- | --- |
| `PATCH` | `/api/v1/admin/landing-settings` |
| `POST` | `/api/v1/admin/cities` |
| `PATCH` | `/api/v1/admin/cities/{city_id}` |
| `POST` | `/api/v1/admin/categories` |
| `PATCH` | `/api/v1/admin/categories/{category_id}` |
| `POST` | `/api/v1/admin/partners` |
| `PATCH` | `/api/v1/admin/partners/{partner_id}` |
| `POST` | `/api/v1/admin/partners/{partner_id}/images` |
| `POST` | `/api/v1/admin/partners/{partner_id}/photos` |
| `PATCH` | `/api/v1/admin/partner-photos/{photo_id}` |
| `POST` | `/api/v1/admin/partners/{partner_id}/offers` |
| `POST` | `/api/v1/admin/offers/{offer_id}/image` |
| `PATCH` | `/api/v1/admin/offers/{offer_id}` |

Read endpoints вроде `GET /api/v1/admin/cities`, `GET /api/v1/admin/categories`, `GET /api/v1/admin/partners`, `GET /api/v1/admin/partners/{id}`, `GET /api/v1/admin/partners/{id}/photos`, `GET /api/v1/admin/partners/{id}/offers`, `GET /api/v1/admin/offers/{id}` остаются доступны при валидном WEB admin JWT.

## C. Какие WEB admin разделы остаются рабочими

После включения read-only режима в legacy WEB admin должны оставаться рабочими не-content операции:

- авторизация администратора и `GET /api/v1/admin/me`;
- просмотр списков content-разделов: города, категории, партнёры, предложения, фото, landing settings;
- пользователи и администраторы;
- оплаты и подтверждения;
- QR-ссылки, лиды и аналитика партнёров;
- content review / модерационные экраны, если они не выполняют legacy content writes.

На content-разделах WEB admin должен показывать read-only notice о переносе редактирования в Telegram Admin Bot и отключать кнопки создания/редактирования/загрузки/активации legacy content.

## D. Какие Content Admin API endpoints проверить

Минимальный smoke-check для Telegram Admin Bot поверхности:

- `GET /api/content/health` без token;
- `GET /api/content/admin/cities` с `TELEGRAM_ADMIN_API_TOKEN`;
- `GET /api/content/admin/categories` с `TELEGRAM_ADMIN_API_TOKEN`;
- `GET /api/content/admin/partners` с `TELEGRAM_ADMIN_API_TOKEN`;
- `GET /api/content/admin/giveaways` с `TELEGRAM_ADMIN_API_TOKEN`;
- `GET /api/content/admin/banners` с `TELEGRAM_ADMIN_API_TOKEN`;
- `GET /api/content/admin/blocks` с `TELEGRAM_ADMIN_API_TOKEN`.

Для полного staging сценария дополнительно проверьте через Telegram Admin Bot создание/редактирование тестовых entities: cities, categories, partners, offers, partner photos, offer photos, giveaways, giveaway items, banners и editable blocks.

## E. Verification commands

Подготовьте переменные окружения локально на staging shell. Не вставляйте реальные tokens в tickets/chat/logs.

```bash
export BASE_URL="https://bloomclub.ru"
export ADMIN_TOKEN="<web-admin-jwt>"
export TELEGRAM_ADMIN_API_TOKEN="<telegram-admin-api-token>"
```

Проверить Content API health:

```bash
curl -fsS "$BASE_URL/api/content/health"
```

Проверить `/api/v1/admin/me` и поле `legacy_content_write_enabled`:

```bash
curl -fsS "$BASE_URL/api/v1/admin/me" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Ожидаемо при включенном read-only режиме: JSON содержит `"legacy_content_write_enabled":false`.

Проверить, что legacy WEB content write endpoint возвращает `403` при `false`:

```bash
curl -sS -o /tmp/legacy-write-check.json -w "%{http_code}\n" \
  -X PATCH "$BASE_URL/api/v1/admin/landing-settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
cat /tmp/legacy-write-check.json
```

Проверить, что `/api/content/admin/cities` с `TELEGRAM_ADMIN_API_TOKEN` возвращает `200`:

```bash
curl -sS -o /tmp/content-cities-ok.json -w "%{http_code}\n" \
  "$BASE_URL/api/content/admin/cities" \
  -H "Authorization: Bearer $TELEGRAM_ADMIN_API_TOKEN"
```

Проверить, что без token `/api/content/admin/cities` возвращает `401`:

```bash
curl -sS -o /tmp/content-cities-missing-token.json -w "%{http_code}\n" \
  "$BASE_URL/api/content/admin/cities"
```

Проверить, что неправильный token возвращает `403`:

```bash
curl -sS -o /tmp/content-cities-bad-token.json -w "%{http_code}\n" \
  "$BASE_URL/api/content/admin/cities" \
  -H "Authorization: Bearer definitely-wrong-token"
```

Если в репозитории доступен operational script, можно выполнить те же safe checks одной командой:

```bash
BASE_URL="$BASE_URL" \
ADMIN_TOKEN="$ADMIN_TOKEN" \
TELEGRAM_ADMIN_API_TOKEN="$TELEGRAM_ADMIN_API_TOKEN" \
python scripts/check_legacy_content_readonly.py
```

Blocked write check в script выключен по умолчанию. Включайте его только на staging и только когда ожидаете `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=false`:

```bash
BASE_URL="$BASE_URL" \
ADMIN_TOKEN="$ADMIN_TOKEN" \
TELEGRAM_ADMIN_API_TOKEN="$TELEGRAM_ADMIN_API_TOKEN" \
python scripts/check_legacy_content_readonly.py --include-write-checks
```

## F. Как проверить Telegram Admin Bot после включения

1. Убедиться, что WEB backend и Telegram Admin Bot используют одинаковый актуальный `TELEGRAM_ADMIN_API_TOKEN`.
2. В Telegram Admin Bot открыть списки cities/categories/partners/offers/giveaways/giveaway items/banners/blocks.
3. На staging выполнить безопасные тестовые изменения на тестовых entities и убедиться, что публичный Content API отражает изменения.
4. Проверить, что ошибки auth различаются корректно: без token — `401`, неправильный token — `403`.
5. Проверить, что legacy WEB read-only notice не мешает Telegram Admin Bot write операциям.

## G. Как откатить

1. Вернуть `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=true` в окружении WEB backend.
2. Перезапустить WEB backend/frontend по стандартному deploy runbook.
3. Проверить `GET /api/v1/admin/me`: `legacy_content_write_enabled` снова `true`.
4. Повторить smoke-check legacy WEB content write на staging перед production rollback, чтобы убедиться, что write controls снова активны.
5. Оставить `TELEGRAM_ADMIN_API_TOKEN` без изменений, если проблема только в legacy WEB read-only режиме.

## H. Staging release checklist

- [ ] Установить `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=false` только в staging окружении WEB backend.
- [ ] Перезапустить WEB backend/frontend/static service по стандартному staging deploy runbook.
- [ ] Выполнить safe script checks без write-проверок: `python scripts/check_legacy_content_readonly.py`.
- [ ] Выполнить explicit blocked write check: `python scripts/check_legacy_content_readonly.py --include-write-checks`.
- [ ] Проверить WEB admin UI: read-only notice виден в content-разделах; content write controls disabled; users/payments/subscriptions доступны.
- [ ] Проверить Telegram Admin Bot на тестовых staging entities и убедиться, что Content Admin API продолжает писать контент.
- [ ] Если любой smoke-check failed, откатить staging env на `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=true` и не переносить изменение в production.

## I. Production rollout checklist

### До изменения production env

- [ ] Staging уже работает с `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=false` минимум один полный редакторский smoke-cycle.
- [ ] Telegram Admin Bot проверен на cities/categories/partners/offers/giveaways/giveaway items/banners/blocks.
- [ ] WEB admin JWT для проверки `/api/v1/admin/me` подготовлен только на время проверки.
- [ ] `TELEGRAM_ADMIN_API_TOKEN` задан в WEB backend и Telegram Admin Bot, не раскрыт в logs/tickets.
- [ ] Команда rollback знает, где поменять env обратно на `true` и как перезапустить сервисы.

### Включение

- [ ] Установить `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=false` в production окружении WEB backend.
- [ ] Перезапустить WEB backend/frontend/static service согласно `docs/deploy_checklist.md`.
- [ ] Проверить health: `curl https://bloomclub.ru/api/content/health`.
- [ ] Проверить `/api/v1/admin/me`: `legacy_content_write_enabled=false`.
- [ ] Проверить legacy blocked write: `PATCH /api/v1/admin/landing-settings` с `{}` возвращает `403`.
- [ ] Проверить Content Admin API auth: valid token `200`, missing token `401`, wrong token `403` на `/api/content/admin/cities`.
- [ ] Проверить WEB admin UI: content controls disabled, read-only notice виден, non-content разделы работают.
- [ ] Проверить Telegram Admin Bot списки и одну staging/prod-safe редакторскую операцию по согласованному редакторскому runbook.

### После включения

- [ ] Мониторить backend logs на `403` spikes от legacy WEB writes и ошибки `/api/content/admin/*`.
- [ ] Подтвердить с редакторами, что Telegram Admin Bot покрывает рабочий контент-процесс.
- [ ] Зафиксировать дату/время включения и владельца rollback.
