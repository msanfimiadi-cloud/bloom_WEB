# Pre-deploy checklist

Use this checklist before promoting the MVP build to production. Keep real secrets in the deployment environment only; do not commit `.env` files.

## 1. Backend sanity checks

```bash
python -m compileall app scripts
pytest -q
alembic heads
```

Confirm Alembic reports a single head before applying migrations.

## 2. Migration dry-run / production note

For a local SQLite smoke test:

```bash
DATABASE_URL="sqlite+aiosqlite:////tmp/womenclub_predeploy_check.db" alembic upgrade head
```

For production, set `DATABASE_URL` to the production PostgreSQL async URL used by the application, for example `postgresql+asyncpg://...`. The Alembic environment converts `postgresql+asyncpg://` to `postgresql+psycopg://` for synchronous migration execution, so ensure the `psycopg` dependency is installed in the migration environment.

## 3. Required environment placeholders

Verify the production environment provides at least:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `BACKEND_CORS_ORIGINS`
- `WEB_PUBLIC_URL`

Use unique production values and never reuse placeholder secrets.

## 4. Create or verify admin access

Create the first admin account only from the server shell with production environment variables loaded:

```bash
read -s ADMIN_PASSWORD
python scripts/create_admin.py --email admin@example.com --password "$ADMIN_PASSWORD"
unset ADMIN_PASSWORD
```

Use the real administrator email and provide the password through the deployment runbook used for the server. Do not store the password in shell history or committed files.

## 5. Frontend build

```bash
cd frontend && npm run build
```

Deploy the generated frontend assets according to the hosting setup.

## 6. Restart services

Restart the backend application service, frontend/static service, and any reverse proxy process used by the deployment. Confirm the restarted backend reads the production environment variables.

## 7. Health checks

After restart, verify:

```bash
curl -fsS https://<production-host>/health
curl -fsS https://<production-host>/api/v1/health
curl -fsS https://<production-host>/health/db
```

See `docs/production-stability.md` for outage diagnostics, systemd checks, nginx checks, and PostgreSQL resource checks. Also smoke-test `/r/p/{slug}` with a known active partner QR slug before announcing the release.

## 8. Legacy WEB content admin read-only rollout

Before setting `WEB_ADMIN_LEGACY_CONTENT_WRITE_ENABLED=false` on staging or production, follow `docs/legacy-content-admin-readonly.md`. The short version is: verify `/api/content/health`, confirm `/api/v1/admin/me` returns `legacy_content_write_enabled=false`, confirm a legacy WEB content write returns `403`, and confirm `/api/content/admin/cities` returns `200` with `TELEGRAM_ADMIN_API_TOKEN`, `401` without a token, and `403` with a wrong token.
