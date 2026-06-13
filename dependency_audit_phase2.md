# RentSecureBE – Dependency Hygiene Audit (Phase 2)

**Auditor:** Principal Staff Engineer / Dependency Governance Reviewer
**Date:** 2026-05-06
**Scope:** `requirements.txt` (217 pinned packages)
**Status:** ANALYSIS ONLY – No changes applied
**Prior Phase:** Phase 1 CI/CD hardening (NOT reviewed)

---

## 1. Executive Summary

The current `requirements.txt` is a **flat, unsorted dump of 217 packages** that mixes:

- **Production runtime** packages (Django, DRF, weasyprint, twilio, etc.)
- **Test-only** packages (`pytest`, `pytest-django`)
- **Transitive dependencies** that should NOT be pinned at top level (cryptography, cffi, certifi, urllib3, etc.)
- **Dev tooling** accidentally absorbed into the lockfile (jupyter, ipython, debugpy, etc.)
- **Possibly Unused / Dead** packages (instagram-private-api, instaloader, Flask, fpdf, fpdf2, selenium, SQLAlchemy, django-rest-auth, django-otp, etc.)
- **Suspicious / Risky** packages (Instagram private API, leaked tokens via razorpay==1.4.2)

The project imports `celery` ecosystem packages and registers `django_celery_beat`, but **there is no `celery.py` file in the project** – this is a major architectural smell.

**Risk Level: HIGH** for the dependency surface area.
**Risk Level: MEDIUM** for security (mostly transitive, but a few old/abandoned packages exist).

---

## 2. Methodology

### 2.1 Import Search Strategy

For every package in `requirements.txt` we ran:

```bash
grep -rhE "^(import|from) <pkg>" --include="*.py" \
  --exclude-dir=".venv" --exclude-dir="venv" --exclude-dir="node_modules" \
  --exclude-dir=".kilo" --exclude-dir=".git" --exclude-dir="migrations"
```

We excluded:
- `.venv` / `venv` (dependencies of dependencies)
- `.kilo/worktrees/*` (transient agent scratch space)
- `migrations/` (auto-generated)

We also searched for indirect uses (decorators, `INSTALLED_APPS`, lazy imports inside function bodies, `Celery` keyword, `shared_task` keyword, etc.).

### 2.2 Result Sets

| Set | Unique top-level packages |
| --- | --- |
| All imports (incl. migrations) | 131 |
| Production + test imports (no migrations) | 129 |
| Production-only (no migrations, no `_legacy`, no `test_*`) | 123 |

### 2.3 Classification Legend

- **P** = Production (imported by production code or listed in `INSTALLED_APPS`)
- **D** = Development (test/lint only, not imported by production code)
- **T** = Transitive (pulled in by a P/D package; do NOT pin at top level)
- **U** = Possibly Unused (no direct or indirect import found)
- **?** = Unknown (no direct import but architecturally wired – needs code review)

---

## 3. Full Dependency Inventory (217 packages)

| # | Package | Version | Class | Evidence / Files | Notes |
|---|---------|---------|-------|------------------|-------|
| 1 | aiohappyeyeballs | 2.6.1 | T | – | aiohttp transitive |
| 2 | aiohttp | 3.11.18 | T | – | aiohttp transitive (httpx optional) |
| 3 | aiohttp-retry | 2.9.1 | T | – | aiohttp transitive |
| 4 | aiosignal | 1.3.2 | T | – | aiohttp transitive |
| 5 | amqp | 5.3.1 | T | – | kombu/celery transitive |
| 6 | anyio | 4.12.1 | T | – | httpx/trio transitive |
| 7 | appnope | 0.1.4 | T | – | jupyter/ipython transitive (macOS debug shim) |
| 8 | argon2-cffi | 23.1.0 | T | – | django.contrib.auth password hasher transitive |
| 9 | argon2-cffi-bindings | 21.2.0 | T | – | argon2-cffi transitive |
| 10 | arrow | 1.3.0 | T | – | Likely celery/scheduler transitive |
| 11 | asgiref | 3.8.1 | P | (Django) | ASGI adapter |
| 12 | asttokens | 3.0.0 | T | – | ipython/jupyter transitive |
| 13 | async-lru | 2.0.4 | T | – | jupyter transitive |
| 14 | async-timeout | 5.0.1 | T | – | aiohttp transitive |
| 15 | attrs | 25.3.0 | T | – | jsonschema/pytest transitive |
| 16 | Babel | 2.15.0 | T | – | jupyter transitive |
| 17 | beautifulsoup4 | 4.14.3 | T | – | jupyter/bleach transitive |
| 18 | billiard | 4.2.4 | T | – | celery transitive |
| 19 | bleach | 6.1.0 | T | – | jupyter transitive |
| 20 | blinker | 1.9.0 | T | – | Flask transitive (will go when Flask removed) |
| 21 | boto3 | 1.18.53 | P | `notification/services/whatsapp_service.py: import boto3` (lazy) | **OUTDATED** (current is 1.35+). Upgrade. |
| 22 | botocore | 1.21.53 | T | – | boto3 transitive |
| 23 | Brotli | 1.1.0 | T | – | httpx / urllib3 transitive |
| 24 | CacheControl | 0.14.3 | T | – | pip cache manager, install-time only |
| 25 | cachetools | 5.5.2 | T | – | google-auth transitive |
| 26 | **celery** | 5.6.3 | **U / Architectural Risk** | 0 `from celery` imports, no `celery.py` file, only docstring + scheduler comments | `django_celery_beat` is in `INSTALLED_APPS`, but **no Celery app is defined**. Either the team forgot to create `rentsecure_be/celery.py`, or the whole celery stack is dead weight. |
| 27 | certifi | 2025.4.26 | T | – | requests / urllib3 transitive |
| 28 | cffi | 1.17.1 | T | – | cryptography transitive |
| 29 | chardet | 3.0.4 | T | – | requests transitive |
| 30 | charset-normalizer | 3.4.2 | T | – | requests transitive |
| 31 | click | 8.1.8 | T | – | celery transitive |
| 32 | click-didyoumean | 0.3.1 | T | – | celery transitive |
| 33 | click-plugins | 1.1.1.2 | T | – | celery transitive |
| 34 | click-repl | 0.3.0 | T | – | celery transitive |
| 35 | comm | 0.2.2 | T | – | ipykernel transitive |
| 36 | cron-descriptor | 1.4.5 | T | – | django-celery-beat transitive |
| 37 | cryptography | 45.0.2 | T | – | PyJWT / requests / twilio transitive |
| 38 | cssselect2 | 0.8.0 | T | – | weasyprint transitive |
| 39 | debugpy | 1.8.14 | T | – | jupyter/IDE debug transitive |
| 40 | decorator | 5.2.1 | T | – | ipython transitive |
| 41 | deep-translator | 1.11.4 | P | `ai_assistant/services/i18n_service.py: from deep_translator import GoogleTranslator` | Production translation |
| 42 | defusedxml | 0.7.1 | T | – | jupyter transitive |
| 43 | **dj-database-url** | 2.3.0 | **U** | 0 imports | Not used in `settings.py` (which uses `decouple.config`) – consider removing |
| 44 | Django | 4.2.30 | P | (framework) | **LTS – upgrade to 5.0 LTS or 5.2 LTS recommended** |
| 45 | django-appconf | 1.1.0 | T | – | django-celery-beat / fcm-django transitive |
| 46 | django-celery-beat | 2.9.0 | P | `INSTALLED_APPS`, `from django_celery_beat.models import PeriodicTask` | Depends on celery being actually configured |
| 47 | **django-cors-headers** | 3.9.0 | **U** | 0 imports, not in INSTALLED_APPS, not in MIDDLEWARE | Should be removed (or wired up) |
| 48 | **django-crum** | 0.7.9 | **U** | 0 imports | Should be removed |
| 49 | **django-multiselectfield** | 0.1.12 | **U** | 0 imports | Should be removed (or used) |
| 50 | **django-otp** | 1.6.0 | **U** | 0 imports; tests use `OTP` model from `core.models`, not from `django_otp` | Should be removed – auth is custom |
| 51 | **django-rest-auth** | 0.9.5 | **U** | 0 imports; **DEPRECATED** (last release 0.9.5 in 2019) | Remove – functionality replaced by `rest_framework_simplejwt` |
| 52 | **django-s3-storage** | 0.13.4 | **U** | 0 imports, not in INSTALLED_APPS | Project uses `django-storages` – this is duplicate functionality |
| 53 | **django-select2** | 8.2.3 | **U** | 0 imports, not in INSTALLED_APPS | Remove – only relevant for admin UI |
| 54 | django-simple-history | 3.8.0 | P | Many imports of `HistoricalRecords`, `SimpleHistoryAdmin`, in INSTALLED_APPS and MIDDLEWARE | Audit tracking – production critical |
| 55 | django-storages | 1.11.1 | T? | Not imported in code; not in `INSTALLED_APPS` and not in `DEFAULT_FILE_STORAGE` | Used as a transitive; confirm if S3 storage is actually needed |
| 56 | django-timezone-field | 7.2.1 | T | – | django-celery-beat transitive |
| 57 | **django-widget-tweaks** | 1.4.8 | **U** | 0 imports | Should be removed (template-only and not referenced) |
| 58 | djangorestframework | 3.16.0 | P | 20+ import sites | API framework |
| 59 | djangorestframework_simplejwt | 5.5.0 | P | `core/urls.py`, `core/views.py`, `rentsecure_be/settings.py` | JWT auth – production critical |
| 60 | **drf-writable-nested** | 0.7.0 | **U** | 0 imports | Remove |
| 61 | et_xmlfile | 2.0.0 | T | – | openpyxl transitive |
| 62 | exceptiongroup | 1.3.1 | T | – | pytest / anyio transitive |
| 63 | executing | 2.2.0 | T | – | stack-data / ipython transitive |
| 64 | fastjsonschema | 2.20.0 | T | – | jupyter transitive |
| 65 | fcm-django | 2.2.1 | P | 2 import sites (`notification/utils.py`, `notification/views.py`), in INSTALLED_APPS | Push notifications |
| 66 | firebase-admin | 6.8.0 | P (transitive-of-P) | No direct import; fcm-django uses it as a backend | Required runtime for fcm-django |
| 67 | **Flask** | 3.1.1 | **U** | 0 imports | **CRITICAL: should not be in a Django project** – remove |
| 68 | fonttools | 4.60.2 | T | – | weasyprint transitive |
| 69 | **fpdf** | 1.7.2 | **U** | 0 imports (project uses fpdf2 and weasyprint) | Remove |
| 70 | **fpdf2** | 2.8.3 | **U** | 0 imports (PDFs are made via weasyprint) | Remove |
| 71 | fqdn | 1.5.1 | T | – | jsonschema transitive |
| 72 | frozenlist | 1.6.0 | T | – | aiohttp transitive |
| 73 | google-api-core | 2.25.0rc1 | T | – | **Outdated pre-release** – comes via firebase-admin/google-api-python-client. |
| 74 | **google-api-python-client** | 2.170.0 | **U** | 0 imports | Remove – firebase-admin provides what is needed |
| 75 | google-auth | 2.40.2 | T | – | google-api-* / firebase transitive |
| 76 | google-auth-httplib2 | 0.2.0 | T | – | google-api-python-client transitive |
| 77 | **google-cloud-core** | 2.4.3 | **U** | 0 imports | Remove – not used |
| 78 | **google-cloud-firestore** | 2.20.2 | **U** | 0 imports | Remove – not used |
| 79 | **google-cloud-storage** | 3.1.0 | **U** | 0 imports | Remove – not used (could be re-added if S3 migration is planned) |
| 80 | google-crc32c | 1.7.1 | T | – | google-cloud-* transitive |
| 81 | google-resumable-media | 2.7.2 | T | – | google-cloud-storage transitive |
| 82 | googleapis-common-protos | 1.70.0 | T | – | google-api-* transitive |
| 83 | grpcio | 1.71.0 | T | – | firebase-admin / google-cloud transitive |
| 84 | grpcio-status | 1.71.0 | T | – | google-cloud transitive |
| 85 | gTTS | 2.5.4 | P | 1 import (`from gtts import gTTS`) | Voice notes via Twilio |
| 86 | h11 | 0.16.0 | T | – | httpcore / hyper transitive |
| 87 | h2 | 3.2.0 | T | – | httpx[http2] transitive |
| 88 | hpack | 3.0.0 | T | – | h2 transitive |
| 89 | hstspreload | 2025.1.1 | T | – | cryptography transitive |
| 90 | httpcore | 1.0.9 | T | – | httpx transitive |
| 91 | httplib2 | 0.22.0 | T | – | google-api-python-client transitive |
| 92 | httpx | 0.28.1 | T | – | Used by `openai` and `notebook` transitively |
| 93 | hyperframe | 5.2.0 | T | – | h2 transitive |
| 94 | idna | 2.10 | T | – | requests / urllib3 transitive |
| 95 | importlib_metadata | 8.2.0 | T | – | celery / pluggy transitive |
| 96 | iniconfig | 2.1.0 | T | – | pytest transitive |
| 97 | **instagram-private-api** | 1.6.0.0 | **U / RISKY** | 0 imports | **HIGH RISK: unofficial reverse-engineered package** – remove immediately. Also unmaintained. |
| 98 | **instaloader** | 4.14.1 | **U** | 0 imports | Likely aspirational – remove |
| 99 | ipykernel | 6.29.5 | T | – | jupyter transitive |
| 100 | ipython | 8.18.1 | T | – | jupyter transitive |
| 101 | ipython_pygments_lexers | 1.1.1 | T | – | ipython transitive |
| 102 | isoduration | 20.11.0 | T | – | jsonschema transitive |
| 103 | itsdangerous | 2.2.0 | T | – | Flask transitive – goes away when Flask is removed |
| 104 | jedi | 0.19.2 | T | – | ipython transitive |
| 105 | Jinja2 | 3.1.4 | T | – | Flask / weasyprint transitive |
| 106 | jmespath | 0.10.0 | T | – | boto3 / botocore transitive |
| 107 | json5 | 0.9.25 | T | – | jupyter transitive |
| 108 | jsonpointer | 3.0.0 | T | – | jsonschema transitive |
| 109 | jsonschema | 4.23.0 | T | – | jupyter / nbformat transitive |
| 110 | jsonschema-specifications | 2023.12.1 | T | – | jsonschema transitive |
| 111 | jupyter-events