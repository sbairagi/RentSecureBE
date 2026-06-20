# RentSecureBE – Phase 4 Validation – Part 2

This document completes `dependency_audit_phase4_validation.md` with:
- Version compatibility matrix
- Per-package verdict (full table)
- Hidden/transitive deps that should be explicit
- Final approval recommendation
- Out-of-scope recap

---

## 3. Version Compatibility Matrix

| Component | Current | Recommended | Python Compat | Notes |
|---|---|---|---|---|
| **Python** | 3.13.3 (live); pyproject targets py312 | 3.12 LTS | n/a | `pyproject.toml: target-version = "py312"` |
| **Django** | 4.2.30 | 4.2.x (pin) → 5.0 LTS or 5.2 LTS in 12 months | 3.8–3.13 | LTS support ends April 2026 |
| **djangorestframework** | 3.16.0 | 3.16.x | 3.9+ | Django 4.2 compat ✓ |
| **djangorestframework_simplejwt** | 5.5.0 | 5.5.x | 3.9+ | DRF 3.16 compat ✓ |
| **django-simple-history** | 3.8.0 | 3.8.x | 3.9+ | Django 4.2 compat ✓ |
| **celery** | 5.6.3 | 5.4.x latest (5.6.3 is current) | 3.8+ | Django 4.2 compat ✓ |
| **django-celery-beat** | 2.9.0 | 2.9.x | 3.8+ | Celery 5.x compat ✓ |
| **django-cors-headers** | 3.9.0 | 4.x latest (4.4+) | 3.8+ | Django 4.2 compat ✓ **⚠ consider upgrade 3.9 → 4.x** |
| **whitenoise** | 5.3.0 | 6.x latest | 3.7+ | Django 4.2 compat ✓ |
| **django-storages** | 1.11.1 | 1.14.x latest | 3.8+ | Django 4.2 compat ✓ |
| **psycopg2-binary** | n/a in requirements.txt | 2.9.10 | 3.8+ | PostgreSQL 16+ compat ✓ |
| **dj-database-url** | 2.3.0 | 2.3.x (current) | 3.8+ | ✓ |
| **Pillow** | 11.2.1 (transitive) | 11.2.1 (pin explicitly) | 3.9+ | Django 4.2 + ImageField ✓ |
| **PyPDF2** | (transitive) | 3.0.1 (pin explicitly) | 3.7+ | Note: `pypdf` is the maintained successor; consider migrating in 12 months |
| **boto3** | 1.18.53 | **≥1.35.x (URGENT)** | 3.8+ | Current is 3+ years stale; many CVE fixes |
| **botocore** (transitive) | 1.21.53 | Latest | 3.8+ | Bundled with boto3 |
| **twilio** | 9.6.1 | 9.x latest | 3.8+ | ✓ |
| **fcm-django** | 2.2.1 | 2.2.x | 3.8+ | Django 4.2 compat ✓ |
| **firebase-admin** | 6.8.0 | 6.6.x | 3.8+ | ✓ |
| **razorpay** | 1.4.2 (2021) | **≥1.4.x latest** | 3.8+ | 4+ years stale; API surface may have changed |
| **weasyprint** | 66.0 | 66.x latest | 3.9+ | ✓ |
| **openpyxl** | 3.1.5 | 3.1.x | 3.8+ | ✓ |
| **xlsxwriter** | 3.2.9 | 3.2.x | 3.8+ | ✓ |
| **requests** | 2.32.3 | 2.32.x | 3.8+ | ✓ |
| **gTTS** | 2.5.4 | 2.5.x | 3.8+ | ✓ |
| **deep-translator** | 1.11.4 | 1.11.x | 3.8+ | ✓ |
| **drf-writable-nested** | 0.7.0 | 0.7.x | 3.9+ | DRF 3.16 compat ✓ |
| **python-decouple** | 3.5 | 3.8 (latest) | 3.8+ | ✓ |
| **python-dateutil** | 2.9.0.post0 | 2.9.x | 3.8+ | ✓ |
| **asgiref** | 3.8.1 | 3.8.x (Django-compatible) | 3.8+ | ✓ |

### Critical Findings (Version)

1. **`boto3 1.18.53` is 3+ years stale** – must upgrade to 1.35.x in Phase 2C
2. **`razorpay 1.4.2` is from August 2021** – must upgrade; current is 1.4.x (later 2024 release)
3. **`urllib3 1.26.20` is EOL** – will be pulled up by boto3 upgrade
4. **`Django 4.2 LTS` ends April 2026** – plan 5.0/5.2 upgrade within 12 months
5. **`pytz 2021.3` is outdated** – Django 4+ supports `zoneinfo`; consider removal (currently transitive)
6. **PyPDF2 maintenance** – `pypdf` is the modern successor; plan migration in 12 months

---

## 4. Per-Package Verdict (Full)

### A. KEEP NOW (Production, 24 packages)

| # | Package | Pinned Version | Used At | Roadmap | Verdict |
|---|---|---|---|---|---|
| 1 | Django | 4.2.30 | Framework | All | ✅ KEEP |
| 2 | djangorestframework | 3.16.0 | 20+ import sites | API for mobile + web | ✅ KEEP |
| 3 | djangorestframework_simplejwt | 5.5.0 | `core/urls.py`, `core/views.py`, settings | Mobile + web auth | ✅ KEEP |
| 4 | django-simple-history | 3.8.0 | Many imports, INSTALLED_APPS, MIDDLEWARE | Audit logs | ✅ KEEP |
| 5 | asgiref | 3.8.1 | Django internal | Async roadmap | ✅ KEEP |
| 6 | python-decouple | 3.5 | `settings.py` | All env config | ✅ KEEP |
| 7 | python-dateutil | 2.9.0.post0 | 2 imports | Date math | ✅ KEEP |
| 8 | requests | 2.32.3 | 5 import sites | HTTP integrations | ✅ KEEP |
| 9 | weasyprint | 66.0 | 9 import sites | PDF generation | ✅ KEEP |
| 10 | **PyPDF2** | **3.0.1 (pin explicitly)** | `documents/utils.py: from PyPDF2 import PdfMerger` | PDF Merging | ✅ KEEP + add to requirements.txt |
| 11 | **Pillow** | **11.2.1 (pin explicitly)** | `ImageField` in 3 models | Image uploads | ✅ KEEP + add to requirements.txt |
| 12 | openpyxl | 3.1.5 | `finance/utils.py` | Excel exports | ✅ KEEP |
| 13 | xlsxwriter | 3.2.9 | `core/utils/export_utils.py` | Excel exports | ✅ KEEP |
| 14 | twilio | 9.6.1 | 4 import sites | WhatsApp + SMS + Voice | ✅ KEEP |
| 15 | gTTS | 2.5.4 | 1 import | Voice notes | ✅ KEEP |
| 16 | razorpay | 1.4.2 | 2 import sites | Payment gateway | ✅ KEEP + **UPGRADE to 1.4 latest** |
| 17 | **boto3** | **1.18.53 → 1.35.x** | `notification/services/whatsapp_service.py: boto3.client("s3")` (active S3) | **S3 + AWS deployment (already in production)** | ✅ KEEP + **URGENT UPGRADE** |
| 18 | fcm-django | 2.2.1 | 2 import sites, INSTALLED_APPS | Push notifications | ✅ KEEP |
| 19 | firebase-admin | 6.8.0 | Backend for fcm-django | Push notifications | ✅ KEEP |
| 20 | deep-translator | 1.11.4 | `ai_assistant/services/i18n_service.py` | AI assistant + i18n | ✅ KEEP |
| 21 | **psycopg2-binary** | **2.9.10 (add to requirements.txt)** | CI installs; production needs | PostgreSQL production | ✅ KEEP + add to requirements.txt |
| 22 | **boto3 (in whatsapp_service)** | confirmed | `boto3.client("s3")` upload_file | (active) | ✅ KEEP |
| 23 | **openai** | (NOT in current requirements.txt!) | 2 import sites: `smartbot/services/chatbot_service.py: import openai`, `smartbot/services/gpt_services.py: import openai` | **AI assistant** | ⚠ **MISSING from requirements.txt** – add `openai>=1.0.0` |
| 24 | **pytest** in current `requirements.txt` | 8.3.5 | `conftest.py` | Tests | **MOVE to `requirements-dev.txt`** |

### B. KEEP FOR ROADMAP (6 packages)

| # | Package | Why Keep | Action Required |
|---|---|---|---|
| 1 | `celery` + `django-celery-beat` | Roadmap: Background Jobs, Scheduled Notifications, Workers, Beat, Queue Processing | **MUST wire up:** create `rentsecure_be/celery.py`, add worker + beat to `deploy.yml`, convert commands to `@shared_task` |
| 2 | `django-cors-headers` | Roadmap: React Native + Angular admin (cross-origin) | **MUST wire up:** add to INSTALLED_APPS + MIDDLEWARE |
| 3 | `whitenoise` | Roadmap: Angular admin + AWS static serving | **MUST wire up:** add to MIDDLEWARE, set STATIC_ROOT |
| 4 | `django-storages` | Roadmap: S3 media storage | Configure `DEFAULT_FILE_STORAGE` when S3 is enabled |
| 5 | `dj-database-url` | Roadmap: 12-factor config (ECS/K8s) | Refactor `settings.py` to use it |
| 6 | `drf-writable-nested` | Roadmap: nested serializers (Renter + Agreement) | Document when to use |

### C. REMOVE (19 packages)

| # | Package | Reason for Removal | Rollback |
|---|---|---|---|
| 1 | **Flask** | 0 imports; framework leak | `git revert` |
| 2 | **fpdf** | 0 imports; weasyprint is the engine | `git revert` |
| 3 | **fpdf2** | 0 imports; weasyprint is the engine | `git revert` |
| 4 | **selenium** | 0 imports; no browser automation | `git revert` |
| 5 | **SQLAlchemy** | 0 imports; Django ORM only | `git revert` |
| 6 | **pandas** | 0 imports; openpyxl/xlsxwriter do not need it | `git revert` |
| 7 | **PyMySQL** | 0 imports; project uses PG/SQLite | `git revert` |
| 8 | **instagram-private-api** | 0 imports; **UNOFFICIAL + SECURITY RISK** | `git revert` |
| 9 | **instaloader** | 0 imports; aspirational | `git revert` |
| 10 | **django-crum** | 0 imports; custom utilities exist | `git revert` |
| 11 | **django-multiselectfield** | 0 imports; no MultiSelectField in models | `git revert` |
| 12 | **django-otp** | 0 imports; custom OTP model | `git revert` |
| 13 | **django-rest-auth** | 0 imports; **DEPRECATED 2019** | `git revert` |
| 14 | **django-s3-storage** | 0 imports; duplicate of django-storages | `git revert` |
| 15 | **django-select2** | 0 imports; not wired | `git revert` |
| 16 | **django-widget-tweaks** | 0 imports; not in templates | `git revert` |
| 17 | **google-api-python-client** | 0 imports; firebase-admin provides what's used | `git revert` |
| 18 | **google-cloud-core** | 0 imports; transitive-only | `git revert` |
| 19 | **arrow** | 0 imports; python-dateutil is used | `git revert` |

### D. INFRASTRUCTURE FIX (3 items)

| # | Item | Current State | Required Action |
|---|---|---|---|
| 1 | Celery application | No `celery.py` exists | **Create `rentsecure_be/celery.py`** with `app = Celery(...)` |
| 2 | CORS middleware | Not configured | **Add to MIDDLEWARE** before CommonMiddleware |
| 3 | WhiteNoise | Not in MIDDLEWARE | **Add `whitenoise.middleware.WhiteNoiseMiddleware`** to MIDDLEWARE |

---

## 5. Hidden / Transitive Dependencies That MUST Become Explicit

| Package | Currently In (as top-level) | Currently Used By (transitive) | Risk | Action |
|---|---|---|---|---|
| **Pillow 11.2.1** | NO (hidden transitive of weasyprint) | `ImageField` in `caretaker_models.py`, `renter_models.py`, `unit_models.py` | **HIGH** – Django raises `ImproperlyConfigured` without Pillow | **ADD as explicit top-level** |
| **PyPDF2 3.0.0** | NO (transitive) | `documents/utils.py: from PyPDF2 import PdfMerger` | **HIGH** – PDF merge breaks | **ADD as explicit top-level** (current `PyPDF2==...` pin in lockfile is older) |
| **psycopg2-binary** | NO (CI installs separately) | Production PostgreSQL deployment | **HIGH** – prod DB driver missing | **ADD as explicit top-level** |
| **openai** | **NO** (missing entirely from requirements.txt) | `smartbot/services/chatbot_service.py: import openai`, `smartbot/services/gpt_services.py: import openai` | **CRITICAL** – AI assistant is in roadmap AND in current code | **ADD as explicit top-level** (openai>=1.0.0) |
| **firebase-admin** | YES (in lockfile) | Backend for fcm-django | MEDIUM – fcm-django is in INSTALLED_APPS | Keep as explicit |
| **cachetools, google-auth, grpcio, etc.** | YES (as top-level) | All transitives of firebase-admin | LOW – correctly marked | Keep as is OR move to dev-only if firebase-admin upgrade isolates them |

### New Finding: `openai` is MISSING from requirements.txt

```python
./smartbot/services/chatbot_service.py:import openai
./smartbot/services/gpt_services.py:import openai
```

**The project is using `openai` but it is NOT pinned in `requirements.txt`.** This is a critical missing dependency. Must be added to the proposed production requirements.

---

## 6. Misclassifications from Phase 3 (Corrections)

| # | Phase 3 Classification | Phase 4 Correction |
|---|---|---|
| 1 | `boto3` listed as "KEEP NOW (lazy import)" | Should be flagged as "KEEP NOW (active S3 use in `whatsapp_service.py: upload_to_s3`)" |
| 2 | `openai` not mentioned in Phase 3 inventory at all | **CRITICAL MISS** – `openai` is used in 2 files; add to production |
| 3 | `Pillow` listed as transitive → "needs explicit pin" | **CONFIRMED** but also add to "Hidden → Must be Explicit" list |
| 4 | `PyPDF2` listed as "re-add" | **CONFIRMED** – used in `documents/utils.py: from PyPDF2 import PdfMerger` |
| 5 | `whitenoise` listed as KEEP FOR ROADMAP | **CONFIRMED** – correct |
| 6 | `celery` listed as KEEP FOR ROADMAP | **CONFIRMED** – correct, but the current `properties/scheduler.py` already uses it for `PeriodicTask` reads |

---

## 7. Final Approval Recommendation: **APPROVE with REVISE notes**

### Approve

The audit's classification is fundamentally correct. The split into 24 production + 6 roadmap + 19 remove is sound.

### Revise Before Application

1. **Add `openai` to production requirements** – currently in code, missing from lockfile
2. **Add `Pillow` to production requirements** – currently transitive, used by `ImageField`
3. **Add `PyPDF2` to production requirements** – currently transitive, used in `documents/utils.py`
4. **Add `psycopg2-binary` to production requirements** – currently CI-only
5. **Upgrade `boto3
