# PR-008B Implementation Specification

## SDK isolation (Cashfree/Razorpay adapters only)

---

## 1. Purpose

Encapsulate all direct payment SDK usage (`razorpay`, `cashfree`) inside the `payments/adapters/` package. Remove the remaining direct `razorpay` SDK import from `core/views/bank_views.py` and replace it with a delegation call to `payments/adapters/razorpay.py`. This PR enforces the architecture rule that payment SDKs must only appear in `payments/adapters/`.

This PR is **blocked until PR-008A is merged** because:
1. `payments/services/cashfree_service.py` and `payments/services/razorpay_service.py` must exist in their new locations
2. All `rentsecure_be/` imports must be removed before SDK isolation can be verified cleanly

---

## 2. Scope

### 2.1 In Scope

- Remove `import razorpay` from `core/views/bank_views.py`
- Add `create_order()` method to `payments/adapters/razorpay.py` to encapsulate direct SDK usage
- Update `core/views/bank_views.py` to delegate order creation to `RazorpayAdapter().create_order()`
- Verify no direct `razorpay` or `cashfree` SDK imports exist outside `payments/adapters/`
- Verify `pytest tests/architecture/ -v` passes with 0 failures

### 2.2 Out of Scope

- Any changes to business logic, model definitions, or serializer definitions
- Any database migrations or schema changes
- Any API endpoint changes or new endpoints
- Removing `rentsecure_be/` imports (PR-008A)
- Removing cross-context imports between `properties/` ↔ `payments/` and `documents/` ↔ `properties/` (PR-008C)
- God view/model splitting (PR-008D)
- Circular dependency resolution (PR-008E)
- Final architecture compliance verification (PR-008F)
- Any changes to `properties/views/rent_record_views.py`
- Any changes to `documents/views.py` or `documents/utils.py`
- Any changes to `properties/views/unit_views.py` or `properties/models/unit_models.py`

---

## 3. Files

### 3.1 Files to Create

None.

### 3.2 Files to Modify

| File | Change | Owner |
|------|--------|-------|
| `payments/adapters/razorpay.py` | Add `create_order()` method that encapsulates direct `razorpay` SDK usage | Platform Team |
| `core/views/bank_views.py` | Remove `import razorpay`; replace direct SDK calls with `RazorpayAdapter().create_order()` | Platform Team |

### 3.3 Files to Delete

None.

---

## 4. Responsibilities

| Role | Responsibility |
|------|----------------|
| **Platform Team Lead** | Approves SDK encapsulation approach; verifies no business behavior changes; owns PR merge |
| **Staff Engineer** | Reviews adapter interface design; verifies no SDK leakage outside `payments/adapters/` |
| **Developer** | Implements `create_order()` in RazorpayAdapter, updates `core/views/bank_views.py`, runs full validation |
| **AI Assistant** | Generates adapter method and view delegation per this spec; stops and asks if SDK behavior changes |

---

## 5. Acceptance Criteria

### 5.1 Functional

- [ ] `payments/adapters/razorpay.py` contains a `create_order()` method that encapsulates all direct `razorpay` SDK usage for order creation.
- [ ] `core/views/bank_views.py` no longer contains `import razorpay` or any other direct `razorpay` SDK import.
- [ ] `core/views/bank_views.py` delegates order creation to `RazorpayAdapter().create_order()`.
- [ ] No direct `razorpay` SDK imports exist outside `payments/adapters/`.
- [ ] No direct `cashfree` SDK imports exist outside `payments/adapters/`.
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
- [ ] All existing tests continue to pass (no behavioral regressions).

### 5.2 Non-Functional

- [ ] No business behavior changes (all existing tests pass).
- [ ] No database migrations required.
- [ ] No model field changes.
- [ ] No serializer changes.
- [ ] No API contract changes.
- [ ] PR-007 architecture tests remain green after PR-008B changes.

---

## 6. Architecture Rules

### 6.1 Bounded Context Compliance

- `payments/` owns all payment SDK interactions.
- No app outside `payments/adapters/` may import `razorpay` or `cashfree` SDK packages directly.
- Other apps must interact with payment SDKs only through adapter interfaces in `payments/adapters/`.

### 6.2 Import Rules

**Critical dependency matrix constraints per ADR-006 v1.1:**

| Source | shared | platform | identity | property | payment | notification | document |
|--------|--------|----------|----------|----------|---------|--------------|----------|
| **core** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **payments** | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |

**Implications for this PR:**
- `core/views/bank_views.py` **cannot** import from `payments/` at module level per the dependency matrix.
- `core/views/bank_views.py` must use a lazy import inside the function body that calls `RazorpayAdapter().create_order()`.
- The lazy import pattern is transitional; the view should eventually be moved to `payments/` in Phase 3.

**Permitted pattern for Phase 0:**
```python
def create_rent_payment(request):
    from payments.adapters.razorpay import RazorpayAdapter
    adapter = RazorpayAdapter()
    order = adapter.create_order(...)
```

### 6.3 SDK Rules

- Payment SDKs (`razorpay`, `cashfree`) must only appear in `payments/adapters/`.
- All SDK usage must be encapsulated in adapter classes.
- Other apps must interact with SDKs only through adapter interfaces.
- Adapter methods must not leak SDK-specific types to callers outside `payments/`.

### 6.4 Adapter Rules

- `payments/adapters/razorpay.py` must implement the `PaymentGateway` interface (or equivalent adapter contract).
- `create_order()` must accept the same parameters as the previous direct SDK call in `core/views/bank_views.py`.
- `create_order()` must return the same data structure (or a compatible one) as the previous direct SDK call.
- Adapter must not modify business behavior — it must be a drop-in replacement for the direct SDK call.

### 6.5 Naming Rules

- Adapter method: `create_order()`.
- Lazy-import wrapper in `core/views/bank_views.py` must preserve the original function name and signature.

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
| `test_sdk_placement.py` | Payment SDKs only in `payments/adapters/` | Pass |
| `test_rentsecure_be_boundary.py` | No app imports from `rentsecure_be/` | Pass |
| `test_layer_compliance.py` | Views do not import models from other apps at module level | Pass |
| `test_circular_deps.py` | No circular dependencies between app packages | Pass |
| `test_import_rules.py` | No forbidden imports in new/modified files | Pass |

---

## 8. Testing Strategy

### 8.1 Test Tiers Required

| Tier | Scope | Requirement |
|------|-------|-------------|
| **Unit** | `RazorpayAdapter.create_order()` | Existing adapter tests must pass |
| **Integration** | `create_rent_payment` API endpoint | All existing tests must pass |
| **Architecture** | SDK placement, import boundaries | 0 failures |
| **Regression** | Full test suite | No test failures |

### 8.2 Existing Test Preservation

All existing tests must continue to pass without modification. If tests patch the direct SDK call in `core/views/bank_views.py`:
- Update test patch targets to patch `payments.adapters.razorpay.RazorpayAdapter.create_order` or use the lazy-import wrapper.
- Preserve patch targets by adding a module-level wrapper function if needed.

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

### 9.1 SDK Encapsulation

1. **Add `create_order()` to `payments/adapters/razorpay.py`**:
   - Move the direct `razorpay` SDK order-creation logic from `core/views/bank_views.py` into `RazorpayAdapter.create_order()`.
   - Ensure the method signature matches the original call site.

2. **Update `core/views/bank_views.py`**:
   - Remove `import razorpay` from the top of the file.
   - Replace the direct SDK call with a lazy import and delegation to `RazorpayAdapter().create_order()`.

3. **Verify SDK isolation**:
   - Run `grep -r "import razorpay" --include="*.py" .` and verify only `payments/adapters/razorpay.py` matches.
   - Run `grep -r "import cashfree" --include="*.py" .` and verify only `payments/adapters/cashfree.py` matches.
   - Run `grep -r "from cashfree" --include="*.py" .` and verify only `payments/adapters/cashfree.py` matches.

### 9.2 Lazy Import Strategy

Because `core/` cannot import from `payments/` at module level, `core/views/bank_views.py` must use a lazy import inside the function body:

```python
def create_rent_payment(request):
    from payments.adapters.razorpay import RazorpayAdapter
    adapter = RazorpayAdapter()
    order = adapter.create_order(amount=..., currency=..., ...)
    # ... rest of function
```

**Rules for lazy imports:**
1. Lazy imports must be inside function/method bodies, not at module level.
2. Lazy imports must preserve the original business behavior exactly.
3. Lazy imports must not introduce circular dependencies.
4. Lazy imports are a transitional pattern only.

### 9.3 Data Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Business behavior change | Low | High | All existing tests must pass; verify API responses match |
| SDK behavior drift | Low | Medium | `create_order()` must return identical data structure |
| Import regression | Low | Medium | Architecture tests enforce SDK placement |
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
- `core/views/bank_views.py` returns 500 errors after deployment.
- CI pipeline cannot be fixed within 30 minutes.

### 10.2 Rollback Steps

1. **Git revert:**
   ```bash
   git revert <PR-008B-merge-commit-sha>
   git push origin main
   ```
2. **Verify rollback:**
   ```bash
   pytest tests/ -v
   pytest tests/architecture/ -v
   import-linter check
   ```
3. **Deploy reverted code** to staging, then production.
4. **Smoke tests:** Verify `create_rent_payment` endpoint returns expected responses.
5. **Notify team:** Post rollback completion notice with root cause and fix plan.

### 10.3 Estimated Rollback Time

**15 minutes** (git revert + deploy + smoke tests).

### 10.4 Data Risk

**None.** This PR does not modify database schema or data.

### 10.5 Rollback Validation

- Rollback must be tested on staging before production deploy.
- Test sequence:
   1. Apply PR-008B to staging.
   2. Verify all architecture tests pass.
   3. Execute rollback steps 1-4 above.
   4. Verify all existing tests still pass.
   5. Verify `import-linter check` passes.
   6. Re-apply PR-008B after successful rollback test.

---

## 11. Expected Git Diff

### 11.1 Summary

| Metric | Value |
|--------|-------|
| Files changed | 2 (0 new, 2 modified, 0 deleted) |
| Files added | 0 |
| Files modified | 2 |
| Files deleted | 0 |
| Lines added | ~25 |
| Lines removed | ~15 |
| Net change | ~10 lines |

### 11.2 Files Modified (~25 lines)

| File | Approx Lines Changed | Description |
|------|----------------------|-------------|
| `payments/adapters/razorpay.py` | +15, -0 | Add `create_order()` method encapsulating direct SDK usage |
| `core/views/bank_views.py` | +10, -15 | Remove `import razorpay`; replace with lazy import + delegation to adapter |

### 11.3 Diff Constraints

- No file in the diff may exceed 400 lines total after modification.
- No database migrations.
- No model field changes.
- No serializer changes.
- No API endpoint changes.
- No business logic changes.

---

## 12. Definition of Done

PR-008B is **Done** when ALL of the following are true.

### Code
- [ ] `payments/adapters/razorpay.py` contains `create_order()` encapsulating all direct SDK usage.
- [ ] `core/views/bank_views.py` no longer contains `import razorpay`.
- [ ] `core/views/bank_views.py` delegates to `RazorpayAdapter().create_order()` via lazy import.
- [ ] No direct `razorpay` SDK imports exist outside `payments/adapters/`.
- [ ] No direct `cashfree` SDK imports exist outside `payments/adapters/`.

### Tests
- [ ] All existing tests pass (no regressions).
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
- [ ] No test patch targets broken by lazy import.

### CI
- [ ] `ruff check .` passes (0 errors).
- [ ] `ruff format --check .` passes.
- [ ] `mypy .` passes (0 errors).
- [ ] `import-linter check` passes (0 violations).
- [ ] `pytest tests/ -v` passes.
- [ ] `pytest tests/architecture/ -v` passes.
- [ ] `python manage.py check` passes.

### Architecture
- [ ] Payment SDKs confined to `payments/adapters/`.
- [ ] No `razorpay` or `cashfree` imports outside `payments/adapters/`.
- [ ] `core/` does not import from `payments/` at module level.
- [ ] No circular dependencies introduced.
- [ ] `import-linter.ini` matches ADR-006 v1.1 matrix.

### Documentation
- [ ] CHANGELOG.md updated.
- [ ] PR description includes summary of SDK encapsulation changes.

### Deployment
- [ ] PR approved by Platform Team Lead and Staff Engineer.
- [ ] Merged to `phase-0-foundation` branch.
- [ ] Deployed to staging.
- [ ] Staging validation passed (24 hours).
- [ ] No production incidents during staging validation.

---

## 13. Developer Checklist

### Pre-Implementation
- [ ] Verify PR-008A is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes (baseline).
- [ ] Verify `import-linter check` passes (baseline).
- [ ] Run `pytest tests/ -v` and verify all pass (baseline).
- [ ] Catalog all direct SDK imports from PR-007 architecture tests.
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Import Rules, SDK Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Refactoring Rules.
- [ ] Confirm `core/` cannot import from `payments/` at module level per dependency matrix.
- [ ] Verify `payments/adapters/razorpay.py` exists and implements the adapter interface.

### Implementation
- [ ] Add `create_order()` method to `payments/adapters/razorpay.py`.
- [ ] Remove `import razorpay` from `core/views/bank_views.py`.
- [ ] Replace direct SDK call in `core/views/bank_views.py` with lazy import + `RazorpayAdapter().create_order()`.
- [ ] Verify no other direct SDK imports exist outside `payments/adapters/`.
- [ ] Run `grep -r "import razorpay" --include="*.py" .` and verify only `payments/adapters/razorpay.py` matches.
- [ ] Run `grep -r "import cashfree" --include="*.py" .` and verify only `payments/adapters/cashfree.py` matches.

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
- [ ] Verify no `import razorpay` or `from razorpay` outside `payments/adapters/razorpay.py`.
- [ ] Verify no `import cashfree` or `from cashfree` outside `payments/adapters/cashfree.py`.
- [ ] Verify `core/views/bank_views.py` uses lazy import, not module-level import.
- [ ] Verify `create_order()` returns the same data structure as the original direct SDK call.

### Rollback
- [ ] Document rollback plan in PR description.
- [ ] Test rollback on staging: apply PR-008B, verify architecture tests pass, execute rollback, verify all tests still pass.

### PR
- [ ] Commit message follows conventional commits format.
- [ ] Branch name follows `<type>/<ticket-id>-<description>` format.
- [ ] PR description includes: summary, motivation, changes, testing, rollback plan.
- [ ] PR size is within limits (~10 lines, 2 files).
- [ ] PR is linked to Phase 0 Architecture Cleanup task.

---

## 14. Reviewer Checklist

Use this checklist when reviewing PR-008B.

### Architecture
- [ ] `payments/adapters/razorpay.py` contains `create_order()` encapsulating direct SDK usage.
- [ ] No `razorpay` or `cashfree` imports outside `payments/adapters/`.
- [ ] `core/views/bank_views.py` uses lazy import, not module-level import from `payments/`.
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
- [ ] `create_order()` is a drop-in replacement for the original direct SDK call.
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
- [ ] PR description includes summary of SDK encapsulation changes.

---

## 15. AI Checklist

Use this checklist when generating PR-008B with AI assistance.

### Pre-Generation
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Import Rules, SDK Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Refactoring Rules.
- [ ] Verify PR-008A is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes on baseline.
- [ ] Verify `import-linter check` passes on baseline.
- [ ] Catalog all direct SDK imports from PR-007 architecture tests.
- [ ] Confirm `core/` cannot import from `payments/` at module level per dependency matrix.
- [ ] Verify `payments/adapters/razorpay.py` exists and implements the adapter interface.

### Code Generation
- [ ] Add `create_order()` method to `payments/adapters/razorpay.py`.
- [ ] Remove `import razorpay` from `core/views/bank_views.py`.
- [ ] Replace direct SDK call in `core/views/bank_views.py` with lazy import + `RazorpayAdapter().create_order()`.
- [ ] Verify no other direct SDK imports exist outside `payments/adapters/`.
- [ ] **Do NOT** modify business logic in `core/views/bank_views.py`.
- [ ] **Do NOT** add database migrations.
- [ ] **Do NOT** change model fields or serializers.
- [ ] **Do NOT** change API endpoints or contracts.
- [ ] **Do NOT** introduce new features.
- [ ] **Do NOT** add module-level `payments/` imports to `core/` files.

### Test Generation
- [ ] No new test files required (existing tests must pass unchanged or with updated patch targets).
- [ ] Update test patch targets if they reference direct SDK calls.
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
- [ ] Verify no `import razorpay` or `from razorpay` outside `payments/adapters/razorpay.py`.
- [ ] Verify no `import cashfree` or `from cashfree` outside `payments/adapters/cashfree.py`.
- [ ] Verify `core/views/bank_views.py` uses lazy import, not module-level import.
- [ ] Verify no circular dependencies.

### Stop and Ask Conditions
AI must **stop and ask human** before proceeding if:
- [ ] Any required change would modify business logic in `core/views/bank_views.py`.
- [ ] Any required change would need a database migration.
- [ ] `core/views/bank_views.py` cannot use a lazy import and must import from `payments/` at module level.
- [ ] `create_order()` cannot be a drop-in replacement for the original direct SDK call.
- [ ] Any CI gate fails after 3 fix attempts.
- [ ] Existing tests fail and cannot be fixed without changing test expectations.

### Commit
- [ ] Commit message follows format: `refactor(architecture): isolate payment SDKs to payments/adapters`.
- [ ] Commit body explains: SDK encapsulation approach, `create_order()` added to RazorpayAdapter, lazy import used in `core/views/bank_views.py` due to dependency matrix.
- [ ] Branch name: `refactor/phase-0-008b-sdk-isolation`.

---

## 16. Stop-and-Ask Conditions

STOP and ask the Principal Software Architect if:

1. Any required fix would change business logic, model definitions, serializers, or API contracts.
2. Any required fix would need a database migration.
3. `core/views/bank_views.py` must import from `payments/` at module level and lazy import is insufficient.
4. `create_order()` cannot be a drop-in replacement for the original direct SDK call.
5. Any existing test fails and cannot be fixed without changing test expectations.
6. Any CI gate fails after 3 fix attempts.

---

## Appendix A: Architecture Decision References

| Decision | Reference |
|----------|-----------|
| Payment SDKs confined to `payments/adapters/` | ADR-006 v1.1 §5.4 |
| `core/` cannot import from `payment/` | ADR-006 v1.1 dependency matrix |
| Lazy imports as transitional pattern | ADR-006 v1.1 §5.3 |
| Architecture tests enforce all rules | ADR-006 v1.1 §5.2 |
| `payments/` bounded context ownership | ADR-004 |

---

## Appendix B: Related Documents

- [Architecture v1.1 Release Candidate](../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Architecture v1.1 Implementation Master Plan — Phase 0](../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan — PR-008](../PHASE_0_EXECUTION_PLAN.md)
- [Engineering Standards](../ENGINEERING_STANDARDS.md)
- [AI Engineering Playbook](../AI_ENGINEERING_PLAYBOOK.md)
- [Import Rules ADR](../docs/architecture/adr/ADR-006_import_rules.md)
- [Payment Architecture ADR](../docs/architecture/adr/ADR-004_payment_architecture.md)

---

## Appendix C: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-20 | Principal Software Architect | Initial PR-008B specification for Architecture Cleanup Phase 1 |

**Next Review:** After PR-008B merge
**Approval Required:** Platform Team Lead, Staff Engineer

---

*End of PR-008B Implementation Specification*
