# RentSecureBE — Official Architecture v1.0

**Status:** APPROVED — Production Standard
**Date:** 2026-07-19
**Scope:** Complete architectural standard for 20+ year maintainability
**Authority:** Principal Software Architect
**Applies to:** All engineering teams

---

## 1. Executive Summary

RentSecureBE is a Django + DRF modular monolith serving property management and rent collection. The current `core` app is a **God App** containing 9+ bounded contexts, violating every DDD and clean-architecture principle. This document defines the target architecture, migration strategy, and long-term evolution path.

**Current State:**
- 1 God App (`core`) with 9 responsibilities
- 145 cross-app import violations
- 4 circular dependency cycles
- 561-line god view file
- Payment SDKs instantiated in views
- No clean architecture layers

**Target State:**
- 11 bounded contexts in `apps/`
- Zero circular dependencies
- Zero infrastructure boundary violations
- Clean architecture layers within each app
- Import-linter enforced in CI
- Independently deployable contexts (future microservice extraction)

**Migration Approach:** Incremental, backward-compatible, zero-downtime phases over 15-20 weeks.

---

## 2. Final Architecture Score

| Dimension | Current | Target | Gap |
|---|---|---|---|
| Bounded Context Separation | 0/10 | 9/10 | Critical |
| Dependency Direction | 2/10 | 9/10 | Critical |
| Layer Compliance | 1/10 | 8/10 | Critical |
| Testability | 4/10 | 8/10 | High |
| Public API Design | 2/10 | 8/10 | High |
| Import-Linter Compliance | 1/10 | 9/10 | Critical |
| Dead Code | 3/10 | 9/10 | Medium |
| Security | 6/10 | 9/10 | Medium |
| Performance | 5/10 | 7/10 | Medium |
| Scalability | 1/10 | 9/10 | Critical |

**Overall:** 2.1/10 → 8.5/10

---

## 3. Architecture Decisions

### 3.1 Bounded Contexts

| Decision | Context | Action | Reason | Risk | Migration Impact | Long-term Impact |
|---|---|---|---|---|---|---|
| **KEEP** | `identity` | Create new app | User, auth, profile, OTP are cohesive | Low | Phase 1 | High — foundation for all other contexts |
| **KEEP** | `subscription` | Create new app | Plans, add-ons, limits, feature flags are cohesive | Low | Phase 2 | High — scales independently |
| **KEEP** | `property` | Keep existing | Already well-structured, owns buildings/units/renters | Low | None | High — stable domain |
| **MODIFY** | `rent` | Split from `property` | `RentRecord` has payment and agreement concerns that cross boundaries | Medium | Phase 2+ | High — clean separation of concerns |
| **KEEP** | `payment` | Extend existing | Already has adapters, add models and webhooks | Medium | Phase 3 | High — payment scales independently |
| **KEEP** | `notification` | Keep existing | Already well-structured | Low | Phase 4 (add preferences) | Medium |
| **KEEP** | `document` | Keep existing | Already well-structured | Low | None | Medium |
| **KEEP** | `finance` | Keep existing | Already well-structured | Low | None | Medium |
| **KEEP** | `referral` | Extend existing | Already exists, add service | Low | Phase 4 | Medium |
| **DEFER** | `ai` | Consolidate later | `ai_assistant` is dead code, `smartbot` exists | Low | Phase 6 | Medium |
| **KEEP** | `dashboard` | Create new | Reporting is distinct from property management | Low | Phase 4 | Medium |
| **KEEP** | `shared` | Keep existing | Shared kernel | Low | Move `type_compat` | High — must remain pure |
| **KEEP** | `platform` | Create new | Infrastructure adapters | Low | Phase 6 | High — enables future extraction |
| **KEEP** | `config` | Create new | Django configuration | Low | Phase 6 | Medium |

### 3.2 AUTH_USER_MODEL Strategy

**Decision: MODIFY — Move User into Identity, but keep Core as thin shim during transition.**

| Approach | Evaluation |
|---|---|
| **Option A: Move User to Identity** | **RECOMMENDED** — User is the identity aggregate root. Long-term maintainability demands it. |
| Option B: Keep User in Core | **REJECTED** — Keeps the God App alive. Identity context cannot be clean without owning its aggregate root. |

**Implementation:**
1. Create `identity.User` model
2. Create migration
3. Create data migration to copy `core_user` → `identity_user`
4. Update `AUTH_USER_MODEL = "identity.User"`
5. Keep `core.User` as proxy for 1 release cycle
6. Remove `core.User` in Phase 5

**Risk:** HIGH — requires database migration and `AUTH_USER_MODEL` change
**Mitigation:**
- Use Django's migration strategy with data migration
- Schedule during low-traffic window
- Keep `core.User` as proxy during transition
- Full rollback plan tested in staging

**Migration Impact:** 1 sprint with downtime window
**Long-term Impact:** Clean identity boundary, enables independent identity service

### 3.3 Folder Structure

**Decision: MODIFY — Use simplified Clean Architecture, not full DDD.**

| Layer | Keep | Reason |
|---|---|---|
| `domain/` | **DEFER** | Overhead for MVP. Add in Phase 6 when teams grow. |
| `application/` | **KEEP** | Services, commands, queries — essential for clean architecture |
| `infrastructure/` | **KEEP** | Persistence, repositories, external adapters — essential |
| `interfaces/` | **KEEP** | Views, serializers, URLs — essential for Django |
| `ports/` | **KEEP for payment** | Payment adapters need clear interfaces |
| `repositories/` | **MODIFY** — Add selectively | Only for complex queries, not every model |
| `events/` | **DEFER** | Use Django signals for now, add event bus in Phase 6 |
| `commands/` | **KEEP** | Write operations |
| `queries/` | **KEEP** | Read operations |

**Simplified Structure (Production-Ready):**
```
apps/<context>/
├── __init__.py
├── apps.py
├── models.py                    # Django ORM models (infrastructure)
├── services.py                  # Application services (or services/)
├── repositories.py              # Only if needed
├── views.py                     # Or views/
├── serializers.py               # Or serializers/
├── urls.py
├── admin.py
├── signals.py
├── migrations/
└── tests/
```

**Rationale:** Full DDD structure (`domain/`, `application/`, `infrastructure/`, `interfaces/`) adds significant file count and cognitive overhead. For a Django monolith with 5-20 developers, the simplified structure is more maintainable. Adopt full DDD structure only when extracting microservices in Stage 2+.

### 3.4 Repository Pattern

**Decision: MODIFY — Use selectively, not universally.**

| Rule | Application |
|---|---|
| **USE repository for:** | Complex queries spanning multiple tables, queries used by 3+ views/services, read models that differ from write models |
| **DO NOT use repository for:** | Simple CRUD, single-model queries, queries used by 1 view |
| **Example USE:** | `OwnerReportingRepository` — complex aggregation for dashboard |
| **Example NO:** | `UserRepository` for `User.objects.get(id=...)` — use ORM directly |

**Rationale:** Repository pattern adds indirection. For Django's well-understood ORM, overuse creates unnecessary abstraction. Use repositories only where they provide clear value: complex queries, query reuse, or read/write model separation.

### 3.5 CQRS

**Decision: REMOVE — Do not implement CQRS at this stage.**

| Aspect | Evaluation |
|---|---|
| Command/Query separation | **REJECTED** — Adds complexity without clear benefit for current scale |
| Separate read models | **DEFER** — Add in Phase 6 if dashboard performance requires it |
| Django support | Django is not designed for CQRS. Fighting the framework reduces productivity. |

**Rationale:** CQRS is appropriate for event-sourced systems or systems with dramatically different read/write loads. RentSecure does not have these characteristics. Use Django's ORM for both reads and writes. Optimize with `select_related`/`prefetch_related` and caching instead.

### 3.6 Domain Events

**Decision: MODIFY — Use Django signals for in-process, add event bus in Phase 6.**

| Approach | Current | Target | Timeline |
|---|---|---|---|
| Direct service calls | Yes | No | Phase 3 |
| Django signals | Yes | Yes (Phase 1-5) | Now |
| Event bus | No | Yes | Phase 6 |
| Outbox pattern | No | Yes (if microservices) | Stage 2+ |

**Evolution Path:**
1. **Phase 1-5:** Use Django signals for in-process events (e.g., `UserCreated` → create subscription)
2. **Phase 6:** Add in-process event bus (`platform/events/bus.py`) for decoupled in-process communication
3. **Stage 2+:** Add outbox pattern if extracting microservices

**Rationale:** Django signals are well-understood, require no additional infrastructure, and work for in-process communication. An event bus adds complexity without clear benefit until microservice extraction. Outbox pattern is only needed for distributed systems.

### 3.7 Platform Layer

**Decision: KEEP — Minimal, focused platform layer.**

| Component | Keep | Reason |
|---|---|---|
| `cache/` | **KEEP** | Cache adapters (LocMem, Redis) |
| `storage/` | **KEEP** | File storage adapters (local, S3) |
| `search/` | **KEEP** | Search adapters (PostgreSQL full-text, OpenSearch) |
| `events/` | **KEEP** | Event bus infrastructure |
| `di/` | **REMOVE** | Django's dependency injection is sufficient. Overhead not justified. |
| `queue/` | **REMOVE** | Use Django management commands + cron/systemd (Year 1). Celery is Stage 2. |
| `email/` | **REMOVE** | Use Django's email framework directly in notification adapters |
| `sms/` | **REMOVE** | Use Django's email framework directly in notification adapters |
| `whatsapp/` | **REMOVE** | Use Django's email framework directly in notification adapters |
| `voice/` | **REMOVE** | Use Django's email framework directly in notification adapters |

**Final Platform Structure:**
```
platform/
├── __init__.py
├── cache/
│   ├── __init__.py
│   ├── interfaces.py
│   ├── locmem.py
│   └── redis.py
├── storage/
│   ├── __init__.py
│   ├── interfaces.py
│   ├── local.py
│   └── s3.py
├── search/
│   ├── __init__.py
│   ├── interfaces.py
│   ├── postgres.py
│   └── opensearch.py
└── events/
    ├── __init__.py
    ├── bus.py
    └── handlers.py
```

**Rationale:** Platform layer should contain only infrastructure adapters with clear interfaces. Communication channels (email, SMS, WhatsApp, voice) belong in `notification/adapters/`, not `platform/`. Queue/celery is Stage 2. DI container is unnecessary for Django.

### 3.8 Shared Kernel

**Decision: KEEP — Strict rules, prevent dumping ground.**

**Allowed in `shared/`:**
- Base exception classes (`exceptions.py`)
- Shared enumerations (`enums.py`)
- Generic type aliases (`types.py`)
- Generic utilities (`utils.py`)
- Shared validators (`validators.py`)
- Base service classes (`services/base.py`)
- Domain event base classes (`domain_events.py`)
- Abstract interface definitions (`interfaces.py`)
- Constants (`constants.py`)
- Python 3.12 compatibility shims (`type_compat.py`)

**Forbidden in `shared/`:**
- Any Django app imports
- Any model definitions
- Any service implementations
- Any business logic
- Any domain-specific code
- Any imports from `apps/`, `platform/`, or `config/`

**Rationale:** Shared kernel is the most stable layer. It must remain pure and free of business logic. Any domain-specific code belongs in the appropriate bounded context.

### 3.9 Import Rules

**Final Dependency Matrix:**

| Source | Can Import | Cannot Import |
|---|---|---|
| `shared/` | Nothing (leaf) | Everything |
| `platform/` | `shared/` | All `apps/*` |
| `config/` | `shared/`, `platform/` | All `apps/*` |
| `identity/` | `shared/`, `platform/` | All other `apps/*` |
| `subscription/` | `shared/`, `platform/`, `identity/` | All other `apps/*` |
| `property/` | `shared/`, `platform/`, `identity/`, `subscription/` | `rent/`, `payment/`, `notification/`, `finance/`, `referral/`, `dashboard/`, `ai/` |
| `rent/` | `shared/`, `platform/`, `identity/`, `subscription/`, `property/`, `payment/` | `notification/`, `finance/`, `referral/`, `dashboard/`, `ai/` |
| `payment/` | `shared/`, `platform/`, `identity/` | `property/`, `rent/`, `notification/`, `finance/`, `referral/`, `dashboard/`, `ai/` |
| `notification/` | `shared/`, `platform/`, `identity/` | All other `apps/*` |
| `document/` | `shared/`, `platform/`, `identity/` | All other `apps/*` |
| `finance/` | `shared/`, `platform/`, `identity/`, `property/`, `payment/`, `document/` | `rent/`, `notification/`, `referral/`, `dashboard/`, `ai/` |
| `referral/` | `shared/`, `platform/`, `identity/` | All other `apps/*` |
| `ai/` | `shared/`, `platform/`, `identity/`, `property/`, `rent/`, `payment/`, `document/`, `notification/` | `subscription/`, `finance/`, `referral/`, `dashboard/` |
| `dashboard/` | `shared/`, `platform/`, `identity/`, `property/`, `payment/`, `finance/` | `rent/`, `notification/`, `document/`, `referral/`, `ai/` |

**Rules:**
1. No circular dependencies
2. No app imports from `rentsecure_be/`
3. No app imports from `management/`
4. All imports from `shared/` must be pure (no Django imports)
5. Import-linter enforced in CI with zero tolerance

### 3.10 Migration Strategy

**Decision: MODIFY — Simplify to 5 phases, reduce risk.**

| Phase | Duration | Goal | Breaking Changes | Risk |
|---|---|---|---|---|
| **Phase 0** | Week 1-2 | Foundation (move `type_compat`, create skeletons, add contract tests) | None | Low |
| **Phase 1** | Week 3-5 | Extract Identity | None (keep `core` as proxy) | Medium |
| **Phase 2** | Week 6-8 | Extract Subscription | None | Low |
| **Phase 3** | Week 9-11 | Extract Payment | None (keep old URLs as redirects) | Medium |
| **Phase 4** | Week 12-13 | Extract Dashboard & Referral | None | Low |
| **Phase 5** | Week 14-15 | Deprecate Core | **YES** — remove `core` from `INSTALLED_APPS` | High (major version) |
| **Phase 6** | Week 16-20 | Optimization (repositories, event bus, adapters) | None | Low |

**Key Principles:**
1. **No breaking changes until Phase 5** — maintain backward compatibility
2. **Old URLs remain valid** — use Django URL redirects during transition
3. **Old imports remain valid** — keep deprecated shims in `core/` during transition
4. **Feature flags for new code paths** — enable gradually
5. **Full test suite runs on every phase** — no exceptions

**Simplification from Original:**
- Removed `rent/` extraction from `property/` — too risky, defer to Stage 2
- Combined Dashboard and Referral into single phase
- Deferred full DDD structure (`domain/`, `application/`, `infrastructure/`, `interfaces/`) — use simplified structure
- Deferred CQRS and event bus — add only when needed

### 3.11 Performance

**Decision: KEEP — Optimize incrementally.**

| Optimization | Location | Timeline |
|---|---|---|
| Add `select_related`/`prefetch_related` | All views with N+1 queries | Phase 2 |
| Add caching for dashboard metrics | `dashboard/` | Phase 4 |
| Add caching for subscription plans | `subscription/` | Phase 2 |
| Async PDF generation | `document/` | Phase 3 |
| Query optimization in reporting | `dashboard/` | Phase 4 |
| Database indexes | All apps | Phase 6 |

**Anti-patterns to Avoid:**
- Do NOT add caching everywhere — cache only where profiling shows need
- Do NOT add repository pattern everywhere — use selectively
- Do NOT add event bus until microservice extraction is planned

### 3.12 Security

**Decision: KEEP — Strengthen existing practices.**

| Control | Current | Target |
|---|---|---|
| Webhook HMAC verification | In views | In adapters (`payment/adapters/`) |
| Payment SDK instantiation | In views | In adapters only |
| Bank details encryption | Plain text | Encrypt at rest (Phase 3) |
| OTP rate limiting | Basic | Add exponential backoff (Phase 1) |
| Idempotency keys | None | Add to all webhooks (Phase 3) |
| Audit logging | None | Add to payment operations (Phase 3) |
| Secrets management | `.env` | Use Django settings + env vars, never commit |

**Rationale:** Security is non-negotiable. All payment and webhook logic must be in adapters with proper verification. Bank details must be encrypted at rest. All webhooks must have idempotency keys.

### 3.13 Testing Strategy

**Final Testing Architecture:**

| Test Type | Scope | Owner | Location | Run Frequency |
|---|---|---|---|---|
| **Unit** | Services, models, utilities | App team | `apps/<context>/tests/unit/` | Every commit |
| **Integration** | View → Service → Model | App team | `apps/<context>/tests/integration/` | Every commit |
| **Contract** | App boundaries | Architecture team | `tests/contract/` | Every PR |
| **Architecture** | Import rules, circular deps | Architecture team | `tests/test_architecture_contract/` | Every commit |
| **Performance** | Query counts, response times | App team | `tests/test_query_count.py` | Nightly |
| **Security** | OWASP Top 10 | Security team | `tests/test_security/` | Every release |

**Rules:**
1. Every app must have `tests/unit/` and `tests/integration/`
2. Architecture contract tests run on every commit
3. Import-linter runs on every commit
4. Mutation testing runs on every PR (Sonar)
5. Performance tests run nightly
6. Security tests run on every release

### 3.14 CI/CD Architecture

**Final CI Pipeline:**

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Ruff
        run: ruff check .
      - name: MyPy
        run: mypy .
      - name: Import Linter
        run: import-linter check

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Unit + Integration
        run: pytest tests/ -v --tb=short
      - name: Architecture Contract
        run: pytest tests/test_architecture_contract/ -v
      - name: Mutation Testing
        run: sonar-scanner

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Security Scan
        run: bandit -r apps/ shared/ platform/

  performance:
    runs-on: ubuntu-latest
    schedule:
      - cron: '0 0 * * *'  # nightly
    steps:
      - uses: actions/checkout@v4
      - name: Query Count Tests
        run: pytest tests/test_query_count.py -v
```

**Tools:**
- **Lint:** Ruff (replaces Flake8/Isort)
- **Type Check:** MyPy (strict mode)
- **Import Linter:** import-linter (zero tolerance)
- **Test:** Pytest + Django
- **Mutation Testing:** SonarQube
- **Security:** Bandit + Safety
- **Performance:** Locust (load tests in `tests/load/`)

### 3.15 Long-Term Evolution

**5-Year Target (Year 5):**
- 11 bounded contexts in modular monolith
- Clean architecture within each context
- Import-linter enforced
- Full test coverage (90%+)
- Event bus for in-process communication
- Repository pattern for complex queries
- Ready for microservice extraction

**10-Year Target (Year 10):**
- Extract `payment/` and `notification/` as first microservices
- Event-driven architecture with outbox pattern
- API versioning (`/api/v1/`, `/api/v2/`)
- Multi-tenant support
- GraphQL API layer

**20-Year Target (Year 20):**
- Full microservice architecture
- Kubernetes deployment
- Service mesh
- Distributed tracing
- AI-powered features in `ai/` context

**Evolution Principles:**
1. **Modular monolith first** — extract microservices only when clear need
2. **Bounded contexts are stable** — do not change context boundaries without ADR
3. **Infrastructure adapters enable swapping** — cache, storage, search, queue
4. **Event bus enables decoupling** — add only when microservice extraction is planned
5. **Shared kernel is sacred** — never add business logic to `shared/`

---

## 4. Final Bounded Contexts

### 4.1 Context Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RentSecure Platform                         │
│                                                                     │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐                  │
│  │ Identity  │    │Subscription│   │  Property │                  │
│  │           │───▶│            │───▶│           │                  │
│  └───────────┘    └───────────┘    └─────┬─────┘                  │
│       ▲                  ▲                │                        │
│       │                  │                ▼                        │
│  ┌────┴────┐       ┌────┴────┐     ┌──────┴──────┐               │
│  │ Referral│       │ Payment │     │     Rent    │                │
│  │         │       │         │     │             │                │
│  └─────────┘       └─────────┘     └──────┬──────┘               │
│                                            │                       │
│  ┌───────────┐    ┌───────────┐           │                       │
│  │Notification│◀──│ Documents │◀──────────┘                       │
│  │            │    │           │                                   │
│  └───────────┘    └───────────┘                                   │
│       ▲                                                           │
│       │                                                           │
│  ┌────┴──────────┐                                               │
│  │  Dashboard    │                                               │
│  │               │                                               │
│  └───────────────┘                                               │
│                                                                   │
│  ┌──────────────┐                                                │
│  │   Finance    │                                                │
│  └──────────────┘                                                │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                      shared/                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    platform/                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Context Definitions

#### Identity
**Module:** `apps/identity/`
**Ownership:** Platform Team
**Maturity:** Stable

**Responsibilities:**
- User registration and authentication
- OTP generation and verification
- Password management
- User profile management
- Notification preference management
- JWT token management

**Owned Data:**
- `User` (AUTH_USER_MODEL)
- `UserProfile`
- `OTP`
- `NotificationPreference`

**Public APIs:**
| Interface | Description |
|---|---|
| `IdentityService.authenticate_with_otp(phone, code, group)` | Returns user and tokens |
| `IdentityService.change_password(user, old, new)` | Change password |
| `IdentityService.reset_password(user, new)` | Reset password |
| `IdentityService.get_profile(user_id)` | Get user profile |
| `OTPService.send_otp(phone, referral_code)` | Send OTP |
| `OTPService.verify(phone, code)` | Verify OTP |

**Dependencies:**
- Depends on: `shared/`, `platform/`
- Depended on by: ALL other contexts

---

#### Subscription
**Module:** `apps/subscription/`
**Ownership:** Platform Team
**Maturity:** Stable

**Responsibilities:**
- Subscription plan management
- User subscription lifecycle
- Add-on purchase and activation
- Usage limit enforcement
- Feature flag evaluation
- Quota enforcement

**Owned Data:**
- `SubscriptionPlan`
- `UserSubscription`
- `AddOnPurchase`
- `PlanFeatureLimit`
- `UsageLimit`

**Public APIs:**
| Interface | Description |
|---|---|
| `SubscriptionService.get_active_subscription(user_id)` | Current plan |
| `SubscriptionService.can_access_feature(user_id, feature)` | Feature gate |
| `SubscriptionService.record_usage(user_id, feature, amount)` | Meter usage |
| `FeatureEnforcer(user).can_create(feature_key)` | Check quota |
| `FeatureEnforcer(user).increment(feature_key)` | Increment usage |

**Dependencies:**
- Depends on: `identity/`, `shared/`, `platform/`
- Depended on by: `property/`, `rent/`, `payment/`, `notification/`, `finance/`, `dashboard/`

---

#### Property
**Module:** `apps/property/`
**Ownership:** Product Team
**Maturity:** Active Development

**Responsibilities:**
- Building and unit management
- Renter profile management
- Rent record creation and tracking
- Caretaker assignment
- Extra charge management
- Property image and document storage
- Occupancy tracking

**Owned Data:**
- `Building`
- `Unit`
- `UnitImage`
- `UnitDocument`
- `Renter`
- `RentRecord`
- `Caretaker`
- `ExtraCharge`
- `PropertyTaxRecord`

**Public APIs:**
| Interface | Description |
|---|---|
| `PropertyService.create_building(owner_id, data)` | New building |
| `PropertyService.add_unit(building_id, data)` | New unit |
| `PropertyService.assign_renter(unit_id, renter_id)` | Renter assignment |
| `RentRecordRepository.get_by_owner(owner_id)` | Owner's rent records |

**Dependencies:**
- Depends on: `identity/`, `subscription/`, `shared/`, `platform/`
- Depended on by: `rent/`, `payment/`, `finance/`, `dashboard/`, `notification/`

---

#### Rent
**Module:** `apps/rent/`
**Ownership:** Product Team
**Maturity:** Active Development

**Responsibilities:**
- Rent amount calculation
- Rent record lifecycle management
- Late fee calculation
- Payment request initiation
- Agreement draft creation
- Rent receipt tracking

**Owned Data:**
- `RentCycle`
- `LateFeePolicy`
- `PaymentRequest`
- `AgreementDraft`

**Public APIs:**
| Interface | Description |
|---|---|
| `RentService.calculate_rent(unit_id, month)` | Rent amount |
| `RentService.apply_late_fee(rent_id)` | Late fee calculation |
| `RentService.initiate_payment(rent_id, method)` | Create payment request |
| `RentService.generate_agreement(unit_id, template)` | Draft agreement |

**Dependencies:**
- Depends on: `property/`, `payment/`, `documents/`, `notification/`, `shared/`, `platform/`
- Depended on by: `finance/`, `dashboard/`

**Note:** `RentRecord` stays in `property/` during transition. `Rent` context extracts higher-level rent logic.

---

#### Payment
**Module:** `apps/payment/`
**Ownership:** Platform Team
**Maturity:** Stable (Manual UPI), Stage 2 (Gateway)

**Responsibilities:**
- Payment initiation and tracking
- Payment verification (manual and automated)
- Refund processing
- Payout management
- Idempotency enforcement
- Payment webhook handling
- Owner bank details management

**Owned Data:**
- `OwnerBankDetails`
- `Payment` (future)
- `PaymentTransaction` (future)
- `Refund` (future)

**Public APIs:**
| Interface | Description |
|---|---|
| `PaymentService.create_payment_link(rent_record)` | Create payment link |
| `PaymentService.process_payout(rent)` | Process payout |
| `PaymentService.register_beneficiary(bank_details)` | Register beneficiary |
| `BankDetailsService.validate_fields(data)` | Validate bank details |
| `WebhookService.verify(provider, payload, signature)` | Verify webhook |
| `WebhookService.handle_payout(payload)` | Handle payout webhook |

**Adapters:**
- `ManualPaymentAdapter` (Year 1, active)
- `RazorpayAdapter` (Stage 2, disabled)
- `CashfreeAdapter` (Stage 2, disabled)

**Dependencies:**
- Depends on: `identity/`, `property/`, `notification/`, `shared/`, `platform/`
- Depended on by: `rent/`, `finance/`, `dashboard/`

---

#### Notification
**Module:** `apps/notification/`
**Ownership:** Platform Team
**Maturity:** Stable

**Responsibilities:**
- Notification preference management
- Multi-channel notification dispatch
- Template rendering per channel
- Delivery tracking
- Notification history

**Owned Data:**
- `Notification`
- `NotificationPreference`
- `NotificationTemplate`
- `NotificationChannel`

**Adapters:**
- `EmailAdapter` (active)
- `FCMAdapter` (active)
- `InAppAdapter` (active)
- `WhatsAppAdapter` (disabled, Stage 2)
- `SMSAdapter` (disabled, Stage 2)

**Public APIs:**
| Interface | Description |
|---|---|
| `NotificationService.send(user_id, event, context)` | Send notification |
| `NotificationService.get_preferences(user_id)` | Get preferences |
| `NotificationService.update_preferences(user_id, prefs)` | Update preferences |

**Dependencies:**
- Depends on: `identity/`, `shared/`, `platform/`
- Depended on by: ALL contexts

---

#### Documents
**Module:** `apps/documents/`
**Ownership:** Platform Team
**Maturity:** Stable

**Responsibilities:**
- PDF generation from templates
- Document storage and retrieval
- Template management
- Digital signature integration (future)

**Owned Data:**
- `Document`
- `DocumentTemplate`
- `DocumentStorage`

**Public APIs:**
| Interface | Description |
|---|---|
| `DocumentService.generate(template_id, context)` | Generate PDF |
| `DocumentService.store(document, owner_id)` | Store document |
| `DocumentService.get(user_id, document_id)` | Retrieve document |

**Dependencies:**
- Depends on: `identity/`, `shared/`, `platform/`
- Depended on by: `rent/`, `payment/`, `property/`, `finance/`

---

#### Finance
**Module:** `apps/finance/`
**Ownership:** Finance Team
**Maturity:** Stable

**Responsibilities:**
- Tax record management
- CA profile management
- Tax filing status tracking
- Financial report generation
- GST compliance (future)
- Expense tracking

**Owned Data:**
- `TaxRecord`
- `CAProfile`
- `TaxFiling`
- `ExpenseRecord`
- `FinancialReport`

**Public APIs:**
| Interface | Description |
|---|---|
| `FinanceService.create_tax_record(owner_id, data)` | New tax record |
| `FinanceService.assign_ca(owner_id, ca_id)` | CA assignment |
| `FinanceService.generate_report(owner_id, period)` | Financial report |
| `FinanceService.get_compliance_status(owner_id)` | Compliance check |

**Dependencies:**
- Depends on: `identity/`, `property/`, `payment/`, `document/`, `shared/`, `platform/`
- Depended on by: `dashboard/`

---

#### Referral
**Module:** `apps/referral/`
**Ownership:** Growth Team
**Maturity:** Stable

**Responsibilities:**
- Referral code generation and validation
- Bonus tracking
- Reward distribution
- Referral analytics

**Owned Data:**
- `ReferralCode`
- `ReferralBonus`
- `ReferralReward`

**Public APIs:**
| Interface | Description |
|---|---|
| `ReferralService.process_referral(otp, user)` | Process referral during signup |
| `ReferralService.validate_code(code)` | Validate code |
| `ReferralService.get_bonuses(user_id)` | Bonus history |

**Dependencies:**
- Depends on: `identity/`, `shared/`, `platform/`
- Depended on by: `identity/` (during signup)

---

#### AI
**Module:** `apps/ai/`
**Ownership:** Platform Team
**Maturity:** Experimental

**Responsibilities:**
- Chatbot intent processing
- AI-powered document analysis
- Smart rent suggestions
- Anomaly detection
- Prompt management
- AI governance and safety

**Owned Data:**
- `ChatSession`
- `ChatMessage`
- `AIPrompt`
- `AIAnalysisResult`

**Public APIs:**
| Interface | Description |
|---|---|
| `AIService.chat(user_id, message, session_id)` | Process chat message |
| `AIService.analyze_document(document_id)` | AI document analysis |
| `AIService.suggest_rent(unit_id, comparables)` | Rent suggestion |
| `AIService.detect_anomaly(payment_id)` | Fraud detection |

**Dependencies:**
- Depends on: `identity/`, `property/`, `rent/`, `payment/`, `document/`, `notification/`, `shared/`, `platform/`
- Depended on by: `dashboard/`

---

#### Dashboard
**Module:** `apps/dashboard/`
**Ownership:** Platform Team
**Maturity:** Stable

**Responsibilities:**
- Owner rent inflow summary
- Owner rent records listing
- Excel/PDF report generation
- Dashboard metrics aggregation
- Data export

**Owned Data:**
- `DashboardMetric` (cached/computed)
- `ReportJob`

**Public APIs:**
| Interface | Description |
|---|---|
| `OwnerReportingService.get_rent_inflow_summary(owner)` | Owner metrics |
| `OwnerReportingService.get_owner_rent_records(owner)` | Rent records |
| `ExportService.generate_rent_excel(owner)` | Excel export |

**Dependencies:**
- Depends on: `identity/`, `property/`, `payment/`, `finance/`, `shared/`, `platform/`
- Depended on by: None (leaf context)

---

## 5. Final Dependency Rules

### 5.1 Allowed Import Matrix

| Source | shared | platform | identity | subscription | property | rent | payment | notification | document | finance | referral | ai | dashboard |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **shared** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **platform** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **config** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **identity** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **subscription** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **property** | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **rent** | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **payment** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **notification** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **document** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **finance** | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| **referral** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **ai** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| **dashboard** | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |

### 5.2 Forbidden Patterns

1. **No app imports from `rentsecure_be/`** — all infrastructure lives in `platform/` or `shared/`
2. **No app imports from `management/`** — management commands belong in app `management/` directories
3. **No circular dependencies** — enforced by import-linter
4. **No direct model imports across contexts** — use repositories or service interfaces
5. **No business logic in views** — views delegate to services
6. **No SDK instantiation in views** — SDKs live in adapters only

---

## 6. Final Folder Structure

### 6.1 Project Root

```
rentsecure_be/
├── apps/                                    # Bounded contexts
│   ├── identity/
│   ├── subscription/
│   ├── property/
│   ├── payment/
│   ├── notification/
│   ├── document/
│   ├── finance/
│   ├── referral/
│   ├── ai/
│   └── dashboard/
├── shared/                                  # Shared kernel
├── platform/                                # Infrastructure adapters
├── config/                                  # Django configuration
├── tests/                                   # Cross-cutting tests
├── docs/
├── scripts/
├── tools/
├── manage.py
├── pyproject.toml
├── pytest.ini
├── mypy.ini
├── ruff.toml
├── import-linter.ini
├── .env.example
└── README.md
```

### 6.2 App Internal Structure (Simplified)

```
apps/<context>/
├── __init__.py
├── apps.py
├── models.py                    # Django ORM models
├── services.py                  # Application services (or services/)
├── views.py                     # API views (or views/)
├── serializers.py               # DRF serializers (or serializers/)
├── urls.py
├── admin.py
├── signals.py
├── migrations/
│   ├── __init__.py
│   └── ...
└── tests/
    ├── __init__.py
    ├── unit/
    │   └── test_*.py
    ├── integration/
    │   └── test_*.py
    └── contract/
        └── test_*_contract.py
```

**When to add extra layers:**
- `repositories.py` — only if complex queries are shared across 3+ services
- `adapters/` — only for payment and notification (external SDKs)
- `ports/` — only for payment (gateway interface)

**When NOT to add extra layers:**
- `domain/` — defer until microservice extraction
- `application/` — defer until team size > 20
- `infrastructure/` — defer until team size > 20
- `interfaces/` — defer until team size > 20

**Rationale:** For a team of 5-20 developers, the simplified structure reduces file count and cognitive overhead while maintaining clean separation of concerns. Adopt full DDD structure only when teams grow or microservice extraction begins.

---

## 7. Final Django App Layout

### 7.1 apps/identity/

**Models:**
- `User` (AUTH_USER_MODEL)
- `UserProfile`
- `OTP`
- `NotificationPreference`

**Services:**
- `identity_service.py` — authenticate, change_password, reset_password, get_profile
- `otp_service.py` — send_otp, verify, invalidate_previous
- `password_service.py` — change_password, reset_password

**Views:**
- `auth_views.py` — SendOTP, OwnerVerifyOTP, RenterVerifyOTP
- `password_views.py` — ChangePasswordView, ResetPasswordView

**Serializers:**
- `user_serializer.py` — UserSerializer
- `notification_preference_serializer.py` — NotificationPreferenceSerializer

**URLs:**
- `auth/send-otp/`
- `auth/owner/verify-otp/`
- `auth/renter/verify-otp/`
- `api/token/refresh/`
- `change-password/`
- `reset-password/`
- `user-profile/`
- `notification-preferences/`

**Signals:**
- `post_save` User → create UserProfile, NotificationPreference

---

### 7.2 apps/subscription/

**Models:**
- `SubscriptionPlan`
- `UserSubscription`
- `AddOnPurchase`
- `PlanFeatureLimit`
- `UsageLimit`

**Services:**
- `subscription_service.py` — get_active_subscription, can_access_feature, record_usage
- `feature_enforcer.py` — can_create, increment, decrement, get_active_limit

**Views:**
- `subscription_plan_viewset.py` — SubscriptionPlanViewSet
- `user_subscription_viewset.py` — UserSubscriptionViewSet
- `addon_purchase_viewset.py` — AddOnPurchaseViewSet
- `usage_limit_viewset.py` — UsageLimitViewSet

**Serializers:**
- `subscription_plan_serializer.py`
- `user_subscription_serializer.py`
- `addon_purchase_serializer.py`
- `usage_limit_serializer.py`

**URLs:**
- `subscription-plans/`
- `user-subscriptions/`
- `addon-purchases/`
- `usage-limits/`

**Signals:**
- `post_save` User → create default SubscriptionPlan, PlanFeatureLimits, UserSubscription

---

### 7.3 apps/property/ (Keep Existing Structure)

**Models:**
- `Building`
- `Unit`
- `UnitImage`
- `UnitDocument`
- `Renter`
- `RentRecord`
- `Caretaker`
- `ExtraCharge`
- `PropertyTaxRecord`
- `RentAgreementDraft`

**Services:**
- Keep existing services, remove subscription-related logic

**Views:**
- Keep existing views, remove reporting views (move to `dashboard/`)

**Serializers:**
- Keep existing serializers

**URLs:**
- Keep existing URLs, remove reporting URLs (move to `dashboard/`)

**Changes:**
- `properties/feature_enforcer.py` → moved to `subscription/`
- `properties/utils/utils.py` — remove subscription imports
- `properties/views/rent_record_views.py` — remove reporting views

---

### 7.4 apps/payment/ (Extend Existing)

**Models (NEW):**
- `OwnerBankDetails`

**Adapters:**
- `manual.py` — ManualPaymentAdapter (Year 1)
- `cashfree.py` — CashfreeAdapter (Stage 2, disabled)
- `razorpay.py` — RazorpayAdapter (Stage 2, disabled)
- `cashfree_client.py` — Cashfree API client (moved from `rentsecure_be/utils/`)

**Services:**
- `payment_service.py` — extend existing with webhook methods
- `bank_details_service.py` — validate_fields, register_beneficiary, save_bank_details
- `webhook_service.py` — verify, handle_payout, handle_payment

**Views:**
- `webhooks.py` — cashfree_payout_webhook, razorpay_webhook
- `bank_details_views.py` — update_owner_bank_details
- `payment_views.py` — create_rent_payment

**Serializers:**
- `bank_details_serializer.py`

**URLs:**
- `webhook/cashfree/payout/`
- `webhook/razorpay/payment/`
- `api/owner/update-bank-details/`
- `api/rent/payment/`

**Ports:**
- `payment_gateway.py` — PaymentGateway interface

---

### 7.5 apps/notification/ (Keep Existing, Add Model)

**Models (ADD):**
- `NotificationPreference` (moved from `core/`)

**Keep Existing:**
- Adapters: email, fcm, inapp, whatsapp (disabled), sms (disabled)
- Services: notification_service, rent_notify_service, etc.
- Views: keep existing

**Changes:**
- Add `NotificationPreference` model
- Update signal handler location

---

### 7.6 apps/referral/ (Extend Existing)

**Models:**
- Keep existing `Referral` model

**Services (ADD):**
- `referral_service.py` — process_referral (moved from `core/`)

**Changes:**
- Update `identity/signals.py` to import from `referral/`

---

### 7.7 apps/dashboard/ (NEW)

**Models:**
- `DashboardMetric` (cached/computed)
- `ReportJob`

**Services:**
- `owner_reporting_service.py` — get_rent_inflow_summary, get_owner_rent_records

**Views:**
- `owner_reporting_views.py` — rent_inflow_summary, owner_rent_records
- `export_views.py` — download_rent_excel

**URLs:**
- `owner/rent-inflow-summary/`
- `owner/rent-records/`
- `owner/rent-report.xlsx`

**Utils:**
- `generate_owner_rent_report` (moved from `rentsecure_be/utils/`)

---

### 7.8 Keep Existing Apps

**apps/finance/** — Keep as-is, no changes
**apps/document/** — Keep as-is, no changes
**apps/ai/** — Keep `smartbot/` for now, consolidate with `ai_assistant/` in Phase 6
**apps/rent/** — Defer creation, keep in `property/` for now

---

## 8. Final Shared Rules

### 8.1 Allowed in `shared/`

| File | Contents | Owner |
|---|---|---|
| `exceptions.py` | Base exception classes | Architecture team |
| `enums.py` | Shared enumerations | App teams (via PR) |
| `types.py` | Shared type aliases | App teams (via PR) |
| `type_compat.py` | Python 3.12 compatibility shims | Architecture team |
| `utils.py` | Generic utilities (date, string, etc.) | App teams (via PR) |
| `validators.py` | Shared validation logic | App teams (via PR) |
| `services/base.py` | BaseService, ServiceResult | Architecture team |
| `domain_events.py` | Domain event base classes | Architecture team |
| `interfaces.py` | Abstract interface definitions | Architecture team |
| `constants.py` | App-wide constants | Architecture team |

### 8.2 Forbidden in `shared/`

- Any Django app imports
- Any model definitions
- Any service implementations
- Any business logic
- Any domain-specific code
- Any imports from `apps/`, `platform/`, or `config/`

### 8.3 Governance

- All additions to `shared/` require Architecture team review
- `shared/` changes require import-linter pass
- No backward-incompatible changes to `shared/` without deprecation period

---

## 9. Final Platform Rules

### 9.1 Allowed in `platform/`

| Component | Purpose | Interface | Implementations |
|---|---|---|---|
| `cache/` | Caching abstraction | `CachePort` | `LocMemCache`, `RedisCache` |
| `storage/` | File storage abstraction | `StoragePort` | `LocalStorage`, `S3Storage` |
| `search/` | Search abstraction | `SearchPort` | `PostgresSearch`, `OpenSearch` |
| `events/` | Event bus | `EventBus` | In-process bus |

### 9.2 Forbidden in `platform/`

- Business logic
- Domain models
- App-specific code
- Communication channels (email, SMS, WhatsApp, voice) — these belong in `notification/adapters/`
- Queue/celery — use management commands + cron (Year 1)
- DI container — unnecessary for Django

### 9.3 Usage Rules

1. All apps can import from `platform/`
2. `platform/` cannot import from any `apps/*`
3. All platform components have clear interfaces
4. Implementations are swappable via settings

---

## 10. Final Event Strategy

### 10.1 Phase 1-5: Django Signals

**Use Django signals for in-process events:**
- `post_save` User → create profile, preferences, subscription
- `post_save` RentRecord → notify tenant, update dashboard
- `post_save` Payment → send notification, update finance

**Advantages:**
- Native Django support
- No additional infrastructure
- Well-understood by team

**Disadvantages:**
- Tightly coupled
- Hard to test
- No event history

### 10.2 Phase 6: Event Bus

**Add in-process event bus:**
```
platform/events/
├── bus.py          # EventBus singleton
├── handlers.py     # Handler registry
└── middleware.py   # Event middleware
```

**Usage:**
```python
event_bus.publish(UserCreated(user))
handler = event_bus.subscribe(UserCreated, create_subscription)
```

**Advantages:**
- Decoupled communication
- Testable
- Event history

**Disadvantages:**
- Additional complexity
- Learning curve

### 10.3 Stage 2+: Outbox Pattern

**Add only when extracting microservices:**
- Outbox table for reliable event publishing
- Event dispatcher process
- Dead letter queue

**Rationale:** Outbox pattern is only needed for distributed systems. For a modular monolith, Django signals or event bus are sufficient.

---

## 11. Final Repository Rules

### 11.1 When to Use Repository

| Use Repository When | Example |
|---|---|
| Complex queries spanning 3+ tables | `OwnerReportingRepository.get_rent_inflow_summary(owner)` |
| Queries used by 3+ services | `RentRecordRepository.get_by_owner(owner_id)` |
| Read models differ from write models | `DashboardMetricRepository` (cached/computed) |
| Query logic is non-trivial | `SubscriptionRepository.get_active_with_limits(user_id)` |

### 11.2 When NOT to Use Repository

| Skip Repository When | Example |
|---|---|
| Simple CRUD operations | `User.objects.get(id=...)` |
| Single-model queries | `SubscriptionPlan.objects.filter(is_active=True)` |
| Query used by 1 view/service | `OTP.objects.filter(phone_number=phone).first()` |
| Straightforward ORM query | `RentRecord.objects.filter(unit__owner=user)` |

### 11.3 Repository Structure

```python
# apps/<context>/repositories.py
class OwnerReportingRepository:
    def get_rent_inflow_summary(self, owner: User) -> dict:
        return RentRecord.objects.filter(...).aggregate(...)

    def get_owner_rent_records(self, owner: User) -> list[dict]:
        return RentRecord.objects.filter(...).select_related(...).all()
```

**Rules:**
1. Repository returns domain objects or dicts, not Django model instances
2. Repository methods are read-only (use services for writes)
3. Repository does not contain business logic
4. Repository is injected into services (dependency injection via constructor)

---

## 12. Final Import Rules

### 12.1 Import Hierarchy

```
shared/        ← leaf, no app imports
platform/      ← can import shared/
config/        ← can import shared/, platform/
apps/*/        ← can import shared/, platform/, and allowed apps per matrix
```

### 12.2 Import-Linter Configuration

```ini
[importlinter]
root_packages =
    apps
    shared
    platform
    config

[importlinter:apps.identity]
type = layers
layers =
    apps.identity
    apps.subscription
    apps.property
    apps.payment
    apps.notification
    apps.document
    apps.finance
    apps.referral
    apps.ai
    apps.dashboard
    platform
    shared

# ... similar for each app

[settings]
exclude =
    .venv
    venv
    build
    dist
    __pycache__
    migrations
    .pytest_cache
    .github
    .kilo
```

### 12.3 Forbidden Imports

1. **No `from rentsecure_be.X import Y`** — all infrastructure lives in `platform/` or `shared/`
2. **No `from management.commands.X import Y`** — management commands belong in app `management/` directories
3. **No `from core.X import Y`** after Phase 5 — `core` is removed
4. **No circular imports** — use dependency injection or string references

---

## 13. Final Migration Strategy

### 13.1 Phase 0: Foundation (Week 1-2) — NO BREAKING CHANGES

**Goal:** Prepare for migration without touching production code.

**Tasks:**
1. Move `type_compat.py` from `rentsecure_be/` to `shared/`
2. Update all 20+ imports across 6 apps
3. Keep `rentsecure_be/type_compat.py` as deprecated shim (re-export from `shared/`)
4. Create `apps/identity/`, `apps/subscription/`, `apps/dashboard/` skeletons
5. Add architecture contract tests to CI
6. Clean up dead code (`ai_assistant/`, `dashboard/`, `properties/models/subscription_models.py`)

**Risk:** LOW
**Rollback:** Trivial — no production code changed
**Success Criteria:** All tests pass, import-linter passes, no production code changes

---

### 13.2 Phase 1: Extract Identity (Week 3-5) — NO BREAKING CHANGES

**Goal:** Move identity concerns out of `core` without breaking existing functionality.

**Tasks:**
1. Create `apps/identity/models.py` with `User`, `UserProfile`, `OTP`, `NotificationPreference`
2. Create migration: `python manage.py makemigrations identity`
3. Create data migration to copy `core_user` → `identity_user`
4. Create `apps/identity/services/` with auth, otp, password services
5. Create `apps/identity/views/` with auth and password views
6. Create `apps/identity/serializers.py`
7. Create `apps/identity/urls.py`
8. Update `rentsecure_be/urls.py` to include `identity/urls.py` BEFORE `core/urls.py`
9. Update all cross-app imports (`properties/`, `finance/`, `documents/` import `User` from `identity/`)
10. Update `core/views.py` to delegate to `identity/` URLs (deprecation warnings)
11. Update `core/signals.py` to import from `identity/`

**Critical:** Keep `core/models.py` as proxy models during transition. Do NOT update `AUTH_USER_MODEL` yet.

**Risk:** MEDIUM
**Rollback:** Keep `core` models, revert URL includes
**Success Criteria:** All identity endpoints work via both `core/` and `identity/` URLs, all tests pass

---

### 13.3 Phase 2: Extract Subscription (Week 6-8) — NO BREAKING CHANGES

**Goal:** Move subscription concerns out of `core`.

**Tasks:**
1. Create `apps/subscription/models.py` with subscription models
2. Create migration
3. Create `apps/subscription/services/` with subscription and feature enforcer services
4. Move `properties/feature_enforcer.py` → `apps/subscription/services/feature_enforcer.py`
5. Update all 10+ imports in `properties/` to use `subscription/`
6. Create `apps/subscription/views/` with ViewSets
7. Create `apps/subscription/urls.py`
8. Update `core/views.py` to delegate to `subscription/` URLs
9. Move signal handler from `core/signals.py` → `apps/subscription/signals.py`

**Risk:** LOW
**Rollback:** Keep `core` models as fallback
**Success Criteria:** All subscription endpoints work via both `core/` and `subscription/` URLs, all tests pass

---

### 13.4 Phase 3: Extract Payment (Week 9-11) — NO BREAKING CHANGES

**Goal:** Move payment and bank details out of `core`.

**Tasks:**
1. Add `OwnerBankDetails` model to `apps/payment/models.py`
2. Create migration
3. Move webhook handlers from `core/views.py` → `apps/payment/views/webhooks.py`
4. Move `update_owner_bank_details` → `apps/payment/views/bank_details_views.py`
5. Move `BankDetailsService` from `core/services/` → `apps/payment/services/`
6. Move Cashfree adapter logic from `rentsecure_be/services/cashfree_service.py` → `apps/payment/adapters/`
7. Move `rentsecure_be/utils/cashfree_payout.py` → `apps/payment/adapters/cashfree_client.py`
8. Update `core/views.py` to delegate to `payment/` URLs (keep old URLs as redirects)
9. Clean up `rentsecure_be/` (remove moved files, keep deprecated shims)

**Critical:** Keep old webhook URLs working via Django redirects for 1 release cycle.

**Risk:** MEDIUM
**Rollback:** Keep `core` views, maintain old URLs
**Success Criteria:** All payment endpoints work via both old and new URLs, webhook signatures verified, all tests pass

---

### 13.5 Phase 4: Extract Dashboard & Referral (Week 12-13) — NO BREAKING CHANGES

**Goal:** Move reporting and referral out of `core`.

**Tasks:**
1. Create `apps/dashboard/models.py` with `DashboardMetric`, `ReportJob`
2. Create migration
3. Move `OwnerReportingService` → `apps/dashboard/services/`
4. Move reporting views → `apps/dashboard/views/`
5. Move `generate_owner_rent_report` from `rentsecure_be/utils/` → `apps/dashboard/utils/`
6. Update `core/views.py` to delegate to `dashboard/` URLs
7. Add `ReferralService` to `apps/referral/services/`
8. Update `identity/signals.py` to import from `referral/`
9. Move `NotificationPreference` model to `apps/notification/models.py`
10. Update `identity/signals.py` to create `NotificationPreference` via notification service

**Risk:** LOW
**Rollback:** Keep `core` views as fallback
**Success Criteria:** All reporting and referral endpoints work, all tests pass

---

### 13.6 Phase 5: Deprecate Core (Week 14-15) — BREAKING CHANGES

**Goal:** Remove `core` app entirely.

**Tasks:**
1. Remove all models from `core/models.py`
2. Remove all views from `core/views.py`
3. Remove all services from `core/services/`
4. Remove `core/serializers.py`, `core/urls.py`, `core/signals.py`
5. Update `AUTH_USER_MODEL = "identity.User"` in settings
6. Remove `core` from `INSTALLED_APPS`
7. Delete `core/` directory
8. Remove deprecated shims from `rentsecure_be/`
9. Update all documentation

**Breaking Changes:**
- `AUTH_USER_MODEL` change (if not done in Phase 1)
- `core` URLs no longer available
- Any external references to `core` models break

**Risk:** HIGH
**Mitigation:**
- Release as major version (v2.0)
- Provide migration guide
- Keep `core` in LTS branch for 6 months
- Full rollback plan tested in staging

**Success Criteria:** All tests pass, no references to `core` remain, application starts without `core` in `INSTALLED_APPS`

---

### 13.7 Phase 6: Optimization (Week 16-20) — NO BREAKING CHANGES

**Goal:** Add missing infrastructure and optimize.

**Tasks:**
1. Add repository pattern for complex queries
2. Add event bus (`platform/events/`)
3. Add port/adapter interfaces for all external integrations
4. Optimize queries — add `select_related`/`prefetch_related`
5. Add caching for dashboard metrics
6. Add architecture contract tests to CI
7. Document bounded context APIs
8. Consolidate `ai_assistant/` into `smartbot/` or `ai/`

**Risk:** LOW
**Rollback:** N/A — additive changes
**Success Criteria:** All tests pass, performance benchmarks met, architecture contract tests pass

---

## 14. Final Coding Standards

### 14.1 Code Style

- **Formatter:** Ruff (replaces Black/Isort)
- **Linter:** Ruff (replaces Flake8/Pylint)
- **Type Checker:** MyPy (strict mode)
- **Docstrings:** Google style for public APIs
- **Line Length:** 100 characters (Ruff default)

### 14.2 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Models | PascalCase, singular | `User`, `SubscriptionPlan` |
| Services | PascalCase + Service suffix | `IdentityService`, `PaymentService` |
| Repositories | PascalCase + Repository suffix | `OwnerReportingRepository` |
| Views | PascalCase + View/ViewSet suffix | `SendOTP`, `RentRecordViewSet` |
| Serializers | PascalCase + Serializer suffix | `UserSerializer` |
| URLs | kebab-case, plural | `subscription-plans/`, `user-subscriptions/` |
| Files | snake_case | `user_serializer.py`, `payment_service.py` |

### 14.3 Django Best Practices

1. **Never call third-party APIs from views** — use adapters
2. **Never put business logic in views** — delegate to services
3. **Never put business logic in models** — use services
4. **Always use `select_related`/`prefetch_related`** — avoid N+1 queries
5. **Always use `AUTH_USER_MODEL`** — never use `User` directly
6. **Always use string references for FKs** — `"identity.User"` instead of `User`
7. **Always use migrations** — never modify database directly
8. **Never commit secrets** — use environment variables
9. **Always use HTTPS in production** — `SECURE_SSL_REDIRECT = True`
10. **Always verify webhooks** — HMAC signature verification

---

## 15. Final Testing Strategy

### 15.1 Test Pyramid

```
        /\
       /  \      E2E (Playwright)
      /____\
     /      \    Integration (pytest + Django test client)
    /________\
   /          \  Unit (pytest + mocks)
  /____________\
```

### 15.2 Test Ownership

| Test Type | Written By | Run Frequency | Blocking |
|---|---|---|---|
| Unit | App team | Every commit | Yes |
| Integration | App team | Every commit | Yes |
| Contract | Architecture team | Every PR | Yes |
| Architecture | Architecture team | Every commit | Yes |
| Performance | App team | Nightly | No |
| Security | Security team | Every release | Yes |

### 15.3 Test Requirements

1. **Every public service method must have unit tests**
2. **Every view must have integration tests**
3. **Every app boundary must have contract tests**
4. **Every migration must have migration tests**
5. **Every webhook must have security tests**
6. **Every adapter must have interface tests**

### 15.4 Test Structure

```
tests/
├── conftest.py                    # Global fixtures
├── factories.py                   # Test factories (factory_boy)
├── unit/
│   └── test_*.py
├── integration/
│   └── test_*.py
├── contract/
│   └── test_*_contract.py
├── architecture/
│   ├── test_dependencies.py       # Import-linter
│   ├── test_layer_rules.py        # Layer compliance
│   └── test_circular_deps.py      # Circular dependency detection
├── performance/
│   └── test_query_count.py
└── load/
    └── locustfile.py
```

---

## 16. Final CI/CD Strategy

### 16.1 CI Pipeline

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install ruff mypy import-linter
      - name: Ruff
        run: ruff check .
      - name: MyPy
        run: mypy .
      - name: Import Linter
        run: import-linter check

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run migrations
        run: python manage.py migrate
      - name: Unit + Integration Tests
        run: pytest tests/ -v --tb=short --cov=apps --cov=shared --cov=platform
      - name: Architecture Contract Tests
        run: pytest tests/architecture/ -v
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install bandit safety
      - name: Bandit
        run: bandit -r apps/ shared/ platform/
      - name: Safety
        run: safety check

  mutation:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - name: SonarCloud Scan
        uses: SonarSource/sonarcloud-github-action@master
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

### 16.2 Quality Gates

| Gate | Tool | Threshold | Blocking |
|---|---|---|---|
| Lint | Ruff | 0 errors | Yes |
| Type Check | MyPy | 0 errors | Yes |
| Import Rules | import-linter | 0 violations | Yes |
| Unit Tests | Pytest | 90% coverage | Yes |
| Integration Tests | Pytest | 80% coverage | Yes |
| Architecture Tests | Pytest | 0 failures | Yes |
| Security | Bandit | 0 high/medium | Yes |
| Mutation | Sonar | 80% mutation score | No |
| Performance | Locust | < 200ms p95 | No |

---

## 17. Final Security Standards

### 17.1 Authentication & Authorization

1. **JWT tokens** — use `rest_framework_simplejwt`
2. **Access token lifetime:** 5 minutes
3. **Refresh token lifetime:** 35 days
4. **Always use `IsAuthenticated`** — never `AllowAny` for sensitive endpoints
5. **Use permission classes** — `IsOwner`, `IsRenter`, etc.

### 17.2 OTP Security

1. **Rate limiting** — 3 OTPs per phone per 10 minutes
2. **OTP lifetime** — 5 minutes
3. **OTP format** — 6 digits, cryptographically random
4. **Never log OTPs** — except in DEBUG mode with clear warning
5. **Invalidate previous OTPs** — on new OTP request

### 17.3 Payment Security

1. **Webhook verification** — HMAC signature in adapter, never in view
2. **Idempotency keys** — all webhooks must support replay
3. **Bank details encryption** — encrypt at rest using Django cryptography
4. **Never log sensitive data** — bank account numbers, IFSC codes
5. **Audit logging** — all payment operations logged
6. **Use HTTPS only** — `SECURE_SSL_REDIRECT = True` in production

### 17.4 Secrets Management

1. **Never commit secrets** — use `.env` (gitignored)
2. **Use Django `config()`** — via `python-decouple`
3. **Rotate secrets regularly** — implement secret rotation policy
4. **Different secrets per environment** — dev, staging, production

### 17.5 Input Validation

1. **Always validate in serializers** — never trust client input
2. **Use Django validators** — for email, phone, etc.
3. **Sanitize user input** — prevent XSS, SQL injection
4. **Limit request size** — prevent DoS

---

## 18. Final Performance Standards

### 18.1 Query Optimization

| Rule | Implementation |
|---|---|
| N+1 prevention | Always use `select_related` for FKs, `prefetch_related` for M2M |
| Query count limit | Max 10 queries per view (enforced in tests) |
| Database indexes | Add indexes on frequently queried fields |
| Query optimization | Use `only()`/`defer()` for large models |

### 18.2 Caching Strategy

| Data | Cache Duration | Invalidation |
|---|---|---|
| Subscription plans | 1 hour | On plan update |
| Feature limits | 1 hour | On subscription change |
| Dashboard metrics | 5 minutes | On data change |
| Notification preferences | 15 minutes | On preference update |

### 18.3 Async Operations

| Operation | Approach |
|---|---|
| PDF generation | Sync with timeout (Year 1) |
| Email sending | Sync via adapter (Year 1) |
| Push notifications | Sync via adapter (Year 1) |
| Report generation | Sync with timeout (Year 1) |

**Note:** Async via Celery is Stage 2. For Year 1, use sync operations with timeouts and retries.

---

## 19. Future Evolution Roadmap

### Year 1: Modular Monolith

**Goal:** Clean architecture within monolith

- 11 bounded contexts in `apps/`
- Clean architecture layers (simplified)
- Import-linter enforced
- Full test coverage (90%+)
- Zero circular dependencies
- Payment adapters with proper interfaces

### Year 2-3: Optimize & Scale

**Goal:** Performance and scalability

- Repository pattern for complex queries
- Event bus for in-process communication
- Caching strategy implemented
- Query optimization complete
- Dashboard performance optimized

### Year 3-5: Prepare for Microservices

**Goal:** Enable microservice extraction

- Full DDD structure (`domain/`, `application/`, `infrastructure/`, `interfaces/`)
- Port/adapter interfaces for all external integrations
- Outbox pattern implemented
- API versioning (`/api/v1/`, `/api/v2/`)
- Multi-tenant support

### Year 5-10: Microservice Extraction

**Goal:** Extract first microservices

- Extract `payment/` as first microservice
- Extract `notification/` as second microservice
- Event-driven architecture
- Service mesh
- Distributed tracing

### Year 10-20: Full Microservices

**Goal:** Complete microservice architecture

- All contexts as independent services
- Kubernetes deployment
- AI-powered features in `ai/` context
- Multi-region deployment
- 99.99% uptime

---

## 20. Risks and Mitigations

### 20.1 High Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| `AUTH_USER_MODEL` migration failure | Medium | High | Test extensively in staging, keep `core.User` as proxy, rollback plan |
| Webhook URL changes break providers | Medium | High | Keep old URLs as redirects for 1 release, update provider dashboards |
| Circular dependencies during migration | High | Medium | Use import-linter in CI, fix immediately, refactor in small steps |
| `core` removal breaks external code | Medium | High | Release as major version, provide migration guide, keep LTS branch |

### 20.2 Medium Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| FeatureEnforcer imports break `properties/` | High | Medium | Update all imports in single PR, run full test suite |
| 20+ `type_compat` imports break | High | Low | Batch update in single PR, keep deprecated shim |
| Migration takes longer than estimated | Medium | Medium | Buffer 20% time, prioritize phases, defer non-critical work |
| Team resistance to new structure | Medium | Medium | Training, documentation, gradual adoption, lead by example |

### 20.3 Low Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Dead code removal breaks something | Low | Low | Search for imports before deletion, keep git history |
| Test coverage gaps | Medium | Low | Add tests during migration, enforce 90% coverage in CI |

---

## 21. Architecture Decision Records (ADR)

### ADR-001: Modular Monolith Architecture

**Status:** Accepted
**Date:** 2026-07-19
**Context:** RentSecure is a single application with multiple domains. We need to choose between monolithic and microservice architecture.
**Decision:** Use modular monolith with clear bounded contexts.
**Rationale:**
- Team size (5-20 developers) does not justify microservices
- Single deployment is simpler to operate
- Bounded contexts enable future microservice extraction
- Lower operational complexity
**Consequences:**
- Clear boundaries required
- Import-linter enforcement required
- Future microservice extraction enabled

### ADR-002: Simplified Clean Architecture

**Status:** Accepted
**Date:** 2026-07-19
**Context:** Full DDD structure (`domain/`, `application/`, `infrastructure/`, `interfaces/`) adds significant file count and cognitive overhead.
**Decision:** Use simplified structure with `models.py`, `services.py`, `views.py`, `serializers.py`.
**Rationale:**
- Django developers understand this structure
- Fewer files to navigate
- Sufficient for team size 5-20
- Can evolve to full DDD when needed
**Consequences:**
- Less strict layer enforcement
- Some business logic may leak into views (mitigated by code review)
- Easier onboarding for new developers

### ADR-003: User Model in Identity Context

**Status:** Accepted
**Date:** 2026-07-19
**Context:** `User` model is currently in `core/` app, which is a God App.
**Decision:** Move `User` model to `identity/` app, update `AUTH_USER_MODEL`.
**Rationale:**
- User is the identity aggregate root
- Identity context cannot be clean without owning its aggregate
- Long-term maintainability requires this
**Consequences:**
- Database migration required
- Downtime window needed
- All cross-app FKs must be updated
- High risk, high reward

### ADR-004: Django Signals for In-Process Events

**Status:** Accepted
**Date:** 2026-07-19
**Context:** Need event mechanism for in-process communication.
**Decision:** Use Django signals for Phase 1-5, add event bus in Phase 6.
**Rationale:**
- Native Django support
- No additional infrastructure
- Well-understood by team
- Event bus adds complexity without clear benefit yet
**Consequences:**
- Tightly coupled during monolith phase
- Will need refactoring for microservice extraction (acceptable)

### ADR-005: Selective Repository Pattern

**Status:** Accepted
**Date:** 2026-07-19
**Context:** Whether to use repository pattern for all models.
**Decision:** Use repositories selectively for complex queries only.
**Rationale:**
- Repository pattern adds indirection
- Django ORM is well-understood
- Overuse creates unnecessary abstraction
**Consequences:**
- Some queries remain inline in services
- Code review ensures repositories used where needed

### ADR-006: No CQRS in Year 1

**Status:** Accepted
**Date:** 2026-07-19
**Context:** Whether to implement CQRS from the start.
**Decision:** Do not implement CQRS. Use Django ORM for reads and writes.
**Rationale:**
- RentSecure does not have dramatically different read/write loads
- CQRS adds complexity without clear benefit
- Django is not designed for CQRS
**Consequences:**
- Read and write models are the same
- Optimize with caching instead
- Can add CQRS in Stage 2 if needed

### ADR-007: Platform Layer Minimalism

**Status:** Accepted
**Date:** 2026-07-19
**Context:** What should live in `platform/` layer.
**Decision:** Keep only infrastructure adapters (cache, storage, search, events). Remove communication channels, queue, DI container.
**Rationale:**
- Platform layer should be minimal
- Communication channels belong in `notification/adapters/`
- Queue is Stage 2
- DI container is unnecessary for Django
**Consequences:**
- Clear separation of concerns
- Less abstraction overhead

### ADR-008: Incremental Migration Strategy

**Status:** Accepted
**Date:** 2026-07-19
**Context:** How to migrate from current architecture to target architecture.
**Decision:** 6-phase incremental migration with backward compatibility.
**Rationale:**
- Production system cannot afford downtime
- Breaking changes should be minimized
- Incremental migration reduces risk
**Consequences:**
- Migration takes 15-20 weeks
- Temporary shims and redirects required
- `core` app remains until Phase 5

---

## 22. Official Architecture v1.0

### 22.1 Principles

1. **Bounded contexts are sacred** — one context = one app in `apps/`
2. **`shared/` is pure** — no business logic, no Django imports
3. **`platform/` is minimal** — infrastructure adapters only
4. **No circular dependencies** — enforced by import-linter
5. **No infrastructure leaks** — no app imports from `rentsecure_be/`
6. **Business logic lives in services** — never in views or models
7. **External SDKs live in adapters** — never in views
8. **All webhooks are verified** — HMAC in adapters, not views
9. **All sensitive data is encrypted** — bank details, secrets
10. **Every public API is tested** — unit, integration, contract tests

### 22.2 Standards

| Standard | Requirement |
|---|---|
| Code Style | Ruff (format + lint) |
| Type Safety | MyPy strict mode |
| Import Rules | import-linter, zero violations |
| Test Coverage | 90% unit, 80% integration |
| Architecture Tests | Run on every commit |
| Security | Bandit + Safety on every PR |
| Performance | < 10 queries per view, < 200ms p95 |
| Documentation | ADR for every architectural decision |

### 22.3 Governance

1. **Architecture Review Board** — reviews all ADRs, approves changes to `shared/` and `platform/`
2. **Import-Linter CI Gate** — blocks PRs with import violations
3. **Architecture Contract Tests** — run on every commit
4. **Quarterly Architecture Review** — review tech debt, update roadmap
5. **ADR Requirement** — all architectural changes require ADR

### 22.4 Enforcement

| Mechanism | Tool | Frequency |
|---|---|---|
| Lint | Ruff | Every commit |
| Type Check | MyPy | Every commit |
| Import Rules | import-linter | Every commit |
| Architecture Tests | Pytest | Every commit |
| Security Scan | Bandit | Every PR |
| Mutation Testing | Sonar | Every PR |
| Performance Tests | Locust | Nightly |
| Code Review | GitHub | Every PR |

---

## Appendix A: Files to Create/Modify

### CREATE

| Path | Purpose |
|---|---|
| `apps/identity/` (full structure) | Identity bounded context |
| `apps/subscription/` (full structure) | Subscription bounded context |
| `apps/dashboard/` (full structure) | Dashboard bounded context |
| `apps/payment/models.py` | OwnerBankDetails model |
| `apps/payment/adapters/cashfree_client.py` | Cashfree API client |
| `apps/payment/services/webhook_service.py` | Webhook handling service |
| `platform/` (full structure) | Infrastructure adapters |
| `config/` (full structure) | Django configuration |
| `tests/test_architecture_contract/` | Architecture tests |

### MODIFY

| Path | Changes |
|---|---|
| `rentsecure_be/settings.py` | Update `INSTALLED_APPS`, `AUTH_USER_MODEL` |
| `rentsecure_be/urls.py` | Update URL includes |
| `import-linter.ini` | Add new apps |
| `shared/type_compat.py` | Add `override` decorator |
| `properties/feature_enforcer.py` | Move to `subscription/` |
| `properties/utils/utils.py` | Remove subscription imports |
| `properties/views/rent_record_views.py` | Remove reporting views |

### REMOVE

| Path | Reason |
|---|---|
| `core/` (entire directory) | God app, replaced by bounded contexts |
| `rentsecure_be/services/cashfree_service.py` | Moved to `payment/` |
| `rentsecure_be/utils/cashfree_payout.py` | Moved to `payment/` |
| `rentsecure_be/utils/export_utils.py` | Moved to `dashboard/` |
| `ai_assistant/` | Dead code |
| `dashboard/` (old, dead) | Dead code |
| `properties/models/subscription_models.py` | Empty placeholder |

---

## Appendix B: Migration Checklist

### Phase 0: Foundation
- [ ] Move `type_compat.py` to `shared/`
- [ ] Update all 20+ imports
- [ ] Create app skeletons
- [ ] Add architecture contract tests
- [ ] Clean up dead code

### Phase 1: Identity
- [ ] Create `identity/models.py`
- [ ] Create migration
- [ ] Create data migration
- [ ] Create services
- [ ] Create views
- [ ] Create serializers
- [ ] Create URLs
- [ ] Update cross-app imports
- [ ] Update signals

### Phase 2: Subscription
- [ ] Create `subscription/models.py`
- [ ] Create migration
- [ ] Move `FeatureEnforcer`
- [ ] Update `properties/` imports
- [ ] Create services
- [ ] Create views
- [ ] Create URLs

### Phase 3: Payment
- [ ] Add `OwnerBankDetails` to `payment/models.py`
- [ ] Create migration
- [ ] Move webhook handlers
- [ ] Move bank details service
- [ ] Move Cashfree adapter
- [ ] Clean up `rentsecure_be/`

### Phase 4: Dashboard & Referral
- [ ] Create `dashboard/models.py`
- [ ] Move `OwnerReportingService`
- [ ] Move reporting views
- [ ] Add `ReferralService` to `referral/`
- [ ] Move `NotificationPreference`

### Phase 5: Deprecate Core
- [ ] Remove all `core` models
- [ ] Remove all `core` views
- [ ] Remove all `core` services
- [ ] Update `AUTH_USER_MODEL`
- [ ] Remove `core` from `INSTALLED_APPS`
- [ ] Delete `core/` directory

### Phase 6: Optimization
- [ ] Add repositories for complex queries
- [ ] Add event bus
- [ ] Add port/adapter interfaces
- [ ] Optimize queries
- [ ] Add caching
- [ ] Document APIs

---

**END OF ARCHITECTURE v1.0**

**Approved by:** Principal Software Architect
**Date:** 2026-07-19
**Next Review:** 2026-10-19 (Quarterly)
