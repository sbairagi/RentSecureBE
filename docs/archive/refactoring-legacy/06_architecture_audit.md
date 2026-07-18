# RentSecure Backend — DDD Architecture Audit

**Project:** RentSecure Backend
**Phase:** Architecture Audit
**Date:** 2026-07-15
**Status:** READ-ONLY — No code modifications
**Constraint:** Analysis only. No production code was modified.

---

## 1. Current Architecture

### App Inventory

| App | Current Responsibility | INSTALLED_APPS | URL Mount |
|-----|----------------------|----------------|-----------|
| `core` | Authentication, users, subscriptions, OTP, bank details, owner reporting | Yes | `/api/` |
| `properties` | Buildings, units, renters, rent records, extra charges, property tax, caretakers, unit images/documents, rent agreement drafts, usage limits, feature enforcer | Yes | `/api/`, `/properties/` |
| `finance` | CA profiles, tax submissions, tax document generation | Yes | `/finance/` |
| `notification` | Notifications, device tokens, push notifications, WhatsApp, SMS, voice notes | Yes | `/api/notifications/` |
| `smartbot` | AI chatbot, actions, Leegality integration, agreement PDF generation, WhatsApp for agreements, cron reminders | Yes | None (not mounted) |
| `ai_assistant` | Archive service, finance AI, invoice service, i18n service, unit service | No | None |
| `documents` | PDF generation for agreements, dossiers, receipts, unit history | Yes | `/documents/` |
| `referral_and_earn` | Referral program models and signals | Yes | None |
| `dashboard` | Analytics and reporting | Deleted | Deleted |
| `shared` | Validators, constants, enums, exceptions, interfaces, types, utils | No | N/A |
| `rentsecure_be` | Settings, URLs, deprecated services, utilities | N/A | N/A |

### Key Observation

The current architecture reflects **rapid development** rather than intentional bounded context design. Several concerns are scattered across multiple apps, and the `smartbot`/`ai_assistant` boundary is blurred.

---

## 2. Problems

### 2.1 Scattered PDF Generation

PDF generation logic is spread across **5+ locations**:

- `smartbot/services/agreement_service.py` — `generate_agreement_pdf()`
- `properties/utils/utils.py` — `generate_rent_invoice_pdf()`
- `documents/views.py` — inline WeasyPrint calls
- `documents/utils.py` — `generate_unit_history_pdf()`
- `finance/views.py` / `finance/utils.py` — `generate_tax_pdf()`

**Impact**: Duplicate WeasyPrint patterns, inconsistent error handling, no shared template management.

### 2.2 Duplicate WhatsApp Implementation

Two implementations of `send_whatsapp_message`:

- `notification/utils.py` — returns Twilio `msg.sid`
- `notification/services/whatsapp_service.py` — returns `bool`

**Impact**: Confusion about which to use, inconsistent return types, duplicated Twilio client setup.

### 2.3 Duplicate Leegality Integration

Two implementations of Leegality e-signature:

- `smartbot/services/leegality_service.py` — `initiate_signature()`, `check_signature_status()`
- `rentsecure_be/services/leegality_service.py` — `send_agreement_for_signature()`

**Impact**: `properties/views/unit_views.py` uses the `rentsecure_be` version; `smartbot/actions.py` uses the `smartbot` version. Divergent behavior risk.

### 2.4 Duplicate i18n Service

Two implementations of translation:

- `rentsecure_be/services/i18n_service.py` — used by notification services
- `ai_assistant/services/i18n_service.py` — imported by `ai_assistant` tests

**Impact**: Dead code in `ai_assistant`; only `rentsecure_be` version is active.

### 2.5 Misplaced Owner Reporting

`core/services/owner_reporting_service.py` contains property-specific reporting logic:

- Queries `RentRecord` by `unit__owner`
- Returns rent inflow summaries and owner rent records
- Used by `core/views.py` endpoints

**Impact**: `core` app should not contain property-domain logic. Violates single responsibility.

### 2.6 Property-Specific Notifications in `notification` App

`notification/services/` contains property-specific notification logic:

- `rent_notify_service.py` — rent payout notifications, renter/owner WhatsApp + voice
- `voice_note_service.py` — thank-you voice notes, late rent reminders
- `extra_charge_reminders.py` — extra charge due reminders
- `late_fees_notify_service.py` — late fee notifications

**Impact**: `notification` app becomes a catch-all. Property-specific notification logic should live with the property domain.

### 2.7 SmartBot Actions are Domain Operations

`smartbot/actions.py` contains operational actions that are NOT AI features:

- `send_rent_reminder()` — sends WhatsApp message
- `retry_payout()` — retries Cashfree payout
- `send_rent_agreement()` — generates and sends PDF
- `send_agreement_for_signature()` — initiates Leegality signature

**Impact**: These are business operations triggered by the chatbot interface, but they belong in their respective domains.

### 2.8 Unconditional Imports of Disabled Services

Despite feature flags (`ENABLE_RAZORPAY=False`, `ENABLE_CASHFREE=False`, etc.), these services are imported unconditionally:

- `core/views.py` → `cashfree_service`
- `properties/views/rent_record_views.py` → `razorpay_service`, `cashfree_service`
- `properties/views/unit_views.py` → `leegality_service`
- `smartbot/actions.py` → `cashfree_service`, `leegality_service`
- `notification/services/rent_notify_service.py` → `i18n_service`

**Impact**: Application fails to start if these services' dependencies are missing, even when the features are disabled.

### 2.9 Multiple Router Mounts on Same Prefix

`rentsecure_be/urls.py` mounts both `core` and `properties` on `/api/`:

```python
path("api/", include("core.urls")),
path("api/", include("properties.urls")),
```

**Impact**: URL namespace collisions; `core/urls.py` and `properties/urls.py` must carefully avoid overlapping patterns.

### 2.10 Signal Orchestration in `properties`

`properties/signals/__init__.py` handles many cross-cutting concerns:

- Usage counting for buildings, units, caretakers, renters, images, documents
- Unit status updates on renter save/delete
- Onboarding token generation
- Rent payment handling (voice notes, receipts, notifications)
- Renter defaulter status updates
- Final invoice generation and renter archival

**Impact**: Signals become a hidden orchestration layer, making the flow hard to trace and test.

---

## 3. Bounded Context Analysis

### 3.1 Ideal Bounded Contexts

| Bounded Context | Responsibility | Current Apps |
|----------------|----------------|-------------|
| **core** | Identity & Access Management (IAM), subscriptions, users, authentication, OTP | `core` |
| **properties** | Property management: buildings, units, renters, rent records, extra charges, property tax, caretakers, unit documents/images, rent agreement drafts, usage limits | `properties` |
| **finance** | Tax management, CA profiles, tax document generation, tax submissions | `finance` |
| **notification** | Notification channels: email, push, WhatsApp, SMS, voice notes | `notification` |
| **documents** | Document generation: PDFs for agreements, receipts, dossiers, tax documents; e-signature orchestration | `documents` |
| **payments** | Payment processing: Razorpay, Cashfree, UPI, payouts, webhooks | `rentsecure_be/services/` (Stage 2) |
| **assistant** | AI assistant: chatbot, GPT, actions, intents, chat history | `smartbot` + `ai_assistant` |
| **analytics** | Analytics and reporting: owner dashboard, rent inflow, occupancy analytics, monthly summaries | `core/services/owner_reporting_service.py`, `properties/services/unit_service.py` |
| **referral** | Referral program | `referral_and_earn` |
| **shared** | Shared utilities, validators, constants, enums, exceptions, interfaces, types | `shared` |

### 3.2 Context Mapping

```
core → properties (User ownership)
core → notification (User preferences)
core → referral (Referral codes)
core → finance (CA profiles)

properties → notification (Rent events, reminders)
properties → documents (Agreements, PDFs)
properties → finance (Tax records)
properties → analytics (Dashboard data)

notification → properties (Rent notifications)
notification → finance (Tax reminders)

finance → documents (Tax PDFs)
finance → properties (Unit data)

assistant → properties (Rent data, agreements)
assistant → notification (WhatsApp actions)
assistant → documents (Agreement PDFs, e-signature)

referral → core (User model)

analytics → properties (Rent records, units)
analytics → notification (Summary delivery)

payments → properties (Rent records, payouts)
payments → notification (Payment notifications)
```

---

## 4. Responsibility Matrix

| Component | Current App | Current Responsibility | Ideal App | Ideal Responsibility | Action |
|-----------|------------|----------------------|-----------|---------------------|--------|
| `smartbot/services/leegality_service.py` | smartbot | Leegality e-signature API client | documents | Document signing service | MOVE |
| `smartbot/services/agreement_service.py` | smartbot | Agreement PDF generation | documents | Agreement PDF generation | MOVE |
| `smartbot/whatsapp_service.py` | smartbot | WhatsApp for agreements | notification | WhatsApp messaging (merge) | MERGE |
| `smartbot/actions.py` (operational) | smartbot | Business operations | properties/notification | Domain actions | MOVE |
| `smartbot/cron/reminders.py` | smartbot | Signature reminders | documents | Document-related cron | MOVE |
| `smartbot/tasks.py` | smartbot | No-op stub | — | Archive/delete | ARCHIVE |
| `core/services/owner_reporting_service.py` | core | Owner rent reporting | properties | Property reporting | MOVE |
| `properties/services/summary_service.py` | properties | Monthly rent summary email/WhatsApp | notification/analytics | Summary delivery | MOVE |
| `notification/services/rent_notify_service.py` | notification | Rent payout notifications | properties | Property notifications | MOVE |
| `notification/services/voice_note_service.py` | notification | Voice notes for rent events | notification | Notification channel | KEEP |
| `notification/services/extra_charge_reminders.py` | notification | Extra charge reminders | properties | Property reminders | MOVE |
| `notification/services/late_fees_notify_service.py` | notification | Late fee notifications | properties | Property notifications | MOVE |
| `notification/utils.py` | notification | Duplicate WhatsApp + Push | notification | Consolidate into services | MERGE |
| `rentsecure_be/services/leegality_service.py` | rentsecure_be | Leegality e-signature | documents | Document signing | MOVE |
| `rentsecure_be/services/i18n_service.py` | rentsecure_be | Translation service | shared | Shared i18n utility | MOVE |
| `properties/utils/utils.py` (PDF) | properties | Rent invoice PDF | documents | Document generation | MOVE |
| `finance/utils.py` (PDF) | finance | Tax PDF generation | documents | Document generation | MOVE |
| `documents/utils.py` | documents | Unit history PDF | documents | Document generation | KEEP |
| `smartbot/services/gpt_services.py` | smartbot | GPT wrapper | assistant | AI/LLM service | KEEP |
| `smartbot/services/chatbot_service.py` | smartbot | Rule-based + GPT chatbot | assistant | AI chatbot | KEEP |
| `smartbot/intents.py` | smartbot | Intent extraction | assistant | AI intents | KEEP |
| `smartbot/views.py` | smartbot | Chatbot API endpoint | assistant | AI API | KEEP |
| `smartbot/models.py` | smartbot | Chat history, AI alerts | assistant | AI models | KEEP |
| `ai_assistant/services/archive_service.py` | ai_assistant | Renter archival | properties | Property archival | MOVE |
| `ai_assistant/services/invoice_service.py` | ai_assistant | Final invoice PDF | documents | Document generation | MOVE |
| `ai_assistant/services/finance_ai.py` | ai_assistant | Financial health analysis | finance/assistant | Finance analytics | EVALUATE |
| `ai_assistant/services/unit_service.py` | ai_assistant | Unit status updates | properties | Property service | MOVE |
| `ai_assistant/services/i18n_service.py` | ai_assistant | Duplicate translation | — | Delete (duplicate) | DELETE |

---

## 5. Merge Recommendations

### 5.1 Merge `smartbot` + `ai_assistant` → `assistant`

**Rationale**: Both apps contain AI-related code. `ai_assistant` has services imported by `smartbot` and `properties`. The boundary is artificial.

**Merge plan**:
1. Create `assistant/` app
2. Move `smartbot/services/gpt_services.py` → `assistant/services/llm.py`
3. Move `smartbot/services/chatbot_service.py` → `assistant/services/chat.py`
4. Move `smartbot/intents.py` → `assistant/intents.py`
5. Move `smartbot/views.py` → `assistant/views.py`
6. Move `smartbot/models.py` → `assistant/models.py`
7. Move `ai_assistant/services/archive_service.py` → `assistant/services/archive.py` (then move to `properties` if not AI-related)
8. Move `ai_assistant/services/invoice_service.py` → `documents/services/` (PDF generation, not AI)
9. Move `ai_assistant/services/unit_service.py` → `properties/services/` (property logic, not AI)
10. Delete `ai_assistant/` after moves complete

**Files to keep in `assistant`**:
- `smartbot/services/gpt_services.py` — Core LLM wrapper
- `smartbot/services/chatbot_service.py` — Core chatbot logic
- `smartbot/intents.py` — Intent extraction
- `smartbot/views.py` — Chatbot API
- `smartbot/models.py` — Chat history
- `smartbot/services/agreement_service.py` — MOVE to `documents`
- `smartbot/services/leegality_service.py` — MOVE to `documents`
- `smartbot/whatsapp_service.py` — MERGE into `notification`
- `smartbot/actions.py` — SPLIT into domain apps
- `smartbot/cron/reminders.py` — MOVE to `documents` or `properties`
- `smartbot/tasks.py` — ARCHIVE (no-op stub)

### 5.2 Consolidate PDF Generation → `documents`

**Rationale**: PDF generation is a cross-cutting concern that belongs in a single place.

**Sources to consolidate**:
- `smartbot/services/agreement_service.py` — `generate_agreement_pdf()`
- `properties/utils/utils.py` — `generate_rent_invoice_pdf()`
- `documents/views.py` — inline WeasyPrint
- `documents/utils.py` — `generate_unit_history_pdf()`
- `finance/utils.py` — `generate_tax_pdf()`

**Target**: `documents/utils/pdf_generator.py`

**Merge plan**:
1. Create `documents/utils/pdf_generator.py` with unified PDF generation API
2. Move all PDF generation functions to `pdf_generator.py`
3. Update all call sites to use `documents.utils.pdf_generator`
4. Remove inline WeasyPrint calls from `documents/views.py`

### 5.3 Consolidate WhatsApp → `notification/services/whatsapp_service.py`

**Rationale**: Single source of truth for WhatsApp messaging.

**Merge plan**:
1. Keep `notification/services/whatsapp_service.py` as canonical implementation
2. Remove `notification/utils.py` WhatsApp functions
3. Update all call sites to use `notification.services.whatsapp_service.send_whatsapp_message`

### 5.4 Consolidate Leegality → `documents/services/leegality.py`

**Rationale**: E-signature is a document concern, not an AI concern.

**Merge plan**:
1. Create `documents/services/leegality.py`
2. Move `rentsecure_be/services/leegality_service.py` functions to `documents/services/leegality.py`
3. Move `smartbot/services/leegality_service.py` functions to `documents/services/leegality.py`
4. Update call sites in `properties/views/unit_views.py` and `smartbot/actions.py`
5. Delete both source files

### 5.5 Move Property Notifications → `properties/services/`

**Rationale**: Property-specific notifications should live with the property domain.

**Move plan**:
1. Create `properties/services/notification_service.py`
2. Move `notification/services/rent_notify_service.py` → `properties/services/notification_service.py`
3. Move `notification/services/extra_charge_reminders.py` → `properties/services/extra_charge_notifications.py`
4. Move `notification/services/late_fees_notify_service.py` → `properties/services/late_fee_notifications.py`
5. Update call sites in `properties/signals/__init__.py`

### 5.6 Move Owner Reporting → `properties`

**Rationale**: Owner reporting is a property-domain concern.

**Move plan**:
1. Move `core/services/owner_reporting_service.py` → `properties/services/owner_reporting_service.py`
2. Update `core/views.py` to import from `properties.services.owner_reporting_service`
3. Consider moving to `analytics` app in future

---

## 6. Rename Recommendations

| Current Name | Recommended Name | Rationale |
|-------------|-----------------|-----------|
| `smartbot/` | `assistant/` | Broader scope includes AI actions, not just chatbot |
| `referral_and_earn/` | `referral/` | Shorter, clearer name |
| `rentsecure_be/services/` | `payments/` (future) | Current name is project-scoped, not domain-scoped |
| `core/services/owner_reporting_service.py` | `properties/services/owner_reporting_service.py` | Moved to properties |
| `notification/services/whatsapp_service.py` | `notification/services/channels/whatsapp.py` | Group channels |
| `notification/services/voice_service.py` | `notification/services/channels/voice.py` | Group channels |
| `notification/services/sms_service.py` | `notification/services/channels/sms.py` | Group channels |

---

## 7. Move Recommendations

### 7.1 From `smartbot` to `documents`

| File | Reason |
|------|--------|
| `smartbot/services/leegality_service.py` | Leegality is document signing, not AI |
| `smartbot/services/agreement_service.py` | PDF generation belongs in documents |
| `smartbot/cron/reminders.py` | Signature reminders are document-related |

### 7.2 From `smartbot` to `notification`

| File | Reason |
|------|--------|
| `smartbot/whatsapp_service.py` | WhatsApp messaging is a notification channel |

### 7.3 From `smartbot` to `properties`

| File | Reason |
|------|--------|
| `smartbot/actions.py` (send_rent_reminder, retry_payout, send_rent_agreement, send_agreement_for_signature) | These are domain operations, not AI features |

### 7.4 From `core` to `properties`

| File | Reason |
|------|--------|
| `core/services/owner_reporting_service.py` | Property-domain reporting logic |

### 7.5 From `notification` to `properties`

| File | Reason |
|------|--------|
| `notification/services/rent_notify_service.py` | Rent-specific notifications |
| `notification/services/extra_charge_reminders.py` | Extra charge reminders |
| `notification/services/late_fees_notify_service.py` | Late fee notifications |

### 7.6 From `rentsecure_be` to `documents`

| File | Reason |
|------|--------|
| `rentsecure_be/services/leegality_service.py` | E-signature is document concern |

### 7.7 From `rentsecure_be` to `shared`

| File | Reason |
|------|--------|
| `rentsecure_be/services/i18n_service.py` | Shared translation utility |

### 7.8 From `properties` to `documents`

| File | Reason |
|------|--------|
| `properties/utils/utils.py` (PDF generation functions) | PDF generation belongs in documents |
| `properties/services/receipt_service.py` | Receipt generation is document concern |

### 7.9 From `finance` to `documents`

| File | Reason |
|------|--------|
| `finance/utils.py` (PDF generation functions) | PDF generation belongs in documents |

### 7.10 From `ai_assistant` to `properties`

| File | Reason |
|------|--------|
| `ai_assistant/services/archive_service.py` | Renter archival is property logic |
| `ai_assistant/services/unit_service.py` | Unit status updates are property logic |

### 7.11 From `ai_assistant` to `documents`

| File | Reason |
|------|--------|
| `ai_assistant/services/invoice_service.py` | Final invoice PDF generation |

---

## 8. Keep As-Is

### 8.1 Apps to Keep

| App | Rationale |
|-----|-----------|
| `core/` | Core identity and subscription domain; well-structured |
| `properties/` | Core property domain; models, services, views are well-organized |
| `finance/` | Tax and CA domain; clean separation |
| `notification/` | Notification channels; well-structured after consolidation |
| `documents/` | Document generation; will receive consolidated PDF logic |
| `referral_and_earn/` | Referral program; keep as-is |
| `shared/` | Shared utilities; keep as-is |

### 8.2 Files to Keep As-Is

| File | Rationale |
|------|-----------|
| `smartbot/services/gpt_services.py` | Core LLM wrapper; belongs in `assistant` |
| `smartbot/services/chatbot_service.py` | Core chatbot logic; belongs in `assistant` |
| `smartbot/intents.py` | Intent extraction; belongs in `assistant` |
| `smartbot/views.py` | Chatbot API endpoint; belongs in `assistant` |
| `smartbot/models.py` | Chat history models; belongs in `assistant` |
| `notification/services/voice_note_service.py` | Property-specific but notification-channel-specific; keep in `notification` |
| `notification/services/notifications.py` | Push notification service; keep in `notification` |
| `notification/services/communication.py` | Multi-channel alert orchestration; keep in `notification` |
| `documents/utils.py` | Unit history PDF; consolidate but keep in `documents` |
| `properties/services/unit_service.py` | Core property service; keep in `properties` |
| `properties/services/receipt_service.py` | Receipt generation; move to `documents` but keep logic |
| `properties/signals/__init__.py` | Signal orchestration; keep but consider refactoring |
| `core/models.py` | Core identity models; keep as-is |
| `properties/models/*.py` | Core domain models; keep as-is |
| `finance/models.py` | Finance domain models; keep as-is |
| `notification/models.py` | Notification models; keep as-is |

---

## 9. Future Architecture

### 9.1 Target App Structure

```
apps/
├── core/                    # IAM, subscriptions, auth
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── otp_service.py
│   │   ├── password_service.py
│   │   ├── bank_details_service.py
│   │   └── subscription_service.py
│   └── signals.py
│
├── properties/              # Property management domain
│   ├── models/
│   ├── views/
│   ├── serializers/
│   ├── services/
│   │   ├── unit_service.py
│   │   ├── building_service.py
│   │   ├── renter_service.py
│   │   ├── rent_record_service.py
│   │   ├── extra_charge_service.py
│   │   ├── owner_reporting_service.py  # MOVED FROM core
│   │   ├── receipt_service.py          # MOVED FROM properties
│   │   └── notifications/              # MOVED FROM notification
│   │       ├── rent_notify_service.py
│   │       ├── extra_charge_reminders.py
│   │       └── late_fees_notify_service.py
│   ├── signals/
│   ├── cron/
│   └── utils/
│
├── finance/                 # Tax and CA domain
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── utils.py             # Tax calculation only; PDF moved to documents
│   └── services/
│
├── notification/            # Notification channels
│   ├── models.py
│   ├── views.py
│   ├── services/
│   │   ├── push.py          # send_push_notification
│   │   ├── channels/
│   │   │   ├── whatsapp.py  # Consolidated WhatsApp
│   │   │   ├── voice.py     # Voice note generation
│   │   │   ├── sms.py       # SMS service
│   │   │   └── email.py     # Email service
│   │   ├── services.py      # notify_user, notify_owner_renter_flagged
│   │   └── communication.py # send_smart_alert
│   └── utils.py             # Removed after consolidation
│
├── documents/               # Document generation & e-signature
│   ├── views.py
│   ├── urls.py
│   ├── utils/
│   │   ├── pdf_generator.py # Unified PDF generation
│   │   └── export_utils.py
│   ├── services/
│   │   ├── leegality.py     # MOVED FROM rentsecure_be + smartbot
│   │   ├── agreement.py     # MOVED FROM smartbot
│   │   └── invoice.py       # MOVED FROM ai_assistant
│   └── templates/
│       └── pdf/
│
├── assistant/               # AI assistant (merged smartbot + ai_assistant)
│   ├── models.py            # SmartBotChat, SmartBotMessage, AIAlert
│   ├── views.py             # smart_bot_reply endpoint
│   ├── intents.py           # Intent extraction
│   ├── services/
│   │   ├── llm.py           # gpt_smart_reply (from gpt_services.py)
│   │   ├── chat.py          # handle_chat_message (from chatbot_service.py)
│   │   └── archive.py       # archive_renter_data (from ai_assistant)
│   └── actions.py           # Domain actions (split from smartbot/actions.py)
│
├── referral/                # Referral program (renamed from referral_and_earn)
│   ├── models.py
│   ├── signals.py
│   └── services/
│
├── analytics/               # Analytics and reporting (NEW)
│   ├── services/
│   │   ├── owner_dashboard.py
│   │   ├── rent_analytics.py
│   │   └── occupancy_analytics.py
│   └── views/
│
├── payments/                # Payment processing (Stage 2)
│   ├── adapters/
│   │   ├── manual.py
│   │   ├── razorpay.py
│   │   └── cashfree.py
│   ├── services/
│   └── webhooks/
│
├── shared/                  # Shared utilities
│   ├── constants.py
│   ├── enums.py
│   ├── exceptions.py
│   ├── interfaces.py
│   ├── types.py
│   ├── utils.py
│   ├── validators.py
│   └── services/
│       └── i18n.py         # MOVED FROM rentsecure_be
│
└── rentsecure_be/           # Project configuration
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    ├── wsgi.py
    └── services/            # DEPRECATED — Stage 2 migration targets
        ├── razorpay_service.py
        ├── cashfree_service.py
        ├── leegality_service.py
        └── i18n_service.py
```

### 9.2 URL Structure

```
/api/
├── auth/                    # core (OTP, login, password)
├── subscriptions/           # core (plans, add-ons, usage limits)
├── bank-details/            # core (owner bank details)
├── properties/              # properties (buildings, units, renters, rent-records)
├── finance/                 # finance (CA profiles, tax submissions)
├── notifications/           # notification (notifications, FCM, device tokens)
├── documents/               # documents (PDFs, agreements)
├── assistant/               # assistant (chatbot)
├── referrals/               # referral (referral codes)
└── analytics/               # analytics (dashboards, reports)
```

---

## 10. Migration Strategy

### Phase 1: Immediate (No Breaking Changes)

**Goal**: Consolidate duplicates and fix misplaced code without breaking existing functionality.

1. **Consolidate WhatsApp** (Low risk)
   - Merge `notification/utils.py` into `notification/services/whatsapp_service.py`
   - Update call sites

2. **Consolidate Leegality** (Medium risk)
   - Merge both Leegality implementations into `documents/services/leegality.py`
   - Update call sites

3. **Move owner reporting** (Low risk)
   - Move `core/services/owner_reporting_service.py` → `properties/services/`
   - Update `core/views.py` imports

4. **Move i18n** (Low risk)
   - Move `rentsecure_be/services/i18n_service.py` → `shared/services/i18n.py`
   - Update call sites

5. **Archive dead stubs** (No risk)
   - Archive `smartbot/tasks.py`

### Phase 2: Assistant Consolidation (Medium risk)

**Goal**: Merge `smartbot` + `ai_assistant` into `assistant`.

1. Create `assistant/` app structure
2. Move AI-related services from `ai_assistant` to `assistant` or their domain apps
3. Move non-AI actions from `smartbot/actions.py` to domain apps
4. Update all imports
5. Delete `ai_assistant/`

### Phase 3: PDF Consolidation (Medium risk)

**Goal**: Consolidate all PDF generation into `documents`.

1. Create `documents/utils/pdf_generator.py`
2. Move all PDF generation functions
3. Update all call sites
4. Remove inline PDF generation

### Phase 4: Notification Restructure (Medium risk)

**Goal**: Separate property-specific notifications from generic channels.

1. Move property-specific notifications to `properties/services/`
2. Keep channel-specific code in `notification/`
3. Update signal handlers

### Phase 5: Create `analytics` App (Low risk)

**Goal**: Extract analytics and reporting.

1. Create `analytics/` app
2. Move `owner_dashboard_summary` to `analytics`
3. Move `properties/services/unit_service.py` analytics functions to `analytics`
4. Update URL routing

### Phase 6: Payments App (Stage 2)

**Goal**: Extract payment processing.

1. Create `payments/` app
2. Move `rentsecure_be/services/razorpay_service.py` → `payments/adapters/razorpay.py`
3. Move `rentsecure_be/services/cashfree_service.py` → `payments/adapters/cashfree.py`
4. Move `rentsecure_be/utils/cashfree_payout.py` → `payments/adapters/cashfree_payout.py`
5. Update imports when feature flags are enabled

---

## 11. Risk Analysis

### 11.1 High-Risk Changes

| Change | Risk | Mitigation |
|--------|------|------------|
| Merge `smartbot` + `ai_assistant` | High | Many cross-imports; run full test suite after each file move |
| Consolidate PDF generation | Medium | Many files depend on PDF functions; maintain backward-compatible wrappers during transition |

### 11.2 Medium-Risk Changes

| Change | Risk | Mitigation |
|--------|------|------------|
| Move Leegality services | Medium | `properties/views/unit_views.py` and `smartbot/actions.py` both depend on it |
| Move property notifications | Medium | `properties/signals/__init__.py` imports from `notification` |
| Move owner reporting | Low | Only `core/views.py` depends on it |

### 11.3 Low-Risk Changes

| Change | Risk | Mitigation |
|--------|------|------------|
| Consolidate WhatsApp | Low | Simple merge; update call sites |
| Move i18n | Low | Only 3 call sites |
| Archive `smartbot/tasks.py` | None | No-op stub; no callers |
| Create `analytics` app | Low | Clean separation; no existing dependencies |

### 11.4 Rollback Strategy

For each phase:
1. Commit each move/merge as a separate commit
2. Run full test suite after each commit
3. If tests fail, revert that specific commit
4. Keep old files as deprecated imports during transition
5. Delete old files only after all call sites are updated

---

## 12. Files That MUST NOT Be Deleted

### 12.1 Core Domain Models

| File | Reason |
|------|--------|
| `core/models.py` | User, UserProfile, OTP, OwnerBankDetails, SubscriptionPlan, UserSubscription, AddOnPurchase, PlanFeatureLimit, UsageLimit, NotificationPreference |
| `properties/models/renter_models.py` | Renter, RentReminderLog, AgreementRevocationLog, ArchivedRenter, RentAgreementDraft, PoliceVerification |
| `properties/models/rent_record_models.py` | RentRecord — core payment tracking |
| `properties/models/unit_models.py` | Unit — core property unit |
| `properties/models/building_models.py` | Building — core property |
| `properties/models/caretaker_models.py` | CareTaker, CareTakerAssignmentLog |
| `properties/models/extra_charge_models.py` | ExtraCharge |
| `properties/models/property_tax_models.py` | PropertyTaxRecord |
| `finance/models.py` | CAProfile, TaxSubmissionToCA |
| `notification/models.py` | Notification, DeviceToken |
| `smartbot/models.py` | SmartBotChat, SmartBotMessage, AIAlert |
| `referral_and_earn/models.py` | Referral |

### 12.2 Core Services (Active)

| File | Reason |
|------|--------|
| `core/services/auth_service.py` | Authentication logic |
| `core/services/otp_service.py` | OTP generation/verification |
| `core/services/password_service.py` | Password management |
| `core/services/subscription_service.py` | Subscription logic |
| `core/services/usage_limit_service.py` | Usage limit enforcement |
| `core/services/bank_details_service.py` | Bank details management |
| `properties/services/unit_service.py` | Core property service |
| `properties/services/building_service.py` | Building CRUD |
| `properties/services/renter_service.py` | Renter management |
| `properties/services/receipt_service.py` | Rent receipt generation |
| `notification/services/notifications.py` | Push notifications |
| `notification/services/voice_note_service.py` | Voice note notifications |
| `documents/utils.py` | Unit history PDF generation |

### 12.3 Deprecated but Must Keep (Stage 2 Migration Targets)

| File | Reason |
|------|--------|
| `rentsecure_be/services/razorpay_service.py` | Stage 2: Move to `payments.adapters.razorpay` |
| `rentsecure_be/services/cashfree_service.py` | Stage 2: Move to `payments.adapters.cashfree` |
| `rentsecure_be/utils/cashfree_payout.py` | Stage 2: Move to `payments.adapters.cashfree_payout` |
| `rentsecure_be/services/leegality_service.py` | Stage 2: Move to `documents.services.leegality` |
| `rentsecure_be/services/i18n_service.py` | Stage 2: Move to `shared.services.i18n` |

### 12.4 AI/Assistant Core (Must Keep)

| File | Reason |
|------|--------|
| `smartbot/services/gpt_services.py` | Core LLM wrapper |
| `smartbot/services/chatbot_service.py` | Core chatbot logic |
| `smartbot/intents.py` | Intent extraction |
| `smartbot/views.py` | Chatbot API endpoint |
| `smartbot/models.py` | Chat history models |
| `ai_assistant/services/archive_service.py` | Renter archival logic |
| `ai_assistant/services/invoice_service.py` | Final invoice PDF generation |

---

## 13. Files That Can Be Archived

| File | Reason | Suggested Action |
|------|--------|-----------------|
| `smartbot/tasks.py` | No-op stub; real signature tracking moved to webhooks | Archive to `archive/smartbot_tasks.py` |
| `smartbot/cron/reminders.py` | Signature reminders; needs manual verification | Move to `properties/cron/` or `documents/cron/` |
| `properties/cron/vacate_reminder.py` | Needs manual verification with ops | Archive until verified |
| `scripts/arch_audit.py` | One-time analysis script | Archive to `scripts/archive/` |
| `tools/migration_rollback_validator.py` | Standalone tool | Archive to `scripts/ci/` |
| `ai_assistant/services/finance_ai.py` | Unclear if actively used; evaluate with product | Archive until product confirmation |
| `smartbot/services/services.py` | Only `notify_owner_renter_flagged`; consider merging into `notification` | Evaluate after notification restructure |

---

## 14. Files That Are True Dead Code

**None identified.**

All files in the repository serve some purpose, even if:
- Misplaced (wrong app)
- Duplicated (multiple implementations)
- Incomplete (placeholder implementations)
- Disabled by feature flag
- Not currently imported

The project is ~50% complete. Many files represent future functionality that has not yet been wired up. **This audit does not classify incomplete or placeholder code as dead code.**

### Previously Deleted (Phase 2 Cleanup)

The following were deleted in Phase 2 and are confirmed safe:

| File/Directory | Reason |
|----------------|--------|
| `dashboard/` | Not in INSTALLED_APPS, no URL routes, no migrations |
| `ai_assistant/` | Not in INSTALLED_APPS, no URL routes (note: some services moved to `assistant` in this audit) |
| `properties/models/subscription_models.py` | Empty placeholder |
| `properties/admin/subscription_admin.py` | Empty placeholder |
| `properties/admin/usage_limit_admin.py` | Empty placeholder |
| `notification/services/schedule_reminders.py` | No imports |
| `properties/services/rent_service.py` | All methods raise NotImplementedError |
| `properties/cron/flag_defaulters.py` | Broken script |
| `scripts/arch_audit.py` | One-time analysis |
| `tools/migration_rollback_validator.py` | Standalone tool |
| `management/commands/seed_subscription_plans.py` | Dev-only script |
| `management/commands/retry_failed_payouts.py` | Disabled Cashfree |
| `management/commands/send_rent_reminders.py` | Disabled WhatsApp |
| `management/commands/monthly_whatsapp_and_email_summary_to_owner.py` | Disabled WhatsApp |
| `management/commands/send_tax_reminders.py` | Empty file |

---

## 15. Special Analysis: `smartbot`, `ai_assistant`, `notification`, `dashboard`

### 15.1 Should `smartbot` remain?

**Yes**, but renamed to `assistant`. The `smartbot` app contains the core AI/chatbot functionality that should remain. However, it has accumulated non-AI responsibilities (Leegality, agreement PDF, WhatsApp, actions) that should be moved out.

### 15.2 Should it become `assistant`?

**Yes.** The name `smartbot` implies a narrow chatbot scope. The app contains broader AI-assisted operations (actions, intent extraction, document signing, PDF generation) that justify the broader `assistant` name.

### 15.3 Should `ai_assistant` merge into `smartbot`?

**Yes.** `ai_assistant` contains services that are imported by `smartbot` and `properties`. The boundary between the two is artificial. Merge into a single `assistant` app.

### 15.4 Should both become `assistant`?

**Yes.** Merge `smartbot` + `ai_assistant` into `assistant`. After the merge, extract non-AI responsibilities to their domain apps.

### 15.5 Which files belong elsewhere?

| File | Destination |
|------|-------------|
| `smartbot/services/leegality_service.py` | `documents/services/leegality.py` |
| `smartbot/services/agreement_service.py` | `documents/services/agreement.py` |
| `smartbot/whatsapp_service.py` | `notification/services/whatsapp_service.py` (merge) |
| `smartbot/actions.py` (operational actions) | `properties/services/` and `notification/services/` |
| `smartbot/cron/reminders.py` | `properties/cron/` or `documents/cron/` |
| `ai_assistant/services/archive_service.py` | `properties/services/` |
| `ai_assistant/services/invoice_service.py` | `documents/services/` |
| `ai_assistant/services/unit_service.py` | `properties/services/` |
| `ai_assistant/services/i18n_service.py` | DELETE (duplicate) |

### 15.6 Which files are temporary?

| File | Reason |
|------|--------|
| `smartbot/tasks.py` | No-op stub; temporary backward compatibility |
| `smartbot/cron/reminders.py` | Needs verification; temporary cron job |
| `ai_assistant/services/finance_ai.py` | Unclear if actively used; temporary prototype |

### 15.7 Which files are feature placeholders?

| File | Reason |
|------|--------|
| `smartbot/intents.py` | Only 4 intents implemented; placeholder for full intent extraction |
| `smartbot/services/chatbot_service.py` | Rule-based + GPT fallback; incomplete intent coverage |
| `smartbot/models.py` (`AIAlert`) | Unused model; placeholder for AI-powered alerts |

### 15.8 Which files should NEVER be deleted?

| File | Reason |
|------|--------|
| `smartbot/services/gpt_services.py` | Core LLM integration |
| `smartbot/services/chatbot_service.py` | Core chatbot logic |
| `smartbot/intents.py` | Intent extraction |
| `smartbot/views.py` | Chatbot API endpoint |
| `smartbot/models.py` | Chat history |
| `ai_assistant/services/archive_service.py` | Renter archival logic |
| `ai_assistant/services/invoice_service.py` | Final invoice generation |
| `smartbot/services/leegality_service.py` | Move to `documents`, but keep implementation |
| `smartbot/services/agreement_service.py` | Move to `documents`, but keep implementation |

---

## 16. Final Recommendations

### Immediate Actions (No Breaking Changes)

1. **Consolidate WhatsApp**: Merge `notification/utils.py` into `notification/services/whatsapp_service.py`
2. **Consolidate Leegality**: Merge both implementations into `documents/services/leegality.py`
3. **Move owner reporting**: `core/services/` → `properties/services/`
4. **Move i18n**: `rentsecure_be/services/i18n_service.py` → `shared/services/i18n.py`
5. **Archive dead stubs**: `smartbot/tasks.py`

### Short-Term Actions (Phase 1-2)

1. **Merge `smartbot` + `ai_assistant`** → `assistant`
2. **Consolidate PDF generation** → `documents/utils/pdf_generator.py`
3. **Move property notifications** → `properties/services/`

### Medium-Term Actions (Phase 3-5)

1. **Create `analytics` app** for owner dashboard and reporting
2. **Restructure notification channels** into `notification/services/channels/`
3. **Extract `payments` app** when Stage 2 payment gateways are activated

### Long-Term Actions (Stage 2+)

1. **Activate payment gateway adapters** (`payments.adapters.razorpay`, `payments.adapters.cashfree`)
2. **Decommission manual payment adapter**
3. **Enable WhatsApp/SMS notifications** when feature flags are turned on

---

## 17. Conclusion

The RentSecure backend is approximately 50% complete and exhibits **rapid development artifacts** rather than intentional architecture. The most critical issues are:

1. **Scattered PDF generation** across 5+ locations
2. **Duplicate implementations** of WhatsApp, Leegality, and i18n
3. **Misplaced services** (owner reporting in `core`, property notifications in `notification`)
4. **Blurred AI boundary** between `smartbot` and `ai_assistant`

The recommended target architecture introduces clear bounded contexts (`core`, `properties`, `finance`, `notification`, `documents`, `assistant`, `analytics`, `payments`, `referral`, `shared`) with well-defined responsibilities and dependency flows.

**No files should be deleted without first moving their functionality to the appropriate bounded context.**

---

*Report generated by Kilo Phase 3 Architecture Audit. All analysis is read-only. No production code was modified.*
