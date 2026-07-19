# RentSecureBE — Comprehensive Architecture Audit Report

**Date:** 2026-07-19
**Scope:** Module boundaries, business logic ownership, cross-module imports, provider SDK placement, duplicate functionality

---

## Executive Summary

The RentSecureBE project exhibits **significant architecture violations** across multiple modules. The primary issues are:

1. **Payment logic is spread across 6+ modules** instead of being confined to `payments/`
2. **Notification dispatch logic is spread across 8+ modules** instead of being confined to `notification/`
3. **Provider SDKs (razorpay, cashfree, twilio, boto3, edge_tts, fcm_django) are used outside their designated adapter modules**
4. **Business event logic (rent due, late fees, extra charges) lives in `notification/` instead of domain modules**
5. **Duplicate implementations** of monthly rent summaries, payout retries, and payment link creation exist in multiple locations
6. **`core/` has become a "god module"** containing webhooks, payment processing, reporting, and notification dispatch
7. **`rentsecure_be/` contains duplicate payment service wrappers** that should live in `payments/`

---

## Module-by-Module Analysis

### 1. `core/` — Authentication & Subscription Core

**Intended Domain:** Authentication, OTP, subscriptions, user profiles, bank details, owner reporting

#### Business Logic from Other Domains Found:

| Issue | File | Lines | Description |
|-------|------|-------|-------------|
| **Payment webhook** | `core/views.py` | 291–337 | `cashfree_payout_webhook` — full Cashfree payout webhook handler with HMAC verification |
| **Payment creation** | `core/views.py` | 340–377 | `create_rent_payment` — creates Razorpay orders directly using `razorpay.Client` |
| **Payment webhook** | `core/views.py` | 387–427 | `razorpay_webhook` — full Razorpay webhook handler |
| **Payment processing** | `core/views.py` | 464–474 | `_process_rent_payment` — calls `PaymentService(CashfreeAdapter()).process_payout(rent)` |
| **Bank details + payout** | `core/views.py` | 482–524 | `update_owner_bank_details` — registers Cashfree beneficiary and retries payouts |
| **Owner reporting** | `core/services/owner_reporting_service.py` | 1–65 | Queries `RentRecord` directly (belongs in `properties/`) |
| **Bank details + payout retry** | `core/services/bank_details_service.py` | 57–60 | `retry_failed_payouts` updates RentRecord payout_status |
| **OTP notification** | `core/views.py` | 72–76 | `send_otp` delegates to `NotificationService` |
| **OTP notification** | `core/services/otp_service.py` | 63–67 | `_deliver_otp` delegates to `NotificationService` |

#### Provider SDKs Used Directly:

| SDK | File | Line | Should Be In |
|-----|------|------|-------------|
| `razorpay` | `core/views.py` | 10, 355–368 | `payments/adapters/razorpay.py` |

#### External Imports from Other Domain Modules:

- `notification.services.notification_service` — `core/views.py:18`
- `notification.services.rent_notify_service` — `core/views.py:35`
- `payments.adapters.cashfree` — `core/views.py:36`
- `payments.services.payment_service` — `core/views.py:37`
- `properties.utils.export_utils` — `core/views.py:38`
- `properties.models.rent_record_models` — `core/views.py:60` (TYPE_CHECKING), `core/services/owner_reporting_service.py:8`

#### Verdict:
`core/` is a **god module** violating single responsibility. It contains:
- Payment webhooks (should be in `payments/` or `properties/`)
- Payment order creation (should be in `payments/adapters/`)
- Bank details + payout orchestration (should be in `payments/`)
- Owner reporting on RentRecord (should be in `properties/services/`)

---

### 2. `properties/` — Property Management Domain

**Intended Domain:** Buildings, units, renters, rent records, extra charges, property tax, caretakers

#### Business Logic from Other Domains Found:

| Issue | File | Lines | Description |
|-------|------|-------|-------------|
| **Payment link creation** | `properties/views/rent_record_views.py` | 73 | `PaymentService(RazorpayAdapter()).create_payment_link(rent)` |
| **Payout retry** | `properties/views/rent_record_views.py` | 113–128 | `retry_payout_api` — calls `PaymentService(CashfreeAdapter()).process_payout(rent)` |
| **Payment + notification** | `properties/communication/auto_generate_rent_records.py` | 1–28 | Creates Razorpay payment links AND sends WhatsApp notifications |
| **Payout retry + notification** | `properties/communication/retry_failed_payouts.py` | 1–57 | Retries Cashfree payouts AND sends WhatsApp notifications |
| **Notification dispatch** | `properties/services/renter_onboarding_service.py` | 12, 61, 109, 126, 153 | Imports `NotificationService` to send WhatsApp onboarding invites/reminders |
| **Notification dispatch** | `properties/services/summary_service.py` | 128, 151 | Imports `NotificationService` to send monthly summaries |
| **Late fee notification** | `properties/utils/utils.py` | 20–22, 169–170 | Imports `notify_renter_about_late_fee`, `notify_owner_about_late_fee` from notification |
| **Signal → notification** | `properties/signals/__init__.py` | 9, 139, 167, 196 | Imports `Notification` model and notification services |
| **Leegality signature** | `properties/views/unit_views.py` | 29 | Imports `send_agreement_for_signature` from `rentsecure_be.services` |
| **AI alert generation** | `smartbot/services/services.py` | 1–78 | Lives in `smartbot/` but generates `AIAlert` for owners |

#### Provider SDKs Used Directly:
None directly in `properties/` — uses `PaymentService` abstraction (good).

#### External Imports from Other Domain Modules:

- `notification.services.notification_service` — 8+ files
- `notification.services.rent_notify_service` — `properties/views/rent_record_views.py:18`
- `notification.services.late_fees_notify_service` — `properties/utils/utils.py:20`
- `notification.services.voice_note_service` — `properties/scheduler.py:24`
- `payments.adapters.cashfree` — `properties/views/rent_record_views.py:20`, `properties/communication/retry_failed_payouts.py:6`
- `payments.adapters.razorpay` — `properties/views/rent_record_views.py:21`, `properties/communication/auto_generate_rent_records.py:4`
- `payments.services.payment_service` — `properties/views/rent_record_views.py:22`, `properties/communication/auto_generate_rent_records.py:5`, `properties/communication/retry_failed_payouts.py:7`
- `rentsecure_be.services.leegality_service` — `properties/views/unit_views.py:29`

#### Verdict:
`properties/` is **leaking payment and notification concerns** into the property domain. The `properties/communication/` package contains orchestration code that mixes payment and notification — this should be in management commands or a dedicated workflow service.

---

### 3. `payments/` — Payment Gateway Adapters

**Intended Domain:** Payment gateway abstraction, adapters, payment orchestration

#### Business Logic from Other Domains Found:

| Issue | File | Lines | Description |
|-------|------|-------|-------------|
| **Notification dispatch** | `payments/adapters/cashfree.py` | 96–127 | `_notify_payout_success` and `_notify_renter_failure` call notification services |
| **Core model access** | `payments/adapters/cashfree.py` | 47, 166 | Imports `OwnerBankDetails` from `core.models` |
| **Notification import** | `payments/adapters/cashfree.py` | 97, 118 | Imports `notify_owner_post_payout`, `notify_renter`, `send_payout_notification` from `notification.services.rent_notify_service` |

#### External Imports from Other Domain Modules:

- `notification.services.rent_notify_service` — `payments/adapters/cashfree.py:97, 118`
- `core.models.OwnerBankDetails` — `payments/adapters/cashfree.py:47, 166`
- `rentsecure_be.utils.cashfree_payout` — `payments/adapters/cashfree.py:14, 20, 31`

#### Verdict:
The Cashfree adapter violates the **single responsibility principle** by mixing payment execution with notification dispatch. Notification logic should be triggered by the caller (e.g., `properties/` or a signal handler), not inside the payment adapter.

---

### 4. `notification/` — Notification Service

**Intended Domain:** Multi-channel notification dispatch (email, push, SMS, WhatsApp, voice)

#### Business Logic from Other Domains Found (Should NOT Be Here):

| Issue | File | Lines | Description |
|-------|------|-------|-------------|
| **Rent due notification** | `notification/services/notification_service.py` | 117–150 | `notify_rent_due` — contains rent-specific business logic |
| **Payment received notification** | `notification/services/notification_service.py` | 152–184 | `notify_payment_received` — contains payment-specific business logic |
| **Rent reminder logic** | `notification/services/schedule_reminders.py` | 13–89 | Queries `RentRecord` and `PropertyTaxRecord`, generates reminder messages |
| **Late fee notification** | `notification/services/late_fees_notify_service.py` | 1–32 | Contains late fee business logic and message composition |
| **Extra charge reminders** | `notification/services/extra_charge_reminders.py` | 1–53 | Queries `ExtraCharge` model, generates due-date reminder messages |
| **Rent payout notification** | `notification/services/rent_notify_service.py` | 1–170 | Contains payout status logic, `send_payout_notification`, `notify_owner_post_payout` |
| **Voice note service** | `notification/services/voice_note_service.py` | 1–77 | Contains rent-specific thank-you and late-reminder voice notes |
| **OTP dispatch** | `notification/services/notification_dispatcher.py` | 112–114 | `dispatch_otp` — OTP is a `core/` concern |

#### Provider SDKs Used Directly (Correct Placement):

| SDK | File | Status |
|-----|------|--------|
| `twilio` | `notification/adapters/sms.py:6` | ✅ Correct |
| `twilio` | `notification/adapters/whatsapp.py:11–12` | ✅ Correct |
| `boto3` | `notification/adapters/whatsapp.py:8` | ✅ Correct |
| `edge_tts` | `notification/adapters/voice.py:8` | ✅ Correct |
| `fcm_django` | `notification/adapters/fcm.py:5` | ✅ Correct |
| `django.core.mail.EmailMessage` | `notification/adapters/email.py:5` | ✅ Correct |

#### Verdict:
`notification/` has **accumulated domain-specific business logic** that belongs in `properties/` or `core/`. The notification module should only contain:
- Adapter implementations (email, SMS, WhatsApp, push, voice)
- A dispatcher/ façade
- Port interfaces

It should **not** contain:
- Rent due message composition
- Late fee message composition
- Extra charge reminder scheduling
- Tax reminder scheduling
- Payout status notification logic
- OTP dispatch (belongs in `core/`)

---

### 5. `smartbot/` — AI Assistant & Chatbot

**Intended Domain:** Chatbot, AI alerts, agreement generation, Leegality e-signature

#### Business Logic from Other Domains Found:

| Issue | File | Lines | Description |
|-------|------|-------|-------------|
| **Payment retry** | `smartbot/actions.py` | 28–36 | `retry_payout` calls `PaymentService(CashfreeAdapter()).process_payout(rent)` |
| **Payment link creation** | `smartbot/actions.py` | 39–55 | `send_rent_agreement` generates PDF and sends via WhatsApp |
| **Notification dispatch** | `smartbot/actions.py` | 5, 22 | Imports `NotificationService` |
| **Notification dispatch** | `smartbot/whatsapp_service.py` | 4, 7–8 | Wraps `NotificationService().send_whatsapp_message` |
| **Property model queries** | `smartbot/actions.py` | 8, 17, 30, 41, 61 | Queries `Renter`, `RentRecord`, `RentAgreementDraft` |
| **AI alert generation** | `smartbot/services/services.py` | 1–78 | Generates `AIAlert` objects based on rent payment patterns |

#### Verdict:
`smartbot/` is **entangled with payment and notification** concerns. The `actions.py` file acts as a catch-all for owner actions including payout retries and agreement sending. The Leegality signature service also has a duplicate implementation in `rentsecure_be/services/leegality_service.py`.

---

### 6. `ai_assistant/` — AI Insights & Analytics

**Intended Domain:** AI-driven insights, financial health analysis, renter archiving, invoice generation

#### Business Logic from Other Domains Found:

| Issue | File | Lines | Description |
|-------|------|-------|-------------|
| **Notification dispatch** | `ai_assistant/views.py` | 26, 258 | Imports `NotificationService` for WhatsApp webhook reply |
| **RentRecord queries** | `ai_assistant/views.py` | 39–88, 107–149, 181–190 | Queries `RentRecord`, `PropertyTaxRecord`, `Renter` |
| **Chatbot delegation** | `ai_assistant/views.py` | 28, 200 | Imports `handle_chat_message` from `smartbot.services.chatbot_service` |
| **WhatsApp webhook** | `ai_assistant/views.py` | 224–259 | `whatsapp_webhook` — handles inbound WhatsApp messages |
| **Invoice generation** | `ai_assistant/services/invoice_service.py` | 1–39 | Generates final invoice PDFs (duplicates `properties/services/receipt_service.py`) |
| **Unit status update** | `ai_assistant/services/unit_service.py` | 1–11 | `update_unit_status` — belongs in `properties/` |

#### Verdict:
`ai_assistant/` is **not isolated** — it directly queries domain models and delegates to `smartbot/` for chat. The invoice generation and unit status update logic is duplicated from `properties/`.

---

### 7. `finance/` — Tax & CA Management

**Intended Domain:** Tax records, CA profiles, tax submissions, tax document generation

#### Business Logic from Other Domains Found:

| Issue | File | Lines | Description |
|-------|------|-------|-------------|
| **Property model queries** | `finance/views.py` | 23, 77–91 | Imports `Unit`, queries `Unit` and accesses `renter.rent_agreement`, `renter.police_verification` |
| **Tax Excel/PDF generation** | `finance/utils.py` | 1–133 | Uses `properties.models.Unit` for tax reporting |

#### Verdict:
`finance/` has **minimal cross-domain leakage**. It appropriately depends on `properties/models` for tax reporting. No payment or notification logic found (clean).

---

### 8. `documents/` — Document & PDF Generation

**Intended Domain:** PDF generation for agreements, dossiers, receipts, unit history

#### Business Logic from Other Domains Found:

| Issue | File | Lines | Description |
|-------|------|-------|-------------|
| **Property model queries** | `documents/views.py` | 15–17 | Imports `User`, `Renter`, `RentRecord`, `Unit` from `properties` |
| **Property model queries** | `documents/utils.py` | 12 | Imports `RentAgreementDraft` from `properties.models` |

#### Verdict:
`documents/` appropriately depends on `properties/` for document context. No payment or notification logic found (clean).

---

### 9. `rentsecure_be/` — Project Configuration & Utilities

**Intended Domain:** Django settings, URL routing, project-level services, utilities

#### Business Logic from Other Domains Found:

| Issue | File | Lines | Description |
|-------|------|-------|-------------|
| **Duplicate Cashfree service** | `rentsecure_be/services/cashfree_service.py` | 1–135 | Duplicates `payments/adapters/cashfree.py` with additional notification calls |
| **Duplicate Razorpay service** | `rentsecure_be/services/razorpay_service.py` | 1–9 | Thin wrapper around `payments/adapters/razorpay.py` |
| **Duplicate Leegality service** | `rentsecure_be/services/leegality_service.py` | 1–62 | Duplicate of `smartbot/services/leegality_service.py` |
| **Cashfree payout utils** | `rentsecure_be/utils/cashfree_payout.py` | 1–45 | Low-level Cashfree API calls — should be in `payments/` |
| **Settings imports** | `rentsecure_be/settings.py` | 128 | `fcm_django` in INSTALLED_APPS (should be fine) |

#### External Imports from Domain Modules:

- `payments.adapters.cashfree` — `rentsecure_be/services/cashfree_service.py:6`
- `payments.adapters.razorpay` — `rentsecure_be/services/razorpay_service.py:4`
- `payments.services.payment_service` — `rentsecure_be/services/cashfree_service.py:7`, `rentsecure_be/services/razorpay_service.py:5`
- `core.models.OwnerBankDetails` — `rentsecure_be/services/cashfree_service.py:10`
- `notification.services.rent_notify_service` — `rentsecure_be/services/cashfree_service.py:44, 103`

#### Verdict:
`rentsecure_be/` contains **duplicate service implementations** that should be consolidated into `payments/` and `smartbot/`. The `cashfree_payout.py` utility functions should be internal to the Cashfree adapter.

---

### 10. `management/commands/` — Scheduled Tasks

**Intended Domain:** Orchestration-only (should call domain services, not contain business logic)

#### Business Logic Found:

| Issue | File | Lines | Description |
|-------|------|-------|-------------|
| **Payment retry** | `management/commands/retry_failed_payouts.py` | 1–30 | Directly instantiates `PaymentService(CashfreeAdapter())` — OK for orchestration |
| **Late fee application** | `management/commands/apply_late_fees.py` | 1–60 | Contains late fee calculation AND WhatsApp notification dispatch |
| **Rent reminder** | `management/commands/daily_rent_reminder.py` | 1–31 | Contains reminder logic and WhatsApp dispatch |
| **Rent reminder** | `management/commands/send_rent_reminders.py` | 1–32 | Contains reminder message composition and WhatsApp dispatch |
| **Monthly summary** | `management/commands/send_monthly_rent_summary.py` | 1–93 | Orchestrates `send_monthly_rent_summary_email` (clean) |
| **Monthly summary** | `management/commands/monthly_whatsapp_and_email_summary_to_owner.py` | 1–75 | Contains duplicate summary generation logic AND WhatsApp/Email dispatch |
| **Vacant unit alert** | `management/commands/check_vacant_units.py` | 1–84 | Contains alert message composition and WhatsApp/Email dispatch |
| **Auto-deactivate renters** | `management/commands/auto_deactivate_renters.py` | 1–34 | Contains renter deactivation AND WhatsApp notification |
| **Generate rent records** | `management/commands/generate_monthly_rent_records.py` | 1–39 | Contains rent record creation logic |
| **Tax reminders** | `management/commands/send_tax_reminders.py` | 0–0 | Empty file (no issue) |

#### Verdict:
Management commands are **mixed** — some are pure orchestration (good), while others contain business logic (late fee calculation, rent record generation) and notification dispatch that should be in domain services.

---

### 11. `shared/` — Cross-Cutting Utilities

**Intended Domain:** Shared types, exceptions, validators, constants, interfaces

#### Contents:

| File | Contents | Verdict |
|------|----------|---------|
| `shared/constants.py` | Pagination, timeout constants | ✅ Clean |
| `shared/domain_events.py` | `BaseDomainEvent`, `EventMetadata` dataclasses | ✅ Clean |
| `shared/enums.py` | `EmptyEnum` placeholder | ✅ Clean |
| `shared/exceptions.py` | `BaseDomainError`, `ValidationError`, `BusinessRuleViolationError`, `ExternalServiceError`, `ConfigurationError` | ✅ Clean |
| `shared/interfaces.py` | `Repository`, `Service`, `EventBus` protocols | ✅ Clean |
| `shared/type_compat.py` | `override` compatibility shim | ✅ Clean |
| `shared/types.py` | `ValidationErrorDict`, `build_validation_error` | ✅ Clean |
| `shared/utils.py` | `to_bool`, `sanitize_phone` | ✅ Clean |
| `shared/validators.py` | `validate_non_empty_string`, `validate_positive_number` | ✅ Clean |

#### Verdict:
`shared/` is **truly shared** and clean. No domain-specific logic.

---

## Specific Pattern Searches

### 1. `send_mail` / `EmailMessage` / `SMTP` outside `notification/adapters/email.py`

| File | Line | Usage | Verdict |
|------|------|-------|---------|
| `notification/adapters/email.py` | 5, 21 | `from django.core.mail import EmailMessage` + usage | ✅ Correct |
| `rentsecure_be/settings.py` | 48 | `EMAIL_BACKEND` config | ✅ Correct (settings) |
| `properties/tests/test_signals.py` | 409 | `side_effect=Exception("SMTP down")` | ✅ Test mock |
| `tests/test_management_commands.py` | 87 | `side_effect=RuntimeError("SMTP down")` | ✅ Test mock |

**Result:** No violations found. Email sending is confined to `notification/adapters/email.py`.

---

### 2. Provider SDK Usage Outside Adapter Modules

| SDK | File | Line | Issue |
|-----|------|------|-------|
| `razorpay` | `core/views.py` | 10, 355–368 | **VIOLATION** — Direct Razorpay SDK usage in `core/views.py` |
| `razorpay` | `properties/models/rent_record_models.py` | 94 | `razorpay_order_id` field — acceptable as data model |
| `razorpay` | `properties/serializers/rent_record_serializers.py` | 24 | Serializer field — acceptable |
| `cashfree` | `core/views.py` | 36 | **VIOLATION** — Imports `CashfreeAdapter` in `core/views.py` |
| `cashfree` | `properties/views/rent_record_views.py` | 20 | **VIOLATION** — Imports `CashfreeAdapter` directly |
| `cashfree` | `properties/communication/auto_generate_rent_records.py` | — | Uses via PaymentService (acceptable) |
| `cashfree` | `properties/communication/retry_failed_payouts.py` | 6 | **VIOLATION** — Imports `CashfreeAdapter` directly |
| `twilio` | `notification/adapters/sms.py` | 6 | ✅ Correct (adapter module) |
| `twilio` | `notification/adapters/whatsapp.py` | 11–12 | ✅ Correct (adapter module) |
| `boto3` | `notification/adapters/whatsapp.py` | 8, 31 | ✅ Correct (adapter module) |
| `edge_tts` | `notification/adapters/voice.py` | 8, 24 | ✅ Correct (adapter module) |
| `fcm_django` | `notification/adapters/fcm.py` | 5 | ✅ Correct (adapter module) |
| `fcm_django` | `rentsecure_be/settings.py` | 128 | `INSTALLED_APPS` — acceptable |
| `fcm_django` | `notification/views.py` | 1 | `FCMDevice` — acceptable in notification views |
| `razorpay` | `payments/adapters/razorpay.py` | 3, 7 | ✅ Correct (adapter module) |
| `cashfree` | `payments/adapters/cashfree.py` | — | Uses `requests` to Cashfree API ✅ Correct |
| `requests` | `payments/adapters/cashfree.py` | 6 | ✅ Correct |
| `requests` | `rentsecure_be/services/leegality_service.py` | 4 | Should be in `smartbot/` adapter |
| `requests` | `smartbot/services/leegality_service.py` | 6 | ✅ Correct location for Leegality adapter |

**Summary of Violations:**
- `razorpay` SDK used directly in `core/views.py` (should use `payments/adapters/razorpay.py`)
- `CashfreeAdapter` imported in `core/views.py`, `properties/views/rent_record_views.py`, `properties/communication/retry_failed_payouts.py` (should use `payments/services/payment_service.py` abstraction consistently)

---

### 3. `Notification.objects.create` Outside `notification/`

| File | Line | Code | Verdict |
|------|------|------|---------|
| `notification/services/rent_notify_service.py` | 158 | `Notification.objects.create(user=user, title=title, message=message)` | ✅ Inside `notification/` |
| `properties/signals/__init__.py` | 145 | `Notification.objects.create(user=instance.renter.user, title="Thanks for Early Rent Payment", ...)` | **VIOLATION** — Should use `notification/` service |

**Verdict:** `properties/signals/__init__.py:145` directly creates `Notification` objects instead of calling a `notification/` service. This bypasses the notification dispatcher and makes it harder to change notification channels.

---

### 4. `RentRecord` or Payment Logic Inside `notification/`

| File | Lines | Issue |
|------|-------|-------|
| `notification/services/rent_notify_service.py` | 1–170 | Contains `send_payout_notification`, `notify_owner_post_payout`, `notify_renter`, `notify_owner` — all rent/payment-specific notification logic |
| `notification/services/late_fees_notify_service.py` | 1–32 | Contains late fee notification logic with rent-specific messages |
| `notification/services/schedule_reminders.py` | 13–89 | Queries `RentRecord` and `PropertyTaxRecord`, generates due-date reminder messages |
| `notification/services/extra_charge_reminders.py` | 11–53 | Queries `ExtraCharge` model, generates due-date reminder messages |
| `notification/services/notification_service.py` | 117–184 | `notify_rent_due` and `notify_payment_received` contain domain-specific message composition |

**Verdict:** `notification/` contains **significant domain-specific business logic** that belongs in `properties/` or dedicated workflow services. The notification module should receive pre-composed messages or event objects, not query domain models and compose business messages.

---

### 5. `OTP` Logic Outside `core/`

| File | Line | Issue |
|------|------|-------|
| `core/models.py` | 96–102 | `class OTP` — ✅ Correct location |
| `core/services/otp_service.py` | 17–67 | `class OTPService` — ✅ Correct location |
| `core/views.py` | 72–76, 88, 115, 127 | `send_otp`, `OTPService.send_otp`, `OTPService.verify` — ✅ Correct location |
| `core/tests/` | Various | Test files — ✅ Correct |

**Verdict:** No OTP logic outside `core/`. Clean.

---

### 6. Duplicate Implementations

| Functionality | Location 1 | Location 2 | Location 3 | Verdict |
|---------------|------------|------------|------------|---------|
| **Monthly rent summary generation** | `properties/services/summary_service.py` (`get_monthly_rent_summary`, `send_monthly_rent_summary_email`) | `management/commands/monthly_whatsapp_and_email_summary_to_owner.py` (`generate_monthly_summary_for_owner`, `build_summary_message`) | `properties/management/commands/send_monthly_rent_summary.py` (orchestrates Location 1) | **DUPLICATE** — `monthly_whatsapp_and_email_summary_to_owner.py` duplicates logic from `summary_service.py` |
| **Payout retry** | `properties/communication/retry_failed_payouts.py` (`retry_failed_payouts`) | `management/commands/retry_failed_payouts.py` | `core/views.py` (`update_owner_bank_details` line 520 calls `BankDetailsService.retry_failed_payouts`) | **DUPLICATE** — Three implementations of payout retry |
| **Rent record generation** | `management/commands/generate_monthly_rent_records.py` | `properties/communication/auto_generate_rent_records.py` | — | **DUPLICATE** — Two commands that generate rent records |
| **Payment link creation** | `payments/adapters/razorpay.py` | `rentsecure_be/services/razorpay_service.py` | — | **DUPLICATE** — Thin wrapper in `rentsecure_be/` |
| **Cashfree payout** | `payments/adapters/cashfree.py` | `rentsecure_be/services/cashfree_service.py` | `rentsecure_be/utils/cashfree_payout.py` | **DUPLICATE** — Three layers of Cashfree logic |
| **Leegality signature** | `smartbot/services/leegality_service.py` | `rentsecure_be/services/leegality_service.py` | — | **DUPLICATE** — Two identical implementations |
| **Rent invoice PDF** | `properties/utils/utils.py` (`generate_rent_invoice_pdf`) | `ai_assistant/services/invoice_service.py` (`generate_final_invoice_pdf`) | `properties/services/receipt_service.py` (`generate_rent_receipt_pdf`) | **DUPLICATE** — Three PDF generation functions for rent documents |
| **Late fee calculation** | `properties/utils/utils.py` (`apply_late_fee_if_needed`) | `management/commands/apply_late_fees.py` | — | **DUPLICATE** — Late fee logic in both |
| **Rent reminder message** | `notification/services/schedule_reminders.py` (`generate_rent_reminder_msg`) | `management/commands/send_rent_reminders.py` | `management/commands/daily_rent_reminder.py` | **DUPLICATE** — Three reminder message compositions |
| **Owner WhatsApp number lookup** | `notification/services/rent_notify_service.py` (`_renter_phone`) | `notification/services/schedule_reminders.py` (`_safe_whatsapp`) | `properties/services/summary_service.py` (inline) | **DUPLICATE** — Phone number resolution logic |

---

## Cross-Module Import Graph (Simplified)

```
core/ ←─────────────────── properties/ ←────────────────── smartbot/
  │                            │                              │
  │                            ├──> notification/             ├──> notification/
  │                            │     (should be reverse)       │
  │                            ├──> payments/                 ├──> payments/
  │                            │     (via views)               │
  │                            └──> rentsecure_be/            └──> ai_assistant/
  │                                  (duplicate services)          (delegates to smartbot)
  │
  ├──> notification/ (OTP dispatch — OK)
  ├──> payments/ (via views — VIOLATION)
  └──> shared/ (OK)

notification/ ──> properties/ (VIOLATION — should not query RentRecord)
payments/adapters/cashfree ──> notification/ (VIOLATION — adapter should not dispatch notifications)
rentsecure_be/ ──> payments/, core/, notification/ (VIOLATION — duplicate services)
ai_assistant/ ──> smartbot/, notification/, properties/ (VIOLATION — not isolated)
```

---

## Critical Findings & Recommendations

### Finding 1: `core/` Contains Payment Webhooks and Order Creation
**Severity:** HIGH
**Files:**
- `core/views.py:291–337` (`cashfree_payout_webhook`)
- `core/views.py:340–377` (`create_rent_payment`)
- `core/views.py:387–427` (`razorpay_webhook`)
- `core/views.py:482–524` (`update_owner_bank_details`)
- `core/urls.py:37–42` (URL routes for payment webhooks)

**Recommendation:** Move all payment webhooks to `properties/urls.py` or a dedicated `payments/urls.py`. Move `create_rent_payment` to `payments/adapters/razorpay.py` or `properties/views/rent_record_views.py`. Move `update_owner_bank_details` to `core/` is acceptable but should use `payments/services/payment_service.py` consistently.

### Finding 2: `core/views.py` Uses Razorpay SDK Directly
**Severity:** HIGH
**File:** `core/views.py:10, 355–368`

**Recommendation:** Replace direct `razorpay.Client` usage with `PaymentService(RazorpayAdapter())`.

### Finding 3: Payment Adapters Contain Notification Logic
**Severity:** HIGH
**File:** `payments/adapters/cashfree.py:96–127`

**Recommendation:** Remove notification calls from `CashfreeAdapter`. Return the payout result and let the caller (e.g., `properties/signals/__init__.py` or a Django signal) dispatch notifications.

### Finding 4: `notification/` Contains Domain Business Logic
**Severity:** HIGH
**Files:**
- `notification/services/notification_service.py:117–184`
- `notification/services/rent_notify_service.py`
- `notification/services/late_fees_notify_service.py`
- `notification/services/schedule_reminders.py`
- `notification/services/extra_charge_reminders.py`
- `notification/services/voice_note_service.py`

**Recommendation:** Move all domain-specific notification triggers to `properties/` or `core/`. The `notification/` module should only provide `NotificationService.send_email()`, `send_push()`, `send_sms()`, `send_whatsapp()`, `send_voice()`. Domain modules should call these methods with pre-composed messages.

### Finding 5: `Notification.objects.create` Outside `notification/`
**Severity:** MEDIUM
**File:** `properties/signals/__init__.py:145`

**Recommendation:** Replace with `NotificationService().send_email()` or `NotificationService().notify()` using the in-app channel. Or, create a `notification/` service method for in-app notifications.

### Finding 6: Duplicate Payment Services in `rentsecure_be/`
**Severity:** HIGH
**Files:**
- `rentsecure_be/services/cashfree_service.py`
- `rentsecure_be/services/razorpay_service.py`
- `rentsecure_be/services/leegality_service.py`
- `rentsecure_be/utils/cashfree_payout.py`

**Recommendation:** Delete `rentsecure_be/services/cashfree_service.py` and `rentsecure_be/services/razorpay_service.py`. Delete `rentsecure_be/utils/cashfree_payout.py` and move its functions into `payments/adapters/cashfree.py`. Delete `rentsecure_be/services/leegality_service.py` and keep `smartbot/services/leegality_service.py`.

### Finding 7: Duplicate Monthly Summary Implementations
**Severity:** MEDIUM
**Files:**
- `properties/services/summary_service.py`
- `management/commands/monthly_whatsapp_and_email_summary_to_owner.py`

**Recommendation:** Delete `management/commands/monthly_whatsapp_and_email_summary_to_owner.py` and use `properties/management/commands/send_monthly_rent_summary.py` instead.

### Finding 8: Duplicate Rent Record Generation
**Severity:** MEDIUM
**Files:**
- `management/commands/generate_monthly_rent_records.py`
- `properties/communication/auto_generate_rent_records.py`

**Recommendation:** Keep one implementation. The management command in `management/commands/` is the appropriate place. Remove `properties/communication/auto_generate_rent_records.py`.

### Finding 9: Duplicate Invoice PDF Generation
**Severity:** LOW
**Files:**
- `properties/utils/utils.py:145` (`generate_rent_invoice_pdf`)
- `properties/services/receipt_service.py:23` (`generate_rent_receipt_pdf`)
- `ai_assistant/services/invoice_service.py:12` (`generate_final_invoice_pdf`)

**Recommendation:** Consolidate into `properties/services/receipt_service.py`. Remove `ai_assistant/services/invoice_service.py`.

### Finding 10: `smartbot/actions.py` Contains Payment Retry
**Severity:** MEDIUM
**File:** `smartbot/actions.py:28–36`

**Recommendation:** Move `retry_payout` action to `properties/` or `payments/`. SmartBot should not directly invoke payment adapters.

### Finding 11: `ai_assistant/` Not Isolated
**Severity:** MEDIUM
**Files:**
- `ai_assistant/views.py` — queries RentRecord, PropertyTaxRecord, Renter
- `ai_assistant/views.py:258` — handles WhatsApp webhook
- `ai_assistant/services/unit_service.py` — duplicates `properties/services/unit_service.py`
- `ai_assistant/services/invoice_service.py` — duplicates invoice generation

**Recommendation:** `ai_assistant/` should call `properties/` services instead of querying models directly. Remove duplicated `unit_service.py` and `invoice_service.py`.

### Finding 12: `properties/communication/` Mixes Payment and Notification
**Severity:** MEDIUM
**Files:**
- `properties/communication/auto_generate_rent_records.py`
- `properties/communication/retry_failed_payouts.py`

**Recommendation:** Move `auto_generate_rent_records` to `management/commands/`. Move `retry_failed_payouts` to `management/commands/` or `properties/services/`.

### Finding 13: Management Commands Contain Business Logic
**Severity:** MEDIUM
**Files:**
- `management/commands/apply_late_fees.py` — contains late fee calculation
- `management/commands/generate_monthly_rent_records.py` — contains rent record creation
- `management/commands/daily_rent_reminder.py` — contains reminder logic
- `management/commands/auto_deactivate_renters.py` — contains deactivation logic

**Recommendation:** Move business logic to `properties/services/` and keep management commands as thin orchestration wrappers.

---

## Summary of Violations by Category

| Category | Count | Severity |
|----------|-------|----------|
| Payment logic outside `payments/` | 12 | HIGH |
| Notification dispatch outside `notification/` | 14 | HIGH |
| Provider SDK outside adapters | 3 | HIGH |
| Domain logic inside `notification/` | 6 | HIGH |
| Duplicate implementations | 10 | MEDIUM |
| `Notification.objects.create` outside `notification/` | 1 | MEDIUM |
| `core/` god module violations | 8 | HIGH |
| `rentsecure_be/` duplicate services | 4 | HIGH |
| Management commands with business logic | 4 | MEDIUM |

---

## Recommended Module Boundaries (Target State)

```
core/                    → Auth, OTP, subscriptions, user profiles, bank details
properties/              → Buildings, units, renters, rent records, extra charges, tax records
payments/                → PaymentGateway interface, adapters (manual, razorpay, cashfree), PaymentService
notification/            → NotificationChannel interfaces, adapters (email, sms, whatsapp, push, voice), NotificationDispatcher
smartbot/                → Chatbot, AI alerts, agreement generation, Leegality e-signature
ai_assistant/            → AI insights, financial health analysis, renter archiving (thin wrappers over properties/)
finance/                 → CA profiles, tax submissions, tax document generation
documents/               → PDF generation for agreements, dossiers, receipts, unit history
referral_and_earn/       → Referral codes, bonus tracking
shared/                  → BaseDomainError, ValidationError, constants, validators, interfaces
rentsecure_be/           → Django settings, URL routing, ASGI/WSGI, Celery config
management/commands/     → Thin orchestration wrappers calling domain services
```

---

## Actionable Refactoring Roadmap

### Phase 1: Stop the Bleeding (1–2 days)
1. Move `core/views.py` payment webhooks to `properties/urls.py`
2. Replace direct `razorpay.Client` in `core/views.py` with `PaymentService(RazorpayAdapter())`
3. Remove notification calls from `payments/adapters/cashfree.py`

### Phase 2: Clean Up Duplicates (2–3 days)
4. Delete `rentsecure_be/services/cashfree_service.py`, `razorpay_service.py`, `leegality_service.py`
5. Delete `rentsecure_be/utils/cashfree_payout.py` (move to `payments/adapters/cashfree.py`)
6. Delete `management/commands/monthly_whatsapp_and_email_summary_to_owner.py`
7. Delete `properties/communication/auto_generate_rent_records.py`
8. Delete `ai_assistant/services/invoice_service.py`, `unit_service.py`

### Phase 3: Isolate Notification (3–5 days)
9. Move `notification/services/notification_service.py` domain methods (`notify_rent_due`, `notify_payment_received`) to `properties/services/`
10. Move `notification/services/schedule_reminders.py` to `properties/cron/`
11. Move `notification/services/late_fees_notify_service.py` to `properties/services/`
12. Move `notification/services/extra_charge_reminders.py` to `properties/services/`
13. Move `notification/services/voice_note_service.py` to `properties/services/`
14. Replace `Notification.objects.create` in `properties/signals/__init__.py:145` with `NotificationService`

### Phase 4: Thin Management Commands (2–3 days)
15. Move `apply_late_fees` logic to `properties/services/late_fee_service.py`
16. Move `generate_monthly_rent_records` logic to `properties/services/rent_service.py`
17. Move `daily_rent_reminder` logic to `properties/cron/`
18. Move `auto_deactivate_renters` logic to `properties/services/renter_service.py`

### Phase 5: Isolate `ai_assistant/` (1–2 days)
19. Make `ai_assistant/views.py` call `properties/services/` instead of querying models directly
20. Remove duplicated services from `ai_assistant/`

---

*End of Report*
