# RAG-020 — Environment & Configuration

**Metadata:** `id=RAG-020` | `tags=env,settings,decouple`

## Setup

1. Copy `.env.example` → `.env`
2. Set `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
3. Database: default SQLite via `DB_ENGINE` / `DB_NAME`

## Key settings file

`rentsecure_be/settings.py` — uses `python-decouple` `config()`

## Database env vars

`DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

## URLs

`FRONTEND_URL`, `BACKEND_URL` — used in emails/links

## JWT / cache

- `REST_FRAMEWORK` → JWT authentication
- `CACHES` → locmem, 5 min default timeout for property lists

## Security-related

`CSRF_TRUSTED_ORIGINS`, `SESSION_COOKIE_SECURE`, `SECURE_SSL_REDIRECT` (production)

## Dependency note

`requirements.txt` may pin `python-decouple==3.9` which **fails pip install** — use 3.8.

## pytest

`pytest.ini` — `DJANGO_SETTINGS_MODULE=rentsecure_be.settings`, coverage 90% threshold

## For AI

When suggesting deployment, always mention: seed `SubscriptionPlan` + `PlanFeatureLimit`, wire signals in apps.py, fix webhook handlers.
