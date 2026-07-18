# ADR-005: Domain Events for Cross-Context Communication

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

Currently, cross-context communication in RentSecure is done through direct service calls and model imports. This creates:
- Tight coupling between contexts
- Difficulty in changing one context without affecting others
- No audit trail of cross-context interactions
- Hard to add new subscribers to events

---

## Decision

Cross-context communication in RentSecure uses **domain events**. When a significant state change occurs in one context, a domain event is published. Other contexts subscribe to relevant events.

**Key rules:**
- Events are immutable and versioned
- Event handlers are idempotent
- Events are processed asynchronously (in-process in Year 1)
- Failed events are retried with exponential backoff
- Dead events go to a dead letter queue

---

## Alternatives Considered

### 1. Direct Service Calls

**Description:** Context A calls services in Context B directly.

**Pros:**
- Simple, synchronous
- Easy to understand

**Cons:**
- Tight coupling between contexts
- Hard to add new subscribers
- No audit trail
- Difficult to test in isolation

**Decision:** Rejected. Creates coupling.

### 2. Shared Database

**Description:** All contexts share the same database and query each other's tables.

**Pros:**
- Simple data access
- No service layer needed

**Cons:**
- Complete coupling between contexts
- Schema changes affect all contexts
- Violates bounded context boundaries

**Decision:** Rejected. Violates DDD principles.

### 3. Domain Events (Selected)

**Description:** Publish events for significant state changes; subscribers react independently.

**Pros:**
- Decouples contexts
- Easy to add new subscribers
- Provides audit trail
- Supports eventual consistency
- Enables future async processing

**Cons:**
- More complex than direct calls
- Requires eventual consistency thinking
- Debugging can be harder

**Decision:** Accepted. Best for long-term maintainability.

---

## Consequences

### Positive
- Contexts are decoupled
- Easy to add new subscribers
- Provides audit trail of cross-context interactions
- Supports future async processing
- Enables event sourcing in the future

### Negative
- More complex than direct calls
- Requires eventual consistency thinking
- Debugging distributed events is harder
- Event versioning requires discipline

### Neutral
- Year 1 uses in-process event bus (simple)
- Event handlers are idempotent by design
- Dead letter queue for failed events

---

## References

- [Domain Events](../future/07_domain_events.md)
- [Bounded Contexts](../future/02_bounded_contexts.md)
- [Architecture Principles](../../../architecture/ARCHITECTURE_PRINCIPLES.md)
