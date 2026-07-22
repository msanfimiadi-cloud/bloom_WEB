# Интернет-эквайринг Точка Банка

Bloom Club создаёт платёжные ссылки только на backend. Цена, срок тарифа и параметры чека берутся из БД и backend-конфигурации. Frontend получает только публичный ID, статус, сумму, валюту, URL оплаты и срок действия.

Первая версия поддерживает СБП и карту, чек с фискализацией, webhook RS256, ручную и фоновую сверку, полный/частичный возврат и аудит. Автопродление и сохранение карты не включены.

## Разрешения JWT

- `MakeAcquiringOperation`
- `ReadAcquiringData`
- `ReadCustomerData`
- `ManageWebhookData`

JWT хранится только в `.env` backend. Он не должен попадать в frontend, логи, fixtures или Git.

## Настройка

Скопируйте список `TOCHKA_*` из `.env.example` в production `.env`. Минимально при `TOCHKA_PAYMENTS_ENABLED=true` обязательны JWT, `customerCode`, `merchantId`, success/fail URL и публичный ключ webhook. `TOCHKA_TAX_SYSTEM_CODE`, НДС, способ и предмет расчёта подтвердите с бухгалтером до включения платежей.

Проверка подключения:

```bash
python -m app.cli.tochka_check
```

Команда проверяет API, Business customer, retailer со статусом `REG`, `isActive`, merchant/terminal, СБП, карту, кассу и webhook, не печатая JWT.

## Webhook

Публичный endpoint:

```text
POST https://bloomclub.ru/api/v1/payments/tochka/webhook
Content-Type: text/plain
```

В теле ожидается JWT, подписанный `RS256`. Подпись, сумма, `operationId`, `paymentLinkId`, `merchantId` и при наличии `customerCode` проверяются до активации подписки.

Управление:

```bash
python -m app.cli.tochka_webhooks list
python -m app.cli.tochka_webhooks ensure
python -m app.cli.tochka_webhooks test
```

`ensure` безопасен для повторного запуска: сохраняет корректную регистрацию, обновляет URL существующего события или создаёт webhook.

## API Bloom Club

- `POST /api/v1/clients/payments`
- `GET /api/v1/clients/payments/{payment_public_id}`
- `POST /api/v1/clients/payments/{payment_public_id}/refresh`
- `POST /api/v1/payments/tochka/webhook`
- `GET /api/v1/admin/payments`
- `GET /api/v1/admin/payments/{payment_id}`
- `POST /api/v1/admin/payments/{payment_id}/sync`
- `POST /api/v1/admin/payments/{payment_id}/refund`

Цена тарифа `monthly` создаётся миграцией как **349 ₽ / 30 дней**. Frontend не отправляет цену.

## Миграция и deploy

```bash
cd /opt/fed_women_club_WEB
git switch main
git pull --ff-only origin main

sudo systemd-run --wait --pipe --collect \
  --unit=bloom-alembic-upgrade \
  --property=Type=oneshot \
  --property=WorkingDirectory=/opt/fed_women_club_WEB \
  --property=EnvironmentFile=/opt/fed_women_club_WEB/.env \
  /opt/fed_women_club_WEB/.venv/bin/alembic upgrade head

cd frontend && npm ci && npm run build
cd ../browser-mobile-app && npm ci && npm run build
sudo systemctl restart womenclub.service
```

Для сверки установите примеры `bloom-tochka-reconcile.service` и `.timer` из `deploy/systemd`, затем выполните `systemctl daemon-reload` и включите timer. Интервал и jitter задаются timer; сама команда дополнительно соблюдает `TOCHKA_RECONCILIATION_INTERVAL_MINUTES`.

## Production-проверка

1. Оставьте `TOCHKA_PAYMENTS_ENABLED=false`, примените миграцию и перезапустите сервис.
2. Выполните `python -m app.cli.tochka_check`.
3. Выполните `python -m app.cli.tochka_webhooks ensure` и `test`.
4. Подтвердите налоговые параметры и включите флаг.
5. Создайте реальный платёж 349 ₽, оплатите СБП, проверьте webhook, чек, подписку и номер розыгрыша.
6. Выполните тестовый возврат из админки.

Redirect `/payment/success` не является подтверждением. Экран всегда запрашивает backend и ждёт webhook или серверную сверку.

## Ротация JWT

Перевыпустите JWT в Точке с теми же разрешениями, замените только `TOCHKA_JWT_TOKEN` в production `.env` и перезапустите backend. Refresh-token отсутствует. Ошибки 401/403 отображаются администратору как ошибка авторизации/разрешений без раскрытия токена.

## Диагностика

- `401`: JWT истёк или неверен.
- `403`: нет одного из требуемых разрешений.
- retailer не `REG` или не активен: эквайринг ещё не готов.
- нет `sbp` в `paymentModes`: СБП не подключён для точки.
- нет payment URL после timeout: внутренняя запись остаётся `pending`; новый `paymentLinkId` автоматически не создаётся. Запустите сверку.
- webhook conflict: проверьте operation/link ID, сумму, merchant и customerCode в журнале `payment_events`.

Официальная документация: [платёжные ссылки](https://developers.tochka.com/docs/tochka-api/opisanie-metodov/platyozhnye-ssylki/), [фискализация](https://developers.tochka.com/docs/tochka-api/opisanie-metodov/platyozhnye-ssylki/s-fiskalizaciej), [webhook](https://developers.tochka.com/docs/tochka-api/opisanie-metodov/vebhuki).

## Ограничения первой версии

Не реализованы двухэтапная оплата, Capture, «Долями», T-pay, сохранение карты, рекуррентные списания, подарок, split payments, несколько юрлиц и валют. При полном возврате подписка автоматически не отзывается: проект пока не хранит достоверный признак фактического использования услуги, поэтому отзыв требует отдельного утверждённого доменного правила.
