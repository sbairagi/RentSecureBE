# RentSecureBE – Dependency Diff (Phase 4A)

**Status:** PROPOSED DIFF – No changes applied
**Date:** 2026-05-06
**Scope:** `requirements.txt` (current 217 lines → proposed 28 lines)
**Reduction:** **87%** of top-level packages

---

## Summary Diff

| Action | Count | Net effect |
|---|---|---|
| ADD (4) | 4 | `openai==0.28.1`, `Pillow==11.2.1`, `PyPDF2==3.0.1`, `psycopg2-binary==2.9.10` |
| UPGRADE (2) | 2 | `boto3 1.18.53 → 1.35.28`, `razorpay 1.4.2 → 1.4.3.1` |
| REMOVE (19) | 19 | Flask, fpdf, fpdf2, selenium, SQLAlchemy, pandas, PyMySQL, instagram-private-api, instaloader, django-crum, django-multiselectfield, django-otp, django-rest-auth, django-s3-storage, django-select2, django-widget-tweaks, drf-writable-nested, google-api-python-client, google-cloud-core, arrow |
| KEEP (unchanged) | 22 | All currently-needed production packages |

---

## Full Proposed `requirements.txt` (28 production lines)

```diff
--- a/requirements.txt (current: 217 lines)
+++ b/requirements.txt (proposed: 28 production lines)
@@
-# OLD (217 lines, mixed production + transitive + dev + unused)
-
-# Top-level packages currently in requirements.txt:
-# (REMOVED: 19 packages)
-Flask==3.1.1
-fpdf==1.7.2
-fpdf2==2.8.3
-selenium==4.29.0
-SQLAlchemy==2.0.41
-pandas==2.2.2
-PyMySQL==1.0.2
-instagram-private-api==1.6.0.0
-instaloader==4.14.1
-django-crum==0.7.9
-django-multiselectfield==0.1.12
-django-otp==1.6.0
-django-rest-auth==0.9.5
-django-s3-storage==0.13.4
-django-select2==8.2.3
-django-widget-tweaks==1.4.8
-drf-writable-nested==0.7.0
-google-api-python-client==2.170.0
-google-cloud-core==2.4.3
-arrow==1.3.0
-
-# Transitive packages (NOT to be pinned at top level; removed from lockfile)
-... (158 transitive packages removed)
-
-# KEEP (production, currently used)
 Django==4.2.30
 asgiref==3.8.1
 djangorestframework==3.16.0
 djangorestframework_simplejwt==5.5.0
 django-simple-history==3.8.0
 python-decouple==3.5
 python-dateutil==2.9.0.post0
 requests==2.32.3
 weasyprint==66.0
 openpyxl==3.1.5
 xlsxwriter==3.2.9
 twilio==9.6.1
 gTTS==2.5.4
 firebase-admin==6.8.0
 fcm-django==2.2.1
 deep-translator==1.11.4
-celery==5.6.3               (note: was already KEEP; in lockfile)
-django-celery-beat==2.9.0   (note: was already KEEP; in lockfile)
-
-# UPGRADE
-boto3==1.18.53              → boto3==1.35.28
-razorpay==1.4.2             → razorpay==1.4.3.1
-
-# ADD (4 critical missing production deps)
+openai==0.28.1              (NEW; code uses v0.x API)
+Pillow==11.2.1              (NEW; was transitive)
+PyPDF2==3.0.1               (NEW; was transitive)
+psycopg2-binary==2.9.10     (NEW; was CI-only)
-
-# KEEP FOR ROADMAP (NOT modified in this PR)
-# django-cors-headers, whitenoise, django-storages, dj-database-url
-# (will be wired up in a separate architect-approved PR)
```

---

## Per-Change Justification

### ADD `openai==0.28.1`

| Field | Detail |
|---|---|
| Current | **MISSING** from `requirements.txt` AND from venv |
| Evidence | `smartbot/services/chatbot_service.py: import openai`; `smartbot/services/gpt_services.py: import openai` |
| Code API used | `openai.ChatCompletion.create()` (v0.x legacy) and `openai.api_key = ...` (v0.x) |
| Why 0.28.1 NOT 1.0+ | openai 1.0+ REMOVED `ChatCompletion` and module-level `api_key`. Code migration is out of scope ("Do NOT modify application code") |
| Risk if not added | smartbot broken at runtime; project ships broken code |
| Rollback | `git revert` |

### ADD `Pillow==11.2.1`

| Field | Detail |
|---|---|
| Current | **MISSING** from `requirements.txt`; installed transitively (11.2.1 in venv) |
| Evidence | `ImageField` in 3 models: `caretaker_models.py`, `renter_models.py`, `unit_models.py` |
| Why needed | Django raises `ImproperlyConfigured` without Pillow; explicit pin prevents breakage if transitive changes |
| Risk if not added | Future deployments may lack Pillow; ImageField breaks |
| Rollback | `git revert` |

### ADD `PyPDF2==3.0.1`

| Field | Detail |
|---|---|
| Current | **MISSING** from `requirements.txt` top-217; installed transitively (3.0.0 in venv) |
| Evidence | `documents/utils.py: from PyPDF2 import PdfMerger`; `documents/tests.py: @patch("documents.utils.PdfMerger")` |
| Why needed | Pin to known-good version; `pypdf` migration is roadmap (12 months) |
| Risk if not added | Future deployment may lack PyPDF2; PDF merge breaks |
| Rollback | `git revert` |

### ADD `psycopg2-binary==2.9.10`

| Field | Detail |
|---|---|
| Current | **MISSING** from `requirements.txt`; CI installs separately (`.github/workflows/test.yml: pip install coverage psycopg2-binary`) |
| Evidence | `settings.DATABASES` config supports PostgreSQL via `DB_ENGINE` env var |
| Why needed | Production PostgreSQL deployment will fail without driver |
| Risk if not added | Production deploy 500s on first DB connection |
| Rollback | `git revert` |

### UPGRADE `boto3` 1.18.53 → 1.35.28

| Field | Detail |
|---|---|
| Current | 1.18.53 (Aug 2021) |
| Evidence | `notification/services/whatsapp_service.py: import boto3` + `boto3.client("s3")` + `s3.upload_file()` |
| Why upgrade | 3+ years stale; many CVE fixes; pulls urllib3 from 1.26 EOL to 2.x |
| API breaking change | **NONE** (`boto3.client("s3")` API stable) |
| Risk | LOW |
| Rollback | pin to `boto3==1.18.53`; `git revert` |

### UPGRADE `razorpay` 1.4.2 → 1.4.3.1

| Field | Detail |
|---|---|
| Current | 1.4.2 (Aug 2021) |
| Evidence | `core/views.py: import razorpay`; `rentsecure_be/services/razorpay_service.py: import razorpay`; both use `razorpay.Client(auth=(...))` |
| Why upgrade | 4+ years stale; security patches; keep within 1.4.x line (no breaking change) |
| API breaking change | **NONE** within 1.4.x |
| Risk | LOW |
| Rollback | pin to `razorpay==1.4.2`; `git revert` |

### REMOVE 19 packages

| # | Package | Reason for safe removal |
|---|---|---|
| 1 | Flask | 0 imports; framework overlap with Django |
| 2 | fpdf | 0 imports; weasyprint is engine |
| 3 | fpdf2 | 0 imports; weasyprint is engine |
| 4 | selenium | 0 imports; no browser automation |
| 5 | SQLAlchemy | 0 imports; Django ORM only |
| 6 | pandas | 0 imports; openpyxl/xlsxwriter don't need it |
| 7 | PyMySQL | 0 imports; PG/SQLite used |
| 8 | instagram-private-api | 0 imports; UNOFFICIAL + SECURITY RISK |
| 9 | instaloader | 0 imports; aspirational |
| 10 | django-crum | 0 imports; custom utilities exist |
| 11 | django-multiselectfield | 0 imports; no MultiSelectField in models |
| 12 | django-otp | 0 imports; custom OTP model in use |
| 13 | django-rest-auth | 0 imports; DEPRECATED 2019 |
| 14 | django-s3-storage | 0 imports; duplicate of django-storages |
| 15 | django-select2 | 0 imports; not wired |
| 16 | django-widget-tweaks | 0 imports; not in templates |
| 17 | drf-writable-nested | 0 imports; not in serializers |
| 18 | google-api-python-client | 0 imports; firebase-admin provides what's used |
| 19 | google-cloud-core | 0 imports; transitive-only |
| 20 | arrow | 0 imports; python-dateutil is used |

**Rollback:** `git revert` of the removal commit restores all 20 packages (and their versions).

### KEEP (no change)

- 6 KEEP FOR ROADMAP (no changes to `celery`, `django-celery-beat`, `django-cors-headers`, `whitenoise`, `django-storages`, `dj-database-url`)
- 22 KEEP NOW (no version change)

---

## Total Lockfile Change

| | Before | After |
|---|---|---|
| Total pinned top-level lines | 217 | **28** |
| Reduction | – | **-189 lines (-87%)** |
| Production-only packages | mixed | **28** |
| Roadmap packages | mixed | **6** (KEEP, not in this PR) |
| Dev packages | mixed (in same file) | **separated into `requirements-dev.txt`** |

---

## Files Affected (If Approved)

| File | Change |
|---|---|
| `requirements.txt` | Rewrite: 217 lines → 28 lines |
| `requirements-dev.txt` | NEW: 13 dev/test packages |
| `.github/workflows/test.yml` | Add `pip install -r requirements-dev.txt` |
| `.github/workflows/lint.yml` | Add `pip install -r requirements-dev.txt` |
| `.github/workflows/quality.yml` | Add `pip install -r requirements-dev.txt` |
| `.github/workflows/security.yml` | Add `pip install -r requirements-dev.txt` |
| `Dockerfile` (if any) | Add `requirements-dev.txt` for build; production installs only `requirements.txt` |
| `deploy.yml` | Add `requirements-dev.txt` for build stage; production uses only `requirements.txt` |

---

## Post-Change Validation Plan

After applying changes:

```bash
# 1. Install
pip install -r requirements.txt -r requirements-dev.txt

# 2. Django system check
python manage.py check

# 3. Test collection
python -m pytest --collect-only

# 4. Full test run
python -m pytest

# 5. Dependency consistency
pip check

# 6. Security scan
pip-audit
```

**Rollback if any step fails:** `git revert <commit-hash>`.
