# RentSecureBE — Architecture Baseline v1

**Status:** READ-ONLY AUDIT — NO CODE MODIFIED
**Date:** 2026-07-18
**Scope:** Complete repository architecture audit
**Purpose:** Reference point for all future architecture work

---

## Executive Summary

RentSecureBE is a Django + DRF modular monolith with 9 Django apps plus a project configuration layer (`rentsecure_be`). The system has:

- 1322 passing tests, 3 skipped, 0 failing
- 29 GitHub Actions workflow files (comprehensive CI/CD)
- Comprehensive existing architecture documentation
- `import-linter.ini` enforcing a layered architecture

However, the actual codebase exhibits **significant architectural debt** relative to its declared layered architecture. This baseline documents the **current state** without recommending fixes.

---

## 1. Facts

### 1.1 Repository Structure

| Directory/File | Purpose |
|---|---|
| `core/` | Identity & Access Management, Subscriptions, Bank Details, OTP, Passwords, Owner Reporting, Webhooks |
| `properties/` | Property Management (Buildings, Units, Renters, Caretakers, Rent Records, Extra Charges, Tax Records) |
| `finance/` | CA Profiles, Tax Submissions |
| `notification/` | In-App Notifications, Push (FCM/Expo), WhatsApp, SMS, Voice |
| `documents/` | PDF Generation (Agreements, Dossiers, Receipts, History) |
| `smartbot/` | Chatbot (Rule + OpenAI), AI Alerts, Actions, Leegality E-Signature, WhatsApp Agreement Delivery |
| `referral_and_earn/` | Referral Codes, Bonus Tracking |
| `ai_assistant/` | AI Insights, Analytics, Chat, WhatsApp Webhook, Invoice Generation, Archiving |
| `dashboard/` | Agreement Status, Signature Retry (SSR) |
| `rentsecure_be/` | Project Config, Settings, URLs, Payment Adapters (Cashfree, Razorpay), i18n, Leegality, Export Utils |
| `shared/` | Shared Kernel (exceptions, types, utils, validators, interfaces, domain events, constants) |
| `management/commands/` | 15 root-level management commands |
| `tools/` | 7 project tooling scripts |
| `tests/` | Root-level integration, hypothesis, contract, architecture tests |

### 1.2 Django Apps

**INSTALLED_APPS** (from `rentsecure_be/settings.py:117-138`):
```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "simple_history",
    "fcm_django",
    "django_celery_beat",
    "core",
    "notification",
    "properties",
    "finance",
    "referral_and_earn",
    "documents",
    "smartbot",
    "django_extensions",
]
```

**Critical Finding:** `ai_assistant` and `dashboard` are **NOT** in `INSTALLED_APPS`. They are dead code from a Django perspective.

### 1.3 Per-App Responsibilities

#### core
- **Models:** User, UserProfile, OTP, OwnerBankDetails, SubscriptionPlan, UserSubscription, AddOnPurchase, PlanFeatureLimit, UsageLimit, NotificationPreference, UpsertMixin
- **Views:** OTP (send/verify), Password (change/reset), Subscription CRUD, Bank Details, Owner Reporting (inflow summary, rent records, Excel download), Cashfree webhook, Razorpay webhook, Create Rent Payment
- **Services:** AuthService, BankDetailsService, OTPService, PasswordService, OwnerReportingService, ReferralService, SubscriptionService, UsageLimitService
- **Size:** 566 lines in views.py (god view)

#### properties
- **Models:** Building, Unit, UnitVacancy, UnitDocument, UnitImage, Renter, RentReminderLog, AgreementRevocationLog, ArchivedRenter, RentAgreementDraft, PoliceVerification, RentRecord, ExtraCharge, PropertyTaxRecord, CareTaker, CareTakerAssignmentLog
- **Views:** 10 view modules (building, unit, renter, rent_record, caretaker, property, subscription, extra_charge, owner_dashboard, usage_limit)
- **Services:** 10 service files (building, unit, renter, rent, occupancy, vacancy, receipt, extra_charge, summary, renter_onboarding)
- **Repositories:** 4 repository files (building, unit, renter, rent_record)
- **Policies:** unit_policy.py
- **Signals:** renter_signals.py
- **Cron:** flag_defaulters, vacate_reminder
- **Communication:** auto_generate_rent_records, retry_failed_payouts
- **Management:** 2 commands (generate_monthly_extra_charges, send_monthly_rent_summary)
- **Other:** feature_enforcer.py (195 lines), constants.py, scheduler.py

#### finance
- **Models:** CAProfile, TaxSubmissionToCA
- **Views:** CAProfileViewSet, TaxSubmissionToCAViewSet, DownloadTaxFilesView
- **Serializers:** CAProfileSerializer, TaxSubmissionToCASerializer
- **Utils:** generate_tax_excel, generate_tax_pdf, create_tax_zip

#### notification
- **Models:** Notification, DeviceToken
- **Views:** get_notifications, mark_notification_read, save_device_token, register_fcm_token
- **Services:** notifications.py, rent_notify_service.py, communication.py, sms_service.py, whatsapp_service.py, voice_service.py, voice_note_service.py, schedule_reminders.py, extra_charge_reminders.py, late_fees_notify_service.py
- **Utils:** send_push_notification, send_whatsapp_message
- **Management:** send_extra_charge_reminders

#### documents
- **Views:** GenerateRentAgreementPdfViewSet, GenerateUnitDossierPdfViewSet, GenerateRentReceiptPdfViewSet, download_unit_history
- **Utils:** generate_unit_history_pdf, _merge_pdfs, etc.
- **Templates:** rent_agreement.html, property_dossier.html, rent_recept.html

#### smartbot
- **Models:** SmartBotChat, SmartBotMessage, AIAlert
- **Views:** smart_bot_reply
- **Actions:** send_rent_reminder, retry_payout, send_rent_agreement, send_agreement_for_signature
- **Services:** chatbot_service, agreement_service, gpt_services, leegality_service, services
- **Cron:** reminders
- **Tasks:** tasks.py
- **WhatsApp:** whatsapp_service.py (thin wrapper)

#### referral_and_earn
- **Models:** Referral
- **Signals:** create_referral post_save
- **No views, no services**

#### ai_assistant
- **Models:** Empty placeholder
- **Views:** ai_assistant_insights, rent_analytics_data, financial_health_report, chat_with_assistant, whatsapp_webhook
- **Services:** finance_ai, invoice_service, i18n_service, unit_service, archive_service
- **Receivers:** receivers.py
- **Status:** NOT in INSTALLED_APPS (dead code)

#### dashboard
- **Views:** agreement_status_view, retry_signature (21 lines total)
- **Status:** NOT in INSTALLED_APPS (dead code)

#### rentsecure_be (project config)
- **Settings:** settings.py (302 lines)
- **URLs:** urls.py
- **Services:** cashfree_service.py, i18n_service.py, leegality_service.py, razorpay_service.py
- **Utils:** cashfree_payout.py, export_utils.py
- **Types:** types.py, type_compat.py

#### shared (shared kernel)
- **Files:** constants.py, domain_events.py, enums.py, exceptions.py, interfaces.py, types.py, utils.py, validators.py
- **Issues:** Naming conflicts, underutilization, missing shared utilities that are duplicated elsewhere

### 1.4 Model Ownership

| Model | App | Location | Notes |
|---|---|---|---|
| User | core | core/models.py:51 | AUTH_USER_MODEL |
| UserProfile | core | core/models.py:66 | OneToOne with User |
| OTP | core | core/models.py:96 | |
| OwnerBankDetails | core | core/models.py:108 | Financial entity — misplaced |
| SubscriptionPlan | core | core/models.py:124 | |
| UserSubscription | core | core/models.py:148 | |
| AddOnPurchase | core | core/models.py:177 | |
| PlanFeatureLimit | core | core/models.py:202 | |
| UsageLimit | core | core/models.py:221 | |
| NotificationPreference | core | core/models.py:77 | Notification concern — misplaced |
| Building | properties | properties/models/building_models.py | |
| Unit | properties | properties/models/unit_models.py | 482 lines |
| UnitVacancy | properties | properties/models/unit_models.py | |
| UnitDocument | properties | properties/models/unit_models.py | |
| UnitImage | properties | properties/models/unit_models.py | |
| Renter | properties | properties/models/renter_models.py | 286 lines |
| RentReminderLog | properties | properties/models/renter_models.py | |
| AgreementRevocationLog | properties | properties/models/renter_models.py | |
| ArchivedRenter | properties | properties/models/renter_models.py | |
| RentAgreementDraft | properties | properties/models/renter_models.py | |
| PoliceVerification | properties | properties/models/renter_models.py | |
| RentRecord | properties | properties/models/rent_record_models.py | Has payment fields |
| ExtraCharge | properties | properties/models/extra_charge_models.py | Financial transaction — misplaced |
| PropertyTaxRecord | properties | properties/models/property_tax_models.py | Financial record — misplaced |
| CareTaker | properties | properties/models/caretaker_models.py | |
| CareTakerAssignmentLog | properties | properties/models/caretaker_models.py | |
| CAProfile | finance | finance/models.py | |
| TaxSubmissionToCA | finance | finance/models.py | |
| Notification | notification | notification/models.py | |
| DeviceToken | notification | notification/models.py | |
| SmartBotChat | smartbot | smartbot/models.py | |
| SmartBotMessage | smartbot | smartbot/models.py | |
| AIAlert | smartbot | smartbot/models.py | |
| Referral | referral_and_earn | referral_and_earn/models.py | |

### 1.5 Declared Architecture (import-linter.ini)

The `import-linter.ini` enforces a **strict layered architecture** where each app can only import from `rentsecure_be` (and itself):

```
core → rentsecure_be (allowed)
properties → rentsecure_be (allowed)
smartbot → rentsecure_be (allowed)
finance → rentsecure_be (allowed)
notification → rentsecure_be (allowed)
documents → rentsecure_be (allowed)
referral_and_earn → rentsecure_be (allowed)
ai_assistant → rentsecure_be (allowed)
dashboard → rentsecure_be (allowed)
```

**No app is allowed to import from another app directly.** All inter-app communication must go through `rentsecure_be`.

### 1.6 Actual Cross-App Imports

**Total cross-app imports (non-test source files): 145**

| Source App | Target App | Import Count | Severity |
|---|---|---|---|
| core | notification | 1 | HIGH |
| core | properties | 8 | HIGH |
| core | rentsecure_be | 6 | MEDIUM |
| core | referral_and_earn | 1 | HIGH |
| properties | core | 10 | LOW (required) |
| properties | rentsecure_be | 25 | HIGH |
| properties | notification | 12 | HIGH |
| finance | core | 1 | MEDIUM |
| finance | properties | 2 | HIGH |
| finance | rentsecure_be | 2 | MEDIUM |
| notification | properties | 4 | HIGH |
| notification | rentsecure_be | 4 | HIGH |
| documents | core | 1 | MEDIUM |
| documents | properties | 3 | HIGH |
| smartbot | notification | 3 | HIGH |
| smartbot | properties | 6 | HIGH |
| smartbot | rentsecure_be | 1 | HIGH |
| ai_assistant | core | 1 | MEDIUM |
| ai_assistant | notification | 1 | HIGH |
| ai_assistant | properties | 7 | HIGH |
| ai_assistant | smartbot | 1 | HIGH |
| dashboard | properties | 1 | HIGH |
| dashboard | smartbot | 1 | HIGH |
| referral_and_earn | rentsecure_be | 2 | MEDIUM |
| rentsecure_be | core | 5 | MEDIUM |
| rentsecure_be | properties | 2 | MEDIUM |
| rentsecure_be | notification | 3 | MEDIUM |

### 1.7 Circular Dependencies

4 circular dependency cycles detected:

1. **core ↔ properties**
   - core → properties: `core/views.py`, `core/services/owner_reporting_service.py`, `core/services/bank_details_service.py`
   - properties → core: `properties/views/unit_views.py`, `properties/views/rent_record_views.py`, `properties/views/renter_views.py`, `properties/services/unit_service.py`, `properties/models/unit_models.py`, `properties/models/renter_models.py`, `properties/models/building_models.py`

2. **core ↔ rentsecure_be**
   - core → rentsecure_be: `core/views.py`, `core/serializers.py`, `core/models.py`, `core/apps.py`, `core/services/bank_details_service.py`
   - rentsecure_be → core: `rentsecure_be/services/cashfree_service.py`

3. **properties ↔ notification**
   - properties → notification: `properties/views/rent_record_views.py`, `properties/views/property_views.py`, `properties/services/summary_service.py`, `properties/services/renter_onboarding_service.py`, `properties/utils/utils.py`, `properties/signals/__init__.py`, `properties/scheduler.py`, `properties/cron/vacate_reminder.py`
   - notification → properties: `notification/services/schedule_reminders.py`, `notification/services/voice_note_service.py`, `notification/services/extra_charge_reminders.py`

4. **properties ↔ rentsecure_be**
   - properties → rentsecure_be: 25+ files across views, serializers, models, services, communication, cron, management commands, apps.py
   - rentsecure_be → properties: `rentsecure_be/services/cashfree_service.py`, `rentsecure_be/utils/export_utils.py`

### 1.8 Infrastructure Boundary Violations

**`rentsecure_be`** is the project configuration / infrastructure layer. Other apps importing from it violate the modular monolith boundary.

**Total violations: 41 imports across 17 files**

| Source App | Import Count | Key Violations |
|---|---|---|
| properties | 25 | type_compat, cashfree_service, razorpay_service, leegality_service |
| core | 6 | type_compat, cashfree_service, export_utils |
| management | 7 | type_compat, cashfree_service |
| notification | 4 | i18n_service |
| finance | 2 | type_compat |
| smartbot | 1 | cashfree_service |
| referral_and_earn | 2 | type_compat |

### 1.9 Duplicated Code

#### Exact Duplicates
| Function | Location 1 | Location 2 |
|---|---|---|
| `translate_msg` | `rentsecure_be/services/i18n_service.py:4` | `ai_assistant/services/i18n_service.py:6` |
| `send_push_notification` | `notification/services/notifications.py:13` | `notification/utils.py:14` |
| `send_whatsapp_message` | `notification/services/whatsapp_service.py:20` | `notification/utils.py:20` |
| `generate_agreement_pdf` | `smartbot/services/agreement_service.py:9` | `documents/views.py` (inline) |
| `update_unit_status` | `properties/services/unit_service.py:171` | `ai_assistant/services/unit_service.py:8` |
| Leegality e-signature | `rentsecure_be/services/leegality_service.py` | `smartbot/services/leegality_service.py` |

#### Duplicate Validators
| Validator | Locations |
|---|---|
| `phone_regex` | `properties/models/unit_models.py:26`, `properties/models/renter_models.py:18`, `properties/models/caretaker_models.py:10` |

#### Duplicate Constants
| Constant | Locations |
|---|---|
| `PAYMENT_STATUS_CHOICES` | `properties/constants.py:21`, `properties/models/rent_record_models.py` (Status.TextChoices) |
| `UNIT_STATUS_CHOICES` | `properties/constants.py:28`, `properties/models/unit_models.py` (VacancyStatus.TextChoices) |
| `RENT_REMINDER_DAYS_BEFORE` | `properties/constants.py:38` (value=3), `core/models.py` UserSubscription (default=7) |

### 1.10 God Modules

| Module | Issue |
|---|---|
| `core/views.py` (566 lines) | Handles auth, OTP, password, subscription CRUD, bank details, owner reporting, 2 webhooks, rent payment creation |
| `properties/models/unit_models.py` (482 lines) | Contains Unit, UnitVacancy, UnitDocument, UnitImage + extensive business logic |
| `notification/services/rent_notify_service.py` (168 lines) | Handles renter notification, owner notification, payout notification, owner post-payout notification |
| `properties/feature_enforcer.py` (195 lines) | Subscription enforcement logic scattered in properties app |
| `properties/services/unit_service.py` (267 lines) | Mix of service functions, analytics, and unit status management |
| `core/services/` (8 service files) | Too many responsibilities for identity/subscription app |
| `properties/services/` (10 service files) | Mix of implemented and stub services |
| `notification/services/` (9 service files) | Notification app has too many channel-specific files |

### 1.11 Root-Level Management Commands

15 management commands at project root that should be in respective apps:

| Command | Likely App Owner |
|---|---|
| `apply_late_fees.py` | properties |
| `archive_expired_users_data.py` | core or properties |
| `auto_deactivate_renters.py` | properties |
| `check_vacant_units.py` | properties |
| `daily_rent_reminder.py` | properties/notification |
| `downgrade_expired_users.py` | core |
| `generate_monthly_rent_records.py` | properties |
| `monthly_whatsapp_and_email_summary_to_owner.py` | notification |
| `rent_reminder_service.py` | notification |
| `retry_failed_payouts.py` | finance |
| `seed_subscription_plans.py` | core |
| `send_monthly_rent_summary.py` | properties/notification |
| `send_rent_reminders.py` | notification |
| `send_tax_reminders.py` | finance |

Some commands also exist inside their respective apps:
- `properties/management/commands/generate_monthly_extra_charges.py`
- `properties/management/commands/send_monthly_rent_summary.py`
- `notification/management/commands/send_extra_charge_reminders.py`

This creates **duplicate management commands** at both root and app level.

### 1.12 Shared Kernel State

| File | Content | Usage |
|---|---|---|
| `shared/constants.py` | DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, DEFAULT_TIMEOUT_SECONDS, EMPTY_STRING | Underused |
| `shared/domain_events.py` | BaseDomainEvent, EventMetadata | Unused |
| `shared/enums.py` | EmptyEnum placeholder | Unused |
| `shared/exceptions.py` | BaseDomainError, ValidationError, BusinessRuleViolationError, ExternalServiceError, ConfigurationError | Used by core, smartbot |
| `shared/interfaces.py` | Repository, Service, EventBus protocols | Defined but not used |
| `shared/types.py` | ValidationError (dict type alias), build_validation_error | Conflicts with exceptions.py |
| `shared/utils.py` | to_bool, sanitize_phone | Partially used |
| `shared/validators.py` | validate_non_empty_string, validate_positive_number | Used by shared/utils.py only |

### 1.13 CI/CD State

- **29 GitHub Actions workflow files** in `.github/workflows/`
- Pipeline stages: Lint → Test (4 shards) → Shard Validation → Contract Tests → Django Check → Architecture → UML → UML Validation → Security → Mutation → Hypothesis → Quality → Deploy Readiness → Deploy
- Architecture compliance report shows **100/100 (COMPLIANT)** — but this refers to the CI pipeline architecture, not the application architecture
- The `architecture.yml` workflow validates the `import-linter.ini` rules, but the actual codebase has 145+ violations

---

## 2. Observations

### 2.1 Bounded Context Mismatch

The declared bounded contexts (from architecture documentation) do not match the actual code organization:

| Bounded Context | Declared App(s) | Actual Reality |
|---|---|---|
| Identity & Access | core | core also owns subscriptions, bank details, webhooks, reporting |
| Subscription & Billing | core | Properties app has its own feature_enforcer and usage limits |
| Property Management | properties | Also owns tax records, extra charges, documents, analytics |
| Finance & Payments | finance | Payment adapters are in rentsecure_be; webhooks are in core |
| Document Management | documents | PDF generation also in smartbot and ai_assistant |
| Notifications | notification | Business logic for when to send notifications is scattered |
| AI Assistant | ai_assistant + smartbot | ai_assistant is dead code; smartbot handles WhatsApp, PDF, payments |
| Dashboard | dashboard | dashboard is dead code; analytics in properties |

### 2.2 Dependency Flow Violations

The actual dependency flow contradicts the layered architecture:

```
Declared:   core → rentsecure_be
Actual:     core → properties → notification → rentsecure_be
            (and circular back-edges exist)
```

### 2.3 Payment Architecture Fragmentation

Payment-related code is scattered across 4 apps:
- `core/views.py`: Cashfree webhook, Razorpay webhook, create_rent_payment
- `rentsecure_be/services/cashfree_service.py`: Cashfree payout adapter
- `rentsecure_be/services/razorpay_service.py`: Razorpay adapter
- `rentsecure_be/utils/cashfree_payout.py`: Cashfree API client
- `smartbot/actions.py`: retry_payout action
- `properties/communication/retry_failed_payouts.py`: Retry logic
- `core/models.py`: OwnerBankDetails model

### 2.4 Notification Architecture Fragmentation

Notification delivery is accessed directly by multiple apps:
- `core/views.py` → `notification.services.rent_notify_service`
- `properties/signals/__init__.py` → `notification.models`, `notification.services.voice_note_service`, `notification.services.services`, `notification.services.whatsapp_service`
- `properties/services/summary_service.py` → `notification.services.whatsapp_service`
- `smartbot/actions.py` → `notification.utils`
- `smartbot/whatsapp_service.py` → `notification.utils`
- `smartbot/cron/reminders.py` → `notification.services.whatsapp_service`
- `notification/services/rent_notify_service.py` → `rentsecure_be.services.i18n_service`

### 2.5 PDF Generation Fragmentation

PDF generation logic exists in 3 apps:
- `documents/views.py`: Rent agreement, unit dossier, rent receipt, unit history
- `smartbot/services/agreement_service.py`: Rent agreement PDF
- `ai_assistant/services/invoice_service.py`: Final invoice PDF

### 2.6 i18n Fragmentation

Translation service is duplicated:
- `rentsecure_be/services/i18n_service.py`
- `ai_assistant/services/i18n_service.py`

### 2.7 Shared Kernel Underutilization

The `shared/` directory contains well-defined abstractions (interfaces, domain events, protocols) that are **never used** in the actual codebase. The shared kernel is effectively a documentation artifact.

### 2.8 Dead Code

- `ai_assistant` app: NOT in INSTALLED_APPS, has models (empty), views, services, receivers, admin
- `dashboard` app: NOT in INSTALLED_APPS, has views, urls, tests
- `properties/models/subscription_models.py`: Placeholder with `__all__ = []`
- `shared/enums.py`: EmptyEnum placeholder
- `shared/domain_events.py`: Defined but never imported
- `shared/interfaces.py`: Defined but never used as type hints

### 2.9 Naming Conflicts in Shared Kernel

- `shared/exceptions.py` defines `ValidationError` as a class (extends `BaseDomainError`)
- `shared/types.py` defines `ValidationError` as `dict[str, list[str]]`

This creates ambiguous imports: `from shared.exceptions import ValidationError` vs `from shared.types import ValidationError`.

### 2.10 Inconsistent Constants

| Constant | Value in properties/constants.py | Value in core/models.py |
|---|---|---|
| RENT_REMINDER_DAYS_BEFORE | 3 | 7 |

---

## 3. Risks

### 3.1 Critical Risks

| Risk | Evidence | Impact |
|---|---|---|
| Cross-app circular dependencies | 4 cycles detected (core↔properties, core↔rentsecure_be, properties↔notification, properties↔rentsecure_be) | Import errors during startup, fragile refactoring |
| Payment logic scattered across 4 apps | core/views.py, rentsecure_be/services/, smartbot/actions.py, properties/communication/ | Inconsistent behavior, hard to debug payment failures |
| ai_assistant and dashboard not in INSTALLED_APPS | rentsecure_be/settings.py:117-138 | Dead code, misleading architecture docs |
| type_compat in rentsecure_be | Imported by 20+ files across 6 apps | Unnecessary infrastructure boundary violations |
| 145 cross-app import violations | cross_app_import_analysis.md | Direct violation of declared architecture |

### 3.2 High Risks

| Risk | Evidence | Impact |
|---|---|---|
| core/views.py god view (566 lines) | core/views.py | Hard to maintain, test, extend |
| Notification business logic in notification app | notification/services/rent_notify_service.py, extra_charge_reminders.py, late_fees_notify_service.py | Violates single responsibility |
| Duplicate PDF generation | smartbot/services/agreement_service.py, documents/views.py, ai_assistant/services/invoice_service.py | Inconsistent output, maintenance burden |
| Duplicate i18n service | rentsecure_be/services/i18n_service.py, ai_assistant/services/i18n_service.py | Inconsistent translations |
| Root management commands | management/commands/ (15 files) | Unclear ownership, hard to discover |
| Phone regex duplicated 3x | properties/models/unit_models.py, renter_models.py, caretaker_models.py | Maintenance burden |

### 3.3 Medium Risks

| Risk | Evidence | Impact |
|---|---|---|
| OwnerBankDetails in core | core/models.py:108 | Financial entity in identity app |
| NotificationPreference in core | core/models.py:77 | Notification concern in identity app |
| PropertyTaxRecord in properties | properties/models/property_tax_models.py | Financial record in property app |
| ExtraCharge in properties | properties/models/extra_charge_models.py | Financial transaction in property app |
| smartbot/whatsapp_service.py thin wrapper | smartbot/whatsapp_service.py | Parallel notification path |
| Shared kernel unused | shared/interfaces.py, shared/domain_events.py | Architectural documentation only |
| ai_assistant imports from smartbot | ai_assistant/views.py:28 | Cross-app coupling in dead code |

---

## 4. Assumptions

1. **The 1322 passing tests accurately reflect the current behavior.** No tests were modified or re-run during this audit.
2. **The existing architecture documentation** (architecture-analysis-report.md, etc.) accurately describes the intended architecture, even if the code does not match.
3. **Dead code (ai_assistant, dashboard)** is intentionally not in INSTALLED_APPS and may be activated in the future.
4. **Circular dependencies are currently working** because Python's import system and Django's app registry handle them, but they create fragility.
5. **The import-linter.ini is not enforced in CI** — the architecture-compliance-report shows 0 violations, suggesting the linter may not be running or is configured to ignore violations.
6. **Feature flags (ENABLE_RAZORPAY, ENABLE_CASHFREE, etc.)** are correctly configured and tested elsewhere.

---

## 5. Architecture Scores

### 5.1 Architecture Baseline Score: 42/100

**Rationale:** The declared architecture (layered modular monolith) is significantly violated. 145 cross-app imports, 4 circular dependency cycles, and 41 infrastructure boundary violations indicate the baseline architecture is not enforced in practice.

### 5.2 Maintainability Score: 55/100

**Rationale:** The codebase has good test coverage (1322 tests), comprehensive CI/CD, and follows Django conventions in many places. However, the god view (core/views.py), scattered business logic, and cross-app coupling reduce maintainability.

### 5.3 Coupling Score: 25/100

**Rationale:** Extremely high coupling. 145 cross-app imports, 4 circular dependency cycles, and apps depending on infrastructure services from `rentsecure_be` directly. The `type_compat` shim alone creates 20+ unnecessary cross-app dependencies.

### 5.4 Cohesion Score: 60/100

**Rationale:** Most apps have reasonably cohesive model ownership (e.g., properties owns buildings, units, renters). However, `core` has low cohesion (auth + subscriptions + bank details + webhooks + reporting), and `properties` has mixed cohesion (property management + finance + documents + analytics).

### 5.5 Scalability Score: 40/100

**Rationale:** The modular monolith structure is a good starting point, but the cross-app coupling and scattered payment/notification logic make it difficult to extract services or scale horizontally. The lack of clear bounded context boundaries prevents independent deployment.

### 5.6 Testability Score: 80/100

**Rationale:** 1322 passing tests with 90%+ coverage, hypothesis testing, contract tests, mutation testing, and comprehensive CI/CD. The test infrastructure is excellent.

### 5.7 Modularity Score: 35/100

**Rationale:** Despite being structured as a modular monolith, the apps are not truly modular. Cross-app imports, circular dependencies, and misplaced models prevent clean modularity. The `import-linter.ini` declares modularity, but the code does not enforce it.

### 5.8 Technical Debt Score: 65/100

**Rationale:** Significant technical debt from:
- Duplicated code (i18n, PDF generation, WhatsApp messaging, phone regex)
- Misplaced models (OwnerBankDetails, NotificationPreference, PropertyTaxRecord, ExtraCharge)
- Scattered payment infrastructure
- Dead code (ai_assistant, dashboard)
- Root-level management commands
- Circular dependencies

However, the debt is manageable because:
- Tests are comprehensive
- CI/CD is stable
- Documentation is thorough
- No failing tests

---

## 6. Architecture Baseline v1 — Reference Diagram

### 6.1 Declared Architecture (import-linter.ini)

```
rentsecure_be (project config)
    ↑
    ├── core
    ├── properties
    ├── smartbot
    ├── finance
    ├── notification
    ├── documents
    ├── referral_and_earn
    ├── ai_assistant
    └── dashboard
```

### 6.2 Actual Architecture (Current State)

```
rentsecure_be (project config + payment adapters + i18n + export)
    ↑ ↑ ↑ ↑ ↑ ↑ ↑
    │ │ │ │ │ │ └── dashboard (DEAD CODE)
    │ │ │ │ │ └── ai_assistant (DEAD CODE)
    │ │ │ │ └── referral_and_earn
    │ │ │ └── documents
    │ │ └── notification
    │ └── smartbot
    └── finance

core (identity + subscriptions + bank details + webhooks + reporting)
    ↑ ↑ ↑ ↑
    │ │ │ └── referral_and_earn
    │ │ └── rentsecure_be (type_compat, cashfree, export_utils)
    │ └── notification (rent_notify_service)
    └── properties (RentRecord)

properties (buildings + units + renters + rent records + tax + extra charges + analytics)
    ↑ ↑ ↑ ↑
    │ │ │ └── rentsecure_be (type_compat, cashfree, razorpay, leegality)
    │ │ └── notification (whatsapp, voice, schedule_reminders)
    │ └── core (User, subscription models)
    └── notification (rent_notify_service, Notification model)

notification (push + whatsapp + sms + voice + email)
    ↑ ↑
    │ └── rentsecure_be (i18n_service)
    └── properties (RentRecord, PropertyTaxRecord, ExtraCharge, RentReminderLog)

smartbot (chatbot + actions + leegality + whatsapp)
    ↑ ↑ ↑
    │ │ └── rentsecure_be (cashfree_service)
    │ └── notification (utils, whatsapp_service)
    └── properties (Renter, RentRecord, RentAgreementDraft)

finance (CA + tax submissions)
    ↑ ↑
    │ └── rentsecure_be (type_compat)
    └── properties (Unit)

documents (PDF generation)
    ↑ ↑
    │ └── properties (Renter, RentRecord, Unit)
    └── core (User)
```

### 6.3 Circular Dependency Map

```
core ←→ properties
core ←→ rentsecure_be
properties ←→ notification
properties ←→ rentsecure_be
```

---

## 7. Detailed Issue Register

### 7.1 Critical Issues

| # | Issue | App | File | Line | Type | Severity |
|---|---|---|---|---|---|---|
| 1 | `ai_assistant` and `dashboard` NOT in INSTALLED_APPS | rentsecure_be | settings.py | 117-138 | Architecture | Critical |
| 2 | 145 cross-app import violations against layered architecture | Multiple | Multiple | Multiple | Architecture | Critical |
| 3 | 4 circular dependency cycles | Multiple | Multiple | Multiple | Architecture | Critical |
| 4 | Payment webhooks in `core/views.py` (566-line god view) | core | views.py | 298, 347, 394 | Design | Critical |
| 5 | `OwnerBankDetails` model in `core/models.py` | core | models.py | 108 | Architecture | Critical |
| 6 | `NotificationPreference` model in `core/models.py` | core | models.py | 77 | Architecture | Critical |

### 7.2 High Issues

| # | Issue | App | File | Line | Type | Severity |
|---|---|---|---|---|---|---|
| 7 | `type_compat.py` in `rentsecure_be` imported by 20+ files across 6 apps | rentsecure_be | type_compat.py | 1-23 | Architecture | High |
| 8 | Payment services accessed directly by multiple apps | rentsecure_be | services/cashfree_service.py, services/razorpay_service.py | Multiple | Architecture | High |
| 9 | `properties/models/property_tax_models.py` — `PropertyTaxRecord` in wrong app | properties | property_tax_models.py | 10-25 | Architecture | High |
| 10 | `properties/models/extra_charge_models.py` — `ExtraCharge` in wrong app | properties | extra_charge_models.py | 14-67 | Architecture | High |
| 11 | `smartbot/whatsapp_service.py` — thin wrapper bypassing notification app | smartbot | whatsapp_service.py | 1-20 | Design | High |
| 12 | Duplicate `translate_msg` in rentsecure_be and ai_assistant | rentsecure_be, ai_assistant | services/i18n_service.py | Multiple | Code Organization | High |
| 13 | Duplicate `generate_agreement_pdf` in smartbot and documents | smartbot, documents | services/agreement_service.py, views.py | Multiple | Code Organization | High |
| 14 | Duplicate `update_unit_status` in properties and ai_assistant | properties, ai_assistant | services/unit_service.py | 171, 8 | Code Organization | High |
| 15 | `core/services/referral_service.py` imports from `referral_and_earn` | core | services/referral_service.py | 23 | Architecture | High |
| 16 | `properties/views/rent_record_views.py` imports from notification | properties | views/rent_record_views.py | 18-19 | Architecture | High |
| 17 | `smartbot/actions.py` imports from notification, properties, rentsecure_be | smartbot | actions.py | 5-7 | Architecture | High |
| 18 | `rentsecure_be/services/cashfree_service.py` imports from core, properties, notification | rentsecure_be | services/cashfree_service.py | 17-151 | Architecture | High |

### 7.3 Medium Issues

| # | Issue | App | File | Line | Type | Severity |
|---|---|---|---|---|---|---|
| 19 | `phone_regex` duplicated 3 times in properties models | properties | models/unit_models.py, renter_models.py, caretaker_models.py | 26, 18, 10 | Code Organization | Medium |
| 20 | Root `management/commands/` has 15 commands | management | commands/ | Multiple | Code Organization | Medium |
| 21 | `shared/exceptions.py` and `shared/types.py` naming conflict | shared | exceptions.py, types.py | 13, 3 | Design | Medium |
| 22 | `shared/` interfaces and domain events unused | shared | interfaces.py, domain_events.py | Multiple | Code Organization | Medium |
| 23 | `properties/models/subscription_models.py` empty placeholder | properties | subscription_models.py | 1-7 | Code Organization | Medium |
| 24 | Inconsistent `RENT_REMINDER_DAYS_BEFORE` constants | core, properties | models.py, constants.py | 158, 38 | Code Organization | Medium |
| 25 | `rentsecure_be/services/leegality_service.py` duplicated in `smartbot` | rentsecure_be, smartbot | services/leegality_service.py | Multiple | Code Organization | Medium |
| 26 | `notification/services/notifications.py` and `notification/utils.py` duplicate `send_push_notification` | notification | services/notifications.py, utils.py | 13, 14 | Code Organization | Medium |
| 27 | `notification/services/whatsapp_service.py` and `notification/utils.py` duplicate `send_whatsapp_message` | notification | services/whatsapp_service.py, utils.py | 20 | Code Organization | Medium |

### 7.4 Low Issues

| # | Issue | App | File | Line | Type | Severity |
|---|---|---|---|---|---|---|
| 28 | `shared/constants.py` underused | shared | constants.py | 1-20 | Code Organization | Low |
| 29 | `shared/enums.py` empty placeholder | shared | enums.py | 1 | Code Organization | Low |
| 30 | `ai_assistant/models.py` empty placeholder | ai_assistant | models.py | 1 | Code Organization | Low |

---

## 8. Integration Boundaries

### 8.1 External Service Boundaries

| Service | Adapter Location | Used By | Feature Flag |
|---|---|---|---|
| Cashfree Payout | `rentsecure_be/services/cashfree_service.py` | core, properties, smartbot, management | ENABLE_CASHFREE |
| Razorpay | `rentsecure_be/services/razorpay_service.py` | core, properties | ENABLE_RAZORPAY |
| Twilio (WhatsApp/SMS/Voice) | `notification/services/` | core, smartbot, properties, management | ENABLE_WHATSAPP, ENABLE_VOICE |
| Firebase Cloud Messaging | `notification/services/notifications.py` | notification | ENABLE_PUSH_NOTIFICATION |
| OpenAI | `smartbot/services/gpt_services.py` | smartbot | ENABLE_OPENAI |
| Leegality E-Signature | `rentsecure_be/services/leegality_service.py`, `smartbot/services/leegality_service.py` | properties, smartbot | ENABLE_LEEGALITY |
| AWS S3 | `documents/` (implied) | documents | (no flag) |
| Deep Translator | `rentsecure_be/services/i18n_service.py`, `ai_assistant/services/i18n_service.py` | notification, ai_assistant | (no flag) |

### 8.2 Domain Boundaries

| Domain | Current Owner(s) | Issues |
|---|---|---|
| Identity & Access | core | Also owns subscriptions, bank details, webhooks, reporting |
| Subscription & Billing | core | Properties has its own enforcement logic |
| Property Management | properties | Also owns tax, extra charges, documents, analytics |
| Finance & Payments | finance, core, rentsecure_be, smartbot | Scattered across 4 apps |
| Document Management | documents, smartbot, ai_assistant | PDF generation in 3 apps |
| Notifications | notification | Business logic scattered; direct imports from multiple apps |
| AI Assistant | smartbot, ai_assistant | ai_assistant is dead code |
| Referral & Loyalty | referral_and_earn | Clean, no issues |
| Dashboard | dashboard | Dead code |

### 8.3 Infrastructure Boundaries

| Layer | Current Contents | Issues |
|---|---|---|
| rentsecure_be | Settings, URLs, WSGI/ASGI, payment adapters, i18n, leegality, export utils, type_compat | Should only contain config; has business services |
| shared | exceptions, types, utils, validators, interfaces, domain events, constants | Underutilized; naming conflicts; missing utilities that are duplicated |

---

## 9. Future Modularization Candidates

Based on the current state, the following modularization steps would align the codebase with its declared architecture:

### 9.1 High Priority (Reduces Coupling)

1. **Move `type_compat.py` from `rentsecure_be` to `shared/`** — eliminates 20+ infrastructure boundary violations
2. **Move payment services from `rentsecure_be` to `finance`** — cashfree_service, razorpay_service, cashfree_payout
3. **Move `i18n_service` from `rentsecure_be` to `shared/` or `notification`** — eliminates duplication
4. **Move `OwnerBankDetails` from `core` to `finance`** — financial entity in wrong app
5. **Move `NotificationPreference` from `core` to `notification`** — notification concern in wrong app
6. **Move `PropertyTaxRecord` and `ExtraCharge` from `properties` to `finance`** — financial records in wrong app
7. **Move payment webhooks from `core/views.py` to `finance/views.py`** — payment handling in wrong app

### 9.2 Medium Priority (Improves Cohesion)

8. **Consolidate notification services** — merge `notification/services/notifications.py` and `notification/utils.py`
9. **Consolidate PDF generation** — move all PDF generation to `documents` app
10. **Consolidate Leegality service** — single implementation instead of duplicate in rentsecure_be and smartbot
11. **Consolidate i18n** — single translation service
12. **Move root management commands to respective apps**
13. **Activate or remove `ai_assistant` and `dashboard`** from INSTALLED_APPS

### 9.3 Low Priority (Cleanup)

14. **Fix shared kernel naming conflicts** — resolve ValidationError naming conflict
15. **Consolidate phone regex** — move to `shared/validators.py`
16. **Fix inconsistent constants** — RENT_REMINDER_DAYS_BEFORE
17. **Remove or implement `shared/interfaces.py` and `shared/domain_events.py`**

---

## 10. Test Coverage & CI/CD State

### 10.1 Test State

- **1322 passing tests**
- **3 skipped tests**
- **0 failing tests**
- **90%+ coverage requirement** (enforced in pytest.ini)
- Hypothesis property-based testing
- Contract tests
- Architecture tests
- Mutation testing (smoke)
- Performance benchmarks
- Query count tests

### 10.2 CI/CD State

- **29 GitHub Actions workflow files**
- Pipeline stages: Lint → Test (4 shards) → Validation → Contract → Django Check → Architecture → UML → Security → Mutation → Hypothesis → Quality → Deploy Readiness → Deploy
- Architecture compliance report: **100/100 (COMPLIANT)** — refers to CI pipeline, not application architecture
- Stable documentation
- Stable CI/CD

---

## 11. Appendix: Key File Locations

### God Views
- `core/views.py` — 566 lines, 8 responsibilities

### God Models
- `properties/models/unit_models.py` — 482 lines, 4 models + business logic
- `properties/models/renter_models.py` — 286 lines, 7 models + business logic

### Cross-App Import Hotspots
- `core/views.py` — imports from notification, properties, rentsecure_be
- `rentsecure_be/services/cashfree_service.py` — imports from core, properties, notification
- `properties/views/rent_record_views.py` — imports from notification, rentsecure_be
- `smartbot/actions.py` — imports from notification, properties, rentsecure_be
- `notification/services/rent_notify_service.py` — imports from rentsecure_be

### Duplicate Code Hotspots
- i18n: `rentsecure_be/services/i18n_service.py`, `ai_assistant/services/i18n_service.py`
- PDF: `smartbot/services/agreement_service.py`, `documents/views.py`, `ai_assistant/services/invoice_service.py`
- WhatsApp: `notification/services/whatsapp_service.py`, `notification/utils.py`, `smartbot/whatsapp_service.py`
- Push: `notification/services/notifications.py`, `notification/utils.py`

### Dead Code
- `ai_assistant/` — full app, NOT in INSTALLED_APPS
- `dashboard/` — full app, NOT in INSTALLED_APPS
- `properties/models/subscription_models.py` — empty placeholder
- `shared/enums.py` — empty placeholder
- `shared/domain_events.py` — unused
- `shared/interfaces.py` — unused

---

*End of Architecture Baseline v1*
