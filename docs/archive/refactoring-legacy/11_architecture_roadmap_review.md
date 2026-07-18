# RentSecure Backend — Architecture Roadmap Review

**Document Type:** Architecture Review Board (ARB) Assessment
**Project:** RentSecure Backend
**Phase:** Roadmap Validation & Redesign
**Date:** 2026-07-17
**Status:** REVIEW — Awaiting Implementation
**Constraint:** Analysis only. No production code was modified.

**Reviewed Document:** `docs/refactoring/10_architecture_gap_analysis.md`
**Target Architecture:** `docs/refactoring/09_target_architecture.md`
**ADRs:** `docs/refactoring/08_architecture_decisions.md`

---

## Executive Summary

The 100-task roadmap in the gap analysis is **structurally unsound** and **violates multiple Clean Architecture and DDD principles**. The phase ordering creates unnecessary risk, schedules critical safety concerns too late, and omits essential prerequisites.

**Key Findings:**
- **Phase ordering is inverted**: Observability, security, and event infrastructure are scheduled last when they should be first.
- **Empty folder creation is treated as deliverable**: 30+ tasks create folder structures without populating them, providing zero business value and creating merge-conflict risk.
- **Critical production risks are deferred**: Unconditional imports of disabled services (critical severity) are not fully addressed in Phase 1.
- **No compatibility wrappers**: ADR-004 mandates compatibility wrappers, but the roadmap contains zero tasks for them.
- **Missing foundational tasks**: Value objects, repository interfaces, and ports are not created before entities, services, and adapters that depend on them.
- **Testing is an afterthought**: Testing is Phase 8 (last) rather than continuous per phase.
- **Dual-model anti-pattern**: The roadmap plans to create pure domain entities alongside existing Django ORM models without a migration strategy.

**Recommendation:** The roadmap must be redesigned before implementation begins. The current roadmap would result in production incidents, circular imports, and significant rework.

---

## Critical Issues

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | **Unconditional imports of disabled services not fully fixed in Phase 1** | Critical | App fails to start if gateway deps missing |
| 2 | **Observability implemented in Phase 7 (week 41+)** | Critical | Cannot debug production issues during Phases 3-6 |
| 3 | **Security (webhooks, rate limiting) implemented in Phase 7** | Critical | Security vulnerabilities exposed during migration |
| 4 | **Event bus created AFTER signals are replaced** | Critical | Cannot replace signals without event bus |
| 5 | **No compatibility wrappers planned** | Critical | Violates ADR-004, high risk of breaking changes |
| 6 | **Domain entities created without value objects** | High | Entities will use primitives instead of VOs, defeating DDD purpose |
| 7 | **Repository interfaces created after entities** | High | Entities depend on repositories that don't exist yet |
| 8 | **Ports created after adapters** | High | Adapters implement ports that don't exist yet |
| 9 | **Empty folder creation as tasks** | Medium | Wasteful, creates merge conflicts, no business value |
| 10 | **`dashboard/` gets `apps.py` instead of creating `analytics/`** | Medium | Creates Frankenstein app, later requires second migration |
| 11 | **`core/` split deferred** | Medium | Identity and Subscriptions remain mixed, violating bounded context boundaries |
| 12 | **No database migration strategy** | Medium | Schema changes will break production |
| 13 | **No CI/CD validation steps** | Medium | Architecture violations won't be caught automatically |
| 14 | **Testing is Phase 8 (last)** | Medium | Bugs discovered late, expensive to fix |
| 15 | **No ADR creation tasks** | Medium | Missing architectural decisions not documented |

---

## Recommended Changes

### 1. Reorder Phases by True Dependency

The current order violates the natural dependency chain of Clean Architecture:

**Current (wrong) order:**
1. Foundation → 2. Folder Structure → 3. Domain → 4. Application/Ports → 5. Events → 6. Analytics → 7. Observability/Security → 8. Testing

**Correct order:**
1. **Safety & Foundation** (fix critical risks, configure tooling, create ADRs)
2. **Shared Kernel** (events, VOs, ports, base protocols — must exist before anything else)
3. **Domain Layer** (entities, domain services, repository interfaces — depend on shared kernel)
4. **Event Infrastructure** (event bus, domain events, integration events — must exist before signals are replaced)
5. **Application Layer** (application services, use cases — depend on domain layer and event bus)
6. **Infrastructure Layer** (adapters, ORM implementations — depend on ports)
7. **Presentation Layer** (views, serializers — depend on application layer)
8. **Security & Observability** (must be in place BEFORE exposing new endpoints)
9. **Analytics & Read Models** (depends on domain and application layers)
10. **Testing & Validation** (continuous, not final phase)

### 2. Merge Empty Folder Creation Tasks

Tasks 16-48 (30 tasks) are mostly "Add `domain/` folder to X", "Add `application/` folder to X", etc. These should be:
- Merged into the task that populates the folder
- Or batched into a single "Establish layer structure" task per app
- Creating empty folders provides no value and creates merge conflicts

### 3. Add Missing Prerequisite Tasks

Before creating entities, the roadmap must include:
- Create base value objects (`Money`, `PhoneNumber`, `Email`, etc.)
- Create base entity class with event-emitting capability
- Create base repository protocol
- Create base domain service class

### 4. Add Compatibility Wrapper Tasks

Every file move must include:
- Create compatibility wrapper at old location
- Update all call sites to new location
- Verify zero imports remain at old location
- Remove compatibility wrapper

### 5. Fix `dashboard/` vs `analytics/` Confusion

Instead of:
1. Add `apps.py` to `dashboard/` (Phase 1)
2. Later move `dashboard/` → `analytics/` (Phase 6)

Do this:
1. Create `analytics/` app directly (Phase 2)
2. Move `dashboard/views.py` → `analytics/presentation/views/` (Phase 2)
3. Delete `dashboard/` (Phase 2)

### 6. Move Critical Risks to Phase 1

The following must be in Phase 1 (Weeks 1-2), not deferred:
- Fix ALL unconditional imports of disabled services (`cashfree_service`, `razorpay_service`, `leegality_service`)
- Configure `import-linter` with initial rules
- Add basic structured logging (JSON format)
- Add health check endpoints
- Add request ID middleware

### 7. Split Phase 7 (Observability & Security) into Two

- **Phase 7a (Security)**: Move to Phase 2 (after shared kernel)
- **Phase 7b (Observability)**: Move to Phase 1-2 (basic logging) and Phase 9 (advanced metrics)

### 8. Integrate Testing Into Every Phase

Instead of a final "Testing & Quality" phase:
- Each phase includes "Write tests for new code"
- Phase 10 becomes "Enforce coverage gates and architecture validation"

### 9. Add ADR Creation Tasks

Before implementation:
- ADR-011: Event Bus Strategy
- ADR-012: Database-per-Context Strategy
- ADR-013: API Versioning Strategy
- ADR-014: Testing Strategy
- ADR-016: Database Migration Strategy
- ADR-017: Secret Management Strategy
- ADR-018: Error Handling Strategy
- ADR-022: Webhook Security Strategy
- ADR-023: Rate Limiting Strategy
- ADR-027: Feature Flag Governance

### 10. Add Database Migration Strategy

- All migrations must be additive (new columns/tables only)
- No column renames or type changes in migration phases
- Data backfill must be async (management command)
- Zero-downtime migration pattern: add column → backfill → switch → remove old column

---

## Improved Phase Ordering

| New Phase | Name | Duration | Prerequisites | Risk |
|-----------|------|----------|---------------|------|
| **0** | ADR Completion & Architecture Validation | Week 0 | None | None |
| **1** | Safety & Foundation | Weeks 1-2 | Phase 0 | Low |
| **2** | Shared Kernel & Event Infrastructure | Weeks 3-4 | Phase 1 | Low |
| **3** | Domain Layer Extraction | Weeks 5-10 | Phase 2 | Medium-High |
| **4** | Event Migration (Signals → Domain Events) | Weeks 11-12 | Phase 3 | High |
| **5** | Application Layer & Ports | Weeks 13-16 | Phase 4 | Medium |
| **6** | Infrastructure Layer & Adapters | Weeks 17-20 | Phase 5 | Medium |
| **7** | Presentation Layer Refactoring | Weeks 21-24 | Phase 6 | Medium |
| **8** | Security Hardening | Weeks 25-26 | Phase 7 | Medium |
| **9** | Analytics & Read Models | Weeks 27-30 | Phase 7 | Medium |
| **10** | Testing, Validation & Coverage Gates | Weeks 31-34 | All phases | Low |

**Total estimated duration: 34 weeks (8.5 months)**

---

## New Task Ordering

### Phase 0: ADR Completion & Architecture Validation (Week 0)

| # | Task | Priority | Risk | Hours | Dependencies |
|---|------|----------|------|-------|-------------|
| 0.1 | Create ADR-011: Event Bus Strategy | High | Low | 4 | None |
| 0.2 | Create ADR-012: Database-per-Context Strategy | High | Low | 4 | None |
| 0.3 | Create ADR-013: API Versioning Strategy | High | Low | 4 | None |
| 0.4 | Create ADR-014: Testing Strategy | High | Low | 4 | None |
| 0.5 | Create ADR-016: Database Migration Strategy | High | Low | 4 | None |
| 0.6 | Create ADR-017: Secret Management Strategy | High | Low | 4 | None |
| 0.7 | Create ADR-018: Error Handling Strategy | High | Low | 4 | None |
| 0.8 | Create ADR-022: Webhook Security Strategy | High | Low | 4 | None |
| 0.9 | Create ADR-023: Rate Limiting Strategy | High | Low | 4 | None |
| 0.10 | Create ADR-027: Feature Flag Governance | High | Low | 4 | None |
| 0.11 | Configure `import-linter` with initial rules | High | Low | 8 | None |
| 0.12 | Set up CI pipeline with architecture validation | High | Low | 8 | 0.11 |
| 0.13 | Create architecture test suite (contract tests) | High | Low | 8 | 0.11 |

**Deliverables:**
- 10 new ADRs approved
- `import-linter` configured and passing in CI
- Architecture validation tests running in CI

### Phase 1: Safety & Foundation (Weeks 1-2)

| # | Task | Priority | Risk | Hours | Dependencies |
|---|------|----------|------|-------|-------------|
| 1.1 | Fix unconditional import of `cashfree_service` in `core/views.py` | Critical | Medium | 4 | None |
| 1.2 | Fix unconditional import of `razorpay_service` in `properties/views/rent_record_views.py` | Critical | Medium | 4 | None |
| 1.3 | Fix unconditional import of `leegality_service` in `properties/views/unit_views.py` | Critical | Medium | 4 | None |
| 1.4 | Fix unconditional import of `cashfree_service`, `leegality_service` in `smartbot/actions.py` | Critical | Medium | 4 | None |
| 1.5 | Fix unconditional import of `i18n_service` in `notification/services/rent_notify_service.py` | Critical | Medium | 4 | None |
| 1.6 | Implement lazy import helper for feature-flagged services | High | Low | 8 | 1.1-1.5 |
| 1.7 | Consolidate WhatsApp in `notification/` (merge `utils.py` into `services/`) | High | Low | 4 | None |
| 1.8 | Move `rentsecure_be/services/i18n_service.py` → `shared/infrastructure/adapters/translation.py` | High | Low | 4 | None |
| 1.9 | Move `core/services/owner_reporting_service.py` → `properties/services/owner_reporting_service.py` | High | Low | 4 | None |
| 1.10 | Archive `smartbot/tasks.py` (no-op stub) | Low | None | 1 | None |
| 1.11 | Delete `ai_assistant/models.py` (empty placeholder) | Low | None | 1 | None |
| 1.12 | Delete `ai_assistant/services/i18n_service.py` (duplicate) | High | Low | 1 | 1.8 |
| 1.13 | Add basic structured JSON logging to `settings.py` | High | Low | 4 | None |
| 1.14 | Add request ID middleware | High | Low | 4 | None |
| 1.15 | Add health check endpoints (`/health/live`, `/health/ready`) | High | Medium | 8 | None |
| 1.16 | Rename `referral_and_earn/` → `referral/` | High | Low | 2 | None |

**Deliverables:**
- All unconditional imports fixed
- Lazy import pattern established
- Basic observability (logging, health checks) in place
- Duplicates consolidated

### Phase 2: Shared Kernel & Event Infrastructure (Weeks 3-4)

| # | Task | Priority | Risk | Hours | Dependencies |
|---|------|----------|------|-------|-------------|
| 2.1 | Create `shared/domain/value_objects/money.py` | High | Low | 4 | None |
| 2.2 | Create `shared/domain/value_objects/phone_number.py` | High | Low | 4 | None |
| 2.3 | Create `shared/domain/value_objects/email.py` | High | Low | 4 | None |
| 2.4 | Create `shared/domain/value_objects/date_range.py` | High | Low | 4 | None |
| 2.5 | Create `shared/domain/value_objects/percentage.py` | High | Low | 4 | None |
| 2.6 | Create `shared/domain/value_objects/base.py` (base VO class) | High | Low | 4 | None |
| 2.7 | Create `shared/domain/events/base.py` (base event class) | High | Low | 4 | None |
| 2.8 | Create `shared/domain/events/bus.py` (event bus interface) | High | Medium | 8 | 2.7 |
| 2.9 | Create `shared/domain/events/handler.py` (base handler class) | High | Low | 4 | 2.7 |
| 2.10 | Create in-process event bus implementation | High | Medium | 12 | 2.8 |
| 2.11 | Create `shared/domain/ports/repository.py` (base repository protocol) | High | Low | 4 | None |
| 2.12 | Create `shared/domain/ports/service.py` (base service protocol) | High | Low | 4 | None |
| 2.13 | Create `shared/domain/ports/cache_service.py` | High | Low | 4 | None |
| 2.14 | Create `shared/domain/ports/audit_logger.py` | High | Low | 4 | None |
| 2.15 | Create `shared/domain/ports/metrics_service.py` | High | Low | 4 | None |
| 2.16 | Implement event bus idempotency (event ID tracking) | High | High | 12 | 2.10 |
| 2.17 | Implement event bus correlation ID propagation | High | Medium | 8 | 2.10 |
| 2.18 | Write tests for all value objects | High | Low | 8 | 2.1-2.6 |
| 2.19 | Write tests for event bus | High | Medium | 12 | 2.10, 2.16, 2.17 |

**Deliverables:**
- Value objects library
- Event bus with idempotency and correlation IDs
- Base protocols for repositories, services, cache, audit, metrics
- All shared kernel tests passing

### Phase 3: Domain Layer Extraction (Weeks 5-10)

**Prerequisite:** Value objects, event bus, and base protocols exist.

| # | Task | Priority | Risk | Hours | Dependencies |
|---|------|----------|------|-------|-------------|
| 3.1 | Create `identity/domain/user/entities/user.py` (pure domain entity) | High | Medium | 8 | 2.1-2.6 |
| 3.2 | Create `identity/domain/profile/entities/profile.py` | High | Low | 4 | 2.1-2.6 |
| 3.3 | Create `identity/domain/otp/value_objects/otp_code.py` | High | Low | 4 | 2.1-2.6 |
| 3.4 | Create `core/domain/subscription/entities/subscription_plan.py` | High | Low | 4 | 2.1-2.6 |
| 3.5 | Create `core/domain/subscription/entities/user_subscription.py` | High | Low | 4 | 2.1-2.6 |
| 3.6 | Create `core/domain/subscription/entities/usage_limit.py` | High | Low | 4 | 2.1-2.6 |
| 3.7 | Create `properties/domain/building/entities/building.py` | High | Medium | 8 | 2.1-2.6 |
| 3.8 | Create `properties/domain/unit/entities/unit.py` | High | Medium | 8 | 2.1-2.6 |
| 3.9 | Create `properties/domain/renter/entities/renter.py` | High | Medium | 8 | 2.1-2.6 |
| 3.10 | Create `properties/domain/rent/entities/rent_record.py` | High | Medium | 8 | 2.1-2.6 |
| 3.11 | Create `properties/domain/extra_charge/entities/extra_charge.py` | High | Low | 4 | 2.1-2.6 |
| 3.12 | Create `properties/domain/property_tax/entities/property_tax_record.py` | High | Low | 4 | 2.1-2.6 |
| 3.13 | Create `properties/domain/caretaker/entities/caretaker.py` | High | Low | 4 | 2.1-2.6 |
| 3.14 | Create `notification/domain/notification/entities/notification.py` | High | Low | 4 | 2.1-2.6 |
| 3.15 | Create `notification/domain/device_token/entities/device_token.py` | High | Low | 4 | 2.1-2.6 |
| 3.16 | Create `finance/domain/ca/entities/ca_profile.py` | High | Low | 4 | 2.1-2.6 |
| 3.17 | Create `finance/domain/tax/entities/tax_submission.py` | High | Low | 4 | 2.1-2.6 |
| 3.18 | Create `referral/domain/referral/entities/referral.py` | High | Low | 4 | 2.1-2.6 |
| 3.19 | Create `assistant/domain/chat/entities/chat.py` | High | Low | 4 | 2.1-2.6 |
| 3.20 | Create `assistant/domain/alert/entities/alert.py` | High | Low | 4 | 2.1-2.6 |
| 3.21 | Create repository interfaces for all aggregates | High | Medium | 16 | 2.11, 3.1-3.20 |
| 3.22 | Create domain services for all aggregates | High | Medium | 24 | 3.1-3.20 |
| 3.23 | Create policies for all aggregates | High | Low | 16 | 3.1-3.20 |
| 3.24 | Write unit tests for all domain entities | High | Medium | 24 | 3.1-3.20 |
| 3.25 | Write unit tests for all domain services | High | Medium | 16 | 3.22 |

**Deliverables:**
- Pure domain entities for all aggregates
- Repository interfaces (protocols)
- Domain services
- Policies
- Domain layer tests (≥90% coverage)

### Phase 4: Event Migration (Weeks 11-12)

**Prerequisite:** Domain layer, event bus, and domain events exist.

| # | Task | Priority | Risk | Hours | Dependencies |
|---|------|----------|------|-------|-------------|
| 4.1 | Create domain events for `core` aggregates | High | Medium | 8 | Phase 3, Phase 2 |
| 4.2 | Create domain events for `properties` aggregates | High | High | 12 | Phase 3, Phase 2 |
| 4.3 | Create domain events for `notification` aggregates | High | Medium | 8 | Phase 3, Phase 2 |
| 4.4 | Create domain events for `finance` aggregates | High | Low | 4 | Phase 3, Phase 2 |
| 4.5 | Create domain events for `referral` aggregates | High | Low | 4 | Phase 3, Phase 2 |
| 4.6 | Create domain events for `assistant` aggregates | High | Low | 4 | Phase 3, Phase 2 |
| 4.7 | Replace `core/signals.py` with domain event handlers | High | High | 12 | 4.1 |
| 4.8 | Replace `properties/signals/` with domain event handlers | High | High | 16 | 4.2 |
| 4.9 | Replace `referral_and_earn/signals.py` with domain event handlers | High | Medium | 8 | 4.5 |
| 4.10 | Replace `ai_assistant/receivers.py` with domain event handlers | High | Medium | 8 | 4.6 |
| 4.11 | Create integration events for cross-module communication | High | Medium | 12 | 4.1-4.6 |
| 4.12 | Implement integration event handlers | High | High | 16 | 4.11 |
| 4.13 | Write tests for all domain event handlers | High | Medium | 16 | 4.7-4.10 |
| 4.14 | Write tests for all integration event handlers | High | Medium | 12 | 4.12 |

**Deliverables:**
- All Django signals replaced with domain events
- Integration events for cross-module communication
- Event handlers with idempotency
- Event tests passing

### Phase 5: Application Layer & Ports (Weeks 13-16)

**Prerequisite:** Domain layer, event bus, and domain events exist.

| # | Task | Priority | Risk | Hours | Dependencies |
|---|------|----------|------|-------|-------------|
| 5.1 | Create `identity/application/` services (AuthService, OTPService, etc.) | High | Medium | 16 | Phase 3 |
| 5.2 | Create `core/application/` services (SubscriptionService, UsageLimitService) | High | Medium | 12 | Phase 3 |
| 5.3 | Create `properties/application/` services (RenterService, UnitService, etc.) | High | High | 24 | Phase 3 |
| 5.4 | Create `notification/application/` services | High | Medium | 12 | Phase 3 |
| 5.5 | Create `documents/application/` services | High | Medium | 12 | Phase 3 |
| 5.6 | Create `finance/application/` services | High | Low | 8 | Phase 3 |
| 5.7 | Create `referral/application/` services | High | Low | 8 | Phase 3 |
| 5.8 | Create `assistant/application/` services | High | Medium | 12 | Phase 3 |
| 5.9 | Create `payments/domain/payment/ports/payment_gateway.py` | High | Low | 4 | Phase 2 |
| 5.10 | Create `notification/domain/channel/ports/channel.py` | High | Low | 4 | Phase 2 |
| 5.11 | Create `documents/domain/pdf/ports/pdf_generator.py` | High | Low | 4 | Phase 2 |
| 5.12 | Create `documents/domain/esignature/ports/esignature_provider.py` | High | Low | 4 | Phase 2 |
| 5.13 | Create `assistant/domain/llm/ports/llm_client.py` | High | Low | 4 | Phase 2 |
| 5.14 | Create `shared/domain/ports/storage_service.py` | High | Low | 4 | Phase 2 |
| 5.15 | Create `shared/domain/ports/translation_service.py` | High | Low | 4 | Phase 2 |
| 5.16 | Create `shared/domain/ports/text_to_speech_service.py` | High | Low | 4 | Phase 2 |
| 5.17 | Write tests for all application services | High | Medium | 24 | 5.1-5.8 |

**Deliverables:**
- Application services for all use cases
- All ports defined
- Application service tests passing

### Phase 6: Infrastructure Layer & Adapters (Weeks 17-20)

**Prerequisite:** Ports and application services exist.

| # | Task | Priority | Risk | Hours | Dependencies |
|---|------|----------|------|-------|-------------|
| 6.1 | Create `payments/infrastructure/adapters/manual.py` (ManualPaymentAdapter) | High | Low | 8 | 5.9 |
| 6.2 | Create `payments/infrastructure/adapters/razorpay.py` (RazorpayAdapter) | High | Medium | 8 | 5.9 |
| 6.3 | Create `payments/infrastructure/adapters/cashfree.py` (CashfreeAdapter) | High | Medium | 8 | 5.9 |
| 6.4 | Move `rentsecure_be/services/razorpay_service.py` → `payments/infrastructure/adapters/razorpay.py` | High | Medium | 8 | 6.2 |
| 6.5 | Move `rentsecure_be/services/cashfree_service.py` → `payments/infrastructure/adapters/cashfree.py` | High | Medium | 8 | 6.3 |
| 6.6 | Move `rentsecure_be/utils/cashfree_payout.py` → `payments/infrastructure/adapters/cashfree_payout.py` | High | Medium | 4 | 6.3 |
| 6.7 | Create compatibility wrapper for old `rentsecure_be/services/` imports | High | Low | 4 | 6.4-6.6 |
| 6.8 | Create `notification/infrastructure/adapters/whatsapp.py` (TwilioWhatsAppAdapter) | High | Low | 8 | 5.10 |
| 6.9 | Create `notification/infrastructure/adapters/sms.py` (TwilioSMSAdapter) | High | Low | 8 | 5.10 |
| 6.10 | Create `notification/infrastructure/adapters/push.py` (FCMAdapter) | High | Low | 8 | 5.10 |
| 6.11 | Create `notification/infrastructure/adapters/email.py` (SESAdapter + SMTPAdapter) | High | Low | 8 | 5.10 |
| 6.12 | Create `notification/infrastructure/adapters/voice.py` (OpenAITTSSAdapter) | High | Low | 8 | 5.10 |
| 6.13 | Merge `smartbot/whatsapp_service.py` into `notification/infrastructure/adapters/whatsapp.py` | High | Medium | 8 | 6.8 |
| 6.14 | Create `documents/infrastructure/adapters/leegality.py` (LeegalityAdapter) | High | Medium | 8 | 5.12 |
| 6.15 | Create `documents/infrastructure/adapters/s3.py` (S3StorageAdapter) | High | Low | 8 | 5.14 |
| 6.16 | Create `documents/infrastructure/adapters/local.py` (LocalStorageAdapter) | High | Low | 4 | 5.14 |
| 6.17 | Create `documents/infrastructure/pdf_generator.py` (unified PDF generation) | High | Medium | 12 | 5.11 |
| 6.18 | Move `smartbot/services/leegality_service.py` → `documents/infrastructure/adapters/leegality.py` | High | Medium | 8 | 6.14 |
| 6.19 | Move `rentsecure_be/services/leegality_service.py` → `documents/infrastructure/adapters/leegality.py` | High | Medium | 8 | 6.14 |
| 6.20 | Consolidate Leegality implementations | High | High | 16 | 6.14, 6.18, 6.19 |
| 6.21 | Move `properties/utils/utils.py` PDF functions → `documents/infrastructure/pdf_generator.py` | High | Medium | 8 | 6.17 |
| 6.22 | Move `finance/utils.py` PDF functions → `documents/infrastructure/pdf_generator.py` | High | Medium | 4 | 6.17 |
| 6.23 | Move `documents/utils.py` → `documents/infrastructure/pdf_generator.py` | High | Low | 4 | 6.17 |
| 6.24 | Move `properties/templates/pdf/` → `documents/templates/pdf/` | High | Low | 4 | None |
| 6.25 | Move `finance/templates/pdf_templates/` → `documents/templates/pdf/` | High | Low | 2 | None |
| 6.26 | Create `assistant/infrastructure/adapters/openai.py` (OpenAILLMAdapter) | High | Medium | 8 | 5.13 |
| 6.27 | Create `shared/infrastructure/adapters/google_translate.py` (GoogleTranslateAdapter) | High | Low | 8 | 5.15 |
| 6.28 | Create `shared/infrastructure/adapters/openai_translation.py` (OpenAITranslationAdapter) | High | Low | 8 | 5.15 |
| 6.29 | Create `infrastructure/infrastructure/adapters/prometheus.py` (PrometheusMetricsAdapter) | High | Low | 8 | None |
| 6.30 | Create `infrastructure/infrastructure/adapters/sentry.py` (SentryErrorAdapter) | High | Low | 8 | None |
| 6.31 | Implement Django ORM repository implementations | High | Medium | 24 | Phase 3 |
| 6.32 | Write tests for all adapters (contract tests) | High | Medium | 24 | 6.1-6.30 |

**Deliverables:**
- All adapters implemented
- All payment gateways in `payments/`
- All notification channels in `notification/`
- PDF generation consolidated in `documents/`
- Adapter contract tests passing

### Phase 7: Presentation Layer Refactoring (Weeks 21-24)

**Prerequisite:** Application services, ports, and adapters exist.

| # | Task | Priority | Risk | Hours | Dependencies |
|---|------|----------|------|-------|-------------|
| 7.1 | Create `identity/presentation/views/` and move views from `core/views.py` | High | Medium | 12 | Phase 5 |
| 7.2 | Create `identity/presentation/serializers/` and move serializers | High | Low | 8 | Phase 5 |
| 7.3 | Create `core/presentation/views/` and move subscription views | High | Low | 8 | Phase 5 |
| 7.4 | Create `core/presentation/serializers/` and move serializers | High | Low | 4 | Phase 5 |
| 7.5 | Create `properties/presentation/views/` and move views from `properties/views/*.py` | High | Medium | 12 | Phase 5 |
| 7.6 | Create `properties/presentation/serializers/` and move serializers | High | Low | 4 | Phase 5 |
| 7.7 | Create `properties/presentation/permissions/` | High | Low | 4 | Phase 5 |
| 7.8 | Create `notification/presentation/views/` and move views | High | Low | 4 | Phase 5 |
| 7.9 | Create `documents/presentation/views/` and move views | High | Low | 4 | Phase 5 |
| 7.10 | Create `finance/presentation/views/` and move views | High | Low | 4 | Phase 5 |
| 7.11 | Create `finance/presentation/serializers/` and move serializers | High | Low | 2 | Phase 5 |
| 7.12 | Create `referral/presentation/views/` and move views (if any) | High | Low | 4 | Phase 5 |
| 7.13 | Create `assistant/presentation/views/` and move views from `smartbot/views.py` and `ai_assistant/views.py` | High | Medium | 8 | Phase 5 |
| 7.14 | Create `payments/presentation/views/` for webhooks | High | Medium | 8 | Phase 5 |
| 7.15 | Create `payments/presentation/urls.py` for webhook endpoints | High | Low | 4 | 7.14 |
| 7.16 | Refactor `core/views.py` to use application services (no business logic) | High | High | 16 | Phase 5 |
| 7.17 | Refactor `properties/views/*.py` to use application services | High | High | 24 | Phase 5 |
| 7.18 | Refactor `notification/views.py` to use application services | High | Medium | 8 | Phase 5 |
| 7.19 | Refactor `documents/views.py` to use application services | High | Medium | 8 | Phase 5 |
| 7.20 | Refactor `finance/views.py` to use application services | High | Medium | 8 | Phase 5 |
| 7.21 | Create compatibility wrappers for old view imports | High | Low | 8 | 7.1-7.20 |
| 7.22 | Write API contract tests for all endpoints | High | Medium | 24 | 7.1-7.21 |

**Deliverables:**
- All views in `presentation/` folders
- Views delegate to application services (no business logic)
- API contract tests passing
- Compatibility wrappers for old imports

### Phase 8: Security Hardening (Weeks 25-26)

**Prerequisite:** Presentation layer exists and all endpoints are defined.

| # | Task | Priority | Risk | Hours | Dependencies |
|---|------|----------|------|-------|-------------|
| 8.1 | Create custom permission classes per module | High | Medium | 16 | Phase 7 |
| 8.2 | Implement object-level permissions for all resources | High | Medium | 24 | 8.1 |
| 8.3 | Implement rate limiting (per endpoint type) | High | Medium | 12 | Phase 7 |
| 8.4 | Implement webhook signature verification (HMAC-SHA256) | High | High | 12 | Phase 6 |
| 8.5 | Implement webhook replay protection (timestamp validation) | High | High | 8 | 8.4 |
| 8.6 | Implement webhook idempotency keys | High | High | 12 | 8.4 |
| 8.7 | Implement secret management abstraction (AWS Secrets Manager / Vault) | High | Medium | 12 | None |
| 8.8 | Implement file upload virus scanning | High | Medium | 12 | None |
| 8.9 | Implement CORS configuration | High | Low | 4 | None |
| 8.10 | Implement input sanitization (XSS/injection prevention) | High | Medium | 12 | None |
| 8.11 | Implement audit logging for sensitive operations | High | High | 16 | Phase 2 |
| 8.12 | Write security tests (penetration tests) | High | Medium | 16 | 8.1-8.11 |

**Deliverables:**
- Custom permission classes
- Rate limiting
- Webhook security (signature, replay protection, idempotency)
- Secret management
- Audit logging
- Security tests passing

### Phase 9: Analytics & Read Models (Weeks 27-30)

**Prerequisite:** Application layer, domain layer, and event bus exist.

| # | Task | Priority | Risk | Hours | Dependencies |
|---|------|----------|------|-------|-------------|
| 9.1 | Create `analytics/` Django app (directly, not via `dashboard/`) | High | Low | 4 | None |
| 9.2 | Move `dashboard/views.py` → `analytics/presentation/views/` | High | Low | 4 | 9.1 |
| 9.3 | Move `dashboard/urls.py` → `analytics/urls.py` | High | Low | 2 | 9.1 |
| 9.4 | Move `dashboard/tests.py` → `analytics/tests/` | High | Low | 2 | 9.1 |
| 9.5 | Delete `dashboard/` directory | High | Low | 1 | 9.2, 9.3, 9.4 |
| 9.6 | Create `analytics/domain/` read models | High | Medium | 12 | Phase 3 |
| 9.7 | Create `analytics/application/` services | High | Medium | 12 | Phase 5 |
| 9.8 | Create `analytics/infrastructure/` query services | High | Medium | 12 | Phase 6 |
| 9.9 | Create `OwnerDashboardReadModel` | High | Medium | 12 | 9.6 |
| 9.10 | Create `RentAnalyticsReadModel` | High | Medium | 12 | 9.6 |
| 9.11 | Create `OccupancyAnalyticsReadModel` | High | Medium | 12 | 9.6 |
| 9.12 | Create `MonthlySummaryReadModel` | High | Medium | 12 | 9.6 |
| 9.13 | Move `core/services/owner_reporting_service.py` → `analytics/application/services/` | High | Medium | 8 | 9.7 |
| 9.14 | Move `properties/services/unit_service.py` analytics methods → `analytics/` | High | Medium | 8 | 9.7 |
| 9.15 | Move `properties/views/owner_dashboard.py` → `analytics/presentation/views/` | High | Medium | 8 | 9.2 |
| 9.16 | Populate read models via domain events | High | Medium | 16 | 9.9-9.12, Phase 4 |
| 9.17 | Write tests for read models | High | Medium | 12 | 9.9-9.12 |

**Deliverables:**
- `analytics/` app with full structure
- Read models for dashboard and analytics
- Analytics queries isolated from transactional queries
- Read model tests passing

### Phase 10: Testing, Validation & Coverage Gates (Weeks 31-34)

**Prerequisite:** All previous phases complete.

| # | Task | Priority | Risk | Hours | Dependencies |
|---|------|----------|------|-------|-------------|
| 10.1 | Reorganize all tests per layer (domain/application/infrastructure/presentation) | High | Medium | 24 | All phases |
| 10.2 | Add unit tests for all domain entities (if missing) | High | Medium | 24 | Phase 3 |
| 10.3 | Add integration tests for all application services | High | Medium | 24 | Phase 5 |
| 10.4 | Add contract tests for all external adapters | High | Medium | 24 | Phase 6 |
| 10.5 | Add API integration tests for all endpoints | High | Medium | 24 | Phase 7 |
| 10.6 | Add event handler tests | High | Medium | 16 | Phase 4 |
| 10.7 | Enforce `mypy --strict` in CI | High | Low | 8 | None |
| 10.8 | Enforce `ruff check` in CI | High | Low | 4 | None |
| 10.9 | Enforce ≥90% coverage for domain and application layers | High | Medium | 8 | 10.1-10.6 |
| 10.10 | Run full test suite and fix all failures | High | Medium | 16 | 10.1-10.9 |
| 10.11 | Perform architecture review (import-linter, dependency graph) | High | Low | 8 | None |
| 10.12 | Update all ADRs with implementation findings | High | Low | 8 | All phases |

**Deliverables:**
- Tests organized per layer
- ≥90% coverage for domain and application layers
- All linting/type checking passes
- Architecture validation passing
- ADRs updated

---

## Additional Tasks Required

The original roadmap is missing these critical tasks:

| # | Missing Task | Phase | Reason |
|---|-------------|-------|--------|
| 1 | Create base value objects before entities | Phase 2 | Entities need VOs to be meaningful |
| 2 | Create base repository protocol before repositories | Phase 2 | Repositories implement this protocol |
| 3 | Create base domain service class | Phase 2 | Domain services inherit from this |
| 4 | Create base entity class with event-emitting capability | Phase 2 | Entities emit domain events |
| 5 | Create event bus BEFORE replacing signals | Phase 2 | Signals must publish to event bus |
| 6 | Create domain events BEFORE replacing signals | Phase 4 | Signals are replaced with domain events |
| 7 | Create compatibility wrappers for ALL file moves | Every phase | ADR-004 requirement |
| 8 | Create `analytics/` app directly (not `dashboard/`) | Phase 9 | Avoids Frankenstein app |
| 9 | Split `core/` into `identity/` and `core/` (subscriptions) | Phase 3 | Enforces bounded context boundaries |
| 10 | Create all repository interfaces (17 interfaces) | Phase 3 | Domain layer depends on them |
| 11 | Create all domain services (13 services) | Phase 3 | Application layer depends on them |
| 12 | Create all application services (13 services) | Phase 5 | Presentation layer depends on them |
| 13 | Create all ports (12 ports) | Phase 2/5 | Adapters implement ports |
| 14 | Create all adapters (17 adapters) | Phase 6 | Infrastructure layer |
| 15 | Implement Django ORM repository implementations | Phase 6 | Infrastructure layer |
| 16 | Create `payments/domain/payment/entities/` | Phase 3 | Payment domain entities |
| 17 | Create `payments/domain/payout/entities/` | Phase 3 | Payout domain entities |
| 18 | Create `assistant/domain/intent/` entities and services | Phase 3 | Intent extraction domain |
| 19 | Create `assistant/domain/action/` entities and services | Phase 3 | Action dispatch domain |
| 20 | Create `documents/domain/agreement/` entities and services | Phase 3 | Agreement domain |
| 21 | Create `documents/domain/receipt/` entities and services | Phase 3 | Receipt domain |
| 22 | Create `notification/domain/voice/` entities and services | Phase 3 | Voice note domain |
| 23 | Split `smartbot/actions.py` operational actions → domain apps | Phase 5 | Actions are domain operations |
| 24 | Move `smartbot/services/agreement_service.py` → `documents/` | Phase 6 | PDF generation in documents |
| 25 | Move `ai_assistant/services/archive_service.py` → `properties/` | Phase 6 | Property archival in properties |
| 26 | Move `ai_assistant/services/unit_service.py` → `properties/` | Phase 6 | Property logic in properties |
| 27 | Move `ai_assistant/services/invoice_service.py` → `documents/` | Phase 6 | PDF generation in documents |
| 28 | Move `notification/services/rent_notify_service.py` → `properties/` | Phase 6 | Property notifications in properties |
| 29 | Move `notification/services/extra_charge_reminders.py` → `properties/` | Phase 6 | Property notifications in properties |
| 30 | Move `notification/services/late_fees_notify_service.py` → `properties/` | Phase 6 | Property notifications in properties |
| 31 | Move `smartbot/cron/reminders.py` → `documents/application/tasks/` | Phase 6 | Document-related cron |
| 32 | Create `infrastructure/` app for cross-cutting concerns | Phase 2 | Logging, metrics, caching, security |
| 33 | Implement structured JSON logging | Phase 1 | Observability from day 1 |
| 34 | Implement Prometheus metrics | Phase 8 | Observability |
| 35 | Implement OpenTelemetry tracing | Phase 8 | Observability |
| 36 | Implement Sentry integration | Phase 8 | Error tracking |
| 37 | Implement distributed tracing | Phase 8 | Observability |
| 38 | Create architecture validation tests | Phase 0 | Prevent architecture violations |
| 39 | Create CI/CD pipeline with architecture gates | Phase 0 | Automated validation |
| 40 | Create database migration strategy | Phase 0 | Zero-downtime migrations |
| 41 | Create rollback procedures per phase | Phase 0 | Disaster recovery |
| 42 | Create feature flag governance ADR | Phase 0 | Feature flag standards |
| 43 | Create API versioning strategy ADR | Phase 0 | API evolution |
| 44 | Create error handling strategy ADR | Phase 0 | Standardized errors |
| 45 | Create database-per-context strategy ADR | Phase 0 | Database evolution |
| 46 | Create testing strategy ADR | Phase 0 | Testing standards |
| 47 | Create secret management strategy ADR | Phase 0 | Security standards |
| 48 | Create webhook security strategy ADR | Phase 0 | Webhook standards |
| 49 | Create rate limiting strategy ADR | Phase 0 | Rate limiting standards |
| 50 | Implement cache invalidation strategy | Phase 8 | Caching |
| 51 | Implement cache warming | Phase 8 | Caching |
| 52 | Implement cache metrics | Phase 8 | Observability |
| 53 | Create `shared/domain/tasks/` base task class | Phase 2 | Background processing |
| 54 | Create task registry | Phase 8 | Background processing |
| 55 | Implement task monitoring | Phase 8 | Background processing |
| 56 | Create Celery configuration (Stage 2) | Phase 8 | Background processing |
| 57 | Fix multiple URL mounts on `/api/` | Phase 7 | URL namespace collisions |
| 58 | Implement CORS configuration | Phase 8 | Security |
| 59 | Implement file upload virus scanning | Phase 8 | Security |
| 60 | Implement input sanitization | Phase 8 | Security |

---

## Tasks That Can Be Removed

The original roadmap contains tasks that are unnecessary or should be merged:

| Original Task # | Task | Reason for Removal |
|-----------------|------|-------------------|
| 2 | Add `apps.py` to `dashboard/` | Should create `analytics/` directly instead |
| 11-14 | Create empty Django apps | Should create apps with initial structure, not empty shells |
| 16-23 | Add `domain/` folder to each app | Merge with task that populates the folder |
| 29-34 | Add `application/` folder to each app | Merge with task that populates the folder |
| 35-41 | Add `infrastructure/` folder to each app | Merge with task that populates the folder |
| 42-48 | Add `presentation/` folder to each app | Merge with task that populates the folder |
| 100 | Implement Prometheus metrics | Move to Phase 8 with other observability tasks |

**Rationale:** Creating empty folders is busywork. The folder structure should be created as part of the task that populates it. This reduces merge conflicts and makes each task independently valuable.

---

## Tasks That Can Be Merged

| Original Tasks | Merged Task | Rationale |
|----------------|-------------|-----------|
| 1, 7, 8 | Rename `referral_and_earn/` → `referral/`, move i18n, move owner reporting | All are low-risk file moves with no dependencies |
| 3, 4, 5 | Archive `smartbot/tasks.py`, delete empty `ai_assistant/models.py`, delete duplicate i18n | All are cleanup tasks |
| 6, 62 | Consolidate WhatsApp, merge `smartbot/whatsapp_service.py` | Both are WhatsApp consolidation |
| 58, 59, 60 | Move both Leegality implementations and consolidate | Single logical operation |
| 64, 65, 66, 67 | Move all PDF generation and templates to `documents/` | Single logical operation |
| 73, 74, 75 | Move all property notification services to `properties/` | Single logical operation |
| 16-48 | Create all folder structures | Batch into "Establish layer structure" per app |
| 98, 99, 100 | Implement health checks, logging, metrics | Batch into "Observability foundation" |

---

## Production Migration Strategy

### Zero-Downtime Principles

1. **Feature flags for all new code**: New bounded contexts and services must be behind feature flags.
2. **Compatibility wrappers**: Old import locations must re-export new implementations during migration.
3. **Canary deployments**: Deploy to 5% of instances first, monitor, then roll out.
4. **Instant rollback**: Each phase must be revertible within 15 minutes.

### Migration Pattern per Task

For every file move or service consolidation:

1. **Create new implementation** at target location
2. **Create compatibility wrapper** at old location (re-exports new implementation)
3. **Update call sites** one-by-one to use new location
4. **Verify zero imports** remain at old location
5. **Remove compatibility wrapper**
6. **Deploy** and monitor
7. **Rollback** if issues detected

### Feature Flag Strategy

| Feature Flag | Purpose | Default | Rollout |
|--------------|---------|---------|---------|
| `ENABLE_NEW_IDENTITY` | Switch to `identity/` bounded context | `False` | Canary 5% → 25% → 100% |
| `ENABLE_NEW_PROPERTIES` | Switch to layered `properties/` structure | `False` | Canary 5% → 25% → 100% |
| `ENABLE_NEW_NOTIFICATIONS` | Switch to notification adapters | `False` | Canary 5% → 25% → 100% |
| `ENABLE_NEW_DOCUMENTS` | Switch to `documents/` adapters | `False` | Canary 5% → 25% → 100% |
| `ENABLE_NEW_PAYMENTS` | Switch to `payments/` adapters | `False` | Canary 5% → 25% → 100% |
| `ENABLE_NEW_ASSISTANT` | Switch to `assistant/` bounded context | `False` | Canary 5% → 25% → 100% |
| `ENABLE_DOMAIN_EVENTS` | Switch from signals to domain events | `False` | Canary 5% → 25% → 100% |

### Rollback Triggers

Rollback immediately if:
1. More than 5% of tests fail after a phase
2. Production error rate increases by >10%
3. Any endpoint returns 500 for >1% of requests
4. Database migration fails
5. `import-linter` violations are introduced
6. Any security control is weakened
7. Feature flag enables new code with >1% error rate

---

## ADR Plan

The following ADRs must be created BEFORE implementation begins:

| ADR | Title | Priority | Status |
|-----|-------|----------|--------|
| ADR-011 | Event Bus Implementation Strategy | High | Missing |
| ADR-012 | Database-per-Context Strategy | High | Missing |
| ADR-013 | API Versioning Strategy | High | Missing |
| ADR-014 | Testing Strategy and Coverage Requirements | High | Missing |
| ADR-015 | CI/CD Pipeline Architecture | High | Missing |
| ADR-016 | Database Migration Strategy | High | Missing |
| ADR-017 | Secret Management Strategy | High | Missing |
| ADR-018 | Error Handling and Exception Hierarchy | High | Missing |
| ADR-019 | Logging and Observability Strategy | High | Missing |
| ADR-020 | Cache Invalidation Strategy | Medium | Missing |
| ADR-021 | File Storage Strategy | Medium | Missing |
| ADR-022 | Webhook Security Strategy | High | Missing |
| ADR-023 | Rate Limiting Strategy | High | Missing |
| ADR-024 | Frontend-Backend Contract Strategy | Medium | Missing |
| ADR-025 | Deployment Strategy | Medium | Missing |
| ADR-026 | Rollback and Disaster Recovery Strategy | High | Missing |
| ADR-027 | Feature Flag Governance | High | Missing |
| ADR-028 | Documentation Standards | Low | Missing |
| ADR-029 | Third-Party Service Dependencies | Medium | Missing |
| ADR-030 | Data Retention and Archival Strategy | Medium | Missing |

---

## Database Migration Strategy

### Principles

1. **Additive migrations only**: New columns/tables only. No column renames or type changes.
2. **Zero-downtime**: No downtime during migrations.
3. **Backfill async**: Data backfill via management command, not in migration.
4. **Validation**: Verify data consistency after backfill.

### Migration Pattern

```python
# Step 1: Add new column (migration)
class Migration(migrations.Migration):
    dependencies = []
    operations = [
        migrations.AddColumn(
            model_name='renter',
            name='new_field',
            field=models.CharField(max_length=255, null=True),
        ),
    ]

# Step 2: Backfill data (management command)
def backfill_new_field():
    for renter in Renter.objects.filter(new_field__isnull=True):
        renter.new_field = compute_value(renter)
        renter.save(update_fields=['new_field'])

# Step 3: Switch application code (deploy)
# Application now uses new_field

# Step 4: Remove old column (future migration)
class Migration(migrations.Migration):
    dependencies = []
    operations = [
        migrations.RemoveField(
            model_name='renter',
            name='old_field',
        ),
    ]
```

### Per-Phase Database Changes

| Phase | Database Changes | Rollback |
|-------|-----------------|----------|
| Phase 1 | None | N/A |
| Phase 2 | None (shared kernel is code-only) | N/A |
| Phase 3 | Add new columns for pure domain entity metadata | Remove columns |
| Phase 4 | Add event store table | Drop table |
| Phase 5 | None (application services are code-only) | N/A |
| Phase 6 | Add adapter configuration tables | Drop tables |
| Phase 7 | None (views are code-only) | N/A |
| Phase 8 | Add audit log table | Drop table |
| Phase 9 | Add read model tables | Drop tables |
| Phase 10 | None | N/A |

---

## CI/CD Validation Plan

### Pipeline Stages

```yaml
stages:
  - lint
  - typecheck
  - architecture
  - test
  - security
  - deploy

jobs:
  lint:
    - ruff check .
    - black --check .
    - isort --check .

  typecheck:
    - mypy --strict .

  architecture:
    - import-linter
    - django-system-check
    - architecture-contract-tests

  test:
    - pytest tests/domain/ -v
    - pytest tests/application/ -v
    - pytest tests/infrastructure/ -v
    - pytest tests/presentation/ -v
    - pytest tests/ -v --cov

  security:
    - bandit -r .
    - safety check
    - secret-scan

  deploy:
    - canary-deploy (5%)
    - smoke-tests
    - monitor (15 min)
    - full-rollout or rollback
```

### Architecture Gates

| Gate | Tool | Fail Condition |
|------|------|----------------|
| Import violations | `import-linter` | Any forbidden dependency |
| Circular imports | `import-linter` | Any circular dependency |
| Framework leakage | Custom script | Domain imports Django/DRF |
| Infrastructure leakage | Custom script | Application imports ORM |
| Cross-module model imports | Custom script | Module imports another module's models |
| Test coverage | `pytest-cov` | <90% for domain/application |
| Type checking | `mypy --strict` | Any errors |
| Linting | `ruff check` | Any errors |

---

## Architecture Validation Plan

### Automated Tests

| Test | Purpose | Frequency |
|------|---------|-----------|
| Import-linter | Enforce dependency rules | Every commit |
| Architecture contract tests | Validate module boundaries | Every commit |
| Layer purity tests | Ensure no framework leakage in domain | Every commit |
| Circular import detection | Prevent circular dependencies | Every commit |
| Test coverage | Enforce ≥90% for domain/application | Every commit |
| Type checking | Enforce `mypy --strict` | Every commit |

### Manual Reviews

| Review | Frequency | Participants |
|--------|-----------|-------------|
| Phase review | End of each phase | Architect, Tech Lead, Senior Engineers |
| Dependency review | Monthly | Architect |
| Security review | Quarterly | Security Engineer, Architect |
| Performance review | Monthly | DevOps, Architect |

---

## Testing Strategy Per Phase

### Phase 0: ADR & Foundation
- **Test type**: None (documentation only)
- **Coverage target**: N/A

### Phase 1: Safety & Foundation
- **Test type**: Regression tests for fixed imports
- **Coverage target**: 100% of changed code
- **Validation**: Smoke tests for all endpoints

### Phase 2: Shared Kernel
- **Test type**: Unit tests for value objects, event bus, protocols
- **Coverage target**: 100%
- **Validation**: Contract tests for event bus

### Phase 3: Domain Layer
- **Test type**: Unit tests for entities, domain services, policies
- **Coverage target**: ≥90%
- **Validation**: Domain tests must pass without Django ORM

### Phase 4: Event Migration
- **Test type**: Integration tests for event handlers
- **Coverage target**: ≥90%
- **Validation**: Event idempotency tests, correlation ID tests

### Phase 5: Application Layer
- **Test type**: Integration tests for application services
- **Coverage target**: ≥90%
- **Validation**: Use case tests with mocked dependencies

### Phase 6: Infrastructure Layer
- **Test type**: Contract tests for adapters
- **Coverage target**: ≥90%
- **Validation**: Mock external APIs, test error handling

### Phase 7: Presentation Layer
- **Test type**: API integration tests
- **Coverage target**: ≥80%
- **Validation**: API contract tests, smoke tests

### Phase 8: Security
- **Test type**: Security tests, penetration tests
- **Coverage target**: 100% of security controls
- **Validation**: OWASP Top 10, webhook security tests

### Phase 9: Analytics
- **Test type**: Read model tests, analytics integration tests
- **Coverage target**: ≥90%
- **Validation**: Data consistency checks

### Phase 10: Validation
- **Test type**: Full regression, architecture validation
- **Coverage target**: ≥90% overall
- **Validation**: Full test suite, architecture review

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation | Phase |
|------|-----------|--------|------------|-------|
| Circular imports during migration | Medium | High | Use dependency injection, lazy imports, compatibility wrappers | All |
| Production incidents from broken imports | Medium | Critical | Fix unconditional imports in Phase 1, feature flags | Phase 1 |
| Event bus performance issues | Low | Medium | Benchmark event bus before replacing signals | Phase 2-4 |
| Domain model inconsistencies | Medium | High | Comprehensive tests, event sourcing for critical aggregates | Phase 3 |
| Adapter interface too rigid | Low | Medium | Design interfaces carefully, allow extension points | Phase 6 |
| Feature flag misconfiguration | Medium | Medium | Automated flag validation, canary deployment | All |
| Database migration failures | Low | Critical | Additive migrations only, backfill async, rollback scripts | Phase 3+ |
| Rollback complexity | Medium | High | Revertible commits, feature flags, compatibility wrappers | All |
| Team resistance to new patterns | Medium | Low | Training, documentation, gradual migration | All |
| Merge conflicts | High | Medium | Small PRs, frequent rebases, feature flags | All |
| Performance regression | Medium | Medium | Benchmark before/after, caching strategy | All |
| Security vulnerabilities | Medium | High | Security phase before production exposure | Phase 8 |
| Observability gaps during migration | High | Medium | Basic logging in Phase 1, advanced in Phase 8 | Phase 1, 8 |
| Test coverage gaps | Medium | Medium | Continuous testing, coverage gates in CI | All |

---

## Estimated Engineering Effort

| Phase | Duration | Team Size | Total Hours | Risk Buffer | Total with Buffer |
|-------|----------|-----------|-------------|-------------|------------------|
| Phase 0 | 1 week | 2 engineers | 80 hrs | 20% | 96 hrs |
| Phase 1 | 2 weeks | 2 engineers | 160 hrs | 20% | 192 hrs |
| Phase 2 | 2 weeks | 2 engineers | 160 hrs | 15% | 184 hrs |
| Phase 3 | 6 weeks | 3 engineers | 720 hrs | 25% | 900 hrs |
| Phase 4 | 2 weeks | 2 engineers | 160 hrs | 25% | 200 hrs |
| Phase 5 | 4 weeks | 2 engineers | 320 hrs | 20% | 384 hrs |
| Phase 6 | 4 weeks | 2 engineers | 320 hrs | 20% | 384 hrs |
| Phase 7 | 4 weeks | 2 engineers | 320 hrs | 20% | 384 hrs |
| Phase 8 | 2 weeks | 2 engineers | 160 hrs | 15% | 184 hrs |
| Phase 9 | 4 weeks | 2 engineers | 320 hrs | 20% | 384 hrs |
| Phase 10 | 4 weeks | 2 engineers | 320 hrs | 15% | 368 hrs |

**Total estimated effort: 3,960 hours (approximately 2 engineer-years)**

**Key assumptions:**
- 2-3 engineers dedicated full-time
- 40-hour work weeks
- 20% average risk buffer
- No major production incidents during migration

---

## Final Improved Roadmap

### Phase 0: ADR Completion & Architecture Validation (Week 0)

**Goal:** Complete missing ADRs, configure tooling, establish validation gates.

**Tasks:**
- Create 10 missing ADRs
- Configure `import-linter` with complete rules
- Set up CI pipeline with architecture gates
- Create architecture validation test suite

**Deliverables:**
- 20 ADRs total (10 existing + 10 new)
- `import-linter` configured
- CI pipeline with architecture gates
- Architecture validation tests

**Success criteria:**
- All ADRs approved by architecture review board
- `import-linter` passes on current codebase
- CI pipeline green

---

### Phase 1: Safety & Foundation (Weeks 1-2)

**Goal:** Fix critical production risks, establish basic observability, consolidate duplicates.

**Tasks:**
- Fix ALL unconditional imports of disabled services
- Implement lazy import pattern for feature-flagged services
- Consolidate duplicate implementations (WhatsApp, i18n, Leegality)
- Add structured JSON logging
- Add request ID middleware
- Add health check endpoints
- Archive dead code

**Deliverables:**
- No unconditional imports of disabled services
- Lazy import pattern established
- Duplicates consolidated
- Basic observability in place

**Success criteria:**
- App starts with all feature flags disabled
- All tests pass
- Health checks return 200

---

### Phase 2: Shared Kernel & Event Infrastructure (Weeks 3-4)

**Goal:** Create shared kernel (value objects, events, ports) that all other modules depend on.

**Tasks:**
- Create base value objects (Money, PhoneNumber, Email, DateRange, Percentage)
- Create base entity class with event-emitting capability
- Create event bus with idempotency and correlation IDs
- Create base repository protocol
- Create base service protocols
- Create cache, audit, metrics ports
- Create `infrastructure/` app for cross-cutting concerns

**Deliverables:**
- Value objects library
- Event bus implementation
- Base protocols
- Infrastructure app

**Success criteria:**
- All value objects have comprehensive tests
- Event bus passes idempotency tests
- Protocols are usable by all modules

---

### Phase 3: Domain Layer Extraction (Weeks 5-10)

**Goal:** Extract pure domain models, domain services, and repository interfaces for all aggregates.

**Tasks:**
- Create domain entities for all aggregates (User, Building, Unit, Renter, RentRecord, etc.)
- Create repository interfaces (protocols) for all aggregates
- Create domain services for all aggregates
- Create policies for all aggregates
- Split `core/` into `identity/` and `core/` (subscriptions)
- Write comprehensive domain layer tests

**Deliverables:**
- Pure domain entities with value objects
- Repository interfaces
- Domain services
- Policies
- Domain layer tests (≥90% coverage)

**Success criteria:**
- Domain layer has zero Django/DRF imports
- Domain tests pass without database
- All business rules enforced in domain layer

---

### Phase 4: Event Migration (Weeks 11-12)

**Goal:** Replace all Django signals with domain events and integration events.

**Tasks:**
- Create domain events for all aggregates
- Create integration events for cross-module communication
- Replace `core/signals.py` with domain event handlers
- Replace `properties/signals/` with domain event handlers
- Replace `referral_and_earn/signals.py` with domain event handlers
- Replace `ai_assistant/receivers.py` with domain event handlers
- Implement integration event handlers
- Write event handler tests

**Deliverables:**
- All Django signals removed
- Domain events published via event bus
- Integration events for cross-module communication
- Event handler tests passing

**Success criteria:**
- Zero Django signals in codebase
- All event handlers idempotent
- Event bus handles 10K events/sec without errors

---

### Phase 5: Application Layer & Ports (Weeks 13-16)

**Goal:** Create application services that orchestrate use cases, and define all ports.

**Tasks:**
- Create application services for all use cases
- Define all ports (PaymentGateway, NotificationChannel, StorageService, LLMClient, etc.)
- Create compatibility wrappers for old service imports
- Write application service tests

**Deliverables:**
- Application services for all use cases
- All ports defined
- Compatibility wrappers for old imports
- Application service tests (≥90% coverage)

**Success criteria:**
- Views delegate to application services
- Application services delegate to domain services
- All ports have at least one implementation

---

### Phase 6: Infrastructure Layer & Adapters (Weeks 17-20)

**Goal:** Implement all adapters, consolidate scattered services, and create ORM repository implementations.

**Tasks:**
- Implement all payment gateway adapters (Manual, Razorpay, Cashfree)
- Implement all notification channel adapters (WhatsApp, SMS, Push, Email, Voice)
- Implement document adapters (Leegality, S3, Local, PDF Generator)
- Implement AI adapter (OpenAI)
- Implement infrastructure adapters (Prometheus, Sentry)
- Move and consolidate all scattered services (Leegality, PDF, WhatsApp, etc.)
- Implement Django ORM repository implementations
- Write adapter contract tests

**Deliverables:**
- All adapters implemented
- All scattered services consolidated
- ORM repository implementations
- Adapter contract tests passing

**Success criteria:**
- All external integrations behind ports
- No direct imports of external services from domain/application layers
- Adapters can be swapped without changing business logic

---

### Phase 7: Presentation Layer Refactoring (Weeks 21-24)

**Goal:** Restructure views and serializers into `presentation/` folders, eliminate business logic from views.

**Tasks:**
- Create `presentation/` folders in all apps
- Move views and serializers to `presentation/` folders
- Refactor all views to delegate to application services
- Create custom permission classes
- Create API contract tests
- Create compatibility wrappers for old view imports

**Deliverables:**
- All views in `presentation/` folders
- Views contain no business logic
- API contract tests passing
- Compatibility wrappers for old imports

**Success criteria:**
- All views delegate to application services
- No business logic in views
- All API endpoints have contract tests

---

### Phase 8: Security Hardening (Weeks 25-26)

**Goal:** Implement all security controls before production exposure.

**Tasks:**
- Implement object-level permissions
- Implement rate limiting
- Implement webhook signature verification
- Implement webhook replay protection
- Implement webhook idempotency keys
- Implement secret management abstraction
- Implement file upload virus scanning
- Implement CORS configuration
- Implement input sanitization
- Implement audit logging
- Write security tests

**Deliverables:**
- All security controls implemented
- Security tests passing
- Penetration test report

**Success criteria:**
- All OWASP Top 10 vulnerabilities mitigated
- Webhooks verified with HMAC-SHA256
- Rate limiting active on all endpoints

---

### Phase 9: Analytics & Read Models (Weeks 27-30)

**Goal:** Create `analytics/` bounded context with read models for dashboard and reporting.

**Tasks:**
- Create `analytics/` Django app directly
- Move `dashboard/` code to `analytics/`
- Delete `dashboard/`
- Create read models (OwnerDashboard, RentAnalytics, Occupancy, MonthlySummary)
- Create analytics application services
- Create analytics query services
- Populate read models via domain events
- Write read model tests

**Deliverables:**
- `analytics/` app with full structure
- Read models for all analytics queries
- Analytics queries isolated from transactional queries
- Read model tests passing

**Success criteria:**
- Dashboard queries use read models
- Analytics queries don't compete with transactional queries
- Read models are eventually consistent

---

### Phase 10: Testing, Validation & Coverage Gates (Weeks 31-34)

**Goal:** Ensure all tests pass, coverage meets targets, and architecture is validated.

**Tasks:**
- Reorganize all tests per layer
- Fill test coverage gaps
- Enforce `mypy --strict`
- Enforce `ruff check`
- Enforce ≥90% coverage for domain and application layers
- Run full regression test suite
- Perform architecture review
- Update all ADRs with implementation findings

**Deliverables:**
- Tests organized per layer
- ≥90% coverage for domain and application layers
- All linting/type checking passes
- Architecture validation passing
- Updated ADRs

**Success criteria:**
- Full test suite passes
- No linting or type checking errors
- Architecture review approved
- Ready for production

---

## Appendix A: Critical Path

```
Phase 0 (ADRs + Tooling)
    │
    ▼
Phase 1 (Safety + Foundation)
    │
    ▼
Phase 2 (Shared Kernel + Events)
    │
    ▼
Phase 3 (Domain Layer)
    │
    ▼
Phase 4 (Event Migration)
    │
    ▼
Phase 5 (Application Layer + Ports)
    │
    ▼
Phase 6 (Infrastructure + Adapters)
    │
    ▼
Phase 7 (Presentation Layer)
    │
    ▼
Phase 8 (Security)
    │
    ▼
Phase 9 (Analytics)
    │
    ▼
Phase 10 (Testing + Validation)
```

**Parallelization opportunities:**
- Phase 3 (Domain Layer) can be done per module in parallel by different engineers
- Phase 5 (Application Layer) can be done per module in parallel
- Phase 6 (Adapters) can be done per integration in parallel

---

## Appendix B: Anti-Patterns to Avoid

| Anti-Pattern | Why It's Wrong | Correct Approach |
|--------------|----------------|-----------------|
| Creating empty folders as tasks | No business value, creates merge conflicts | Create and populate folders in single task |
| Implementing adapters before ports | Adapters depend on ports that don't exist | Define ports first, then implement adapters |
| Replacing signals before event bus exists | No mechanism to publish events | Create event bus first, then replace signals |
| Creating entities without value objects | Entities will use primitives, defeating DDD | Create value objects first |
| Creating entities without repository interfaces | Entities depend on repositories that don't exist | Create repository interfaces first |
| Implementing observability last | Cannot debug production issues during migration | Implement basic logging in Phase 1 |
| Implementing security last | Security vulnerabilities exposed during migration | Implement security in Phase 8 (after endpoints exist) |
| Testing as final phase | Bugs discovered late, expensive to fix | Test continuously per phase |
| Big bang migrations | High risk, hard to rollback | Incremental migration with feature flags |
| No compatibility wrappers | Breaking changes for existing callers | Use compatibility wrappers per ADR-004 |

---

## Appendix C: Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Architecture completeness | 100/100 | Gap analysis score |
| Test coverage (domain) | ≥90% | `pytest --cov` |
| Test coverage (application) | ≥90% | `pytest --cov` |
| Import-linter violations | 0 | `import-linter` CI check |
| Circular imports | 0 | `import-linter` CI check |
| Mypy errors | 0 | `mypy --strict` CI check |
| Ruff errors | 0 | `ruff check` CI check |
| Production error rate increase | <5% | Monitoring/alerting |
| Rollback time | <15 minutes | Incident response |
| Phase duration variance | <20% | Project tracking |

---

*Document generated by Kilo Architecture Roadmap Review. This is an analysis document only. No production code was modified.*
