# RentSecureBE — Architecture v1.1 Implementation Master Plan

**Status:** APPROVED FOR EXECUTION
**Date:** 2026-07-19
**Architecture Baseline:** v1.1 Release Candidate
**Constraint:** Execute only. No redesign. No new patterns. No rejected patterns.
**Scope:** Complete migration from current state to Architecture v1.1 target state

---

## Table of Contents

1. [Overall Implementation Strategy](#1-overall-implementation-strategy)
2. [Phase -1: Break Circular Dependencies](#2-phase--1-break-circular-dependencies)
3. [Phase 0: Foundation & Critical Fixes](#3-phase-0-foundation--critical-fixes)
4. [Phase 1: Extract Identity Services](#4-phase-1-extract-identity-services)
5. [Phase 2: Extract Subscription](#5-phase-2-extract-subscription)
6. [Phase 3: Extract Payment](#6-phase-3-extract-payment)
7. [Phase 4: Extract Dashboard & Notification](#7-phase-4-extract-dashboard--notification)
8. [Phase 5: Deprecate Core](#8-phase-5-deprecate-core)
9. [Phase 6: Optimization](#9-phase-6-optimization)
10. [Git Branch Strategy](#10-git-branch-strategy)
11. [CI/CD Pipeline](#11-cicd-pipeline)
12. [Rollback Strategies](#12-rollback-strategies)
13. [Testing Strategy](#13-testing-strategy)
14. [Architecture Validation](#14-architecture-validation)
15. [Database Migrations](#15-database-migrations)
16. [API Compatibility](#16-api-compatibility)
17. [Deprecation Plans](#17-deprecation-plans)
18. [Release Plans](#18-release-plans)
19. [Documentation Updates](#19-documentation-updates)
20. [ADR Updates](#20-adr-updates)
21. [Risk Register](#21-risk-register)
22. [Deliverables Summary](#22-deliverables-summary)

---

## 1. Overall Implementation Strategy

### 1.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **Incremental** | Each phase delivers working software. No big-bang migrations. |
| **Production-Safe** | Every change is backward-compatible. Old URLs, imports, and APIs remain valid during transition. |
| **Zero Downtime** | No phase requires application downtime. Deployments are rolling updates. |
| **Test-Driven** | Every phase includes tests before, during, and after implementation. |
| **Rollback-Ready** | Every phase has a tested rollback procedure. |
| **Architecture-Enforced** | import-linter and architecture tests run on every commit. |

### 1.2 Implementation Constraints

| Constraint | Rationale |
|------------|-----------|
| **No `apps/` parent directory** | Changes every import path. No architectural value. High risk. |
| **No `AUTH_USER_MODEL` migration** | Django does not support dual user models or proxy transitions. |
| **No `rent/` bounded context** | Phantom context. Rent logic stays in `properties/`. |
| **Keep `core.User` as `AUTH_USER_MODEL`** | Permanent. Identity services move; model stays. |
| **Apps at project root** | Keep existing app locations. No path changes. |
| **Phase 5 is the only breaking change** | All prior phases are additive or internal refactors. |

### 1.3 Success Metrics

| Metric | Target |
|--------|--------|
| **Zero production incidents** | No downtime, no data loss, no security incidents |
| **Test coverage** | ≥90% unit, ≥80% integration, 100% architecture tests passing |
| **Import-linter violations** | 0 at all times |
| **Circular dependencies** | 0 at all times |
| **Rollback tested** | Every phase has a tested rollback procedure |
| **CI green** | All pipelines pass on every commit |
| **API compatibility** | 100% backward-compatible until Phase 5 |

### 1.4 Team Structure

| Role | Responsibility |
|------|----------------|
| **Staff Engineer** | Overall technical leadership, ADR approvals, architecture gates |
| **Platform Team Lead** | `platform/`, `shared/`, `payments/`, `notification/`, `config/` |
| **Product Team Lead** | `properties/`, `finance/`, `documents/`, `dashboard/` |
| **Security Lead** | Security reviews, encryption, audit logging, webhook verification |
| **DevOps Engineer** | CI/CD, deployments, infrastructure, monitoring |
| **QA Lead** | Test strategy, coverage enforcement, regression testing |

### 1.5 Timeline Overview

| Phase | Duration | Weeks | Risk | Breaking Changes |
|-------|----------|-------|------|------------------|
| Phase -1 | Break circular dependencies | Week 1 | Medium | None |
| Phase 0 | Foundation & Critical Fixes | Week 2-3 | Medium | None |
| Phase 1 | Extract Identity Services | Week 4-6 | Medium | None |
| Phase 2 | Extract Subscription | Week 7-9 | Low | None |
| Phase 3 | Extract Payment | Week 10-12 | Medium | None |
| Phase 4 | Extract Dashboard & Notification | Week 13-14 | Low | None |
| Phase 5 | Deprecate Core | Week 15-16 | High | **YES** — major version |
| Phase 6 | Optimization | Week 17-20 | Low | None |

**Total Duration:** 20 weeks (5 months)

---

## 2. Phase -1: Break Circular Dependencies

### Purpose

Eliminate all 4 circular dependency cycles before any structural changes. Circular dependencies are the #1 cause of import errors and fragile refactoring. Breaking them first makes all subsequent phases safer.

### Dependencies

- None (entry point for the entire migration)

### Risk

**Medium** — Moving `type_compat.py` touches 20+ files. Must be done in a single coordinated PR.

### Rollback

Revert the single Phase -1 PR. All changes are additive (file moves + import updates). No data changes.

### Tasks

| ID | Task | Files Affected | Effort | Risk |
|----|------|----------------|--------|------|
| -1.1 | Move `type_compat.py` from `rentsecure_be/` to `shared/` | `rentsecure_be/type_compat.py`, 20+ importers | 4h | Medium |
| -1.2 | Keep deprecated shim in `rentsecure_be/type_compat.py` | `rentsecure_be/type_compat.py` | 1h | Low |
| -1.3 | Update all `from rentsecure_be.type_compat import override` → `from shared.type_compat import override` | 20+ files across 6 apps | 4h | Medium |
| -1.4 | Move `cashfree_payout.py` from `rentsecure_be/utils/` to `payments/adapters/cashfree_client.py` | `rentsecure_be/utils/cashfree_payout.py`, `payments/adapters/cashfree.py` | 3h | Medium |
| -1.5 | Update `payments/adapters/cashfree.py` imports | `payments/adapters/cashfree.py` | 1h | Low |
| -1.6 | Add `payments` to `INSTALLED_APPS` | `rentsecure_be/settings.py` | 0.5h | Low |
| -1.7 | Create initial `payments/migrations/` package | `payments/migrations/__init__.py` | 0.5h | Low |

### Validation Checklist

- [ ] `import-linter check` passes with 0 violations
- [ ] `python manage.py check` passes
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] No circular dependencies detected by AST analysis
- [ ] `shared/type_compat.py` exists and is imported by all former `rentsecure_be.type_compat` importers
- [ ] `rentsecure_be/type_compat.py` is a deprecated shim that re-exports from `shared/`

### Definition of Done

- [ ] All 7 tasks complete
- [ ] CI passes on `phase--1-break-cycles` branch
- [ ] PR approved by Staff Engineer and Platform Team Lead
- [ ] Merged to `main`

### CI Gates

| Gate | Tool | Threshold | Blocking |
|------|------|-----------|----------|
| Lint | Ruff | 0 errors | Yes |
| Type Check | MyPy | 0 errors | Yes |
| Import Rules | import-linter | 0 violations | Yes |
| Tests | Pytest | All pass, ≥90% coverage | Yes |
| Django Check | `manage.py check` | 0 errors | Yes |

### Architecture Gates

| Gate | Validation |
|------|-----------|
| Circular dependencies | AST analysis confirms 0 cycles |
| Import boundaries | `import-linter` confirms 0 violations |
| `rentsecure_be/` boundary | No app (except `rentsecure_be/`) imports from `rentsecure_be/` |

### Testing Gates

| Gate | Validation |
|------|-----------|
| Unit tests | All existing tests pass |
| Integration tests | All existing tests pass |
| No new test failures | CI passes |

### Expected Deliverables

- `shared/type_compat.py` (moved from `rentsecure_be/`)
- `rentsecure_be/type_compat.py` (deprecated shim)
- `payments/adapters/cashfree_client.py` (moved from `rentsecure_be/utils/cashfree_payout.py`)
- `payments/migrations/__init__.py` (new)
- Updated `rentsecure_be/settings.py` with `payments` in `INSTALLED_APPS`
- 20+ files updated with new import paths

---

## 3. Phase 0: Foundation & Critical Fixes

### Purpose

Fix all Critical findings from Architecture v1.1 Review before any app extraction begins. This phase is entirely additive — no existing functionality is removed. All changes are backward-compatible.

### Dependencies

- Phase -1 complete (circular dependencies broken)

### Risk

**Medium** — Moving models requires data migrations. Must be tested in staging.

### Rollback

Revert the Phase 0 PR. Since all changes are additive (new models, new files, new URLs alongside old ones), rollback is safe.

### Tasks

| ID | Task | Files Affected | Effort | Risk |
|----|------|----------------|--------|------|
| 0.1 | Add encrypted `BankAccountNumber` and `IFSCCode` field types to `shared/` | `shared/fields.py` (new) | 3h | Low |
| 0.2 | Create `payments/models.py` with `OwnerBankDetails` using encrypted fields | `payments/models.py` (new), `core/migrations/` (new) | 4h | Medium |
| 0.3 | Create data migration: `core_ownerbankdetails` → `payment_ownerbankdetails` | `payments/migrations/0001_initial.py`, `core/migrations/XXXX_copy_bank_details.py` | 4h | Medium |
| 0.4 | Create `notification/models.py` with `NotificationPreference` | `notification/models.py` (new), `core/migrations/` (new) | 3h | Medium |
| 0.5 | Create data migration: `core_notificationpreference` → `notification_notificationpreference` | `notification/migrations/0001_initial.py`, `core/migrations/XXXX_copy_prefs.py` | 4h | Medium |
| 0.6 | Create `payments/views/webhooks.py` with webhook handlers | `payments/views/webhooks.py` (new) | 4h | Medium |
| 0.7 | Move webhook URLs from `core/urls.py` to `payments/urls.py` | `payments/urls.py` (new), `core/urls.py`, `rentsecure_be/urls.py` | 2h | Medium |
| 0.8 | Keep old webhook URLs in `core/urls.py` as deprecated redirects | `core/urls.py` | 1h | Low |
| 0.9 | Split `core/views.py` into `auth_views.py`, `subscription_views.py`, `bank_views.py`, `reporting_views.py` | `core/views.py` → 4 files | 6h | Medium |
| 0.10 | Move root management commands to app `management/` directories | 15 files moved | 8h | Medium |
| 0.11 | Rewrite `import-linter.ini` without `rentsecure_be` as allowed layer | `import-linter.ini` | 3h | Medium |
| 0.12 | Add architecture regression tests | `tests/architecture/` (new) | 6h | Medium |
| 0.13 | Add webhook idempotency keys | `payments/models.py` (new), webhook views | 3h | Medium |
| 0.14 | Add audit logging for payment operations | `payments/models.py`, `core/models.py` | 3h | Low |
| 0.15 | Add migration rollback tests to CI | `.github/workflows/ci.yml`, `tests/test_migrations.py` (new) | 3h | Low |

### Validation Checklist

- [ ] `python manage.py makemigrations` generates migrations for `payments` and `notification`
- [ ] `python manage.py migrate` applies all migrations cleanly
- [ ] Data migrations copy `OwnerBankDetails` and `NotificationPreference` correctly
- [ ] Old webhook URLs return 301/302 redirects to new URLs
- [ ] New webhook URLs handle Cashfree and Razorpay payloads
- [ ] `core/views.py` is split into 4 focused view modules
- [ ] All 15 root management commands are in app `management/` directories
- [ ] `import-linter check` passes with 0 violations
- [ ] Architecture tests pass
- [ ] All existing tests pass
- [ ] `python manage.py migrate --reverse` works on test database

### Definition of Done

- [ ] All 15 tasks complete
- [ ] `payments` in `INSTALLED_APPS`
- [ ] `OwnerBankDetails` in `payments/models.py` with encrypted fields
- [ ] `NotificationPreference` in `notification/models.py`
- [ ] Webhooks in `payments/views/webhooks.py`
- [ ] Old webhook URLs redirect to new URLs
- [ ] `core/views.py` split into 4 files
- [ ] Root management commands moved to apps
- [ ] `import-linter.ini` rewritten
- [ ] Architecture regression tests added
- [ ] CI passes on `phase-0-foundation` branch
- [ ] PR approved by Staff Engineer, Platform Lead, Security Lead
- [ ] Merged to `main`

### CI Gates

| Gate | Tool | Threshold | Blocking |
|------|------|-----------|----------|
| Lint | Ruff | 0 errors | Yes |
| Type Check | MyPy | 0 errors | Yes |
| Import Rules | import-linter | 0 violations | Yes |
| Tests | Pytest | All pass, ≥90% coverage | Yes |
| Django Check | `manage.py check` | 0 errors | Yes |
| Migration Forward | `manage.py migrate` | 0 errors | Yes |
| Migration Reverse | `manage.py migrate --reverse` | 0 errors | Yes |
| Security | Bandit | 0 high/medium | Yes |
| Architecture | pytest `tests/architecture/` | 0 failures | Yes |

### Architecture Gates

| Gate | Validation |
|------|-----------|
| No `rentsecure_be/` imports | AST scan confirms 0 imports from `rentsecure_be/` in app code |
| `payments/` registered | `payments` in `INSTALLED_APPS` |
| Encrypted fields | `bank_account_number` and `ifsc_code` use encrypted field types |
| Webhook location | All webhook handlers in `payments/views/webhooks.py` |
| `core/views.py` size | No file in `core/views/` exceeds 300 lines |
| Management commands | No management commands at project root |

### Testing Gates

| Gate | Validation |
|------|-----------|
| Unit tests | ≥90% coverage, all pass |
| Integration tests | ≥80% coverage, all pass |
| Webhook tests | Cashfree and Razorpay webhooks verified with idempotency |
| Data migration tests | Bank details and preferences copied correctly |
| Rollback tests | `migrate --reverse` passes |
| Architecture tests | All pass |

### Expected Deliverables

- `shared/fields.py` (encrypted field types)
- `payments/models.py` (`OwnerBankDetails` with encrypted fields)
- `payments/migrations/0001_initial.py`
- `notification/models.py` (`NotificationPreference`)
- `notification/migrations/0001_initial.py`
- `payments/views/webhooks.py` (webhook handlers)
- `payments/urls.py` (webhook URLs)
- `core/views/` package (4 view modules)
- Root `management/commands/` removed
- App-level `management/commands/` populated
- `import-linter.ini` v1.1
- `tests/architecture/` package
- `tests/test_migrations.py`

---

## 4. Phase 1: Extract Identity Services

### Purpose

Move identity services (authentication, OTP, password management) out of `core/` into `identity/services/`. The `User` model stays in `core/models.py` permanently. This phase establishes the pattern for all subsequent service extractions.

### Dependencies

- Phase -1 complete (circular dependencies broken)
- Phase 0 complete (critical fixes applied)

### Risk

**Medium** — Service extraction touches authentication flow. Must be thoroughly tested.

### Rollback

Revert Phase 1 PR. `core/services/` files remain. `identity/services/` is removed.

### Tasks

| ID | Task | Files Affected | Effort | Risk |
|----|------|----------------|--------|------|
| 1.1 | Create `identity/services/` package | `identity/services/__init__.py` (new) | 1h | Low |
| 1.2 | Move `AuthService` from `core/services/auth_service.py` to `identity/services/auth_service.py` | `core/services/auth_service.py` → `identity/services/auth_service.py` | 3h | Medium |
| 1.3 | Move `OTPService` from `core/services/otp_service.py` to `identity/services/otp_service.py` | `core/services/otp_service.py` → `identity/services/otp_service.py` | 3h | Medium |
| 1.4 | Move `PasswordService` from `core/services/password_service.py` to `identity/services/password_service.py` | `core/services/password_service.py` → `identity/services/password_service.py` | 3h | Medium |
| 1.5 | Update `core/views/auth_views.py` to import from `identity/services/` | `core/views/auth_views.py` | 2h | Low |
| 1.6 | Update `core/views/password_views.py` to import from `identity/services/` | `core/views/password_views.py` | 2h | Low |
| 1.7 | Update all cross-app imports of `core.services.auth_service`, `core.services.otp_service`, `core.services.password_service` | 5+ files across apps | 4h | Medium |
| 1.8 | Add `identity/services/` unit tests | `identity/tests/unit/test_auth_service.py` (new) | 4h | Low |
| 1.9 | Add `identity/services/` integration tests | `identity/tests/integration/` (new) | 4h | Low |
| 1.10 | Update documentation | `docs/architecture/` | 2h | Low |

### Validation Checklist

- [ ] `identity/services/auth_service.py` exists and passes all tests
- [ ] `identity/services/otp_service.py` exists and passes all tests
- [ ] `identity/services/password_service.py` exists and passes all tests
- [ ] `core/views/auth_views.py` imports from `identity/services/`
- [ ] All cross-app imports updated
- [ ] `import-linter check` passes with 0 violations
- [ ] All existing tests pass
- [ ] No circular dependencies

### Definition of Done

- [ ] All 10 tasks complete
- [ ] `core/services/auth_service.py`, `otp_service.py`, `password_service.py` are deprecated shims or removed
- [ ] All identity service tests pass
- [ ] CI passes on `phase-1-identity-services` branch
- [ ] PR approved by Staff Engineer and Platform Team Lead
- [ ] Merged to `main`

### CI Gates

| Gate | Tool | Threshold | Blocking |
|------|------|-----------|----------|
| Lint | Ruff | 0 errors | Yes |
| Type Check | MyPy | 0 errors | Yes |
| Import Rules | import-linter | 0 violations | Yes |
| Tests | Pytest | All pass, ≥90% coverage | Yes |
| Django Check | `manage.py check` | 0 errors | Yes |
| Architecture | pytest `tests/architecture/` | 0 failures | Yes |

### Architecture Gates

| Gate | Validation |
|------|-----------|
| No `core.services` imports in views | AST scan confirms views import from `identity/services/` |
| No circular dependencies | AST analysis confirms 0 cycles |
| Import boundaries | `import-linter` confirms 0 violations |
| Service ownership | All identity services in `identity/services/` |

### Testing Gates

| Gate | Validation |
|------|-----------|
| Unit tests | ≥90% coverage for `identity/services/` |
| Integration tests | Auth, OTP, password flows work end-to-end |
| Regression tests | All existing auth tests pass |
| No new test failures | CI passes |

### Expected Deliverables

- `identity/services/__init__.py`
- `identity/services/auth_service.py`
- `identity/services/otp_service.py`
- `identity/services/password_service.py`
- `identity/tests/unit/` and `identity/tests/integration/`
- Deprecated `core/services/auth_service.py`, `otp_service.py`, `password_service.py` (shims or removed)

---

## 5. Phase 2: Extract Subscription

### Purpose

Move subscription logic out of `core/` into `subscription/services/`. This includes `SubscriptionService`, `UsageLimitService`, and `FeatureEnforcer`.

### Dependencies

- Phase 1 complete (identity services extracted)

### Risk

**Low** — Subscription logic is well-isolated. `FeatureEnforcer` is already in `properties/feature_enforcer.py`.

### Rollback

Revert Phase 2 PR. `core/services/subscription_service.py` and `usage_limit_service.py` remain. `subscription/services/` is removed.

### Tasks

| ID | Task | Files Affected | Effort | Risk |
|----|------|----------------|--------|------|
| 2.1 | Create `subscription/services/` package | `subscription/services/__init__.py` (new) | 1h | Low |
| 2.2 | Move `SubscriptionService` from `core/services/subscription_service.py` to `subscription/services/subscription_service.py` | `core/services/subscription_service.py` → `subscription/services/subscription_service.py` | 3h | Medium |
| 2.3 | Move `UsageLimitService` from `core/services/usage_limit_service.py` to `subscription/services/usage_limit_service.py` | `core/services/usage_limit_service.py` → `subscription/services/usage_limit_service.py` | 3h | Medium |
| 2.4 | Move `FeatureEnforcer` from `properties/feature_enforcer.py` to `subscription/services/feature_enforcer.py` | `properties/feature_enforcer.py` → `subscription/services/feature_enforcer.py` | 3h | Medium |
| 2.5 | Update `properties/` to import `FeatureEnforcer` from `subscription/services/` | 10+ files in `properties/` | 4h | Medium |
| 2.6 | Update `core/views/subscription_views.py` to import from `subscription/services/` | `core/views/subscription_views.py` | 2h | Low |
| 2.7 | Update all cross-app imports of `core.services.subscription_service` and `core.services.usage_limit_service` | 5+ files across apps | 3h | Medium |
| 2.8 | Add `subscription/services/` unit tests | `subscription/tests/unit/` (new) | 4h | Low |
| 2.9 | Add `subscription/services/` integration tests | `subscription/tests/integration/` (new) | 4h | Low |
| 2.10 | Update documentation | `docs/architecture/` | 2h | Low |

### Validation Checklist

- [ ] `subscription/services/subscription_service.py` exists and passes all tests
- [ ] `subscription/services/usage_limit_service.py` exists and passes all tests
- [ ] `subscription/services/feature_enforcer.py` exists and passes all tests
- [ ] `properties/` imports `FeatureEnforcer` from `subscription/`
- [ ] `core/views/subscription_views.py` imports from `subscription/services/`
- [ ] All cross-app imports updated
- [ ] `import-linter check` passes with 0 violations
- [ ] All existing tests pass

### Definition of Done

- [ ] All 10 tasks complete
- [ ] `core/services/subscription_service.py`, `usage_limit_service.py` are deprecated shims or removed
- [ ] `properties/feature_enforcer.py` is removed
- [ ] All subscription service tests pass
- [ ] CI passes on `phase-2-subscription` branch
- [ ] PR approved by Staff Engineer and Platform Team Lead
- [ ] Merged to `main`

### CI Gates

| Gate | Tool | Threshold | Blocking |
|------|------|-----------|----------|
| Lint | Ruff | 0 errors | Yes |
| Type Check | MyPy | 0 errors | Yes |
| Import Rules | import-linter | 0 violations | Yes |
| Tests | Pytest | All pass, ≥90% coverage | Yes |
| Django Check | `manage.py check` | 0 errors | Yes |
| Architecture | pytest `tests/architecture/` | 0 failures | Yes |

### Architecture Gates

| Gate | Validation |
|------|-----------|
| No `core.services.subscription_service` imports in views | AST scan confirms views import from `subscription/services/` |
| No `properties.feature_enforcer` imports | AST scan confirms imports from `subscription/services/` |
| No circular dependencies | AST analysis confirms 0 cycles |
| Import boundaries | `import-linter` confirms 0 violations |

### Testing Gates

| Gate | Validation |
|------|-----------|
| Unit tests | ≥90% coverage for `subscription/services/` |
| Integration tests | Subscription flows work end-to-end |
| Regression tests | All existing subscription tests pass |
| No new test failures | CI passes |

### Expected Deliverables

- `subscription/services/__init__.py`
- `subscription/services/subscription_service.py`
- `subscription/services/usage_limit_service.py`
- `subscription/services/feature_enforcer.py`
- `subscription/tests/unit/` and `subscription/tests/integration/`
- Deprecated `core/services/subscription_service.py`, `usage_limit_service.py` (shims or removed)
- Removed `properties/feature_enforcer.py`

---

## 6. Phase 3: Extract Payment

### Purpose

Consolidate all payment logic in `payments/`. Move webhook handlers, bank details service, and payment views from `core/` to `payments/`. Remove duplicate services from `rentsecure_be/`.

### Dependencies

- Phase 2 complete (subscription extracted)
- Phase 0 complete (OwnerBankDetails model in `payments/`, webhooks in `payments/`)

### Risk

**Medium** — Payment logic touches financial data. Must preserve audit trail and webhook idempotency.

### Rollback

Revert Phase 3 PR. `core/views/` payment views remain. `rentsecure_be/services/` payment services remain.

### Tasks

| ID | Task | Files Affected | Effort | Risk |
|----|------|----------------|--------|------|
| 3.1 | Create `payments/services/webhook_service.py` | `payments/services/webhook_service.py` (new) | 4h | Medium |
| 3.2 | Create `payments/services/bank_details_service.py` | `payments/services/bank_details_service.py` (new) | 4h | Medium |
| 3.3 | Move `update_owner_bank_details` view from `core/views/bank_views.py` to `payments/views/bank_details_views.py` | `core/views/bank_views.py`, `payments/views/bank_details_views.py` (new) | 4h | Medium |
| 3.4 | Move `cashfree_payout_webhook` and `razorpay_webhook` to `payments/views/webhooks.py` | Already in `payments/views/webhooks.py` from Phase 0 | 2h | Low |
| 3.5 | Remove duplicate `cashfree_service.py`, `razorpay_service.py`, `leegality_service.py` from `rentsecure_be/services/` | `rentsecure_be/services/` (3 files removed) | 3h | Medium |
| 3.6 | Remove `cashfree_payout.py` from `rentsecure_be/utils/` | Already moved in Phase -1 | 0h | Low |
| 3.7 | Remove `export_utils.py` from `rentsecure_be/utils/` (move to `properties/` or `dashboard/`) | `rentsecure_be/utils/export_utils.py` → `properties/utils/` or `dashboard/utils/` | 3h | Medium |
| 3.8 | Update `core/views/bank_views.py` to delegate to `payments/` URLs (deprecated) | `core/views/bank_views.py` | 2h | Low |
| 3.9 | Update `core/urls.py` to include `payments/` URLs as deprecated redirects | `core/urls.py` | 1h | Low |
| 3.10 | Update all cross-app imports of `core.services.bank_details_service` and `rentsecure_be.services.cashfree_service` | 10+ files across apps | 6h | High |
| 3.11 | Add `payments/services/` unit tests | `payments/tests/unit/` (new) | 4h | Low |
| 3.12 | Add `payments/services/` integration tests | `payments/tests/integration/` (new) | 4h | Low |
| 3.13 | Add webhook idempotency tests | `payments/tests/integration/test_webhooks.py` (new) | 3h | Low |
| 3.14 | Update documentation | `docs/architecture/` | 2h | Low |

### Validation Checklist

- [ ] `payments/services/webhook_service.py` exists and passes all tests
- [ ] `payments/services/bank_details_service.py` exists and passes all tests
- [ ] `payments/views/bank_details_views.py` exists and handles bank details updates
- [ ] `payments/views/webhooks.py` handles Cashfree and Razorpay webhooks with idempotency
- [ ] `rentsecure_be/services/cashfree_service.py`, `razorpay_service.py`, `leegality_service.py` are removed
- [ ] All cross-app imports updated
- [ ] `import-linter check` passes with 0 violations
- [ ] All existing tests pass
- [ ] Webhook idempotency tests pass
- [ ] No duplicate payment logic remains

### Definition of Done

- [ ] All 14 tasks complete
- [ ] All payment logic in `payments/`
- [ ] No duplicate payment services in `rentsecure_be/`
- [ ] All payment service tests pass
- [ ] CI passes on `phase-3-payment` branch
- [ ] PR approved by Staff Engineer, Platform Lead, Security Lead
- [ ] Merged to `main`

### CI Gates

| Gate | Tool | Threshold | Blocking |
|------|------|-----------|----------|
| Lint | Ruff | 0 errors | Yes |
| Type Check | MyPy | 0 errors | Yes |
| Import Rules | import-linter | 0 violations | Yes |
| Tests | Pytest | All pass, ≥90% coverage | Yes |
| Django Check | `manage.py check` | 0 errors | Yes |
| Security | Bandit | 0 high/medium | Yes |
| Architecture | pytest `tests/architecture/` | 0 failures | Yes |

### Architecture Gates

| Gate | Validation |
|------|-----------|
| No payment SDK in views | AST scan confirms no `razorpay`, `cashfree` imports in views |
| No duplicate services | `rentsecure_be/services/` contains no payment services |
| Webhook location | All webhook handlers in `payments/views/webhooks.py` |
| No circular dependencies | AST analysis confirms 0 cycles |
| Import boundaries | `import-linter` confirms 0 violations |

### Testing Gates

| Gate | Validation |
|------|-----------|
| Unit tests | ≥90% coverage for `payments/services/` |
| Integration tests | Payment flows work end-to-end |
| Webhook tests | Cashfree and Razorpay webhooks verified with idempotency |
| Regression tests | All existing payment tests pass |
| No new test failures | CI passes |

### Expected Deliverables

- `payments/services/webhook_service.py`
- `payments/services/bank_details_service.py`
- `payments/views/bank_details_views.py`
- `payments/tests/unit/` and `payments/tests/integration/`
- Removed `rentsecure_be/services/cashfree_service.py`, `razorpay_service.py`, `leegality_service.py`
- Removed `rentsecure_be/utils/cashfree_payout.py`, `export_utils.py`

---

## 7. Phase 4: Extract Dashboard & Notification

### Purpose

Move reporting out of `core/` into `dashboard/`. Isolate notification concerns by moving domain-specific notification triggers from `notification/services/` to `properties/services/`. Simplify `notification/` to only channel adapters.

### Dependencies

- Phase 3 complete (payment extracted)

### Risk

**Low** — Dashboard and notification refactoring is additive. Old code remains as deprecated shims.

### Rollback

Revert Phase 4 PR. `core/views/reporting_views.py` remains. `notification/services/` domain logic remains.

### Tasks

| ID | Task | Files Affected | Effort | Risk |
|----|------|----------------|--------|------|
| 4.1 | Create `dashboard/services/` package | `dashboard/services/__init__.py` (new) | 1h | Low |
| 4.2 | Move `OwnerReportingService` from `core/services/owner_reporting_service.py` to `dashboard/services/owner_reporting_service.py` | `core/services/owner_reporting_service.py` → `dashboard/services/owner_reporting_service.py` | 4h | Medium |
| 4.3 | Create `dashboard/views/` package | `dashboard/views/__init__.py` (new) | 1h | Low |
| 4.4 | Move reporting views from `core/views/reporting_views.py` to `dashboard/views/` | `core/views/reporting_views.py` → `dashboard/views/` (3 files) | 4h | Medium |
| 4.5 | Update `core/views/reporting_views.py` to delegate to `dashboard/` URLs (deprecated) | `core/views/reporting_views.py` | 2h | Low |
| 4.6 | Update `core/urls.py` to include `dashboard/` URLs as deprecated redirects | `core/urls.py` | 1h | Low |
| 4.7 | Move `generate_owner_rent_report` from `rentsecure_be/utils/` to `dashboard/utils/` | `rentsecure_be/utils/export_utils.py` → `dashboard/utils/` | 2h | Low |
| 4.8 | Move domain notification triggers from `notification/services/` to `properties/services/` | 6 files moved/refactored | 8h | High |
| 4.9 | Simplify `notification/services/notification_dispatcher.py` to only channel adapters | `notification/services/notification_dispatcher.py` | 4h | Medium |
| 4.10 | Update all cross-app imports of `core.services.owner_reporting_service` | 5+ files across apps | 4h | Medium |
| 4.11 | Add `dashboard/services/` and `dashboard/views/` tests | `dashboard/tests/` (new) | 4h | Low |
| 4.12 | Add `notification/` simplified adapter tests | `notification/tests/` (updated) | 3h | Low |
| 4.13 | Update documentation | `docs/architecture/` | 2h | Low |

### Validation Checklist

- [ ] `dashboard/services/owner_reporting_service.py` exists and passes all tests
- [ ] `dashboard/views/` package exists and handles reporting endpoints
- [ ] `notification/services/` contains only channel adapters (no domain logic)
- [ ] Domain notification triggers in `properties/services/`
- [ ] Old reporting URLs redirect to `dashboard/` URLs
- [ ] All cross-app imports updated
- [ ] `import-linter check` passes with 0 violations
- [ ] All existing tests pass

### Definition of Done

- [ ] All 13 tasks complete
- [ ] `dashboard/` is fully functional
- [ ] `notification/` is simplified to adapters only
- [ ] All tests pass
- [ ] CI passes on `phase-4-dashboard-notification` branch
- [ ] PR approved by Staff Engineer, Platform Lead, Product Lead
- [ ] Merged to `main`

### CI Gates

| Gate | Tool | Threshold | Blocking |
|------|------|-----------|----------|
| Lint | Ruff | 0 errors | Yes |
| Type Check | MyPy | 0 errors | Yes |
| Import Rules | import-linter | 0 violations | Yes |
| Tests | Pytest | All pass, ≥90% coverage | Yes |
| Django Check | `manage.py check` | 0 errors | Yes |
| Architecture | pytest `tests/architecture/` | 0 failures | Yes |

### Architecture Gates

| Gate | Validation |
|------|-----------|
| No domain logic in `notification/services/` | AST scan confirms no `RentRecord`, `PropertyTaxRecord`, `ExtraCharge` imports in `notification/services/` |
| Reporting in `dashboard/` | All reporting views in `dashboard/views/` |
| No circular dependencies | AST analysis confirms 0 cycles |
| Import boundaries | `import-linter` confirms 0 violations |

### Testing Gates

| Gate | Validation |
|------|-----------|
| Unit tests | ≥90% coverage for `dashboard/` and `notification/` |
| Integration tests | Reporting and notification flows work end-to-end |
| Regression tests | All existing tests pass |
| No new test failures | CI passes |

### Expected Deliverables

- `dashboard/services/owner_reporting_service.py`
- `dashboard/views/` package
- `dashboard/utils/` (report generation)
- `properties/services/` (domain notification triggers)
- Simplified `notification/services/notification_dispatcher.py`
- `dashboard/tests/` package
- Deprecated `core/services/owner_reporting_service.py`, `core/views/reporting_views.py` (shims or removed)

---

## 8. Phase 5: Deprecate Core

### Purpose

Remove `core/` as a God app. `core/` retains only `User`, `UserProfile`, and `OTP` models. All views, services, and other models have been moved to their owning apps. This is the **only breaking change** in the entire migration.

### Dependencies

- Phase 4 complete (dashboard and notification extracted)

### Risk

**High** — Breaking change. Requires major version release. All old `core/` URLs and imports become invalid.

### Rollback

Rollback is **not automatic**. Requires:
1. Revert Phase 5 PR
2. Restore `core/` from `main` branch before Phase 5 merge
3. Redeploy previous version
4. Estimated rollback time: 2-4 hours

### Tasks

| ID | Task | Files Affected | Effort | Risk |
|----|------|----------------|--------|------|
| 5.1 | Remove all views from `core/views/` | `core/views/` (all files removed) | 2h | High |
| 5.2 | Remove `OwnerBankDetails` from `core/models.py` | Already moved to `payments/models.py` in Phase 0 | 0h | Low |
| 5.3 | Remove `NotificationPreference` from `core/models.py` | Already moved to `notification/models.py` in Phase 0 | 0h | Low |
| 5.4 | Remove subscription models from `core/models.py` | `core/models.py` (SubscriptionPlan, UserSubscription, AddOnPurchase, PlanFeatureLimit, UsageLimit removed) | 2h | High |
| 5.5 | Create data migration to delete `core_*` subscription tables | `core/migrations/XXXX_delete_subscription_tables.py` | 3h | High |
| 5.6 | Remove `core/services/` (all remaining services) | `core/services/` (all files removed) | 2h | High |
| 5.7 | Remove `core/serializers.py` | `core/serializers.py` (removed) | 1h | Low |
| 5.8 | Remove `core/urls.py` | `core/urls.py` (removed) | 1h | High |
| 5.9 | Update `rentsecure_be/urls.py` to remove `core/` URL includes | `rentsecure_be/urls.py` | 1h | High |
| 5.10 | Update `INSTALLED_APPS` if `core` is removed | `rentsecure_be/settings.py` | 1h | High |
| 5.11 | Add deprecation warnings to any remaining `core/` imports | 5+ files | 3h | Medium |
| 5.12 | Create migration guide for external consumers | `docs/migration/v1-to-v2.md` (new) | 4h | Medium |
| 5.13 | Update all documentation | `docs/architecture/`, `README.md` | 4h | Medium |
| 5.14 | Add ADR for Phase 5 breaking changes | `docs/architecture/adr/ADR-XXX-phase5.md` (new) | 2h | Low |

### Validation Checklist

- [ ] `core/models.py` contains only `User`, `UserProfile`, `OTP`
- [ ] `core/views/` is empty or removed
- [ ] `core/services/` is empty or removed
- [ ] `core/urls.py` is removed
- [ ] `rentsecure_be/urls.py` does not include `core/urls.py`
- [ ] `import-linter check` passes with 0 violations
- [ ] No circular dependencies
- [ ] All tests pass
- [ ] Migration guide published

### Definition of Done

- [ ] All 14 tasks complete
- [ ] `core/` is a minimal identity app (models only)
- [ ] All old `core/` URLs return 404 (not 500)
- [ ] Migration guide published
- [ ] CI passes on `phase-5-deprecate-core` branch
- [ ] PR approved by Staff Engineer (2-of-3 board)
- [ ] Merged to `main`
- [ ] **Released as v2.0.0**

### CI Gates

| Gate | Tool | Threshold | Blocking |
|------|------|-----------|----------|
| Lint | Ruff | 0 errors | Yes |
| Type Check | MyPy | 0 errors | Yes |
| Import Rules | import-linter | 0 violations | Yes |
| Tests | Pytest | All pass, ≥90% coverage | Yes |
| Django Check | `manage.py check` | 0 errors | Yes |
| Security | Bandit | 0 high/medium | Yes |
| Architecture | pytest `tests/architecture/` | 0 failures | Yes |

### Architecture Gates

| Gate | Validation |
|------|-----------|
| `core/` minimal | `core/models.py` contains only `User`, `UserProfile`, `OTP` |
| No `core/` URLs | `rentsecure_be/urls.py` does not include `core/urls.py` |
| No circular dependencies | AST analysis confirms 0 cycles |
| Import boundaries | `import-linter` confirms 0 violations |

### Testing Gates

| Gate | Validation |
|------|-----------|
| Unit tests | ≥90% coverage for remaining `core/` code |
| Integration tests | Identity flows work end-to-end |
| Regression tests | All existing tests pass |
| Breaking change tests | Verify old `core/` URLs return 404 |
| No new test failures | CI passes |

### Expected Deliverables

- Minimal `core/` app (models only: `User`, `UserProfile`, `OTP`)
- Removed `core/views/`, `core/services/`, `core/serializers.py`, `core/urls.py`
- `docs/migration/v1-to-v2.md` (migration guide)
- ADR for Phase 5 breaking changes
- **Release v2.0.0**

---

## 9. Phase 6: Optimization

### Purpose

Add missing infrastructure: event bus, repositories for complex queries, Redis cache backend, and consolidate `ai_assistant/` and `smartbot/`.

### Dependencies

- Phase 5 complete (core deprecated)

### Risk

**Low** — All changes are additive. No breaking changes.

### Rollback

Revert individual PRs. No data changes.

### Tasks

| ID | Task | Files Affected | Effort | Risk |
|----|------|----------------|--------|------|
| 6.1 | Implement `InProcessEventBus` in `platform/events/` | `platform/events/event_bus.py` (new) | 6h | Medium |
| 6.2 | Implement event middleware (logging, retry) | `platform/events/middleware.py` (new) | 4h | Medium |
| 6.3 | Define domain events for all contexts | `shared/domain_events.py`, `*/events.py` (new) | 6h | Low |
| 6.4 | Integrate event bus with services | 10+ service files | 8h | Medium |
| 6.5 | Add repositories for complex queries | `properties/repositories/`, `dashboard/repositories/` | 8h | Medium |
| 6.6 | Add `RedisCache` backend to `platform/cache/` | `platform/cache/redis.py` (new) | 4h | Low |
| 6.7 | Add `CACHE_BACKEND` setting | `rentsecure_be/settings/base.py` | 1h | Low |
| 6.8 | Consolidate `ai_assistant/` and `smartbot/` or remove dead code | `ai_assistant/`, `smartbot/` | 8h | High |
| 6.9 | Document bounded context APIs | `docs/architecture/contexts/` (new) | 6h | Low |
| 6.10 | Add performance benchmarks | `tests/performance/` (new) | 4h | Low |

### Validation Checklist

- [ ] `platform/events/event_bus.py` exists and passes tests
- [ ] Domain events defined for all contexts
- [ ] Event bus integrated with services
- [ ] Repositories implemented for complex queries
- [ ] `RedisCache` backend available
- [ ] `ai_assistant/` and `smartbot/` consolidated or removed
- [ ] Bounded context APIs documented
- [ ] Performance benchmarks established
- [ ] `import-linter check` passes with 0 violations
- [ ] All tests pass

### Definition of Done

- [ ] All 10 tasks complete
- [ ] Event bus functional
- [ ] Repositories used for complex queries
- [ ] Redis cache backend available
- [ ] `ai_assistant/` and `smartbot/` resolved
- [ ] CI passes on `phase-6-optimization` branch
- [ ] PR approved by Staff Engineer
- [ ] Merged to `main`

### CI Gates

| Gate | Tool | Threshold | Blocking |
|------|------|-----------|----------|
| Lint | Ruff | 0 errors | Yes |
| Type Check | MyPy | 0 errors | Yes |
| Import Rules | import-linter | 0 violations | Yes |
| Tests | Pytest | All pass, ≥90% coverage | Yes |
| Performance | Locust | < 200ms p95 | No |
| Architecture | pytest `tests/architecture/` | 0 failures | Yes |

### Architecture Gates

| Gate | Validation |
|------|-----------|
| Event bus | `platform/events/` implements `EventBus` protocol |
| Repositories | Complex queries use repositories, simple queries use ORM |
| Cache | `RedisCache` backend available via setting |
| No circular dependencies | AST analysis confirms 0 cycles |
| Import boundaries | `import-linter` confirms 0 violations |

### Testing Gates

| Gate | Validation |
|------|-----------|
| Unit tests | ≥90% coverage |
| Integration tests | ≥80% coverage |
| Event bus tests | Events published and received correctly |
| Performance tests | Query counts within limits, response times < 200ms p95 |
| No new test failures | CI passes |

### Expected Deliverables

- `platform/events/event_bus.py`
- `platform/events/middleware.py`
- `platform/cache/redis.py`
- `shared/domain_events.py` (updated)
- `properties/repositories/`, `dashboard/repositories/`
- `tests/performance/`
- `docs/architecture/contexts/` (API documentation)
- Resolved `ai_assistant/` and `smartbot/`

---

## 10. Git Branch Strategy

### 10.1 Branch Naming Convention

| Branch Type | Naming Pattern | Purpose |
|-------------|----------------|---------|
| **Main** | `main` | Production-ready code |
| **Phase branch** | `phase-{N}-{name}` | Long-lived branch for each phase |
| **Task branch** | `phase-{N}-{name}/{task-id}-{description}` | Short-lived branch for each task |
| **Hotfix** | `hotfix-{description}` | Production fixes |
| **Release** | `release/v{N}.{M}.{Z}` | Release preparation |

### 10.2 Branch Hierarchy

```
main (protected)
├── phase--1-break-cycles
│   ├── -1.1-move-type-compat
│   ├── -1.2-add-payments-to-installed-apps
│   └── ...
├── phase-0-foundation
│   ├── 0.1-add-encrypted-fields
│   ├── 0.2-create-payments-models
│   └── ...
├── phase-1-identity-services
│   ├── 1.1-create-identity-services-package
│   ├── 1.2-move-auth-service
│   └── ...
├── phase-2-subscription
│   ├── 2.1-create-subscription-services
│   ├── 2.2-move-subscription-service
│   └── ...
├── phase-3-payment
│   ├── 3.1-create-webhook-service
│   ├── 3.2-create-bank-details-service
│   └── ...
├── phase-4-dashboard-notification
│   ├── 4.1-create-dashboard-services
│   ├── 4.2-move-reporting-views
│   └── ...
├── phase-5-deprecate-core
│   ├── 5.1-remove-core-views
│   ├── 5.2-remove-core-models
│   └── ...
└── phase-6-optimization
    ├── 6.1-implement-event-bus
    ├── 6.2-add-repositories
    └── ...
```

### 10.3 Branch Protection Rules

| Rule | main | phase branches | task branches |
|------|------|----------------|---------------|
| Require PR | Yes | Yes | Yes |
| Require approvals | 2 | 1 | 0 |
| Require status checks | All | All | Lint + Tests |
| Dismiss stale reviews | Yes | Yes | No |
| Enforce admins | Yes | Yes | No |
| Allow force push | No | No | Yes |

### 10.4 PR Size Limits

| Metric | Limit |
|--------|-------|
| Lines changed per PR | Max 400 |
| Files changed per PR | Max 15 |
| PR lifetime | Max 7 days |

If a task exceeds these limits, split it into smaller PRs.

---

## 11. CI/CD Pipeline

### 11.1 Pipeline Stages

```
┌─────────────┐
│   Lint      │ Ruff, MyPy, import-linter
└──────┬──────┘
       │
┌──────▼──────┐
│   Test      │ Unit + Integration (4 shards)
└──────┬──────┘
       │
┌──────▼──────┐
│  Shard Val  │ Validate test distribution
└──────┬──────┘
       │
┌──────▼──────┐
│  Contract   │ API contract tests
└──────┬──────┘
       │
┌──────▼──────┐
│ Django Check│ System checks + migrations
└──────┬──────┘
       │
┌──────▼──────┐
│ Architecture│ AST-based architecture tests
└──────┬──────┘
       │
┌──────▼──────┐
│   Security  │ Bandit + Safety + dependency audit
└──────┬──────┘
       │
┌──────▼──────┐
│  Mutation   │ SonarCloud mutation testing
└──────┬──────┘
       │
┌──────▼──────┐
│  Hypothesis │ Property-based testing
└──────┬──────┘
       │
┌──────▼──────┐
│ Migration   │ Forward + reverse migration tests
└──────┬──────┘
       │
┌──────▼──────┐
│ Quality Gate│ Coverage, mutation score thresholds
└──────┬──────┘
       │
┌──────▼──────┐
│ Deploy Ready│ Pre-deployment validation
└──────┬──────┘
       │
┌──────▼──────┐
│   Deploy    │ Deploy to staging/production
└─────────────┘
```

### 11.2 CI Gates by Phase

| Phase | Additional Gates |
|-------|------------------|
| Phase -1 | Circular dependency check, `rentsecure_be/` boundary check |
| Phase 0 | Migration forward/reverse tests, encrypted field verification, webhook idempotency tests |
| Phase 1 | Service ownership tests, identity flow regression |
| Phase 2 | Subscription flow regression, `FeatureEnforcer` import check |
| Phase 3 | Webhook security tests, payment flow regression, duplicate service removal check |
| Phase 4 | Dashboard API tests, notification adapter tests |
| Phase 5 | Breaking change tests, 404 validation for old URLs, migration guide validation |
| Phase 6 | Performance benchmarks, event bus tests, repository tests |

### 11.3 Deployment Pipeline

| Environment | Trigger | Approval Required |
|-------------|---------|-------------------|
| **Development** | Every push to task branch | None |
| **Staging** | PR merged to `phase-{N}` branch | 1 approval |
| **Production** | PR merged from `phase-{N}` to `main` | 2 approvals, Security Lead sign-off |

### 11.4 Deployment Strategy

| Phase | Strategy |
|-------|----------|
| Phase -1 | Deploy to staging only. No production deploy. |
| Phase 0 | Blue-green deploy to staging. Production deploy after 3 days stable. |
| Phase 1-4 | Rolling deploy. Old code remains as deprecated shims. |
| Phase 5 | Blue-green deploy. Major version release (v2.0.0). |
| Phase 6 | Rolling deploy. |

---

## 12. Rollback Strategies

### 12.1 Rollback Decision Matrix

| Scenario | Action | Time to Rollback |
|----------|--------|------------------|
| CI fails after merge | Revert merge commit | 5 minutes |
| Staging test failure | Revert PR, fix, resubmit | 30 minutes |
| Production incident (Phase -1 to 4) | Revert to previous stable tag | 15-30 minutes |
| Production incident (Phase 5) | Blue-green switch to previous version | 2-4 hours |
| Data corruption | Restore from backup + revert code | 1-4 hours |

### 12.2 Rollback by Phase

| Phase | Rollback Method | Data Risk | Time Estimate |
|-------|-----------------|-----------|---------------|
| Phase -1 | `git revert` Phase -1 PR | None (no data changes) | 10 minutes |
| Phase 0 | `git revert` Phase 0 PR + `manage.py migrate --reverse` | Low (data migrations are additive) | 30 minutes |
| Phase 1 | `git revert` Phase 1 PR | None (services only) | 15 minutes |
| Phase 2 | `git revert` Phase 2 PR | None (services only) | 15 minutes |
| Phase 3 | `git revert` Phase 3 PR | Medium (payment views moved) | 30 minutes |
| Phase 4 | `git revert` Phase 4 PR | Low (additive changes) | 20 minutes |
| Phase 5 | Restore from backup + deploy previous version | **High** (breaking changes) | 2-4 hours |
| Phase 6 | `git revert` individual PRs | None (additive changes) | 15 minutes per PR |

### 12.3 Rollback Runbook

For each phase, the rollback runbook must include:

1. **Pre-rollback checklist**
   - [ ] Identify failing commit/PR
   - [ ] Notify team of rollback decision
   - [ ] Backup current database state

2. **Rollback steps**
   - [ ] `git revert {commit-sha}` or `git checkout {previous-tag}`
   - [ ] `python manage.py migrate --reverse` (if needed)
   - [ ] Deploy reverted code
   - [ ] Run smoke tests
   - [ ] Verify production health

3. **Post-rollback checklist**
   - [ ] Verify all services healthy
   - [ ] Notify team of rollback completion
   - [ ] Document root cause
   - [ ] Create fix plan

### 12.4 Rollback Testing

| Phase | Rollback Test Requirement |
|-------|---------------------------|
| Phase -1 | Dry-run revert on test environment |
| Phase 0 | Test `migrate --reverse` on test database |
| Phase 1-4 | Test revert on staging environment |
| Phase 5 | Full disaster recovery drill (backup restore + deploy) |
| Phase 6 | Test revert of individual PRs |

---

## 13. Testing Strategy

### 13.1 Test Pyramid

```
        /\
       /  \      E2E (Playwright)
      /____\
     /      \    Integration (pytest + Django test client)
    /________\
   /          \  Unit (pytest + mocks)
  /____________\
```

### 13.2 Test Ownership

| Test Type | Written By | Run Frequency | Blocking |
|-----------|-----------|---------------|----------|
| **Unit** | App team | Every commit | Yes |
| **Integration** | App team | Every commit | Yes |
| **Contract** | Architecture team | Every PR | Yes |
| **Architecture** | Architecture team | Every commit | Yes |
| **Migration** | App team | Every PR | Yes |
| **Security** | Security team | Every release | Yes |
| **Performance** | App team | Nightly | No |

### 13.3 Test Requirements by Phase

| Phase | New Tests Required |
|-------|-------------------|
| Phase -1 | Import boundary tests, circular dependency tests |
| Phase 0 | Data migration tests, webhook idempotency tests, rollback tests |
| Phase 1 | Identity service unit + integration tests |
| Phase 2 | Subscription service unit + integration tests |
| Phase 3 | Payment service unit + integration tests, webhook security tests |
| Phase 4 | Dashboard service tests, notification adapter tests |
| Phase 5 | Breaking change tests, 404 validation tests |
| Phase 6 | Event bus tests, repository tests, performance benchmarks |

### 13.4 Test Coverage Requirements

| Metric | Requirement |
|--------|-------------|
| Unit test coverage | ≥90% |
| Integration test coverage | ≥80% |
| Architecture test pass rate | 100% |
| Mutation testing score | ≥80% (blocking) |
| Performance p95 | < 200ms |

---

## 14. Architecture Validation

### 14.1 Architecture Tests

All architecture tests run on every commit via CI.

| Test | Description | Tool |
|------|-------------|------|
| **Import Linter** | Enforce allowed import matrix | `import-linter` |
| **Circular Dependencies** | Detect circular import cycles | Custom AST pytest |
| **Layer Compliance** | Views do not import models from other apps | Custom AST pytest |
| **SDK Placement** | Payment SDKs only in adapter modules | Custom AST pytest |
| **God View Detection** | No view file exceeds 300 lines | Custom pytest |
| **God Model Detection** | No model file exceeds 400 lines | Custom pytest |
| **Dead Code Detection** | No unused imports or modules | `vulture` |
| **Shared Purity** | `shared/` does not import Django or apps | Custom AST pytest |

### 14.2 Architecture Test Examples

```python
# tests/architecture/test_import_rules.py

def test_no_views_import_payment_adapters():
    """Views must not import payment SDKs directly."""
    for view_file in glob("core/views/*.py") + glob("properties/views/*.py"):
        content = read(view_file)
        assert "razorpay" not in content
        assert "cashfree" not in content
        assert "CashfreeAdapter" not in content
        assert "RazorpayAdapter" not in content

def test_no_rentsecure_be_imports():
    """No app may import from rentsecure_be/ (except rentsecure_be/ itself)."""
    for app in ["core", "properties", "notification", "smartbot", "finance", "documents"]:
        for file in glob(f"{app}/**/*.py"):
            content = read(file)
            assert "rentsecure_be" not in content, f"{file} imports from rentsecure_be"

def test_no_notification_imports_property_models():
    """notification/ must not import property models directly."""
    for file in glob("notification/services/*.py"):
        content = read(file)
        assert "RentRecord" not in content
        assert "PropertyTaxRecord" not in content
        assert "ExtraCharge" not in content
```

### 14.3 Architecture Gates by Phase

| Phase | Gate | Validation Method |
|-------|------|-------------------|
| Phase -1 | No circular dependencies | AST analysis |
| Phase -1 | No `rentsecure_be/` imports | AST scan |
| Phase 0 | `payments/` in `INSTALLED_APPS` | `manage.py check` |
| Phase 0 | Encrypted fields used | AST scan |
| Phase 0 | Webhooks in `payments/` | AST scan |
| Phase 1 | Identity services in `identity/` | AST scan |
| Phase 2 | Subscription services in `subscription/` | AST scan |
| Phase 3 | Payment services in `payments/` | AST scan |
| Phase 3 | No duplicate services in `rentsecure_be/` | AST scan |
| Phase 4 | Dashboard views in `dashboard/` | AST scan |
| Phase 4 | No domain logic in `notification/services/` | AST scan |
| Phase 5 | `core/` minimal | AST scan |
| Phase 6 | Event bus in `platform/events/` | AST scan |

---

## 15. Database Migrations

### 15.1 Migration Strategy

| Principle | Description |
|-----------|-------------|
| **Additive first** | New tables/columns added before old ones removed |
| **Backward-compatible** | Old and new schema coexist during transition |
| **Zero downtime** | Migrations run in < 30 seconds on production |
| **Reversible** | Every migration has a reverse operation |
| **Tested** | Every migration tested forward and backward in CI |

### 15.2 Migration Phases

| Phase | Migration | Tables Affected | Risk |
|-------|-----------|-----------------|------|
| Phase -1 | Add `payments` app | None (empty initial) | Low |
| Phase 0 | Move `OwnerBankDetails` to `payments` | `core_ownerbankdetails` → `payment_ownerbankdetails` | Medium |
| Phase 0 | Move `NotificationPreference` to `notification` | `core_notificationpreference` → `notification_notificationpreference` | Medium |
| Phase 2 | Move subscription tables to `subscription` | `core_subscription*` → `subscription_*` | Medium |
| Phase 5 | Remove `core` subscription tables | Drop `core_*` tables | High |
| Phase 6 | Add event bus tables | `domain_events` (new) | Low |

### 15.3 Data Migration Requirements

| Migration | Source | Target | Rollback |
|-----------|--------|--------|----------|
| Bank details | `core_ownerbankdetails` | `payment_ownerbankdetails` | Keep `core_ownerbankdetails` for 1 release cycle |
| Notification preferences | `core_notificationpreference` | `notification_notificationpreference` | Keep `core_notificationpreference` for 1 release cycle |
| Subscription models | `core_subscriptionplan`, `core_usersubscription`, `core_addonpurchase`, `core_planfeaturelimit`, `core_usagelimit` | `subscription_*` | Keep `core_*` for 1 release cycle |

### 15.4 Migration Testing

| Test | Frequency | Tool |
|------|-----------|------|
| Forward migration | Every PR touching migrations | `manage.py migrate` |
| Reverse migration | Every PR touching migrations | `manage.py migrate --reverse` |
| Data integrity | Every PR with data migrations | Custom pytest |
| Migration on production copy | Weekly | Staging environment |

---

## 16. API Compatibility

### 16.1 Compatibility Promise

| Phase | Compatibility |
|-------|---------------|
| Phase -1 | 100% backward-compatible |
| Phase 0 | 100% backward-compatible (additive only) |
| Phase 1 | 100% backward-compatible (internal refactor) |
| Phase 2 | 100% backward-compatible (internal refactor) |
| Phase 3 | 100% backward-compatible (old URLs redirect) |
| Phase 4 | 100% backward-compatible (old URLs redirect) |
| Phase 5 | **BREAKING** — v2.0.0 release |
| Phase 6 | 100% backward-compatible |

### 16.2 Backward Compatibility Mechanisms

| Mechanism | Description |
|-----------|-------------|
| **URL redirects** | Old `core/` URLs return 301/302 to new URLs during transition |
| **Deprecated shims** | Old `core/services/` files re-export from new locations |
| **API versioning** | Not required until Stage 2 (microservice extraction) |
| **Feature flags** | Not used for architectural changes (only for feature toggles) |

### 16.3 Breaking Changes (Phase 5 Only)

| Breaking Change | Impact | Mitigation |
|-----------------|--------|------------|
| `core/` URLs removed | Clients using old URLs get 404 | Migration guide, redirects in v1.x LTS |
| `core.services.*` removed | Internal imports break | Internal code updated during Phase 1-4 |
| `AUTH_USER_MODEL` unchanged | No impact | Kept as `core.User` |

### 16.4 API Compatibility Tests

| Test | Description |
|------|-------------|
| **URL contract tests** | All public API endpoints return expected status codes |
| **Response schema tests** | JSON response schemas unchanged |
| **Deprecation warning tests** | Old URLs return `Deprecation` header |
| **404 validation tests** | Removed URLs return 404 (Phase 5) |

---

## 17. Deprecation Plans

### 17.1 Deprecation Policy

| Element | Deprecation Period | Removal Phase |
|---------|-------------------|---------------|
| `core/views/` URLs | 3 phases (Phase 1-4) | Phase 5 |
| `core/services/` imports | 3 phases (Phase 1-4) | Phase 5 |
| `rentsecure_be/services/` payment services | Phase 0-3 | Phase 3 |
| `rentsecure_be/utils/` utilities | Phase 0-3 | Phase 3 |
| `properties/feature_enforcer.py` | Phase 2 | Phase 2 end |
| `core/models.py` non-identity models | Phase 0-4 | Phase 5 |

### 17.2 Deprecation Warnings

All deprecated code must emit warnings:

```python
import warnings

def old_function():
    warnings.warn(
        "old_function is deprecated. Use new_function instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return new_function()
```

### 17.3 Deprecation Tracking

| Deprecated Element | Introduced | Deprecated | Removal | Replacement |
|--------------------|------------|------------|---------|-------------|
| `core/views/auth_views.py` | v1.0 | Phase 1 | Phase 5 | `identity/views/auth_views.py` |
| `core/views/subscription_views.py` | v1.0 | Phase 2 | Phase 5 | `subscription/views/` |
| `core/views/bank_views.py` | v1.0 | Phase 3 | Phase 5 | `payments/views/bank_details_views.py` |
| `core/views/reporting_views.py` | v1.0 | Phase 4 | Phase 5 | `dashboard/views/` |
| `core/services/auth_service.py` | v1.0 | Phase 1 | Phase 5 | `identity/services/auth_service.py` |
| `core/services/subscription_service.py` | v1.0 | Phase 2 | Phase 5 | `subscription/services/subscription_service.py` |
| `core/services/bank_details_service.py` | v1.0 | Phase 3 | Phase 5 | `payments/services/bank_details_service.py` |
| `core/services/owner_reporting_service.py` | v1.0 | Phase 4 | Phase 5 | `dashboard/services/owner_reporting_service.py` |
| `rentsecure_be/services/cashfree_service.py` | v1.0 | Phase 0 | Phase 3 | `payments/adapters/cashfree.py` |
| `rentsecure_be/services/razorpay_service.py` | v1.0 | Phase 0 | Phase 3 | `payments/adapters/razorpay.py` |
| `properties/feature_enforcer.py` | v1.0 | Phase 2 | Phase 2 | `subscription/services/feature_enforcer.py` |

---

## 18. Release Plans

### 18.1 Release Schedule

| Release | Version | Phase | Content | Date |
|---------|---------|-------|---------|------|
| v1.x LTS | v1.99.x | Phase -1 to 4 | Backward-compatible changes only | Week 1-14 |
| **v2.0.0** | **v2.0.0** | **Phase 5** | **Breaking changes — core deprecated** | **Week 16** |
| v2.1.x | v2.1.x | Phase 6 | Optimization, event bus, repositories | Week 17-20 |

### 18.2 v1.x LTS Strategy

During Phase -1 through Phase 4, all changes are backward-compatible. The v1.x branch receives:

- Phase -1: Bug fixes only
- Phase 0-4: Architectural refactors (additive)
- Security patches
- Critical bug fixes

**v1.x LTS ends** 6 months after v2.0.0 release.

### 18.3 v2.0.0 Release Plan

| Step | Action | Owner | Time |
|------|--------|-------|------|
| 1 | Freeze v1.x LTS branch | DevOps | Week 15 |
| 2 | Merge Phase 5 to `main` | Staff Engineer | Week 16 |
| 3 | Run full regression suite | QA Lead | Week 16 |
| 4 | Deploy to staging | DevOps | Week 16 |
| 5 | Staging validation (3 days) | QA Lead | Week 16-17 |
| 6 | Security audit | Security Lead | Week 17 |
| 7 | Deploy to production (blue-green) | DevOps | Week 17 |
| 8 | Monitor for 48 hours | DevOps + Platform Lead | Week 17 |
| 9 | Tag v2.0.0 | DevOps | Week 17 |
| 10 | Publish release notes | Staff Engineer | Week 17 |

### 18.4 Release Criteria

| Criterion | Requirement |
|-----------|-------------|
| CI green | All pipelines pass |
| Test coverage | ≥90% unit, ≥80% integration |
| Architecture tests | 100% pass |
| Security scan | 0 high/medium vulnerabilities |
| Migration tests | Forward + reverse pass |
| Staging validation | 3 days stable |
| Rollback tested | Disaster recovery drill passed |

---

## 19. Documentation Updates

### 19.1 Documentation Ownership

| Document | Owner | Update Frequency |
|----------|-------|-----------------|
| `ARCHITECTURE_V1.1.md` | Staff Engineer | After each phase |
| `ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md` | Staff Engineer | After each phase |
| `docs/architecture/contexts/` | App owners | After each phase |
| `docs/api/` | App owners | After each phase |
| `docs/deployment/` | DevOps | After each phase |
| `README.md` | Staff Engineer | After each phase |
| `CHANGELOG.md` | DevOps | Every release |
| `docs/migration/v1-to-v2.md` | Staff Engineer | Before v2.0.0 |

### 19.2 Documentation Requirements by Phase

| Phase | Documents to Update |
|-------|---------------------|
| Phase -1 | `docs/architecture/dependencies.md` |
| Phase 0 | `docs/architecture/security.md`, `docs/architecture/payment.md` |
| Phase 1 | `docs/architecture/contexts/identity.md` |
| Phase 2 | `docs/architecture/contexts/subscription.md` |
| Phase 3 | `docs/architecture/contexts/payment.md`, `docs/architecture/security.md` |
| Phase 4 | `docs/architecture/contexts/dashboard.md`, `docs/architecture/contexts/notification.md` |
| Phase 5 | `docs/migration/v1-to-v2.md`, `CHANGELOG.md` |
| Phase 6 | `docs/architecture/contexts/*.md`, `docs/operations/runbook.md` |

### 19.3 Documentation Standards

| Standard | Requirement |
|----------|-------------|
| **Format** | Markdown |
| **Location** | `docs/` directory |
| **Review** | Every document requires PR review |
| **Links** | All internal links validated by Documentation Guardian |
| **Versioning** | Documents versioned with code releases |

---

## 20. ADR Updates

### 20.1 ADR Lifecycle

| Status | Description | Approval |
|--------|-------------|----------|
| **Proposed** | Created as PR | None |
| **Accepted** | Approved by 2-of-3 board | Staff Engineer + relevant Lead |
| **Deprecated** | Superseded by new ADR | Staff Engineer |
| **Archived** | Moved to `docs/architecture/adr/archive/` | Staff Engineer |

### 20.2 ADRs to Create/Update During Implementation

| ADR | Title | Status | Phase |
|-----|-------|--------|-------|
| ADR-001 | Modular Monolith Architecture | Accepted | Phase -1 |
| ADR-002 | Simplified Clean Architecture | Accepted | Phase -1 |
| ADR-003 | User Model in Core (Permanent) | **New** — supersedes v1.0 ADR-003 | Phase -1 |
| ADR-004 | Django Signals for In-Process Events | Accepted | Phase -1 |
| ADR-005 | Selective Repository Pattern | Accepted | Phase 6 |
| ADR-006 | No CQRS in Year 1 | Accepted | Phase -1 |
| ADR-007 | Platform Layer Minimalism | Accepted | Phase -1 |
| ADR-008 | Incremental Migration Strategy | **Updated** — v1.1 phases | Phase -1 |
| ADR-009 | No `apps/` Parent Directory | **New** | Phase -1 |
| ADR-010 | No `rent/` Bounded Context | **New** | Phase -1 |
| ADR-011 | Payment App Registration | **New** | Phase 0 |
| ADR-012 | Encrypted Financial Fields | **New** | Phase 0 |
| ADR-013 | Webhook Location | **New** | Phase 0 |
| ADR-014 | Breaking Changes Only in Phase 5 | **New** | Phase -1 |

### 20.3 ADR Format

Every ADR must include:

```markdown
# ADR-XXX: Title

**Status:** Proposed | Accepted | Deprecated | Archived
**Date:** YYYY-MM-DD
**Supersedes:** ADR-XXX (if applicable)
**Context:** Why are we making this decision?
**Decision:** What are we doing?
**Rationale:** Why this option over alternatives?
**Consequences:** What are the trade-offs?
**Validation:** How do we know this works?
```

---

## 21. Risk Register

### 21.1 Critical Risks

| ID | Risk | Phase | Probability | Impact | Mitigation |
|----|------|-------|-------------|--------|------------|
| CR-1 | `AUTH_USER_MODEL` migration attempted despite rejection | All | Low | Critical | Reject in ADR-003. Enforce via architecture test. |
| CR-2 | `apps/` parent directory introduced | All | Low | Critical | Reject in ADR-009. Enforce via architecture test. |
| CR-3 | `payments/` not added to `INSTALLED_APPS` | Phase 0 | Low | Critical | Add in Phase -1. Verify in CI. |
| CR-4 | Bank details not encrypted | Phase 0 | Low | Critical | Add in Phase 0. Enforce via architecture test. |
| CR-5 | Circular dependencies introduced during refactor | All | Medium | High | Break in Phase -1. Enforce via import-linter + AST tests. |
| CR-6 | Data migration fails in production | Phase 0, 2, 5 | Medium | High | Test in staging. Have rollback. Use additive migrations. |

### 21.2 High Risks

| ID | Risk | Phase | Probability | Impact | Mitigation |
|----|------|-------|-------------|--------|------------|
| HI-1 | `core/views.py` split breaks existing endpoints | Phase 0 | Medium | High | Thorough integration tests. Keep old URLs as redirects. |
| HI-2 | Webhook URLs change breaks provider callbacks | Phase 0 | Medium | High | Keep old URLs as 301 redirects. Update provider dashboards. |
| HI-3 | Cross-app imports missed during refactor | Phase 1-4 | Medium | High | AST-based architecture tests on every commit. |
| HI-4 | `rentsecure_be/` utilities still imported after move | Phase 0-3 | Medium | High | Architecture test: no `rentsecure_be` imports in apps. |
| HI-5 | Feature flags not per-user | Phase 0 | Medium | Medium | Plan `FeatureFlag` model for Phase 6. |
| HI-6 | `notification/` domain logic not fully moved | Phase 4 | Medium | Medium | Architecture test: no `RentRecord` imports in `notification/services/`. |
| HI-7 | `ai_assistant/` and `smartbot/` consolidation fails | Phase 6 | Medium | Medium | Treat as separate task. Can be deferred. |

### 21.3 Medium Risks

| ID | Risk | Phase | Probability | Impact | Mitigation |
|----|------|-------|-------------|--------|------------|
| MD-1 | `import-linter.ini` misconfigured | Phase 0 | Low | Medium | Review by Staff Engineer. Test in CI. |
| MD-2 | Management commands not moved to apps | Phase 0 | Low | Medium | Architecture test: no management commands at root. |
| MD-3 | `type_compat.py` shim causes confusion | Phase -1 | Low | Low | Add deprecation warning. Remove after 1 release cycle. |
| MD-4 | `shared/` naming conflicts (`ValidationError`) | Phase 0 | Low | Medium | Resolve in Phase 0. Enforce naming convention. |
| MD-5 | Performance regression from service indirection | Phase 1-4 | Low | Medium | Performance benchmarks in CI. |
| MD-6 | Rollback not tested | All | Low | High | Mandatory rollback test for each phase. |

### 21.4 Risk Monitoring

| Activity | Frequency | Owner |
|----------|-----------|-------|
| Risk register review | Weekly | Staff Engineer |
| Rollback drill | Every phase | DevOps |
| Architecture test review | Every PR | Architecture team |
| Security scan | Every PR | Security Lead |

---

## 22. Deliverables Summary

### 22.1 Deliverables by Phase

| Phase | Deliverables |
|-------|-------------|
| **Phase -1** | `shared/type_compat.py`, `payments/adapters/cashfree_client.py`, `payments/migrations/`, updated `import-linter.ini` |
| **Phase 0** | Encrypted fields, `payments/models.py`, `notification/models.py`, `payments/views/webhooks.py`, split `core/views/`, moved management commands, architecture tests, webhook idempotency |
| **Phase 1** | `identity/services/`, `identity/tests/` |
| **Phase 2** | `subscription/services/`, `subscription/tests/` |
| **Phase 3** | `payments/services/`, `payments/tests/`, removed `rentsecure_be/services/` duplicates |
| **Phase 4** | `dashboard/services/`, `dashboard/views/`, simplified `notification/services/` |
| **Phase 5** | Minimal `core/`, `docs/migration/v1-to-v2.md`, **v2.0.0 release** |
| **Phase 6** | `platform/events/`, `platform/cache/redis.py`, repositories, `docs/architecture/contexts/`, performance benchmarks |

### 22.2 Final State (Post Phase 6)

```
rentsecure_be/
├── apps/                           # NOT USED — apps at root
├── core/                           # Minimal identity app
│   ├── models.py                   # User, UserProfile, OTP only
│   ├── views/                      # Empty or removed
│   ├── services/                   # Empty or removed
│   └── migrations/
├── identity/                       # Identity services (new)
│   ├── services/
│   ├── views/
│   └── tests/
├── subscription/                   # Subscription services (new)
│   ├── services/
│   ├── views/
│   └── tests/
├── property/                       # Property management (existing)
├── payment/                        # Payment services (existing, expanded)
│   ├── models.py                   # OwnerBankDetails
│   ├── adapters/
│   ├── services/
│   ├── views/
│   └── tests/
├── notification/                   # Notification adapters (simplified)
│   ├── adapters/
│   ├── services/                   # Dispatcher only
│   └── tests/
├── document/                       # Document management (existing)
├── finance/                        # Finance (existing)
├── referral/                       # Referral (existing)
├── dashboard/                      # Dashboard (new)
│   ├── services/
│   ├── views/
│   └── tests/
├── ai/                             # AI (deferred)
├── shared/                         # Shared kernel
│   ├── fields.py                   # Encrypted fields
│   ├── type_compat.py              # Moved from rentsecure_be/
│   └── tests/
├── platform/                       # Infrastructure adapters
│   ├── cache/
│   ├── storage/
│   ├── search/
│   └── events/                     # Event bus (Phase 6)
├── config/                         # Django configuration (new)
├── tests/                          # Cross-cutting tests
│   ├── architecture/
│   ├── contract/
│   └── performance/
├── docs/                           # Documentation
├── manage.py
├── pyproject.toml
├── pytest.ini
├── mypy.ini
├── ruff.toml
├── import-linter.ini
└── .env.example
```

### 22.3 Success Criteria

| Criterion | Target |
|-----------|--------|
| **Production incidents** | 0 |
| **Data loss** | 0 |
| **Downtime** | 0 minutes |
| **Test coverage** | ≥90% unit, ≥80% integration |
| **Import-linter violations** | 0 |
| **Circular dependencies** | 0 |
| **Architecture test pass rate** | 100% |
| **Rollback tested** | Every phase |
| **Documentation complete** | All contexts documented |
| **ADR compliance** | All changes have ADRs |

---

## Appendix A: Phase Dependencies Graph

```
Phase -1 (Break Cycles)
    │
    ├──→ Phase 0 (Foundation)
    │       │
    │       ├──→ Phase 1 (Identity Services)
    │       │       │
    │       │       ├──→ Phase 2 (Subscription)
    │       │       │       │
    │       │       │       ├──→ Phase 3 (Payment)
    │       │       │       │       │
    │       │       │       │       ├──→ Phase 4 (Dashboard & Notification)
    │       │       │       │       │       │
    │       │       │       │       │       ├──→ Phase 5 (Deprecate Core) ← BREAKING
    │       │       │       │       │       │       │
    │       │       │       │       │       │       └──→ Phase 6 (Optimization)
    │       │       │       │       │       │
    │       │       │       │       │       └──→ Phase 6 (Optimization)
```

## Appendix B: Key Decisions Summary

| Decision | Rationale |
|----------|-----------|
| No `apps/` parent directory | Changes every import path. No architectural value. |
| Keep `core.User` as `AUTH_USER_MODEL` | Django does not support dual user models or proxy transitions. |
| No `rent/` bounded context | Phantom context. Rent logic stays in `properties/`. |
| `payments/` in `INSTALLED_APPS` from Phase -1 | Zombie app. Must be registered to be functional. |
| `type_compat.py` in `shared/` from Phase -1 | Eliminates 20+ infrastructure boundary violations. |
| `OwnerBankDetails` in `payments/` from Phase 0 | Financial entity in identity app is a critical risk. |
| Webhooks in `payments/` from Phase 0 | Payment webhooks in `core/views.py` is a critical risk. |
| Phase 5 is the only breaking change | All prior phases are additive or internal refactors. |
| No `rentsecure_be/` imports in apps | Eliminates God-layer anti-pattern. |
| Architecture tests on every commit | Prevents architectural decay. |

---

*End of Architecture v1.1 Implementation Master Plan*

**Prepared by:** Principal Software Architect
**Date:** 2026-07-19
**Next Review:** After Phase 0 completion
**Approval Required:** Staff Engineer, Platform Team Lead, Product Team Lead, Security Lead, DevOps Engineer
