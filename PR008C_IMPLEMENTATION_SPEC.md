# PR-008C Implementation Specification

## Remove cross-context imports (properties ↔ payments, documents ↔ properties)

---

## 1. Purpose

Resolve the remaining cross-context import violations between `properties/` ↔ `payments/` and `documents/` ↔ `properties/` by replacing module-level forbidden imports with lazy imports, `apps.get_model()`, or service delegation patterns. This PR enforces the architecture rule that `properties/` must not import from `payments/` at module level, and `documents/` must not import from `properties/` at module level.

This PR is **blocked until PR-008B is merged** because:
1. SDK isolation must be verified before fixing other import violations
2. `payments/` adapters must be in place for delegation patterns
3. `import-linter check` must pass on baseline before new fixes are applied

---

## 2. Scope

### 2.1 In Scope

- Remove top-level `payments/` imports from `properties/views/rent_record_views.py`; replace with lazy imports or service delegation
- Remove `properties/` imports from `documents/views.py`; replace with `django.apps.apps.get_model()` or lazy imports
- Remove `properties/` imports from `documents/utils.py`; replace with `django.apps.apps.get_model()` or lazy imports
- Add module-level lazy-import wrapper functions to `properties/views/rent_record_views.py` if needed to preserve test patch targets
- Verify `pytest tests/architecture/ -v` passes with 0 failures

### 2.2 Out of Scope

- Any changes to business logic, model definitions, or serializer definitions
- Any database migrations or schema changes
- Any API endpoint changes or new endpoints
- Removing `rentsecure_be/` imports (PR-008A)
- SDK isolation work (PR-008B)
- God view/model splitting (PR-008D)
- Circular dependency resolution (PR-008E)
- Final architecture compliance verification (PR-008F)
- Any changes to `core/views/bank_views.py`
- Any changes to `properties/views/unit_views.py` or `properties/models/unit_models.py`
- Any changes to `shared/` package structure

---

## 3. Files

### 3.1 Files to Create

None.

### 3.2 Files to Modify

| File | Change | Owner |
|------|--------|-------|
| `properties/views/rent_record_views.py` | Remove top-level `payments/` imports; add lazy-import wrappers inside function bodies; preserve test patch targets | Platform Team |
| `documents/views.py` | Remove top-level `properties/` imports; use `apps.get_model()` or lazy imports inside function bodies | Platform Team |
| `documents/utils.py` | Remove top-level `properties/` imports; use `apps.get_model()` or lazy imports inside function bodies | Platform Team |

### 3.3 Files to Delete

None.

---

## 4. Responsibilities

| Role | Responsibility |
|------|----------------|
| **Platform Team Lead** | Approves lazy-import approach; verifies no business behavior changes; owns PR merge |
| **Staff Engineer** | Reviews dependency matrix compliance; verifies no circular dependencies introduced |
| **Developer** | Implements lazy imports and `apps.get_model()` patterns, updates test patch targets, runs full validation |
| **AI Assistant** | Generates refactored code per this spec; stops and asks if business behavior changes are required |

---

## 5. Acceptance Criteria

### 5.1 Functional

- [ ] `properties/views/rent_record_views.py` does not import from `payments/` at module level.
- [ ] `documents/views.py` does not import from `properties/` at module level.
- [ ] `documents/utils.py` does not import from `properties/` at module level.
- [ ] Lazy imports in `properties/views/rent_record_views.py` preserve original business behavior.
- [ ] `apps.get_model()` calls in `documents/views.py` and `documents/utils.py` resolve the correct models.
- [ ] Test patch targets are preserved (via lazy-import wrappers if needed).
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
- [ ] All existing tests continue to pass (no behavioral regressions).

### 5.2 Non-Functional

- [ ] No business behavior changes (all existing tests pass).
- [ ] No database migrations required.
- [ ] No model field changes.
- [ ] No serializer changes.
- [ ] No API contract changes.
- [ ] PR-007 architecture tests remain green after PR-008C changes.

---

## 6. Architecture Rules

### 6.1 Bounded Context Compliance

- `properties/` must not import from `payments/` at module level.
- `documents/` must not import from `properties/` at module level.
- Lazy imports inside function/method bodies are permitted as a transitional pattern.
- `apps.get_model()` is the preferred pattern for `documents/` to reference `properties/` models without a direct import.

### 6.2 Import Rules

**Critical dependency matrix constraints per ADR-006 v1.1:**

| Source | shared | platform | identity | property | payment | notification | document |
|--------|--------|----------|----------|----------|---------|--------------|----------|
| **core** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **properties** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **payments** | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| **notification** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **documents** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Forbidden patterns (must be eliminated in this PR):**
- `properties/` → `payments/` at module level
- `documents/` → `properties/` at module level

**Permitted patterns:**
- Lazy imports inside function/method bodies (transitional)
- `django.apps.apps.get_model()` for deferred model resolution
- Service delegation through adapter interfaces

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

### 6.4 apps.get_model() Rules

For `documents/` to reference `properties/` models without a direct import:

```python
from django.apps import apps

def some_function():
    Unit = apps.get_model('properties', 'Unit')
    # ... use Unit model
```

**Rules for `apps.get_model()`:**
1. Use the app label `'properties'` and the model name `'Unit'` (case-sensitive).
2. `apps.get_model()` must be called inside function/method bodies, not at module level.
3. The model name must match the actual `class Meta: db_table` or model name exactly.
4. `apps.get_model()` is preferred over lazy imports for model references in `documents/`.

### 6.5 View Rules

- View files must not exceed 300 lines.
- If a view file exceeds 300 lines, extract helper functions into a separate module (e.g., `properties/views/rent_record_helpers.py`).
- Extracted helpers must not introduce new cross-app imports.

### 6.6 Naming Rules

- Lazy-import wrapper functions must be named clearly (e.g., `_get_payment_service()`, `_get_razorpay_adapter()`).
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
| `test_properties_isolation.py` | `properties/` does not import from `payments/` at module level | Pass |
| `test_documents_isolation.py` | `documents/` does not import from `properties/` at module level | Pass |
| `test_rentsecure_be_boundary.py` | No app imports from `rentsecure_be/` | Pass |
| `test_sdk_placement.py` | Payment SDKs only in `payments/adapters/` | Pass |
| `test_layer_compliance.py` | Views do not import models from other apps at module level | Pass |
| `test_circular_deps.py` | No circular dependencies between app packages | Pass |
| `test_import_rules.py` | No forbidden imports in new/modified files | Pass |

---

## 8. Testing Strategy

### 8.1 Test Tiers Required

| Tier | Scope | Requirement |
|------|-------|-------------|
| **Unit** | Refactored view and utility methods | No coverage requirement (behavior unchanged) |
| **Integration** | Existing API endpoints | All existing tests must pass |
| **Architecture** | Import boundaries, layer compliance | 0 failures |
| **Regression** | Full test suite | No test failures |

### 8.2 Existing Test Preservation

All existing tests must continue to pass without modification. If test patch targets are affected by lazy imports:
- Preserve original patch targets by adding module-level wrapper functions.
- Example: If tests patch `properties.views.rent_record_views.PaymentService`, add:
  ```python
  def _get_payment_service():
      from payments.services.payment_service import PaymentService
      return PaymentService
  ```
  And update tests to patch `properties.views.rent_record_views._get_payment_service`.

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

### 9.1 properties/views/rent_record_views.py

1. **Identify all top-level `payments/` imports** in the file.
2. **Remove module-level imports** and replace with lazy imports inside each function that uses them.
3. **Add module-level wrapper functions** if needed to preserve test patch targets.
4. **Example transformation:**

   Before:
   ```python
   from payments.services.payment_service import PaymentService
   from payments.adapters.razorpay import RazorpayAdapter
   ```

   After:
   ```python
   def _get_payment_service():
       from payments.services.payment_service import PaymentService
       return PaymentService

   def _get_razorpay_adapter():
       from payments.adapters.razorpay import RazorpayAdapter
       return RazorpayAdapter
   ```

   And in each function:
   ```python
   def some_view(request):
       PaymentService = _get_payment_service()
       RazorpayAdapter = _get_razorpay_adapter()
       # ... use them
   ```

### 9.2 documents/views.py and documents/utils.py

1. **Identify all top-level `properties/` imports** in the files.
2. **Remove module-level imports** and replace with `apps.get_model()` or lazy imports inside each function that uses them.
3. **Example transformation:**

   Before:
   ```python
   from properties.models import Unit, Property
   ```

   After:
   ```python
   from django.apps import apps

   def some_function():
       Unit = apps.get_model('properties', 'Unit')
       Property = apps.get_model('properties', 'Property')
       # ... use them
   ```

### 9.3 Circular Dependency Avoidance

- Lazy imports must not introduce circular dependencies.
- `apps.get_model()` does not introduce circular dependencies because it defers model resolution to runtime.
- Verify `test_circular_deps.py` passes after all changes.

### 9.4 Data Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Business behavior change | Low | High | All existing tests must pass; verify API responses match |
| Import regression | Low | Medium | Architecture tests enforce import boundaries |
| Circular dependency introduced | Low | Medium | `test_circular_deps.py` must pass |
| Test patch target broken | Medium | Low | Preserve patch targets via lazy-import wrappers |

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
   git revert <PR-008C-merge-commit-sha>
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
   1. Apply PR-008C to staging.
   2. Verify all architecture tests pass.
   3. Execute rollback steps 1-4 above.
   4. Verify all existing tests still pass.
   5. Verify `import-linter check` passes.
   6. Re-apply PR-008C after successful rollback test.

---

## 11. Expected Git Diff

### 11.1 Summary

| Metric | Value |
|--------|-------|
| Files changed | 3 (0 new, 3 modified, 0 deleted) |
| Files added | 0 |
| Files modified | 3 |
| Files deleted | 0 |
| Lines added | ~40 |
| Lines removed | ~20 |
| Net change | ~20 lines |

### 11.2 Files Modified (~40 lines)

| File | Approx Lines Changed | Description |
|------|----------------------|-------------|
| `properties/views/rent_record_views.py` | +20, -10 | Remove top-level `payments/` imports; add lazy-import wrappers |
| `documents/views.py` | +10, -5 | Remove `properties/` imports; use `apps.get_model()` |
| `documents/utils.py` | +10, -5 | Remove `properties/` imports; use `apps.get_model()` |

### 11.3 Diff Constraints

- No file in the diff may exceed 400 lines total after modification.
- No database migrations.
- No model field changes.
- No serializer changes.
- No API endpoint changes.
- No business logic changes.

---

## 12. Definition of Done

PR-008C is **Done** when ALL of the following are true.

### Code
- [ ] `properties/views/rent_record_views.py` does not import from `payments/` at module level.
- [ ] `documents/views.py` does not import from `properties/` at module level.
- [ ] `documents/utils.py` does not import from `properties/` at module level.
- [ ] Lazy imports in `properties/views/rent_record_views.py` preserve original business behavior.
- [ ] `apps.get_model()` calls in `documents/views.py` and `documents/utils.py` resolve correct models.
- [ ] Test patch targets are preserved.

### Tests
- [ ] All existing tests pass (no regressions).
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
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
- [ ] No `properties/` → `payments/` imports at module level.
- [ ] No `documents/` → `properties/` imports at module level.
- [ ] No circular dependencies introduced.
- [ ] `import-linter.ini` matches ADR-006 v1.1 matrix.

### Documentation
- [ ] CHANGELOG.md updated.
- [ ] PR description includes summary of import fixes.

### Deployment
- [ ] PR approved by Platform Team Lead and Staff Engineer.
- [ ] Merged to `phase-0-foundation` branch.
- [ ] Deployed to staging.
- [ ] Staging validation passed (24 hours).
- [ ] No production incidents during staging validation.

---

## 13. Developer Checklist

### Pre-Implementation
- [ ] Verify PR-008B is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes (baseline).
- [ ] Verify `import-linter check` passes (baseline).
- [ ] Run `pytest tests/ -v` and verify all pass (baseline).
- [ ] Catalog all cross-context import violations from PR-007 architecture tests.
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Import Rules, Dependency Rules, Lazy Import Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Refactoring Rules.
- [ ] Confirm `properties/` cannot import from `payments/` at module level.
- [ ] Confirm `documents/` cannot import from `properties/` at module level.

### Implementation
- [ ] Remove top-level `payments/` imports from `properties/views/rent_record_views.py`.
- [ ] Add lazy-import wrapper functions to `properties/views/rent_record_views.py` if needed for test patch targets.
- [ ] Replace direct `payments/` usage in `properties/views/rent_record_views.py` with lazy imports.
- [ ] Remove top-level `properties/` imports from `documents/views.py`.
- [ ] Replace direct `properties/` usage in `documents/views.py` with `apps.get_model()` or lazy imports.
- [ ] Remove top-level `properties/` imports from `documents/utils.py`.
- [ ] Replace direct `properties/` usage in `documents/utils.py` with `apps.get_model()` or lazy imports.
- [ ] Update test patch targets if they reference moved imports.

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

### Validation
- [ ] Verify no `properties/` → `payments/` imports at module level.
- [ ] Verify no `documents/` → `properties/` imports at module level.
- [ ] Verify lazy imports are inside function bodies, not at module level.
- [ ] Verify `apps.get_model()` calls use correct app labels and model names.
- [ ] Verify no circular dependencies introduced.

### Rollback
- [ ] Document rollback plan in PR description.
- [ ] Test rollback on staging: apply PR-008C, verify architecture tests pass, execute rollback, verify all tests still pass.

### PR
- [ ] Commit message follows conventional commits format.
- [ ] Branch name follows `<type>/<ticket-id>-<description>` format.
- [ ] PR description includes: summary, motivation, changes, testing, rollback plan.
- [ ] PR size is within limits (~20 lines, 3 files).
- [ ] PR is linked to Phase 0 Architecture Cleanup task.

---

## 14. Reviewer Checklist

Use this checklist when reviewing PR-008C.

### Architecture
- [ ] `properties/views/rent_record_views.py` does not import from `payments/` at module level.
- [ ] `documents/views.py` does not import from `properties/` at module level.
- [ ] `documents/utils.py` does not import from `properties/` at module level.
- [ ] Lazy imports are inside function bodies, not at module level.
- [ ] `apps.get_model()` calls use correct app labels and model names.
- [ ] No circular dependencies introduced.
- [ ] `import-linter.ini` matches ADR-006 v1.1 matrix.
- [ ] All architecture tests pass.
- [ ] No architecture rules weakened.

### Code Quality
- [ ] Ruff passes (0 errors, 0 formatting issues).
- [ ] MyPy passes (0 errors).
- [ ] No `print()` statements.
- [ ] No `# TODO` or `# FIXME` comments.
- [ ] No commented-out code.
- [ ] Business behavior is preserved (no logic changes).
- [ ] Test patch targets are preserved.

### Testing
- [ ] All existing tests pass (no regressions).
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
- [ ] No test patch targets broken.

### CI
- [ ] All CI gates pass.
- [ ] No import-linter violations.
- [ ] No architecture test failures.
- [ ] No circular dependency warnings.

### Documentation
- [ ] CHANGELOG.md updated.
- [ ] PR description includes summary of import fixes.

---

## 15. AI Checklist

Use this checklist when generating PR-008C with AI assistance.

### Pre-Generation
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Import Rules, Dependency Rules, Lazy Import Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Refactoring Rules.
- [ ] Verify PR-008B is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes on baseline.
- [ ] Verify `import-linter check` passes on baseline.
- [ ] Catalog all cross-context import violations from PR-007 architecture tests.
- [ ] Confirm `properties/` cannot import from `payments/` at module level.
- [ ] Confirm `documents/` cannot import from `properties/` at module level.

### Code Generation
- [ ] Remove top-level `payments/` imports from `properties/views/rent_record_views.py`.
- [ ] Add lazy-import wrapper functions to `properties/views/rent_record_views.py` if needed for test patch targets.
- [ ] Replace direct `payments/` usage in `properties/views/rent_record_views.py` with lazy imports.
- [ ] Remove top-level `properties/` imports from `documents/views.py`.
- [ ] Replace direct `properties/` usage in `documents/views.py` with `apps.get_model()` or lazy imports.
- [ ] Remove top-level `properties/` imports from `documents/utils.py`.
- [ ] Replace direct `properties/` usage in `documents/utils.py` with `apps.get_model()` or lazy imports.
- [ ] **Do NOT** modify business logic in any view or utility.
- [ ] **Do NOT** add database migrations.
- [ ] **Do NOT** change model fields or serializers.
- [ ] **Do NOT** change API endpoints or contracts.
- [ ] **Do NOT** introduce new features.
- [ ] **Do NOT** add module-level `payments/` imports to `properties/` files.
- [ ] **Do NOT** add module-level `properties/` imports to `documents/` files.

### Test Generation
- [ ] No new test files required (existing tests must pass unchanged or with updated patch targets).
- [ ] Update test patch targets if they reference moved imports.
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
- [ ] Verify no `properties/` → `payments/` imports at module level.
- [ ] Verify no `documents/` → `properties/` imports at module level.
- [ ] Verify lazy imports are inside function bodies, not at module level.
- [ ] Verify `apps.get_model()` calls use correct app labels and model names.
- [ ] Verify no circular dependencies.

### Stop and Ask Conditions
AI must **stop and ask human** before proceeding if:
- [ ] Any required change would modify business logic in a view or utility.
- [ ] Any required change would need a database migration.
- [ ] `properties/views/rent_record_views.py` or `documents/views.py` requires cross-app imports that cannot be resolved via lazy imports or `apps.get_model()`.
- [ ] Any CI gate fails after 3 fix attempts.
- [ ] Existing tests fail and cannot be fixed without changing test expectations.

### Commit
- [ ] Commit message follows format: `refactor(architecture): remove cross-context imports between properties/payments and documents/properties`.
- [ ] Commit body explains: lazy imports added, `apps.get_model()` used, test patch targets preserved.
- [ ] Branch name: `refactor/phase-0-008c-remove-cross-context-imports`.

---

## 16. Stop-and-Ask Conditions

STOP and ask the Principal Software Architect if:

1. Any required fix would change business logic, model definitions, serializers, or API contracts.
2. Any required fix would need a database migration.
3. `properties/views/rent_record_views.py` requires module-level `payments/` imports that cannot be deferred to lazy imports.
4. `documents/views.py` or `documents/utils.py` requires `properties/` imports that cannot be resolved via `apps.get_model()` or lazy imports.
5. Any existing test fails and cannot be fixed without changing test expectations.
6. Any CI gate fails after 3 fix attempts.

---

## Appendix A: Architecture Decision References

| Decision | Reference |
|----------|-----------|
| `properties/` cannot import from `payment/` | ADR-006 v1.1 dependency matrix |
| `documents/` cannot import from `properties/` | ADR-006 v1.1 dependency matrix |
| Lazy imports as transitional pattern | ADR-006 v1.1 §5.3 |
| `apps.get_model()` for deferred model resolution | ADR-006 v1.1 §5.3 |
| Architecture tests enforce all rules | ADR-006 v1.1 §5.2 |
| `properties/` bounded context ownership | ADR-001 |
| `documents/` bounded context ownership | ADR-001 |

---

## Appendix B: Related Documents

- [Architecture v1.1 Release Candidate](../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Architecture v1.1 Implementation Master Plan — Phase 0](../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan — PR-008](../PHASE_0_EXECUTION_PLAN.md)
- [Engineering Standards](../ENGINEERING_STANDARDS.md)
- [AI Engineering Playbook](../AI_ENGINEERING_PLAYBOOK.md)
- [Import Rules ADR](../docs/architecture/adr/ADR-006_import_rules.md)
- [Bounded Context Strategy ADR](../docs/architecture/adr/ADR-001_bounded_context_strategy.md)

---

## Appendix C: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-20 | Principal Software Architect | Initial PR-008C specification for Architecture Cleanup Phase 1 |

**Next Review:** After PR-008C merge
**Approval Required:** Platform Team Lead, Staff Engineer

---

*End of PR-008C Implementation Specification*
