# ADR-004: No Business Logic in Views

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

Currently, some views in RentSecure contain business logic (e.g., payment verification logic in views, rent calculation in views). This creates:
- Duplicate logic across views
- Views that are hard to test
- Views that know too much about the domain
- Difficult to reuse logic

---

## Decision

**Views must never contain business logic.** Views handle HTTP concerns only:
- Request parsing
- Authentication/authorization
- Calling application services
- Serializing responses
- Setting HTTP status codes

Business logic must live in application services or domain entities.

---

## Alternatives Considered

### 1. Keep Business Logic in Views

**Description:** Allow some business logic in views for simple cases.

**Pros:**
- Less code for simple operations
- Faster initial development

**Cons:**
- Logic is hard to reuse
- Hard to test without HTTP stack
- Views become inconsistent
- Violates separation of concerns

**Decision:** Rejected. Creates unmaintainable views.

### 2. No Views (API-only)

**Description:** Use only DRF viewsets with minimal customization.

**Pros:**
- Very thin views
- Consistent pattern

**Cons:**
- Limits flexibility for complex workflows
- Some business logic inevitably leaks

**Decision:** Rejected. Too restrictive.

### 3. Thin Views (Selected)

**Description:** Views are orchestration only. All business logic in services.

**Pros:**
- Views are predictable and consistent
- Business logic is testable
- Logic is reusable
- Clear separation of concerns

**Cons:**
- More code
- Requires discipline

**Decision:** Accepted. Standard in Clean Architecture.

---

## Consequences

### Positive
- Views are predictable and easy to understand
- Business logic is testable in isolation
- Logic is reusable across views and other entry points
- Views are consistent across the codebase

### Negative
- More boilerplate for simple CRUD
- Requires team discipline

### Neutral
- Simple CRUD can use generic viewsets with service delegation
- Views remain thin but functional

---

## References

- [Service Layer](../future/09_service_layer.md)
- [Architecture Principles](../../../architecture/ARCHITECTURE_PRINCIPLES.md)
