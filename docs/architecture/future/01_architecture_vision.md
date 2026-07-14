# RentSecure — Target Architecture Vision

**Version:** 1.0.0
**Status:** Proposed
**Date:** 2026-07-14
**Author:** RentSecure Engineering
**Review Cycle:** Quarterly

---

## Mission

Build a rental management platform that is reliable, scalable, and maintainable for 10+ years. RentSecure connects property owners and tenants through transparent rent tracking, automated reminders, and secure document management—while keeping operational costs minimal in early stages and enabling smooth growth to enterprise scale.

---

## Architecture Goals

1. **Maintainability:** Any engineer can understand, modify, and extend any bounded context in under 2 days.
2. **Testability:** Every business rule is independently testable without Django's HTTP stack.
3. **Independence:** Bounded contexts can be developed, tested, and deployed independently when the time comes.
4. **Performance:** APIs respond under 200ms at p95 for all read operations and under 500ms for write operations at 10,000 concurrent users.
5. **Cost Efficiency:** Operates within ₹2,000–3,000 INR/month for Year 1; scales cost-effectively.
6. **Security:** Every boundary enforces authentication, authorization, and input validation by default.
7. **Observability:** Every business event is traceable through logs, metrics, and distributed traces.
8. **Backward Compatibility:** External APIs remain stable across all architecture phases.

---

## Design Philosophy

### Structured Modular Monolith
RentSecure is a **modular monolith with strict bounded context boundaries**—not a distributed monolith, not a collection of microservices, and not a "big ball of mud." Each bounded context owns its data, logic, and APIs. Dependencies flow inward. No cross-context direct coupling.

### Domain-Driven Design
The codebase is organized around business domains, not technical layers. Bounded contexts reflect how the business actually thinks about the problem. The domain model is the source of truth.

### Clean Architecture
The system is divided into layers with strict dependency rules. Domain logic has zero framework dependencies. The framework (Django) is a plugin to the domain, not the other way around.

### Vertical Slices
Where practical, features are organized as vertical slices through the architecture (command → service → repository → model) rather than horizontal layers. This keeps related code together and reduces navigation cost.

### Event-Driven Where Beneficial
Domain events are used for cross-context communication where eventual consistency is acceptable. Not every interaction requires an event—direct service calls within a context are preferred for synchronous workflows.

---

## Engineering Principles

| Principle | Description |
|-----------|-------------|
| **Single Responsibility** | Every class, module, and service has exactly one reason to change. |
| **Open/Closed** | New features extend existing abstractions; existing code is never modified for new behavior. |
| **Liskov Substitution** | All implementations of an interface are interchangeable without side effects. |
| **Interface Segregation** | Interfaces are small and focused; no client depends on methods it doesn't use. |
| **Dependency Inversion** | High-level modules depend on abstractions, not concretions. |
| **Explicit Over Implicit** | Dependencies, data flows, and side effects are always visible in code. |
| **Fail Fast** | Errors are detected at the earliest possible point with clear messages. |
| **Idempotency** | All write operations are safe to retry without duplicate side effects. |
| **Observability First** | Every service method logs its entry, exit, and errors with structured context. |
| **Security by Default** | Authentication and authorization are applied at every boundary, not as an afterthought. |

---

## Non-Goals

The following are explicitly **not** goals of the target architecture:

1. **Microservices:** Service extraction is a future possibility, not an architectural goal. The modular monolith remains the deployment unit.
2. **Event Sourcing:** Event sourcing is not adopted. Audit trails use `django-simple-history`. Events are for decoupling, not persistence.
3. **CQRS Everywhere:** CQRS is applied selectively where read/write models diverge significantly (e.g., analytics dashboards). Most bounded contexts use a single model.
4. **Distributed Transactions:** Two-phase commit and saga patterns are not introduced. Compensation logic handles rollback within bounded contexts.
5. **Kubernetes/Container Orchestration:** Not required until Stage 4. Single EC2 + systemd is sufficient for Years 1–3.
6. **Multi-Region:** Single-region (ap-south-1) deployment is the default. Multi-region is a Stage 4 concern.
7. **API Gateway:** Not required until Stage 3. Django URL routing is sufficient for the modular monolith.
8. **Message Broker (RabbitMQ/Kafka):** Not required until Stage 2+ (Celery with Redis). Domain events use in-process handlers in Year 1.

---

## Architecture Constraints

| Constraint | Rationale |
|------------|-----------|
| **Remain a Django project** | The team is proficient in Django; rewriting to another framework has no ROI. |
| **Year 1 cost ≤ ₹3,000/month** | Business requirement for bootstrap viability. |
| **No breaking API changes during migration** | External clients depend on existing contracts. |
| **Feature flags for all premium integrations** | Cashfree, Razorpay, WhatsApp, SMS, OpenSearch must be switchable via environment. |
| **CI always green** | Every commit must pass full test suite, lint, typecheck, and architecture contract. |
| **Import-linter enforcement** | All cross-module dependencies are verified in CI. |
| **PostgreSQL as primary datastore** | No polyglot persistence until Stage 3. |

---

*This document is the north star for all architecture decisions. All ADRs and implementation plans must align with this vision.*
