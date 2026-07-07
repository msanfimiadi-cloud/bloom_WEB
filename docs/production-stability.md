# Production stability diagnostics for bloomclub.ru

This runbook is for `Kosmos327/fed_women_club_WEB` deployed at `/opt/fed_women_club_WEB` behind nginx as `womenclub.service`.

## What changed for hardening

- `/health` and `/api/v1/health` are unauthenticated lightweight process checks.
- `/health/db` runs only `SELECT 1` and returns controlled JSON `503` if PostgreSQL is unavailable.
- The SQLAlchemy engine uses `pool_pre_ping=True` to avoid stale PostgreSQL connections after idle periods and `pool_recycle=1800` for non-SQLite databases.
- SQLAlchemy connectivity failures are logged and converted to controlled JSON responses instead of HTML tracebacks.
- Lightweight request logging records method, path, status, duration, and request ID without query strings, authorization tokens, hashes, passwords, or Mini App init data.

## Immediate checks when the site looks down

Run these from the production server first. If external curl fails but local curl works, focus on nginx, TLS, firewall, or network. If local backend health fails, focus on `womenclub.service`, Python logs, database, or host resources.

### Server/service

```bash
systemctl status womenclub --no-pager
journalctl -u womenclub -n 300 --no-pager
journalctl -u womenclub -f --no-pager
```

Check whether systemd reports repeated restarts, a non-zero exit code, `OOMKilled`, timeout, or dependency failures.

### Nginx

```bash
systemctl status nginx --no-pager
nginx -t
journalctl -u nginx -n 200 --no-pager
tail -n 200 /var/log/nginx/error.log
tail -n 200 /var/log/nginx/access.log
```

Look for `connect() failed`, `upstream timed out`, `connection refused`, TLS errors, or a spike of `502/503/504` responses.

### Network and health endpoints

```bash
curl -I https://bloomclub.ru
curl -i https://bloomclub.ru/health
curl -i https://bloomclub.ru/api/v1/health
curl -i https://bloomclub.ru/health/db
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/health/db
```

Expected results:

- `/health` and `/api/v1/health`: HTTP `200` with `status=ok`.
- `/health/db`: HTTP `200` when PostgreSQL is reachable; controlled HTTP `503` JSON if PostgreSQL is unavailable.
- `http://127.0.0.1:8000/` may still be `404` if nginx serves the frontend root; that is not a backend failure by itself.

### DB

Use the real values from the production environment and do not paste secrets into tickets or chat.

```bash
DATABASE_URL='...' alembic current
PGPASSWORD='...' psql -h localhost -U women_club_user -d women_club -c "SELECT 1;"
PGPASSWORD='...' psql -h localhost -U women_club_user -d women_club -c "SELECT count(*) FROM pg_stat_activity;"
```

If `SELECT 1` fails locally, inspect PostgreSQL status and logs. If `pg_stat_activity` is near the database limit, inspect request logs for slow endpoints and check whether clients are retrying aggressively.

### Resources

```bash
free -h
df -h
top
htop
dmesg -T | grep -iE "oom|killed|out of memory"
journalctl -k -n 200 --no-pager
```

Low memory, full disk, or kernel OOM kills can make both the website and Mini Apps appear offline because all API traffic depends on the same backend host.

## Recommended systemd unit hardening

Do not edit blindly; first inspect the active unit:

```bash
systemctl cat womenclub --no-pager
systemctl show womenclub -p Restart -p RestartSec -p MainPID -p NRestarts -p MemoryCurrent -p MemoryMax -p TasksCurrent -p LimitNOFILE --no-pager
```

Recommended settings for the backend service or an override file:

```ini
[Service]
Restart=on-failure
RestartSec=3
TimeoutStartSec=30
TimeoutStopSec=30
LimitNOFILE=65535
```

`Restart=always` is also acceptable when the process must be kept up even after clean exits, but `on-failure` is safer if planned maintenance uses clean stops. After changing an override:

```bash
systemctl daemon-reload
systemctl restart womenclub
systemctl status womenclub --no-pager
journalctl -u womenclub -n 100 --no-pager
```

## Recommended nginx reverse proxy assumptions

Confirm the active nginx site points API and health traffic to Uvicorn on `127.0.0.1:8000` and keeps the SPA static fallback intact. A typical proxy block should include:

```nginx
proxy_pass http://127.0.0.1:8000;
proxy_http_version 1.1;
proxy_connect_timeout 5s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

For the frontend static site, keep the SPA fallback, for example `try_files $uri $uri/ /index.html;`. Do not proxy the frontend root to FastAPI unless the deployment intentionally changed static hosting.

## After merge deployment checklist

```bash
cd /opt/fed_women_club_WEB
git status --short
git pull --ff-only
python -m compileall app scripts
pytest -q
cd frontend && npm run build
cd /opt/fed_women_club_WEB
alembic current
systemctl restart womenclub
systemctl status womenclub --no-pager
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/health/db
curl -i https://bloomclub.ru/health
curl -i https://bloomclub.ru/api/v1/health
curl -i https://bloomclub.ru/health/db
```

No new migration is required for this hardening change.
