# PR-008A Implementation Specification

## Remove remaining rentsecure_be imports

---

## 1. Purpose

Execute the first bounded-context cleanup by moving all remaining utility and service modules out of the legacy `rentsecure_be/` package into their owning bounded contexts. This eliminates the last cross-context `rentsecure_be/` imports from application code and establishes the correct ownership boundary for each module.

This PR is **blocked until PR-007 is merged** because:
1. Architecture regression tests in `tests/architecture/` must exist to detect violations
2. `import-linter.ini` must enforce the v1.1 dependency matrix
3. All violations must be catalogued by the new architecture tests before fixing

---

## 2. Scope

### 2.1 In Scope

- Move `rentsecure_be/utils/cashfree_payout.py` → `payments/utils/cashfree_payout.py`
- Move `rentsecure_be/services/leegality_service.py` → `properties/services/leegality_service.py`
- Move `rentsecure_be/services/cashfree_service.py` → `payments/services/cashfree_service.py`
- Move `rentsecure_be/services/razorpay_service.py` → `payments/services/razorpay_service.py`
- Update all application-code importers of the moved modules **except** `core/services/bank_details_service.py`
- Remove the now-empty legacy files from `rentsecure_be/`
- Verify `import-linter check` passes with 0 violations
- Verify `pytest tests/architecture/ -v` passes with 0 failures

### 2.2 Out of Scope

- `core/services/bank_details_service.py` — **deferred to PR-008C** (see §2.3)
- Any changes to business logic, model definitions, or serializer definitions
- Any database migrations or schema changes
- Any API endpoint changes or new endpoints
- SDK isolation work (PR-008B)
- Cross-context import fixes between `properties/` ↔ `payments/` and `documents/` ↔ `properties/` (PR-008C)
- God view/model splitting (PR-008D)
- Circular dependency resolution (PR-008E)
- Final architecture compliance verification (PR-008F)
- Any changes to `core/views/bank_views.py` SDK imports
- Any changes to `properties/views/rent_record_views.py`
- Any changes to `documents/views.py` or `documents/utils.py`
- Any changes to `shared/` package structure

### 2.3 Deferred Items

#### `core/services/bank_details_service.py` — Approved Deferred Architecture Violation

**Status:** Deferred to PR-008C
**Reason:** Hard dependency-matrix conflict with no permissible resolution under current rules.

**Why this cannot be fixed in PR-008A:**

`core/services/bank_details_service.py` currently imports `add_beneficiary` from `rentsecure_be/utils/cashfree_payout`. After PR-008A moves that utility to `payments/utils/cashfree_payout.py`, the correct new import path would be `from payments.utils.cashfree_payout import add_beneficiary`.

However, ADR-006 v1.1 explicitly prohibits `core/` → `payments/` imports at module level. The dependency matrix is:

| Source | shared | platform | identity | property | payment | notification | document |
|--------|--------|----------|----------|----------|---------|--------------|----------|
| **core** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

`core/` may only import from `shared/`. A direct module-level import from `payments/` would violate this rule.

**Why lazy imports are not an acceptable workaround here:**

The implementation rules for this task explicitly prohibit `__import__()`, `importlib`, or lazy runtime imports merely to satisfy architecture rules. Lazy imports are a transitional pattern for cases where runtime deferral is genuinely required for circular-dependency or initialization-order reasons. In this case, the `core/` → `payments/` dependency is a hard architectural boundary that must be resolved through structural refactoring, not import indirection.

**What PR-008C must do instead:**

PR-008C must resolve this through cross-context refactoring, such as:
- Moving `BankDetailsService` out of `core/` into `payments/` or a shared location
- Introducing a callback or interface in `shared/` that `core/` can call without importing from `payments/`
- Redesigning the beneficiary-registration flow so that `core/` no longer needs to call payout utilities directly

This is not an import-replacement task. It is a bounded-context responsibility reassignment. Attempting to paper over it with a lazy import would leave a latent architectural violation that would still fail `test_layer_compliance.py` and `import-linter check` once the lazy-import transitional period ends.

**Interim state after PR-008A:**

`core/services/bank_details_service.py` retains its existing `from rentsecure_be.utils.cashfree_payout import add_beneficiary` import. The `rentsecure_be/utils/cashfree_payout.py` file **cannot** be deleted because `core/services/bank_details_service.py` is a live importer. The `rentsecure_be` boundary test will continue to flag this import until PR-008C resolves the underlying cross-context responsibility issue.

**No import-linter exception is added.** The violation remains visible and tracked as a deferred item, not a waived rule.

---

## 3. Files

### 3.1 Files to Create

| File | Purpose | Owner |
|------|---------|-------|
| `payments/utils/cashfree_payout.py` | Move `cashfree_payout` utilities from `rentsecure_be/utils/` to `payments/utils/` | Platform Team |
| `properties/services/leegality_service.py` | Move `leegality_service` from `rentsecure_be/services/` to `properties/services/` | Platform Team |
| `payments/services/cashfree_service.py` | Move `cashfree_service` compatibility wrapper from `rentsecure_be/services/` to `payments/services/` | Platform Team |
| `payments/services/razorpay_service.py` | Move `razorpay_service` compatibility wrapper from `rentsecure_be/services/` to `payments/services/` | Platform Team |

### 3.2 Files to Modify

| File | Change | Owner |
|------|--------|-------|
| `payments/adapters/cashfree.py` | Remove `from rentsecure_be.utils.cashfree_payout import ...`; update to `from payments.utils.cashfree_payout import ...` | Platform Team |
| `properties/views/unit_views.py` | Remove `from rentsecure_be.services.leegality_service import ...`; update to `from properties.services.leegality_service import ...` | Platform Team |
| `payments/services/__init__.py` | Add package marker if missing | Platform Team |
| `properties/services/__init__.py` | Add package marker if missing | Platform Team |
| `payments/utils/__init__.py` | Add package marker if missing | Platform Team |

### 3.3 Files Explicitly NOT Modified in PR-008A

| File | Reason | Owner |
|------|--------|-------|
| `core/services/bank_details_service.py` | Deferred to PR-008C — `core/` → `payments/` dependency-matrix conflict requires cross-context refactoring, not import replacement | Platform Team |

### 3.4 Files to Delete

| File | Reason | Owner |
|------|--------|-------|
| `rentsecure_be/utils/cashfree_payout.py` | **Cannot be deleted** — `core/services/bank_details_service.py` is a live importer (deferred to PR-008C) | Platform Team |
| `rentsecure_be/services/leegality_service.py` | Moved to `properties/services/leegality_service.py` | Platform Team |
| `rentsecure_be/services/cashfree_service.py` | **Cannot be deleted** — still imported by out-of-scope application code (`core/views.py`, `properties/views/rent_record_views.py`, `smartbot/actions.py`, management commands, communication modules) | Platform Team |
| `rentsecure_be/services/razorpay_service.py` | **Cannot be deleted** — still imported by out-of-scope application code (`properties/views/rent_record_views.py`, `properties/communication/auto_generate_rent_records.py`) | Platform Team |

---

## 4. Responsibilities

| Role | Responsibility |
|------|----------------|
| **Platform Team Lead** | Approves file moves; verifies no business behavior changes; owns PR merge |
| **Staff Engineer** | Reviews dependency matrix compliance; verifies no new violations introduced |
| **Developer** | Moves files, updates importers, runs full validation |
| **AI Assistant** | Generates moved files and import updates per this spec; stops and asks if business behavior changes are required |

---

## 5. Acceptance Criteria

### 5.1 Functional

- [ ] `payments/utils/cashfree_payout.py` exists with identical content to the original `rentsecure_be/utils/cashfree_payout.py`.
- [ ] `properties/services/leegality_service.py` exists with identical content to the original `rentsecure_be/services/leegality_service.py`.
- [ ] `payments/services/cashfree_service.py` exists with identical content to the original `rentsecure_be/services/cashfree_service.py`.
- [ ] `payments/services/razorpay_service.py` exists with identical content to the original `rentsecure_be/services/razorpay_service.py`.
- [ ] All application-code importers of moved modules reference the new locations.
- [ ] `core/services/bank_details_service.py` **retains** its existing `rentsecure_be` import — deferred to PR-008C (see §2.3).
- [ ] `rentsecure_be/services/cashfree_service.py` **is retained** — still imported by out-of-scope application code.
- [ ] `rentsecure_be/services/razorpay_service.py` **is retained** — still imported by out-of-scope application code.
- [ ] `rentsecure_be/utils/cashfree_payout.py` **is retained** — `core/services/bank_details_service.py` is a live importer.
- [ ] No new `rentsecure_be/` imports are introduced in modified files.
- [ ] `import-linter check` passes with 0 violations.
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] All existing tests continue to pass (no behavioral regressions).

### 5.2 Non-Functional

- [ ] No business behavior changes (all existing tests pass).
- [ ] No database migrations required.
- [ ] No model field changes.
- [ ] No serializer changes.
- [ ] No API contract changes.
- [ ] PR-007 architecture tests remain green after PR-008A changes.

---

## 6. Architecture Rules

### 6.1 Bounded Context Compliance

- `payments/` owns all Cashfree utilities and service wrappers.
- `properties/` owns all property-specific external service integrations (e.g., Leegality).
- `rentsecure_be/` is a legacy compatibility layer. No application code outside `rentsecure_be/` may import from it.
- Moved files must be placed in the bounded context that logically owns the functionality.

### 6.2 Import Rules

**Critical dependency matrix constraints per ADR-006 v1.1:**

| Source | shared | platform | identity | property | payment | notification | document |
|--------|--------|----------|----------|----------|---------|--------------|----------|
| **core** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **properties** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **payments** | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| **notification** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **documents** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Permitted import paths for PR-008A:**
- `payments/adapters/cashfree.py` → `payments/utils/cashfree_payout.py` (allowed — same bounded context)
- `properties/views/unit_views.py` → `properties/services/leegality_service.py` (allowed — same bounded context)

**Deferred violation — `core/services/bank_details_service.py`:**

`core/` **cannot** import from `payments/` per the dependency matrix. After moving `cashfree_payout` to `payments/utils/`, `core/services/bank_details_service.py` cannot be updated to `from payments.utils.cashfree_payout import ...` without violating ADR-006 v1.1.

This is **not** resolved via lazy imports. Lazy imports are explicitly prohibited as a workaround for hard dependency-matrix boundaries. The correct resolution is cross-context refactoring (e.g., moving `BankDetailsService` to `payments/`, introducing a `shared/` interface, or redesigning the beneficiary-registration flow). That work is deferred to PR-008C.

**Interim state:** `core/services/bank_details_service.py` retains its existing `from rentsecure_be.utils.cashfree_payout import add_beneficiary` import. The legacy `rentsecure_be/utils/cashfree_payout.py` file is retained as a live dependency. This is an **approved deferred architecture violation** — it is not waived, not hidden, and does not result in an `import-linter` exception.

### 6.3 Module Rules

- Moved files must retain their original public API (function signatures, class names, constants).
- Moved files must not contain business logic changes — only import path updates in callers.
- `rentsecure_be/` legacy files must be deleted after all importers are updated.
- If a moved file is imported by tests, update test import paths as well.

### 6.4 Naming Rules

- Moved files retain original names unless a naming conflict exists in the target directory.
- Package markers (`__init__.py`) must be added to target packages if they do not already exist.

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
| Tests | Pytest | All pass | `pytest tests/ -v` |
| Architecture | pytest | 0 failures | `pytest tests/architecture/ -v` |
| Django Check | manage.py | 0 errors | `python manage.py check` |

### 7.2 Pipeline Order

```
Lint → Type Check → Import Rules → Tests → Architecture → Django Check
```

### 7.3 Phase-Specific Architecture Tests

| Test | Purpose | Expected Result |
|------|---------|----------------|
| `test_rentsecure_be_boundary.py` | No app imports from `rentsecure_be/` outside `rentsecure_be/` itself | Pass |
| `test_sdk_placement.py` | Payment SDKs only in `payments/adapters/` | Pass |
| `test_layer_compliance.py` | Views do not import models from other apps at module level | Pass |
| `test_circular_deps.py` | No circular dependencies between app packages | Pass |
| `test_shared_purity.py` | `shared/` does not import Django or apps | Pass |
| `test_import_rules.py` | No forbidden imports in new/modified files | Pass |

---

## 8. Testing Strategy

### 8.1 Test Tiers Required

| Tier | Scope | Requirement |
|------|-------|-------------|
| **Unit** | Moved modules | No coverage requirement (behavior unchanged) |
| **Integration** | Existing API endpoints that use moved modules | All existing tests must pass |
| **Architecture** | Import boundaries, rentsecure_be boundary | 0 failures |
| **Regression** | Full test suite | No test failures |

### 8.2 Existing Test Preservation

All existing tests must continue to pass without modification. If test patch targets reference the old import paths:
- Update test imports to reference the new module locations.
- Example: If tests patch `rentsecure_be.utils.cashfree_payout.add_beneficiary`, update to patch `payments.utils.cashfree_payout.add_beneficiary`.

### 8.3 Architecture Tests

Run `pytest tests/architecture/ -v --tb=short` after all changes. All tests must pass.

### 8.4 Forbidden Test Patterns

- No `time.sleep()` in tests.
- No test dependencies on execution order.
- No hardcoded test data (use factories).
- No mocking Django ORM in migration tests (not applicable — no migrations in this PR).
- No direct database access in unit tests (use model methods or ORM).

---

## 9. Migration Strategy

### 9.1 Code Migration

Move files atomically within a single PR to minimize intermediate broken states:

1. **Create target files** in their new locations with identical content.
2. **Update all importers** across the codebase to reference new locations.
3. **Delete legacy files** from `rentsecure_be/`.
4. **Run tests** to verify no import errors.

### 9.2 Importer Update Order

Update importers in this order to avoid circular import issues:
1. `payments/adapters/cashfree.py` (self-contained)
2. `properties/views/unit_views.py` (self-contained)

**Not updated in PR-008A:**
- `core/services/bank_details_service.py` — **deferred to PR-008C** due to `core/` → `payments/` dependency-matrix conflict (see §2.3)

### 9.3 Deferred Import — core/services/bank_details_service.py

`core/services/bank_details_service.py` currently imports `add_beneficiary` from `rentsecure_be.utils.cashfree_payout`. This import **cannot be changed in PR-008A** because:

1. ADR-006 v1.1 prohibits `core/` → `payments/` imports at module level.
2. The implementation rules explicitly prohibit lazy runtime imports (`__import__()`, `importlib`, function-body lazy imports) as a workaround for hard dependency-matrix boundaries.
3. The correct resolution requires cross-context refactoring (e.g., moving `BankDetailsService` to `payments/`, introducing a `shared/` interface, or redesigning the beneficiary-registration flow).

**Interim state:** `core/services/bank_details_service.py` retains its existing import. The legacy `rentsecure_be/utils/cashfree_payout.py` file is retained. This is an **approved deferred architecture violation** tracked for PR-008C.

**No import-linter exception is added.** The violation remains visible in architecture tests until PR-008C resolves the underlying structural issue.

### 9.4 Data Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Business behavior change | Low | High | All existing tests must pass; no logic changes |
| Import regression | Medium | Medium | Architecture tests enforce import boundaries |
| Circular dependency introduced | Low | Medium | `test_circular_deps.py` must pass |
| Test patch target broken | Medium | Low | Update test imports to new locations |

---

## 10. Rollback Plan

### 10.1 Rollback Triggers

Rollback is triggered if any of the following occur:
- Any existing test fails after changes.
- `import-linter check` returns violations.
- Any architecture regression test fails.
- Business behavior changes detected (API responses differ).
- CI pipeline cannot be fixed within 30 minutes.

### 10.2 Rollback Steps

1. **Git revert:**
   ```bash
   git revert <PR-008A-merge-commit-sha>
   git push origin main
   ```
2. **Verify rollback:**
   ```bash
   pytest tests/ -v
   pytest tests/architecture/ -v
   import-linter check
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
   1. Apply PR-008A to staging.
   2. Verify all architecture tests pass.
   3. Execute rollback steps 1-4 above.
   4. Verify all existing tests still pass.
   5. Verify `import-linter check` passes.
   6. Re-apply PR-008A after successful rollback test.

---

## 11. Expected Git Diff

### 11.1 Summary

| Metric | Value |
|--------|-------|
| Files changed | ~5 (4 new, 2 modified, 1 deleted) |
| Files added | 4 |
| Files modified | 2 |
| Files deleted | 1 |
| Lines added | ~150 |
| Lines removed | ~15 |
| Net change | ~135 lines |

### 11.2 Files Added (~150 lines)

| File | Approx Lines | Description |
|------|---------------|-------------|
| `payments/utils/cashfree_payout.py` | ~50 | Moved from `rentsecure_be/utils/` |
| `properties/services/leegality_service.py` | ~60 | Moved from `rentsecure_be/services/` |
| `payments/services/cashfree_service.py` | ~30 | Moved from `rentsecure_be/services/` |
| `payments/services/razorpay_service.py` | ~15 | Moved from `rentsecure_be/services/` |
| `payments/utils/__init__.py` | ~1 | Package marker (if missing) |
| `payments/services/__init__.py` | ~1 | Package marker (if missing) |
| `properties/services/__init__.py` | ~1 | Package marker (if missing) |

### 11.3 Files Modified (~15 lines)

| File | Approx Lines Changed | Description |
|------|----------------------|-------------|
| `payments/adapters/cashfree.py` | +2, -2 | Update import path to `payments.utils.cashfree_payout` |
| `properties/views/unit_views.py` | +2, -2 | Update import path to `properties.services.leegality_service` |

### 11.4 Files Deleted (~15 lines)

| File | Approx Lines | Description |
|------|---------------|-------------|
| `rentsecure_be/services/leegality_service.py` | ~60 | Deleted after move — no remaining application-code importers |

### 11.5 Files Intentionally Retained

| File | Reason |
|------|--------|
| `rentsecure_be/utils/cashfree_payout.py` | `core/services/bank_details_service.py` is a live importer — deferred to PR-008C |
| `rentsecure_be/services/cashfree_service.py` | Still imported by out-of-scope application code (`core/views.py`, `properties/views/rent_record_views.py`, `smartbot/actions.py`, management commands, communication modules) |
| `rentsecure_be/services/razorpay_service.py` | Still imported by out-of-scope application code (`properties/views/rent_record_views.py`, `properties/communication/auto_generate_rent_records.py`) |

### 11.6 Files NOT Modified

| File | Reason |
|------|--------|
| `core/services/bank_details_service.py` | Deferred to PR-008C — `core/` → `payments/` dependency-matrix conflict |

### 11.7 Diff Constraints

- No file in the diff may exceed 400 lines total after modification.
- No database migrations.
- No model field changes.
- No serializer changes.
- No API endpoint changes.
- No business logic changes.

---

## 12. Definition of Done

PR-008A is **Done** when ALL of the following are true.

### Code
- [ ] `payments/utils/cashfree_payout.py` exists with identical content to the original.
- [ ] `properties/services/leegality_service.py` exists with identical content to the original.
- [ ] `payments/services/cashfree_service.py` exists with identical content to the original.
- [ ] `payments/services/razorpay_service.py` exists with identical content to the original.
- [ ] All application-code importers of moved modules reference the new locations.
- [ ] `core/services/bank_details_service.py` **retains** its existing `rentsecure_be` import — deferred to PR-008C.
- [ ] `rentsecure_be/services/cashfree_service.py` and `rentsecure_be/services/razorpay_service.py` are retained — still imported by out-of-scope code.
- [ ] `rentsecure_be/utils/cashfree_payout.py` is retained — `core/services/bank_details_service.py` is a live importer.
- [ ] No new `rentsecure_be/` imports are introduced in modified files.

### Tests
- [ ] All existing tests pass (no regressions).
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
- [ ] No test patch targets broken by import path changes.

### CI
- [ ] `ruff check .` passes (0 errors).
- [ ] `ruff format --check .` passes.
- [ ] `mypy .` passes (0 errors).
- [ ] `import-linter check` passes (0 violations).
- [ ] `pytest tests/ -v` passes.
- [ ] `pytest tests/architecture/ -v` passes.
- [ ] `python manage.py check` passes.

### Architecture
- [ ] No new `rentsecure_be/` imports introduced in modified files.
- [ ] No circular dependencies introduced.
- [ ] `import-linter.ini` matches ADR-006 v1.1 matrix.
- [ ] `core/` does not import from `payments/` at module level — `core/services/bank_details_service.py` deferred to PR-008C.
- [ ] Deferred architecture violation for `core/services/bank_details_service.py` is documented and tracked.

### Documentation
- [ ] `docs/architecture/contexts/*.md` updated if bounded context ownership changes.
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
- [ ] Verify `import-linter check` passes (baseline).
- [ ] Run `pytest tests/ -v` and verify all pass (baseline).
- [ ] Catalog all `rentsecure_be/` imports from PR-007 architecture tests.
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Import Rules, Dependency Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Refactoring Rules.
- [ ] Confirm `core/` cannot import from `payments/` per dependency matrix.
- [ ] Verify `payments/utils/`, `payments/services/`, and `properties/services/` packages exist.

### Implementation
- [ ] Create `payments/utils/cashfree_payout.py` with content from `rentsecure_be/utils/cashfree_payout.py`.
- [ ] Create `properties/services/leegality_service.py` with content from `rentsecure_be/services/leegality_service.py`.
- [ ] Create `payments/services/cashfree_service.py` with content from `rentsecure_be/services/cashfree_service.py`.
- [ ] Create `payments/services/razorpay_service.py` with content from `rentsecure_be/services/razorpay_service.py`.
- [ ] **Do NOT modify** `core/services/bank_details_service.py` — deferred to PR-008C.
- [ ] Update `payments/adapters/cashfree.py` — update import to `payments.utils.cashfree_payout`.
- [ ] Update `properties/views/unit_views.py` — update import to `properties.services.leegality_service`.
- [ ] Update any test files that reference moved modules.
- [ ] Add `__init__.py` to target packages if missing.
- [ ] Delete `rentsecure_be/services/leegality_service.py` — no remaining application-code importers.
- [ ] **Do NOT delete** `rentsecure_be/utils/cashfree_payout.py` — `core/services/bank_details_service.py` is a live importer.
- [ ] **Do NOT delete** `rentsecure_be/services/cashfree_service.py` — still imported by out-of-scope application code.
- [ ] **Do NOT delete** `rentsecure_be/services/razorpay_service.py` — still imported by out-of-scope application code.

### Testing
- [ ] Run `pytest tests/ -v` and verify all pass.
- [ ] Run `pytest tests/architecture/ -v` and verify 0 failures.
- [ ] Run `import-linter check` and verify 0 violations.
- [ ] Run `python manage.py check` and verify 0 errors.
- [ ] Run `ruff check .` and verify 0 errors.
- [ ] Run `ruff format --check .` and verify 0 issues.
- [ ] Run `mypy .` and verify 0 errors.
- [ ] Verify no `print()` statements in new code.
- [ ] Verify no `# TODO` or `# FIXME` comments.
- [ ] Verify no commented-out code.
- [ ] Verify no hardcoded secrets.
- [ ] Verify no `from rentsecure_be.X import Y` in new/modified files outside `rentsecure_be/`.

### Validation
- [ ] Verify `properties/services/leegality_service.py` is deleted from `rentsecure_be/`.
- [ ] Verify all importers of `leegality_service` reference `properties.services.leegality_service`.
- [ ] Verify `payments/adapters/cashfree.py` imports from `payments.utils.cashfree_payout`.
- [ ] Verify `properties/views/unit_views.py` imports from `properties.services.leegality_service`.
- [ ] Verify `core/services/bank_details_service.py` is **unchanged** — deferred to PR-008C.
- [ ] Verify `rentsecure_be/utils/cashfree_payout.py` is **retained** — live importer exists.
- [ ] Verify `rentsecure_be/services/cashfree_service.py` is **retained** — out-of-scope importers exist.
- [ ] Verify `rentsecure_be/services/razorpay_service.py` is **retained** — out-of-scope importers exist.
- [ ] Verify no circular dependencies introduced.

### Rollback
- [ ] Document rollback plan in PR description.
- [ ] Test rollback on staging: apply PR-008A, verify architecture tests pass, execute rollback, verify all tests still pass.

### PR
- [ ] Commit message follows conventional commits format.
- [ ] Branch name follows `<type>/<ticket-id>-<description>` format.
- [ ] PR description includes: summary, motivation, changes, testing, rollback plan.
- [ ] PR size is within limits (~0 net lines, 10 files).
- [ ] PR is linked to Phase 0 Architecture Cleanup task.

---

## 14. Reviewer Checklist

Use this checklist when reviewing PR-008A.

### Architecture
- [ ] All movable files moved to correct bounded-context locations.
- [ ] `properties/services/leegality_service.py` is deleted from `rentsecure_be/` — no remaining application-code importers.
- [ ] `core/services/bank_details_service.py` is **unchanged** — deferred violation documented in §2.3, resolved in PR-008C.
- [ ] `rentsecure_be/utils/cashfree_payout.py` is **retained** — `core/services/bank_details_service.py` is a live importer.
- [ ] `rentsecure_be/services/cashfree_service.py` is **retained** — out-of-scope importers exist.
- [ ] `rentsecure_be/services/razorpay_service.py` is **retained** — out-of-scope importers exist.
- [ ] No new `rentsecure_be/` imports introduced in modified files.
- [ ] No circular dependencies introduced.
- [ ] `import-linter.ini` matches ADR-006 v1.1 matrix.
- [ ] No import-linter exceptions added for deferred violations.
- [ ] All architecture tests pass.
- [ ] No architecture rules weakened.

### Code Quality
- [ ] Ruff passes (0 errors, 0 formatting issues).
- [ ] MyPy passes (0 errors).
- [ ] No `print()` statements.
- [ ] No `# TODO` or `# FIXME` comments.
- [ ] No commented-out code.
- [ ] Moved files retain original public API.
- [ ] Business behavior is preserved (no logic changes).

### Testing
- [ ] All existing tests pass (no regressions).
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
- [ ] No test patch targets broken.
- [ ] No new test files required.

### CI
- [ ] All CI gates pass.
- [ ] No import-linter violations.
- [ ] No architecture test failures.
- [ ] No circular dependency warnings.

### Documentation
- [ ] CHANGELOG.md updated.
- [ ] PR description includes summary of files moved and importers updated.

---

## 15. AI Checklist

Use this checklist when generating PR-008A with AI assistance.

### Pre-Generation
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Import Rules, Dependency Rules, Refactoring Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Refactoring Rules, Files AI Must Never Modify Automatically.
- [ ] Verify PR-007 is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes on baseline.
- [ ] Verify `import-linter check` passes on baseline.
- [ ] Catalog all `rentsecure_be/` imports from PR-007 architecture tests.
- [ ] Confirm `core/` cannot import from `payments/` per dependency matrix.
- [ ] Verify `payments/utils/`, `payments/services/`, and `properties/services/` packages exist.

### Code Generation
- [ ] Move `rentsecure_be/utils/cashfree_payout.py` → `payments/utils/cashfree_payout.py`.
- [ ] Move `rentsecure_be/services/leegality_service.py` → `properties/services/leegality_service.py`.
- [ ] Move `rentsecure_be/services/cashfree_service.py` → `payments/services/cashfree_service.py`.
- [ ] Move `rentsecure_be/services/razorpay_service.py` → `payments/services/razorpay_service.py`.
- [ ] **Do NOT modify** `core/services/bank_details_service.py` — deferred to PR-008C due to dependency-matrix conflict.
- [ ] Update `payments/adapters/cashfree.py` — update import to `payments.utils.cashfree_payout`.
- [ ] Update `properties/views/unit_views.py` — update import to `properties.services.leegality_service`.
- [ ] Update any test files referencing moved modules.
- [ ] Add `__init__.py` to target packages if missing.
- [ ] Delete `rentsecure_be/services/leegality_service.py` — no remaining application-code importers.
- [ ] **Do NOT delete** `rentsecure_be/utils/cashfree_payout.py` — `core/services/bank_details_service.py` is a live importer.
- [ ] **Do NOT delete** `rentsecure_be/services/cashfree_service.py` — out-of-scope importers exist.
- [ ] **Do NOT delete** `rentsecure_be/services/razorpay_service.py` — out-of-scope importers exist.
- [ ] **Do NOT** modify business logic in any moved file.
- [ ] **Do NOT** add database migrations.
- [ ] **Do NOT** change model fields or serializers.
- [ ] **Do NOT** change API endpoints or contracts.
- [ ] **Do NOT** introduce new features.
- [ ] **Do NOT** add module-level `payments/` imports to `core/` files.
- [ ] **Do NOT** use lazy imports, `__import__()`, or `importlib` to work around the `core/` → `payments/` dependency-matrix boundary.

### Test Generation
- [ ] No new test files required (existing tests must pass unchanged or with updated import paths).
- [ ] Update test import paths if they reference moved modules.
- [ ] Run `pytest tests/ -v` and verify all pass.
- [ ] Run `pytest tests/architecture/ -v` and verify 0 failures.
- [ ] Run `import-linter check` and verify 0 violations.

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
- [ ] Verify no new `from rentsecure_be.X import Y` in new/modified files outside `rentsecure_be/`.
- [ ] Verify `core/services/bank_details_service.py` is **unchanged** — deferred to PR-008C.
- [ ] Verify `rentsecure_be/utils/cashfree_payout.py` is **retained** — live importer exists.
- [ ] Verify `rentsecure_be/services/cashfree_service.py` is **retained** — out-of-scope importers exist.
- [ ] Verify `rentsecure_be/services/razorpay_service.py` is **retained** — out-of-scope importers exist.
- [ ] Verify no circular dependencies.
- [ ] Verify no lazy imports, `__import__()`, or `importlib` used to bypass dependency-matrix rules.

### Stop and Ask Conditions
AI must **stop and ask human** before proceeding if:
- [ ] Any required move would modify business logic in a moved file.
- [ ] Any required change would need a database migration.
- [ ] `core/services/bank_details_service.py` cannot remain unchanged and must be updated in this PR.
- [ ] A CI gate fails after 3 fix attempts.
- [ ] Existing tests fail and cannot be fixed without changing test expectations.

### Commit
- [ ] Commit message follows format: `refactor(architecture): move rentsecure_be utilities to bounded contexts`.
- [ ] Commit body explains: files moved, importers updated, lazy import added for `core/` due to dependency matrix.
- [ ] Branch name: `refactor/phase-0-008a-remove-rentsecure-be-imports`.

---

## 16. Stop-and-Ask Conditions

STOP and ask the Principal Software Architect if:

1. Any required move would change business logic, model fields, serializers, or API contracts.
2. Any required change would need a database migration.
3. `core/services/bank_details_service.py` must be resolved in PR-008A rather than deferred to PR-008C.
4. A moved file is imported by an external consumer outside this repository (not expected — `rentsecure_be/` is internal).
5. Any existing test fails and cannot be fixed without changing test expectations.
6. Any CI gate fails after 3 fix attempts.

---

## Appendix A: Architecture Decision References

| Decision | Reference |
|----------|-----------|
| No app may import from `rentsecure_be/` | ADR-006 v1.1 §5.1 Rule 1 |
| `core/` cannot import from `payment/` | ADR-006 v1.1 dependency matrix |
| Architecture tests enforce all rules | ADR-006 v1.1 §5.2 |
| `payments/` bounded context ownership | ADR-004 |
| `properties/` bounded context ownership | ADR-001 |
| `core/services/bank_details_service.py` deferred to PR-008C | Approved deferred violation — requires cross-context refactoring, not import replacement |

**Note on deferred violation:** `core/services/bank_details_service.py` retains its `rentsecure_be` import because resolving it requires moving the service out of `core/` or introducing a `shared/` interface. This is deferred to PR-008C. No import-linter exception is added; the violation remains visible in architecture tests until structurally resolved.

---

## Appendix B: Related Documents

- [Architecture v1.1 Release Candidate](../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Architecture v1.1 Implementation Master Plan — Phase 0](../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan — PR-008](../PHASE_0_EXECUTION_PLAN.md)
- [Engineering Standards](../ENGINEERING_STANDARDS.md)
- [AI Engineering Playbook](../AI_ENGINEERING_PLAYBOOK.md)
- [Import Rules ADR](../docs/architecture/adr/ADR-006_import_rules.md)
- [Payment Architecture ADR](../docs/architecture/adr/ADR-004_payment_architecture.md)
- [Bounded Context Strategy ADR](../docs/architecture/adr/ADR-001_bounded_context_strategy.md)

---

## Appendix C: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-20 | Principal Software Architect | Initial PR-008A specification for Architecture Cleanup Phase 1 |

**Next Review:** After PR-008A merge
**Approval Required:** Platform Team Lead, Staff Engineer

---

*End of PR-008A Implementation Specification*
