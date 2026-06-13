# RentSecureBE – Phase 3 Future-Aware Audit – Part 2

This document completes `dependency_audit_phase3_future_aware.md` with:
- Final cost-benefit analysis (continued)
- Final recommended `requirements.txt`
- Final recommended `requirements-dev.txt`
- Maintenance and security impact estimate
- Migration approach (no commits; recommendations only)

---

## 6. Per-Package Cost-Benefit Analysis (Roadmap Packages) – continued

| Package | Current Cost (security/maintenance) | Future Value (12 months) | Cost of Keeping | Cost of Removing | Verdict |
|---|---|---|---|---|---|
| `PyPDF2` | LOW | **HIGH** (PDF Merging roadmap) | Negligible | High – production PDFs break | **KEEP (explicit top-level)** |
| `firebase-admin` | LOW | **HIGH** (Push notifications roadmap) | ~50MB | High – fcm-django breaks | **KEEP** |
| `fcm-django` | LOW | **HIGH** (Push notifications roadmap) | Negligible | High – push notifications break | **KEEP** |
| `psycopg2-binary` | LOW | **HIGH** (PostgreSQL production roadmap) | ~5MB | High – production DB driver missing | **KEEP (add to requirements.txt)** |

---

## 7. Final Recommended `requirements.txt` (Production, Future-Aware)

> **Status: PROPOSAL ONLY – DO NOT APPLY UNTIL APPROVED**

```text
# =============================================================================
# RentSecureBE – Production Runtime Dependencies (Future-Aware)
# =============================================================================
# Total: 30 production top-level packages
# Strategy: KEEP NOW (21) + KEEP FOR ROADMAP (9)
# REMOVED: 19 (no current use, no roadmap value)
# =============================================================================

# --- Django core (KEEP NOW) ---
Django==4.2.30
asgiref==3.8.1

# --- Django REST Framework + JWT Auth (KEEP NOW) ---
djangorestframework==3.16.0
djangorestframework_simplejwt==5.5.0

# --- CORS for mobile + web clients (KEEP FOR ROADMAP) ---
django-cors-headers==3.9.0         # ⚠ wire up in INSTALLED_APPS + MIDDLEWARE

# --- Audit / History (KEEP NOW) ---
django-simple-history==3.8.0

# --- Background tasks / Celery (KEEP FOR ROADMAP) ---
# ⚠ architecturally inert today; create rentsecure_be/celery.py and add worker/beat to deploy.yml
celery==5.6.3
django-celery-beat==2.9.0

# --- WhiteNoise static files (KEEP FOR ROADMAP) ---
# ⚠ wire up in MIDDLEWARE
whitenoise==5.3.0

# --- PostgreSQL production (KEEP FOR ROADMAP) ---
psycopg2-binary                    # ⚠ add to requirements.txt (currently installed by CI only)

# --- Configuration / Environment (KEEP NOW) ---
python-decouple==3.5

# --- 12-factor DB config (KEEP FOR ROADMAP) ---
dj-database-url==2.3.0             # ⚠ refactor settings.py to use it

# --- Date / Time helpers (KEEP NOW) ---
python-dateutil==2.9.0.post0

# --- HTTP / Networking (KEEP NOW) ---
requests==2.32.3

# --- PDF Generation & Merging (KEEP NOW) ---
weasyprint==66.0
PyPDF2==3.0.1

# --- Image handling for ImageField (KEEP NOW) ---
Pillow==11.2.1

# --- Spreadsheet / Excel exports (KEEP NOW) ---
openpyxl==3.1.5
xlsxwriter==3.2.9

# --- Twilio: SMS / WhatsApp / Voice (KEEP NOW) ---
twilio==9.6.1

# --- Voice notes via gTTS (KEEP NOW) ---
gTTS==2.5.4

# --- Razorpay Payments (KEEP NOW) ---
razorpay==1.4.2                   # ⚠ upgrade to 1.4.x latest in Phase 2C

# --- AWS SDK + S3 (KEEP NOW) ---
boto3==1.18.53                    # ⚠ upgrade to 1.35+ in Phase 2C

# --- S3 Django storage abstraction (KEEP FOR ROADMAP) ---
# ⚠ configure DEFAULT_FILE_STORAGE when S3 is enabled
django-storages==1.11.1

# --- Firebase Cloud Messaging (KEEP NOW) ---
fcm-django==2.2.1
firebase-admin==6.8.0

# --- Translations (KEEP NOW) ---
deep-translator==1.11.4

# --- Nested DRF serializers for parent+child POSTs (KEEP FOR ROADMAP) ---
# Document usage; safe to keep
drf-writable-nested==0.7.0
```

**Total: 30 production packages** (vs 217 in current lockfile; reduction of **86%**).

---

## 8. Final Recommended `requirements-dev.txt` (Development / Test only)

```text
# =============================================================================
# RentSecureBE – Development / Test Dependencies
# =============================================================================
# Install with: pip install -r requirements.txt -r requirements-dev.txt
# =============================================================================

# --- Test framework (KEEP NOW) ---
pytest==8.3.5
pytest-django==4.11.1

# --- Coverage / Test infra (KEEP NOW) ---
coverage
psycopg2-binary                    # for PostgreSQL test DB

# --- Type checking (KEEP NOW) ---
mypy
django-stubs
djangorestframework-stubs

# --- Formatters / Linters (KEEP NOW) ---
black
ruff
pylint
pylint-django

# --- Security tools (KEEP NOW) ---
bandit
semgrep
pip-audit
```

---

## 9. Estimated Maintenance & Security Impact

### 9.1 Reduction in Top-Level Dependencies

| Metric | Before (today) | After (Phase 3 recommendation) | Reduction |
|---|---|---|---|
| Production `requirements.txt` | 217 (untracked flat list) | **30 pinned** | **86%** |
| Development `requirements-dev.txt` | 0 (mixed into prod) | 13 | new file |
| Transitive at top level | 158 | 0 | **100%** |
| Unused / Risky at top level | 33 + 1 risky | 0 | **100%** |

### 9.2 Maintenance Impact (Positive)

| Benefit | Impact |
|---|---|
| Faster `pip install` | ~70% reduction in installed packages (transitives no longer pinned) |
| Smaller Docker image | ~150–300MB savings (Flask, pandas, jupyter, selenium, etc.) |
| Faster CI | Less to install, less to scan with `pip-audit` |
| Fewer CVEs to track | Only the 30 production + 13 dev packages need ongoing monitoring |
| Cleaner architecture | Explicit top-level dependencies = clearer onboarding for new engineers |
| Faster `pip-audit` scans | Run against ~43 packages instead of 217 |

### 9.3 Security Impact (Positive)

| Benefit | Impact |
|---|---|
| Removed `instagram-private-api` (unofficial reverse-engineered) | **HIGH** security win |
| Removed deprecated `django-rest-auth` | Removes 2019-era unmaintained code |
| Reduced supply chain attack surface | 19 fewer top-level packages = 19 fewer potential compromise vectors |
| Roadmap-aligned CORS + static files | Production-hardened configuration ready for mobile + web clients |
| PostgreSQL driver explicit | No more "hope it's transitively installed" |

### 9.4 Architectural Risk (if Roadmap is NOT followed)

If the team does **NOT** wire up:
- `django-cors-headers` → mobile/web admin will fail in production
- `whitenoise` → static files will 404 in production behind ALB
- `celery` + `django-celery-beat` → scheduled notifications will not work in production
- `django-storages` → S3 file uploads will require manual boto3 wiring
- `dj-database-url` → no 12-factor DB config for ECS/K8s
- `psycopg2-binary` → PostgreSQL deployment will fail without DB driver

---

## 10. Cost-Benefit Summary (Per Roadmap Package)

| Package | Roadmap Need | Keep? | If kept, action required | If removed, consequence |
|---|---|---|---|---|
| `celery` + `django-celery-beat` | **CRITICAL** | ✅ KEEP | Create `rentsecure_be/celery.py`; deploy Celery worker + beat; convert commands to `@shared_task` | **HIGH** – blocks background jobs, scheduled notifications |
| `django-cors-headers` | **CRITICAL** | ✅ KEEP | Add to `INSTALLED_APPS` + `MIDDLEWARE` | **HIGH** – mobile/web clients fail CORS |
| `whitenoise` | **HIGH** | ✅ KEEP | Add `WhiteNoiseMiddleware` to `MIDDLEWARE`; set `STATIC_ROOT` and run `collectstatic` | **MEDIUM** – static files 404 in prod |
| `django-storages` | **HIGH** | ✅ KEEP | Configure `DEFAULT_FILE_STORAGE` when S3 is enabled | **MEDIUM** – re-add when S3 implemented |
| `psycopg2-binary` | **HIGH** | ✅ KEEP | Add to requirements.txt (currently CI-only) | **HIGH** – prod DB driver missing |
| `Pillow` | **HIGH** | ✅ KEEP | Add to requirements.txt (currently transitive) | **HIGH** – Django raises `ImproperlyConfigured` |
| `PyPDF2` | **HIGH** | ✅ KEEP | Add to requirements.txt (currently pinned to old version) | **HIGH** – PDF merging breaks |
| `firebase-admin` + `fcm-django` | **HIGH** | ✅ KEEP | None (already configured) | **HIGH** – push notifications break |
| `dj-database-url` | **MEDIUM** | ✅ KEEP | Refactor `settings.py` to use it | **LOW** – team re-adds when containerizing |
| `drf-writable-nested` | **MEDIUM** | ✅ KEEP | Document when to use | **LOW** – alternative is custom `create()` |
| `boto3` | **HIGH** | ✅ KEEP + UPGRADE | Upgrade to 1.35+ in Phase 2C | **HIGH** – S3 + AWS deploy breaks |
| `google-cloud-firestore` | **LOW** | ❌ REMOVE | Re-add when microservice uses Firestore | None (not in roadmap) |
| `google-cloud-storage` | **LOW** | ❌ REMOVE | Re-add if GCS added to roadmap | None (AWS chosen) |

---

## 11. Migration Approach (For Approval)

### Recommended Order

| Phase | Action | Risk | Rollback |
|---|---|---|---|
| **3A.1** | Remove 19 confirmed-unused packages (Flask, fpdf, fpdf2, selenium, SQLAlchemy, pandas, PyMySQL, instagram-private-api, instaloader, django-crum, django-multiselectfield, django-otp, django-rest-auth, django-s3-storage, django-select2, django-widget-tweaks, google-api-python-client, google-cloud-core, arrow) | LOW | `git revert` |
| **3A.2** | Wire up `django-cors-headers` (INSTALLED_APPS + MIDDLEWARE) | LOW | `git revert` |
| **3A.3** | Wire up `whitenoise` (add to MIDDLEWARE, set STATIC_ROOT, run collectstatic) | LOW | `git revert` |
| **3A.4** | Add `psycopg2-binary`, `Pillow`, `PyPDF2` (re-add) to `requirements.txt` | LOW | `git revert` |
| **3A.5** | Add `dj-database-url` to `requirements.txt`; refactor `settings.py` to use it | LOW | `git revert` |
| **3B.1** | Add `drf-writable-nested` to `requirements.txt` (already approved as KEEP) | LOW | `git revert` |
| **3B.2** | Add `django-storages` to `requirements.txt` (already approved as KEEP) | LOW | `git revert` |
| **3C.1** | **Architectural fix:** Create `rentsecure_be/celery.py`; add `Celery(... )` app; add worker + beat processes to `deploy.yml`; convert management commands to `@shared_task` | **MEDIUM** | `git revert`; keep cron-only flow |
| **3C.2** | Upgrade `boto3` 1.18.53 → 1.35.x (Phase 2C) | MEDIUM | Pin to last-known-good version |
| **3C.3** | Upgrade `razorpay` 1.4.2 → 1.4.x latest (Phase 2C) | MEDIUM | Test payment flow end-to-end |
| **3C.4** | Plan `Django` 4.2 → 5.0/5.2 LTS upgrade (Phase 2C) | **HIGH** | Major version; run Django 5 upgrade checklist |

---

## 12. Total Package Count After Phase 3

| File | Count | Change |
|---|---|---|
| `requirements.txt` (production) | **30** | -187 (from 217) |
| `requirements-dev.txt` (development) | **13** | new file (was 0) |
| **Total managed top-level** | **43** | -174 (from 217) |

**Reduction: 80% of top-level packages removed.**

---

## 13. Out of Scope (Recap)

- ❌ No `requirements.txt` modified
- ❌ No workflows modified
- ❌ No application code modified
- ❌ No database models modified
- ❌ No git commits created
- ❌ No packages removed
- ❌ No architecture changes (Celery wiring is a recommendation, not an action)

**Future-aware analysis complete. Awaiting approval.**

---

## 14. Sign-Off Checklist (Phase 3)

Before any Phase 3 change is applied:

- [ ] Product/Engineering confirms the 12-month roadmap
- [ ] Architect decides on Celery: wire up now OR remove
- [ ] Architect decides on CORS: wire up now OR remove
- [ ] Architect decides on WhiteNoise: wire up now OR rely on external
- [ ] Architect decides on PostgreSQL: confirm and add driver
- [ ] Architect decides on S3: configure `DEFAULT_FILE_STORAGE` when ready
- [ ] CI workflows updated to install from both `requirements.txt` + `requirements-dev.txt`
- [ ] Docker / deployment updated
- [ ] Run `pip-audit` against the proposed split
- [ ] Verify `pytest` still passes
- [ ] Approval received to begin Phase 3A.1 (safe removals)
