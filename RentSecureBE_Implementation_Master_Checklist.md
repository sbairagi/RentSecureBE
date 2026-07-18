# RentSecureBE Implementation Master Checklist

**Version:** 1.0.0
**Date:** 2026-07-18
**Status:** APPROVED FOR EXECUTION
**Source of Truth:** Approved Final Architecture Audit & Decision document
**Constraint:** No redesign. No new patterns. No rejected patterns. Execute only.

---

## Document Conventions

| Symbol | Meaning |
|--------|---------|
| ⬜ | Not Started |
| 🟨 | In Progress |
| 🟩 | Complete |
| P0 | Critical — blocks other work |
| P1 | High — core path |
| P2 | Medium — can be parallelized |

---

## Pre-Implementation

### Objectives
Validate environment, freeze baselines, and confirm Phase 1.3 certification before any code changes.

### Entry Criteria
- Phase 1.3 Migration Readiness Certification is COMPLETE
- Documentation Guardian exits 0
- Zero active broken links in canonical docs
- CI pipeline is green on `main`

### Exit Criteria
- All pre-implementation checks pass
- Branch strategy and tagging scheme agreed
- Rollback runbook reviewed

### Deliverables
- Pre-implementation checklist signed off
- Branch protection config verified
- Rollback runbook stored at `docs/archive/runbooks/`

### Success Metrics
- 100% of pre-implementation checks green
- Zero open blockers

### Pre-Implementation Tasks

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| PRE-1 | Verify Phase 1.3 certification artifacts | P0 | 2h | Low | ⬜ |
| PRE-2 | Freeze ADR set — no new ADRs during implementation | P0 | 1h | Low | ⬜ |
| PRE-3 | Confirm CI green on main | P0 | 1h | Low | ⬜ |
| PRE-4 | Agree branch naming and PR size limits | P1 | 1h | Low | ⬜ |
| PRE-5 | Document rollback runbook | P1 | 2h | Low | ⬜ |
| PRE-6 | Confirm test command and coverage threshold | P1 | 1h | Low | ⬜ |
| PRE-7 | Verify import-linter baseline | P1 | 1h | Low | ⬜ |

#### PRE-1: Verify Phase 1.3 Certification Artifacts

**Purpose:** Confirm the repository is certified for Phase 2 and that no blocker has emerged since certification.

**Dependencies:** None

**Estimated Effort:** 2 hours

**Estimated Risk:** Low

**Acceptance Criteria**
- `PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md` exists and is marked COMPLETE
- Documentation Guardian exits 0
- Zero broken links in active docs
- CI is green on `main`

**Definition of Done**
- [ ] Certification file exists and is COMPLETE
- [ ] Guardian run exits 0
- [ ] CI main is green

**Rollback Strategy:** N/A — read-only verification

**Files Likely to Change**
- None (read-only)

**Testing Requirements**
- None (verification only)

**Security Considerations**
- None

**Documentation Updates Required**
- None

**Git Commit Recommendation**
- N/A — verification only

---

#### PRE-2: Freeze ADR Set

**Purpose:** Prevent architectural drift during implementation. No new ADRs may be opened without Architecture Review Board approval.

**Dependencies:** None

**Estimated Effort:** 1 hour

**Estimated Risk:** Low

**Acceptance Criteria**
- ADR freeze announced in team channel
- ADR template marked FROZEN in `docs/architecture/adr/README.md` (canonical collection)
- All team members acknowledge freeze

**Definition of Done**
- [ ] ADR freeze communicated
- [ ] Template updated with FROZEN banner
- [ ] Team acknowledgment recorded

**Rollback Strategy:** Lift freeze via Architecture Review Board decision

**Files Likely to Change**
- `docs/architecture/adr/README.md` — add FROZEN notice to canonical ADR index
- `architecture/adr/000-template.md` — add FROZEN notice to legacy template (historical)

**Testing Requirements**
- None

**Security Considerations**
- None

**Documentation Updates Required**
- `README.md` — add ADR freeze notice

**Git Commit Recommendation**
```
chore(architecture): freeze ADR set for implementation phase
```

---

#### PRE-3: Confirm CI Green on Main

**Purpose:** Establish baseline before any implementation work begins.

**Dependencies:** None

**Estimated Effort:** 1 hour

**Estimated Risk:** Low

**Acceptance Criteria**
- All required CI jobs pass on `main`
- No flaky tests detected in last 10 runs
- Architecture guard passes

**Definition of Done**
- [ ] CI dashboard screenshot archived
- [ ] Flaky tests documented (if any)
- [ ] Baseline CI health confirmed

**Rollback Strategy:** N/A — read-only verification

**Files Likely to Change**
- None

**Testing Requirements**
- None

**Security Considerations**
- None

**Documentation Updates Required**
- None

**Git Commit Recommendation**
- N/A — verification only

---

#### PRE-4: Agree Branch Naming and PR Size Limits

**Purpose:** Enforce consistent git workflow for the implementation phase.

**Dependencies:** None

**Estimated Effort:** 1 hour

**Estimated Risk:** Low

**Acceptance Criteria**
- Branch naming convention documented
- PR size limits agreed (max 400 lines changed per PR)
- Merge order defined

**Definition of Done**
- [ ] Branch naming convention documented
- [ ] PR size limits agreed
- [ ] Merge order defined

**Rollback Strategy:** N/A — process definition only

**Files Likely to Change**
- None (process definition)

**Testing Requirements**
- None

**Security Considerations**
- None

**Documentation Updates Required**
- None (agreed in team channel)

**Git Commit Recommendation**
- N/A

---

#### PRE-5: Document Rollback Runbook

**Purpose:** Ensure every phase has a tested rollback procedure.

**Dependencies:** None

**Estimated Effort:** 2 hours

**Estimated Risk:** Low

**Acceptance Criteria**
- Rollback runbook template created
- Each phase has a rollback section in this document
- Rollback tested on at least one dry-run

**Definition of Done**
- [ ] Rollback runbook template created
- [ ] Each phase has rollback section
- [ ] Dry-run performed

**Rollback Strategy:** N/A — this is the rollback planning task

**Files Likely to Change**
- `docs/archive/runbooks/rollback-runbook.md` (new)

**Testing Requirements**
- Dry-run rollback on test environment

**Security Considerations**
- None

**Documentation Updates Required**
- `docs/archive/runbooks/rollback-runbook.md`

**Git Commit Recommendation**
```
docs: add rollback runbook template
```

---

#### PRE-6: Confirm Test Command and Coverage Threshold

**Purpose:** Establish the exact test invocation and coverage threshold used during implementation.

**Dependencies:** None

**Estimated Effort:** 1 hour

**Estimated Risk:** Low

**Acceptance Criteria**
- Test command documented
- Coverage threshold confirmed at ≥90%
- Test shard configuration verified

**Definition of Done**
- [ ] Test command documented
- [ ] Coverage threshold confirmed
- [ ] Shard configuration verified

**Rollback Strategy:** N/A — verification only

**Files Likely to Change**
- None

**Testing Requirements**
- None

**Security Considerations**
- None

**Documentation Updates Required**
- None

**Git Commit Recommendation**
- N/A

---

#### PRE-7: Verify Import-Linter Baseline

**Purpose:** Capture current import-linter state as the baseline for Phase 2+.

**Dependencies:** None

**Estimated Effort:** 1 hour

**Estimated Risk:** Low

**Acceptance Criteria**
- `import-linter.ini` exists and is current
- Baseline import-linter run passes
- No violations on `main`

**Definition of Done**
- [ ] `import-linter.ini` verified
- [ ] Baseline run passes
- [ ] Violations documented (if any)

**Rollback Strategy:** N/A — verification only

**Files Likely to Change**
- None

**Testing Requirements**
- Run `import-linter` locally

**Security Considerations**
- None

**Documentation Updates Required**
- None

**Git Commit Recommendation**
- N/A

---

## Phase 0 — Architecture Baseline

### Status: 🟩 Complete

### Objectives
Establish permanent architecture workspace, ADRs, principles, coding standards, and roadmap. Documentation only. No code changes.

### Entry Criteria
- Repository exists
- No prior architecture documentation

### Exit Criteria
- All Phase 0 deliverables complete
- ADR template created
- Architecture README created
- Roadmap created

### Deliverables
- `architecture/` directory structure
- ADR template and initial ADRs
- Architecture principles
- Coding standards
- Roadmap
- Architecture README

### Success Metrics
- Zero broken links in canonical docs
- All Tier 1 documents present
- Documentation Guardian exits 0

### Completed Tasks
All Phase 0 tasks are complete. No further action required.

---

## Phase 1.0 — Repository Preparation

### Status: 🟨 In Progress (setup phase)

### Objectives
Create required directory structure, validate documentation paths, and establish CI baseline before Phase 1.4–1.9 implementation tasks begin.

### Entry Criteria
- Phase 0 complete
- Pre-Implementation tasks (PRE-1 through PRE-7) complete

### Exit Criteria
- All required directories exist
- Documentation paths validated
- CI remains green

### Deliverables
- `platform/di/` — dependency injection directory
- `platform/events/` — event bus directory
- `rentsecure_be/settings/` — split settings package
- `shared/tests/` — shared test utilities
- `docs/architecture/contracts/` — contract documentation with README
- CI baseline validated

### Success Metrics
- All required directories created
- Documentation Guardian exits 0
- CI remains green

---

## Phase 1.0 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 1.0.1 | Create required directory structure | P0 | 1h | Low | ⬜ |
| 1.0.2 | Create architecture contracts documentation structure | P1 | 2h | Low | ⬜ |
| 1.0.3 | Validate import boundaries | P1 | 2h | Low | ⬜ |
| 1.0.4 | Validate CI baseline | P0 | 1h | Low | ⬜ |

**Phase 1.0 Exit Criteria**
- [ ] `platform/di/` directory created
- [ ] `platform/events/` directory created
- [ ] `rentsecure_be/settings/` package created
- [ ] `shared/tests/` directory created
- [ ] `docs/architecture/contracts/` directory created with README
- [ ] CI baseline validated
- [ ] CI remains green

**Phase 1.0 Rollback Strategy:** N/A — directory creation only; revert by removing created directories

**Phase 1.0 Files Created**
- `platform/di/` (new directory)
- `platform/events/` (new directory)
- `rentsecure_be/settings/` (new package)
- `shared/tests/` (new directory)
- `docs/architecture/contracts/README.md` (new)

**Phase 1.0 Security Considerations**
- None (directory structure only)

---

## Phase 1 — Shared Foundation

### Status: 🟨 Partially Complete (1.1–1.3 done; 1.4–1.9 pending)

### Objectives
Establish shared kernel contracts, base classes, utilities, and contracts used across all contexts. Do NOT move business logic.

### Entry Criteria
- Phase 0 complete
- Documentation baseline clean
- Documentation Guardian reliable
- Required directories created (see Phase 1.0):
  - `platform/di/`
  - `platform/events/`
  - `rentsecure_be/settings/`
  - `shared/tests/`
  - `docs/architecture/contracts/`

### Exit Criteria
- All adapter interfaces defined
- DI container implemented and tested
- Event bus implemented and tested
- Settings split complete
- Repository pattern covers `core/` app
- `core/views.py` business logic extracted
- CI passes
- Coverage ≥90%

### Deliverables
- `shared/interfaces.py` — full adapter interfaces
- `shared/domain_events.py` — complete event infrastructure
- `platform/di/` — dependency injection container
- `platform/events/` — event bus implementation
- `rentsecure_be/settings/` — split settings
- `core/repositories/` — repository pattern for core models
- `docs/architecture/contracts/` — architecture contract documentation

### Success Metrics
- All adapter interfaces defined
- DI container functional
- Event bus functional
- Settings split validated
- CI remains green

---

## Phase 1.4 — Adapter Interfaces

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 1.4.1 | Define `PaymentGateway` interface | P0 | 4h | Low | ⬜ |
| 1.4.2 | Define `NotificationChannel` interface | P0 | 4h | Low | ⬜ |
| 1.4.3 | Define `PDFGeneratorAdapter` interface | P1 | 3h | Low | ⬜ |
| 1.4.4 | Define `StorageAdapter` interface | P1 | 3h | Low | ⬜ |
| 1.4.5 | Define `CacheAdapter` interface | P1 | 2h | Low | ⬜ |
| 1.4.6 | Define `QueueAdapter` interface | P1 | 2h | Low | ⬜ |
| 1.4.7 | Add adapter interface tests | P0 | 4h | Low | ⬜ |

**Phase 1.4 Exit Criteria**
- [ ] All 6 adapter interfaces defined in `shared/interfaces.py`
- [ ] Each interface has protocol compliance tests
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 1.4 Rollback Strategy:** Revert interface definitions; adapters continue using implicit contracts

**Phase 1.4 Files Likely to Change**
- `shared/interfaces.py`
- `shared/tests/test_interfaces.py` (new)

**Phase 1.4 Security Considerations**
- Payment and notification interfaces are security-sensitive
- All methods must have typed signatures
- Webhook secret validation must be part of payment interface
- Rate limiting must be part of notification interface

---

## Phase 1.5 — Dependency Injection Container

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 1.5.1 | Create `platform/di/` directory structure | P1 | 1h | Low | ⬜ |
| 1.5.2 | Implement `ServiceContainer` class | P1 | 6h | Medium | ⬜ |
| 1.5.3 | Implement `ContainerAwareService` base class | P1 | 4h | Low | ⬜ |
| 1.5.4 | Migrate `AuthService` to DI | P1 | 3h | Low | ⬜ |
| 1.5.5 | Migrate `OTPService` to DI | P1 | 3h | Low | ⬜ |
| 1.5.6 | Migrate `SubscriptionService` to DI | P1 | 3h | Low | ⬜ |
| 1.5.7 | Migrate `RentService` to DI | P1 | 3h | Low | ⬜ |
| 1.5.8 | Add DI container tests | P0 | 4h | Medium | ⬜ |

**Phase 1.5 Exit Criteria**
- [ ] `ServiceContainer` implemented with registration/resolution
- [ ] `ContainerAwareService` base class available
- [ ] AuthService, OTPService, SubscriptionService, RentService migrated to DI
- [ ] DI container tests pass
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 1.5 Rollback Strategy:** Remove `platform/di/` directory; services revert to static methods or direct instantiation

**Phase 1.5 Files Likely to Change**
- `platform/di/container.py` (new)
- `platform/di/exceptions.py` (new)
- `core/services/auth_service.py`
- `core/services/otp_service.py`
- `core/services/subscription_service.py`
- `properties/services/rent_service.py`
- `platform/tests/test_container.py` (new)

**Phase 1.5 Security Considerations**
- Container must not expose resolved instances to unauthorized callers
- Singleton services must be thread-safe
- AuthService migration must not change auth behavior

---

## Phase 1.6 — Event Bus Implementation

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 1.6.1 | Implement `InProcessEventBus` | P1 | 6h | Medium | ⬜ |
| 1.6.2 | Implement event middleware (logging, retry) | P1 | 4h | Medium | ⬜ |
| 1.6.3 | Implement dead letter queue | P2 | 4h | Medium | ⬜ |
| 1.6.4 | Define domain events for core contexts | P1 | 6h | Low | ⬜ |
| 1.6.5 | Integrate event bus with services | P1 | 4h | Medium | ⬜ |
| 1.6.6 | Add event bus tests | P0 | 4h | Medium | ⬜ |

**Phase 1.6 Exit Criteria**
- [ ] `InProcessEventBus` implements `EventBus` protocol
- [ ] Middleware (logging, retry) implemented
- [ ] Dead letter queue implemented
- [ ] Core domain events defined
- [ ] Event bus integrated with AuthService, SubscriptionService, RentService
- [ ] Event bus tests pass
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 1.6 Rollback Strategy:** Remove event bus; services use direct calls

**Phase 1.6 Files Likely to Change**
- `platform/events/event_bus.py` (new)
- `platform/events/middleware.py` (new)
- `platform/events/dead_letter_queue.py` (new)
- `shared/domain_events.py`
- `core/events.py` (new)
- `properties/events.py` (new)
- `notification/events.py` (new)
- `platform/tests/test_event_bus.py` (new)

**Phase 1.6 Security Considerations**
- Event bus must validate event schemas
- Event metadata must include correlation IDs
- Events must not contain sensitive data in plain text
- Retry middleware must not retry security-sensitive events indefinitely

---

## Phase 1.7 — Settings Split

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 1.7.1 | Create `rentsecure_be/settings/` package | P1 | 2h | Medium | ⬜ |
| 1.7.2 | Extract `base.py` from current `settings.py` | P1 | 4h | Medium | ⬜ |
| 1.7.3 | Create `development.py` | P1 | 2h | Low | ⬜ |
| 1.7.4 | Create `production.py` | P1 | 3h | Medium | ⬜ |
| 1.7.5 | Create `testing.py` | P1 | 2h | Low | ⬜ |
| 1.7.6 | Create `ci.py` | P1 | 2h | Low | ⬜ |
| 1.7.7 | Update manage.py and wsgi/asgi imports | P1 | 2h | Medium | ⬜ |
| 1.7.8 | Validate settings in all environments | P0 | 3h | Medium | ⬜ |

**Phase 1.7 Exit Criteria**
- [ ] `rentsecure_be/settings/` package created
- [ ] `base.py`, `development.py`, `production.py`, `testing.py`, `ci.py` created
- [ ] All entry points updated
- [ ] All environments validated
- [ ] CI passes
- [ ] All tests pass

**Phase 1.7 Rollback Strategy:** Move `settings/base.py` back to `settings.py`; update imports

**Phase 1.7 Files Likely to Change**
- `rentsecure_be/settings/` (new directory)
- `rentsecure_be/settings/base.py`
- `rentsecure_be/settings/development.py` (new)
- `rentsecure_be/settings/production.py` (new)
- `rentsecure_be/settings/testing.py` (new)
- `rentsecure_be/settings/ci.py` (new)
- `manage.py`
- `rentsecure_be/wsgi.py`
- `rentsecure_be/asgi.py`

**Phase 1.7 Security Considerations**
- `production.py` must not be committed with defaults
- `SECRET_KEY` validation must remain in `base.py`
- `DEBUG = True` must never be in production
- Production security headers must be enforced

---

## Phase 1.8 — Repository Pattern Coverage

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 1.8.1 | Create `core/repositories/` directory | P1 | 1h | Low | ⬜ |
| 1.8.2 | Implement `UserRepository` | P1 | 4h | Low | ⬜ |
| 1.8.3 | Implement `OTPRepository` | P1 | 3h | Low | ⬜ |
| 1.8.4 | Implement `SubscriptionRepository` | P1 | 4h | Low | ⬜ |
| 1.8.5 | Implement `BankDetailsRepository` | P1 | 3h | Low | ⬜ |
| 1.8.6 | Migrate `AuthService` to use `UserRepository` | P1 | 3h | Low | ⬜ |
| 1.8.7 | Migrate `OTPService` to use `OTPRepository` | P1 | 3h | Low | ⬜ |
| 1.8.8 | Migrate `SubscriptionService` to use `SubscriptionRepository` | P1 | 3h | Low | ⬜ |
| 1.8.9 | Add repository tests | P0 | 4h | Low | ⬜ |

**Phase 1.8 Exit Criteria**
- [ ] `core/repositories/` directory created
- [ ] UserRepository, OTPRepository, SubscriptionRepository, BankDetailsRepository implemented
- [ ] AuthService, OTPService, SubscriptionService migrated to use repositories
- [ ] Repository tests pass
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 1.8 Rollback Strategy:** Revert repository additions; services continue using direct ORM

**Phase 1.8 Files Likely to Change**
- `core/repositories/` (new directory)
- `core/repositories/user_repository.py` (new)
- `core/repositories/otp_repository.py` (new)
- `core/repositories/subscription_repository.py` (new)
- `core/repositories/bank_details_repository.py` (new)
- `core/services/auth_service.py`
- `core/services/otp_service.py`
- `core/services/subscription_service.py`
- `core/tests/test_repositories.py` (new)

**Phase 1.8 Security Considerations**
- Repository must not expose password hashes
- OTP codes must not be logged
- Bank details are highly sensitive; must not log sensitive fields

---

## Phase 1.9 — Extract Business Logic from Views

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 1.9.1 | Audit `core/views.py` for business logic | P0 | 4h | Medium | ⬜ |
| 1.9.2 | Extract OTP logic to `OTPService` | P0 | 4h | Medium | ⬜ |
| 1.9.3 | Extract auth logic to `AuthService` | P0 | 4h | Medium | ⬜ |
| 1.9.4 | Extract subscription logic to `SubscriptionService` | P0 | 4h | Medium | ⬜ |
| 1.9.5 | Extract bank details logic to `BankDetailsService` | P1 | 3h | Medium | ⬜ |
| 1.9.6 | Extract referral logic to `ReferralService` | P1 | 3h | Medium | ⬜ |
| 1.9.7 | Extract password logic to `PasswordService` | P1 | 3h | Medium | ⬜ |
| 1.9.8 | Add view extraction tests | P0 | 4h | Medium | ⬜ |

**Phase 1.9 Task Dependencies**

| Task | Title | Dependencies |
|------|-------|-------------|
| 1.9.1 | Audit `core/views.py` | None |
| 1.9.2 | Extract OTP logic to `OTPService` | 1.9.1, 1.8.7 (OTPService must use OTPRepository before extraction) |
| 1.9.3 | Extract auth logic to `AuthService` | 1.9.1, 1.8.6 (AuthService must use UserRepository before extraction) |
| 1.9.4 | Extract subscription logic to `SubscriptionService` | 1.9.1, 1.8.8 |
| 1.9.5 | Extract bank details logic to `BankDetailsService` | 1.9.1 |
| 1.9.6 | Extract referral logic to `ReferralService` | 1.9.1 |
| 1.9.7 | Extract password logic to `PasswordService` | 1.9.1 |
| 1.9.8 | Add view extraction tests | 1.9.2–1.9.7 |

**Why:** Service extraction must happen after repository migration (1.8.6, 1.8.7, 1.8.8) to avoid temporary ORM coupling in extracted services.

**Phase 1.9 Exit Criteria**
- [ ] `core/views.py` audited and extraction plan documented
- [ ] All business logic extracted to services
- [ ] View methods under 20 lines each
- [ ] View extraction tests pass
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 1.9 Rollback Strategy:** Revert to original view logic

**Phase 1.9 Files Likely to Change**
- `core/views.py`
- `core/services/otp_service.py`
- `core/services/auth_service.py`
- `core/services/subscription_service.py`
- `core/services/bank_details_service.py`
- `core/services/referral_service.py`
- `core/services/password_service.py`
- `core/tests/test_views.py` (update)

**Phase 1.9 Security Considerations**
- OTP rate limiting must remain intact
- OTP generation must remain cryptographically secure
- Authentication logic must not change
- JWT token handling must remain secure
- Password reset logic must remain secure
- Token generation must remain cryptographically secure

---

## Phase 2 — Infrastructure

### Status: ⬜ Not Started

### Objectives
Extract infrastructure concerns (cache, queue, storage) into explicit adapters.

### Entry Criteria
- Phase 1 complete
- All shared interfaces defined
- DI container functional
- Event bus functional

### Exit Criteria
- Cache adapter interface + implementation complete
- Queue adapter interface + implementation complete
- Storage adapter interface + implementation complete
- Configuration-driven adapter selection working

### Deliverables
- `platform/adapters/cache/` — cache adapter
- `platform/adapters/queue/` — queue adapter
- `platform/adapters/storage/` — storage adapter
- `platform/adapters/pdf/` — PDF adapter
- Adapter selection via configuration

### Success Metrics
- All adapters implement defined interfaces
- Adapter selection works via feature flags
- CI passes
- Coverage ≥90%

---

## Phase 2 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 2.1 | Implement `LocMemCacheAdapter` | P0 | 4h | Low | ⬜ |
| 2.2 | Implement `RedisCacheAdapter` (disabled) | P1 | 4h | Low | ⬜ |
| 2.3 | Implement `LocalQueueAdapter` | P1 | 4h | Low | ⬜ |
| 2.4 | Implement `CeleryQueueAdapter` (disabled) | P1 | 6h | Medium | ⬜ |
| 2.5 | Implement `S3StorageAdapter` | P0 | 6h | Medium | ⬜ |
| 2.6 | Implement `LocalStorageAdapter` (disabled) | P2 | 3h | Low | ⬜ |
| 2.7 | Implement `WeasyPrintPDFAdapter` | P1 | 6h | Medium | ⬜ |
| 2.8 | Wire adapters into DI container | P0 | 4h | Medium | ⬜ |
| 2.9 | Add adapter tests | P0 | 6h | Low | ⬜ |

**Phase 2 Exit Criteria**
- [ ] All adapters implemented
- [ ] Adapter selection works via configuration
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 2 Rollback Strategy:** Remove adapters; services use direct Django/infrastructure calls

**Phase 2 Files Likely to Change**
- `platform/adapters/cache/locmem_adapter.py` (new)
- `platform/adapters/cache/redis_adapter.py` (new)
- `platform/adapters/queue/local_adapter.py` (new)
- `platform/adapters/queue/celery_adapter.py` (new)
- `platform/adapters/storage/s3_adapter.py` (new)
- `platform/adapters/storage/local_adapter.py` (new)
- `platform/adapters/pdf/weasyprint_adapter.py` (new)
- `platform/tests/test_adapters.py` (new)

**Phase 2 Security Considerations**
- S3 bucket must have proper ACLs
- Presigned URLs must have short expiry
- Redis connection must use authentication
- Celery broker must use authentication
- Cache keys must be namespaced
- Sensitive data must not be cached without encryption

---

## Phase 3 — Identity

### Status: ⬜ Not Started

### Objectives
Define and enforce Identity bounded context boundaries. Extract authentication, authorization, and user management from `core/`.

### Entry Criteria
- Phase 1 complete
- Phase 2 complete
- Repository pattern covers `core/` models
- Views in `core/` are thin

### Exit Criteria
- `identity/` package created
- User, OTP, auth models moved
- Identity service interface defined
- Contract tests for identity boundaries pass
- import-linter contracts updated

### Deliverables
- `identity/` package with models, services, serializers, views
- Identity service interface
- Permission service interface
- Contract tests for identity boundaries

### Success Metrics
- Identity context is independently testable
- No cross-context model imports
- CI passes
- Coverage ≥90%

---

## Phase 3 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 3.1 | Create `identity/` package structure | P0 | 4h | High | ⬜ |
| 3.2 | Move `User` model to `identity/` | P0 | 6h | High | ⬜ |
| 3.3 | Move `OTP` model to `identity/` | P0 | 4h | Medium | ⬜ |
| 3.4 | Move auth services to `identity/` | P0 | 6h | Medium | ⬜ |
| 3.5 | Move auth views to `identity/` | P0 | 4h | Medium | ⬜ |
| 3.6 | Update all imports across codebase | P0 | 8h | High | ⬜ |
| 3.7 | Add identity contract tests | P0 | 6h | Medium | ⬜ |
| 3.8 | Update import-linter contracts | P0 | 4h | Medium | ⬜ |
| 3.9 | Validate identity context isolation | P0 | 4h | Medium | ⬜ |

**Phase 3 Exit Criteria**
- [ ] `identity/` package created and functional
- [ ] User and OTP models moved
- [ ] Auth services and views moved
- [ ] All imports updated
- [ ] Contract tests pass
- [ ] import-linter contracts updated
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 3 Rollback Strategy:** Remove `identity/` package; keep code in `core/`

**Phase 3 Files Likely to Change**
- `identity/` (new directory)
- `core/models.py` (remove User, OTP)
- `core/services/` (remove auth services)
- `core/views.py` (remove auth views)
- All files importing from `core.models`, `core.services`, `core.views`
- `rentsecure_be/settings/base.py` — update `AUTH_USER_MODEL`
- `import-linter.ini`

**Phase 3 Security Considerations**
- `AUTH_USER_MODEL` change requires migration
- Password hashing must not be broken
- JWT token validation must not be broken
- Auth endpoints must remain protected
- Rate limiting must remain intact

---

## Phase 4 — Subscription

### Status: ⬜ Not Started

### Objectives
Define and enforce Subscription bounded context boundaries. Extract subscription and usage limit enforcement from `core/`.

### Entry Criteria
- Phase 3 complete
- Identity context isolated
- Repository pattern covers `core/` models

### Exit Criteria
- `subscription/` package created
- Subscription models moved
- Subscription service interface defined
- Contract tests for subscription boundaries pass
- import-linter contracts updated

### Deliverables
- `subscription/` package with models, services, serializers, views
- Subscription service interface
- Limit enforcement contracts
- Contract tests for subscription boundaries

### Success Metrics
- Subscription context is independently testable
- No cross-context model imports
- CI passes
- Coverage ≥90%

---

## Phase 4 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 4.1 | Create `subscription/` package structure | P0 | 4h | High | ⬜ |
| 4.2 | Move subscription models to `subscription/` | P0 | 6h | High | ⬜ |
| 4.3 | Move subscription services to `subscription/` | P0 | 6h | Medium | ⬜ |
| 4.4 | Move subscription views to `subscription/` | P0 | 4h | Medium | ⬜ |
| 4.5 | Update all imports across codebase | P0 | 8h | High | ⬜ |
| 4.6 | Add subscription contract tests | P0 | 6h | Medium | ⬜ |
| 4.7 | Update import-linter contracts | P0 | 4h | Medium | ⬜ |
| 4.8 | Validate subscription context isolation | P0 | 4h | Medium | ⬜ |

**Phase 4 Exit Criteria**
- [ ] `subscription/` package created and functional
- [ ] Subscription models moved
- [ ] Subscription services and views moved
- [ ] All imports updated
- [ ] Contract tests pass
- [ ] import-linter contracts updated
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 4 Rollback Strategy:** Remove `subscription/` package; keep code in `core/`

**Phase 4 Files Likely to Change**
- `subscription/` (new directory)
- `core/models.py` (remove subscription models)
- `core/services/` (remove subscription services)
- `core/views.py` (remove subscription views)
- All files importing subscription models/services
- `rentsecure_be/settings/base.py`
- `import-linter.ini`

**Phase 4 Security Considerations**
- Subscription checks must remain intact
- Subscription endpoints must remain protected

---

## Phase 5 — Property

### Status: 🟨 Partially Complete

### Objectives
Define and enforce Property bounded context boundaries. The `properties/` app is already well-structured; this phase focuses on formalizing boundaries and adding missing pieces.

### Entry Criteria
- Phase 3 complete
- Phase 4 complete
- Identity and subscription contexts isolated

### Exit Criteria
- Property context fully isolated
- Repository pattern complete
- All services use repositories
- Contract tests for property boundaries pass
- import-linter contracts updated

### Deliverables
- Complete repository pattern in `properties/`
- Property service interface
- Contract tests for property boundaries
- import-linter contracts updated

### Success Metrics
- Property context is independently testable
- No cross-context model imports
- CI passes
- Coverage ≥90%

---

## Phase 5 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 5.1 | Complete repository pattern in `properties/` | P0 | 8h | Low | ⬜ |
| 5.2 | Migrate all services to use repositories | P0 | 8h | Medium | ⬜ |
| 5.3 | Add property contract tests | P0 | 6h | Medium | ⬜ |
| 5.4 | Update import-linter contracts | P0 | 4h | Medium | ⬜ |
| 5.5 | Validate property context isolation | P0 | 4h | Medium | ⬜ |

**Phase 5 Exit Criteria**
- [ ] Repository pattern complete in `properties/`
- [ ] All services use repositories
- [ ] Contract tests pass
- [ ] import-linter contracts updated
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 5 Rollback Strategy:** Revert repository additions; services continue using existing repositories

**Phase 5 Files Likely to Change**
- `properties/repositories/` (add missing repositories)
- `properties/services/*.py`
- `properties/tests/test_contracts.py` (new)
- `import-linter.ini`

**Phase 5 Security Considerations**
- None

---

## Phase 6 — Renter

### Status: ⬜ Not Started

### Objectives
Define and enforce Renter bounded context boundaries.

### Entry Criteria
- Phase 5 complete
- Property context isolated

### Exit Criteria
- Renter context fully isolated
- Contract tests for renter boundaries pass
- import-linter contracts updated

### Deliverables
- Renter service interface
- Contract tests for renter boundaries

### Success Metrics
- Renter context is independently testable
- CI passes
- Coverage ≥90%

---

## Phase 6 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 6.1 | Complete renter service layer | P1 | 6h | Low | ⬜ |
| 6.2 | Add renter contract tests | P1 | 6h | Medium | ⬜ |
| 6.3 | Validate renter context isolation | P1 | 4h | Medium | ⬜ |

**Phase 6 Exit Criteria**
- [ ] Renter service layer complete
- [ ] Contract tests pass
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 6 Rollback Strategy:** Revert service layer changes

**Phase 6 Files Likely to Change**
- `properties/services/renter_service.py`
- `properties/views/renter_views.py`
- `properties/tests/test_renter_contracts.py` (new)

**Phase 6 Security Considerations**
- None

---

## Phase 7 — Rent

### Status: ⬜ Not Started

### Objectives
Define and enforce Rent bounded context boundaries.

### Entry Criteria
- Phase 6 complete

### Exit Criteria
- Rent context fully isolated
- Contract tests for rent boundaries pass
- import-linter contracts updated

### Deliverables
- Rent service interface
- Calculation contracts
- Contract tests for rent boundaries

### Success Metrics
- Rent context is independently testable
- CI passes
- Coverage ≥90%

---

## Phase 7 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 7.1 | Implement rent calculation service | P0 | 8h | Medium | ⬜ |
| 7.2 | Implement rent state machine | P0 | 6h | Medium | ⬜ |
| 7.3 | Add rent contract tests | P0 | 6h | Medium | ⬜ |
| 7.4 | Validate rent context isolation | P0 | 4h | Medium | ⬜ |

**Phase 7 Exit Criteria**
- [ ] Rent calculation service implemented
- [ ] Rent state machine implemented
- [ ] Contract tests pass
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 7 Rollback Strategy:** Remove state machine; use simple status field

**Phase 7 Files Likely to Change**
- `properties/services/rent_calculation_service.py` (new)
- `properties/services/rent_state_machine.py` (new)
- `properties/models/rent_record_models.py`
- `properties/tests/test_rent_contracts.py` (new)

**Phase 7 Security Considerations**
- State transitions must be audited
- No unauthorized state changes

---

## Phase 8 — Payments

### Status: ⬜ Not Started

### Objectives
Define and enforce Payments bounded context boundaries. Implement manual UPI payment flow with webhook idempotency.

### Entry Criteria
- Phase 7 complete

### Exit Criteria
- Payments context fully isolated
- Manual UPI adapter implemented
- Webhook idempotency implemented
- Rent receipt PDF generation working
- Contract tests for payment boundaries pass

### Deliverables
- `payments/` package
- `ManualPaymentAdapter` implementing `PaymentGateway`
- Webhook idempotency
- Rent receipt PDF generation
- Contract tests for payment boundaries

### Success Metrics
- Payments context is independently testable
- Manual UPI flow works end-to-end
- CI passes
- Coverage ≥90%

---

## Phase 8 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 8.1 | Create `payments/` package structure | P0 | 4h | High | ⬜ |
| 8.2 | Implement `ManualPaymentAdapter` | P0 | 8h | Medium | ⬜ |
| 8.3 | Implement webhook idempotency | P0 | 6h | High | ⬜ |
| 8.4 | Implement rent receipt PDF generation | P0 | 8h | Medium | ⬜ |
| 8.5 | Implement payment state machine | P0 | 6h | Medium | ⬜ |
| 8.6 | Add payment contract tests | P0 | 6h | Medium | ⬜ |
| 8.7 | Validate payment context isolation | P0 | 4h | Medium | ⬜ |

**Phase 8 Exit Criteria**
- [ ] `payments/` package created and functional
- [ ] `ManualPaymentAdapter` implemented
- [ ] Webhook idempotency implemented
- [ ] Rent receipt PDF generation working
- [ ] Payment state machine implemented
- [ ] Contract tests pass
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 8 Rollback Strategy:** Remove `payments/` package; keep code in existing locations

**Phase 8 Files Likely to Change**
- `payments/` (new directory)
- `payments/adapters/manual_adapter.py` (new)
- `payments/models/payment_models.py` (new)
- `payments/views/webhooks.py` (new)
- `payments/services/webhook_service.py` (new)
- `payments/services/payment_service.py` (new)
- `payments/services/receipt_service.py` (new)
- `payments/tests/test_contracts.py` (new)
- `payments/tests/test_webhooks.py` (new)

**Phase 8 Security Considerations**
- UTR validation must be strict
- Payment amounts must be validated
- Webhook signature validation is security-critical
- Timing attack prevention for signature comparison
- State transitions must be audited
- No unauthorized state changes

---

## Phase 9 — Notification

### Status: 🟨 Partially Complete

### Objectives
Define and enforce Notification bounded context boundaries. Implement notification dispatch service with adapter pattern.

### Entry Criteria
- Phase 8 complete
- Event bus functional

### Exit Criteria
- Notification context fully isolated
- All notification adapters implement `NotificationChannel`
- Notification dispatch service implemented
- Contract tests for notification boundaries pass
- import-linter contracts updated

### Deliverables
- `notification/` package with complete adapter pattern
- Notification dispatch service
- Contract tests for notification boundaries

### Success Metrics
- Notification context is independently testable
- All free channels (email, push, in-app) working
- CI passes
- Coverage ≥90%

---

## Phase 9 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 9.1 | Implement `EmailAdapter` | P0 | 4h | Low | ⬜ |
| 9.2 | Implement `FCMAdapter` (Push) | P0 | 4h | Low | ⬜ |
| 9.3 | Implement `InAppAdapter` | P0 | 4h | Low | ⬜ |
| 9.4 | Implement `WhatsAppAdapter` (disabled) | P1 | 4h | Low | ⬜ |
| 9.5 | Implement `SMSAdapter` (disabled) | P1 | 4h | Low | ⬜ |
| 9.6 | Implement `VoiceAdapter` (disabled) | P2 | 4h | Low | ⬜ |
| 9.7 | Implement notification dispatch service | P0 | 6h | Medium | ⬜ |
| 9.8 | Add notification contract tests | P0 | 6h | Medium | ⬜ |
| 9.9 | Validate notification context isolation | P0 | 4h | Medium | ⬜ |

**Phase 9 Exit Criteria**
- [ ] All notification adapters implemented
- [ ] Notification dispatch service implemented
- [ ] Contract tests pass
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 9 Rollback Strategy:** Remove dispatch service; services call adapters directly

**Phase 9 Files Likely to Change**
- `notification/adapters/email_adapter.py` (new)
- `notification/adapters/fcm_adapter.py` (new)
- `notification/adapters/inapp_adapter.py` (new)
- `notification/adapters/whatsapp_adapter.py` (new)
- `notification/adapters/sms_adapter.py` (new)
- `notification/adapters/voice_adapter.py` (new)
- `notification/services/dispatch_service.py` (new)
- `notification/tests/test_contracts.py` (new)

**Phase 9 Security Considerations**
- Email must use TLS
- No sensitive data in email body without encryption
- FCM server key must be kept secret
- Device tokens must be stored securely
- In-app notifications must be user-scoped
- No unauthorized access to other users' notifications
- Rate limiting must prevent abuse
- Notification preferences must be enforced

---

## Phase 10 — Documents

### Status: ⬜ Not Started

### Objectives
Define and enforce Documents bounded context boundaries.

### Entry Criteria
- Phase 9 complete

### Exit Criteria
- Documents context fully isolated
- PDF generation service implemented
- Contract tests for document boundaries pass

### Deliverables
- `documents/` package with complete service layer
- Document service interface
- Contract tests for document boundaries

### Success Metrics
- Documents context is independently testable
- CI passes
- Coverage ≥90%

---

## Phase 10 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 10.1 | Implement `WeasyPrintPDFAdapter` | P0 | 6h | Medium | ⬜ |
| 10.2 | Implement document template service | P1 | 6h | Medium | ⬜ |
| 10.3 | Implement document storage service | P1 | 4h | Low | ⬜ |
| 10.4 | Add document contract tests | P0 | 6h | Medium | ⬜ |
| 10.5 | Validate document context isolation | P0 | 4h | Medium | ⬜ |

**Phase 10 Exit Criteria**
- [ ] PDF generation adapter implemented
- [ ] Template service implemented
- [ ] Storage service implemented
- [ ] Contract tests pass
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 10 Rollback Strategy:** Remove services; documents managed manually

**Phase 10 Files Likely to Change**
- `documents/adapters/weasyprint_adapter.py` (new)
- `documents/services/template_service.py` (new)
- `documents/services/storage_service.py` (new)
- `documents/models/template_models.py` (new)
- `documents/tests/test_contracts.py` (new)

**Phase 10 Security Considerations**
- Template injection prevention
- PDF generation must not execute arbitrary code
- Presigned URLs must have short expiry
- Document access must be user-scoped

---

## Phase 11 — AI

### Status: ⬜ Not Started

### Objectives
Define and enforce AI bounded context boundaries. Consolidate `smartbot/` and `ai_assistant/`.

### Entry Criteria
- Phase 10 complete

### Exit Criteria
- AI context fully isolated
- SmartBot service implemented
- Contract tests for AI boundaries pass

### Deliverables
- `ai/` package (consolidated)
- AI service interface
- Contract tests for AI boundaries

### Success Metrics
- AI context is independently testable
- CI passes
- Coverage ≥90%

---

## Phase 11 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 11.1 | Consolidate `smartbot/` and `ai_assistant/` | P1 | 8h | High | ⬜ |
| 11.2 | Implement AI service interface | P1 | 4h | Medium | ⬜ |
| 11.3 | Add AI contract tests | P1 | 6h | Medium | ⬜ |
| 11.4 | Validate AI context isolation | P1 | 4h | Medium | ⬜ |

**Phase 11 Exit Criteria**
- [ ] AI context consolidated
- [ ] AI service interface defined
- [ ] Contract tests pass
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 11 Rollback Strategy:** Keep separate packages; remove `ai/`

**Phase 11 Files Likely to Change**
- `ai/` (new)
- `smartbot/` (deprecated)
- `ai_assistant/` (deprecated)
- All files importing from `smartbot` or `ai_assistant`
- `shared/interfaces.py`

**Phase 11 Security Considerations**
- AI governance rules must be preserved
- Prompt injection prevention must remain
- AI inputs must be validated
- AI outputs must be sanitized

---

## Phase 12 — Dashboard

### Status: ⬜ Not Started

### Objectives
Define and enforce Dashboard bounded context boundaries. Implement analytics with selective CQRS.

### Entry Criteria
- Phase 11 complete

### Exit Criteria
- Dashboard context fully isolated
- Analytics aggregation service implemented
- Selective CQRS implemented for dashboards
- Contract tests for dashboard boundaries pass

### Deliverables
- `dashboard/` package with complete service layer
- Dashboard service interface
- Analytics aggregation contracts
- Contract tests for dashboard boundaries

### Success Metrics
- Dashboard context is independently testable
- CQRS read models working
- CI passes
- Coverage ≥90%

---

## Phase 12 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 12.1 | Implement analytics aggregation service | P0 | 8h | Medium | ⬜ |
| 12.2 | Implement selective CQRS for dashboards | P1 | 8h | High | ⬜ |
| 12.3 | Add dashboard contract tests | P0 | 6h | Medium | ⬜ |
| 12.4 | Validate dashboard context isolation | P0 | 4h | Medium | ⬜ |

**Phase 12 Exit Criteria**
- [ ] Analytics aggregation service implemented
- [ ] Selective CQRS implemented
- [ ] Contract tests pass
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 12 Rollback Strategy:** Remove CQRS; use direct queries

**Phase 12 Files Likely to Change**
- `dashboard/services/analytics_service.py` (new)
- `dashboard/models/read_models.py` (new)
- `dashboard/services/cqrs_service.py` (new)
- `dashboard/tests/test_contracts.py` (new)

**Phase 12 Security Considerations**
- Aggregation queries must respect tenant isolation
- No data leakage between owners
- Read models must respect tenant isolation

---

## Phase 13 — Architecture Enforcement

### Status: ⬜ Not Started

### Objectives
Automate architecture validation and enforce contracts in CI.

### Entry Criteria
- Phases 1–12 complete

### Exit Criteria
- import-linter contracts fully enforced
- Architecture test suite complete
- Contract validation automated in CI
- Architecture review checklist complete

### Deliverables
- Enhanced import-linter configuration
- Architecture test suite
- Automated contract validation
- Architecture review checklist

### Success Metrics
- All architecture tests pass
- import-linter blocks violations
- CI always green
- Coverage ≥90%

---

## Phase 13 — Detailed Task Breakdown

| ID | Title | Priority | Effort | Risk | Status |
|----|-------|----------|--------|------|--------|
| 13.1 | Enhance import-linter configuration | P0 | 8h | Medium | ⬜ |
| 13.2 | Implement architecture test suite | P0 | 8h | Medium | ⬜ |
| 13.3 | Automate contract validation in CI | P0 | 6h | Medium | ⬜ |
| 13.4 | Create architecture review checklist | P1 | 4h | Low | ⬜ |
| 13.5 | Validate architecture enforcement | P0 | 4h | Medium | ⬜ |

**Phase 13 Exit Criteria**
- [ ] import-linter enhanced with bounded context contracts
- [ ] Architecture test suite complete
- [ ] Contract validation automated in CI
- [ ] Architecture review checklist complete
- [ ] CI passes
- [ ] Coverage ≥90%

**Phase 13 Rollback Strategy:** Revert to baseline import-linter configuration

**Phase 13 Files Likely to Change**
- `import-linter.ini`
- `tests/test_architecture_contract/` (update)
- `.github/workflows/architecture-guard.yml` (update)

**Phase 13 Security Considerations**
- None

---

# Dependency Graph

```
Phase 0 (Complete)
    ↓
Phase 1.4 (Adapter Interfaces)
    ↓
Phase 1.5 (DI Container)
    ↓
Phase 1.6 (Event Bus)
    ↓
Phase 1.7 (Settings Split)
    ↓
Phase 1.8 (Repository Pattern)
    ↓
Phase 1.9 (Extract Business Logic from Views)
    ↓
Phase 2 (Infrastructure)
    ↓
Phase 3 (Identity)
    ↓
Phase 4 (Subscription)
    ↓
Phase 5 (Property)
    ↓
Phase 6 (Renter)
    ↓
Phase 7 (Rent)
    ↓
Phase 8 (Payments)
    ↓
Phase 9 (Notification)
    ↓
Phase 10 (Documents)
    ↓
Phase 11 (AI)
    ↓
Phase 12 (Dashboard)
    ↓
Phase 13 (Architecture Enforcement)
```

**Critical Path Tasks (longest dependency chain):**
1. Phase 1.4: Adapter Interfaces (1.4.1–1.4.7)
2. Phase 1.5: DI Container (1.5.1–1.5.8)
3. Phase 1.6: Event Bus (1.6.1–1.6.6)
4. Phase 1.7: Settings Split (1.7.1–1.7.8)
5. Phase 1.8: Repository Pattern (1.8.1–1.8.9)
6. Phase 1.9: Extract Business Logic from Views (1.9.1–1.9.8)
7. Phase 2: Infrastructure (2.1–2.9)
8. Phase 3: Identity (3.1–3.9)
9. Phase 4: Subscription (4.1–4.8)
10. Phase 5: Property (5.1–5.5)
11. Phase 6: Renter (6.1–6.3)
12. Phase 7: Rent (7.1–7.4)
13. Phase 8: Payments (8.1–8.7)
14. Phase 9: Notification (9.1–9.9)
15. Phase 10: Documents (10.1–10.5)
16. Phase 11: AI (11.1–11.4)
17. Phase 12: Dashboard (12.1–12.4)
18. Phase 13: Architecture Enforcement (13.1–13.5)

---

# Parallelizable Tasks

## Within Phase 1

- **Phase 1.4 (Adapter Interfaces)** can be done in parallel with **Phase 1.7 (Settings Split)** and **Phase 1.8 (Repository Pattern)**
- **Phase 1.5 (DI Container)** can be done in parallel with **Phase 1.6 (Event Bus)** and **Phase 1.9 (Extract Business Logic from Views)**
- Within Phase 1.4, all adapter interface definitions (1.4.1–1.4.6) can be done in parallel
- Within Phase 1.8, all repository implementations (1.8.2–1.8.5) can be done in parallel
- Within Phase 1.9, all extractions (1.9.2–1.9.7) can be done in parallel after the audit (1.9.1)

## Within Phase 2

- All adapter implementations (2.1–2.7) can be done in parallel
- Adapter tests (2.9) can be written in parallel with adapter implementation

## Within Phase 3

- All move tasks (3.2–3.5) can be done in parallel after package structure is created (3.1)

## Within Phase 4

- All move tasks (4.2–4.4) can be done in parallel after package structure is created (4.1)

## Within Phase 8

- All adapter implementations within payments can be done in parallel
- PDF generation (8.4) can be done in parallel with state machine (8.5)

---

# Tasks That Block Other Tasks

| Task | Blocks |
|------|--------|
| 1.4.1: PaymentGateway interface | 8.2: ManualPaymentAdapter |
| 1.4.2: NotificationChannel interface | 9.1–9.6: All notification adapters |
| 1.4.3: PDFGeneratorAdapter interface | 2.7: WeasyPrintPDFAdapter, 8.4: Rent Receipt PDF |
| 1.4.4: StorageAdapter interface | 2.5: S3StorageAdapter, 2.6: LocalStorageAdapter |
| 1.4.5: CacheAdapter interface | 2.1: LocMemCacheAdapter, 2.2: RedisCacheAdapter |
| 1.4.6: QueueAdapter interface | 2.3: LocalQueueAdapter, 2.4: CeleryQueueAdapter |
| 1.5.2: ServiceContainer | 1.5.3: ContainerAwareService, 1.5.4–1.5.7: Service migrations |
| 1.5.3: ContainerAwareService | 1.5.4–1.5.7: Service migrations |
| 1.6.1: InProcessEventBus | 1.6.2–1.6.5: Middleware, DLQ, Domain Events, Integration |
| 1.7.1: Settings Package | 1.7.2–1.7.8: All settings files |
| 1.8.1: Repositories Directory | 1.8.2–1.8.5: All repositories |
| 1.8.2: UserRepository | 1.8.6: AuthService migration |
| 1.8.3: OTPRepository | 1.8.7: OTPService migration |
| 1.8.4: SubscriptionRepository | 1.8.8: SubscriptionService migration |
| 3.1: Identity Package | 3.2–3.9: All identity tasks |
| 4.1: Subscription Package | 4.2–4.8: All subscription tasks |
| 5.1: Complete Repository Pattern | 5.2: Migrate Services |
| 8.1: Payments Package | 8.2–8.7: All payments tasks |

---

# Testing Strategy

## Unit Tests
- Every service method must have unit tests
- Every repository method must have unit tests
- Every adapter must have unit tests
- Every state machine transition must have unit tests
- Target: ≥90% coverage

## Integration Tests
- Every API endpoint must have integration tests
- Every cross-context communication must have integration tests
- Every adapter selection must have integration tests
- Every migration must have integration tests

## Contract Tests
- Every bounded context must have contract tests
- Every service interface must have contract tests
- Every adapter interface must have contract tests
- Contract tests verify no cross-context model imports

## Regression Tests
- Full test suite runs on every PR
- Hypothesis property-based tests for critical paths
- Mutation testing (weekly) to verify test quality

## Security Tests
- bandit runs on every PR
- semgrep runs on every PR
- Trivy vulnerability scanning runs on every PR
- OWASP Top 10 coverage verified in security tests

## Performance Tests
- Query count tests verify no N+1 queries
- Benchmark tests for critical paths (weekly)
- Load tests for payment and notification endpoints (weekly)

## Contract Test Registry

Each bounded context must maintain contract tests at the following locations:

| Context | Contract Test File |
|---------|-------------------|
| identity | `identity/tests/test_contracts.py` |
| subscription | `subscription/tests/test_contracts.py` |
| properties | `properties/tests/test_contracts.py` |
| payments | `payments/tests/test_contracts.py` |
| notification | `notification/tests/test_contracts.py` |
| documents | `documents/tests/test_contracts.py` |
| ai | `ai/tests/test_contracts.py` |
| dashboard | `dashboard/tests/test_contracts.py` |

Contract tests verify:
- No cross-context model imports
- Service interface compliance
- Adapter interface compliance
- Context boundary isolation

---

# Git Workflow

## Branch Naming

```
feature/phase-{N}-{short-description}
bugfix/phase-{N}-{short-description}
hotfix/phase-{N}-{short-description}
refactor/phase-{N}-{short-description}
```

Examples:
- `feature/phase-1-adapter-interfaces`
- `bugfix/phase-1-di-container-circular-dep`
- `hotfix/phase-8-payment-webhook-idempotency`

## Commit Naming

```
{type}({scope}): {description}

Types:
- feat: new feature
- fix: bug fix
- refactor: code refactoring
- test: test additions
- docs: documentation changes
- chore: maintenance tasks

Scope examples:
- shared: shared module changes
- platform: platform module changes
- core: core app changes
- properties: properties app changes
- identity: identity context changes
- subscription: subscription context changes
- payments: payments context changes
- notification: notification context changes
- documents: documents context changes
- ai: AI context changes
- dashboard: dashboard context changes
```

## PR Size Limits

- Max 400 lines changed per PR
- Max 10 files changed per PR
- If PR exceeds limits, split into multiple PRs
- Each PR must pass all CI checks before merge

## Merge Order

1. Smallest, least risky PRs first
2. Infrastructure changes before business logic changes
3. Interface definitions before implementations
4. Base classes before migrations to them
5. Tests alongside implementation (not after)

## Tagging Strategy

```
v{phase}.{major}.{minor}

Examples:
- v1.4.0 — Phase 1.4 complete (adapter interfaces)
- v1.5.0 — Phase 1.5 complete (DI container)
- v2.0.0 — Phase 2 complete (infrastructure)
- v3.0.0 — Phase 3 complete (identity)
```

## Rollback Strategy

1. **Immediate:** Revert the specific commit that introduced the issue
2. **Verification:** Re-run CI to confirm rollback
3. **Root Cause:** Identify the issue in the rolled-back commit
4. **Fix:** Address the issue in a new branch
5. **Re-attempt:** Apply the fix with additional safeguards

Rollback commands:
```bash
# Revert a single commit
git revert {commit-hash}

# Revert multiple commits (if needed)
git revert --no-commit {oldest-hash}^..{newest-hash}
git commit -m "chore: rollback Phase N changes due to {reason}"
```

## Rollback Trigger Conditions

Rollback is triggered when any of the following conditions are met:

1. CI failure persists >24 hours
2. Security scan failure (bandit, semgrep, Trivy)
3. Coverage below 90%
4. Migration failure in staging
5. Business behavior regression detected

When a rollback trigger fires:
1. Halt all parallel work in the affected phase
2. Notify the Architecture Review Board
3. Revert to the last known good state
4. Conduct root cause analysis before re-attempting

---

# CI/CD Configuration

# CI/CD Configuration

## When CI Should Pass

- Every PR must pass all CI checks before merge
- Every push to `main` must pass all CI checks
- Architecture guard must pass on every PR that modifies workflows or architecture scripts

## When Architecture Validation Runs

- On every PR that modifies `.github/workflows/**`
- On every PR that modifies `scripts/architecture_contract.py`
- Daily scheduled run (cron: `0 0 * * *`)
- On every push to `main`/`master`

## When Import-Linter Runs

- On every PR (via `lint.yml`)
- On every push to `main`/`master`
- Import-linter violations block CI

## When Sonar Runs

- On every PR (via `quality.yml`)
- After test shards are combined
- Coverage report uploaded to SonarCloud

## When Security Scans Run

- On every PR (via `security.yml`):
  - bandit
  - semgrep
  - Trivy
- Daily (via `security-deep.yml`):
  - Scorecard
- Weekly (via `sbom.yml`):
  - SBOM generation
  - Grype
  - OSV

## When Deployment Readiness Runs

- On every PR (via `deploy-readiness.yml`)
- Checks: migrations, settings validation, health endpoints

## CI Jobs Required for Each Phase

| Phase | Required CI Jobs |
|-------|------------------|
| 1 | lint, test, architecture-guard, security, quality |
| 2 | lint, test, architecture-guard, security, quality |
| 3 | lint, test, architecture-guard, security, quality, import-linter |
| 4 | lint, test, architecture-guard, security, quality, import-linter |
| 5+ | lint, test, architecture-guard, security, quality, import-linter, contract-tests |

---

# Security Considerations

## Security-Sensitive Tasks

The following tasks are marked as security-sensitive and require additional review:

| Task ID | Title | Threat Addressed | OWASP Mapping | Verification Method |
|---------|-------|------------------|---------------|---------------------|
| 1.5.4 | Migrate AuthService to DI | Authentication bypass | A01: Broken Access Control | Auth flow integration tests |
| 1.9.2 | Extract OTP Logic | OTP bypass | A02: Cryptographic Failures | OTP flow tests |
| 1.9.3 | Extract Auth Logic | Authentication bypass | A01: Broken Access Control | Auth flow integration tests |
| 2.5 | Implement S3StorageAdapter | Unauthorized file access | A01: Broken Access Control | S3 ACL verification |
| 8.2 | Implement ManualPaymentAdapter | Payment fraud | A04: Insecure Design | Payment flow tests |
| 8.3 | Implement Webhook Idempotency | Webhook replay attacks | A08: Software and Data Integrity Failures | Webhook idempotency tests |
| 9.1 | Implement EmailAdapter | Email injection | A03: Injection | Email security tests |
| 9.2 | Implement FCMAdapter | Device token leakage | A01: Broken Access Control | FCM security tests |
| 1.9.7 | Extract Password Logic to PasswordService | Password reset token exposure | A02: Cryptographic Failures | Password reset flow tests, token expiry tests, security scan validation |
| 3.2 | Move User model to identity/ | AUTH_USER_MODEL migration risk | A01: Broken Access Control | Authentication integration tests, migration validation tests |
| 3.5 | Move Auth Views to identity/ | Auth endpoint protection bypass | A01: Broken Access Control | Auth endpoint security tests, permission tests |
| 8.5 | Implement Payment State Machine | Unauthorized payment state transitions | A04: Insecure Design | State transition tests, invalid transition rejection tests |
| 9.3 | Implement InAppAdapter | User-scoped notification leakage | A01: Broken Access Control | Tenant isolation tests, user authorization tests |

## Security Review Requirements

All security-sensitive tasks require:
1. Security review by at least one team member
2. OWASP mapping documented
3. Verification tests written
4. Security scan passes (bandit, semgrep)

---

# Master Implementation Timeline

## Estimated Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Pre-Implementation | 1 week | Week 1 | Week 1 |
| Phase 1 (Shared Foundation) | 6–8 weeks | Week 2 | Week 9 |
| Phase 2 (Infrastructure) | 3–4 weeks | Week 10 | Week 13 |
| Phase 3 (Identity) | 4–5 weeks | Week 14 | Week 18 |
| Phase 4 (Subscription) | 4–5 weeks | Week 19 | Week 23 |
| Phase 5 (Property) | 2–3 weeks | Week 24 | Week 26 |
| Phase 6 (Renter) | 2–3 weeks | Week 27 | Week 29 |
| Phase 7 (Rent) | 3–4 weeks | Week 30 | Week 33 |
| Phase 8 (Payments) | 5–6 weeks | Week 34 | Week 39 |
| Phase 9 (Notification) | 3–4 weeks | Week 40 | Week 43 |
| Phase 10 (Documents) | 3–4 weeks | Week 44 | Week 47 |
| Phase 11 (AI) | 3–4 weeks | Week 48 | Week 51 |
| Phase 12 (Dashboard) | 3–4 weeks | Week 52 | Week 55 |
| Phase 13 (Architecture Enforcement) | 2–3 weeks | Week 56 | Week 58 |
| **Total** | **~58 weeks** | | |

> **Timeline Note:** The 6–8 week estimate for Phase 1 assumes 2–3 developers working in parallel on independent tasks. Single developer execution is expected to take approximately 12–15 weeks for Phase 1.

---

# Critical Path

```
Phase 1.4 (Adapter Interfaces) [Weeks 2–3]
    ↓
Phase 1.5 (DI Container) [Weeks 3–5]
    ↓
Phase 1.6 (Event Bus) [Weeks 5–7]
    ↓
Phase 1.7 (Settings Split) [Weeks 2–4] (parallel with 1.4–1.6)
    ↓
Phase 1.8 (Repository Pattern) [Weeks 4–6] (parallel with 1.5–1.7)
    ↓
Phase 1.9 (Extract Business Logic from Views) [Weeks 6–9] (parallel with 1.6–1.8)
    ↓
Phase 2 (Infrastructure) [Weeks 10–13]
    ↓
Phase 3 (Identity) [Weeks 14–18]
    ↓
Phase 4 (Subscription) [Weeks 19–23]
    ↓
Phase 5 (Property) [Weeks 24–26]
    ↓
Phase 6 (Renter) [Weeks 27–29]
    ↓
Phase 7 (Rent) [Weeks 30–33]
    ↓
Phase 8 (Payments) [Weeks 34–39]
    ↓
Phase 9 (Notification) [Weeks 40–43]
    ↓
Phase 10 (Documents) [Weeks 44–47]
    ↓
Phase 11 (AI) [Weeks 48–51]
    ↓
Phase 12 (Dashboard) [Weeks 52–55]
    ↓
Phase 13 (Architecture Enforcement) [Weeks 56–58]
```

**Note:** Phases 1.4, 1.5, 1.6, 1.7, 1.8, and 1.9 can be executed in parallel where dependencies allow, reducing total Phase 1 duration from 24 weeks to 8 weeks.

---

# Top 10 Highest-Risk Tasks

| Rank | Task ID | Title | Risk Level | Mitigation |
|------|---------|-------|------------|------------|
| 1 | 3.2 | Move `User` model to `identity/` | HIGH | Requires `AUTH_USER_MODEL` change; migration must preserve data |
| 2 | 3.6 | Update all imports across codebase | HIGH | Large diff; risk of missed imports |
| 3 | 4.2 | Move subscription models to `subscription/` | HIGH | Migration must preserve subscription state |
| 4 | 4.5 | Update all imports across codebase | HIGH | Large diff; risk of missed imports |
| 5 | 5.1 | Complete repository pattern in `properties/` | MEDIUM | Risk of breaking existing queries |
| 6 | 8.3 | Implement webhook idempotency | HIGH | Security-critical; must prevent replay attacks |
| 7 | 11.1 | Consolidate `smartbot/` and `ai_assistant/` | HIGH | Risk of breaking AI features |
| 8 | 12.2 | Implement selective CQRS for dashboards | HIGH | Complex pattern; risk of data inconsistency |
| 9 | 1.5.2 | Implement `ServiceContainer` | MEDIUM | Risk of circular dependencies |
| 10 | 1.9.1 | Audit `core/views.py` for business logic | MEDIUM | 566-line file; risk of missing logic |

---

# Top 10 Highest-Impact Tasks

| Rank | Task ID | Title | Impact Level | Reason |
|------|---------|-------|--------------|--------|
| 1 | 1.4.1 | Define `PaymentGateway` interface | HIGH | Unblocks all payment adapters |
| 2 | 1.4.2 | Define `NotificationChannel` interface | HIGH | Unblocks all notification adapters |
| 3 | 1.5.2 | Implement `ServiceContainer` | HIGH | Enables DI across all services |
| 4 | 1.6.1 | Implement `InProcessEventBus` | HIGH | Enables cross-context communication |
| 5 | 1.8.2 | Implement `UserRepository` | HIGH | Enables repository pattern for auth |
| 6 | 3.1 | Create `identity/` package structure | HIGH | Unblocks all identity extraction |
| 7 | 4.1 | Create `subscription/` package structure | HIGH | Unblocks all subscription extraction |
| 8 | 8.2 | Implement `ManualPaymentAdapter` | HIGH | Core payment flow |
| 9 | 8.3 | Implement webhook idempotency | HIGH | Security-critical for payments |
| 10 | 9.7 | Implement notification dispatch service | HIGH | Centralizes notification logic |

---

# Recommended Git Milestones

| Milestone | Tag | Phase | Description |
|-----------|-----|-------|-------------|
| 1 | v1.4.0 | Phase 1.4 | Adapter interfaces defined |
| 2 | v1.5.0 | Phase 1.5 | DI container implemented |
| 3 | v1.6.0 | Phase 1.6 | Event bus implemented |
| 4 | v1.7.0 | Phase 1.7 | Settings split complete |
| 5 | v1.8.0 | Phase 1.8 | Repository pattern complete |
| 6 | v1.9.0 | Phase 1.9 | Business logic extracted from views |
| 7 | v2.0.0 | Phase 2 | Infrastructure adapters complete |
| 8 | v3.0.0 | Phase 3 | Identity context isolated |
| 9 | v4.0.0 | Phase 4 | Subscription context isolated |
| 10 | v5.0.0 | Phase 5 | Property context isolated |
| 11 | v6.0.0 | Phase 6 | Renter context isolated |
| 12 | v7.0.0 | Phase 7 | Rent context isolated |
| 13 | v8.0.0 | Phase 8 | Payments context isolated |
| 14 | v9.0.0 | Phase 9 | Notification context isolated |
| 15 | v10.0.0 | Phase 10 | Documents context isolated |
| 16 | v11.0.0 | Phase 11 | AI context isolated |
| 17 | v12.0.0 | Phase 12 | Dashboard context isolated |
| 18 | v13.0.0 | Phase 13 | Architecture enforcement complete |

---

# Implementation Readiness Score

| Category | Score | Weight | Weighted Score |
|----------|-------|--------|----------------|
| Documentation | 9/10 | 15% | 1.35 |
| CI/CD | 10/10 | 15% | 1.50 |
| Testing Infrastructure | 9/10 | 15% | 1.35 |
| Architecture Clarity | 8/10 | 15% | 1.20 |
| Team Readiness | 7/10 | 10% | 0.70 |
| Codebase Maturity | 7/10 | 10% | 0.70 |
| Security Posture | 8/10 | 10% | 0.80 |
| Dependency Management | 9/10 | 10% | 0.90 |
| **Total** | | **100%** | **8.50/10** |

**Readiness Level:** READY — Implementation can proceed

---

# Final Go / No-Go Decision

## ✅ GO

The repository is **READY** for implementation.

**Evidence:**
- Phase 1.3 Migration Readiness Certification: COMPLETE
- Documentation Guardian: PASS (exit code 0)
- CI pipeline: GREEN
- Zero broken links in active documentation
- All Tier 1 canonical documents present
- Import-linter baseline: PASS
- ADR set: FROZEN
- Rollback runbook: PREPARED

**Conditions:**
1. Pre-implementation tasks (PRE-1 through PRE-7) must complete before Phase 1 starts
2. Each phase must pass its exit criteria before proceeding to the next phase
3. CI must remain green throughout implementation
4. Coverage must remain ≥90% throughout implementation

## Phase 1 Review Gate

After Phase 1.9 completion, the following criteria must be met before proceeding to Phase 2:

- All Phase 1 exit criteria passed
- Coverage ≥90%
- No import-linter violations
- Security reviews completed for all security-sensitive tasks
- ADR references validated
- All contract tests pass

**Go/No-Go Gate:** After Phase 1.9, conduct a mid-implementation review. If Phase 1 is not complete by Week 10, escalate to architecture review board.

---

# Appendix A: Task Summary by Phase

| Phase | Tasks | Total Effort | P0 Tasks |
|-------|-------|--------------|----------|
| Pre-Implementation | 7 | 9h | 3 |
| Phase 0 | 0 (complete) | 0h | 0 |
| Phase 1 | 33 | 118h | 12 |
| Phase 2 | 9 | 46h | 4 |
| Phase 3 | 9 | 46h | 6 |
| Phase 4 | 8 | 42h | 5 |
| Phase 5 | 5 | 30h | 3 |
| Phase 6 | 3 | 16h | 1 |
| Phase 7 | 4 | 24h | 2 |
| Phase 8 | 7 | 42h | 4 |
| Phase 9 | 9 | 42h | 4 |
| Phase 10 | 5 | 26h | 2 |
| Phase 11 | 4 | 22h | 1 |
| Phase 12 | 4 | 26h | 2 |
| Phase 13 | 5 | 30h | 3 |
| **Total** | **107** | **519h** | **48** |

---

# ADR Authority and Reference

## Canonical ADR Location

**Directory:** `docs/architecture/adr/`

`docs/architecture/adr/` contains all accepted architecture decisions and is the authoritative source for implementation decisions. All new ADRs must be created here. All references in this checklist point to this location.

## Legacy / Baseline ADR Location

**Directory:** `architecture/adr/`

`architecture/adr/` contains initial baseline templates and historical migration documents (ADRs 000–003). It must not be used as the source of truth for new implementation decisions.

## ADR Reference Policy

- All future ADR references in this document point to `docs/architecture/adr/`
- The `architecture/adr/` collection is preserved for historical reference only
- New ADRs use the template at `docs/ai-governance/AI-Decision-Record.md`
- The canonical ADR index is at `docs/architecture/adr/README.md`

---

# Appendix B: Reference ADRs

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Modular Monolith Architecture | Accepted |
| ADR-002 | Repository Pattern for Data Access | Accepted |
| ADR-003 | Service Layer as Business Logic Entry Point | Accepted |
| ADR-004 | No Business Logic in Views | Accepted |
| ADR-005 | Domain Events for Cross-Context Communication | Accepted |
| ADR-006 | Import Rules and Architecture Enforcement | Accepted |
| ADR-007 | Testing Strategy (4-tier) | Accepted |
| ADR-008 | Shared Module Rules | Accepted |
| ADR-009 | Configuration Strategy (split settings) | Accepted |
| ADR-010 | Payment Integration Strategy | Accepted |
| ADR-011 | Notification Strategy | Accepted |
| ADR-012 | Document Generation Strategy | Accepted |
| ADR-013 | Error Handling Strategy | Accepted |
| ADR-014 | Background Jobs Strategy | Accepted |
| ADR-015 | API Versioning Strategy | Accepted |
| ADR-016 | Feature Flags for Optional Integrations | Accepted |
| ADR-017 | CQRS for Read/Write Separation (selective) | Accepted |
| ADR-018 | Dependency Injection Strategy | Accepted |
| ADR-019 | Event Bus Implementation | Accepted |
| ADR-020 | Vertical Slice Architecture | Accepted |
| ADR-021 | Audit Logging | Accepted |
| ADR-022 | Cache Strategy | Accepted |
| ADR-023 | Search Strategy | Accepted |

---

# Appendix C: Reference Documents

- `architecture/ROADMAP.md` — Phase definitions and infrastructure stages
- `architecture/CODING_STANDARDS.md` — Folder conventions and naming rules
- `architecture/module-boundaries.md` — Bounded context definitions
- `architecture/dependency-rules.md` — Dependency direction rules
- `architecture/import-layers.md` — Layered import rules
- `architecture/ARCHITECTURE_PRINCIPLES.md` — 18 architecture principles
- `import-linter.ini` — Import-linter configuration
- `PHASE_1_3_MIGRATION_READINESS_CERTIFICATION.md` — Current certification
- `PHASE_2A_ARTIFACT_DEPENDENCY_AUDIT.md` — Artifact dependency map

---

# Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-18 | Kilo | Initial implementation master checklist |

**Review Cycle:** This document is reviewed at the end of each phase.
**Change Control:** Changes require Architecture Review Board approval.
**Next Review:** End of Phase 1

---

*End of RentSecureBE Implementation Master Checklist*
