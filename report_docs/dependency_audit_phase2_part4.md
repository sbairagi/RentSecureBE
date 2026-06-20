# RentSecureBE – Dependency Hygiene Audit (Phase 2) – Part 4

**Status:** ANALYSIS ONLY – No changes applied

This document finalizes the audit with the remainder of the Phase 2C upgrade
roadmap and the **proposed** `requirements.txt` and `requirements-dev.txt` files
(do not apply yet).

---

## 6.3 Phase 2C – Upgrade Roadmap (continued)

| Step | Action | Risk | Rollback Strategy |
|---|---|---|---|
| 2C.1 | Upgrade `boto3` 1.18.53 → 1.35.x (and `botocore` accordingly) | **HIGH** – boto3 is used in `notification/services/whatsapp_service.py` (lazy import) | Pin to last-known-good version; run Twilio WhatsApp smoke test |
| 2C.2 | Upgrade `razorpay` 1.4.2 → 1.4.x latest (or 1.5+) | MEDIUM – Razorpay API surface may have changed | Test payment flow end-to-end with sandbox; pin older version if API mismatches |
| 2C.3 | Upgrade `urllib3` 1.26.20 → 2.x | MEDIUM – 2.x is major; `requests<2.32` is incompatible | Test all HTTP integrations (cashfree, leegality, twilio, fcm, etc.) |
| 2C.4 | Upgrade `pytz` 2021.3 → 2024.2 | LOW | Tests around timezone handling |
| 2C.5 | Plan `Django` 4.2 → 5.0/5.2 LTS upgrade | **HIGH** – major version | Run Django 5 upgrade checklist; do NOT combine with other upgrades |
| 2C.6 | Upgrade `google-api-core` 2.25.0rc1 → 2.25.x stable | LOW | Pin stable; only if `google-api-python-client` is re-added |
| 2C.7 | Run `pip-audit` against new requirements | LOW | n/a |
| 2C.8 | Update `pip-audit` ignore list (whitelist acceptable noisy advisories) | LOW | n/a |

**Affected packages:** `boto3`, `razorpay`, `urllib3`, `pytz`, `Django`, `google-api-core` (if needed).

**Recommended ordering:** URL/PDF/critical-path upgrades LAST (Django, boto3, urllib3).
Low-risk upgrades FIRST (pytz, dev tools).

---

## 7. Proposed Files (DO NOT APPLY YET)

### 7.1 Proposed `requirements.txt` (Production only)

> Note: This is a **proposal only**. Nothing has been written to the file.

```text
# =============================================================================
# RentSecureBE – Production Runtime Dependencies
# =============================================================================
# Pin all packages with == for reproducibility.
# Dev / test / lint tools go in requirements-dev.txt.
# This file must contain only packages imported by production code or
# registered in INSTALLED_APPS.
# =============================================================================

# --- Django core ---
Django==4.2.30
asgiref==3.8.1

# --- Django REST Framework + JWT Auth ---
djangorestframework==3.16.0
djangorestframework_simplejwt==5.5.0

# --- Audit / History ---
django-simple-history==3.8.0

# --- Background tasks (Celery beat schedule) ---
django-celery-beat==2.9.0
celery==5.6.3              # see note: requires rentsecure_be/celery.py

# --- Configuration / Environment ---
python-decouple==3.5

# --- Date / Time helpers ---
python-dateutil==2.9.0.post0

# --- HTTP / Networking ---
requests==2.32.3

# --- PDF Generation (production critical) ---
weasyprint==66.0
PyPDF2==3.0.1              # re-add; see documents/utils.py

# --- Spreadsheet / Excel exports ---
openpyxl==3.1.5
xlsxwriter==3.2.9

# --- Twilio: SMS / WhatsApp / Voice (production critical) ---
twilio==9.6.1

# --- Voice notes via gTTS (used by Twilio) ---
gTTS==2.5.4

# --- Razorpay Payments (production critical) ---
razorpay==1.4.2            # ⚠ upgrade in Phase 2C

# --- AWS SDK (used in whatsapp_service.py) ---
boto3==1.18.53             # ⚠ upgrade in Phase 2C (very stale)

# --- Firebase Cloud Messaging (push notifications) ---
fcm-django==2.2.1
firebase-admin==6.8.0

# --- Translations ---
deep-translator==1.11.4
```

**Note:** `PyPDF2` and `Pillow` were not in the top-217 list but ARE used in
production code. They will be re-added to the production requirements.

### 7.2 Proposed `requirements-dev.txt` (Development / Test only)

```text
# =============================================================================
# RentSecureBE – Development / Test Dependencies
# =============================================================================
# Install with: pip install -r requirements.txt -r requirements-dev.txt
# These are NOT shipped to production.
# =============================================================================

# --- Test framework ---
pytest==8.3.5
pytest-django==4.11.1

# --- Coverage / Test infra ---
coverage
psycopg2-binary            # for PostgreSQL test DB

# --- Type checking ---
mypy
django-stubs
djangorestframework-stubs

# --- Formatters / Linters ---
black
ruff
pylint
pylint-django

# --- Security tools ---
bandit
semgrep
pip-audit                  # Phase 1 already integrated
```

### 7.3 Recommended `.github/workflows` Change Sketch

```yaml
# In test.yml, lint.yml, quality.yml, security.yml
- name: Install
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
```

(The current `pip install bandit` / `pip install black` / `pip install ruff` lines
in workflows can stay OR be removed in favor of the consolidated install.)

---

## 8. Key Risks & Recommendations Summary

| # | Risk | Severity | Recommendation |
|---|---|---|---|
| 1 | `instagram-private-api` (unofficial, reverse-engineered) | **HIGH** | Remove in Phase 2B.1 |
| 2 | `django-rest-auth` (deprecated since 2019) | **HIGH** | Remove in Phase 2B.2 |
| 3 | `boto3` 1.18.53 (very stale) | HIGH | Upgrade in Phase 2C.1 |
| 4 | `celery` registered but no Celery app defined | MEDIUM | Architect decision in 2B.8 |
| 5 | `Django` 4.2 LTS nearing EOL (Apr 2026) | MEDIUM | Plan upgrade in Phase 2C.5 |
| 6 | `Flask` accidentally in Django project | MEDIUM | Remove in Phase 2B.3 |
| 7 | 33+ Possibly Unused packages | MEDIUM | Remove in Phase 2B.5–2B.7 |
| 8 | `pytest` in production `requirements.txt` | LOW | Move to `requirements-dev.txt` (Phase 2A) |
| 9 | No `Pillow` / `PyPDF2` pin (used by code) | LOW | Re-add in proposed `requirements.txt` |
| 10 | Duplicate S3 storage libs (`boto3` + `django-storages` + `django-s3-storage`) | LOW | Consolidate in Phase 2B |

---

## 9. Sign-off Checklist (Phase 2)

Before applying changes:

- [ ] Team agrees with the proposed `requirements.txt` package list
- [ ] Team agrees with the proposed `requirements-dev.txt` package list
- [ ] Architect decision: celery stay or go?
- [ ] Architect decision: whitenoise wire up or remove?
- [ ] Architect decision: django-storages needed?
- [ ] Backup of current `requirements.txt` stored in git history (already there)
- [ ] CI workflows updated to install from both files
- [ ] Docker / deployment updated to install from both files
- [ ] Run `pip-audit` against the proposed `requirements.txt`
- [ ] Verify `pytest` still passes
- [ ] Verify Bandit, Ruff, Mypy still pass
- [ ] Approval received to begin Phase 2A

---

## 10. Out of Scope (Phase 2 does NOT touch)

- Application code (no source files modified)
- Database models / migrations (no schema changes)
- CI workflow logic beyond install commands (no Phase 1 re-review)
- Removal of any package (Phase 2B is a *plan*, not an action)
- Git commits (audit only, no commits created)

---

**END OF AUDIT REPORT**

Generated by: Principal Staff Engineer / Dependency Governance Reviewer
Pipeline: Phase 2 of dependency hygiene; Phase 1 (CI/CD) preserved untouched.
