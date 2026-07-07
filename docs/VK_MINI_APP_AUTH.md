# VK Mini App Auth

## Endpoint

- `POST /api/v1/auth/vk-miniapp-login`
- Request body:
  - `launch_params` (required primary): raw VK Mini App launch query string.
  - `params` (optional): parsed params map.

## Required env vars

- `VK_APP_ID` — VK Mini App ID (for Bloom Club: `54600832`).
- `VK_APP_SECRET` — Mini App secret, required for signature verification.
- `VK_MINIAPP_AUTH_MAX_AGE_SECONDS` — max payload age (default `86400`).

## Signature verification

Backend verifies launch params before issuing JWT:

1. Parse query string.
2. Read `sign` and ensure it exists.
3. Collect only params starting with `vk_`.
4. Sort by key and build canonical query string.
5. HMAC-SHA256 using `VK_APP_SECRET`.
6. Encode digest as base64url without padding.
7. Compare with `sign` via `hmac.compare_digest`.
8. Validate `vk_app_id == VK_APP_ID`.
9. Validate numeric `vk_user_id`.
10. Validate `vk_ts` freshness against `VK_MINIAPP_AUTH_MAX_AGE_SECONDS`.

If client profile is not linked by `vk_user_id`, endpoint returns:

```json
{
  "status": "join_via_bot_required",
  "message": "Сначала присоединитесь к клубу через VK-бота."
}
```

## Frontend integration contract

Frontend VK Mini App should send launch params string as received from VK (`window.location.search` without trusted local transformations).


## CORS для VK Mini App

- Добавьте домен фронтенда Mini App в `BACKEND_CORS_ORIGINS` backend-сервера.
- Текущий домен фронтенда Timeweb: `https://kosmos327-fed-women-club-mini-app-3f15.twc1.net`.
- Пример: `BACKEND_CORS_ORIGINS=https://bloomclub.ru,https://www.bloomclub.ru,https://kosmos327-fed-women-club-mini-app-3f15.twc1.net`.
