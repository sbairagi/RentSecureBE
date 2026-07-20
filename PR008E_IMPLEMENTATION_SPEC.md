# PR-008E Implementation Specification

## Resolve circular dependencies

---

## 1. Purpose

Identify and resolve all circular dependency chains between app packages that remain after PR-008A through PR-008D. Circular dependencies violate the v1.1 dependency matrix and must be eliminated by introducing interfaces in `shared/`, using dependency injection or callback patterns, or moving shared types to `shared/`. No business behavior changes — pure architectural fix.

This PR is **blocked until PR-008D is merged** because:
1. File size fixes must be applied before resolving circular deps
2. `import-linter check` must pass on baseline before new fixes are applied
3. All prior architecture cleanup must be verified before tackling circular dependencies

---

## 2. Scope

### 2.1 In Scope

- Run `pytest tests/architecture/test_circular_deps.py -v` to catalog remaining circular dependencies
- Resolve identified circular dependency chains using one or more of:
  - Introduce interfaces/protocols in `shared/`
  - Use dependency injection or callback patterns
  - Move shared types to `shared/` package
- Verify `pytest tests/architecture/ -v` passes with 0 failures
- Verify `import-linter check` passes with 0 violations

### 2.2 Out of Scope

- Any changes to business logic, model definitions, or serializer definitions
- Any database migrations or schema changes
- Any API endpoint changes or new endpoints
- Removing `rentsecure_be/` imports (PR-008A)
- SDK isolation work (PR-008B)
- Removing cross-context imports (PR-008C)
- God view/model splitting (PR-008D)
- Final architecture compliance verification (PR-008F)
- Any changes to `core/views/bank_views.py`
- Any changes to `properties/views/unit_views.py` or `properties/models/unit_models.py`
- Any changes to `shared/` package structure beyond adding interfaces/protocols
- Weakening architecture rules to accommodate circular dependencies

---

## 3. Files

### 3.1 Files to Create

| File | Purpose | Owner |
|------|---------|-------|
| `shared/interfaces.py` (or relevant submodule) | Introduce interfaces/protocols to break circular dependencies | Platform Team |
| `shared/types.py` (or relevant submodule) | Move shared types to `shared/` to break circular dependencies | Platform Team |

### 3.2 Files to Modify

| File | Change | Owner |
|------|--------|-------|
| Circular dependency source files | Refactor to use `shared/` interfaces, DI, or callbacks | Platform Team |

### 3.3 Files to Delete

None.

---

## 4. Responsibilities

| Role | Responsibility |
|------|----------------|
| **Platform Team Lead** | Approves circular dependency resolution approach; verifies no business behavior changes; owns PR merge |
| **Staff Engineer** | Reviews interface design; verifies dependency matrix compliance after resolution |
| **Architecture Review Board** | Approves any ADR exceptions if resolution requires temporary matrix relaxation (not expected) |
| **Developer** | Implements interface extraction, DI patterns, or type moves; runs full validation |
| **AI Assistant** | Generates interfaces and refactored code per this spec; stops and asks if business behavior changes are required |

---

## 5. Acceptance Criteria

### 5.1 Functional

- [ ] `pytest tests/architecture/test_circular_deps.py -v` passes with 0 failures.
- [ ] All identified circular dependency chains are resolved.
- [ ] No new circular dependencies are introduced.
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
- [ ] All existing tests continue to pass (no behavioral regressions).

### 5.2 Non-Functional

- [ ] No business behavior changes (all existing tests pass).
- [ ] No database migrations required.
- [ ] No model field changes.
- [ ] No serializer changes.
- [ ] No API contract changes.
- [ ] PR-007 architecture tests remain green after PR-008E changes.

---

## 6. Architecture Rules

### 6.1 Bounded Context Compliance

- All bounded contexts must comply with the v1.1 dependency matrix.
- Circular dependencies between app packages are strictly prohibited.
- Shared interfaces and types must live in `shared/`.

### 6.2 Import Rules

**Critical dependency matrix constraints per ADR-006 v1.1:**

| Source | shared | platform | identity | property | payment | notification | document |
|--------|--------|----------|----------|----------|---------|--------------|----------|
| **core** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **properties** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **payments** | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| **notification** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **documents** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Implications for this PR:**
- Circular dependencies must be resolved by introducing interfaces in `shared/`, using DI/callbacks, or moving shared types to `shared/`.
- **Never** weaken architecture rules to accommodate circular dependencies.

### 6.3 Circular Dependency Resolution Strategies

Use the following strategies in order of preference:

1. **Introduce interfaces in `shared/`**: If two apps need to reference each other's types, define an abstract interface or protocol in `shared/` and have each app implement it.
2. **Dependency injection**: Pass dependencies as function parameters or constructor arguments instead of importing them.
3. **Callback patterns**: Use callback functions or signals to invert the dependency direction.
4. **Move shared types to `shared/`**: If a type is used by multiple apps, move it to `shared/types.py` or a dedicated `shared/` submodule.

### 6.4 Interface Rules

- Interfaces in `shared/` must be abstract (no concrete implementations).
- Interfaces must not import from any app package.
- Interface names must be descriptive (e.g., `PaymentGateway`, `NotificationSender`).
- Existing adapter interfaces (e.g., `PaymentGateway`) must be reused if they solve the circular dependency.

### 6.5 Dependency Injection Rules

- DI must not introduce new cross-app imports at module level.
- DI parameters must use `shared/` types or Python builtins.
- DI must preserve the original business behavior exactly.

### 6.6 Naming Rules

- Interface files: `shared/interfaces.py` or `shared/interfaces/<context>.py`.
- Shared type files: `shared/types.py` or `shared/types/<context>.py`.
- Callback functions must be named clearly (e.g., `on_payment_completed`, `on_document_generated`).

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
| `test_circular_deps.py` | No circular dependencies between app packages | Pass |
| `test_rentsecure_be_boundary.py` | No app imports from `rentsecure_be/` | Pass |
| `test_sdk_placement.py` | Payment SDKs only in `payments/adapters/` | Pass |
| `test_properties_isolation.py` | `properties/` does not import from `payments/` | Pass |
| `test_documents_isolation.py` | `documents/` does not import from `properties/` | Pass |
| `test_layer_compliance.py` | Views do not import models from other apps at module level | Pass |
| `test_god_views.py` | No view file exceeds 300 lines | Pass |
| `test_god_models.py` | No model file exceeds 400 lines | Pass |
| `test_import_rules.py` | No forbidden imports in new/modified files | Pass |

---

## 8. Testing Strategy

### 8.1 Test Tiers Required

| Tier | Scope | Requirement |
|------|-------|-------------|
| **Unit** | Refactored modules using new interfaces | No coverage requirement (behavior unchanged) |
| **Integration** | Existing API endpoints | All existing tests must pass |
| **Architecture** | Circular dependencies, import boundaries | 0 failures |
| **Regression** | Full test suite | No test failures |

### 8.2 Circular Dependency Detection

Run the following commands to catalog circular dependencies before and after changes:

```bash
# Before
pytest tests/architecture/test_circular_deps.py -v

# After each change
pytest tests/architecture/test_circular_deps.py -v
```

### 8.3 Existing Test Preservation

All existing tests must continue to pass without modification. The refactor is purely architectural — no business logic changes.

### 8.4 Architecture Tests

Run `pytest tests/architecture/ -v --tb=short` after all changes. All tests must pass.

### 8.5 Forbidden Test Patterns

- No `time.sleep()` in tests.
- No test dependencies on execution order.
- No hardcoded test data (use factories).
- No mocking Django ORM in migration tests (not applicable — no migrations in this PR).
- No direct database access in unit tests (use model methods or ORM).

---

## 9. Migration Strategy

### 9.1 Circular Dependency Catalog

Before making any changes, run the architecture tests to identify all remaining circular dependencies:

```bash
pytest tests/architecture/test_circular_deps.py -v --tb=short
```

Document each circular dependency chain:
- Source app → Target app → Source app (cycle description)
- Files involved in the cycle
- Recommended resolution strategy

### 9.2 Resolution Strategies

Apply the appropriate strategy for each circular dependency:

**Strategy 1: Introduce interfaces in `shared/`**
```python
# shared/interfaces.py
from typing import Protocol

class PaymentNotifier(Protocol):
    def notify_payment_completed(self, payment_id: int) -> None: ...

# properties/services/rent_service.py
from shared.interfaces import PaymentNotifier

class RentService:
    def __init__(self, payment_notifier: PaymentNotifier) -> None:
        self.payment_notifier = payment_notifier

    def process_rent(self, ...):
        self.payment_notifier.notify_payment_completed(...)
```

**Strategy 2: Dependency injection**
```python
# properties/views/rent_views.py
def process_rent(request, payment_service):
    # payment_service is injected, not imported
    payment_service.process(...)
```

**Strategy 3: Callback patterns**
```python
# properties/signals.py
from django.dispatch import Signal

rent_processed = Signal()

# payments/receivers.py
def on_rent_processed(sender, **kwargs):
    # Handle payment-related logic
    pass

rent_processed.connect(on_rent_processed)
```

**Strategy 4: Move shared types to `shared/`**
```python
# shared/types.py
class RentStatus:
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"

# Used by both properties/ and payments/
```

### 9.3 Implementation Order

Resolve circular dependencies in this order:
1. Catalog all remaining cycles.
2. Prioritize cycles that are easiest to resolve (e.g., simple type moves to `shared/`).
3. Resolve one cycle at a time, running architecture tests after each resolution.
4. Do not batch multiple cycle resolutions in a single commit — each resolution should be independently reviewable.

### 9.4 Data Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Business behavior change | Low | High | All existing tests must pass; verify API responses match |
| New circular dependency introduced | Low | High | `test_circular_deps.py` must pass after each change |
| Interface design flaw | Low | Medium | Staff Engineer reviews interface design |
| Import regression | Low | Medium | Architecture tests enforce import boundaries |

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
   git revert <PR-008E-merge-commit-sha>
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
   1. Apply PR-008E to staging.
   2. Verify all architecture tests pass.
   3. Execute rollback steps 1-4 above.
   4. Verify all existing tests still pass.
   5. Verify `import-linter check` passes.
   6. Re-apply PR-008E after successful rollback test.

---

## 11. Expected Git Diff

### 11.1 Summary

| Metric | Value |
|--------|-------|
| Files changed | ~5 (2 new, 3 modified, 0 deleted) |
| Files added | ~2 |
| Files modified | ~3 |
| Files deleted | 0 |
| Lines added | ~100 |
| Lines removed | ~50 |
| Net change | ~50 lines |

### 11.2 Files Added (~100 lines)

| File | Approx Lines | Description |
|------|---------------|-------------|
| `shared/interfaces.py` | ~50 | New interfaces/protocols to break circular dependencies |
| `shared/types.py` | ~50 | Shared types moved from app packages |

### 11.3 Files Modified (~100 lines)

| File | Approx Lines Changed | Description |
|------|----------------------|-------------|
| Circular dependency source files | +50, -50 | Refactored to use `shared/` interfaces, DI, or callbacks |

### 11.4 Diff Constraints

- No file in the diff may exceed 400 lines total after modification.
- No database migrations.
- No model field changes.
- No serializer changes.
- No API endpoint changes.
- No business logic changes.

---

## 12. Definition of Done

PR-008E is **Done** when ALL of the following are true.

### Code
- [ ] All circular dependency chains identified by `test_circular_deps.py` are resolved.
- [ ] `shared/interfaces.py` (or relevant submodule) contains new interfaces/protocols.
- [ ] `shared/types.py` (or relevant submodule) contains moved shared types.
- [ ] No new circular dependencies introduced.
- [ ] All refactored files comply with dependency matrix.

### Tests
- [ ] All existing tests pass (no regressions).
- [ ] `pytest tests/architecture/test_circular_deps.py -v` passes with 0 failures.
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.

### CI
- [ ] `ruff check .` passes (0 errors).
- [ ] `ruff format --check .` passes.
- [ ] `mypy .` passes (0 errors).
- [ ] `import-linter check` passes (0 violations).
- [ ] `pytest tests/ -v` passes.
- [ ] `pytest tests/architecture/ -v` passes.
- [ ] `python manage.py check` passes.

### Architecture
- [ ] No circular dependencies between app packages.
- [ ] `shared/` contains only interfaces and types (no concrete implementations).
- [ ] `import-linter.ini` matches ADR-006 v1.1 matrix.
- [ ] No architecture rules weakened.

### Documentation
- [ ] CHANGELOG.md updated.
- [ ] PR description includes summary of circular dependencies resolved.

### Deployment
- [ ] PR approved by Platform Team Lead, Staff Engineer, and Architecture Review Board (if ADR exception required).
- [ ] Merged to `phase-0-foundation` branch.
- [ ] Deployed to staging.
- [ ] Staging validation passed (24 hours).
- [ ] No production incidents during staging validation.

---

## 13. Developer Checklist

### Pre-Implementation
- [ ] Verify PR-008D is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes (baseline).
- [ ] Verify `import-linter check` passes (baseline).
- [ ] Run `pytest tests/ -v` and verify all pass (baseline).
- [ ] Catalog all circular dependencies from `test_circular_deps.py`.
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Dependency Rules, Import Rules, Interface Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Refactoring Rules.
- [ ] Confirm no architecture rules may be weakened to accommodate circular dependencies.

### Implementation
- [ ] Run `pytest tests/architecture/test_circular_deps.py -v` and catalog all cycles.
- [ ] For each cycle, select resolution strategy (interface, DI, callback, or type move).
- [ ] Create `shared/interfaces.py` or relevant submodule with new interfaces.
- [ ] Create `shared/types.py` or relevant submodule with moved shared types.
- [ ] Refactor source files to use `shared/` interfaces, DI, or callbacks.
- [ ] Run `pytest tests/architecture/test_circular_deps.py -v` after each resolution.
- [ ] Verify no new circular dependencies introduced.

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
- [ ] Verify `pytest tests/architecture/test_circular_deps.py -v` passes.
- [ ] Verify no circular dependencies remain.
- [ ] Verify `shared/` contains only interfaces and types (no concrete app logic).
- [ ] Verify no cross-app imports at module level in refactored files.

### Rollback
- [ ] Document rollback plan in PR description.
- [ ] Test rollback on staging: apply PR-008E, verify architecture tests pass, execute rollback, verify all tests still pass.

### PR
- [ ] Commit message follows conventional commits format.
- [ ] Branch name follows `<type>/<ticket-id>-<description>` format.
- [ ] PR description includes: summary, motivation, changes, testing, rollback plan.
- [ ] PR size is within limits (~50 lines, 5 files).
- [ ] PR is linked to Phase 0 Architecture Cleanup task.

---

## 14. Reviewer Checklist

Use this checklist when reviewing PR-008E.

### Architecture
- [ ] All circular dependency chains are resolved.
- [ ] `shared/interfaces.py` (or submodule) contains abstract interfaces only.
- [ ] `shared/types.py` (or submodule) contains shared types only.
- [ ] No new circular dependencies introduced.
- [ ] No architecture rules weakened.
- [ ] `import-linter.ini` matches ADR-006 v1.1 matrix.
- [ ] All architecture tests pass.

### Code Quality
- [ ] Ruff passes (0 errors, 0 formatting issues).
- [ ] MyPy passes (0 errors).
- [ ] No `print()` statements.
- [ ] No `# TODO` or `# FIXME` comments.
- [ ] No commented-out code.
- [ ] Business behavior is preserved (no logic changes).
- [ ] Interfaces are abstract and reusable.

### Testing
- [ ] All existing tests pass (no regressions).
- [ ] `pytest tests/architecture/test_circular_deps.py -v` passes with 0 failures.
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.

### CI
- [ ] All CI gates pass.
- [ ] No import-linter violations.
- [ ] No architecture test failures.
- [ ] No circular dependency warnings.

### Documentation
- [ ] CHANGELOG.md updated.
- [ ] PR description includes summary of circular dependencies resolved.

---

## 15. AI Checklist

Use this checklist when generating PR-008E with AI assistance.

### Pre-Generation
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Dependency Rules, Import Rules, Interface Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Dependency Rules, Refactoring Rules.
- [ ] Verify PR-008D is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes on baseline.
- [ ] Verify `import-linter check` passes on baseline.
- [ ] Catalog all circular dependencies from `test_circular_deps.py`.
- [ ] Confirm no architecture rules may be weakened.

### Code Generation
- [ ] Run `pytest tests/architecture/test_circular_deps.py -v` and catalog all cycles.
- [ ] For each cycle, select resolution strategy (interface, DI, callback, or type move).
- [ ] Create `shared/interfaces.py` or relevant submodule with new interfaces.
- [ ] Create `shared/types.py` or relevant submodule with moved shared types.
- [ ] Refactor source files to use `shared/` interfaces, DI, or callbacks.
- [ ] **Do NOT** modify business logic in any file.
- [ ] **Do NOT** add database migrations.
- [ ] **Do NOT** change model fields or serializers.
- [ ] **Do NOT** change API endpoints or contracts.
- [ ] **Do NOT** introduce new features.
- [ ] **Do NOT** weaken architecture rules.

### Test Generation
- [ ] No new test files required (existing tests must pass unchanged).
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
- [ ] Verify no circular dependencies remain.
- [ ] Verify `shared/` contains only interfaces and types.

### Stop and Ask Conditions
AI must **stop and ask human** before proceeding if:
- [ ] Any required change would modify business logic.
- [ ] Any required change would need a database migration.
- [ ] A circular dependency cannot be resolved without weakening architecture rules or requiring an ADR exception.
- [ ] Any CI gate fails after 3 fix attempts.
- [ ] Existing tests fail and cannot be fixed without changing test expectations.

### Commit
- [ ] Commit message follows format: `refactor(architecture): resolve circular dependencies between app packages`.
- [ ] Commit body explains: circular dependencies identified, resolution strategy applied, interfaces/types added to `shared/`.
- [ ] Branch name: `refactor/phase-0-008e-resolve-circular-dependencies`.

---

## 16. Stop-and-Ask Conditions

STOP and ask the Principal Software Architect if:

1. Any required fix would change business logic, model definitions, serializers, or API contracts.
2. Any required fix would need a database migration.
3. A circular dependency cannot be resolved without weakening architecture rules or requiring an ADR exception.
4. Any existing test fails and cannot be fixed without changing test expectations.
5. Any CI gate fails after 3 fix attempts.

---

## Appendix A: Architecture Decision References

| Decision | Reference |
|----------|-----------|
| No circular dependencies between app packages | ADR-006 v1.1 §5.1 |
| `shared/` owns interfaces and shared types | ADR-001, ADR-005 |
| Lazy imports as transitional pattern | ADR-006 v1.1 §5.3 |
| Architecture tests enforce all rules | ADR-006 v1.1 §5.2 |
| Dependency injection and callbacks as resolution strategies | ADR-006 v1.1 §5.3 |

---

## Appendix B: Related Documents

- [Architecture v1.1 Release Candidate](../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Architecture v1.1 Implementation Master Plan — Phase 0](../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan — PR-008](../PHASE_0_EXECUTION_PLAN.md)
- [Engineering Standards](../ENGINEERING_STANDARDS.md)
- [AI Engineering Playbook](../AI_ENGINEERING_PLAYBOOK.md)
- [Import Rules ADR](../docs/architecture/adr/ADR-006_import_rules.md)
- [Shared Kernel Rules ADR](../docs/architecture/adr/ADR-005_shared_kernel_rules.md)
- [Bounded Context Strategy ADR](../docs/architecture/adr/ADR-001_bounded_context_strategy.md)

---

## Appendix C: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-20 | Principal Software Architect | Initial PR-008E specification for Architecture Cleanup Phase 1 |

**Next Review:** After PR-008E merge
**Approval Required:** Platform Team Lead, Staff Engineer, Architecture Review Board (if ADR exception required)

---

*End of PR-008E Implementation Specification*
