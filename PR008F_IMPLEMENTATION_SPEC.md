# PR-008F Implementation Specification

## Final architecture compliance and cleanup

---

## 1. Purpose

Perform final architecture compliance verification after PR-008A through PR-008E have been merged. This PR ensures all bounded-context violations are resolved, all architecture regression tests pass, `import-linter` configuration is correct, and any remaining cleanup is performed. No new refactoring work — only verification, minor fixes, and cleanup.

This PR is **blocked until PR-008E is merged** because:
1. All prior architecture cleanup must be completed before final verification
2. `import-linter check` must pass on the fully cleaned-up codebase
3. Any remaining minor violations must be identified and resolved

---

## 2. Scope

### 2.1 In Scope

- Run full architecture test suite (`pytest tests/architecture/ -v`) and verify 0 failures
- Run `import-linter check` and verify 0 violations
- Fix any remaining minor import violations or architecture test failures
- Update `import-linter.ini` if new app-level utilities were introduced in prior PRs
- Remove any temporary files, shims, or compatibility code introduced during the cleanup phase
- Verify all CI gates pass on the fully cleaned-up codebase
- Update documentation to reflect Architecture Cleanup Phase 1 completion

### 2.2 Out of Scope

- Any new refactoring work beyond fixing minor violations found during final verification
- Removing `rentsecure_be/` imports (PR-008A)
- SDK isolation work (PR-008B)
- Removing cross-context imports (PR-008C)
- God view/model splitting (PR-008D)
- Circular dependency resolution (PR-008E)
- Any changes to business logic, model definitions, or serializer definitions
- Any database migrations or schema changes
- Any API endpoint changes or new endpoints
- Any changes to `core/views/bank_views.py`
- Any changes to `properties/views/unit_views.py` or `properties/models/unit_models.py`
- Any changes to `shared/` package structure beyond minor cleanup

---

## 3. Files

### 3.1 Files to Create

None.

### 3.2 Files to Modify

| File | Change | Owner |
|------|--------|-------|
| `import-linter.ini` | Update if new app-level utilities were introduced in prior PRs | Platform Team |
| `docs/architecture/contexts/*.md` | Update bounded context ownership if changed during cleanup | Platform Team |
| `CHANGELOG.md` | Document Architecture Cleanup Phase 1 completion | Platform Team |
| Any files with minor remaining violations | Fix import or architecture violations | Platform Team |

### 3.3 Files to Delete

| File | Reason | Owner |
|------|--------|-------|
| Any temporary compatibility shims | Remove temporary code introduced during cleanup phase | Platform Team |

---

## 4. Responsibilities

| Role | Responsibility |
|------|----------------|
| **Platform Team Lead** | Approves final compliance state; verifies all architecture tests pass; owns PR merge |
| **Staff Engineer** | Reviews final architecture state; verifies dependency matrix compliance |
| **Architecture Review Board** | Signs off on Architecture Cleanup Phase 1 completion |
| **Developer** | Fixes minor violations, updates config, runs full validation |
| **AI Assistant** | Generates fixes for minor violations per this spec; stops and asks if new refactoring is required |

---

## 5. Acceptance Criteria

### 5.1 Functional

- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
- [ ] `import-linter.ini` is up to date and reflects the current app structure.
- [ ] Any remaining minor import violations are fixed.
- [ ] Any temporary compatibility shims are removed.
- [ ] All CI gates pass on the fully cleaned-up codebase.
- [ ] All existing tests continue to pass (no behavioral regressions).

### 5.2 Non-Functional

- [ ] No business behavior changes (all existing tests pass).
- [ ] No database migrations required.
- [ ] No model field changes.
- [ ] No serializer changes.
- [ ] No API contract changes.
- [ ] Architecture Cleanup Phase 1 is fully complete and verified.

---

## 6. Architecture Rules

### 6.1 Bounded Context Compliance

- All bounded contexts must comply with the v1.1 dependency matrix.
- No `rentsecure_be/` imports may remain in application code.
- No payment SDK imports may exist outside `payments/adapters/`.
- No cross-context imports at module level (transitional lazy imports must be minimized).
- No view file may exceed 300 lines.
- No model file may exceed 400 lines.
- No circular dependencies may exist between app packages.

### 6.2 Import Rules

**Critical dependency matrix constraints per ADR-006 v1.1:**

| Source | shared | platform | identity | property | payment | notification | document |
|--------|--------|----------|----------|----------|---------|--------------|----------|
| **core** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **properties** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **payments** | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| **notification** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **documents** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Final state requirements:**
- `core/` → `shared/` only
- `properties/` → `shared/` only
- `payments/` → `shared/`, `properties/`
- `notification/` → `shared/` only
- `documents/` → `shared/` only

### 6.3 Cleanup Rules

- Temporary compatibility shims introduced during cleanup must be removed.
- Lazy imports that are no longer needed must be replaced with direct imports where permitted.
- Any unused `__init__.py` files or empty modules must be removed.
- `import-linter.ini` must accurately reflect the current app structure.

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
| `test_shared_purity.py` | `shared/` does not import Django or apps | Pass |

---

## 8. Testing Strategy

### 8.1 Test Tiers Required

| Tier | Scope | Requirement |
|------|-------|-------------|
| **Unit** | Any minor fixes made during verification | No coverage requirement (behavior unchanged) |
| **Integration** | Existing API endpoints | All existing tests must pass |
| **Architecture** | Full architecture test suite | 0 failures |
| **Regression** | Full test suite | No test failures |

### 8.2 Architecture Test Verification

Run the full architecture test suite and verify all tests pass:

```bash
pytest tests/architecture/ -v --tb=short
```

Expected result: All 640+ tests pass with 0 failures.

### 8.3 Import-Linter Verification

Run import-linter and verify 0 violations:

```bash
import-linter check
```

Expected result: 0 violations.

### 8.4 Existing Test Preservation

All existing tests must continue to pass without modification. If minor fixes are required:
- Make the smallest possible change to resolve the violation.
- Do not introduce new business logic.

### 8.5 Forbidden Test Patterns

- No `time.sleep()` in tests.
- No test dependencies on execution order.
- No hardcoded test data (use factories).
- No mocking Django ORM in migration tests (not applicable — no migrations in this PR).
- No direct database access in unit tests (use model methods or ORM).

---

## 9. Migration Strategy

### 9.1 Final Verification Checklist

Run the following verification sequence:

1. **Lint and format:**
   ```bash
   ruff check .
   ruff format --check .
   ```

2. **Type check:**
   ```bash
   mypy .
   ```

3. **Import rules:**
   ```bash
   import-linter check
   ```

4. **Tests:**
   ```bash
   pytest tests/ -v
   ```

5. **Architecture tests:**
   ```bash
   pytest tests/architecture/ -v --tb=short
   ```

6. **Django check:**
   ```bash
   python manage.py check
   ```

7. **Circular dependency check:**
   ```bash
   pytest tests/architecture/test_circular_deps.py -v
   ```

8. **SDK placement check:**
   ```bash
   pytest tests/architecture/test_sdk_placement.py -v
   ```

9. **Rentsecure_be boundary check:**
   ```bash
   pytest tests/architecture/test_rentsecure_be_boundary.py -v
   ```

10. **God views/models check:**
    ```bash
    pytest tests/architecture/test_god_views.py -v
    pytest tests/architecture/test_god_models.py -v
    ```

### 9.2 Minor Violation Fixes

If any minor violations are found during final verification:

1. **Document the violation** in the PR description.
2. **Fix the violation** with the smallest possible change.
3. **Re-run architecture tests** to verify the fix.
4. **Do not introduce new refactoring** beyond fixing the identified violation.

### 9.3 Temporary Shim Removal

If temporary compatibility shims were introduced during PR-008A through PR-008E:

1. **Verify the shim is no longer needed** by checking that all importers have been updated.
2. **Remove the shim** and delete the file or code block.
3. **Run tests** to verify no `ImportError` or `AttributeError` is introduced.
4. **Re-run architecture tests** to verify compliance.

### 9.4 import-linter.ini Update

If new app-level utilities were introduced in prior PRs (e.g., `payments/utils/`, `properties/services/`):

1. **Review `import-linter.ini`** to ensure it reflects the current app structure.
2. **Add new packages** to the allowed layers if needed.
3. **Verify `import-linter check`** passes after updates.

### 9.5 Data Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Minor violation missed | Low | Medium | Run full architecture test suite |
| Temporary shim removal breaks import | Low | Medium | Verify all importers updated before removal |
| import-linter.ini out of date | Low | Low | Review and update during final verification |
| Business behavior change | Low | High | All existing tests must pass |

---

## 10. Rollback Plan

### 10.1 Rollback Triggers

Rollback is triggered if any of the following occur:
- Any existing test fails after changes.
- `import-linter check` returns violations.
- Any architecture regression test fails.
- Business behavior changes detected.
- CI pipeline cannot be fixed within 30 minutes.

### 10.2 Rollback Steps

1. **Git revert:**
   ```bash
   git revert <PR-008F-merge-commit-sha>
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
   1. Apply PR-008F to staging.
   2. Verify all architecture tests pass.
   3. Execute rollback steps 1-4 above.
   4. Verify all existing tests still pass.
   5. Verify `import-linter check` passes.
   6. Re-apply PR-008F after successful rollback test.

---

## 11. Expected Git Diff

### 11.1 Summary

| Metric | Value |
|--------|-------|
| Files changed | ~5 (0 new, 3 modified, 2 deleted) |
| Files added | 0 |
| Files modified | ~3 |
| Files deleted | ~2 |
| Lines added | ~20 |
| Lines removed | ~20 |
| Net change | ~0 lines (minor fixes and cleanup) |

### 11.2 Files Modified (~20 lines)

| File | Approx Lines Changed | Description |
|------|----------------------|-------------|
| `import-linter.ini` | +5, -0 | Update if new packages were introduced |
| `docs/architecture/contexts/*.md` | +5, -5 | Update bounded context ownership if changed |
| `CHANGELOG.md` | +10, -0 | Document Architecture Cleanup Phase 1 completion |
| Any files with minor violations | +5, -5 | Fix minor import or architecture violations |

### 11.3 Files Deleted (~20 lines)

| File | Approx Lines | Description |
|------|---------------|-------------|
| Temporary compatibility shims | ~10 | Remove temporary code introduced during cleanup |
| Unused empty modules | ~10 | Remove unused `__init__.py` or empty modules |

### 11.4 Diff Constraints

- No file in the diff may exceed 400 lines total after modification.
- No database migrations.
- No model field changes.
- No serializer changes.
- No API endpoint changes.
- No new business logic.
- No new features.

---

## 12. Definition of Done

PR-008F is **Done** when ALL of the following are true.

### Code
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
- [ ] `import-linter.ini` is up to date.
- [ ] Any remaining minor violations are fixed.
- [ ] Any temporary compatibility shims are removed.
- [ ] No unused empty modules remain.

### Tests
- [ ] All existing tests pass (no regressions).
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
- [ ] No `rentsecure_be/` imports in application code.
- [ ] No payment SDK imports outside `payments/adapters/`.
- [ ] No cross-context imports at module level.
- [ ] No view file exceeds 300 lines.
- [ ] No model file exceeds 400 lines.
- [ ] No circular dependencies.
- [ ] `import-linter.ini` matches ADR-006 v1.1 matrix.
- [ ] All architecture rules are enforced.

### Documentation
- [ ] `docs/architecture/contexts/*.md` updated if bounded context ownership changed.
- [ ] ADR-006 updated if dependency matrix changed (should not change in this PR).
- [ ] CHANGELOG.md updated with Architecture Cleanup Phase 1 completion.

### Deployment
- [ ] PR approved by Platform Team Lead, Staff Engineer, and Architecture Review Board.
- [ ] Merged to `phase-0-foundation` branch.
- [ ] Deployed to staging.
- [ ] Staging validation passed (24 hours).
- [ ] No production incidents during staging validation.
- [ ] Architecture Cleanup Phase 1 signed off by Architecture Review Board.

---

## 13. Developer Checklist

### Pre-Implementation
- [ ] Verify PR-008E is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes (baseline).
- [ ] Verify `import-linter check` passes (baseline).
- [ ] Run `pytest tests/ -v` and verify all pass (baseline).
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Import Rules, Dependency Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Refactoring Rules.
- [ ] Catalog any remaining minor violations from architecture tests.

### Implementation
- [ ] Run full architecture test suite and catalog any remaining failures.
- [ ] Fix any remaining minor import violations.
- [ ] Fix any remaining architecture test failures.
- [ ] Update `import-linter.ini` if new packages were introduced.
- [ ] Remove any temporary compatibility shims.
- [ ] Remove any unused empty modules.
- [ ] Update `docs/architecture/contexts/*.md` if bounded context ownership changed.
- [ ] Update `CHANGELOG.md`.

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
- [ ] Verify full architecture test suite passes.
- [ ] Verify `import-linter check` passes.
- [ ] Verify no `rentsecure_be/` imports remain.
- [ ] Verify no payment SDK imports outside `payments/adapters/`.
- [ ] Verify no cross-context imports at module level.
- [ ] Verify no view file exceeds 300 lines.
- [ ] Verify no model file exceeds 400 lines.
- [ ] Verify no circular dependencies.
- [ ] Verify `import-linter.ini` is up to date.
- [ ] Verify temporary shims are removed.

### Rollback
- [ ] Document rollback plan in PR description.
- [ ] Test rollback on staging: apply PR-008F, verify architecture tests pass, execute rollback, verify all tests still pass.

### PR
- [ ] Commit message follows conventional commits format.
- [ ] Branch name follows `<type>/<ticket-id>-<description>` format.
- [ ] PR description includes: summary, motivation, changes, testing, rollback plan.
- [ ] PR size is within limits (~0 net lines, 5 files).
- [ ] PR is linked to Phase 0 Architecture Cleanup task.

---

## 14. Reviewer Checklist

Use this checklist when reviewing PR-008F.

### Architecture
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
- [ ] `import-linter.ini` is up to date.
- [ ] No `rentsecure_be/` imports remain in application code.
- [ ] No payment SDK imports outside `payments/adapters/`.
- [ ] No cross-context imports at module level.
- [ ] No view file exceeds 300 lines.
- [ ] No model file exceeds 400 lines.
- [ ] No circular dependencies.
- [ ] All architecture rules are enforced.
- [ ] Architecture Cleanup Phase 1 is fully complete.

### Code Quality
- [ ] Ruff passes (0 errors, 0 formatting issues).
- [ ] MyPy passes (0 errors).
- [ ] No `print()` statements.
- [ ] No `# TODO` or `# FIXME` comments.
- [ ] No commented-out code.
- [ ] Business behavior is preserved (no logic changes).

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
- [ ] `docs/architecture/contexts/*.md` updated if bounded context ownership changed.
- [ ] ADR-006 updated if dependency matrix changed.
- [ ] CHANGELOG.md updated with Architecture Cleanup Phase 1 completion.
- [ ] PR description includes summary of final verification and any minor fixes applied.

---

## 15. AI Checklist

Use this checklist when generating PR-008F with AI assistance.

### Pre-Generation
- [ ] Read `ENGINEERING_STANDARDS.md` sections: Import Rules, Dependency Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Refactoring Rules.
- [ ] Verify PR-008E is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes on baseline.
- [ ] Verify `import-linter check` passes on baseline.
- [ ] Catalog any remaining minor violations from architecture tests.
- [ ] Confirm Architecture Cleanup Phase 1 is ready for final verification.

### Code Generation
- [ ] Run full architecture test suite and catalog any remaining failures.
- [ ] Fix any remaining minor import violations with smallest possible changes.
- [ ] Fix any remaining architecture test failures.
- [ ] Update `import-linter.ini` if new packages were introduced.
- [ ] Remove any temporary compatibility shims.
- [ ] Remove any unused empty modules.
- [ ] Update `docs/architecture/contexts/*.md` if bounded context ownership changed.
- [ ] Update `CHANGELOG.md`.
- [ ] **Do NOT** introduce new refactoring beyond fixing identified violations.
- [ ] **Do NOT** modify business logic.
- [ ] **Do NOT** add database migrations.
- [ ] **Do NOT** change model fields or serializers.
- [ ] **Do NOT** change API endpoints or contracts.
- [ ] **Do NOT** introduce new features.

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
- [ ] Verify no `rentsecure_be/` imports remain.
- [ ] Verify no payment SDK imports outside `payments/adapters/`.
- [ ] Verify no cross-context imports at module level.
- [ ] Verify no circular dependencies.
- [ ] Verify `import-linter.ini` is up to date.
- [ ] Verify temporary shims are removed.

### Stop and Ask Conditions
AI must **stop and ask human** before proceeding if:
- [ ] Any required fix would modify business logic.
- [ ] Any required fix would need a database migration.
- [ ] A remaining violation requires new refactoring beyond the scope of PR-008A through PR-008E.
- [ ] Any CI gate fails after 3 fix attempts.
- [ ] Existing tests fail and cannot be fixed without changing test expectations.

### Commit
- [ ] Commit message follows format: `refactor(architecture): final architecture compliance and cleanup for Phase 1`.
- [ ] Commit body explains: all architecture tests pass, import-linter passes, minor fixes applied, temporary shims removed.
- [ ] Branch name: `refactor/phase-0-008f-final-compliance-cleanup`.

---

## 16. Stop-and-Ask Conditions

STOP and ask the Principal Software Architect if:

1. Any required fix would change business logic, model definitions, serializers, or API contracts.
2. Any required fix would need a database migration.
3. A remaining violation requires new refactoring beyond the scope of PR-008A through PR-008E.
4. Temporary shims cannot be removed without breaking external consumers (not expected — `rentsecure_be/` is internal).
5. Any existing test fails and cannot be fixed without changing test expectations.
6. Any CI gate fails after 3 fix attempts.

---

## Appendix A: Architecture Decision References

| Decision | Reference |
|----------|-----------|
| No app may import from `rentsecure_be/` | ADR-006 v1.1 §5.1 Rule 1 |
| Payment SDKs confined to `payments/adapters/` | ADR-006 v1.1 §5.4 |
| No view file exceeds 300 lines | ADR-006 v1.1 §5.3 |
| No model file exceeds 400 lines | ADR-006 v1.1 §5.3 |
| No circular dependencies between app packages | ADR-006 v1.1 §5.1 |
| Lazy imports as transitional pattern | ADR-006 v1.1 §5.3 |
| Architecture tests enforce all rules | ADR-006 v1.1 §5.2 |
| `payments/` bounded context ownership | ADR-004 |
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
- [Payment Architecture ADR](../docs/architecture/adr/ADR-004_payment_architecture.md)
- [Shared Kernel Rules ADR](../docs/architecture/adr/ADR-005_shared_kernel_rules.md)
- [Bounded Context Strategy ADR](../docs/architecture/adr/ADR-001_bounded_context_strategy.md)

---

## Appendix C: Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-20 | Principal Software Architect | Initial PR-008F specification for Architecture Cleanup Phase 1 |

**Next Review:** After PR-008F merge
**Approval Required:** Platform Team Lead, Staff Engineer, Architecture Review Board

---

*End of PR-008F Implementation Specification*
