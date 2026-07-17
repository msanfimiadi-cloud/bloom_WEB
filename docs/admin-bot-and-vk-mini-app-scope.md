# Admin bot and VK Mini App deployment scope

## Admin bot

The Browser Mobile App does not embed a Python `admin_bot` package or server component. Admin automation for the current WEB repository is handled by the documented bot/runtime flows outside `browser-mobile-app`:

- VK login-code bot deployment is documented in `docs/vk-bot-deploy.md`.
- Telegram/local catalog administration is served by the Browser Mobile App production server and its `/tg-admin` and `/api/tg/admin/*` routes when that deployment mode is enabled.

Because of this, Browser Mobile App tests must not require `admin_bot/admin_bot/__main__.py`. If a standalone admin bot is reintroduced, it must come with its own package, deployment documentation, and tests.

## VK Mini App

VK Mini App hosting on the WEB backend is optional and is documented separately in `docs/VK_MINI_APP_HOSTING.md`. Environments that declare VK Mini App support must build and place the VK Mini App artifact under `app/static/vk-mini-app/index.html`; environments that do not deploy it should not use Browser Mobile App tests as a proxy for VK Mini App readiness.

## Test contract

Regression tests should verify the active product contract:

- Browser Mobile App login-code and guest flows live under `browser-mobile-app`.
- VK bot login-code deployment is documented separately and links users to `https://app.bloomclub.ru`.
- VK Mini App hosting readiness is documented separately and depends on `app/static/vk-mini-app/index.html` in deployments that enable it.
