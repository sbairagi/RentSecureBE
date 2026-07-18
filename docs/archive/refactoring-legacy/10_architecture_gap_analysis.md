# RentSecure Backend — Architecture Gap Analysis

**Project:** RentSecure Backend
**Phase:** Target Architecture Gap Analysis
**Date:** 2026-07-17
**Status:** ANALYSIS — Awaiting Implementation
**Constraint:** Analysis only. No production code was modified.

**Source Document:** `docs/refactoring/09_target_architecture.md`
**Baseline Audit:** `docs/refactoring/06_architecture_audit.md`
**ADRs:** `docs/refactoring/08_architecture_decisions.md`

---

## 1. Architecture Completeness Score

**Overall Score: 18 / 100**

| Category | Target State | Current State | Gap | Score |
|----------|-------------|---------------|-----|-------|
| Bounded Context Separation | 13 modules with clear boundaries | 8 apps, 2 with no `apps.py` | 5 modules missing or merged | 15 / 100 |
| Layer Architecture (Domain/Application/Infrastructure/Presentation) | Strict 4-layer per module | Flat Django layout everywhere | 0 modules have layered structure | 0 / 100 |
| Domain Layer (entities, value objects, domain services) | Rich domain models, persistence-ignorant | Django ORM models with business logic in views | No pure domain layer exists | 0 / 100 |
| Application Services | Orchestration layer between views and domain | Services exist but mix application and domain logic | No clear application service layer | 20 / 100 |
| Repository Pattern (ports + adapters) | Protocol-based interfaces + ORM implementations | Repository classes without protocols | Interfaces missing, implementations exist | 30 / 100 |
| Ports/Adapters for External Integrations | All integrations behind ports | Direct imports of external services | Only partial adapter pattern | 20 / 100 |
| Domain Events | Event bus with explicit handlers | Django signals for orchestration | Signals used instead of domain events | 10 / 100 |
| Value Objects | Immutable VO layer | None | No value objects | 0 / 100 |
| Specifications | Query specification pattern | Ad-hoc queryset filtering | Not implemented | 0 / 100 |
| Read Models | Denormalized projections for analytics | Raw queries in views/services | Not implemented | 0 / 100 |
| Caching Strategy | Named caches with invalidation rules | LocMemCache only, no strategy | Basic cache only | 20 / 100 |
| Observability | Structured logging, metrics, tracing | Basic Django logging | Minimal observability | 15 / 100 |
| Security Architecture | RBAC, webhook security, audit logging | Basic JWT auth, no audit log | Partial security | 30 / 100 |
| Background Processing | Management commands + Celery | Management commands + cron | Partial | 40 / 100 |
| Feature Flags | Runtime evaluation with guarded imports | Settings flags with unconditional imports | Broken feature flags | 20 / 100 |
| Coding Standards | Enforced import rules, folder structure | Some conventions exist | Partial enforcement | 25 / 100 |
| Import-linter | Automated dependency enforcement | Not configured | Not present | 0 / 100 |
| Testing Structure | Per-layer tests (domain/application/infrastructure/presentation) | Mixed per-app tests | Structure missing | 20 / 100 |

**Weighted Average: 18 / 100**

---

## 2. Major Strengths

| Strength | Description | Current Evidence |
|----------|-------------|------------------|
| **Existing bounded context awareness** | Apps already loosely correspond to business capabilities | `core`, `properties`, `finance`, `notification`, `documents`, `smartbot`, `referral_and_earn` |
| **Repository pattern partially implemented** | Properties app has repository classes | `properties/repositories/` with `BuildingRepository`, `UnitRepository`, `RenterRepository`, `RentRecordRepository` |
| **Policies partially implemented** | Unit policy exists | `properties/policies/unit_policy.py` |
| **Feature flags exist** | Environment-based flags for disabled features | `ENABLE_RAZORPAY`, `ENABLE_CASHFREE`, `ENABLE_WHATSAPP`, etc. |
| **Shared kernel exists** | Common utilities are centralized | `shared/` with `constants.py`, `enums.py`, `exceptions.py`, `interfaces.py`, `types.py`, `validators.py` |
| **Existing ADRs** | Architecture decisions are documented | `docs/refactoring/08_architecture_decisions.md` with 10 ADRs |
| **Management commands for background jobs** | Scheduled tasks exist | 15+ management commands for reminders, rent generation, etc. |
| **Test coverage exists** | Tests are present across apps | Multiple test files per app, some comprehensive test suites |
| **Django best practices partially followed** | Models in separate files, views in views folder | `properties/models/`, `properties/views/`, `properties/serializers/` |
| **URL routing exists** | URL configurations per app | `*/urls.py` in most apps |

---

## 3. Architectural Risks

| Risk | Severity | Likelihood | Impact | Mitigation |
|------|----------|-----------|--------|------------|
| **Unconditional imports of disabled services** | Critical | High | App fails to start when gateway deps missing | Implement lazy imports behind feature flags immediately |
| **Fat views with business logic** | High | Certain | Business rules scattered, hard to test | Extract application services, then domain services |
| **No domain layer** | High | Certain | Cannot enforce business invariants, no testability | Create domain/ folder structure per module |
| **Signals as hidden orchestration** | High | Certain | Flow is untraceable, hard to debug | Replace signals with domain events + explicit handlers |
| **Duplicate service implementations** | High | Certain | Inconsistent behavior, doubled maintenance | Consolidate per ADR-003 with compatibility wrappers |
| **Circular import risk during migration** | High | Medium | Import errors break app startup | Use dependency injection, lazy imports |
| **Cross-module model imports** | High | Certain | Tight coupling, hard to extract services | Enforce import-linter, use DTOs/events |
| **No import-linter enforcement** | Medium | Certain | Dependency rules not enforced | Configure import-linter before any migration |
| **Stubs with NotImplementedError** | Medium | High | Incomplete features block dependent code | Implement or remove stubs before dependent features |
| **Feature flags not guarding imports** | Medium | High | Disabled features still require dependencies | Fix all unconditional imports |
| **No read models for analytics** | Medium | Medium | Dashboard queries compete with transactional queries | Implement read models before scaling |
| **No structured observability** | Medium | Medium | Debugging production issues is difficult | Add structured logging, metrics before scaling |
| **No audit logging** | Medium | Medium | Compliance and security risk | Implement audit events for sensitive operations |
| **Multiple URL mounts on `/api/`** | Low | Certain | Namespace collision risk | Consolidate URL mounting strategy |
| **`dashboard` has no `apps.py`** | Low | Low | Not a proper Django app, cannot register signals/events | Add `apps.py` or integrate into `analytics` module |

---

## 4. Missing Bounded Contexts

| Missing Context | Target Location | Current Location(s) | Gap Description |
|----------------|----------------|---------------------|-----------------|
| **Identity** (separate from Subscriptions) | `identity/` | `core/` | `core/` currently combines Identity AND Subscriptions. Target architecture requires them as separate bounded contexts. |
| **Payments** | `payments/` | `rentsecure_be/services/` | Payment gateway code lives in project-level `rentsecure_be/services/`. No dedicated `payments` app exists. |
| **Assistant** (merged smartbot + ai_assistant) | `assistant/` | `smartbot/` + `ai_assistant/` | Two separate apps contain AI code. Neither is named `assistant`. `ai_assistant` is not in `INSTALLED_APPS`. |
| **Analytics** | `analytics/` | `dashboard/` (thin views), `properties/`, `core/` | `dashboard/` has no `apps.py` and no models. Analytics logic is scattered across `properties/views/owner_dashboard.py`, `properties/services/unit_service.py`, `core/services/owner_reporting_service.py`. |
| **Infrastructure** | `infrastructure/` | None | Cross-cutting concerns (logging, metrics, caching, security, health checks) have no centralized module. |

### Bounded Contexts That Exist But Need Renaming

| Current Name | Target Name | Action Required |
|-------------|-------------|-----------------|
| `core/` | Split into `identity/` + keep subscriptions-related parts | Extract Identity models/services/views into new `identity/` app |
| `referral_and_earn/` | `referral/` | Rename app |
| `smartbot/` + `ai_assistant/` | `assistant/` | Merge and rename |
| `dashboard/` | `analytics/` | Rename and add proper app structure |

---

## 5. Missing Modules

| Missing Module | Purpose | Required For |
|---------------|---------|--------------|
| `payments/` | Payment gateway adapters, webhooks, payout processing | ADR-010, Stage 2 payment gateway activation |
| `assistant/` | Merged AI assistant (smartbot + ai_assistant) | ADR-005 |
| `analytics/` | Owner dashboard, analytics, reporting | ADR-009 |
| `infrastructure/` | Cross-cutting concerns (logging, metrics, caching, security, health) | Target architecture section 3.2.13 |
| `identity/` | Separate Identity bounded context from Subscriptions | ADR-002 |
| `shared/domain_events.py` (enhanced) | Event bus with idempotency, correlation IDs | Section 6 |
| `shared/events/` | Base event classes, event bus implementation | Section 5.9 |

---

## 6. Incorrect Module Ownership

| Component | Current Owner | Target Owner | Gap |
|-----------|--------------|--------------|-----|
| `owner_reporting_service.py` | `core/` | `properties/` (or `analytics/`) | Property-domain logic in Identity app |
| `rent_notify_service.py` | `notification/` | `properties/` | Property-specific notification logic in Notification app |
| `extra_charge_reminders.py` | `notification/` | `properties/` | Property-specific notification logic in Notification app |
| `late_fees_notify_service.py` | `notification/` | `properties/` | Property-specific notification logic in Notification app |
| `leegality_service.py` (×2) | `rentsecure_be/`, `smartbot/` | `documents/` | E-signature in project-level and AI apps |
| `agreement_service.py` | `smartbot/` | `documents/` | PDF generation in AI app |
| `whatsapp_service.py` | `smartbot/` | `notification/` | WhatsApp in AI app |
| `i18n_service.py` (×2) | `rentsecure_be/`, `ai_assistant/` | `shared/` | Translation in project-level and AI apps |
| `archive_service.py` | `ai_assistant/` | `properties/` | Property archival in AI app |
| `invoice_service.py` | `ai_assistant/` | `documents/` | PDF generation in AI app |
| `unit_service.py` | `ai_assistant/` | `properties/` | Property logic in AI app |
| `cashfree_service.py` | `rentsecure_be/` | `payments/` | Payment gateway in project-level |
| `razorpay_service.py` | `rentsecure_be/` | `payments/` | Payment gateway in project-level |
| `cashfree_payout.py` | `rentsecure_be/utils/` | `payments/` | Payout logic in project-level utils |
| Subscription models + services | `core/` | `core/` (keep, but separate from Identity) | Currently combined with Identity |
| `summary_service.py` | `properties/` | `notification/` or `analytics/` | Summary delivery logic in Property app |
| `receipt_service.py` | `properties/` | `documents/` | PDF generation in Property app |
| PDF generation (×5 locations) | Multiple | `documents/` | Scattered across 5+ files |

---

## 7. Incorrect Dependency Directions

| Source | Current Import | Target Dependency | Issue |
|--------|---------------|------------------|-------|
| `core/views.py` | `cashfree_service` from `rentsecure_be` | Should go through `payments` adapter | Direct import of payment gateway |
| `properties/views/rent_record_views.py` | `razorpay_service`, `cashfree_service` | Should go through `payments` adapter | Direct import of payment gateways |
| `properties/views/unit_views.py` | `leegality_service` from `rentsecure_be` | Should go through `documents` port | Direct import of e-signature |
| `smartbot/actions.py` | `cashfree_service`, `leegality_service` | Should go through ports | Direct imports of external services |
| `notification/services/rent_notify_service.py` | `i18n_service` from `rentsecure_be` | Should go through `shared` port | Direct import of project-level service |
| `properties/signals/__init__.py` | Direct WhatsApp calls | Should use `notification` channel port | Signal handlers calling external services directly |
| `core/views.py` | `owner_reporting_service` (own service) | Property-domain logic in Identity app | Cross-domain logic in wrong module |
| `ai_assistant/views.py` | Various property/payment services | Should use `assistant` bounded context | AI app directly importing domain services |

---

## 8. Circular Dependency Risks

| Risk | Current State | Target State | Mitigation |
|------|---------------|--------------|------------|
| `core` ↔ `properties` | `core` has owner reporting that queries `properties` models | `core` should not import `properties` | Move owner reporting to `properties` or `analytics` |
| `notification` ↔ `properties` | `properties/signals/` imports `notification` services; `notification` has property-specific logic | `notification` should not import `properties`; `properties` should use `notification` ports | Move property notifications to `properties`, keep channels in `notification` |
| `smartbot` ↔ `ai_assistant` | `ai_assistant` services imported by `smartbot` | Merge into single `assistant` app | ADR-005 |
| `documents` ↔ `properties` | `documents` needs `properties` models for PDF generation | Acceptable dependency (documents depends on properties) | Use DTOs/events to decouple |
| `finance` ↔ `properties` | `finance` needs `properties` data for tax | Acceptable dependency | Use events for async communication |
| `payments` ↔ `properties` | `payments` needs `RentRecord` for payouts | Acceptable dependency | Use domain events for payment status changes |

**Key Rule:** No circular dependencies are permitted. All dependencies must be acyclic.

---

## 9. Missing Domain Services

| Missing Domain Service | Location | Purpose | Current Alternative |
|------------------------|----------|---------|---------------------|
| `RenterService` (domain) | `properties/domain/renter/services/` | Renter business logic | `properties/services/renter_service.py` (stub, all `NotImplementedError`) |
| `RentRecordService` (domain) | `properties/domain/rent/services/` | Rent record business logic | `properties/services/rent_service.py` (stub, all `NotImplementedError`) |
| `UnitService` (domain) | `properties/domain/unit/services/` | Unit business logic | `properties/services/unit_service.py` (has logic but mixed with application concerns) |
| `BuildingService` (domain) | `properties/domain/building/services/` | Building business logic | `properties/services/building_service.py` (mixed concerns) |
| `ExtraChargeService` (domain) | `properties/domain/extra_charge/services/` | Extra charge business logic | `properties/services/extra_charge_service.py` |
| `PaymentService` (domain) | `payments/domain/payment/services/` | Payment orchestration | `properties/services/` (mixed with rent service) |
| `PayoutService` (domain) | `payments/domain/payout/services/` | Payout processing | `properties/communication/retry_failed_payouts.py` |
| `NotificationService` (domain) | `notification/domain/notification/services/` | Notification orchestration | `notification/services/` (mixed channel + orchestration) |
| `TaxService` (domain) | `finance/domain/tax/services/` | Tax calculation logic | `finance/utils.py` |
| `CAService` (domain) | `finance/domain/ca/services/` | CA profile management | `finance/views.py` (logic in view) |
| `ChatbotService` (domain) | `assistant/domain/chatbot/services/` | Chatbot business logic | `smartbot/services/chatbot_service.py` |
| `ReferralService` (domain) | `referral/domain/referral/services/` | Referral business logic | `core/services/referral_service.py` |
| `FeatureEnforcer` (domain) | `core/domain/subscription/services/` or `properties/domain/` | Feature/quota enforcement | `properties/feature_enforcer.py` |

---

## 10. Missing Repositories

| Missing Repository | Location | Purpose |
|--------------------|----------|---------|
| `UserRepository` (interface) | `identity/domain/user/repositories/` | User data access abstraction |
| `ProfileRepository` (interface) | `identity/domain/profile/repositories/` | Profile data access abstraction |
| `SubscriptionRepository` (interface) | `core/domain/subscription/repositories/` | Subscription data access |
| `UsageLimitRepository` (interface) | `core/domain/usage_limit/repositories/` | Usage limit data access |
| `BuildingRepository` (interface) | `properties/domain/building/repositories/` | Building data access |
| `UnitRepository` (interface) | `properties/domain/unit/repositories/` | Unit data access |
| `RenterRepository` (interface) | `properties/domain/renter/repositories/` | Renter data access |
| `RentRecordRepository` (interface) | `properties/domain/rent/repositories/` | Rent record data access |
| `ExtraChargeRepository` (interface) | `properties/domain/extra_charge/repositories/` | Extra charge data access |
| `PropertyTaxRepository` (interface) | `properties/domain/property_tax/repositories/` | Property tax data access |
| `CareTakerRepository` (interface) | `properties/domain/caretaker/repositories/` | Caretaker data access |
| `NotificationRepository` (interface) | `notification/domain/notification/repositories/` | Notification data access |
| `DeviceTokenRepository` (interface) | `notification/domain/device_token/repositories/` | Device token data access |
| `TaxRepository` (interface) | `finance/domain/tax/repositories/` | Tax submission data access |
| `CAProfileRepository` (interface) | `finance/domain/ca/repositories/` | CA profile data access |
| `ReferralRepository` (interface) | `referral/domain/referral/repositories/` | Referral data access |
| `ChatRepository` (interface) | `assistant/domain/chat/repositories/` | Chat history data access |

**Note:** Implementations exist in some cases (`properties/repositories/`), but they are not protocol-based interfaces. All repositories need to be converted to `Protocol` classes in the domain layer.

---

## 11. Missing Application Services

| Missing Application Service | Location | Purpose |
|----------------------------|----------|---------|
| `CreateRenterUseCase` | `properties/application/renter/` | Orchestrate renter creation |
| `CreateUnitUseCase` | `properties/application/unit/` | Orchestrate unit creation |
| `CreateBuildingUseCase` | `properties/application/building/` | Orchestrate building creation |
| `ProcessRentPaymentUseCase` | `properties/application/rent/` | Orchestrate rent payment flow |
| `GenerateRentReceiptUseCase` | `documents/application/receipt/` | Orchestrate receipt generation |
| `SendForSignatureUseCase` | `documents/application/esignature/` | Orchestrate e-signature flow |
| `SendNotificationUseCase` | `notification/application/` | Orchestrate notification sending |
| `ProcessPayoutUseCase` | `payments/application/` | Orchestrate payout processing |
| `VerifyWebhookUseCase` | `payments/application/` | Orchestrate webhook verification |
| `ChatUseCase` | `assistant/application/` | Orchestrate chatbot interaction |
| `SubmitTaxUseCase` | `finance/application/` | Orchestrate tax submission |
| `GenerateDashboardUseCase` | `analytics/application/` | Orchestrate dashboard data aggregation |
| `ProcessReferralUseCase` | `referral/application/` | Orchestrate referral processing |

**Current Gap:** Views call services directly. There is no application service layer that orchestrates use cases. Services mix application orchestration with domain logic.

---

## 12. Missing Ports/Interfaces

| Missing Port | Location | Purpose | Current Alternative |
|-------------|----------|---------|---------------------|
| `PaymentGateway` | `payments/domain/payment/ports/` | Payment gateway abstraction | Direct adapter imports in views |
| `NotificationChannel` | `notification/domain/channel/ports/` | Notification channel abstraction | Direct channel imports |
| `StorageService` | `documents/domain/storage/ports/` | File storage abstraction | Direct S3/local storage calls |
| `LLMClient` | `assistant/domain/llm/ports/` | LLM API abstraction | Direct OpenAI imports |
| `ESignatureProvider` | `documents/domain/esignature/ports/` | E-signature abstraction | Direct Leegality imports |
| `TranslationService` | `shared/domain/integration/ports/` | Translation abstraction | Direct Google/OpenAI imports |
| `TextToSpeechService` | `notification/domain/voice/ports/` | TTS abstraction | Direct OpenAI/TTS imports |
| `PDFGenerator` | `documents/domain/pdf/ports/` | PDF generation abstraction | Direct WeasyPrint calls |
| `CacheService` | `shared/domain/infrastructure/ports/` | Cache abstraction | Direct Django cache calls |
| `MetricsService` | `infrastructure/domain/observability/ports/` | Metrics abstraction | None |
| `AuditLogger` | `shared/domain/infrastructure/ports/` | Audit logging abstraction | None |
| `EventBus` | `shared/domain/events/ports/` | Event publishing abstraction | Django signals |

---

## 13. Missing Adapters

| Missing Adapter | Implements | Location | Purpose |
|-----------------|-----------|----------|---------|
| `ManualPaymentAdapter` | `PaymentGateway` | `payments/infrastructure/adapters/manual.py` | Manual UPI payment (Year 1) |
| `RazorpayAdapter` | `PaymentGateway` | `payments/infrastructure/adapters/razorpay.py` | Razorpay integration (Stage 2) |
| `CashfreeAdapter` | `PaymentGateway` | `payments/infrastructure/adapters/cashfree.py` | Cashfree integration (Stage 2) |
| `TwilioWhatsAppAdapter` | `NotificationChannel` | `notification/infrastructure/adapters/whatsapp.py` | WhatsApp messaging |
| `TwilioSMSAdapter` | `NotificationChannel` | `notification/infrastructure/adapters/sms.py` | SMS messaging |
| `FCMAdapter` | `NotificationChannel` | `notification/infrastructure/adapters/push.py` | Firebase push notifications |
| `SESAdapter` | `NotificationChannel` | `notification/infrastructure/adapters/email.py` | AWS SES email |
| `SMTPAdapter` | `NotificationChannel` | `notification/infrastructure/adapters/email.py` | SMTP email |
| `OpenAILLMAdapter` | `LLMClient` | `assistant/infrastructure/adapters/openai.py` | OpenAI GPT integration |
| `LeegalityAdapter` | `ESignatureProvider` | `documents/infrastructure/adapters/leegality.py` | Leegality e-signature |
| `S3StorageAdapter` | `StorageService` | `documents/infrastructure/adapters/s3.py` | S3 file storage |
| `LocalStorageAdapter` | `StorageService` | `documents/infrastructure/adapters/local.py` | Local file storage |
| `GoogleTranslateAdapter` | `TranslationService` | `shared/infrastructure/adapters/google_translate.py` | Google Translate |
| `OpenAITranslationAdapter` | `TranslationService` | `shared/infrastructure/adapters/openai_translation.py` | OpenAI translation |
| `OpenAITTSSAdapter` | `TextToSpeechService` | `notification/infrastructure/adapters/tts.py` | OpenAI TTS |
| `PrometheusMetricsAdapter` | `MetricsService` | `infrastructure/infrastructure/adapters/prometheus.py` | Prometheus metrics |
| `SentryErrorAdapter` | `ErrorReporter` | `infrastructure/infrastructure/adapters/sentry.py` | Sentry error reporting |

---

## 14. Missing Domain Events

| Missing Domain Event | Source Aggregate | Target Module | Current Alternative |
|---------------------|-----------------|---------------|---------------------|
| `UserCreated` | User | `identity` | Django signal `post_save` in `core/signals.py` |
| `UserVerified` | User | `identity` | Not implemented |
| `PasswordChanged` | User | `identity` | Not implemented |
| `SubscriptionCreated` | UserSubscription | `core` (or `identity`) | Not implemented |
| `SubscriptionExpired` | UserSubscription | `core` (or `identity`) | Not implemented |
| `UsageLimitExceeded` | UsageLimit | `core` (or `identity`) | Not implemented |
| `BuildingCreated` | Building | `properties` | Not implemented |
| `UnitCreated` | Unit | `properties` | Not implemented |
| `RenterCreated` | Renter | `properties` | Custom signal `renter_created` in `properties/signals/renter_signals.py` |
| `RenterUpdated` | Renter | `properties` | Not implemented |
| `RenterExited` | Renter | `properties` | Custom signal `renter_exited` |
| `RenterArchived` | Renter | `properties` | Custom signal `renter_archived` |
| `RentRecordCreated` | RentRecord | `properties` | Not implemented |
| `RentPaid` | RentRecord | `properties` | Django signal `post_save` in `properties/signals/__init__.py` |
| `RentOverdue` | RentRecord | `properties` | Not implemented |
| `ExtraChargeCreated` | ExtraCharge | `properties` | Not implemented |
| `PaymentInitiated` | RentRecord | `payments` | Not implemented |
| `PaymentCompleted` | RentRecord | `payments` | Not implemented |
| `PaymentFailed` | RentRecord | `payments` | Not implemented |
| `PayoutInitiated` | RentRecord | `payments` | Not implemented |
| `PayoutCompleted` | RentRecord | `payments` | Not implemented |
| `PayoutFailed` | RentRecord | `payments` | Not implemented |
| `NotificationSent` | Notification | `notification` | Not implemented |
| `NotificationFailed` | Notification | `notification` | Not implemented |
| `DocumentGenerated` | Document | `documents` | Not implemented |
| `DocumentSent` | Document | `documents` | Not implemented |
| `DocumentSigned` | Document | `documents` | Not implemented |
| `TaxSubmitted` | TaxSubmissionToCA | `finance` | Not implemented |
| `TaxDocumentsGenerated` | TaxSubmissionToCA | `finance` | Not implemented |
| `ChatMessageReceived` | SmartBotChat | `assistant` | Not implemented |
| `ActionExecuted` | SmartBotMessage | `assistant` | Not implemented |
| `AlertCreated` | AIAlert | `assistant` | Not implemented |
| `ReferralCreated` | Referral | `referral` | Django signal `post_save` in `referral_and_earn/signals.py` |
| `ReferralProcessed` | Referral | `referral` | Not implemented |
| `BonusEarned` | Referral | `referral` | Not implemented |
| `DashboardViewed` | N/A | `analytics` | Not implemented |
| `ReportGenerated` | N/A | `analytics` | Not implemented |

---

## 15. Missing Integration Events

| Missing Integration Event | Producer | Consumer | Purpose |
|---------------------------|----------|----------|---------|
| `UserCreated` → `SendWelcomeEmail` | `identity` | `notification` | Send welcome email on user registration |
| `UserCreated` → `CreateReferralCode` | `identity` | `referral` | Create referral code on user registration |
| `UserCreated` → `CreateUsageLimits` | `identity` | `core` (or `identity`) | Initialize usage limits |
| `RenterCreated` → `GenerateOnboardingToken` | `properties` | `identity` | Generate onboarding token |
| `RenterCreated` → `SendWelcomeNotification` | `properties` | `notification` | Send welcome message to renter |
| `RenterCreated` → `CreateUsageLimits` | `properties` | `core` (or `identity`) | Initialize renter usage limits |
| `RentPaid` → `GenerateReceipt` | `properties` | `documents` | Generate rent receipt PDF |
| `RentPaid` → `SendPaymentConfirmation` | `properties` | `notification` | Send payment confirmation |
| `RentPaid` → `ProcessPayout` | `properties` | `payments` | Trigger owner payout |
| `RentOverdue` → `SendReminder` | `properties` | `notification` | Send rent reminder |
| `DocumentSent` → `NotifyRecipient` | `documents` | `notification` | Notify recipient of document |
| `DocumentSigned` → `UpdateStatus` | `documents` | `properties` | Update agreement status |
| `PaymentCompleted` → `UpdateRentRecord` | `payments` | `properties` | Update rent record status |
| `PayoutCompleted` → `NotifyOwner` | `payments` | `notification` | Notify owner of payout |
| `ChatMessageReceived` → `ProcessAIResponse` | `assistant` | `assistant` | Process and store AI response |
| `ActionExecuted` → `LogAction` | `assistant` | `assistant` | Log AI action for audit |

---

## 16. Missing Value Objects

| Missing Value Object | Location | Purpose |
|---------------------|----------|---------|
| `Money` | `shared/domain/value_objects/` | Represent monetary amounts with currency |
| `DateRange` | `shared/domain/value_objects/` | Represent date ranges (e.g., lease period) |
| `Address` | `properties/domain/value_objects/` | Represent property addresses |
| `PhoneNumber` | `shared/domain/value_objects/` | Validated phone number |
| `Email` | `shared/domain/value_objects/` | Validated email address |
| `OTPCode` | `identity/domain/value_objects/` | OTP code with validation |
| `RentAmount` | `properties/domain/value_objects/` | Rent amount with currency and period |
| `Percentage` | `shared/domain/value_objects/` | Percentage values (e.g., late fees) |
| `UserID` | `shared/domain/value_objects/` | Typed user identifier |
| `BuildingID` | `properties/domain/value_objects/` | Typed building identifier |
| `UnitID` | `properties/domain/value_objects/` | Typed unit identifier |
| `RenterID` | `properties/domain/value_objects/` | Typed renter identifier |
| `RentRecordID` | `properties/domain/value_objects/` | Typed rent record identifier |
| `DocumentID` | `documents/domain/value_objects/` | Typed document identifier |
| `SignatureRequestID` | `documents/domain/value_objects/` | Typed signature request identifier |
| `PaymentID` | `payments/domain/value_objects/` | Typed payment identifier |
| `PayoutID` | `payments/domain/value_objects/` | Typed payout identifier |

---

## 17. Missing Policies

| Missing Policy | Location | Purpose |
|----------------|----------|---------|
| `UserPolicy` | `identity/domain/policies/` | User access and modification rules |
| `SubscriptionPolicy` | `core/domain/policies/` or `identity/domain/policies/` | Subscription change rules |
| `BuildingPolicy` | `properties/domain/policies/` | Building access and modification rules |
| `UnitPolicy` | `properties/domain/policies/` | Unit access and modification rules |
| `RenterPolicy` | `properties/domain/policies/` | Renter access and modification rules |
| `RentRecordPolicy` | `properties/domain/policies/` | Rent record access and modification rules |
| `ExtraChargePolicy` | `properties/domain/policies/` | Extra charge access and modification rules |
| `PaymentPolicy` | `payments/domain/policies/` | Payment processing rules |
| `PayoutPolicy` | `payments/domain/policies/` | Payout processing rules |
| `DocumentPolicy` | `documents/domain/policies/` | Document access rules |
| `TaxPolicy` | `finance/domain/policies/` | Tax submission rules |
| `FeatureEnforcer` (as policy) | `core/domain/policies/` or `properties/domain/policies/` | Feature flag and quota enforcement |

**Current Gap:** Only `UnitPolicy` exists (`properties/policies/unit_policy.py`). All other policies are missing. Business rules are currently embedded in views and services.

---

## 18. Missing Specifications

| Missing Specification | Location | Purpose |
|-----------------------|----------|---------|
| `OverdueRentSpecification` | `properties/domain/rent/specifications/` | Query rent records that are overdue |
| `PendingPayoutSpecification` | `properties/domain/rent/specifications/` | Query rent records pending payout |
| `PaidRentSpecification` | `properties/domain/rent/specifications/` | Query paid rent records |
| `ActiveRenterSpecification` | `properties/domain/renter/specifications/` | Query active renters |
| `VacantUnitSpecification` | `properties/domain/unit/specifications/` | Query vacant units |
| `OwnerBuildingSpecification` | `properties/domain/building/specifications/` | Query buildings by owner |
| `PendingExtraChargeSpecification` | `properties/domain/extra_charge/specifications/` | Query pending extra charges |
| `UnreadNotificationSpecification` | `notification/domain/notification/specifications/` | Query unread notifications |
| `ActiveSubscriptionSpecification` | `core/domain/subscription/specifications/` | Query active subscriptions |
| `ExpiredSubscriptionSpecification` | `core/domain/subscription/specifications/` | Query expired subscriptions |
| `PendingTaxSubmissionSpecification` | `finance/domain/tax/specifications/` | Query pending tax submissions |
| `UnsentDocumentSpecification` | `documents/domain/document/specifications/` | Query unsent documents |

---

## 19. Missing Read Models

| Missing Read Model | Location | Purpose | Current Alternative |
|--------------------|----------|---------|---------------------|
| `OwnerDashboardReadModel` | `analytics/read-models/` | Denormalized owner dashboard data | `properties/views/owner_dashboard.py` with raw queries |
| `RentAnalyticsReadModel` | `analytics/read-models/` | Denormalized rent analytics | `properties/services/unit_service.py` analytics methods |
| `OccupancyAnalyticsReadModel` | `analytics/read-models/` | Denormalized occupancy data | `properties/services/unit_service.py` analytics methods |
| `MonthlySummaryReadModel` | `analytics/read-models/` | Denormalized monthly summary | `core/services/owner_reporting_service.py` |
| `PropertyListReadModel` | `properties/read-models/` | Denormalized property list for owners | Direct ORM queries in views |
| `RentRecordListReadModel` | `properties/read-models/` | Denormalized rent record list | Direct ORM queries in views |

---

## 20. Missing Caching Layer

| Missing Caching Component | Location | Purpose |
|---------------------------|----------|---------|
| Cache decorator/infrastructure | `infrastructure/caching/` | Centralized cache abstraction |
| Cache key generator | `shared/domain/caching/` | Consistent cache key naming |
| Cache invalidation strategy | Per module | Event-driven/TTL/manual invalidation |
| Cache warming | `infrastructure/caching/` | Pre-populate caches |
| Cache metrics | `infrastructure/metrics/` | Track hit/miss rates |

**Current State:** Only Django's `LocMemCache` is configured in `settings.py`. No caching strategy exists beyond basic Django cache framework usage.

---

## 21. Missing Observability Pieces

| Missing Component | Location | Purpose |
|-------------------|----------|---------|
| Structured JSON logging | `infrastructure/logging/` | Replace basic Django logging |
| Request ID middleware | `infrastructure/logging/` | Correlation IDs for requests |
| Prometheus metrics | `infrastructure/metrics/` | Request latency, error rates, queue depth |
| OpenTelemetry tracing | `infrastructure/tracing/` | Distributed tracing |
| Health check endpoints | `infrastructure/health/` | `/health/live`, `/health/ready`, `/health/startup` |
| Sentry integration | `infrastructure/error_reporting/` | Error tracking and alerting |
| Audit event emitter | `shared/domain/events/` | Emit audit events for sensitive operations |
| Audit log storage | `infrastructure/audit/` | Persist audit events |
| Performance profiling | `infrastructure/` | Query count, N+1 detection |

---

## 22. Missing Security Pieces

| Missing Component | Location | Purpose |
|-------------------|----------|---------|
| Custom permission classes | `*/permissions/` per module | Object-level permissions |
| Rate limiting | `infrastructure/security/` | API rate limiting |
| Input sanitization | `shared/validators/` | XSS/injection prevention |
| Webhook signature verification | `payments/webhooks/`, `documents/webhooks/` | HMAC verification for webhooks |
| Secret management abstraction | `infrastructure/security/` | AWS Secrets Manager / Vault integration |
| File upload virus scanning | `infrastructure/security/` | Scan uploaded files |
| Audit logging | `infrastructure/audit/` | Log sensitive operations |
| CORS configuration | `rentsecure_be/settings.py` | Cross-origin resource sharing |

**Current State:** Basic JWT auth exists. No custom permissions, no rate limiting, no webhook security, no audit logging.

---

## 23. Missing Background Processing

| Missing Component | Location | Purpose |
|-------------------|----------|---------|
| Task base class | `shared/domain/tasks/` | Idempotent, retryable task base |
| Task registry | `infrastructure/tasks/` | Register and discover tasks |
| Scheduled job configuration | `management/commands/` + cron | Cron/systemd scheduling |
| Task monitoring | `infrastructure/tasks/` | Track task execution, failures |
| Celery configuration (Stage 2) | `infrastructure/tasks/` | Background worker when needed |

**Current State:** 15+ management commands exist. No task abstraction layer, no idempotency framework, no monitoring.

---

## 24. Missing ADRs

| Missing ADR | Purpose |
|-------------|---------|
| **ADR-011** | Event Bus Implementation Strategy (in-process vs message queue) |
| **ADR-012** | Database-per-Context Strategy (single DB vs separate DBs) |
| **ADR-013** | API Versioning Strategy |
| **ADR-014** | Testing Strategy and Coverage Requirements |
| **ADR-015** | CI/CD Pipeline Architecture |
| **ADR-016** | Database Migration Strategy (additive only) |
| **ADR-017** | Secret Management Strategy (env vars vs Vault) |
| **ADR-018** | Error Handling and Exception Hierarchy |
| **ADR-019** | Logging and Observability Strategy |
| **ADR-020** | Cache Invalidation Strategy |
| **ADR-021** | File Storage Strategy (local vs S3) |
| **ADR-022** | Webhook Security Strategy |
| **ADR-023** | Rate Limiting Strategy |
| **ADR-024** | Frontend-Backend Contract Strategy |
| **ADR-025** | Deployment Strategy (EC2 vs ECS vs EKS) |
| **ADR-026** | Rollback and Disaster Recovery Strategy |
| **ADR-027** | Feature Flag Governance |
| **ADR-028** | Documentation Standards |
| **ADR-029** | Third-Party Service Dependencies |
| **ADR-030** | Data Retention and Archival Strategy |

---

## 25. Missing Coding Standards

| Missing Standard | Current State | Required State |
|-----------------|---------------|----------------|
| **Layer import rules** | No enforcement | `import-linter` configuration with layer rules |
| **Module boundary rules** | No enforcement | `import-linter` configuration with module boundaries |
| **No circular import policy** | No automated checks | `import-linter` + CI enforcement |
| **Domain layer purity** | Django models in domain | Domain layer must not import Django ORM |
| **Service layer rules** | Services mix concerns | Application services orchestrate, domain services decide |
| **View purity** | Views contain business logic | Views delegate to application services |
| **Naming conventions** | Partial (some conventions exist) | Full convention enforcement via ruff/mypy |
| **Test organization** | Mixed per-app tests | Per-layer tests (domain/application/infrastructure/presentation) |
| **Coverage requirements** | No minimum enforced | ≥90% for domain and application layers |
| **Type hints** | Partial | `mypy --strict` enforcement |
| **Docstrings** | Inconsistent | Required for public APIs |
| **Error handling** | Ad-hoc | Standardized error hierarchy |
| **Logging standards** | Inconsistent | Structured JSON logging |
| **API documentation** | None | OpenAPI/Swagger |

---

## 26. Import-Linter Rule Coverage Gaps

| Gap | Current State | Required State |
|-----|---------------|----------------|
| **Layer dependencies** | Not configured | Presentation → Application → Domain ← Infrastructure |
| **Module boundaries** | Not configured | Each bounded context has explicit allowed/forbidden dependencies |
| **Circular import detection** | Not configured | Automated CI checks |
| **Cross-module model imports** | Not configured | Forbidden (use events/DTOs) |
| **Framework leakage** | Not configured | Domain layer must not import Django/DRF |
| **Infrastructure leakage** | Not configured | Application/Domain layers must not import infrastructure |
| **Shared kernel dependencies** | Not configured | All modules can depend on shared, shared depends on nothing |

**Required `import-linter` configuration:**

```yaml
# .importlinter/import_linter.yml
exclude:
  - ".*migrations.*"
  - ".*tests.*"
  - ".*__pycache__.*"
  - ".*static.*"

layers:
  - name: Presentation
    modules:
      - "properties.presentation"
      - "core.presentation"
      - "notification.presentation"
      - "documents.presentation"
      - "finance.presentation"
      - "assistant.presentation"
      - "analytics.presentation"
      - "referral.presentation"
  - name: Application
    modules:
      - "properties.application"
      - "core.application"
      - "notification.application"
      - "documents.application"
      - "finance.application"
      - "assistant.application"
      - "analytics.application"
      - "referral.application"
      - "payments.application"
  - name: Domain
    modules:
      - "properties.domain"
      - "core.domain"
      - "notification.domain"
      - "documents.domain"
      - "finance.domain"
      - "assistant.domain"
      - "analytics.domain"
      - "referral.domain"
      - "payments.domain"
      - "shared.domain"
  - name: Infrastructure
    modules:
      - "properties.infrastructure"
      - "core.infrastructure"
      - "notification.infrastructure"
      - "documents.infrastructure"
      - "finance.infrastructure"
      - "assistant.infrastructure"
      - "analytics.infrastructure"
      - "referral.infrastructure"
      - "payments.infrastructure"
      - "infrastructure"

layer_contracts:
  - name: "Layer Dependencies"
    layers:
      - Presentation
      - Application
      - Domain
      - Infrastructure
    modules:
      - name: "properties.presentation"
        dependencies:
          - "properties.application"
          - "properties.domain"
          - "shared.domain"
      # ... (per-module contracts)

module_contracts:
  - name: "No cross-module model imports"
    modules:
      - "properties"
      - "core"
      - "finance"
      - "notification"
      - "documents"
      - "assistant"
      - "analytics"
      - "referral"
      - "payments"
    dependencies:
      forbidden:
        - "properties.*:core.*"
        - "properties.*:finance.*"
        # ... (all forbidden dependencies from target architecture)
```

---

## 27. Current Project Structure vs Target Structure

### 27.1 Per-App Comparison Tables

#### `core/` → Split into `identity/` + `core/` (subscriptions)

| Current Structure | Target Structure | Missing Folders | Files Requiring Relocation | Estimated Effort | Migration Complexity | Risk |
|-------------------|------------------|-----------------|---------------------------|------------------|---------------------|------|
| `core/models.py` (all models in one file) | `identity/domain/user/entities/`, `identity/domain/profile/entities/`, `core/domain/subscription/entities/` | `domain/`, `application/`, `infrastructure/`, `presentation/` per subdomain | `models.py` → split into per-entity files | 16 hours | High | Medium |
| `core/views.py` (all views in one file) | `identity/presentation/views/`, `core/presentation/views/` | `presentation/views/` | Split views by bounded context | 12 hours | High | Medium |
| `core/serializers.py` | `identity/presentation/serializers/`, `core/presentation/serializers/` | `presentation/serializers/` | Split serializers | 8 hours | Medium | Low |
| `core/services/` (exists) | `identity/domain/user/services/`, `core/domain/subscription/services/`, `identity/application/`, `core/application/` | `domain/`, `application/` per service | Move and refactor services | 20 hours | High | Medium |
| `core/signals.py` | `identity/domain/events/` + explicit handlers | `domain/events/` | Replace signals with domain events | 12 hours | High | Medium |
| `core/urls.py` | `identity/urls.py`, `core/urls.py` | N/A | Split URL configs | 4 hours | Low | Low |
| `core/tests/` | `identity/tests/domain/`, `identity/tests/application/`, `core/tests/domain/`, `core/tests/application/` | `tests/` subfolders | Reorganize tests | 8 hours | Medium | Low |

#### `properties/`

| Current Structure | Target Structure | Missing Folders | Files Requiring Relocation | Estimated Effort | Migration Complexity | Risk |
|-------------------|------------------|-----------------|---------------------------|------------------|---------------------|------|
| `properties/models/*.py` (exists) | `properties/domain/*/entities/` + `properties/models/` | `domain/*/entities/` per entity | Move models to `domain/` (keep Django models in `models/`) | 16 hours | High | Medium |
| `properties/views/*.py` | `properties/presentation/views/` | `presentation/views/` | Move views | 8 hours | Medium | Low |
| `properties/serializers/*.py` | `properties/presentation/serializers/` | `presentation/serializers/` | Move serializers | 4 hours | Low | Low |
| `properties/services/*.py` | Split into `properties/domain/*/services/` and `properties/application/` | `domain/`, `application/` per service | Refactor services into domain + application | 24 hours | High | High |
| `properties/repositories/*.py` | `properties/domain/*/repositories/` (interfaces) + `properties/infrastructure/repositories/` (implementations) | `domain/*/repositories/`, `infrastructure/repositories/` | Add protocol interfaces, move implementations | 12 hours | Medium | Medium |
| `properties/policies/unit_policy.py` | `properties/domain/*/policies/` | `domain/*/policies/` per aggregate | Add missing policies | 16 hours | Medium | Low |
| `properties/signals/` | `properties/domain/*/events/` + explicit handlers | `domain/*/events/` per aggregate | Replace signals with domain events | 16 hours | High | High |
| `properties/cron/` | `properties/application/tasks/` | `application/tasks/` | Move cron tasks | 4 hours | Low | Low |
| `properties/communication/` | `properties/application/` or move to `notification` | N/A | Evaluate and move | 8 hours | Medium | Medium |
| `properties/templates/pdf/` | `documents/templates/pdf/` | N/A | Move PDF templates | 4 hours | Low | Low |
| `properties/utils/` | `shared/utils/` or `properties/domain/*/utils/` | N/A | Move utilities | 4 hours | Low | Low |
| `properties/tests/` | `properties/tests/domain/`, `properties/tests/application/`, etc. | `tests/` subfolders | Reorganize tests | 12 hours | Medium | Low |

#### `finance/`

| Current Structure | Target Structure | Missing Folders | Files Requiring Relocation | Estimated Effort | Migration Complexity | Risk |
|-------------------|------------------|-----------------|---------------------------|------------------|---------------------|------|
| `finance/models.py` | `finance/domain/ca/entities/`, `finance/domain/tax/entities/` | `domain/` subfolders | Move models to domain entities | 8 hours | Medium | Low |
| `finance/views.py` | `finance/presentation/views/` | `presentation/views/` | Move views | 4 hours | Low | Low |
| `finance/serializers.py` | `finance/presentation/serializers/` | `presentation/serializers/` | Move serializers | 2 hours | Low | Low |
| `finance/utils.py` (tax calc + PDF) | `finance/domain/tax/services/` + move PDF to `documents/` | `domain/tax/services/` | Split tax calc from PDF generation | 8 hours | Medium | Medium |
| `finance/templates/pdf_templates/` | `documents/templates/pdf/` | N/A | Move templates | 2 hours | Low | Low |
| `finance/tests/` | `finance/tests/domain/`, `finance/tests/application/`, etc. | `tests/` subfolders | Reorganize tests | 6 hours | Medium | Low |

#### `notification/`

| Current Structure | Target Structure | Missing Folders | Files Requiring Relocation | Estimated Effort | Migration Complexity | Risk |
|-------------------|------------------|-----------------|---------------------------|------------------|---------------------|------|
| `notification/models.py` | `notification/domain/notification/entities/`, `notification/domain/device_token/entities/` | `domain/` subfolders | Move models | 6 hours | Medium | Low |
| `notification/views.py` | `notification/presentation/views/` | `presentation/views/` | Move views | 4 hours | Low | Low |
| `notification/services/*.py` | Split: channels → `notification/infrastructure/adapters/`, orchestration → `notification/domain/notification/services/` | `infrastructure/adapters/channels/`, `domain/notification/services/` | Restructure services | 20 hours | High | High |
| `notification/utils.py` | Delete after consolidation | N/A | Remove duplicate WhatsApp | 2 hours | Low | Low |
| `notification/management/commands/` | `notification/application/tasks/` | `application/tasks/` | Move commands | 4 hours | Low | Low |
| `notification/tests/` | `notification/tests/domain/`, `notification/tests/infrastructure/`, etc. | `tests/` subfolders | Reorganize tests | 8 hours | Medium | Low |

#### `smartbot/` + `ai_assistant/` → `assistant/`

| Current Structure | Target Structure | Missing Folders | Files Requiring Relocation | Estimated Effort | Migration Complexity | Risk |
|-------------------|------------------|-----------------|---------------------------|------------------|---------------------|------|
| `smartbot/models.py` | `assistant/domain/chat/entities/`, `assistant/domain/alert/entities/` | `domain/` subfolders | Move models | 6 hours | Medium | Low |
| `smartbot/views.py` | `assistant/presentation/views/` | `presentation/views/` | Move views | 4 hours | Low | Low |
| `smartbot/services/gpt_services.py` | `assistant/domain/llm/services/` | `domain/llm/services/` | Move and refactor | 8 hours | Medium | Medium |
| `smartbot/services/chatbot_service.py` | `assistant/domain/chatbot/services/` | `domain/chatbot/services/` | Move and refactor | 8 hours | Medium | Medium |
| `smartbot/services/leegality_service.py` | `documents/infrastructure/adapters/leegality.py` | N/A | Move to documents | 8 hours | Medium | Medium |
| `smartbot/services/agreement_service.py` | `documents/domain/agreement/services/` + `documents/infrastructure/` | N/A | Move to documents | 8 hours | Medium | Medium |
| `smartbot/actions.py` | Split: operational → domain apps, AI → `assistant/domain/` | N/A | Split and redistribute | 16 hours | High | High |
| `smartbot/whatsapp_service.py` | Merge into `notification/infrastructure/adapters/whatsapp.py` | N/A | Merge and delete | 4 hours | Medium | Medium |
| `smartbot/intents.py` | `assistant/domain/intent/` | `domain/intent/` | Move and refactor | 6 hours | Medium | Low |
| `smartbot/tasks.py` | Archive (no-op stub) | N/A | Archive | 1 hour | Low | None |
| `smartbot/cron/reminders.py` | `documents/application/tasks/` or `properties/application/tasks/` | N/A | Move | 4 hours | Low | Low |
| `ai_assistant/services/archive_service.py` | `properties/domain/renter/services/` | N/A | Move to properties | 8 hours | Medium | Medium |
| `ai_assistant/services/invoice_service.py` | `documents/domain/invoice/services/` | N/A | Move to documents | 8 hours | Medium | Medium |
| `ai_assistant/services/unit_service.py` | `properties/domain/unit/services/` | N/A | Move to properties | 8 hours | Medium | Medium |
| `ai_assistant/services/i18n_service.py` | Delete (duplicate of `rentsecure_be/services/i18n_service.py`) | N/A | Delete after consolidation | 1 hour | Low | None |
| `ai_assistant/services/finance_ai.py` | Evaluate: `assistant/domain/finance/services/` or archive | N/A | Evaluate with product | 4 hours | Low | Low |
| `ai_assistant/models.py` | Delete (empty placeholder) | N/A | Delete | 1 hour | Low | None |
| `ai_assistant/views.py` | Move AI-related views to `assistant/presentation/views/` | N/A | Move and merge | 8 hours | Medium | Medium |
| `ai_assistant/receivers.py` | Replace with domain events | N/A | Remove | 2 hours | Low | Low |
| `smartbot/tests/`, `ai_assistant/tests/` | `assistant/tests/domain/`, `assistant/tests/application/`, etc. | `tests/` subfolders | Reorganize tests | 8 hours | Medium | Low |

#### `documents/`

| Current Structure | Target Structure | Missing Folders | Files Requiring Relocation | Estimated Effort | Migration Complexity | Risk |
|-------------------|------------------|-----------------|---------------------------|------------------|---------------------|------|
| `documents/views.py` | `documents/presentation/views/` | `presentation/views/` | Move views | 4 hours | Low | Low |
| `documents/utils.py` | `documents/infrastructure/pdf_generator.py` or `documents/domain/pdf/` | `infrastructure/` or `domain/pdf/` | Move and unify with other PDF code | 8 hours | Medium | Medium |
| `documents/templates/pdf_templates/` | `documents/templates/pdf/` | N/A | Rename folder | 1 hour | Low | None |
| `documents/tests/` | `documents/tests/domain/`, `documents/tests/infrastructure/`, etc. | `tests/` subfolders | Reorganize tests | 4 hours | Low | Low |

#### `referral_and_earn/` → `referral/`

| Current Structure | Target Structure | Missing Folders | Files Requiring Relocation | Estimated Effort | Migration Complexity | Risk |
|-------------------|------------------|-----------------|---------------------------|------------------|---------------------|------|
| `referral_and_earn/models.py` | `referral/domain/referral/entities/` | `domain/` subfolders | Move models | 4 hours | Low | Low |
| `referral_and_earn/signals.py` | `referral/domain/referral/events/` + handlers | `domain/events/` | Replace signals with domain events | 4 hours | Medium | Medium |
| No services | `referral/domain/referral/services/`, `referral/application/` | `domain/`, `application/` | Add services | 8 hours | Medium | Low |
| No views | `referral/presentation/views/` | `presentation/views/` | Add views | 4 hours | Low | Low |
| No tests | `referral/tests/` | `tests/` subfolders | Add tests | 4 hours | Low | Low |
| App rename | `referral/` | N/A | Rename directory + update `INSTALLED_APPS` | 2 hours | Low | Low |

#### `dashboard/` → `analytics/`

| Current Structure | Target Structure | Missing Folders | Files Requiring Relocation | Estimated Effort | Migration Complexity | Risk |
|-------------------|------------------|-----------------|---------------------------|------------------|---------------------|------|
| `dashboard/views.py` (no `apps.py`) | `analytics/presentation/views/` | Full app structure | Move views, add `apps.py` | 8 hours | Medium | Medium |
| `dashboard/urls.py` | `analytics/urls.py` | N/A | Move URLs | 2 hours | Low | Low |
| `dashboard/tests.py` | `analytics/tests/` | `tests/` subfolders | Reorganize tests | 4 hours | Low | Low |
| No models | `analytics/domain/` (read models only) | `domain/`, `application/`, `infrastructure/` | Add read models | 12 hours | Medium | Medium |
| Scattered analytics in `properties/` and `core/` | Move to `analytics/` | N/A | Move analytics code | 16 hours | High | Medium |

#### `rentsecure_be/` (project-level)

| Current Structure | Target Structure | Missing Folders | Files Requiring Relocation | Estimated Effort | Migration Complexity | Risk |
|-------------------|------------------|-----------------|---------------------------|------------------|---------------------|------|
| `rentsecure_be/services/razorpay_service.py` | `payments/infrastructure/adapters/razorpay.py` | `payments/` app + `infrastructure/adapters/` | Move to payments | 8 hours | Medium | Medium |
| `rentsecure_be/services/cashfree_service.py` | `payments/infrastructure/adapters/cashfree.py` | `payments/` app + `infrastructure/adapters/` | Move to payments | 8 hours | Medium | Medium |
| `rentsecure_be/services/leegality_service.py` | `documents/infrastructure/adapters/leegality.py` | N/A | Move to documents | 8 hours | Medium | Medium |
| `rentsecure_be/services/i18n_service.py` | `shared/infrastructure/adapters/translation.py` | N/A | Move to shared | 4 hours | Low | Low |
| `rentsecure_be/utils/cashfree_payout.py` | `payments/infrastructure/adapters/cashfree_payout.py` | `payments/` app | Move to payments | 4 hours | Low | Low |
| `rentsecure_be/tests/` | Move to respective app tests | N/A | Redistribute tests | 4 hours | Low | Low |

#### `shared/`

| Current Structure | Target Structure | Missing Folders | Files Requiring Relocation | Estimated Effort | Migration Complexity | Risk |
|-------------------|------------------|-----------------|---------------------------|------------------|---------------------|------|
| `shared/` (no `apps.py`) | `shared/` (no `apps.py`, keep as-is) | `domain/`, `infrastructure/` | Add `domain/events/`, `domain/value_objects/`, `infrastructure/` | 12 hours | Low | Low |
| `shared/domain_events.py` | `shared/domain/events/` | `domain/events/` | Move and enhance | 4 hours | Low | Low |
| `shared/interfaces.py` | `shared/domain/ports/` | `domain/ports/` | Move and expand | 4 hours | Low | Low |
| `shared/validators.py` | `shared/domain/value_objects/` or keep | N/A | Keep or move | 2 hours | Low | None |

---

## 27. Implementation Roadmap

### Top 100 Implementation Tasks (Easiest to Hardest)

| # | Task | Priority | Risk | Est. Hours | Dependencies | Rollback Difficulty | Files Affected |
|---|------|----------|------|------------|-------------|---------------------|----------------|
| 1 | Rename `referral_and_earn/` → `referral/` | High | Low | 2 | None | Easy | `INSTALLED_APPS`, imports |
| 2 | Add `apps.py` to `dashboard/` | High | Low | 2 | None | Easy | `dashboard/apps.py` |
| 3 | Archive `smartbot/tasks.py` | Low | None | 1 | None | Easy | `smartbot/tasks.py` |
| 4 | Delete `ai_assistant/models.py` (empty) | Low | None | 1 | None | Easy | `ai_assistant/models.py` |
| 5 | Delete `ai_assistant/services/i18n_service.py` (duplicate) | High | Low | 1 | ADR-003 | Easy | `ai_assistant/services/i18n_service.py` |
| 6 | Consolidate WhatsApp in `notification/` | High | Low | 4 | ADR-003 | Easy | `notification/utils.py`, `notification/services/whatsapp_service.py` |
| 7 | Move `rentsecure_be/services/i18n_service.py` → `shared/` | High | Low | 4 | ADR-003 | Easy | `rentsecure_be/services/i18n_service.py`, `shared/` |
| 8 | Move `core/services/owner_reporting_service.py` → `properties/services/` | High | Low | 4 | ADR-003 | Easy | `core/services/owner_reporting_service.py`, `core/views.py` |
| 9 | Fix unconditional imports in `core/views.py` | High | Medium | 4 | Feature flags | Medium | `core/views.py` |
| 10 | Fix unconditional imports in `properties/views/` | High | Medium | 8 | Feature flags | Medium | `properties/views/*.py` |
| 11 | Create `payments/` Django app | High | Low | 4 | None | Easy | New app |
| 12 | Create `assistant/` Django app | High | Medium | 4 | None | Easy | New app |
| 13 | Create `analytics/` Django app | High | Low | 4 | None | Easy | New app |
| 14 | Create `infrastructure/` Django app | High | Low | 4 | None | Easy | New app |
| 15 | Configure `import-linter` | High | Low | 8 | None | Easy | `.importlinter/` config |
| 16 | Add `domain/` folder structure to `core/` | High | Medium | 8 | None | Medium | `core/domain/` |
| 17 | Add `domain/` folder structure to `properties/` | High | Medium | 16 | None | Medium | `properties/domain/` |
| 18 | Add `domain/` folder structure to `finance/` | High | Low | 8 | None | Medium | `finance/domain/` |
| 19 | Add `domain/` folder structure to `notification/` | High | Medium | 12 | None | Medium | `notification/domain/` |
| 20 | Add `domain/` folder structure to `documents/` | High | Low | 8 | None | Medium | `documents/domain/` |
| 21 | Add `domain/` folder structure to `referral/` | High | Low | 4 | None | Medium | `referral/domain/` |
| 22 | Add `domain/` folder structure to `assistant/` | High | Medium | 12 | None | Medium | `assistant/domain/` |
| 23 | Add `domain/` folder structure to `payments/` | High | Medium | 12 | None | Medium | `payments/domain/` |
| 24 | Create `shared/domain/events/` with base event classes | High | Low | 8 | None | Easy | `shared/domain/events/` |
| 25 | Create `shared/domain/value_objects/` with base VOs | High | Low | 8 | None | Easy | `shared/domain/value_objects/` |
| 26 | Create event bus implementation | High | Medium | 16 | #24 | Medium | `shared/domain/events/bus.py` |
| 27 | Create base repository protocol in `shared/` | High | Low | 4 | None | Easy | `shared/interfaces.py` |
| 28 | Create base service protocols in `shared/` | High | Low | 4 | None | Easy | `shared/interfaces.py` |
| 29 | Add `application/` folder to `core/` | High | Medium | 8 | #16 | Medium | `core/application/` |
| 30 | Add `application/` folder to `properties/` | High | Medium | 12 | #17 | Medium | `properties/application/` |
| 31 | Add `application/` folder to `notification/` | High | Medium | 8 | #19 | Medium | `notification/application/` |
| 32 | Add `application/` folder to `documents/` | High | Low | 4 | #20 | Medium | `documents/application/` |
| 33 | Add `application/` folder to `assistant/` | High | Medium | 8 | #22 | Medium | `assistant/application/` |
| 34 | Add `application/` folder to `payments/` | High | Medium | 8 | #23 | Medium | `payments/application/` |
| 35 | Add `infrastructure/` folder to `core/` | High | Medium | 8 | #16 | Medium | `core/infrastructure/` |
| 36 | Add `infrastructure/` folder to `properties/` | High | Medium | 12 | #17 | Medium | `properties/infrastructure/` |
| 37 | Add `infrastructure/` folder to `finance/` | High | Low | 4 | #18 | Medium | `finance/infrastructure/` |
| 38 | Add `infrastructure/` folder to `notification/` | High | Medium | 8 | #19 | Medium | `notification/infrastructure/` |
| 39 | Add `infrastructure/` folder to `documents/` | High | Low | 4 | #20 | Medium | `documents/infrastructure/` |
| 40 | Add `infrastructure/` folder to `assistant/` | High | Medium | 8 | #22 | Medium | `assistant/infrastructure/` |
| 41 | Add `infrastructure/` folder to `payments/` | High | Medium | 8 | #23 | Medium | `payments/infrastructure/` |
| 42 | Add `presentation/` folder to `core/` | High | Medium | 8 | #16 | Medium | `core/presentation/` |
| 43 | Add `presentation/` folder to `properties/` | High | Medium | 12 | #17 | Medium | `properties/presentation/` |
| 44 | Add `presentation/` folder to `finance/` | High | Low | 4 | #18 | Medium | `finance/presentation/` |
| 45 | Add `presentation/` folder to `notification/` | High | Medium | 8 | #19 | Medium | `notification/presentation/` |
| 46 | Add `presentation/` folder to `documents/` | High | Low | 4 | #20 | Medium | `documents/presentation/` |
| 47 | Add `presentation/` folder to `assistant/` | High | Medium | 8 | #22 | Medium | `assistant/presentation/` |
| 48 | Add `presentation/` folder to `payments/` | High | Medium | 8 | #23 | Medium | `payments/presentation/` |
| 49 | Move `smartbot/services/gpt_services.py` → `assistant/domain/llm/services/` | High | Medium | 8 | #12, #22 | Medium | `smartbot/services/gpt_services.py` |
| 50 | Move `smartbot/services/chatbot_service.py` → `assistant/domain/chatbot/services/` | High | Medium | 8 | #12, #22 | Medium | `smartbot/services/chatbot_service.py` |
| 51 | Move `smartbot/intents.py` → `assistant/domain/intent/` | High | Low | 4 | #12, #22 | Medium | `smartbot/intents.py` |
| 52 | Move `smartbot/views.py` → `assistant/presentation/views/` | High | Low | 4 | #12, #47 | Medium | `smartbot/views.py` |
| 53 | Move `smartbot/models.py` → `assistant/domain/chat/entities/` | High | Low | 6 | #12, #22 | Medium | `smartbot/models.py` |
| 54 | Move `ai_assistant/services/archive_service.py` → `properties/domain/renter/services/` | High | Medium | 8 | #17 | Medium | `ai_assistant/services/archive_service.py` |
| 55 | Move `ai_assistant/services/unit_service.py` → `properties/domain/unit/services/` | High | Medium | 8 | #17 | Medium | `ai_assistant/services/unit_service.py` |
| 56 | Move `ai_assistant/services/invoice_service.py` → `documents/domain/invoice/services/` | High | Medium | 8 | #20 | Medium | `ai_assistant/services/invoice_service.py` |
| 57 | Move `ai_assistant/views.py` → `assistant/presentation/views/` | High | Medium | 8 | #12, #47 | Medium | `ai_assistant/views.py` |
| 58 | Move `smartbot/services/leegality_service.py` → `documents/infrastructure/adapters/leegality.py` | High | Medium | 8 | #20, #39 | Medium | `smartbot/services/leegality_service.py` |
| 59 | Move `rentsecure_be/services/leegality_service.py` → `documents/infrastructure/adapters/leegality.py` | High | Medium | 8 | #11, #39 | Medium | `rentsecure_be/services/leegality_service.py` |
| 60 | Consolidate Leegality implementations | High | High | 16 | #58, #59 | Hard | Both leegality files |
| 61 | Move `smartbot/services/agreement_service.py` → `documents/domain/agreement/services/` | High | Medium | 8 | #20 | Medium | `smartbot/services/agreement_service.py` |
| 62 | Move `smartbot/whatsapp_service.py` → merge into `notification/infrastructure/adapters/whatsapp.py` | High | Medium | 8 | #19, #38 | Medium | `smartbot/whatsapp_service.py` |
| 63 | Split `smartbot/actions.py` operational actions → domain apps | High | High | 16 | #12, #17 | Hard | `smartbot/actions.py` |
| 64 | Move `properties/utils/utils.py` PDF functions → `documents/` | High | Medium | 8 | #20 | Medium | `properties/utils/utils.py` |
| 65 | Move `finance/utils.py` PDF functions → `documents/` | High | Medium | 4 | #20 | Medium | `finance/utils.py` |
| 66 | Move `properties/templates/pdf/` → `documents/templates/pdf/` | High | Low | 4 | #20 | Easy | `properties/templates/` |
| 67 | Move `finance/templates/pdf_templates/` → `documents/templates/pdf/` | High | Low | 2 | #20 | Easy | `finance/templates/` |
| 68 | Create `payments/domain/payment/ports/payment_gateway.py` | High | Low | 4 | #23 | Easy | New file |
| 69 | Create `payments/infrastructure/adapters/manual.py` | High | Low | 8 | #11, #41 | Medium | New file |
| 70 | Move `rentsecure_be/services/razorpay_service.py` → `payments/infrastructure/adapters/razorpay.py` | High | Medium | 8 | #11, #41 | Medium | `rentsecure_be/services/razorpay_service.py` |
| 71 | Move `rentsecure_be/services/cashfree_service.py` → `payments/infrastructure/adapters/cashfree.py` | High | Medium | 8 | #11, #41 | Medium | `rentsecure_be/services/cashfree_service.py` |
| 72 | Move `rentsecure_be/utils/cashfree_payout.py` → `payments/infrastructure/adapters/cashfree_payout.py` | High | Medium | 4 | #11, #41 | Medium | `rentsecure_be/utils/cashfree_payout.py` |
| 73 | Move `notification/services/rent_notify_service.py` → `properties/domain/notification/services/` | High | Medium | 8 | #17, #19 | Medium | `notification/services/rent_notify_service.py` |
| 74 | Move `notification/services/extra_charge_reminders.py` → `properties/domain/notification/services/` | High | Medium | 8 | #17, #19 | Medium | `notification/services/extra_charge_reminders.py` |
| 75 | Move `notification/services/late_fees_notify_service.py` → `properties/domain/notification/services/` | High | Medium | 8 | #17, #19 | Medium | `notification/services/late_fees_notify_service.py` |
| 76 | Replace `core/signals.py` with domain events + handlers | High | High | 12 | #24, #29 | Hard | `core/signals.py` |
| 77 | Replace `properties/signals/` with domain events + handlers | High | High | 16 | #24, #30 | Hard | `properties/signals/__init__.py` |
| 78 | Replace `referral_and_earn/signals.py` with domain events + handlers | High | Medium | 8 | #24, #21 | Medium | `referral_and_earn/signals.py` |
| 79 | Create `properties/domain/renter/entities/renter.py` (VO-based) | High | Medium | 8 | #17 | Medium | `properties/models/renter_models.py` |
| 80 | Create `properties/domain/unit/entities/unit.py` (VO-based) | High | Medium | 8 | #17 | Medium | `properties/models/unit_models.py` |
| 81 | Create `properties/domain/building/entities/building.py` (VO-based) | High | Medium | 8 | #17 | Medium | `properties/models/building_models.py` |
| 82 | Create `properties/domain/rent/entities/rent_record.py` (VO-based) | High | Medium | 8 | #17 | Medium | `properties/models/rent_record_models.py` |
| 83 | Create `core/domain/user/entities/user.py` (VO-based) | High | Medium | 8 | #16 | Medium | `core/models.py` |
| 84 | Create `core/domain/subscription/entities/` | High | Medium | 8 | #16 | Medium | `core/models.py` |
| 85 | Add `RenterPolicy`, `BuildingPolicy`, `RentRecordPolicy`, `ExtraChargePolicy` | High | Low | 12 | #17 | Medium | `properties/policies/` |
| 86 | Add `UserPolicy`, `SubscriptionPolicy` | High | Low | 8 | #16 | Medium | `core/policies/` |
| 87 | Create `notification/domain/channel/ports/channel.py` | High | Low | 4 | #19 | Easy | New file |
| 88 | Create `documents/domain/pdf/ports/pdf_generator.py` | High | Low | 4 | #20 | Easy | New file |
| 89 | Create `documents/domain/esignature/ports/esignature_provider.py` | High | Low | 4 | #20 | Easy | New file |
| 90 | Create `assistant/domain/llm/ports/llm_client.py` | High | Low | 4 | #22 | Easy | New file |
| 91 | Create `shared/domain/infrastructure/ports/cache_service.py` | High | Low | 4 | None | Easy | New file |
| 92 | Create `shared/domain/infrastructure/ports/audit_logger.py` | High | Low | 4 | None | Easy | New file |
| 93 | Create `shared/domain/infrastructure/ports/metrics_service.py` | High | Low | 4 | None | Easy | New file |
| 94 | Implement `EventBus` with idempotency | High | High | 16 | #26 | Hard | `shared/domain/events/bus.py` |
| 95 | Implement domain event handlers for all events | High | High | 24 | #94 | Hard | Per-module handlers |
| 96 | Create `OwnerDashboardReadModel` | High | Medium | 12 | #13 | Medium | `analytics/read-models/` |
| 97 | Create `RentAnalyticsReadModel` | High | Medium | 12 | #13 | Medium | `analytics/read-models/` |
| 98 | Implement health check endpoints | High | Medium | 8 | #14 | Medium | `infrastructure/health/` |
| 99 | Implement structured JSON logging | High | Medium | 12 | #14 | Medium | `infrastructure/logging/` |
| 100 | Implement Prometheus metrics | High | Medium | 12 | #14 | Medium | `infrastructure/metrics/` |

### Recommended Implementation Phases

#### Phase 1: Foundation & Safety (Weeks 1-4)

**Goal:** Establish foundational structure and fix critical risks without breaking existing functionality.

| Task # | Task | Risk |
|--------|------|------|
| 1 | Rename `referral_and_earn/` → `referral/` | Low |
| 2 | Add `apps.py` to `dashboard/` | Low |
| 3 | Archive `smartbot/tasks.py` | None |
| 4 | Delete `ai_assistant/models.py` (empty) | None |
| 5 | Delete `ai_assistant/services/i18n_service.py` (duplicate) | Low |
| 6 | Consolidate WhatsApp in `notification/` | Low |
| 7 | Move `rentsecure_be/services/i18n_service.py` → `shared/` | Low |
| 8 | Move `core/services/owner_reporting_service.py` → `properties/services/` | Low |
| 15 | Configure `import-linter` | Low |
| 27 | Create base repository protocol in `shared/` | Low |
| 28 | Create base service protocols in `shared/` | Low |

**Deliverables:**
- `referral/` app renamed
- `dashboard/` has `apps.py`
- Duplicate i18n and WhatsApp consolidated
- `import-linter` configured
- Base protocols established

#### Phase 2: App Creation & Layer Structure (Weeks 5-10)

**Goal:** Create missing apps and establish 4-layer structure per module.

| Task # | Task | Risk |
|--------|------|------|
| 11 | Create `payments/` Django app | Low |
| 12 | Create `assistant/` Django app | Medium |
| 13 | Create `analytics/` Django app | Low |
| 14 | Create `infrastructure/` Django app | Low |
| 16 | Add `domain/` folder to `core/` | Medium |
| 17 | Add `domain/` folder to `properties/` | Medium |
| 18 | Add `domain/` folder to `finance/` | Low |
| 19 | Add `domain/` folder to `notification/` | Medium |
| 20 | Add `domain/` folder to `documents/` | Low |
| 21 | Add `domain/` folder to `referral/` | Low |
| 22 | Add `domain/` folder to `assistant/` | Medium |
| 23 | Add `domain/` folder to `payments/` | Medium |
| 24 | Create `shared/domain/events/` with base event classes | Low |
| 25 | Create `shared/domain/value_objects/` with base VOs | Low |
| 29-48 | Add `application/`, `infrastructure/`, `presentation/` folders to all apps | Medium |

**Deliverables:**
- All target apps created
- 4-layer folder structure established in all apps
- Base event and value object classes created

#### Phase 3: Core Domain Extraction (Weeks 11-18)

**Goal:** Extract pure domain models, value objects, and domain services.

| Task # | Task | Risk |
|--------|------|------|
| 79 | Create `properties/domain/renter/entities/renter.py` (VO-based) | Medium |
| 80 | Create `properties/domain/unit/entities/unit.py` (VO-based) | Medium |
| 81 | Create `properties/domain/building/entities/building.py` (VO-based) | Medium |
| 82 | Create `properties/domain/rent/entities/rent_record.py` (VO-based) | Medium |
| 83 | Create `core/domain/user/entities/user.py` (VO-based) | Medium |
| 84 | Create `core/domain/subscription/entities/` | Medium |
| 85 | Add `RenterPolicy`, `BuildingPolicy`, `RentRecordPolicy`, `ExtraChargePolicy` | Low |
| 86 | Add `UserPolicy`, `SubscriptionPolicy` | Low |
| 49-56 | Move smartbot/ai_assistant services to target modules | Medium |
| 57-63 | Split smartbot/actions.py and move to domain apps | High |

**Deliverables:**
- Pure domain entities with value objects
- Domain services extracted
- Policies implemented
- Smartbot/ai_assistant merged into `assistant/`

#### Phase 4: Application Services & Ports (Weeks 19-26)

**Goal:** Create application services, ports, and adapters.

| Task # | Task | Risk |
|--------|------|------|
| 11-48 | Application services in all modules | Medium |
| 68-93 | Create all ports and adapters | Medium |
| 58-65 | Move and consolidate Leegality, PDF, WhatsApp | Medium |
| 73-75 | Move property notifications to `properties/` | Medium |

**Deliverables:**
- Application services orchestrate use cases
- All external integrations behind ports
- PDF generation consolidated in `documents/`
- Notifications restructured

#### Phase 5: Events & Integration (Weeks 27-34)

**Goal:** Replace signals with domain events and implement integration events.

| Task # | Task | Risk |
|--------|------|------|
| 76 | Replace `core/signals.py` with domain events | High |
| 77 | Replace `properties/signals/` with domain events | High |
| 78 | Replace `referral_and_earn/signals.py` with domain events | Medium |
| 94 | Implement `EventBus` with idempotency | High |
| 95 | Implement domain event handlers | High |

**Deliverables:**
- All Django signals replaced with domain events
- Event bus with idempotency and correlation IDs
- Integration events for cross-module communication

#### Phase 6: Read Models & Analytics (Weeks 35-40)

**Goal:** Implement read models for analytics and dashboard.

| Task # | Task | Risk |
|--------|------|------|
| 13 | `analytics/` app created (Phase 2) | Low |
| 96 | Create `OwnerDashboardReadModel` | Medium |
| 97 | Create `RentAnalyticsReadModel` | Medium |
| Move scattered analytics from `properties/` and `core/` | High |

**Deliverables:**
- `analytics/` app with read models
- Dashboard data served from denormalized projections
- Analytics queries isolated from transactional queries

#### Phase 7: Observability & Security (Weeks 41-48)

**Goal:** Implement observability, security, and operational concerns.

| Task # | Task | Risk |
|--------|------|------|
| 98 | Implement health check endpoints | Medium |
| 99 | Implement structured JSON logging | Medium |
| 100 | Implement Prometheus metrics | Medium |
| Add OpenTelemetry tracing | High |
| Add Sentry integration | Low |
| Implement webhook signature verification | Medium |
| Implement rate limiting | Medium |
| Implement audit logging | Medium |

**Deliverables:**
- Structured logging with correlation IDs
- Prometheus metrics
- Health checks
- Webhook security
- Rate limiting
- Audit logging

#### Phase 8: Testing & Quality (Weeks 49-52)

**Goal:** Reorganize tests, enforce coverage, and validate architecture.

| Task # | Task | Risk |
|--------|------|------|
| Reorganize all tests per layer | Medium |
| Add unit tests for domain layer | Medium |
| Add integration tests for application layer | Medium |
| Add contract tests for adapters | Medium |
| Enforce `mypy --strict` | Low |
| Enforce `ruff check` | Low |
| Run full test suite | Low |

**Deliverables:**
- Tests organized per layer
- ≥90% coverage for domain and application layers
- All linting/type checking passes

---

## Appendix A: Dependency Enforcement Checklist

Before any migration phase begins:

- [ ] `import-linter` is configured and passing in CI
- [ ] All new imports follow the dependency matrix
- [ ] No circular dependencies exist
- [ ] Domain layer has zero Django/DRF imports
- [ ] Application layer has zero Django ORM imports
- [ ] No cross-module model imports

## Appendix B: Migration Validation Checklist

After each migration phase:

- [ ] All tests pass (`pytest`)
- [ ] No new mypy errors (`mypy --strict`)
- [ ] No new ruff errors (`ruff check`)
- [ ] Django system checks pass (`python manage.py check`)
- [ ] No new DeprecationWarnings
- [ ] `import-linter` passes
- [ ] Manual smoke test of affected endpoints
- [ ] No breaking API changes
- [ ] Documentation updated

## Appendix C: Rollback Triggers

Rollback immediately if:

1. More than 5% of tests fail after a phase
2. Production error rate increases by >10%
3. Any endpoint returns 500 for >1% of requests
4. Database migration fails
5. `import-linter` violations are introduced
6. Any security control is weakened

---

*Document generated by Kilo Architecture Gap Analysis. This is an analysis document only. No production code was modified.*
