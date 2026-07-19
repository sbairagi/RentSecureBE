# ADR-003: Subscription Strategy

**Status:** Accepted
**Date:** 2026-07-19
**Deciders:** Chief Software Architect, Staff Engineer, Platform Team Lead
**Supersedes:** ADR-003 (v1.0 — Service Layer, partial)

---

## Context

Subscription logic in RentSecureBE is currently scattered across two locations:
- `core/models.py`: `SubscriptionPlan`, `UserSubscription`, `AddOnPurchase`, `PlanFeatureLimit`, `UsageLimit`
- `core/services/`: `SubscriptionService`, `UsageLimitService`
- `properties/feature_enforcer.py`: `FeatureEnforcer` (product-team-owned file containing platform logic)

This scattering creates several problems:
- **Ownership ambiguity:** Product Team owns `properties/` but `FeatureEnforcer` controls feature access, which is a platform concern
- **Circular dependency risk:** `properties/` imports from `core/` for subscription models, and `core/` imports from `properties/` for unit management
- **Testing difficulty:** Subscription logic is split across two apps, requiring integration tests across boundaries
- **Extraction risk:** Removing subscription models from `core/` in Phase 5 requires moving 5 tables and updating 10+ importers

The v1.1 architecture requires a single, clear owner for all subscription concerns.

---

## Decision

RentSecureBE uses a **dedicated `subscription/` bounded context** for all subscription and feature-enforcement logic.

### Key Rules

1. **`subscription/` owns all subscription models:** `SubscriptionPlan`, `UserSubscription`, `AddOnPurchase`, `PlanFeatureLimit`, `UsageLimit`
2. **`subscription/` owns all subscription services:** `SubscriptionService`, `UsageLimitService`, `FeatureEnforcer`
3. **`properties/` does not import subscription models directly.** It imports `FeatureEnforcer` from `subscription/services/`.
4. **`core/` does not contain subscription models or services after Phase 2.**
5. **Subscription data migration is additive:** old `core_subscription*` tables remain for one release cycle before deletion in Phase 5.

### Extraction Sequence

| Phase | Action |
|-------|--------|
| Phase 0 | No subscription work (focus on critical fixes) |
| Phase 1 | Prepare `identity/` extraction (no subscription work) |
| Phase 2 | Create `subscription/services/`; move `SubscriptionService`, `UsageLimitService`, `FeatureEnforcer`; update all cross-app imports; remove `properties/feature_enforcer.py` |
| Phase 5 | Move subscription tables from `core/` to `subscription/` via data migration; delete old `core_*` tables |

### Ownership

| Component | Owner |
|-----------|-------|
| `subscription/models.py` | Platform Team |
| `subscription/services/` | Platform Team |
| `subscription/views/` (future) | Platform Team |
| Feature enforcement logic | Platform Team |

---

## Alternatives Considered

### 1. Keep Subscription Logic in `core/`

**Description:** Leave `SubscriptionPlan`, `UserSubscription`, etc. in `core/models.py` and `core/services/`.

**Pros:**
- No migration effort
- Simple for current team size

**Cons:**
- `core/` remains a God app with 5+ responsibilities
- Ownership ambiguity between Platform and Product teams
- `properties/feature_enforcer.py` creates a hidden dependency on `core/`
- Future extraction becomes harder as `core/` grows

**Decision:** Rejected. `core/` must shrink to identity-only models.

### 2. Keep `FeatureEnforcer` in `properties/`

**Description:** Move subscription models to `subscription/` but leave `FeatureEnforcer` in `properties/` because it was "always there."

**Pros:**
- No need to update `properties/` imports
- Product Team retains ownership of feature enforcement

**Cons:**
- `FeatureEnforcer` is platform logic (subscription enforcement), not property logic
- Creates circular dependency: `properties/` imports from `subscription/` for models, `subscription/` imports from `properties/` for `FeatureEnforcer`
- Violates single-responsibility: `properties/` should not control subscription features

**Decision:** Rejected. `FeatureEnforcer` is a platform service.

### 3. Dedicated `subscription/` Context (Selected)

**Description:** Create `subscription/` bounded context containing all subscription models, services, and feature enforcement.

**Pros:**
- Clear ownership: Platform Team owns all subscription logic
- Single source of truth for subscription state
- `properties/` imports `FeatureEnforcer` as a service, not as a domain concern
- `core/` shrinks as planned
- Easy to test subscription flows in isolation

**Cons:**
- Requires updating 10+ importers in `properties/`
- Data migration for subscription tables in Phase 5 is medium-risk
- `properties/` team must coordinate with Platform Team for feature changes

**Decision:** Accepted. Best balance of ownership clarity and migration safety.

---

## Consequences

### Positive
- Platform Team owns the complete subscription flow
- `core/` shrinks as planned (models move to `subscription/` in Phase 5)
- `properties/` no longer contains platform logic (`FeatureEnforcer` removed)
- Subscription logic is testable in isolation
- Data migration is additive (old tables retained for one release cycle)

### Negative
- Requires updating 10+ importers in `properties/` (Phase 2 effort)
- Data migration in Phase 5 drops `core_subscription*` tables (irreversible)
- Product Team loses direct control over feature enforcement (must request Platform Team changes)

### Neutral
- `subscription/` does not have views in Year 1 (admin only via Django admin or management commands)
- `UsageLimitService` is extracted alongside `SubscriptionService` (they are cohesive)
- Phase 2 is low-risk (no data changes, only service moves)

---

## Migration Notes

### Phase 2: Service Extraction (No Data Migration)

**Tasks:**
1. Create `subscription/services/__init__.py`
2. Move `SubscriptionService` from `core/services/subscription_service.py` to `subscription/services/subscription_service.py`
3. Move `UsageLimitService` from `core/services/usage_limit_service.py` to `subscription/services/usage_limit_service.py`
4. Move `FeatureEnforcer` from `properties/feature_enforcer.py` to `subscription/services/feature_enforcer.py`
5. Update all 10+ `properties/` importers to use `subscription/services/feature_enforcer.py`
6. Update `core/views/subscription_views.py` to import from `subscription/services/`
7. Update all cross-app imports of `core.services.subscription_service` and `core.services.usage_limit_service`
8. Remove `properties/feature_enforcer.py`
9. Add `subscription/tests/unit/` and `subscription/tests/integration/`

**Rollback:** Revert Phase 2 PR. `core/services/` and `properties/feature_enforcer.py` remain.

### Phase 5: Model Migration (Data Migration)

**Tasks:**
1. Create `subscription/models.py` with `SubscriptionPlan`, `UserSubscription`, `AddOnPurchase`, `PlanFeatureLimit`, `UsageLimit`
2. Create data migration: copy `core_subscription*` → `subscription_*`
3. Keep old `core_*` tables for one release cycle
4. Update all remaining `core.models.SubscriptionPlan` imports to `subscription.models.SubscriptionPlan`
5. Create irreversible migration to drop `core_subscription*` tables
6. Test on production-like data before merge

**Rollback:** Restore from backup. Cannot reverse table-drop migration.

---

## Future Evolution

### Short-term (Phase 6)
- `subscription/` may introduce usage analytics and quota management endpoints
- `FeatureEnforcer` may support per-tenant overrides and grace periods

### Medium-term (Stage 2)
- If subscription volume grows, `subscription/` may become a microservice
- Integration with billing gateways (Cashfree, Razorpay) for auto-renewal
- Webhook-based subscription state synchronization

### Long-term
- `subscription/` remains a stable bounded context
- Add-on purchases may become a separate `billing/` context if complexity grows
- Feature flags (per-user, per-tenant) replace global boolean flags

---

## References

- [Architecture v1.1 Release Candidate — Phase 2](../../../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Implementation Master Plan — Phase 2](../../../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Migration Strategy](./ADR-007_migration_strategy.md)
- [Testing Strategy](./ADR-009_testing_strategy.md)
