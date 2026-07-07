# WEB Release QA Checklist

## Scope and guardrails
- Scope: **WEB repository only** (`fed_women_club_WEB`).
- Mini App is out of scope and must not be changed.
- No production code changes unless a real release blocker is found.
- No feature additions/redesign in release QA.

## WEB checks
- Verify admin partners table and filter behavior.
- Verify Admin Partner Wizard open state and step transitions:
  - `adminState.partnerFormOpen`
  - `adminState.partnerFormStep`
  - wizard steps basic → media → offers → review.
- Verify client catalog and partner details are available in WEB flows.
- Verify partner offers are rendered from `partner_offers` and pricing block uses:
  - `getOfferPricingView`
  - `renderOfferPricingBlock`
  - labels: `Обычная цена`, `Для участниц клуба`, `Выгода`.
- Verify `discount_percent` remains supported as legacy/fallback input.

## Backend checks
Run from repo root:

```bash
python -m compileall app scripts
pytest -q
alembic heads
alembic current
```

Notes:
- Do **not** run `alembic upgrade` on production DB in this QA PR.
- Record `alembic heads/current` output in release summary.

## Frontend build checks
Run from `frontend/`:

```bash
npm install
npm run build
node --check dist/assets/main.js
```

## dist integrity checks
`frontend/dist/index.html` must reference:
- `/assets/main.js`
- `/assets/styles.css`

And must **not** reference:
- `/src/main.js`
- `/src/styles.css`

## Catalog contract checklist
- `GET /api/v1/clients/catalog/partners` requires client Bearer auth (`require_client`).
- City filter behavior:
  - `city_id`
  - `city_slug`
  - fallback to client profile selected city.
- Category filter is M2M-aware (`category_ids/category_slugs/categories`) with legacy fallback.
- `GET /api/v1/clients/partners/{id}/offers` returns active `PartnerOffer` entries from `partner_offers`.
- `image_url` is optional and must not break response visibility.

## Price UX contract checklist
For partner offers in WEB client/admin views:
- Show **Обычная цена** when base price exists.
- Show **Для участниц клуба** when member price/fallback is available.
- Show **Выгода** when saving is calculable.
- Keep `discount_percent` as legacy/fallback compatibility field.

## Admin Partner Wizard checklist
- Admin → Partners opens correctly.
- `+ Добавить партнёра` opens wizard panel.
- Steps switch correctly and validation blocks invalid transitions.
- Multi-category selection (`category_ids`) persists on save.
- Edit partner preserves selected categories and offer data.

## Deploy commands
```bash
cd /opt/fed_women_club_WEB
git fetch origin
git checkout main
git pull origin main

source .venv/bin/activate
set -a
source .env
set +a

python -m compileall app scripts
pytest -q

cd frontend
npm install
npm run build
node --check dist/assets/main.js
cd ..

systemctl restart womenclub
systemctl status womenclub --no-pager
journalctl -u womenclub -n 120 --no-pager
```

## Manual QA checklist
- [ ] WEB opens.
- [ ] Admin login works.
- [ ] Admin → Партнёры opens.
- [ ] Search/filter partners works.
- [ ] + Добавить партнёра opens wizard.
- [ ] Wizard steps work.
- [ ] Multi-category save works.
- [ ] Edit partner works.
- [ ] Client catalog endpoint works with Bearer token.
- [ ] Partner detail works.
- [ ] Partner offers endpoint works.
- [ ] Price block shows: Обычная цена / Для участниц клуба / Выгода.
- [ ] Savings page works.
- [ ] No JS console errors.

## Rollback hints
- Re-deploy previous known-good commit/tag.
- Rebuild frontend assets from that commit (`npm install && npm run build`).
- Restart service and verify health/status logs.
- If DB schema drift is suspected, stop rollout and validate alembic revision state before any migration action.
