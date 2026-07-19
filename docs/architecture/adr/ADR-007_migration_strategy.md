# ADR-007: Migration Strategy

**Status:** Accepted
**Date:** 2026-07-19
**Deciders:** Chief Software Architect, Staff Engineer, Platform Team Lead, DevOps Engineer
**Supersedes:** ADR-008 (v1.0 — Incremental Migration Strategy)

---

## Context

The v1.0 migration strategy proposed:
- Moving all apps into a parent `apps/` directory (rejected: hidden mega-migration)
- Changing `AUTH_USER_MODEL` from `core.User` to `identity.User` in Phase 5 (rejected: architecturally impossible in Django)
- Deferring `rent/` extraction to Stage 2 (rejected: phantom context)
- No Phase -1 for breaking circular dependencies
- No data migration plan for `OwnerBankDetails` and `NotificationPreference` moves

The v1.1 migration strategy must address these gaps:
- No mega-migrations (`apps/` parent directory rejected)
- No impossible `AUTH_USER_MODEL` change (`core.User` stays permanent)
- No phantom `rent/` context (rent logic stays in `properties/`)
- Phase -1 added to break circular dependencies before structural changes
- Explicit data migration plans for model moves
- Only one breaking change (Phase 5 → v2.0.0)

---

## Decision

RentSecureBE uses an **8-phase incremental migration** from v1.0 to v1.1 target state. All phases before Phase 5 are additive or internal refactors. Phase 5 is the **only breaking change** and is released as v2.0.0.

### Phase Overview

| Phase | Duration | Goal | Breaking Changes |
|-------|----------|------|------------------|
| **Phase -1** | Week 1 | Break circular dependencies | None |
| **Phase 0** | Week 2-3 | Foundation & Critical Fixes | None |
| **Phase 1** | Week 4-6 | Extract Identity Services | None |
| **Phase 2** | Week 7-9 | Extract Subscription | None |
| **Phase 3** | Week 10-12 | Extract Payment | None |
| **Phase 4** | Week 13-14 | Extract Dashboard & Notification | None |
| **Phase 5** | Week 15-16 | Deprecate Core | **YES — v2.0.0** |
| **Phase 6** | Week 17-20 | Optimization | None |

### Core Principles

1. **Incremental:** Each phase delivers working software. No big-bang migrations.
2. **Production-Safe:** Every change is backward-compatible. Old URLs, imports, and APIs remain valid during transition.
3. **Zero Downtime:** No phase requires application downtime. Deployments are rolling updates.
4. **Test-Driven:** Every phase includes tests before, during, and after implementation.
5. **Rollback-Ready:** Every phase has a tested rollback procedure.
6. **Architecture-Enforced:** import-linter and architecture tests run on every commit.

### Data Migration Rules

| Rule | Description |
|------|-------------|
| **Additive first** | New tables/columns added before old ones removed |
| **Backward-compatible** | Old and new schema coexist during transition |
| **Reversible** | Every migration has a reverse operation |
| **Tested** | Every migration tested forward and backward in CI |
| **Retention** | Old tables retained for 1 release cycle before deletion |

### Specific Data Migrations

| Model Move | Source | Target | Rollback |
|-----------|--------|--------|----------|
| `OwnerBankDetails` | `core_ownerbankdetails` | `payment_ownerbankdetails` | Keep `core_ownerbankdetails` for 1 release cycle |
| `NotificationPreference` | `core_notificationpreference` | `notification_notificationpreference` | Keep `core_notificationpreference` for 1 release cycle |
| Subscription models | `core_subscriptionplan`, `core_usersubscription`, `core_addonpurchase`, `core_planfeaturelimit`, `core_usagelimit` | `subscription_*` | Keep `core_*` for 1 release cycle |

### Breaking Change Policy

- Breaking changes are ONLY allowed in Phase 5
- Phase 5 must be released as a major version (v2.0.0)
- `core/` must remain in `INSTALLED_APPS` as deprecated shims for 6 months post-Phase 5
- LTS branch must be maintained for 6 months
- Migration guide (`docs/migration/v1-to-v2.md`) published before v2.0.0 release

### Rollback Policy

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

---

## Alternatives Considered

### 1. Big-Bang Migration

**Description:** Migrate all apps and models in a single release.

**Pros:**
- Fast (one release instead of 8 phases)
- No need to maintain backward-compatible shims

**Cons:**
- Extremely high risk (all changes at once)
- Difficult to debug issues (which change caused the problem?)
- Long feature branch (merge conflicts, stale code)
- Production outage likely during migration
- No rollback granularity

**Decision:** Rejected. Too risky for production system with financial data.

### 2. Skip Phase -1 (Break Cycles)

**Description:** Start with Phase 0 and break circular dependencies as they are encountered.

**Pros:**
- Faster start (no separate Phase -1)

**Cons:**
- Circular dependencies worsen during Phase 0-4 refactors
- Import errors at application startup
- Fragile refactoring (moving code while cycles exist)
- Phase 0 changes may introduce new cycles

**Decision:** Rejected. Circular dependencies must be broken before any structural changes.

### 3. Incremental Migration with Phase -1 (Selected)

**Description:** 8 phases over 20 weeks. Phase -1 breaks cycles. Phases 0-4 are additive. Phase 5 is breaking change (v2.0.0). Phase 6 is optimization.

**Pros:**
- Each phase delivers working software
- Backward-compatible until Phase 5
- Rollback is tested per phase
- Circular dependencies eliminated before they cause problems
- Data migrations are additive (old tables retained)
- Phase 5 is the only breaking change (clear upgrade path for consumers)

**Cons:**
- Longer timeline (20 weeks / 5 months)
- Requires discipline to maintain backward-compatible shims
- `core/` remains larger than desired during Phases 0-4
- Team must maintain two import paths during transition

**Decision:** Accepted. Best balance of risk and progress.

---

## Consequences

### Positive
- Zero production incidents target (no downtime, no data loss)
- Each phase is independently deployable and testable
- Rollback is tested and documented per phase
- Phase 5 breaking change is clearly signaled (v2.0.0)
- LTS branch provides safety net for consumers
- Data migrations are reversible (old tables retained)

### Negative
- 20-week timeline is long (requires sustained team focus)
- Backward-compatible shims add code volume during transition
- Team must maintain two import paths during Phases 0-4
- Phase 5 rollback is complex (2-4 hours, requires backup restore)

### Neutral
- Phase -1 is a separate 1-week effort (not merged with Phase 0)
- Phase 6 optimization work can be deferred if team capacity is constrained
- Cross-cutting tasks (CI/CD, security, documentation) run throughout all phases

---

## Migration Notes

### Phase -1: Break Circular Dependencies (Week 1)

**Goal:** Eliminate all 4 circular dependency cycles before any structural changes.

**Tasks:**
1. Move `type_compat.py` from `rentsecure_be/` to `shared/` (breaks `core ↔ rentsecure_be` and `properties ↔ rentsecure_be`)
2. Extract `NotificationService.send_otp()` to a shared interface (breaks `core → notification`)
3. Move `rent_notify_service.py` domain methods to `properties/services/` (breaks `properties ↔ notification`)
4. Move `OwnerBankDetails` from `core/models.py` to `payments/models.py` (breaks `core → payment`)

**Rollback:** Revert single PR. All changes are additive (file moves + import updates). No data changes.

### Phase 0: Foundation & Critical Fixes (Week 2-3)

**Goal:** Fix all Critical findings without breaking production.

**Key Tasks:**
- Register `payments` in `INSTALLED_APPS`
- Move `OwnerBankDetails` to `payments/models.py` with encrypted fields
- Move `NotificationPreference` to `notification/models.py`
- Move webhooks to `payments/views/webhooks.py` with idempotency
- Split `core/views.py` into 4 focused modules
- Move root management commands to app directories
- Rewrite `import-linter.ini` without `rentsecure_be` as allowed layer
- Add architecture regression tests
- Add migration rollback tests to CI

**Rollback:** `git revert` + `migrate --reverse`. Old tables remain.

### Phase 1-4: Service Extraction (Week 4-14)

**Goal:** Extract services from `core/` to their owning bounded contexts.

**Pattern per phase:**
1. Create target app `services/` package
2. Move service files to target app
3. Update views to import from target app
4. Update all cross-app imports
5. Deprecate old files in `core/services/` (shims or removed)
6. Add tests for new location

**Rollback:** Revert phase PR. Old services in `core/services/` remain.

### Phase 5: Deprecate Core (Week 15-16) — BREAKING CHANGE

**Goal:** Remove `core/` as a God app. Released as v2.0.0.

**Key Tasks:**
- Remove all views from `core/views/`
- Remove `OwnerBankDetails`, `NotificationPreference`, subscription models from `core/models.py`
- Remove `core/services/` (all remaining services)
- Remove `core/serializers.py` and `core/urls.py`
- Rename `core/` to `identity/` (keep as model container)
- Create `docs/migration/v1-to-v2.md`
- Create ADR for Phase 5 breaking changes
- Freeze v1.x LTS branch
- Run full regression suite
- Deploy to staging (3 days validation)
- Security audit
- Deploy to production (blue-green)
- Monitor for 48 hours
- Tag v2.0.0

**Rollback:** Restore from backup + deploy previous version. 2-4 hours. Cannot reverse table-drop migration.

### Phase 6: Optimization (Week 17-20)

**Goal:** Add missing infrastructure.

**Key Tasks:**
- Implement `InProcessEventBus` in `platform/events/`
- Add repositories for complex queries
- Add Redis cache backend
- Consolidate `ai_assistant/` and `smartbot/` or remove dead code
- Document bounded context APIs
- Add performance benchmarks

**Rollback:** Revert individual PRs. No data changes.

---

## Future Evolution

### Stage 2 (Trigger: >500 payments/month or >10 hours/week manual verification)
- Evaluate extracting `payment/` as first microservice
- Introduce message broker (Redis/Celery) for async events
- Service mesh for inter-service communication

### Stage 3 (Trigger: Team >15 engineers or >50,000 users)
- Evaluate extracting `property/` and `notification/` as microservices
- Introduce API gateway
- Distributed tracing and observability

### Long-term
- Migration strategy remains the template for future major versions
- Phases become shorter as team gains experience
- Automation increases (more migration scripts, fewer manual steps)

---

## References

- [Architecture v1.1 Release Candidate — Part 2](../../../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Implementation Master Plan — All Phases](../../../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Phase 0 Execution Plan](../../../PHASE_0_EXECUTION_PLAN.md)
- [Bounded Context Strategy](./ADR-001_bounded_context_strategy.md)
- [Identity Strategy](./ADR-002_identity_strategy.md)
- [Payment Architecture](./ADR-004_payment_architecture.md)
