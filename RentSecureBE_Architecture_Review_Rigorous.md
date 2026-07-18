# RentSecureBE — Rigorous Architecture Review

**Document:** Rigorous Architecture Review
**Version:** 1.0.0
**Date:** 2026-07-18
**Author:** Principal Software Architect
**Status:** REVIEW — FINDINGS ONLY
**Scope:** Critical, honest assessment of the Modular Monolith Architecture Reference

---

## Review Methodology

This review evaluates `RentSecureBE_Modular_Monolith_Architecture_Review.md` against 20 architectural perspectives. Each finding is rated by severity and assigned a recommended implementation phase. The review is intentionally brutal — no section receives praise unless it is genuinely excellent.

---

## Part 1: Findings by Perspective

### 1. Domain Driven Design

#### Finding 1.1 — Aggregate Boundaries Are Unenforceable as Specified
**Severity:** HIGH
**Why it is a problem:**
- The document lists entities across 12 contexts but never defines **aggregate invariants** or **consistency boundaries**.
- `RentRecord`, `ExtraCharge`, and `RentReminderLog` are listed under Rent Context, but `RentReminderLog` is physically implemented in `properties/models/renter_models.py` and consumed by `notification/`. This is a cross-aggregate ownership violation.
- `PropertyTaxRecord` appears under both Property Context (Section 4.2.3) and Finance Context (Section 4.2.7). An entity cannot belong to two aggregates.
- `NotificationPreference` is listed as an Identity entity (Section 4.2.1) AND a Notification entity (Section 4.2.9). It lives in `core/models.py` in production.
- `ArchivedRenter` is listed as a Renter entity. In DDD, archived state is typically a lifecycle transition of the same aggregate, not a separate aggregate.

**Recommended solution:**
1. Define each aggregate's **invariant list** — the business rules that must be consistent within the aggregate.
2. Assign each entity to exactly one aggregate. `RentReminderLog` belongs to Rent. `PropertyTaxRecord` belongs to Finance (it is a financial record, not a property asset). `NotificationPreference` belongs to Notification.
3. Document **aggregate boundaries** explicitly: which entities are roots, which are owned, and what references cross the boundary.
4. For `ArchivedRenter`, make it a lifecycle state of `Renter` or a separate read model, not an aggregate root.

**Phase:** Phase 1 (design), Phase 2 (enforcement)

---

#### Finding 1.2 — No Anti-Corruption Layer (ACL) Specification
**Severity:** MEDIUM
**Why it is a problem:**
- External providers (Razorpay, Cashfree, Leegality, OpenAI, Twilio) are mentioned but the document never specifies how their models map to domain models.
- Without ACLs, external provider concepts (e.g., `razorpay_payment_id`, `cashfree_beneficiary_id`) will leak into the domain layer.

**Recommended solution:**
- For each external provider, define an ACL module in `payments/infrastructure/adapters/` that translates between provider DTOs and domain value objects.
- Document the mapping explicitly.

**Phase:** Phase 1 (Payments), Phase 2 (others)

---

#### Finding 1.3 — Domain Events Are Defined But Not Versioned
**Severity:** HIGH
**Why it is a problem:**
- Section 7 defines `PaymentInitiated`, `PaymentVerified`, `PayoutProcessed` but provides no versioning strategy.
- When `PaymentInitiated` v2 adds a `payout_id` field, all handlers must be updated simultaneously or the system breaks.
- In a monolith with a single deployment unit, this is manageable but still risky during rolling deployments with multiple workers.

**Recommended solution:**
- Adopt **event versioning by schema evolution**: add new optional fields, never remove or rename required fields.
- Use `pydantic` or `dataclasses` with `field(default=...)` for forward compatibility.
- Document the versioning policy: "Events are backward-compatible within a major version."

**Phase:** Phase 1 (event bus), Phase 2 (formalize)

---

### 2. Clean Architecture

#### Finding 2.1 — Django ORM Leakage Is Not Addressed
**Severity:** HIGH
**Why it is a problem:**
- The document states: "Infrastructure may import Domain" (Section 6.1). But in Django, `models.py` files serve double duty as both Infrastructure (ORM mapping) and Domain (business objects).
- The document does not specify how to prevent Django's `QuerySet`, `Manager`, and ORM-specific methods from leaking into the Domain layer.
- Without explicit guidance, developers will call `.filter()`, `.select_related()`, and `.annotate()` directly in domain services, violating Clean Architecture.

**Recommended solution:**
- Define a strict rule: **Domain layer may only reference Django's `Model` base class, never `QuerySet` or `Manager`.**
- All database queries must go through Repository interfaces defined in `shared_kernel/interfaces/`.
- Repositories in `infrastructure/repositories/` return domain entities, not `QuerySet` objects.
- Use Django's `only()`, `defer()`, `select_related()`, and `prefetch_related()` exclusively inside repository implementations.

**Phase:** Phase 1 (enforce via code review), Phase 2 (add linter rules)

---

#### Finding 2.2 — Application Services Are Ambiguous
**Severity:** MEDIUM
**Why it is a problem:**
- The document defines Application Services but never specifies their interface or lifecycle.
- Are Application Services stateless classes with methods? Are they Django views? Are they management commands?
- Without a clear contract, Application Services will become god objects that mix orchestration, validation, and transaction management.

**Recommended solution:**
- Define the Application Service contract:
  ```python
  class ApplicationService(Protocol):
      def execute(self, input: InputDTO) -> OutputDTO: ...
  ```
- Each method must:
  1. Accept a DTO (no raw `dict` or `request` objects).
  2. Return a `Result[T]` or raise a domain exception.
  3. Be wrapped in a single `transaction.atomic()` block at the Django view level, NOT inside the service.
  4. Never import from `infrastructure/` or `presentation/`.

**Phase:** Phase 1 (define contract), Phase 2 (enforce)

---

#### Finding 2.3 — No Transaction Boundary Specification
**Severity:** HIGH
**Why it is a problem:**
- The document mentions "Within a transaction: Synchronous Application Service call" (Section 17.2) but never defines where transactions start and end.
- In Django, `transaction.atomic()` is typically used in views. If Application Services are called from views, management commands, and event handlers, each caller must remember to wrap in a transaction.
- Without explicit transaction boundaries, partial commits will occur, leading to data inconsistency.

**Recommended solution:**
- Define transaction boundaries at the Presentation layer only:
  - Views: `transaction.atomic()` per request.
  - Management commands: `transaction.atomic()` per command.
  - Event handlers: `transaction.atomic()` per handler.
- Application Services must NEVER call `transaction.atomic()` themselves.
- Document this as a non-negotiable rule.

**Phase:** Phase 1 (document), Phase 2 (enforce via decorator or base class)

---

### 3. Modular Monolith

#### Finding 3.1 — No Module Boundary Enforcement Mechanism
**Severity:** HIGH
**Why it is a problem:**
- The document describes ideal boundaries but provides no enforcement mechanism beyond "import-linter" (mentioned in the analysis document but not in this review).
- The current codebase has 79+ `from core.models import User` violations. Without enforcement, the refactoring will not stick.
- Django's `AppConfig.ready()` and Python's import system make circular imports easy to introduce accidentally.

**Recommended solution:**
- Configure `django-import-linter` with explicit layer rules.
- Add a CI gate that fails if import-linter reports violations.
- Define app-level `__init__.py` files that explicitly export public APIs and hide internal modules.
- Use `import-linter`'s `assert_clean_architecture` with a layered contract:
  - `shared_kernel`: can be imported by anyone.
  - `payments.domain`: can only be imported by `payments.application` and `payments.infrastructure`.
  - `properties.domain`: can only be imported by `properties.application` and `properties.infrastructure`.
  - No app may import another app's `domain/` or `infrastructure/` directly.

**Phase:** Phase 1 (configure), Phase 2 (enforce)

---

#### Finding 3.2 — Context Boundaries Are Overlapping
**Severity:** HIGH
**Why it is a problem:**
- The `core/` app contains Identity AND Subscription entities. These are separate bounded contexts in the document but share a database table namespace.
- `core/views.py` handles auth, subscription, AND webhooks. This is a 566-line god view that violates Single Responsibility.
- The `properties/` app contains Property, Renter, AND Rent entities. The document says these are separate contexts but they share one Django app.

**Recommended solution:**
- In Phase 1, keep `core/` as a combined app for pragmatic reasons BUT enforce internal module boundaries:
  - `core/identity/` module
  - `core/subscription/` module
  - `core/webhooks/` module
- In Phase 2, extract `identity/` and `subscription/` as separate Django apps (not services) within the monolith.
- Similarly, split `properties/` into `properties/`, `renters/`, and `rent/` Django apps within the monolith.

**Phase:** Phase 1 (internal modules), Phase 2 (separate apps)

---

### 4. Shared Kernel

#### Finding 4.1 — Shared Kernel Structure Has Redundancy
**Severity:** MEDIUM
**Why it is a problem:**
- The proposed `shared_kernel/` structure lists both `value_objects/ids/` AND a top-level `ids/` directory.
- It lists both `value_objects/money.py` AND a top-level `money/` directory.
- This duplication creates confusion about where developers should place and import typed IDs and Money values.

**Recommended solution:**
- Choose ONE location for each concept:
  - Typed IDs: `value_objects/ids/` (delete top-level `ids/`).
  - Money: `value_objects/money.py` (delete top-level `money/`).
- Document: "All value objects live under `shared_kernel/value_objects/`. No top-level duplicate directories."

**Phase:** Phase 1 (fix structure)

---

#### Finding 4.2 — Shared Kernel Migration Strategy Is Missing
**Severity:** MEDIUM
**Why it is a problem:**
- The existing `shared/` directory contains `interfaces.py`, `exceptions.py`, `types.py`, `constants.py`, `validators.py`, `utils.py`, `domain_events.py`, `enums.py`.
- The document proposes `shared_kernel/` with a different structure but does not explain how to migrate from `shared/` without breaking existing imports.
- `shared/` is imported by 74+ modules (per the analysis document). A hard cutover will break CI.

**Recommended solution:**
- Phase 1: Create `shared_kernel/` alongside `shared/`. Add a compatibility shim in `shared/__init__.py` that re-exports from `shared_kernel/`.
- Phase 2: Migrate imports context by context. Deprecate `shared/` with warnings.
- Phase 3: Remove `shared/` after all imports are migrated.

**Phase:** Phase 1 (create + shim), Phase 2 (migrate), Phase 3 (remove)

---

#### Finding 4.3 — `utils.py` in Shared Kernel Is a Code Smell
**Severity:** MEDIUM
**Why it is a problem:**
- The existing `shared/utils.py` is a dumping ground for uncategorized functions.
- In Clean Architecture, `utils.py` modules become implicit dependencies that violate layer boundaries.
- The proposed `shared_kernel/` does not include a `utils.py` directory, which is correct, but the migration plan does not address where existing utility functions go.

**Recommended solution:**
- Audit every function in `shared/utils.py`.
- Move functions to their owning context's `infrastructure/utils/` or `shared_kernel/value_objects/` or `shared_kernel/base/`.
- Delete `shared/utils.py` once empty.
- Rule: "No context may import from another context's utils."

**Phase:** Phase 1 (audit), Phase 2 (migrate)

---

### 5. Event Architecture

#### Finding 5.1 — No Outbox Pattern for Event Durability
**Severity:** MEDIUM
**Why it is a problem:**
- The in-process event bus (Section 7.2) publishes events synchronously within a transaction.
- If an event handler raises an exception after the transaction commits, the event is lost.
- If an event handler raises an exception before the transaction commits, the entire transaction rolls back — which may be correct, but it couples event handling to the main transaction.
- There is no persistence of events for replay or audit.

**Recommended solution:**
- For Phase 1, accept the synchronous, in-process bus as pragmatic. Document its limitations.
- For Phase 3 (or when async background processing is needed), implement an **outbox pattern**:
  - Events are written to an `outbox` table in the same transaction as the domain change.
  - A background worker (management command or Celery task) reads the outbox and dispatches events.
- This provides durability without requiring Kafka or Redis Streams.

**Phase:** Phase 1 (document limitation), Phase 3 (outbox)

---

#### Finding 5.2 — Event Handler Failure Behavior Is Undefined
**Severity:** MEDIUM
**Why it is a problem:**
- The event bus publishes to all handlers in a loop. If handler A succeeds and handler B fails, the system is in an inconsistent state.
- No retry policy, dead-letter queue, or failure isolation is defined.

**Recommended solution:**
- Define handler contract: "Event handlers must be idempotent. A failed handler does not roll back the event publication for other handlers."
- Implement a try/except wrapper in the event bus that logs failures and continues.
- For critical events (payment, notification), use a dead-letter pattern or manual retry.

**Phase:** Phase 1 (implement wrapper), Phase 2 (add dead-letter)

---

#### Finding 5.3 — Django Signals Migration Plan Is Too Vague
**Severity:** LOW
**Why it is a problem:**
- Section 7.3 says "Identify all signal senders/receivers. Convert to explicit Domain Events." But the current codebase has 12+ signal receivers in `properties/signals/__init__.py` and `core/signals.py`.
- No timeline or prioritization is given.

**Recommended solution:**
- In Phase 1, add a `signals/` directory inside each context's `infrastructure/` layer to isolate Django-specific signal wiring.
- In Phase 2, convert high-value signals (renter lifecycle, payment events) to domain events.
- In Phase 3, remove remaining Django signals.

**Phase:** Phase 1 (isolate), Phase 2 (convert critical), Phase 3 (remove rest)

---

### 6. Repository Pattern

#### Finding 6.1 — Repository Pattern Adds Unnecessary Abstraction in Django
**Severity:** MEDIUM
**Why it is a problem:**
- The document recommends "Add Repository Pattern" (Section 16.1, item 10) as HIGH priority.
- Django's ORM is already a repository pattern. Wrapping it in another repository interface adds boilerplate without measurable benefit in a monolith.
- The current code has `repositories/` directories that are "minimal" (per the analysis document), which suggests they were added because the architecture demanded them, not because they provided value.

**Recommended solution:**
- **Do NOT mandate repositories for all aggregates in Phase 1.**
- Use Django ORM directly in Application Services for simple CRUD.
- Introduce repository interfaces ONLY when:
  - The aggregate has complex query logic that would otherwise leak into Application Services.
  - The aggregate needs to be swapped for a different data source (e.g., external API, read model).
  - Testing requires mocking data access.
- For Payment, Document, and Dashboard contexts (which have complex querying or external dependencies), repositories are justified.
- For simple CRUD contexts (Renter, Unit, Caretaker), skip repositories initially.

**Phase:** Phase 1 (selective use), Phase 2 (expand as needed)

---

#### Finding 6.2 — Generic Repository Anti-Pattern Risk
**Severity:** MEDIUM
**Why it is a problem:**
- The shared_kernel proposes `BaseRepository` interface (Section 5.1). If this becomes a generic `get_all()`, `get_by_id()`, `save()`, `delete()` interface, it will violate the Repository pattern's purpose (encapsulate aggregate-specific queries).
- Generic repositories leak query capabilities through a common interface, making it impossible to change an aggregate's storage without changing callers.

**Recommended solution:**
- Define repository interfaces per aggregate, not generically:
  ```python
  class RentRecordRepository(Protocol):
      def find_by_renter_and_month(self, renter_id: RenterId, year: int, month: int) -> RentRecord | None: ...
      def find_overdue_for_owner(self, owner_id: UserId) -> list[RentRecord]: ...
  ```
- Do NOT create a `BaseRepository` with generic CRUD methods unless it is purely internal to one context.

**Phase:** Phase 1 (design), Phase 2 (enforce)

---

### 7. CQRS

#### Finding 7.1 — CQRS Is Recommended and Simultaneously Rejected
**Severity:** MEDIUM
**Why it is a problem:**
- Section 9.1 shows `dashboard/infrastructure/read_models/materialized_views.py` in the proposed structure. This IS CQRS.
- Section 9.2 says "Do NOT introduce CQRS read models unless analytics complexity justifies it."
- The document contradicts itself: the proposed structure already includes CQRS patterns.

**Recommended solution:**
- Remove `read_models/` and `materialized_views.py` from the proposed dashboard structure if CQRS is not recommended.
- OR, explicitly state that materialized views are a database optimization, not CQRS, and keep them out of the application layer.
- If CQRS is ever introduced, define clear triggers and a separate migration phase.

**Phase:** Phase 1 (fix inconsistency)

---

### 8. Dashboard

#### Finding 8.1 — Dashboard Context Has Undefined Data Ownership
**Severity:** HIGH
**Why it is a problem:**
- The Dashboard context depends on Rent, Property, Finance, and Notification contexts (Section 4.2.12).
- If Dashboard queries these contexts directly, it creates coupling.
- The document does not specify whether Dashboard owns its own read models, subscribes to events, or queries other contexts synchronously.

**Recommended solution:**
- Dashboard must own its read models explicitly.
- Data flows INTO Dashboard via:
  - **Option A (Phase 1):** Direct queries with read replicas. Acceptable for monolith.
  - **Option B (Phase 3):** Materialized views refreshed on a schedule.
  - **Option C (Phase 3):** Domain events that update dashboard-specific tables.
- Dashboard must NEVER hold transactions open across contexts.

**Phase:** Phase 1 (Option A), Phase 3 (Option B/C)

---

#### Finding 8.2 — No Analytics Query Optimization Strategy
**Severity:** MEDIUM
**Why it is a problem:**
- The document mentions "optimized Django queries" but does not specify which optimizations.
- Dashboard queries typically involve GROUP BY, date truncation, and multi-table joins. Without specific guidance, these queries will be slow and cause N+1 problems.

**Recommended solution:**
- Document specific Django optimizations for analytics:
  - `TruncMonth`, `TruncDay` for time-series aggregation.
  - `conditional aggregation` with `Case/When` instead of Python loops.
  - `values()` + `annotate()` for grouped results.
  - Database indexes on date fields and foreign keys used in dashboard queries.
- Add a `dashboard/` query style guide.

**Phase:** Phase 1 (guide), Phase 2 (implement indexes)

---

### 9. Payments

#### Finding 9.1 — Feature Flags Are Swapped and Misnamed
**Severity:** CRITICAL
**Why it is a problem:**
- Section 8.3 table:
  - `RAZORPAY_PAYMENTS_ENABLED` row says "Cashfree integration"
  - `CASHFREE_PAYMENTS_ENABLED` row says "Razorpay integration"
- The actual settings.py (line 90-91) uses `ENABLE_RAZORPAY` and `ENABLE_CASHFREE`.
- If a developer follows the architecture document, they will enable the wrong gateway or disable both.

**Recommended solution:**
- Correct the table immediately:
  - `RAZORPAY_PAYMENTS_ENABLED = False` → "Razorpay integration"
  - `CASHFREE_PAYMENTS_ENABLED = False` → "Cashfree integration"
- Align flag names with `settings.py`: either rename to `ENABLE_RAZORPAY`/`ENABLE_CASHFREE` or update settings to match the document.
- Add a validation test that asserts flag names match between docs and code.

**Phase:** Phase 1 (fix immediately)

---

#### Finding 9.2 — Manual UPI Does Not Fit the PaymentGateway Abstraction
**Severity:** HIGH
**Why it is a problem:**
- The `PaymentGateway` interface (Section 8.2) defines `initiate_payment`, `verify_payment`, `create_payout`.
- Manual UPI does not "initiate" a payment programmatically. The owner provides a QR code; the tenant pays externally. There is no API call to initiate.
- Forcing Manual UPI into the same interface as Razorpay/Cashfree creates a leaky abstraction.

**Recommended solution:**
- Split the abstraction:
  - `PaymentGateway` (for online gateways: Razorpay, Cashfree, Stripe).
  - `ManualPaymentFlow` (for UPI, bank transfer): a separate interface with `generate_utr_verification_request`, `verify_utr`, `record_manual_payment`.
- Or, make `PaymentGateway.initiate_payment` return a payment instruction object (QR code, UPI ID, bank details) rather than assuming an API call.

**Phase:** Phase 1 (fix abstraction)

---

#### Finding 9.3 — No Payment State Machine
**Severity:** HIGH
**Why it is a problem:**
- `PaymentStatus` is listed as a value object (pending, completed, failed, cancelled) but no state transitions are defined.
- What transitions are valid? Can a payment go from `pending` → `failed` → `completed`? Can it go from `completed` → `cancelled`?
- Without a state machine, invalid transitions will occur (e.g., approving an already-cancelled payment).

**Recommended solution:**
- Define a state machine for `PaymentTransaction`:
  ```
  pending → completed (verified)
  pending → failed (gateway error / UTR mismatch)
  pending → cancelled (owner rejection)
  completed → refunded (if refunds are supported)
  ```
- Implement as a method on the entity: `payment_transition.transition_to(new_status)` that validates the transition.
- Document allowed transitions in the domain model.

**Phase:** Phase 1 (design), Phase 2 (implement)

---

#### Finding 9.4 — Webhook Handling Is Underspecified
**Severity:** MEDIUM
**Why it is a problem:**
- Section 8.1 lists webhook endpoints but does not discuss:
  - Signature verification (Razorpay, Cashfree)
  - Idempotency (handling duplicate webhook deliveries)
  - Retry logic (what to do when the webhook handler fails)
  - Async processing (webhooks should not block the provider)

**Recommended solution:**
- All webhook handlers must:
  1. Verify signature immediately (before any processing).
  2. Check an idempotency key (webhook `id` or `reference_id`) stored in the database. Return 200 OK if already processed.
  3. Return 200 OK immediately. Process the event asynchronously via the outbox or a management command.
  4. Never raise unhandled exceptions (return 200 to prevent provider retries).

**Phase:** Phase 1 (implement for existing webhooks), Phase 2 (add outbox)

---

#### Finding 9.5 — No Payment Reconciliation Strategy
**Severity:** MEDIUM
**Why it is a problem:**
- Manual UPI payments require the owner to verify UTR numbers against their bank statement.
- The document does not mention how owners reconcile payments or how the system helps them.
- For automated gateways (Razorpay, Cashfree), settlement reports are needed.

**Recommended solution:**
- Add a `ReconciliationReport` entity in the Payments context.
- Provide owner-facing endpoints to:
  - View pending UTR verifications.
  - Bulk approve/reject manual payments.
  - Download settlement reports for automated gateways.
- For Year 1, manual reconciliation via the dashboard is sufficient.

**Phase:** Phase 1 (manual reconciliation UI), Phase 2 (automated reports)

---

### 10. AI Context

#### Finding 10.1 — Document Incorrectly States `ai_assistant/` Is Empty
**Severity:** CRITICAL
**Why it is a problem:**
- Section 4.2.10, Section 6.1.8, and Section 10.1 all claim `ai_assistant/` is empty.
- Actual code shows `ai_assistant/` has:
  - `views.py` (with real endpoints)
  - `services/finance_ai.py`
  - `services/invoice_service.py`
  - `services/i18n_service.py`
  - `services/archive_service.py`
  - `services/unit_service.py`
  - `receivers.py`
  - `apps.py`
  - `tests/test_services.py`
- Recommending deletion of `ai_assistant/` would destroy production functionality.

**Recommended solution:**
- Update the document immediately to reflect reality.
- `ai_assistant/` is NOT empty. It contains AI functionality that overlaps with `smartbot/`.
- The correct recommendation is: **Consolidate `ai_assistant/` into `smartbot/` by migrating its functionality, then delete the duplicate app.**
- Do NOT delete `ai_assistant/` without first moving its code.

**Phase:** Phase 1 (correct doc, plan migration)

---

#### Finding 10.2 — AI Action Dispatch Has No Safety Guardrails
**Severity:** HIGH
**Why it is a problem:**
- Section 4.2.10 says SmartBot can dispatch actions like "create rent record" and "send notification."
- There is no specification of:
  - Which actions are allowed (allow-list)?
  - Who can trigger actions (owner, renter, both)?
  - What confirmation is required before destructive actions?
  - How actions are audited?
- Without guardrails, a misconfigured GPT prompt could create duplicate rent records or send unauthorized notifications.

**Recommended solution:**
- Define an explicit `ActionDispatcher` interface with an allow-list of actions.
- Each action requires:
  - Permission check (can the user perform this action manually?).
  - Confirmation for destructive actions (delete, send, approve).
  - Audit log entry.
- AI-generated actions are treated as "suggestions" requiring explicit user confirmation, not automatic execution.

**Phase:** Phase 1 (design guardrails), Phase 2 (implement)

---

#### Finding 10.3 — No Cost Control for OpenAI
**Severity:** MEDIUM
**Why it is a problem:**
- OpenAI API costs are usage-based. Without rate limiting or cost controls, a runaway chatbot conversation could exhaust the API budget.
- The document does not mention cost monitoring or rate limiting for AI features.

**Recommended solution:**
- Add per-user and per-tenant rate limits for OpenAI calls.
- Cache common responses (FAQ answers) to reduce API calls.
- Set a monthly budget cap per tenant and disable AI features when exceeded.
- Log all OpenAI calls with token counts for cost tracking.

**Phase:** Phase 1 (rate limits), Phase 2 (budget caps)

---

### 11. Search

#### Finding 11.1 — Search Strategy Is Too Vague
**Severity:** LOW
**Why it is a problem:**
- Section 11.4 says "Use PostgreSQL full-text search with trigram indexes" but does not specify how.
- How are search queries constructed? How are results ranked? How is search across multiple models handled?
- Django's `SearchVector` and `SearchQuery` are not mentioned.

**Recommended solution:**
- Document the PostgreSQL full-text search implementation:
  - Use `SearchVector` on relevant fields (`name`, `address`, `phone`).
  - Use `SearchRank` for relevance ordering.
  - Create a `SearchIndex` model or use database views for cross-entity search.
- If search becomes a requirement, use `django.contrib.postgres.search`.

**Phase:** Phase 3 (when needed)

---

### 12. Storage

#### Finding 12.1 — File Upload Security Is Not Addressed
**Severity:** HIGH
**Why it is a problem:**
- The Storage context (Section 11.2) mentions S3 and CDN but does not address:
  - File type validation (prevent executable uploads).
  - File size limits.
  - Virus scanning (ClamAV or AWS Inspector).
  - Signed URL expiration.
- Without these, the system is vulnerable to malicious uploads.

**Recommended solution:**
- Validate file types on upload (allow-list: images, PDFs, documents).
- Enforce file size limits at the application level.
- Use pre-signed S3 URLs with short expiration (5-15 minutes).
- For PDFs and documents, consider server-side virus scanning before storage.
- Document these as non-negotiable security requirements.

**Phase:** Phase 1 (validation + limits), Phase 2 (virus scanning)

---

#### Finding 12.2 — Image Processing Is Not Mentioned
**Severity:** LOW
**Why it is a problem:**
- Unit images and document scans will need thumbnails, compression, and format conversion.
- The document does not mention image processing strategy.

**Recommended solution:**
- Use `Pillow` for client-side image processing (resize, compress, convert to WebP).
- Generate thumbnails on upload.
- Store only processed images in S3.
- This is a Phase 2 optimization; raw uploads work for Phase 1.

**Phase:** Phase 2

---

### 13. Documents

#### Finding 13.1 — Document Entity Is Too Generic
**Severity:** MEDIUM
**Why it is a problem:**
- Section 4.2.8 defines `Document` as an aggregate root with `DocumentType` (receipt, agreement, invoice, dossier).
- But `RentReceipt`, `RentAgreement`, and `Invoice` have very different lifecycles, storage requirements, and access patterns.
- A generic `Document` entity will accumulate conditional logic for each type.

**Recommended solution:**
- Use **discriminated unions** or separate entities for each document type:
  - `RentReceipt` — generated after payment, immutable, emailed to tenant.
  - `RentAgreement` — generated during onboarding, mutable until signed, requires e-signature.
  - `Invoice` — generated monthly, contains line items, may be regenerated.
- Keep `Document` as a base class or abstract model only if Django's model inheritance is used; otherwise, separate entities are cleaner.

**Phase:** Phase 2 (refine after payments context is stable)

---

#### Finding 13.2 — No Template Versioning
**Severity:** LOW
**Why it is a problem:**
- Section 4.2.8 mentions "Template management" but does not address template versioning.
- When a rent receipt template is updated, old receipts should not change. This requires versioned templates.

**Recommended solution:**
- `DocumentTemplate` has a `version` field and a `is_active` flag.
- When generating a document, the template version at generation time is stored with the document.
- This ensures historical documents remain unchanged.

**Phase:** Phase 2

---

### 14. Notifications

#### Finding 14.1 — NotificationPreference Is in the Wrong Context
**Severity:** HIGH
**Why it is a problem:**
- `NotificationPreference` is currently in `core/models.py` (Identity context).
- It is listed as an Identity entity (Section 4.2.1) AND a Notification entity (Section 4.2.9).
- Notification preferences control how and when notifications are sent. They are part of the Notification domain, not Identity.
- This is a domain modeling error that will cause coupling.

**Recommended solution:**
- Move `NotificationPreference` to the Notification context in Phase 1.
- Identity context references the user; Notification context owns the preferences.
- Update all references from `core.models.NotificationPreference` to `notification.models.NotificationPreference`.

**Phase:** Phase 1

---

#### Finding 14.2 — Notification Deduplication Is Not Specified
**Severity:** MEDIUM
**Why it is a problem:**
- Multiple signal handlers can trigger the same notification (e.g., `rent_record_views.py` and `rent_notify_service.py` both send WhatsApp messages for rent).
- The document does not specify how duplicate notifications are prevented.

**Recommended solution:**
- Add a `Notification` entity with a unique constraint on `(user, notification_type, related_object_id, created_at__date)`.
- Before creating a notification, check if one already exists for the same user/type/object within a deduplication window (e.g., 24 hours).
- This prevents signal storms from spamming users.

**Phase:** Phase 1

---

#### Finding 14.3 — Notification Channels Are Not Isolated Enough
**Severity:** MEDIUM
**Why it is a problem:**
- `notification/services/` contains `rent_notify_service.py`, `whatsapp_service.py`, `voice_service.py`, `sms_service.py`, `communication.py`, `extra_charge_reminders.py`, `late_fees_notify_service.py`, `schedule_reminders.py`, `services.py`.
- This is a "fat context" with business logic for specific domains (rent reminders, extra charge reminders, late fees) embedded in the notification app.
- Notification should dispatch generic messages; the **content** of rent reminders belongs in the Rent context.

**Recommended solution:**
- Notification context provides: `NotificationChannel` interface, `NotificationDispatchService`, `NotificationTemplate` management.
- Rent context defines: `RentReminderMessage` (content, template, timing).
- Rent context publishes a `RentReminderDue` event. Notification context subscribes and dispatches via the appropriate channel.
- Remove `rent_notify_service.py`, `extra_charge_reminders.py`, `late_fees_notify_service.py` from notification/ and move them to their owning contexts or delete them (they become event handlers).

**Phase:** Phase 2

---

### 15. Audit

#### Finding 15.1 — Audit Context Recommendation Is Good but Incomplete
**Severity:** LOW
**Why it is not a problem (but incomplete):**
- Section 11.1 recommends an Audit context in Phase 2. This is correct.
- However, it does not specify the implementation mechanism.
- Django signals can capture many actions, but they are not sufficient for all audit trails (e.g., model deletions are not captured by `post_save`).

**Recommended solution:**
- Use Django's built-in `LogEntry` for admin actions (it is already enabled).
- For business actions, use domain events with an `AuditLog` handler that persists to an `audit_log` table.
- For model deletions, use `post_delete` signals or override `Model.delete()`.
- Document the audit log schema: `user, action, entity_type, entity_id, changes, timestamp, ip_address`.

**Phase:** Phase 2

---

### 16. Security

#### Finding 16.1 — OTP Brute-Force Protection Is Not Specified
**Severity:** HIGH
**Why it is a problem:**
- Section 4.2.1 mentions OTP authentication but does not mention rate limiting or brute-force protection.
- An attacker can request unlimited OTPs, exhausting Twilio quota or spamming users.
- The document mentions `OTPService` with "rate limiting" but does not specify the implementation.

**Recommended solution:**
- Implement rate limiting in the OTP flow:
  - Max 3 OTP requests per phone number per 15 minutes.
  - Max 5 verification attempts per OTP.
  - Exponential backoff after failed attempts.
- Store rate limit state in Redis (Phase 2) or cache (Phase 1 with LocMemCache, noting it is per-process).
- Add CAPTCHA after repeated failures.

**Phase:** Phase 1 (basic rate limit), Phase 2 (Redis-backed)

---

#### Finding 16.2 — JWT Token Revocation Is Not Addressed
**Severity:** MEDIUM
**Why it is a problem:**
- SimpleJWT is used (Section 2.2) but the document does not mention token revocation or blacklisting.
- If a user's password is changed or they are banned, existing JWTs remain valid until expiration.
- SimpleJWT supports token blacklisting but it requires Redis.

**Recommended solution:**
- Add `TokenBlacklist` app from SimpleJWT's recommended setup.
- In Phase 1, use short-lived access tokens (15 minutes) and long refresh tokens (7 days).
- In Phase 2, enable Redis-backed token blacklisting for logout and password change flows.
- Document the trade-off: blacklisting adds Redis dependency; short tokens reduce the window of vulnerability.

**Phase:** Phase 1 (short tokens), Phase 2 (blacklist)

---

#### Finding 16.3 — Webhook Security Is Mentioned But Not Specified
**Severity:** HIGH
**Why it is a problem:**
- Section 8.4 says "All payment flows must be idempotent. Webhooks must support retries."
- But Section 12.1 says "Fix Razorpay webhook security — Add signature verification" as a Phase 1 task.
- The current `core/views.py` handles webhooks. The document does not show the current implementation or specify what signature verification looks like.

**Recommended solution:**
- For each webhook provider, document the exact signature verification algorithm:
  - Razorpay: ` razorpay_webhook_secret` + HMAC-SHA256.
  - Cashfree: `CASHFREE_WEBHOOK_SECRET` + HMAC-SHA256.
  - Leegality: `LEEGALITY_WEBHOOK_SECRET` + HMAC-SHA256.
- Add a reusable `WebhookVerificationMixin` or decorator.
- Add tests that verify signature verification works and rejects tampered payloads.

**Phase:** Phase 1 (implement)

---

#### Finding 16.4 — No Discussion of Secrets Management
**Severity:** MEDIUM
**Why it is a problem:**
- Settings.py (lines 65-84) defines API keys, secrets, and credentials.
- The document does not mention how these are stored in production (environment variables? AWS Secrets Manager? Parameter Store?).
- The current code uses `python-decouple` which reads from `.env` files. This is acceptable for Year 1 but should be documented.

**Recommended solution:**
- Document the secrets management strategy:
  - Development: `.env` file (git-ignored).
  - Production: AWS Systems Manager Parameter Store or environment variables set by ECS/EKS task definition.
- Never commit secrets to version control.
- Rotate secrets quarterly.

**Phase:** Phase 1 (document), Phase 2 (SSM Parameter Store)

---

### 17. Testing

#### Finding 17.1 — No Test Strategy for Domain Layer
**Severity:** MEDIUM
**Why it is a problem:**
- Section 17.5 mentions "Unit tests per context (domain layer)" but the document does not explain how to unit test domain entities without Django's test framework.
- Django's `TestCase` wraps each test in a transaction and uses the test database. This is slow for domain logic tests.
- Without a clear strategy, domain tests will either not exist or will be integration tests that are slow and brittle.

**Recommended solution:**
- Domain layer tests must NOT depend on Django's database.
- Use `pytest` with `pytest-django` for integration tests.
- Use plain `unittest` or `pytest` for pure domain logic tests (entities, value objects, domain services).
- Define a test directory structure:
  - `tests/unit/domain/` — pure domain tests, no database.
  - `tests/unit/application/` — application service tests with mocked repositories.
  - `tests/integration/` — Django test cases with database.

**Phase:** Phase 1 (setup), Phase 2 (enforce)

---

#### Finding 17.2 — No Contract Testing Between Contexts
**Severity:** LOW
**Why it is a problem:**
- When contexts communicate via events or application services, there is no contract test to ensure the consumer's expectations match the producer's output.
- This is a minor issue in a monolith where changes are deployed together, but it becomes critical before service extraction.

**Recommended solution:**
- For Phase 1-2, rely on integration tests.
- For Phase 4 (service extraction), add contract tests using Pact or Schemathesis.

**Phase:** Phase 4 (if/when services are extracted)

---

### 18. Scalability

#### Finding 18.1 — Gunicorn Configuration Is Not Specified
**Severity:** LOW
**Why it is a problem:**
- Section 15.2 says "Gunicorn with 4 workers" but does not specify the worker class, timeout, or worker connections.
- For Django, `gthread` or `gevent` workers are typically better than sync workers for I/O-bound workloads (API calls to external services).

**Recommended solution:**
- Specify Gunicorn configuration:
  - Worker class: `gthread` (for I/O-bound) or `gevent` (if websockets are needed).
  - Workers: `2 * CPU cores + 1` (not a fixed 4).
  - Timeout: 60 seconds (with health checks to detect hung workers).
  - Max requests: 1000 (to prevent memory leaks).
  - Preload app: `True` (to reduce memory usage).

**Phase:** Phase 1 (configure)

---

#### Finding 18.2 — Database Connection Pooling Is Missing
**Severity:** MEDIUM
**Why it is a problem:**
- Section 15.1 mentions PgBouncer as a Phase 2 task but does not explain why.
- Django opens a new database connection per request by default. With Gunicorn's multiple workers and long-running management commands, connection exhaustion is a real risk.
- The default `CONN_MAX_AGE = 0` closes connections after each request, which is safe but adds latency.

**Recommended solution:**
- Set `CONN_MAX_AGE = 60` in Phase 1 to enable persistent connections.
- In Phase 2, add PgBouncer in transaction-pooling mode when connection count exceeds 20-30.
- Monitor `pg_stat_activity` to track connection usage.

**Phase:** Phase 1 (CONN_MAX_AGE), Phase 2 (PgBouncer)

---

#### Finding 18.3 — No Health Check or Readiness Probe Specification
**Severity:** MEDIUM
**Why it is a problem:**
- For Phase 4 horizontal scaling, health checks are essential. But even in Phase 1, a health check endpoint helps with monitoring and deployment verification.
- The document does not mention health checks.

**Recommended solution:**
- Add `/health/` and `/health/ready/` endpoints:
  - `/health/` — returns 200 if Django is running.
  - `/health/ready/` — checks database connectivity, S3 connectivity, cache connectivity.
- Use `django-health-check` or implement a simple view.

**Phase:** Phase 1

---

### 19. Operational Cost

#### Finding 19.1 — Cost Estimates Are Unrealistic for Production
**Severity:** MEDIUM
**Why it is a problem:**
- Section 12.3 estimates ₹1,500–2,500/month for "EC2 (t3.small) or ECS Fargate, RDS PostgreSQL (db.t3.micro), S3, CloudFront."
- In AWS India, a `t3.small` EC2 instance costs ~₹1,200/month. A `db.t3.micro` RDS instance costs ~₹1,500/month. S3 + CloudFront + data transfer can easily add another ₹1,000-2,000/month.
- The estimate does not account for data transfer costs, S3 GET requests, or CloudFront data transfer.
- ECS Fargate is significantly more expensive than EC2 for consistent workloads.

**Recommended solution:**
- Provide realistic cost estimates:
  - EC2 `t3.small` + RDS `db.t3.micro` + S3: ~₹3,000–4,000/month minimum.
  - AWS Free Tier covers `t2.micro` or `t3.micro` for 12 months only.
  - After Free Tier, realistic production cost is ₹4,000–6,000/month for low traffic.
- If the budget is strictly ₹2,000–3,000/month, recommend:
  - EC2 `t3.micro` (or Free Tier if eligible).
  - SQLite for development, PostgreSQL only for production with minimal traffic.
  - No CloudFront (serve media via Nginx on EC2).
  - No RDS (run PostgreSQL on EC2).

**Phase:** Phase 1 (realistic planning)

---

#### Finding 19.2 — No Cost Monitoring Strategy
**Severity:** LOW
**Why it is a problem:**
- The document does not mention AWS Budgets, cost alerts, or resource tagging.
- Without monitoring, a runaway process or storage leak could exceed the budget silently.

**Recommended solution:**
- Set up AWS Budgets with alerts at 50%, 80%, and 100% of monthly budget.
- Tag all resources with `Project=RentSecure` and `Environment=production`.
- Enable S3 storage class analytics to move old files to Infrequent Access.

**Phase:** Phase 1

---

### 20. Long-term Maintainability

#### Finding 20.1 — No Dependency Management Strategy
**Severity:** MEDIUM
**Why it is a problem:**
- The document does not mention how Python dependencies are managed (Poetry, Pipenv, requirements.txt?).
- It does not mention dependency updates, security patches, or deprecation policies.
- Django 4.2 LTS is current but will reach end-of-life. Django 5.x LTS is the future target.

**Recommended solution:**
- Use `uv` or `pip` with a locked `requirements.txt` (or `poetry.lock`).
- Enable Dependabot or Renovate for automated dependency updates.
- Document the Django upgrade path: 4.2 LTS → 5.2 LTS → 6.x LTS.
- Set a policy: "Upgrade minor versions monthly, major versions quarterly."

**Phase:** Phase 1 (document), Phase 2 (automate)

---

#### Finding 20.2 — No Deprecation Policy
**Severity:** LOW
**Why it is a problem:**
- The document mentions "deprecate `shared/`" but does not define a deprecation policy.
- How long does old code remain supported? How are deprecation warnings communicated to the team?

**Recommended solution:**
- Define a deprecation policy:
  - Mark deprecated code with `warnings.warn(..., DeprecationWarning, stacklevel=2)`.
  - Remove deprecated code after 2 minor versions or 6 months.
  - Document all deprecations in a `CHANGELOG.md`.

**Phase:** Phase 1 (document), Phase 2 (enforce)

---

## Part 2: Section-by-Section Verdict

### What Is Excellent (No Changes Recommended)

| Section | Why It Is Excellent |
|---------|---------------------|
| **Phase 4 Trigger Conditions** (Section 13) | The explicit trigger conditions for service extraction are measurable, objective, and aligned with business reality. This is the strongest part of the document. |
| **Infrastructure "Do NOT Introduce" Table** (Section 12.2) | Correctly identifies Kubernetes, Kafka, and Event Sourcing as premature. The "When It Might Be Justified" column provides objective thresholds. |
| **Budget-Conscious Deployment** (Section 12.3) | Pragmatic Year 1 deployment with realistic stack choices. |
| **Premature Microservices Risks** (Section 19) | Excellent breakdown of operational, cost, and organizational risks. |
| **Modular Monolith Best Practices** (Section 17) | Concise, actionable rules for module boundaries, deployment, and testing. |

### What Needs Correction

| Section | Issue | Severity |
|---------|-------|----------|
| **8.3 Feature Flags** | Swapped descriptions for Razorpay/Cashfree flags | CRITICAL |
| **4.2.10 AI Context** | Incorrectly claims `ai_assistant/` is empty | CRITICAL |
| **4.2.1 / 4.2.9** | `NotificationPreference` listed in both Identity and Notification | HIGH |
| **4.2.4 / 4.2.5** | `RentReminderLog` listed in both Renter and Rent | HIGH |
| **4.2.3 / 4.2.7** | `PropertyTaxRecord` listed in both Property and Finance | HIGH |
| **5.1 Shared Kernel** | Duplicate `ids/` and `money/` directories | MEDIUM |
| **9.1 / 9.2** | Dashboard structure includes CQRS read models while CQRS is rejected | MEDIUM |
| **9.2 Manual UPI** | Manual UPI forced into `PaymentGateway` interface designed for online gateways | HIGH |
| **8.4 Webhooks** | No specification of signature verification, idempotency, or async processing | HIGH |
| **17.2 Shared Kernel** | No migration strategy from existing `shared/` | MEDIUM |

### What Is Missing

| Topic | Where It Should Be | Severity |
|-------|-------------------|----------|
| Transaction boundary specification | Section 6 or 17 | HIGH |
| Django ORM leakage prevention | Section 6 | HIGH |
| Aggregate invariants | Section 4 | HIGH |
| Payment state machine | Section 8 | HIGH |
| AI action guardrails | Section 10 | HIGH |
| OTP brute-force protection | Section 4.2.1 or 16 | HIGH |
| File upload security | Section 11.2 or 12 | HIGH |
| JWT token revocation | Section 4.2.1 or 16 | MEDIUM |
| Secrets management | Section 12 | MEDIUM |
| Event versioning | Section 7 | HIGH |
| Event handler failure behavior | Section 7 | MEDIUM |
| Gunicorn configuration | Section 15 | LOW |
| Health checks | Section 15 or 12 | MEDIUM |
| Cost monitoring | Section 12 | LOW |
| Dependency management | Section 12 or 17 | MEDIUM |
| Test strategy for domain layer | Section 17 | MEDIUM |
| Payment reconciliation | Section 8 | MEDIUM |
| Notification deduplication | Section 4.2.9 | MEDIUM |
| Notification channel isolation | Section 4.2.9 | MEDIUM |
| Anti-corruption layers | Section 8 or new section | MEDIUM |
| Repository per aggregate vs generic | Section 6 | MEDIUM |
| Materialized views vs CQRS | Section 9 | MEDIUM |

---

## Part 3: Scores

### 1. Overall Architecture Score: **6.5 / 10**

The document provides a solid foundation but contains critical factual errors, internal contradictions, and missing specifications that would cause implementation failures if followed literally.

### 2. DDD Score: **5 / 10**
- **Strengths:** 12 bounded contexts are identified with clear responsibilities.
- **Weaknesses:** Aggregate boundaries are undefined and contradictory (entities appear in multiple contexts). No invariants, no state machines, no ACLs. `NotificationPreference` and `PropertyTaxRecord` are placed in the wrong contexts.

### 3. Clean Architecture Score: **5 / 10**
- **Strengths:** Layer ordering is correctly stated. Dependencies point inward in theory.
- **Weaknesses:** Django ORM leakage is not addressed. Transaction boundaries are undefined. Application Service contract is missing. Repository pattern is mandated without explaining why or when it adds value.

### 4. Maintainability Score: **5 / 10**
- **Strengths:** Clear phase plan. Good prioritization of Phase 1 tasks.
- **Weaknesses:** Critical feature flag swap would cause production incidents. `ai_assistant/` deletion recommendation would destroy functionality. No deprecation policy. No dependency management strategy.

### 5. Scalability Score: **6 / 10**
- **Strengths:** Correctly defers Kubernetes, Kafka, and microservices. PostgreSQL read replicas are the right choice.
- **Weaknesses:** Gunicorn configuration is unspecified. Database connection pooling is deferred too long. Health checks are missing. Cost estimates are unrealistic.

### 6. Operational Simplicity Score: **7 / 10**
- **Strengths:** Single deployable unit. Year 1 stack is simple (EC2 + RDS + S3). No Kubernetes, no Kafka.
- **Weaknesses:** Celery + Redis is introduced in Phase 2 without clear justification (management commands + crontab may be sufficient for longer).

### 7. Cost Efficiency Score: **6 / 10**
- **Strengths:** Correctly avoids expensive technologies. Year 1 budget target is reasonable in intent.
- **Weaknesses:** Cost estimates are too low. No cost monitoring strategy. CloudFront and RDS costs are underestimated.

### 8. Future Microservice Readiness Score: **7 / 10**
- **Strengths:** Every context is designed for extraction. Trigger conditions are measurable. Extraction order is logical.
- **Weaknesses:** Some contexts (Notification, Audit) are coupled to many others, making extraction expensive. No discussion of API versioning strategy for extracted services.

### 9. Technical Debt Score: **3 / 10**
- **Strengths:** Debt inventory is comprehensive.
- **Weaknesses:** Critical errors (feature flag swap, wrong `ai_assistant/` assessment) make the debt assessment unreliable. Many "CRITICAL" items are actually design issues, not code issues.

### 10. Completeness Score: **5 / 10**
- **Strengths:** Covers most major architectural concerns.
- **Weaknesses:** Missing transaction boundaries, Django ORM leakage, aggregate invariants, event versioning, secrets management, test strategy, cost monitoring, Gunicorn config, health checks.

---

## Part 4: Prioritized Improvement Roadmap

### Phase 0 — Immediate Corrections (Week 1, before any implementation)

| Priority | Item | Rationale |
|----------|------|-----------|
| P0 | **Fix feature flag table** (Section 8.3) | Prevents production incidents. Wrong flag names/descriptions will cause wrong gateway activation. |
| P0 | **Correct `ai_assistant/` assessment** | The document says it is empty; it is not. Deleting it would destroy functionality. |
| P0 | **Fix entity ownership conflicts** | `NotificationPreference`, `PropertyTaxRecord`, and `RentReminderLog` must be assigned to exactly one aggregate. |
| P0 | **Fix Shared Kernel redundancy** | Remove duplicate `ids/` and `money/` directories from proposed structure. |
| P0 | **Fix CQRS contradiction** | Remove `read_models/` from Dashboard structure OR explicitly state that materialized views are database optimizations, not CQRS. |

### Phase 1 — Foundation (Monolith Discipline)

| Priority | Item | Rationale |
|----------|------|-----------|
| P1 | **Create `payments/` bounded context** | Payment logic is scattered; this is the highest-value extraction. |
| P1 | **Fix business logic in views** | Views must be thin. This is a CRITICAL Clean Architecture violation. |
| P1 | **Fix cross-app model imports** | 79+ violations. Use `settings.AUTH_USER_MODEL`. |
| P1 | **Fix Razorpay webhook security** | Signature verification is non-negotiable for payment security. |
| P1 | **Define transaction boundary rules** | Prevent partial commits and data inconsistency. |
| P1 | **Define Django ORM leakage rules** | Domain layer must not depend on QuerySet/Manager. |
| P1 | **Implement OTP rate limiting** | Prevent brute-force attacks on authentication. |
| P1 | **Fix `NotificationPreference` ownership** | Move to Notification context. |
| P1 | **Implement basic event bus** | Replace Django Signals for critical events. |
| P1 | **Add health check endpoints** | Required for monitoring and future load balancing. |
| P1 | **Set `CONN_MAX_AGE = 60`** | Reduce database connection overhead. |
| P1 | **Document secrets management** | Prevent credential leakage. |

### Phase 2 — Internal Refinement

| Priority | Item | Rationale |
|----------|------|-----------|
| P2 | **Extract `identity/` and `subscription/` from `core/`** | Clarify context boundaries within the monolith. |
| P2 | **Extract `rent/` and `renter/` from `properties/`** | Separate contexts need separate apps. |
| P2 | **Implement payment state machine** | Prevent invalid payment transitions. |
| P2 | **Add AI action guardrails** | Prevent unsafe AI-generated actions. |
| P2 | **Consolidate `ai_assistant/` into `smartbot/`** | Eliminate duplicate after migrating functionality. |
| P2 | **Implement outbox pattern** | Event durability for async processing. |
| P2 | **Configure Celery + Redis** | Replace management commands for async workloads. |
| P2 | **Migrate cache to Redis** | Enable horizontal scaling and shared session state. |
| P2 | **Add PgBouncer** | Connection pooling for production load. |
| P2 | **Add file upload validation** | Prevent malicious uploads. |
| P2 | **Implement JWT token blacklisting** | Enable secure logout. |
| P2 | **Isolate notification content from dispatch** | Move rent/extra-charge/late-fee reminder logic out of notification app. |
| P2 | **Add notification deduplication** | Prevent spam from signal storms. |
| P2 | **Add Audit context** | Centralized audit trail. |
| P2 | **Add Storage context** | Isolate S3/CDN logic. |
| P2 | **Add materialized views for dashboard** | Optimize analytics queries. |

### Phase 3 — Advanced Patterns (Only If Justified)

| Priority | Item | Rationale |
|----------|------|-----------|
| P3 | **Add read replicas** | Only if read load exceeds primary capacity. |
| P3 | **Implement Redis Streams** | Only if async processing volume exceeds single-process capacity. |
| P3 | **Add Search context** | Only if global search is a user requirement. |
| P3 | **Add Billing context** | Only when automated payments + GST compliance are required. |
| P3 | **Implement CQRS** | Only if analytics queries exceed 500ms or require custom report builder. |
| P3 | **Add API versioning** | `/api/v1/` should have been in Phase 1. |

### Phase 4 — Service Extraction (Only If Business Scale Justifies)

| Priority | Item | Rationale |
|----------|------|-----------|
| P4 | **Extract `payments/`** | Compliance and scaling requirements. |
| P4 | **Extract `notification/`** | Independent delivery infrastructure. |
| P4 | **Extract `identity/`** | Shared across all services. |
| P4 | **Add API gateway** | Required for service-to-service auth and routing. |
| P4 | **Add distributed tracing** | Required for debugging cross-service calls. |
| P4 | **Horizontal scaling** | Multiple EC2 behind ALB. |

---

## Part 5: Critical Warnings

1. **Do NOT follow Section 10.1's instruction to "Delete `ai_assistant/`"** — the app is not empty. It contains functional AI services that would be lost.
2. **Do NOT use the feature flags as named in Section 8.3** — the descriptions are swapped. Verify against `settings.py` before implementation.
3. **Do NOT implement a generic repository** — the `BaseRepository` pattern in Section 5.1 is an anti-pattern. Use aggregate-specific repositories.
4. **Do NOT deploy the Phase 4 infrastructure** — Kubernetes, Kafka, and service meshes are explicitly excluded by the project's budget and team size constraints.
5. **Do NOT treat the 12 bounded contexts as deployable units** — they are modules within a single deployable monolith. Service extraction is a Phase 4 contingency, not a goal.

---

*End of Rigorous Architecture Review*
