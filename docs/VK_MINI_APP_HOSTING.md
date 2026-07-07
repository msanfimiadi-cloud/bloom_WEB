# VK Mini App hosting on WEB (`/vk-mini-app/`)

## Purpose
This WEB repository serves the **compiled** frontend bundle of the separate Mini App project (`Kosmos327/fed_women_club_mini-app`) at:

- `https://bloomclub.ru/vk-mini-app/`

> Mini App source code is **not** moved into this repository.

## Build source
Mini App build is produced in the dedicated frontend repository:

- Repo: `Kosmos327/fed_women_club_mini-app`
- Build output: `dist/` (or the output directory configured in that repository)

## Where to copy build in WEB repo
Copy the built Mini App files into:

- `app/static/vk-mini-app/`

Expected result after copy:

- `app/static/vk-mini-app/index.html`
- `app/static/vk-mini-app/assets/*`
- other static files from Mini App build

## Runtime URL routing in WEB
Configured routes in FastAPI:

- `GET /vk-mini-app/` → serves `app/static/vk-mini-app/index.html`
- `GET /vk-mini-app/*`:
  - if exact static file exists, serves that file;
  - otherwise returns `index.html` (SPA fallback for client-side routing).

## VK Developer URL
For VK Mini Apps settings use:

- `https://bloomclub.ru/vk-mini-app/`

## Required frontend env for Mini App build
Set these in the **Mini App frontend repository** build pipeline/environment:

- `VITE_API_BASE_URL=https://bloomclub.ru`
- `VITE_VK_APP_ID=54600832`
- `VITE_VK_BOT_URL=<ссылка на VK bot/community>`

## Secrets rule
- `VK_APP_SECRET` must be stored **only in backend/server env**.
- Never expose `VK_APP_SECRET` in frontend `.env`, source code, or build artifacts.

## Example build/copy/deploy flow

### 1) Build in Mini App repository
```bash
cd /path/to/fed_women_club_mini-app
npm ci
VITE_API_BASE_URL=https://bloomclub.ru \
VITE_VK_APP_ID=54600832 \
VITE_VK_BOT_URL=https://vk.com/<community_or_bot_link> \
npm run build
```

### 2) Copy build into WEB repository
```bash
cd /path/to/fed_women_club_WEB
rm -rf app/static/vk-mini-app/*
cp -R /path/to/fed_women_club_mini-app/dist/* app/static/vk-mini-app/
```

### 3) Deploy WEB backend/service
Use the existing WEB deploy process (service restart / container rollout) so new static files become available at:

- `https://bloomclub.ru/vk-mini-app/`

## Quick post-deploy checks
```bash
curl -I https://bloomclub.ru/vk-mini-app/
curl -I https://bloomclub.ru/vk-mini-app/assets/<bundle-file>.js
curl -I https://bloomclub.ru/vk-mini-app/any/client/route
```

Expected: index route and SPA route return `200` (SPA route should resolve to `index.html`).
