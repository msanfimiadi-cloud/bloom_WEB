# Federal Women Club WEB

MVP web/backend skeleton based on club subscription platform.

Проект находится на этапе адаптации imported skeleton под федеральный женский клуб: визуальный слой переводится в premium beauty / lifestyle стиль, при этом бизнес-логика, backend-контракты и старые MVP flows не ломаются.

Federal Women Club проектируется как федеральный multi-city продукт с первого MVP:

- пользователь выбирает город в VK-боте и/или web;
- партнёр принадлежит одному городу;
- каталог партнёров фильтруется по городу;
- админка и аналитика должны быть готовы к фильтрам по городу;
- подписка в MVP глобальная для клуба, а не отдельная для каждого города;
- филиалы/locations партнёров не вводятся в MVP.


## Brand note

Визуальный стиль: premium beauty / lifestyle, пудрово-розовая палитра, rose-gold accents, federal/no city in brand. Основное название в интерфейсе — «Женский клуб», дополнительное позиционирование — «Федеральный клуб привилегий для девушек».

## Категории женского клуба

Централизованный backend-список категорий хранится в `app/core/categories.py`:

- Красота
- Маникюр / педикюр
- Волосы / окрашивание
- Брови / ресницы
- Косметология
- Массаж / SPA
- Фитнес / йога
- Здоровье
- Психология
- Одежда / аксессуары
- Кафе / рестораны
- Обучение / мастер-классы
- Фотосессии
- Цветы / подарки
- Другое

## Структура

- `app/` — backend application skeleton.
- `alembic/` — migration environment and migration versions.
- `scripts/` — operational helper scripts.
- `tests/` — backend tests.
- `frontend/` — frontend MVP skeleton.
- `docs/` — project documentation.

## Multi-city MVP notes

- `City` — минимальный справочник городов (`id`, `name`, `slug`, `is_active`, `sort_order`, `created_at`).
- `Partner.city_id` — nullable связь партнёра с городом для безопасной миграции skeleton-проекта.
- `ClientProfile.selected_city_id` — nullable выбранный город клиента; подписка остаётся глобальной.
- API/catalog план описан в `docs/mvp-spec.md` и подготовлен service-level helper для будущего endpoint.

## Локальный запуск backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Environment

Use `.env.example` as a safe local template. Do not commit real `.env` files or production secrets.

Key placeholders:

```bash
WEB_PUBLIC_URL=https://women-club.example
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Alembic

```bash
alembic heads
alembic upgrade head
```

## Frontend

```bash
cd frontend
npm install
npm run build
```

## Checks

```bash
python -m compileall app scripts
pytest -q
alembic heads
cd frontend && npm run build
```

## Admin Auth MVP

Минимальная авторизация администратора добавляет:

- таблицу `admin_users` с email, bcrypt-хешем пароля, ролью, активностью и датой создания;
- `POST /api/v1/auth/login` для получения JWT access token;
- `GET /api/v1/admin/me` для проверки текущего администратора по `Authorization: Bearer <token>`;
- frontend-форму входа, которая сохраняет token в `localStorage` и показывает простую карточку администратора.

### Required env

```bash
DATABASE_URL=sqlite+aiosqlite:///./test.db
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

`JWT_SECRET_KEY=change-me-in-production` — только безопасный placeholder для шаблона. На production необходимо задать длинный уникальный секрет через окружение и не коммитить его в репозиторий.

### Create the first admin

Перед созданием администратора примените миграции:

```bash
alembic upgrade head
python scripts/create_admin.py --email admin@example.com --password "StrongPassword123"
```

Если пользователь с таким email уже существует, скрипт напишет понятное сообщение и не создаст дубль. Пароль не выводится в лог и сохраняется только как bcrypt-хеш.

### Check login manually

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"StrongPassword123"}'
```

Затем проверьте защищённый endpoint:

```bash
curl http://localhost:8000/api/v1/admin/me \
  -H "Authorization: Bearer <access_token>"
```

### Frontend MVP security note

Для MVP frontend хранит JWT access token в `localStorage`, восстанавливает сессию через `/api/v1/admin/me`, удаляет token при ошибке проверки и показывает форму входа без валидного token. Для следующего production-hardening этапа стоит перейти на более строгую cookie/session модель и добавить refresh/revocation механику.
