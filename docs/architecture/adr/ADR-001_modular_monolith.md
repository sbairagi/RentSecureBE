# ADR-001: Modular Monolith Architecture

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure is a Django-based rental management platform. The current architecture is a modular monolith with loosely coupled Django apps. The team is small (2–5 engineers) and the product is in early growth phase (0–10,000 users).

We need an architecture that:
- Allows independent development of features
- Enables future service extraction without rewrite
- Maintains operational simplicity (single deployment)
- Keeps infrastructure costs low in early stages
- Provides clear boundaries for team autonomy

---

## Decision

RentSecure will use a **Modular Monolith** architecture with strict bounded context boundaries.

The system remains a single deployable unit but is internally structured as independent modules with explicit contracts between them.

**Key characteristics:**
- Single Django project, single deployment
- Bounded contexts as Django apps with internal layer structure
- Dependency injection for all external services
- Domain events for cross-context communication
- Import-linter enforcing module boundaries
- Feature flags controlling premium integrations

---

## Alternatives Considered

### 1. Full Microservices

**Description:** Extract each bounded context into a separate deployable service.

**Pros:**
- Independent deployment per service
- Technology heterogeneity per service
- Team autonomy at scale

**Cons:**
- High operational overhead (orchestration, service mesh, monitoring)
- Distributed system complexity (transactions, consistency, latency)
- Requires message broker, service discovery, API gateway
- Overkill for 2–5 engineer team
- Significantly higher infrastructure cost

**Decision:** Rejected. Premature for current scale and team size.

### 2. Layered Monolith (Traditional)

**Description:** Standard Django project with models → views → templates structure.

**Pros:**
- Simple to understand
- Django community standard
- Fast initial development

**Cons:**
- Tight coupling between layers
- Difficult to test business logic in isolation
- Hard to extract services later
- Business logic scattered across views and serializers

**Decision:** Rejected. Accumulates technical debt that becomes expensive later.

### 3. Modular Monolith with Enforced Boundaries (Selected)

**Description:** Single deployable unit with strict module boundaries, dependency injection, and clean architecture.

**Pros:**
- Single deployment (operational simplicity)
- Clear module boundaries (team autonomy)
- Easy to extract services later (just deploy module independently)
- Testable business logic
- Low infrastructure cost
- Gradual migration path from existing code

**Cons:**
- More upfront design work
- Requires discipline to maintain boundaries
- Some patterns feel "heavy" for small codebase

**Decision:** Accepted. Best balance for current maturity.

---

## Consequences

### Positive
- Teams can work on bounded contexts with minimal coordination
- Future service extraction becomes a configuration change, not a rewrite
- Import-linter contracts become the architecture enforcement mechanism
- Shared kernel is minimized to prevent coupling
- Domain events replace direct cross-context calls over time
- Single deployment reduces operational complexity

### Negative
- More upfront design work required
- Some patterns feel heavy for small codebase
- Requires discipline to maintain boundaries
- Import-linter adds CI time

### Neutral
- Single deployment remains the default
- Service extraction is a future possibility, not a goal

---

## References

- [Architecture Principles](../../../architecture/ARCHITECTURE_PRINCIPLES.md)
- [Module Boundaries](../../../architecture/module-boundaries.md)
- [Dependency Rules](../../../architecture/dependency-rules.md)
- [Production Architecture](../production-architecture.md)
