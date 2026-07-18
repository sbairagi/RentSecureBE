# ADR-002: Repository Pattern for Data Access

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

Currently, data access in RentSecure is scattered across services and views using direct Django ORM queries. This creates tight coupling between business logic and persistence mechanisms, making it difficult to:
- Test business logic without a database
- Swap persistence mechanisms (e.g., move to OpenSearch)
- Enforce query optimization standards
- Implement caching consistently

---

## Decision

All data access in RentSecure will go through **repository interfaces** defined in the domain layer and implemented in the infrastructure layer.

**Key rules:**
- Repository interfaces live in `domain/repositories/`
- Repository implementations live in `infrastructure/repositories/`
- Application services depend on repository interfaces (injected via DI)
- Domain entities never query the database directly
- Selectors handle complex read operations that don't return entities

---

## Alternatives Considered

### 1. Direct ORM Access in Services

**Description:** Continue using Django ORM directly in application services.

**Pros:**
- Simple, no abstraction overhead
- Django developers are familiar with ORM
- Less code

**Cons:**
- Tight coupling to Django ORM
- Hard to test without database
- Difficult to add caching consistently
- Query optimization scattered across services

**Decision:** Rejected. Repository pattern provides better testability and flexibility.

### 2. Django Manager Pattern

**Description:** Use custom Django managers for query logic.

**Pros:**
- Django-native pattern
- Familiar to Django developers

**Cons:**
- Managers are tied to Django models
- Business logic still in models/managers
- Hard to test without database
- Not suitable for complex cross-entity queries

**Decision:** Rejected. Repository pattern provides cleaner separation.

### 3. Repository Pattern (Selected)

**Description:** Abstract data access behind interfaces.

**Pros:**
- Business logic independent of persistence
- Easy to mock for testing
- Consistent caching strategy
- Query optimization centralized
- Future persistence swaps are easy

**Cons:**
- More code (interface + implementation)
- Requires discipline to maintain

**Decision:** Accepted. Benefits outweigh costs.

---

## Consequences

### Positive
- Business logic is testable without database
- Query optimization is centralized
- Caching can be added consistently
- Future persistence swaps (e.g., OpenSearch) are easy
- Clear data access contract per context

### Negative
- More boilerplate code
- Requires discipline to not bypass repositories
- Slightly more complex for simple queries

### Neutral
- Repository implementations use Django ORM (not changed)
- Performance is equivalent to direct ORM access

---

## References

- [Repository Pattern](../future/08_repository_pattern.md)
- [Layer Rules](../future/04_layer_rules.md)
- [Dependency Rules](../future/05_dependency_rules.md)
