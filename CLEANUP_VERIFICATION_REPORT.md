# CLEANUP VERIFICATION REPORT

**Project:** RentSecureBE
**Verification Date:** 2026-06-23
**Purpose:** Pre-deletion verification of 7 candidate files/directories
**Methodology:** Static import tracing, URL routing analysis, Django app registry inspection, test discovery pattern analysis

---

## Summary

| # | Item | Runtime Imports | Router Registrations | Django Registrations | Test References | SAFE_TO_DELETE |
|---|------|----------------|---------------------|----------------------|-----------------|----------------|
| 1 | `properties/_legacy/` (entire directory) | **0** | **0** | **0** | **0** | **YES** |
| 2 | `properties/original_models.py` | **0** | **0** | **0** | **0** | **YES** |
| 3 | `properties/refactored_models_combined.py` | **0** | **0** | **0** | **0** | **YES** |
| 4 | `properties/pdf_utils.py` | **0** | **0** | **0** | **0** | **YES** |
| 5 | `properties/constants.py` | **2** | **0** | **0** | **0** | **NO** |
| 6 | `smartbot/urls.py` | **0** | **0** | **0** | **0** | **YES** |
| 7 | `referral_and_earn/views.py` | **0** | **0** | **0** | **0** | **YES** (file only, not the app) |

---

## 1. `properties/_legacy/` (entire directory)

### 1.1 Files in Directory

| File | Lines |
|------|-------|
| `properties/_legacy/admin.py` | 336 |
| `properties/_legacy/models.py` | 576 |
| `properties/_legacy/serializers.py` | 249 |
| `properties/_legacy/signals.py` | 126 |
| `properties/_legacy/utils.py` | 266 |
| `properties/_legacy/views.py` | 674 |
| **Total** | **2242** |

### 1.2 Import References

**Search query:** `grep -r "properties\._legacy\|from properties\._legacy\|import properties\._legacy" --include="*.py" .`

**Result:** **0 matches** in active codebase (excluding `.kilo/worktrees/`, `__pycache__/`, `.venv/`).

**Verified no imports from:**
- `core/`
- `properties/views/`
- `properties/serializers/`
- `properties/models/`
- `properties/admin/`
- `properties/signals/`
- `properties/utils/`
- `rentsecure_be/`
- `dashboard/`
- `documents/`
- `finance/`
- `notification/`
- `smartbot/`
- `referral_and_earn/`
- `ai_assistant/`
- `tests/`

### 1.3 Router/URL Registrations

**Search query:** `grep -r "_legacy" --include="*.py" . | grep -E "urls\.py|router\.register|path\(|include\("`

**Result:** **0 matches**

**Verified not in:**
- `rentsecure_be/urls.py`
- `core/urls.py`
- `properties/urls.py`
- `finance/urls.py`
- `documents/urls.py`
- `dashboard/urls.py`

### 1.4 Django App Registrations

**Search query:** `grep -r "_legacy" --include="*.py" . | grep -E "INSTALLED_APPS|AppConfig|apps\.py"`

**Result:** **0 matches**

`properties/_legacy/` is NOT in `INSTALLED_APPS` (`rentsecure_be/settings.py:103-123`).

### 1.5 Test References

**Search query:** `grep -r "test_loopholes_critical\|notification/test_extra_charge_reminders\|smartbot/tests\|documents/tests\|referral_and_earn/tests\|ai_assistant/tests" --include="*.py" .`

**Result:** **0 matches** in Python code (only found in `pyproject.toml` as a per-file-ignore linting config, not as test imports).

**Pytest auto-discovery:** `pytest.ini` specifies `python_files = tests.py test_*.py *_tests.py`. Files in `properties/_legacy/` do NOT match these patterns (they are not named `test_*.py` or `*_tests.py`).

### 1.6 Additional Evidence

`pyproject.toml` explicitly excludes `properties/_legacy/**` from:
- Ruff linting (`exclude = ["...", "properties/_legacy/**", ...]`)
- Coverage reporting (`omit = ["...", "properties/_legacy/*", ...]`)

**Conclusion:** `properties/_legacy/` is a complete dead directory. SAFE_TO_DELETE = **YES**

---

## 2. `properties/original_models.py`

### 2.1 Import References

**Search query:** `grep -r "original_models" --include="*.py" .`

**Result:** **0 matches**

**Verified no imports from any active module.**

### 2.2 Router/URL Registrations

**Result:** **0 matches** — not referenced in any `urls.py`.

### 2.3 Django App Registrations

**Result:** **0 matches** — not in `INSTALLED_APPS`. File is not an app module.

### 2.4 Test References

**Result:** **0 matches** — no test imports or references.

**Additional evidence:** `pyproject.toml` explicitly lists `properties/original_models.py` in both Ruff exclusions and coverage exclusions.

**Conclusion:** Dead file. SAFE_TO_DELETE = **YES**

---

## 3. `properties/refactored_models_combined.py`

### 3.1 Import References

**Search query:** `grep -r "refactored_models_combined" --include="*.py" .`

**Result:** **0 matches**

**Verified no imports from any active module.**

### 3.2 Router/URL Registrations

**Result:** **0 matches** — not referenced in any `urls.py`.

### 3.3 Django App Registrations

**Result:** **0 matches** — not in `INSTALLED_APPS`. File is not an app module.

### 3.4 Test References

**Result:** **0 matches** — no test imports or references.

**Additional evidence:** `pyproject.toml` explicitly lists `properties/refactored_models_combined.py` in both Ruff exclusions and coverage exclusions.

**Conclusion:** Dead file. SAFE_TO_DELETE = **YES**

---

## 4. `properties/pdf_utils.py`

### 4.1 Import References

**Search query:** `grep -r "pdf_utils" --include="*.py" . | grep -v "# utils/pdf_utils.py"`

**Result:** **0 matches** with actual import/usage.

**Matches found ONLY in comments:**
- `properties/pdf_utils.py` line 1: `# utils/pdf_utils.py`
- `properties/_legacy/utils.py`: `# utils/pdf_utils.py` (2 occurrences)

**Verified no active imports from:**
- `properties/views/`
- `properties/serializers/`
- `properties/services/`
- `properties/utils/`
- Any other active module

**Active duplicate exists:** `properties/utils/__init__.py:167` defines `generate_rent_invoice_pdf()` which IS imported by `properties/views/rent_record_views.py:26`.

### 4.2 Router/URL Registrations

**Result:** **0 matches** — not referenced in any `urls.py`.

### 4.3 Django App Registrations

**Result:** **0 matches** — not in `INSTALLED_APPS`.

### 4.4 Test References

**Result:** **0 matches** — no test imports or references.

**Additional evidence:** `pyproject.toml` lists `properties/pdf_utils.py` in coverage exclusions.

**Conclusion:** Dead file with active duplicate in `properties/utils/__init__.py`. SAFE_TO_DELETE = **YES**

---

## 5. `properties/constants.py`

### 5.1 Import References

**Search query:** `grep -rn "from \.\.constants\|from properties\.constants\|import constants" --include="*.py" .`

**Result:** **2 matches** — ACTIVE IMPORTS FOUND.

**Active imports:**
1. `properties/views/building_views.py:11` — `from ..constants import BUILDINGS_CACHE_TIMEOUT`
2. `properties/views/unit_views.py:27` — `from ..constants import UNITS_CACHE_TIMEOUT`

**Constants defined and used:**

| Constant | Defined In | Used In |
|----------|-----------|---------|
| `BUILDINGS_CACHE_TIMEOUT` | `properties/constants.py:8` | `properties/views/building_views.py:30` |
| `UNITS_CACHE_TIMEOUT` | `properties/constants.py:9` | `properties/views/unit_views.py:66` |

**Impact of deletion:** Removing `properties/constants.py` would cause `ImportError` at runtime when either `BuildingViewSet` or `UnitViewSet` is accessed.

### 5.2 Router/URL Registrations

**Result:** **0 matches** — `constants.py` is not a view or URL module.

### 5.3 Django App Registrations

**Result:** **0 matches** — not in `INSTALLED_APPS`. It is a plain Python module imported by views.

### 5.4 Test References

**Result:** **0 matches** — no direct test imports of `properties.constants`.

### 5.5 Additional Evidence

`pyproject.toml` does NOT list `properties/constants.py` in any exclusion list.

**Conclusion:** `properties/constants.py` has **active runtime imports**. Deleting it would break `BuildingViewSet` and `UnitViewSet`. SAFE_TO_DELETE = **NO**

**Required action before deletion:** Move `BUILDINGS_CACHE_TIMEOUT` and `UNITS_CACHE_TIMEOUT` to `properties/settings.py` or inline them into the consuming views, then delete `properties/constants.py`.

---

## 6. `smartbot/urls.py`

### 6.1 Import References

**Search query:** `grep -r "smartbot\.urls\|from smartbot\.urls\|import smartbot\.urls" --include="*.py" .`

**Result:** **0 matches**

**Verified no imports from any active module.**

### 6.2 Router/URL Registrations

**Search query:** `grep -r "include.*smartbot\|path.*smartbot\|smartbot/urls" --include="*.py" .`

**Result:** **0 matches**

**Verified not in:**
- `rentsecure_be/urls.py`
- `core/urls.py`
- `properties/urls.py`
- `finance/urls.py`
- `documents/urls.py`
- `dashboard/urls.py`

### 6.3 Django App Registrations

`smartbot` IS in `INSTALLED_APPS` (`rentsecure_be/settings.py:122`), but `smartbot/urls.py` is an empty file (0 lines) and is not included in any root URLconf.

### 6.4 Test References

**Result:** **0 matches** — no test imports of `smartbot.urls`.

### 6.5 Additional Evidence

`smartbot/urls.py` contains **0 lines** of code (empty file).

**Conclusion:** `smartbot/urls.py` is an empty, unreferenced file. SAFE_TO_DELETE = **YES**

---

## 7. `referral_and_earn/views.py`

### 7.1 Import References

**Search query:** `grep -r "referral_and_earn\.views\|from referral_and_earn\.views\|import referral_and_earn\.views" --include="*.py" .`

**Result:** **0 matches**

**Verified no imports from any active module.**

### 7.2 Router/URL Registrations

**Search query:** `grep -r "include.*referral_and_earn\|path.*referral_and_earn\|referral_and_earn/urls" --include="*.py" .`

**Result:** **0 matches**

`referral_and_earn/urls.py` does NOT exist (verified: `ls referral_and_earn/urls.py` → "File not found").

**Verified not in:**
- `rentsecure_be/urls.py`
- `core/urls.py`
- `properties/urls.py`
- `finance/urls.py`
- `documents/urls.py`
- `dashboard/urls.py`

### 7.3 Django App Registrations

`referral_and_earn` IS in `INSTALLED_APPS` (`rentsecure_be/settings.py:120`). The app has:
- `models.py` — **ACTIVE** (`Referral` model used in `core/views.py`)
- `signals.py` — **ACTIVE** (imported by `apps.py`)
- `views.py` — **DEAD** (contains only `# Create your views here.`)
- No `urls.py` — no URL routing exists

### 7.4 Test References

**Result:** **0 matches** — no test imports of `referral_and_earn.views`. No `referral_and_earn/tests.py` file exists.

### 7.5 Additional Evidence

`referral_and_earn/views.py` contains only:
```python
# Create your views here.
```

**Conclusion:** `referral_and_earn/views.py` is a 1-line placeholder with no views and no references. The `referral_and_earn` app itself is alive (models and signals are used), but this specific file is dead. SAFE_TO_DELETE = **YES** (file deletion only; do not delete the app).

---

## Final Recommendations

| Priority | Item | Action |
|----------|------|--------|
| **1** | `properties/_legacy/` | **DELETE** — 2242 lines of dead code |
| **2** | `properties/original_models.py` | **DELETE** — dead file |
| **3** | `properties/refactored_models_combined.py` | **DELETE** — dead file |
| **4** | `properties/pdf_utils.py` | **DELETE** — dead file; active duplicate in `properties/utils/__init__.py` |
| **5** | `smartbot/urls.py` | **DELETE** — empty file, no references |
| **6** | `referral_and_earn/views.py` | **DELETE** — 1-line placeholder, no references |
| **7** | `properties/constants.py` | **DO NOT DELETE** — has active imports in `building_views.py` and `unit_views.py`. If cleanup is desired, inline `BUILDINGS_CACHE_TIMEOUT` and `UNITS_CACHE_TIMEOUT` into the consuming views first. |

---

## Post-Deletion Checklist

- [ ] Run full test suite after each deletion batch
- [ ] Verify `BuildingViewSet` and `UnitViewSet` still function (if `constants.py` is later inlined)
- [ ] Update `pyproject.toml` exclusions if any deleted items were listed
- [ ] Commit deletions separately from functional changes for easy revert

---

*End of Cleanup Verification Report*
