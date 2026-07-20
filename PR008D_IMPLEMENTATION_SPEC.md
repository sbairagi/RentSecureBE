# PR-008D Implementation Specification

## Split remaining god views and god models

---

## 1. Purpose

Refactor the two remaining oversized files that violate the architecture file-size limits: `properties/views/unit_views.py` (358 lines, limit 300) and `properties/models/unit_models.py` (482 lines, limit 400). Extract helper functions and mixins into separate modules to bring both files within compliance. No functional changes — pure structural refactor.

This PR is **blocked until PR-008C is merged** because:
1. Cross-context import violations must be resolved before refactoring file sizes
2. `import-linter check` must pass on baseline before structural changes
3. All architecture tests must be green before size-limit fixes are applied

---

## 2. Scope

### 2.1 In Scope

- Extract helper functions from `properties/views/unit_views.py` into `properties/views/unit_helpers.py`
- Extract mixins from `properties/models/unit_models.py` into `properties/models/unit_mixins.py`
- Verify both files are within size limits after refactoring
- Verify `pytest tests/architecture/ -v` passes with 0 failures
- Verify all existing tests continue to pass

### 2.2 Out of Scope

- Any changes to business logic, model field definitions, or serializer definitions
- Any database migrations or schema changes
- Any API endpoint changes or new endpoints
- Removing `rentsecure_be/` imports (PR-008A)
- SDK isolation work (PR-008B)
- Removing cross-context imports (PR-008C)
- Circular dependency resolution (PR-008E)
- Final architecture compliance verification (PR-008F)
- Any changes to `core/views/bank_views.py`
- Any changes to `properties/views/rent_record_views.py`
- Any changes to `documents/views.py` or `documents/utils.py`
- Any changes to `shared/` package structure

---

## 3. Files

### 3.1 Files to Create

| File | Purpose | Owner |
|------|---------|-------|
| `properties/views/unit_helpers.py` | Extract standalone helper functions from `properties/views/unit_views.py` | Platform Team |
| `properties/models/unit_mixins.py` | Extract mixins from `properties/models/unit_models.py` | Platform Team |

### 3.2 Files to Modify

| File | Change | Owner |
|------|--------|-------|
| `properties/views/unit_views.py` | Remove extracted helper functions; update imports from `unit_helpers`; reduce line count below 300 | Platform Team |
| `properties/models/unit_models.py` | Remove extracted mixins; update imports from `unit_mixins`; reduce line count below 400 | Platform Team |

### 3.3 Files to Delete

None.

---

## 4. Responsibilities

| Role | Responsibility |
|------|----------------|
| **Platform Team Lead** | Approves extraction approach; verifies no business behavior changes; owns PR merge |
| **Staff Engineer** | Reviews mixin and helper extraction; verifies no new circular dependencies |
| **Developer** | Extracts helpers and mixins, updates imports, runs full validation |
| **AI Assistant** | Generates extracted modules and import updates per this spec; stops and asks if business logic extraction is required |

---

## 5. Acceptance Criteria

### 5.1 Functional

- [ ] `properties/views/unit_views.py` is under 300 lines.
- [ ] `properties/models/unit_models.py` is under 400 lines.
- [ ] `properties/views/unit_helpers.py` contains extracted standalone helper functions with no new cross-app imports.
- [ ] `properties/models/unit_mixins.py` contains extracted mixins with no new cross-app imports.
- [ ] All original functionality is preserved (same behavior, same API contracts).
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
- [ ] All existing tests continue to pass (no behavioral regressions).

### 5.2 Non-Functional

- [ ] No business behavior changes (all existing tests pass).
- [ ] No database migrations required.
- [ ] No model field changes.
- [ ] No serializer changes.
- [ ] No API contract changes.
- [ ] PR-007 architecture tests remain green after PR-008D changes.

---

## 6. Architecture Rules

### 6.1 Bounded Context Compliance

- `properties/` owns all extracted helpers and mixins.
- Extracted modules must be placed in the same app (`properties/`).
- Extracted helpers and mixins must not introduce new cross-app imports.

### 6.2 Import Rules

**Critical dependency matrix constraints per ADR-006 v1.1:**

| Source | shared | platform | identity | property | payment | notification | document |
|--------|--------|----------|----------|----------|---------|--------------|----------|
| **properties** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Implications for this PR:**
- `properties/views/unit_helpers.py` must not import from `payments/`, `notification/`, or any other app outside `properties/` and `shared/`.
- `properties/models/unit_mixins.py` must not import from `payments/`, `notification/`, or any other app outside `properties/` and `shared/`.
- All imports in extracted modules must be intra-app (`properties/` → `properties/`) or from `shared/`.

### 6.3 View Rules

- View files must not exceed 300 lines.
- If a view file exceeds 300 lines, extract standalone helper functions into a separate module (e.g., `properties/views/unit_helpers.py`).
- Extracted helpers must not introduce new cross-app imports.
- Views must not import models from other apps at module level.
- Do not extract ViewSet classes — extract standalone functions only.

### 6.4 Model Rules

- Model files must not exceed 400 lines.
- If a model file exceeds 400 lines, extract mixins or proxy models into separate modules.
- Extracted mixins must be placed in the same app (e.g., `properties/models/unit_mixins.py`).
- Do not change model inheritance hierarchy.

### 6.5 Extraction Rules

- Extracted functions must remain in the same app (`properties/`).
- Extracted mixins must be in the same app (`properties/`).
- Extracted code must not contain business logic changes.
- Extracted code must preserve the original function signatures and class interfaces.
- No new cross-app imports may be introduced in extracted modules.

### 6.6 Naming Rules

- Extracted helper module: `properties/views/unit_helpers.py`.
- Extracted mixin module: `properties/models/unit_mixins.py`.
- Mixin classes must use `Mixin` suffix (e.g., `AddressMixin`, `AmenityMixin`, `ImageMixin`).

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
| `test_god_views.py` | No view file exceeds 300 lines | Pass |
| `test_god_models.py` | No model file exceeds 400 lines | Pass |
| `test_properties_isolation.py` | `properties/` does not import from `payments/` or `notification/` | Pass |
| `test_rentsecure_be_boundary.py` | No app imports from `rentsecure_be/` | Pass |
| `test_layer_compliance.py` | Views do not import models from other apps at module level | Pass |
| `test_circular_deps.py` | No circular dependencies between app packages | Pass |
| `test_import_rules.py` | No forbidden imports in new/modified files | Pass |

---

## 8. Testing Strategy

### 8.1 Test Tiers Required

| Tier | Scope | Requirement |
|------|-------|-------------|
| **Unit** | Extracted helper functions and mixins | No coverage requirement (behavior unchanged) |
| **Integration** | Existing API endpoints | All existing tests must pass |
| **Architecture** | File size limits, import boundaries | 0 failures |
| **Regression** | Full test suite | No test failures |

### 8.2 Existing Test Preservation

All existing tests must continue to pass without modification. The refactor is purely structural — no business logic changes.

### 8.3 Architecture Tests

Run `pytest tests/architecture/ -v --tb=short` after all changes. All tests must pass, specifically:
- `test_god_views.py` — `properties/views/unit_views.py` < 300 lines
- `test_god_models.py` — `properties/models/unit_models.py` < 400 lines

### 8.4 Forbidden Test Patterns

- No `time.sleep()` in tests.
- No test dependencies on execution order.
- No hardcoded test data (use factories).
- No mocking Django ORM in migration tests (not applicable — no migrations in this PR).
- No direct database access in unit tests (use model methods or ORM).

---

## 9. Migration Strategy

### 9.1 properties/views/unit_views.py Refactoring

1. **Analyze the file** to identify standalone helper functions that can be extracted (e.g., Leegality webhook handler, unit image/document logic).
2. **Create `properties/views/unit_helpers.py`** and move the identified helper functions.
3. **Update imports** in `properties/views/unit_views.py` to import from `unit_helpers`.
4. **Verify line count** is below 300.
5. **Run tests** to verify no behavioral regressions.

**Candidate functions to extract** (based on PR-008 analysis):
- Leegality webhook handler
- Unit image/document upload logic
- Any other standalone utility functions that are not ViewSet methods

**Do NOT extract:**
- ViewSet classes
- Functions that require cross-app imports
- Functions that are tightly coupled to view state

### 9.2 properties/models/unit_models.py Refactoring

1. **Analyze the file** to identify mixins that can be extracted (e.g., `AddressMixin`, `AmenityMixin`, `ImageMixin`).
2. **Create `properties/models/unit_mixins.py`** and move the identified mixins.
3. **Update imports** in `properties/models/unit_models.py` to import from `unit_mixins`.
4. **Update model inheritance** to use the extracted mixins.
5. **Verify line count** is below 400.
6. **Run tests** to verify no behavioral regressions.

**Candidate mixins to extract** (based on PR-008 analysis):
- `AddressMixin`
- `AmenityMixin`
- `ImageMixin`

**Do NOT change:**
- Model inheritance hierarchy
- Model field definitions
- Model Meta classes (unless moving them with the mixin)

### 9.3 Circular Dependency Avoidance

- Extracted helpers and mixins must not introduce new cross-app imports.
- Verify `test_circular_deps.py` passes after all changes.

### 9.4 Data Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Business behavior change | Low | High | All existing tests must pass; verify API responses match |
| Import regression | Low | Medium | Architecture tests enforce import boundaries |
| Circular dependency introduced | Low | Medium | `test_circular_deps.py` must pass |
| File size not reduced | Low | Low | Verify line counts in CI |

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
   git revert <PR-008D-merge-commit-sha>
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
   1. Apply PR-008D to staging.
   2. Verify all architecture tests pass.
   3. Execute rollback steps 1-4 above.
   4. Verify all existing tests still pass.
   5. Verify `import-linter check` passes.
   6. Re-apply PR-008D after successful rollback test.

---

## 11. Expected Git Diff

### 11.1 Summary

| Metric | Value |
|--------|-------|
| Files changed | 4 (2 new, 2 modified, 0 deleted) |
| Files added | 2 |
| Files modified | 2 |
| Files deleted | 0 |
| Lines added | ~150 |
| Lines removed | ~150 |
| Net change | ~0 lines (pure extraction) |

### 11.2 Files Added (~150 lines)

| File | Approx Lines | Description |
|------|---------------|-------------|
| `properties/views/unit_helpers.py` | ~80 | Extracted helper functions from `unit_views.py` |
| `properties/models/unit_mixins.py` | ~70 | Extracted mixins from `unit_models.py` |

### 11.3 Files Modified (~150 lines)

| File | Approx Lines Changed | Description |
|------|----------------------|-------------|
| `properties/views/unit_views.py` | +10, -80 | Remove extracted helpers; add imports from `unit_helpers` |
| `properties/models/unit_models.py` | +10, -70 | Remove extracted mixins; add imports from `unit_mixins`; update inheritance |

### 11.4 Diff Constraints

- No file in the diff may exceed 400 lines total after modification.
- No database migrations.
- No model field changes.
- No serializer changes.
- No API endpoint changes.
- No business logic changes.

---

## 12. Definition of Done

PR-008D is **Done** when ALL of the following are true.

### Code
- [ ] `properties/views/unit_views.py` is under 300 lines.
- [ ] `properties/models/unit_models.py` is under 400 lines.
- [ ] `properties/views/unit_helpers.py` contains extracted helper functions.
- [ ] `properties/models/unit_mixins.py` contains extracted mixins.
- [ ] Extracted modules contain no new cross-app imports.
- [ ] Original functionality is preserved.

### Tests
- [ ] All existing tests pass (no regressions).
- [ ] `pytest tests/architecture/ -v` passes with 0 failures.
- [ ] `import-linter check` passes with 0 violations.
- [ ] No test patch targets broken.

### CI
- [ ] `ruff check .` passes (0 errors).
- [ ] `ruff format --check .` passes.
- [ ] `mypy .` passes (0 errors).
- [ ] `import-linter check` passes (0 violations).
- [ ] `pytest tests/ -v` passes.
- [ ] `pytest tests/architecture/ -v` passes.
- [ ] `python manage.py check` passes.

### Architecture
- [ ] No view file exceeds 300 lines.
- [ ] No model file exceeds 400 lines.
- [ ] No circular dependencies introduced.
- [ ] `import-linter.ini` matches ADR-006 v1.1 matrix.
- [ ] Extracted modules contain no cross-app imports.

### Documentation
- [ ] CHANGELOG.md updated.
- [ ] PR description includes summary of files refactored.

### Deployment
- [ ] PR approved by Platform Team Lead and Staff Engineer.
- [ ] Merged to `phase-0-foundation` branch.
- [ ] Deployed to staging.
- [ ] Staging validation passed (24 hours).
- [ ] No production incidents during staging validation.

---

## 13. Developer Checklist

### Pre-Implementation
- [ ] Verify PR-008C is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes (baseline).
- [ ] Verify `import-linter check` passes (baseline).
- [ ] Run `pytest tests/ -v` and verify all pass (baseline).
- [ ] Read `ENGINEERING_STANDARDS.md` sections: View Rules, Model Rules, Import Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Refactoring Rules.
- [ ] Confirm `properties/views/unit_views.py` is over 300 lines.
- [ ] Confirm `properties/models/unit_models.py` is over 400 lines.
- [ ] Identify candidate helper functions and mixins for extraction.

### Implementation
- [ ] Create `properties/views/unit_helpers.py` and extract standalone helper functions.
- [ ] Update `properties/views/unit_views.py` to import from `unit_helpers`.
- [ ] Verify `properties/views/unit_views.py` is under 300 lines.
- [ ] Create `properties/models/unit_mixins.py` and extract mixins.
- [ ] Update `properties/models/unit_models.py` to import from `unit_mixins`.
- [ ] Update model inheritance to use extracted mixins.
- [ ] Verify `properties/models/unit_models.py` is under 400 lines.
- [ ] Verify no new cross-app imports in extracted modules.

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
- [ ] Verify `properties/views/unit_views.py` line count < 300.
- [ ] Verify `properties/models/unit_models.py` line count < 400.
- [ ] Verify extracted modules contain no cross-app imports.
- [ ] Verify no circular dependencies introduced.
- [ ] Verify model inheritance hierarchy is unchanged.

### Rollback
- [ ] Document rollback plan in PR description.
- [ ] Test rollback on staging: apply PR-008D, verify architecture tests pass, execute rollback, verify all tests still pass.

### PR
- [ ] Commit message follows conventional commits format.
- [ ] Branch name follows `<type>/<ticket-id>-<description>` format.
- [ ] PR description includes: summary, motivation, changes, testing, rollback plan.
- [ ] PR size is within limits (~0 net lines, 4 files).
- [ ] PR is linked to Phase 0 Architecture Cleanup task.

---

## 14. Reviewer Checklist

Use this checklist when reviewing PR-008D.

### Architecture
- [ ] `properties/views/unit_views.py` is under 300 lines.
- [ ] `properties/models/unit_models.py` is under 400 lines.
- [ ] Extracted helpers and mixins are in the same app (`properties/`).
- [ ] Extracted modules contain no cross-app imports.
- [ ] No circular dependencies introduced.
- [ ] Model inheritance hierarchy is unchanged.
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
- [ ] Extracted functions and mixins retain original interfaces.

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
- [ ] PR description includes summary of files refactored.

---

## 15. AI Checklist

Use this checklist when generating PR-008D with AI assistance.

### Pre-Generation
- [ ] Read `ENGINEERING_STANDARDS.md` sections: View Rules, Model Rules, Import Rules.
- [ ] Read `AI_ENGINEERING_PLAYBOOK.md` sections: Refactoring Rules.
- [ ] Verify PR-008C is merged to `phase-0-foundation` branch.
- [ ] Verify `pytest tests/architecture/ -v` passes on baseline.
- [ ] Verify `import-linter check` passes on baseline.
- [ ] Confirm `properties/views/unit_views.py` is over 300 lines.
- [ ] Confirm `properties/models/unit_models.py` is over 400 lines.
- [ ] Identify candidate helper functions and mixins for extraction.

### Code Generation
- [ ] Create `properties/views/unit_helpers.py` and extract standalone helper functions.
- [ ] Update `properties/views/unit_views.py` to import from `unit_helpers`.
- [ ] Verify `properties/views/unit_views.py` is under 300 lines.
- [ ] Create `properties/models/unit_mixins.py` and extract mixins.
- [ ] Update `properties/models/unit_models.py` to import from `unit_mixins`.
- [ ] Update model inheritance to use extracted mixins.
- [ ] Verify `properties/models/unit_models.py` is under 400 lines.
- [ ] **Do NOT** modify business logic in any view or model.
- [ ] **Do NOT** add database migrations.
- [ ] **Do NOT** change model fields or serializers.
- [ ] **Do NOT** change API endpoints or contracts.
- [ ] **Do NOT** introduce new features.
- [ ] **Do NOT** extract ViewSet classes — extract standalone functions only.
- [ ] **Do NOT** change model inheritance hierarchy.

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
- [ ] Verify `properties/views/unit_views.py` line count < 300.
- [ ] Verify `properties/models/unit_models.py` line count < 400.
- [ ] Verify extracted modules contain no cross-app imports.
- [ ] Verify no circular dependencies.

### Stop and Ask Conditions
AI must **stop and ask human** before proceeding if:
- [ ] Any required extraction would modify business logic.
- [ ] Any required extraction would need a database migration.
- [ ] `properties/views/unit_views.py` cannot be reduced below 300 lines without extracting ViewSet classes.
- [ ] `properties/models/unit_models.py` cannot be reduced below 400 lines without changing model inheritance.
- [ ] Any CI gate fails after 3 fix attempts.
- [ ] Existing tests fail and cannot be fixed without changing test expectations.

### Commit
- [ ] Commit message follows format: `refactor(architecture): split god views and god models in properties`.
- [ ] Commit body explains: helper functions extracted to `unit_helpers.py`, mixins extracted to `unit_mixins.py`, file sizes now within limits.
- [ ] Branch name: `refactor/phase-0-008d-split-god-views-models`.

---

## 16. Stop-and-Ask Conditions

STOP and ask the Principal Software Architect if:

1. Any required extraction would change business logic, model fields, serializers, or API contracts.
2. Any required extraction would need a database migration.
3. `properties/views/unit_views.py` cannot be reduced below 300 lines without extracting ViewSet classes or business logic.
4. `properties/models/unit_models.py` cannot be reduced below 400 lines without changing model inheritance hierarchy.
5. Any existing test fails and cannot be fixed without changing test expectations.
6. Any CI gate fails after 3 fix attempts.

---

## Appendix A: Architecture Decision References

| Decision | Reference |
|----------|-----------|
| No view file exceeds 300 lines | ADR-006 v1.1 §5.3 |
| No model file exceeds 400 lines | ADR-006 v1.1 §5.3 |
| `properties/` bounded context ownership | ADR-001 |
| Extracted modules must be in same app | ADR-006 v1.1 §5.3 |
| Architecture tests enforce all rules | ADR-006 v1.1 §5.2 |

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
| 1.0 | 2026-07-20 | Principal Software Architect | Initial PR-008D specification for Architecture Cleanup Phase 1 |

**Next Review:** After PR-008D merge
**Approval Required:** Platform Team Lead, Staff Engineer

---

*End of PR-008D Implementation Specification*
