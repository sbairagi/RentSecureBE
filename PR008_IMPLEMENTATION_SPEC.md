# PR-008 Implementation Specification

## Architecture Cleanup Phase 1 — Remove PR-007 Violations

---

## 1. Purpose

Execute the first Architecture Cleanup phase by resolving all bounded-context violations detected by the architecture regression tests added in PR-007. This PR fixes import-level architecture violations without changing any business behavior, database schema, models, serializers, or API contracts.

This PR is **blocked until PR-007 is merged** because:
1. Architecture regression tests in `tests/architecture/` must exist to detect violations
2. `import-linter.ini` must enforce the v1.1 dependency matrix
3. All violations must be catalogued by the new architecture tests before fixing

---

## 2. Scope

### 2.1 In Scope

- Remove all `rentsecure_be/` imports from application code (`core/`, `payments/`, `properties/`)
- Remove direct payment SDK (`razorpay`, `cashfree`) imports outside `payments/adapters/`
- Remove `properties/` → `payments/` forbidden imports in `properties/views/rent_record_views.py`
- Remove `documents/` → `properties/` forbidden imports in `documents/views.py` and `documents/utils.py`
- Fix view files exceeding 300-line limit (`properties/views/unit_views.py`)
- Fix model files exceeding 400-line limit (`properties/models/unit_models.py`)
- Resolve circular dependency chains between app packages
- Fix view-layer compliance violations (views importing models from other apps)
- Add necessary lazy-import helper utilities to preserve test patch targets
- Update `import-linter.ini` if new app-level utilities are introduced
- Verify all architecture regression tests pass

### 2.2 Out of Scope

- Any changes to business logic, model definitions, or serializer definitions
- Any database migrations or schema changes
- Any API endpoint changes or new endpoints
- Any new features or functionality
- Changes to `shared/` package structure
- Changes to `rentsecure_be/` package (legacy compatibility layer)
- Moving or renaming entire view modules
- Changes to `notification/` bounded context
- Any changes to existing tests outside `tests/architecture/`
- ADR modifications

---

## 3. Files

### 3.1 Files to Create

| File | Purpose | Owner |
|------|---------|-------|
| `payments/utils/cashfree_payout.py` | Move `cashfree_payout` utilities from `rentsecure_be/utils/` to `payments/utils/` | Platform Team |
| `properties/services/leegality_service.py` | Move `leegality_service` from `rentsecure_be/services/` to `properties/services/` | Platform Team |
| `payments/services/cashfree_service.py` | Move `cashfree_service` compatibility wrapper from `rentsecure_be/services/` to `payments/services/` | Platform Team |
| `payments/services/razorpay_service.py` | Move `razorpay_service` compatibility wrapper from `rentsecure_be/services/` to `payments/services/` | Platform Team |
| `core/services/bank_details_service.py` | Refactor to remove `rentsecure_be/` import; use `payments/` adapter or lazy import | Platform Team |
| `properties/views/rent_record_views.py` | Refactor to remove direct `payments/` imports; use lazy imports or service delegation | Platform Team |
| `documents/views.py` | Refactor to remove `properties/` imports; use lazy imports or Django apps.get_model | Platform Team |
| `documents/utils.py` | Refactor to remove `properties/` imports; use lazy imports or Django apps.get_model | Platform Team |
| `properties/views/unit_views.py` | Refactor to reduce line count below 300 lines (extract helper functions) | Platform Team |
| `properties/models/unit_models.py` | Refactor to reduce line count below 400 lines (extract mixins or proxy models) | Platform Team |
| `core/views/bank_views.py` | Remove direct `razorpay` SDK import; delegate to `payments/adapters/razorpay.py` | Platform Team |
| `payments/adapters/razorpay.py` | Add `create_order()` method to encapsulate direct SDK usage | Platform Team |

### 3.2 Files to Modify

| File | Change | Owner |
|------|--------|-------|
| `import-linter.ini` | Ensure `rentsecure_be` is not in any app's allowed layers; verify `payments` → `properties` dependency is correct | Platform Team |
| `core/services/bank_details_service.py` | Remove `from rentsecure_be.utils.cashfree_payout import add_beneficiary`; use lazy import or delegate to `payments/` | Platform Team |
| `payments/adapters/cashfree.py` | Remove `from rentsecure_be.utils.cashfree_payout import ...`; import from `payments.utils.cashfree_payout` | Platform Team |
| `properties/views/unit_views.py` | Remove `from rentsecure_be.services.leegality_service import send_agreement_for_signature`; import from `properties/services/leegality_service.py` | Platform Team |
| `properties/views/rent_record_views.py` | Remove top-level `payments/` imports; use module-level lazy-import wrappers (`create_payment_link()`, `process_rent_payout()`) to preserve test patch targets | Platform Team |
| `documents/views.py` | Remove `from properties.models import ...` and `from properties.serializers import ...`; use `apps.get_model()` and lazy imports | Platform Team |
| `documents/utils.py` | Remove `from properties.models import ...`; use `apps.get_model()` or lazy import | Platform Team |
| `core/views/bank_views.py` | Remove `import razorpay`; use `RazorpayAdapter().create_order()` instead | Platform Team |
| `.github/workflows/architecture.yml` | Ensure `architecture-tests` job runs `pytest tests/architecture/ -v --tb=short` and blocks CI on failure | Platform Team |
| `.github/workflows/ci.yml` | Ensure `architecture-tests` job is in quality gate `needs` | Platform Team |

### 3.3 Files to Delete

| File | Reason | Owner |
|------|--------|-------|
| `rentsecure_be/utils/cashfree_payout.py` | Moved to `payments/utils/cashfree_payout.py` | Platform Team |
| `rentsecure_be/services/leegality_service.py` | Moved to `properties/services/leegality_service.py` | Platform Team |
| `rentsecure_be/services/cashfree_service.py` | Moved to `payments/services/cashfree_service.py` | Platform Team |
| `rentsecure_be/services/razorpay_service.py` | Moved to `payments/services/razorpay_service.py` | Platform Team |

---

## 4. Responsibilities

| Role | Responsibility |
|------|----------------|
| **Platform Team Lead** | Approves refactoring approach; verifies no business behavior changes; owns PR merge |
| **Staff Engineer** | Reviews dependency matrix compliance; verifies no circular dependencies introduced |
| **Architecture Review Board** | Approves any ADR exceptions if refactoring requires temporary matrix relaxation |
| **Developer** | Implements fixes; runs full validation; ensures all architecture tests pass |
| **AI Assistant** | Generates refactored code per this spec; stops and asks if business behavior changes are required |

---

## 5. Acceptance Criteria

### 5.1 Functional

- [ ] No `rentsecure_be/` imports remain in application code outside `rentsecure_be/` itself.
- [ ] No direct `razorpay` or `cashfree` SDK imports exist outside `payments/adapters/`.
- [ ] `properties/views/rent_record_views.py` does not import from `payments/` at module level.
- [ ] `documents/views.py` does not import from `properties/` at module level.
- [ ] `documents/utils.py` does not import from `properties/` at module level.
- [ ] `properties/views/unit_views.py` is under 300 lines.
- [ ] `properties/models/unit_models.py` is under 400 lines.
- [ ] No circular dependency chains exist between app packages.
- [ ] All view files comply with layer compliance rules (no cross-app model imports at module level).
- [ ] `core/views/bank_views.py` delegates to `payments/adapters/razorpay.py` instead of importing SDK directly.
- [ ] All existing tests continue to pass (no behavioral regressions).
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.

### 5.2 Non-Functional

- [ ] `import-linter check` passes with 0 violations.
- [ ] No business behavior changes (all existing tests pass).
- [ ] No database migrations required.
- [ ] No model field changes.
- [ ] No serializer changes.
- [ ] No API contract changes.
- [ ] No new features introduced.
- [ ] PR-007 architecture tests remain green after PR-008 changes.

---

## 6. Architecture Rules

### 6.1 Bounded Context Compliance

- `core/` must not import from `rentsecure_be/`, `payments/`, or `notification/`.
- `properties/` must not import from `payments/` or `notification/` at module level.
- `documents/` must not import from `properties/` at module level.
- `payments/` must not import from `rentsecure_be/`.
- Payment SDKs (`razorpay`, `cashfree`) must only appear in `payments/adapters/`.

### 6.2 Import Rules

**Critical dependency matrix constraints per ADR-006 v1.1:**

| Source | shared | platform | identity | property | payment | notification | document |
|--------|--------|----------|----------|----------|---------|--------------|----------|
| **core** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **properties** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **payments** | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| **notification** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **documents** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Permitted patterns:**
- `core/` → `shared/` only
- `properties/` → `shared/` only
- `payments/` → `shared/`, `properties/`
- `notification/` → `shared/` only
- `documents/` → `shared/` only

**Forbidden patterns (must be eliminated in this PR):**
- `core/` → `rentsecure_be/`
- `payments/` → `rentsecure_be/`
- `properties/` → `rentsecure_be/`
- `core/` → `payments/` (direct SDK import)
- `properties/` → `payments/` (direct adapter/service imports)
- `documents/` → `properties/`

### 6.3 Lazy Import Rules

When module-level imports violate architecture rules, use lazy imports inside function/method bodies:

```python
def some_view_function(request):
    from payments.services.payment_service import PaymentService
    from payments.adapters.razorpay import RazorpayAdapter
    # ... use PaymentService and RazorpayAdapter
```

**Rules for lazy imports:**
1. Lazy imports must be inside function/method bodies, not at module level.
2. Lazy imports must preserve the original business behavior exactly.
3. Lazy imports must not introduce circular dependencies.
4. Test patch targets must be preserved (use module-level wrapper functions if needed).
5. Lazy imports are a transitional pattern only; they must not be used to bypass architecture rules permanently.

### 6.4 View Rules

- View files must not exceed 300 lines.
- If a view file exceeds 300 lines, extract helper functions into a separate module (e.g., `properties/views/rent_record_helpers.py`).
- Extracted helpers must not introduce new cross-app imports.
- Views must not import models from other apps at module level.

### 6.5 Model Rules

- Model files must not exceed 400 lines.
- If a model file exceeds 400 lines, extract mixins or proxy models into separate modules.
- Extracted mixins must be placed in the same app (e.g., `properties/models/mixins.py`).

### 6.6 SDK Rules

- Payment SDKs (`razorpay`, `cashfree`) must only appear in `payments/adapters/`.
- All SDK usage must be encapsulated in adapter classes.
- Other apps must interact with SDKs only through adapter interfaces.

### 6.7 Naming Rules

- Moved files retain original names unless conflict exists.
- Lazy-import wrapper functions must be named clearly (e.g., `create_payment_link()`, `process_rent_payout()`).
- Extracted helper modules must use `_helpers.py` or `_utils.py` suffix.

---

## 7. CI Requirements

### 7.1 Required CI Gates

All gates are **blocking**. PR cannot be merged if any gate fails.

| Gate | Tool | Threshold | Command |
|------|------|-----------|---------|
| Lint | Ruff | 0 errors | `ruff check .` |
| Format | Ruff | 0 issues | `ruff format --check .` |
| Type Check | MyPy | 0 errors | `mypy .` |
| Import Rules | import-linter | 0 violations | `lint-imports --config import-linter.ini` |
| Tests | Pytest | All pass | `pytest tests/ -v` |
| Architecture | pytest | 0 failures | `pytest tests/architecture/ -v` |
| Django Check | manage.py | 0 errors | `python manage.py check` |

### 7.2 Pipeline Order

```
Lint → Type Check → Import Rules → Tests → Architecture → Django Check
```

### 7.3 Phase-Specific Architecture Tests

| Test | Purpose | Expected Result |
|------|---------|-----------------|
| `test_rentsecure_be_boundary.py` | No app imports from `rentsecure_be/` | Pass |
| `test_sdk_placement.py` | Payment SDKs only in `payments/adapters/` | Pass |
| `test_properties_isolation.py` | `properties/` does not import from `payments/` | Pass |
| `test_documents_isolation.py` | `documents/` does not import from `properties/` | Pass |
| `test_core_isolation.py` | `core/` does not import from `payments/` or `rentsecure_be/` | Pass |
| `test_layer_compliance.py` | Views do not import models from other apps at module level | Pass |
| `test_god_views.py` | No view file exceeds 300 lines | Pass |
| `test_god_models.py` | No model file exceeds 400 lines | Pass |
| `test_circular_deps.py` | No circular dependencies between app packages | Pass |
| `test_shared_purity.py` | `shared/` does not import Django or apps | Pass |
| `test_import_rules.py` | `Notification.objects.create` stays in `notification/` | Pass |

---

## 8. Testing Strategy

### 8.1 Test Tiers Required

| Tier | Scope | Requirement |
|------|-------|-------------|
| **Unit** | Refactored view and service methods | No coverage requirement (behavior unchanged) |
| **Integration** | Existing API endpoints | All existing tests must pass |
| **Architecture** | Import boundaries, layer compliance, SDK placement, file size limits | 0 failures |
| **Regression** | Full test suite | No test failures |

### 8.2 Existing Test Preservation

All existing tests must continue to pass without modification. If test patch targets are affected by lazy imports:
- Preserve original patch targets by adding module-level wrapper functions.
- Example: If `properties/views/rent_record_views.py` previously had `from payments.services.payment_service import PaymentService` at module level, and tests patch `properties.views.rent_record_views.PaymentService`, add:
  ```python
  def _get_payment_service():
      from payments.services.payment_service import PaymentService
      return PaymentService
  ```
  And update tests to patch `properties.views.rent_record_views._get_payment_service`.

### 8.3 Architecture Tests

Run `pytest tests/architecture/ -v --tb=short` after all changes. All 640+ tests must pass.

### 8.4 Forbidden Test Patterns

- No `time.sleep()` in tests.
- No test dependencies on execution order.
- No hardcoded test data (use factories).
- No mocking Django ORM in migration tests (not applicable — no migrations in this PR).
- No direct database access in unit tests (use model methods or ORM).

---

## 9. Migration Strategy

### 9.1 Code Migration

This PR involves moving utility modules from `rentsecure_be/` to their respective bounded contexts:

1. **`rentsecure_be/utils/cashfree_payout.py` → `payments/utils/cashfree_payout.py`**
   - Move file to `payments/utils/cashfree_payout.py`.
   - Update all importers to use `payments.utils.cashfree_payout`.
   - Update `import-linter.ini` if needed.

2. **`rentsecure_be/services/leegality_service.py` → `properties/services/leegality_service.py`**
   - Move file to `properties/services/leegality_service.py`.
   - Update all importers to use `properties.services.leegality_service`.
   - Add deprecation shim in `rentsecure_be/services/leegality_service.py` if backward compatibility is required (not required for this PR — `rentsecure_be/` is internal).

3. **`rentsecure_be/services/cashfree_service.py` → `payments/services/cashfree_service.py`**
   - Move file to `payments/services/cashfree_service.py`.
   - Update all importers to use `payments.services.cashfree_service`.

4. **`rentsecure_be/services/razorpay_service.py` → `payments/services/razorpay_service.py`**
   - Move file to `payments/services/razorpay_service.py`.
   - Update all importers to use `payments.services.razorpay_service`.

### 9.2 Lazy Import Strategy

For files that cannot directly import from target bounded contexts due to dependency matrix constraints:

1. **`core/views/bank_views.py`** — Remove `import razorpay`. Add `create_order()` method to `payments/adapters/razorpay.py` and call it from `core/views/bank_views.py`.
2. **`properties/views/rent_record_views.py`** — Remove top-level `payments/` imports. Add module-level wrapper functions `create_payment_link()` and `process_rent_payout()` that use lazy imports inside function bodies.
3. **`documents/views.py`** and **`documents/utils.py`** — Remove top-level `properties/` imports. Use `django.apps.apps.get_model()` or lazy imports inside function bodies.

### 9.3 View/Model Refactoring Strategy

1. **`properties/views/unit_views.py` (358 lines → <300 lines)**
   - Extract helper functions into `properties/views/unit_helpers.py`.
   - Candidate functions: Leegality webhook handler, unit image/document logic.
   - Do not extract ViewSet classes — extract standalone functions only.

2. **`properties/models/unit_models.py` (482 lines → <400 lines)**
   - Extract mixins into `properties/models/mixins.py` or `properties/models/unit_mixins.py`.
   - Candidate mixins: `AddressMixin`, `AmenityMixin`, `ImageMixin`.
   - Do not change model inheritance hierarchy.

### 9.4 Circular Dependency Resolution

Circular dependencies must be resolved by:
1. Introducing interfaces in `shared/` (if not already present).
2. Using dependency injection or callback patterns.
3. Moving shared types to `shared/` package.
4. **Never** weakening architecture rules to accommodate circular dependencies.

### 9.5 Data Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Business behavior change | Low | High | All existing tests must pass; no serializer/model changes |
| Import regression | Medium | Medium | Architecture tests enforce import boundaries |
| Circular dependency introduced | Medium | High | `test_circular_deps.py` must pass |
| View/model file size not reduced | Low | Low | Verify line counts in CI |
| Test patch target broken | Medium | Low | Preserve patch targets via lazy-import wrappers |

---

## 10. Rollback Plan

### 10.1 Rollback Triggers

Rollback is triggered if any of the following occur:
- Any existing test fails after changes.
- `import-linter check` returns violations.
- Any architecture regression test fails.
- Business behavior changes detected (API responses differ).
- Circular dependencies introduced.
- CI pipeline cannot be fixed within 30 minutes.

### 10.2 Rollback Steps

1. **Git revert:**
   ```bash
   git revert <PR-008-merge-commit-sha>
   git push origin main
   ```
2. **Verify rollback:**
   ```bash
   pytest tests/ -v
   pytest tests/architecture/ -v
   lint-imports --config import-linter.ini
   ```
3. **Deploy reverted code** to staging, then production.
4. **Smoke tests:** Verify all API endpoints return expected responses.
5. **Notify team:** Post rollback completion notice with root cause and fix plan.

### 10.3 Estimated Rollback Time

**15 minutes** (git revert + deploy + smoke tests).

### 10.4 Data Risk

**None.** This PR does not modify database schema or data.

### 10.5 Rollback Validation

- Rollback must be tested on staging before production deploy.
- Test sequence:
  1. Apply PR-008 to staging.
  2. Verify all architecture tests pass.
  3. Execute rollback steps 1-4 above.
  4. Verify all existing tests still pass.
  5. Verify `import-linter check` passes.
  6. Re-apply PR-008 after successful rollback test.

---

## 11. Expected Git Diff

### 11.1 Summary

| Metric | Value |
|--------|-------|
| Files changed | ~15 (12 modified, 3 deleted, 4 new) |
| Files added | ~4 |
| Files modified | ~12 |
| Files deleted | ~4 |
| Lines added | ~400 |
| Lines removed | ~200 |
| Net change | ~200 lines |

### 11.2 Files Added (~100 lines)

| File | Approx Lines | Description |
|------|---------------|-------------|
| `payments/utils/cashfree_payout.py` | ~50 | Moved from `rentsecure_be/utils/` |
| `properties/services/leegality_service.py` | ~60 | Moved from `rentsecure_be/services/` |
| `payments/services/cashfree_service.py` | ~30 | Moved from `rentsecure_be/services/` |
| `payments/services/razorpay_service.py` | ~15 | Moved from `rentsecure_be/services/` |

### 11.3 Files Modified (~400 lines)

| File | Approx Lines Changed | Description |
|------|----------------------|-------------|
| `core/services/bank_details_service.py` | +10, -5 | Remove `rentsecure_be/` import; use lazy import or delegate |
| `core/views/bank_views.py` | +5, -5 | Remove `import razorpay`; use `RazorpayAdapter().create_order()` |
| `payments/adapters/cashfree.py` | +5, -5 | Update imports from `payments.utils.cashfree_payout` |
| `payments/adapters/razorpay.py` | +15, -0 | Add `create_order()` method |
| `properties/views/unit_views.py` | +10, -50 | Remove `rentsecure_be/` import; reduce line count |
| `properties/views/rent_record_views.py` | +20, -15 | Remove top-level `payments/` imports; add lazy-import wrappers |
| `documents/views.py` | +10, -10 | Remove `properties/` imports; use `apps.get_model()` |
| `documents/utils.py` | +5, -5 | Remove `properties/` imports; use `apps.get_model()` |
| `import-linter.ini` | +5, -0 | Verify configuration (minor updates if needed) |
| `.github/workflows/architecture.yml` | +0, -0 | No changes (already updated in PR-007) |
| `.github/workflows/ci.yml` | +0, -0 | No changes (already updated in PR-007) |

### 11.4 Diff Constraints

- No file in the diff may exceed 400 lines total after modification.
- No database migrations.
- No model field changes.
- No serializer changes.
- No API endpoint changes.
- No business logic changes.

---

## 12. Definition of Done

PR-008 is **Done** when ALL of the following are true.

### Code
- [ ] All `rentsecure_be/` imports removed from application code.
- [ ] All direct payment SDK imports outside `payments/adapters/` removed.
- [ ] `properties/` → `payments/` forbidden imports resolved.
- [ ] `documents/` → `properties/` forbidden imports resolved.
- [ ] `core/views/bank_views.py` delegates to `payments/adapters/razorpay.py`.
- [ ] `properties/views/unit_views.py` is under 300 lines.
- [ ] `properties/models/unit_models.py` is under 400 lines.
- [ ] No circular dependencies between app packages.
- [ ] All view files comply with layer compliance rules.

### Tests
- [ ] All existing tests pass (no regressions).
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `lint-imports --config import-linter.ini` passes with 0 violations.
- [ ] No test patch targets broken by lazy imports.

### CI
- [ ] `ruff check .` passes (0 errors).
- [ ] `ruff format --check .` passes.
- [ ] `mypy .` passes (0 errors).
- [ ] `import-linter check` passes (0 violations).
- [ ] `pytest tests/ -v` passes.
- [ ] `pytest tests/architecture/ -v` passes.
- [ ] `python manage.py check` passes.

### Architecture
- [ ] No `rentsecure_be/` imports in new/modified files.
- [ ] No payment SDK imports outside `payments/adapters/`.
- [ ] No `properties/` → `payments/` imports at module level.
- [ ] No `documents/` → `properties/` imports at module level.
- [ ] No circular dependencies.
- [ ] No view file exceeds 300 lines.
- [ ] No model file exceeds 400 lines.
- [ ] `import-linter.ini` matches ADR-006 v1.1 matrix.

### Documentation
- [ ] `docs/architecture/contexts/*.md` updated if bounded context ownership changes.
- [ ] ADR-006 updated if dependency matrix changes (should not change in this PR).
- [ ] CHANGELOG.md updated.

### Deployment
- [ ] PR approved by Platform Team Lead and Staff Engineer.
- [ ] Merged to `phase-0-foundation` branch.
- [ ] Deployed to staging.
- [ ] Staging validation passed (24 hours).
- [ ] No production incidents during staging validation.

---

## 13. Developer Checklist

### Pre-Implementation
- [ ] Verify PR-007 is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes (baseline).
- [ ] Verify `lint-imports --config import-linter.ini` passes (baseline).
- [ ] Run `pytest tests/ -v` and verify all pass (baseline).
- [ ] Catalog all violations detected by PR-007 architecture tests.
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Import Rules, Dependency Rules, Files AI Must Never Modify Automatically.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Refactoring Rules.
- [ ] Confirm no database migrations are needed.
- [ ] Confirm no model/serializer/API changes are needed.

### Implementation
- [ ] Move `rentsecure_be/utils/cashfree_payout.py` → `payments/utils/cashfree_payout.py`.
- [ ] Move `rentsecure_be/services/leegality_service.py` → `properties/services/leegality_service.py`.
- [ ] Move `rentsecure_be/services/cashfree_service.py` → `payments/services/cashfree_service.py`.
- [ ] Move `rentsecure_be/services/razorpay_service.py` → `payments/services/razorpay_service.py`.
- [ ] Update all importers of moved files.
- [ ] Remove `rentsecure_be/` imports from `core/services/bank_details_service.py`.
- [ ] Remove `razorpay` SDK import from `core/views/bank_views.py`; delegate to `payments/adapters/razorpay.py`.
- [ ] Remove top-level `payments/` imports from `properties/views/rent_record_views.py`; add lazy-import wrappers.
- [ ] Remove `properties/` imports from `documents/views.py` and `documents/utils.py`; use `apps.get_model()` or lazy imports.
- [ ] Refactor `properties/views/unit_views.py` to reduce line count below 300.
- [ ] Refactor `properties/models/unit_models.py` to reduce line count below 400.
- [ ] Resolve circular dependency chains between app packages.

### Testing
- [ ] Run `pytest tests/ -v` and verify all pass.
- [ ] Run `pytest tests/architecture/ -v` and verify 0 failures.
- [ ] Run `lint-imports --config import-linter.ini` and verify 0 violations.
- [ ] Run `python manage.py check` and verify 0 errors.
- [ ] Run `ruff check .` and verify 0 errors.
- [ ] Run `ruff format --check .` and verify 0 issues.
- [ ] Run `mypy .` and verify 0 errors.
- [ ] Verify no `print()` statements in new code.
- [ ] Verify no `# TODO` or `# FIXME` comments.
- [ ] Verify no commented-out code.
- [ ] Verify no hardcoded secrets.

### Validation
- [ ] Verify no `rentsecure_be/` imports remain in application code.
- [ ] Verify no payment SDK imports outside `payments/adapters/`.
- [ ] Verify no `properties/` → `payments/` imports at module level.
- [ ] Verify no `documents/` → `properties/` imports at module level.
- [ ] Verify no circular dependencies.
- [ ] Verify view files are under 300 lines.
- [ ] Verify model files are under 400 lines.
- [ ] Verify `import-linter.ini` matches ADR-006 v1.1.

### Rollback
- [ ] Document rollback plan in PR description.
- [ ] Test rollback on staging: apply PR-008, verify architecture tests pass, execute rollback, verify all tests still pass.

### PR
- [ ] Commit message follows conventional commits format.
- [ ] Branch name follows `<type>/<ticket-id>-<description>` format.
- [ ] PR description includes: summary, motivation, changes, testing, rollback plan.
- [ ] PR is linked to Phase 0 Architecture Cleanup task.

---

## 14. Reviewer Checklist

Use this checklist when reviewing PR-008.

### Architecture
- [ ] No `rentsecure_be/` imports in new/modified files.
- [ ] No payment SDK imports outside `payments/adapters/`.
- [ ] No `properties/` → `payments/` imports at module level.
- [ ] No `documents/` → `properties/` imports at module level.
- [ ] No circular dependencies introduced.
- [ ] No view file exceeds 300 lines.
- [ ] No model file exceeds 400 lines.
- [ ] `import-linter.ini` matches ADR-006 v1.1 matrix.
- [ ] All architecture tests pass.
- [ ] No architecture rules weakened.

### Code Quality
- [ ] Ruff passes (0 errors, 0 formatting issues).
- [ ] MyPy passes (0 errors).
- [ ] No `print()` statements.
- [ ] No `# TODO` or `# FIXME` comments.
- [ ] No commented-out code.
- [ ] Lazy imports are inside function bodies, not at module level.
- [ ] Business behavior is preserved (no logic changes).

### Testing
- [ ] All existing tests pass (no regressions).
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `lint-imports --config import-linter.ini` passes with 0 violations.
- [ ] No test patch targets broken.
- [ ] No new test files added (only architecture tests in `tests/architecture/`).

### CI
- [ ] All CI gates pass.
- [ ] No import-linter violations.
- [ ] No architecture test failures.
- [ ] No circular dependency warnings.

### Documentation
- [ ] CHANGELOG.md updated.
- [ ] PR description includes summary of violations fixed.
- [ ] No ADR changes required (dependency matrix unchanged).

---

## 15. AI Checklist

Use this checklist when generating PR-008 with AI assistance.

### Pre-Generation
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Import Rules, Dependency Rules, Refactoring Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Refactoring Rules, Files AI Must Never Modify Automatically.
- [ ] Verify PR-007 is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes on baseline.
- [ ] Verify `lint-imports --config import-linter.ini` passes on baseline.
- [ ] Catalog all violations from PR-007 architecture tests.
- [ ] Confirm no database migrations are needed.
- [ ] Confirm no model/serializer/API changes are needed.

### Code Generation
- [ ] Move `rentsecure_be/utils/cashfree_payout.py` → `payments/utils/cashfree_payout.py`.
- [ ] Move `rentsecure_be/services/leegality_service.py` → `properties/services/leegality_service.py`.
- [ ] Move `rentsecure_be/services/cashfree_service.py` → `payments/services/cashfree_service.py`.
- [ ] Move `rentsecure_be/services/razorpay_service.py` → `payments/services/razorpay_service.py`.
- [ ] Update all importers of moved files.
- [ ] Remove `rentsecure_be/` imports from `core/services/bank_details_service.py`.
- [ ] Remove `razorpay` SDK import from `core/views/bank_views.py`; delegate to `payments/adapters/razorpay.py`.
- [ ] Remove top-level `payments/` imports from `properties/views/rent_record_views.py`; add lazy-import wrappers.
- [ ] Remove `properties/` imports from `documents/views.py` and `documents/utils.py`; use `apps.get_model()` or lazy imports.
- [ ] Refactor `properties/views/unit_views.py` to reduce line count below 300.
- [ ] Refactor `properties/models/unit_models.py` to reduce line count below 400.
- [ ] Resolve circular dependency chains between app packages.
- [ ] **Do NOT** modify business logic in any view, service, or model.
- [ ] **Do NOT** add database migrations.
- [ ] **Do NOT** change model fields or serializers.
- [ ] **Do NOT** change API endpoints or contracts.
- [ ] **Do NOT** introduce new features.

### Test Generation
- [ ] No new test files required (existing tests must pass unchanged).
- [ ] If test patch targets are affected by lazy imports, add module-level wrapper functions to preserve targets.
- [ ] Run `pytest tests/ -v` and verify all pass.
- [ ] Run `pytest tests/architecture/ -v` and verify 0 failures.
- [ ] Run `lint-imports --config import-linter.ini` and verify 0 violations.

### Validation
- [ ] Run `ruff check .` and fix all errors.
- [ ] Run `ruff format --check .` and fix all issues.
- [ ] Run `mypy .` and fix all errors.
- [ ] Run `import-linter check` and verify 0 violations.
- [ ] Run `pytest tests/ -v` and verify all pass.
- [ ] Run `pytest tests/architecture/ -v` and verify 0 failures.
- [ ] Run `python manage.py check` and verify 0 errors.
- [ ] Verify no `print()` statements in new code.
- [ ] Verify no `# TODO` or `# FIXME` comments.
- [ ] Verify no commented-out code.
- [ ] Verify no hardcoded secrets.
- [ ] Verify no `from rentsecure_be.X import Y` in new/modified files.
- [ ] Verify no payment SDK imports outside `payments/adapters/`.
- [ ] Verify no circular dependencies.
- [ ] Verify view files are under 300 lines.
- [ ] Verify model files are under 400 lines.

### Stop and Ask Conditions
AI must **stop and ask human** before proceeding if:
- [ ] Any required change would modify business logic, model fields, serializers, or API contracts.
- [ ] Any required change would need a database migration.
- [ ] Circular dependency cannot be resolved without weakening architecture rules.
- [ ] `properties/views/rent_record_views.py` or `documents/views.py` requires cross-app imports that cannot be resolved via lazy imports or delegation.
- [ ] `core/views/bank_views.py` must import from `payments/` and delegation to `RazorpayAdapter` is insufficient.
- [ ] View or model file cannot be reduced below size limit without extracting core business logic.
- [ ] Any CI gate fails after 3 fix attempts.
- [ ] Existing tests fail and cannot be fixed without changing test expectations.

### Commit
- [ ] Commit message follows format: `refactor(architecture): remove rentsecure_be and SDK imports; fix layer compliance`.
- [ ] Commit body explains: violations fixed, files moved, lazy imports added, view/model refactoring approach.
- [ ] Branch name: `refactor/phase-0-008-architecture-cleanup-1`.

---

## 16. Stop-and-Ask Conditions

STOP and ask the Principal Software Architect if:

1. Any required fix would change business behavior, model definitions, serializers, or API contracts.
2. Any required fix would need a database migration.
3. Circular dependency cannot be resolved without introducing an ADR exception.
4. `properties/views/rent_record_views.py` requires module-level `payments/` imports that cannot be deferred to lazy imports.
5. `documents/views.py` or `documents/utils.py` requires `properties/` imports that cannot be resolved via `apps.get_model()` or lazy imports.
6. `core/views/bank_views.py` must import from `payments/` and delegation to `payments/adapters/razorpay.py` is insufficient.
7. View or model file cannot be reduced below size limit without extracting business logic.
8. Any existing test fails and cannot be fixed without changing test expectations.
9. `rentsecure_be/` compatibility shims are required for external consumers (not in scope for this PR).
10. Any CI gate fails after 3 fix attempts.

---

## Appendix A: Architecture Decision References

| Decision | Reference |
|----------|-----------|
| No app may import from `rentsecure_be/` | ADR-006 v1.1 §5.1 Rule 1 |
| `payment/` may import from `property/` | ADR-006 v1.1 §5.1 Rule 2 |
| `notification/` may NOT import from `property/` | ADR-006 v1.1 §5.1 Rule 3 |
| Payment SDKs confined to `payments/adapters/` | ADR-006 v1.1 §5.4 |
| No view file exceeds 300 lines | ADR-006 v1.1 §5.3 |
| No model file exceeds 400 lines | ADR-006 v1.1 §5.3 |
| `core/` cannot import from `payment/` | ADR-006 v1.1 dependency matrix |
| `properties/` cannot import from `payment/` | ADR-006 v1.1 dependency matrix |
| `documents/` cannot import from `properties/` | ADR-006 v1.1 dependency matrix |
| Lazy imports as transitional pattern | ADR-006 v1.1 §5.3 |
| Architecture tests enforce all rules | ADR-006 v1.1 §5.2 |

---

## Appendix B: Related Documents

- [Architecture v1.1 Release Candidate](../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Architecture v1.1 Implementation Master Plan — Phase 0](../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan — PR-008](../PHASE_0_EXECUTION_PLAN.md)
- [Engineering Standards](../ENGINEERING_STANDARDS.md)
- [AI Engineering Playbook](../AI_ENGINEERING_PLAYBOOK.md)
- [Import Rules ADR](../docs/architecture/adr/ADR-006_import_rules.md)
- [Payment Architecture ADR](../docs/architecture/adr/ADR-004_payment_architecture.md)
- [Shared Kernel Rules ADR](../docs/architecture/adr/ADR-005_shared_kernel_rules.md)

---

## Appendix C: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-20 | Principal Software Architect | Initial PR-008 specification for Architecture Cleanup Phase 1 |

**Next Review:** After PR-008 merge
**Approval Required:** Platform Team Lead, Staff Engineer

---

*End of PR-008 Implementation Specification*
