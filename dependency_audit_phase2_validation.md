# RentSecureBE – Phase 2 VALIDATION Audit (Pre-Removal Verification)

**Status:** ANALYSIS ONLY – No changes applied
**Date:** 2026-05-06
**Purpose:** Verify every "Possibly Unused" / "Unused" / "Unknown" package with multi-evidence
proof before any removal is approved.

---

## 1. Methodology – Multi-Evidence Verification

For each candidate package we ran 5–7 independent checks:

1. **Import grep** – `grep -rE "^(import|from) <pkg>" *.py` (production source, excluding venv / migrations / `.kilo`)
2. **Indirect reference grep** – substring search for module / class / setting names
3. **`INSTALLED_APPS` check** – verify in `rentsecure_be/settings.py`
4. **`MIDDLEWARE` check** – verify in `rentsecure_be/settings.py`
5. **Template grep** – `*.html` for `{% load %}` directives
6. **Management command grep** – dynamic-import patterns in `management/commands/`
7. **Celery task grep** – `@shared_task`, `@periodic_task`, `Celery()` instantiations
8. **Live venv check** – `pip show <pkg>` to confirm whether the package is actually present in `.venv`

Excluded from search: `.venv`, `venv`, `node_modules`, `.kilo/worktrees/*`, `.git`, `migrations/`.

---

## 2. Per-Package Deep Validation

### 2.1 celery

| Check | Result |
|---|---|
| Import grep `^(import\|from) celery` | **0 matches** |
| `find -name celery.py` | **0 files** (only `venv/.../site-packages/celery/bin/celery.py` – 3rd party) |
| `@shared_task` decorator | **0** in our code |
| `@app.task` decorator | **0** in our code |
| `Celery()` instantiation | **0** in our code |
| `INSTALLED_APPS` | `django_celery_beat` is in INSTALLED_APPS, but **celery itself is not registered anywhere** |
| Docstring references | `properties/scheduler.py` and `smartbot/tasks.py` reference Celery in comments only |
| Live venv check (`pip show celery`) | Celery 5.x **is installed** (likely via `django-celery-beat`) |

**Verdict:** **Possibly Used (read-only infrastructure) → Confirmed Architecturally Unused.**

- The project *imports* `from django_celery_beat.models import PeriodicTask` to read / write `PeriodicTask` rows
- The project does **NOT** run a Celery worker, beat scheduler, or define any tasks
- Management commands (`auto_deactivate_renters.py`, `daily_rent_reminder.py`, `apply_late_fees.py`, `generate_monthly_rent_records.py`, `check_vacant_units.py`, etc.) appear to be **run via cron** (Linux crontab / system scheduler), not Celery beat

**Risk if removed:** Removal of `celery` + `django-celery-beat` will:
- Break the `PeriodicTask` admin (currently accessible)
- Break `properties/scheduler.py: cancel_reminder_job()` (uses `django_celery_beat.models.PeriodicTask`)

**Decision required:** Either (a) wire up actual Celery worker + beat + convert management commands to `@shared_task`; or (b) confirm cron-only operation and remove celery stack.

**Category:** **Possibly Used** (architecturally wired; needs explicit owner decision).

---

### 2.2 django-celery-beat

| Check | Result |
|---|---|
| `INSTALLED_APPS` | **YES** – `rentsecure_be/settings.py: "django_celery_beat"` |
| `from django_celery_beat.models import PeriodicTask` | **1** – `properties/scheduler.py` |
| Used in migrations / admin | Inferred (admin registers `PeriodicTask` model) |
| Management commands rely on Celery beat? | **No** – they are plain `BaseCommand` subclasses that are meant to be cron-scheduled |

**Verdict:** **Used** (imported + in INSTALLED_APPS). However, **functionally inactive** (no worker / beat / tasks).

**Category:** **Required if Celery is kept; removable if Celery is removed.**

---

### 2.3 django-storages

| Check | Result |
|---|---|
| `^(import\|from) storages` | **0 matches** |
| `from django.db.models.fields.files` (where storages is sometimes referenced) | 0 storage-related |
| `DEFAULT_FILE_STORAGE` setting | **NOT SET** in `settings.py` |
| `STATICFILES_STORAGE` setting | **NOT SET** |
| `MEDIA_ROOT` | `BASE_DIR / "media"` (local FS) |
| `MEDIA_URL` | `/media/` |
| `INSTALLED_APPS` | **NOT** in INSTALLED_APPS |
| S3 usage in code | `boto3` is used directly in `notification/services/whatsapp_service.py` (lazy import). No use of `storages.backends.s3boto3` |

**Verdict:** **Confirmed Unused.**

**Risk if removed:** None. S3 logic (if any in whatsapp_service) goes through `boto3.client('s3')` directly.

**Category:** **Confirmed Unused.**

---

### 2.4 whitenoise

| Check | Result |
|---|---|
| `MIDDLEWARE` | `whitenoise.middleware.WhiteNoiseMiddleware` **NOT** in `MIDDLEWARE` |
| `INSTALLED_APPS` | **NOT** in INSTALLED_APPS |
| `^(import\|from) whitenoise` | **0 matches** |
| `STATICFILES_STORAGE` | **NOT SET** |
| `STATIC_ROOT` | **NOT SET** |
| `urls.py` | Uses `from django.conf.urls.static import static` for development only |

**Verdict:** **Confirmed Unused.** Static files served via Django's `staticfiles` app + development server only.

**Risk if removed:** None in development. In production, static files would need to be served by nginx / ALB / CDN. (This is the correct pattern anyway.)

**Category:** **Confirmed Unused.**

---

### 2.5 pandas

| Check | Result |
|---|---|
| `^(import\|from) pandas` | **0 matches** |
| `pd.DataFrame`, `pd.read_*` | **0 matches** |
| Transitive use | `openpyxl` does NOT require pandas; `xlsxwriter` does NOT require pandas |

**Verdict:** **Confirmed Unused.**

**Risk if removed:** None. May marginally speed up Docker build (saves ~50MB).

**Category:** **Confirmed Unused.**

---

### 2.6 Flask

| Check | Result |
|---|---|
| `^(import\|from) flask` | **0 matches** |
| `Flask(` constructor | **0 matches** |
| `@app.route` | **0 matches** |
| `werkzeug` | 0 matches in our code (in `requirements.txt` as transitive of Flask) |
| `jinja2` (shared between Django/Flask) | 0 matches in our code |

**Verdict:** **Confirmed Unused.** Likely artifact of someone's `pip freeze` from a different project.

**Risk if removed:** None. Cleanup will also remove `Werkzeug`, `itsdangerous`, `blinker`, `Jinja2`, `MarkupSafe` from the *top-level* file (they are Flask transitives; they will be removed from the lockfile entirely).

**Category:** **Confirmed Unused.**

---

### 2.7 SQLAlchemy

| Check | Result |
|---|---|
| `^(import\|from) sqlalchemy` | **0 matches** |
| `create_engine`, `Session(`, `declarative_base` | **0 matches** |
| Any `models.py` using SQLAlchemy? | All 7 apps use Django ORM |

**Verdict:** **Confirmed Unused.** Project uses Django ORM exclusively.

**Risk if removed:** None.

**Category:** **Confirmed Unused.**

---

### 2.8 selenium

| Check | Result |
|---|---|
| `^(import\|from) selenium` | **0 matches** |
| `webdriver.`, `WebDriver`, `Chrome(`, `Firefox(` | **0 matches** |

**Verdict:** **Confirmed Unused.**

**Risk if removed:** None.

**Category:** **Confirmed Unused.**

---

### 2.9 PyMySQL

| Check | Result |
|---|---|
| `^(import\|from) pymysql` | **0 matches** |
| `MySQLdb` | **0 matches** |
| `DATABASES` config | `ENGINE: "django.db.backends.sqlite3"` (default) or via env (likely PostgreSQL in prod – `psycopg2-binary` is the proper driver) |

**Verdict:** **Confirmed Unused.** Project runs on SQLite (dev) or PostgreSQL (prod). PyMySQL is for MySQL.

**Risk if removed:** None.

**Category:** **Confirmed Unused.**

---

### 2.10 PyPDF2

| Check | Result |
|---|---|
| `^(import\|from) PyPDF2` | **1 match** |
| File evidence | `./documents/utils.py: from PyPDF2 import PdfMerger` |
| Usage in tests | `./documents/tests.py: @patch("documents.utils.PdfMerger")` |
| Live venv | `pip show pypdf2 → Version: 3.0.0` (installed) |

**Verdict:** **CONFIRMED PRODUCTION CRITICAL.** Used in production code (PDF merge).

**Note:** PyPDF2 is in `requirements.txt` (originally row 20) but **NOT in the top-217 list** (it's installed as 3.0.0, the lockfile shows an older version). Re-add as explicit top-level pin.

**Category:** **Required Production.**

---

### 2.11 Pillow

| Check | Result |
|---|---|
| `^(import\|from) PIL` | **0 matches** in our code (PIL is a Python package, we use it via `ImageField`) |
| `ImageField` in models | **3 models** in `properties/models/`: `caretaker_image`, `renter_image`, `image` |
| Template usage | `image="test.jpg"`, `image="img1.png"` in tests |
| Live venv | `pip show pillow → Version: 11.2.1` (installed transitively via weasyprint) |

**Verdict:** **REQUIRED RUNTIME PRODUCTION.** Django's `ImageField` requires Pillow to be installed (raises `ImproperlyConfigured` otherwise). Even though no code does `from PIL import …`, the ORM uses Pillow internally.

**Action:** **ADD as explicit top-level** in production `requirements.txt`. Currently it's a hidden transitive.

**Category:** **Required Production (explicit pin required).**

---

### 2.12 dj-database-url

| Check | Result |
|---|---|
| `^(import\|from) dj_database_url` | **0 matches** |
| `import_url`, `dj-database-url` (any form) | **0 matches** |
| `DATABASES` setting | Built manually with `decouple.config("DB_ENGINE", default="django.db.backends.sqlite3")` etc. |
| `DATABASE_URL` env var | Not referenced |

**Verdict:** **Confirmed Unused.** Settings uses `decouple` directly.

**Risk if removed:** None. Slight loss of convenience (could refactor to use `dj-database-url` if multi-DB env-var support is needed, but currently not used).

**Category:** **Confirmed Unused.**

---

## 3. Other "Possibly Unused" Packages – Validation

| Package | `^(import\|from)` | `INSTALLED_APPS` | `MIDDLEWARE` | Template `{% load %}` | Indirect grep | Verdict |
|---|---|---|---|---|---|---|
| `django-crum` | 0 | 0 | 0 | n/a | `crum.`, `get_current_request` – 0 | **CONFIRMED UNUSED** |
| `django-multiselectfield` | 0 | 0 | 0 | n/a | `MultiSelectField` – 0 | **CONFIRMED UNUSED** |
| `django-otp` | 0 | 0 | 0 | n/a | `from otp_`, `OTPMiddleware` – 0 | **CONFIRMED UNUSED** (custom `OTP` model in `core.models`) |
| `django-rest-auth` | 0 | 0 | 0 | n/a | `rest_auth`, `restauth` – 0 | **CONFIRMED UNUSED + DEPRECATED 2019** |
| `django-s3-storage` | 0 | 0 | 0 | n/a | `S3Storage` – 0 | **CONFIRMED UNUSED** (overlaps `django-storages`) |
| `django-select2` | 0 | 0 | 0 | 0 | `Select2Widget` – 0 | **CONFIRMED UNUSED** |
| `django-widget-tweaks` | 0 | 0 | 0 | 0 | `render_field` – 0 | **CONFIRMED UNUSED** |
| `drf-writable-nested` | 0 | 0 | 0 | n/a | `WritableNestedSerializer` – 0 | **CONFIRMED UNUSED** |
| `django-cors-headers` | 0 | 0 | 0 | 0 | `corsheaders`, `CorsMiddleware` – 0 | **CONFIRMED UNUSED** (or not wired) |
| `google-api-python-client` | 0 | 0 | 0 | n/a | `googleapiclient` – 0 | **CONFIRMED UNUSED** |
| `google-cloud-core` | 0 | 0 | 0 | n/a | `google.cloud` – 0 | **CONFIRMED UNUSED** |
| `google-cloud-firestore` | 0 | 0 | 0 | n/a | `google.cloud.firestore` – 0 | **CONFIRMED UNUSED** |
| `google-cloud-storage` | 0 | 0 | 0 | n/a | `google.cloud.storage` – 0 | **CONFIRMED UNUSED** |
| `instagram-private-api` | 0 | 0 | 0 | n/a | `instagram_private_api` – 0 | **CONFIRMED UNUSED + RISKY** (unofficial reverse-engineered) |
| `instaloader` | 0 | 0 | 0 | n/a | `instaloader` – 0 | **CONFIRMED UNUSED** |
| `fpdf` | 0 | 0 | 0 | n/a | `from fpdf` – 0 | **CONFIRMED UNUSED** |
| `fpdf2` | 0 | 0 | 0 | n/a | `from fpdf2` – 0 | **CONFIRMED UNUSED** |
| `boto3` | 0 (top-level) | 0 | 0 | n/a | **1 lazy import** in `notification/services/whatsapp_service.py: import boto3` | **REQUIRED PRODUCTION** (lazy, but used) |
| `botocore` (transitive) | 0 | 0 | 0 | n/a | transitive of boto3 | **TRANSITIVE – keep boto3** |

---

## 4. Final Categorization (Per Audit Step 4)

### A. Confirmed Unused (Safe to remove – Phase 2B)

| # | Package | Confidence | Why safe to remove |
|---|---|---|---|
| 1 | `Flask==3.1.1` | 99% | 0 imports; will also drop Werkzeug, itsdangerous, blinker, Jinja2, MarkupSafe |
| 2 | `fpdf==1.7.2` | 99% | 0 imports (project uses weasyprint) |
| 3 | `fpdf2==2.8.3` | 99% | 0 imports |
| 4 | `selenium==4.29.0` | 99% | 0 imports |
| 5 | `SQLAlchemy==2.0.41` | 99% | Django ORM only |
| 6 | `pandas==2.2.2` | 99% | openpyxl/xlsxwriter do not need it |
| 7 | `PyMySQL==1.0.2` | 99% | Project uses PostgreSQL/SQLite |
| 8 | `instagram-private-api==1.6.0.0` | 99% | **UNOFFICIAL + RISKY** |
| 9 | `instaloader==4.14.1` | 99% | 0 imports |
| 10 | `django-crum==0.7.9` | 99% | 0 imports |
| 11 | `django-multiselectfield==0.1.12` | 99% | 0 imports |
| 12 | `django-otp==1.6.0` | 99% | 0 imports; custom OTP model in use |
| 13 | `django-rest-auth==0.9.5` | 99% | **DEPRECATED 2019** |
| 14 | `django-s3-storage==0.13.4` | 99% | 0 imports; overlaps django-storages |
| 15 | `django-select2==8.2.3` | 99% | 0 imports; not wired |
| 16 | `django-widget-tweaks==1.4.8` | 99% | 0 imports; not in templates |
| 17 | `drf-writable-nested==0
