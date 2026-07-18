# RentSecureBE — Modular Monolith Architecture Review & Refactoring

**Document:** Modular Monolith Architecture Reference
**Version:** 2.0.0
**Date:** 2026-07-18
**Author:** Principal Software Architect
**Status:** REFERENCE ARCHITECTURE — MODULAR MONOLITH
**Scope:** 10–20 year architecture guidance for RentSecure
**Constraint:** Analysis + Recommendations. No code modifications.

---

## 1. Executive Summary

RentSecureBE is a Django 4.2 + DRF application intended to evolve into a world-class **Modular Monolith**. The existing architecture document describes a microservice-first migration path that is **misaligned with current business priorities**: deployment simplicity, maintainability, and low operational cost (target budget ₹2,000–3,000/month).

**Key Findings:**
- The project has excellent documentation of bounded contexts, but the target architecture pivots prematurely toward microservices.
- Payment logic is scattered across `rentsecure_be/services/` instead of a dedicated `payments/` bounded context.
- Dashboard is a shell; analytics logic lives in `properties/`.
- `ai_assistant/` is empty while `smartbot/` contains the actual AI code.
- The codebase needs a **Shared Kernel** with properly scoped shared abstractions.
- The current migration roadmap prioritizes service extraction (Phase 3–4) over **Modular Monolith discipline** (Phase 1–2).

**Recommendation:** Refactor the architecture to a **true Modular Monolith** where every bounded context is designed for future service extraction but remains in a single deployable unit until business scale justifies otherwise. Microservices are an **optimization**, not an architectural milestone.

---

## 2. Current Architecture

### 2.1 Actual Codebase Structure

```
rentsecure_be/
├── core/                          # Identity + Subscription combined
│   ├── models.py                  # User, UserProfile, OTP, OwnerBankDetails, SubscriptionPlan, UserSubscription, AddOnPurchase, PlanFeatureLimit, UsageLimit, NotificationPreference
│   ├── views.py                   # Auth, subscription, webhook views (566 lines, mixed concerns)
│   ├── serializers.py
│   ├── services/                  # Business logic layer (partial)
│   │   ├── auth_service.py
│   │   ├── otp_service.py
│   │   ├── password_service.py
│   │   ├── subscription_service.py
│   │   ├── usage_limit_service.py
│   │   ├── bank_details_service.py
│   │   ├── owner_reporting_service.py
│   │   └── referral_service.py
│   ├── urls.py
│   ├── admin.py
│   ├── apps.py                    # Signals ARE wired (contradicts older docs)
│   └── signals/
│
├── properties/                    # Core domain — most complete
│   ├── models/                    # Split across multiple files
│   │   ├── __init__.py
│   │   ├── building_models.py     # Building
│   │   ├── unit_models.py         # Unit, UnitImage, UnitDocument, UnitVacancy
│   │   ├── renter_models.py       # Renter, ArchivedRenter, RentAgreementDraft, PoliceVerification, RentReminderLog
│   │   ├── rent_record_models.py  # RentRecord
│   │   ├── caretaker_models.py    # CareTaker
│   │   ├── extra_charge_models.py # ExtraCharge
│   │   └── property_tax_models.py # PropertyTaxRecord
│   ├── views/                     # Split by entity
│   │   ├── building_views.py
│   │   ├── unit_views.py
│   │   ├── renter_views.py
│   │   ├── rent_record_views.py   # Contains business logic (payment links, WhatsApp)
│   │   ├── caretaker_views.py
│   │   ├── extra_charge_views.py
│   │   ├── owner_dashboard.py     # Dashboard summary endpoint
│   │   ├── property_views.py
│   │   ├── subscription_views.py
│   │   └── usage_limit_views.py
│   ├── serializers/               # Split by entity
│   ├── services/                  # Business logic
│   │   ├── building_service.py
│   │   ├── unit_service.py
│   │   ├── renter_service.py
│   │   ├── rent_service.py        # STUB — all methods raise NotImplementedError
│   │   ├── receipt_service.py
│   │   ├── summary_service.py
│   │   ├── vacancy_service.py
│   │   ├── occupancy_service.py
│   │   ├── extra_charge_service.py
│   │   └── renter_onboarding_service.py
│   ├── repositories/              # Data access (exists but minimal)
│   ├── policies/                  # Authorization policies
│   ├── signals/                   # Django signals (wired in apps.py)
│   │   ├── __init__.py            # Main signal handlers
│   │   └── renter_signals.py      # Custom signals: renter_archived, renter_exited
│   ├── cron/                      # Cron-style tasks
│   │   ├── flag_defaulters.py
│   │   └── vacate_reminder.py
│   ├── feature_enforcer.py        # Subscription/enforcement logic
│   ├── constants.py
│   ├── urls.py
│   ├── apps.py                    # Signals ARE wired
│   └── migrations/
│
├── notification/                  # Notifications bounded context
│   ├── models.py                  # Notification, DeviceToken
│   ├── views.py                   # FCM registration, notification list
│   ├── serializers.py
│   ├── services/                  # Channel implementations
│   │   ├── rent_notify_service.py
│   │   ├── whatsapp_service.py
│   │   ├── voice_service.py
│   │   ├── voice_note_service.py
│   │   ├── sms_service.py
│   │   ├── communication.py
│   │   ├── extra_charge_reminders.py
│   │   ├── late_fees_notify_service.py
│   │   ├── schedule_reminders.py
│   │   └── services.py
│   ├── urls.py
│   └── management/commands/
│
├── finance/                       # Finance & Tax bounded context
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── migrations/
│
├── documents/                     # Documents bounded context
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── migrations/
│
├── smartbot/                      # AI bounded context
│   ├── models.py                  # SmartBotChat, SmartBotMessage, AIAlert
│   ├── views.py
│   ├── services/
│   │   ├── chatbot_service.py
│   │   ├── gpt_services.py
│   │   ├── agreement_service.py
│   │   ├── leegality_service.py
│   │   └── services.py
│   └── cron/
│
├── ai_assistant/                  # AI assistant (EMPTY)
│   ├── models.py                  # Empty (1 comment line)
│   ├── views.py
│   ├── services/
│   └── urls.py
│
├── referral_and_earn/             # Referral bounded context
│   ├── models.py
│   ├── services/
│   ├── migrations/
│   └── NO urls.py                 # NOT exposed via API
│
├── dashboard/                     # Dashboard bounded context (SHELL)
│   ├── views.py                   # Only 2 endpoints
│   ├── urls.py
│   └── tests.py
│
├── shared/                        # Shared kernel
│   ├── interfaces.py              # Repository, Service, EventBus protocols
│   ├── exceptions.py
│   ├── types.py
│   ├── constants.py
│   ├── validators.py
│   ├── utils.py
│   ├── domain_events.py
│   └── enums.py
│
└── rentsecure_be/                 # Infrastructure / project config
    ├── settings/
    ├── services/                  # Cross-cutting integrations
    │   ├── razorpay_service.py    # Razorpay payment links
    │   ├── cashfree_service.py    # Cashfree payouts
    │   ├── leegality_service.py   # E-signature
    │   └── i18n_service.py        # Translation
    ├── utils/
    │   ├── export_utils.py        # Excel report generation
    │   └── cashfree_payout.py     # Low-level Cashfree API
    └── type_compat.py
```

### 2.2 Current Tech Stack (Actual)

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Framework | Django | 4.2.30 | LTS |
| API | DRF | 3.16.0 | |
| Auth | SimpleJWT | 5.5.1 | JWT-only, no session auth |
| Database | PostgreSQL / SQLite | — | Environment-dependent |
| Cache | LocMemCache | — | Year 1 strategy |
| Background | Management commands + crontab | — | Celery installed but not configured |
| Storage | Local / S3 | — | Environment-dependent |
| PDF | WeasyPrint | 69.0 | |
| Notifications | SMTP, FCM | — | WhatsApp disabled by default |
| AI | OpenAI | 0.28.1 | Disabled by default |
| Payments | Manual UPI (Year 1) | — | Razorpay/Cashfree code exists but disabled |
| Frontend | Angular + Ionic | — | Separate repo |

### 2.3 Current API Structure

| Base Path | App | Endpoints |
|-----------|-----|-----------|
| `/api/auth/` | core | send-otp, owner/verify-otp, renter/verify-otp |
| `/api/token/` | core | refresh |
| `/api/subscription-plans/` | core | CRUD |
| `/api/user-subscriptions/` | core | CRUD |
| `/api/addon-purchases/` | core | CRUD |
| `/api/usage-limits/` | core | CRUD |
| `/api/buildings/` | properties | CRUD |
| `/api/units/` | properties | CRUD |
| `/api/caretakers/` | properties | CRUD |
| `/api/renters/` | properties | CRUD |
| `/api/rent-records/` | properties | CRUD |
| `/api/extra-charges/` | properties | CRUD |
| `/api/owner/` | properties | dashboard-summary, rent-records, retry_payout_api |
| `/api/renter/` | properties | rent-due, rent-history |
| `/api/notifications/` | notification | register-fcm, get, mark, save-token |
| `/documents/` | documents | rent_receipt, rent_agreement, send-for-signature |
| `/dashboard/` | dashboard | agreements, retry-signature |
| `/webhook/cashfree/payout/` | core | Cashfree payout webhook |
| `/api/rent/payment-callback/` | core | Razorpay webhook |
| `/leegality/webhook/` | properties | Leegality webhook |

**Note:** No API versioning. Duplicate mounts at `/api/` and `/properties/` for some endpoints.

---

## 3. Domain Map

### 3.1 Identified Business Domains

| # | Domain | Description | Current Location | Status |
|---|--------|-------------|-----------------|--------|
| 1 | **Identity & Access** | OTP authentication, JWT tokens, user profiles, roles/groups | `core/` (combined with subscription) | Active |
| 2 | **Subscription** | Plans, add-ons, usage limits, feature enforcement, grace periods | `core/` (combined with identity) | Active |
| 3 | **Property Management** | Buildings, units, unit images, unit documents, property tax | `properties/` | Active |
| 4 | **Caretaker Management** | Caretaker profiles, assignments, permissions | `properties/` | Active |
| 5 | **Renter Management** | Renter profiles, lifecycle (active/notice/revoked), onboarding, KYC, police verification | `properties/` | Active |
| 6 | **Rent & Payments** | Rent records, payment links, UPI payments, payouts, late fees, defaulter handling, reminders | `properties/` + `rentsecure_be/services/` | Fragmented |
| 7 | **Finance & Tax** | CA profiles, tax submissions, tax calculations, tax documents, tax reminders | `finance/` | Active |
| 8 | **Notifications** | Email, FCM push, in-app, WhatsApp, SMS, voice notes, templates, preferences | `notification/` | Active |
| 9 | **Documents** | PDF generation (WeasyPrint), rent receipts, rent agreements, e-signature (Leegality), document storage | `documents/` | Active |
| 10 | **AI / SmartBot** | Chatbot, GPT integration, intent extraction, action dispatcher, chat history, agreement AI | `smartbot/` + `ai_assistant/` | Fragmented |
| 11 | **Referral & Growth** | Referral codes, validation, bonus tracking, rewards | `referral_and_earn/` | Active |
| 12 | **Dashboard / Analytics** | Owner dashboard summary, rent analytics, occupancy analytics, monthly summaries | `dashboard/` (shell) + `properties/views/owner_dashboard.py` | Fragmented |

### 3.2 Domain Relationships

```
Identity ──────┐
               ├──→ Subscription ──→ Property ──→ Renter ──→ Rent ──→ Payments
               │         │              │           │           │          │
               │         │              │           │           │          │
               └─────────┘              └───────────┘           └──────────┘
                     │                       │                       │
                     ▼                       ▼                       ▼
               Notifications ◄── Documents ◄── Finance ◄── Referral
                     │                       │
                     ▼                       ▼
                  AI/SmartBot ────────── Dashboard
```

**Key Insight:** The `Rent & Payments` domain is the most fragmented, with logic spread across `properties/` (rent records), `rentsecure_be/services/` (payment gateways), `core/views.py` (webhooks), and `notification/` (payment notifications).

---

## 4. Bounded Context Diagram

### 4.1 Proposed Bounded Contexts (Target Architecture — Modular Monolith)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     RentSecure Modular Monolith — Bounded Contexts            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│  │   Identity   │    │ Subscription │    │   Property   │                 │
│  │  Context     │───▶│   Context    │───▶│   Context    │                 │
│  │              │    │              │    │              │                 │
│  │ • Users      │    │ • Plans      │    │ • Buildings  │                 │
│  │ • OTP        │    │ • Add-ons    │    │ • Units      │                 │
│  │ • JWT        │    │ • Limits     │    │ • Images     │                 │
│  │ • Groups     │    │ • Features   │    │ • Documents  │                 │
│  │ • Passwords  │    │ • Grace      │    │ • Tax        │                 │
│  └──────────────┘    └──────────────┘    └──────────────┘                 │
│         ▲                    │                    │                        │
│         │                    │                    │                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│  │   Referral   │    │   Renter     │    │     Rent     │                 │
│  │   Context    │    │   Context    │    │   Context    │                 │
│  │              │    │              │    │              │                 │
│  │ • Codes      │    │ • Profiles   │    │ • Records    │                 │
│  │ • Bonuses    │    │ • Lifecycle  │    │ • Payments   │                 │
│  │ • Rewards    │    │ • Onboarding │    │ • Late Fees  │                 │
│  │              │    │ • KYC        │    │ • Reminders  │                 │
│  └──────────────┘    │ • Police Ver │    │ • Invoices   │                 │
│                       └──────────────┘    └──────────────┘                 │
│                              │                    │                        │
│                              │                    │                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│  │   Payments   │    │   Finance    │    │   Document   │                 │
│  │   Context    │◄───│   Context    │    │   Context    │                 │
│  │              │    │              │    │              │                 │
│  │ • Gateways   │    │ • CA Profiles│    │ • PDFs       │                 │
│  │ • Webhooks   │    │ • Tax Submit │    │ • E-sign     │                 │
│  │ • Payouts    │    │ • Reports    │    │ • Receipts   │                 │
│  │ • UTR Verify │    │ • Compliance │    │ • Storage    │                 │
│  └──────────────┘    └──────────────┘    └──────────────┘                 │
│         │                    │                    │                        │
│         │                    │                    │                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│  │ Notification│    │     AI       │    │  Dashboard   │                 │
│  │   Context   │    │   Context    │    │   Context    │                 │
│  │              │    │              │    │              │                 │
│  │ • Email      │    │ • Chatbot    │    │ • Analytics  │                 │
│  │ • Push       │    │ • GPT        │    │ • Reports    │                 │
│  │ • WhatsApp   │    │ • Intents    │    │ • Summaries  │                 │
│  │ • SMS        │    │ • Actions    │    │ • Insights   │                 │
│  │ • Voice      │    │ • History    │    │              │                 │
│  └──────────────┘    └──────────────┘    └──────────────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Design Principle:** Each bounded context above is a **first-class module** inside a single deployable Django project. Internal communication uses **Domain Events** and **Application Services**. External provider integrations (Razorpay, Cashfree, FCM, OpenAI, Leegality) are isolated behind ports in the Infrastructure layer.

### 4.2 Bounded Context Details

#### 4.2.1 Identity Context
**Purpose:** Manage user identities, authentication, and authorization
**Responsibilities:**
- OTP-based phone authentication
- JWT token issuance and refresh
- Password management
- User profile management
- Role/group assignment

**Entities:**
- `User` (aggregate root)
- `UserProfile`
- `OTP`
- `NotificationPreference`

**Value Objects:**
- `PhoneNumber`
- `JWTTokenPair`
- `OTPCode`

**Domain Services:**
- `AuthService` — login, token issuance
- `OTPService` — OTP generation, delivery, rate limiting
- `PasswordService` — password reset/change

**Application Services:**
- `UserRegistrationService`
- `TokenRefreshService`

**External Integrations:**
- Twilio (SMS/WhatsApp)
- Firebase Admin (FCM tokens)

**Future Growth:**
- Social authentication (Google, Apple)
- Biometric authentication
- SSO/SAML for enterprise

**Dependencies:**
- `shared_kernel/` — utilities, exceptions, base classes
- Currently lives in `core/` — **Phase 1**: keep as module, extract as subpackage if needed

**Expected APIs:**
- `POST /api/v1/auth/send-otp`
- `POST /api/v1/auth/owner/verify-otp`
- `POST /api/v1/auth/renter/verify-otp`
- `POST /api/v1/auth/change-password`
- `POST /api/v1/auth/reset-password`
- `POST /api/v1/auth/token/refresh`
- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`

---

#### 4.2.2 Subscription Context
**Purpose:** Manage subscription plans, feature limits, and usage enforcement
**Responsibilities:**
- Subscription plan CRUD
- User subscription management
- Add-on purchase processing
- Feature limit enforcement
- Grace period management

**Entities:**
- `SubscriptionPlan` (aggregate root)
- `UserSubscription`
- `AddOnPurchase`
- `PlanFeatureLimit`
- `UsageLimit`

**Value Objects:**
- `PlanName` (free/pro/elite)
- `FeatureKey`
- `UsageCount`
- `GracePeriodDays`

**Domain Services:**
- `SubscriptionService` — plan resolution, active subscription queries
- `UsageLimitService` — feature flag evaluation, limit checks
- `FeatureEnforcer` — limit enforcement with add-on overrides

**Application Services:**
- `PlanPurchaseService`
- `AddOnPurchaseService`
- `SubscriptionUpgradeService`

**External Integrations:**
- None (internal only)

**Future Growth:**
- Usage-based billing
- Metered features
- Team/org subscriptions

**Dependencies:**
- `shared_kernel/` — utilities, exceptions, base classes
- Currently lives in `core/` — **Phase 1**: keep as module, extract as subpackage if needed

**Expected APIs:**
- `GET /api/v1/subscription-plans/`
- `GET/POST /api/v1/user-subscriptions/`
- `GET/POST /api/v1/addon-purchases/`
- `GET /api/v1/usage-limits/`

---

#### 4.2.3 Property Context
**Purpose:** Manage physical property assets (buildings, units, images, documents, tax)
**Responsibilities:**
- Building CRUD
- Unit CRUD
- Unit image/document management
- Property tax record management
- Caretaker assignment

**Entities:**
- `Building` (aggregate root)
- `Unit` (aggregate root)
- `UnitImage`
- `UnitDocument`
- `UnitVacancy`
- `CareTaker`
- `PropertyTaxRecord`

**Value Objects:**
- `Address` (address_line, city, state, country, postal_code)
- `UnitType` (flat, house, commercial, etc.)
- `VacancyStatus` (vacant, occupied)

**Domain Services:**
- `BuildingService` — building CRUD, usage counting
- `UnitService` — unit CRUD, status updates, occupancy tracking
- `VacancyService` — vacancy tracking and reporting
- `OccupancyService` — occupancy analytics

**Application Services:**
- `PropertyCreationService`
- `UnitTransferService`

**External Integrations:**
- AWS S3 (image/document storage)

**Future Growth:**
- Multi-property portfolios
- Property verification
- Maintenance scheduling
- Utility billing integration

**Dependencies:**
- `shared_kernel/` — utilities, exceptions
- `identity/` — User model reference (via `settings.AUTH_USER_MODEL`)

**Expected APIs:**
- `GET/POST /api/v1/buildings/`
- `GET/POST /api/v1/units/`
- `GET/POST /api/v1/caretakers/`
- `GET/POST /api/v1/unit-images/`
- `GET/POST /api/v1/unit-documents/`

---

#### 4.2.4 Renter Context
**Purpose:** Manage renter profiles, lifecycle, onboarding, KYC, and police verification
**Responsibilities:**
- Renter profile CRUD
- Lifecycle management (active → notice_period → revoked/deactivated)
- Onboarding workflow (token generation, link sending)
- KYC verification
- Police verification
- Agreement management (drafts, revocation)

**Entities:**
- `Renter` (aggregate root)
- `ArchivedRenter`
- `RentAgreementDraft`
- `PoliceVerification`
- `RentReminderLog`
- `AgreementRevocationLog`

**Value Objects:**
- `RenterStatus` (active, notice_period, revoked, deactivated)
- `RenterPhone`
- `OnboardingToken`

**Domain Services:**
- `RenterService` — renter CRUD, lifecycle transitions
- `RenterOnboardingService` — onboarding workflow
- `PoliceVerificationService` — police check workflow

**Application Services:**
- `RenterRegistrationService`
- `RenterExitService`

**External Integrations:**
- None (future: police verification APIs)

**Future Growth:**
- Digital KYC (Aadhaar, PAN)
- Background checks
- Renter ratings/reviews
- Insurance integration

**Dependencies:**
- `shared_kernel/` — utilities, exceptions
- `properties/` — Unit, Building
- `identity/` — User

**Expected APIs:**
- `GET/POST /api/v1/renters/`
- `POST /api/v1/renters/{id}/onboard`
- `POST /api/v1/renters/{id}/verify-kyc`
- `POST /api/v1/renters/{id}/police-verification`
- `GET /api/v1/rent-agreement-drafts/`
- `POST /api/v1/rent-agreement-drafts/{id}/send-for-signature`

---

#### 4.2.5 Rent Context
**Purpose:** Manage rent records, payment tracking, late fees, reminders, and invoices
**Responsibilities:**
- Rent record CRUD
- Payment status management
- Late fee calculation and application
- Rent reminder scheduling
- Invoice generation
- Defaulter tracking

**Entities:**
- `RentRecord` (aggregate root)
- `ExtraCharge`
- `RentReminderLog`

**Value Objects:**
- `PaymentMethod` (cash, bank_transfer, UPI, cheque, card, online, other)
- `RentStatus` (pending, paid, overdue, cancelled)
- `Money` (amount, currency)
- `RentDueDate`

**Domain Services:**
- `RentService` — rent calculation, record creation
- `LateFeeService` — late fee calculation
- `ReminderService` — reminder scheduling and dispatch
- `InvoiceService` — invoice generation

**Application Services:**
- `RentCollectionService`
- `LateFeeApplicationService`
- `DefaulterManagementService`

**External Integrations:**
- `notification/` — reminder dispatch (via domain event or application service)
- `documents/` — invoice PDF generation (via domain event or application service)

**Future Growth:**
- Dynamic rent pricing
- Split payments
- Installment plans
- Rent negotiation

**Dependencies:**
- `shared_kernel/` — utilities, exceptions
- `properties/` — Renter, Unit
- `notification/` — reminders
- `documents/` — invoices

**Expected APIs:**
- `GET/POST /api/v1/rent-records/`
- `GET /api/v1/rent-records/{id}/invoice`
- `POST /api/v1/rent-records/{id}/mark-paid`
- `POST /api/v1/rent-records/{id}/apply-late-fee`
- `GET /api/v1/renter/rent-due`
- `GET /api/v1/renter/rent-history`
- `GET /api/v1/owner/rents`
- `GET /api/v1/owner/dashboard-summary`

---

#### 4.2.6 Payments Context
**Purpose:** Manage payment gateways, payout processing, webhook verification, and UTR reconciliation
**Responsibilities:**
- Payment gateway abstraction (Manual UPI, Razorpay, Cashfree)
- Payment link creation
- Webhook verification and processing
- Payout processing to owners
- UTR verification
- Retry logic for failed payouts

**Entities:**
- `PaymentTransaction` (aggregate root)
- `Payout`
- `UTRVerification`

**Value Objects:**
- `PaymentMethod` (manual_upi, razorpay, cashfree)
- `PaymentStatus` (pending, completed, failed, cancelled)
- `UTRNumber`
- `Money`

**Domain Services:**
- `PaymentGateway` (interface/port)
- `ManualPaymentAdapter` — UPI QR, UTR verification
- `RazorpayAdapter` — payment links, webhooks (Stage 2, disabled by feature flag)
- `CashfreeAdapter` — payouts, beneficiary management (Stage 2, disabled by feature flag)
- `PayoutService` — payout orchestration

**Application Services:**
- `PaymentInitiationService`
- `PaymentVerificationService`
- `PayoutProcessingService`

**External Integrations:**
- Razorpay API (disabled by default)
- Cashfree API (disabled by default)
- Manual UPI (bank transfer)

**Future Growth:**
- Auto-payment via UPI mandate
- Payment splits
- Escrow accounts
- Multi-currency support

**Dependencies:**
- `shared_kernel/` — utilities, exceptions
- `rent/` — RentRecord
- `properties/` — Unit, Owner bank details
- `notification/` — payment notifications

**Expected APIs:**
- `POST /api/v1/payments/initiate`
- `POST /api/v1/payments/verify`
- `POST /api/v1/payouts/process`
- `POST /api/v1/payouts/retry`
- `POST /api/v1/utr/verify`
- `POST /api/v1/webhooks/razorpay`
- `POST /api/v1/webhooks/cashfree`

**Location:** Create as `payments/` Django app inside the monolith. **Priority: Phase 1.**

---

#### 4.2.7 Finance Context
**Purpose:** Manage CA profiles, tax submissions, tax calculations, and compliance
**Responsibilities:**
- CA profile management
- Tax submission workflows
- Tax calculation
- Tax document generation
- Tax reminder dispatch
- Compliance reporting

**Entities:**
- `CAProfile` (aggregate root)
- `TaxSubmission`
- `PropertyTaxRecord`

**Value Objects:**
- `TaxPeriod`
- `TaxAmount`
- `TaxStatus` (draft, submitted, approved, rejected)

**Domain Services:**
- `TaxCalculationService`
- `TaxSubmissionService`
- `TaxReportService`

**Application Services:**
- `TaxFilingService`
- `TaxReminderService`

**External Integrations:**
- Government tax APIs (future)
- Document generation (`documents/`)

**Future Growth:**
- GST filing
- TDS management
- Tax audit trail
- Multi-state tax compliance

**Dependencies:**
- `shared_kernel/` — utilities, exceptions
- `properties/` — PropertyTaxRecord
- `documents/` — PDF generation
- `notification/` — reminders

**Expected APIs:**
- `GET/POST /api/v1/finance/ca-profiles/`
- `GET/POST /api/v1/finance/tax-submissions/`
- `GET /api/v1/finance/tax-summary/`
- `POST /api/v1/finance/tax-submissions/{id}/submit`
- `GET /api/v1/finance/tax-documents/`

---

#### 4.2.8 Document Context
**Purpose:** Generate, store, and manage documents (PDFs, e-signatures, agreements)
**Responsibilities:**
- PDF generation (rent receipts, invoices, agreements)
- E-signature orchestration
- Document storage
- Document retrieval
- Template management

**Entities:**
- `Document` (aggregate root)
- `DocumentTemplate`
- `SignatureRequest`

**Value Objects:**
- `DocumentType` (receipt, agreement, invoice, dossier)
- `DocumentStatus` (draft, generated, signed, expired)
- `FilePath`

**Domain Services:**
- `PDFGenerationService` — WeasyPrint-based PDF generation
- `ESignatureService` — Leegality integration
- `DocumentStorageService` — S3/local storage

**Application Services:**
- `RentReceiptGenerationService`
- `RentAgreementGenerationService`
- `DocumentDeliveryService`

**External Integrations:**
- WeasyPrint (PDF)
- Leegality (e-signature)
- AWS S3 (storage)

**Future Growth:**
- Template engine
- Document versioning
- Digital stamping
- Multi-language documents

**Dependencies:**
- `shared_kernel/` — utilities, exceptions
- `rent/` — RentRecord
- `finance/` — Tax documents
- `renter/` — Agreement data

**Expected APIs:**
- `GET /api/v1/documents/rent-receipt/{rent_id}`
- `GET /api/v1/documents/rent-agreement/{renter_id}`
- `POST /api/v1/documents/send-for-signature`
- `GET /api/v1/documents/unit-dossier/{unit_id}`
- `POST /api/v1/documents/webhooks/leegality`

---

#### 4.2.9 Notification Context
**Purpose:** Dispatch notifications across all channels (email, push, WhatsApp, SMS, voice)
**Responsibilities:**
- Channel abstraction (email, FCM, WhatsApp, SMS, voice)
- Template management
- Preference management
- Notification scheduling
- Delivery tracking
- Retry logic

**Entities:**
- `Notification` (aggregate root)
- `DeviceToken`
- `NotificationTemplate`
- `NotificationPreference`

**Value Objects:**
- `NotificationChannel` (email, push, whatsapp, sms, voice)
- `NotificationType` (rent_reminder, payment_confirmation, tax_alert, etc.)
- `DeliveryStatus`

**Domain Services:**
- `NotificationChannel` (interface/port)
- `EmailAdapter` — SMTP
- `FCMAdapter` — Firebase Cloud Messaging
- `WhatsAppAdapter` — WhatsApp Business API (**Stage 2, disabled**)
- `SMSAdapter` — Twilio/MSG91 (**Stage 2, disabled**)
- `VoiceAdapter` — gTTS/OpenAI (**Stage 3**)

**Application Services:**
- `NotificationDispatchService`
- `NotificationPreferenceService`
- `NotificationSchedulingService`

**External Integrations:**
- SMTP (email)
- Firebase Cloud Messaging (push)
- Twilio (WhatsApp, SMS) — disabled by default
- edge-tts / OpenAI (voice)

**Future Growth:**
- In-app notification center
- Notification analytics
- A/B testing for templates
- Multi-language templates

**Dependencies:**
- `shared_kernel/` — utilities, exceptions
- All other contexts (receive notifications)

**Expected APIs:**
- `POST /api/v1/notifications/register-fcm`
- `GET /api/v1/notifications/`
- `POST /api/v1/notifications/{id}/mark-read`
- `POST /api/v1/notifications/save-token`
- `GET/POST /api/v1/notification-preferences/`

---

#### 4.2.10 AI/SmartBot Context
**Purpose:** Provide AI-powered chatbot, intent extraction, and action automation
**Responsibilities:**
- Chatbot conversation management
- Intent extraction from user messages
- Action dispatching (create rent record, send notification, etc.)
- Chat history management
- GPT-powered responses
- Agreement AI assistance

**Entities:**
- `SmartBotChat` (aggregate root)
- `SmartBotMessage`
- `AIAlert`

**Value Objects:**
- `Intent`
- `Action`
- `ConfidenceScore`

**Domain Services:**
- `ChatbotService` — conversation flow
- `GPTService` — OpenAI integration
- `AgreementAIService` — agreement analysis

**Application Services:**
- `ChatProcessingService`
- `IntentExtractionService`
- `ActionDispatchService`

**External Integrations:**
- OpenAI API
- Leegality (agreement analysis)

**Future Growth:**
- Voice-based chatbot
- Multi-language support
- Predictive analytics
- Automated rent negotiation

**Dependencies:**
- `shared_kernel/` — utilities, exceptions
- `rent/` — rent actions
- `notification/` — notifications
- `documents/` — agreements

**Expected APIs:**
- `POST /api/v1/assistant/chat`
- `GET /api/v1/assistant/chats`
- `GET /api/v1/assistant/chats/{id}/messages`
- `POST /api/v1/assistant/actions/dispatch`

**Note:** Merge `ai_assistant/` into `smartbot/`. There must be exactly one AI bounded context. **Phase 1 action.**

---

#### 4.2.11 Referral Context
**Purpose:** Manage referral programs, code validation, and bonus tracking
**Responsibilities:**
- Referral code generation
- Code validation during registration
- Bonus awarding
- Reward tracking

**Entities:**
- `ReferralCode` (aggregate root)
- `ReferralBonus`
- `Reward`

**Value Objects:**
- `ReferralCode`
- `BonusPoints`
- `RewardType`

**Domain Services:**
- `ReferralService` — code validation, bonus awarding

**Application Services:**
- `ReferralProcessingService`
- `RewardRedemptionService`

**External Integrations:**
- None

**Future Growth:**
- Tiered rewards
- Referral analytics
- Social sharing
- Coupon system

**Dependencies:**
- `shared_kernel/` — utilities, exceptions
- `identity/` — User

**Expected APIs:**
- `POST /api/v1/referrals/process`
- `GET /api/v1/referrals/my-referrals`
- `GET /api/v1/referrals/rewards`

---

#### 4.2.12 Dashboard/Analytics Context
**Purpose:** Provide analytics, reporting, and dashboard data for owners
**Responsibilities:**
- Owner dashboard summary
- Rent analytics (trends, collections)
- Occupancy analytics
- Monthly summaries
- Report generation

**Entities:**
- `DashboardSummary` (read model)
- `RentAnalytics`
- `OccupancyAnalytics`

**Value Objects:**
- `TimeRange`
- `AnalyticsMetric`
- `ReportFormat`

**Domain Services:**
- `DashboardSummaryService`
- `RentAnalyticsService`
- `OccupancyAnalyticsService`

**Application Services:**
- `DashboardQueryService`
- `ReportGenerationService`

**External Integrations:**
- Excel export (`rentsecure_be/utils/export_utils.py`)

**Future Growth:**
- Real-time dashboards
- Custom reports
- Data export (CSV, PDF)
- Predictive analytics

**Dependencies:**
- `shared_kernel/` — utilities, exceptions
- `rent/` — RentRecord
- `properties/` — Unit, Building
- `finance/` — tax data

**Expected APIs:**
- `GET /api/v1/dashboard/owner/summary`
- `GET /api/v1/dashboard/owner/rent-analytics`
- `GET /api/v1/dashboard/owner/occupancy-analytics`
- `GET /api/v1/dashboard/owner/monthly-summary`

**Note:** Currently a shell. Must be promoted to a proper bounded context. **Phase 1 action.** CQRS-style read models only if analytics complexity justifies it (likely not until Phase 3).

---

## 5. Shared Kernel

### 5.1 Structure

Replace the generic `shared/` recommendation with a proper Shared Kernel:

```
shared_kernel/
├── base/
│   ├── __init__.py
│   ├── entity.py                 # BaseEntity with id, created_at, updated_at
│   ├── aggregate_root.py         # AggregateRoot with event dispatching
│   └── repository.py             # BaseRepository interface
├── domain/
│   ├── __init__.py
│   └── event_handler.py          # Domain event handler interface
├── events/
│   ├── __init__.py
│   ├── domain_event.py           # DomainEvent base class
│   ├── application_event.py      # ApplicationEvent base class
│   └── event_bus.py              # In-process event bus (synchronous)
├── interfaces/
│   ├── __init__.py
│   ├── repository.py             # Repository port (protocol)
│   ├── service.py                # Service port (protocol)
│   └── unit_of_work.py           # Unit of Work interface
├── value_objects/
│   ├── __init__.py
│   ├── money.py                  # Money (amount, currency)
│   ├── phone_number.py           # PhoneNumber validation
│   ├── datetime_helpers.py       # Timezone-aware datetime utilities
│   ├── pagination.py             # PaginationResult, PaginationParams
│   └── ids/                      # Typed IDs
│       ├── __init__.py
│       ├── user_id.py
│       ├── rent_record_id.py
│       └── ...
├── exceptions/
│   ├── __init__.py
│   ├── domain_exception.py       # Base domain exception
│   └── ...
├── result/
│   ├── __init__.py
│   ├── result.py                 # Result[T] for explicit error handling
│   └── ...
├── ids/
│   └── ...                       # Typed ID wrappers (if not in value_objects)
└── money/
    └── ...                       # If not in value_objects
```

### 5.2 Rules

**Place ONLY genuinely shared abstractions in the Shared Kernel.**

- ✅ Base entity/aggregate classes
- ✅ Repository/Service interfaces (ports)
- ✅ Value objects used by 2+ contexts (Money, PhoneNumber)
- ✅ Domain Event and Application Event base classes
- ✅ Base exceptions
- ✅ Result type for explicit error handling
- ✅ Pagination utilities

**Do NOT place business logic in the Shared Kernel.**

- ❌ Any domain service with business rules
- ❌ Context-specific entities
- ❌ Context-specific value objects
- ❌ Concrete implementations of ports (adapters belong in context `infrastructure/`)

### 5.3 Usage

All bounded contexts may import from `shared_kernel`. No context may import from another context's `domain/` or `infrastructure/` layer directly.

---

## 6. Dependency Rules

### 6.1 Clean Architecture Layer Order

```
Presentation (Views, Serializers, URLs)
    ↓
Application (Services, DTOs, Queries)
    ↓
Domain (Entities, Value Objects, Domain Services, Repository Interfaces)
    ↓
Infrastructure (ORM Models, External APIs, Concrete Repositories)
```

**Dependencies always point inward.**

- Presentation may import Application.
- Application may import Domain.
- Domain may import only `shared_kernel/`.
- Infrastructure may import Domain and `shared_kernel/`.
- Presentation and Application must never import Infrastructure directly.

### 6.2 Allowed Cross-Context Dependencies

| Source Context | Target Context | Mechanism | Rationale |
|---------------|----------------|-----------|-----------|
| Any | `shared_kernel/` | Direct import | Shared abstractions only |
| Context A | Context B | Published Interface (Port/Adapter) | Context B exposes an interface; Context A depends on the port in `shared_kernel/`, Context B's Infrastructure implements it |
| Context A | Context B | Domain Event | Context A publishes; Context B subscribes |
| Context A | Context B | Application Event | Cross-context workflow orchestration |
| Context A | Context B | Synchronous Application Service | Acceptable in Modular Monolith for transactional workflows |

**Forbidden:**
- ❌ Cross-context model imports (e.g., `from properties.models import RentRecord`)
- ❌ Cross-context service imports (e.g., `from notification.services import send_whatsapp_message`)
- ❌ Cross-context domain layer imports

### 6.3 Implementation Strategy

Use Django's `settings.AUTH_USER_MODEL` string reference instead of direct `core.models.User` imports.

For cross-context communication:
1. **Same transaction:** Synchronous Application Service call.
2. **Eventually consistent:** Domain Event via in-process event bus.
3. **External provider:** Adapter pattern with interface in `shared_kernel/`.

---

## 7. Event Communication

### 7.1 Preferred Patterns

| Pattern | Implementation | Use Case |
|---------|---------------|----------|
| **Synchronous Application Service** | Direct method call | Transactional workflows within monolith |
| **Domain Event** | In-process event bus | Decoupled reactions within same transaction |
| **Application Event** | In-process event bus | Cross-context workflows, async optional |
| **Published Interface** | Port/Adapter | External provider abstraction |
| **Django Signals** | Existing `@receiver` | **Temporary only** — migrate to Domain Events |

### 7.2 Event Bus (Year 1)

**Recommendation:** Use a lightweight in-process event bus for Domain Events and Application Events.

```python
# shared_kernel/events/event_bus.py
class EventBus:
    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers[type(event)]:
            handler.handle(event)
```

**Do NOT introduce Kafka as an initial solution.** Kafka is justified only when:
- Multiple deployable services exist (not applicable to Modular Monolith)
- Event replay/audit is a primary requirement
- Throughput exceeds a single process's capacity

**Redis Streams** are recommended only when asynchronous background processing becomes necessary (Phase 3).

### 7.3 Migration from Django Signals

Django Signals are acceptable as a **temporary bridge** but should be replaced by Domain Events because:
- Signals are hard to trace
- Signals are global and implicit
- Signals make testing difficult

**Migration approach:**
1. Identify all signal senders/receivers
2. Convert to explicit Domain Events
3. Wire events via the event bus in Application Services

---

## 8. Payments Strategy

### 8.1 Bounded Context

Keep Payments as a dedicated bounded context. **Phase 1 priority.**

**Location:** `payments/` Django app within the monolith.

**Structure:**
```
payments/
├── domain/
│   ├── entities/
│   │   ├── payment_transaction.py
│   │   ├── payout.py
│   │   └── utr_verification.py
│   ├── value_objects/
│   │   ├── payment_method.py
│   │   ├── payment_status.py
│   │   └── utr_number.py
│   ├── services/
│   │   ├── payment_gateway.py         # Interface
│   │   ├── manual_payment_adapter.py
│   │   ├── razorpay_adapter.py        # Stage 2
│   │   ├── cashfree_adapter.py        # Stage 2
│   │   └── payout_service.py
│   └── events/
│       ├── payment_initiated.py
│       ├── payment_verified.py
│       └── payout_processed.py
├── application/
│   ├── services/
│   │   ├── payment_initiation_service.py
│   │   ├── payment_verification_service.py
│   │   └── payout_processing_service.py
│   └── dto/
│       └── ...
├── infrastructure/
│   ├── models/
│   │   ├── payment_transaction.py
│   │   ├── payout.py
│   │   └── utr_verification.py
│   ├── repositories/
│   │   └── django_payment_repository.py
│   └── adapters/
│       ├── manual_payment_adapter.py
│       ├── razorpay_adapter.py
│       └── cashfree_adapter.py
└── presentation/
    ├── views/
    ├── serializers/
    └── urls.py
```

### 8.2 Provider Abstraction

All payment providers must implement the `PaymentGateway` interface:

```python
# payments/domain/services/payment_gateway.py
class PaymentGateway(Protocol):
    def initiate_payment(self, request: PaymentRequest) -> PaymentResponse: ...
    def verify_payment(self, request: VerificationRequest) -> VerificationResult: ...
    def create_payout(self, request: PayoutRequest) -> PayoutResponse: ...
```

**Year 1 (Enabled):**
- `ManualPaymentAdapter` — UPI QR, UTR verification

**Stage 2 (Disabled by feature flags):**
- `RazorpayAdapter` — `CASHFREE_PAYMENTS_ENABLED = False`
- `CashfreeAdapter` — `RAZORPAY_PAYMENTS_ENABLED = False`

**UI Requirement:** Display "Coming Soon" badge on Cashfree/Razorpay options.

### 8.3 Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `UPI_PAYMENT_ENABLED` | `True` | Manual UPI flow |
| `RAZORPAY_PAYMENTS_ENABLED` | `False` | Razorpay integration |
| `CASHFREE_PAYMENTS_ENABLED` | `False` | Cashfree integration |

### 8.4 Idempotency

All payment flows must be idempotent. Webhooks must support retries. Use idempotency keys for safe retries.

---

## 9. Dashboard Strategy

### 9.1 Bounded Context

Keep Dashboard as an independent bounded context within the monolith.

**Location:** `dashboard/` Django app.

**Structure:**
```
dashboard/
├── domain/
│   ├── entities/
│   │   ├── dashboard_summary.py       # Read model
│   │   ├── rent_analytics.py
│   │   └── occupancy_analytics.py
│   ├── value_objects/
│   │   ├── time_range.py
│   │   └── analytics_metric.py
│   └── services/
│       ├── dashboard_summary_service.py
│       ├── rent_analytics_service.py
│       └── occupancy_analytics_service.py
├── application/
│   └── services/
│       └── dashboard_query_service.py
├── infrastructure/
│   ├── repositories/
│   │   └── django_dashboard_repository.py
│   └── read_models/
│       └── materialized_views.py      # Optional: materialized views for analytics
└── presentation/
    ├── views/
    ├── serializers/
    └── urls.py
```

### 9.2 CQRS Evaluation

**Recommendation:** Do NOT introduce CQRS read models unless analytics complexity justifies it. For Year 1, use optimized Django queries with `select_related`/`prefetch_related` and database indexes.

**When to introduce CQRS read models:**
- Dashboard queries exceed 500ms consistently
- Analytics reports require joins across 5+ tables
- Read volume significantly exceeds write volume (>10:1)
- Owner requests custom report builder

### 9.3 Read Model Strategy (Year 1)

Use PostgreSQL full-text search with trigram indexes. Do not introduce OpenSearch unless search complexity justifies it (trigger: global search across properties, renters, documents becomes a user requirement).

---

## 10. AI / SmartBot Strategy

### 10.1 Single AI Context

There must be exactly one AI bounded context. **Merge `ai_assistant/` into `smartbot/`.**

**Action:** Delete `ai_assistant/` app. Move any useful code to `smartbot/`. Update `INSTALLED_APPS`.

### 10.2 Scope

```
smartbot/
├── domain/
│   ├── entities/
│   │   ├── smart_bot_chat.py
│   │   ├── smart_bot_message.py
│   │   └── ai_alert.py
│   ├── value_objects/
│   │   ├── intent.py
│   │   ├── action.py
│   │   └── confidence_score.py
│   └── services/
│       ├── chatbot_service.py
│       ├── gpt_service.py
│       └── agreement_ai_service.py
├── application/
│   └── services/
│       ├── chat_processing_service.py
│       ├── intent_extraction_service.py
│       └── action_dispatch_service.py
├── infrastructure/
│   ├── repositories/
│   │   └── django_smartbot_repository.py
│   └── clients/
│       └── openai_client.py
└── presentation/
    ├── views/
    ├── serializers/
    └── urls.py
```

---

## 11. Missing Bounded Contexts

### 11.1 Audit Context

**Recommendation:** **Phase 2** — Create as a dedicated context.

**Rationale:** Activity logs, security logs, user actions, and admin logs are currently scattered. A dedicated `audit/` context provides:
- Centralized audit trail
- Compliance-ready logging
- Security event tracking
- Admin action history

**Scope:**
- `ActivityLog` — user actions
- `SecurityLog` — login attempts, permission changes
- `AdminLog` — admin actions

**Do NOT use Django's built-in logging for business audit trails.** Use explicit domain events.

### 11.2 Storage Context

**Recommendation:** **Phase 2** — Create as a dedicated context, but keep implementation simple.

**Rationale:** File management, images, documents, S3 integration, and CDN logic are currently scattered across `properties/`, `documents/`, and `rentsecure_be/utils/`.

**Scope:**
- `File` — uploaded file entity
- `S3StorageService` — S3 upload/download
- `CDNService` — CDN URL generation
- `DocumentStorageService` — document-specific storage

**Implementation:** Use Django's storage backends (`storages` library) but wrap them in a Storage context to isolate external integration.

**Do NOT introduce a complex file management system.** Simple S3-backed storage with signed URLs is sufficient for Year 1.

### 11.3 Billing Context

**Recommendation:** **Postpone** — Not required for Year 1.

**Rationale:** The existing `Subscription` context already handles plan purchases and usage limits. Full subscription billing (GST invoices, payment gateway integration, usage tracking) is overkill until:
- Monthly transaction volume exceeds 500 payments/month
- GST compliance becomes a requirement
- Users request detailed invoicing

**Year 1 alternative:** Keep subscription logic in `Subscription` context. Add basic invoice generation in `Documents` context when needed.

**When to introduce:** Stage 2, when automated payment gateways are enabled and GST compliance is required.

### 11.4 Search Context

**Recommendation:** **Phase 3** — Introduce only when needed.

**Rationale:** Global search across properties, renters, documents, and finance records is not a Year 1 requirement.

**Year 1 alternative:** Use PostgreSQL full-text search with trigram indexes on key fields.

**When to introduce:** When users request cross-entity search and PostgreSQL full-text search performance degrades.

**Do NOT introduce OpenSearch without a clear trigger.** OpenSearch adds operational cost and complexity.

### 11.5 Workflow / Automation Context

**Recommendation:** **Postpone** — Not required for Year 1.

**Rationale:** Rules, triggers, scheduled actions, and an automation engine are valuable but add significant complexity. Current requirements can be met with Django management commands and crontab.

**Year 1 alternative:** Use Django management commands triggered by systemd timers or crontab.

**When to introduce:** When non-technical users need to configure automation rules, or when scheduled actions exceed 10 distinct workflows.

---

## 12. Infrastructure Recommendations

### 12.1 Keep These Technologies

| Technology | Use Case | Phase |
|-----------|----------|-------|
| **PostgreSQL** | Primary database | Current |
| **LocMemCache** | Year 1 caching | Phase 1 |
| **Redis** | Cache upgrade, Celery broker | Phase 2 |
| **Celery** | Background job processing | Phase 2 |
| **S3** | File/document storage | Current |
| **Nginx** | Reverse proxy, static files | Current |
| **Gunicorn** | WSGI server | Current |
| **Django 4.2/5.x LTS** | Web framework | Current |
| **DRF** | REST API | Current |

### 12.2 Do NOT Introduce Unless Strongly Justified

| Technology | Reason to Avoid | When It Might Be Justified |
|-----------|----------------|---------------------------|
| **Kubernetes** | Extreme operational overhead for a small team; ₹2-3k/month budget cannot support it | >50 services, >10 deployments/day |
| **Service Mesh** | Adds latency and complexity; no benefit in monolith | Microservice architecture with >20 services |
| **Istio / Linkerd** | Overkill for monolith; steep learning curve | Microservice architecture |
| **Kafka** | Heavy operational burden; single-process event bus is sufficient for monolith | >5 deployable services, event replay required |
| **CockroachDB / Google Spanner** | High cost; PostgreSQL with read replicas is sufficient for most use cases | Global multi-region, >1M rows/second write |
| **Event Sourcing** | Complex to implement and debug; not justified for current domain complexity | Audit-heavy domains, financial ledger requirements |
| **GraphQL** | Adds API surface complexity; DRF is sufficient | Multiple client types with divergent data needs |
| **Microservices** | Premature optimization; increases latency, operational cost, and deployment complexity | >10 developers, >5 independent deployment units |

### 12.3 Year 1 Deployment (Budget-Conscious)

**Target:** Single EC2 instance (t3.small or t3.medium) or AWS Free Tier.

**Stack:**
- EC2 (t3.small) or ECS Fargate (low usage)
- RDS PostgreSQL (db.t3.micro or Free Tier)
- S3 (storage)
- CloudFront (CDN, optional)
- ALB or Nginx on EC2
- No Redis (use LocMemCache until Phase 2)
- No Celery (use management commands + crontab until Phase 2)

**Estimated monthly cost:** ₹1,500–2,500.

---

## 13. Migration Strategy — Modular Monolith Roadmap

### Phase 1: Foundation (Monolith Discipline) — Current → 6 months

**Objective:** Establish proper bounded context boundaries within the monolith. No service extraction.

- [ ] **Create `payments/` bounded context** — Extract from `rentsecure_be/services/`
- [ ] **Promote `dashboard/` to proper bounded context** — Move analytics from `properties/`
- [ ] **Merge `ai_assistant/` into `smartbot/`** — Eliminate duplicate
- [ ] **Fix business logic in views** — Extract to Application Services
- [ ] **Fix cross-app model imports** — Use `settings.AUTH_USER_MODEL`
- [ ] **Add API versioning** — `/api/v1/`
- [ ] **Establish Shared Kernel** — Restructure `shared/` to `shared_kernel/`
- [ ] **Add domain layer structure** — `domain/`, `application/`, `infrastructure/` in each context
- [ ] **Remove duplicate URL mounts** — Keep only `/api/`
- [ ] **Fix Razorpay webhook security** — Add signature verification
- [ ] **Implement or remove stub `rent_service.py`**

**Deliverable:** A clean Modular Monolith with proper context boundaries, no cross-context coupling violations, and a working Shared Kernel.

---

### Phase 2: Internal Refinement — 6–18 months

**Objective:** Strengthen internal architecture. Prepare for future service extraction without actually extracting.

- [ ] **Extract `identity/` from `core/`** — As subpackage or rename app
- [ ] **Extract `subscription/` from `core/`** — As subpackage
- [ ] **Introduce Audit Context** — `audit/` for activity logs, security logs
- [ ] **Introduce Storage Context** — `storage/` for S3, CDN, file management
- [ ] **Implement Domain Events** — Replace Django Signals with explicit event bus
- [ ] **Add Repository Pattern** — With protocols in `shared_kernel/`
- [ ] **Configure Celery + Redis** — Replace management commands for async tasks
- [ ] **Migrate cache to Redis** — Replace LocMemCache
- [ ] **Add comprehensive tests** — Unit tests for domain layer, integration tests for APIs
- [ ] **Optimize queries** — Add missing indexes, partial indexes, covering indexes

**Deliverable:** A robust Modular Monolith with clean internal boundaries, async processing, and strong test coverage.

---

### Phase 3: Advanced Patterns — 18–36 months

**Objective:** Introduce patterns that prepare for future scale without changing deployment model.

- [ ] **CQRS Read Models** — Only if analytics complexity justifies it
- [ ] **Redis Streams** — Only if async processing volume justifies it
- [ ] **Materialized Views** — For dashboard analytics
- [ ] **Search Context** — Only if global search becomes a requirement
- [ ] **Add read replicas** — For PostgreSQL if read load increases
- [ ] **Implement Billing Context** — When automated payments and GST compliance are required

**Deliverable:** An optimized Modular Monolith with advanced patterns where justified.

---

### Phase 4: Service Extraction (Only If Business Scale Justifies) — 36+ months

**Objective:** Extract bounded contexts into independent services ONLY when measurable business needs require it.

**Trigger Conditions (all must be met):**
- [ ] Monthly transaction volume exceeds 5,000 payments/month
- [ ] Manual verification overhead exceeds 20 hours/week
- [ ] Team size exceeds 15 engineers
- [ ] Deployment frequency is blocked by monolith coupling
- [ ] Specific contexts have independent scaling requirements

**Extraction Order (if triggered):**
1. `payments/` — Highest scaling and compliance requirements
2. `notification/` — Independent delivery requirements
3. `identity/` — Shared across all other services
4. `rent/` — Core business domain
5. Others as needed

**Infrastructure to introduce ONLY at this stage:**
- API Gateway (AWS API Gateway or Kong)
- Load Balancer + multiple app servers
- Service discovery (if needed)
- Distributed tracing (Jaeger/Zipkin) — optional
- **NOT** Kubernetes unless team size and deployment frequency justify it

**Make it explicit:** Microservices are an **optimization**, not an architectural milestone. The Modular Monolith remains the primary architecture for many years.

---

## 14. Review of Existing Recommendations

| # | Existing Recommendation | Classification | Reasoning |
|---|------------------------|---------------|-----------|
| 1 | Extract `payments/` bounded context | **Keep** | Critical — payment logic is scattered |
| 2 | Fix business logic in views | **Keep** | CRITICAL — violates Clean Architecture |
| 3 | Fix cross-app model imports | **Keep** | HIGH — violates import rules |
| 4 | Implement proper `dashboard` context | **Keep** | HIGH — analytics logic is coupled to `properties` |
| 5 | Merge `ai_assistant/` into `smartbot/` | **Keep** | MEDIUM — eliminates duplicate |
| 6 | Add API versioning | **Keep** | MEDIUM — prevents breaking changes |
| 7 | Configure Celery + Redis | **Modify** | Keep goal, but postpone to Phase 2; use management commands + crontab in Phase 1 |
| 8 | Migrate from LocMemCache to Redis | **Modify** | Keep goal, but postpone to Phase 2; LocMemCache is fine for Year 1 |
| 9 | Implement event bus | **Modify** | Replace Kafka with lightweight in-process event bus |
| 10 | Add repository pattern | **Keep** | HIGH — enables testability and future extraction |
| 11 | Implement domain layer | **Keep** | HIGH — core to Clean Architecture |
| 12 | Add proper testing | **Keep** | HIGH — required for maintainability |
| 13 | Deploy bounded contexts as independent services | **Remove** | Wrong target for Modular Monolith; postpone to Phase 4 with clear triggers |
| 14 | Add API gateway | **Remove** | Not needed until service extraction (Phase 4) |
| 15 | Add service mesh (Istio/Linkerd) | **Remove** | Never needed for monolith; only if >20 services |
| 16 | Implement distributed tracing | **Postpone** | Not needed until Phase 4 service extraction |
| 17 | Add circuit breakers | **Remove** | Not needed in monolith; only relevant for inter-service communication |
| 18 | Implement CQRS | **Modify** | Keep as Phase 3 option, not Phase 2 requirement |
| 19 | Add event sourcing | **Remove** | Not justified for current domain complexity |
| 20 | Multi-region deployment | **Remove** | Not needed for Year 1 budget |
| 21 | Add AI/ML services for predictive analytics | **Postpone** | Valuable but not Year 1 priority |
| 22 | Database per context | **Remove** | Single PostgreSQL is correct for monolith; read replicas if needed |
| 23 | Polyglot persistence | **Remove** | Single PostgreSQL is correct for monolith |
| 24 | Distributed SQL (CockroachDB/Spanner) | **Remove** | Never needed unless global scale is reached |
| 25 | Implement GraphQL | **Remove** | DRF is sufficient; adds unnecessary complexity |
| 26 | Use FastAPI hybrid | **Remove** | Django + DRF is sufficient; no hybrid needed |
| 27 | Extract `identity/` as independent service | **Modify** | Keep as internal refactoring in Phase 2; service extraction only in Phase 4 |
| 28 | Extract `subscription/` as independent service | **Modify** | Keep as internal refactoring in Phase 2; service extraction only in Phase 4 |
| 29 | Extract `rent/` from `properties/` | **Keep** | Internal refactoring in Phase 2 to clarify boundaries |
| 30 | Extract `renter/` from `properties/` | **Keep** | Internal refactoring in Phase 2 to clarify boundaries |

---

## 15. Scalability Recommendations

### 15.1 Database Scalability

| Aspect | Recommendation | Phase | Cost Impact |
|--------|---------------|-------|-------------|
| Primary DB | PostgreSQL single instance | Current | Low |
| Indexes | Add composite and partial indexes | Phase 1 | None |
| Read Replicas | Add 1 read replica for analytics | Phase 3 | Medium (~₹1,000/month) |
| Connection Pooling | PgBouncer | Phase 2 | Low |
| Query Optimization | `select_related`/`prefetch_related`, avoid N+1 | Current | None |
| **Sharding** | **NOT recommended** | Never | High |

**Rationale:** PostgreSQL with proper indexes handles millions of rows. Read replicas are the correct scaling mechanism for read-heavy workloads.

### 15.2 Application Scalability

| Aspect | Recommendation | Phase | Cost Impact |
|--------|---------------|-------|-------------|
| Deployment | Single EC2 instance (t3.medium) or ECS Fargate | Current | Low |
| WSGI | Gunicorn with 4 workers | Current | None |
| Reverse Proxy | Nginx | Current | None |
| Horizontal Scaling | Multiple EC2 behind ALB | Phase 4 | Medium (~₹2,000/month) |
| Session Storage | Redis (when horizontal scaling) | Phase 2 | Low (~₹500/month) |
| Cache | Redis | Phase 2 | Low (~₹500/month) |

**Rationale:** A single well-configured EC2 instance handles thousands of requests per minute. Horizontal scaling is only needed when CPU/memory consistently exceeds 70%.

### 15.3 Background Job Scalability

| Aspect | Recommendation | Phase | Cost Impact |
|--------|---------------|-------|-------------|
| Current | Management commands + crontab | Phase 1 | None |
| Upgrade | Celery + Redis | Phase 2 | Low (~₹500/month) |
| Distributed Locking | Redis lock or `django-redis` | Phase 2 | None |
| Retry Policies | Celery retry with exponential backoff | Phase 2 | None |

**Rationale:** Celery is overkill for Year 1. Management commands + crontab are simpler, cheaper, and sufficient for low-volume background tasks.

### 15.4 Storage Scalability

| Aspect | Recommendation | Phase | Cost Impact |
|--------|---------------|-------|-------------|
| Current | Local storage or S3 | Current | Low (~₹100/month) |
| Upgrade | S3 + CloudFront CDN | Phase 2 | Medium (~₹500/month) |
| File Size Limits | Enforce in application | Current | None |

---

## 16. Technical Debt Priorities

### 16.1 Debt Inventory

| # | Debt Item | Location | Severity | Effort | Impact |
|---|-----------|----------|----------|--------|--------|
| 1 | Business logic in views | `properties/views/rent_record_views.py` | CRITICAL | 4h | Testing, maintenance |
| 2 | Cross-app model imports | `properties/models/*.py` | HIGH | 2h | Import-linter violations |
| 3 | Missing payments context | `rentsecure_be/services/` | CRITICAL | 2w | Domain ownership |
| 4 | Anemic domain models | All apps | HIGH | 1w | Logic scattering |
| 5 | Stub rent service | `properties/services/rent_service.py` | MEDIUM | 1h | False sense of completion |
| 6 | Feature flag mismatch | `core/views.py`, docs | MEDIUM | 30m | Configuration confusion |
| 7 | No API versioning | All endpoints | MEDIUM | 1d | Breaking changes |
| 8 | Duplicate URL mounts | `rentsecure_be/urls.py` | LOW | 10m | Maintenance |
| 9 | Empty ai_assistant app | `ai_assistant/` | MEDIUM | 2h | Duplicate structure |
| 10 | Dashboard shell | `dashboard/` | HIGH | 1w | No analytics context |
| 11 | Signals tightly coupled | `properties/signals/__init__.py` | MEDIUM | 4h | Testability |
| 12 | No domain layer | All apps | HIGH | 3mo | Clean Architecture |
| 13 | Razorpay webhook security | `core/views.py` | HIGH | 2h | Security |
| 14 | LocMemCache | `settings.py` | LOW | 1d | Horizontal scaling (defer) |
| 15 | Celery not configured | `settings.py` | MEDIUM | 1d | Background jobs (defer) |
| 16 | Missing Audit context | Cross-cutting | MEDIUM | 1w | Compliance, security |
| 17 | Missing Storage context | Cross-cutting | MEDIUM | 3d | File management isolation |

### 16.2 Prioritization

**Priority 1 (Critical — Phase 1):**
1. Missing payments context
2. Business logic in views
3. Cross-app model imports
4. Razorpay webhook security
5. Dashboard shell (promote to context)
6. Merge `ai_assistant/` into `smartbot/`
7. Stub rent service
8. Remove duplicate URL mounts

**Priority 2 (High — Phase 1-2):**
9. Anemic domain models (start adding domain methods)
10. No API versioning
11. Feature flag mismatch
12. Establish Shared Kernel
13. Add domain layer structure
14. Signals tightly coupled

**Priority 3 (Medium — Phase 2):**
15. Celery + Redis configuration
16. Migrate cache to Redis
17. Missing Audit context
18. Missing Storage context

**Priority 4 (Low — Phase 2-3):**
19. LocMemCache migration
20. CQRS read models (only if justified)

---

## 17. Modular Monolith Best Practices

### 17.1 Module Boundaries

- Each bounded context is a Django app with a clear, single responsibility.
- No circular dependencies between apps.
- Apps communicate only via:
  - `shared_kernel/` interfaces
  - Domain Events
  - Application Services (synchronous)

### 17.2 Internal Communication

- **Within a transaction:** Synchronous Application Service call.
- **Across contexts, same transaction:** Domain Event via event bus.
- **Across contexts, eventual consistency:** Application Event with background handler (when Celery is configured).

### 17.3 Database

- Single PostgreSQL database.
- Use database-level foreign keys.
- Do NOT use separate databases per context in the monolith.
- Read replicas are added at the infrastructure level, not per context.

### 17.4 Deployment

- Single deployable unit (one Docker image, one Gunicorn process group).
- One `manage.py migrate` runs all migrations.
- One `collectstatic` collects all static files.
- One process restart deploys all contexts.

### 17.5 Testing

- Unit tests per context (domain layer).
- Integration tests per context (application layer with test database).
- Contract tests between contexts (if event-based communication is used).
- End-to-end tests for critical user journeys.

### 17.6 Configuration

- Environment variables for all configuration.
- Feature flags in `settings.py` or environment.
- No hardcoded URLs, credentials, or magic numbers.

---

## 18. Future Service Extraction Strategy

### 18.1 Design for Extraction

Every bounded context is designed as if it could become an independent service later, **without actually splitting it.**

**Implementation rules:**
1. Each context has its own `domain/`, `application/`, `infrastructure/`, `presentation/` layers.
2. Each context owns its database tables (via Django models in `infrastructure/`).
3. Cross-context communication uses interfaces, not concrete classes.
4. Each context can be extracted by:
   - Moving its directory to a new repository
   - Creating a new Django project
   - Exposing its Application Services via REST/GraphQL
   - Updating the `shared_kernel/` interfaces to network protocols

### 18.2 Extraction Checklist

When business scale justifies extraction, verify:
- [ ] Context has no direct model imports from other contexts
- [ ] Context communicates only via ports/adapters or events
- [ ] Context has its own test suite (passes in isolation)
- [ ] Context has no circular dependencies
- [ ] Context's data model can be separated without breaking other contexts

### 18.3 Extraction Order (If Triggered)

1. **`payments/`** — Compliance and scaling requirements
2. **`notification/`** — Independent delivery infrastructure
3. **`identity/`** — Shared across all services
4. **`rent/`** — Core business domain
5. **Others** — As needed based on team structure

**Extraction does not mean microservices for all contexts.** Some contexts (e.g., `referral/`) may stay in the monolith indefinitely.

---

## 19. Risks Introduced by Premature Microservices

### 19.1 Operational Risks

| Risk | Description | Impact |
|------|-------------|--------|
| **Increased Latency** | Network calls replace in-process calls | 10-100ms per cross-service call |
| **Distributed Transactions** | No ACID across services | Data inconsistency risk |
| **Complex Deployments** | Multiple services to deploy, monitor, rollback | Higher operational cost |
| **Service Discovery** | Need for Consul, Eureka, or cloud service mesh | Additional infrastructure |
| **Network Partitions** | Services become unavailable independently | Cascading failures |

### 19.2 Cost Risks

| Risk | Description | Impact |
|------|-------------|--------|
| **Higher Infrastructure Cost** | Load balancers, API gateways, service mesh, monitoring | ₹10,000–50,000/month |
| **Team Coordination Cost** | More meetings, API contracts, versioning | Slower delivery |
| **Observability Cost** | Distributed tracing, metrics, logging aggregation | ₹5,000–15,000/month |
| **Security Surface** | More endpoints to secure, authenticate, authorize | Increased attack surface |

### 19.3 Organizational Risks

| Risk | Description | Impact |
|------|-------------|--------|
| **Premature Optimization** | Solving problems that don't exist yet | Wasted engineering effort |
| **Loss of Modularity Benefits** | Modular Monolith gives most benefits without cost | Architectural regret |
| **Team Friction** | "Who owns this service?" disputes | Slower decision making |
| **Onboarding Complexity** | New devs must understand distributed system | Longer ramp-up time |

### 19.4 When Microservices ARE Justified

Microservices become the right choice only when:
- The team is large enough that multiple squads need independent deployment (typically >15 engineers).
- Specific contexts have wildly different scaling requirements (e.g., AI inference vs. CRUD).
- Compliance or security requires strict isolation between domains.
- The business can afford the operational overhead (₹20,000+/month infrastructure).

**For RentSecure at current scale (₹2,000–3,000/month budget, small team), microservices are a liability, not an asset.**

---

## 20. Modular Monolith vs. Microservices Decision Matrix

| Factor | Modular Monolith | Microservices |
|--------|-----------------|---------------|
| **Team Size** | 1–10 engineers | >15 engineers |
| **Deployment Frequency** | Weekly | Multiple/day |
| **Scaling Needs** | Uniform | Heterogeneous |
| **Operational Budget** | Low (₹2–5k/month) | High (₹20k+/month) |
| **Domain Complexity** | Medium | High |
| **Latency Sensitivity** | High | Medium |
| **Compliance Isolation** | Low | High |
| **Correct Choice for RentSecure (Year 1–3)** | ✅ Yes | ❌ No |

---

## 21. Final Architecture Score

| Category | Score (1-10) | Rationale |
|----------|-------------|-----------|
| **Modular Monolith Discipline** | 4/10 | Bounded contexts exist but boundaries are violated; cross-app coupling is high |
| **Clean Architecture Compliance** | 3/10 | Business logic in views, anemic models, no domain layer |
| **Shared Kernel Quality** | 5/10 | `shared/` exists but is generic; needs restructuring to `shared_kernel/` |
| **Dependency Management** | 4/10 | Direct cross-app model imports violate import-linter |
| **Testability** | 5/10 | Service layer exists but views contain business logic |
| **Scalability Path** | 6/10 | Architecture supports scaling within monolith; microservice path is documented but premature |
| **Operational Cost** | 8/10 | Year 1 budget is realistic for monolith |
| **Maintainability** | 4/10 | Logic scattering, stub services, duplicate apps |
| **Security** | 7/10 | JWT auth present; webhook security needs hardening |
| **Documentation** | 7/10 | Well-documented target architecture, but code drift exists |

### Overall Score: **5.5/10** → Target: **8.5/10** after Phase 1

**Gap Analysis:**
- Current state: Codebase is in early transformation stage with significant violations.
- Target state: World-class Modular Monolith with clean boundaries, proper domain layer, and Shared Kernel.
- Path: Phased migration with strong emphasis on monolith discipline before considering service extraction.

---

## 22. Conclusion

The RentSecureBE project has a **solid foundation** and an **excellent documented target architecture**, but the current codebase is in an **early transformation stage** with a **misaligned migration roadmap** that prioritizes microservices before establishing Modular Monolith discipline.

**The most critical gaps are:**
1. **Missing `payments/` bounded context** — Payment logic is scattered and lacks domain ownership
2. **Business logic in views** — Violates Clean Architecture principles
3. **Cross-app coupling** — Direct model imports create maintenance risk
4. **Anemic domain models** — Logic scattering reduces maintainability
5. **Empty `ai_assistant/` app** — Duplicate of `smartbot/`
6. **Dashboard is a shell** — Analytics logic coupled to `properties/`

**The recommended approach is a phased Modular Monolith migration** that:
- Preserves existing functionality
- Adds proper domain layers incrementally
- Extracts bounded contexts internally (not as services)
- Maintains CI green throughout
- Validates each phase before proceeding
- Keeps deployment simple and cost-effective
- **Explicitly delays microservice extraction until business scale justifies it**

**With disciplined execution, the codebase can reach a world-class Modular Monolith architecture within 12-18 months**, positioning RentSecure for scalable, maintainable growth over the next 10–20 years without incurring unnecessary operational cost or complexity.

---

*End of Modular Monolith Architecture Review & Refactoring*
