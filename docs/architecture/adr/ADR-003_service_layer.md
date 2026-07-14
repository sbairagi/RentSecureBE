# ADR-003: Service Layer as Business Logic Entry Point

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

Currently, business logic is spread across views, serializers, and models. This creates:
- Duplicate logic across views
- Difficult-to-test business rules
- Views that are too complex
- Serializers that enforce business rules (wrong place)

The service layer must be the **only** entry point for business workflows.

---

## Decision

All business logic in RentSecure lives in **application services**. Views and serializers are thin orchestration layers only.

**Rules:**
- Views delegate to services, never contain business logic
- Serializers validate and transform only, never enforce business rules
- Models are persistence artifacts, not business logic containers
- Services are stateless and injectable
- One service method = one use case

---

## Alternatives Considered

### 1. Business Logic in Views

**Description:** Keep business logic in views (current pattern for some features).

**Pros:**
- Simple, no extra layer
- Familiar Django pattern

**Cons:**
- Hard to reuse logic across views
- Difficult to test without HTTP stack
- Views become complex and hard to maintain
- Violates separation of concerns

**Decision:** Rejected. Violates architecture principles.

### 2. Business Logic in Models (Fat Models)

**Description:** Use Django models as the primary business logic container.

**Pros:**
- Django community standard
- Logic close to data
- Familiar pattern

**Cons:**
- Models become God objects
- Hard to test model methods in isolation
- Models know too much about the system
- Violates single responsibility

**Decision:** Rejected. Models should be persistence artifacts only.

### 3. Service Layer (Selected)

**Description:** Application services orchestrate workflows; domain entities contain behavior.

**Pros:**
- Clear separation of concerns
- Testable without HTTP or database
- Reusable across views and other services
- Easy to understand workflows
- Supports dependency injection

**Cons:**
- More code
- Requires discipline

**Decision:** Accepted. Standard in Clean Architecture and DDD.

---

## Consequences

### Positive
- Business logic is testable in isolation
- Workflows are easy to understand
- Logic is reusable across views
- Services are stateless and injectable
- Clear separation of concerns

### Negative
- More boilerplate
- Requires team discipline
- Slightly higher initial complexity

### Neutral
- Services use repositories for data access
- Domain entities contain behavior, not services

---

## References

- [Service Layer](docs/architecture/future/09_service_layer.md)
- [Architecture Principles](architecture/ARCHITECTURE_PRINCIPLES.md)
- [Dependency Rules](architecture/dependency-rules.md)
