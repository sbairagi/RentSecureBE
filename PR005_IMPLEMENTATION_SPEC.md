# PR-005 Implementation Specification

## Split core/views.py

---

## 1. Purpose

Split the 399-line `core/views.py` god view into 4 focused modules: `auth_views.py`, `subscription_views.py`, `bank_views.py`, and `reporting_views.py`. No functional changes — pure refactor. Remove `core/views.py` and replace it with a `core/views/` package.

This PR is **blocked until PR-001 is merged** because:
1. `payments` must be in `INSTALLED_APPS`
2. `payments/views/webhooks.py` must exist (webhook handlers removed from `core/views.py` in PR-004)
3. `payment_ownerbankdetails` table must exist

---

## 2. Scope

### 2.1 In Scope

- Create `core/views/__init__.py` — package marker
- Create `core/views/auth_views.py` — OTP, authentication, and password views (`send_otp`, `SendOTP`, `_process_referral`, `_verify_otp_and_login`, `OwnerVerifyOTP`, `RenterVerifyOTP`, `ChangePasswordView`, `ResetPasswordView`)
- Create `core/views/subscription_views.py` — Subscription CRUD viewsets (`SubscriptionPlanViewSet`, `PlanFeatureLimitViewSet`, `UserSubscriptionViewSet`, `AddOnPurchaseViewSet`, `UsageLimitViewSet`)
- Create `core/views/bank_views.py` — Bank details and rent payment views (`update_owner_bank_details`, `create_rent_payment`)
- Create `core/views/reporting_views.py` — Owner reporting views (`rent_inflow_summary`, `owner_rent_records`, `download_rent_excel`)
- Delete `core/views.py` — replaced by `core/views/` package
- Update `core/urls.py` — update imports from `.views` to `.views.<module>`
- Update `core/tests/test_views.py` — update imports from `core.views` to `core.views.<module>`
- Update `core/tests/test_core_views.py` — update imports from `core.views` to `core.views.<module>`
- Update `core/tests/test_core_webhooks.py` — update imports from `core.views` to `core.views.<module>`

### 2.2 Out of Scope

- Moving `create_rent_payment` to `payments/` (Phase 3, PR-030)
- Moving `update_owner_bank_details` to `payments/views/bank_details_views.py` (Phase 3, PR-030)
- Moving identity services to `identity/` (Phase 1)
- Moving subscription services to `subscription/` (Phase 2)
- Creating `payments/views/bank_details_views.py` (Phase 3)
- Splitting `core/models.py` (Phase 5)
- Any changes to `core/services/` or other `core/` modules
- Any changes to `properties/`, `payments/`, `notification/`, or other apps
- Fixing the `razorpay` SDK import violation in `bank_views.py` (Phase 3)
- Creating `tests/architecture/` (PR-007)

---

## 3. Files

### 3.1 Files to Create

| File | Purpose | Owner |
|------|---------|-------|
| `core/views/__init__.py` | Package marker | Platform Team |
| `core/views/auth_views.py` | OTP, authentication, and password views | Platform Team |
| `core/views/subscription_views.py` | Subscription CRUD viewsets | Platform Team |
| `core/views/bank_views.py` | Bank details and rent payment views | Platform Team |
| `core/views/reporting_views.py` | Owner reporting views | Platform Team |

### 3.2 Files to Modify

| File | Change | Owner |
|------|--------|-------|
| `core/urls.py` | Update imports from `.views` to `.views.<module>` | Platform Team |
| `core/tests/test_views.py` | Update imports from `core.views` to `core.views.<module>` | Platform Team |
| `core/tests/test_core_views.py` | Update imports from `core.views` to `core.views.<module>` | Platform Team |
| `core/tests/test_core_webhooks.py` | Update imports from `core.views` to `core.views.<module>` | Platform Team |

### 3.3 Files to Delete

| File | Reason |
|------|--------|
| `core/views.py` | Replaced by `core/views/` package with 4 focused modules |

---

## 4. Responsibilities

| Role | Responsibility |
|------|----------------|
| **Platform Team Lead** | Owns `core/views/` split, `core/urls.py` updates, and test updates. Approves PR. |
| **Developer** | Implements view split, updates imports across codebase, runs full validation. |
| **AI Assistant** | Generates view modules, import updates, and test updates per this spec. Stops and asks if import paths are unclear. |

---

## 5. Acceptance Criteria

### 5.1 Functional

- [ ] `core/views/__init__.py` exists.
- [ ] `core/views/auth_views.py` contains all auth and password views and helpers.
- [ ] `core/views/subscription_views.py` contains all subscription viewsets.
- [ ] `core/views/bank_views.py` contains bank details and rent payment views.
- [ ] `core/views/reporting_views.py` contains all owner reporting views.
- [ ] `core/views.py` no longer exists (deleted).
- [ ] `core/urls.py` imports from `.views.<module>` instead of `.views`.
- [ ] All URLs resolve correctly (same URLs, same behavior).
- [ ] All existing tests pass without modification to test logic (only import paths change).
- [ ] No `from core.views import ...` (direct module import) remains in any file.

### 5.2 Non-Functional

- [ ] No view file exceeds 300 lines.
- [ ] All tests pass (existing + no regressions).
- [ ] No architecture test violations.
- [ ] No import-linter violations.
- [ ] No circular dependencies introduced.
- [ ] No security vulnerabilities (Bandit 0 high/medium).

---

## 6. Architecture Rules

### 6.1 Bounded Context Compliance

- `core/views/` is a transitional package. All views remain in `core/` during Phase 0.
- Views are split by domain responsibility, not by bounded context. This is a structural refactor only.
- No views are moved to other apps in this PR.
- `create_rent_payment` remains in `core/` until Phase 3 (PR-030).

### 6.2 Import Rules

| Source | shared | platform | identity (core) | subscription | property | payment | notification | document | finance | referral | dashboard |
|--------|--------|----------|-----------------|--------------|----------|---------|--------------|----------|---------|----------|-----------|
| **core (identity)** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Implications for this PR:**

1. `core/views/auth_views.py` **may** import from `notification/` (e.g., `NotificationService`) — `identity → notification` is allowed by the dependency matrix.
2. `core/views/bank_views.py` **must not** import from `payments/models.py` directly — `identity → payment` is NOT allowed by the dependency matrix. It must use the existing `core.models.OwnerBankDetails` shim or delegate via services.
3. `core/views/bank_views.py` contains `create_rent_payment` which directly imports `razorpay`. This violates ENGINEERING_STANDARDS §6.1 but is **out of scope** for this PR. The violation is noted and will be fixed in Phase 3.
4. All relative imports (`from .models import ...`, `from .serializers import ...`) remain unchanged.

**Critical constraint:** The `bank_views.py` module must not introduce new cross-app imports that violate the dependency matrix. Existing imports (e.g., `razorpay`, `properties.models.rent_record_models`) are grandfathered from the original `core/views.py` and will be addressed in Phase 3.

### 6.3 View Rules

- No view file may exceed **300 lines**.
- Views must not contain business logic (delegate to services).
- Views must not import models from other apps (use services instead).
- Views must not import payment SDKs (`razorpay`, `cashfree`) directly — existing violation in `bank_views.py` is grandfathered for Phase 0.
- Views must not import from `rentsecure_be/`.

### 6.4 URL Rules

- `core/urls.py` must import views from `core.views.<module>` instead of `core.views`.
- All URL patterns remain unchanged.
- All URL names remain unchanged.
- Redirect URLs from PR-004 remain unchanged.

### 6.5 Naming Rules

- View modules: `auth_views.py`, `subscription_views.py`, `bank_views.py`, `reporting_views.py`.
- Package marker: `__init__.py`.
- Test files: existing test files are updated with new import paths; no new test files are required.
- Test classes and methods remain unchanged.

### 6.6 Test Import Rules

- All `from core.views import X` must be changed to `from core.views.<module> import X`.
- All `@patch("core.views.Y")` must be changed to `@patch("core.views.<module>.Y")`.
- All `from core.views import (...)` multi-line imports must be updated.

---

## 7. CI Requirements

### 7.1 Required CI Gates

All gates are **blocking**. PR cannot be merged if any gate fails.

| Gate | Tool | Threshold | Command |
|------|------|-----------|---------|
| Lint | Ruff | 0 errors | `ruff check .` |
| Format | Ruff | 0 issues | `ruff format --check .` |
| Type Check | MyPy | 0 errors | `mypy .` |
| Import Rules | import-linter | 0 violations | `import-linter check` |
| Tests | Pytest | All pass, ≥90% coverage | `pytest tests/ -v --cov` |
| Django Check | manage.py | 0 errors | `python manage.py check` |
| Security | Bandit | 0 high/medium | `bandit -r core/` |

### 7.2 Pipeline Order

```
Lint → Type Check → Import Rules → Tests → Django Check → Security
```

### 7.3 Phase-Specific Architecture Tests

| Test | Purpose | Expected Result |
|------|---------|-----------------|
| `test_god_views.py` | No view file exceeds 300 lines | Pass (PR-005 enables this test for `core/views/`) |
| `test_import_rules.py` | No forbidden SDK imports in new code | Pass |
| `test_rentsecure_be_boundary.py` | No app imports from `rentsecure_be/` | Pass |
| `test_circular_deps.py` | No new circular dependencies | Pass |

**Note:** `test_god_views.py` will be created in PR-007. For PR-005, the implementer must manually verify that no view file exceeds 300 lines.

---

## 8. Testing Strategy

### 8.1 Test Tiers Required

| Tier | Scope | Requirement |
|------|-------|-------------|
| **Unit** | View import updates | ≥90% coverage for new code |
| **Integration** | URL resolution and view behavior | ≥80% coverage |
| **Architecture** | View file sizes, import boundaries | 0 violations |
| **Security** | Bandit scan on changed files | 0 high/medium |

### 8.2 Existing Test Updates

All existing tests must pass after import path updates. No test logic changes are required.

**Files to update:**

- `core/tests/test_views.py` — update `from core.views import (...)` to `from core.views.auth_views import ...`, `from core.views.subscription_views import ...`, etc.
- `core/tests/test_core_views.py` — update `from core.views import download_rent_excel, owner_rent_records, rent_inflow_summary` to `from core.views.reporting_views import ...`
- `core/tests/test_core_webhooks.py` — update `from core.views import _process_referral, create_rent_payment` to `from core.views.auth_views import _process_referral` and `from core.views.bank_views import create_rent_payment`

### 8.3 Import Path Update Patterns

**Pattern 1: Multi-line imports in `core/tests/test_views.py`**
```python
# Before
from core.views import (
    AddOnPurchaseViewSet,
    ChangePasswordView,
    ...
)

# After
from core.views.auth_views import ChangePasswordView, ResetPasswordView, SendOTP, OwnerVerifyOTP, RenterVerifyOTP
from core.views.subscription_views import (
    AddOnPurchaseViewSet,
    PlanFeatureLimitViewSet,
    SubscriptionPlanViewSet,
    UsageLimitViewSet,
    UserSubscriptionViewSet,
)
from core.views.bank_views import create_rent_payment, update_owner_bank_details
from core.views.reporting_views import download_rent_excel, owner_rent_records, rent_inflow_summary
```

**Pattern 2: Single-line imports in `core/tests/test_core_views.py`**
```python
# Before
from core.views import download_rent_excel, owner_rent_records, rent_inflow_summary

# After
from core.views.reporting_views import download_rent_excel, owner_rent_records, rent_inflow_summary
```

**Pattern 3: Patch strings in test decorators**
```python
# Before
@patch("core.views.send_otp")
@patch("core.views.Client")
@patch("core.views.razorpay.Client")
@patch("core.views.delete_beneficiary")
@patch("core.views.generate_owner_rent_report")

# After
@patch("core.views.auth_views.send_otp")
@patch("core.views.auth_views.Client")  # if Client is used there
@patch("core.views.bank_views.razorpay.Client")
@patch("core.views.bank_views.delete_beneficiary")
@patch("core.views.reporting_views.generate_owner_rent_report")
```

### 8.4 URL Resolution Tests

Required verification:
- All URLs in `core/urls.py` resolve to the correct view functions/classes.
- All URL names remain unchanged.
- Router URLs (`subscription-plans`, `user-subscriptions`, etc.) continue to work.

### 8.5 Architecture Tests

AI must verify the following after changes:
- No view file exceeds 300 lines.
- No `from core.views import X` (direct module import) remains in any file.
- No `from core.views import (...)` multi-line import remains.
- No `@patch("core.views.Y")` string remains.
- `core/urls.py` imports from `.views.<module>` only.
- No circular dependencies introduced.

### 8.6 Security Tests

- Run `bandit -r core/views/` and verify 0 high/medium findings.
- Note: `bank_views.py` contains `razorpay` SDK import and `create_rent_payment` which uses it directly. This is an existing violation grandfathered from the original `core/views.py`. Bandit must not flag new issues introduced by the split.

### 8.7 Forbidden Test Patterns

- No `time.sleep()` in tests.
- No test dependencies on execution order.
- No hardcoded test data (use factories).
- No mocking Django ORM in integration tests (use test database).

---

## 9. Migration Strategy

### 9.1 Forward Migration

**Step 1: Deploy PR-005 to staging**
```bash
python manage.py migrate
```
No new migrations are created in this PR. Verifies all existing migrations apply cleanly.

**Step 2: Verify URL resolution**
```bash
python manage.py show_urls | grep "api/"
```
All expected URLs are present and resolve to the correct views.

**Step 3: Run smoke tests**
```bash
python manage.py test core.tests
```
All existing tests pass with updated import paths.

### 9.2 No Data Migration

This PR is a pure refactor. No data migration is required. No database schema changes. No data risk.

### 9.3 Reverse Migration

Reverse migration is a `git revert` of PR-005. The `core/views.py` file is restored from git history. All import paths are reverted. No database changes required.

---

## 10. Rollback Plan

### 10.1 Rollback Triggers

Rollback is triggered if any of the following occur:
- URL resolution fails after deployment (404/500 on any endpoint).
- Import errors occur in production (`ImportError: cannot import name 'X' from 'core.views'`).
- Any CI gate fails after merge and cannot be fixed within 15 minutes.
- Production incident: any endpoint returns 500 after deployment.
- Test suite fails to pass after import updates.

### 10.2 Rollback Steps

1. **Deploy decision:** Confirm rollback decision with Platform Team Lead.
2. **Git revert:**
   ```bash
   git revert <PR-005-merge-commit-sha>
   git push origin main
   ```
3. **Restore `core/views.py`:** The revert restores the original `core/views.py` from git.
4. **Revert import updates:** All test and URL config changes are reverted.
5. **Deploy reverted code:** Deploy the reverted commit to staging, then production.
6. **Smoke tests:**
   ```bash
   python manage.py check
   python manage.py migrate
   python manage.py shell -c "from django.urls import reverse; print(reverse('token_refresh'))"
   ```
7. **Verify production health:** Check that all `core/` endpoints return 200.
8. **Notify team:** Post rollback completion notice with root cause and fix plan.

### 10.3 Estimated Rollback Time

**15 minutes** (git revert + deploy + smoke tests).

### 10.4 Data Risk

**None.** No data changes. No schema changes. Pure code reorganization.

### 10.5 Rollback Validation

- Rollback must be tested on staging **before** production deploy.
- Test sequence:
  1. Apply PR-005 to staging.
  2. Verify all URLs resolve correctly.
  3. Verify all tests pass.
  4. Execute rollback steps 2-7 above.
  5. Verify `core/views.py` is restored and all endpoints work.
  6. Re-apply PR-005 after successful rollback test.

---

## 11. Expected Git Diff

### 11.1 Summary

| Metric | Value |
|--------|-------|
| Files changed | 8 (5 new, 3 modified, 1 deleted) |
| Files added | 5 |
| Files modified | 3 |
| Files deleted | 1 |
| Lines added | ~420 |
| Lines removed | ~399 |
| Net change | ~21 lines |

### 11.2 Files Added (~420 lines)

| File | Approx Lines | Description |
|------|---------------|-------------|
| `core/views/__init__.py` | 0 | Package marker |
| `core/views/auth_views.py` | ~160 | OTP, auth, password views and helpers |
| `core/views/subscription_views.py` | ~80 | Subscription viewsets |
| `core/views/bank_views.py` | ~100 | Bank details and rent payment views |
| `core/views/reporting_views.py` | ~80 | Owner reporting views |

### 11.3 Files Modified (~30 lines)

| File | Approx Lines Changed | Description |
|------|----------------------|-------------|
| `core/urls.py` | +12, -8 | Update imports from `.views` to `.views.<module>` |
| `core/tests/test_views.py` | +15, -20 | Update imports and patch strings |
| `core/tests/test_core_views.py` | +3, -3 | Update import |
| `core/tests/test_core_webhooks.py` | +4, -4 | Update imports |

### 11.4 Files Deleted (~399 lines)

| File | Approx Lines | Description |
|------|---------------|-------------|
| `core/views.py` | 399 | Replaced by `core/views/` package |

### 11.5 Diff Constraints

- No file in the diff may exceed 400 lines total after modification.
- No more than 15 files changed (actual count: 8 — well within limit).
- No deletions of existing functionality (all views are relocated, not removed).
- Net change is small (~21 lines) because this is a pure file reorganization.

---

## 12. Definition of Done

PR-005 is **Done** when ALL of the following are true.

### Code
- [ ] `core/views/` package created with 4 modules.
- [ ] `core/views/auth_views.py` contains all auth/password views.
- [ ] `core/views/subscription_views.py` contains all subscription viewsets.
- [ ] `core/views/bank_views.py` contains bank details and rent payment views.
- [ ] `core/views/reporting_views.py` contains all reporting views.
- [ ] `core/views.py` deleted.
- [ ] No view file exceeds 300 lines.
- [ ] `core/urls.py` imports from `.views.<module>` only.
- [ ] No `from core.views import X` (direct module import) remains in any file.

### Tests
- [ ] `core/tests/test_views.py` updated with new import paths.
- [ ] `core/tests/test_core_views.py` updated with new import paths.
- [ ] `core/tests/test_core_webhooks.py` updated with new import paths.
- [ ] All existing tests pass (no regressions).
- [ ] All URL resolution tests pass.
- [ ] Test coverage ≥90% for new code.

### CI
- [ ] `ruff check .` passes (0 errors).
- [ ] `ruff format --check .` passes.
- [ ] `mypy .` passes (0 errors).
- [ ] `import-linter check` passes (0 violations).
- [ ] `pytest tests/ -v --cov` passes.
- [ ] `python manage.py check` passes.
- [ ] `bandit -r core/views/` passes (0 high/medium for new code).

### Architecture
- [ ] No view file exceeds 300 lines.
- [ ] No `core.views` direct imports remain.
- [ ] No circular dependencies introduced.
- [ ] No `rentsecure_be/` imports in new files.
- [ ] `bank_views.py` `razorpay` import is grandfathered (noted for Phase 3 fix).

### Deployment
- [ ] PR approved by Platform Team Lead.
- [ ] Merged to `phase-0-foundation` branch.
- [ ] Deployed to staging.
- [ ] Staging validation passed (24 hours).
- [ ] Rollback tested on staging before production deploy.
- [ ] No production incidents during staging validation.

---

## 13. Developer Checklist

### Pre-Implementation
- [ ] Verify PR-004 is merged to `phase-0-foundation` branch.
- [ ] Verify `core/views.py` exists and is 399 lines (webhooks removed by PR-004).
- [ ] Verify `core/views/` directory does not exist.
- [ ] Read `ENGINEERING_STANDARDS.md` sections: View Rules, Import Rules, Naming Conventions.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Import Rules.
- [ ] Check current `core/views.py` for all view classes and functions.
- [ ] Check current `core/urls.py` for `.views` imports.
- [ ] Check all test files for `core.views` imports and patch strings.
- [ ] Verify dependency matrix: `core/` may import from `notification/` but NOT from `payment/`.

### Implementation
- [ ] Create `core/views/__init__.py`.
- [ ] Create `core/views/auth_views.py` with auth/password views and helpers.
- [ ] Create `core/views/subscription_views.py` with subscription viewsets.
- [ ] Create `core/views/bank_views.py` with bank details and rent payment views.
- [ ] Create `core/views/reporting_views.py` with owner reporting views.
- [ ] Delete `core/views.py`.
- [ ] Update `core/urls.py` imports.
- [ ] Update `core/tests/test_views.py` imports and patch strings.
- [ ] Update `core/tests/test_core_views.py` imports.
- [ ] Update `core/tests/test_core_webhooks.py` imports.
- [ ] Verify no view file exceeds 300 lines.
- [ ] Verify no `from core.views import` remains.

### Testing
- [ ] Run `pytest core/tests/test_views.py -v`.
- [ ] Run `pytest core/tests/test_core_views.py -v`.
- [ ] Run `pytest core/tests/test_core_webhooks.py -v`.
- [ ] Run `pytest tests/ -v --cov` and verify ≥90% coverage.
- [ ] Verify all URLs resolve: `python manage.py show_urls | grep "api/"`.
- [ ] Verify no `from core.views import` remains in any file.

### Validation
- [ ] Run `ruff check .` and verify 0 errors.
- [ ] Run `ruff format --check .` and verify 0 issues.
- [ ] Run `mypy .` and verify 0 errors.
- [ ] Run `import-linter check` and verify 0 violations.
- [ ] Run `python manage.py check` and verify 0 errors.
- [ ] Run `bandit -r core/views/` and verify 0 high/medium for new code.
- [ ] Verify no `print()` statements in new code.
- [ ] Verify no `# TODO` or `# FIXME` comments.
- [ ] Verify no commented-out code.
- [ ] Verify no hardcoded secrets.

### Rollback
- [ ] Document rollback plan in PR description.
- [ ] Test rollback on staging: apply PR-005, verify URLs, execute rollback, verify `core/views.py` restored.

### PR
- [ ] Commit message follows conventional commits format.
- [ ] Branch name follows `<type>/<ticket-id>-<description>` format.
- [ ] PR description includes: summary, motivation, changes, testing, rollback plan.
- [ ] PR size is within limits (≤400 lines, ≤15 files).
- [ ] PR is linked to Phase 0 task 0.6.

---

## 14. Reviewer Checklist

Use this checklist when reviewing PR-005.

### Architecture
- [ ] `core/views/` package created with exactly 4 modules.
- [ ] No view file exceeds 300 lines.
- [ ] `core/views.py` is deleted.
- [ ] No `from core.views import X` (direct module import) remains in any file.
- [ ] `core/urls.py` imports from `.views.<module>` only.
- [ ] No circular dependencies introduced.
- [ ] No new `apps/` or `config/` directories.
- [ ] No views moved to other apps (pure `core/` refactor).
- [ ] Dependency matrix compliance: no `core/` imports from `payment/`.

### Security
- [ ] No new security vulnerabilities introduced.
- [ ] No sensitive data logged in new view files.
- [ ] No secrets or API keys in new view files.
- [ ] Bandit scan passes (0 high/medium for new code).
- [ ] `razorpay` import in `bank_views.py` is grandfathered (noted for Phase 3 fix).

### Code Quality
- [ ] Ruff passes (0 errors, 0 formatting issues).
- [ ] MyPy passes (0 errors).
- [ ] No `print()` statements.
- [ ] No `# TODO` or `# FIXME` comments.
- [ ] No commented-out code.
- [ ] No empty `except:` clauses.

### Testing
- [ ] All existing tests pass with updated import paths.
- [ ] `core/tests/test_views.py` updated correctly.
- [ ] `core/tests/test_core_views.py` updated correctly.
- [ ] `core/tests/test_core_webhooks.py` updated correctly.
- [ ] All URL resolution tests pass.
- [ ] No test depends on execution order.
- [ ] No test uses `time.sleep()`.

### Migrations
- [ ] No new migrations required (pure refactor).
- [ ] `python manage.py migrate` applies cleanly.

### Documentation
- [ ] `docs/architecture/contexts/identity.md` updated with view split info.
- [ ] ADR-001 updated to reflect `core/views/` package structure.
- [ ] CHANGELOG.md updated.

### CI
- [ ] All CI gates pass.
- [ ] No import-linter violations.
- [ ] No architecture test failures.

---

## 15. AI Checklist

Use this checklist when generating PR-005 with AI assistance.

### Pre-Generation
- [ ] Read `ENGINEERING_STANDARDS.md` sections: View Rules, Import Rules, Naming Conventions.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Import Rules.
- [ ] Verify PR-004 is merged to `phase-0-foundation` branch.
- [ ] Verify `core/views.py` exists and contains the expected views (399 lines after PR-004).
- [ ] Verify `core/views/` directory does not exist.
- [ ] Verify `core/urls.py` imports from `.views`.
- [ ] Verify all test files that import from `core.views`.
- [ ] Confirm dependency matrix constraint: `core/` may import from `notification/` but NOT from `payment/`.

### Code Generation
- [ ] Generate `core/views/__init__.py`.
- [ ] Generate `core/views/auth_views.py` with all auth/password views and helpers.
- [ ] Generate `core/views/subscription_views.py` with all subscription viewsets.
- [ ] Generate `core/views/bank_views.py` with bank details and rent payment views.
- [ ] Generate `core/views/reporting_views.py` with all reporting views.
- [ ] Delete `core/views.py`.
- [ ] Update `core/urls.py` imports.
- [ ] Update `core/tests/test_views.py` imports and patch strings.
- [ ] Update `core/tests/test_core_views.py` imports.
- [ ] Update `core/tests/test_core_webhooks.py` imports.
- [ ] **Do NOT** move any views to other apps.
- [ ] **Do NOT** fix the `razorpay` import violation in `bank_views.py` (Phase 3 scope).
- [ ] **Do NOT** create `tests/architecture/` (PR-007 scope).

### Test Generation
- [ ] No new test files required (existing tests are updated with new import paths).
- [ ] Update all `from core.views import X` to `from core.views.<module> import X`.
- [ ] Update all `@patch("core.views.Y")` to `@patch("core.views.<module>.Y")`.
- [ ] **Do NOT** modify test logic (only import paths).
- [ ] **Do NOT** use `time.sleep()` in tests.

### Validation
- [ ] Run `ruff check .` and fix all errors.
- [ ] Run `ruff format --check .` and fix all issues.
- [ ] Run `mypy .` and fix all errors.
- [ ] Run `import-linter check` and fix all violations.
- [ ] Run `pytest tests/ -v --cov` and verify all pass.
- [ ] Run `python manage.py check` and verify 0 errors.
- [ ] Run `bandit -r core/views/` and verify 0 high/medium for new code.
- [ ] Verify no `from core.views import X` remains in any file.
- [ ] Verify no view file exceeds 300 lines.
- [ ] Verify all URLs resolve correctly.

### Stop and Ask Conditions
AI must **stop and ask human** before proceeding if:
- [ ] `create_rent_payment` or `update_owner_bank_details` must be moved to another app (not in scope for PR-005).
- [ ] Any file other than the 4 test files and `core/urls.py` imports from `core.views`.
- [ ] A view file exceeds 300 lines after the split and cannot be further subdivided within the 4-module constraint.
- [ ] The `razorpay` import in `bank_views.py` must be removed as part of this PR (Phase 3 scope — stop and ask).
- [ ] Any CI gate fails after 3 fix attempts.
- [ ] Dependency matrix exception is required to complete the task.

### Commit
- [ ] Commit message follows format: `refactor(core): split god view into 4 focused modules`.
- [ ] Commit body explains: view split rationale, file structure, import updates, reference to ADR-004 and ADR-001.
- [ ] Branch name: `feature/phase-0-005-split-core-views`.

---

## 16. Stop-and-Ask Conditions

AI must **stop and ask human** before proceeding if:

1. `create_rent_payment` or `update_owner_bank_details` must be moved to `payments/` or another app (not in scope for PR-005).
2. Any file outside the identified 4 test files and `core/urls.py` imports from `core.views`.
3. A view file exceeds 300 lines and cannot fit within the 4-module constraint without further splitting.
4. The `razorpay` SDK import in `bank_views.py` must be removed (Phase 3 scope — requires ADR exception if forced).
5. `core/urls.py` relative imports cannot be updated to submodule imports (unexpected Django limitation).
6. Any CI gate fails after 3 fix attempts.
7. Dependency matrix exception is required to complete the task.
8. A new bounded context or app directory is required to accommodate the split.

---

## 17. Appendices

### Appendix A: Architecture Decision References

| Decision | Reference |
|----------|-----------|
| `core/` as identity bounded context | ADR-001 |
| View file size limit (300 lines) | ADR-001 §2.3, ENGINEERING_STANDARDS §6.3 |
| No `core.views` direct imports | ADR-001 §2.3, ENGINEERING_STANDARDS §16.2, AI_ENGINEERING_PLAYBOOK §6.2 |
| `core/` may import from `notification/` | ADR-001 §2.3, dependency matrix |
| `core/` cannot import from `payment/` | ADR-001 §2.3, dependency matrix |
| God view anti-pattern | ENGINEERING_STANDARDS §24.1, ADR-004 |
| Phase 0 is additive/internal refactor only | ADR-007 §2.1 |
| No `apps/` parent directory | ADR-001 |
| `razorpay` import grandfathered in `core/` | ADR-004 §3.7, Phase 3 scope |

### Appendix B: Related Documents

- [Architecture v1.1 Release Candidate](../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Architecture v1.1 Implementation Master Plan — Phase 0](../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan — PR-005](../PHASE_0_EXECUTION_PLAN.md)
- [Engineering Standards](../ENGINEERING_STANDARDS.md)
- [AI Engineering Playbook](../AI_ENGINEERING_PLAYBOOK.md)
- [Bounded Context Strategy ADR](../docs/architecture/adr/ADR-001_bounded_context_strategy.md)
- [Payment Architecture ADR](../docs/architecture/adr/ADR-004_payment_architecture.md)
- [Migration Strategy ADR](../docs/architecture/adr/ADR-007_migration_strategy.md)
- [Import Rules ADR](../docs/architecture/adr/ADR-006_import_rules.md)

### Appendix C: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-20 | Principal Software Architect | Initial PR-005 specification for v1.1 freeze |

**Next Review:** After PR-005 merge
**Approval Required:** Platform Team Lead

---

*End of PR-005 Implementation Specification*
