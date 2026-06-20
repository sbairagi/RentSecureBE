# RentSecureBE – Phase 4A Dependency Changes Report

**Status:** ANALYSIS + BASELINE CHECKS COMPLETE – **NO COMMITS MADE**
**Date:** 2026-05-06
**Auditor:** Principal Staff Engineer
**Branch:** `447de77eed173750d4c2036c4ba4b248950d4ae8` (current, no new branch created)

---

## 1. Pre-Change Baseline

| Check | Result | Notes |
|---|---|---|
| `python manage.py check` | ✅ **PASS** | "System check identified no issues (0 silenced)" |
| `pytest --collect-only` | ✅ **PASS** | 384 tests collected, 0 import errors |
| `pytest` (full) | ⚠ Coverage 53.35% < 90% | PRE-EXISTING; unrelated to dependency audit |
| `pip check` | ⚠ 2 pre-existing conflicts | `djangorestframework-stubs` wants `django-stubs>=6.0.4` (have 5.0.4); `djangorestframework-simplejwt 5.5.0` wants `pyjwt<2.10.0` (have 2.13.0). NOT caused by audit. |
| `openai` installed in venv | ❌ **MISSING** | Used in code but not installed |
| `Pillow` installed in venv | ✅ 11.2.1 (transitive) | Used by `ImageField` |
| `PyPDF2` installed in venv | ✅ 3.0.0 (transitive) | Used by `documents/utils.py` |
| `psycopg2-binary` installed in venv | ❌ Not currently in venv | Installed by CI separately |

**Baseline verdict:** Project is in a **partially broken state**:
- `openai` is used in 2 files but **NOT installed** and **NOT in `requirements.txt`** → smartbot is broken at runtime
- `Pillow` and `PyPDF2` are installed as transitives (work today, but no explicit guarantee)
- `psycopg2-binary` is installed by CI only → production will fail

---

## 2. Fresh Re-Validation of Each REMOVE Candidate (with evidence)

| Package | Direct imports | Dynamic imports | Settings / INSTALLED_APPS / Middleware | Signals / Mgmt Cmd / Celery | Templates | Verdict |
|---|---|---|---|---|---|---|
| `flask` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `fpdf` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `fpdf2` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `selenium` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `sqlalchemy` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `pandas` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `pymysql` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `instagram-private-api` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE (security win) |
| `instaloader` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `django-crum` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `django-multiselectfield` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `django-otp` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `django-rest-auth` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE (deprecated 2019) |
| `django-s3-storage` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `django-select2` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `django-widget-tweaks` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `drf-writable-nested` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE (unused today; can re-add when needed) |
| `google-api-python-client` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `google-cloud-core` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `arrow` | 0 | 0 | 0 | 0 | 0 | ✅ SAFE TO REMOVE |
| `whitenoise` | 0 | 0 | not in MIDDLEWARE | 0 | 0 | ⚠ KEEP FOR ROADMAP |
| `django-storages` | 0 | 0 | not in INSTALLED_APPS | 0 | 0 | ⚠ KEEP FOR ROADMAP |
| `dj-database-url` | 0 | 0 | 0 | 0 | 0 | ⚠ KEEP FOR ROADMAP |
| `django-cors-headers` | 0 | 0 | not in MIDDLEWARE | 0 | 0 | ⚠ KEEP FOR ROADMAP |
| `celery` | 0 | 0 | not in INSTALLED_APPS (django_celery_beat is) | 0 | 0 | ⚠ KEEP FOR ROADMAP (infrastructure) |
| `django-celery-beat` | 1 (`properties/scheduler.py`) | 0 | in INSTALLED_APPS | 0 (no `@shared_task`) | 0 | ⚠ KEEP FOR ROADMAP |
| `boto3` | 1 (`whatsapp_service.py: import boto3`) | 0 | uses `settings.AWS_S3_BUCKET_NAME` | 0 | 0 | ⚠ KEEP (active S3) + UPGRADE |
| `Pillow` (PIL) | 0 (via Django ImageField) | 0 | 0 | 0 | 0 | ⚠ ADD as explicit (ImageField backend) |
| `PyPDF2` | 1 (`documents/utils.py: from PyPDF2 import PdfMerger`) | 0 | 0 | 0 | 0 | ⚠ ADD as explicit |
| `openai` | 2 (`smartbot/services/chatbot_service.py`, `gpt_services.py`) | 0 | 0 | 0 | 0 | ⚠ ADD as explicit + CRITICAL version note |
| `razorpay` | 2 (`core/views.py`, `rentsecure_be/services/razorpay_service.py`) | 0 | uses `settings.RAZORPAY_*` | 0 | 0 | ⚠ KEEP + UPGRADE |
| `psycopg2-binary` | 0 (no import, but DB driver) | 0 | `settings.DATABASES` supports PG | 0 | 0 | ⚠ ADD as explicit |

---

## 3. CRITICAL Discovery: `openai` Version Compatibility

The smartbot code uses the **OLD openai v0.x API**:

```python
# smartbot/services/chatbot_service.py
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[...],
)
```

```python
# smartbot/services/gpt_services.py
openai.api_key = settings.OPENAI_API_KEY
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[...],
)
```

**Both APIs were REMOVED in `openai>=1.0.0`** (released Nov 2023). The current openai 1.x SDK requires:
- `from openai import OpenAI; client = OpenAI(api_key=...); client.chat.completions.create(...)`

**Implication:**
- Pinning `openai>=1.0.0` (as proposed in Phase 4) would **break smartbot at runtime**
- Pinning `openai<1.0` (legacy v0.28.x) keeps code working but is end-of-life
- Migration to the new API requires application code changes (out of scope per user's instruction "Do NOT modify application code")

**Safe choice given the constraint:** Pin `openai<1.0` (e.g., `openai==0.28.1`) until code migration is approved as a separate task.

---

## 4. `boto3` Upgrade Target

| Field | Current | Recommended |
|---|---|---|
| Version | 1.18.53 (Aug 2021) | **1.35.28** (latest stable, Dec 2024) |
| Python compat | 3.8+ | 3.8+ |
| API used | `boto3.client("s3").upload_file()` | Same (no breaking change) |
| Risk | **MEDIUM** – 3+ years stale; many CVEs in transitively pulled urllib3 1.26.x | Low – same API surface |

**Safe to upgrade:** the only `boto3` usage is `boto3.client("s3")` + `s3.upload_file()` which is stable across versions.

---

## 5. `razorpay` Upgrade Target

| Field | Current | Recommended |
|---|---|---|
| Version | 1.4.2 (Aug 2021) | **1.4.3.1** (latest 1.4.x, Jul 2024) |
| Python compat | 3.x | 3.x |
| API used | `razorpay.Client(auth=(...))` + `client.order.create()` | Same (no breaking change) |
| Risk | **MEDIUM** – 4-year-old SDK | Low |

**Safe to upgrade** within the 1.4.x line. Avoid jumping to 1.5+ (breaking changes).

---

## 6. Proposed Changes (Detailed)

### 6.1 ADD (4 critical missing production deps)

| # | Package | Pin | Why | File evidence |
|---|---|---|---|---|
| 1 | `openai` | **`==0.28.1`** (NOT 1.0+) | Used in code; v0.x API only | `smartbot/services/chatbot_service.py: import openai`; `smartbot/services/gpt_services.py: import openai` |
| 2 | `Pillow` | `==11.2.1` | `ImageField` backend | 3 models: `caretaker_models.py`, `renter_models.py`, `unit_models.py` |
| 3 | `PyPDF2` | `==3.0.1` | PDF merging | `documents/utils.py: from PyPDF2 import PdfMerger` |
| 4 | `psycopg2-binary` | `==2.9.10` | PostgreSQL production driver | `settings.DATABASES` config (no actual import; driver is required at runtime) |

### 6.2 UPGRADE (2)

| # | Package | From | To | Reason |
|---|---|---|---|---|
| 1 | `boto3` | 1.18.53 | **1.35.28** (latest 1.35.x stable) | 3+ years stale; security; transitively upgrades urllib3 |
| 2 | `razorpay` | 1.4.2 | **1.4.3.1** (latest 1.4.x) | 4+ years stale |

### 6.3 REMOVE (19)

| # | Package | Version (from current lockfile) | Reason |
|---|---|---|---|
| 1 | `Flask` | 3.1.1 | 0 imports |
| 2 | `fpdf` | 1.7.2 | 0 imports (weasyprint is engine) |
| 3 | `fpdf2` | 2.8.3 | 0 imports (weasyprint is engine) |
| 4 | `selenium` | 4.29.0 | 0 imports |
| 5 | `SQLAlchemy` | 2.0.41 | 0 imports (Django ORM) |
| 6 | `pandas` | 2.2.2 | 0 imports |
| 7 | `PyMySQL` | 1.0.2 | 0 imports |
| 8 | `instagram-private-api` | 1.6.0.0 | 0 imports + SECURITY RISK |
| 9 | `instaloader` | 4.14.1 | 0 imports |
| 10 | `django-crum` | 0.7.9 | 0 imports |
| 11 | `django-multiselectfield` | 0.1.12 | 0 imports |
| 12 | `django-otp` | 1.6.0 | 0 imports |
| 13 | `django-rest-auth` | 0.9.5 | 0 imports + DEPRECATED 2019 |
| 14 | `django-s3-storage` | 0.13.4 | 0 imports |
| 15 | `django-select2` | 8.2.3 | 0 imports |
| 16 | `django-widget-tweaks` | 1.4.8 | 0 imports |
| 17 | `google-api-python-client` | 2.170.0 | 0 imports |
| 18 | `google-cloud-core` | 2.4.3 | 0 imports |
| 19 | `arrow` | 1.3.0 | 0 imports |

### 6.4 KEEP (6, for roadmap)

| # | Package | Reason |
|---|---|---|
| 1 | `celery` | Roadmap: Background Jobs, Workers, Beat |
| 2 | `django-celery-beat` | Already in INSTALLED_APPS; `properties/scheduler.py` uses it |
| 3 | `django-cors-headers` | Roadmap: React Native + Angular admin |
| 4 | `whitenoise` | Roadmap: AWS static serving |
| 5 | `django-storages` | Roadmap: S3 media |
| 6 | `dj-database-url` | Roadmap: 12-factor config |

### 6.5 KEEP (already in lockfile, no change)

Django 4.2.30, asgiref 3.8.1, djangorestframework 3.16.0, djangorestframework_simplejwt 5.5.0, django-simple-history 3.8.0, python-decouple 3.5, python-dateutil 2.9.0.post0, requests 2.32.3, weasyprint 66.0, openpyxl 3.1.5, xlsxwriter 3.2.9, twilio 9.6.1, gTTS 2.5.4, fcm-django 2.2.1, firebase-admin 6.8.0, deep-translator 1.11.4.

---

## 7. Order of Operations (Safest Migration Sequence)

| Order | Action | Why this order |
|---|---|---|
| 1 | **ADD** missing deps first (`openai`, `Pillow`, `PyPDF2`, `psycopg2-binary`) | Restore runtime; no code removal yet |
| 2 | **UPGRADE** `boto3` and `razorpay` (pin to safe latest) | Improves security; same API surface |
| 3 | **REMOVE** the 19 unused packages in **one batch** | Single rollback point |
| 4 | **VERIFY** `python manage.py check` + `pytest` after each batch | Catch regressions early |
| 5 | **DO NOT** wire up Celery/CORS/WhiteNoise in this PR | Out of scope; needs separate architect decision + code change |

---

## 8. Pre-Commit Validation Status

| Check | Status |
|---|---|
| `python manage.py check` | ✅ Pass (no issues) |
| `pytest --collect-only` (384 tests) | ✅ Pass (all tests importable) |
| `pip check` | ⚠ 2 PRE-EXISTING conflicts (unrelated to audit) |
| `git status` | ⚠ Audit documents created in working tree (untracked); no `requirements.txt` modified yet |
| `git diff requirements.txt` | empty (no changes made) |

---

## 9. Final Recommendation

**APPROVE Phase 4A** with the following modifications to the original proposal:

1. **Pin `openai==0.28.1`** (NOT `>=1.0.0`) — code uses legacy v0.x API
2. **Pin `boto3==1.35.28`** and `razorpay==1.4.3.1` — keep within 1.x / 1.4.x lines
3. **Add 4 critical deps** + **Upgrade 2** + **Remove 19** in one atomic commit (or 2 commits: adds+upgrades first, then removes)
4. **DO NOT** modify `celery`, `django-cors-headers`, `whitenoise`, `django-storages`, `dj-database-url` in this PR (keep for later; needs architect decision + code change)

**No changes applied yet. Awaiting user approval to proceed with PR creation.**
