# RentSecure Backend — Architecture Decision Records

**Project:** RentSecure Backend
**Phase:** Architecture Decision Records
**Date:** 2026-07-15
**Status:** RECORDED — Awaiting Implementation
**Constraint:** Documentation only. No production code was modified.

---

## ADR Index

| ADR | Title | Status | Priority |
|-----|-------|--------|----------|
| ADR-001 | Modular Monolith vs Microservices | Accepted | High |
| ADR-002 | Bounded Contexts by Business Capability | Accepted | High |
| ADR-003 | Duplicate Service Consolidation | Accepted | High |
| ADR-004 | Compatibility Wrappers During Migration | Accepted | High |
| ADR-005 | Merge `smartbot` + `ai_assistant` into `assistant` | Accepted | Medium |
| ADR-006 | Notification Channel Centralization | Accepted | Medium |
| ADR-007 | PDF Generation as Shared Documents Capability | Accepted | Medium |
| ADR-008 | Leegality in Documents Bounded Context | Accepted | Medium |
| ADR-009 | Analytics as Independent Bounded Context | Accepted | Low |
| ADR-010 | Payment Gateways Behind Adapters | Accepted | High |

---

## ADR-001: Modular Monolith vs Microservices

**Status:** Accepted
**Owner:** Principal Architect
**Date:** 2026-07-15

### Context

RentSecure is approximately 50% complete. The team is considering whether to:
1. Continue as a modular monolith (current state)
2. Migrate to microservices
3. Adopt a hybrid approach

### Problem

Microservices introduce significant operational complexity:
- Service discovery and registry
- Distributed tracing and logging
- Cross-service transactions and sagas
- Network latency and reliability concerns
- Increased DevOps burden

However, the current modular monolith has unclear boundaries and scattered concerns.

### Decision

**RentSecure will remain a modular monolith through Year 1 production.**

The monolith will be structured with clear bounded contexts (Django apps) that can be extracted into services later if needed.

### Alternatives Considered

1. **Full Microservices Architecture**
   - Each bounded context becomes a separate service
   - Communicates via REST/events
   - Pros: Independent deployment, scaling, team ownership
   - Cons: Extreme operational complexity, network overhead, debugging difficulty

2. **Modular Monolith with Service Extraction Points**
   - Keep monolith but design clear interfaces for future extraction
   - Pros: Best of both worlds, gradual migration path
   - Cons: Requires discipline, premature abstraction risk

3. **Hybrid Approach**
   - Core domains in monolith, select services extracted
   - Pros: Flexibility, targeted scaling
   - Cons: Complex deployment topology, inconsistent patterns

### Pros of Chosen Approach

- **Operational simplicity**: Single deployment, single database, straightforward monitoring
- **Development velocity**: No network overhead, easier debugging, faster iteration
- **Data consistency**: ACID transactions across bounded contexts
- **Team structure**: Small team can maintain a well-structured monolith
- **Cost efficiency**: No service mesh, no distributed tracing infrastructure
- **Future-proofing**: Clear boundaries allow extraction to microservices when needed

### Cons of Chosen Approach

- **Scaling limitations**: Cannot scale individual bounded contexts independently
- **Team scaling**: Multiple teams may step on each other's code
- **Technology lock-in**: All bounded contexts share the same tech stack
- **Deployment coupling**: Changes require full redeployment

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Monolith becomes "big ball of mud" | Medium | High | Enforce bounded context boundaries via import-linter |
| Scaling bottlenecks | Low | Medium | Profile before extracting; extract only proven bottlenecks |
| Team coordination overhead | Medium | Low | Clear ownership per bounded context |

### Long-term Consequences

- The monolith will likely be extracted into microservices when:
  - Monthly transaction volume exceeds 500,000 requests/month
  - Multiple teams need independent deployment cycles
  - Specific bounded contexts need different scaling characteristics
- Clear boundaries make extraction cheaper later
- No technical debt from premature microservice adoption

### Reversibility

**Partially reversible.** Extracting microservices later is possible but expensive. The decision to stay monolith is reversible by extracting services, but the reverse (consolidating microservices into monolith) is not recommended.

### Decision Status

**ACCEPTED** — RentSecure will remain a modular monolith through Year 1 production.

---

## ADR-002: Bounded Contexts by Business Capability

**Status:** Accepted
**Owner:** Principal Architect
**Date:** 2026-07-15

### Context

The current Django app structure reflects rapid development rather than intentional design:
- `core/` contains identity, subscriptions, AND owner reporting
- `properties/` contains property management AND usage limits
- `notification/` contains channel code AND property-specific notification logic
- `smartbot/` contains AI features AND business operations

### Problem

Technical-layer organization (models, views, services) leads to:
- Cross-cutting concerns scattered across apps
- Unclear ownership and responsibility boundaries
- Difficult to reason about change impact
- Hard to onboard new developers

### Decision

**Organize bounded contexts by business capability, not technical layer.**

Each Django app represents a business capability:
- `core` — Identity & Access Management
- `properties` — Property Management
- `finance` — Tax & Compliance
- `notification` — Notification Channels
- `documents` — Document Generation & E-Signature
- `assistant` — AI Assistant
- `analytics` — Analytics & Reporting
- `payments` — Payment Processing
- `referral` — Referral Program
- `shared` — Shared Utilities

### Alternatives Considered

1. **Technical Layer Organization**
   - Apps organized by technical concern (models, views, services)
   - Pros: Familiar pattern, easy to find code by type
   - Cons: Business logic scattered, unclear ownership

2. **Feature-Based Organization**
   - Apps organized by user-facing feature
   - Pros: Clear feature ownership
   - Cons: Overlapping features, duplication risk

3. **Entity-Based Organization**
   - Apps organized by primary entity (User, Property, Rent)
   - Pros: Intuitive entity location
   - Cons: Related entities split across apps

### Pros of Chosen Approach

- **Clear ownership**: Each bounded context has a single, well-defined responsibility
- **Business alignment**: Code structure mirrors organizational structure
- **Change isolation**: Changes to one context don't affect others
- **Team autonomy**: Teams can own entire contexts
- **Easier reasoning**: Developers know where to find and modify code
- **DDD alignment**: Follows Domain-Driven Design principles

### Cons of Chosen Approach

- **Learning curve**: Developers must understand bounded contexts
- **Cross-context complexity**: Some features span multiple contexts
- **Initial refactoring cost**: Moving code between contexts is expensive
- **Overlap risk**: Boundaries may blur over time without discipline

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Boundary confusion | Medium | Medium | Import-linter rules, architecture guardian |
| Over-engineering | Low | Low | Start with coarse boundaries, refine later |
| Resistance to change | Medium | Low | Training, documentation, gradual migration |

### Long-term Consequences

- **Positive**: Clean architecture enables faster feature development
- **Positive**: Easier to extract microservices when needed
- **Negative**: Initial migration overhead is significant
- **Negative**: Requires ongoing architecture governance

### Reversibility

**Partially reversible.** Moving code between contexts is possible but expensive. The decision to use business-capability boundaries is reversible by reorganizing apps, but this causes significant churn.

### Decision Status

**ACCEPTED** — Bounded contexts will be organized by business capability.

---

## ADR-003: Duplicate Service Consolidation

**Status:** Accepted
**Owner:** Principal Architect
**Date:** 2026-07-15

### Context

The codebase contains duplicate implementations of critical services:

| Service | Location 1 | Location 2 |
|---------|-----------|-----------|
| WhatsApp | `notification/utils.py` | `notification/services/whatsapp_service.py` |
| Leegality | `rentsecure_be/services/leegality_service.py` | `smartbot/services/leegality_service.py` |
| i18n | `rentsecure_be/services/i18n_service.py` | `ai_assistant/services/i18n_service.py` |
| PDF generation | 5+ locations | — |

### Problem

Duplicate implementations cause:
- **Inconsistent behavior**: Different return types, error handling, defaults
- **Maintenance burden**: Bugs fixed in one place but not the other
- **Developer confusion**: Unclear which implementation to use
- **Testing overhead**: Must test both implementations
- **Code bloat**: Unnecessary duplication increases codebase size

### Decision

**Consolidate duplicate services into canonical implementations.**

For each duplicate:
1. Choose the canonical implementation (usually the more complete/feature-rich one)
2. Move or merge into a single, well-defined location
3. Create compatibility wrappers at old locations during migration
4. Remove wrappers after all call sites are updated

### Alternatives Considered

1. **Keep Both Implementations**
   - Pros: No migration effort
   - Cons: Ongoing maintenance burden, inconsistency risk

2. **Delete One Implementation**
   - Pros: Simple, immediate consolidation
   - Cons: Breaking changes for existing callers

3. **Runtime Selection**
   - Pros: Flexibility, gradual migration
   - Cons: Complexity, configuration overhead

4. **Consolidate with Compatibility Wrappers**
   - Pros: Zero breaking changes, gradual migration
   - Cons: Temporary code duplication during migration

### Pros of Chosen Approach

- **Single source of truth**: One implementation to maintain and test
- **Consistent behavior**: All callers get the same behavior
- **Reduced maintenance**: Fixes apply everywhere
- **Clear ownership**: One team owns the service
- **Gradual migration**: Compatibility wrappers prevent breaking changes

### Cons of Chosen Approach

- **Migration effort**: Requires updating all call sites
- **Temporary complexity**: Compatibility wrappers add indirection
- **Coordination required**: Multiple teams may need to update simultaneously

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Missed call sites | Medium | Medium | Comprehensive grep analysis before migration |
| Behavioral differences | Low | High | Document and test behavioral differences |
| Rollback complexity | Low | Medium | Compatibility wrappers enable instant rollback |

### Long-term Consequences

- **Positive**: Reduced codebase size, easier maintenance
- **Positive**: Consistent behavior across all callers
- **Negative**: Migration effort is significant
- **Negative**: Temporary compatibility code adds complexity

### Reversibility

**Reversible during migration.** Compatibility wrappers allow instant rollback. After wrappers are removed, reversal requires re-duplicating the implementation.

### Decision Status

**ACCEPTED** — Duplicate services will be consolidated with compatibility wrappers.

---

## ADR-004: Compatibility Wrappers During Migration

**Status:** Accepted
**Owner:** Principal Architect
**Date:** 2026-07-15

### Context

The migration plan involves moving files between apps and consolidating implementations. Direct moves would break existing imports and cause production failures.

### Problem

How to migrate code without breaking existing callers?

Options:
1. **Big Bang Migration**: Move everything at once, update all imports simultaneously
   - Pros: Clean, no temporary code
   - Cons: High risk, large PR, hard to review, hard to rollback

2. **Compatibility Wrappers**: Keep old locations as wrappers during migration
   - Pros: Zero breaking changes, gradual migration, easy rollback
   - Cons: Temporary code duplication, indirection overhead

3. **Runtime Resolution**: Use importlib or settings to resolve at runtime
   - Pros: No code changes at call sites
   - Cons: Magic, hard to debug, performance overhead

### Decision

**Use compatibility wrappers during migration.**

Old import locations re-export new implementations with deprecation warnings. Call sites migrate gradually. Wrappers are removed only after zero imports remain.

### Alternatives Considered

1. **Big Bang Migration**
   - Rejected due to high risk and coordination cost

2. **Runtime Resolution**
   - Rejected due to magic and debugging difficulty

3. **No Migration (Keep Duplicates)**
   - Rejected due to ongoing maintenance burden

### Pros of Chosen Approach

- **Zero breaking changes**: Old imports continue to work
- **Gradual migration**: Call sites migrate one-at-a-time
- **Easy rollback**: Revert wrapper removal to restore old behavior
- **Clear deprecation path**: Warnings guide developers to new locations
- **Independent PRs**: Each call site migration is a separate PR

### Cons of Chosen Approach

- **Temporary indirection**: Extra layer during migration
- **Deprecation warnings**: May clutter test output
- **Code bloat**: Temporary wrapper code
- **Discipline required**: Must remember to remove wrappers

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Wrappers never removed | Medium | Medium | Automated checks for zero imports before removal |
| Deprecation warnings ignored | Medium | Low | CI fails on new warnings after migration |
| Performance overhead | Low | Low | Wrappers are simple re-exports, negligible overhead |

### Long-term Consequences

- **Positive**: Zero breaking changes during migration
- **Positive**: Clear deprecation path for developers
- **Negative**: Temporary code complexity during migration
- **Negative**: Requires discipline to clean up wrappers

### Reversibility

**Highly reversible.** Removing a wrapper is a single-line change. Restoring old code is instant.

### Decision Status

**ACCEPTED** — Compatibility wrappers will be used for all migrations.

---

## ADR-005: Merge `smartbot` + `ai_assistant` into `assistant`

**Status:** Accepted
**Owner:** Principal Architect
**Date:** 2026-07-15

### Context

Two apps contain AI-related code:
- `smartbot/`: Chatbot, GPT, intents, actions, Leegality, agreement PDF, WhatsApp
- `ai_assistant/`: Archive service, finance AI, invoice service, i18n service, unit service

The boundary is artificial. `ai_assistant` services are imported by `smartbot` and `properties`.

### Problem

- **Blurred boundaries**: Unclear which app owns AI functionality
- **Scattered AI logic**: AI-related code split across two apps
- **Import confusion**: Developers unsure which app to import from
- **Inconsistent naming**: `smartbot` implies narrow chatbot, but app does more

### Decision

**Merge `smartbot` and `ai_assistant` into a single `assistant` bounded context.**

After merge:
1. Core AI functionality stays in `assistant/`:
   - `models.py` — Chat history, AI alerts
   - `views.py` — Chatbot API endpoint
   - `intents.py` — Intent extraction
   - `services/gpt_services.py` — LLM wrapper
   - `services/chatbot_service.py` — Chatbot logic

2. Non-AI functionality moves to domain apps:
   - `services/leegality_service.py` → `documents/services/`
   - `services/agreement_service.py` → `documents/services/`
   - `whatsapp_service.py` → merge into `notification`
   - `actions.py` operational functions → `properties/services/`

3. `ai_assistant` files move to appropriate domains:
   - `archive_service.py` → `properties/services/`
   - `invoice_service.py` → `documents/services/`
   - `unit_service.py` → `properties/services/`

### Alternatives Considered

1. **Keep Both Apps Separate**
   - Pros: No migration effort
   - Cons: Continued boundary confusion, scattered AI logic

2. **Merge into `smartbot`**
   - Pros: Smaller rename
   - Cons: `smartbot` name is too narrow

3. **Merge into `ai_assistant`**
   - Pros: Broader name
   - Cons: Less established, smaller codebase

4. **Create New `assistant` App**
   - Pros: Clean start, clear purpose
   - Cons: More migration effort, lose git history

### Pros of Chosen Approach

- **Clear naming**: `assistant` encompasses all AI/assistant functionality
- **Unified ownership**: Single team owns AI features
- **Reduced confusion**: One app to import from
- **Easier refactoring**: Related code is co-located
- **Future-proof**: Name accommodates future AI features

### Cons of Chosen Approach

- **Migration effort**: Requires moving and merging code
- **Git history**: File moves lose line-level history (preserved at directory level)
- **Temporary complexity**: Two apps coexist during migration

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Merge conflicts | Medium | Medium | Sequential migration, frequent rebases |
| Lost git history | Low | Low | `git mv` preserves directory history |
| Missed functionality | Low | High | Comprehensive test coverage, manual verification |
| Import breakage | Low | High | Compatibility wrappers during migration |

### Long-term Consequences

- **Positive**: Clear, unified AI bounded context
- **Positive**: Easier to add new AI features
- **Positive**: Single place for AI documentation
- **Negative**: Migration effort is significant
- **Negative**: Temporary duplication during migration

### Reversibility

**Partially reversible.** Can split back into `smartbot` and `ai_assistant`, but effort is high. Better to complete the merge.

### Decision Status

**ACCEPTED** — `smartbot` and `ai_assistant` will be merged into `assistant`.

---

## ADR-006: Notification Channel Centralization

**Status:** Accepted
**Owner:** Principal Architect
**Date:** 2026-07-15

### Context

Notification logic is scattered:
- `notification/services/` contains channel implementations (WhatsApp, push, voice, SMS)
- `notification/services/rent_notify_service.py` contains rent-specific logic
- `notification/services/extra_charge_reminders.py` contains property-specific logic
- `notification/services/late_fees_notify_service.py` contains property-specific logic
- `properties/signals/__init__.py` directly calls WhatsApp from signal handlers

### Problem

- **Mixed concerns**: Channel code and business logic are intermingled
- **Hard to test**: Signal handlers with embedded notification logic
- **Hard to reuse**: Property notification logic can't be reused by other domains
- **Hard to extend**: Adding a new channel requires touching business logic

### Decision

**Notification channels remain centralized in `notification/`, but business notification orchestration moves to domain apps.**

```
notification/
  services/
    channels/
      whatsapp.py    # WhatsApp channel implementation
      voice.py       # Voice note generation
      sms.py         # SMS channel implementation
      email.py       # Email channel implementation
      push.py        # FCM push notifications
    services.py      # notify_user, notify_owner_renter_flagged
    communication.py # send_smart_alert

properties/
  services/
    notification_service.py       # Rent payout notifications
    extra_charge_notifications.py # Extra charge reminders
    late_fee_notifications.py     # Late fee notifications
```

### Alternatives Considered

1. **Keep All in `notification/`**
   - Pros: Simple, no migration
   - Cons: `notification` becomes catch-all, violates SRP

2. **Move All to Properties**
   - Pros: Property logic stays together
   - Cons: Duplicates channel code, hard to reuse channels

3. **Event-Driven Notification**
   - Pros: Decoupled, extensible
   - Cons: Requires message broker, premature for Year 1

### Pros of Chosen Approach

- **Separation of concerns**: Channels separate from business logic
- **Reusability**: Channels can be used by any domain
- **Testability**: Business logic testable without channel dependencies
- **Extensibility**: New channels don't require domain changes
- **Clear ownership**: Notification team owns channels, domain teams own orchestration

### Cons of Chosen Approach

- **Migration effort**: Moving notification services
- **Indirection**: Domain code must call into notification channels
- **Coordination required**: Domain and notification teams must agree on interfaces

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Interface mismatch | Medium | Medium | Define channel interfaces before migration |
| Duplicate orchestration | Low | Medium | Document orchestration patterns |
| Performance overhead | Low | Low | Direct function calls, no network overhead |

### Long-term Consequences

- **Positive**: Clean separation of channels and orchestration
- **Positive**: Easy to add new notification channels
- **Positive**: Notification logic is testable and reusable
- **Negative**: More files and indirection
- **Negative**: Requires interface governance

### Reversibility

**Reversible.** Can move orchestration back to `notification/` if needed, but effort is high.

### Decision Status

**ACCEPTED** — Channels remain in `notification/`, orchestration moves to domain apps.

---

## ADR-007: PDF Generation as Shared Documents Capability

**Status:** Accepted
**Owner:** Principal Architect
**Date:** 2026-07-15

### Context

PDF generation is scattered across 5+ locations:
- `smartbot/services/agreement_service.py`
- `properties/utils/utils.py`
- `documents/views.py`
- `documents/utils.py`
- `finance/views.py`

Each uses WeasyPrint with different patterns, error handling, and template management.

### Problem

- **Code duplication**: WeasyPrint setup repeated 5+ times
- **Inconsistent behavior**: Different error handling, fallbacks, formats
- **Hard to maintain**: Bug fixes must be applied in multiple places
- **Template scattering**: PDF templates spread across apps
- **Testing difficulty**: Must test PDF generation in multiple contexts

### Decision

**Consolidate all PDF generation into `documents/utils/pdf_generator.py`.**

The `documents` app becomes the single owner of PDF generation:
- `documents/utils/pdf_generator.py` — Unified PDF generation API
- `documents/services/` — Document-specific services (agreement, invoice, receipt, dossier)
- `documents/templates/pdf/` — All PDF templates in one location

### Alternatives Considered

1. **Keep Scattered PDF Generation**
   - Pros: No migration effort
   - Cons: Ongoing duplication, maintenance burden

2. **Create Separate `pdf/` App**
   - Pros: Clear ownership
   - Cons: Overkill for a single concern

3. **PDF Generation Service**
   - Pros: Extensible, testable
   - Cons: Over-engineering for current needs

4. **Consolidate in `documents/`**
   - Pros: Documents already owns PDFs, natural fit
   - Cons: `documents` app becomes larger

### Pros of Chosen Approach

- **Single source of truth**: One implementation to maintain
- **Consistent behavior**: All PDFs generated the same way
- **Easier testing**: Test PDF generation in one place
- **Template centralization**: All templates in one location
- **Natural fit**: `documents` already owns document generation

### Cons of Chosen Approach

- **Migration effort**: Moving 5+ implementations
- **Larger `documents` app**: More responsibility in one app
- **Cross-app dependencies**: `documents` depends on `properties` models

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Behavioral differences | Medium | High | Document and test each PDF type before migration |
| Template path issues | Medium | Medium | Validate template paths before moving |
| Performance regression | Low | Low | Benchmark PDF generation before/after |

### Long-term Consequences

- **Positive**: Single, maintainable PDF generation layer
- **Positive**: Easy to add new document types
- **Positive**: Consistent error handling and logging
- **Negative**: `documents` app becomes larger and more complex
- **Negative**: Cross-app dependencies increase

### Reversibility

**Reversible but costly.** Can split PDF generation back to original locations, but effort is high.

### Decision Status

**ACCEPTED** — All PDF generation will be consolidated into `documents/utils/pdf_generator.py`.

---

## ADR-008: Leegality in Documents Bounded Context

**Status:** Accepted
**Owner:** Principal Architect
**Date:** 2026-07-15

### Context

Leegality e-signature integration is implemented in two places:
- `rentsecure_be/services/leegality_service.py` — Used by `properties/views/unit_views.py`
- `smartbot/services/leegality_service.py` — Used by `smartbot/actions.py`

Both implement the same Leegality API with different function signatures and error handling.

### Problem

- **Duplicate implementations**: Two versions of the same API client
- **Inconsistent behavior**: Different error handling, return types
- **Wrong ownership**: E-signature is a document concern, not an AI concern
- **Hard to maintain**: Bug fixes must be applied twice

### Decision

**Move Leegality integration to `documents/services/leegality.py`.**

E-signature is a document capability, so it belongs in the `documents` bounded context:
- `documents/services/leegality.py` — Unified Leegality API client
- `documents/views.py` — Leegality webhook (already exists)
- `documents/services/agreement.py` — Agreement PDF + send for signature

### Alternatives Considered

1. **Keep in `rentsecure_be/`**
   - Pros: No migration effort
   - Cons: Wrong bounded context, not a project-level concern

2. **Keep in `smartbot/`**
   - Pros: AI assistant initiates signatures
   - Cons: E-signature is not an AI feature

3. **Create `esign/` App**
   - Pros: Clear ownership
   - Cons: Overkill for a single integration

4. **Move to `documents/`**
   - Pros: Natural fit with document generation
   - Cons: `documents` app grows larger

### Pros of Chosen Approach

- **Correct ownership**: E-signature is a document capability
- **Single implementation**: Merge duplicates into one
- **Natural workflow**: PDF generation → e-signature → download
- **Easier testing**: Document flows testable in one place
- **Future extensibility**: Easy to add other e-signature providers

### Cons of Chosen Approach

- **Migration effort**: Merging two implementations
- **Larger `documents` app**: More responsibility
- **Cross-app dependencies**: `documents` depends on `properties` models

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Behavioral differences | Medium | High | Document and test both implementations before merging |
| Webhook breakage | Low | High | Test Leegality webhook thoroughly after migration |
| Signature flow regression | Low | High | End-to-end test of signature flow |

### Long-term Consequences

- **Positive**: E-signature is in the right bounded context
- **Positive**: Single implementation to maintain
- **Positive**: Easy to add new document types with e-signature
- **Negative**: `documents` app becomes larger
- **Negative**: Cross-app dependencies increase

### Reversibility

**Reversible but costly.** Can move back to `rentsecure_be/` or `smartbot/`, but effort is high.

### Decision Status

**ACCEPTED** — Leegality integration will be moved to `documents/services/leegality.py`.

---

## ADR-009: Analytics as Independent Bounded Context

**Status:** Accepted
**Owner:** Principal Architect
**Date:** 2026-07-15

### Context

Analytics and reporting logic is scattered:
- `core/services/owner_reporting_service.py` — Owner rent inflow, rent records
- `properties/services/unit_service.py` — Building analytics, owner analytics
- `properties/views/owner_dashboard.py` — Dashboard summary endpoint
- `properties/views/property_views.py` — `unit_analytics` endpoint

### Problem

- **Scattered logic**: Analytics code spread across `core` and `properties`
- **Mixed concerns**: Property management and analytics intermingled
- **Hard to optimize**: Analytics queries not optimized separately
- **Hard to scale**: Analytics queries compete with transactional queries
- **Unclear ownership**: No single team owns analytics

### Decision

**Extract analytics into an independent `analytics/` bounded context.**

The `analytics` app will own:
- `analytics/views/` — Dashboard and analytics endpoints
- `analytics/services/` — Analytics computation and aggregation
- `analytics/serializers/` — Analytics-specific serializers

### Alternatives Considered

1. **Keep Analytics in `properties/`**
   - Pros: No migration effort, property data is co-located
   - Cons: `properties` becomes too large, mixed concerns

2. **Keep Analytics in `core/`**
   - Pros: Owner reporting already there
   - Cons: `core` shouldn't contain property logic

3. **Create Separate Analytics Service**
   - Pros: Independent scaling, deployment
   - Cons: Overkill for current needs, operational complexity

4. **Extract to `analytics/` App**
   - Pros: Clear ownership, can optimize independently
   - Cons: Migration effort, cross-app dependencies

### Pros of Chosen Approach

- **Clear ownership**: Dedicated bounded context for analytics
- **Performance isolation**: Analytics queries can be optimized separately
- **Scalability**: Can extract to separate service later if needed
- **Team autonomy**: Clear ownership for future analytics features
- **Separation of concerns**: Property management ≠ analytics

### Cons of Chosen Approach

- **Migration effort**: Moving analytics code from `core` and `properties`
- **Cross-app dependencies**: `analytics` depends on `properties` and `finance`
- **Additional app**: More apps to maintain

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Performance regression | Low | Medium | Optimize queries, add caching |
| Cross-app dependency issues | Medium | Medium | Define clear interfaces, use dependency injection |
| Underutilization | Medium | Low | Validate analytics requirements with product team |

### Long-term Consequences

- **Positive**: Clear analytics ownership
- **Positive**: Easy to add new analytics features
- **Positive**: Can optimize analytics independently
- **Positive**: Can extract to separate service when needed
- **Negative**: Additional app to maintain
- **Negative**: Cross-app dependencies must be managed

### Reversibility

**Reversible but costly.** Can move analytics back to `properties/` or `core/`, but effort is high.

### Decision Status

**ACCEPTED** — Analytics will be extracted into an independent `analytics/` bounded context.

---

## ADR-010: Payment Gateways Behind Adapters

**Status:** Accepted
**Owner:** Principal Architect
**Date:** 2026-07-15

### Context

Payment gateway code is currently in `rentsecure_be/services/`:
- `razorpay_service.py` — Razorpay integration
- `cashfree_service.py` — Cashfree integration
- `cashfree_payout.py` — Cashfree payout logic

These are imported unconditionally despite feature flags being `False`.

### Problem

- **Tight coupling**: Views directly import payment gateway services
- **Unconditional imports**: Application fails to start if gateway dependencies are missing
- **Hard to test**: Cannot test without gateway credentials
- **Hard to switch**: Adding a new gateway requires touching multiple files
- **Feature flag misuse**: Code is imported even when feature is disabled

### Decision

**Isolate payment gateways behind adapters in a `payments/` bounded context.**

```
payments/
  adapters/
    manual.py          # Manual UPI payment (Year 1)
    razorpay.py        # Razorpay adapter (Stage 2)
    cashfree.py        # Cashfree adapter (Stage 2)
  services/
    payment_service.py # Unified payment interface
  webhooks/
    razorpay_webhook.py
    cashfree_webhook.py
```

All payment code goes through `PaymentService` interface:
```python
class PaymentService:
    def create_payment(self, rent_record: RentRecord) -> PaymentResult: ...
    def process_payout(self, rent_record: RentRecord) -> PayoutResult: ...
    def verify_webhook(self, request: HttpRequest) -> WebhookResult: ...
```

### Alternatives Considered

1. **Keep Current Structure**
   - Pros: No migration effort
   - Cons: Tight coupling, hard to test, feature flag issues

2. **Payment Service in `properties/`**
   - Pros: Close to rent records
   - Cons: `properties` shouldn't know about payment gateways

3. **Payment Microservice**
   - Pros: Independent scaling, deployment
   - Cons: Overkill for Year 1, operational complexity

4. **Adapter Pattern in `payments/`**
   - Pros: Clean separation, easy to test, easy to extend
   - Cons: Migration effort, additional abstraction

### Pros of Chosen Approach

- **Loose coupling**: Views don't know about specific gateways
- **Easy testing**: Can mock adapters for tests
- **Feature flag compliance**: Gateways only imported when needed
- **Easy extension**: New gateways implement same interface
- **Clean architecture**: Payment concerns isolated

### Cons of Chosen Approach

- **Migration effort**: Moving payment code to new app
- **Indirection**: Additional layer between views and gateways
- **Additional app**: More apps to maintain

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Adapter interface too rigid | Low | Medium | Design interface carefully, allow extension points |
| Performance overhead | Low | Low | Direct function calls, no network overhead |
| Migration complexity | Medium | Medium | Phase migration, compatibility wrappers |

### Long-term Consequences

- **Positive**: Clean payment architecture
- **Positive**: Easy to add new payment gateways
- **Positive**: Easy to test payment flows
- **Positive**: Can extract to microservice when needed
- **Negative**: Additional abstraction layer
- **Negative**: Migration effort required

### Reversibility

**Reversible but costly.** Can move adapters back to `rentsecure_be/`, but effort is high.

### Decision Status

**ACCEPTED** — Payment gateways will be isolated behind adapters in `payments/`.

---

## ADR Dependency Graph

```
ADR-001: Modular Monolith
    │
    ├── ADR-002: Bounded Contexts by Business Capability
    │       │
    │       ├── ADR-003: Duplicate Service Consolidation
    │       │       │
    │       │       ├── ADR-004: Compatibility Wrappers
    │       │       │       │
    │       │       │       ├── ADR-005: Assistant Merge
    │       │       │       │       │
    │       │       │       │       ├── ADR-007: PDF Consolidation
    │       │       │       │       │       │
    │       │       │       │       │       └── ADR-008: Leegality in Documents
    │       │       │       │       │
    │       │       │       │       └── ADR-006: Notification Channels
    │       │       │       │               │
    │       │       │       │               └── ADR-009: Analytics Extraction
    │       │       │       │
    │       │       │       └── ADR-010: Payment Adapters
    │       │       │               │
    │       │       │               └── (Stage 2 activation)
    │       │       │
    │       │       └── (Other consolidations)
    │       │
    │       └── (Other bounded context decisions)
    │
    └── (Other architecture decisions)
```

### Dependency Explanation

1. **ADR-001** (Monolith) is the root decision — all other decisions assume a monolith architecture.

2. **ADR-002** (Business Capability Contexts) depends on ADR-001 — bounded contexts only make sense in a monolith.

3. **ADR-003** (Consolidation) depends on ADR-002 — consolidation happens within bounded contexts.

4. **ADR-004** (Compatibility Wrappers) depends on ADR-003 — wrappers are the migration strategy for consolidation.

5. **ADR-005** (Assistant Merge) depends on ADR-004 — merging apps requires compatibility wrappers.

6. **ADR-006** (Notification Channels) depends on ADR-004 — moving notification orchestration requires wrappers.

7. **ADR-007** (PDF Consolidation) depends on ADR-004 — moving PDF generation requires wrappers.

8. **ADR-008** (Leegality in Documents) depends on ADR-007 — Leegality is a document capability, so PDF consolidation must happen first.

9. **ADR-009** (Analytics Extraction) depends on ADR-006 — analytics depends on notification for summary delivery.

10. **ADR-010** (Payment Adapters) depends on ADR-004 — adapter pattern requires compatibility wrappers during migration.

### Critical Path

```
ADR-001 → ADR-002 → ADR-003 → ADR-004 → ADR-005
                                    ├── ADR-006 → ADR-009
                                    ├── ADR-007 → ADR-008
                                    └── ADR-010
```

### Parallelizable Decisions

After ADR-004 is accepted, these can proceed in parallel:
- ADR-005 (Assistant Merge)
- ADR-006 (Notification Channels)
- ADR-007 (PDF Consolidation)
- ADR-010 (Payment Adapters)

### Sequential Dependencies

- ADR-008 (Leegality) must wait for ADR-007 (PDF Consolidation)
- ADR-009 (Analytics) must wait for ADR-006 (Notification Channels)

---

## ADR Summary Table

| ADR | Decision | Reversible? | Implementation Order |
|-----|----------|-------------|---------------------|
| ADR-001 | Remain modular monolith | Partially | 0 (foundational) |
| ADR-002 | Bounded contexts by business capability | Partially | 0 (foundational) |
| ADR-003 | Consolidate duplicates | Yes (during migration) | 1-4 |
| ADR-004 | Use compatibility wrappers | Yes | 0 (foundational) |
| ADR-005 | Merge smartbot + ai_assistant | Partially | 7 |
| ADR-006 | Centralize channels, domain orchestration | Yes | 6 |
| ADR-007 | Consolidate PDF in documents | Yes | 4 |
| ADR-008 | Leegality in documents | Yes | 2 (after 7) |
| ADR-009 | Analytics as independent context | Partially | 8 |
| ADR-010 | Payment gateways behind adapters | Yes | 9 |

---

## Appendix: Decision Principles

These ADRs are guided by the following principles:

1. **Business Capability Over Technical Layer**: Organize by what the business does, not how the code is structured
2. **Gradual Migration Over Big Bang**: Small, reversible changes over risky rewrites
3. **Zero Breaking Changes**: Maintain backward compatibility throughout
4. **Single Source of Truth**: One implementation, one location
5. **Clear Ownership**: One bounded context owns each capability
6. **Future Extensibility**: Design for growth, not just current needs
7. **Operational Simplicity**: Prefer simple solutions that solve today's problems

---

*Report generated by Kilo Architecture Decision Records Phase. All decisions are documented. No production code was modified.*
