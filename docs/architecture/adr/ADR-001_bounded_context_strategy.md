# ADR-001: Bounded Context Strategy

**Status:** Accepted
**Date:** 2026-07-19
**Deciders:** Chief Software Architect, Staff Engineer, Platform Team Lead, Product Team Lead
**Supersedes:** ADR-001 (v1.0 — Modular Monolith Architecture)

---

## Context

RentSecureBE is a Django-based rental management platform in early growth phase (0–10,000 users). The team is small (2–5 engineers) and needs an architecture that:

- Allows independent development of features by bounded context
- Enables future service extraction without rewrite
- Maintains operational simplicity (single deployment)
- Keeps infrastructure costs low in early stages
- Provides clear boundaries for team autonomy

v1.0 proposed several structural changes that were later rejected in v1.1 review:
- A parent `apps/` directory (rejected: changes every import path with no architectural value)
- A deferred `rent/` bounded context (rejected: phantom context; rent logic stays in `properties/`)
- Active treatment of dead code (`ai_assistant/`, `dashboard/`) as deployed contexts

The v1.1 bounded context strategy must reflect the actual target state: apps at the project root, no phantom contexts, and deferred modules clearly marked.

---

## Decision

RentSecureBE uses a **Modular Monolith** with **7 active bounded contexts** and **3 deferred contexts**.

### Active Bounded Contexts

| Context | App Directory | Owner | Maturity | Public APIs |
|---------|--------------|-------|----------|-------------|
| Identity | `core/` (models) + `identity/` (services) | Platform Team | Production | Auth, OTP, Password, Profile |
| Property | `properties/` | Product Team | Production | Units, RentRecords, Owners, Renters |
| Subscription | `subscription/` | Platform Team | Production | Plans, Limits, Features |
| Payment | `payments/` | Platform Team | Production | BankDetails, Webhooks, Transactions |
| Notification | `notification/` | Platform Team | Production | Email, Push, InApp, WhatsApp, SMS |
| Document | `documents/` | Product Team | Production | RentAgreements, Invoices |
| Finance | `finance/` | Product Team | Production | TaxRecords, Payouts |

### Deferred Bounded Contexts

| Context | App Directory | Status | Future Trigger |
|---------|--------------|--------|---------------|
| Dashboard | `dashboard/` | Experimental / Not Deployed | Product team activation |
| AI Assistant | `smartbot/` (active), `ai_assistant/` (dead code) | Experimental / Not Deployed | Consolidation in Phase 6 |
| Referral | `referral/` | Production (minimal) | Growth trigger |

### Key Principles

1. **Single Django project, single deployment** — no microservices in Year 1
2. **Bounded contexts as Django apps** with internal layer structure (`models/`, `services/`, `views/`, `tests/`)
3. **Dependency injection** for all external services (payment gateways, notification channels)
4. **Domain events** for cross-context communication (event bus in Phase 6)
5. **Import-linter** enforcing module boundaries on every commit
6. **Feature flags** controlling premium integrations (per-user, not global boolean)
7. **Apps at project root** — no `apps/` parent directory
8. **No phantom contexts** — `rent/` is rejected; rent logic stays in `properties/`

### Ownership Model

Each bounded context has a single owning team:
- **Platform Team:** `platform/`, `shared/`, `payments/`, `notification/`, `identity/`
- **Product Team:** `properties/`, `finance/`, `documents/`, `dashboard/`

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

**Decision:** Rejected. Premature for current scale and team size. Re-evaluate when transaction volume exceeds 500 payments/month or team exceeds 15 engineers.

### 2. Layered Monolith (Traditional Django)

**Description:** Standard Django project with models → views → templates structure, no enforced boundaries.

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

### 3. Modular Monolith with `apps/` Parent Directory

**Description:** Move all apps into a parent `apps/` directory for visual organization.

**Pros:**
- Visual grouping of apps
- Cleaner project root

**Cons:**
- Every import path changes across 300+ files
- Every URL include changes
- Every migration reference changes
- Every template tag and static file path changes
- No architectural value (boundaries already enforced by import-linter)
- Hidden mega-migration that blocks all other phases if it fails

**Decision:** Rejected. Changes every import path with no architectural value and enormous migration risk.

### 4. Modular Monolith with Enforced Boundaries (Selected)

**Description:** Single deployable unit with strict module boundaries, dependency injection, clean architecture, and import-linter enforcement.

**Pros:**
- Single deployment (operational simplicity)
- Clear module boundaries (team autonomy)
- Easy to extract services later (just deploy module independently)
- Testable business logic
- Low infrastructure cost
- Gradual migration path from existing code
- import-linter prevents architectural drift

**Cons:**
- More upfront design work
- Requires discipline to maintain boundaries
- Some patterns feel "heavy" for small codebase
- import-linter adds CI time (minimal)

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
- Apps at root level avoid mega-migration risk

### Negative
- More upfront design work required
- Some patterns feel heavy for small codebase
- Requires discipline to maintain boundaries
- import-linter adds CI time (minimal)
- `properties/` is a large context that may need sub-modules later

### Neutral
- Single deployment remains the default
- Service extraction is a future possibility, not a goal
- `ai_assistant/` and `dashboard/` are deferred; no resources spent on them until activated
- `rent/` is permanently rejected; rent logic is a `properties` sub-module

---

## Migration Notes

### v1.0 to v1.1 Changes

| v1.0 Decision | v1.1 Decision | Reason |
|---------------|---------------|--------|
| `apps/` parent directory | Rejected | Mega-migration risk, no architectural value |
| `rent/` bounded context (deferred) | Rejected | Phantom context; responsibilities already assigned |
| `ai_assistant/` as active context | Deferred / Not Deployed | Not in `INSTALLED_APPS`, dead code |
| `dashboard/` as active context | Deferred / Not Deployed | Not in `INSTALLED_APPS`, dead code |
| 8 active contexts | 7 active + 3 deferred | Accurate representation of target state |

### Phase Mapping

| Phase | Bounded Context Work |
|-------|---------------------|
| Phase -1 | Break circular dependencies across all active contexts |
| Phase 0 | Register `payments/`; move `OwnerBankDetails` and `NotificationPreference` |
| Phase 1 | Extract identity services from `core/` to `identity/` |
| Phase 2 | Extract subscription services from `core/` and `properties/` to `subscription/` |
| Phase 3 | Consolidate payment logic in `payments/` |
| Phase 4 | Extract dashboard services; isolate notification adapters |
| Phase 5 | Deprecate `core/` views/services/models (non-identity) |
| Phase 6 | Event bus, repositories, Redis cache, AI consolidation |

### PR-005: Split `core/views.py` into `core/views/` Package

`core/views.py` was removed and replaced with a `core/views/` package containing four focused modules:
- `auth_views.py` — OTP, authentication, and password views
- `subscription_views.py` — Subscription CRUD viewsets
- `bank_views.py` — Bank details and rent payment views
- `reporting_views.py` — Owner reporting views

No API changes. No database migration. Backward compatibility is maintained through updated import paths; all existing URLs and behaviors remain unchanged.

---

## Future Evolution

### Stage 1 (Year 1)
- Maintain modular monolith
- Enforce boundaries via import-linter and architecture tests
- Introduce domain events via in-process event bus (Phase 6)

### Stage 2 (Trigger: >500 payments/month or >10 hours/week manual verification)
- Evaluate extracting `payment/` as first microservice
- Introduce message broker (Redis/Celery) for async events
- Service mesh for inter-service communication

### Stage 3 (Trigger: Team >15 engineers or >50,000 users)
- Evaluate extracting `property/` and `notification/` as microservices
- Introduce API gateway
- Distributed tracing and observability

### Long-term
- Bounded contexts remain stable; no new contexts added without ADR
- `dashboard/` and `ai/` may be activated based on product roadmap
- `referral/` may grow into a full context if referral program scales

---

## References

- [Architecture v1.1 Release Candidate](../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Implementation Master Plan](../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Dependency Rules](./ADR-006_import_rules.md)
- [Migration Strategy](./ADR-007_migration_strategy.md)
- [Module Boundaries](../../../architecture/module-boundaries.md)
