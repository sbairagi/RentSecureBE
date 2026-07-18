# RentSecureBE — Comprehensive Architecture Analysis

**Document:** Comprehensive Architecture Analysis
**Version:** 1.0.0
**Date:** 2026-07-18
**Author:** Principal Software Architect
**Status:** ANALYSIS COMPLETE — READ-ONLY
**Scope:** Complete codebase analysis for architecture redesign
**Constraint:** No code modifications. Analysis only.

---

## 1. Executive Summary

RentSecureBE is a Django 4.2.30 + DRF modular monolith designed for property management, rent collection, and financial operations. The project has an **extremely well-documented target architecture** describing Clean Architecture, DDD, Hexagonal Architecture, and 10+ bounded contexts. However, the **actual codebase is in an earlier transformation stage** with significant gaps between documented intent and implemented reality.

**Key Findings:**
- **11 business domains** identified across the codebase
- **8 bounded contexts** exist in code; **4 are missing** (`payments/`, `infrastructure/`, `identity/`, `assistant/`)
- **Critical architecture violations**: business logic in views, anemic domain models, missing domain layer, cross-app coupling
- **Payment logic is scattered** in `rentsecure_be/services/` instead of a dedicated `payments/` app
- **Dashboard is a shell** with no real analytics implementation
- **`ai_assistant/` is empty** while `smartbot/` contains the actual AI code
- **Feature flags in code don't match documentation**
- **API has no versioning** despite documented requirement

**Recommendation:** The codebase needs a phased migration to the documented target architecture, prioritizing the extraction of the missing `payments/` bounded context and the establishment of a proper domain layer.

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
│   └── migrations/
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

### 4.1 Proposed Bounded Contexts (Target Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RentSecure Bounded Context Map                        │
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
- `shared/` — utilities, exceptions
- `core/` — currently owns this context

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
- `shared/` — utilities, exceptions
- `core/` — currently owns this context

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
- `shared/` — utilities, exceptions
- `core/` — User model (owner)

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
- `shared/` — utilities, exceptions
- `properties/` — Unit, Building
- `core/` — User

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
- `notification/` — reminder dispatch
- `documents/` — invoice PDF generation

**Future Growth:**
- Dynamic rent pricing
- Split payments
- Installment plans
- Rent negotiation

**Dependencies:**
- `shared/` — utilities, exceptions
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
- `PaymentGateway` (interface)
- `ManualPaymentAdapter` — UPI QR, UTR verification
- `RazorpayAdapter` — payment links, webhooks (Stage 2)
- `CashfreeAdapter` — payouts, beneficiary management (Stage 2)
- `PayoutService` — payout orchestration

**Application Services:**
- `PaymentInitiationService`
- `PaymentVerificationService`
- `PayoutProcessingService`

**External Integrations:**
- Razorpay API
- Cashfree API
- Manual UPI (bank transfer)

**Future Growth:**
- Auto-payment via UPI mandate
- Payment splits
- Escrow accounts
- Multi-currency support

**Dependencies:**
- `shared/` — utilities, exceptions
- `rent/` — RentRecord
- `property/` — Unit, Owner bank details
- `notification/` — payment notifications

**Expected APIs:**
- `POST /api/v1/payments/initiate`
- `POST /api/v1/payments/verify`
- `POST /api/v1/payouts/process`
- `POST /api/v1/payouts/retry`
- `POST /api/v1/utr/verify`
- `POST /api/v1/webhooks/razorpay`
- `POST /api/v1/webhooks/cashfree`

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
- `shared/` — utilities, exceptions
- `property/` — PropertyTaxRecord
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
- `shared/` — utilities, exceptions
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
- `NotificationChannel` (interface)
- `EmailAdapter` — SMTP
- `FCMAdapter` — Firebase Cloud Messaging
- `WhatsAppAdapter` — WhatsApp Business API (Stage 2)
- `SMSAdapter` — Twilio/MSG91 (Stage 2)
- `VoiceAdapter` — gTTS/OpenAI (Stage 3)

**Application Services:**
- `NotificationDispatchService`
- `NotificationPreferenceService`
- `NotificationSchedulingService`

**External Integrations:**
- SMTP (email)
- Firebase Cloud Messaging (push)
- Twilio (WhatsApp, SMS)
- edge-tts / OpenAI (voice)

**Future Growth:**
- In-app notification center
- Notification analytics
- A/B testing for templates
- Multi-language templates

**Dependencies:**
- `shared/` — utilities, exceptions
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
- `shared/` — utilities, exceptions
- `rent/` — rent actions
- `notification/` — notifications
- `documents/` — agreements

**Expected APIs:**
- `POST /api/v1/assistant/chat`
- `GET /api/v1/assistant/chats`
- `GET /api/v1/assistant/chats/{id}/messages`
- `POST /api/v1/assistant/actions/dispatch`

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
- `shared/` — utilities, exceptions
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
- `shared/` — utilities, exceptions
- `rent/` — RentRecord
- `property/` — Unit, Building
- `finance/` — tax data

**Expected APIs:**
- `GET /api/v1/dashboard/owner/summary`
- `GET /api/v1/dashboard/owner/rent-analytics`
- `GET /api/v1/dashboard/owner/occupancy-analytics`
- `GET /api/v1/dashboard/owner/monthly-summary`

---

## 5. Dependency Diagram

### 5.1 Current Dependency Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CURRENT DEPENDENCY FLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐                                                          │
│  │     core     │                                                          │
│  │  (Identity + │                                                          │
│  │ Subscription)│                                                          │
│  └──────┬───────┘                                                          │
│         │                                                                  │
│         │ imports                                                          │
│         ▼                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│  │ properties/  │────▶│ notification │────▶│   documents  │              │
│  │              │     │              │     │              │              │
│  │ • Building   │     │ • WhatsApp   │     │ • PDF        │              │
│  │ • Unit       │     │ • Voice      │     │ • E-sign     │              │
│  │ • Renter     │     │ • Email      │     │ • Receipts   │              │
│  │ • RentRecord │     │ • FCM        │     │              │              │
│  └──────┬───────┘     └──────┬───────┘     └──────────────┘              │
│         │                    │                                            │
│         │                    │ imports                                    │
│         │                    ▼                                            │
│         │              ┌──────────────┐                                   │
│         │              │   finance    │                                   │
│         │              │              │                                   │
│         │              │ • Tax        │                                   │
│         │              │ • CA Profiles│                                   │
│         │              │ • Reports    │                                   │
│         │              └──────────────┘                                   │
│         │                                                                  │
│         │ imports                                                        │
│         ▼                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│  │smartbot/     │     │referral_and_ │     │  dashboard/  │              │
│  │              │     │   earn/      │     │              │              │
│  │ • Chatbot    │     │              │     │ • Summary    │              │
│  │ • GPT        │     │ • Referral   │     │ • Analytics  │              │
│  │ • Intents    │     │ • Bonuses    │     │ • Reports    │              │
│  └──────────────┘     └──────────────┘     └──────────────┘              │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────┐             │
│  │              rentsecure_be/ (project services)            │             │
│  │  • razorpay_service.py  • cashfree_service.py            │             │
│  │  • leegality_service.py • i18n_service.py                │             │
│  └──────────────────────────────────────────────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Actual Import Dependencies

#### 5.2.1 Allowed Dependencies (per import-linter.ini)

| App | Can Import From |
|-----|-----------------|
| `core` | `core`, `rentsecure_be` |
| `properties` | `properties`, `rentsecure_be` |
| `notification` | `notification`, `rentsecure_be` |
| `finance` | `finance`, `rentsecure_be` |
| `documents` | `documents`, `rentsecure_be` |
| `smartbot` | `smartbot`, `rentsecure_be` |
| `referral_and_earn` | `referral_and_earn`, `rentsecure_be` |
| `ai_assistant` | `ai_assistant`, `rentsecure_be` |
| `dashboard` | `dashboard`, `rentsecure_be` |

#### 5.2.2 Actual Cross-App Dependencies (Violations)

| Source App | Target App | Import | Severity |
|------------|-----------|--------|----------|
| `properties` | `core` | `from core.models import User` | **HIGH** — Direct model import |
| `properties` | `core` | `from core.models import ...` (multiple) | **HIGH** — Direct model import |
| `properties` | `notification` | `from notification.services...` | **HIGH** — Service import |
| `properties` | `notification` | `from notification.models import Notification` | **HIGH** — Model import |
| `properties` | `rentsecure_be` | `from rentsecure_be.services.cashfree_service import ...` | **MEDIUM** — Infrastructure import |
| `properties` | `rentsecure_be` | `from rentsecure_be.services.razorpay_service import ...` | **MEDIUM** — Infrastructure import |
| `core` | `notification` | `from notification.services.rent_notify_service import send_payout_notification` | **HIGH** — Service import |
| `core` | `properties` | `from properties.models.rent_record_models import RentRecord` | **HIGH** — Model import |
| `notification` | `properties` | `from properties.models...` | **HIGH** — Model import |
| `smartbot` | `core` | `from core.models...` | **MEDIUM** — Model import |
| `finance` | `core` | `from core.models...` | **MEDIUM** — Model import |

**Key Violation:** The `properties` app directly imports `core.models.User`, violating the import-linter rule that apps should only import from themselves and `rentsecure_be`.

### 5.3 Cross-Context Communication

#### 5.3.1 Current Communication Patterns

| Pattern | Implementation | Usage |
|---------|---------------|-------|
| **Direct Service Calls** | `from notification.services import send_whatsapp_message` | `properties/signals/__init__.py` |
| **Direct Model Imports** | `from core.models import User` | `properties/models/building_models.py` |
| **Django Signals** | `@receiver(post_save, sender=Renter)` | `properties/signals/__init__.py` |
| **Custom Signals** | `renter_archived.send(...)` | `properties/signals/renter_signals.py` |

#### 5.3.2 Forbidden Dependencies

| Source | Target | Reason |
|--------|--------|--------|
| `properties` | `core.models` | Cross-app model import |
| `properties` | `notification.services` | Direct service import |
| `core` | `properties.models` | Cross-app model import |
| `notification` | `properties.models` | Cross-app model import |
| `core` | `notification.services` | Direct service import |

#### 5.3.3 Allowed Dependencies (Target Architecture)

| Source | Target | Mechanism |
|--------|--------|-----------|
| Any context | `shared/` | Direct import (utilities, exceptions, interfaces) |
| Context A | Context B | Via published interface (port/adapter) |
| Context A | Context B | Via domain events (event bus) |
| Context A | Context B | Via application service API |

---

## 6. Existing Problems

### 6.1 Critical Architecture Violations

#### 6.1.1 Business Logic in Views
**Severity:** CRITICAL
**Location:** `properties/views/rent_record_views.py`
**Description:** The `RentRecordViewSet.perform_create()` method contains business logic for payment link creation and WhatsApp notification sending.

```python
# properties/views/rent_record_views.py:51-79
@override
def perform_create(self, serializer: BaseSerializer[Any]) -> None:
    # ... validation logic in view ...
    enforcer = FeatureEnforcer(user)
    if not enforcer.can_create("rent_records"):
        raise PermissionDenied("You have reached your rent record creation limit.")

    rent = serializer.save()

    try:
        link = create_payment_link(rent)  # Business logic in view
        rent.payment_link = link
        rent.save(update_fields=["payment_link"])
        send_whatsapp_message(  # Notification in view
            rent.renter.phone if rent.renter else "", f"📩 Pay your rent: {link}"
        )
    except Exception as e:
        logger.warning(f"Failed to create payment link for rent {rent.id}: {e}")
```

**Impact:**
- Violates Single Responsibility Principle
- Difficult to test business logic independently
- Tightly couples HTTP layer with payment and notification domains

**Recommendation:** Extract to `RentRecordService.create_rent_record_with_payment()`.

---

#### 6.1.2 Anemic Domain Models
**Severity:** HIGH
**Location:** `properties/models/unit_models.py`, `properties/models/renter_models.py`
**Description:** Domain models are primarily data containers with minimal behavior. Business logic lives in services or views instead of on the models themselves.

```python
# properties/models/unit_models.py
class Unit(models.Model):
    # ... fields ...

    @property
    def units_count(self) -> int:
        return self.units.count()

    # No behavior for:
    # - Status transitions (vacant → occupied)
    # - Occupancy checks
    # - Validation
```

**Impact:**
- Logic scattered across services and views
- Hard to understand domain rules
- Difficult to enforce invariants

**Recommendation:** Add domain methods to models (e.g., `unit.vacate()`, `unit.occupy(renter)`, `renter.archive()`).

---

#### 6.1.3 Cross-App Model Imports
**Severity:** HIGH
**Location:** `properties/models/building_models.py`, `properties/models/unit_models.py`
**Description:** Property models directly import `core.models.User`.

```python
# properties/models/building_models.py:5
from core.models import User

class Building(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="buildings",
        ...
    )
```

**Impact:**
- Violates import-linter rules
- Creates circular dependency risk
- Makes it impossible to extract bounded contexts

**Recommendation:** Use `settings.AUTH_USER_MODEL` string reference instead of direct import.

---

#### 6.1.4 Stub Service with No Implementation
**Severity:** MEDIUM
**Location:** `properties/services/rent_service.py`
**Description:** `RentService` is a stub with all methods raising `NotImplementedError`.

```python
class RentService:
    @staticmethod
    def create_rent_record(user: Any, validated_data: dict[str, Any]) -> Any:
        raise NotImplementedError

    @staticmethod
    def update_rent_status(rent_record: Any, status: str) -> None:
        raise NotImplementedError
```

**Impact:**
- Suggests incomplete implementation
- May be called accidentally
- Creates false sense of architecture

**Recommendation:** Either implement the service or remove it and consolidate logic into existing services.

---

#### 6.1.5 Duplicate URL Mounts
**Severity:** LOW
**Location:** `rentsecure_be/urls.py`
**Description:** `properties/urls.py` is mounted at both `/api/` and `/properties/`.

```python
path("api/", include("properties.urls")),
path("properties/", include("properties.urls")),
```

**Impact:**
- Duplicate endpoints
- Potential confusion
- Maintenance burden

**Recommendation:** Remove one mount point.

---

#### 6.1.6 Missing Payments Bounded Context
**Severity:** CRITICAL
**Location:** `rentsecure_be/services/`
**Description:** Payment logic is scattered in project-level services instead of a dedicated `payments/` app.

```python
# rentsecure_be/services/razorpay_service.py
# rentsecure_be/services/cashfree_service.py
```

**Impact:**
- No clear ownership
- No domain layer
- No repository pattern
- Difficult to test
- Cannot scale payment domain independently

**Recommendation:** Create `payments/` app with proper domain layer, repositories, and port/adapter structure.

---

#### 6.1.7 Dashboard is a Shell
**Severity:** HIGH
**Location:** `dashboard/`
**Description:** The `dashboard` app has only 2 endpoints (`agreements/`, `retry-signature/`) and no analytics implementation. Dashboard logic lives in `properties/views/owner_dashboard.py`.

```python
# dashboard/views.py
# Only 2 endpoints, no analytics
```

**Impact:**
- No dedicated analytics context
- Dashboard logic coupled to `properties`
- Cannot evolve analytics independently

**Recommendation:** Either implement proper `dashboard` bounded context or merge into `properties`.

---

#### 6.1.8 AI Assistant is Empty
**Severity:** MEDIUM
**Location:** `ai_assistant/`
**Description:** `ai_assistant/models.py` is empty (1 comment line). Actual AI code lives in `smartbot/`.

```python
# ai_assistant/models.py
# (empty - 1 comment line)
```

**Impact:**
- Duplicate app structure
- Unclear ownership of AI domain
- Wasted app registration

**Recommendation:** Merge `ai_assistant/` into `smartbot/` or vice versa.

---

### 6.2 Architecture Violations Summary

| # | Violation | Severity | Location | Impact |
|---|-----------|----------|----------|--------|
| 1 | Business logic in views | CRITICAL | `properties/views/rent_record_views.py` | Testing, maintenance |
| 2 | Anemic domain models | HIGH | `properties/models/*.py` | Logic scattering |
| 3 | Cross-app model imports | HIGH | `properties/models/building_models.py` | Import-linter violation |
| 4 | Missing payments context | CRITICAL | `rentsecure_be/services/` | No domain ownership |
| 5 | Dashboard is a shell | HIGH | `dashboard/` | No analytics context |
| 6 | AI assistant empty | MEDIUM | `ai_assistant/` | Duplicate apps |
| 7 | Stub service | MEDIUM | `properties/services/rent_service.py` | Incomplete implementation |
| 8 | Duplicate URL mounts | LOW | `rentsecure_be/urls.py` | Maintenance burden |
| 9 | Feature flag mismatch | MEDIUM | `core/views.py` | Documentation drift |
| 10 | No API versioning | MEDIUM | All endpoints | Breaking changes risk |
| 11 | Signals tightly coupled | MEDIUM | `properties/signals/__init__.py` | Hard to test |
| 12 | No domain layer | HIGH | All apps | Clean Architecture violation |

---

## 7. Risk Level

### 7.1 Overall Risk Assessment

| Category | Risk Level | Justification |
|----------|-----------|---------------|
| **Architecture** | **HIGH** | Significant violations of Clean Architecture and DDD principles |
| **Data Integrity** | **MEDIUM** | Cross-app model imports create coupling risk |
| **Scalability** | **MEDIUM** | Modular monolith foundation is solid but missing key contexts |
| **Maintainability** | **HIGH** | Logic scattered across views and services |
| **Testing** | **MEDIUM** | Business logic in views is hard to test |
| **Security** | **LOW** | JWT auth, permission classes, input validation present |
| **Performance** | **LOW** | Caching in place, select_related used |
| **Observability** | **MEDIUM** | Logging present but no structured metrics |

### 7.2 Risk Matrix

```
                 High
                  │
                  │
    Architecture   │   Data Integrity
    Violations     │   Coupling Risk
                  │
                  │
    Maintainability│   Scalability
    Issues         │   Concerns
                  │
    ───────────────┼────────────────
                  │
                  │
    Testing Gaps   │   Performance
                  │   Concerns
                  │
                 Low
```

---

## 8. Scalability Risks

### 8.1 Database Scalability

| Risk | Current State | Future Impact | Mitigation |
|------|--------------|---------------|------------|
| **God Models** | `properties.models` fan-in: 74 imports | Changes break 74+ modules | Introduce DTOs, use `settings.AUTH_USER_MODEL` |
| **Missing Indexes** | Some indexes exist, but not comprehensive | Slow queries as data grows | Add composite indexes, partial indexes |
| **No Read Replicas** | Single PostgreSQL instance | Read-heavy dashboard queries will bottleneck | Add read replicas for analytics |
| **No Database Sharding** | Single database | Cannot scale beyond single instance | Plan for sharding by owner_id |

### 8.2 Application Scalability

| Risk | Current State | Future Impact | Mitigation |
|------|--------------|---------------|------------|
| **Monolithic Deployment** | Single Django process | Cannot scale contexts independently | Extract bounded contexts to separate services |
| **No Horizontal Scaling** | Single EC2 instance | Single point of failure | Add load balancer, multiple app servers |
| **Celery Not Configured** | Management commands only | Cannot scale background jobs | Configure Celery with Redis broker |
| **LocMemCache** | In-process cache | Cannot scale across multiple servers | Migrate to Redis cache |
| **No API Gateway** | Direct Django endpoints | Cannot rate-limit, authenticate at edge | Add API gateway (Kong, AWS API Gateway) |

### 8.3 Code Scalability

| Risk | Current State | Future Impact | Mitigation |
|------|--------------|---------------|------------|
| **Fat Views** | `core/views.py` 566 lines, mixed concerns | Hard to extend, test, maintain | Extract to services, split viewsets |
| **Cross-App Coupling** | 11 direct cross-app imports | Changes cascade across apps | Enforce import-linter, use interfaces |
| **No Domain Layer** | Models are anemic | Cannot express complex business rules | Introduce domain services, value objects |
| **Missing Payments Context** | Logic scattered | Cannot evolve payments independently | Extract `payments/` bounded context |

---

## 9. Maintainability Risks

### 9.1 Code Maintainability

| Risk | Current State | Impact | Mitigation |
|------|--------------|--------|------------|
| **Business Logic in Views** | `rent_record_views.py` has payment + notification logic | Hard to test, understand, modify | Extract to services |
| **Anemic Models** | Models are data containers | Logic scattered, hard to find | Add domain methods |
| **Stub Services** | `rent_service.py` raises NotImplementedError | False sense of completion | Implement or remove |
| **Duplicate Code** | Similar logic in multiple services | Bug fixes duplicated | Consolidate into shared services |
| **Magic Numbers** | Hardcoded values in code | Hard to change, understand | Move to constants, config |

### 9.2 Documentation Maintainability

| Risk | Current State | Impact | Mitigation |
|------|--------------|--------|------------|
| **Docs vs Code Drift** | Documentation describes target architecture, code is different | Confusion, incorrect assumptions | Update docs to reflect reality |
| **Feature Flag Mismatch** | Docs say `UPI_PAYMENT_ENABLED`, code has `ENABLE_RAZORPAY` | Incorrect configuration | Align flag names |
| **Missing API Docs** | No OpenAPI/Swagger docs | Hard to understand APIs | Generate API docs |

### 9.3 Test Maintainability

| Risk | Current State | Impact | Mitigation |
|------|--------------|--------|------------|
| **Hard-to-Test Views** | Business logic in views | Tests require full HTTP stack | Extract logic to services |
| **Cross-App Test Dependencies** | Tests import across apps | Test failures cascade | Isolate test domains |
| **Missing Contract Tests** | No API contract validation | Breaking changes undetected | Add Schemathesis/contract tests |

---

## 10. Technical Debt

### 10.1 Debt Inventory

| # | Debt Item | Location | Severity | Effort to Fix | Impact |
|---|-----------|----------|----------|---------------|--------|
| 1 | Business logic in views | `properties/views/rent_record_views.py` | HIGH | 4 hours | Testing, maintenance |
| 2 | Cross-app model imports | `properties/models/*.py` | HIGH | 2 hours | Import-linter violations |
| 3 | Missing payments context | `rentsecure_be/services/` | CRITICAL | 2 weeks | Domain ownership |
| 4 | Anemic domain models | All apps | HIGH | 1 week | Logic scattering |
| 5 | Stub rent service | `properties/services/rent_service.py` | MEDIUM | 1 hour | False sense of completion |
| 6 | Feature flag mismatch | `core/views.py`, docs | MEDIUM | 30 min | Configuration confusion |
| 7 | No API versioning | All endpoints | MEDIUM | 1 day | Breaking changes |
| 8 | Duplicate URL mounts | `rentsecure_be/urls.py` | LOW | 10 min | Maintenance |
| 9 | Empty ai_assistant app | `ai_assistant/` | MEDIUM | 2 hours | Duplicate structure |
| 10 | Dashboard shell | `dashboard/` | HIGH | 1 week | No analytics context |
| 11 | Signals tightly coupled | `properties/signals/__init__.py` | MEDIUM | 4 hours | Testability |
| 12 | No domain layer | All apps | HIGH | 3 months | Clean Architecture |
| 13 | Celery not configured | `settings.py` | MEDIUM | 1 day | Background jobs |
| 14 | LocMemCache | `settings.py` | MEDIUM | 1 day | Horizontal scaling |
| 15 | Razorpay webhook security | `core/views.py` | HIGH | 2 hours | Security |

### 10.2 Debt Prioritization

**Priority 1 (Critical — Fix Immediately):**
1. Missing payments context
2. Business logic in views
3. Razorpay webhook security

**Priority 2 (High — Fix in Next Sprint):**
4. Cross-app model imports
5. Anemic domain models
6. Dashboard shell
7. No domain layer (start)

**Priority 3 (Medium — Fix in Next Month):**
8. Feature flag mismatch
9. No API versioning
10. Empty ai_assistant app
11. Signals tightly coupled
12. Stub rent service

**Priority 4 (Low — Fix When Time Permits):**
13. Duplicate URL mounts
14. Celery not configured
15. LocMemCache

---

## 11. Suggested Future Architecture

### 11.1 Target Architecture (10-20 Year Vision)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     RentSecure Platform — Target Architecture                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                        API Gateway / Edge                         │       │
│  │                  (Kong / AWS API Gateway / Envoy)                 │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                     Load Balancer + CDN                          │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         │                          │                          │             │
│         ▼                          ▼                          ▼             │
│  ┌──────────────┐          ┌──────────────┐          ┌──────────────┐       │
│  │   Frontend    │          │   Frontend    │          │   Frontend   │       │
│  │   (Angular)   │          │   (Ionic)     │          │ (React Native│       │
│  │               │          │               │          │   Future)    │       │
│  └──────────────┘          └──────────────┘          └──────────────┘       │
│                                    │                          │             │
│                                    └──────────┬───────────────┘             │
│                                               ▼                              │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                    Event Bus (Kafka / Redis Streams)              │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         │                          │                          │             │
│         ▼                          ▼                          ▼             │
│  ┌──────────────┐          ┌──────────────┐          ┌──────────────┐       │
│  │   Identity   │          │ Subscription │          │   Property   │       │
│  │   Service    │          │   Service    │          │   Service    │       │
│  │  (独立部署)   │          │  (独立部署)   │          │  (独立部署)   │       │
│  └──────────────┘          └──────────────┘          └──────────────┘       │
│                                    │                          │             │
│                                    │                          │             │
│  ┌──────────────┐          ┌──────────────┐          ┌──────────────┐       │
│  │   Renter     │          │     Rent     │          │   Payments   │       │
│  │   Service    │          │   Service    │          │   Service    │       │
│  │  (独立部署)   │          │  (独立部署)   │          │  (独立部署)   │       │
│  └──────────────┘          └──────────────┘          └──────────────┘       │
│                                    │                          │             │
│                                    │                          │             │
│  ┌──────────────┐          ┌──────────────┐          ┌──────────────┐       │
│  │   Finance    │          │  Document    │          │ Notification │       │
│  │   Service    │          │   Service    │          │   Service    │       │
│  │  (独立部署)   │          │  (独立部署)   │          │  (独立部署)   │       │
│  └──────────────┘          └──────────────┘          └──────────────┘       │
│                                    │                          │             │
│                                    │                          │             │
│  ┌──────────────┐          ┌──────────────┐          ┌──────────────┐       │
│  │     AI       │          │   Referral   │          │  Dashboard   │       │
│  │   Service    │          │   Service    │          │   Service    │       │
│  │  (独立部署)   │          │  (独立部署)   │          │  (独立部署)   │       │
│  └──────────────┘          └──────────────┘          └──────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Migration Path

#### Phase 1: Foundation (Current → 6 months)
- [ ] Extract `payments/` bounded context from `rentsecure_be/services/`
- [ ] Introduce domain layer in `properties/` (domain/, application/, infrastructure/)
- [ ] Fix business logic in views (extract to services)
- [ ] Fix cross-app model imports (use `settings.AUTH_USER_MODEL`)
- [ ] Implement proper `dashboard` bounded context
- [ ] Merge `ai_assistant/` into `smartbot/`
- [ ] Add API versioning (`/api/v1/`)
- [ ] Configure Celery with Redis
- [ ] Migrate from LocMemCache to Redis

#### Phase 2: Bounded Context Extraction (6-18 months)
- [ ] Extract `identity/` from `core/`
- [ ] Extract `subscription/` from `core/` (or keep in `core`)
- [ ] Extract `rent/` from `properties/`
- [ ] Extract `renter/` from `properties/`
- [ ] Extract `payments/` (if not done in Phase 1)
- [ ] Implement event bus for cross-context communication
- [ ] Add proper domain events
- [ ] Implement repository pattern with protocols

#### Phase 3: Independent Services (18-36 months)
- [ ] Deploy `identity` as independent service
- [ ] Deploy `subscription` as independent service
- [ ] Deploy `property` as independent service
- [ ] Deploy `rent` as independent service
- [ ] Deploy `payments` as independent service
- [ ] Deploy `notification` as independent service
- [ ] Deploy `finance` as independent service
- [ ] Deploy `document` as independent service
- [ ] Deploy `ai` as independent service
- [ ] Deploy `referral` as independent service
- [ ] Deploy `dashboard` as independent service

#### Phase 4: Platform Scale (36+ months)
- [ ] Implement API gateway
- [ ] Add service mesh (Istio/Linkerd)
- [ ] Implement distributed tracing (Jaeger/Zipkin)
- [ ] Add circuit breakers (Hystrix/Resilience4j)
- [ ] Implement CQRS for read models
- [ ] Add event sourcing for audit trails
- [ ] Implement multi-region deployment
- [ ] Add AI/ML services for predictive analytics

### 11.3 Technology Evolution

| Phase | Technology | Rationale |
|-------|-----------|-----------|
| Current | Django 4.2 LTS | Stable, well-supported |
| Phase 1 | Django 5.x + DRF 3.16+ | Latest features, performance |
| Phase 2 | Django + FastAPI hybrid | GraphQL for complex queries |
| Phase 3 | Microservices (FastAPI/Go) | Independent scaling |
| Phase 4 | Kubernetes + Service Mesh | Platform scale |

### 11.4 Data Architecture Evolution

| Phase | Database Strategy | Rationale |
|-------|-------------------|-----------|
| Current | PostgreSQL (single) | Simplicity |
| Phase 1 | PostgreSQL + read replicas | Read scaling |
| Phase 2 | Database per context | Domain isolation |
| Phase 3 | Polyglot persistence | Right tool for each context |
| Phase 4 | Distributed SQL (CockroachDB/Spanner) | Global scale |

---

## 12. Final Recommendations

### 12.1 Immediate Actions (Week 1-2)

1. **Fix Razorpay webhook security** — Add signature verification
2. **Fix cross-app model imports** — Use `settings.AUTH_USER_MODEL`
3. **Extract payment logic from views** — Move to `RentRecordService`
4. **Remove duplicate URL mounts** — Keep only `/api/`

### 12.2 Short-Term Actions (Month 1-3)

1. **Create `payments/` bounded context** — Extract from `rentsecure_be/services/`
2. **Implement proper `dashboard` context** — Move analytics from `properties/`
3. **Merge `ai_assistant/` into `smartbot/`** — Eliminate duplicate
4. **Add API versioning** — `/api/v1/`
5. **Configure Celery + Redis** — Replace management commands
6. **Migrate to Redis cache** — Replace LocMemCache

### 12.3 Medium-Term Actions (Month 3-12)

1. **Introduce domain layer** — Add `domain/`, `application/`, `infrastructure/` to each app
2. **Extract `identity/` context** — From `core/`
3. **Extract `rent/` context** — From `properties/`
4. **Implement event bus** — Replace direct service calls
5. **Add repository pattern** — With protocols in `shared/`
6. **Implement proper testing** — Unit tests for domain layer, integration tests for APIs

### 12.4 Long-Term Actions (Year 1-2)

1. **Deploy bounded contexts as independent services** — When scale justifies
2. **Implement API gateway** — Kong or AWS API Gateway
3. **Add service mesh** — Istio or Linkerd
4. **Implement CQRS** — For read models in dashboard/analytics
5. **Add event sourcing** — For audit trails and compliance
6. **Multi-region deployment** — For global availability

---

## 13. Conclusion

The RentSecureBE project has a **solid foundation** and an **excellent documented target architecture**, but the current codebase is in an **early transformation stage**. The most critical gaps are:

1. **Missing `payments/` bounded context** — Payment logic is scattered and lacks domain ownership
2. **Business logic in views** — Violates Clean Architecture principles
3. **Cross-app coupling** — Direct model imports create maintenance risk
4. **Anemic domain models** — Logic scattering reduces maintainability

**The recommended approach is a phased migration** that:
- Preserves existing functionality
- Adds proper domain layers incrementally
- Extracts bounded contexts one at a time
- Maintains CI green throughout
- Validates each phase before proceeding

**With disciplined execution, the codebase can reach the documented target architecture within 12-18 months**, positioning RentSecure for scalable growth over the next 10-20 years.

---

*End of Comprehensive Architecture Analysis*
