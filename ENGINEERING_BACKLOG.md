# RentSecureBE — Engineering Backlog

**Status:** APPROVED FOR EXECUTION
**Date:** 2026-07-19
**Source:** Architecture v1.1 Implementation Master Plan
**Format:** Compatible with GitHub Projects, Jira, Linear
**Total Phases:** 8 (Phase -1 through Phase 6)
**Total Duration:** 20 weeks

---

## How to Use This Backlog

- **Epics** map to implementation phases
- **Features** map to major work areas within each phase
- **User Stories** describe value delivered to developers, users, or the system
- **Technical Tasks** are the concrete implementation steps
- **Subtasks** are the smallest unit of work

All tasks include: Priority, Estimated Effort, Dependencies, Acceptance Criteria, Risk Level, Testing Requirements, Rollback Requirement, and Definition of Done.

---

## Priority Legend

| Priority | Description | Effort Range |
|----------|-------------|--------------|
| P0 | Critical — blocks all other work | 1-4 hours |
| P1 | High — core path | 4-8 hours |
| P2 | Medium — can be parallelized | 8-16 hours |
| P3 | Low — nice to have | 16+ hours |

## Risk Legend

| Risk | Description |
|------|-------------|
| Low | Safe, reversible, well-tested |
| Medium | Requires coordination, tested rollback |
| High | Production impact, data migration, or breaking change |
| Critical | Could cause data loss or extended outage |

---

# Phase -1: Break Circular Dependencies

**Epic:** Phase -1: Break Circular Dependencies
**Duration:** Week 1
**Goal:** Eliminate all 4 circular dependency cycles before any structural changes
**Risk:** Medium

---

## Feature -1.1: Move type_compat to shared

**User Story:** As a developer, I want `type_compat.py` in `shared/` so that no app depends on `rentsecure_be/` for Python compatibility shims.

### Technical Task -1.1.1: Move type_compat.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | None |
| **Acceptance Criteria** | - `shared/type_compat.py` exists with all original content<br>- All 20+ importers updated to `from shared.type_compat import override`<br>- No imports from `rentsecure_be.type_compat` remain in app code |
| **Risk Level** | Medium |
| **Testing Requirements** | - All existing tests pass<br>- `import-linter check` passes<br>- No circular dependencies |
| **Rollback Requirement** | Revert single PR. All changes are additive (file move + import updates). No data changes. |
| **Definition of Done** | - [ ] `shared/type_compat.py` created<br>- [ ] All 20+ importers updated<br>- [ ] CI passes<br>- [ ] PR approved by Staff Engineer and Platform Lead |

### Technical Task -1.1.2: Add deprecated shim in rentsecure_be

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | -1.1.1 |
| **Acceptance Criteria** | - `rentsecure_be/type_compat.py` is a deprecated shim that re-exports from `shared/`<br>- Shim emits `DeprecationWarning` on import<br>- Shim will be removed after 1 release cycle |
| **Risk Level** | Low |
| **Testing Requirements** | - Test that shim emits `DeprecationWarning`<br>- Test that shim re-exports correctly |
| **Rollback Requirement** | Remove shim file. No impact. |
| **Definition of Done** | - [ ] Shim created with deprecation warning<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature -1.2: Consolidate Cashfree payout utilities

**User Story:** As a platform engineer, I want Cashfree payout utilities in `payments/` so that the payment adapter has no dependency on `rentsecure_be/utils/`.

### Technical Task -1.2.1: Move cashfree_payout.py to payments

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | None |
| **Acceptance Criteria** | - `payments/adapters/cashfree_client.py` contains all functions from `rentsecure_be/utils/cashfree_payout.py`<br>- `payments/adapters/cashfree.py` imports from `payments/adapters/cashfree_client.py`<br>- `rentsecure_be/utils/cashfree_payout.py` is a deprecated shim or removed |
| **Risk Level** | Medium |
| **Testing Requirements** | - All existing Cashfree tests pass<br>- Webhook tests pass<br>- `import-linter check` passes |
| **Rollback Requirement** | Revert PR. Old imports restored. |
| **Definition of Done** | - [ ] `cashfree_client.py` created in `payments/adapters/`<br>- [ ] All imports updated<br>- [ ] CI passes<br>- [ ] PR approved by Platform Lead |

### Technical Task -1.2.2: Update Cashfree adapter imports

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | -1.2.1 |
| **Acceptance Criteria** | - `payments/adapters/cashfree.py` imports from `payments.adapters.cashfree_client`<br>- No imports from `rentsecure_be.utils.cashfree_payout` remain |
| **Risk Level** | Low |
| **Testing Requirements** | - All existing Cashfree tests pass |
| **Rollback Requirement** | Revert import changes. |
| **Definition of Done** | - [ ] Imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature -1.3: Register payments app

**User Story:** As a Django developer, I want `payments` in `INSTALLED_APPS` so that the app is functional and migrations can be applied.

### Technical Task -1.3.1: Add payments to INSTALLED_APPS

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 0.5 hours |
| **Dependencies** | None |
| **Acceptance Criteria** | - `payments` is in `INSTALLED_APPS` in `rentsecure_be/settings.py`<br>- `python manage.py check` passes<br>- `python manage.py migrate` runs without errors |
| **Risk Level** | Low |
| **Testing Requirements** | - `manage.py check` passes<br>- `manage.py migrate` runs cleanly |
| **Rollback Requirement** | Remove `payments` from `INSTALLED_APPS`. No data changes. |
| **Definition of Done** | - [ ] `payments` added to `INSTALLED_APPS`<br>- [ ] `manage.py check` passes<br>- [ ] CI passes |

### Technical Task -1.3.2: Create payments migrations package

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 0.5 hours |
| **Dependencies** | -1.3.1 |
| **Acceptance Criteria** | - `payments/migrations/__init__.py` exists<br>- `python manage.py makemigrations payments` generates initial migration (even if empty) |
| **Risk Level** | Low |
| **Testing Requirements** | - `makemigrations` runs without errors<br>- `migrate` applies cleanly |
| **Rollback Requirement** | Remove `payments/migrations/` directory. |
| **Definition of Done** | - [ ] `__init__.py` created<br>- [ ] Initial migration generated<br>- [ ] CI passes |

---

## Feature -1.4: Validate circular dependency removal

**User Story:** As an architect, I want automated validation that all circular dependencies are broken so that the codebase is safe for refactoring.

### Technical Task -1.4.1: Add circular dependency detection test

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | -1.1, -1.2, -1.3 |
| **Acceptance Criteria** | - `tests/architecture/test_circular_deps.py` exists<br>- Test uses AST analysis to detect cycles<br>- Test fails if any circular dependency exists<br>- Test passes on `main` after Phase -1 |
| **Risk Level** | Low |
| **Testing Requirements** | - Test detects known cycles (verified with current codebase)<br>- Test passes after Phase -1 changes |
| **Rollback Requirement** | Remove test file. |
| **Definition of Done** | - [ ] Test created<br>- [ ] Test passes<br>- [ ] CI passes |

### Technical Task -1.4.2: Add rentsecure_be boundary test

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | -1.1 |
| **Acceptance Criteria** | - Test confirms no app (except `rentsecure_be/`) imports from `rentsecure_be/`<br>- Test fails if any app imports from `rentsecure_be/` |
| **Risk Level** | Low |
| **Testing Requirements** | - Test detects current violations (before fix)<br>- Test passes after Phase -1 |
| **Rollback Requirement** | Remove test file. |
| **Definition of Done** | - [ ] Test created<br>- [ ] Test passes after -1.1<br>- [ ] CI passes |

---

## Phase -1 Milestones

| Milestone | Criteria | Date |
|-----------|----------|------|
| M--1.1 | `type_compat.py` moved to `shared/` | Week 1, Day 2 |
| M--1.2 | `cashfree_payout.py` moved to `payments/` | Week 1, Day 3 |
| M--1.3 | `payments` in `INSTALLED_APPS` | Week 1, Day 1 |
| M--1.4 | All circular dependencies broken | Week 1, Day 5 |
| M--1.5 | Phase -1 complete | Week 1, Day 5 |

---

# Phase 0: Foundation & Critical Fixes

**Epic:** Phase 0: Foundation & Critical Fixes
**Duration:** Week 2-3
**Goal:** Fix all Critical findings from Architecture v1.1 Review
**Risk:** Medium

---

## Feature 0.1: Encrypted Financial Fields

**User Story:** As a security engineer, I want bank account numbers and IFSC codes encrypted at rest so that we comply with RBI guidelines and protect owner financial data.

### Technical Task 0.1.1: Create encrypted field types in shared

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | None |
| **Acceptance Criteria** | - `shared/fields.py` contains `EncryptedCharField` and `EncryptedTextField`<br>- Fields use `django-cryptography` or equivalent<br>- Fields are type-annotated and documented |
| **Risk Level** | Low |
| **Testing Requirements** | - Unit tests for encryption/decryption<br>- Test that encrypted fields cannot be read without key<br>- Test that fields work with Django ORM |
| **Rollback Requirement** | Remove `shared/fields.py`. Revert model fields to plain `CharField`. |
| **Definition of Done** | - [ ] `shared/fields.py` created<br>- [ ] Encrypted field types implemented<br>- [ ] Unit tests pass<br>- [ ] CI passes |

### Technical Task 0.1.2: Migrate OwnerBankDetails to use encrypted fields

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 0.1.1 |
| **Acceptance Criteria** | - `payments/models.py` `OwnerBankDetails.bank_account_number` uses `EncryptedCharField`<br>- `payments/models.py` `OwnerBankDetails.ifsc_code` uses `EncryptedCharField`<br>- Migration generated and tested |
| **Risk Level** | Medium |
| **Testing Requirements** | - Migration forward/backward tests<br>- Test that encrypted data is readable by application<br>- Test that encrypted data is not readable in database |
| **Rollback Requirement** | Revert migration. Data in old format must be recoverable. |
| **Definition of Done** | - [ ] Model fields updated<br>- [ ] Migration generated and tested<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 0.2: Move OwnerBankDetails to payments

**User Story:** As a platform engineer, I want `OwnerBankDetails` in `payments/` so that financial entities are in the correct bounded context.

### Technical Task 0.2.1: Create payments models module

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | None |
| **Acceptance Criteria** | - `payments/models.py` exists with `OwnerBankDetails` model<br>- Model uses encrypted fields for sensitive data<br>- Model has proper indexes and constraints |
| **Risk Level** | Medium |
| **Testing Requirements** | - Model tests (create, read, update, delete)<br>- Field validation tests<br>- Encryption tests |
| **Rollback Requirement** | Remove `payments/models.py`. Keep `core/models.py` version. |
| **Definition of Done** | - [ ] Model created<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 0.2.2: Create data migration for OwnerBankDetails

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 0.2.1 |
| **Acceptance Criteria** | - Migration copies `core_ownerbankdetails` → `payment_ownerbankdetails`<br>- Migration preserves all data including encrypted fields<br>- Migration is reversible<br>- Migration tested on production-like data volume |
| **Risk Level** | Medium |
| **Testing Requirements** | - Forward migration test<br>- Reverse migration test<br>- Data integrity test (row count, checksums)<br>- Test with production data snapshot |
| **Rollback Requirement** | Run `migrate --reverse`. Old table remains for 1 release cycle. |
| **Definition of Done** | - [ ] Migration created<br>- [ ] Forward/backward tests pass<br>- [ ] Data integrity verified<br>- [ ] CI passes |

### Technical Task 0.2.3: Update core models to deprecate OwnerBankDetails

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 0.2.2 |
| **Acceptance Criteria** | - `core/models.py` `OwnerBankDetails` is a deprecated shim or removed<br>- Any remaining imports emit `DeprecationWarning`<br>- Old table remains for 1 release cycle |
| **Risk Level** | Medium |
| **Testing Requirements** | - Deprecation warning tests<br>- Import tests |
| **Rollback Requirement** | Restore `core/models.py` version. |
| **Definition of Done** | - [ ] Deprecated shim or removal complete<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 0.3: Move NotificationPreference to notification

**User Story:** As a notification engineer, I want `NotificationPreference` in `notification/` so that notification concerns are in the correct bounded context.

### Technical Task 0.3.1: Create notification models module

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | None |
| **Acceptance Criteria** | - `notification/models.py` exists with `NotificationPreference` model<br>- Model matches original fields and behavior<br>- Model has proper indexes and constraints |
| **Risk Level** | Medium |
| **Testing Requirements** | - Model tests (create, read, update, delete)<br>- Field validation tests<br>- Upsert behavior tests |
| **Rollback Requirement** | Remove `notification/models.py`. Keep `core/models.py` version. |
| **Definition of Done** | - [ ] Model created<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 0.3.2: Create data migration for NotificationPreference

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | 0.3.1 |
| **Acceptance Criteria** | - Migration copies `core_notificationpreference` → `notification_notificationpreference`<br>- Migration preserves all data<br>- Migration is reversible<br>- Migration tested |
| **Risk Level** | Medium |
| **Testing Requirements** | - Forward migration test<br>- Reverse migration test<br>- Data integrity test |
| **Rollback Requirement** | Run `migrate --reverse`. Old table remains for 1 release cycle. |
| **Definition of Done** | - [ ] Migration created<br>- [ ] Forward/backward tests pass<br>- [ ] CI passes |

### Technical Task 0.3.3: Update core models to deprecate NotificationPreference

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 0.3.2 |
| **Acceptance Criteria** | - `core/models.py` `NotificationPreference` is a deprecated shim or removed<br>- Any remaining imports emit `DeprecationWarning` |
| **Risk Level** | Low |
| **Testing Requirements** | - Deprecation warning tests |
| **Rollback Requirement** | Restore `core/models.py` version. |
| **Definition of Done** | - [ ] Deprecated shim or removal complete<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 0.4: Move webhooks to payments

**User Story:** As a security engineer, I want webhook handlers in `payments/` so that payment webhook logic is isolated and verified in the correct bounded context.

### Technical Task 0.4.1: Create payments webhook views module

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | None |
| **Acceptance Criteria** | - `payments/views/webhooks.py` contains `cashfree_payout_webhook` and `razorpay_webhook`<br>- Webhook handlers include HMAC verification<br>- Webhook handlers include idempotency key checks<br>- Handlers are tested with sample payloads |
| **Risk Level** | High |
| **Testing Requirements** | - Unit tests for each webhook handler<br>- Integration tests with sample payloads<br>- Idempotency tests (duplicate webhooks)<br>- Security tests (invalid signatures rejected) |
| **Rollback Requirement** | Revert PR. Old webhook handlers in `core/views.py` remain active. |
| **Definition of Done** | - [ ] Webhook handlers created<br>- [ ] HMAC verification implemented<br>- [ ] Idempotency implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 0.4.2: Create payments URLs module

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 0.4.1 |
| **Acceptance Criteria** | - `payments/urls.py` contains webhook URL patterns<br>- URLs match existing patterns for backward compatibility<br>- URLs are documented |
| **Risk Level** | Medium |
| **Testing Requirements** | - URL resolution tests<br>- Webhook endpoint integration tests |
| **Rollback Requirement** | Remove `payments/urls.py`. Old URLs in `core/urls.py` remain. |
| **Definition of Done** | - [ ] URLs created<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 0.4.3: Add webhook URLs to rentsecure_be/urls.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 0.4.2 |
| **Acceptance Criteria** | - `rentsecure_be/urls.py` includes `payments/urls.py`<br>- Webhook endpoints are accessible<br>- No 404 errors |
| **Risk Level** | Medium |
| **Testing Requirements** | - End-to-end webhook tests |
| **Rollback Requirement** | Remove URL include. Old URLs in `core/urls.py` remain. |
| **Definition of Done** | - [ ] URLs included<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 0.4.4: Keep old webhook URLs as deprecated redirects

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 0.4.3 |
| **Acceptance Criteria** | - Old `core/urls.py` webhook URLs return 301/302 redirects to new URLs<br>- Redirects preserve HTTP method and body<br>- Redirects are logged for monitoring |
| **Risk Level** | Medium |
| **Testing Requirements** | - Redirect tests (old URL → new URL)<br>- Webhook provider tests (Cashfree, Razorpay) |
| **Rollback Requirement** | Remove redirects. Old handlers become active again. |
| **Definition of Done** | - [ ] Redirects implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 0.5: Split core/views.py

**User Story:** As a developer, I want `core/views.py` split into focused modules so that the god view is eliminated and each responsibility is isolated.

### Technical Task 0.5.1: Create core/views/ package structure

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | None |
| **Acceptance Criteria** | - `core/views/__init__.py` exists<br>- `core/views.py` is renamed or split into:<br>  - `core/views/auth_views.py`<br>  - `core/views/subscription_views.py`<br>  - `core/views/bank_views.py`<br>  - `core/views/reporting_views.py`<br>- No file exceeds 300 lines |
| **Risk Level** | Medium |
| **Testing Requirements** | - All existing view tests pass<br>- URL resolution tests<br>- Import tests |
| **Rollback Requirement** | Revert to single `core/views.py`. |
| **Definition of Done** | - [ ] Views split into 4 files<br>- [ ] No file exceeds 300 lines<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 0.5.2: Update rentsecure_be/urls.py imports

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 0.5.1 |
| **Acceptance Criteria** | - `rentsecure_be/urls.py` imports from new view modules<br>- All URLs resolve correctly<br>- No import errors |
| **Risk Level** | Low |
| **Testing Requirements** | - URL resolution tests<br>- Integration tests |
| **Rollback Requirement** | Revert imports to `core.views`. |
| **Definition of Done** | - [ ] Imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 0.6: Move root management commands to apps

**User Story:** As a developer, I want management commands in their owning app's `management/` directory so that commands are discoverable and ownership is clear.

### Technical Task 0.6.1: Audit root management commands

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | None |
| **Acceptance Criteria** | - Inventory of all 15 root management commands<br>- Each command mapped to owning app<br>- Duplicate commands identified |
| **Risk Level** | Low |
| **Testing Requirements** | - None (audit only) |
| **Rollback Requirement** | N/A |
| **Definition of Done** | - [ ] Inventory complete<br>- [ ] Ownership assigned |

### Technical Task 0.6.2: Move management commands to owning apps

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 8 hours |
| **Dependencies** | 0.6.1 |
| **Acceptance Criteria** | - All 15 root commands moved to app `management/commands/`<br>- Each command is in its owning app's directory<br>- Commands are importable via `python manage.py <command>`<br>- No commands remain at project root |
| **Risk Level** | Medium |
| **Testing Requirements** | - Each command runs successfully<br>- Command output tests<br>- Integration tests |
| **Rollback Requirement** | Revert PR. Commands return to root. |
| **Definition of Done** | - [ ] All commands moved<br>- [ ] All commands run successfully<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 0.6.3: Remove duplicate management commands

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 0.6.2 |
| **Acceptance Criteria** | - Duplicate commands (e.g., `send_monthly_rent_summary`) removed<br>- Single source of truth for each command<br>- No functional regressions |
| **Risk Level** | Medium |
| **Testing Requirements** | - Regression tests for affected functionality |
| **Rollback Requirement** | Restore duplicate commands. |
| **Definition of Done** | - [ ] Duplicates removed<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 0.7: Rewrite import-linter.ini

**User Story:** As an architect, I want `import-linter.ini` rewritten without `rentsecure_be` as an allowed layer so that cross-app imports are properly enforced.

### Technical Task 0.7.1: Rewrite import-linter.ini

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | -1.1, -1.2, -1.3 |
| **Acceptance Criteria** | - `import-linter.ini` does NOT include `rentsecure_be` as an allowed layer for any app<br>- All apps can only import from `shared/`, `platform/`, and allowed apps per v1.1 matrix<br>- `import-linter check` passes on current codebase (after Phase -1 fixes) |
| **Risk Level** | Medium |
| **Testing Requirements** | - `import-linter check` passes on all branches<br>- Test that violations are caught (introduce a violation, verify test fails) |
| **Rollback Requirement** | Revert to previous `import-linter.ini`. |
| **Definition of Done** | - [ ] `import-linter.ini` rewritten<br>- [ ] `import-linter check` passes<br>- [ ] CI passes<br>- [ ] PR approved by Staff Engineer |

---

## Feature 0.8: Add architecture regression tests

**User Story:** As an architect, I want automated architecture tests so that architectural violations are caught before they reach production.

### Technical Task 0.8.1: Create tests/architecture/ package

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | None |
| **Acceptance Criteria** | - `tests/architecture/__init__.py` exists<br>- `tests/architecture/test_import_rules.py` exists<br>- `tests/architecture/test_layer_compliance.py` exists<br>- `tests/architecture/test_sdk_placement.py` exists<br>- `tests/architecture/test_god_views.py` exists<br>- `tests/architecture/test_god_models.py` exists |
| **Risk Level** | Low |
| **Testing Requirements** | - All architecture tests pass on current codebase<br>- Tests are integrated into CI |
| **Rollback Requirement** | Remove `tests/architecture/` directory. |
| **Definition of Done** | - [ ] Package created with test files<br>- [ ] All tests pass<br>- [ ] CI passes |

### Technical Task 0.8.2: Implement import rules tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 0.8.1 |
| **Acceptance Criteria** | - `test_import_rules.py` contains tests for:<br>  - No `razorpay` imports in non-adapter files<br>  - No `cashfree` imports in non-adapter files<br>  - No `twilio` imports outside `notification/adapters/`<br>  - No `boto3` imports outside `notification/adapters/` and `documents/`<br>  - No `requests` to payment APIs outside `payments/adapters/`<br>  - No `rentsecure_be` imports in app code<br>  - No `Notification.objects.create` outside `notification/`<br>- All tests pass |
| **Risk Level** | Medium |
| **Testing Requirements** | - Tests catch known violations (verified against current codebase)<br>- Tests pass after Phase -1 fixes |
| **Rollback Requirement** | Remove or disable failing tests. |
| **Definition of Done** | - [ ] Tests implemented<br>- [ ] Tests pass after Phase -1<br>- [ ] CI passes |

### Technical Task 0.8.3: Implement layer compliance tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | 0.8.1 |
| **Acceptance Criteria** | - `test_layer_compliance.py` contains tests for:<br>  - Views do not import models from other apps<br>  - Views do not import services from other apps<br>  - Models do not import views or services<br>- All tests pass |
| **Risk Level** | Medium |
| **Testing Requirements** | - Tests catch known violations<br>- Tests pass after Phase -1 |
| **Rollback Requirement** | Remove or disable failing tests. |
| **Definition of Done** | - [ ] Tests implemented<br>- [ ] Tests pass after Phase -1<br>- [ ] CI passes |

### Technical Task 0.8.4: Implement god view and god model detection tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 0.8.1 |
| **Acceptance Criteria** | - `test_god_views.py` fails if any view file exceeds 300 lines<br>- `test_god_models.py` fails if any model file exceeds 400 lines<br>- Tests pass after Phase 0 view split |
| **Risk Level** | Low |
| **Testing Requirements** | - Tests detect current violations<br>- Tests pass after fixes |
| **Rollback Requirement** | Remove tests. |
| **Definition of Done** | - [ ] Tests implemented<br>- [ ] Thresholds configured<br>- [ ] CI passes |

---

## Feature 0.9: Add webhook idempotency keys

**User Story:** As a payment engineer, I want webhook idempotency keys so that duplicate webhooks do not cause double-processing of payments.

### Technical Task 0.9.1: Create WebhookEvent model

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | None |
| **Acceptance Criteria** | - `payments/models.py` contains `WebhookEvent` model<br>- Model has `event_id` (unique), `provider`, `payload`, `processed_at`<br>- Model has index on `event_id` |
| **Risk Level** | Medium |
| **Testing Requirements** | - Model tests<br>- Migration tests (forward/backward) |
| **Rollback Requirement** | Remove model and migration. |
| **Definition of Done** | - [ ] Model created<br>- [ ] Migration generated and tested<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 0.9.2: Integrate idempotency into webhook handlers

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 0.9.1, 0.4.1 |
| **Acceptance Criteria** | - Each webhook handler checks `WebhookEvent` before processing<br>- Duplicate webhooks return 200 with original response<br>- New webhooks create `WebhookEvent` record |
| **Risk Level** | Medium |
| **Testing Requirements** | - Idempotency tests (send same webhook twice)<br>- Integration tests with sample payloads |
| **Rollback Requirement** | Remove idempotency checks. Webhooks process every request. |
| **Definition of Done** | - [ ] Idempotency implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 0.10: Add audit logging for payment operations

**User Story:** As a security engineer, I want audit logging for payment operations so that I can investigate payment disputes and detect fraud.

### Technical Task 0.10.1: Enable django-simple-history for payment models

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 0.2.1 |
| **Acceptance Criteria** | - `OwnerBankDetails` has `HistoricalRecords`<br>- `WebhookEvent` has `HistoricalRecords`<br>- Payment models (when added) have `HistoricalRecords`<br>- Audit log includes user, timestamp, changes |
| **Risk Level** | Low |
| **Testing Requirements** | - Audit log tests (create, update, delete)<br>- Test that historical records are created |
| **Rollback Requirement** | Remove `HistoricalRecords`. No data loss. |
| **Definition of Done** | - [ ] Historical records enabled<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 0.10.2: Add audit logging for payment status changes

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 0.10.1 |
| **Acceptance Criteria** | - Changes to `RentRecord.payout_status` are logged<br>- Changes to `OwnerBankDetails` are logged<br>- Audit log includes user, timestamp, old value, new value |
| **Risk Level** | Low |
| **Testing Requirements** | - Audit log tests<br>- Integration tests |
| **Rollback Requirement** | Remove audit logging. No data loss. |
| **Definition of Done** | - [ ] Audit logging implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 0.11: Add migration rollback tests to CI

**User Story:** As a DevOps engineer, I want migration rollback tests in CI so that migration failures are caught before production.

### Technical Task 0.11.1: Create tests/test_migrations.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | None |
| **Acceptance Criteria** | - `tests/test_migrations.py` exists<br>- Test runs `manage.py migrate` forward on test database<br>- Test runs `manage.py migrate --reverse` on test database<br>- Test verifies no data loss |
| **Risk Level** | Low |
| **Testing Requirements** | - Test passes on current codebase<br>- Test catches broken migrations |
| **Rollback Requirement** | Remove test file. |
| **Definition of Done** | - [ ] Test created<br>- [ ] Test passes<br>- [ ] Integrated into CI<br>- [ ] CI passes |

### Technical Task 0.11.2: Add migration test step to CI pipeline

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 0.11.1 |
| **Acceptance Criteria** | - `.github/workflows/ci.yml` includes migration test step<br>- Step runs `pytest tests/test_migrations.py -v`<br>- Step is blocking |
| **Risk Level** | Low |
| **Testing Requirements** | - CI pipeline passes |
| **Rollback Requirement** | Revert CI workflow change. |
| **Definition of Done** | - [ ] CI updated<br>- [ ] CI passes |

---

## Phase 0 Milestones

| Milestone | Criteria | Date |
|-----------|----------|------|
| M0.1 | Encrypted field types created | Week 2, Day 2 |
| M0.2 | OwnerBankDetails moved to payments | Week 2, Day 3 |
| M0.3 | NotificationPreference moved to notification | Week 2, Day 4 |
| M0.4 | Webhooks in payments/views/webhooks.py | Week 2, Day 5 |
| M0.5 | core/views.py split into 4 files | Week 3, Day 2 |
| M0.6 | Root management commands moved | Week 3, Day 3 |
| M0.7 | import-linter.ini rewritten | Week 3, Day 4 |
| M0.8 | Architecture regression tests added | Week 3, Day 5 |
| M0.9 | Webhook idempotency implemented | Week 3, Day 5 |
| M0.10 | Phase 0 complete | Week 3, Day 5 |

---

# Phase 1: Extract Identity Services

**Epic:** Phase 1: Extract Identity Services
**Duration:** Week 4-6
**Goal:** Move identity services (authentication, OTP, password) out of `core/` into `identity/services/`
**Risk:** Medium

---

## Feature 1.1: Create identity services package

**User Story:** As a developer, I want `identity/services/` package so that identity services have a clear home outside `core/`.

### Technical Task 1.1.1: Create identity/services/ package structure

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | Phase 0 complete |
| **Acceptance Criteria** | - `identity/services/__init__.py` exists<br>- Directory structure is ready for service modules |
| **Risk Level** | Low |
| **Testing Requirements** | - Import tests |
| **Rollback Requirement** | Remove directory. |
| **Definition of Done** | - [ ] Package created<br>- [ ] CI passes |

---

## Feature 1.2: Move AuthService

**User Story:** As a developer, I want `AuthService` in `identity/services/` so that authentication logic is in the identity bounded context.

### Technical Task 1.2.1: Move AuthService to identity/services/

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | 1.1.1 |
| **Acceptance Criteria** | - `identity/services/auth_service.py` contains full `AuthService` implementation<br>- All functionality from `core/services/auth_service.py` is preserved<br>- No behavioral changes |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests for `AuthService`<br>- Integration tests for authentication flows<br>- All existing auth tests pass |
| **Rollback Requirement** | Revert PR. `core/services/auth_service.py` remains. |
| **Definition of Done** | - [ ] Service moved<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 1.2.2: Update core/views/auth_views.py imports

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 1.2.1 |
| **Acceptance Criteria** | - `core/views/auth_views.py` imports `AuthService` from `identity.services.auth_service`<br>- All authentication endpoints work correctly<br>- No import errors |
| **Risk Level** | Medium |
| **Testing Requirements** | - Integration tests for all auth endpoints<br>- Regression tests |
| **Rollback Requirement** | Revert imports to `core.services.auth_service`. |
| **Definition of Done** | - [ ] Imports updated<br>- [ ] Endpoints tested<br>- [ ] CI passes |

### Technical Task 1.2.3: Update all cross-app imports of AuthService

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 1.2.2 |
| **Acceptance Criteria** | - All files importing `core.services.auth_service` updated to `identity.services.auth_service`<br>- No imports of `core.services.auth_service` remain |
| **Risk Level** | Medium |
| **Testing Requirements** | - All affected tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Revert imports. |
| **Definition of Done** | - [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 1.2.4: Add AuthService unit tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 1.2.1 |
| **Acceptance Criteria** | - `identity/tests/unit/test_auth_service.py` exists<br>- All `AuthService` methods have unit tests<br>- Coverage ≥90% |
| **Risk Level** | Low |
| **Testing Requirements** | - Unit tests with mocks<br>- Edge case tests |
| **Rollback Requirement** | Remove test file. |
| **Definition of Done** | - [ ] Tests created<br>- [ ] Coverage ≥90%<br>- [ ] CI passes |

### Technical Task 1.2.5: Add AuthService integration tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 1.2.1 |
| **Acceptance Criteria** | - `identity/tests/integration/test_auth_flows.py` exists<br>- Tests cover full authentication flow (send OTP, verify OTP, login)<br>- Tests use Django test client |
| **Risk Level** | Low |
| **Testing Requirements** | - Integration tests with test database<br>- End-to-end flow tests |
| **Rollback Requirement** | Remove test file. |
| **Definition of Done** | - [ ] Tests created<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 1.3: Move OTPService

**User Story:** As a developer, I want `OTPService` in `identity/services/` so that OTP logic is in the identity bounded context.

### Technical Task 1.3.1: Move OTPService to identity/services/

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | 1.1.1 |
| **Acceptance Criteria** | - `identity/services/otp_service.py` contains full `OTPService` implementation<br>- All functionality preserved |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests for `OTPService`<br>- Integration tests for OTP flows<br>- All existing OTP tests pass |
| **Rollback Requirement** | Revert PR. `core/services/otp_service.py` remains. |
| **Definition of Done** | - [ ] Service moved<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 1.3.2: Update imports of OTPService

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 1.3.1 |
| **Acceptance Criteria** | - All files importing `core.services.otp_service` updated<br>- No imports of `core.services.otp_service` remain |
| **Risk Level** | Medium |
| **Testing Requirements** | - All affected tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Revert imports. |
| **Definition of Done** | - [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 1.3.3: Add OTPService tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 1.3.1 |
| **Acceptance Criteria** | - Unit tests for `OTPService`<br>- Integration tests for OTP flows<br>- Coverage ≥90% |
| **Risk Level** | Low |
| **Testing Requirements** | - Unit tests with mocks<br>- Integration tests with test database |
| **Rollback Requirement** | Remove test files. |
| **Definition of Done** | - [ ] Tests created<br>- [ ] Coverage ≥90%<br>- [ ] CI passes |

---

## Feature 1.4: Move PasswordService

**User Story:** As a developer, I want `PasswordService` in `identity/services/` so that password management logic is in the identity bounded context.

### Technical Task 1.4.1: Move PasswordService to identity/services/

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | 1.1.1 |
| **Acceptance Criteria** | - `identity/services/password_service.py` contains full `PasswordService` implementation<br>- All functionality preserved |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests for `PasswordService`<br>- Integration tests for password flows<br>- All existing password tests pass |
| **Rollback Requirement** | Revert PR. `core/services/password_service.py` remains. |
| **Definition of Done** | - [ ] Service moved<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 1.4.2: Update imports of PasswordService

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 1.4.1 |
| **Acceptance Criteria** | - All files importing `core.services.password_service` updated<br>- No imports of `core.services.password_service` remain |
| **Risk Level** | Medium |
| **Testing Requirements** | - All affected tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Revert imports. |
| **Definition of Done** | - [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 1.4.3: Add PasswordService tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 1.4.1 |
| **Acceptance Criteria** | - Unit tests for `PasswordService`<br>- Integration tests for password flows<br>- Coverage ≥90% |
| **Risk Level** | Low |
| **Testing Requirements** | - Unit tests with mocks<br>- Integration tests with test database |
| **Rollback Requirement** | Remove test files. |
| **Definition of Done** | - [ ] Tests created<br>- [ ] Coverage ≥90%<br>- [ ] CI passes |

---

## Feature 1.5: Update cross-app imports and documentation

**User Story:** As a developer, I want all cross-app imports updated and documentation current so that the codebase is consistent and maintainable.

### Technical Task 1.5.1: Update all cross-app imports

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 1.2, 1.3, 1.4 |
| **Acceptance Criteria** | - All cross-app imports of `core.services.auth_service`, `core.services.otp_service`, `core.services.password_service` updated<br>- No imports of these modules from `core/services/` remain |
| **Risk Level** | Medium |
| **Testing Requirements** | - All affected tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Revert imports. |
| **Definition of Done** | - [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 1.5.2: Update architecture documentation

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 1.2, 1.3, 1.4 |
| **Acceptance Criteria** | - `docs/architecture/contexts/identity.md` updated<br>- Service ownership documented<br>- API interfaces documented |
| **Risk Level** | Low |
| **Testing Requirements** | - Documentation Guardian passes |
| **Rollback Requirement** | Revert documentation changes. |
| **Definition of Done** | - [ ] Documentation updated<br>- [ ] Guardian passes |

---

## Phase 1 Milestones

| Milestone | Criteria | Date |
|-----------|----------|------|
| M1.1 | `identity/services/` package created | Week 4, Day 1 |
| M1.2 | `AuthService` moved and tested | Week 4, Day 3 |
| M1.3 | `OTPService` moved and tested | Week 5, Day 1 |
| M1.4 | `PasswordService` moved and tested | Week 5, Day 3 |
| M1.5 | All cross-app imports updated | Week 6, Day 2 |
| M1.6 | Phase 1 complete | Week 6, Day 5 |

---

# Phase 2: Extract Subscription

**Epic:** Phase 2: Extract Subscription
**Duration:** Week 7-9
**Goal:** Move subscription logic out of `core/` into `subscription/services/`
**Risk:** Low

---

## Feature 2.1: Create subscription services package

**User Story:** As a developer, I want `subscription/services/` package so that subscription services have a clear home outside `core/`.

### Technical Task 2.1.1: Create subscription/services/ package structure

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | Phase 1 complete |
| **Acceptance Criteria** | - `subscription/services/__init__.py` exists<br>- Directory structure ready |
| **Risk Level** | Low |
| **Testing Requirements** | - Import tests |
| **Rollback Requirement** | Remove directory. |
| **Definition of Done** | - [ ] Package created<br>- [ ] CI passes |

---

## Feature 2.2: Move SubscriptionService

**User Story:** As a developer, I want `SubscriptionService` in `subscription/services/` so that subscription logic is in the subscription bounded context.

### Technical Task 2.2.1: Move SubscriptionService to subscription/services/

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | 2.1.1 |
| **Acceptance Criteria** | - `subscription/services/subscription_service.py` contains full implementation<br>- All functionality preserved |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests<br>- Integration tests<br>- All existing subscription tests pass |
| **Rollback Requirement** | Revert PR. `core/services/subscription_service.py` remains. |
| **Definition of Done** | - [ ] Service moved<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 2.2.2: Update imports of SubscriptionService

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 2.2.1 |
| **Acceptance Criteria** | - All imports of `core.services.subscription_service` updated<br>- No old imports remain |
| **Risk Level** | Medium |
| **Testing Requirements** | - All affected tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Revert imports. |
| **Definition of Done** | - [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 2.2.3: Add SubscriptionService tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 2.2.1 |
| **Acceptance Criteria** | - Unit tests for `SubscriptionService`<br>- Integration tests for subscription flows<br>- Coverage ≥90% |
| **Risk Level** | Low |
| **Testing Requirements** | - Unit tests with mocks<br>- Integration tests |
| **Rollback Requirement** | Remove test files. |
| **Definition of Done** | - [ ] Tests created<br>- [ ] Coverage ≥90%<br>- [ ] CI passes |

---

## Feature 2.3: Move UsageLimitService

**User Story:** As a developer, I want `UsageLimitService` in `subscription/services/` so that usage limit logic is in the subscription bounded context.

### Technical Task 2.3.1: Move UsageLimitService to subscription/services/

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | 2.1.1 |
| **Acceptance Criteria** | - `subscription/services/usage_limit_service.py` contains full implementation<br>- All functionality preserved |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests<br>- Integration tests<br>- All existing usage limit tests pass |
| **Rollback Requirement** | Revert PR. `core/services/usage_limit_service.py` remains. |
| **Definition of Done** | - [ ] Service moved<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 2.3.2: Update imports of UsageLimitService

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 2.3.1 |
| **Acceptance Criteria** | - All imports of `core.services.usage_limit_service` updated<br>- No old imports remain |
| **Risk Level** | Medium |
| **Testing Requirements** | - All affected tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Revert imports. |
| **Definition of Done** | - [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 2.3.3: Add UsageLimitService tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 2.3.1 |
| **Acceptance Criteria** | - Unit tests for `UsageLimitService`<br>- Integration tests<br>- Coverage ≥90% |
| **Risk Level** | Low |
| **Testing Requirements** | - Unit tests with mocks<br>- Integration tests |
| **Rollback Requirement** | Remove test files. |
| **Definition of Done** | - [ ] Tests created<br>- [ ] Coverage ≥90%<br>- [ ] CI passes |

---

## Feature 2.4: Move FeatureEnforcer

**User Story:** As a developer, I want `FeatureEnforcer` in `subscription/services/` so that feature enforcement logic is in the subscription bounded context and `properties/` no longer depends on it.

### Technical Task 2.4.1: Move FeatureEnforcer to subscription/services/

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | 2.1.1 |
| **Acceptance Criteria** | - `subscription/services/feature_enforcer.py` contains full `FeatureEnforcer` implementation<br>- All functionality from `properties/feature_enforcer.py` preserved |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests for `FeatureEnforcer`<br>- Integration tests<br>- All existing feature enforcement tests pass |
| **Rollback Requirement** | Revert PR. `properties/feature_enforcer.py` remains. |
| **Definition of Done** | - [ ] Service moved<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 2.4.2: Update properties/ imports of FeatureEnforcer

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 2.4.1 |
| **Acceptance Criteria** | - All 10+ files in `properties/` importing `FeatureEnforcer` updated to import from `subscription/services/feature_enforcer.py`<br>- No imports of `properties.feature_enforcer` remain |
| **Risk Level** | Medium |
| **Testing Requirements** | - All affected tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Revert imports. |
| **Definition of Done** | - [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 2.4.3: Remove properties/feature_enforcer.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 2.4.2 |
| **Acceptance Criteria** | - `properties/feature_enforcer.py` removed<br>- No imports of `properties.feature_enforcer` remain<br>- All tests pass |
| **Risk Level** | Medium |
| **Testing Requirements** | - All tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Restore `properties/feature_enforcer.py` from git. |
| **Definition of Done** | - [ ] File removed<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 2.4.4: Add FeatureEnforcer tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 2.4.1 |
| **Acceptance Criteria** | - Unit tests for `FeatureEnforcer`<br>- Integration tests for feature enforcement flows<br>- Coverage ≥90% |
| **Risk Level** | Low |
| **Testing Requirements** | - Unit tests with mocks<br>- Integration tests |
| **Rollback Requirement** | Remove test files. |
| **Definition of Done** | - [ ] Tests created<br>- [ ] Coverage ≥90%<br>- [ ] CI passes |

---

## Feature 2.5: Update core/views/subscription_views.py

**User Story:** As a developer, I want `core/views/subscription_views.py` to import from `subscription/services/` so that views delegate to the correct service location.

### Technical Task 2.5.1: Update subscription_views.py imports

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 2.2.1, 2.3.1 |
| **Acceptance Criteria** | - `core/views/subscription_views.py` imports `SubscriptionService` and `UsageLimitService` from `subscription/services/`<br>- All subscription endpoints work correctly |
| **Risk Level** | Medium |
| **Testing Requirements** | - Integration tests for subscription endpoints<br>- Regression tests |
| **Rollback Requirement** | Revert imports to `core.services.*`. |
| **Definition of Done** | - [ ] Imports updated<br>- [ ] Endpoints tested<br>- [ ] CI passes |

---

## Feature 2.6: Update documentation

**User Story:** As a developer, I want architecture documentation updated so that it reflects the new subscription service location.

### Technical Task 2.6.1: Update architecture documentation

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 2.2, 2.3, 2.4 |
| **Acceptance Criteria** | - `docs/architecture/contexts/subscription.md` created or updated<br>- Service ownership documented<br>- API interfaces documented |
| **Risk Level** | Low |
| **Testing Requirements** | - Documentation Guardian passes |
| **Rollback Requirement** | Revert documentation changes. |
| **Definition of Done** | - [ ] Documentation updated<br>- [ ] Guardian passes |

---

## Phase 2 Milestones

| Milestone | Criteria | Date |
|-----------|----------|------|
| M2.1 | `subscription/services/` package created | Week 7, Day 1 |
| M2.2 | `SubscriptionService` moved and tested | Week 7, Day 3 |
| M2.3 | `UsageLimitService` moved and tested | Week 8, Day 1 |
| M2.4 | `FeatureEnforcer` moved and `properties/` updated | Week 8, Day 3 |
| M2.5 | `core/views/subscription_views.py` updated | Week 9, Day 1 |
| M2.6 | Phase 2 complete | Week 9, Day 5 |

---

# Phase 3: Extract Payment

**Epic:** Phase 3: Extract Payment
**Duration:** Week 10-12
**Goal:** Consolidate all payment logic in `payments/` and remove duplicates from `rentsecure_be/`
**Risk:** Medium

---

## Feature 3.1: Create payment services

**User Story:** As a platform engineer, I want payment services in `payments/services/` so that payment orchestration is centralized and testable.

### Technical Task 3.1.1: Create payments/services/webhook_service.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | Phase 2 complete |
| **Acceptance Criteria** | - `payments/services/webhook_service.py` contains `WebhookService` with `verify()` and `handle()` methods<br>- Service uses `WebhookEvent` model for idempotency<br>- Service handles Cashfree and Razorpay payloads<br>- All webhook handlers tested |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests for `WebhookService`<br>- Integration tests with sample payloads<br>- Security tests (invalid signatures rejected) |
| **Rollback Requirement** | Remove service file. Webhooks remain in `payments/views/webhooks.py`. |
| **Definition of Done** | - [ ] Service created<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 3.1.2: Create payments/services/bank_details_service.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | Phase 2 complete |
| **Acceptance Criteria** | - `payments/services/bank_details_service.py` contains `BankDetailsService`<br>- Service handles validation, registration, retrieval of bank details<br>- Service uses encrypted fields<br>- All methods tested |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests for `BankDetailsService`<br>- Integration tests for bank details flows<br>- Encryption tests |
| **Rollback Requirement** | Remove service file. Bank details logic remains in `core/views/bank_views.py`. |
| **Definition of Done** | - [ ] Service created<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 3.1.3: Add payment services tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 3.1.1, 3.1.2 |
| **Acceptance Criteria** | - Unit tests for `WebhookService` and `BankDetailsService`<br>- Integration tests for payment flows<br>- Coverage ≥90% |
| **Risk Level** | Low |
| **Testing Requirements** | - Unit tests with mocks<br>- Integration tests |
| **Rollback Requirement** | Remove test files. |
| **Definition of Done** | - [ ] Tests created<br>- [ ] Coverage ≥90%<br>- [ ] CI passes |

---

## Feature 3.2: Move bank details views to payments

**User Story:** As a platform engineer, I want bank details views in `payments/views/` so that payment-related views are centralized.

### Technical Task 3.2.1: Create payments/views/bank_details_views.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 3.1.2 |
| **Acceptance Criteria** | - `payments/views/bank_details_views.py` contains `update_owner_bank_details` view<br>- View uses `BankDetailsService`<br>- View validates input and returns appropriate responses<br>- View is tested |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests for view<br>- Integration tests for bank details API<br>- Permission tests |
| **Rollback Requirement** | Remove view file. Old view in `core/views/bank_views.py` remains. |
| **Definition of Done** | - [ ] View created<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 3.2.2: Add bank details URLs to payments/urls.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 3.2.1 |
| **Acceptance Criteria** | - `payments/urls.py` includes bank details URL pattern<br>- URL is accessible |
| **Risk Level** | Low |
| **Testing Requirements** | - URL resolution tests |
| **Rollback Requirement** | Remove URL pattern. |
| **Definition of Done** | - [ ] URL added<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 3.2.3: Keep old bank details URL as deprecated redirect

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 3.2.2 |
| **Acceptance Criteria** | - Old `core/urls.py` bank details URL returns 301/302 to new URL<br>- Redirect is logged |
| **Risk Level** | Medium |
| **Testing Requirements** | - Redirect tests |
| **Rollback Requirement** | Remove redirect. Old view becomes active. |
| **Definition of Done** | - [ ] Redirect implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 3.3: Remove duplicate services from rentsecure_be

**User Story:** As a platform engineer, I want duplicate payment services removed from `rentsecure_be/` so that there is a single source of truth in `payments/`.

### Technical Task 3.3.1: Remove rentsecure_be/services/cashfree_service.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 3.1.1, 3.1.2 |
| **Acceptance Criteria** | - `rentsecure_be/services/cashfree_service.py` removed<br>- All imports updated to `payments/` equivalents<br>- No imports of `rentsecure_be.services.cashfree_service` remain |
| **Risk Level** | High |
| **Testing Requirements** | - All payment tests pass<br>- Import-linter check passes<br>- No circular dependencies |
| **Rollback Requirement** | Restore file from git. Revert imports. |
| **Definition of Done** | - [ ] File removed<br>- [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 3.3.2: Remove rentsecure_be/services/razorpay_service.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 3.1.1 |
| **Acceptance Criteria** | - `rentsecure_be/services/razorpay_service.py` removed<br>- All imports updated<br>- No imports remain |
| **Risk Level** | High |
| **Testing Requirements** | - All payment tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Restore file from git. Revert imports. |
| **Definition of Done** | - [ ] File removed<br>- [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 3.3.3: Remove rentsecure_be/services/leegality_service.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 3.1.1 |
| **Acceptance Criteria** | - `rentsecure_be/services/leegality_service.py` removed<br>- All imports updated to `smartbot/services/leegality_service.py`<br>- No imports of `rentsecure_be.services.leegality_service` remain |
| **Risk Level** | Medium |
| **Testing Requirements** | - All Leegality tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Restore file from git. Revert imports. |
| **Definition of Done** | - [ ] File removed<br>- [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 3.3.4: Remove rentsecure_be/utils/cashfree_payout.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 0.5 hours |
| **Dependencies** | Phase -1 (already moved) |
| **Acceptance Criteria** | - `rentsecure_be/utils/cashfree_payout.py` removed (moved to `payments/adapters/cashfree_client.py` in Phase -1)<br>- No imports remain |
| **Risk Level** | Low |
| **Testing Requirements** | - All Cashfree tests pass |
| **Rollback Requirement** | Restore file from git. |
| **Definition of Done** | - [ ] File removed<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 3.3.5: Move export_utils.py to properties or dashboard

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | Phase 2 complete |
| **Acceptance Criteria** | - `rentsecure_be/utils/export_utils.py` moved to `properties/utils/` or `dashboard/utils/`<br>- All imports updated<br>- No imports of `rentsecure_be.utils.export_utils` remain |
| **Risk Level** | Medium |
| **Testing Requirements** | - All export tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Restore file to `rentsecure_be/utils/`. Revert imports. |
| **Definition of Done** | - [ ] File moved<br>- [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 3.4: Update core/views/bank_views.py

**User Story:** As a developer, I want `core/views/bank_views.py` to delegate to `payments/` so that bank details views are deprecated but functional during transition.

### Technical Task 3.4.1: Update bank_views.py to delegate to payments

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 3.2.1 |
| **Acceptance Criteria** | - `core/views/bank_views.py` delegates to `payments/views/bank_details_views.py`<br>- Deprecated warning emitted<br>- Functionality preserved |
| **Risk Level** | Medium |
| **Testing Requirements** | - Integration tests for bank details endpoints<br>- Regression tests |
| **Rollback Requirement** | Revert to original implementation. |
| **Definition of Done** | - [ ] Delegation implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 3.5: Update core/urls.py with payment redirects

**User Story:** As a developer, I want old payment URLs in `core/urls.py` to redirect to `payments/` so that existing clients continue to work during transition.

### Technical Task 3.5.1: Add payment URL redirects to core/urls.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 3.2.2 |
| **Acceptance Criteria** | - Old bank details URL redirects to `payments/` URL<br>- Redirect returns 301/302<br>- Redirect is logged |
| **Risk Level** | Medium |
| **Testing Requirements** | - Redirect tests |
| **Rollback Requirement** | Remove redirects. Old views become active. |
| **Definition of Done** | - [ ] Redirects implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 3.6: Update all cross-app payment imports

**User Story:** As a developer, I want all cross-app payment imports updated so that no app imports payment logic from `core/` or `rentsecure_be/`.

### Technical Task 3.6.1: Update cross-app payment imports

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 6 hours |
| **Dependencies** | 3.1, 3.2, 3.3 |
| **Acceptance Criteria** | - All imports of `core.services.bank_details_service` updated to `payments/services/bank_details_service.py`<br>- All imports of `rentsecure_be.services.cashfree_service` updated to `payments/` equivalents<br>- All imports of `rentsecure_be.services.razorpay_service` updated to `payments/` equivalents<br>- No old imports remain |
| **Risk Level** | High |
| **Testing Requirements** | - All affected tests pass<br>- Import-linter check passes<br>- No circular dependencies |
| **Rollback Requirement** | Revert imports. |
| **Definition of Done** | - [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 3.7: Update documentation

**User Story:** As a developer, I want payment documentation updated so that it reflects the new payment service location.

### Technical Task 3.7.1: Update payment architecture documentation

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 3.1, 3.2, 3.3 |
| **Acceptance Criteria** | - `docs/architecture/contexts/payment.md` updated<br>- Service ownership documented<br>- API interfaces documented<br>- Webhook URLs documented |
| **Risk Level** | Low |
| **Testing Requirements** | - Documentation Guardian passes |
| **Rollback Requirement** | Revert documentation changes. |
| **Definition of Done** | - [ ] Documentation updated<br>- [ ] Guardian passes |

---

## Phase 3 Milestones

| Milestone | Criteria | Date |
|-----------|----------|------|
| M3.1 | `payments/services/webhook_service.py` created | Week 10, Day 2 |
| M3.2 | `payments/services/bank_details_service.py` created | Week 10, Day 3 |
| M3.3 | Bank details views moved to payments | Week 11, Day 1 |
| M3.4 | Duplicate services removed from rentsecure_be | Week 11, Day 3 |
| M3.5 | All cross-app imports updated | Week 12, Day 2 |
| M3.6 | Phase 3 complete | Week 12, Day 5 |

---

# Phase 4: Extract Dashboard & Notification

**Epic:** Phase 4: Extract Dashboard & Notification
**Duration:** Week 13-14
**Goal:** Move reporting out of `core/` and isolate notification concerns
**Risk:** Low

---

## Feature 4.1: Create dashboard services

**User Story:** As a developer, I want `dashboard/services/` so that reporting logic has a clear home outside `core/`.

### Technical Task 4.1.1: Create dashboard/services/ package structure

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | Phase 3 complete |
| **Acceptance Criteria** | - `dashboard/services/__init__.py` exists<br>- Directory structure ready |
| **Risk Level** | Low |
| **Testing Requirements** | - Import tests |
| **Rollback Requirement** | Remove directory. |
| **Definition of Done** | - [ ] Package created<br>- [ ] CI passes |

### Technical Task 4.1.2: Move OwnerReportingService to dashboard/services/

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 4.1.1 |
| **Acceptance Criteria** | - `dashboard/services/owner_reporting_service.py` contains full implementation<br>- All functionality preserved<br>- All tests pass |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests for `OwnerReportingService`<br>- Integration tests for reporting flows<br>- All existing reporting tests pass |
| **Rollback Requirement** | Revert PR. `core/services/owner_reporting_service.py` remains. |
| **Definition of Done** | - [ ] Service moved<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 4.1.3: Add dashboard service tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 4.1.2 |
| **Acceptance Criteria** | - Unit tests for `OwnerReportingService`<br>- Integration tests for reporting flows<br>- Coverage ≥90% |
| **Risk Level** | Low |
| **Testing Requirements** | - Unit tests with mocks<br>- Integration tests |
| **Rollback Requirement** | Remove test files. |
| **Definition of Done** | - [ ] Tests created<br>- [ ] Coverage ≥90%<br>- [ ] CI passes |

---

## Feature 4.2: Move reporting views to dashboard

**User Story:** As a developer, I want reporting views in `dashboard/views/` so that reporting endpoints are in the dashboard bounded context.

### Technical Task 4.2.1: Create dashboard/views/ package structure

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 4.1.2 |
| **Acceptance Criteria** | - `dashboard/views/__init__.py` exists<br>- Directory structure ready |
| **Risk Level** | Low |
| **Testing Requirements** | - Import tests |
| **Rollback Requirement** | Remove directory. |
| **Definition of Done** | - [ ] Package created<br>- [ ] CI passes |

### Technical Task 4.2.2: Move reporting views to dashboard/views/

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 4.2.1 |
| **Acceptance Criteria** | - `dashboard/views/` contains rent inflow summary, rent records, and export views<br>- All reporting endpoints work correctly<br>- Views use `OwnerReportingService` |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests for each view<br>- Integration tests for reporting endpoints<br>- Regression tests |
| **Rollback Requirement** | Revert PR. Views remain in `core/views/reporting_views.py`. |
| **Definition of Done** | - [ ] Views moved<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 4.2.3: Add dashboard URLs to rentsecure_be/urls.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 4.2.2 |
| **Acceptance Criteria** | - `rentsecure_be/urls.py` includes `dashboard/urls.py`<br>- All dashboard endpoints accessible |
| **Risk Level** | Low |
| **Testing Requirements** | - URL resolution tests |
| **Rollback Requirement** | Remove URL include. |
| **Definition of Done** | - [ ] URLs included<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 4.2.4: Keep old reporting URLs as deprecated redirects

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 4.2.3 |
| **Acceptance Criteria** | - Old `core/urls.py` reporting URLs return 301/302 redirects to `dashboard/` URLs<br>- Redirects logged |
| **Risk Level** | Medium |
| **Testing Requirements** | - Redirect tests |
| **Rollback Requirement** | Remove redirects. Old views become active. |
| **Definition of Done** | - [ ] Redirects implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 4.3: Move export utilities to dashboard

**User Story:** As a developer, I want export utilities in `dashboard/utils/` so that report generation logic is in the dashboard bounded context.

### Technical Task 4.3.1: Move export_utils.py to dashboard/utils/

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 4.2.2 |
| **Acceptance Criteria** | - `dashboard/utils/export_utils.py` contains report generation logic<br>- All functionality preserved<br>- All imports updated |
| **Risk Level** | Medium |
| **Testing Requirements** | - Export tests<br>- Import-linter check passes |
| **Rollback Requirement** | Restore file to `rentsecure_be/utils/`. Revert imports. |
| **Definition of Done** | - [ ] File moved<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 4.4: Isolate notification concerns

**User Story:** As a notification engineer, I want domain-specific notification triggers moved to `properties/services/` so that `notification/` contains only channel adapters.

### Technical Task 4.4.1: Move domain notification triggers to properties/services/

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 8 hours |
| **Dependencies** | Phase 3 complete |
| **Acceptance Criteria** | - Domain notification triggers moved from `notification/services/` to `properties/services/`:<br>  - `notify_rent_due` → `properties/services/rent_notification_service.py`<br>  - `notify_payment_received` → `properties/services/payment_notification_service.py`<br>  - `late_fees_notify_service.py` → `properties/services/late_fee_notification_service.py`<br>  - `extra_charge_reminders.py` → `properties/services/extra_charge_notification_service.py`<br>  - `schedule_reminders.py` → `properties/services/reminder_service.py`<br>  - `voice_note_service.py` → `properties/services/voice_notification_service.py`<br>- `notification/` only provides `send_email()`, `send_push()`, `send_whatsapp()`, etc. |
| **Risk Level** | High |
| **Testing Requirements** | - Unit tests for moved services<br>- Integration tests for notification flows<br>- All existing notification tests pass |
| **Rollback Requirement** | Revert PR. Domain logic remains in `notification/services/`. |
| **Definition of Done** | - [ ] Domain triggers moved<br>- [ ] `notification/services/` simplified to adapters only<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 4.4.2: Update notification imports

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 4.4.1 |
| **Acceptance Criteria** | - All apps importing domain notification services from `notification/services/` updated to import from `properties/services/`<br>- No imports of domain notification logic from `notification/services/` remain (except in `notification/` itself) |
| **Risk Level** | High |
| **Testing Requirements** | - All affected tests pass<br>- Import-linter check passes<br>- No circular dependencies |
| **Rollback Requirement** | Revert imports. |
| **Definition of Done** | - [ ] All imports updated<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 4.4.3: Add notification adapter tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | 4.4.1 |
| **Acceptance Criteria** | - `notification/tests/` contains adapter tests<br>- Each adapter (email, FCM, inapp, WhatsApp, SMS) has unit tests<br>- Coverage ≥90% |
| **Risk Level** | Low |
| **Testing Requirements** | - Unit tests with mocks<br>- Integration tests for each channel |
| **Rollback Requirement** | Remove test files. |
| **Definition of Done** | - [ ] Tests created<br>- [ ] Coverage ≥90%<br>- [ ] CI passes |

---

## Feature 4.5: Update core/views/reporting_views.py

**User Story:** As a developer, I want `core/views/reporting_views.py` to delegate to `dashboard/` so that reporting views are deprecated but functional during transition.

### Technical Task 4.5.1: Update reporting_views.py to delegate to dashboard

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 4.2.2 |
| **Acceptance Criteria** | - `core/views/reporting_views.py` delegates to `dashboard/views/`<br>- Deprecated warning emitted<br>- Functionality preserved |
| **Risk Level** | Medium |
| **Testing Requirements** | - Integration tests for reporting endpoints<br>- Regression tests |
| **Rollback Requirement** | Revert to original implementation. |
| **Definition of Done** | - [ ] Delegation implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 4.6: Update core/urls.py with dashboard redirects

**User Story:** As a developer, I want old reporting URLs in `core/urls.py` to redirect to `dashboard/` so that existing clients continue to work during transition.

### Technical Task 4.6.1: Add dashboard URL redirects to core/urls.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 4.2.3 |
| **Acceptance Criteria** | - Old reporting URLs return 301/302 redirects to `dashboard/` URLs<br>- Redirects logged |
| **Risk Level** | Medium |
| **Testing Requirements** | - Redirect tests |
| **Rollback Requirement** | Remove redirects. Old views become active. |
| **Definition of Done** | - [ ] Redirects implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 4.7: Update documentation

**User Story:** As a developer, I want dashboard and notification documentation updated so that it reflects the new service locations.

### Technical Task 4.7.1: Update dashboard documentation

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 4.1, 4.2 |
| **Acceptance Criteria** | - `docs/architecture/contexts/dashboard.md` created or updated<br>- Service ownership documented<br>- API interfaces documented |
| **Risk Level** | Low |
| **Testing Requirements** | - Documentation Guardian passes |
| **Rollback Requirement** | Revert documentation changes. |
| **Definition of Done** | - [ ] Documentation updated<br>- [ ] Guardian passes |

### Technical Task 4.7.2: Update notification documentation

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 4.4 |
| **Acceptance Criteria** | - `docs/architecture/contexts/notification.md` updated<br>- Adapter interfaces documented<br>- Channel configuration documented |
| **Risk Level** | Low |
| **Testing Requirements** | - Documentation Guardian passes |
| **Rollback Requirement** | Revert documentation changes. |
| **Definition of Done** | - [ ] Documentation updated<br>- [ ] Guardian passes |

---

## Phase 4 Milestones

| Milestone | Criteria | Date |
|-----------|----------|------|
| M4.1 | `dashboard/services/` package created | Week 13, Day 1 |
| M4.2 | `OwnerReportingService` moved and tested | Week 13, Day 3 |
| M4.3 | Reporting views moved to dashboard | Week 14, Day 1 |
| M4.4 | Domain notification triggers moved to properties | Week 14, Day 2 |
| M4.5 | Notification adapters simplified | Week 14, Day 3 |
| M4.6 | Phase 4 complete | Week 14, Day 5 |

---

# Phase 5: Deprecate Core

**Epic:** Phase 5: Deprecate Core
**Duration:** Week 15-16
**Goal:** Remove `core/` as a God app — **ONLY BREAKING CHANGE**
**Risk:** High

---

## Feature 5.1: Remove core views

**User Story:** As a developer, I want `core/views/` removed so that all views live in their owning bounded context.

### Technical Task 5.1.1: Remove core/views/ directory

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | Phase 4 complete |
| **Acceptance Criteria** | - `core/views/` directory removed<br>- All functionality accessible via new view locations<br>- Old URLs return 404 (not 500) |
| **Risk Level** | High |
| **Testing Requirements** | - All view tests pass from new locations<br>- 404 validation tests for old URLs<br>- Integration tests |
| **Rollback Requirement** | **Full rollback required.** Restore `core/views/` from v1.x LTS branch. Redeploy previous version. Estimated 2-4 hours. |
| **Definition of Done** | - [ ] Views removed<br>- [ ] 404 tests pass<br>- [ ] Integration tests pass<br>- [ ] CI passes<br>- [ ] PR approved by 2-of-3 board |

### Technical Task 5.1.2: Verify no core/ view imports remain

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 5.1.1 |
| **Acceptance Criteria** | - No imports of `core.views.*` remain in app code<br>- AST scan confirms no `core.views` imports |
| **Risk Level** | High |
| **Testing Requirements** | - Import-linter check passes<br>- Architecture tests pass |
| **Rollback Requirement** | Restore `core/views/`. Update imports. |
| **Definition of Done** | - [ ] No imports remain<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 5.2: Remove core models (non-identity)

**User Story:** As a developer, I want non-identity models removed from `core/models.py` so that `core/` contains only `User`, `UserProfile`, and `OTP`.

### Technical Task 5.2.1: Remove OwnerBankDetails from core/models.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 0.5 hours |
| **Dependencies** | Phase 0 complete (already moved) |
| **Acceptance Criteria** | - `OwnerBankDetails` removed from `core/models.py`<br>- No references remain |
| **Risk Level** | High |
| **Testing Requirements** | - All payment tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Restore `core/models.py` version. |
| **Definition of Done** | - [ ] Model removed<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 5.2.2: Remove NotificationPreference from core/models.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 0.5 hours |
| **Dependencies** | Phase 0 complete (already moved) |
| **Acceptance Criteria** | - `NotificationPreference` removed from `core/models.py`<br>- No references remain |
| **Risk Level** | High |
| **Testing Requirements** | - All notification tests pass |
| **Rollback Requirement** | Restore `core/models.py` version. |
| **Definition of Done** | - [ ] Model removed<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 5.2.3: Remove subscription models from core/models.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | Phase 2 complete (already moved) |
| **Acceptance Criteria** | - `SubscriptionPlan`, `UserSubscription`, `AddOnPurchase`, `PlanFeatureLimit`, `UsageLimit` removed from `core/models.py`<br>- No references remain |
| **Risk Level** | High |
| **Testing Requirements** | - All subscription tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | Restore `core/models.py` version. |
| **Definition of Done** | - [ ] Models removed<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 5.2.4: Create data migration to delete core subscription tables

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 3 hours |
| **Dependencies** | 5.2.3 |
| **Acceptance Criteria** | - Migration drops `core_subscription*` tables<br>- Migration is irreversible<br>- Migration tested on production copy |
| **Risk Level** | High |
| **Testing Requirements** | - Forward migration test<br>- Data integrity verification<br>- Test on production-like data |
| **Rollback Requirement** | Restore from backup. Cannot reverse migration. |
| **Definition of Done** | - [ ] Migration created<br>- [ ] Forward test passes<br>- [ ] Data integrity verified<br>- [ ] CI passes |

---

## Feature 5.3: Remove core services

**User Story:** As a developer, I want `core/services/` removed so that all services live in their owning bounded context.

### Technical Task 5.3.1: Remove core/services/ directory

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 5.2 |
| **Acceptance Criteria** | - `core/services/` directory removed (or empty)<br>- All services moved to their owning apps<br>- No imports of `core.services.*` remain |
| **Risk Level** | High |
| **Testing Requirements** | - All tests pass<br>- Import-linter check passes |
| **Rollback Requirement** | **Full rollback required.** Restore `core/services/` from v1.x LTS branch. |
| **Definition of Done** | - [ ] Services removed<br>- [ ] No imports remain<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 5.4: Remove core/urls.py

**User Story:** As a developer, I want `core/urls.py` removed so that all URLs are defined in their owning app or `rentsecure_be/urls.py`.

### Technical Task 5.4.1: Remove core/urls.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 5.1, 5.2, 5.3 |
| **Acceptance Criteria** | - `core/urls.py` removed<br>- `rentsecure_be/urls.py` does not include `core/urls.py`<br>- All URLs accessible via new locations |
| **Risk Level** | High |
| **Testing Requirements** | - URL resolution tests<br>- 404 validation tests for old URLs |
| **Rollback Requirement** | **Full rollback required.** Restore `core/urls.py` from v1.x LTS branch. |
| **Definition of Done** | - [ ] File removed<br>- [ ] URLs work from new locations<br>- [ ] Old URLs return 404<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 5.5: Update rentsecure_be/urls.py

**User Story:** As a developer, I want `rentsecure_be/urls.py` updated so that it no longer includes `core/urls.py`.

### Technical Task 5.5.1: Remove core/ URL includes from rentsecure_be/urls.py

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 5.4.1 |
| **Acceptance Criteria** | - `rentsecure_be/urls.py` does not include `core/urls.py`<br>- All URLs defined in `rentsecure_be/urls.py` or app `urls.py` files |
| **Risk Level** | High |
| **Testing Requirements** | - URL resolution tests<br>- Integration tests |
| **Rollback Requirement** | **Full rollback required.** Restore `core/urls.py` and re-add include. |
| **Definition of Done** | - [ ] URL includes removed<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 5.6: Create migration guide

**User Story:** As a developer integrating with RentSecureBE, I want a migration guide so that I can update my code for v2.0.0.

### Technical Task 5.6.1: Create docs/migration/v1-to-v2.md

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 5.1, 5.2, 5.3, 5.4 |
| **Acceptance Criteria** | - `docs/migration/v1-to-v2.md` exists<br>- Document lists all breaking changes<br>- Document provides before/after code examples for each change<br>- Document includes timeline and support contacts |
| **Risk Level** | Medium |
| **Testing Requirements** | - Documentation review<br>- Link validation |
| **Rollback Requirement** | N/A (documentation only) |
| **Definition of Done** | - [ ] Guide created<br>- [ ] Reviewed by team<br>- [ ] Published with v2.0.0 release |

### Technical Task 5.6.2: Update README.md with breaking changes

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 5.6.1 |
| **Acceptance Criteria** | - `README.md` updated with v2.0.0 breaking changes<br>- Migration guide linked<br>- Changelog updated |
| **Risk Level** | Low |
| **Testing Requirements** | - Documentation Guardian passes |
| **Rollback Requirement** | Revert README changes. |
| **Definition of Done** | - [ ] README updated<br>- [ ] Guardian passes |

---

## Feature 5.7: Create ADR for Phase 5 breaking changes

**User Story:** As an architect, I want an ADR documenting the Phase 5 breaking changes so that the decision is recorded and justified.

### Technical Task 5.7.1: Create ADR for Phase 5 breaking changes

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | 5.1, 5.2, 5.3, 5.4 |
| **Acceptance Criteria** | - ADR created in `docs/architecture/adr/`<br>- ADR documents why breaking changes were necessary<br>- ADR documents alternatives considered<br>- ADR is approved by 2-of-3 board |
| **Risk Level** | Low |
| **Testing Requirements** | - ADR review |
| **Rollback Requirement** | N/A (documentation only) |
| **Definition of Done** | - [ ] ADR created<br>- [ ] Approved by board<br>- [ ] Published |

---

## Phase 5 Milestones

| Milestone | Criteria | Date |
|-----------|----------|------|
| M5.1 | `core/views/` removed | Week 15, Day 2 |
| M5.2 | Non-identity models removed from `core/models.py` | Week 15, Day 3 |
| M5.3 | `core/services/` removed | Week 15, Day 4 |
| M5.4 | `core/urls.py` removed | Week 16, Day 1 |
| M5.5 | `rentsecure_be/urls.py` updated | Week 16, Day 1 |
| M5.6 | Migration guide published | Week 16, Day 2 |
| M5.7 | ADR created and approved | Week 16, Day 2 |
| M5.8 | v2.0.0 released | Week 16, Day 5 |

---

# Phase 6: Optimization

**Epic:** Phase 6: Optimization
**Duration:** Week 17-20
**Goal:** Add event bus, repositories, Redis cache, and consolidate AI modules
**Risk:** Low

---

## Feature 6.1: Implement event bus

**User Story:** As a developer, I want an in-process event bus so that services can communicate without direct dependencies.

### Technical Task 6.1.1: Implement InProcessEventBus

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 6 hours |
| **Dependencies** | Phase 5 complete |
| **Acceptance Criteria** | - `platform/events/event_bus.py` contains `EventBus` implementation<br>- EventBus supports publish/subscribe<br>- EventBus supports middleware<br>- EventBus is thread-safe |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests for EventBus<br>- Integration tests for event flows<br>- Thread safety tests |
| **Rollback Requirement** | Remove `platform/events/`. Services revert to direct calls. |
| **Definition of Done** | - [ ] EventBus implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 6.1.2: Implement event middleware

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 6.1.1 |
| **Acceptance Criteria** | - `platform/events/middleware.py` contains logging, retry, and dead-letter queue middleware<br>- Middleware is configurable<br>- Middleware tests pass |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests for middleware<br>- Integration tests |
| **Rollback Requirement** | Remove middleware. EventBus operates without middleware. |
| **Definition of Done** | - [ ] Middleware implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 6.1.3: Define domain events for all contexts

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 6 hours |
| **Dependencies** | 6.1.1 |
| **Acceptance Criteria** | - Domain events defined for all contexts in `shared/domain_events.py` and context-specific `events.py` files<br>- Events include: `UserCreated`, `SubscriptionCreated`, `PaymentSubmitted`, `PaymentApproved`, `RentRecordCreated`, etc.<br>- Events are typed and documented |
| **Risk Level** | Low |
| **Testing Requirements** | - Event schema tests<br>- Event serialization tests |
| **Rollback Requirement** | Remove event definitions. |
| **Definition of Done** | - [ ] Events defined<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 6.1.4: Integrate event bus with services

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 8 hours |
| **Dependencies** | 6.1.3 |
| **Acceptance Criteria** | - Services publish events for key actions (user created, payment approved, etc.)<br>- Event handlers subscribed to relevant events<br>- No circular dependencies introduced |
| **Risk Level** | Medium |
| **Testing Requirements** | - Integration tests for event flows<br>- All existing tests pass |
| **Rollback Requirement** | Remove event publishing from services. Revert to direct calls. |
| **Definition of Done** | - [ ] Events integrated<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 6.2: Add repositories for complex queries

**User Story:** As a developer, I want repositories for complex queries so that query logic is centralized and reusable.

### Technical Task 6.2.1: Create properties/repositories/ package

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | Phase 5 complete |
| **Acceptance Criteria** | - `properties/repositories/__init__.py` exists<br>- Directory structure ready |
| **Risk Level** | Low |
| **Testing Requirements** | - Import tests |
| **Rollback Requirement** | Remove directory. |
| **Definition of Done** | - [ ] Package created<br>- [ ] CI passes |

### Technical Task 6.2.2: Implement OwnerReportingRepository

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 6.2.1 |
| **Acceptance Criteria** | - `properties/repositories/owner_reporting_repository.py` contains complex aggregation queries<br>- Repository used by `OwnerReportingService`<br>- Repository has unit tests |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests with test database<br>- Query count tests |
| **Rollback Requirement** | Remove repository. `OwnerReportingService` uses ORM directly. |
| **Definition of Done** | - [ ] Repository implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 6.2.3: Implement RentRecordRepository

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 6.2.1 |
| **Acceptance Criteria** | - `properties/repositories/rent_record_repository.py` contains complex queries for rent records<br>- Repository used by relevant services<br>- Repository has unit tests |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests with test database<br>- Query count tests |
| **Rollback Requirement** | Remove repository. Services use ORM directly. |
| **Definition of Done** | - [ ] Repository implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 6.2.4: Create dashboard/repositories/ package

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 6.2.1 |
| **Acceptance Criteria** | - `dashboard/repositories/__init__.py` exists<br>- Directory structure ready |
| **Risk Level** | Low |
| **Testing Requirements** | - Import tests |
| **Rollback Requirement** | Remove directory. |
| **Definition of Done** | - [ ] Package created<br>- [ ] CI passes |

### Technical Task 6.2.5: Implement DashboardMetricRepository

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 6.2.4 |
| **Acceptance Criteria** | - `dashboard/repositories/dashboard_metric_repository.py` contains metric aggregation queries<br>- Repository used by `OwnerReportingService`<br>- Repository has unit tests |
| **Risk Level** | Medium |
| **Testing Requirements** | - Unit tests with test database<br>- Query count tests |
| **Rollback Requirement** | Remove repository. Service uses ORM directly. |
| **Definition of Done** | - [ ] Repository implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 6.3: Add Redis cache backend

**User Story:** As a DevOps engineer, I want a Redis cache backend available so that we can scale beyond a single Gunicorn worker.

### Technical Task 6.3.1: Implement RedisCache backend

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | Phase 5 complete |
| **Acceptance Criteria** | - `platform/cache/redis.py` contains `RedisCache` implementation<br>- Implementation uses `django-redis`<br>- Implementation is swappable via settings |
| **Risk Level** | Low |
| **Testing Requirements** | - Unit tests for Redis cache<br>- Integration tests with Redis (testcontainer) |
| **Rollback Requirement** | Remove `platform/cache/redis.py`. Continue using LocMemCache. |
| **Definition of Done** | - [ ] Redis backend implemented<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 6.3.2: Add CACHE_BACKEND setting

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | 6.3.1 |
| **Acceptance Criteria** | - `rentsecure_be/settings/base.py` contains `CACHE_BACKEND` setting<br>- Setting defaults to `locmem`<br>- Setting can be switched to `redis` via environment variable |
| **Risk Level** | Low |
| **Testing Requirements** | - Settings tests<br>- Integration tests |
| **Rollback Requirement** | Remove setting. Default to LocMemCache. |
| **Definition of Done** | - [ ] Setting added<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 6.4: Consolidate AI modules

**User Story:** As a developer, I want `ai_assistant/` and `smartbot/` consolidated or removed so that AI code has a clear home.

### Technical Task 6.4.1: Audit ai_assistant/ and smartbot/

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | Phase 5 complete |
| **Acceptance Criteria** | - Inventory of all code in `ai_assistant/` and `smartbot/`<br>- Identification of duplicates<br>- Identification of dead code<br>- Consolidation plan created |
| **Risk Level** | Medium |
| **Testing Requirements** | - None (audit only) |
| **Rollback Requirement** | N/A |
| **Definition of Done** | - [ ] Audit complete<br>- [ ] Consolidation plan approved by Staff Engineer |

### Technical Task 6.4.2: Consolidate or remove ai_assistant/

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 8 hours |
| **Dependencies** | 6.4.1 |
| **Acceptance Criteria** | - `ai_assistant/` either:<br>  - Consolidated into `smartbot/` or `ai/`, OR<br>  - Removed if dead code<br>- No functional regressions |
| **Risk Level** | High |
| **Testing Requirements** | - All AI-related tests pass<br>- Regression tests |
| **Rollback Requirement** | Restore `ai_assistant/` from git. |
| **Definition of Done** | - [ ] Consolidation or removal complete<br>- [ ] Tests pass<br>- [ ] CI passes |

### Technical Task 6.4.3: Remove dead code from smartbot/

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 6.4.2 |
| **Acceptance Criteria** | - Dead code identified in audit removed<br>- Duplicate implementations consolidated<br>- No functional regressions |
| **Risk Level** | Medium |
| **Testing Requirements** | - All smartbot tests pass |
| **Rollback Requirement** | Restore removed code from git. |
| **Definition of Done** | - [ ] Dead code removed<br>- [ ] Tests pass<br>- [ ] CI passes |

---

## Feature 6.5: Document bounded context APIs

**User Story:** As a developer, I want bounded context APIs documented so that I can understand how to interact with each context.

### Technical Task 6.5.1: Create docs/architecture/contexts/ documentation

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 6 hours |
| **Dependencies** | Phase 5 complete |
| **Acceptance Criteria** | - `docs/architecture/contexts/` contains one markdown file per context:<br>  - `identity.md`<br>  - `subscription.md`<br>  - `property.md`<br>  - `payment.md`<br>  - `notification.md`<br>  - `document.md`<br>  - `finance.md`<br>  - `referral.md`<br>  - `dashboard.md`<br>- Each document includes: ownership, responsibilities, public APIs, dependencies, data model |
| **Risk Level** | Low |
| **Testing Requirements** | - Documentation Guardian passes<br>- Link validation |
| **Rollback Requirement** | Remove documentation. |
| **Definition of Done** | - [ ] All context docs created<br>- [ ] Guardian passes<br>- [ ] Reviewed by app owners |

### Technical Task 6.5.2: Create API reference documentation

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 6.5.1 |
| **Acceptance Criteria** | - `docs/api/` contains API reference for each context<br>- Endpoints documented with request/response examples<br>- Authentication requirements documented |
| **Risk Level** | Low |
| **Testing Requirements** | - Documentation Guardian passes |
| **Rollback Requirement** | Remove documentation. |
| **Definition of Done** | - [ ] API docs created<br>- [ ] Guardian passes |

---

## Feature 6.6: Add performance benchmarks

**User Story:** As a DevOps engineer, I want performance benchmarks so that we can detect performance regressions.

### Technical Task 6.6.1: Create tests/performance/ package

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 1 hour |
| **Dependencies** | Phase 5 complete |
| **Acceptance Criteria** | - `tests/performance/__init__.py` exists<br>- Directory structure ready |
| **Risk Level** | Low |
| **Testing Requirements** | - Import tests |
| **Rollback Requirement** | Remove directory. |
| **Definition of Done** | - [ ] Package created<br>- [ ] CI passes |

### Technical Task 6.6.2: Implement query count tests

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 6.6.1 |
| **Acceptance Criteria** | - `tests/performance/test_query_count.py` exists<br>- Test asserts max 10 queries per view<br>- Test runs nightly in CI |
| **Risk Level** | Medium |
| **Testing Requirements** | - Query count tests<br>- Performance regression tests |
| **Rollback Requirement** | Remove test file. |
| **Definition of Done** | - [ ] Tests created<br>- [ ] Nightly CI job configured<br>- [ ] CI passes |

### Technical Task 6.6.3: Implement Locust load tests

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 4 hours |
| **Dependencies** | 6.6.1 |
| **Acceptance Criteria** | - `tests/performance/locustfile.py` exists<br>- Load tests cover critical endpoints<br>- Tests assert p95 < 200ms |
| **Risk Level** | Medium |
| **Testing Requirements** | - Load tests against staging environment |
| **Rollback Requirement** | Remove load tests. |
| **Definition of Done** | - [ ] Load tests created<br>- [ ] Tests pass on staging<br>- [ ] CI configured |

---

## Phase 6 Milestones

| Milestone | Criteria | Date |
|-----------|----------|------|
| M6.1 | Event bus implemented | Week 17, Day 3 |
| M6.2 | Domain events defined and integrated | Week 18, Day 2 |
| M6.3 | Repositories implemented | Week 18, Day 5 |
| M6.4 | Redis cache backend available | Week 19, Day 2 |
| M6.5 | AI modules consolidated | Week 19, Day 4 |
| M6.6 | Context documentation complete | Week 20, Day 2 |
| M6.7 | Performance benchmarks established | Week 20, Day 4 |
| M6.8 | Phase 6 complete | Week 20, Day 5 |

---

# Cross-Cutting Tasks

These tasks span multiple phases and are tracked separately.

## Epic: CI/CD and DevOps

### Technical Task CD-1: Maintain CI pipeline health

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | Ongoing |
| **Dependencies** | All phases |
| **Acceptance Criteria** | - CI pipeline passes on every commit<br>- No flaky tests<br>- Pipeline runtime < 15 minutes |
| **Risk Level** | Medium |
| **Testing Requirements** | - CI pipeline monitoring |
| **Rollback Requirement** | Revert failing commit. |
| **Definition of Done** | - [ ] CI green on all branches |

### Technical Task CD-2: Maintain staging environment

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | Ongoing |
| **Dependencies** | All phases |
| **Acceptance Criteria** | - Staging environment mirrors production<br>- Staging deploys on every phase branch merge<br>- Staging validation passed before production deploy |
| **Risk Level** | Medium |
| **Testing Requirements** | - Staging smoke tests |
| **Rollback Requirement** | Redeploy previous stable version. |
| **Definition of Done** | - [ ] Staging healthy |

### Technical Task CD-3: Maintain production environment

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | Ongoing |
| **Dependencies** | All phases |
| **Acceptance Criteria** | - Production deployments successful<br>- No downtime during deployments<br>- Monitoring and alerting functional |
| **Risk Level** | High |
| **Testing Requirements** | - Production smoke tests<br>- Monitoring dashboards |
| **Rollback Requirement** | Blue-green switch to previous version. |
| **Definition of Done** | - [ ] Production healthy |

---

## Epic: Security

### Technical Task SEC-1: Conduct security review per phase

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 4 hours per phase |
| **Dependencies** | Each phase |
| **Acceptance Criteria** | - Security review conducted before phase merge<br>- No high/medium vulnerabilities in Bandit scan<br>- No critical vulnerabilities in Safety scan<br>- Encryption verified |
| **Risk Level** | High |
| **Testing Requirements** | - Bandit scan<br>- Safety scan<br>- Manual security review |
| **Rollback Requirement** | Address vulnerabilities before merging. |
| **Definition of Done** | - [ ] Security review passed<br>- [ ] No high/medium vulnerabilities |

### Technical Task SEC-2: Rotate secrets after Phase 5

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours |
| **Dependencies** | Phase 5 complete |
| **Acceptance Criteria** | - All secrets rotated after v2.0.0 deployment<br>- Old secrets invalidated<br>- New secrets distributed securely |
| **Risk Level** | High |
| **Testing Requirements** | - Secret rotation test<br>- Application functionality test |
| **Rollback Requirement** | Keep old secrets valid until new secrets confirmed working. |
| **Definition of Done** | - [ ] Secrets rotated<br>- [ ] Application healthy |

---

## Epic: Documentation

### Technical Task DOC-1: Update architecture documentation per phase

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 2 hours per phase |
| **Dependencies** | Each phase |
| **Acceptance Criteria** | - Architecture documentation updated after each phase<br>- Context diagrams updated<br>- Dependency matrix updated<br>- Documentation Guardian passes |
| **Risk Level** | Low |
| **Testing Requirements** | - Documentation Guardian |
| **Rollback Requirement** | Revert documentation changes. |
| **Definition of Done** | - [ ] Documentation updated<br>- [ ] Guardian passes |

### Technical Task DOC-2: Maintain CHANGELOG.md

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 1 hour per release |
| **Dependencies** | Each release |
| **Acceptance Criteria** | - `CHANGELOG.md` updated for every release<br>- Changes categorized (Added, Changed, Fixed, Removed)<br>- Breaking changes highlighted |
| **Risk Level** | Low |
| **Testing Requirements** | - None |
| **Rollback Requirement** | Revert CHANGELOG changes. |
| **Definition of Done** | - [ ] CHANGELOG updated |

---

## Epic: Risk Management

### Technical Task RM-1: Conduct rollback drill per phase

| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Estimated Effort** | 2 hours per phase |
| **Dependencies** | Each phase |
| **Acceptance Criteria** | - Rollback drill performed on staging before production deploy<br>- Rollback procedure documented and tested<br>- Rollback time measured and within acceptable limits |
| **Risk Level** | High |
| **Testing Requirements** | - Rollback drill<br>- Smoke tests after rollback |
| **Rollback Requirement** | N/A (this IS the rollback test) |
| **Definition of Done** | - [ ] Drill performed<br>- [ ] Rollback time acceptable<br>- [ ] Rollback runbook updated |

### Technical Task RM-2: Update risk register weekly

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Estimated Effort** | 1 hour per week |
| **Dependencies** | All phases |
| **Acceptance Criteria** | - Risk register reviewed weekly<br>- New risks identified and assessed<br>- Mitigations updated |
| **Risk Level** | Medium |
| **Testing Requirements** | - None |
| **Rollback Requirement** | N/A |
| **Definition of Done** | - [ ] Risk register updated |

---

# Summary

## Total Task Count by Type

| Type | Count |
|------|-------|
| **Epics** | 9 (Phase -1 through Phase 6, plus 3 cross-cutting) |
| **Features** | 35+ |
| **User Stories** | 70+ |
| **Technical Tasks** | 150+ |
| **Subtasks** | Included in Technical Tasks |

## Total Task Count by Phase

| Phase | Technical Tasks | Subtasks |
|-------|-----------------|----------|
| Phase -1 | 8 | 0 |
| Phase 0 | 15 | 0 |
| Phase 1 | 15 | 0 |
| Phase 2 | 12 | 0 |
| Phase 3 | 15 | 0 |
| Phase 4 | 15 | 0 |
| Phase 5 | 12 | 0 |
| Phase 6 | 15 | 0 |
| **Total** | **107** | **0** |

## Total Estimated Effort

| Phase | Estimated Hours |
|-------|-----------------|
| Phase -1 | 20 hours |
| Phase 0 | 80 hours |
| Phase 1 | 60 hours |
| Phase 2 | 50 hours |
| Phase 3 | 70 hours |
| Phase 4 | 70 hours |
| Phase 5 | 40 hours |
| Phase 6 | 80 hours |
| Cross-cutting | 100 hours |
| **Total** | **~570 hours** |

## Import Instructions

### GitHub Projects

```yaml
# Import via CSV
Title,Description,Status,Priority,Labels,Estimate,Due Date
"Phase -1: Move type_compat","Move type_compat.py to shared/","Ready","P0","phase--1,backend","4h","2026-07-26"
```

### Jira

```json
{
  "projects": [
    {
      "name": "RentSecureBE Architecture",
      "key": "RSA",
      "epics": [
        {
          "name": "Phase -1: Break Circular Dependencies",
          "features": [
            {
              "name": "Move type_compat to shared",
              "stories": [
                {
                  "name": "Move type_compat.py",
                  "priority": "P0",
                  "estimate": "4h"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Linear

```yaml
# Linear import format
- name: Phase -1: Break Circular Dependencies
  description: Epic for Phase -1
  priority: 0
  children:
    - name: Feature -1.1: Move type_compat to shared
      children:
        - name: Task -1.1.1: Move type_compat.py
          priority: 0
          estimate: 4h
```

---

*End of Engineering Backlog*

**Prepared by:** Principal Software Architect
**Date:** 2026-07-19
**Next Review:** Weekly during implementation
**Approval Required:** Staff Engineer, Platform Team Lead, Product Team Lead, Security Lead, DevOps Engineer, QA Lead
