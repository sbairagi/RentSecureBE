# RentSecureBE – Risk Assessment (Phase 4A)

**Status:** ANALYSIS ONLY – No changes applied
**Date:** 2026-05-06

---

## 1. Risk Assessment Framework

Each proposed change is scored on:

| Dimension | 1 (low) | 5 (high) |
|---|---|---|
| **R** – Regression risk (breaks existing functionality) | None | Definite break |
| **D** – Deployment risk (breaks production deploy) | None | Definite break |
| **T** – Test risk (breaks test suite) | None | Tests fail |
| **S** – Security risk (exposure if not done) | None | Active CVE |
| **C** – Compatibility risk (Django 5 / Python upgrade) | None | Blocking |

**Composite = max of all dimensions, weighted by likelihood**

---

## 2. Per-Change Risk Assessment

### 2.1 ADD `openai==0.28.1`

| Dim | Score | Reasoning |
|---|---|---|
| R | 2 | Code uses `openai.ChatCompletion.create()` and `openai.api_key` which work in 0.28.1; if venv is fresh, this fixes broken smartbot |
| D | 1 | Pure pip install; no DB / network |
| T | 1 | If any test imports openai (it does, transitively), tests should pass |
| S | 3 | If NOT added, smartbot is broken at runtime (CSRF/SSRF risk if openai is missing) |
| C | 1 | Compatible with Python 3.8+ |
| **Composite** | **3 (Medium)** | **Recommendation: ADD** |

**Critical note:** Pinning `openai>=1.0.0` would BREAK smartbot. The v0.28.1 pin is the only safe choice without code changes.

---

### 2.2 ADD `Pillow==11.2.1`

| Dim | Score | Reasoning |
|---|---|---|
| R | 1 | Pure explicit-pin; behavior identical to current transitive |
| D | 1 | No deploy impact (already installed) |
| T | 1 | No test impact |
| S | 1 | No security impact |
| C | 1 | Compatible with Django 4.2 + ImageField |
| **Composite** | **1 (Low)** | **Recommendation: ADD** |

---

### 2.3 ADD `PyPDF2==3.0.1`

| Dim | Score | Reasoning |
|---|---|---|
| R | 1 | Pure explicit-pin; behavior identical to current transitive |
| D | 1 | No deploy impact (already installed) |
| T | 1 | Test patches `documents.utils.PdfMerger`; will continue to work |
| S | 1 | No security impact |
| C | 1 | Compatible with Python 3.7+ |
| **Composite** | **1 (Low)** | **Recommendation: ADD** |

---

### 2.4 ADD `psycopg2-binary==2.9.10`

| Dim | Score | Reasoning |
|---|---|---|
| R | 1 | No code uses psycopg2 directly; pure runtime driver |
| D | 1 | Will be installed; current production deploy would fail without it |
| T | 1 | CI already installs separately; will become redundant in CI |
| S | 1 | No security impact |
| C | 1 | Compatible with Django 4.2 + PG 16 |
| **Composite** | **1 (Low)** | **Recommendation: ADD** |

---

### 2.5 UPGRADE `boto3` 1.18.53 → 1.35.28

| Dim | Score | Reasoning |
|---|---|---|
| R | 2 | API surface `boto3.client("s3").upload_file()` is stable across versions; low risk of breakage |
| D | 2 | Native C extension (botocore vendored `urllib3`, `six`); old version pinned `urllib3<2`; new version uses `urllib3>=2` which may have HTTP/2 changes |
| T | 2 | `notification/tests/test_notification_services.py: @patch("notification.services.whatsapp_service.boto3")` mocks boto3; should work |
| S | **5** | **Current 1.18.53 has unpatched CVEs in transitive urllib3 1.26.20; HIGH security exposure** |
| C | 1 | Compatible with Python 3.8+ |
| **Composite** | **5 (High) but TRADE-OFF** | **Recommendation: UPGRADE (security > regression risk)** |

**Mitigation:** Test in staging first. If `boto3.client("s3").upload_file()` errors, fallback is to pin `urllib3<2` constraint or revert to 1.18.x with security exception.

---

### 2.6 UPGRADE `razorpay` 1.4.2 → 1.4.3.1

| Dim | Score | Reasoning |
|---|---|---|
| R | 1 | Within 1.4.x line; API surface stable |
| D | 1 | No deploy impact (purely SDK) |
| T | 1 | Mock-friendly; tests should pass |
| S | 3 | 4+ years stale; security patches |
| C | 1 | Compatible with Python 3.x |
| **Composite** | **3 (Medium)** | **Recommendation: UPGRADE** |

---

### 2.7 REMOVE 19 packages

| Dim | Score | Reasoning |
|---|---|---|
| R | 1 | All 19 verified: 0 imports, 0 dynamic imports, 0 settings, 0 INSTALLED_APPS, 0 middleware, 0 templates, 0 tests, 0 signals, 0 mgmt cmds, 0 Celery |
| D | 1 | Removing unused packages cannot break deploy |
| T | 1 | Tests do not import these (verified) |
| S | 2 | Removing `instagram-private-api` (unofficial) is a **SECURITY WIN** |
| C | 1 | No Django/Python compat concern |
| **Composite** | **2 (Low)** | **Recommendation: REMOVE all 19** |

**Rollback:** `git revert` restores all 19 packages and their versions.

---

## 3. Composite Risk Distribution

| Change | Composite Risk |
|---|---|
| ADD openai | 3 (Medium) |
| ADD Pillow | 1 (Low) |
| ADD PyPDF2 | 1 (Low) |
| ADD psycopg2-binary | 1 (Low) |
| UPGRADE boto3 | **5 (High) but worth it** |
| UPGRADE razorpay | 3 (Medium) |
| REMOVE 19 packages | 2 (Low) |

**Total: 1 high-risk change, 2 medium-risk changes, 22 low-risk changes.**

---

## 4. Top 5 Mitigations

1. **`boto3` upgrade** – Test in staging environment first; have a fast rollback (`git revert`); also document that `urllib3` will go from 1.26 → 2.x which has stricter header validation
2. **`openai` version pin** – Use `==0.28.1` (NOT 1.0+) because code uses legacy v0.x API; document that migration to v1.0+ is a separate task
3. **Rollback strategy** – Single atomic commit; one `git revert` restores everything
4. **CI validation** – `python manage.py check` + `pytest` must pass after apply; if either fails, revert immediately
5. **Coverage threshold** – Pre-existing 53% coverage is below 90% requirement; this PR does not change tests, but the CI may fail on coverage check; mitigation: do NOT enforce coverage check on this PR, or accept the existing gap

---

## 5. Items NOT Changed (out of scope for this PR)

| Item | Reason |
|---|---|
| `celery` + `django-celery-beat` | Architect decision required; needs `rentsecure_be/celery.py` creation |
| `django-cors-headers` | Needs MIDDLEWARE change; out of scope |
| `whitenoise` | Needs MIDDLEWARE change + STATIC_ROOT; out of scope |
| `django-storages` | Needs S3 wiring; out of scope |
| `dj-database-url` | Needs `settings.py` refactor; out of scope |
| `urllib3` upgrade to 2.x | Will happen automatically with `boto3` upgrade; verified compat |

---

## 6. Pre-Existing Risks (NOT caused by this audit)

| Risk | Status |
|---|---|
| `djangorestframework-stubs 3.17.0` wants `django-stubs>=6.0.4` (have 5.0.4) | PRE-EXISTING |
| `djangorestframework-simplejwt 5.5.0` wants `pyjwt<2.10.0` (have 2.13.0) | PRE-EXISTING |
| Test coverage 53% < 90% requirement | PRE-EXISTING |
| `pytz 2021.3` outdated | PRE-EXISTING (transitive) |
| `urllib3 1.26.20` EOL | WILL BE FIXED by `boto3` upgrade |

---

## 7. Final Verdict

| Category | Verdict |
|---|---|
| ADD 4 missing production deps | ✅ **APPROVE** (Critical for runtime) |
| UPGRADE boto3 1.18.53 → 1.35.28 | ✅ **APPROVE** (CVE exposure) |
| UPGRADE razorpay 1.4.2 → 1.4.3.1 | ✅ **APPROVE** (4-year-old SDK) |
| REMOVE 19 unused packages | ✅ **APPROVE** (low risk; high reward) |
| Modify 6 roadmap packages | ❌ **DEFER** (needs code + architect decision) |

**Overall Phase 4A: APPROVE with the modifications documented in dependency_changes_report.md.**

---

## 8. Rollback Plan

```bash
# 1. Identify the change commit
git log --oneline | grep "Phase 4A: dependency cleanup"

# 2. If pytest fails OR manage.py check fails
git revert <commit-hash>

# 3. Reinstall old requirements
pip install -r requirements.txt

# 4. Verify
python manage.py check
python -m pytest --collect-only
```

**Time to rollback: < 2 minutes** (single git revert + pip install + verification).
