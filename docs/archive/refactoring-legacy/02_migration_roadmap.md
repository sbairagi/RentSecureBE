# RentSecure Backend — Implementation Migration Roadmap

**Document:** Implementation Migration Roadmap
**Version:** 1.0.0
**Date:** 2026-07-15
**Owner:** Principal Software Architect
**Status:** Ratified
**Scope:** Complete migration from current state to target architecture
**Constraint:** This document is the master migration plan. Every PR, every branch, and every deployment must follow this roadmap. No deviation is permitted without a formal ADR and Principal Architect approval.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Assessment](#2-current-state-assessment)
3. [Migration Principles](#3-migration-principles)
4. [Migration Phases](#4-migration-phases)
5. [Pull Request Strategy](#5-pull-request-strategy)
6. [Git Workflow](#6-git-workflow)
7. [Risk Register](#7-risk-register)
8. [Dependency Order](#8-dependency-order)
9. [Testing Strategy During Migration](#9-testing-strategy-during-migration)
10. [CI Requirements](#10-ci-requirements)
11. [Code Review Checklist](#11-code-review-checklist)
12. [Definition of Done](#12-definition-of-done)
13. [Final Migration Checklist](#13-final-migration-checklist)
14. [Estimated Timeline](#14-estimated-timeline)
15. [AI Agent Workflow](#15-ai-agent-workflow)
16. [Long-Term Maintenance Strategy](#16-long-term-maintenance-strategy)

---

## 1. Executive Summary

### 1.1 Overall Migration Philosophy

The RentSecure backend migration follows a **"strangler fig" pattern**: the existing monolith is gradually wrapped, extracted, and reorganized into bounded contexts without ever stopping production traffic. No Big Bang migration. No rewrite. No downtime.

Every phase is a deployable, testable, independently verifiable increment. The system is always in a working state. If any phase introduces a regression, it is reverted before the next phase begins.

### 1.2 Goals

| Goal | Success Criteria |
|------|-----------------|
| Zero downtime | No production outage during any phase |
| Zero breaking API changes | All existing API contracts preserved |
| Incremental refactoring | Each phase is a small, reviewable PR |
| Every phase deployable | Application passes all tests and health checks at the end of each phase |
| Architecture compliance | Final state matches `01_target_architecture.md` |
| Test coverage | Business logic coverage ≥ 90% at migration end |
| Developer velocity | No phase blocks feature development for more than 1 sprint |

### 1.3 Constraints

| Constraint | Rationale |
|------------|-----------|
| Zero downtime | Production serves paying customers |
| Zero breaking API changes | Mobile apps and frontends depend on stable APIs |
| No source code in roadmap | This document is planning only; implementation lives in PRs |
| Incremental PRs | Large PRs are impossible to review safely |
| Every phase must be testable | No phase may leave the system in an untestable state |
| Every phase must pass CI | No exception for "we'll fix it in the next phase" |
| Backward compatibility mandatory | Compatibility wrappers required for all moved code |
| No premature optimization | Extract only when scale justifies it |

### 1.4 Success Criteria

The migration is complete when:

1. All bounded contexts match the target architecture structure.
2. All duplicate services are consolidated.
3. `smartbot` and `ai_assistant` are merged into `assistant`.
4. All business logic is in services, not views or signals.
5. All cross-context communication uses public interfaces.
6. No circular imports exist.
7. No private modules are imported across bounded contexts.
8. Architecture tests pass in CI.
9. Test coverage on business logic ≥ 90%.
10. `rentsecure_be/` is empty or deleted.
11. All 130+ architecture rules are enforced by CI.
12. Documentation is updated to reflect the new structure.

---

## 2. Current State Assessment

### 2.1 Pre-Migration Audit Checklist

Before writing a single line of migration code, the following audit must be completed and documented.

#### 2.1.1 Application Inventory

- [ ] List all Django apps with `apps.py` configurations.
- [ ] List all `models.py` files and their model counts.
- [ ] List all `views.py` files and their view counts.
- [ ] List all `serializers.py` files and their serializer counts.
- [ ] List all `services/` directories and their service files.
- [ ] List all `utils.py` and `utils/` directories.
- [ ] List all `signals.py` files and their signal handlers.
- [ ] List all `tasks.py` and management commands.
- [ ] List all `tests/` directories and their test counts.
- [ ] List all `migrations/` directories and their migration counts.

**Current state (as of 2026-07-15):**

| App | Models | Views | Services | Tests | Notes |
|-----|--------|-------|----------|-------|-------|
| `core` | 1 file | 1 file | 1 dir | 1 dir | Has `utils/` |
| `properties` | 1 dir | 1 dir | 1 dir | 1 dir | Has `repositories/`, `utils/`, `signals/`, `views/` |
| `finance` | 1 file | 1 file | — | 1 dir | Has `templates/` |
| `documents` | 1 file | 1 file | — | 1 dir | Has `templates/`, `utils/` |
| `notification` | 1 file | 1 file | 1 dir | 1 dir | Has `services/`, `management/` |
| `smartbot` | 1 file | 1 file | 1 dir | 1 dir | Has `cron/`, `actions.py` |
| `ai_assistant` | 1 file | 1 file | 1 dir | 1 dir | Has `services/` |
| `rentsecure_be` | — | — | 1 dir | 1 dir | Legacy app with scattered services |
| `referral_and_earn` | 1 file | — | — | — | Has `signals/` |
| `shared` | — | — | — | — | Has `utils/`, `exceptions.py`, etc. |
| `dashboard` | — | 1 file | — | — | Separate views app |

#### 2.1.2 Dependency Audit

- [ ] Run `grep -r "from <app>"` across all apps to find cross-imports.
- [ ] Document all imports from `rentsecure_be`.
- [ ] Document all imports from `smartbot`.
- [ ] Document all imports from `ai_assistant`.
- [ ] Document all imports from `shared`.
- [ ] Identify circular imports.
- [ ] Identify private module imports across boundaries.

**Known cross-imports to verify:**
- `properties` → `notification` (notification orchestration)
- `properties` → `finance` (rent records)
- `finance` → `documents` (PDF generation)
- `smartbot` → `ai_assistant` (AI services)
- Various apps → `rentsecure_be` (legacy services)

#### 2.1.3 Duplicate Service Audit

- [ ] Identify all duplicate service implementations.
- [ ] Document behavioral differences between duplicates.
- [ ] Identify the canonical implementation for each duplicate.
- [ ] Document all call sites for each duplicate.

**Known duplicates:**
- `leegality_service.py`: `rentsecure_be/services/` and `smartbot/services/`
- `i18n_service.py`: `rentsecure_be/services/` and `ai_assistant/services/`
- PDF generation: `documents/utils.py`, `properties/utils/utils.py`, `finance/views.py`
- WhatsApp: `notification/utils.py`, `notification/services/whatsapp_service.py`

#### 2.1.4 Signal Audit

- [ ] List all signal handlers across all apps.
- [ ] Identify handlers that contain business logic.
- [ ] Identify handlers that call external APIs.
- [ ] Identify handlers that modify unrelated models.
- [ ] Document which handlers are compliant and which violate architecture rules.

**Known signal files:**
- `core/signals.py`
- `referral_and_earn/signals.py`
- `properties/signals/` (directory)

#### 2.1.5 View Audit

- [ ] List all views across all apps.
- [ ] Identify views that contain business logic.
- [ ] Identify views that query ORM directly.
- [ ] Identify views that call external APIs.
- [ ] Document which views are thin and which violate architecture rules.

**Known views files:**
- `ai_assistant/views.py`
- `core/views.py`
- `dashboard/views.py`
- `documents/views.py`
- `finance/views.py`
- `notification/views.py`
- `smartbot/views.py`

#### 2.1.6 Test Audit

- [ ] Count total test files.
- [ ] Count total test functions/methods.
- [ ] Measure current test coverage (if available).
- [ ] Identify untested modules.
- [ ] Identify flaky tests.
- [ ] Document test execution time.

**Current state:** 81 test files across 9 test directories.

#### 2.1.7 CI/CD Audit

- [ ] Document all existing GitHub Actions workflows.
- [ ] Document what each workflow checks.
- [ ] Identify gaps in CI coverage.
- [ ] Document current coverage thresholds.
- [ ] Document current linting tools.
- [ ] Document current type checking tools.

**Existing workflows:**
- `architecture.yml` — Architecture validation
- `architecture-guard.yml` — Architecture guard
- `lint.yml` — Linting
- `test.yml` — Unit/integration tests
- `mutation.yml` — Mutation testing
- `security.yml` — Security scanning
- `security-deep.yml` — Deep security scan
- `performance.yml` — Performance tests
- `contract-tests.yml` — Contract tests
- `ci-metrics.yml` — CI metrics
- `deploy.yml` — Deployment
- `rollback.yml` — Rollback procedures
- And more...

#### 2.1.8 Deployment Audit

- [ ] Document current deployment process.
- [ ] Document current environment variables.
- [ ] Document current database migration strategy.
- [ ] Document current rollback procedure.
- [ ] Document current monitoring setup.
- [ ] Document current alerting setup.

### 2.2 Current Architecture Weaknesses

| Weakness | Impact | Migration Phase |
|----------|--------|-----------------|
| `rentsecure_be/` is a catch-all app | High | Phase 2 |
| Duplicate `leegality_service.py` | High | Phase 6 |
| Duplicate `i18n_service.py` | Medium | Phase 2 |
| PDF generation scattered | Medium | Phase 6 |
| Business logic in signals | High | Phase 3 |
| Business logic in views | High | Phase 3 |
| `smartbot` + `ai_assistant` overlap | High | Phase 7 |
| No bounded context structure | High | Phase 3-9 |
| `shared` contains business logic | Medium | Phase 2 |
| No architecture tests | High | Phase 1 |
| No import-linter enforcement | High | Phase 1 |

---

## 3. Migration Principles

These principles govern every decision during the migration. They are non-negotiable.

### 3.1 Never Break APIs

Every public API endpoint must continue to work exactly as before. Request/response contracts, authentication methods, and error formats must not change. If an API must change, the old API is preserved with a deprecation header, and the new API is added alongside it.

**Enforcement:** Integration tests run against every PR. Any test failure blocks the PR.

### 3.2 Move Before Rewrite

Code is moved, not rewritten. When consolidating duplicate services, the canonical implementation is moved to the target location. A compatibility wrapper is left at the old location. Call sites are migrated gradually. Only after zero imports remain is the wrapper deleted.

**Enforcement:** Code review checklist requires evidence of move-before-rewrite for every refactoring PR.

### 3.3 One Responsibility Per PR

Each PR must have a single, clearly stated purpose. A PR that moves a service, restructures a folder, and fixes a bug is too large to review safely. If a change touches more than three bounded contexts or more than twenty files, it must be split into multiple PRs.

**Enforcement:** PR template requires a single-line purpose statement. Reviewers reject multi-purpose PRs.

### 3.4 Preserve Behavior

Refactoring must not change behavior. If a service method returned a dictionary before, it must return the same dictionary after. If a view returned a 400 error for invalid input, it must still return a 400 error. Behavioral changes are implemented in separate PRs after the refactoring is complete.

**Enforcement:** Regression tests run against every PR. Any behavioral change detected by tests must be explicitly justified.

### 3.5 Add Tests Before Refactoring

Before moving or restructuring any code, tests must be added (if missing) or updated (if outdated) to cover the existing behavior. Refactoring without tests is gambling.

**Enforcement:** PR cannot be merged without tests that cover the refactored code.

### 3.6 Remove Duplicates Only After Replacement

Duplicate services must not be deleted until the canonical implementation is fully in place and all call sites have been migrated. The compatibility wrapper is removed only after `grep` confirms zero remaining imports.

**Enforcement:** Architecture tests verify that only one implementation exists for each capability.

### 3.7 Backward Compatibility First

Every migration must preserve backward compatibility for existing callers. Compatibility wrappers are not optional—they are mandatory. Old import paths must continue to work until all call sites are migrated.

**Enforcement:** Import-linter and custom tests verify that old import paths still work during migration.

### 3.8 Every Phase Must Be Deployable

At the end of every phase, the application must:
- Start without errors.
- Pass all tests.
- Pass all CI checks.
- Be deployable to production.

**Enforcement:** Deployment to staging is required at the end of each phase.

### 3.9 Document as You Go

Every architectural decision made during migration must be recorded in an ADR. Every significant refactoring must be documented in the migration plan. Documentation is not a post-migration task—it is part of the migration.

**Enforcement:** PR template requires an ADR reference for any architectural change.

### 3.10 Communicate Early and Often

Migration progress is communicated to the entire team weekly. Blockers are escalated immediately. No phase may proceed without team awareness.

**Enforcement:** Weekly sync meeting mandatory. Migration status updated in shared doc.

---

## 4. Migration Phases

### Phase 0: Repository Audit and Baseline

**Purpose:** Establish a complete understanding of the current codebase before any changes are made. Create a baseline that can be used to measure progress and detect regressions.

**Duration:** 1 week

**Files Affected:** None (read-only audit)

**Activities:**
1. Complete the Current State Assessment checklist (Section 2).
2. Run full test suite and record current coverage.
3. Run architecture audit and document violations.
4. Run dependency graph analysis.
5. Document all duplicate services with call sites.
6. Document all cross-context imports.
7. Document all signals with business logic.
8. Document all views with business logic.
9. Create baseline metrics: test count, coverage %, query performance, API latency.
10. Create `02_migration_baseline.md` with all findings.

**Deliverables:**
- `02_migration_baseline.md` — Complete current state documentation.
- Baseline test coverage report.
- Baseline architecture violation report.
- Baseline performance metrics.

**Validation:**
- All audit checklists completed.
- Baseline document reviewed and approved by Principal Architect.

**Exit Criteria:**
- Baseline document is complete and approved.
- No code has been modified.
- Team has reviewed and understands the baseline.

**Rollback Strategy:** N/A (no code changes)

---

### Phase 1: Architecture Enforcement Foundation

**Purpose:** Establish the tools and CI gates that will enforce the target architecture throughout the migration. No refactoring yet—only infrastructure.

**Duration:** 1-2 weeks

**Files Affected:**
- `.github/workflows/architecture.yml` (update)
- `.github/workflows/architecture-guard.yml` (update)
- `import-linter.ini` (create/update)
- `pyproject.toml` (add tools)
- `conftest.py` (add architecture fixtures)
- `tests/architecture/` (create)

**Activities:**
1. Configure `import-linter` with layers and contract rules matching target architecture.
2. Create architecture test suite:
   - `test_no_private_imports_across_contexts.py`
   - `test_no_circular_dependencies.py`
   - `test_views_do_not_contain_business_logic.py`
   - `test_no_orm_in_views.py`
   - `test_signals_do_not_contain_business_logic.py`
   - `test_shared_has_no_business_logic.py`
3. Add pre-commit hooks for architecture rules.
4. Update CI workflows to run architecture tests on every PR.
5. Add coverage reporting to CI.
6. Add mutation testing to CI.
7. Document architecture test patterns for future phases.

**Deliverables:**
- `import-linter.ini` with all layers and contracts.
- Architecture test suite in `tests/architecture/`.
- Updated CI workflows.
- Pre-commit configuration.
- Architecture enforcement documentation.

**Validation:**
- Architecture tests pass on current codebase (may have violations documented).
- CI fails on architecture violations.
- Team trained on architecture tests.

**Exit Criteria:**
- All architecture tools are configured.
- CI runs architecture tests on every PR.
- Baseline architecture violations are documented but do not block CI yet (transition period).
- Team understands how to run architecture tests locally.

**Rollback Strategy:**
- Revert CI workflow changes if they block legitimate work.
- Keep architecture tests running but non-blocking during transition.

---

### Phase 2: Shared Package Restructure

**Purpose:** Reorganize `shared/` into the target structure defined in `01_target_architecture.md`. Move any business logic currently in `shared/` to the appropriate bounded context. Establish `shared/` as a true leaf module.

**Duration:** 1 week

**Files Affected:**
- `shared/exceptions.py` → `shared/exceptions/` (split into multiple files)
- `shared/utils.py` → `shared/utils/` (split by category)
- `shared/` (add missing folders: `types/`, `enums/`, `protocols/`, `validators/`, `constants/`, `dto/`, `interfaces/`)

**Activities:**
1. Audit `shared/` for business logic. Move any business logic to appropriate bounded context.
2. Create new folder structure:
   - `shared/exceptions/` with separate files per exception type.
   - `shared/types/` for type aliases.
   - `shared/enums/` for shared enumerations.
   - `shared/protocols/` for abstract interfaces.
   - `shared/validators/` for reusable validators.
   - `shared/constants/` for shared constants.
   - `shared/dto/` for data transfer objects.
3. Update all imports across the codebase.
4. Leave compatibility wrappers at old import paths during migration.
5. Remove wrappers only after zero imports remain.

**Deliverables:**
- Restructured `shared/` directory matching target architecture.
- Compatibility wrappers for old import paths.
- Updated imports in all consuming apps.
- Tests for new `shared/` structure.

**Validation:**
- All tests pass.
- No import errors.
- `shared/` contains no business logic (verified by architecture tests).
- All imports use new paths (old wrappers have zero imports).

**Exit Criteria:**
- `shared/` matches target structure.
- No business logic in `shared/`.
- All imports updated to new paths.
- Compatibility wrappers removed.
- CI passes all checks.

**Rollback Strategy:**
- Revert compatibility wrappers if import errors occur.
- Keep old structure alongside new during transition.

---

### Phase 3: Accounts Bounded Context Creation

**Purpose:** Create the `accounts/` bounded context from existing owner/tenant profile code scattered in `core/`, `properties/`, and `rentsecure_be/`.

**Duration:** 2 weeks

**Files Affected:**
- New: `accounts/` (entire app)
- `core/` (remove owner/tenant profile code)
- `properties/` (remove tenant onboarding/offboarding)
- `rentsecure_be/` (remove account-related services)

**Activities:**
1. Create `accounts/` app with target folder structure.
2. Move `OwnerProfile`, `TenantProfile` models from `core/` or `properties/` to `accounts/`.
3. Move owner/tenant services to `accounts/services/`.
4. Move owner/tenant serializers to `accounts/serializers/`.
5. Move owner/tenant views to `accounts/api/v1/`.
6. Move billing/payment method code to `accounts/`.
7. Create compatibility wrappers at old import paths.
8. Update imports in dependent apps.
9. Add `accounts` to `INSTALLED_APPS`.
10. Create and run migrations.

**Deliverables:**
- `accounts/` app with complete target structure.
- Compatibility wrappers at old locations.
- Updated imports in all consuming apps.
- Database migrations.
- Tests for `accounts/`.

**Validation:**
- All tests pass.
- No import errors.
- Owner/tenant APIs work identically to before.
- Database migrations apply cleanly.
- CI passes all checks.

**Exit Criteria:**
- `accounts/` is fully functional.
- All owner/tenant code lives in `accounts/`.
- Old import paths have zero imports.
- Compatibility wrappers removed.
- CI passes all checks.

**Rollback Strategy:**
- Revert compatibility wrappers if imports break.
- Keep old models in place until all migrations are verified.

---

### Phase 4: Properties Bounded Context Restructure

**Purpose:** Restructure `properties/` into the target bounded context structure with proper internal folders (`api/`, `services/`, `repositories/`, `selectors/`, `validators/`, `serializers/`, `permissions/`, `signals/`, `exceptions/`, `constants/`, `interfaces/`, `dto/`).

**Duration:** 2 weeks

**Files Affected:**
- `properties/` (restructure all internal folders)
- `properties/models/` (split `models.py` into per-entity files)
- `properties/views/` (move to `properties/api/v1/`)
- `properties/serializers/` (already exists, verify structure)
- `properties/signals/` (already exists, fix violations)
- `properties/utils/` (move non-business utilities to `shared/`)

**Activities:**
1. Split `properties/models.py` into per-entity files in `properties/models/`.
2. Move `properties/views/` to `properties/api/v1/`.
3. Ensure all services are in `properties/services/`.
4. Create `properties/repositories/` and move query logic from services.
5. Create `properties/selectors/` for read-optimized queries.
6. Create `properties/validators/` for input validation.
7. Create `properties/permissions/` for DRF permissions.
8. Create `properties/exceptions/` for domain exceptions.
9. Create `properties/constants/` for status enums and constants.
10. Create `properties/interfaces/` for protocols.
11. Create `properties/dto/` for request/response DTOs.
12. Fix all signal handlers that contain business logic (move to services).
13. Move pure utilities to `shared/utils/`.
14. Update all imports.
15. Add compatibility wrappers during migration.

**Deliverables:**
- Fully restructured `properties/` app.
- Compatibility wrappers at old paths.
- Updated imports in all consuming apps.
- Tests for restructured code.
- Signal handler fixes.

**Validation:**
- All tests pass.
- No import errors.
- Property APIs work identically.
- Signals are thin (verified by architecture tests).
- CI passes all checks.

**Exit Criteria:**
- `properties/` matches target structure.
- All internal folders exist and are used correctly.
- Signals contain no business logic.
- Old paths have zero imports.
- Compatibility wrappers removed.
- CI passes all checks.

**Rollback Strategy:**
- Revert compatibility wrappers if imports break.
- Keep old folder structure alongside new during transition.

---

### Phase 5: Finance Bounded Context Restructure

**Purpose:** Restructure `finance/` into the target bounded context structure. Consolidate PDF generation from `finance/` into `documents/`.

**Duration:** 1.5 weeks

**Files Affected:**
- `finance/` (restructure internal folders)
- `documents/` (add PDF generation services)
- `properties/` (update PDF generation imports)

**Activities:**
1. Restructure `finance/` internal folders to match target.
2. Split `finance/models.py` into per-entity files.
3. Move `finance/views.py` to `finance/api/v1/`.
4. Create `finance/repositories/`, `finance/selectors/`, `finance/validators/`, etc.
5. Move PDF generation code from `finance/views.py` to `documents/services/pdf_generator.py`.
6. Create `documents/services/invoice_service.py` and `documents/services/receipt_service.py`.
7. Update finance services to use `documents` public interface for PDF generation.
8. Add compatibility wrappers for old PDF generation paths.
9. Update imports in consuming apps.

**Deliverables:**
- Restructured `finance/` app.
- New PDF generation services in `documents/`.
- Compatibility wrappers for old PDF paths.
- Updated imports.
- Tests for restructured code.

**Validation:**
- All tests pass.
- No import errors.
- Finance APIs work identically.
- PDF generation produces identical output.
- CI passes all checks.

**Exit Criteria:**
- `finance/` matches target structure.
- PDF generation centralized in `documents/`.
- Old PDF paths have zero imports.
- Compatibility wrappers removed.
- CI passes all checks.

**Rollback Strategy:**
- Keep old PDF generation code alongside new during transition.
- Revert compatibility wrappers if issues arise.

---

### Phase 6: Documents and Integration Consolidation

**Purpose:** Consolidate document generation, e-signature, and external integration adapters into their target locations. This phase includes the high-priority duplicate service consolidation from ADR-003.

**Duration:** 2 weeks

**Files Affected:**
- `documents/` (consolidate PDF generation, add Leegality)
- `rentsecure_be/services/leegality_service.py` (move to `documents/`)
- `smartbot/services/leegality_service.py` (move to `documents/`)
- `integrations/` (new app for adapters)
- `rentsecure_be/services/` (move payment services to `integrations/`)

**Activities:**
1. Create `integrations/` app with target folder structure.
2. Move `RazorpayAdapter` and `CashfreeAdapter` from `rentsecure_be/services/` to `integrations/adapters/payment/`.
3. Move `ManualPaymentAdapter` to `integrations/adapters/payment/`.
4. Move `LeegalityClient` from `smartbot/services/leegality_service.py` to `documents/services/leegality.py`.
5. Merge the two `leegality_service.py` duplicates into one canonical implementation.
6. Move PDF generation utilities to `documents/utils/pdf_generator.py`.
7. Create `documents/services/agreement_service.py`, `invoice_service.py`, `receipt_service.py`.
8. Create `integrations/adapters/notification/` for email, FCM, SMS, WhatsApp adapters.
9. Create `integrations/adapters/storage/` for S3 adapter.
10. Create `integrations/adapters/ai/` for OpenAI adapter.
11. Create `integrations/webhooks/` for webhook handlers.
12. Add compatibility wrappers at all old locations.
13. Update imports in all consuming apps.
14. Remove dead code from `rentsecure_be/services/`.

**Deliverables:**
- `integrations/` app with adapter implementations.
- Consolidated Leegality client in `documents/`.
- Consolidated PDF generation in `documents/`.
- Compatibility wrappers at old locations.
- Updated imports.
- Tests for new adapters and services.

**Validation:**
- All tests pass.
- No import errors.
- Leegality webhook works identically.
- PDF generation produces identical output.
- Payment adapters are functional (even if disabled).
- CI passes all checks.

**Exit Criteria:**
- `integrations/` app is complete.
- Leegality is consolidated in `documents/`.
- PDF generation is centralized in `documents/`.
- All adapter interfaces are defined in `shared/protocols/`.
- Old duplicate locations have zero imports.
- Compatibility wrappers removed.
- `rentsecure_be/services/` is empty or deleted.
- CI passes all checks.

**Rollback Strategy:**
- Keep duplicate implementations alongside wrappers during transition.
- Revert wrappers if behavioral differences are found.

---

### Phase 7: Notification Restructure

**Purpose:** Restructure `notification/` into the target bounded context with channel implementations separated from business orchestration. Fix signal violations and duplicate service issues.

**Duration:** 1.5 weeks

**Files Affected:**
- `notification/` (restructure internal folders)
- `properties/` (move notification orchestration to `properties/services/notification_service.py`)
- `notification/services/` (separate channels from orchestration)

**Activities:**
1. Restructure `notification/` internal folders to match target.
2. Create `notification/services/channels/` with separate adapter files:
   - `base.py` (base adapter)
   - `email.py`
   - `fcm.py`
   - `inapp.py`
   - `whatsapp.py`
   - `sms.py`
3. Move business notification orchestration from `notification/services/rent_notify_service.py` to `properties/services/notification_service.py`.
4. Move `extra_charge_reminders.py` and `late_fees_notify_service.py` to `properties/services/`.
5. Fix signal handlers in `properties/signals/` that call WhatsApp directly (replace with thin wrappers).
6. Create `notification/services/orchestrator.py` for channel selection and fallback logic.
7. Move `notification/utils.py` content to appropriate locations:
   - Template rendering → `notification/services/`
   - Pure utilities → `shared/utils/`
8. Add compatibility wrappers at old import paths.
9. Update imports in consuming apps.

**Deliverables:**
- Restructured `notification/` app with channel adapters.
- Notification orchestration moved to domain apps.
- Fixed signal handlers.
- Compatibility wrappers at old paths.
- Updated imports.
- Tests for restructured code.

**Validation:**
- All tests pass.
- No import errors.
- Notifications are delivered identically.
- Signals are thin (verified by architecture tests).
- CI passes all checks.

**Exit Criteria:**
- `notification/` matches target structure.
- Channel implementations are in `notification/services/channels/`.
- Business orchestration is in domain apps.
- Signals contain no business logic.
- Old paths have zero imports.
- Compatibility wrappers removed.
- CI passes all checks.

**Rollback Strategy:**
- Keep old notification services alongside wrappers during transition.
- Revert wrappers if notification delivery changes.

---

### Phase 8: Assistant Merge (smartbot + ai_assistant)

**Purpose:** Merge `smartbot/` and `ai_assistant/` into a single `assistant/` bounded context. Move non-AI services to their correct domain apps.

**Duration:** 2 weeks

**Files Affected:**
- `assistant/` (new app, created from `smartbot/` + `ai_assistant/`)
- `smartbot/` (emptied and deleted)
- `ai_assistant/` (emptied and deleted)
- `documents/` (receive Leegality, agreement, invoice services)
- `properties/` (receive archive, unit services)
- `rentsecure_be/` (receive any remaining services)

**Activities:**
1. Create `assistant/` app with target folder structure.
2. Move AI services from `smartbot/services/` to `assistant/services/`:
   - `chatbot_service.py`
   - `gpt_services.py`
   - `services.py` (action execution)
3. Move AI services from `ai_assistant/services/` to `assistant/services/`:
   - `finance_ai.py` → `assistant/services/finance_ai_service.py`
   - `archive_service.py` → `properties/services/archive_service.py` (non-AI)
   - `invoice_service.py` → `documents/services/invoice_service.py` (non-AI)
   - `unit_service.py` → `properties/services/unit_service.py` (non-AI)
4. Move `smartbot/models.py` to `assistant/models.py`.
5. Move `smartbot/views.py` to `assistant/api/v1/`.
6. Move `smartbot/actions.py` to `assistant/services/action_service.py`.
7. Move `smartbot/intents.py` to `assistant/services/intent_service.py`.
8. Move `ai_assistant/models.py` to `assistant/models.py` (merge with smartbot models).
9. Move `ai_assistant/views.py` to `assistant/api/v1/`.
10. Move `smartbot/tests/` and `ai_assistant/tests/` to `assistant/tests/`.
11. Delete non-AI services from `assistant/` after moving to correct domains.
12. Add compatibility wrappers at old import paths.
13. Update imports in all consuming apps.
14. Delete `smartbot/` and `ai_assistant/` after zero imports remain.

**Deliverables:**
- `assistant/` app with complete target structure.
- Non-AI services moved to correct domains.
- Compatibility wrappers at old paths.
- Updated imports.
- Tests for `assistant/`.

**Validation:**
- All tests pass.
- No import errors.
- AI features work identically.
- Chatbot API works identically.
- CI passes all checks.

**Exit Criteria:**
- `assistant/` app is complete.
- `smartbot/` and `ai_assistant/` are deleted.
- All AI services live in `assistant/`.
- All non-AI services live in correct domains.
- Old paths have zero imports.
- Compatibility wrappers removed.
- CI passes all checks.

**Rollback Strategy:**
- Keep `smartbot/` and `ai_assistant/` alongside wrappers during transition.
- Revert wrappers if AI behavior changes.

---

### Phase 9: Cross-Cutting Concerns and Cleanup

**Purpose:** Complete the migration of remaining cross-cutting concerns: create `analytics/` bounded context, extract `dashboard/` views, clean up `rentsecure_be/`, and finalize all compatibility wrappers.

**Duration:** 2 weeks

**Files Affected:**
- `analytics/` (new app)
- `dashboard/` (move to `analytics/` or appropriate context)
- `rentsecure_be/` (delete or repurpose)
- All apps (remove compatibility wrappers)

**Activities:**
1. Create `analytics/` app with target structure.
2. Move analytics code from `properties/services/summary_service.py` to `analytics/services/`.
3. Move dashboard views from `dashboard/views.py` to `analytics/api/v1/`.
4. Move owner reporting from `core/services/owner_reporting_service.py` to `analytics/services/`.
5. Move `properties/services/unit_service.py` analytics methods to `analytics/`.
6. Create `analytics/services/dashboard_service.py`, `report_service.py`, `metric_service.py`.
7. Create `analytics/selectors/` for optimized analytics queries.
8. Move any remaining code from `rentsecure_be/` to appropriate contexts.
9. Delete `rentsecure_be/` after zero imports remain.
10. Remove all compatibility wrappers (verify zero imports with `grep`).
11. Run dead code cleanup (remove unused imports, unused variables, commented-out code).
12. Update all documentation.

**Deliverables:**
- `analytics/` app with complete target structure.
- `dashboard/` views integrated into `analytics/`.
- `rentsecure_be/` deleted or empty.
- All compatibility wrappers removed.
- Dead code cleaned up.
- Updated documentation.

**Validation:**
- All tests pass.
- No import errors.
- Dashboard and analytics work identically.
- No dead code (verified by linter).
- CI passes all checks.

**Exit Criteria:**
- `analytics/` app is complete.
- `dashboard/` is integrated or deleted.
- `rentsecure_be/` is deleted.
- No compatibility wrappers remain.
- No dead code remains.
- CI passes all checks.

**Rollback Strategy:**
- Keep `rentsecure_be/` in version control after deletion (git can restore).
- Re-delete if issues arise after wrapper removal.

---

### Phase 10: Performance Optimization

**Purpose:** Optimize database queries, add indexes, implement caching, and ensure the application meets performance targets at scale.

**Duration:** 1.5 weeks

**Files Affected:**
- All apps with database queries (primarily `properties/`, `finance/`, `analytics/`)
- `shared/` (add caching utilities)

**Activities:**
1. Profile all API endpoints for N+1 queries.
2. Add `select_related` and `prefetch_related` where missing.
3. Add database indexes for common filter fields.
4. Implement view-level caching for expensive analytics endpoints.
5. Implement data caching for frequently accessed reference data.
6. Add query count assertions to integration tests.
7. Optimize slow queries identified by profiling.
8. Add pagination to all list endpoints.
9. Implement cursor-based pagination for large datasets.
10. Add streaming responses for large file downloads.

**Deliverables:**
- Optimized querysets across all apps.
- Database indexes added.
- Caching layer implemented.
- Performance tests added.
- Query count assertions in integration tests.

**Validation:**
- All tests pass.
- No N+1 queries (verified by `assertNumQueries`).
- API latency meets targets (p95 < 500ms).
- CI performance tests pass.

**Exit Criteria:**
- No N+1 queries in any endpoint.
- All list endpoints are paginated.
- Caching is implemented for expensive operations.
- Performance tests pass.
- CI passes all checks.

**Rollback Strategy:**
- Revert caching changes if cache invalidation issues arise.
- Revert index changes if migration performance degrades.

---

### Phase 11: Security Hardening

**Purpose:** Implement all security measures defined in the target architecture: input validation, secrets management, rate limiting, OWASP mitigations, and security testing.

**Duration:** 1 week

**Files Affected:**
- All apps (security hardening)
- `config/` (security settings)
- `shared/validators/` (add missing validators)

**Activities:**
1. Audit all inputs for validation coverage.
2. Add missing validators (GSTIN, UPI ID, Indian phone, pincode).
3. Implement rate limiting on all endpoints.
4. Verify JWT implementation (short-lived access tokens, refresh token rotation).
5. Implement file upload validation (magic bytes, size limits).
6. Add webhook signature verification for all incoming webhooks.
7. Implement secrets management (no hardcoded secrets).
8. Add security headers (CSP, HSTS, X-Frame-Options).
9. Add PII redaction in logs.
10. Run security scans (Semgrep, Bandit) and fix findings.
11. Add security tests to CI.

**Deliverables:**
- Input validation coverage 100%.
- Rate limiting on all endpoints.
- Webhook signature verification.
- Secrets management implemented.
- Security tests in CI.
- Security scan reports clean.

**Validation:**
- All tests pass.
- Security scans pass.
- No hardcoded secrets.
- No PII in logs.
- CI security checks pass.

**Exit Criteria:**
- All security measures implemented.
- Security tests pass in CI.
- No security scan findings.
- CI passes all checks.

**Rollback Strategy:**
- Revert rate limiting if it blocks legitimate traffic.
- Revert security headers if they break frontend functionality.

---

### Phase 12: Production Readiness

**Purpose:** Prepare the application for production deployment with monitoring, alerting, disaster recovery, and operational runbooks.

**Duration:** 1 week

**Files Affected:**
- `config/` (production settings)
- `scripts/` (operational scripts)
- Documentation (runbooks, monitoring docs)

**Activities:**
1. Finalize production settings (debug=False, secure cookies, etc.).
2. Configure structured logging (JSON format, correlation IDs).
3. Set up monitoring dashboards (error rate, latency, database connections).
4. Configure alerts (error rate threshold, latency threshold, queue depth).
5. Create runbooks for common operational tasks.
6. Document disaster recovery procedure.
7. Document rollback procedure.
8. Load test the application at expected peak load.
9. Verify database backup and restore procedure.
10. Verify health check endpoints.
11. Final architecture review against target architecture.
12. Final security review.

**Deliverables:**
- Production-ready configuration.
- Monitoring and alerting setup.
- Operational runbooks.
- Disaster recovery documentation.
- Load test report.
- Final architecture compliance report.

**Validation:**
- All tests pass.
- Load test passes at expected peak load.
- Health checks pass.
- Monitoring dashboards display correct data.
- Alerts trigger correctly.
- CI passes all checks.

**Exit Criteria:**
- Application is production-ready.
- All monitoring and alerting is configured.
- Runbooks are documented.
- Load test passes.
- Final architecture review passes.
- CI passes all checks.

**Rollback Strategy:**
- Maintain previous production deployment as rollback target.
- Database backups taken before final deployment.

---

## 5. Pull Request Strategy

### 5.1 PR Size

| Type | Max Files Changed | Max Lines Changed | Description |
|------|-------------------|-------------------|-------------|
| Small | 5 | 200 | Single service move, single wrapper creation, single test addition |
| Medium | 15 | 500 | App restructure phase, bounded context creation |
| Large | 30 | 1000 | Only for Phase 0-1 setup, never for refactoring |

**Rule:** Any PR larger than "medium" must be split. If a change cannot be split, it requires Principal Architect approval.

### 5.2 Branch Naming

```
migration/phase-<N>-<brief-description>

Examples:
migration/phase-1-architecture-enforcement
migration/phase-2-shared-restructure
migration/phase-3-accounts-context
migration/phase-4-properties-restructure
migration/phase-6-documents-consolidation
migration/phase-8-assistant-merge
```

**Rules:**
- Branch name must start with `migration/phase-<N>-`.
- Description must be lowercase, hyphen-separated, max 40 characters.
- No branch names without phase number.

### 5.3 Review Checklist

Every PR must complete this checklist before requesting review:

- [ ] **Single purpose:** PR does exactly one thing.
- [ ] **Tests added:** New code has tests; refactored code has regression tests.
- [ ] **Tests pass:** All tests pass locally and in CI.
- [ ] **Architecture tests pass:** No new architecture violations introduced.
- [ ] **No breaking changes:** Public APIs unchanged.
- [ ] **Compatibility wrappers:** Wrappers added for all moved/renamed code.
- [ ] **Documentation updated:** ADR created for architectural changes.
- [ ] **No dead code:** No unused imports, variables, or commented-out code.
- [ ] **Lint passes:** No lint errors.
- [ ] **Type checking passes:** No type errors.
- [ ] **No secrets:** No hardcoded credentials or keys.
- [ ] **Performance checked:** No N+1 queries introduced.
- [ ] **Security checked:** No new vulnerabilities introduced.
- [ ] **Rollback plan:** Documented if PR is high-risk.

### 5.4 Merge Rules

| Rule | Description |
|------|-------------|
| No self-merge | Author cannot merge own PR. |
| Minimum 1 approval | At least one reviewer must approve. |
| CI must pass | All checks must pass before merge. |
| No force push | Force push is forbidden on shared branches. |
| Squash and merge | PRs are squash-merged to keep history clean. |
| ADR required | Architectural changes require ADR reference in PR description. |

### 5.5 Commit Strategy

| Type | Convention | Example |
|------|-----------|---------|
| Feature | `feat: <description>` | `feat: add BuildingRepository to properties` |
| Fix | `fix: <description>` | `fix: handle null tenant in rent service` |
| Refactor | `refactor: <description>` | `refactor: move leegality_service to documents` |
| Test | `test: <description>` | `test: add regression test for payment flow` |
| Docs | `docs: <description>` | `docs: update migration plan for Phase 6` |
| Chore | `chore: <description>` | `chore: update dependencies` |

**Rules:**
- Commit messages must be imperative mood ("add", not "added" or "adds").
- Commit messages must be lowercase except for proper nouns.
- Commit messages must be under 72 characters.
- Each commit must be a single logical change.
- No "misc changes" or "WIP" commits in final PR.

### 5.6 Tagging

- Phase completion tags: `phase-<N>-complete` (e.g., `phase-3-complete`).
- Release tags: `v<major>.<minor>.<patch>` following SemVer.
- Migration tags are lightweight tags pointing to the merge commit.

---

## 6. Git Workflow

### 6.1 Branch Strategy

```
main (production)
  ├── migration/phase-0-baseline
  ├── migration/phase-1-architecture-enforcement
  ├── migration/phase-2-shared-restructure
  ├── migration/phase-3-accounts-context
  ├── ...
  └── migration/phase-12-production-readiness
```

**Rules:**
- `main` is the production branch. It is always deployable.
- Migration branches are created from `main` and merged back to `main`.
- No long-lived feature branches during migration.
- Each phase is a separate branch that is merged and deleted before the next phase begins.
- Hotfix branches are created from `main` and merged back to `main` and the current migration branch.

### 6.2 Commit Conventions

Follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:** `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`, `perf`, `style`.

**Scope:** The bounded context or module affected (e.g., `properties`, `notification`, `shared`).

**Examples:**
```
feat(properties): add BuildingRepository for query abstraction
fix(notification): handle null user in send_smart_alert
refactor(documents): move PDF generation to documents/utils
test(accounts): add regression test for owner creation
docs(migration): update Phase 4 exit criteria
```

### 6.3 Release Branches

- Release branches are created from `main` only for production releases.
- Naming: `release/v<major>.<minor>.<patch>`.
- Only hotfixes are merged to release branches.
- Release branches are deleted after release.

### 6.4 Hotfix Branches

- Hotfix branches are created from `main` for production issues.
- Naming: `hotfix/<issue-number>-<description>`.
- Hotfixes are merged to `main` and the current migration branch.
- Hotfixes are cherry-picked, not merged, to avoid bringing migration changes into production.

### 6.5 Versioning

- Follows [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.
- `MAJOR`: Breaking API changes (should not occur during migration).
- `MINOR`: New features, bounded context additions.
- `PATCH`: Bug fixes, refactorings.
- Migration phases do not bump version independently.
- Version is bumped only on production releases.

---

## 7. Risk Register

| # | Risk | Probability | Impact | Mitigation | Rollback |
|---|------|-------------|--------|------------|----------|
| 1 | Import errors during phase migration | High | High | Compatibility wrappers at all old paths. Run full test suite before merging. | Revert compatibility wrapper removal. Keep old code in place. |
| 2 | Behavioral regression in moved services | Medium | High | Add regression tests before moving. Test behavior before and after. | Revert to canonical implementation. Keep old code alongside new during transition. |
| 3 | Circular import introduced during restructure | Medium | High | Architecture tests block PRs with circular imports. Manual review of imports. | Revert import changes. Refactor to extract shared logic to `shared/`. |
| 4 | Database migration failure | Low | High | Test migrations on staging database. Use `RunPython` for data migrations. Keep old models until migration is verified. | Restore database backup. Revert migration. |
| 5 | Performance regression from query changes | Medium | Medium | Profile queries before and after. Add query count assertions. Load test after each phase. | Revert query changes. Restore previous query patterns. |
| 6 | CI pipeline breaks, blocking all development | Low | High | Run CI changes in separate PR. Keep CI non-blocking during transition. Have rollback plan for CI changes. | Revert CI workflow changes. Restore previous CI configuration. |
| 7 | Team resistance to migration pace | Medium | Medium | Weekly sync meetings. Clear phase goals. Celebrate phase completions. Adjust pace if needed. | Slow down migration pace. Increase communication frequency. |
| 8 | Duplicate service behavioral differences missed | Medium | High | Document behavioral differences before consolidation. Add tests for both implementations before merging. | Keep both implementations. Defer consolidation until differences are understood. |
| 9 | Dead code removal breaks hidden dependencies | Low | Medium | Use `grep` and IDE "find usages" before deletion. Run full test suite after deletion. | Restore deleted code from git history. |
| 10 | Compatibility wrappers never removed | Medium | Medium | Automated checks for zero imports before wrapper removal. Schedule wrapper cleanup as explicit phase task. | Keep wrappers if removal is too risky. Document why wrappers are permanent. |
| 11 | Phase takes longer than estimated | Medium | Low | Split phase into smaller PRs. Adjust timeline. Communicate delays to stakeholders. | Extend phase duration. Defer non-critical tasks to later phases. |
| 12 | Production deployment fails after phase | Low | High | Deploy to staging first. Run smoke tests. Have rollback procedure ready. | Rollback to previous production version. Fix issues in migration branch. |
| 13 | Secrets accidentally committed during migration | Low | High | Pre-commit hooks for secret scanning. Review diffs carefully. Rotate any exposed secrets immediately. | Rotate exposed secrets. Remove from git history with `git filter-branch`. |
| 14 | Test suite becomes flaky during migration | Medium | Medium | Fix flaky tests immediately. Isolate flaky tests. Do not merge PRs with flaky tests. | Revert changes that introduced flakiness. Fix tests before proceeding. |

---

## 8. Dependency Order

### 8.1 Migration Dependency Graph

```
Phase 0: Repository Audit
    │
    ▼
Phase 1: Architecture Enforcement Foundation
    │
    ▼
Phase 2: Shared Package Restructure
    │
    ▼
Phase 3: Accounts Bounded Context Creation
    │
    ▼
Phase 4: Properties Bounded Context Restructure
    │
    ▼
Phase 5: Finance Bounded Context Restructure
    │
    ▼
Phase 6: Documents and Integration Consolidation
    │
    ▼
Phase 7: Notification Restructure
    │
    ▼
Phase 8: Assistant Merge
    │
    ▼
Phase 9: Cross-Cutting Concerns and Cleanup
    │
    ▼
Phase 10: Performance Optimization
    │
    ▼
Phase 11: Security Hardening
    │
    ▼
Phase 12: Production Readiness
```

### 8.2 Dependency Rationale

| Phase | Depends On | Why |
|-------|-----------|-----|
| Phase 0 | None | Baseline must be established before any changes. |
| Phase 1 | Phase 0 | Architecture tools must be in place before refactoring begins. |
| Phase 2 | Phase 1 | `shared/` is a leaf module; it must be restructured before other contexts depend on it. |
| Phase 3 | Phase 2 | `accounts/` depends on `shared/` for exceptions, types, and validators. |
| Phase 4 | Phase 3 | `properties/` depends on `accounts/` for owner and tenant models. |
| Phase 5 | Phase 4 | `finance/` depends on `properties/` for rent records and buildings. |
| Phase 6 | Phase 5 | `documents/` depends on `finance/` for invoice PDFs. `integrations/` depends on `shared/` for protocols. |
| Phase 7 | Phase 6 | `notification/` is relatively independent but should be consolidated after core domains are stable. |
| Phase 8 | Phase 7 | `assistant/` depends on `notification/`, `documents/`, and `properties/`. Must wait until those are stable. |
| Phase 9 | Phase 8 | `analytics/` depends on `properties/`, `finance/`, and `notification/`. Cleanup must happen after all contexts are stable. |
| Phase 10 | Phase 9 | Performance optimization requires stable bounded contexts to measure and optimize. |
| Phase 11 | Phase 10 | Security hardening is easier on stable, optimized code. |
| Phase 12 | Phase 11 | Production readiness is the final step after all other work is complete. |

### 8.3 Parallelizable Work

Within each phase, these tasks can be done in parallel:
- Unit test creation for new modules.
- Integration test creation for new workflows.
- Documentation updates.
- CI configuration updates (within the same phase).

These tasks must NOT be done in parallel across phases:
- No work on Phase 4 until Phase 3 is merged.
- No work on Phase 5 until Phase 4 is merged.

---

## 9. Testing Strategy During Migration

### 9.1 Test Types Per Phase

| Phase | Unit Tests | Integration Tests | Architecture Tests | Regression Tests | Performance Tests | Security Tests |
|-------|-----------|-------------------|-------------------|------------------|-------------------|----------------|
| Phase 0 | — | Baseline | Baseline | — | Baseline | Baseline |
| Phase 1 | Add arch tests | — | New | — | — | — |
| Phase 2 | New structure | Import paths | Shared rules | — | — | — |
| Phase 3 | New app | Owner/tenant flows | Context rules | API contract | — | — |
| Phase 4 | Restructured | Property flows | Internal rules | API contract | Query counts | — |
| Phase 5 | Restructured | Finance flows | Context rules | PDF output | — | — |
| Phase 6 | New adapters | Document flows | Adapter rules | Webhook contract | — | Signature verify |
| Phase 7 | Channels | Notification flows | Channel rules | Delivery contract | — | — |
| Phase 8 | New app | Chat flows | Context rules | AI contract | — | — |
| Phase 9 | Analytics | Dashboard | All rules | Analytics contract | — | — |
| Phase 10 | — | All endpoints | — | Latency targets | Load tests | — |
| Phase 11 | Validators | Auth flows | Security rules | Security contract | — | Full scan |
| Phase 12 | — | End-to-end | Final audit | — | Load test | Final audit |

### 9.2 Unit Tests

**Location:** `<bounded_context>/tests/unit/`

**Strategy:**
- Every service method must have unit tests.
- Every utility function must have unit tests.
- Every validator must have unit tests.
- Use mocks for all external dependencies.
- Tests must be fast (< 100ms each).
- Tests must be deterministic (no time-dependent logic without control).

**Phase-specific focus:**
- Phase 2: Test new `shared/` structure.
- Phase 3: Test all `accounts/` services.
- Phase 4: Test restructured `properties/` services.
- Phase 5: Test restructured `finance/` services.
- Phase 6: Test new adapters and document services.
- Phase 7: Test channel adapters and orchestrator.
- Phase 8: Test `assistant/` services.
- Phase 9: Test `analytics/` services.

### 9.3 Integration Tests

**Location:** `<bounded_context>/tests/integration/` and `tests/integration/`

**Strategy:**
- Test complete workflows that span multiple layers.
- Use real database (test database).
- Use real Django ORM.
- Test API endpoints end-to-end.
- Test cross-context communication through public interfaces.

**Phase-specific focus:**
- Phase 3: Owner creation, tenant onboarding, profile updates.
- Phase 4: Building creation, unit creation, lease creation.
- Phase 5: Rent record creation, tax calculation, invoice generation.
- Phase 6: Document generation, e-signature flow, webhook handling.
- Phase 7: Notification delivery via all channels.
- Phase 8: Chatbot conversation, intent extraction, action execution.
- Phase 9: Dashboard summary, report generation.

### 9.4 Architecture Tests

**Location:** `tests/architecture/`

**Strategy:**
- Enforce all 130+ architecture rules.
- Run on every PR.
- Block merge on failure.

**Phase-specific focus:**
- Phase 1: Create initial architecture test suite.
- Phase 2-9: Add new rules as contexts are restructured.
- Phase 9: Final architecture audit.

### 9.5 Regression Tests

**Strategy:**
- Before any refactoring, record the current behavior with tests.
- After refactoring, verify identical behavior.
- If behavior changes, the change must be explicitly justified and documented.

**Phase-specific focus:**
- Every phase must have regression tests for the code being moved.
- API contract tests ensure request/response formats are unchanged.

### 9.6 Performance Tests

**Location:** `tests/performance/`

**Strategy:**
- Baseline performance established in Phase 0.
- Performance tests run in Phase 10 and beyond.
- Alert if performance degrades > 10% from baseline.

**Metrics:**
- API endpoint latency (p50, p95, p99).
- Database query count per endpoint.
- Database query execution time.
- Memory usage.
- Response payload size.

### 9.7 Security Tests

**Location:** `tests/security/` or within existing test directories.

**Strategy:**
- Input validation tests for all endpoints.
- Authentication and authorization tests.
- Rate limiting tests.
- File upload validation tests.
- Webhook signature verification tests.
- Secrets scanning in CI.

**Phase-specific focus:**
- Phase 11: Comprehensive security test suite.
- Phase 12: Final security audit.

---

## 10. CI Requirements

### 10.1 What Must Pass Before Merge

Every PR must pass ALL of the following before it can be merged:

| Check | Tool | Blocking | Phase Introduced |
|-------|------|----------|-----------------|
| Lint | Ruff | Yes | Phase 1 |
| Type checking | Mypy | Yes | Phase 1 |
| Unit tests | pytest | Yes | Phase 1 |
| Integration tests | pytest | Yes | Phase 1 |
| Architecture tests | import-linter, custom pytest | Yes | Phase 1 |
| Security scan | Semgrep, Bandit | Yes | Phase 11 |
| Mutation tests | mutmut | No (advisory) | Phase 1 |
| Performance tests | pytest-benchmark | No (advisory) | Phase 10 |
| Code coverage | coverage.py | Yes (> 80%) | Phase 1 |

### 10.2 Coverage Requirements

| Layer | Minimum | Target |
|-------|---------|--------|
| Services | 90% | 95% |
| Utilities | 85% | 90% |
| Models | 80% | 85% |
| Views | 70% | 80% |
| Integration tests | Critical paths | All critical paths |

**Rules:**
- Coverage must not decrease in any PR.
- New code must meet target coverage.
- Coverage reports are uploaded to CI artifacts.
- Coverage trends are tracked over time.

### 10.3 Architecture Validation

| Check | Tool | Blocking |
|-------|------|----------|
| No circular imports | import-linter | Yes |
| No private imports across contexts | import-linter | Yes |
| No business logic in views | Custom pytest plugin | Yes |
| No business logic in signals | Custom pytest plugin | Yes |
| No business logic in shared | Custom pytest plugin | Yes |
| No duplicate services | Custom pytest plugin | Yes |

### 10.4 Import Rules

- All imports must follow the import order convention (standard lib → third-party → shared → current context → local).
- No wildcard imports (`from module import *`).
- No unused imports.
- No circular imports.

**Enforcement:** Ruff + import-linter + custom architecture tests.

### 10.5 Lint

- **Tool:** Ruff
- **Rules:** Default + Django + pytest rules.
- **Blocking:** Yes. Zero lint errors allowed.
- **Auto-fix:** Ruff auto-fix runs in pre-commit.

### 10.6 Type Checking

- **Tool:** Mypy
- **Configuration:** `mypy.ini` with strict mode.
- **Blocking:** Yes. Zero type errors allowed.
- **Exclusions:** Tests, migrations, settings.

### 10.7 Security

- **Tools:** Semgrep, Bandit, GitLeaks.
- **Blocking:** Yes. High and medium severity findings block merge.
- **Scans:** Run on every PR.

### 10.8 Mutation Tests

- **Tool:** `mutmut`
- **Threshold:** 80% mutation score for critical services.
- **Blocking:** No (advisory). Report uploaded to CI artifacts.
- **Frequency:** Run on PRs that modify business logic.

### 10.9 Performance

- **Tool:** pytest-benchmark, Locust
- **Threshold:** No regression > 10% from baseline.
- **Blocking:** No (advisory). Report uploaded to CI artifacts.
- **Frequency:** Run on PRs that modify queries or services.

---

## 11. Code Review Checklist

Reviewers must verify ALL of the following before approving a PR:

### General
- [ ] PR has a single, clear purpose.
- [ ] PR description explains what changed and why.
- [ ] PR references an ADR if it makes architectural changes.
- [ ] PR size is within limits (small: 5 files / 200 lines, medium: 15 files / 500 lines).
- [ ] No unrelated changes are included.

### Tests
- [ ] Tests are added for new code.
- [ ] Regression tests are added for refactored code.
- [ ] All tests pass locally and in CI.
- [ ] Test coverage does not decrease.
- [ ] Tests are meaningful (not just coverage padding).

### Architecture
- [ ] No new architecture violations introduced.
- [ ] Public interfaces are stable or backward compatible.
- [ ] Compatibility wrappers are present for moved code.
- [ ] No circular imports.
- [ ] No private imports across bounded contexts.
- [ ] Views contain no business logic.
- [ ] Signals contain no business logic.
- [ ] Services contain no view logic.
- [ ] Repositories contain no business logic.
- [ ] Utilities contain no business logic.

### Code Quality
- [ ] No dead code (unused imports, variables, functions).
- [ ] No commented-out code.
- [ ] No `print()` statements.
- [ ] No hardcoded credentials.
- [ ] No PII in logs.
- [ ] No magic numbers (use named constants).
- [ ] No wildcard imports.
- [ ] No mutable default arguments.
- [ ] No bare `except:` clauses.
- [ ] No silent failures.

### Security
- [ ] Input validation is present for all user inputs.
- [ ] No SQL injection vulnerabilities.
- [ ] No XSS vulnerabilities.
- [ ] No CSRF vulnerabilities.
- [ ] No insecure direct object references.
- [ ] No sensitive data in error messages.
- [ ] File uploads are validated.

### Performance
- [ ] No N+1 queries introduced.
- [ ] Database queries use `select_related` / `prefetch_related`.
- [ ] Large result sets are paginated.
- [ ] No unnecessary database queries.

### Documentation
- [ ] ADR is created for architectural changes.
- [ ] Migration plan is updated if phase goals change.
- [ ] Docstrings are present for public methods.
- [ ] README is updated if app structure changes.

---

## 12. Definition of Done

### 12.1 Per-Phase Definition of Done

A phase is **done** only when ALL of the following are true:

1. **All planned activities are complete.** No activities are deferred without explicit approval.
2. **All tests pass.** Unit, integration, and architecture tests pass locally and in CI.
3. **CI passes all checks.** Lint, type checking, architecture tests, security scans.
4. **Code coverage meets targets.** No decrease from baseline; new code meets target.
5. **No breaking API changes.** All existing APIs work identically.
6. **Compatibility wrappers are in place** for all moved/renamed code (if applicable to phase).
7. **Documentation is updated.** Migration plan, ADRs, and inline documentation reflect the changes.
8. **Phase is deployed to staging.** Application runs correctly in staging environment.
9. **Smoke tests pass on staging.** Critical user journeys work on staging.
10. **Phase is reviewed and approved** by Principal Architect.
11. **Rollback plan is documented** and tested (if phase is high-risk).
12. **Team is informed** of phase completion and next steps.

### 12.2 What "Not Done" Looks Like

A phase is **NOT done** if:

1. Tests are failing in CI.
2. Architecture tests show new violations.
3. Code coverage has decreased.
4. APIs are broken (even if "just temporarily").
5. Compatibility wrappers are missing for moved code.
6. The application does not start.
7. The application crashes on staging.
8. Critical user journeys fail on staging.
9. Documentation is outdated.
10. The phase was not reviewed by Principal Architect.
11. Rollback plan was not tested.
12. The team was not informed.

---

## 13. Final Migration Checklist

This checklist tracks the complete migration from start to finish.

### Phase 0: Repository Audit
- [ ] Complete current state assessment checklist.
- [ ] Document all apps, models, views, services, signals, tests.
- [ ] Document all cross-context imports.
- [ ] Document all duplicate services.
- [ ] Document all signal violations.
- [ ] Document all view violations.
- [ ] Record baseline test coverage.
- [ ] Record baseline performance metrics.
- [ ] Create `02_migration_baseline.md`.
- [ ] Review baseline with team.
- [ ] Get Principal Architect approval.

### Phase 1: Architecture Enforcement
- [ ] Configure `import-linter.ini`.
- [ ] Create architecture test suite.
- [ ] Add pre-commit hooks.
- [ ] Update CI workflows.
- [ ] Add coverage reporting.
- [ ] Add mutation testing.
- [ ] Document architecture test patterns.
- [ ] Train team on architecture tests.
- [ ] Deploy to staging.
- [ ] Get Principal Architect approval.

### Phase 2: Shared Package Restructure
- [ ] Audit `shared/` for business logic.
- [ ] Move business logic to appropriate contexts.
- [ ] Create `shared/exceptions/`.
- [ ] Create `shared/types/`.
- [ ] Create `shared/enums/`.
- [ ] Create `shared/protocols/`.
- [ ] Create `shared/validators/`.
- [ ] Create `shared/constants/`.
- [ ] Create `shared/dto/`.
- [ ] Update all imports.
- [ ] Add compatibility wrappers.
- [ ] Remove wrappers after zero imports.
- [ ] Run full test suite.
- [ ] Deploy to staging.
- [ ] Get Principal Architect approval.

### Phase 3: Accounts Bounded Context
- [ ] Create `accounts/` app.
- [ ] Move `OwnerProfile` and `TenantProfile` models.
- [ ] Move owner/tenant services.
- [ ] Move serializers.
- [ ] Move views to `api/v1/`.
- [ ] Move billing/payment method code.
- [ ] Add `accounts` to `INSTALLED_APPS`.
- [ ] Create and run migrations.
- [ ] Update imports in consuming apps.
- [ ] Add compatibility wrappers.
- [ ] Remove wrappers after zero imports.
- [ ] Run full test suite.
- [ ] Deploy to staging.
- [ ] Get Principal Architect approval.

### Phase 4: Properties Bounded Context
- [ ] Split `properties/models.py` into per-entity files.
- [ ] Move views to `properties/api/v1/`.
- [ ] Create `properties/repositories/`.
- [ ] Create `properties/selectors/`.
- [ ] Create `properties/validators/`.
- [ ] Create `properties/permissions/`.
- [ ] Create `properties/exceptions/`.
- [ ] Create `properties/constants/`.
- [ ] Create `properties/interfaces/`.
- [ ] Create `properties/dto/`.
- [ ] Fix signal handlers.
- [ ] Move pure utilities to `shared/`.
- [ ] Update imports.
- [ ] Add compatibility wrappers.
- [ ] Remove wrappers after zero imports.
- [ ] Run full test suite.
- [ ] Deploy to staging.
- [ ] Get Principal Architect approval.

### Phase 5: Finance Bounded Context
- [ ] Restructure `finance/` internal folders.
- [ ] Split `finance/models.py` into per-entity files.
- [ ] Move views to `finance/api/v1/`.
- [ ] Create `finance/repositories/`, `selectors/`, etc.
- [ ] Move PDF generation to `documents/`.
- [ ] Create `documents/services/pdf_generator.py`.
- [ ] Create `documents/services/invoice_service.py`.
- [ ] Create `documents/services/receipt_service.py`.
- [ ] Update finance services to use `documents` interface.
- [ ] Add compatibility wrappers.
- [ ] Remove wrappers after zero imports.
- [ ] Run full test suite.
- [ ] Deploy to staging.
- [ ] Get Principal Architect approval.

### Phase 6: Documents and Integrations
- [ ] Create `integrations/` app.
- [ ] Move payment adapters to `integrations/adapters/payment/`.
- [ ] Consolidate Leegality client in `documents/services/leegality.py`.
- [ ] Merge duplicate Leegality implementations.
- [ ] Create `documents/services/agreement_service.py`.
- [ ] Create notification adapters in `integrations/`.
- [ ] Create storage adapter in `integrations/`.
- [ ] Create AI adapter in `integrations/`.
- [ ] Create webhook handlers in `integrations/webhooks/`.
- [ ] Move remaining services from `rentsecure_be/`.
- [ ] Add compatibility wrappers.
- [ ] Remove wrappers after zero imports.
- [ ] Delete `rentsecure_be/` after zero imports.
- [ ] Run full test suite.
- [ ] Deploy to staging.
- [ ] Get Principal Architect approval.

### Phase 7: Notification Restructure
- [ ] Restructure `notification/` internal folders.
- [ ] Create `notification/services/channels/`.
- [ ] Move orchestration to `properties/services/notification_service.py`.
- [ ] Move `extra_charge_reminders.py` and `late_fees_notify_service.py`.
- [ ] Fix signal handlers.
- [ ] Create `notification/services/orchestrator.py`.
- [ ] Move utilities to `shared/` or `notification/services/`.
- [ ] Add compatibility wrappers.
- [ ] Remove wrappers after zero imports.
- [ ] Run full test suite.
- [ ] Deploy to staging.
- [ ] Get Principal Architect approval.

### Phase 8: Assistant Merge
- [ ] Create `assistant/` app.
- [ ] Move AI services from `smartbot/` and `ai_assistant/`.
- [ ] Move non-AI services to correct domains.
- [ ] Move models, views, tests.
- [ ] Delete `smartbot/` and `ai_assistant/`.
- [ ] Add compatibility wrappers.
- [ ] Remove wrappers after zero imports.
- [ ] Run full test suite.
- [ ] Deploy to staging.
- [ ] Get Principal Architect approval.

### Phase 9: Cross-Cutting Concerns
- [ ] Create `analytics/` app.
- [ ] Move analytics code from `properties/` and `core/`.
- [ ] Move dashboard views.
- [ ] Create `analytics/services/`, `selectors/`, etc.
- [ ] Delete `dashboard/` after integration.
- [ ] Delete `rentsecure_be/` after zero imports.
- [ ] Remove all compatibility wrappers.
- [ ] Clean up dead code.
- [ ] Run full test suite.
- [ ] Deploy to staging.
- [ ] Get Principal Architect approval.

### Phase 10: Performance Optimization
- [ ] Profile all API endpoints.
- [ ] Add `select_related` / `prefetch_related`.
- [ ] Add database indexes.
- [ ] Implement caching.
- [ ] Add pagination to list endpoints.
- [ ] Implement cursor-based pagination.
- [ ] Add streaming responses.
- [ ] Add query count assertions.
- [ ] Run performance tests.
- [ ] Deploy to staging.
- [ ] Get Principal Architect approval.

### Phase 11: Security Hardening
- [ ] Audit input validation.
- [ ] Add missing validators.
- [ ] Implement rate limiting.
- [ ] Verify JWT implementation.
- [ ] Implement file upload validation.
- [ ] Add webhook signature verification.
- [ ] Implement secrets management.
- [ ] Add security headers.
- [ ] Add PII redaction in logs.
- [ ] Run security scans.
- [ ] Add security tests to CI.
- [ ] Deploy to staging.
- [ ] Get Principal Architect approval.

### Phase 12: Production Readiness
- [ ] Finalize production settings.
- [ ] Configure structured logging.
- [ ] Set up monitoring dashboards.
- [ ] Configure alerts.
- [ ] Create operational runbooks.
- [ ] Document disaster recovery.
- [ ] Document rollback procedure.
- [ ] Run load tests.
- [ ] Verify backup/restore.
- [ ] Verify health checks.
- [ ] Final architecture review.
- [ ] Final security review.
- [ ] Deploy to production.
- [ ] Get Principal Architect approval.

---

## 14. Estimated Timeline

### 14.1 Timeline Overview

| Phase | Duration | Start | End | Dependencies |
|-------|----------|-------|-----|--------------|
| Phase 0 | 1 week | Week 1 | Week 1 | None |
| Phase 1 | 1-2 weeks | Week 2 | Week 3 | Phase 0 |
| Phase 2 | 1 week | Week 3 | Week 4 | Phase 1 |
| Phase 3 | 2 weeks | Week 4 | Week 6 | Phase 2 |
| Phase 4 | 2 weeks | Week 6 | Week 8 | Phase 3 |
| Phase 5 | 1.5 weeks | Week 8 | Week 9.5 | Phase 4 |
| Phase 6 | 2 weeks | Week 9.5 | Week 11.5 | Phase 5 |
| Phase 7 | 1.5 weeks | Week 11.5 | Week 13 | Phase 6 |
| Phase 8 | 2 weeks | Week 13 | Week 15 | Phase 7 |
| Phase 9 | 2 weeks | Week 15 | Week 17 | Phase 8 |
| Phase 10 | 1.5 weeks | Week 17 | Week 18.5 | Phase 9 |
| Phase 11 | 1 week | Week 18.5 | Week 19.5 | Phase 10 |
| Phase 12 | 1 week | Week 19.5 | Week 20.5 | Phase 11 |

**Total estimated duration:** 20.5 weeks (~5 months)

### 14.2 Critical Path

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8 → Phase 9 → Phase 10 → Phase 11 → Phase 12
```

Every phase depends on the previous phase. There is no parallelization of phases.

### 14.3 Task Sizing

| Task Type | Small | Medium | Large | Epic |
|-----------|-------|--------|-------|------|
| Move a single service file | 2h | — | — | — |
| Create compatibility wrapper | 1h | — | — | — |
| Update imports in one app | 1h | — | — | — |
| Restructure a bounded context | — | 2-3 days | — | — |
| Create a new bounded context | — | 3-5 days | — | — |
| Consolidate duplicate services | — | 3-5 days | — | — |
| Merge two bounded contexts | — | — | 1-2 weeks | — |
| Complete phase | — | — | — | 1-2 weeks |

### 14.4 Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| Phase 0 | Must complete first | Baseline must be established. |
| Phase 1 | Must complete before Phase 2 | Architecture tools must be in place. |
| Phase 2 | Must complete before Phase 3 | `shared/` is a leaf module. |
| Phase 3 | Must complete before Phase 4 | `accounts/` is dependency of `properties/`. |
| Phase 4 | Must complete before Phase 5 | `properties/` is dependency of `finance/`. |
| Phase 5 | Must complete before Phase 6 | `finance/` is dependency of `documents/`. |
| Phase 6 | Must complete before Phase 7 | Core domains must be stable. |
| Phase 7 | Must complete before Phase 8 | `notification/` must be stable. |
| Phase 8 | Must complete before Phase 9 | `assistant/` must be stable. |
| Phase 9 | Must complete before Phase 10 | All contexts must be stable. |
| Phase 10 | Must complete before Phase 11 | Performance baseline must be established. |
| Phase 11 | Must complete before Phase 12 | Security must be verified. |

### 14.5 Buffer

- **Phase buffer:** 20% buffer added to each phase estimate.
- **Total buffer:** ~4 weeks.
- **Total with buffer:** ~24.5 weeks (~6 months).

**Contingency:** If a phase takes longer than estimated, the timeline is adjusted. No phase is rushed. Quality is never sacrificed for schedule.

---

## 15. AI Agent Workflow

AI agents (including Kilo, Copilot, and other coding assistants) must follow this workflow for every migration task.

### 15.1 Task Lifecycle

```
1. Analyze
   ↓
2. Plan
   ↓
3. Refactor
   ↓
4. Self-Review
   ↓
5. Architecture Review
   ↓
6. Human Approval
   ↓
7. Commit
   ↓
8. Push
   ↓
9. CI Validation
   ↓
10. Merge
```

### 15.2 Step 1: Analyze

**Objective:** Understand the current state and the target state.

**Actions:**
1. Read the relevant section of `01_target_architecture.md`.
2. Read the relevant section of `02_migration_roadmap.md`.
3. Read the current code that needs to be changed.
4. Identify all files that will be affected.
5. Identify all imports that will be affected.
6. Identify all tests that cover the affected code.
7. Identify any duplicate services or circular dependencies.
8. Document the current behavior with examples.

**Output:** Analysis document with:
- List of affected files.
- List of affected imports.
- List of affected tests.
- Current behavior description.
- Target behavior description.
- Risks and assumptions.

### 15.3 Step 2: Plan

**Objective:** Create a detailed plan for the refactoring.

**Actions:**
1. Break the task into atomic steps.
2. Identify the order of steps (dependencies between steps).
3. Identify which steps can be done in parallel.
4. For each step, identify:
   - What files to create.
   - What files to modify.
   - What files to delete.
   - What imports to update.
   - What tests to add or modify.
5. Identify compatibility wrapper requirements.
6. Identify rollback strategy for each step.
7. Create a checklist of all steps.

**Output:** Plan document with:
- Step-by-step checklist.
- File changes per step.
- Import changes per step.
- Test changes per step.
- Compatibility wrapper plan.
- Rollback plan per step.

### 15.4 Step 3: Refactor

**Objective:** Execute the plan, making one atomic change at a time.

**Actions:**
1. Execute the first step in the plan.
2. Run tests after each step.
3. Run architecture tests after each step.
4. If tests fail, fix before proceeding.
5. If architecture tests fail, fix before proceeding.
6. Continue to next step.
7. After all steps are complete, run the full test suite.

**Rules:**
- Never skip tests.
- Never skip architecture tests.
- Never make multiple unrelated changes in one step.
- Always add compatibility wrappers when moving code.
- Never delete code until zero imports remain.

**Output:** Branch with all changes committed.

### 15.5 Step 4: Self-Review

**Objective:** Review the changes as if you were a human reviewer.

**Actions:**
1. Review the git diff.
2. Check that every change matches the plan.
3. Check that no unintended changes were made.
4. Check that all tests pass.
5. Check that architecture tests pass.
6. Check that lint passes.
7. Check that type checking passes.
8. Check that no secrets were introduced.
9. Check that no PII was introduced.
10. Check that the commit messages follow conventions.
11. Check that the PR description is complete.

**Output:** Self-review checklist completed. Any issues found are fixed before proceeding.

### 15.6 Step 5: Architecture Review

**Objective:** Verify that the changes comply with the target architecture.

**Actions:**
1. Read `01_target_architecture.md`.
2. Verify that the changes match the target architecture.
3. Check that bounded context boundaries are respected.
4. Check that dependency direction is correct.
5. Check that no circular imports were introduced.
6. Check that public interfaces are stable.
7. Check that no business logic was added to views or signals.
8. Check that no business logic was added to `shared/`.
9. Check that duplicate services were not created.
10. Run architecture tests locally.
11. Verify that the changes align with architecture principles.

**Output:** Architecture review checklist completed. Any violations are fixed before proceeding.

### 15.7 Step 6: Human Approval

**Objective:** Get human review and approval before merging.

**Actions:**
1. Push the branch to remote.
2. Create a PR with a complete description.
3. Request review from at least one human reviewer.
4. Address all review comments.
5. Re-run CI after addressing comments.
6. Get explicit approval from reviewer.

**Rules:**
- AI agents cannot merge their own PRs.
- Human approval is mandatory for all PRs.
- If reviewer requests changes, return to Step 3.

**Output:** Approved PR ready to merge.

### 15.8 Step 7: Commit

**Objective:** Create clean, conventional commits.

**Actions:**
1. Ensure all changes are committed.
2. Use conventional commit messages.
3. Squash commits if necessary (follow team convention).
4. Verify commit message quality.

**Output:** Clean commit history.

### 15.9 Step 8: Push

**Objective:** Push the branch to remote.

**Actions:**
1. Push the branch to the remote repository.
2. Verify that CI starts running.
3. Monitor CI progress.

**Output:** Branch pushed, CI running.

### 15.10 Step 9: CI Validation

**Objective:** Ensure all CI checks pass.

**Actions:**
1. Monitor CI pipeline.
2. If any check fails, fix the issue and push again.
3. If all checks pass, proceed to merge.

**Output:** All CI checks passing.

### 15.11 Step 10: Merge

**Objective:** Merge the PR to `main`.

**Actions:**
1. Wait for human reviewer to merge.
2. Verify that the merge to `main` succeeds.
3. Verify that the deployment to staging succeeds.
4. Run smoke tests on staging.
5. Delete the migration branch.

**Output:** Changes merged to `main`, deployed to staging.

### 15.12 AI Agent Rules

| Rule | Description |
|------|-------------|
| No autonomous merging | AI agents cannot merge PRs without human approval. |
| No skipping steps | All 10 steps must be completed for every task. |
| No large PRs | AI agents must split large changes into multiple PRs. |
| No breaking changes | AI agents must preserve backward compatibility. |
| No secrets | AI agents must never introduce secrets. |
| No assumptions | AI agents must verify assumptions with code inspection, not guesses. |
| Document everything | AI agents must document their analysis and plan. |
| Ask for help | AI agents must escalate to humans when stuck. |
| Follow conventions | AI agents must follow naming, import, and commit conventions. |
| Test everything | AI agents must run all relevant tests after every change. |

---

## 16. Long-Term Maintenance Strategy

### 16.1 Evolving the Codebase Without Violating Architecture

After the migration is complete, the codebase must continue to evolve without violating the target architecture. This section defines how future developers (human and AI) should work with the codebase.

### 16.2 Adding New Features

When adding a new feature:

1. **Identify the bounded context.** Which business capability does this feature serve? Add the feature to that context.
2. **Check the target architecture.** Does the feature fit the existing structure? If not, propose an ADR.
3. **Follow the layer rules.** Business logic goes in services. Views stay thin. Signals trigger events.
4. **Use existing interfaces.** Do not create new adapters for existing external services.
5. **Add tests.** Unit tests for services, integration tests for workflows.
6. **Update architecture tests.** If the feature introduces new patterns, add architecture tests.
7. **Get review.** Follow the PR strategy and code review checklist.

### 16.3 Modifying Existing Code

When modifying existing code:

1. **Understand the current structure.** Read the target architecture document.
2. **Preserve public interfaces.** If modifying a public interface, maintain backward compatibility.
3. **Update tests.** If behavior changes, update tests. If behavior stays the same, tests should still pass.
4. **Check for duplicates.** If modifying a service, check if a duplicate exists. If so, consolidate.
5. **Run architecture tests.** Ensure no violations are introduced.

### 16.4 Refactoring

When refactoring:

1. **Follow the migration principles.** Move before rewrite. One responsibility per PR. Preserve behavior.
2. **Add tests first.** Ensure the current behavior is tested before refactoring.
3. **Use compatibility wrappers.** Never break existing callers.
4. **Remove dead code.** Delete wrappers and dead code after migration is complete.
5. **Document the refactoring.** Create an ADR if the refactoring changes architecture.

### 16.5 Adding New Bounded Contexts

When a new business capability emerges that does not fit existing contexts:

1. **Propose an ADR.** Explain why a new context is needed.
2. **Get approval.** Principal Architect must approve new contexts.
3. **Follow the target structure.** New contexts must match the folder structure and layering defined in `01_target_architecture.md`.
4. **Define public interfaces.** Export only what other contexts need.
5. **Add architecture tests.** Ensure the new context follows all rules.
6. **Update dependency graph.** Document the new context's dependencies.

### 16.6 Adding New External Integrations

When adding a new external service (payment gateway, notification channel, etc.):

1. **Use the adapter pattern.** Define a protocol in `shared/protocols/`.
2. **Implement in `integrations/`.** Add the adapter to `integrations/adapters/`.
3. **Follow existing patterns.** Study existing adapters for conventions.
4. **Add tests.** Unit tests for the adapter, integration tests for the workflow.
5. **Add to feature flags.** If the integration is Stage 2, wrap it in a feature flag.
6. **Update documentation.** Document the new integration.

### 16.7 Preventing Architecture Drift

Architecture drift is the gradual accumulation of changes that violate the target architecture. To prevent drift:

1. **Run architecture tests in CI.** Every PR must pass architecture tests.
2. **Review PRs for architecture compliance.** Use the code review checklist.
3. **Schedule architecture reviews.** Monthly review of the codebase against the target architecture.
4. **Update documentation.** Keep `01_target_architecture.md` and `02_migration_roadmap.md` current.
5. **Train new developers.** Onboard new team members with the architecture documents.
6. **Automate enforcement.** Use import-linter, custom pytest plugins, and pre-commit hooks.
7. **Address violations immediately.** Do not let violations accumulate.

### 16.8 What Must Never Change

These architectural decisions are permanent. They must not be reversed without a formal ADR and Principal Architect approval:

1. **Business capability organization.** Bounded contexts must remain organized by business capability.
2. **Views are thin.** Business logic must never return to views.
3. **Signals trigger events.** Signals must never contain business logic.
4. **Public interfaces are contracts.** Breaking a public interface requires formal deprecation.
5. **No circular dependencies.** This must be maintained forever.
6. **Single source of truth.** Duplicate implementations must never be reintroduced.
7. **Dependency direction.** Dependencies must always flow from business to infrastructure.
8. **Zero breaking changes during migration.** Compatibility wrappers are mandatory for all moves.
9. **Shared has no business logic.** This must be enforced permanently.
10. **Testability is non-negotiable.** Code that cannot be tested easily must be refactored.

### 16.9 Continuous Improvement

The architecture is not static. It must evolve as the business evolves. However, evolution must be deliberate, documented, and approved.

**Process for architectural changes:**
1. Propose an ADR explaining the change.
2. Get team feedback.
3. Get Principal Architect approval.
4. Implement the change following the migration principles.
5. Update documentation.
6. Communicate the change to the team.

**Process for emergency fixes:**
1. Fix the emergency.
2. Create an ADR after the fact explaining what changed and why.
3. Get Principal Architect review.
4. If the fix violates architecture, schedule a follow-up to restore architecture compliance.

---

*Document ratified by the Principal Software Architect. This is the permanent implementation roadmap for the RentSecure backend migration. Every developer, reviewer, and AI agent must follow this roadmap.*
