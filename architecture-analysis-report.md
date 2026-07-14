# RentSecureBE Architecture Analysis Report

**Generated:** 2026-07-14
**Scope:** READ-ONLY analysis — no files modified

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Per-App Analysis](#2-per-app-analysis)
   - [core](#21-core)
   - [properties](#22-properties)
   - [notification](#23-notification)
   - [finance](#24-finance)
   - [documents](#25-documents)
   - [ai_assistant](#26-ai_assistant)
   - [smartbot](#27-smartbot)
   - [referral_and_earn](#28-referral_and_earn)
   - [dashboard](#29-dashboard)
   - [rentsecure_be](#210-rentsecure_be-project-config)
3. [Cross-App Import Analysis](#3-cross-app-import-analysis)
4. [Dependency Violations](#4-dependency-violations)
5. [Duplication Analysis](#5-duplication-analysis)
6. [God Classes & God Modules](#6-god-classes--god-modules)
7. [Root-Level management/commands Analysis](#7-root-level-managementcommands-analysis)
8. [tools/ Directory Analysis](#8-tools-directory-analysis)
9. [shared/ Directory (Shared Kernel) Analysis](#9-shared-directory-shared-kernel-analysis)
10. [Summary & Recommendations](#10-summary--recommendations)

---

## 1. Project Overview

RentSecureBE is a Django + DRF backend for a property management platform. The project defines 9 Django apps plus a project config app (`rentsecure_be`). An `import-linter.ini` enforces a **layered architecture** where each app may only import from `rentsecure_be` (and itself), but the actual codebase has extensive cross-app imports.

**INSTALLED_APPS** (from `rentsecure_be/settings.py:117-138`):
```python
INSTALLED_APPS = [
    "core", "notification", "properties", "finance",
    "referral_and_earn", "documents", "smartbot", "django_extensions",
]
```
Note: `ai_assistant` and `dashboard` are **NOT** listed in `INSTALLED_APPS` — they are dead code from a Django perspective.

---

## 2. Per-App Analysis

### 2.1 core

**Files:**
- `models.py` — User, UserProfile, OTP, OwnerBankDetails, SubscriptionPlan, UserSubscription, AddOnPurchase, PlanFeatureLimit, UsageLimit, NotificationPreference, UpsertMixin
- `views.py` (566 lines) — OTP views, password views, subscription viewsets, bank details view, owner reporting views, Cashfree webhook, Razorpay webhook, create_rent_payment
- `serializers.py` — UserSerializer, SubscriptionPlanSerializer, UserSubscriptionSerializer, AddOnPurchaseSerializer, PlanFeatureLimitSerializer, UsageLimitSerializer
- `services/` — auth_service, bank_details_service, otp_service, password_service, owner_reporting_service, referral_service, subscription_service, usage_limit_service
- `urls.py`
- `signals.py`

**Current responsibility:** Authentication, user management, subscription/usage-limit management, bank details, OTP, password management, owner reporting, referral processing, Cashfree/Razorpay webhook handling.

**Expected responsibility (bounded context):** Identity & Access Management + Subscription & Billing. Should own User, UserProfile, OTP, SubscriptionPlan, UserSubscription, AddOnPurchase, PlanFeatureLimit, UsageLimit, and related auth/subscription services.

**Files belonging to another bounded context:**
- `NotificationPreference` model (`core/models.py:77`) — belongs in `notification` app
- `OwnerBankDetails` model (`core/models.py:108`) — belongs in `finance` or a dedicated `payments` app
- Cashfree webhook (`core/views.py:298`) — belongs in `finance` or `rentsecure_be/services`
- Razorpay webhook (`core/views.py:394`) — belongs in `finance` or `rentsecure_be/services`
- `create_rent_payment` view (`core/views.py:347`) — belongs in `finance`
- `owner_reporting_service.py` — uses `properties.models.rent_record_models.RentRecord`; belongs in `properties` or `dashboard`
- `bank_details_service.py` — imports from `properties.models.rent_record_models` and `rentsecure_be.utils.cashfree_payout`; belongs in `finance`

**Cross-app imports (core imports from):**
- `notification.services.rent_notify_service` (`core/views.py:35`)
- `rentsecure_be.services.cashfree_service` (`core/views.py:36`)
- `rentsecure_be.utils.export_utils` (`core/views.py:40`)
- `properties.models.rent_record_models` (`core/views.py:62`, `core/services/bank_details_service.py:7`)
- `rentsecure_be.type_compat` (`core/models.py:10`, `core/serializers.py:5`)
- `shared.exceptions` (`core/views.py:41`, `core/services/referral_service.py:6`)
- `referral_and_earn.models` (`core/services/referral_service.py:23`)

**Dependency violations:**
- `core → notification` (views.py imports `send_payout_notification`) — **VIOLATION** of layered architecture
- `core → properties` (views.py and services import RentRecord) — **VIOLATION**
- `core → rentsecure_be` (views.py imports cashfree_service, export_utils) — technically allowed by import-linter, but conceptually wrong since rentsecure_be is the project config layer
- `core → referral_and_earn` (referral_service.py) — **VIOLATION**

**God classes:**
- `core/views.py` (566 lines) — handles auth, OTP, password, subscription CRUD, bank details, owner reporting, two payment webhooks, and rent payment creation. **Severe god view.**

---

### 2.2 properties

**Files:**
- `models/` — building_models, unit_models (482 lines), renter_models (286 lines), caretaker_models, extra_charge_models, property_tax_models, rent_record_models, subscription_models (placeholder), usage_limit_models
- `views/` — building, unit, renter, rent_record, caretaker, property, subscription, extra_charge, owner_dashboard, usage_limit
- `serializers/` — 9 serializer files
- `services/` — building_service, unit_service (267 lines), renter_service (stub), rent_service (stub), occupancy_service (stub), vacancy_service (stub), receipt_service, extra_charge_service, summary_service, renter_onboarding_service
- `repositories/` — building, unit, renter, rent_record
- `policies/unit_policy.py`
- `feature_enforcer.py` (195 lines)
- `constants.py`
- `cron/` — flag_defaulters, vacate_reminder
- `communication/` — auto_generate_rent_records, retry_failed_payouts
- `management/commands/` — generate_monthly_extra_charges, send_monthly_rent_summary
- `scheduler.py`
- `signals/renter_signals.py`

**Current responsibility:** Property management (buildings, units, renters, caretakers), rent records, extra charges, property tax records, feature enforcement, vacancy management, renter onboarding.

**Expected responsibility (bounded context):** Property Management — buildings, units, renters, rent records, caretakers, vacancies. Should NOT own tax records (finance), should NOT own documents.

**Files belonging to another bounded context:**
- `property_tax_models.py` — `PropertyTaxRecord` belongs in `finance` app
- `extra_charge_models.py` — `ExtraCharge` belongs in `finance` app (financial transaction)
- `rent_record_models.py` — `RentRecord` has extensive payment fields (razorpay_order_id, payout_status, payout_reference, payment_link, invoice_pdf) — payment concerns belong in `finance`
- `receipt_service.py` — generates and emails rent receipt PDFs; belongs in `documents` or `notification`
- `renter_onboarding_service.py` — may belong in `properties`
- `feature_enforcer.py` — subscription enforcement; arguably belongs in `core` or a dedicated `subscriptions` app
- `owner_dashboard.py` view — analytics/dashboard; belongs in `dashboard` app
- `summary_service.py` — analytics; belongs in `dashboard`

**Cross-app imports (properties imports from):**
- `core.models` (User) — required, acceptable
- `rentsecure_be.type_compat` — required, acceptable
- `django.conf.settings` — standard

**Dependency violations:** None critical from properties outward (it only imports from core and rentsecure_be, which is allowed).

---

### 2.3 notification

**Files:**
- `models.py` — Notification, DeviceToken
- `views.py` — get_notifications, mark_notification_read, save_device_token, register_fcm_token
- `urls.py`
- `admin.py`
- `services/` — notifications.py, rent_notify_service.py, communication.py, sms_service.py, whatsapp_service.py, voice_service.py, voice_note_service.py, schedule_reminders.py, extra_charge_reminders.py, late_fees_notify_service.py
- `utils.py`
- `management/commands/send_extra_charge_reminders.py`

**Current responsibility:** In-app notifications, push notifications (Expo/FCM), WhatsApp messaging, SMS, voice notes, rent notifications, extra charge reminders, late fee notifications.

**Expected responsibility (bounded context):** Notification Delivery — should own all notification channels (push, email, WhatsApp, SMS, voice) with adapter pattern. Should NOT own business logic for when to send notifications (that's in the triggering apps).

**Files belonging to another bounded context:**
- `services/rent_notify_service.py` — contains business logic for rent payout notifications; notification triggers belong in `finance` or `properties`
- `services/extra_charge_reminders.py` — business logic for extra charge reminders; belongs in `properties` or `finance`
- `services/late_fees_notify_service.py` — business logic for late fee notifications; belongs in `properties`
- `services/schedule_reminders.py` — scheduling logic; could belong in `properties`
- `services/communication.py` — `send_smart_alert` orchestration; could belong in shared

**Cross-app imports (notification imports from):**
- None explicitly in notification code (uses `fcm_django`, `twilio` directly)
- `rentsecure_be.services.i18n_service` is imported lazily in `rent_notify_service.py`

**Dependency violations:** None significant.

**Duplicates within notification:**
- `send_push_notification` defined in BOTH `notification/services/notifications.py` (lines 13-27) AND `notification/utils.py` (lines 14-17). The former uses the Expo push API directly; the latter uses FCMDevice. **These are different implementations of the same concept.**
- `send_whatsapp_message` defined in `notification/services/whatsapp_service.py` AND referenced in `notification/utils.py` (which has the same function name but different implementation using Twilio).

---

### 2.4 finance

**Files:**
- `models.py` — CAProfile, TaxSubmissionToCA
- `views.py` — CAProfileViewSet, TaxSubmissionToCAViewSet, DownloadTaxFilesView
- `serializers.py` — CAProfileSerializer, TaxSubmissionToCASerializer
- `utils.py` — generate_tax_excel, generate_tax_pdf, create_tax_zip
- `urls.py`
- `admin.py`

**Current responsibility:** CA (Chartered Accountant) profiles, tax submissions to CA, tax document generation (Excel, PDF, ZIP).

**Expected responsibility (bounded context):** Finance & Payments — should own all payment-related models (transactions, payouts), tax records, CA management, payment gateway adapters.

**Files belonging to another bounded context:**
- `utils.py` generates tax documents — this is document generation, arguably belongs in `documents` app
- `DownloadTaxFilesView` — downloads tax documents; belongs in `documents`

**Cross-app imports (finance imports from):**
- `core.models.User` (`finance/views.py:22`)
- `properties.models.Unit` (`finance/views.py:23`)
- `rentsecure_be.type_compat` (`finance/views.py:24`)
- `properties.models` (TYPE_CHECKING in `finance/utils.py:26`)

**Dependency violations:**
- `finance → properties` (views.py imports Unit) — **VIOLATION** of layered architecture

---

### 2.5 documents

**Files:**
- `views.py` — GenerateRentAgreementPdfViewSet, GenerateUnitDossierPdfViewSet, GenerateRentReceiptPdfViewSet, download_unit_history
- `utils.py` — generate_unit_history_pdf, _merge_pdfs, etc.
- `urls.py`

**Current responsibility:** PDF generation for rent agreements, unit dossiers, rent receipts, unit history.

**Expected responsibility (bounded context):** Document Management — should own all document generation, storage, and retrieval. Should NOT own property-specific business logic.

**Files belonging to another bounded context:**
- `views.py` directly queries `properties.models.Renter`, `properties.models.RentRecord`, `properties.models.Unit` — document views should accept IDs and delegate to services
- `utils.py` imports `properties.models.RentAgreementDraft` — document generation should be generic

**Cross-app imports (documents imports from):**
- `core.models.User` (`documents/views.py:15`)
- `properties.models` (Renter, RentRecord, Unit) (`documents/views.py:16`)
- `properties.serializers.RentRecordSerializer` (`documents/views.py:17`)

**Dependency violations:**
- `documents → properties` (views.py, utils.py) — **VIOLATION**
- `documents → core` (views.py) — **VIOLATION** (though importing User is often necessary)

---

### 2.6 ai_assistant

**Files:**
- `models.py` — empty placeholder
- `views.py` — ai_assistant_insights, rent_analytics_data, financial_health_report, chat_with_assistant, whatsapp_webhook
- `urls.py`
- `services/` — finance_ai.py, invoice_service.py, i18n_service.py, unit_service.py, archive_service.py
- `receivers.py`
- `admin.py`

**Current responsibility:** AI insights, rent analytics, financial health report, chat assistant, WhatsApp webhook, invoice generation, unit status updates, renter archiving.

**Expected responsibility (bounded context):** AI Assistant / Smart Insights — should provide AI-driven insights, chat interface, and financial analysis. Should NOT own document generation or WhatsApp webhooks.

**Files belonging to another bounded context:**
- `services/invoice_service.py` — PDF invoice generation; belongs in `documents`
- `services/archive_service.py` — renter archiving; belongs in `properties`
- `services/unit_service.py` — unit status updates; belongs in `properties`
- `views.py` WhatsApp webhook — belongs in `notification` or `smartbot`
- `views.py` ai_assistant_insights — analytics; belongs in `dashboard`

**Cross-app imports (ai_assistant imports from):**
- `core.models.UserProfile` (`ai_assistant/views.py:25`)
- `notification.services.whatsapp_service` (`ai_assistant/views.py:26`)
- `properties.models` (PropertyTaxRecord, Renter, RentRecord) (`ai_assistant/views.py:27`)
- `smartbot.services.chatbot_service` (`ai_assistant/views.py:28`)
- `rentsecure_be.services.i18n_service` (`ai_assistant/views.py:48` via lazy import in rent_notify_service)

**Dependency violations:**
- `ai_assistant → notification` — **VIOLATION**
- `ai_assistant → smartbot` — **VIOLATION**
- `ai_assistant → properties` — **VIOLATION**

**Note:** `ai_assistant` is NOT in `INSTALLED_APPS` — it is dead code.

---

### 2.7 smartbot

**Files:**
- `models.py` — SmartBotChat, SmartBotMessage, AIAlert
- `views.py` — smart_bot_reply
- `actions.py` — send_rent_reminder, retry_payout, send_rent_agreement, send_agreement_for_signature
- `intents.py` — extract_intent
- `whatsapp_service.py` — send_agreement_via_whatsapp
- `services/` — chatbot_service, agreement_service, gpt_services, leegality_service, services (AI alerts)
- `cron/reminders.py`
- `tasks.py`
- `tests/`

**Current responsibility:** Chatbot (rule-based + GPT), AI alert generation, rent reminder actions, payout retry actions, agreement sending, Leegality e-signature integration, WhatsApp agreement delivery.

**Expected responsibility (bounded context):** AI Assistant / Chatbot — should own chat logic, intent extraction, and AI-driven actions. Should NOT own notification delivery or payment processing.

**Files belonging to another bounded context:**
- `services/leegality_service.py` — e-signature integration; arguably belongs in `documents`
- `whatsapp_service.py` — notification delivery; belongs in `notification`
- `services/agreement_service.py` — PDF generation for agreements; belongs in `documents`
- `actions.py` — `retry_payout` calls `rentsecure_be.services.cashfree_service.process_rent_payout`; payment processing belongs in `finance`
- `cron/reminders.py` — reminder scheduling; belongs in `properties` or `notification`

**Cross-app imports (smartbot imports from):**
- `properties.models` (Renter, RentRecord, RentAgreementDraft) — **VIOLATION**
- `core.models` (via properties) — **VIOLATION** (transitive)
- `notification.utils` (`smartbot/actions.py:5`, `smartbot/whatsapp_service.py:4`) — **VIOLATION**
- `rentsecure_be.services.cashfree_service` (`smartbot/actions.py:7`) — **VIOLATION**
- `smartbot.services.leegality_service` (self-reference for initiate_signature)

**Dependency violations:**
- `smartbot → notification` (actions.py, whatsapp_service.py) — **VIOLATION**
- `smartbot → properties` (views.py, actions.py, services/) — **VIOLATION**
- `smartbot → rentsecure_be` (actions.py imports cashfree_service) — **VIOLATION**

---

### 2.8 referral_and_earn

**Files:**
- `models.py` — Referral
- `signals.py` — create_referral post_save signal
- `admin.py`, `apps.py`, `migrations/`

**Current responsibility:** Referral codes, referral tracking, bonus earnings.

**Expected responsibility (bounded context):** Referral & Loyalty — referral codes, referral tracking, bonus/earnings management.

**Cross-app imports (referral_and_earn imports from):**
- None (standalone app)

**Dependency violations:** None. However, `core/services/referral_service.py` imports from `referral_and_earn.models` — this means `core → referral_and_earn`, which is a **VIOLATION** of the layered architecture.

---

### 2.9 dashboard

**Files:**
- `views.py` (21 lines) — agreement_status_view, retry_signature
- `urls.py`
- `tests.py`

**Current responsibility:** Very thin — shows agreement status and retries signature. Essentially a server-side rendered dashboard.

**Expected responsibility (bounded context):** Dashboard & Analytics — should own owner dashboard, analytics endpoints, reports. Should NOT own business actions.

**Files belonging to another bounded context:**
- `views.py` calls `smartbot.actions.send_agreement_for_signature` — business action execution; dashboard should not invoke actions directly

**Cross-app imports (dashboard imports from):**
- `properties.models.RentRecord` — **VIOLATION**
- `smartbot.actions` — **VIOLATION**

**Dependency violations:**
- `dashboard → properties` — **VIOLATION**
- `dashboard → smartbot` — **VIOLATION**

---

### 2.10 rentsecure_be (project config)

**Files:**
- `settings.py`
- `urls.py`
- `wsgi.py`, `asgi.py`
- `services/` — cashfree_service.py, i18n_service.py, leegality_service.py, razorpay_service.py
- `utils/` — cashfree_payout.py, export_utils.py
- `types.py`, `type_compat.py`
- `tests/`

**Current responsibility:** Django project configuration, payment gateway adapters (Cashfree, Razorpay), i18n translation, Leegality e-signature, export utilities, type definitions.

**Expected responsibility (bounded context):** Project Configuration & Infrastructure — should ONLY own settings, URL routing, WSGI/ASGI config, and shared infrastructure utilities. Should NOT own business services.

**Files belonging to another bounded context:**
- `services/cashfree_service.py` — payment gateway adapter; belongs in `finance`
- `services/razorpay_service.py` — payment gateway adapter; belongs in `finance`
- `services/leegality_service.py` — e-signature integration; belongs in `documents` or `smartbot`
- `services/i18n_service.py` — translation utility; belongs in `shared` or `notification`
- `utils/cashfree_payout.py` — payment API client; belongs in `finance`
- `utils/export_utils.py` — Excel export; belongs in `documents` or `shared`

**Cross-app imports:** None (rentsecure_be is the top layer).

**Dependency violations:** None from an import-linter perspective, but conceptually rentsecure_be has too many responsibilities.

---

## 3. Cross-App Import Analysis

### Import Map (source → target)

| Source App | Target App | Files | Severity |
|-----------|-----------|-------|----------|
| core | notification | `views.py` (rent_notify_service) | **HIGH** |
| core | properties | `views.py`, `services/bank_details_service.py`, `services/owner_reporting_service.py` | **HIGH** |
| core | rentsecure_be | `views.py` (cashfree_service, export_utils) | MEDIUM |
| core | referral_and_earn | `services/referral_service.py` | **HIGH** |
| properties | core | All model files (User import) | LOW (required) |
| finance | properties | `views.py`, `utils.py` (TYPE_CHECKING) | **HIGH** |
| documents | properties | `views.py`, `utils.py` | **HIGH** |
| documents | core | `views.py` (User) | MEDIUM |
| ai_assistant | notification | `views.py` | **HIGH** |
| ai_assistant | smartbot | `views.py` | **HIGH** |
| ai_assistant | properties | `views.py`, `services/*` | **HIGH** |
| ai_assistant | core | `views.py` (UserProfile) | MEDIUM |
| smartbot | notification | `actions.py`, `whatsapp_service.py` | **HIGH** |
| smartbot | properties | `views.py`, `actions.py`, `services/*` | **HIGH** |
| smartbot | rentsecure_be | `actions.py` (cashfree_service) | **HIGH** |
| dashboard | properties | `views.py` | **HIGH** |
| dashboard | smartbot | `views.py` | **HIGH** |

### import-linter Compliance

The `import-linter.ini` defines a strict layered architecture where each app can only import from `rentsecure_be`. The actual codebase has **15+ cross-app import violations**:

1. `core → notification` (views.py)
2. `core → properties` (views.py, services/)
3. `core → referral_and_earn` (referral_service.py)
4. `finance → properties` (views.py)
5. `documents → properties` (views.py, utils.py)
6. `documents → core` (views.py)
7. `ai_assistant → notification` (views.py)
8. `ai_assistant → smartbot` (views.py)
9. `ai_assistant → properties` (views.py, services/)
10. `smartbot → notification` (actions.py, whatsapp_service.py)
11. `smartbot → properties` (views.py, actions.py, services/)
12. `smartbot → rentsecure_be` (actions.py)
13. `dashboard → properties` (views.py)
14. `dashboard → smartbot` (views.py)
15. `notification → rentsecure_be` (lazy imports in rent_notify_service.py)

---

## 4. Dependency Violations (Architecture Rules)

### Violation: core app handles payment webhooks

`core/views.py` contains:
- `cashfree_payout_webhook` (line 298) — Cashfree webhook handler
- `razorpay_webhook` (line 394) — Razorpay webhook handler
- `create_rent_payment` (line 347) — Razorpay order creation

These belong in `finance` or `rentsecure_be/services`. The `core` app should not know about payment providers.

### Violation: core app contains bank details model

`core/models.py` has `OwnerBankDetails` (line 108). This is a financial entity and belongs in `finance`.

### Violation: core app contains NotificationPreference

`core/models.py` has `NotificationPreference` (line 77). This belongs in `notification`.

### Violation: ai_assistant and dashboard not in INSTALLED_APPS

`ai_assistant` and `dashboard` are defined as Django apps with `apps.py`, `urls.py`, and views, but they are NOT listed in `INSTALLED_APPS` in `rentsecure_be/settings.py`. This means:
- Their models (if any) are not migrated
- Their URL patterns are not included
- They are effectively dead code

### Violation: properties app contains tax and extra charge models

`properties/models/property_tax_models.py` has `PropertyTaxRecord`. This belongs in `finance`.

`properties/models/extra_charge_models.py` has `ExtraCharge`. This is a financial transaction and belongs in `finance`.

### Violation: smartbot handles payment processing

`smartbot/actions.py` `retry_payout` calls `rentsecure_be.services.cashfree_service.process_rent_payout`. Payment processing belongs in `finance`.

### Violation: smartbot has its own WhatsApp service

`smartbot/whatsapp_service.py` is a thin wrapper around `notification.utils.send_whatsapp_message`. This creates a parallel notification path that bypasses the notification app.

---

## 5. Duplication Analysis

### 5.1 Duplicate Utilities

| Function | Location 1 | Location 2 | Notes |
|----------|-----------|-----------|-------|
| `translate_msg` | `rentsecure_be/services/i18n_service.py:4` | `ai_assistant/services/i18n_service.py:6` | **Exact duplicate** — both use `deep_translator.GoogleTranslator` |
| `send_push_notification` | `notification/services/notifications.py:13` | `notification/utils.py:14` | Different implementations: one uses Expo push API directly, the other uses FCMDevice |
| `send_whatsapp_message` | `notification/services/whatsapp_service.py:20` | `notification/utils.py:20` | Different implementations; `notification/utils.py` also imports from `fcm_django` |
| `send_whatsapp_message` (wrapper) | `smartbot/whatsapp_service.py:7` | `notification/services/whatsapp_service.py:20` | Thin wrapper that delegates to notification |
| `generate_agreement_pdf` | `smartbot/services/agreement_service.py:9` | `documents/views.py` (inline) | Both use WeasyPrint to generate rent agreement PDFs |
| `update_unit_status` | `properties/services/unit_service.py:171` | `ai_assistant/services/unit_service.py:8` | Both set unit status based on active renter |

### 5.2 Duplicate Constants

| Constant | Location 1 | Location 2 | Notes |
|----------|-----------|-----------|-------|
| `PAYMENT_STATUS_CHOICES` | `properties/constants.py:21` | `properties/models/rent_record_models.py` (Status.TextChoices) | Duplicated in constants file and model |
| `UNIT_STATUS_CHOICES` | `properties/constants.py:28` | `properties/models/unit_models.py` (VacancyStatus.TextChoices) | Duplicated |
| `RENT_REMINDER_DAYS_BEFORE` | `properties/constants.py:38` (value=3) | `core/models.py` UserSubscription (default=7) | Inconsistent values |
| `phone_regex` | `properties/models/unit_models.py:26` | `properties/models/renter_models.py:18` | Same RegexValidator defined twice |
| `phone_regex` | `properties/models/caretaker_models.py:10` | `properties/models/unit_models.py:26` | Same RegexValidator defined thrice |

### 5.3 Duplicate Services

| Service | Location 1 | Location 2 |
|---------|-----------|-----------|
| i18n `translate_msg` | `rentsecure_be/services/i18n_service.py` | `ai_assistant/services/i18n_service.py` |
| Leegality e-signature | `rentsecure_be/services/leegality_service.py` | `smartbot/services/leegality_service.py` |
| Cashfree payout | `rentsecure_be/utils/cashfree_payout.py` | `rentsecure_be/services/cashfree_service.py` (wraps it) |
| Push notification | `notification/services/notifications.py` | `notification/utils.py` |

### 5.4 Duplicate Adapters

The notification module has multiple WhatsApp implementations:
- `notification/services/whatsapp_service.py` — primary adapter
- `notification/utils.py` — secondary adapter (also has push notification)
- `smartbot/whatsapp_service.py` — wrapper around notification/utils

The project does NOT follow the adapter pattern defined in the architecture docs (`notifications.adapters.email.EmailAdapter`, etc.).

### 5.5 Duplicate Validators

- `phone_regex` RegexValidator is defined in 3 places in the properties app (unit_models, renter_models, caretaker_models)
- `validate_non_empty_string` and `validate_positive_number` exist in `shared/validators.py` but are not used by the properties models

---

## 6. God Classes & God Modules

### God Classes

| Class/Module | File | Lines | Issue |
|--------------|------|-------|-------|
| `core/views.py` | `core/views.py` | 566 | Handles auth, OTP, password, subscription CRUD, bank details, owner reporting, 2 webhooks, rent payment creation |
| `properties/models/unit_models.py` | `unit_models.py` | 482 | Contains Unit, UnitVacancy, UnitDocument, UnitImage models + extensive business logic |
| `notification/services/rent_notify_service.py` | `rent_notify_service.py` | 168 | Handles renter notification, owner notification, payout notification, owner post-payout notification |

### God Modules

| Module | File Count | Issue |
|--------|-----------|-------|
| `core/services/` | 8 service files | Too many responsibilities for identity/subscription app |
| `properties/services/` | 10 service files (several are stubs) | Mix of implemented and stub services |
| `notification/services/` | 9 service files | Notification app has too many channel-specific files |
| `smartbot/services/` | 5 service files | Mix of AI, PDF, e-signature, WhatsApp concerns |
| `properties/models/` | 9 model files | Tax and extra charge models should not be here |
| `properties/views/` | 10 view files | Too many view modules; owner_dashboard should be in dashboard app |

---

## 7. Root-Level management/commands Analysis

The root `management/commands/` directory contains **15 management commands**:

| Command | Likely App Owner | Current Location |
|---------|-----------------|-----------------|
| `apply_late_fees.py` | properties | ROOT (should be in properties) |
| `archive_expired_users_data.py` | core or properties | ROOT |
| `auto_deactivate_renters.py` | properties | ROOT |
| `check_vacant_units.py` | properties | ROOT |
| `daily_rent_reminder.py` | properties/notification | ROOT |
| `downgrade_expired_users.py` | core | ROOT |
| `generate_monthly_rent_records.py` | properties | ROOT |
| `monthly_whatsapp_and_email_summary_to_owner.py` | notification | ROOT |
| `rent_reminder_service.py` | notification | ROOT |
| `retry_failed_payouts.py` | finance | ROOT |
| `seed_subscription_plans.py` | core | ROOT |
| `send_monthly_rent_summary.py` | properties/notification | ROOT |
| `send_rent_reminders.py` | notification | ROOT |
| `send_tax_reminders.py` | finance | ROOT |

**Recommendation:** Each management command should be moved to its respective app's `management/commands/` directory. Having them at the root level violates Django conventions and makes it unclear which app owns which scheduled task.

Some commands also exist inside their respective apps:
- `properties/management/commands/generate_monthly_extra_charges.py`
- `properties/management/commands/send_monthly_rent_summary.py`
- `notification/management/commands/send_extra_charge_reminders.py`

This creates **duplicate management commands** at both root and app level.

---

## 8. tools/ Directory Analysis

The `tools/` directory contains 7 files:

| File | Purpose | Appropriate Location |
|------|---------|---------------------|
| `autofix.py` | Auto-fix tooling | `scripts/` |
| `ci_guard.py` | CI pipeline guard | `scripts/` |
| `migration_guard.py` | Migration safety checks | `scripts/` |
| `migration_rollback_validator.py` | Migration rollback validation | `scripts/` |
| `report_generator.py` | Report generation tooling | `scripts/` |
| `security_guard.py` | Security checks | `scripts/` |
| `ship.py` | Deployment tooling | `scripts/` |

**Assessment:** The `tools/` directory contains project-level tooling scripts that are not part of any Django app. These are better placed in a `scripts/` directory (which already exists at the project root) or a dedicated `ci/` directory. Having them in `tools/` at the Django project root level is unconventional and could confuse Django's app discovery. The existing `scripts/` directory already contains similar tools (`architecture_contract.py`, `check_api_contracts.py`, etc.).

---

## 9. shared/ Directory (Shared Kernel) Analysis

The `shared/` directory is used as a shared kernel with the following files:

| File | Content | Usage |
|------|---------|-------|
| `constants.py` | DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, DEFAULT_TIMEOUT_SECONDS, EMPTY_STRING | Underused |
| `domain_events.py` | BaseDomainEvent, EventMetadata | Unused |
| `enums.py` | EmptyEnum placeholder | Unused |
| `exceptions.py` | BaseDomainError, ValidationError, BusinessRuleViolationError, ExternalServiceError, ConfigurationError | Used by core, smartbot |
| `interfaces.py` | Repository, Service, EventBus protocols | Defined but not used |
| `types.py` | ValidationError (dict type alias), build_validation_error | Conflicts with exceptions.py |
| `utils.py` | to_bool, sanitize_phone | Partially used |
| `validators.py` | validate_non_empty_string, validate_positive_number | Used by shared/utils.py only |

**Issues:**

1. **Naming conflict:** `shared/exceptions.py` defines `ValidationError` as a class (extends `BaseDomainError`), while `shared/types.py` defines `ValidationError` as `dict[str, list[str]]`. This creates an ambiguous import — `from shared.exceptions import ValidationError` vs `from shared.types import ValidationError`.

2. **Underutilization:** Most of the shared kernel is unused or underused:
   - `shared/domain_events.py` is defined but never imported
   - `shared/enums.py` is a placeholder
   - `shared/interfaces.py` (Repository, Service, EventBus protocols) are defined but never used as actual type hints
   - `shared/types.py` ValidationError dict type is unused (the exceptions class is used instead)
   - `shared/constants.py` has generic constants that are not referenced by other apps

3. **Missing shared utilities:** Common patterns that SHOULD be in shared but are duplicated:
   - Phone regex validator (duplicated in 3 places in properties)
   - i18n translation (duplicated in rentsecure_be and ai_assistant)
   - PDF generation utilities (duplicated in properties/receipt_service, documents, smartbot/agreement_service)

---

## 10. Summary & Recommendations

### Critical Architecture Violations

1. **`core` app is a god module** — handles auth, subscriptions, bank details, payment webhooks, and owner reporting. Should be split.
2. **`core` contains models from other bounded contexts** — `NotificationPreference` (notification), `OwnerBankDetails` (finance).
3. **`ai_assistant` and `dashboard` are not in `INSTALLED_APPS`** — they are dead code.
4. **15+ cross-app import violations** against the import-linter layered architecture.
5. **Payment webhooks in `core`** — should be in `finance`.

### High-Impact Duplications

1. **`translate_msg` duplicated** in `rentsecure_be/services/i18n_service.py` and `ai_assistant/services/i18n_service.py` — exact copy.
2. **`send_push_notification` duplicated** in `notification/services/notifications.py` and `notification/utils.py` — different implementations.
3. **`send_whatsapp_message` duplicated** across `notification/services/whatsapp_service.py` and `notification/utils.py`.
4. **Leegality service duplicated** in `rentsecure_be/services/leegality_service.py` and `smartbot/services/leegality_service.py`.
5. **Phone regex validator** duplicated 3 times in properties models.

### Recommended Refactoring

1. **Move `OwnerBankDetails` from `core` to `finance`** — it's a financial entity.
2. **Move `NotificationPreference` from `core` to `notification`** — it's a notification concern.
3. **Move payment webhooks from `core/views.py` to `finance/views.py`** — payment handling belongs in finance.
4. **Move `rentsecure_be/services/i18n_service.py` to `shared/` or `notification/`** — eliminate duplication with `ai_assistant/services/i18n_service.py`.
5. **Consolidate `notification/services/notifications.py` and `notification/utils.py`** — merge into a single notification service with adapter pattern.
6. **Move management commands to their respective apps** — root `management/commands/` should be emptied.
7. **Add `ai_assistant` and `dashboard` to `INSTALLED_APPS`** or remove them if they're not ready.
8. **Move `tools/` contents to `scripts/`** — consolidate project tooling.
9. **Move `PropertyTaxRecord` and `ExtraCharge` models from `properties` to `finance`** — they are financial records.
10. **Consolidate `smartbot/whatsapp_service.py`** — remove the thin wrapper and use `notification/services/whatsapp_service.py` directly.
11. **Move `receipt_service.py` from `properties` to `documents`** — rent receipt generation is document generation.
12. **Consolidate duplicate phone regex** into `shared/validators.py` or a shared constants module.

### Bounded Context Mapping

| Bounded Context | App(s) | Notes |
|----------------|--------|-------|
| Identity & Access | core | Users, auth, OTP, passwords |
| Subscription & Billing | core | Plans, subscriptions, usage limits, add-ons |
| Property Management | properties | Buildings, units, renters, caretakers, vacancies |
| Rent Management | properties | Rent records, rent reminders |
| Finance & Payments | finance | Tax records, CA profiles, payment adapters (Cashfree, Razorpay) |
| Document Management | documents | PDF generation, document storage |
| Notifications | notification | Push, WhatsApp, SMS, voice, email |
| AI Assistant | ai_assistant + smartbot | Chatbot, AI alerts, insights, analytics |
| Referral & Loyalty | referral_and_earn | Referral codes, bonuses |
| Dashboard | dashboard | Owner dashboard, analytics, reports |
| Infrastructure | rentsecure_be | Settings, URLs, payment API clients, i18n |
