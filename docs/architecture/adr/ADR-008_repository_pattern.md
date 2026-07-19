# ADR-008: Repository Pattern

**Status:** Accepted
**Date:** 2026-07-19
**Deciders:** Chief Software Architect, Staff Engineer, Platform Team Lead
**Supersedes:** ADR-002 (v1.0 — Repository Pattern)

---

## Context

In v1.0, the repository pattern was declared as architecture policy ("use repositories selectively") but provided no enforcement mechanism. The `properties/repositories/` directory exists with dead modules, and no criteria existed for when to use a repository versus direct ORM access.

The v1.1 review found:
- `properties.models` is imported by 74 modules (highest fan-in in the codebase)
- `core.models` is imported by 63 modules
- Query logic is scattered across services, leading to inconsistent optimization
- No centralized query patterns make it hard to add caching or switch persistence

The repository pattern must have clear criteria, clear ownership, and a phased introduction that doesn't overburden the team during the 20-week migration.

---

## Decision

RentSecureBE uses a **selective repository pattern** introduced in Phase 6.

### Decision Tree

```
Use repository if:
  - Query spans 3+ tables AND
  - Query is used by 3+ services
  → Create repository in owning app's repositories/ directory

Use ORM if:
  - Query touches 1-2 tables OR
  - Query is used by 1-2 services
  → Use Django ORM directly in service
```

### Repository Ownership

| Repository | Owning App | Purpose | Phase |
|-----------|-----------|---------|-------|
| `OwnerReportingRepository` | `properties/repositories/` | Complex aggregation queries for owner reports | Phase 6 |
| `RentRecordRepository` | `properties/repositories/` | Complex rent record queries with filters | Phase 6 |
| `DashboardMetricRepository` | `dashboard/repositories/` | Dashboard metric aggregation | Phase 6 |

### Repository Rules

1. **Repositories live in the owning app's `repositories/` directory.** E.g., `properties/repositories/owner_reporting_repository.py`.
2. **Repository interfaces are implicit** (Python protocols or abstract base classes in `shared/interfaces.py` if needed).
3. **Repositories use Django ORM** under the hood. They do not introduce a new query language.
4. **Services depend on repositories** (injected via constructor or method parameter).
5. **Views never call repositories directly.** Views call services, services use repositories.
6. **No repository for simple CRUD.** Use Django ORM directly for single-table operations.
7. **All repositories have unit tests** with test database fixtures.

### Why Phase 6

Repositories are introduced in Phase 6 (not earlier) because:
- Phases 0-5 focus on structural refactoring (app extraction, model moves)
- Repositories add abstraction overhead; introducing them during service extraction would double the migration effort
- The team needs to stabilize the new app boundaries before adding query abstractions
- Phase 6 is the optimization phase, which is the right time to introduce query patterns

---

## Alternatives Considered

### 1. Always Use Repositories (v1.0 Approach)

**Description:** Every data access goes through a repository, even for simple CRUD.

**Pros:**
- Consistent pattern across codebase
- Easy to mock for testing
- Centralized query optimization

**Cons:**
- Massive over-engineering for Year 1
- Every simple query requires interface + implementation + tests
- Developer velocity drops significantly
- Repositories for single-table CRUD add no value

**Decision:** Rejected. Too much boilerplate for current needs.

### 2. Never Use Repositories

**Description:** Continue using Django ORM directly in services. No repository abstraction.

**Pros:**
- Simple, no abstraction overhead
- Django developers are familiar with ORM
- Less code to maintain

**Cons:**
- Complex queries are scattered across services
- Query optimization is inconsistent
- Hard to add caching consistently
- Difficult to swap persistence (e.g., OpenSearch) later
- No centralized place for complex aggregation logic

**Decision:** Rejected. Complex queries become unmaintainable as the codebase grows.

### 3. Selective Repository Pattern (Selected)

**Description:** Use repositories only for complex, multi-table queries used by multiple services. Use ORM directly for simple queries.

**Pros:**
- Repositories add value where needed (complex queries)
- No overhead for simple CRUD
- Clear decision tree (no ambiguity)
- Query optimization is centralized for complex cases
- Future persistence swaps are easier for repository-backed queries

**Cons:**
- Requires discipline to apply the decision tree consistently
- Developers may over-use or under-use repositories initially
- Requires Phase 6 introduction (not available during Phases 0-5)

**Decision:** Accepted. Best balance of value and simplicity.

---

## Consequences

### Positive
- Complex queries are centralized and optimized in one place
- Services are testable (repositories can be mocked)
- Caching can be added consistently at the repository level
- Future persistence swaps are easier for repository-backed queries
- No overhead for simple CRUD operations
- Clear decision tree eliminates ambiguity

### Negative
- Requires discipline to apply the decision tree consistently
- Developers may over-use or under-use repositories initially
- Phase 6 introduction means complex queries in Phases 0-5 are not yet optimized
- `properties/` and `dashboard/` teams need training on repository pattern

### Neutral
- Repositories use Django ORM under the hood (no new query language)
- Performance is equivalent to direct ORM access (no overhead)
- Repository tests use the test database (not mocks)

---

## Migration Notes

### Phase 0-5: No Repositories
- All data access uses Django ORM directly in services
- Query logic is colocated in services
- No repository directory structure exists yet

### Phase 6: Introduce Repositories

**Tasks:**
1. Create `properties/repositories/__init__.py`
2. Implement `OwnerReportingRepository` in `properties/repositories/owner_reporting_repository.py`
3. Implement `RentRecordRepository` in `properties/repositories/rent_record_repository.py`
4. Create `dashboard/repositories/__init__.py`
5. Implement `DashboardMetricRepository` in `dashboard/repositories/dashboard_metric_repository.py`
6. Update `OwnerReportingService` to use `OwnerReportingRepository`
7. Add unit tests for each repository
8. Document repository pattern in `docs/architecture/patterns/repositories.md`

**Criteria for Adding New Repositories:**
- Query spans 3+ tables AND is used by 3+ services
- Requires ADR approval (unless it matches the decision tree exactly)

### Rollback
- Phase 6: Remove repository files. Services revert to ORM directly. No data changes.

---

## Future Evolution

### Short-term (Phase 6)
- Repositories are introduced for the 3 known complex queries
- Team training on repository pattern
- Query count tests verify repositories don't introduce N+1 problems

### Medium-term
- If `properties/` grows, additional repositories are added per the decision tree
- Repositories may introduce caching decorators (`@cached_result(ttl=300)`)
- Repositories may support query logging and performance monitoring

### Long-term
- Repository pattern may be standardized across all apps if team grows
- If microservices are extracted, repositories become the service data-access layer
- Repositories may be replaced by CQRS query handlers if read/write separation is needed

---

## References

- [Architecture v1.1 Release Candidate — Finding AD-07](../../../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Implementation Master Plan — Phase 6](../../../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Testing Strategy](./ADR-009_testing_strategy.md)
- [Bounded Context Strategy](./ADR-001_bounded_context_strategy.md)
