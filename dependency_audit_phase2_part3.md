# RentSecureBE – Dependency Hygiene Audit (Phase 2) – Part 3

**Status:** ANALYSIS ONLY – No changes applied

This document extends the audit with Security findings, Migration Plan, and the
proposed requirements split. See `dependency_audit_phase2.md` for the full
inventory and `dependency_audit_phase2_part2.md` for Possibly Unused evidence.

---

## 5. Security Review

### 5.1 Unmaintained Packages

| Package | Current Version | Last Release (PyPI) | Risk | Action |
|---|---|---|---|---|
| `django-rest-auth` | 0.9.5 | 2019 | **HIGH** – officially deprecated, no security backports | Remove (replaced by simplejwt) |
| `instagram-private-api` | 1.6.0.0 | 2019 (community fork, abandoned) | **HIGH** – unofficial reverse-engineered client, license risk | Remove immediately |
| `instaloader` | 4.14.1 | Active but unused | LOW (only because we don't use it) | Remove |
| `pytz` | 2021.3 | Many newer versions | MEDIUM – outdated tz data; CVE history around DST rules | Upgrade to 2024.x |
| `boto3` | 1.18.53 | Latest is 1.35+ (released 2024+) | MEDIUM – many CVEs fixed in newer boto3/botocore | Upgrade to latest 1.x |

### 5.2 Deprecated Packages

| Package | Replacement | Notes |
|---|---|---|
| `django-rest-auth` | `djangorestframework_simplejwt` (already used) | Removable |
| `pytz` | Python 3.9+ has `zoneinfo` in stdlib | Django 4+ can use zoneinfo; consider removal |
| `PyMySQL` | – | Project does not use MySQL |

### 5.3 Known Risky Packages

| Package | Risk | Reason | Action |
|---|---|---|---|
| `instagram-private-api` | **HIGH** | Unofficial reverse-engineered client; license uncertain; common target for malicious code; **NOT used in code** | **Remove immediately** |
| `boto3==1.18.53` | MEDIUM | Old release; botocore has had security advisories | Upgrade to ≥1.34 |
| `urllib3==1.26.20` | LOW-MEDIUM | 1.26.x is EOL branch; 2.x has CVE fixes | Upgrade to 2.x (verify compatibility) |
| `cryptography==45.0.2` | LOW | Newer than 42.x, generally safe | Keep; consider pinning to >=43 |
| `Pillow` (currently missing) | LOW | Frequent CVEs; **must be explicit dep** | Pin explicitly to latest stable |
| `google-api-core==2.25.0rc1` | LOW | Pre-release; rc1 in production | Replace with stable `google-api-core` if used (currently only transitive) |

### 5.4 Duplicate Functionality

| Functionality | Packages in requirements.txt | Recommendation |
|---|---|---|
| S3 storage | `boto3`, `django-storages`, `django-s3-storage` | Keep only `boto3` (used by code) + `django-storages` (Django abstraction). Remove `django-s3-storage` |
| PDF generation | `weasyprint`, `fpdf`, `fpdf2` | Keep only `weasyprint` (used). Remove `fpdf`, `fpdf2` |
| Web framework | `Django` (used), `Flask` (unused) | Remove `Flask` |
| ORM | Django ORM (used), `SQLAlchemy` (unused) | Remove `SQLAlchemy` |
| Auth | `rest_framework_simplejwt` (used), `django-rest-auth` (unused), `django-otp` (unused) | Keep simplejwt; remove the rest |
| Google APIs | `firebase-admin` (used via fcm_django), `google-api-python-client` (unused), `google-cloud-core/firestore/storage` (unused) | Keep `firebase-admin`; remove the rest |
| Database driver | `psycopg2-binary` (CI installs separately; not in requirements.txt – flag for prod) | Add `psycopg[binary]>=3.1` or `psycopg2-binary>=2.9` to requirements.txt for prod |
| HTTP client | `requests` (used) | Keep |
| Translation | `deep-translator` (used) | Keep |

### 5.5 Packages That Should Be Upgraded

| Package | Current | Recommended | Severity | Reason |
|---|---|---|---|---|
| `Django` | 4.2.30 | 5.0 LTS or 5.2 LTS | MEDIUM | 4.2 LTS ends April 2026; need upgrade path |
| `boto3` | 1.18.53 | ≥1.34.x | HIGH | 3+ years stale; security advisories |
| `botocore` (transitive) | 1.21.53 | Latest | HIGH | bundled with boto3 |
| `razorpay` | 1.4.2 | ≥1.4 latest (1.4.2 from 2021) | MEDIUM | old SDK; API surface may have changed |
| `urllib3` | 1.26.20 | 2.x | MEDIUM | 1.26 EOL |
| `pytz` | 2021.3 | 2024.2 | LOW | tz data updates |
| `cryptography` | 45.0.2 | Latest | LOW | keep current |
| `twilio` | 9.6.1 | Latest | LOW | keep current |
| `weasyprint` | 66.0 | Latest | LOW | keep current |
| `celery` | 5.6.3 | 5.4.x (already current) | n/a | current |
| `djangorestframework` | 3.16.0 | 3.15.x | LOW | already current |
| `djangorestframework_simplejwt` | 5.5.0 | 5.5.x | LOW | current |
| `django-simple-history` | 3.8.0 | 3.8.x | LOW | current |
| `fcm-django` | 2.2.1 | 2.2.x | LOW | current |
| `firebase-admin` | 6.8.0 | 6.6.x | LOW | current |
| `google-api-core` | 2.25.0rc1 | 2.25.x stable | MEDIUM | pre-release in production |

### 5.6 Pre-commit / CI Tool Hygiene

The CI workflows install tools individually (`pip install black`, `pip install ruff`, etc.).
This is correct – these tools should **NOT** be in `requirements.txt` and instead live
in `requirements-dev.txt` (test runners install from both) or be installed at the
tool level in CI (current pattern).

**Add to `requirements-dev.txt`:**
- `pytest==8.3.5`
- `pytest-django==4.11.1`
- `coverage`
- `psycopg2-binary` (test DB driver)
- `mypy`, `django-stubs`, `djangorestframework-stubs`
- `black`, `ruff`, `pylint`, `pylint-django`
- `bandit`, `semgrep`
- `pip-audit` (Phase 1 already integrated)

### 5.7 CVEs / pip-audit Suggestions

This audit is static. We recommend a follow-up `pip-audit` run on the proposed
`requirements.txt` to surface any CVEs in the remaining 20 top-level packages.
Phase 1 has already integrated `pip-audit` – run it after the proposed split.

---

## 6. Migration Plan

### 6.1 Phase 2A – Requirements Split (Low Risk)

**Objective:** Create `requirements.txt` (production) and `requirements-dev.txt`
(development) without removing any package from the lockfile.

| Step | Action | Risk | Rollback Strategy |
|---|---|---|---|
| 2A.1 | Add the proposed `requirements.txt` (production-only, ~20 packages) and `requirements-dev.txt` (tests + dev tools) | **LOW** – additive, doesn't remove anything | `git revert` the commit |
| 2A.2 | Update `.github/workflows/test.yml` to do `pip install -r requirements.txt -r requirements-dev.txt` | LOW | Revert workflow change |
| 2A.3 | Update `.github/workflows/lint.yml` and `quality.yml` to use `requirements-dev.txt` (or install tools individually as before) | LOW | Revert workflow change |
| 2A.4 | Run CI to confirm green | LOW | n/a |

**Affected packages:** All 217 packages, but only the structure changes.

**Affected files:**
- `requirements.txt` (rewritten to ~20 lines)
- `requirements-dev.txt` (new file, ~15 lines)
- `.github/workflows/*.yml` (install commands updated)
- `Dockerfile` / `docker-compose.yml` / `deploy.yml` (install commands updated)

### 6.2 Phase 2B – Dependency Cleanup Candidates (Medium Risk)

**Objective:** Remove confirmed-unused and high-risk packages from the production
lockfile once the project confirms they are not needed.

| Step | Action | Risk | Rollback Strategy |
|---|---|---|---|
| 2B.1 | Remove **`instagram-private-api==1.6.0.0`** (security) | **HIGH** *if* secretly used at runtime | Verify via `python -c "import instagram_private_api"` in CI; revert commit if import error |
| 2B.2 | Remove **`django-rest-auth==0.9.5`** (deprecated) | MEDIUM – if some old code still references it | Search code for `rest_auth` URLs/views; remove references before deleting |
| 2B.3 | Remove **`Flask==3.1.1`** (framework leak) | LOW – unused | `git revert` |
| 2B.4 | Remove **`SQLAlchemy==2.0.41`** (duplicate ORM) | LOW – unused | `git revert` |
| 2B.5 | Remove **`fpdf==1.7.2`, `fpdf2==2.8.3`, `selenium==4.29.0`, `pandas==2.2.2`, `PyMySQL==1.0.2`, `instaloader==4.14.1`** | LOW – all unused | `git revert` |
| 2B.6 | Remove **`django-crum`, `django-multiselectfield`, `django-otp`, `django-s3-storage`, `django-select2`, `django-widget-tweaks`, `drf-writable-nested`, `dj-database-url`** | LOW | `git revert` |
| 2B.7 | Remove **`google-api-python-client`, `google-cloud-core`, `google-cloud-firestore`, `google-cloud-storage`** | LOW – all unused | `git revert` |
| 2B.8 | **Decide celery**: either (a) define `rentsecure_be/celery.py` and keep packages, or (b) remove `celery` + `django-celery-beat` | MEDIUM – architectural | (a) is reversible; (b) requires removing migrations and admin references |
| 2B.9 | **Decide whitenoise**: either wire it up in MIDDLEWARE or remove | MEDIUM | Reversible |
| 2B.10 | **Decide django-storages**: confirm with team; remove if S3 is not planned | MEDIUM | Reversible |
| 2B.11 | Run `pip-audit`, `bandit`, `pytest`, smoke tests | LOW | n/a |

**Affected packages:** ~25 packages removed.

### 6.3 Phase 2C – Upgrade Roadmap (Medium-High Risk)

**Objective:** Upgrade outdated and high-CVE packages. Each upgrade in a separate PR.

| Step | Action | Risk | Rollback Strategy |
|---|---|---|---|
| 2C.1 | Upgrade `boto3` from 1.18.53 → 1.35.x | **HIGH** – boto3 is used in `whatsapp_service.py` | Pin to last-known-good version; test Twilio path |
| 2C.2 | Upgrade `botocore` (transitive) – b
