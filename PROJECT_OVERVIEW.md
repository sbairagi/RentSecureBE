# RentSecureBE - Property Management Backend

## Overview
RentSecureBE is a Django-based backend API for a property management SaaS platform. It enables property owners to manage their rental properties, including buildings, units, tenants, caretakers, rent collection, financial reporting, document generation, and more.

## Technology Stack
- **Framework**: Django 4.2.30 + Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT (SimpleJWT)
- **Task Scheduling**: Background scheduler for rent reminders, late fees
- **External Services**: Cashfree (payments), Razorpay, Leegality (e-signatures), WhatsApp Business API
- **CI/CD**: GitHub Actions (pytest, coverage, bandit, SonarCloud, Trivy)
- **Python**: 3.13+
- **Other**: django-simple-history, weasyprint (PDF), drf-yasg (Swagger)

## Project Structure

```
RentSecureBE/
├── core/                       # User management & subscriptions
│   ├── models.py               # User, SubscriptionPlan, UserSubscription, PlanFeatureLimit, UsageLimit, UserProfile, OTP, etc.
│   ├── views.py                # Auth views, profile, admin endpoints
│   ├── serializers.py          # User, plan, profile serializers
│   └── tests/
│       └── test_auth.py        # Model tests for core app
│
├── properties/                 # Core property management
│   ├── models/                 # Building, Unit, Renter, Caretaker, RentRecord, ExtraCharge models
│   ├── views/                  # ViewSets for all property entities
│   ├── serializers/            # DRF serializers
│   ├── feature_enforcer.py     # Subscription limit enforcement
│   ├── signals.py              # Unit status updates on renter create/delete
│   ├── scheduler.py            # Automated tasks
│   ├── admin/                  # Django admin configurations
│   └── tests/                  # ViewSet tests (building, unit, renter, caretaker, rent record)
│
├── finance/                    # Tax & financial reporting
│   ├── models.py               # CAProfile, TaxSubmissionToCA
│   ├── utils.py                # Tax Excel/PDF generation
│   └── views.py                # Tax submission API
│
├── documents/                  # Document generation
│   ├── templates/              # HTML templates for PDFs
│   ├── utils.py                # PDF generation logic
│   └── views.py                # Document download API
│
├── notification/               # Notifications
│   ├── models.py               # Notification, DeviceToken
│   ├── services/               # WhatsApp, Email, Voice, SMS integrations
│   └── views.py                # FCM registration
│
├── smartbot/                   # WhatsApp chatbot
│   ├── actions.py              # Bot action handlers
│   ├── intents.py              # NLP intent definitions
│   └── views.py                # Webhook endpoints
│
├── ai_assistant/               # AI-powered features
│   ├── services/               # FinanceAI, Invoice, Archive, Unit services
│   └── views.py                # AI assistant API
│
├── management/commands/        # Django management commands
│   ├── daily_rent_reminder.py
│   ├── apply_late_fees.py
│   ├── generate_monthly_rent_records.py
│   ├── check_vacant_units.py
│   └── monthly_whatsapp_and_email_summary_to_owner.py
│
├── dashboard/                  # Dashboard & agreement status
├── referral_and_earn/          # Referral program
└── rentsecure_be/              # Project settings & URLs
    ├── settings.py
    ├── urls.py
    └── services/               # Cashfree, Razorpay, Leegality integrations
```

## Core Business Models

### User & Subscription
```
User (AbstractUser) → UserProfile (language, whatsapp)
                    → NotificationPreference (alerts config)
                    → OwnerBankDetails (payout info)
                    → SubscriptionPlan → PlanFeatureLimit
                                       → UserSubscription
                                       → AddOnPurchase
                                       → UsageLimit
```

### Property Management
```
Building (owner) → Unit (owner, building) → Renter (unit)
                                          → Caretaker (unit)
                                          → RentRecord (unit, renter) → ExtraCharge
                                          → UnitImage
                                          → UnitDocument
                                          → RentAgreementDraft
```

### Financial
```
User → CAProfile (CA firm info)
     → TaxSubmissionToCA (yearly tax filings)
```

## API Endpoints

### Authentication (`/auth/`)
- `POST /register/` - User registration
- `POST /login/` - JWT login
- `GET /profile/` - User profile
- `POST /send-otp/`, `/verify-otp/` - Phone verification
- `POST /change-password/`, `/reset-password/`

### Properties (`/properties/`)
- `/buildings/` - CRUD for buildings
- `/units/` - CRUD for units
- `/renters/` - CRUD for renters
- `/caretakers/` - CRUD for caretakers
- `/rent-records/` - Rent payment records
- `/extra-charges/` - Additional charges
- `/unit-images/` - Unit photo uploads
- `/unit-all-documents/` - Unit document uploads
- `/rent-agreements/` - Rent agreement drafts

### Finance (`/finance/`)
- `/tax-submissions/` - Tax submissions to CA
- `/tax-summary/download/` - Download tax files

### Notifications (`/notification/`)
- `/register-fcm/` - Register device for push notifications

### SmartBot (`/smartbot/`)
- Webhook endpoints for WhatsApp bot

## Business Rules
- **Phone format**: +1 (US) or +91 (India), 9-15 digits
- **Unit statuses**: vacant, occupied, rented, maintenance, archived
- **Renter statuses**: active, notice_period, revoked, deactivated
- **Payment statuses**: pending, paid, partial, overdue, late
- **Late fees**: ₹50/day, max ₹1000 or 10% of rent
- **Countries**: Only India (IN) supported

## Subscription Plans
| Feature | Free | Pro |
|---------|------|-----|
| Buildings | 1 | 10 |
| Units | 3 | 50 |
| Renters | 2 | 50 |
| Caretakers | 2 | 10 |
| Unit Images | 3 | 10 |
| Unit Documents | 2 | 5 |
| Rent Agreement Drafts | 1 | 10 |

Grace period: 7 days after subscription expiry for paid plan features.
Grace limit: Uses free plan limits during grace period.

## Testing
Tests are located in `*/tests/` directories and use pytest with django plugin.

```bash
# Run all tests
python -m pytest properties/tests/ core/tests/ finance/tests.py notification/tests.py --ds=rentsecure_be.settings --no-cov -v

# Run with coverage
python -m pytest --ds=rentsecure_be.settings --cov=.
```

## Environment Variables
Key settings in `settings.py`:
- `DATABASE_URL` - Database connection
- `SECRET_KEY` - Django secret
- `CASHFREE_*` - Cashfree payment config
- `RAZORPAY_*` - Razorpay config
- `TWILIO_*` - SMS/Voice config
- `WHATSAPP_*` - WhatsApp API config