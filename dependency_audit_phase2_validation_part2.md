# RentSecureBE – Phase 2 VALIDATION Audit – Part 2

This document completes `dependency_audit_phase2_validation.md` with:
- Final categorization (A: Confirmed Unused, B: Possibly Used, C: Required Production, D: Required Development)
- Removal Risk Matrix (Risk / Files / Impact / Rollback)
- New findings
- Final Required Production list
- Owner-decision checklist

---

## 4. Final Categorization (Per Audit Step 4)

### A. Confirmed Unused (Safe to remove – Phase 2B)

| # | Package | Confidence | Why safe to remove |
|---|---|---|---|
| 1 | `Flask==3.1.1` | 99% | 0 imports; will cascade-remove Werkzeug, itsdangerous, blinker, Jinja2, MarkupSafe |
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
| 17 | `drf-writable-nested==0.7.0` | 99% | 0 imports |
| 18 | `django-cors-headers==3.9.0` | 99% | Not in INSTALLED_APPS, not in MIDDLEWARE |
| 19 | `google-api-python-client==2.170.0` | 99% | 0 imports; firebase-admin provides what's needed |
| 20 | `google-cloud-core==2.4.3` | 99% | 0 imports |
| 21 | `google-cloud-firestore==2.20.2` | 99% | 0 imports |
| 22 | `google-cloud-storage==3.1.0` | 99% | 0 imports |
| 23 | `whitenoise==5.3.0` | 99% | Not in MIDDLEWARE |
| 24 | `django-storages==1.11.1` | 99% | Not imported; not in INSTALLED_APPS; local FS only |
| 25 | `dj-database-url==2.3.0` | 99% | 0 imports; decouple used instead |

### B. Possibly Used (Architecturally wired – needs owner decision)

| # | Package | Confidence | Reason | Decision required |
|---|---|---|---|---|
| 1 | `celery==5.6.3` | 60% | `django_celery_beat` is in INSTALLED_APPS, `PeriodicTask` is read; but no Celery app / worker / tasks exist. | Either wire up Celery worker+beat+convert commands to `@shared_task`, or remove entire celery stack |
| 2 | `django-celery-beat==2.9.0` | 80% | Imported in `properties/scheduler.py`, in INSTALLED_APPS | Remove if celery is removed; keep if celery is wired |

### C. Required Production (Cannot be removed)

| # | Package | Evidence | Why required |
|---|---|---|---|
| 1 | `Django==4.2.30` | Framework | Core framework |
| 2 | `djangorestframework==3.16.0` | 20+ import sites | API framework |
| 3 | `djangorestframework_simplejwt==5.5.0` | `core/urls.py`, `core/views.py`, settings | JWT auth |
| 4 | `django-simple-history==3.8.0` | Many imports of `HistoricalRecords`, in INSTALLED_APPS + MIDDLEWARE | Audit tracking |
| 5 | `asgiref==3.8.1` | Django internal | ASGI |
| 6 | `python-decouple==3.5` | `settings.py: from decouple import Csv, config` | Env config |
| 7 | `python-dateutil==2.9.0.post0` | 2 imports of `dateutil.relativedelta` | Date math |
| 8 | `requests==2.32.3` | 5 import sites | HTTP client |
| 9 | `weasyprint==66.0` | 9 import sites | PDF generation |
| 10 | `twilio==9.6.1` | 4 import sites | WhatsApp/SMS/Voice |
| 11 | `razorpay==1.4.2` | `core/views.py`, `rentsecure_be/services/razorpay_service.py` | Payments (upgrade in Phase 2C) |
| 12 | `boto3==1.18.53` | `notification/services/whatsapp_service.py: import boto3` (lazy) | AWS SDK (upgrade in Phase 2C) |
| 13 | `fcm-django==2.2.1` | 2 import sites; in INSTALLED_APPS | Push notifications |
| 14 | `firebase-admin==6.8.0` | Backend for fcm-django | Required runtime |
| 15 | `openpyxl==3.1.5` | `finance/utils.py: from openpyxl import Workbook` | Excel exports |
| 16 | `xlsxwriter==3.2.9` | `core/utils/export_utils.py: import xlsxwriter` | Excel exports |
| 17 | `gTTS==2.5.4` | 1 import (`from gtts import gTTS`) | Voice notes |
| 18 | `deep-translator==1.11.4` | `ai_assistant/services/i18n_service.py: from deep_translator import GoogleTranslator` | Translation |
| 19 | `PyPDF2==3.0.0` (currently 3.0.0 in venv) | `documents/utils.py: from PyPDF2 import PdfMerger` | PDF merging |
| 20 | `Pillow==11.2.1` | `ImageField` in 3 models (`caretaker_image`, `renter_image`, `unit_image`) | ImageField backend |
| 21 | **`psycopg2-binary`** (NOT in current requirements.txt) | CI installs separately for test DB; production likely needs it | Add to production `requirements.txt` for PostgreSQL |

### D. Required Development (Test/lint only)

| # | Package | Evidence | Why required |
|---|---|---|---|
| 1 | `pytest==8.3.5` | `conftest.py` | Test runner |
| 2 | `pytest-django==4.11.1` | pytest plugin | Django test integration |
| 3 | `coverage` | `.coveragerc` + pyproject | Test coverage |
| 4 | `psycopg2-binary` (for test DB) | `.github/workflows/test.yml: pip install coverage psycopg2-binary` | Test DB driver |
| 5 | `black`, `ruff`, `pylint`, `pylint-django`, `mypy`, `django-stubs`, `djangorestframework-stubs`, `bandit`, `semgrep`, `pip-audit` | CI workflows + pre-commit | Lint / security / type-check (currently installed per-job, not in `requirements.txt`) |

---

## 5. Removal Risk Matrix (Per Audit Step 5)

For every package proposed for removal:

| # | Package | Risk Level | Files Referencing (verified) | Removal Impact | Rollback Strategy |
|---|---|---|---|---|---|
| 1 | `instagram-private-api` | **HIGH (security)** | **0** in our code | None on app; reduces supply-chain attack surface | `git revert`; if downstream system needs it (none found), add back with justification |
| 2 | `django-rest-auth` | **MEDIUM** | 0 imports; settings has **NO** `rest_auth` URL include | May break an old admin or hidden URL pattern. Searched: 0 matches anywhere. | `git revert` + restore any removed URL conf |
| 3 | `Flask` | **LOW** | 0 imports | None. Will cascade-remove Werkzeug, itsdangerous, blinker, Jinja2, MarkupSafe from top-level. | `git revert` |
| 4 | `fpdf` | **LOW** | 0 imports | None. (weasyprint is the PDF engine.) | `git revert` |
| 5 | `fpdf2` | **LOW** | 0 imports | None. (weasyprint is the PDF engine.) | `git revert` |
| 6 | `selenium` | **LOW** | 0 imports | None. (No browser automation in code.) | `git revert` |
| 7 | `SQLAlchemy` | **LOW** | 0 imports | None. (Django ORM only.) | `git revert` |
| 8 | `pandas` | **LOW** | 0 imports | None. (openpyxl/xlsxwriter don't need it.) | `git revert` |
| 9 | `PyMySQL` | **LOW** | 0 imports; engine is sqlite/postgresql | None. | `git revert` |
| 10 | `instaloader` | **LOW** | 0 imports | None. | `git revert` |
| 11 | `django-crum` | **LOW** | 0 imports | None. | `git revert` |
| 12 | `django-multiselectfield` | **LOW** | 0 imports; no `MultiSelectField` in models | None. (If a model needs multi-select, can use a JSONField.) | `git revert` |
| 13 | `django-otp` | **LOW** | 0 imports; custom `OTP` model in use | None. | `git revert` |
| 14 | `django-s3-storage` | **LOW** | 0 imports; not in INSTALLED_APPS | None. (boto3 is used directly.) | `git revert` |
| 15 | `django-select2` | **LOW** | 0 imports; not in INSTALLED_APPS | None. | `git revert` |
| 16 | `django-widget-tweaks` | **LOW** | 0 imports; not in templates | None. | `git revert` |
| 17 | `drf-writable-nested` | **LOW** | 0 imports; not used in serializers | None. | `git revert` |
| 18 | `django-cors-headers` | **LOW** (unused) / **MEDIUM** (if API is consumed cross-origin) | Not wired | If CORS is needed in production, must be re-added and wired. (Currently the API may not be serving cross-origin clients.) | `git revert` + add to `INSTALLED_APPS` and `MIDDLEWARE` |
| 19 | `whitenoise` | **LOW** (unused) | Not in MIDDLEWARE | None in dev. In prod, static files need to be served by nginx/ALB/CDN anyway. | `git revert` |
| 20 | `django-storages` | **LOW** (unused) | Not imported; not in INSTALLED_APPS | None. (S3 calls go through boto3 directly.) | `git revert` |
| 21 | `dj-database-url` | **LOW** | 0 imports; decouple used | None. | `git revert` |
| 22 | `google-api-python-client` | **LOW** | 0 imports | None. (firebase-admin provides what's used.) | `git revert` |
| 23 | `google-cloud-core` | **LOW** | 0 imports | None. | `git revert` |
| 24 | `google-cloud-firestore` | **LOW** | 0 imports | None. | `git revert` |
| 25 | `google-cloud-storage` | **LOW** | 0 imports | None. (boto3 used for S3 if any.) | `git revert` |
| 26 | `celery` + `django-celery-beat` | **MEDIUM (architectural)** | `django_celery_beat` in INSTALLED_APPS; `PeriodicTask` imported in `properties/scheduler.py` | Removing breaks `cancel_reminder_job()` and PeriodicTask admin | (a) wire up Celery; (b) `git revert` + accept current cron-only flow |

---

## 6. NEW FINDINGS (from this validation pass)

1. **`Pillow` MUST be added** to production `requirements.txt` (currently a hidden transitive of weasyprint, but `ImageField` in 3 models needs it). **Add to Required Production (C).**
2. **`PyPDF2` MUST be re-added** to production `requirements.txt` (used in `documents/utils.py`). Already known from Part 1 inventory but reaffirmed.
3. **`psycopg2-binary` is NOT in `requirements.txt`** but CI installs it (`pip install coverage psycopg2-binary`). Production PostgreSQL deployments will need it. **Add to Required Production (C).**
4. **`Arrow==1.3.0` is in requirements.txt** but has 0 imports. Verified to be a celery-scheduler transitive. Safe to remove from top-level (transitive of celery).
5. **Management commands are NOT Celery tasks.** They are plain Django management commands meant to be run via crontab. This confirms that the celery stack is currently **inert**.

---

## 7. Updated Required Production (Final List)

> **Total: 22 production packages** (was 16 in Part 1; added 6 from this validation)

```text
Django==4.2.30
asgiref==3.8.1
djangorestframework==3.16.0
djangorestframework_simplejwt==5.5.0
django-simple-history==3.8.0
django-celery-beat==2.9.0         # only if celery is kept
celery==5.6.3                     # only if celery is kept (currently architecturally inert)
python-decouple==3.5
python-dateutil==2.9.0.post0
requests==2.32.3
weasyprint==66.0
PyPDF2==3.0.1                     # re-add (was missing from top-217)
Pillow==11.2.1                    # MUST be explicit (ImageField)
openpyxl==3.1.5
xlsxwriter==3.2.9
twilio==9.6.1
gTTS==2.5.4
razorpay==1.4.2
boto3==1.18.53
fcm-django==2.2.1
firebase-admin==6.8.0
deep-translator==1.11.4
psycopg2-binary                   # add for production PostgreSQL
```

---

## 8. Out of Scope (Recap)

- ❌ No `requirements.txt` modified
- ❌ No workflows modified
- ❌ No application code modified
- ❌ No git commits created
- ❌ No packages removed

**Validation report only. Awaiting approval.**

---

## 9. Next Step (Awaiting Owner Decision)

Before any package is removed, the team must decide:

1. **Celery**: Wire up actual Celery worker + beat + tasks, OR remove the celery stack entirely?
2. **CORS**: Is the API consumed cross-origin? (If yes, `django-cors-headers` must be wired up; if no, remove.)
3. **WhiteNoise**: Add it to `MIDDLEWARE` for production static files, OR rely on external serving?
4. **PostgreSQL driver**: Confirm production uses PostgreSQL and add `psycopg2-binary` to production requirements?

Once these 4 decisions are made, the migration plan in `dependency_audit_phase2_part3.md` / `part4.md` can be applied (Phase 2A → 2B → 2C).
