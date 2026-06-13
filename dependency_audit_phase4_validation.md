# RentSecureBE – Phase 4 Dependency Validation (Final Production-Grade Audit)

**Status:** ANALYSIS ONLY – No changes applied
**Date:** 2026-05-06
**Auditor:** Principal Staff Engineer / SaaS Architect / Dependency Governance Reviewer
**Python Runtime:** 3.13.3 (live); `pyproject.toml` targets `py312` (compatible)
**Live Packages Installed:** 186

---

## 1. Executive Summary

A full re-scan of the codebase was performed against 8 evidence vectors: actual imports, dynamic imports, Django settings, INSTALLED_APPS, MIDDLEWARE, management commands, Celery tasks, signals, and the multi-tenant SaaS roadmap.

### Key Corrections from Phase 3

| # | Phase 3 Claim | Phase 4 Correction | Why |
|---|---|---|---|
| 1 | `boto3` = KEEP NOW (lazy import) | **CONFIRMED + ESCALATED** | `whatsapp_service.py: upload_to_s3()` actively uses `boto3.client("s3")` to upload voice notes. S3 is in **active production use**, not just roadmap |
| 2 | `django-storages` = KEEP FOR ROADMAP | **KEEP NOW (advisory)** | Project still uses `MEDIA_ROOT` (local FS) for general file uploads; `django-storages` remains a forward-looking abstraction (not currently required) |
| 3 | `Pillow` = KEEP NOW (explicit) | **CONFIRMED** | 3 models use `ImageField` |
| 4 | `whitenoise` = KEEP FOR ROADMAP | **CONFIRMED** | Roadmap-aligned (Angular admin + AWS) |
| 5 | `celery` = KEEP FOR ROADMAP | **CONFIRMED** | `properties/scheduler.py` uses `django_celery_beat.models.PeriodicTask` (read-only); roadmap lists scheduled jobs |
| 6 | `pytest` in `requirements.txt` | **CORRECT** – must move to `requirements-dev.txt` |

### Final Tally (Phase 4)

- **A. KEEP NOW (Production, ~24 packages)**: 24 confirmed required packages
- **B. KEEP FOR ROADMAP (~6 packages)**: Roadmap-justified but not currently used
- **C. REMOVE (~19 packages)**: No current use, no roadmap value
- **D. INFRASTRUCTURE / FIX (~3 items)**: items that need code or settings change to be useful (celery app, whitenoise middleware, CORS)

### Phase 4 Verdict: **APPROVE with REVISE notes** (see Section 9)

---

## 2. Full Re-Scan Evidence Summary

### 2.1 Dynamic Imports

| Pattern | Found | Implications |
|---|---|---|
| `importlib.import_module` | 0 in production code (only test fixtures) | No hidden imports |
| `__import__(...)` | 2: `properties/tests/test_coverage.py` and `properties/models/caretaker_models.py: __import__("datetime").date.today()` (built-in module, not a package) | No package hidden behind dynamic import |
| `getattr(settings, ...)` pattern in `whatsapp_service.py` | YES (uses `settings.AWS_S3_BUCKET_NAME`) | Confirms S3 is wired into settings |
| `try: import boto3 except ImportError: boto3 = None` | YES in `whatsapp_service.py` | **Confirms boto3 is a hard runtime requirement** for `upload_to_s3()` |

### 2.2 Signals

- `core/signals.py`: `@receiver(post_save, sender=User)` → UserProfile auto-create (uses django.contrib.auth)
- `referral_and_earn/signals.py`: `@receiver(post_save, sender=User)` → Referral code generate
- `properties/signals/__init__.py`: 12 receivers (Renter, Building, Unit, Caretaker create/delete)
- All signals are **Django built-in** (no extra packages)

### 2.3 Management Commands

- 4 active `BaseCommand` subclasses in `management/commands/` + `notification/management/commands/`
- 2 commented-out (`seed_subscription_plans.py`, `send_tax_reminders.py`)
- **All use only Django built-ins** (no extra package)

### 2.4 INSTALLED_APPS (from `apps.py`)

8 first-party apps: `core`, `notification`, `referral_and_earn`, `ai_assistant`, `properties`, `smartbot`, `finance`, `documents`. **No new apps to add.**

### 2.5 Boto3 / S3 Sub-Modules

```python
# notification/services/whatsapp_service.py
s3 = boto3.client("s3")
s3.upload_file(file_path, bucket_name, key, ExtraArgs={"ContentType": "audio/mpeg"})
```

**This is a hard production dependency, not roadmap-only.**

### 2.6 Live Versions Verified

| Package | Current (requirements.txt) | Installed (venv) | Notes |
|---|---|---|---|
| Django | 4.2.30 | 4.2.30 | LTS until April 2026 |
| Pillow | 11.2.1 | 11.2.1 | (NOT pinned in requirements.txt top-217 – was missed) |
| PyPDF2 | (not in top-217) | 3.0.0 | Used in documents/utils.py |
| twilio | 9.6.1 | 9.6.1 | Current |
| fcm-django | 2.2.1 | 2.2.1 | Current |
| firebase-admin | 6.8.0 | 6.8.0 | Current |
| boto3 | 1.18.53 | (transitive) | **STALE** – needs upgrade |
| cel