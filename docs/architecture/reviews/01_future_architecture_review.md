# Future Architecture Review

**Document:** `docs/architecture/future/` + `docs/architecture/adr/`
**Review Date:** 2026-07-14
**Reviewer:** Principal Software Architect
**Status:** APPROVED WITH MINOR CHANGES

---

## Executive Summary

The target architecture blueprint for RentSecure is **well-designed, principled, and production-ready**. It correctly identifies the project as a modular monolith that must remain Django-native, operationally simple, and cost-efficient in early stages while being upgradeable to enterprise scale. The documentation is comprehensive, the ADR process is sound, and the diagrams are largely accurate.

However, the review identified **one structural bug** in the folder structure, **several ADR inconsistencies**, **missing strategic ADRs**, and **moderate overengineering risk** in the layer definitions that should be addressed before freezing the architecture.

**Overall Assessment:** The architecture is sound and should be approved with minor corrections. The team can begin Phase 1 migration immediately while addressing the identified gaps.

---

## Architecture Score: 82/100

| Category | Score | Weight | Weighted |
|----------|-------|--------|----------|
| Clean Architecture | 8/10 | 10% | 0.80 |
| Domain Driven Design | 9/10 | 10% | 0.90 |
| Modular Monolith Boundaries | 8/10 | 10% | 0.80 |
| SOLID Compliance | 8/10 | 10% | 0.80 |
| Repository Pattern | 9/10 | 8% | 0.72 |
| Service Layer | 9/10 | 8% | 0.72 |
| CQRS Usage | 7/10 | 5% | 0.35 |
| Domain Events | 8/10 | 8% | 0.64 |
| Dependency Direction | 9/10 | 10% | 0.90 |
| Import-Linter Rules | 8/10 | 5% | 0.40 |
| Layering | 8/10 | 8% | 0.64 |
| Folder Structure | 6/10 | 5% | 0.30 |
| Django Best Practices | 7/10 | 5% | 0.35 |
| Maintainability | 8/10 | 5% | 0.40 |
| Scalability | 9/10 | 5% | 0.45 |
| Extensibility | 9/10 | 5% | 0.45 |
| Testability | 9/10 | 5% | 0.45 |
| Operational Simplicity | 8/10 | 5% | 0.40 |
| Developer Experience | 7/10 | 5% | 0.35 |
| Overengineering Risk | 5/10 | 5% | 0.25 |

**Total: 81.5/100 → 82/100**

---

## Production Readiness Score: 7/10

The architecture is production-ready **conceptually** but not **immediately implementable** due to:
- One structural bug in folder layout (duplicate `infrastructure/` directory)
- Missing ADRs for observability, security, deployment, and i18n
- Inconsistent adapter path references between ADRs and folder structure

**Recommendation:** Address the 6 minor changes below before beginning Phase 1 implementation.

---

## Maintainability Score: 9/10

The architecture excels in maintainability:
- Clear bounded contexts with explicit boundaries
- Thin views, fat services
- Repository pattern abstracts persistence
- Domain events decouple contexts
- Import-linter enforces boundaries in CI
- Comprehensive naming conventions
- Four-tier testing strategy

**Deductions for:**
- Vertical slice ADR (ADR-020) conflicts slightly with horizontal layer structure, creating potential confusion
- Some ADRs are too thin (ADR-001 through ADR-007 lack depth)

---

## Scalability Score: 9/10

The architecture scales well:
- Modular monolith prepares for service extraction
- CQRS supports read-heavy dashboards
- Cache abstraction allows Redis migration
- Search abstraction allows OpenSearch migration
- Event bus abstraction allows distributed messaging
- Stage 2-4 infrastructure evolution is well-defined

**Deductions for:**
- No clear multi-tenancy strategy (if required later)
- Dashboard context depends on all other contexts (potential bottleneck)

---

## Complexity Score: 6/10

**Moderate complexity.** The architecture introduces significant structure (layers, repositories, DI container, event bus) that is justified for a 10+ year platform but may feel heavy for a 2-5 engineer team in Year 1.

**Risk areas:**
- The 5-layer structure + DI container + event bus adds ceremony
- Each bounded context has ~15+ repository interfaces
- The service container requires manual wiring
- New developers need to understand Clean Architecture + DDD + CQRS + Event-Driven patterns simultaneously

**Mitigation:** The migration phases allow incremental adoption. The team can start with simpler patterns and add complexity as needed.

---

## Document-by-Document Review

### 01_architecture_vision.md
**Score: 9/10**

**Strengths:**
- Clear mission aligned with business goals
- Well-defined architecture goals with measurable targets
- Design philosophy is consistent and well-articulated
- Engineering principles are concrete and actionable
- Non-goals section prevents scope creep
- Architecture constraints are realistic

**Weaknesses:**
- Missing explicit **security principles** (authn/authz, input validation, output encoding)
- Missing **observability principles** (structured logging, metrics, tracing standards)
- No mention of **internationalization** strategy

**Missing Ideas:**
- Data retention and archival policy
- Disaster recovery and backup strategy
- Compliance requirements (if any)

**Approval:** Approved. Minor additions recommended.

---

### 02_bounded_contexts.md
**Score: 8/10**

**Strengths:**
- 11 bounded contexts identified with clear responsibilities
- Each context has public APIs, internal APIs, dependencies
- Context map shows relationships
- Interaction summary table is comprehensive

**Weaknesses:**
- **Inconsistency:** Context map shows `ID → SUB` and `SUB → ID` (bidirectional), but the correct relationship is SUB depends on ID (unidirectional)
- **Conceptual issue:** `RENT →|depends on| PAY` in the interaction table is misleading. Rent initiates payment requests but doesn't depend on payment processing internals. This should be `RENT →|triggers| PAY` via event.
- Dashboard is described as "read-only, cross-cutting" but it depends on ALL contexts—this is a potential scalability bottleneck
- Missing explicit **anti-corruption layers** for contexts that read from other contexts

**Missing Ideas:**
- Context versioning strategy
- Context deployment independence criteria
- Shared kernel definition (what exactly is in shared/)

**Approval:** Approved with minor clarifications on dependency directions.

---

### 03_target_folder_structure.md
**Score: 5/10 — REQUIRES FIX**

**Strengths:**
- Complete directory tree
- Clear purpose for each top-level directory
- Internal app structure is well-defined
- Migration mapping is practical

**Critical Bug:**
- **`infrastructure/` is listed TWICE** in the internal app structure (lines 295-303 and 317-322). The second occurrence (for signals, tasks, management commands) should be named `operations/` or `cross_cutting/`.

```markdown
# WRONG:
├── infrastructure/            # Infrastructure implementations
│   ├── __init__.py
│   ├── repositories/          # Repository implementations
│   ├── persistence/           # Django model definitions
│   │   ├── __init__.py
│   │   ├── models.py          # Django ORM models
│   │   └── migrations/        # Auto-generated migrations
│   └── external/              # External service adapters
│       └── <adapter_name>.py
├── infrastructure/            # Cross-cutting concerns  <-- DUPLICATE!
│   ├── __init__.py
│   ├── signals.py
│   ├── tasks.py
│   └── management/

# CORRECT:
├── infrastructure/            # Infrastructure implementations
│   ├── __init__.py
│   ├── repositories/          # Repository implementations
│   ├── persistence/           # Django model definitions
│   │   ├── __init__.py
│   │   ├── models.py          # Django ORM models
│   │   └── migrations/        # Auto-generated migrations
│   └── external/              # External service adapters
│       └── <adapter_name>.py
├── operations/                 # Cross-cutting concerns
│   ├── __init__.py
│   ├── signals.py
│   ├── tasks.py
│   └── management/
```

**Other Issues:**
- `infrastructure/persistence/` has an extra `__init__.py` that Django's migration autodetector doesn't need (not harmful, but unnecessary)
- Migration mapping table doesn't address how to handle the current `properties/models/` split (multiple model files vs. single `models.py`)

**Approval:** Requires fix before Phase 2.

---

### 04_layer_rules.md
**Score: 8/10**

**Strengths:**
- Clear 5-layer hierarchy with dependency arrows
- Each layer has explicit allowed/forbidden imports
- Cross-cutting concerns (logging, validation, auth, errors, caching) are well-defined
- Dependency matrix is clear

**Weaknesses:**
- **Layer 1 combines Platform + Shared** which creates confusion. Shared (types, exceptions) and Platform (cache, storage adapters) have different dependency rules. Shared should be Layer 0, Platform should be Layer 1.
- Application layer is allowed to import from Infrastructure layer (repositories), but this creates a circular dependency risk if Infrastructure ever needs to call back to Application
- No mention of **anti-corruption layers** for cross-context reads

**Missing Ideas:**
- Exception propagation rules (how domain exceptions become HTTP responses)
- Transaction boundary rules (which layers can start/commit/rollback transactions)
- Testing rules per layer (what to mock, what to test)

**Approval:** Approved with minor restructuring (separate Shared as Layer 0).

---

### 05_dependency_rules.md
**Score: 9/10**

**Strengths:**
- Core principle (dependencies flow inward) is clear
- Allowed/forbidden imports are explicit with code examples
- Cross-app communication patterns are well-defined
- Import-linter contracts are provided for both current and future structures
- Exceptions process is clear

**Weaknesses:**
- Future import-linter.ini shows `apps/<context>` containers but the current `import-linter.ini` uses root packages without the `apps/` prefix. Migration needs a clear transition plan.
- The container contracts section shows `config` as a container, but `config/` is the Django project and should be able to import from apps (for URL routing). This is missing from the allowed rules.

**Missing Ideas:**
- How to handle `apps/<context>/operations/` (or whatever the signals/tasks folder is called) in import-linter
- Migration rules for existing violations

**Approval:** Approved. Minor adjustment to import-linter transition plan.

---

### 06_module_responsibilities.md
**Score: 9/10**

**Strengths:**
- Every app has a clear "what belongs / what doesn't belong" table
- Covers all 5 internal layers per app
- Includes shared/, platform/, config/
- Explicitly states this is the code review reference

**Weaknesses:**
- None significant

**Missing Ideas:**
- Migration priority for each app (which to refactor first)
- Inter-context data ownership rules (which context owns which database tables)

**Approval:** Approved. This is the gold standard document.

---

### 07_domain_events.md
**Score: 8/10**

**Strengths:**
- 30+ domain events catalogued
- Each event has publisher, subscribers, payload, purpose
- Event flow examples are clear
- Event handling rules are comprehensive

**Weaknesses:**
- **Inconsistency:** The event `PaymentRecorded` is referenced in the Context Interaction Summary (02_bounded_contexts.md) but is NOT defined in this catalog. Either add it or remove the reference.
- Event versioning is mentioned but no version scheme is defined (e.g., `v1`, `v2` suffix or `version` field semantics)
- No dead letter queue handling specification

**Missing Ideas:**
- Event schema registry (where event schemas are stored and versioned)
- Event replay strategy
- Event ordering guarantees (or lack thereof)

**Approval:** Approved. Add `PaymentRecorded` event and version scheme.

---

### 08_repository_pattern.md
**Score: 9/10**

**Strengths:**
- Generic `Repository[T]` base interface
- Complete repository catalog for all 11 contexts
- Clear implementation rules
- Selectors for read-model queries
- Examples for every pattern

**Weaknesses:**
- The generic `Repository[T]` base with `create(entity: T) -> T` pattern assumes the entity is passed in, but in practice the service creates the entity and the repository persists it. The interface should accept DTOs or the entity should be passed. This is a minor design question.
- `list(**filters)` on the base repository is too generic. Each repository defines specific query methods, which is correct, but the base interface's `list` is never used. Consider removing it from the base.

**Missing Ideas:**
- Unit of Work pattern (mentioned in production architecture but not here)
- Transaction management rules

**Approval:** Approved. Minor interface cleanup recommended.

---

### 09_service_layer.md
**Score: 9/10**

**Strengths:**
- Three service types clearly defined (Application, Domain, Infrastructure)
- Application service rules are comprehensive
- Domain service example is clear
- Infrastructure adapter examples show Year 1 vs Stage 2
- Transaction boundary example is correct

**Weaknesses:**
- The example `PaymentService.submit_payment()` calls `self.notifier.send()` directly. According to the domain events design, this should be done via event handler, not direct call. This is a **minor inconsistency** with ADR-005.
- Return type is `PaymentResult` (DTO) but the example also returns `receipt` in `verify_payment()`. The DTO pattern should be consistent.

**Missing Ideas:**
- Idempotency key handling in services
- Retry policies for external calls

**Approval:** Approved. Fix the direct notifier call to use events.

---

### 10_naming_conventions.md
**Score: 9/10**

**Strengths:**
- Comprehensive coverage: Python, Django, API, Serializer, Repository, Service, Policy, Selector, Command, Event, File, Package, Migration
- Code examples for each convention
- Anti-patterns table is practical

**Weaknesses:**
- The `InputSerializer`/`OutputSerializer` convention is not Django-idiomatic. Django developers expect `ModelSerializer` or `Serializer`. Consider `CreateBuildingSerializer` and `BuildingDetailSerializer` instead.
- `PascalCaseSelector` is unusual. Selectors are closer to queries; consider `PascalCaseQuery` instead.

**Approval:** Approved. Consider Django-idiomatic alternatives for serializer naming.

---

### 11_migration_strategy.md
**Score: 8/10**

**Strengths:**
- 9 phases with clear objectives, risks, rollback procedures
- Validation criteria for each phase
- Phase dependencies are visualized
- Success criteria are measurable

**Weaknesses:**
- Phase 2 (Move Files) doesn't address how to handle Django app registry changes. Moving `core/` to `apps/identity/` requires updating `INSTALLED_APPS` and migration dependencies.
- Phase 2 mentions `rent/` as a new context extracted from `property/`, but there's no guidance on how to split the existing `RentRecord` model from `properties/` into `apps/rent/`.
- Phase 4 (Repository Pattern) shows an example where `_to_entity()` converts Django model to domain entity. This mapping layer is significant work and should be highlighted as a risk.

**Missing Ideas:**
- Database migration strategy (how to handle table renames)
- Feature flag strategy for dual-running old/new code
- Rollback testing requirements

**Approval:** Approved. Add Django-specific migration guidance.

---

### Diagrams Review

#### 01_context.mmd (Context Diagram)
**Score: 7/10**

**Strengths:**
- Shows all external users
- Shows all layers
- Shows external systems

**Issues:**
- **Web Frontend** is shown inside the "RentSecure Platform" subgraph, but it should be external (it's a separate client application)
- Arrows from AppServices to ORM/Adapters/Cache are correct, but the diagram implies AppServices directly connects to all external systems. In reality, the Platform layer mediates these connections.

**Recommendation:** Move Web Frontend to External Users subgraph. Add Platform layer as mediator between AppServices and external systems.

---

#### 02_container.mmd (Container Diagram)
**Score: 4/10 — REQUIRES FIX**

**Strengths:**
- Shows major infrastructure components

**Critical Errors:**
- `Cron --> Gunicorn` is **backwards**. Cron triggers management commands, which run inside the Django process (which may be Gunicorn workers or a separate process). The arrow should be `Cron --> Django` or `Cron --> ManagementCommand`.
- `Celery --> Gunicorn` is **incorrect**. Celery workers are separate processes that communicate with Django via the database/Redis. They don't point to Gunicorn.
- Web tier shows LB and Nginx but no HTTPS/SSL termination detail
- Missing the Django application as a distinct container

**Recommendation:** Redraw with correct process relationships. Use the C4 model properly.

---

#### 03_component.mmd (Component Diagram)
**Score: 8/10**

**Strengths:**
- Shows all 11 apps with their 4 internal layers
- Shows shared/ and platform/
- Shows correct internal dependency direction within each app
- Shows all apps depending on shared and platform

**Issues:**
- Missing cross-app communication lines (events, service calls). The diagram only shows intra-app dependencies.
- Very large and hard to read (11 apps × 4 layers = 44 nodes)

**Recommendation:** Add a separate diagram for cross-app communication. Consider splitting into multiple diagrams.

---

#### 04_layers.mmd (Layer Diagram)
**Score: 7/10**

**Strengths:**
- Shows all 6 layers
- Shows correct dependency arrows between layers
- Color-coded for clarity

**Issues:**
- `Adapters --> RepoInterfaces` is **conceptually backwards**. Adapters IMPLEMENT repository interfaces. The arrow should point from RepoInterfaces to Adapters (interface → implementation), or be bidirectional.
- `Cache --> SharedUtils` and `Storage --> SharedUtils` are correct but confusingly placed. Platform depends on Shared, not the other way around.

**Recommendation:** Fix adapter arrow direction. Clarify that Platform depends on Shared.

---

#### 05_dependencies.mmd (Dependency Diagram)
**Score: 8/10**

**Strengths:**
- Clear allowed vs forbidden dependencies
- Color-coded (green for allowed, red for forbidden)
- Covers all major violation patterns

**Issues:**
- `L4 --> L2` (Application → Infrastructure) is shown as allowed, which is correct for repositories, but this should be qualified (only repositories, not other infrastructure)
- `F8: Cross-App Direct` is vague. Should specify what "direct" means.

**Recommendation:** Qualify L4 → L2 as "Application → Infrastructure (repositories only)".

---

#### 06_bounded_context.mmd (Bounded Context Diagram)
**Score: 7/10**

**Strengths:**
- Shows all 11 contexts
- Color-coded by domain
- Shows dependency and notification relationships

**Issues:**
- Very busy with ~30 arrows
- `RENT -->|depends on| PAY` is misleading (rent initiates payment, doesn't depend on payment internals)
- `DASH -->|reads from| ...` all contexts makes dashboard a potential bottleneck
- No clear visual distinction between "depends on" (synchronous) and "notifies" (async/event)

**Recommendation:** Use different arrow styles (solid for sync, dashed for async). Reduce clutter by grouping contexts.

---

#### 07_package.mmd (Package Diagram)
**Score: 8/10**

**Strengths:**
- Shows complete package structure
- Color-coded by domain
- Shows all top-level directories

**Issues:**
- Uses `rentsecure_be/` as top-level subgraph, which is confusing since the actual top-level is the project root
- Some nodes are very long (multi-line text in single node)

**Recommendation:** Rename top-level to `Project Root` or just show packages without the project root wrapper.

---

## ADR Review

### ADR Inventory

| ADR | Title | Status | Verdict |
|-----|-------|--------|---------|
| ADR-001 | Modular Monolith Architecture | Accepted | Approved |
| ADR-002 | Repository Pattern for Data Access | Accepted | Approved |
| ADR-003 | Service Layer as Business Logic Entry Point | Accepted | Approved |
| ADR-004 | No Business Logic in Views | Accepted | Approved |
| ADR-005 | Domain Events for Cross-Context Communication | Accepted | Approved |
| ADR-006 | Import Rules and Architecture Enforcement | Accepted | Approved |
| ADR-007 | Testing Strategy | Accepted | Approved |
| ADR-008 | Shared Module Rules | Accepted | Approved |
| ADR-009 | Configuration Strategy | Accepted | Approved |
| ADR-010 | Payment Integration Strategy | Accepted | Approved |
| ADR-011 | Notification Strategy | Approved | Approved |
| ADR-012 | Document Generation Strategy | Accepted | Approved |
| ADR-013 | Error Handling Strategy | Accepted | Approved |
| ADR-014 | Background Jobs Strategy | Accepted | Approved |
| ADR-015 | API Versioning Strategy | Accepted | Approved |
| ADR-016 | Feature Flag Strategy | Accepted | Approved |
| ADR-017 | CQRS for Read/Write Separation | Accepted | Approved |
| ADR-018 | Dependency Injection Strategy | Accepted | Approved |
| ADR-019 | Event Bus Implementation | Accepted | Approved |
| ADR-020 | Vertical Slice Architecture for Features | Accepted | Approved with notes |
| ADR-021 | Audit Logging Strategy | Accepted | Approved |
| ADR-022 | Cache Strategy | Accepted | Approved |
| ADR-023 | Search Strategy | Accepted | Approved |

### Conflicting ADRs

**No direct conflicts found.** All ADRs are consistent with each other.

**Potential tension:**
- **ADR-003** (Service Layer) + **ADR-020** (Vertical Slice): ADR-003 advocates horizontal organization (services in `application/services/`), while ADR-020 advocates vertical slices for new features. This is not a true conflict but could confuse developers. ADR-020 should clarify that vertical slices are for FEATURES while the standard structure is for SHARED code.

### Duplicated ADRs

**No exact duplicates found.**

**Near-duplicates:**
- ADR-003 (Service Layer) and ADR-004 (No Business Logic in Views) are closely related. ADR-004 could be merged into ADR-003 as a subsection, or ADR-003 could reference ADR-004 more explicitly.
- ADR-005 (Domain Events) and ADR-019 (Event Bus) are complementary but ADR-019 could be a subsection of ADR-005.

### Unnecessary ADRs

**None.** All 23 ADRs cover distinct architectural decisions.

**Recommendation:** Consider merging:
- ADR-003 + ADR-004 → "Service Layer and Thin Views"
- ADR-005 + ADR-019 → "Domain Events and Event Bus"

This would reduce the ADR count from 23 to 21, making the set easier to navigate.

### Missing ADRs

The following strategic decisions lack ADRs:

| Missing ADR | Rationale | Priority |
|-------------|-----------|----------|
| **ADR-024: Observability Strategy** | Structured logging, metrics, tracing, health checks | High |
| **ADR-025: Security Strategy** | Authentication flow, authorization model, input validation, output encoding, rate limiting | High |
| **ADR-026: Deployment Strategy** | EC2 + systemd, blue-green deploys, rollback procedure | Medium |
| **ADR-027: Database Strategy** | Connection pooling, migration strategy, read replicas, data retention | Medium |
| **ADR-028: Internationalization (i18n)** | Language support, currency, date/time formatting | Low (Year 1: English only) |
| **ADR-029: API Design Conventions** | Request/response formats, pagination, filtering, error envelopes | Medium |
| **ADR-030: Multi-Tenancy Strategy** | If required for enterprise customers | Low (Year 1: not required) |

**Recommendation:** Add ADR-024, ADR-025, ADR-026, and ADR-029 before Phase 1 implementation.

---

## Cross-Check Analysis

### Folder Structure ↔ Bounded Contexts

| Context | Folder | Bounded Context Doc | Match? |
|---------|--------|---------------------|--------|
| Identity | `apps/identity/` | ✅ | Yes |
| Subscription | `apps/subscription/` | ✅ | Yes |
| Property | `apps/property/` | ✅ | Yes |
| Rent | `apps/rent/` | ✅ | Yes (new) |
| Payment | `apps/payment/` | ✅ | Yes |
| Notification | `apps/notification/` | ✅ | Yes |
| Document | `apps/document/` | ✅ | Yes |
| Finance | `apps/finance/` | ✅ | Yes |
| Referral | `apps/referral/` | ✅ | Yes (renamed) |
| AI | `apps/ai/` | ✅ | Yes (consolidated) |
| Dashboard | `apps/dashboard/` | ✅ | Yes |

**Verdict:** ✅ Consistent.

### Dependency Rules ↔ Layer Rules

| Rule | Dependency Rules | Layer Rules | Match? |
|------|-----------------|-------------|--------|
| Shared cannot import apps | ✅ | ✅ | Yes |
| Domain cannot import infrastructure | ✅ | ✅ | Yes |
| Application cannot import presentation | ✅ | ✅ | Yes |
| Presentation cannot import domain | ✅ | ✅ | Yes |
| Presentation cannot import infrastructure | ✅ | ✅ | Yes |
| Cross-app imports forbidden | ✅ | ✅ | Yes |

**Verdict:** ✅ Consistent.

### Repository Pattern ↔ Service Layer

| Rule | Repository Doc | Service Layer Doc | Match? |
|------|----------------|-------------------|--------|
| Services use repositories | ✅ | ✅ | Yes |
| Services don't query ORM directly | ✅ | ✅ | Yes |
| Repositories don't contain business logic | ✅ | ✅ | Yes |
| Services are stateless | ✅ | ✅ | Yes |
| Services publish events | ❌ | ✅ | **MISMATCH** |

**Verdict:** ⚠️ Minor inconsistency. Repository doc doesn't mention events; service layer doc does.

### Migration Strategy ↔ Target Architecture

| Phase | Target | Achievable? |
|-------|--------|-------------|
| Phase 1: Cleanup | Remove dead code | ✅ Yes |
| Phase 2: Move Files | Reorganize into target structure | ✅ Yes (with bug fix) |
| Phase 3: Split God Classes | Break up large files | ✅ Yes |
| Phase 4: Repository Pattern | Add repositories | ✅ Yes |
| Phase 5: Service Layer | Extract business logic | ✅ Yes |
| Phase 6: Import Boundaries | Enforce with import-linter | ✅ Yes |
| Phase 7: Dead Code Removal | Clean up | ✅ Yes |
| Phase 8: Performance | Optimize | ✅ Yes |
| Phase 9: Architecture Freeze | Lock decisions | ✅ Yes |

**Verdict:** ✅ Realistic and achievable.

---

## Top 20 Improvements

### Critical (Fix Before Phase 1)

1. **Fix duplicate `infrastructure/` directory** in `03_target_folder_structure.md` (line 317). Rename the second occurrence to `operations/`.

2. **Fix context map arrows** in `02_bounded_contexts.md`. Change bidirectional `ID → SUB` and `SUB → ID` to unidirectional `ID → SUB`. Change `RENT →|depends on| PAY` to `RENT →|triggers| PAY`.

3. **Add missing `PaymentRecorded` event** to `07_domain_events.md` (referenced in bounded contexts but not defined).

4. **Fix Mermaid diagram 02_container.mmd**: Correct `Cron --> Gunicorn` to `Cron --> Django` and `Celery --> Gunicorn` to `Celery --> Redis --> Django`.

5. **Fix Mermaid diagram 04_layers.mmd**: Reverse `Adapters --> RepoInterfaces` arrow to `RepoInterfaces --> Adapters` (interface → implementation).

### High Priority (Address Before Phase 2)

6. **Add ADR-024: Observability Strategy** (structured logging, metrics, tracing, health checks).

7. **Add ADR-025: Security Strategy** (authentication, authorization, input validation, rate limiting).

8. **Add ADR-026: Deployment Strategy** (blue-green deploys, rollback, infrastructure as code).

9. **Add ADR-029: API Design Conventions** (request/response formats, pagination, error envelopes).

10. **Separate Shared as Layer 0** in `04_layer_rules.md`. Currently Platform and Shared are lumped together as Layer 1, but they have different dependency rules.

11. **Fix ADR path references** in ADR-010, ADR-011. The paths reference `payments.adapters.manual.ManualPaymentAdapter` but the future structure uses `apps/payment/infrastructure/adapters/`.

12. **Clarify Vertical Slice vs Horizontal Layer tension** in ADR-020. Add explicit guidance on when to use each pattern.

### Medium Priority (Address During Phase 1-2)

13. **Add transaction boundary rules** to `04_layer_rules.md`. Which layers can start/commit/rollback transactions?

14. **Add Unit of Work pattern** to `08_repository_pattern.md`. The production architecture mentions it but the target architecture doesn't include it.

15. **Standardize `PaymentResult` DTO** in `09_service_layer.md`. The `verify_payment` example returns a receipt in the result, but `submit_payment` doesn't. Make the DTO pattern consistent.

16. **Add Django migration strategy** to `11_migration_strategy.md`. How to handle app splits (e.g., `core` → `identity` + `subscription`)? How to handle table renames?

17. **Add `apps/<context>/operations/`** to `03_target_folder_structure.md` as the home for signals, tasks, and management commands (replaces the duplicate `infrastructure/`).

18. **Fix Mermaid diagram 01_context.mmd**: Move Web Frontend to External Users subgraph.

19. **Define event versioning scheme** in `07_domain_events.md`. How are event versions numbered? What is the backward compatibility policy?

20. **Add `__init__.py` guidance** to `03_target_folder_structure.md`. Currently shows `__init__.py` everywhere, but some packages (like `migrations/`) don't need it in modern Django.

---

## Top Risks

### Risk 1: Overengineering for Year 1 Team
**Severity:** Medium
**Probability:** High

The 5-layer structure + DI container + event bus + repository pattern + selectors + DTOs + commands + queries is a lot of ceremony for a 2-5 engineer team. The risk is that developers will bypass the patterns under pressure, creating inconsistency.

**Mitigation:**
- Start with simplified patterns in Phase 1-2 (skip DI container, use simple constructor injection)
- Add patterns incrementally (repositories in Phase 4, events in Phase 5)
- Enforce with architecture tests only after patterns are established

### Risk 2: Dashboard Context as Bottleneck
**Severity:** Medium
**Probability:** Medium

The Dashboard context depends on ALL other contexts. As the platform grows, dashboard queries will hit every database table, creating N+1 query storms and tight coupling.

**Mitigation:**
- Use CQRS with pre-aggregated read models for dashboard
- Implement materialized views for common dashboard queries
- Consider read replicas for dashboard queries in Stage 2

### Risk 3: Eventual Consistency Confusion
**Severity:** Medium
**Probability:** High

Domain events introduce eventual consistency. Developers used to Django's synchronous ORM may not understand that `PaymentSubmitted` event handlers run after the HTTP response returns (in Stage 2+). In Year 1, in-process events are synchronous, but the abstraction prepares for async.

**Mitigation:**
- Document the consistency model clearly in each service
- Add architecture tests that verify synchronous behavior in Year 1
- Add integration tests that verify eventual consistency in Stage 2+

### Risk 4: Django App Split Complexity
**Severity:** Medium
**Probability:** High

Splitting `core/` into `identity/` and `subscription/` requires careful migration of Django's app registry, migration history, and `INSTALLED_APPS`. Django doesn't natively support splitting one app into two.

**Mitigation:**
- Create new apps with `startapp` and manually copy models
- Create data migration to copy existing data
- Keep old app in `INSTALLED_APPS` during transition, remove after validation
- Use `allow_migrate` to control which apps migrate on which database

### Risk 5: Repository Pattern Overhead
**Severity:** Low
**Probability:** Medium

The repository pattern adds ~2x code (interface + implementation + mapping). For simple CRUD, this is overkill.

**Mitigation:**
- Provide a `GenericRepository` base class to reduce boilerplate
- Use code generation for repository implementations
- Allow direct ORM access in infrastructure layer for simple queries (bypass repository)

---

## Approval Status

### APPROVED WITH MINOR CHANGES

The target architecture is **approved** with the following conditions:

1. **Before Phase 1:** Fix the 5 critical items listed above (duplicate infrastructure directory, context map arrows, missing event, Mermaid diagrams).
2. **Before Phase 2:** Add the 4 missing ADRs (Observability, Security, Deployment, API Design).
3. **During Phase 1:** Address the 9 high-priority items.
4. **Ongoing:** Monitor the 5 risks and adjust as needed.

### What This Means

- The architecture team can proceed with **Phase 1 (Architecture Cleanup) immediately**
- **Phase 2 (Move Files)** should wait until the 5 critical fixes are applied
- The 4 missing ADRs should be drafted in parallel with Phase 1
- All future ADRs must reference this review and address the identified gaps

### What Should NOT Be Done

- Do NOT begin Phase 2 until the folder structure bug is fixed
- Do NOT implement the DI container (ADR-018) until Phase 4+
- Do NOT enforce strict import-linter rules until Phase 6
- Do NOT merge ADR-003 and ADR-004 without explicit team consensus

---

## Summary of Key Decisions

| Decision | Rationale |
|----------|-----------|
| Approve with minor changes | Architecture is sound; fixes are straightforward |
| Fix before Phase 2 | Structural bugs would cause migration failures |
| Add 4 missing ADRs | Observability, security, deployment, and API design are foundational |
| Merge ADR-003+004, ADR-005+019 | Reduces ADR count from 23 to 21, improves navigability |
| Start with simplified patterns | Reduce overengineering risk for Year 1 team |
| Enforce boundaries incrementally | Import-linter strict mode in Phase 6, not Phase 1 |

---

*This review is the final gate before architecture implementation. All identified issues must be tracked in the architecture backlog.*
