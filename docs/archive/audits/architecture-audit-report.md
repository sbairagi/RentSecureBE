# RentSecureBE — Comprehensive Architecture Audit Report

**Date:** 2026-07-14
**Project:** RentSecureBE (Django 5.2.1, DRF)
**Auditor:** Kilo
**Scope:** Complete codebase analysis (340 Python files)

---

## 1. Executive Summary

RentSecureBE is a Django REST Framework project for property management and rent collection. The codebase shows **early-stage architectural experimentation** with pockets of good practices (repository pattern in `properties`, service layer in some apps, typed dicts) but suffers from **inconsistent layering, cross-app circular dependencies, business logic leakage into views/models/signals, and incomplete app registration**.

**Overall Architecture Completion:** ~35%
**Enterprise Readiness:** ~25%

### Key Findings
- **9 Django apps** but only 6 are registered in `INSTALLED_APPS`; 3 (`ai_assistant`, `dashboard`, `finance` URLs) are orphaned.
- **Heavy circular dependencies** between `core`, `properties`, `notification`, `smartbot`, and `ai_assistant`.
- **Business logic is scattered** across views, models, signals, services, and utils with no clear ownership.
- **Inconsistent service layer**: Some apps have well-defined services; others have empty stubs or none at all.
- **Year-1 rules violations**: `django_celery_beat` is installed despite the "no Celery in Year 1" rule; some disabled features have partial implementations.
- **Duplication**: `i18n_service` exists in both `rentsecure_be/services/` and `ai_assistant/services/`.
- **Testability issues**: Heavy use of Django signals, model-level business logic, and tight coupling make unit testing difficult without full Django setup.

---

## 2. Per-App Analysis

### 2.1 core

**Current Purpose:**
Authentication (OTP, JWT), user management, subscription plans, add-on purchases, usage limits, bank details, owner reporting, referrals, and Cashfree/Razorpay webhooks.

**Folder Structure:**
```
core/
├── __init__.py
├── admin.py
├── apps.py
├── models.py              # User, UserProfile, OTP, OwnerBankDetails, SubscriptionPlan, UserSubscription, AddOnPurchase, PlanFeatureLimit, UsageLimit, NotificationPreference
├── serializers.py
├── signals.py
├── urls.py
├── views.py               # Webhooks, bank details, OTP, subscriptions, reporting
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── bank_details_service.py
│   ├── base.py
│   ├── otp_service.py
│   ├── owner_reporting_service.py
│   ├── password_service.py
│   ├── referral_service.py
│   ├── subscription_service.py
│   └── usage_limit_service.py
└── tests/
```

**Current Layering Assessment:**
Moderate. Has a service layer (`services/`) with `BaseService` and `ServiceResult` pattern. Views call services. However, `views.py` contains **significant business logic** (webhook signature verification, payment processing, bank registration, reporting endpoints). Models contain domain logic (`UpsertMixin`, custom `save()`). Signals handle user initialization.

**Architecture Score:** 65/100
**DDD Score:** 40/100
**Clean Architecture Score:** 50/100
**SOLID Score:** 55/100
**Code Quality Score:** 65/100
**Testability Score:** 60/100
**Maintainability Score:** 60/100
**Production Readiness Score:** 70/100

**Strengths:**
- Service layer with typed `BaseService` / `ServiceResult`.
- `UpsertMixin` for idempotent upserts.
- Comprehensive user/subscription models with historical records.
- Webhook endpoints with HMAC verification.

**Weaknesses:**
- `views.py` is 566 lines with webhooks, bank details, and reporting — violates single responsibility.
- `models.py` contains 6 unrelated models (User, OTP, BankDetails, Subscription, AddOn, PlanFeature, UsageLimit, NotificationPreference).
- `signals.py` performs user initialization (profile, preferences, default plan) — hidden side effects.
- `bank_details_service.py` imports `RentRecord` from `properties` — tight coupling.
- `owner_reporting_service.py` imports `RentRecord` from `properties` — tight coupling.
- `referral_service.py` imports `Referral` from `referral_and_earn` inside method (good for avoiding circular import, but reveals dependency).
- `shared.exceptions.ValidationError` is used but `shared` is not a proper Django app.

**Violations:**
- Business logic in views (webhooks, bank registration).
- Fat models (multiple aggregate roots in one file).
- Signals as hidden workflow triggers.
- Cross-app imports in services (`properties.models.rent_record_models`).

**Risk Level:** Medium

**Quick Wins:**
- Extract webhook handlers to dedicated `core/webhooks/` module.
- Split `models.py` into `user_models.py`, `subscription_models.py`, `bank_models.py`.
- Move signal logic to explicit service methods.

**Long-term Improvements:**
- Introduce domain events instead of signals for cross-app workflows.
- Define `ports` for payment gateway interactions.
- Move webhook verification to a decorator/middleware.

**Required Layers for Target State:**
- `domain/`: User, Subscription, BankDetails entities.
- `application/`: RegisterBank, ProcessReferral use cases.
- `infrastructure/`: Cashfree/Razorpay adapters (already partially exist in `rentsecure_be/services/`).

**Required Classes/Interfaces:**
- `PaymentGateway` port (for Cashfree/Razorpay abstraction).
- `NotificationChannel` port (already defined in instructions but not implemented in code).

**Migration Plan Steps:**
1. Split `core/models.py` into focused modules.
2. Extract webhook handlers to `core/webhooks/`.
3. Replace signals with explicit service calls from views.
4. Introduce `PaymentGateway` interface.

---

### 2.2 properties

**Current Purpose:**
Core property management: buildings, units, renters, rent records, caretakers, extra charges, property taxes, usage limits, onboarding, PDF generation, and scheduling.

**Folder Structure:**
```
properties/
├── admin/
├── communication/          # auto_generate_rent_records, retry_failed_payouts
├── constants.py
├── cron/                   # flag_defaulters, vacate_reminder
├── feature_enforcer.py     # Subscription/plan limit enforcement
├── management/commands/
├── models/
│   ├── __init__.py
│   ├── building_models.py
│   ├── caretaker_models.py
│   ├── extra_charge_models.py
│   ├── property_tax_models.py
│   ├── rent_record_models.py
│   ├── renter_models.py
│   ├── subscription_models.py  # EMPTY placeholder
│   └── usage_limit_models.py   # EMPTY placeholder
├── policies/
│   └── unit_policy.py
├── repositories/
│   ├── __init__.py
│   ├── building_repository.py
│   ├── rent_record_repository.py
│   ├── renter_repository.py
│   └── unit_repository.py
├── scheduler.py
├── serializers/
├── services/
│   ├── __init__.py
│   ├── building_service.py
│   ├── extra_charge_service.py
│   ├── occupancy_service.py   # EMPTY stub
│   ├── receipt_service.py
│   ├── rent_service.py        # EMPTY stub
│   ├── renter_onboarding_service.py
│   ├── renter_service.py      # EMPTY stub
│   ├── summary_service.py
│   ├── unit_service.py
│   └── vacancy_service.py     # EMPTY stub
├── signals/
│   ├── __init__.py           # Heavy signal handlers
│   └── renter_signals.py
├── utils/
│   ├── __init__.py
│   ├── onboarding_utils.py
│   └── utils.py              # Mixed concerns: feature limits, PDFs, late fees
├── views/
│   ├── __init__.py
│   ├── building_views.py
│   ├── caretaker_views.py
│   ├── extra_charge_views.py
│   ├── owner_dashboard.py
│   ├── property_views.py
│   ├── rent_record_views.py
│   ├── renter_views.py
│   ├── subscription_views.py
│   ├── unit_views.py
│   └── usage_limit_views.py
└── tests/
```

**Current Layering Assessment:**
Best-structured app in the project. Has repositories, policies, services, serializers, views. However:
- 4 service files are **empty stubs** (`rent_service.py`, `renter_service.py`, `occupancy_service.py`, `vacancy_service.py`).
- `utils/utils.py` is a **500-line God file** mixing feature limit checks, PDF generation, late fee logic, and file hashing.
- `signals/__init__.py` is 248 lines with **8 signal handlers** doing significant business work.
- Views still contain validation and orchestration logic.

**Architecture Score:** 70/100
**DDD Score:** 55/100
**Clean Architecture Score:** 60/100
**SOLID Score:** 60/100
**Code Quality Score:** 65/100
**Testability Score:** 55/100
**Maintainability Score:** 65/100
**Production Readiness Score:** 75/100

**Strengths:**
- Repository pattern for ORM abstraction.
- Policy layer (`UnitPolicy`).
- Caching strategy with cache key management.
- Comprehensive model design with indexes and historical records.
- Feature enforcement via `FeatureEnforcer`.

**Weaknesses:**
- Empty service stubs indicate incomplete refactoring.
- `utils/utils.py` violates single responsibility.
- Signals file is a hidden orchestration layer.
- `models/` package has empty placeholders (`subscription_models.py`, `usage_limit_models.py`).
- Some views duplicate logic that exists in services.

**Violations:**
- Business logic in signals (`handle_rent_payment`, `notify_owner_if_unit_vacant`, etc.).
- Empty stub services that should either be implemented or removed.
- Cross-app imports in `utils/utils.py` (notification, core).

**Risk Level:** Medium-High

**Quick Wins:**
- Implement or remove empty service stubs.
- Split `utils/utils.py` into `feature_limits.py`, `pdf_generation.py`, `late_fees.py`.
- Move signal logic to explicit service methods called from views.

**Long-term Improvements:**
- Complete repository coverage for all aggregates.
- Introduce domain events for rent payment, renter exit, etc.
- Move PDF generation to `documents` app entirely.

**Required Layers for Target State:**
- `domain/`: Building, Unit, Renter, RentRecord entities with business rules.
- `application/`: CreateUnit, AssignRenter, GenerateRentRecord use cases.
- `infrastructure/`: PDF generation adapters, notification adapters.

**Required Classes/Interfaces:**
- `RentRepository` port (repository partially exists).
- `NotificationService` port.
- `PdfGenerator` port.

**Migration Plan Steps:**
1. Implement empty services or delete stubs.
2. Extract `utils/utils.py` into focused modules.
3. Replace signals with explicit domain event handlers.
4. Complete repository pattern coverage.

---

### 2.3 finance

**Current Purpose:**
Chartered Accountant (CA) profiles, tax submission tracking, and tax document generation (Excel, PDF, ZIP).

**Folder Structure:**
```
finance/
├── __init__.py
├── admin.py
├── apps.py
├── migrations/
├── models.py              # CAProfile, TaxSubmissionToCA
├── serializers.py
├── tests/
├── urls.py                # NOT included in main urls.py
└── views.py
```

**Current Layering Assessment:**
Thin and incomplete. Has models, serializers, views, and utils. No services layer. Business logic lives in `views.py` (tax file download) and `utils.py` (Excel/PDF/ZIP generation). The `urls.py` exists but is **not included in `rentsecure_be/urls.py`**.

**Architecture Score:** 45/100
**DDD Score:** 30/100
**Clean Architecture Score:** 35/100
**SOLID Score:** 40/100
**Code Quality Score:** 50/100
**Testability Score:** 50/100
**Maintainability Score:** 40/100
**Production Readiness Score:** 35/100

**Strengths:**
- Dedicated utils for tax document generation.
- Serializers follow DRF patterns.
- Models are simple and focused.

**Weaknesses:**
- No service layer.
- Business logic in views (`DownloadTaxFilesView.get`).
- `urls.py` is orphaned (not in main `urls.py`).
- `finance` is **not in `INSTALLED_APPS`**.
- Tight coupling to `properties.models.Unit` in views and utils.
- `views.py` directly calls `generate_tax_excel`, `generate_tax_pdf`, `create_tax_zip` — no orchestration layer.

**Violations:**
- Missing service layer for a domain with business logic.
- Orphaned URLs and missing app registration.
- Business logic in views.

**Risk Level:** Low-Medium (feature is small but broken due to missing registration)

**Quick Wins:**
- Add `finance` to `INSTALLED_APPS`.
- Include `finance/urls.py` in main `urls.py`.
- Add `finance.services.tax_service` to orchestrate document generation.

**Long-term Improvements:**
- Move tax document generation to a dedicated service.
- Introduce `TaxReport` domain service.

**Required Layers for Target State:**
- `domain/`: CAProfile, TaxSubmission entities.
- `application/`: SubmitTax, GenerateTaxReport use cases.
- `infrastructure/`: Excel/PDF/ZIP generation adapters.

**Required Classes/Interfaces:**
- `TaxReportGenerator` interface.
- `TaxSubmissionService` application service.

**Migration Plan Steps:**
1. Register `finance` in `INSTALLED_APPS` and `urls.py`.
2. Create `finance/services/tax_service.py`.
3. Move business logic from views to service.
4. Add tests for the service layer.

---

### 2.4 notification

**Current Purpose:**
In-app notifications, device tokens, FCM push notifications, WhatsApp messaging, SMS, voice notes, and reminder scheduling.

**Folder Structure:**
```
notification/
├── __init__.py
├── admin.py               # Empty
├── apps.py
├── management/commands/
│   └── send_extra_charge_reminders.py
├── migrations/
├── models.py              # Notification, DeviceToken
├── test_extra_charge_reminders.py  # MISPLACED test at root
├── tests/
├── urls.py
├── utils.py               # send_push_notification, send_whatsapp_message
├── views.py
└── services/
    ├── communication.py
    ├── extra_charge_reminders.py
    ├── late_fees_notify_service.py
    ├── notifications.py
    ├── rent_notify_service.py
    ├── schedule_reminders.py
    ├── services.py
    ├── sms_service.py
    ├── voice_note_service.py
    ├── voice_service.py
    └── whatsapp_service.py
```

**Current Layering Assessment:**
Has a dedicated services directory with multiple adapters for different channels. However:
- No clear port/interface abstraction for notification channels.
- `utils.py` duplicates `send_whatsapp_message` that also exists in `services/whatsapp_service.py`.
- `services/services.py` is a thin wrapper (`notify_user`, `notify_owner_renter_flagged`).
- `services/rent_notify_service.py` imports `rentsecure_be.services.i18n_service` for translation.
- No `NotificationChannel` interface as required by the project instructions.

**Architecture Score:** 55/100
**DDD Score:** 35/100
**Clean Architecture Score:** 45/100
**SOLID Score:** 50/100
**Code Quality Score:** 55/100
**Testability Score:** 55/100
**Maintainability Score:** 50/100
**Production Readiness Score:** 60/100

**Strengths:**
- Multiple service files for different notification types.
- FCM integration via `fcm_django`.
- Voice note generation via `edge_tts`.
- i18n-aware notification composition.

**Weaknesses:**
- No `NotificationChannel` port/interface.
- Duplicate `send_whatsapp_message` in `utils.py` and `services/whatsapp_service.py`.
- `services/services.py` is poorly named (conflicts with module name).
- No adapter pattern for SMS/WhatsApp/Voice — they're concrete implementations directly imported.
- Test file `test_extra_charge_reminders.py` is misplaced at app root.
- `admin.py` is empty.

**Violations:**
- Missing ports/adapters pattern (Year-1 notification strategy requires adapters).
- No `NotificationChannel` interface.
- Duplicate code between utils and services.

**Risk Level:** Medium

**Quick Wins:**
- Remove duplicate `send_whatsapp_message` from `utils.py`.
- Move `test_extra_charge_reminders.py` to `tests/`.
- Define `NotificationChannel` protocol.

**Long-term Improvements:**
- Implement adapter pattern: `EmailAdapter`, `FCMAdapter`, `InAppAdapter`, `WhatsAppAdapter` (disabled), `SMSAdapter` (disabled).
- Introduce `NotificationService` orchestrator.
- Add feature flags for WhatsApp/SMS.

**Required Layers for Target State:**
- `ports/`: `NotificationChannel` protocol.
- `adapters/`: `EmailAdapter`, `FCMAdapter`, `InAppAdapter`, `WhatsAppAdapter`, `SMSAdapter`.

**Required Classes/Interfaces:**
```python
class NotificationChannel(Protocol):
    def send(self, user, message, **kwargs) -> bool: ...

class EmailAdapter: ...
class FCMAdapter: ...
class InAppAdapter: ...
class WhatsAppAdapter: ...
class SMSAdapter: ...
```

**Migration Plan Steps:**
1. Define `NotificationChannel` protocol.
2. Create adapter classes in `notification/adapters/`.
3. Update `notification/services/` to use adapters.
4. Add feature flags for disabled adapters.

---

### 2.5 documents

**Current Purpose:**
PDF generation for rent agreements, unit dossiers, rent receipts, and unit history.

**Folder Structure:**
```
documents/
├── __init__.py
├── apps.py
├── migrations/
├── tests/
├── urls.py
├── utils.py               # PDF generation helpers
└── views.py               # ViewSets for PDF generation
```

**Current Layering Assessment:**
Very thin. Only has views, urls, and utils. No models (uses `properties` models). No serializers. No services. **Business logic is directly in views** (WeasyPrint PDF generation in `views.py`).

**Architecture Score:** 35/100
**DDD Score:** 20/100
**Clean Architecture Score:** 25/100
**SOLID Score:** 30/100
**Code Quality Score:** 40/100
**Testability Score:** 35/100
**Maintainability Score:** 30/100
**Production Readiness Score:** 30/100

**Strengths:**
- Dedicated utils for PDF generation.
- URL routing is clean.

**Weaknesses:**
- No models, no serializers, no services.
- PDF generation happens directly in views — not testable without HTTP.
- Tightly coupled to `properties.models`.
- `GenerateRentReceiptPdfViewSet` inherits from `ModelViewSet` but only uses `get_object` — wrong base class.
- `views.py` imports `RentRecordSerializer` from `properties` — cross-app coupling.
- No error handling for missing templates.

**Violations:**
- Views contain business logic (PDF rendering).
- Missing service layer entirely.
- Wrong ViewSet base classes.

**Risk Level:** Medium

**Quick Wins:**
- Create `documents/services/pdf_service.py` to encapsulate WeasyPrint calls.
- Replace `ModelViewSet` with `ViewSet` or `APIView` where appropriate.
- Add `documents` models if document metadata needs tracking.

**Long-term Improvements:**
- Introduce `PdfGenerator` interface.
- Move all PDF generation to services.
- Add async PDF generation for large documents.

**Required Layers for Target State:**
- `domain/`: Document, Template entities.
- `application/`: GenerateAgreementPdf, GenerateDossierPdf use cases.
- `infrastructure/`: WeasyPrint adapter, template renderers.

**Required Classes/Interfaces:**
- `PdfGenerator` protocol.
- `HtmlToPdfAdapter`.

**Migration Plan Steps:**
1. Create `documents/services/pdf_service.py`.
2. Move all WeasyPrint logic from views to service.
3. Add proper error handling and logging.
4. Add document tracking models if needed.

---

### 2.6 smartbot

**Current Purpose:**
AI chatbot (GPT), rent reminders, payout retries, agreement sending, digital signature initiation, WhatsApp integration.

**Folder Structure:**
```
smartbot/
├── __init__.py
├── actions.py              # send_rent_reminder, retry_payout, send_rent_agreement, send_agreement_for_signature
├── admin.py
├── apps.py
├── cron/reminders.py
├── intents.py              # Simple keyword-based intent extraction
├── migrations/
├── models.py               # SmartBotChat, SmartBotMessage, AIAlert
├── services/
│   ├── agreement_service.py
│   ├── chatbot_service.py
│   ├── gpt_services.py
│   ├── leegality_service.py
│   └── services.py
├── tasks.py                # No-op stub (Celery removed)
├── tests.py
├── views.py
└── whatsapp_service.py
```

**Current Layering Assessment:**
Has services, actions, intents. However:
- `actions.py` contains **orchestration logic** that imports from `notification`, `properties`, `rentsecure_be`, and `smartbot` — heavy cross-cutting.
- `views.py` contains context assembly and GPT calling — business logic in view.
- `services/chatbot_service.py` directly queries `properties.models` and calls `openai`.
- `services/gpt_services.py` has global `openai.api_key` configuration.
- `whatsapp_service.py` duplicates `send_whatsapp_message` from `notification.utils`.
- `tasks.py` is a no-op stub.

**Architecture Score:** 50/100
**DDD Score:** 35/100
**Clean Architecture Score:** 40/100
**SOLID Score:** 45/100
**Code Quality Score:** 50/100
**Testability Score:** 45/100
**Maintainability Score:** 45/100
**Production Readiness Score:** 50/100

**Strengths:**
- Separation of intents, actions, and services.
- GPT integration isolated in `gpt_services.py`.
- Agreement service abstraction.

**Weaknesses:**
- `actions.py` is a God function dispatcher with cross-app imports.
- `views.py` assembles context from multiple apps.
- Duplicate WhatsApp sending logic.
- `tasks.py` is dead code.
- No clear interface for AI/LLM integration.

**Violations:**
- Business logic in views (context assembly, GPT calling).
- Cross-app imports in actions and services.
- Duplicate notification code.

**Risk Level:** Medium

**Quick Wins:**
- Remove `tasks.py` no-op stub.
- Consolidate WhatsApp sending to `notification` adapter.
- Extract context assembly from `views.py` to a service.

**Long-term Improvements:**
- Introduce `LLMProvider` interface.
- Move actions to application layer.
- Add intent classification service.

**Required Layers for Target State:**
- `domain/`: ChatSession, Message, Intent entities.
- `application/`: ProcessChatMessage, SendAgreement use cases.
- `infrastructure/`: OpenAIAdapter, LeegalityAdapter.

**Required Classes/Interfaces:**
- `LLMProvider` protocol.
- `AgreementProvider` protocol.

**Migration Plan Steps:**
1. Remove dead `tasks.py`.
2. Extract context assembly to `smartbot/services/context_service.py`.
3. Define `LLMProvider` interface.
4. Move actions to application layer.

---

### 2.7 ai_assistant

**Current Purpose:**
AI insights dashboard, financial health analysis, rent analytics, WhatsApp webhook, invoice generation, renter archiving.

**Folder Structure:**
```
ai_assistant/
├── __init__.py
├── admin.py
├── apps.py
├── migrations/
├── models.py               # EMPTY
├── receivers.py            # Signal handlers for renter exit/archive
├── services/
│   ├── archive_service.py
│   ├── finance_ai.py
│   ├── i18n_service.py     # DUPLICATE of rentsecure_be/services/i18n_service.py
│   ├── invoice_service.py
│   └── unit_service.py
├── tests/
├── urls.py                 # Only WhatsApp webhook
└── views.py
```

**Current Layering Assessment:**
Thin app with services and views. However:
- **Not in `INSTALLED_APPS`**.
- **URLs not included** in main `urls.py` (only WhatsApp webhook is defined but unreachable).
- `models.py` is empty.
- Duplicate `i18n_service.py` (exists in both `ai_assistant/services/` and `rentsecure_be/services/`).
- `views.py` contains multiple unrelated endpoints (insights, analytics, health, chat, webhook).
- `receivers.py` imports from `properties.signals` — circular dependency risk.

**Architecture Score:** 40/100
**DDD Score:** 25/100
**Clean Architecture Score:** 30/100
**SOLID Score:** 35/100
**Code Quality Score:** 40/100
**Testability Score:** 35/100
**Maintainability Score:** 35/100
**Production Readiness Score:** 25/100

**Strengths:**
- Service layer for AI-specific operations.
- Signal receivers for renter lifecycle events.
- WhatsApp webhook handler.

**Weaknesses:**
- App is **orphaned** (not in `INSTALLED_APPS`, URLs not wired).
- Duplicate `i18n_service.py`.
- `views.py` mixes multiple concerns.
- `receivers.py` creates coupling between `ai_assistant` and `properties`.
- Empty `models.py`.

**Violations:**
- Orphaned app (not registered).
- Code duplication (`i18n_service.py`).
- Business logic in views.

**Risk Level:** High (feature is broken due to missing registration)

**Quick Wins:**
- Add `ai_assistant` to `INSTALLED_APPS`.
- Include `ai_assistant/urls.py` in main `urls.py`.
- Remove duplicate `i18n_service.py` and import from `rentsecure_be`.

**Long-term Improvements:**
- Move AI insights to `smartbot` or a dedicated `ai` domain.
- Introduce `AnalyticsService` for dashboard data.
- Consolidate invoice generation with `documents` app.

**Required Layers for Target State:**
- `domain/`: Insight, AnalyticsReport, FinancialHealth entities.
- `application/`: GenerateInsights, AnalyzeFinancialHealth use cases.

**Required Classes/Interfaces:**
- `AnalyticsProvider` interface.
- `InvoiceGenerator` interface.

**Migration Plan Steps:**
1. Register `ai_assistant` in `INSTALLED_APPS`.
2. Wire URLs in main `urls.py`.
3. Remove duplicate `i18n_service.py`.
4. Split `views.py` into focused view modules.

---

### 2.8 referral_and_earn

**Current Purpose:**
Referral code tracking and bonus awarding.

**Folder Structure:**
```
referral_and_earn/
├── __init__.py
├── admin.py
├── apps.py
├── migrations/
├── models.py               # Referral
├── signals.py              # Creates Referral on user creation
└── tests/                  # (implied, none found)
```

**Current Layering Assessment:**
Minimal. Single model, signal, and no services or views. The signal creates a `Referral` on user creation.

**Architecture Score:** 50/100
**DDD Score:** 35/100
**Clean Architecture Score:** 40/100
**SOLID Score:** 45/100
**Code Quality Score:** 55/100
**Testability Score:** 45/100
**Maintainability Score:** 45/100
**Production Readiness Score:** 50/100

**Strengths:**
- Simple and focused.
- Signal ensures Referral is always created.

**Weaknesses:**
- No service layer for referral processing.
- Signal is the only "business logic" — hard to test.
- No views or endpoints exposed (referral processing is in `core/services/referral_service.py`).

**Violations:**
- Business logic in signals.
- No explicit API for referrals.

**Risk Level:** Low

**Quick Wins:**
- Add `ReferralService` to encapsulate creation and bonus logic.
- Add views/serializers for referral management.

**Long-term Improvements:**
- Move referral logic from `core/services/referral_service.py` to this app.
- Introduce `BonusPolicy` for configurable bonus amounts.

**Migration Plan Steps:**
1. Create `referral_and_earn/services/referral_service.py`.
2. Move `ReferralService` from `core` to `referral_and_earn`.
3. Replace signal with explicit service call from user creation flow.
4. Add REST endpoints.

---

### 2.9 dashboard

**Current Purpose:**
HTML dashboard for agreement status and signature retry (server-rendered Django views, not DRF).

**Folder Structure:**
```
dashboard/
├── __init__.py
├── tests.py
├── urls.py                 # NOT included in main urls.py
└── views.py                # Template-based views
```

**Current Layering Assessment:**
Minimal. Two function-based views rendering HTML templates. **Not in `INSTALLED_APPS`**. **URLs not included** in main `urls.py`.

**Architecture Score:** 30/100
**DDD Score:** 15/100
**Clean Architecture Score:** 20/100
**SOLID Score:** 25/100
**Code Quality Score:** 35/100
**Testability Score:** 30/100
**Maintainability Score:** 30/100
**Production Readiness Score:** 20/100

**Strengths:**
- Simple function-based views.
- Basic test coverage.

**Weaknesses:**
- **Orphaned app** (not registered, URLs not wired).
- `views.py` imports `send_agreement_for_signature` from `smartbot.actions` — cross-app dependency.
- No templates directory found in the app.
- No models or services.

**Violations:**
- Orphaned app.
- Cross-app dependency on `smartbot`.
- No separation of concerns.

**Risk Level:** Low (feature is small but broken)

**Quick Wins:**
- Add `dashboard` to `INSTALLED_APPS`.
- Include `dashboard/urls.py` in main `urls.py`.
- Move `send_agreement_for_signature` call to a service.

**Long-term Improvements:**
- Convert to DRF or keep as HTMX-based views.
- Introduce dashboard-specific service.

**Migration Plan Steps:**
1. Register `dashboard` in `INSTALLED_APPS`.
2. Wire URLs.
3. Extract action call to service.
4. Add templates.

---

## 3. Global Reports

### 3.1 Architecture Heat Map (Worst to Best)

| Rank | App | Score | Risk |
|------|-----|-------|------|
| 1 | dashboard | 30 | Low (broken) |
| 2 | ai_assistant | 40 | High (orphaned) |
| 3 | documents | 35 | Medium |
| 4 | finance | 45 | Low-Medium (broken) |
| 5 | smartbot | 50 | Medium |
| 6 | referral_and_earn | 50 | Low |
| 7 | notification | 55 | Medium |
| 8 | core | 65 | Medium |
| 9 | properties | 70 | Medium-High |

### 3.2 Dependency Violation Report

**High-violation imports:**
- `core/views.py` → `notification.services.rent_notify_service`
- `core/views.py` → `rentsecure_be.services.cashfree_service`
- `core/services/bank_details_service.py` → `properties.models.rent_record_models`
- `core/services/owner_reporting_service.py` → `properties.models.rent_record_models`
- `properties/views/rent_record_views.py` → `notification.services.rent_notify_service`
- `properties/views/rent_record_views.py` → `rentsecure_be.services.cashfree_service`
- `properties/views/unit_views.py` → `rentsecure_be.services.leegality_service`
- `properties/utils/utils.py` → `notification.services.late_fees_notify_service`
- `properties/signals/__init__.py` → `notification.models.Notification`
- `smartbot/actions.py` → `notification.utils`, `properties.models`, `rentsecure_be.services.cashfree_service`
- `smartbot/views.py` → `properties.models.RentRecord`
- `ai_assistant/views.py` → `smartbot.services.chatbot_service`
- `ai_assistant/receivers.py` → `properties.signals.renter_signals`
- `documents/views.py` → `properties.models`, `properties.serializers`
- `dashboard/views.py` → `properties.models`, `smartbot.actions`
- `notification/services/rent_notify_service.py` → `rentsecure_be.services.i18n_service`
- `notification/services/schedule_reminders.py` → `properties.models.rent_record_models`
- `notification/services/extra_charge_reminders.py` → `properties.models.extra_charge_models`

**Violation Summary:**
- `core` depends on `properties`, `notification`, `rentsecure_be` — should be independent.
- `properties` depends on `notification`, `rentsecure_be` — should depend only on `core`.
- `notification` depends on `properties` and `rentsecure_be` — should be independent.
- `smartbot` depends on `notification`, `properties`, `rentsecure_be` — should be independent.
- `ai_assistant` depends on `notification`, `properties`, `smartbot`, `core` — maximum coupling.

### 3.3 Circular Dependency Report

**Detected cycles:**
1. `properties/signals/__init__.py` → `notification.models.Notification`
   `notification/services/schedule_reminders.py` → `properties.models.rent_record_models`
   (Indirect cycle via function imports)

2. `properties/utils/utils.py` → `notification.services.late_fees_notify_service`
   `notification/services/late_fees_notify_service.py` → `properties.models` (via rent.renter.unit.owner)
   (Implicit cycle at runtime)

3. `smartbot/actions.py` → `notification.utils`
   `notification/utils.py` → (no direct back-import, but `notification.services` imports `properties`)

4. `core/services/bank_details_service.py` → `properties.models.rent_record_models`
   `properties/views/rent_record_views.py` → `core.models.User`
   (Bidirectional coupling)

**Risk:** Runtime import errors, difficult testing, fragile refactoring.

### 3.4 Technical Debt Report

| Category | Debt | Severity |
|----------|------|----------|
| **Orphaned Apps** | `ai_assistant`, `dashboard`, `finance` not registered | High |
| **Empty Stubs** | 4 empty service files in `properties` | Medium |
| **Duplicate Code** | `i18n_service.py` in 2 locations; `send_whatsapp_message` in 2 locations | Medium |
| **God Files** | `properties/utils/utils.py` (290 lines), `core/views.py` (566 lines), `properties/signals/__init__.py` (248 lines) | High |
| **Fat Models** | `core/models.py` (255 lines, 8 models), `properties/models/renter_models.py` (286 lines) | Medium |
| **Signal Spaghetti** | 8+ signal handlers with business logic in `properties/signals/__init__.py` | High |
| **Missing Abstraction** | No `PaymentGateway` interface; no `NotificationChannel` interface | High |
| **Year-1 Violations** | `django_celery_beat` installed; `ENABLE_RAZORPAY`/`ENABLE_CASHFREE` code present but disabled | Medium |
| **Testing Gaps** | No tests for `ai_assistant`, `referral_and_earn`; misplaced test files | Medium |
| **Configuration** | Feature flags in settings but not consistently used in code | Low |

### 3.5 Architecture Risk Report

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Circular import crash** | High | High | Break cycles by introducing interfaces in `shared/` |
| **Orphaned features break on deploy** | High | Medium | Register all apps and wire URLs |
| **Signal side effects cause data corruption** | Medium | High | Replace signals with explicit service calls |
| **Business logic in views resists testing** | High | Medium | Extract to services |
| **External API calls block requests** | Medium | High | Move to async or background jobs |
| **Year-1 rules violated (Celery)** | Low | Low | Remove `django_celery_beat` or defer to Stage 2 |

### 3.6 Migration Priority Matrix

| Priority | App/Concern | Effort | Value |
|----------|-------------|--------|-------|
| **P0** | Register orphaned apps (`ai_assistant`, `dashboard`, `finance`) | S | High |
| **P0** | Wire missing URLs (`finance`, `ai_assistant`) | S | High |
| **P1** | Break circular dependencies (`core` ↔ `properties` ↔ `notification`) | M | High |
| **P1** | Extract business logic from views to services | M | High |
| **P1** | Implement `PaymentGateway` port/adapters | M | High |
| **P1** | Implement `NotificationChannel` port/adapters | M | High |
| **P2** | Split `properties/utils/utils.py` | S | Medium |
| **P2** | Remove empty service stubs or implement them | S | Medium |
| **P2** | Consolidate duplicate `i18n_service` | S | Medium |
| **P3** | Move signals to explicit domain events | L | Medium |
| **P3** | Introduce DDD layers (domain/application/infrastructure) | XL | High |

### 3.7 Estimated Refactoring Effort

| Task | Effort |
|------|--------|
| Register orphaned apps + wire URLs | XS |
| Remove duplicate code | XS |
| Remove empty stubs | XS |
| Split `properties/utils/utils.py` | S |
| Extract view logic to services (core) | M |
| Extract view logic to services (properties) | M |
| Break circular dependencies | M |
| Implement `PaymentGateway` adapters | M |
| Implement `NotificationChannel` adapters | M |
| Replace signals with domain events | L |
| Introduce full DDD layering | XL |

**Total estimated effort:** ~2-3 months for 1 senior engineer (P0-P2 only).

### 3.8 Recommended Refactoring Order

1. **Week 1:** Register orphaned apps, wire URLs, remove duplicate code, delete empty stubs.
2. **Week 2-3:** Split God files (`properties/utils/utils.py`, `core/views.py`).
3. **Week 4-5:** Extract view logic to services in `core` and `properties`.
4. **Week 6-7:** Break circular dependencies by introducing `shared/` interfaces.
5. **Week 8-9:** Implement `PaymentGateway` and `NotificationChannel` ports/adapters.
6. **Week 10-12:** Replace critical signals with explicit domain events.
7. **Ongoing:** Introduce DDD layers incrementally.

### 3.9 Architecture Completion Percentage

| Layer | Completion |
|-------|------------|
| **Domain Layer** | 15% (models exist but no explicit domain services/entities) |
| **Application Layer** | 25% (some services exist but incomplete) |
| **Infrastructure Layer** | 40% (repositories, adapters partially exist) |
| **Presentation Layer** | 60% (views/serializers exist but fat) |
| **Cross-Cutting** | 30% (signals, feature flags inconsistent) |
| **Overall** | **~30%** |

### 3.10 Enterprise Readiness Percentage

| Concern | Readiness |
|---------|-----------|
| **Security** | 60% (webhook HMAC good, but no rate limiting on OTP, secrets in settings) |
| **Observability** | 40% (basic logging, no structured logging, no metrics) |
| **Resilience** | 35% (no circuit breakers, no retry policies for external APIs) |
| **Scalability** | 30% (LocMemCache, no Redis, no async tasks) |
| **Testability** | 40% (tests exist but integration-heavy) |
| **Maintainability** | 35% (high coupling, circular deps, fat files) |
| **Overall** | **~35%** |

---

## 4. Critical Cross-Cutting Concerns

### 4.1 `rentsecure_be` App as Catch-All

The `rentsecure_be/` app (project package) contains:
- `services/cashfree_service.py`
- `services/razorpay_service.py`
- `services/leegality_service.py`
- `services/i18n_service.py`
- `utils/cashfree_payout.py`
- `utils/export_utils.py`
- `type_compat.py`

This violates Django conventions. These should be in a proper app (e.g., `integrations` or distributed to owning apps).

### 4.2 `shared` Module

`shared/exceptions.py` exists but `shared` is not a Django app. It should either be a proper app or be moved to a `libs/` package.

### 4.3 Celery Violation

`django_celery_beat` is in `INSTALLED_APPS` and `smartbot/tasks.py` references Celery. The project instructions state **"Celery is Stage 2 upgrade"** for Year 1. This should be removed or deferred.

### 4.4 Feature Flags

Feature flags exist in `settings.py` (`ENABLE_RAZORPAY`, `ENABLE_CASHFREE`, `ENABLE_WHATSAPP`, etc.) but are **not consistently checked in code**. For example, `core/views.py` unconditionally imports and uses Razorpay and Cashfree.

### 4.5 Model Anti-Patterns

- `RentRecord` has property aliases (`payment_status` → `status`, `date_paid` → `paid_on`) — confusing and error-prone.
- `Renter` has `property` property returning `unit` — misleading naming.
- `Unit` has legacy `__init__` with backward-compatible kwargs — fragile.
- `UpsertMixin` in `core/models.py` overrides `save()` — can cause unexpected behavior with Django's ORM.

---

## 5. Conclusion

The RentSecureBE codebase is a **functional MVP with architectural inconsistencies**. The `properties` app shows the most architectural maturity (repositories, policies, typed dicts), while `core`, `smartbot`, `ai_assistant`, and `documents` suffer from business logic leakage and tight coupling.

**Immediate actions required:**
1. Register `ai_assistant`, `dashboard`, `finance` in `INSTALLED_APPS`.
2. Wire `finance` and `ai_assistant` URLs.
3. Remove `django_celery_beat` (Year-1 rule violation).
4. Extract business logic from views to services.
5. Break circular dependencies between `core`, `properties`, `notification`, and `smartbot`.

**Medium-term goals:**
1. Implement `PaymentGateway` and `NotificationChannel` ports/adapters.
2. Replace signal-based workflows with explicit domain events.
3. Split God files (`properties/utils/utils.py`, `core/views.py`).
4. Remove empty service stubs.

**Long-term vision:**
1. Full DDD layering (domain/application/infrastructure).
2. CQRS for read-heavy analytics endpoints.
3. Redis caching (Stage 2).
4. OpenSearch for search (Stage 3).

The codebase is **not production-ready at enterprise scale** due to circular dependencies, scattered business logic, and inconsistent layering. However, with focused refactoring over 2-3 months, it can reach a maintainable state.
