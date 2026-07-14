# RentSecureBE — Architecture Baseline

**Version:** 1.0.0
**Date:** 2026-07-14
**Status:** Baseline (Phase 0)
**Repository:** RentSecureBE
**Baseline Scope:** Current state before Phase 1 refactoring

---

## 1. Current Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PRESENTATION LAYER                               │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  DRF Viewsets │  │  Function-   │  │   Admin      │  │  Templates   │  │
│  │  (ViewSets)   │  │  based Views │  │   (Django)   │  │  (PDF/HTML)  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘  └──────────────┘  │
│         │                  │                                               │
│         ▼                  ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        URL Routing Layer                              │  │
│  │  rentsecure_be/urls.py  →  core/urls.py  →  properties/urls.py     │  │
│  │  notification/urls.py   →  finance/urls.py  →  documents/urls.py    │  │
│  │  ai_assistant/urls.py   →  smartbot/urls.py                         │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                           │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            APPLICATION LAYER                                │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    core      │  │  properties  │  │  notification│  │   finance    │  │
│  │  (Identity   │  │  (Property   │  │  (Comm.)     │  │  (Tax/CA)    │  │
│  │  &Subscript.) │  │  & Rent)     │  │              │  │              │  │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤  │
│  │  services/   │  │  services/   │  │  services/   │  │  (no svc)    │  │
│  │  serializers │  │  serializers │  │              │  │  serializers │  │
│  │  views       │  │  views       │  │  views       │  │  views       │  │
│  │  models      │  │  models/     │  │  models      │  │  models      │  │
│  │  repositories│  │  repositories│  │              │  │              │  │
│  │  policies/   │  │  policies/   │  │              │  │              │  │
│  │  signals/    │  │  signals/    │  │              │  │              │  │
│  │  utils/      │  │  utils/      │  │              │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │                  │        │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐  │
│  │  documents   │  │  smartbot    │  │  ai_assistant│  │ referral_and │  │
│  │  (PDF gen)   │  │  (AI/Chat)   │  │  (AI svcs)   │  │   _earn      │  │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤  │
│  │  (no models) │  │  services/   │  │  services/   │  │  models      │  │
│  │  views       │  │  views       │  │  views       │  │  signals     │  │
│  │  templates/  │  │  models      │  │  receivers   │  │              │  │
│  │  utils/      │  │  cron/       │  │              │  │              │  │
│  │  tests/      │  │  tests/      │  │              │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────────────┘  │
│         │                  │                  │                            │
│         ▼                  ▼                  ▼                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       rentsecure_be (Project Core)                  │  │
│  │  services/  (cashfree_service, razorpay_service, i18n_service,     │  │
│  │              leegality_service)                                      │  │
│  │  utils/     (cashfree_payout, etc.)                                 │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                           │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DOMAIN LAYER                                   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          shared/                                     │  │
│  │  constants.py  enums.py  exceptions.py  types.py  utils.py          │  │
│  │  validators.py  interfaces.py  domain_events.py                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Each app's models/ defines the domain entities for that bounded context   │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            INFRASTRUCTURE LAYER                             │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  PostgreSQL  │  │    Redis     │  │   Celery     │  │   Twilio     │  │
│  │  (Database)  │  │  (Cache/     │  │  + Beat      │  │  (SMS/WA)    │  │
│  │              │  │   Queue)     │  │  (Tasks)     │  │              │  │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤  │
│  │  Razorpay    │  │  Cashfree    │  │   OpenAI     │  │    S3        │  │
│  │  (Payments)  │  │  (Payouts)   │  │  (AI/Chat)   │  │  (Storage)   │  │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤  │
│  │  Leegality   │  │  Firebase    │  │  edge-tts    │  │  Google      │  │
│  │  (E-Sign)    │  │  (FCM Push)  │  │  (TTS)       │  │  Translate   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    CI/CD: GitHub Actions (27 workflows)              │  │
│  │  lint → test → architecture → security → quality → deploy           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              Target: AWS EC2 (Docker Compose)                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Dependency Graph

### 2.1 App-to-App Dependencies

```
rentsecure_be (project core)
├── core (Identity, Subscription, Auth)
│   └── properties (Property, Rent, Renter)
├── notification (Communication)
│   ├── imports from: rentsecure_be (i18n, payment services)
│   └── imports from: properties (rent records, extra charges)
├── properties
│   └── imports from: rentsecure_be (i18n)
├── smartbot (AI, Chatbot, Agreements)
│   ├── imports from: rentsecure_be (cashfree, leegality)
│   └── imports from: notification (whatsapp)
├── ai_assistant (AI services, Invoice, Archive)
│   ├── imports from: properties (models, signals)
│   └── imports from: rentsecure_be (i18n — duplicate)
├── finance (Tax, CA)
│   └── imports from: properties (tax records)
├── documents (PDF generation)
│   ├── imports from: properties (rent records, units)
│   └── imports from: finance (tax submissions)
├── referral_and_earn (Referral codes)
│   └── imported by: core (ReferralService)
└── dashboard (Analytics — NOT registered in INSTALLED_APPS)
```

### 2.2 Internal Module Dependencies

```
core/
  models.py          ← AbstractUser extension, OTP, Subscription, Bank
  services/          ← BaseService (unused), Auth, OTP, Subscription, Bank, Referral
  serializers.py     ← DRF serializers
  views.py           ← API endpoints
  signals.py         ← post_save on User

properties/
  models/            ← Building, Unit, Renter, RentRecord, ExtraCharge, CareTaker, etc.
  repositories/      ← Building, Unit, Renter, RentRecord (concrete, no interface)
  services/          ← Building, Unit (class-based); Rent, Renter, Vacancy, Occupancy (stubs)
                        Summary, Receipt, Onboarding, ExtraCharge, Renter (module fns)
  serializers/        ← Per-model DRF serializers
  views/              ← Per-model ViewSets + function-based views
  policies/           ← UnitPolicy (authorization)
  signals/            ← Renter lifecycle signals
  cron/               ← Flag defaulters, vacate reminders
  management/commands ← Monthly rent records, reminders, late fees, payouts

notification/
  models.py           ← Notification, DeviceToken
  services/           ← Module-level functions: WhatsApp, SMS, Voice, Push, Rent notify
  views.py            ← Notification CRUD, FCM registration
  management/commands ← Extra charge reminders

rentsecure_be/
  services/           ← cashfree_service, razorpay_service, i18n_service, leegality_service
  utils/              ← cashfree_payout (external API wrapper)
```

### 2.3 External Integration Dependencies

```
RentSecureBE
├── Twilio (SMS, WhatsApp)
│   └── Used by: core/services/otp_service.py, notification/services/
├── Razorpay (Payment Links)
│   └── Used by: rentsecure_be/services/razorpay_service.py, core/views.py
├── Cashfree (Payouts, Beneficiary Management)
│   └── Used by: rentsecure_be/services/cashfree_service.py, core/services/bank_details_service.py
├── Leegality (E-Signature)
│   └── Used by: rentsecure_be/services/leegality_service.py, smartbot/services/leegality_service.py
├── OpenAI (GPT Chat)
│   └── Used by: smartbot/services/gpt_services.py, smartbot/services/chatbot_service.py
├── AWS S3 (File Storage)
│   └── Used by: notification/services/whatsapp_service.py (voice note uploads)
├── Firebase FCM (Push Notifications)
│   └── Used by: notification/views.py, notification/utils.py
├── Google Translate (i18n)
│   └── Used by: rentsecure_be/services/i18n_service.py, ai_assistant/services/i18n_service.py (duplicate)
└── edge-tts (Text-to-Speech)
    └── Used by: notification/services/voice_service.py
```

---

## 3. Layer Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                │
│                                                                           │
│  REST API (DRF ViewSets + Function-based Views)                           │
│  Admin Interface (Django Admin)                                           │
│  PDF Generation (WeasyPrint + Django Templates)                           │
│  WebSocket (Channels + Redis)                                             │
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │ HTTP / WS
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                                 │
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Serializ-  │  │   Permis-   │  │   Service   │  │   Policy/       │  │
│  │   ers (DRF)  │  │   sions     │  │   Layer     │  │   Enforcer      │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────────┘  │
│         │                │                │                │              │
│         └────────────────┼────────────────┼────────────────┘              │
│                          │                │                               │
│                          ▼                ▼                               │
│                 ┌──────────────────────────────────┐                      │
│                 │    Views (thin, orchestrate)     │                      │
│                 └──────────────────────────────────┘                      │
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                            DOMAIN LAYER                                   │
│                                                                           │
│  ┌─────────────────────────┐  ┌───────────────────────────────────────┐  │
│  │      Models (ORM)       │  │     Repositories (Data Access)        │  │
│  │  - Entities             │  │  - Query construction                 │  │
│  │  - Value Objects        │  │  - Eager loading                      │  │
│  │  - Aggregates           │  │  - No business logic                  │  │
│  │  - Domain Events        │  │                                       │  │
│  │  - Invariants (clean()) │  │  (properties app only — 4 repos)      │  │
│  └──────────┬──────────────┘  └───────────────────────────────────────┘  │
│             │                                                             │
│  ┌──────────┴──────────────┐  ┌───────────────────────────────────────┐  │
│  │   Domain Services        │  │     Shared Kernel                     │  │
│  │  - FeatureEnforcer       │  │  - constants, enums, exceptions       │  │
│  │  - UnitPolicy            │  │  - types, validators, utils           │  │
│  │  - (Business logic)      │  │  - interfaces (unused Protocols)      │  │
│  └──────────────────────────┘  └───────────────────────────────────────┘  │
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         INFRASTRUCTURE LAYER                              │
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  PostgreSQL │  │    Redis    │  │   Celery    │  │  External APIs  │  │
│  │  (ORM)      │  │  (Cache/    │  │  (Beat +    │  │  (Twilio,       │  │
│  │             │  │   Broker)   │  │   Workers)  │  │   Razorpay,     │  │
│  │             │  │             │  │             │  │   Cashfree,     │  │
│  │             │  │             │  │             │  │   OpenAI, etc.) │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Layer Rules (Current State)

| Layer | Allowed Imports | Forbidden Imports |
|-------|-----------------|-------------------|
| Views | Services, Serializers, Permissions, Models, Shared | Other apps' views/serializers |
| Services | Models (same app), Repositories (same app), Shared | Other apps' services (except via rentsecure_be), HTTP clients |
| Repositories | Models (same app), Django ORM | Business logic, services, HTTP |
| Models | Django, Shared (utilities only) | Services, Views, Other apps' models |
| Shared | Python stdlib only | Django, Models, Services, Views |

**Current Violations:**
- `notification/services/` imports `rentsecure_be/services/i18n_service.py` (cross-app)
- `smartbot/` imports `rentsecure_be/services/cashfree_service.py` (cross-app)
- `core/services/bank_details_service.py` imports `rentsecure_be/utils/cashfree_payout.py` (cross-app)
- `ai_assistant/services/i18n_service.py` duplicates `rentsecure_be/services/i18n_service.py`

---

## 4. Domain Map

### 4.1 Bounded Contexts

| Bounded Context | App | Description | Aggregate Roots |
|-----------------|-----|-------------|-----------------|
| **Identity & Subscription** | `core` | User authentication, OTP, profiles, subscription plans, usage limits, referrals, bank details | `User`, `SubscriptionPlan`, `UserSubscription`, `UsageLimit`, `Referral` |
| **Property & Rent** | `properties` | Buildings, units, renters, rent records, extra charges, caretakers, property tax, agreements | `Building`, `Unit`, `Renter`, `RentRecord`, `ExtraCharge`, `CareTaker`, `PropertyTaxRecord` |
| **Finance & Compliance** | `finance` | CA profiles, tax submissions | `CAProfile`, `TaxSubmissionToCA` |
| **Communication** | `notification` | Notifications, device tokens, multi-channel messaging | `Notification`, `DeviceToken` |
| **Documents** | `documents` | PDF generation for receipts, agreements, dossiers | *(no models — stateless generators)* |
| **AI Assistant** | `smartbot`, `ai_assistant` | Chatbot, AI alerts, agreement generation, invoice generation, archive | `SmartBotChat`, `SmartBotMessage`, `AIAlert` |
| **Growth** | `referral_and_earn` | Referral codes and bonuses | `Referral` |
| **Analytics** | `dashboard` | Owner dashboard (views exist but app NOT registered) | *(no models)* |
| **Infrastructure** | `rentsecure_be` | Payment services, i18n, e-signature, project configuration | *(no models — pure service layer)* |

### 4.2 Context Map

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         RENTSECURE DOMAIN MAP                             │
│                                                                           │
│  ┌──────────────────────┐       ┌──────────────────────┐                │
│  │  Identity &          │       │  Property &          │                │
│  │  Subscription        │◄─────►│  Rent                │                │
│  │  (core)              │       │  (properties)        │                │
│  │                      │       │                      │                │
│  │  - User              │       │  - Building          │                │
│  │  - SubscriptionPlan  │       │  - Unit              │                │
│  │  - UserSubscription  │       │  - Renter            │                │
│  │  - UsageLimit        │       │  - RentRecord        │                │
│  │  - OwnerBankDetails  │       │  - ExtraCharge       │                │
│  │  - Referral          │       │  - CareTaker         │                │
│  │                      │       │  - RentAgreement     │                │
│  └──────────┬───────────┘       └──────────┬───────────┘                │
│             │                               │                            │
│             │                               │                            │
│  ┌──────────┴───────────┐       ┌──────────┴───────────┐                │
│  │  Finance &           │       │  Communication       │                │
│  │  Compliance          │       │  (notification)      │                │
│  │  (finance)           │       │                      │                │
│  │                      │       │  - Notification      │                │
│  │  - CAProfile         │       │  - DeviceToken       │                │
│  │  - TaxSubmission     │       │  - WhatsApp/SMS/Push │                │
│  │                      │       │  - Voice notes       │                │
│  └──────────────────────┘       └──────────────────────┘                │
│                                                                           │
│  ┌──────────────────────┐       ┌──────────────────────┐                │
│  │  AI Assistant        │       │  Growth              │                │
│  │  (smartbot +         │       │  (referral_and_earn) │                │
│  │   ai_assistant)      │       │                      │                │
│  │                      │       │  - Referral          │                │
│  │  - SmartBotChat      │       │  - Bonus             │                │
│  │  - AIAlert           │       │                      │                │
│  │  - AgreementService  │       │                      │                │
│  │  - InvoiceService    │       │                      │                │
│  └──────────────────────┘       └──────────────────────┘                │
│                                                                           │
│  ┌──────────────────────┐       ┌──────────────────────┐                │
│  │  Documents           │       │  Analytics           │                │
│  │  (documents)         │       │  (dashboard —        │                │
│  │                      │       │   UNREGISTERED)      │                │
│  │  - PDF Generators    │       │                      │                │
│  │  - Templates         │       │  - Dashboard views   │                │
│  └──────────────────────┘       └──────────────────────┘                │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  Infrastructure (rentsecure_be)                                  │    │
│  │  - Payment services (Razorpay, Cashfree)                         │    │
│  │  - i18n service                                                  │    │
│  │  - E-signature service (Leegality)                               │    │
│  │  - Project configuration (settings, urls, wsgi, asgi)            │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  Shared Kernel (shared/)                                         │    │
│  │  - constants, enums, exceptions, types, utils, validators        │    │
│  │  - interfaces (unused Protocols), domain_events (unused)         │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Anti-Corruption Layers

**Current State:** None. Cross-context communication is via direct imports.

| From | To | Mechanism | Problem |
|------|----|-----------|---------|
| `notification` | `rentsecure_be` | Direct import of `i18n_service` | Breaks bounded context boundary |
| `smartbot` | `rentsecure_be` | Direct import of `cashfree_service` | Breaks bounded context boundary |
| `ai_assistant` | `rentsecure_be` | Duplicate `i18n_service` | No shared kernel, code duplication |
| `core` | `referral_and_earn` | Lazy import of model | Works but bypasses context |

---

## 5. Bounded Contexts (Detailed)

### 5.1 Identity & Subscription (`core`)

**Purpose:** User identity, authentication, authorization, subscription management, usage limits, referrals, and owner banking details.

**Aggregate Roots:**
- `User` — Central identity aggregate. Extends `AbstractUser`. Owns profiles, subscriptions, bank details, referrals, notifications.
- `SubscriptionPlan` — Plan catalog (Free, Pro, Elite). Defines feature limits.
- `UserSubscription` — Active subscription for a user. Links to a plan.
- `UsageLimit` — Tracks current usage against plan limits per feature key.
- `Referral` — Referral code and bonus tracking per user.

**Entities:**
- `UserProfile` — Extended profile (WhatsApp, language).
- `NotificationPreference` — Per-user notification channel preferences.
- `OTP` — Temporary OTP for phone verification.
- `OwnerBankDetails` — Bank account for Cashfree payouts.
- `AddOnPurchase` — One-time or recurring add-on purchases.
- `PlanFeatureLimit` — Feature limit definition per plan.

**Domain Events:**
- `UserCreated` (signal: `post_save` on User)
- `OTPSent`, `OTPVerified`

**External Integrations:**
- Twilio (OTP via SMS)
- Cashfree (beneficiary registration)

### 5.2 Property & Rent (`properties`)

**Purpose:** Property portfolio management, unit management, renter lifecycle, rent collection, extra charges, caretakers, property tax, agreements.

**Aggregate Roots:**
- `Building` — Property building. Owns units, tax records.
- `Unit` — Individual unit within a building. Links to renters, rent records, images, documents, agreements, caretakers.
- `Renter` — Renter occupying a unit. Has lifecycle (onboarding → active → exited → archived).
- `RentRecord` — Monthly rent record for a unit/renter. Tracks payment status, payout status, late fees.

**Entities:**
- `UnitVacancy` — Vacancy reason and date.
- `UnitDocument` — Documents uploaded for a unit.
- `UnitImage` — Images uploaded for a unit.
- `RentReminderLog` — Log of rent reminder sends.
- `AgreementRevocationLog` — Log of agreement revocations.
- `RentAgreementDraft` — Draft agreement for e-signature.
- `PoliceVerification` — Police verification document.
- `CareTaker` — Caretaker assigned to a unit.
- `CareTakerAssignmentLog` — Audit log for caretaker assignments.
- `ExtraCharge` — Additional charges (maintenance, electricity) for a renter.
- `PropertyTaxRecord` — Property tax record for a building.
- `ArchivedRenter` — Snapshot of renter data after exit.

**Domain Events:**
- `renter_exited` — Emitted when renter exits.
- `renter_archived` — Emitted when renter is archived.
- `unit_vacated` — Implicit via signal.

**External Integrations:**
- Leegality (e-signature)
- WeasyPrint (PDF generation)
- Twilio (WhatsApp notifications)
- edge-tts (voice notes)

### 5.3 Finance & Compliance (`finance`)

**Purpose:** Chartered accountant profiles and tax submission management.

**Aggregate Roots:**
- `CAProfile` — CA profile linked to a user.
- `TaxSubmissionToCA` — Tax submission record sent to a CA.

**External Integrations:**
- Email (tax summary PDFs)

### 5.4 Communication (`notification`)

**Purpose:** Multi-channel notification delivery (WhatsApp, SMS, Push, Email, Voice).

**Aggregate Roots:**
- `Notification` — In-app notification record.
- `DeviceToken` — FCM device token for push notifications.

**External Integrations:**
- Twilio (WhatsApp, SMS)
- Firebase FCM (Push)
- AWS S3 (Voice note upload)
- edge-tts (TTS)

### 5.5 AI Assistant (`smartbot`, `ai_assistant`)

**Purpose:** AI-powered chatbot, smart alerts, agreement generation, invoice generation, data archival.

**Aggregate Roots:**
- `SmartBotChat` — Chat conversation.
- `SmartBotMessage` — Individual chat message.
- `AIAlert` — AI-generated alert for owners.

**External Integrations:**
- OpenAI (GPT chat)
- Leegality (e-signature)
- WeasyPrint (PDF)

### 5.6 Growth (`referral_and_earn`)

**Purpose:** Referral program management.

**Aggregate Roots:**
- `Referral` — Referral code and bonus per user.

### 5.7 Documents (`documents`)

**Purpose:** PDF document generation (receipts, agreements, dossiers).

**Aggregate Roots:** None (stateless generators).

**External Integrations:**
- WeasyPrint (PDF)
- Django Templates (HTML → PDF)

### 5.8 Analytics (`dashboard`)

**Purpose:** Owner dashboard and analytics.

**Aggregate Roots:** None (read-only views).

**Status:** App exists but is **NOT registered in INSTALLED_APPS** and URLs are **not included** in root `urls.py`.

---

## 6. Aggregate Roots

### 6.1 Identity & Subscription

| Aggregate Root | Root Entity | Children / Entities | Invariants | Repository |
|---------------|-------------|---------------------|------------|-----------|
| `User` | `User` | UserProfile, NotificationPreference, OTP, OwnerBankDetails, UserSubscription, AddOnPurchase, Referral | User must have exactly one profile, subscription, and notification preference | No repository (uses Django ORM directly) |
| `SubscriptionPlan` | `SubscriptionPlan` | PlanFeatureLimit | Plan name must be unique | No repository |
| `UserSubscription` | `UserSubscription` | — | User can have only one active subscription | No repository |
| `UsageLimit` | `UsageLimit` | — | Unique per (user, feature_key) | No repository |

### 6.2 Property & Rent

| Aggregate Root | Root Entity | Children / Entities | Invariants | Repository |
|---------------|-------------|---------------------|------------|-----------|
| `Building` | `Building` | Unit, PropertyTaxRecord | Unique per (name, address_line, city, owner) | `BuildingRepository` |
| `Unit` | `Unit` | Renter, UnitImage, UnitDocument, RentAgreementDraft, PoliceVerification, CareTaker, RentRecord, ExtraCharge, UnitVacancy | Unique per (owner, unit, building, address_line); only one active renter per unit | `UnitRepository` |
| `Renter` | `Renter` | RentRecord, AgreementRevocationLog, ArchivedRenter | Unique per (unit, phone); end_date ≥ start_date | `RenterRepository` |
| `RentRecord` | `RentRecord` | — | Unique per (unit, due_date); amount > 0; status ∈ {pending, paid, overdue, cancelled} | `RentRecordRepository` |
| `ExtraCharge` | `ExtraCharge` | — | amount > 0; due_date in future | No repository (uses ORM directly) |

### 6.3 Finance & Compliance

| Aggregate Root | Root Entity | Children / Entities | Invariants | Repository |
|---------------|-------------|---------------------|------------|-----------|
| `CAProfile` | `CAProfile` | TaxSubmissionToCA | One CA profile per user | No repository |
| `TaxSubmissionToCA` | `TaxSubmissionToCA` | — | financial_year format YYYY-YY | No repository |

### 6.4 Communication

| Aggregate Root | Root Entity | Children / Entities | Invariants | Repository |
|---------------|-------------|---------------------|------------|-----------|
| `Notification` | `Notification` | — | Owned by user | No repository |
| `DeviceToken` | `DeviceToken` | — | Unique per (user, token) | No repository |

### 6.5 AI Assistant

| Aggregate Root | Root Entity | Children / Entities | Invariants | Repository |
|---------------|-------------|---------------------|------------|-----------|
| `SmartBotChat` | `SmartBotChat` | SmartBotMessage | Owned by user | No repository |
| `AIAlert` | `AIAlert` | — | Owned by owner | No repository |

### 6.6 Growth

| Aggregate Root | Root Entity | Children / Entities | Invariants | Repository |
|---------------|-------------|---------------------|------------|-----------|
| `Referral` | `Referral` | — | referral_code unique; auto-generated UUID | No repository |

---

## 7. Entity Relationships

### 7.1 Core Domain

```
User (1) ────────────── (1) UserProfile
User (1) ────────────── (1) NotificationPreference
User (1) ────────────── (1) UserSubscription
User (1) ────────────── (1) OwnerBankDetails
User (1) ────────────── (1) Referral
User (1) ────────────── (N) AddOnPurchase
User (1) ────────────── (N) OTP

SubscriptionPlan (1) ─── (N) UserSubscription
SubscriptionPlan (1) ─── (N) PlanFeatureLimit

Referral (N) ─────────── (1) User (referred_by)
```

### 7.2 Property Domain

```
User (1) ────────────── (N) Building
Building (1) ────────── (N) Unit
Building (1) ────────── (N) PropertyTaxRecord

Unit (1) ────────────── (N) Renter
Unit (1) ────────────── (N) UnitImage
Unit (1) ────────────── (N) UnitDocument
Unit (1) ────────────── (1) RentAgreementDraft
Unit (1) ────────────── (1) PoliceVerification
Unit (1) ────────────── (N) CareTaker
Unit (1) ────────────── (N) RentRecord
Unit (1) ────────────── (N) ExtraCharge
Unit (1) ────────────── (1) UnitVacancy

Renter (1) ──────────── (N) RentRecord
Renter (1) ──────────── (N) UnitDocument
Renter (1) ──────────── (N) UnitImage
Renter (1) ──────────── (1) AgreementRevocationLog
Renter (1) ──────────── (1) ArchivedRenter

CareTaker (1) ───────── (N) CareTakerAssignmentLog
```

### 7.3 Finance Domain

```
User (1) ────────────── (1) CAProfile
User (1) ────────────── (N) TaxSubmissionToCA
CAProfile (1) ───────── (N) TaxSubmissionToCA
```

### 7.4 Notification Domain

```
User (1) ────────────── (N) Notification
User (1) ────────────── (N) DeviceToken
```

### 7.5 AI Domain

```
User (1) ────────────── (N) SmartBotChat
User (1) ────────────── (N) SmartBotMessage
User (1) ────────────── (N) AIAlert (as owner)
```

### 7.6 Cross-Domain Relationships

```
RentRecord ────────────► notification (sends notifications)
RentRecord ────────────► cashfree_service (payouts)
Renter ───────────────► notification (WhatsApp onboarding)
Renter ───────────────► ai_assistant (archive on exit)
Building ─────────────► properties (analytics, summaries)
Unit ──────────────────► properties (analytics, vacancy)
```

---

## 8. Shared Kernel

### 8.1 Current Shared Kernel (`shared/`)

| Module | Contents | Usage | Notes |
|--------|----------|-------|-------|
| `constants.py` | Shared constants | Used across apps | Stable, low-risk |
| `enums.py` | Enum definitions (RenterStatus, VacancyStatus, etc.) | Used across apps | Stable, low-risk |
| `exceptions.py` | Custom exception classes | Used across apps | Stable, low-risk |
| `types.py` | TypedDicts, type aliases | Used across apps | Stable, low-risk |
| `utils.py` | Utility functions | Used across apps | Needs review for domain leakage |
| `validators.py` | Django validators | Used across apps | Stable, low-risk |
| `interfaces.py` | `Repository[T]`, `Service`, `EventBus` Protocols | **NOT IMPLEMENTED** | Dead code — no concrete implementations |
| `domain_events.py` | `BaseDomainEvent`, `EventMetadata` dataclasses | **NOT USED** | Dead code — no events dispatched |

### 8.2 Shared Kernel Issues

1. **`interfaces.py` defines unused Protocols** — `Repository[T]`, `Service`, `EventBus` are defined but no concrete class implements them. This creates confusion and maintenance burden.
2. **`domain_events.py` is unused** — Domain events are defined but never dispatched. Signals are used instead.
3. **Code duplication in `i18n_service.py`** — Identical `translate_msg` function exists in both `rentsecure_be/services/` and `ai_assistant/services/`. This should be in the shared kernel.
4. **`utils.py` may contain domain-specific code** — Needs audit to ensure no business logic leaks into shared utilities.

### 8.3 Recommended Shared Kernel Boundaries

**Allowed in Shared Kernel:**
- Pure Python utilities (no Django dependencies)
- Type definitions (TypedDict, Literal, Protocol)
- Enum definitions
- Exception classes
- Validators (pure validation logic)
- Constants (non-business)

**Forbidden in Shared Kernel:**
- Django model imports
- Business logic
- External API calls
- Database queries
- Django-specific utilities

---

## 9. External Integrations

### 9.1 Integration Inventory

| Service | Protocol | Auth Method | Feature Flag | Retry Policy | Circuit Breaker |
|---------|----------|-------------|--------------|--------------|-----------------|
| **Twilio SMS** | HTTPS REST | Account SID + Auth Token | None (mocked in DEBUG) | None | None |
| **Twilio WhatsApp** | HTTPS REST | Account SID + Auth Token | `ENABLE_WHATSAPP` | None | None |
| **Razorpay** | HTTPS REST | Key ID + Key Secret | `ENABLE_RAZORPAY` | None | None |
| **Cashfree** | HTTPS REST | Client ID + Client Secret | `ENABLE_CASHFREE` | None | None |
| **Leegality** | HTTPS REST | API Key + Org ID | `ENABLE_LEEGALITY` | None | None |
| **OpenAI** | HTTPS REST | API Key | `ENABLE_OPENAI` | None | None |
| **AWS S3** | HTTPS REST | Access Key + Secret | Implicit (bucket config) | None | None |
| **Firebase FCM** | HTTPS REST | Server Key | `ENABLE_PUSH_NOTIFICATION` | None | None |
| **Google Translate** | HTTPS REST | Implicit (deep-translator) | None | None | None |
| **edge-tts** | HTTPS REST | None | `ENABLE_VOICE` | None | None |

### 9.2 Integration Issues

1. **No retry policies** — All external API calls are fire-and-forget. No exponential backoff, no retry decorators.
2. **No circuit breakers** — If an external service is down, the application will hang or fail silently.
3. **No timeout configuration visible** — HTTP client timeouts are not explicitly configured in many places.
4. **Direct HTTP calls in services** — Some services use `requests` directly instead of through an abstraction layer.
5. **No bulkhead pattern** — All external calls share the same connection pool.
6. **No fallback strategies** — If WhatsApp fails, no fallback to SMS or email is configured in most places.

### 9.3 Webhook Integrations

| Webhook | Provider | Signature Verification | Retry Handling | Idempotency |
|---------|----------|----------------------|----------------|-------------|
| Cashfree Payout | Cashfree | ✅ HMAC-SHA256 | None | ✅ (by payout_reference) |
| Razorpay Payment | Razorpay | ✅ HMAC-SHA256 | None | ✅ (by status check) |
| Leegality E-Sign | Leegality | ✅ HMAC-SHA256 | None | ✅ (always 200) |
| WhatsApp/Meta | Meta | ✅ HMAC-SHA256 | None | None |

---

## 10. Request Lifecycle

### 10.1 Owner API Request Flow

```
1. HTTP Request
   ↓
2. Django URL Router (rentsecure_be/urls.py → properties/urls.py)
   ↓
3. Middleware Stack
   - SecurityMiddleware (SSL redirect)
   - SessionMiddleware
   - CsrfViewMiddleware (skipped for @csrf_exempt views)
   - AuthenticationMiddleware
   - HistoryRequestMiddleware (simple-history)
   ↓
4. DRF ViewSet / Function-based View
   - Permission check (IsAuthenticated)
   - Authentication (JWTAuthentication)
   ↓
5. Serializer (validation)
   ↓
6. Service Layer (if exists)
   - Business logic
   - Repository calls (if exists)
   ↓
7. Model Layer (if no service/repository)
   - Direct ORM calls
   ↓
8. Response
   - DRF Response
   - PDF (WeasyPrint)
   - JSON
```

### 10.2 Renter-Facing Request Flow

```
1. HTTP Request
   ↓
2. URL Router
   ↓
3. View (often function-based)
   - Renter lookup by phone/onboarding_token
   ↓
4. Direct ORM calls (no service layer for renter views)
   ↓
5. Response (JSON, PDF, or redirect)
```

### 10.3 Webhook Request Flow

```
1. HTTP POST from External Provider
   ↓
2. @csrf_exempt decorator (CSRF bypass)
   ↓
3. Signature Verification (HMAC-SHA256)
   - Fail → 400
   ↓
4. Business Logic
   - Idempotency check (where implemented)
   - Model updates
   - Signal triggers
   ↓
5. Notification Dispatch (async in some cases)
   ↓
6. HTTP 200/201 Response
```

### 10.4 Background Task Flow

```
1. Django Management Command (cron-style)
   OR
   django_celery_beat PeriodicTask
   ↓
2. Task Execution
   - Direct ORM queries
   - Service functions
   - Notification dispatch
   ↓
3. No retry policy
   No error handling
   No monitoring
```

---

## 11. Payment Flow

### 11.1 Rent Collection Flow (Razorpay)

```
Owner creates RentRecord (status=pending)
   ↓
Razorpay payment link created (rentsecure_be/services/razorpay_service.py)
   ↓
Link sent to renter (WhatsApp/Email)
   ↓
Renter pays via Razorpay
   ↓
Razorpay webhook → /api/rent/payment-callback/
   ↓
Signature verification
   ↓
RentRecord.status = PAID
RentRecord.paid_on = today
RentRecord.transaction_id = razorpay_txn_id
   ↓
Signal: handle_rent_payment
   ↓
- send_thank_you_voice_note
- send_rent_receipt_on_payment
- Cancel reminder jobs
   ↓
Cashfree payout initiated (rentsecure_be/services/cashfree_service.py)
   ↓
OwnerBankDetails lookup
   ↓
Cashfree beneficiary registration (if needed)
   ↓
Cashfree payout creation
   ↓
Cashfree webhook → /webhook/cashfree/payout/
   ↓
RentRecord.payout_status = SUCCESS/FAILED
   ↓
Notification to owner and renter
```

### 11.2 Payout Retry Flow

```
RentRecord.payout_status = FAILED
   ↓
Manual retry: /api/owner/retry_payout_api/<rent_id>/
   ↓
BankDetailsService.retry_failed_payouts(owner)
   ↓
Cashfree payout retry (increments payout_retries)
   ↓
Notification to owner
```

### 11.3 Payment Flow Issues

1. **No distributed locking** — Multiple webhook retries could cause duplicate processing.
2. **No idempotency key** — Razorpay callback relies on status check, not a proper idempotency key.
3. **No saga pattern** — Payment → payout is a two-phase commit without compensation.
4. **Cashfree webhook is synchronous** — Long-running webhook could timeout.
5. **No payment reconciliation job** — No scheduled task to reconcile pending payouts.

---

## 12. Notification Flow

### 12.1 Notification Dispatch Flow

```
Trigger (signal, webhook, management command)
   ↓
Service function (e.g., notify_renter, notify_owner)
   ↓
i18n translation (if target_lang != 'en')
   ↓
Channel selection:
   - WhatsApp (Twilio) — primary
   - SMS (Twilio) — fallback
   - Push (FCM) — mobile app
   - Email (SMTP) — documents
   - Voice (edge-tts + Twilio audio) — premium
   ↓
Notification record created (Notification model)
   ↓
DeviceToken lookup (for FCM)
   ↓
External API call
   ↓
RentReminderLog entry (for reminders)
```

### 12.2 Notification Issues

1. **No notification queue** — Notifications are sent synchronously in the request path.
2. **No fallback chain** — If WhatsApp fails, no automatic fallback to SMS.
3. **No notification deduplication** — Same notification could be sent multiple times.
4. **No notification preferences enforcement** — `NotificationPreference` model exists but is not consulted by notification services.
5. **No notification template management** — Messages are hardcoded in service functions.

---

## 13. Authentication Flow

### 13.1 OTP-Based Authentication

```
Client sends phone number
   ↓
POST /api/auth/send-otp/
   ↓
OTPService.send_otp()
   - Rate limit check (60s cooldown)
   - OTP creation (6-digit, 5min expiry)
   - Twilio SMS delivery
   ↓
Client receives OTP
   ↓
POST /api/auth/owner/verify-otp/ or /api/auth/renter/verify-otp/
   ↓
OTP verification
   - Code match check
   - Expiry check
   ↓
User lookup/creation (by phone)
   ↓
JWT token pair (access: 5min, refresh: 35 days)
   ↓
Referral processing (if referral_code in OTP)
   ↓
Default subscription assignment (signal: assign_default_plan)
```

### 13.2 Authentication Issues

1. **No MFA** — OTP is only for initial login, not for sensitive operations.
2. **Long-lived refresh tokens** — 35 days is excessive for a property management app.
3. **No token revocation** — No mechanism to revoke refresh tokens.
4. **No session management** — No way to see active sessions or force logout.
5. **No password policy enforcement** — Password validators exist but are minimal.
6. **No account lockout** — No brute-force protection beyond OTP rate limiting.

---

## 14. Background Processing Flow

### 14.1 Current Background Processing

| Task Type | Mechanism | Location |
|-----------|-----------|----------|
| Daily rent reminders | Management command | `management/commands/send_rent_reminders.py` |
| Monthly rent records generation | Management command | `management/commands/generate_monthly_rent_records.py` |
| Late fee application | Management command | `management/commands/apply_late_fees.py` |
| Tax reminders | Management command | `management/commands/send_tax_reminders.py` |
| Monthly owner summary | Management command | `management/commands/monthly_whatsapp_and_email_summary_to_owner.py` |
| Extra charge reminders | Management command | `management/commands/send_extra_charge_reminders.py` |
| Renter auto-deactivation | Management command | `management/commands/auto_deactivate_renters.py` |
| Vacant unit checks | Management command | `management/commands/check_vacant_units.py` |
| Flag defaulters | Cron job | `properties/cron/flag_defaulters.py` |
| Vacate reminders | Cron job | `properties/cron/vacate_reminder.py` |
| Retry failed payouts | Management command | `management/commands/retry_failed_payouts.py` |
| Archive expired users | Management command | `management/commands/archive_expired_users_data.py` |
| Payout retry | Communication module | `properties/communication/retry_failed_payouts.py` |
| Rent record generation | Communication module | `properties/communication/auto_generate_rent_records.py` |

### 14.2 Background Processing Issues

1. **No Celery tasks** — Despite `django_celery_beat` in INSTALLED_APPS, no actual Celery tasks are defined. All background work is via management commands.
2. **No task retry policies** — If a management command fails, there's no automatic retry.
3. **No task monitoring** — No visibility into task execution, failures, or durations.
4. **No task scheduling in code** — Schedule is managed externally or manually.
5. **No task result backend** — No way to query task status or results.
6. **No distributed locking** — Multiple instances could run the same management command simultaneously.

---

## 15. Cache Flow

### 15.1 Current Caching

| Cache Key Pattern | TTL | Location | Purpose |
|-------------------|-----|----------|---------|
| `rentrecord_list_{user_id}` | 5 minutes | `RentRecordViewSet.get_queryset()` | Rent record list caching |
| `unit_list_{user_id}` | 5 minutes | `UnitService.get_unit_queryset()` | Unit list caching |
| `building_list_{user_id}` | 5 minutes | `BuildingService.get_owner_buildings()` | Building list caching |
| `owner_analytics_{user_id}` | 5 minutes | `get_owner_analytics()` | Analytics caching |

### 15.2 Cache Configuration

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-rentsecure-cache",
    }
}
```

### 15.3 Cache Issues

1. **LocMemCache is not production-ready** — LocMemCache is per-process. In a multi-worker deployment, each worker has its own cache, leading to stale data and cache stampedes.
2. **No cache invalidation strategy** — Cache keys are deleted manually in service methods, but there's no systematic invalidation.
3. **No cache warming** — No proactive cache population.
4. **No cache versioning** — Changing cache key format requires manual migration.
5. **No cache metrics** — No hit/miss ratio tracking.
6. **No cache fallback** — If cache is down, the application degrades to database queries (which is fine, but not intentional).

---

## 16. Deployment Architecture

### 16.1 Current Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AWS EC2 (Single Instance)                         │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Docker Compose                                  │  │
│  │                                                                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │   Django     │  │    Redis     │  │  Celery      │             │  │
│  │  │   (Gunicorn) │  │   (Cache)    │  │  Worker      │             │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │  │
│  │                                                                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │  PostgreSQL  │  │  Celery      │  │  Nginx      │             │  │
│  │  │              │  │  Beat        │  │  (Proxy)    │             │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Deployment: SSH deploy via GitHub Actions (appleboy/ssh-action)           │
│  Rollback: Manual SHA checkout via workflow_dispatch                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 16.2 Deployment Issues

1. **No Dockerfile in repo** — Docker Compose configuration lives on the remote host, not version-controlled.
2. **No infrastructure as code** — EC2 provisioning is manual.
3. **No blue-green or canary deployment** — Deploy is all-or-nothing.
4. **No health checks** — Deploy readiness validates `/api/health/` but no liveness/readiness probes.
5. **No auto-scaling** — Single EC2 instance.
6. **No database migration strategy** — Migrations run as part of deploy without rollback plan.
7. **No secrets management** — Secrets are in GitHub Secrets and `.env` on the server.

---

## 17. CI/CD Architecture

### 17.1 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CI/CD PIPELINE (27 Workflows)                       │
│                                                                             │
│  Stage 1: Lint & Code Quality                                               │
│  ├── lint-fast (pre-commit, black, ruff, pylint, mypy, vulture)            │
│  └── architecture (import-linter, dependency graphs)                       │
│                                                                             │
│  Stage 2: Testing                                                           │
│  ├── test-shard-1/2/3/4 (pytest + coverage, sharded)                       │
│  ├── contract-tests (DRF API contracts via Schemathesis)                    │
│  ├── django-check (manage.py check, makemigrations --check)                 │
│  ├── architecture (UML generation + validation)                             │
│  ├── security-fast (bandit, pip-audit, semgrep, trivy, gitleaks)            │
│  ├── mutation-smoke (mutmut on changed files)                               │
│  ├── migration-rollback-validation                                          │
│  └── hypothesis-fast (property-based tests)                                 │
│                                                                             │
│  Stage 3: Quality Gate                                                      │
│  └── quality (SonarCloud quality gate)                                      │
│                                                                             │
│  Stage 4: Deploy Readiness                                                  │
│  └── deploy-readiness (env validation, system checks)                       │
│                                                                             │
│  Stage 5: Deploy (main/master push only)                                    │
│  └── deploy (EC2 SSH + Sentry release tracking)                             │
│                                                                             │
│  Stage 6: Rollback (manual only)                                            │
│  └── rollback (SHA-based rollback with validation)                          │
│                                                                             │
│  Nightly: hypothesis-full, mutation-full, security-deep                     │
│  Weekly: exhaustive mutation, stress testing, SBOM, benchmarks             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 17.2 CI/CD Architecture Strengths

1. **Architecture Guard** — Machine-verifiable CI/CD pipeline contract.
2. **Sharded Tests** — 4-shard pytest for faster feedback.
3. **Multi-layered Security** — SAST, SCA, secret scanning, dependency review.
4. **Mutation Testing** — Ensures tests actually verify behavior.
5. **Property-Based Testing** — Hypothesis for invariant checking.
6. **Contract Testing** — API contract stability via Schemathesis.
7. **Rollback Workflow** — SHA-based rollback with health validation.
8. **Sentry Integration** — Release tracking and deploy events.

### 17.3 CI/CD Architecture Issues

1. **No CI for branch deployments** — Only main/master deploys.
2. **No preview environments** — PRs don't get deployed environments.
3. **No performance regression in main CI** — Locust and benchmarks are standalone workflows.
4. **No SBOM in main CI** — SBOM is a weekly workflow, not enforced on every PR.
5. **No dependency caching for nox** — Nox sessions install dependencies fresh each time.

---

## 18. Testing Architecture

### 18.1 Test Pyramid

```
                    ┌──────────────┐
                    │   Unit Tests │  ← Service layer, models, utils
                    │  (pytest)    │
                    ├──────────────┤
                    │ Integration  │  ← API endpoints, workflows
                    │   Tests      │
                    ├──────────────┤
                    │ Architecture │  ← Contract, query budget, invariants
                    │   Tests      │
                    ├──────────────┤
                    │   Security   │  ← Bandit, Semgrep, Trivy
                    │   Tests      │
                    ├──────────────┤
                    │  Property-   │  ← Hypothesis (invariants)
                    │   Based      │
                    ├──────────────┤
                    │  Mutation    │  ← mutmut (test quality)
                    │   Tests      │
                    ├──────────────┤
                    │  Contract    │  ← Schemathesis (API stability)
                    │   Tests      │
                    ├──────────────┤
                    │   Load       │  ← Locust (performance)
                    │   Tests      │
                    └──────────────┘
```

### 18.2 Test Infrastructure

| Component | Tool | Configuration |
|-----------|------|---------------|
| Test Runner | pytest | `pytest.ini`, `pyproject.toml` |
| Coverage | pytest-cov | ≥90% on 10 business-logic packages |
| Factories | factory_boy | 16 factories in `conftest.py` |
| Fixtures | pytest fixtures | Autouse + explicit fixtures |
| Hypothesis | hypothesis | 200 examples, 5s deadline |
| Mutation | mutmut | 8 source paths, 2-4 workers |
| Contracts | schemathesis | DRF endpoint contracts |
| Load | locust | 20 users, 2 spawn-rate, 2 min |
| Benchmarks | pytest-benchmark | Performance regression |

### 18.3 Test Coverage Gaps

1. **No service layer tests for stubs** — `RentService`, `RenterService`, `VacancyService`, `OccupancyService` are stubs with no tests.
2. **No repository tests** — Repositories have no dedicated unit tests.
3. **No notification service tests** — Notification services are module-level functions with minimal tests.
4. **No external integration tests** — Twilio, Razorpay, Cashfree are mocked but not integration-tested.
5. **No webhook tests** — Webhook handlers have no dedicated test coverage.
6. **No signal tests** — Signal handlers have limited test coverage.
7. **No management command tests** — Background tasks have no tests.
8. **Dashboard app untested** — `dashboard/` has no tests and is not registered.

---

## 19. Security Architecture

### 19.1 Defense in Depth

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SECURITY ARCHITECTURE                               │
│                                                                             │
│  Layer 1: Network                                                           │
│  ├── HTTPS only (SECURE_SSL_REDIRECT)                                       │
│  ├── HSTS (1 year, include subdomains, preload)                             │
│  └── No CORS configured (no frontend SPA)                                   │
│                                                                             │
│  Layer 2: Transport                                                         │
│  ├── Secure cookies (SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE)             │
│  ├── X-Content-Type-Options: nosniff                                       │
│  ├── X-XSS-Protection: 1; mode=block                                        │
│  └── X-Frame-Options: DENY                                                  │
│                                                                             │
│  Layer 3: Authentication                                                    │
│  ├── JWT (SimpleJWT) — access: 5min, refresh: 35 days                      │
│  ├── OTP-based login (Twilio)                                               │
│  └── Password validators (4 validators)                                     │
│                                                                             │
│  Layer 4: Authorization                                                     │
│  ├── IsAuthenticated on all protected endpoints                             │
│  ├── Inline ownership checks (no custom permissions)                        │
│  ├── FeatureEnforcer for plan limits                                        │
│  └── No RBAC beyond owner/renter/admin                                     │
│                                                                             │
│  Layer 5: Input Validation                                                  │
│  ├── DRF serializers (validation at API boundary)                           │
│  ├── Model clean() methods                                                  │
│  ├── Shared validators                                                     │
│  └── Webhook signature verification (HMAC-SHA256)                           │
│                                                                             │
│  Layer 6: Data Protection                                                    │
│  ├── SECRET_KEY validation (reject insecure keys in prod)                   │
│  ├── No PII in logs (no logging configuration found)                        │
│  └── Simple-history for audit trail                                         │
│                                                                             │
│  Layer 7: CI/CD Security                                                    │
│  ├── Harden Runner (step-security)                                          │
│  ├── Bandit (SAST)                                                          │
│  ├── pip-audit (SCA)                                                        │
│  ├── Semgrep (semantic analysis)                                            │
│  ├── Trivy (filesystem + secrets)                                           │
│  ├── Gitleaks (secret scanning)                                             │
│  ├── Dependabot                                                             │
│  └── CodeQL (nightly deep scan)                                             │
│                                                                             │
│  Layer 8: Governance                                                        │
│  ├── Architecture Guard (import-linter, CI contract)                        │
│  ├── Branch protection validation                                           │
│  ├── SonarCloud quality gate                                                │
│  └── Mutation testing (test quality)                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 19.2 Security Gaps

| Gap | Severity | Impact |
|------|----------|--------|
| **No DRF throttling** | High | API is vulnerable to brute-force and DoS |
| **No CORS** | Medium | No frontend SPA, but blocks mobile/web app origins |
| **No rate limiting** | High | OTP and login endpoints can be abused |
| **No MFA** | Medium | Single factor authentication for owners |
| **Long-lived refresh tokens** | Medium | 35-day token lifetime is excessive |
| **No token revocation** | Medium | Cannot invalidate compromised tokens |
| **No distributed locking** | High | Payment operations vulnerable to race conditions |
| **No Celery task retry policies** | Medium | Background tasks fail silently |
| **No circuit breakers for external APIs** | High | Cascading failures from external service outages |
| **No request/response logging** | Medium | Security incident investigation is difficult |
| **No audit logging for sensitive operations** | Medium | No trail for financial operations |
| **No secrets rotation** | Medium | API keys and secrets have no rotation policy |
| **No WAF/IPS** | Low | Single EC2 instance exposed to internet |
| **No database encryption at rest** | Medium | PostgreSQL data is unencrypted |
| **No file upload validation** | Medium | Uploaded files (ID proofs, agreements) not scanned |
| **No CSRF protection on some endpoints** | Low | Webhooks are exempt by necessity |

### 19.3 Compliance Status

| Control | Status | Evidence |
|---------|--------|----------|
| OWASP Top 10 | Partial | SAST (Bandit, Semgrep) covers some; missing throttling, crypto, logging |
| PCI DSS | Not Applicable | Razorpay handles card data; we only store payment IDs |
| GDPR | Partial | No data export/delete endpoints; no consent management |
| SOC 2 | Partial | Audit trail (simple-history); missing access controls, change management |
| HSTS | Compliant | 1 year, include subdomains, preload |
| HTTPS | Compliant | SECURE_SSL_REDIRECT in production |
| Webhook Security | Compliant | HMAC-SHA256 on all 4 webhooks |
| CI Security | Compliant | 5 SAST/SCA tools + CodeQL nightly |

---

*End of Architecture Baseline v1.0.0*
