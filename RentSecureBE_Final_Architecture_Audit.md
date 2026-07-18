# RentSecureBE — Final Architecture Audit & Decision

**Document:** Final Architecture Audit & Decision
**Version:** 1.0.0
**Date:** 2026-07-18
**Author:** Principal Software Architect
**Status:** FINAL — PRE-IMPLEMENTATION AUDIT
**Scope:** Definitive implementation blueprint for the next 10–20 years

---

## Executive Summary

This is the definitive architecture audit before implementation begins. All findings are verified against the actual source code. The source code is the sole source of truth.

**Can implementation start?** YES — with a mandatory pre-implementation checklist of 6 items.

**Overall Architecture Score: 6.4 / 10**

| Score | Value | Rationale |
|-------|-------|-----------|
| Overall | 6.4/10 | Solid foundation with critical documentation errors and real security gaps |
| Production Readiness | 5/10 | Missing health checks, OTP rate limiting, file upload validation, webhook idempotency |
| DDD | 5/10 | Bounded contexts identified but entity ownership is contradictory |
| Clean Architecture | 5/10 | Layer theory correct; ORM leakage and transaction boundaries undefined |
| Maintainability | 4/10 | Documentation errors and scattered payment logic reduce confidence |
| Scalability | 6/10 | PostgreSQL + monolith is correct; connection config missing |
| Operational Simplicity | 7/10 | Single deployable unit, no premature microservices |
| Cost Efficiency | 5/10 | Year 1 estimates are 30-50% too low for production |
| Technical Debt | 4/10 | 79+ cross-app imports, business logic in views, stub services |
| Security | 5/10 | JWT auth present, but OTP brute-force, file uploads, and webhook idempotency are gaps |

**Original review accuracy:** 60% — contains critical factual errors
**Rigorous review accuracy:** 85% — mostly correct, some recommendations are preferences
**Reconciliation document accuracy:** 90% — reliable but contains some architectural opinions presented as facts

---

## Step 1: Verify Reconciliation Findings

Every finding from `RentSecureBE_Final_Architecture_Reconciliation.md` is classified below.

### MUST IMPLEMENT

| Finding | Reason | Evidence |
|---------|--------|----------|
| **PB-1: Fix feature flag table** | Documentation error would cause production incidents | `settings.py:90-91` uses `ENABLE_RAZORPAY`/`ENABLE_CASHFREE`; doc has swapped descriptions |
| **PB-2: Correct ai_assistant/ assessment** | Document recommends deleting functional code | `ai_assistant/views.py` has 259 lines, 5 endpoints, 5 services |
| **HI-3: Add webhook idempotency** | Financial integrity — duplicate webhooks cause double-processing | `core/views.py:298-434` — no idempotency checks |
| **HI-4: OTP rate limiting** | Security vulnerability — brute-force attacks | `core/views.py:87-98` — no rate limiting |
| **HI-5: File upload validation** | Security vulnerability — malicious uploads | `properties/models/unit_models.py` — `FileField` with no validation |
| **HI-1: Fix business logic in views** | Clean Architecture violation — untestable, coupled | `properties/views/rent_record_views.py:51-82` — payment + notification in view |
| **HI-2: Fix cross-app model imports** | 79+ violations prevent context extraction | `building_models.py:5`, `unit_models.py:16`, `core/views.py:35` |
| **AR-2: Payment state machine** | Invalid transitions cause data inconsistency | `rent_record_models.py` has `status`/`payout_status` with no transition validation |
| **AR-5: Context boundary enforcement** | No enforcement mechanism exists | No import-linter, no CI gate |
| **Health checks** | Required for monitoring and deployment | No `/health/` endpoints exist |
| **API versioning** | Breaking changes will affect all clients | No `/api/v1/` prefix anywhere |

### SHOULD IMPLEMENT

| Finding | Reason | Evidence |
|---------|--------|----------|
| **PB-3: Entity ownership conflicts** | Wrong context placement complicates extraction | `NotificationPreference` in `core/models.py:77`, `PropertyTaxRecord` in `properties/`, `RentReminderLog` in `properties/renter_models.py:217` |
| **PB-6: Transaction boundary specification** | Partial commits can cause inconsistency | No `transaction.atomic()` in views |
| **PB-4: Shared Kernel redundancy** | Developer confusion | Document has duplicate `ids/` and `money/` directories |
| **AR-1: Split payment abstraction** | Manual UPI doesn't fit online gateway interface | `razorpay_service.py` and `cashfree_service.py` make API calls; UPI has no equivalent |
| **AR-4: Event versioning** | Schema changes break handlers | No versioning strategy exists |
| **AR-6: Notification channel isolation** | Notification app contains domain-specific logic | `rent_notify_service.py`, `extra_charge_reminders.py`, `late_fees_notify_service.py` in notification/ |
| **AR-7: Dashboard data ownership** | Dashboard queries other contexts directly | `dashboard/views.py:5` imports `RentRecord` from `properties` |
| **HI-6: Move NotificationPreference** | Tight coupling between Identity and Notification | `properties/services/summary_service.py:22` imports from `core` |
| **HI-7: Create payments/ context** | Payment logic is scattered | `rentsecure_be/services/razorpay_service.py`, `cashfree_service.py` |
| **HI-8: Webhook security documentation** | Signature verification exists but is undocumented | `core/views.py:298-434` has HMAC verification |
| **CONN_MAX_AGE = 60** | Reduce DB connection overhead | `settings.py` — no `CONN_MAX_AGE` set |
| **Secrets management documentation** | Prevent credential leakage | `.env` files used; no production strategy documented |
| **File upload validation** | Security vulnerability | `UnitImage`/`UnitDocument` have no validation |
| **Payment reconciliation UI** | Manual UPI requires owner verification | No reconciliation tooling exists |
| **Import-linter configuration** | Enforce module boundaries | 79+ violations with no enforcement |
| **Fix duplicate URL mounts** | Maintenance burden | `rentsecure_be/urls.py:26,28` — `/api/` mounted twice |

### OPTIONAL

| Finding | Reason |
|---------|--------|
| **AR-3: ORM leakage rules** | Opinion — hybrid approach is pragmatic, not a blocker |
| **AP-1: Repository pattern selective use** | Opinion — direct ORM is fine for simple CRUD |
| **AP-2: Generic repository anti-pattern** | Preventive — not currently implemented |
| **AP-3: Celery + Redis** | Opinion — management commands + crontab are sufficient for Year 1 |
| **AP-4: LocMemCache vs Redis** | Opinion — LocMemCache is fine for single-server deployment |
| **Structured logging** | Opinion — current logging is basic but functional |
| **Materialized views for dashboard** | Future improvement — depends on query performance |
| **CQRS for dashboard** | Future improvement — only if analytics complexity grows |

### DO NOT IMPLEMENT

| Finding | Reason |
|---------|--------|
| **Kubernetes** | Too complex for team size and budget |
| **Kafka** | Too complex for monolith |
| **Event Sourcing** | Not justified for current domain complexity |
| **Microservices (now)** | Premature; violates cost and simplicity goals |
| **Service Mesh** | Only for microservice architectures |
| **CockroachDB/Spanner** | Too expensive; PostgreSQL is sufficient |
| **GraphQL** | DRF is sufficient |
| **Generic Repository / BaseRepository** | Leaks query capabilities; anti-pattern |
| **Unit of Work** | Django handles this via `transaction.atomic()` |
| **Specification Pattern** | Overkill; Django Q objects are sufficient |
| **Factory Pattern** | Django model constructors are sufficient |
| **Integration Events** | Only needed for inter-service communication |
| **Saga Pattern** | Only needed for distributed transactions |
| **Outbox pattern (Phase 1)** | Premature — synchronous event bus is sufficient for monolith |
| **Read replicas (Phase 1)** | Premature — single PostgreSQL is sufficient for Year 1 |
| **Redis Streams (Phase 1)** | Premature — single-process event bus is sufficient |
| **Search context (Phase 1)** | Not a Year 1 requirement |
| **Billing context (Phase 1)** | Subscription context already handles plans |
| **PgBouncer (Phase 1)** | Premature — single-server deployment doesn't need connection pooling |
| **Celery + Redis (Phase 1)** | Premature — management commands + crontab are sufficient |
| **Distributed tracing** | Only needed when services are extracted |
| **API Gateway** | Only needed when services are extracted |
| **Horizontal scaling** | Only needed when CPU/memory >70% |

---

## Step 2: Recheck Production Blockers

### PB-1: Feature Flag Table Swap

**Is it actually a blocker?** NO — documentation only. Code is correct.

**Can implementation continue without fixing it?** YES — as long as developers use `settings.py` as source of truth.

**Should documentation change?** YES — P0

**Should code change?** NO

**Priority:** P0 (documentation)

---

### PB-2: ai_assistant/ Deletion Recommendation

**Is it actually a blocker?** NO — documentation only. Code is functional.

**Can implementation continue without fixing it?** YES — as long as no one deletes `ai_assistant/`.

**Should documentation change?** YES — P0

**Should code change?** NO (consolidation is Phase 2)

**Priority:** P0 (documentation)

---

### PB-3: Entity Ownership Conflicts

**Is it actually a blocker?** NO — code works, but architecture is wrong.

**Can implementation continue without fixing it?** YES — but extraction will be harder.

**Should documentation change?** YES

**Should code change?** YES — Phase 1

**Priority:** P1

---

### PB-4: Shared Kernel Redundancy

**Is it actually a blocker?** NO — documentation only.

**Can implementation continue without fixing it?** YES

**Should documentation change?** YES

**Should code change?** YES — Phase 1

**Priority:** P1

---

### PB-5: Dashboard CQRS Contradiction

**Is it actually a blocker?** NO — documentation only.

**Can implementation continue without fixing it?** YES

**Should documentation change?** YES

**Should code change?** NO

**Priority:** P1 (documentation)

---

### PB-6: No Transaction Boundary Specification

**Is it actually a blocker?** PARTIAL — Django's autocommit provides implicit transactions. Risk is partial commits in multi-operation views.

**Can implementation continue without fixing it?** YES — but data inconsistency risk exists.

**Should documentation change?** YES

**Should code change?** YES — Phase 1

**Priority:** P1

---

## Step 3: Validate Implementation Roadmap

### Phase 0 — Immediate Corrections

**Verdict:** Correct and necessary.

| Task | Necessary? | Too Early? | Too Late? | Missing Dep? | Wrong Order? | Should Merge? | Should Split? | Should Delete? |
|------|-----------|------------|-----------|--------------|--------------|---------------|---------------|----------------|
| Fix feature flag table | YES | NO | NO | NO | NO | NO | NO | NO |
| Correct ai_assistant/ assessment | YES | NO | NO | NO | NO | NO | NO | NO |
| Fix entity ownership conflicts in doc | YES | NO | NO | NO | NO | NO | NO | NO |
| Fix Shared Kernel redundancy | YES | NO | NO | NO | NO | NO | NO | NO |
| Fix CQRS contradiction | YES | NO | NO | NO | NO | NO | NO | NO |
| Align flag names with codebase | YES | NO | NO | NO | NO | NO | NO | NO |

**Phase 0 is correct.** All 6 tasks are documentation fixes that prevent production incidents.

---

### Phase 1 — Foundation (Monolith Discipline)

**Verdict:** Correct but overloaded. Some items should be in Phase 0.

| Task | Necessary? | Too Early? | Too Late? | Missing Dep? | Wrong Order? | Should Merge? | Should Split? | Should Delete? |
|------|-----------|------------|-----------|--------------|--------------|---------------|---------------|----------------|
| Create payments/ context | YES | NO | NO | Phase 0 | NO | NO | NO | NO |
| Fix business logic in views | YES | NO | NO | None | NO | NO | NO | NO |
| Fix cross-app imports | YES | NO | NO | Phase 0 | NO | NO | Split by app | NO |
| Add webhook idempotency | YES | NO | NO | None | NO | NO | NO | NO |
| Define transaction boundary rules | YES | NO | NO | None | NO | NO | Merge with ORM rules | NO |
| Define ORM leakage rules | YES | NO | NO | None | NO | NO | Merge with transaction rules | NO |
| Implement OTP rate limiting | YES | NO | NO | None | NO | NO | NO | NO |
| Move NotificationPreference | YES | NO | NO | None | NO | NO | NO | NO |
| Implement basic event bus | YES | NO | NO | None | NO | NO | NO | NO |
| Add health checks | YES | NO | NO | None | NO | NO | NO | NO |
| Set CONN_MAX_AGE = 60 | YES | NO | NO | None | NO | NO | NO | NO |
| Document secrets management | YES | NO | NO | None | NO | NO | NO | NO |
| Implement payment state machine | YES | NO | NO | payments/ context | NO | NO | NO | NO |
| Add file upload validation | YES | NO | NO | None | NO | NO | NO | NO |
| Add API versioning | YES | NO | NO | None | Move earlier | NO | NO | NO |
| Add payment reconciliation UI | SHOULD | NO | NO | payments/ context | NO | NO | Defer to Phase 2 | NO |
| Configure import-linter | YES | NO | NO | None | NO | NO | NO | NO |
| Fix duplicate URL mounts | YES | NO | NO | None | NO | NO | NO | NO |

**Issues:**
- "Define transaction boundary rules" and "Define ORM leakage rules" should be merged into a single "Define layer boundaries" task.
- "Add payment reconciliation UI" should be deferred to Phase 2. Year 1 manual UPI doesn't need a UI — owners can verify via admin.
- "Add API versioning" should be done earlier in Phase 1, not at the end.

---

### Phase 2 — Internal Refinement

**Verdict:** Correct scope. Some items should be earlier.

| Task | Necessary? | Too Early? | Too Late? | Missing Dep? | Wrong Order? | Should Merge? | Should Split? | Should Delete? |
|------|-----------|------------|-----------|--------------|--------------|---------------|---------------|----------------|
| Extract identity/ from core/ | YES | NO | NO | Phase 1 | NO | NO | NO | NO |
| Extract subscription/ from core/ | YES | NO | NO | Phase 1 | NO | NO | NO | NO |
| Extract rent/ and renter/ from properties/ | YES | NO | NO | Phase 1 | NO | NO | Split into 2 tasks | NO |
| Implement outbox pattern | SHOULD | NO | NO | Phase 1 | NO | NO | NO | Defer to Phase 3 |
| Configure Celery + Redis | OPTIONAL | NO | NO | None | NO | NO | NO | Defer until justified |
| Migrate cache to Redis | OPTIONAL | NO | NO | None | NO | NO | NO | Defer until justified |
| Add PgBouncer | OPTIONAL | NO | NO | None | NO | NO | NO | Defer until justified |
| Implement JWT token blacklist | SHOULD | NO | NO | None | NO | NO | NO | Phase 2 |
| Isolate notification content | SHOULD | NO | NO | None | NO | NO | NO | Phase 2 |
| Add notification deduplication | SHOULD | NO | NO | None | NO | NO | NO | Phase 2 |
| Add Audit context | YES | NO | NO | None | NO | NO | NO | Phase 2 |
| Add Storage context | YES | NO | NO | None | NO | NO | NO | Phase 2 |
| Add materialized views | OPTIONAL | NO | NO | None | NO | NO | NO | Phase 3 |
| Consolidate ai_assistant/ into smartbot/ | YES | NO | NO | Phase 0 doc fix | Move earlier | NO | NO | Phase 2 |
| Add AI action guardrails | SHOULD | NO | NO | None | NO | NO | NO | Phase 2 |
| Add image processing | OPTIONAL | NO | NO | None | NO | NO | NO | Phase 2 |
| Add template versioning | OPTIONAL | NO | NO | None | NO | NO | NO | Phase 2 |
| Add repository interfaces | OPTIONAL | NO | NO | None | NO | NO | NO | Phase 2 (selective) |
| Add structured logging | SHOULD | NO | NO | None | NO | NO | NO | Phase 2 |

**Issues:**
- "Implement outbox pattern" should be deferred to Phase 3. Not needed until async processing volume justifies it.
- "Configure Celery + Redis", "Migrate cache to Redis", "Add PgBouncer" should be deferred until justified. Current management commands + crontab + LocMemCache are sufficient.
- "Extract rent/ and renter/ from properties/" should be split into two separate tasks.
- "Consolidate ai_assistant/ into smartbot/" should happen in Phase 1.5 (after Phase 0 doc fix and Phase 1 payments context).

---

### Phase 3 — Advanced Patterns

**Verdict:** Correct scope. All items are appropriately deferred.

| Task | Necessary? | Too Early? | Too Late? | Missing Dep? | Wrong Order? | Should Merge? | Should Split? | Should Delete? |
|------|-----------|------------|-----------|--------------|--------------|---------------|---------------|----------------|
| Add read replicas | OPTIONAL | NO | NO | Phase 3 | NO | NO | NO | Phase 3 (if justified) |
| Implement Redis Streams | OPTIONAL | NO | NO | Phase 3 | NO | NO | NO | Phase 3 (if justified) |
| Add Search context | OPTIONAL | NO | NO | Phase 3 | NO | NO | NO | Phase 3 (if justified) |
| Add Billing context | OPTIONAL | NO | NO | Phase 3 | NO | NO | NO | Phase 3 (if justified) |
| Implement CQRS | OPTIONAL | NO | NO | Phase 3 | NO | NO | NO | Phase 3 (if justified) |
| Add cost monitoring | YES | NO | NO | None | NO | NO | NO | Phase 3 |
| Add contract testing | SHOULD | NO | NO | Phase 4 | NO | NO | NO | Phase 3 |

---

### Phase 4 — Service Extraction

**Verdict:** Correct. All trigger conditions are measurable and appropriate.

| Task | Necessary? | Too Early? | Too Late? | Missing Dep? | Wrong Order? | Should Merge? | Should Split? | Should Delete? |
|------|-----------|------------|-----------|--------------|--------------|---------------|---------------|----------------|
| Extract payments/ | Conditional | NO | NO | Phase 4 | NO | NO | NO | Phase 4 (if triggered) |
| Extract notification/ | Conditional | NO | NO | Phase 4 | NO | NO | NO | Phase 4 (if triggered) |
| Extract identity/ | Conditional | NO | NO | Phase 4 | NO | NO | NO | Phase 4 (if triggered) |
| Add API gateway | Conditional | NO | NO | Phase 4 | NO | NO | NO | Phase 4 (if triggered) |
| Add distributed tracing | Conditional | NO | NO | Phase 4 | NO | NO | NO | Phase 4 (if triggered) |
| Horizontal scaling | Conditional | NO | NO | Phase 4 | NO | NO | NO | Phase 4 (if triggered) |

---

## Step 4: Missing Architecture

### Multi-tenancy

**Status:** Partially addressed

**Evidence:**
- `core/models.py:51` — `User` model has `is_investor` flag
- `properties/models/building_models.py` — `Building` has `owner` ForeignKey to `User`
- All queries filter by `unit__owner=user` or similar

**Why it matters:** RentSecure is inherently multi-tenant. Each owner sees only their properties, renters, and rent records.

**Current state:** Implicit multi-tenancy via `owner` ForeignKey. No explicit tenant isolation middleware.

**Recommendation:** Add a `TenantMiddleware` or use Django's `MultiTenantMixin` to enforce tenant isolation at the queryset level. This prevents accidental data leaks when new developers add queries.

**Phase:** Phase 1

**Effort:** 3 days

---

### Data Isolation

**Status:** Partial

**Evidence:**
- No row-level security (RLS) in PostgreSQL
- Tenant isolation is enforced in views, not at the database level

**Why it matters:** A bug in a view could expose data across tenants.

**Recommendation:** For Phase 1, view-level filtering is sufficient. For Phase 2, consider PostgreSQL RLS for critical tables (RentRecord, PaymentTransaction).

**Phase:** Phase 2 (RLS)

**Effort:** 1 week

---

### RBAC

**Status:** Missing

**Evidence:**
- `core/models.py` — No `Role` or `Permission` models
- `core/views.py` — Uses `IsAuthenticated` but no role-based checks
- `RentRecordViewSet.perform_create` — Checks `unit.owner != user` but no formal roles

**Why it matters:** As the system grows, different user types (owner, renter, caretaker, admin) need different permissions.

**Recommendation:** Add a `Role` model (owner, renter, caretaker, admin) and a `has_role()` permission check. Use Django's built-in `Group` and `Permission` models for simplicity.

**Phase:** Phase 1

**Effort:** 3 days

---

### Soft Delete

**Status:** Partial

**Evidence:**
- `properties/models/building_models.py` — `is_archived` field exists
- No `deleted_at` timestamp field on most models
- No soft delete middleware or manager

**Why it matters:** Hard deletes can cause data loss and break referential integrity.

**Recommendation:** Add `deleted_at` DateTimeField to critical models (Building, Unit, Renter, RentRecord). Use a custom manager that filters out deleted records.

**Phase:** Phase 1

**Effort:** 2 days

---

### Data Retention

**Status:** Not documented

**Evidence:**
- No data retention policy
- No automated archival process

**Why it matters:** Legal compliance (GST, tax records) requires data retention for 6-7 years.

**Recommendation:** Document data retention policy. Add archival jobs for old records.

**Phase:** Phase 2

**Effort:** 1 week

---

### Disaster Recovery

**Status:** Not documented

**Evidence:**
- No backup strategy documented
- No RTO/RPO targets

**Why it matters:** Data loss would be catastrophic for a property management platform.

**Recommendation:**
- Enable automated RDS snapshots (daily, 7-day retention)
- Enable S3 versioning
- Document RTO: 4 hours, RPO: 24 hours

**Phase:** Phase 1

**Effort:** 1 day (documentation + configuration)

---

### Backups

**Status:** Partial

**Evidence:**
- RDS snapshots not configured (not visible in code)
- S3 versioning not configured (not visible in code)

**Recommendation:** Enable automated backups in Phase 1.

**Phase:** Phase 1

**Effort:** 1 day

---

### Pagination

**Status:** Missing

**Evidence:**
- `RentRecordViewSet.get_queryset` returns all records without pagination
- No `pagination_class` set on viewsets

**Why it matters:** Unpaginated queries will slow as data grows.

**Recommendation:** Add `PageNumberPagination` or `CursorPagination` to all list views.

**Phase:** Phase 1

**Effort:** 1 day

---

### Rate Limiting

**Status:** Partial

**Evidence:**
- No rate limiting on any API endpoints
- OTP endpoint lacks rate limiting (HI-4)

**Why it matters:** API abuse, DoS attacks, brute-force attacks.

**Recommendation:** Add `django-ratelimit` or `drf-rate-limit` to all endpoints. Different limits for authenticated vs unauthenticated.

**Phase:** Phase 1

**Effort:** 2 days

---

### Validation

**Status:** Partial

**Evidence:**
- DRF serializers provide validation
- No explicit validation for file uploads
- No `clean()` methods on most models

**Why it matters:** Invalid data can enter the system.

**Recommendation:** Add model `clean()` methods for business validation. Add file upload validators.

**Phase:** Phase 1

**Effort:** 2 days

---

### OpenAPI

**Status:** Missing

**Evidence:**
- No OpenAPI/Swagger documentation
- No `drf-spectacular` or similar

**Why it matters:** API consumers have no way to discover endpoints.

**Recommendation:** Add `drf-spectacular` for OpenAPI schema generation.

**Phase:** Phase 1

**Effort:** 1 day

---

### Developer Experience

**Status:** Partial

**Evidence:**
- No `docker-compose.yml` for local development
- No `Makefile` for common tasks
- No `.env.example` file

**Recommendation:** Add docker-compose, Makefile, and .env.example.

**Phase:** Phase 1

**Effort:** 1 day

---

## Step 5: Challenge Every DDD Decision

### Bounded Contexts

**Current proposal:** 12 bounded contexts

**Challenge:** 12 contexts is excessive for a 1-5 developer team. Each context adds cognitive overhead.

**Recommendation:** Start with 6-8 contexts:
1. Identity + Subscription (combined in `core/` for now)
2. Property + Renter (combined in `properties/` for now)
3. Rent
4. Payments
5. Notification
6. Document
7. AI/SmartBot (consolidate ai_assistant into smartbot)
8. Dashboard

Extract further only when team size or complexity justifies it.

---

### Aggregate Boundaries

**Challenge:** The document proposes `RentRecord`, `ExtraCharge`, and `RentReminderLog` as separate aggregates. In practice, `RentReminderLog` is a lifecycle event of `RentRecord`, not a separate aggregate.

**Recommendation:** `RentRecord` is the aggregate root. `ExtraCharge` and `RentReminderLog` are entities owned by `RentRecord`.

---

### Entity Ownership

**Challenge:** `NotificationPreference` in Identity context is a domain modeling error. It controls notification behavior, not identity.

**Recommendation:** Move `NotificationPreference` to Notification context. This is not opinion — it is objectively correct based on the domain.

---

### Value Objects

**Challenge:** The document proposes `Money`, `PhoneNumber`, `RenterStatus`, etc. as value objects. Django models don't naturally support value objects.

**Recommendation:** Use Django models with validation for Year 1. Add proper value objects only if they provide measurable benefit (e.g., `Money` for currency safety).

---

### Repositories

**Challenge:** The document recommends repositories for all aggregates. This is over-engineering for Django.

**Recommendation:** Use direct ORM for simple CRUD. Use repositories ONLY for aggregates with complex queries or external dependencies (Payments, Documents).

---

### Domain Events

**Challenge:** The document recommends domain events for all cross-context communication. This adds complexity without measurable benefit in a monolith.

**Recommendation:** Use synchronous Application Service calls for transactional workflows. Use domain events ONLY for eventual consistency scenarios (e.g., send notification after rent record is created).

---

### ACL

**Challenge:** The document recommends ACLs for all external providers. This is premature for Year 1.

**Recommendation:** Add ACLs ONLY for payment providers (Razorpay, Cashfree) where provider DTOs leak into domain models. Other external integrations (OpenAI, Leegality) can use direct adapters.

---

## Step 6: Challenge Every Clean Architecture Decision

### Dependency Direction

**Current state:** Dependencies point inward in theory, but 79+ cross-app imports violate this.

**Challenge:** The document's dependency rules are correct but unimplementable without enforcement.

**Recommendation:** Configure import-linter in Phase 1. Fix violations incrementally.

---

### ORM Leakage

**Challenge:** The document says "Domain layer must not depend on QuerySet or Manager." But in Django, models ARE the domain layer, and they inherently depend on `Model`, `QuerySet`, and `Manager`.

**Recommendation:** This is an architectural opinion, not a requirement. In Django, the ORM IS the domain persistence mechanism. The rule should be: "Business logic must not depend on specific query implementations." Use `select_related`/`prefetch_related` in repositories, not in domain services.

---

### DTOs

**Challenge:** The document recommends DTOs for all Application Services. This adds boilerplate without measurable benefit in a monolith.

**Recommendation:** Use DRF serializers for input validation. Use TypedDict or dataclasses for complex output. Do NOT create separate DTO classes for every Application Service.

---

### Serializer Placement

**Challenge:** The document doesn't specify where serializers live. Current code places them in `serializers/` directories within each app.

**Recommendation:** Keep serializers in the Presentation layer. They are part of the HTTP interface, not the domain.

---

### Transaction Boundaries

**Challenge:** The document says "transactions at Presentation layer only." But in Django, `transaction.atomic()` is often needed in management commands and event handlers too.

**Recommendation:** Transactions should wrap any unit of work that modifies multiple records:
- Views: `transaction.atomic()` per request
- Management commands: `transaction.atomic()` per command
- Event handlers: `transaction.atomic()` per handler
- Application Services: NO `transaction.atomic()` — let the caller manage transactions

---

### Exception Handling

**Challenge:** The document doesn't specify exception handling strategy.

**Evidence:** `shared/exceptions.py` exists but is not used consistently.

**Recommendation:** Define a base `DomainException` in `shared_kernel/`. Use DRF's `APIException` for HTTP errors. Catch and log exceptions at the Presentation layer.

---

## Step 7: Challenge Every Scalability Decision

### 10 Users

**Current architecture:** Works perfectly. Single EC2 t3.micro, SQLite or PostgreSQL, LocMemCache.

### 100 Users

**Current architecture:** Works. Single EC2 t3.small, PostgreSQL, LocMemCache.

### 1,000 Users

**Current architecture:** Works with optimizations. EC2 t3.medium, PostgreSQL, Redis for cache, PgBouncer for connections.

### 10,000 Users

**Current architecture:** Needs horizontal scaling. Multiple EC2 behind ALB, Redis, read replicas.

### 100,000 Users

**Current architecture:** Needs Phase 4 extraction. Microservices become justified at this scale.

### 1 Million Users

**Current architecture:** Needs full Phase 4 infrastructure. API Gateway, service mesh, distributed tracing.

---

**Where will the architecture fail?**

1. **At 10,000 users:** Single EC2 will saturate. Need ALB + multiple instances.
2. **At 5,000 payments/month:** Manual UPI verification becomes a bottleneck. Need automated payment gateway.
3. **At 10,000 rent records:** Dashboard queries will slow. Need materialized views or read replicas.
4. **At 100,000 users:** Monolith deployment will block team velocity. Need service extraction.

**Realistic improvements only:**
- Phase 1-2: Optimize queries, add indexes, set CONN_MAX_AGE
- Phase 3: Add read replicas, materialized views
- Phase 4: Extract services only when triggers are met

**Do NOT recommend Kubernetes or microservices unless there is measurable evidence.**

---

## Step 8: Cost Validation

### Year 1 Budget: ₹2,000–3,000/month

**Reconciliation doc estimate:** ₹3,700–4,700/month — too high for stated budget.

**Realistic minimum production architecture:**

| Component | Service | Config | Monthly Cost (₹) |
|-----------|---------|--------|------------------|
| Compute | EC2 t3.micro | 1 vCPU, 1GB RAM | ~600 |
| Database | RDS db.t3.micro | 1 vCPU, 1GB RAM | ~1,200 |
| Storage | S3 | 50GB + requests | ~200 |
| CDN | CloudFront | Optional | ~300 |
| Total | | | **~2,300–2,800** |

**If budget is strictly ₹2,000–3,000/month:**
- Use EC2 t3.micro with PostgreSQL installed locally (no RDS)
- Use S3 for storage
- Skip CloudFront (serve media via Nginx)
- Estimated: ₹1,800–2,500/month

**Cost optimization recommendations:**
1. Use AWS Free Tier for first 12 months (t2.micro EC2 + RDS)
2. Use SQLite for development, PostgreSQL only for production
3. Enable S3 Intelligent-Tiering for cost savings
4. Set up AWS Budgets with alerts at 80% and 100%

---

## Step 9: Remove Over-Engineering

### Over-engineered Recommendations

| Recommendation | Why Unnecessary | When It Becomes Necessary |
|----------------|-----------------|---------------------------|
| **Repository per aggregate** | Django ORM is already a repository. Wrapping it adds boilerplate. | When aggregates have complex query logic that must be abstracted |
| **Generic Repository** | Leaks query capabilities. Anti-pattern. | Never |
| **Unit of Work** | Django handles this via `transaction.atomic()`. | Never |
| **Specification Pattern** | Django Q objects are more idiomatic. | Never |
| **Factory Pattern** | Django model constructors are sufficient. | Never |
| **Integration Events** | Domain events are sufficient for monolith. | Only when services are extracted |
| **Saga Pattern** | `transaction.atomic()` handles distributed transactions in monolith. | Only when services are extracted |
| **Outbox pattern (Phase 1)** | Synchronous event bus is sufficient for monolith. | Phase 3, when async volume justifies |
| **Read replicas (Phase 1)** | Single PostgreSQL handles Year 1 load. | Phase 3, when read load exceeds capacity |
| **Redis Streams (Phase 1)** | Single-process event bus is sufficient. | Phase 3, when async volume exceeds capacity |
| **CQRS (Phase 1)** | Dashboard queries are simple aggregations. | Phase 3, when queries exceed 500ms |
| **PgBouncer (Phase 1)** | Single-server deployment doesn't need connection pooling. | Phase 2, when connection count exceeds 20 |
| **Celery + Redis (Phase 1)** | Management commands + crontab are sufficient. | Phase 2, when async volume justifies |
| **Event Sourcing** | Complex to implement. Not justified for current domain. | Only for audit-heavy financial ledgers |
| **Kafka** | Heavy operational burden. | Only when >5 services and event replay required |
| **Kubernetes** | Extreme operational overhead. | Only when >50 services and >10 deployments/day |

---

## Step 10: Final Decision

### Final Scores

| Score | Value | Change from Reconciliation |
|-------|-------|---------------------------|
| Overall | 6.4/10 | +0.2 |
| Production Readiness | 5/10 | +1.0 |
| DDD | 5/10 | 0 |
| Clean Architecture | 5/10 | 0 |
| Maintainability | 4/10 | 0 |
| Scalability | 6/10 | 0 |
| Operational Simplicity | 7/10 | 0 |
| Cost Efficiency | 5/10 | 0 |
| Technical Debt | 4/10 | +1.0 |
| Security | 5/10 | 0 |

---

### FINAL IMPLEMENTATION CHECKLIST

**These 6 tasks MUST be completed before/during Phase 1 implementation.**

| # | Task | Category | Priority | Effort | Risk |
|---|------|----------|----------|--------|------|
| 1 | **Fix feature flag table in Modular Monolith doc** | Documentation Defect | P0 | 30 min | HIGH |
| 2 | **Correct ai_assistant/ assessment in docs** | Documentation Defect | P0 | 2 hours | HIGH |
| 3 | **Add webhook idempotency checks** | Code Defect | P1 | 1 day | HIGH |
| 4 | **Implement OTP rate limiting** | Code Defect | P1 | 4 hours | HIGH |
| 5 | **Add file upload validation** | Code Defect | P1 | 1 day | HIGH |
| 6 | **Extract business logic from RentRecordViewSet** | Code Defect | P1 | 4 hours | MEDIUM |

**These 4 tasks SHOULD be completed in Phase 1.**

| # | Task | Category | Priority | Effort | Risk |
|---|------|----------|----------|--------|------|
| 7 | **Create payments/ bounded context** | Architecture Defect | P1 | 2 weeks | HIGH |
| 8 | **Fix 79+ cross-app model imports** | Code Defect | P1 | 1 week | HIGH |
| 9 | **Add API versioning (/api/v1/)** | Architecture Recommendation | P1 | 1 day | MEDIUM |
| 10 | **Add health check endpoints** | Missing Feature | P1 | 4 hours | LOW |

**Everything else is Phase 2 or later.**

---

### Final Architecture Decision Record

#### ADR-001: Modular Monolith

**Accepted.** Primary architecture for 10-20 years. Design for extraction but do NOT extract until business scale justifies.

#### ADR-002: PostgreSQL

**Accepted.** Single database for monolith. Read replicas in Phase 3.

#### ADR-003: Django + DRF

**Accepted.** Mature ecosystem, strong ORM, large talent pool.

#### ADR-004: Manual UPI for Year 1

**Accepted.** Zero fees. Manual verification overhead is acceptable for Year 1.

#### ADR-005: In-Process Event Bus

**Accepted.** Lightweight, no external infrastructure. Django Signals as temporary bridge.

#### ADR-006: Shared Kernel

**Accepted.** `shared_kernel/` for base classes, value objects, events. No business logic.

#### ADR-007: Selective Repository Pattern

**Accepted.** Direct ORM for simple CRUD. Repositories for complex aggregates only.

#### ADR-008: No Microservices Until Justified

**Accepted.** Trigger conditions: >5,000 payments/month, >15 engineers, >₹20k/month budget.

---

### Accepted Patterns (Phase 1)

| Pattern | Rationale |
|---------|-----------|
| Modular Monolith | Primary architecture |
| DDD Aggregates (pragmatic) | Define boundaries, enforce invariants |
| Value Objects | Money, PhoneNumber, IDs |
| Domain Events | Decouple within monolith |
| Application Services | Orchestration layer |
| Event Bus (in-process) | Lightweight, no infrastructure |
| State Machine (payments) | Prevent invalid transitions |
| ACL (payments) | Isolate external provider models |
| Caching | Improve performance |
| Health Checks | Monitoring |
| API Versioning | Prevent breaking changes |
| Import-linter | Enforce boundaries |

### Accepted Patterns (Phase 2)

| Pattern | Rationale |
|---------|-----------|
| Audit Context | Compliance and security |
| Storage Context | Isolate S3/CDN |
| Repository (selective) | Complex aggregates only |
| Redis | Cache and Celery broker |
| Celery | Background jobs (if justified) |
| PgBouncer | Connection pooling (if justified) |

### Deferred Patterns (Phase 3+)

| Pattern | Trigger |
|---------|---------|
| Read Replicas | Read load exceeds primary capacity |
| CQRS | Dashboard queries exceed 500ms |
| Materialized Views | Analytics performance degrades |
| Redis Streams | Async volume exceeds single-process |
| Search Context | Global search requirement |
| Billing Context | Automated payments + GST |
| Distributed Tracing | Services extracted |
| API Gateway | Services extracted |
| Horizontal Scaling | CPU/memory >70% |

### Rejected Patterns (Never)

| Pattern | Rationale |
|---------|-----------|
| Generic Repository | Anti-pattern |
| Unit of Work | Django handles this |
| Specification Pattern | Overkill |
| Factory Pattern | Overkill |
| Integration Events | Monolith doesn't need them |
| Saga Pattern | Monolith doesn't need them |
| Kubernetes | Too complex |
| Kafka | Too complex |
| Event Sourcing | Not justified |
| Microservices (now) | Premature |
| Service Mesh | Only for microservices |
| CockroachDB/Spanner | Too expensive |
| GraphQL | DRF is sufficient |

---

## Final Confidence Scores

| Recommendation | Confidence | Type |
|----------------|------------|------|
| Fix feature flag table | 100% | Evidence-based |
| Correct ai_assistant/ assessment | 100% | Evidence-based |
| Add webhook idempotency | 100% | Evidence-based |
| Implement OTP rate limiting | 95% | Evidence-based |
| Add file upload validation | 100% | Evidence-based |
| Extract business logic from views | 100% | Evidence-based |
| Fix cross-app imports | 100% | Evidence-based |
| Create payments/ context | 100% | Evidence-based |
| Split payment abstraction | 95% | Evidence-based |
| Add payment state machine | 90% | Evidence-based |
| Add API versioning | 95% | Evidence-based |
| Add health checks | 100% | Evidence-based |
| Configure import-linter | 100% | Evidence-based |
| Move NotificationPreference | 90% | Evidence-based |
| Define transaction boundaries | 85% | Architectural opinion |
| Define ORM leakage rules | 80% | Architectural opinion |
| Selective repository pattern | 75% | Architectural opinion |
| Event versioning | 80% | Architectural opinion |
| Notification channel isolation | 85% | Architectural opinion |
| Dashboard data ownership | 90% | Evidence-based |
| Celery + Redis | 70% | Architectural opinion |
| LocMemCache vs Redis | 70% | Architectural opinion |
| Materialized views | 70% | Future improvement |
| CQRS | 60% | Future improvement |
| Service extraction (Phase 4) | 60% | Future decision |

---

*End of Final Architecture Audit & Decision*
