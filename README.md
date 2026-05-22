# RentSecureBE - Project Overview

<!-- demo: this comment is used to verify the master->main pipeline -->

## 📋 Project Summary

**RentSecureBE** is a comprehensive Django-based backend system for rental property management. It's designed to help property owners manage their buildings, units, tenants (renters), rent collection, and related financial operations.

---

## 🏗️ Project Architecture

### Technology Stack
- **Framework**: Django 4.2.30 with Django REST Framework 3.16.0
- **Authentication**: JWT (Simple JWT) with OTP-based verification
- **Database**: Configurable (SQLite for development, supports PostgreSQL/MySQL)
- **Task Queue**: Celery with django-celery-beat for scheduled tasks
- **Push Notifications**: Firebase Cloud Messaging (FCM)
- **Payment Gateways**: Razorpay, Cashfree
- **Document Signing**: Leegality API integration
- **AI/ML**: OpenAI API integration for SmartBot
- **Communication**: Twilio (WhatsApp/SMS), Email (SMTP)
- **Cloud Storage**: AWS S3, Google Cloud Storage
- **Monitoring**: Sentry SDK for error tracking

### Code Quality Tools
- **Testing**: pytest with django-test-plus, coverage reporting (90% threshold)
- **Linting**: pylint, ruff, semgrep
- **Type Checking**: mypy (strict mode)
- **Formatting**: black (88 char line length)
- **Pre-commit Hooks**: Configured

### Local pre-push hook
To ensure `pre-commit` runs before any local push, enable the repository’s hook folder once:

```bash
git config core.hooksPath .githooks
```

Then install Python dependencies and pre-commit:

```bash
python -m pip install -r requirements.txt
pre-commit install --install-hooks
```

Now every `git push` will run the configured `pre-push` hook and block the push if any hook fails.

---

## 📦 Django Applications

### 1. **Core** (`core/`)
The foundation app containing user management and subscription system.

**Models:**
- `User` - Custom user model extending AbstractUser
- `UserProfile` - Additional user preferences (WhatsApp, language)
- `NotificationPreference` - User notification settings
- `OTP` - One-time password for authentication
- `OwnerBankDetails` - Bank details for payouts
- `SubscriptionPlan` - Plan definitions (Free, Pro, Elite)
- `UserSubscription` - User's active subscription
- `AddOnPurchase` - Additional feature purchases
- `PlanFeatureLimit` - Feature limits per plan
- `UsageLimit` - Track user's feature usage

**Key Features:**
- OTP-based authentication (owner/renter flows)
- Subscription management with plan limits
- Password reset functionality
- Bank details management for payouts

---

### 2. **Properties** (`properties/`)
The main app for property and tenant management.

**Models:**
- `Building` - Physical building/property
- `Unit` - Individual rental units within buildings
- `UnitImage` / `UnitDocument` - Media files for units
- `UnitVacancy` - Tracks vacancy reasons
- `Renter` - Tenant information with KYC status
- `RentRecord` - Monthly rent payment records
- `ExtraCharge` - Additional charges (maintenance, utilities)
- `Caretaker` - Property caretaker information
- `RentAgreementDraft` - Auto-generated rental agreements
- `PoliceVerification` - Police verification records
- `ArchivedRenter` - Archived tenant data

**Key Features:**
- Building and unit management with ownership validation
- Tenant onboarding with KYC verification
- Rent collection with payment tracking
- Automatic agreement generation via Leegality
- Unit occupancy analytics
- Document and image management with deduplication
- Feature enforcement based on subscription plans

**Services:**
- `unit_service.py` - Unit status management and analytics
- `renter_onboarding_service.py` - Tenant self-onboarding
- `receipt_service.py` - Rent receipt generation
- `summary_service.py` - Owner summary reports
- `extra_charge_service.py` - Additional charge management

**Views:**
- CRUD operations for buildings, units, renters, rent records
- Owner dashboard summaries
- Rent history and payment tracking
- Payout retry operations
- Leegality webhook handling

---

### 3. **Finance** (`finance/`)
Tax and financial management module.

**Models:**
- `CAProfile` - Chartered Accountant profiles
- `TaxSubmissionToCA` - Tax submission tracking

**Key Features:**
- Tax submission to CA
- Financial year tracking
- Integration with payment gateways

---

### 4. **Notification** (`notification/`)
Notification management system.

**Models:**
- `Notification` - In-app notifications
- `DeviceToken` - Push notification device tokens

**Key Features:**
- WhatsApp notifications via Twilio
- Email notifications
- Push notifications via FCM
- Rent reminders and alerts
- Monthly summary notifications

---

### 5. **SmartBot** (`smartbot/`)
AI-powered chatbot assistant.

**Models:**
- `SmartBotChat` - Chat history
- `SmartBotMessage` - Query/response logging
- `AIAlert` - AI-generated alerts

**Key Features:**
- GPT-powered natural language responses
- Intent detection and action execution
- Rent reminder automation
- Payout retry commands
- Agreement sending via chat commands

---

### 6. **Documents** (`documents/`)
Document generation and management.

**Key Features:**
- Rent agreement PDF generation
- Property dossier creation
- Rent receipt generation
- PDF template management

---

### 7. **Referral & Earn** (`referral_and_earn/`)
Referral program management.

**Models:**
- `Referral` - Referral tracking with unique codes
- Bonus earning tracking

---

### 8. **AI Assistant** (`ai_assistant/`)
AI-powered features.

**Services:**
- `finance_ai.py` - Financial analytics
- `invoice_service.py` - Invoice generation
- `unit_service.py` - Unit analytics
- `archive_service.py` - Data archival
- `i18n_service.py` - Internationalization

---

## 🔌 API Endpoints Overview

### Authentication (`/api/auth/`)
- `POST /auth/send-otp/` - Send OTP
- `POST /auth/owner/verify-otp/` - Owner verification
- `POST /auth/renter/verify-otp/` - Renter verification
- `POST /api/token/refresh/` - Refresh JWT token
- `POST /change-password/` - Change password
- `POST /reset-password/` - Reset password

### Properties (`/api/` and `/properties/`)
- `GET/POST /buildings/` - Building management
- `GET/POST /units/` - Unit management
- `GET/POST /renters/` - Tenant management
- `GET/POST /rent-records/` - Rent payment records
- `GET/POST /extra-charges/` - Extra charge management
- `GET/POST /unit-images/` - Unit image uploads
- `GET/POST /unit-all-documents/` - Document management
- `GET/POST /rent-agreements/` - Agreement drafts

### Owner Dashboard (`/api/owner/`)
- `GET /owner/rent-records/` - Owner's rent records
- `GET /owner/rents/` - Rent overview
- `GET /owner/dashboard-summary/` - Dashboard metrics
- `GET /owner/retry_payout_api/<rent_id>/` - Retry failed payouts

### Renter APIs (`/api/renter/`)
- `GET /renter/rent-due/` - Check due rent
- `GET /renter/rent-history/` - Payment history

### Subscription (`/api/`)
- `GET/POST /subscription-plans/` - Plan management
- `GET/POST /user-subscriptions/` - User subscription
- `GET/POST /addon-purchases/` - Add-on features
- `GET/POST /usage-limits/` - Usage tracking

### Webhooks
- `POST /webhook/cashfree/payout/` - Cashfree payout webhook
- `POST /api/rent/payment-callback/` - Razorpay webhook
- `POST /leegality/webhook/` - Leegality document signing webhook

---

## 🔄 Key Business Logic

### Subscription & Feature Limits
- Plans: Free, Pro, Elite with different feature limits
- Feature keys: `max_buildings`, `max_units`, `max_renters`, `max_caretakers`, `unit_images`, `unit_documents`, `rent_agreement_drafts`
- Add-on purchases can extend limits
- Grace period of 7 days after subscription expiry

### Unit Occupancy Management
- Automatic status sync between `Unit.status` and `is_vacant`
- Signals update unit status when renters are created/updated/deleted
- Analytics endpoint provides occupancy rates per building and overall

### Rent Collection
- Monthly rent records generated automatically
- Payment links via Razorpay
- Payout to owners via Cashfree
- Late fee automation
- WhatsApp/Email reminders

### Tenant Onboarding
- Self-onboarding with secure tokens
- KYC verification workflow
- Document upload with hash-based deduplication
- Police verification integration

---

## 📁 Project Structure
```
RentSecureBE/
├── rentsecure_be/          # Main Django settings
├── core/                   # Users, subscriptions, auth
├── properties/             # Main property management
│   ├── models/             # Data models
│   ├── views/              # API endpoints
│   ├── serializers/        # Data serialization
│   ├── services/           # Business logic
│   ├── signals/            # Django signals
│   ├── permissions/        # Access control
│   └── utils/              # Helper functions
├── finance/                # Tax and financial management
├── notification/           # Notifications
├── smartbot/               # AI chatbot
├── documents/              # Document generation
├── ai_assistant/           # AI features
├── referral_and_earn/      # Referral program
├── dashboard/              # Dashboard views
├── management/commands/    # Scheduled tasks
└── tests/                  # Test suite
```

---

## 🚀 Scheduled Management Commands
- `generate_monthly_rent_records` - Create monthly rent records
- `apply_late_fees` - Apply late payment fees
- `daily_rent_reminder` - Send daily rent reminders
- `monthly_whatsapp_and_email_summary_to_owner` - Monthly summaries
- `auto_deactivate_renters` - Deactivate expired agreements
- `downgrade_expired_users` - Downgrade expired subscriptions
- `archive_expired_users_data` - Archive old data
- `check_vacant_units` - Update vacancy status

---

## 📊 Key Features Summary

1. **Multi-tenant Property Management** - Support for multiple owners, buildings, and units
2. **Subscription-based Access Control** - Feature limits based on subscription plans
3. **Automated Rent Collection** - Payment links, reminders, and payout automation
4. **Digital Agreement Signing** - Integration with Leegality for e-signatures
5. **AI-Powered Assistant** - SmartBot for natural language queries and actions
6. **Multi-channel Notifications** - WhatsApp, Email, Push notifications
7. **Comprehensive Analytics** - Occupancy rates, rent collection, financial summaries
8. **Document Management** - Secure storage with deduplication
9. **KYC Verification** - Tenant verification workflow
10. **Referral Program** - User acquisition through referrals

---

This is a production-ready rental property management system with enterprise-grade features including subscription management, payment processing, AI assistance, and comprehensive notification systems.