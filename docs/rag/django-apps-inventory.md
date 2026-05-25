# RAG-004 — Django Apps & URL Mounts

**Metadata:** `id=RAG-004` | `tags=installed_apps,urls,django`

## INSTALLED_APPS (`rentsecure_be/settings.py`)

| App | Registered | In root URLs | Notes |
|-----|------------|--------------|-------|
| `core` | Yes | `/api/` via `core.urls` | Auth, subscriptions, webhooks |
| `notification` | Yes | (no direct prefix) | Imported by other apps |
| `properties` | Yes | `/api/`, `/properties/` | Main REST API |
| `finance` | Yes | `/finance/` | Tax, CA |
| `referral_and_earn` | Yes | (OTP only) | No dedicated URL include |
| `documents` | Yes | `/documents/` | PDF generation |
| `smartbot` | Yes | **No** | Not in `rentsecure_be/urls.py` |
| `ai_assistant` | **No** | No | Imported by `properties/signals` only |
| `dashboard` | **No** | `/dashboard/` | Views work but app not registered |
| `fcm_django` | Yes | — | Push tokens |
| `django_celery_beat` | Yes | — | Schedules |

## Root URL patterns (`rentsecure_be/urls.py`)

| Prefix | Included urls |
|--------|----------------|
| `/admin/` | Django admin |
| `/api/` | `core.urls` + `properties.urls` |
| `/properties/` | `properties.urls` (duplicate mount) |
| `/finance/` | `finance.urls` |
| `/documents/` | `documents.urls` |
| `/dashboard/` | `dashboard.urls` |

## AUTH

- `AUTH_USER_MODEL = 'core.User'`
- JWT: access 5 min, refresh 35 days (`SIMPLE_JWT` in settings)
