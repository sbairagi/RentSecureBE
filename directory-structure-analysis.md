# RentSecureBE Directory Structure Analysis

**Analysis Date:** 2026-07-14
**Project:** RentSecureBE (Django + DRF Modular Monolith)
**Analysis Type:** READ-ONLY Structural Audit

---

## Executive Summary

The RentSecureBE project contains **22 top-level directories** (excluding cache/venv/git directories). The codebase exhibits significant structural issues:

- **Duplicated bounded contexts** (`ai_assistant` duplicates `smartbot` + `dashboard`)
- **Payment services misplaced** in project configuration (`rentsecure_be/services/`)
- **Business logic scattered** across notification, smartbot, and management commands
- **Empty architecture contracts** directory despite documented boundary rules
- **Single Responsibility violations** in `core` (Identity + Subscription) and `properties` (10+ model files)
- **Shared module severely underutilized** — protocols defined but never consumed

---

## Directory-by-Directory Analysis

### 1. `.benchmarks`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Performance benchmark result storage |
| **Ownership** | DevOps / Platform |
| **Architecture Layer** | Infrastructure |
| **Bounded Context** | CI/CD & Performance |
| **Problems** | Empty directory; no benchmark artifacts present |
| **Recommended Structure** | Remove or populate with benchmark result schemas |

---

### 2. `.githooks`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Git pre-push hook for local enforcement |
| **Ownership** | DevOps / Platform |
| **Architecture Layer** | Infrastructure |
| **Bounded Context** | Development Tooling |
| **Problems** | Single hook file; no documentation on what it enforces |
| **Recommended Structure** | Keep minimal; add README explaining hook behavior |

---

### 3. `.github`

| Attribute | Value |
|-----------|-------|
| **Purpose** | GitHub Actions CI/CD workflows, custom actions, dependabot config |
| **Ownership** | DevOps / Platform |
| **Architecture Layer** | Infrastructure |
| **Bounded Context** | CI/CD & Quality Gates |
| **Problems** | **25+ workflows** indicate over-instrumentation; architecture validation, UML generation, diagram checks, and security scans all run as separate workflows, creating long CI times |
| **Recommended Structure** | Consolidate related workflows (lint + typecheck + architecture into a single `quality.yml`); move diagram generation to a scheduled workflow rather than PR-triggered |

---

### 4. `.grimp_cache`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Grimp import analysis cache for import-linter |
| **Ownership** | Platform / Architecture |
| **Architecture Layer** | Infrastructure |
| **Bounded Context** | Architecture Enforcement |
| **Problems** | Cache files should be git-ignored; contains meta.json per app |
| **Recommended Structure** | Verify `.gitignore` coverage; add to `.gitignore` if missing |

---

### 5. `ai_assistant`

| Attribute | Value |
|-----------|-------|
| **Purpose** | AI-powered assistant services (finance analysis, invoice generation, unit status, i18n, archive) |
| **Ownership** | AI / SmartBot Team |
| **Architecture Layer** | Application (Cross-Cutting) |
| **Bounded Context** | AI Assistant (overlaps with `smartbot` and `dashboard`) |

**Problems:**
- **Duplicate bounded context**: `ai_assistant/views.py` contains `ai_assistant_insights`, `rent_analytics_data`, and `financial_health_report` which duplicate `properties/views/owner_dashboard.py` and `dashboard/views.py`
- **Duplicate chat functionality**: `chat_with_assistant` view duplicates `smartbot/views.py` `smart_bot_reply`
- **Empty models file**: `ai_assistant/models.py` is a 1-line placeholder with no actual models
- **Cross-context imports**: `views.py` imports from `core.models`, `properties.models`, `smartbot.services`, `notification.services` — violates bounded context isolation
- **Not wired in root URLs**: `ai_assistant/urls.py` exists but is not included in `rentsecure_be/urls.py`
- **`finance_ai.py` contains domain logic** for financial health scoring that belongs in `finance/`
- **`unit_service.py` directly queries `Renter` model** — should go through a repository or service

**Recommended Structure:**
- Consolidate into `smartbot/` or create a dedicated `ai/` package
- Move `finance_ai.py` → `finance/services/`
- Move `unit_service.py` → `properties/services/`
- Move `invoice_service.py` → `documents/services/`
- Remove duplicate analytics views; delegate to `properties` or `dashboard`
- Wire `ai_assistant/urls.py` into root URLs or remove the app

---

### 6. `architecture`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Architecture decision records (ADRs), baseline docs, dependency rules, module boundaries, generated architecture JSON |
| **Ownership** | Architecture / Platform |
| **Architecture Layer** | Documentation |
| **Bounded Context** | Platform Governance |

**Problems:**
- **Duplicate with `docs/`**: Both `architecture/adr/` and `docs/adr/` contain ADRs; `architecture/` has `001-current-architecture.md` while `docs/adr/` has ADR-001 through ADR-036
- **Empty `contracts/` directory**: Documented in `module-boundaries.md` as where bounded context contracts should live, but completely empty
- **Generated artifacts in source tree**: `architecture/generated/architecture.json` and `docs/uml/generated/` contain generated files that should be in `build/` or `.generated/`
- **Mixed concerns**: Contains both decision records and runtime governance scripts

**Recommended Structure:**
- Keep ADRs in `docs/adr/` only; remove `architecture/adr/`
- Move `architecture/contracts/` content to actual contract definitions or remove the empty directory
- Move generated artifacts to a `.generated/` directory or `build/`
- Consolidate `architecture/` and `docs/architecture/` into a single location

---

### 7. `core`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Authentication, OTP, password management, subscriptions, bank details, usage limits, referral processing |
| **Ownership** | Identity & Subscription Team |
| **Architecture Layer** | Domain (mixed Identity + Subscription) |
| **Bounded Context** | Identity & Subscription (two contexts in one app) |

**Problems:**
- **Mixed bounded contexts**: `core/models.py` contains `User`, `UserProfile`, `OTP`, `NotificationPreference`, `OwnerBankDetails`, `SubscriptionPlan`, `UserSubscription`, `AddOnPurchase`, `PlanFeatureLimit`, `UsageLimit` — Identity and Subscription are separate bounded contexts per `module-boundaries.md`
- **Infrastructure imports**: `core/views.py` imports `rentsecure_be.services.cashfree_service` and `notification.services.rent_notify_service` — domain layer depends on infrastructure
- **Fat views**: `core/views.py` is 566 lines with OTP logic, webhook handling, bank details, subscription CRUD — violates thin-views rule
- **`services/` contains business logic** for subscription, auth, OTP, bank details, referral, usage limits, and owner reporting — 8 service files in one app
- **`utils/export_utils.py`** exists in `core/utils/` but is also duplicated in `rentsecure_be/utils/export_utils.py`

**Recommended Structure:**
- Split into `core/` (Identity) and `subscription/` (Subscription) bounded contexts
- Move `OwnerBankDetails` to `properties/` or a dedicated `payments/` module
- Move payment webhook views to `finance/` or `properties/`
- Extract `export_utils.py` to `shared/` or `documents/`
- Ensure views only orchestrate; move all business logic to services

---

### 8. `dashboard`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Agreement status HTML template and simple view for retrying signatures |
| **Ownership** | Frontend / Product |
| **Architecture Layer** | Presentation |
| **Bounded Context** | Analytics (partial) |

**Problems:**
- **Not wired in root URLs**: `dashboard/urls.py` is not included in `rentsecure_be/urls.py`
- **Duplicate analytics**: `dashboard/views.py` is a 21-line HTML renderer, but `ai_assistant/views.py` contains full JSON analytics endpoints (`rent_analytics_data`, `ai_assistant_insights`) that should live here
- **Thin app with no models/services**: Only a view, template, and tests — essentially a placeholder
- **Imports from `smartbot.actions`**: `dashboard/views.py` imports `send_agreement_for_signature` from `smartbot` — presentation layer depends on another app's actions

**Recommended Structure:**
- Wire `dashboard/urls.py` into `rentsecure_be/urls.py` or remove the app
- Move analytics endpoints from `ai_assistant/views.py` to `dashboard/views.py`
- Convert to a proper analytics module with serializers, services, and caching

---

### 9. `docs`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Project documentation: ADRs, business rules, RAG context, architecture docs, UML diagrams, AI governance |
| **Ownership** | Architecture / Documentation |
| **Architecture Layer** | Documentation |
| **Bounded Context** | Platform Governance |

**Problems:**
- **Massive size**: 17 subdirectories with 40+ markdown files; difficult to navigate
- **Duplicate ADRs**: `docs/adr/ADR-001.md` through `ADR-036.md` duplicate `architecture/adr/`
- **Generated artifacts in docs**: `docs/uml/generated/`, `docs/diagrams/generated/`, `docs/history/generated/` contain generated files that belong in `build/` or CI artifacts
- **RAG docs mix internal and external**: `docs/rag/` contains both internal API docs and external integration docs (payments-razorpay-cashfree.md)
- **AI governance docs in `docs/ai-governance/`** should probably be in a dedicated `governance/` directory

**Recommended Structure:**
- Consolidate ADRs into `docs/adr/` only; remove duplicate `architecture/adr/`
- Move generated UML/diagrams to CI artifacts or `build/`
- Split `docs/rag/` into internal API docs and external integration docs
- Consider a top-level `governance/` directory for AI governance docs

---

### 10. `documents`

| Attribute | Value |
|-----------|-------|
| **Purpose** | PDF generation (rent receipts, agreements, property dossiers, tax summaries), document templates, utilities |
| **Ownership** | Documents Team |
| **Architecture Layer** | Application |
| **Bounded Context** | Documents |

**Problems:**
- **Templates inside app**: `documents/templates/pdf_templates/` contains HTML templates for WeasyPrint; acceptable but could conflict with global template dirs
- **Static PDFs in `properties/static/`**: `properties/static/` contains `Rent Receipt.pdf`, `Property Dossier.pdf`, `Leave and License Agreement.pdf` — these are document outputs, not static assets
- **`utils.py` contains route helpers** that could be in a dedicated routes module

**Recommended Structure:**
- Move static PDFs from `properties/static/` to `documents/output/` or `media/`
- Keep templates in `documents/templates/` but add a `documents/output/` for generated PDFs
- Extract PDF generation utilities to a dedicated `documents/generators/` package

---

### 11. `finance`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Tax management (CA profiles, tax submissions, tax summaries), financial document generation |
| **Ownership** | Finance & Compliance Team |
| **Architecture Layer** | Application |
| **Bounded Context** | Finance & Compliance |

**Problems:**
- **Payment services in wrong place**: `rentsecure_be/services/cashfree_service.py` and `razorpay_service.py` contain payment/payout logic that belongs here or in a dedicated `payments/` module
- **`finance/views.py` imports from `core.models` and `properties.models`** — acceptable for a monolith but violates the documented "no cross-context model imports" rule
- **`finance/templates/pdf_templates/`** duplicates template location pattern from `documents/`
- **No service layer**: `finance/views.py` calls `generate_tax_excel` and `generate_tax_pdf` directly from `finance/utils.py` — no service abstraction

**Recommended Structure:**
- Move payment/payout services from `rentsecure_be/` to `finance/services/`
- Add a proper service layer (`finance/services/tax_service.py`)
- Move `finance/templates/` to `documents/templates/finance/` for consistency

---

### 12. `fonts`

| Attribute | Value |
|-----------|-------|
| **Purpose** | WeasyPrint font assets (DejaVu font family) and app logo |
| **Ownership** | Documents / Frontend |
| **Architecture Layer** | Infrastructure |
| **Bounded Context** | Document Generation |

**Problems:**
- **Top-level static assets**: 22 font files and a logo PNG at the project root
- **No configuration reference**: Unclear how WeasyPrint discovers these fonts
- **Mixed asset types**: TrueType fonts and a PNG logo in the same directory

**Recommended Structure:**
- Move to `documents/assets/fonts/` or `static/fonts/`
- Add a README documenting font usage and WeasyPrint configuration

---

### 13. `management`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Global Django management commands (not app-specific) |
| **Ownership** | Platform / DevOps |
| **Architecture Layer** | Infrastructure |
| **Bounded Context** | Background Jobs |

**Problems:**
- **15 management commands** in a flat directory — violates organization by domain
- **Duplicate commands**: `send_monthly_rent_summary.py` exists in both `management/commands/` and `properties/management/commands/`
- **Duplicate rent reminder logic**: `daily_rent_reminder.py`, `rent_reminder_service.py`, and `send_rent_reminders.py` all handle rent reminders
- **Mixed domains**: `apply_late_fees.py` (properties), `send_tax_reminders.py` (finance), `retry_failed_payouts.py` (payments), `archive_expired_users_data.py` (core) all in one flat directory
- **`monthly_whatsapp_and_email_summary_to_owner.py`** contains notification logic that belongs in `notification/`

**Recommended Structure:**
- Move commands to their respective app `management/commands/` directories
- Consolidate rent reminder commands into a single `send_rent_reminders.py`
- Move notification-related commands to `notification/management/commands/`
- Move payment-related commands to `finance/management/commands/`

---

### 14. `notification`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Notification preferences, in-app notifications, FCM push, WhatsApp, voice notes, SMS (disabled), extra charge reminders, rent notifications |
| **Ownership** | Communication Team |
| **Architecture Layer** | Application (Cross-Cutting) |
| **Bounded Context** | Communication |

**Problems:**
- **Business logic embedded in services**: `extra_charge_reminders.py`, `late_fees_notify_service.py`, `rent_notify_service.py` contain domain logic (when to notify, what to say) that belongs in the domain apps (`properties`, `finance`)
- **WhatsApp service duplication**: `notification/services/whatsapp_service.py` contains `send_whatsapp_message` and `send_whatsapp_audio`, but `smartbot/whatsapp_service.py` wraps the same function with `send_agreement_via_whatsapp`
- **`notification/services/voice_note_service.py`** imports from `rentsecure_be.services.i18n_service` — notification depends on infrastructure
- **`notification/services/sms_service.py`** exists but is disabled per feature flags
- **`notification/views.py`** handles device tokens and in-app notifications — thin and acceptable
- **`notification/management/commands/send_extra_charge_reminders.py`** duplicates logic in `notification/services/extra_charge_reminders.py`

**Recommended Structure:**
- Move `extra_charge_reminders.py`, `late_fees_notify_service.py`, and `rent_notify_service.py` to their respective domain apps (`properties/services/`, `finance/services/`)
- Keep only channel adapters (`EmailAdapter`, `FCMAdapter`, `WhatsAppAdapter`, `SMSAdapter`, `VoiceAdapter`) in `notification/`
- Remove duplicate `smartbot/whatsapp_service.py`; use `notification.services.whatsapp_service` directly
- Move `send_extra_charge_reminders` management command to `properties/`

---

### 15. `properties`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Buildings, units, renters, rent records, caretakers, extra charges, property tax, subscriptions (placeholder), usage limits (placeholder), rent agreement drafts, police verification |
| **Ownership** | Property Management Team |
| **Architecture Layer** | Domain |
| **Bounded Context** | Property & Rent |

**Problems:**
- **God module**: 10 model files, 7 serializer files, 8 view files, 7 service files, 4 admin files, 2 repository files, 1 policy file, 1 scheduler, 1 cron module, 1 communication module, 1 feature enforcer, 1 constants file, 1 business rules doc, static files, templates, and tests — far exceeds single responsibility
- **Placeholder models**: `properties/models/subscription_models.py` and `properties/models/usage_limit_models.py` are empty placeholders with comments saying models live in `core/` — violates "no empty placeholder files" rule
- **Static files in app**: `properties/static/` contains 12 image files and 3 PDF files — static assets should not be in the app directory
- **Templates in app**: `properties/templates/pdf/rent_receipt.html` and `properties/templates/pdf/` — acceptable but conflicts with `documents/templates/`
- **`properties/views/owner_dashboard.py`** duplicates analytics in `ai_assistant/views.py` and `dashboard/views.py`
- **`properties/views/property_views.py`** imports `send_whatsapp_message` from `notification.services` — domain view depends on notification infrastructure
- **`properties/views/rent_record_views.py`** imports `process_rent_payout` from `rentsecure_be.services` — domain view depends on project infrastructure
- **`properties/scheduler.py`** contains cron logic that belongs in `management/commands/`
- **`properties/cron/`** contains `vacate_reminder.py` and `flag_defaulters.py` — cron logic scattered
- **`properties/communication/`** contains `auto_generate_rent_records.py` and `retry_failed_payouts.py` — these are management commands, not communication logic
- **`properties/tests/test_cashfree_service.py`** tests code in `rentsecure_be/services/` — tests should be co-located with the code under test
- **`properties/tests/test_signals.py`** mocks `notification.services.whatsapp_service` — tight coupling between domain tests and notification infrastructure

**Recommended Structure:**
- Split into sub-packages: `properties/buildings/`, `properties/units/`, `properties/renters/`, `properties/rent_records/`
- Remove placeholder model files
- Move static files to `static/` or `documents/assets/`
- Consolidate templates into `documents/templates/`
- Move scheduler/cron/communication logic to `management/commands/`
- Move payout logic to `finance/` or a dedicated `payments/` module
- Move `test_cashfree_service.py` to `rentsecure_be/tests/`

---

### 16. `referral_and_earn`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Referral codes, bonus tracking, referral rewards |
| **Ownership** | Growth / Referrals Team |
| **Architecture Layer** | Domain |
| **Bounded Context** | Growth & Referrals |

**Problems:**
- **Minimal module**: Only 4 Python files (models, admin, signals, migrations)
- **Signals in module root**: `referral_and_earn/signals.py` at app root instead of in a `signals/` package
- **No services or views**: Business logic is likely in `core/services/referral_service.py` — cross-app coupling

**Recommended Structure:**
- Move referral logic from `core/services/referral_service.py` to `referral_and_earn/services/`
- Move signals to `referral_and_earn/signals/__init__.py` package
- Add views and serializers if the app is meant to be self-contained

---

### 17. `rentsecure_be`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Django project configuration (settings, urls, wsgi, asgi) + domain services (payments, i18n, leegality) + utilities |
| **Ownership** | Platform / Infrastructure |
| **Architecture Layer** | Infrastructure (mixed with Application) |
| **Bounded Context** | Project Configuration + Payment Processing + AI Services |

**Problems:**
- **Domain services in project config**: `rentsecure_be/services/cashfree_service.py`, `razorpay_service.py`, `i18n_service.py`, `leegality_service.py` are domain-specific services that belong in `finance/`, `shared/`, and `smartbot/` respectively
- **Utilities in project config**: `rentsecure_be/utils/cashfree_payout.py` and `export_utils.py` are domain utilities
- **Settings file is 302 lines**: Contains third-party credentials (Twilio, Cashfree, Razorpay, OpenAI, Leegality, AWS) inline; should use a secrets manager or environment-specific settings files
- **`type_compat.py`** is a Python version compatibility shim — could be in `shared/`
- **`settings.py` imports `django_celery_beat`** but project docs say "NO Celery in Year 1" — contradiction
- **`CHANNEL_LAYERS` uses Redis** but docs say "NO Redis mandatory in Year 1" — contradiction
- **All apps import from `rentsecure_be` for configuration** — this is documented as the current pattern but creates a dependency on the project config

**Recommended Structure:**
- Move `services/` and `utils/` to their respective domain apps
- Split `settings.py` into `settings/base.py`, `settings/development.py`, `settings/production.py`
- Move `type_compat.py` to `shared/`
- Remove Celery-related apps from `INSTALLED_APPS` or document the exception
- Use environment variables or a secrets manager for third-party credentials

---

### 18. `scripts`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Development scripts: diagram generation, architecture validation, CI guards, security hardening, seed data, performance checks |
| **Ownership** | Platform / Architecture |
| **Architecture Layer** | Infrastructure / Tooling |
| **Bounded Context** | Development Tooling |

**Problems:**
- **Mixed concerns**: Contains both CI validation scripts (`architecture_contract.py`, `check_api_contracts.py`, `check_perf_thresholds.py`) and diagram generation scripts (`scripts/diagrams/`)
- **Diagram scripts duplicate CI workflows**: `scripts/diagrams/generate_*.py` are also triggered by `.github/workflows/uml.yml` and `architecture.yml`
- **`seed_load_test_data.py`** is a development script that should not be in production code paths
- **27 Python files** in a flat structure with one subdirectory (`diagrams/`)

**Recommended Structure:**
- Split into `scripts/ci/` (validation, guards) and `scripts/dev/` (diagrams, seed data)
- Move diagram generation to a dedicated `tools/diagrams/` or CI-only location
- Add a `Makefile` or task runner to orchestrate common script invocations

---

### 19. `shared`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generic, reusable foundations: interfaces (Repository, Service, EventBus protocols), types, validators, constants, exceptions, utilities |
| **Ownership** | Platform / Shared Libraries |
| **Architecture Layer** | Shared |
| **Bounded Context** | Cross-Cutting (Generic) |

**Problems:**
- **Severely underutilized**: Only 3 files import from `shared` (`core/services/otp_service.py`, `core/services/referral_service.py`, `core/views.py`)
- **Protocols unused**: `shared/interfaces.py` defines `Repository`, `Service`, and `EventBus` protocols but no code implements them
- **`shared/exceptions.py` defines `ValidationError`** as `dict[str, list[str]]` but other apps use Django's `ValidationError` or custom exceptions
- **`shared/validators.py`** exists but is barely used
- **`shared/constants.py`** exists but no constants are defined in it (all constants are in app-specific files)
- **`shared/types.py`** duplicates type aliases that could be in `rentsecure_be/type_compat.py`

**Recommended Structure:**
- Populate `shared/interfaces.py` with actual implementations or remove unused protocols
- Consolidate exception handling strategy across all apps
- Move `type_compat.py` from `rentsecure_be/` to `shared/`
- Add `shared/constants.py` with project-wide constants (feature flags, status codes)
- Ensure all new code uses `shared/` utilities to justify its existence

---

### 20. `smartbot`

| Attribute | Value |
|-----------|-------|
| **Purpose** | AI chatbot, smart actions (rent reminders, payouts, agreements), GPT services, Leegality e-signature integration, WhatsApp agreement delivery, cron reminders |
| **Ownership** | AI / SmartBot Team |
| **Architecture Layer** | Application (Cross-Cutting) |
| **Bounded Context** | AI Assistant |

**Problems:**
- **Actions span multiple domains**: `smartbot/actions.py` contains `send_rent_reminder` (notification), `retry_payout` (finance), `send_rent_agreement` (documents), `send_agreement_for_signature` (smartbot) — an action orchestrator should not contain domain logic
- **WhatsApp service duplication**: `smartbot/whatsapp_service.py` is a 10-line wrapper around `notification.services.whatsapp_service.send_whatsapp_message` — adds no value
- **Cron jobs in app**: `smartbot/cron/reminders.py` duplicates rent reminder logic found in `management/commands/` and `notification/services/`
- **`smartbot/views.py`** imports from `properties.models` and `smartbot.services` — mixes domain queries with AI orchestration
- **`smartbot/models.py`** has `SmartBotChat`, `SmartBotMessage`, and `AIAlert` — `SmartBotChat` and `SmartBotMessage` are duplicates; `AIAlert` should be in `notification/` or `core/`
- **`smartbot/tests.py`** at module root contains tests — should be in `smartbot/tests/`
- **`smartbot/services/leegality_service.py`** is duplicated in `rentsecure_be/services/leegality_service.py`

**Recommended Structure:**
- Move `leegality_service.py` from `rentsecure_be/services/` to `smartbot/services/` (or `documents/services/`)
- Remove `smartbot/whatsapp_service.py`; use `notification.services.whatsapp_service` directly
- Move cron/reminder logic to `notification/` or `management/commands/`
- Split `actions.py` into domain-specific action handlers
- Move `AIAlert` model to `notification/models.py`
- Remove duplicate `smartbot/tests.py`

---

### 21. `tests`

| Attribute | Value |
|-----------|-------|
| **Purpose** | Cross-cutting tests: architecture contract validation, hypothesis property-based tests, performance benchmarks, API contract tests, query count tests, load tests (Locust) |
| **Ownership** | QA / Platform |
| **Architecture Layer** | Testing |
| **Bounded Context** | Cross-Cutting (Test Infrastructure) |

**Problems:**
- **Top-level test directory**: Mixes cross-cutting tests with app-specific tests (which live in `*/tests/` subdirectories)
- **Architecture contract tests** (`test_architecture_contract/`) validate import-linter rules but the `architecture/contracts/` directory they validate is empty
- **`tests/factories.py`** contains test factories for all apps — should be in a dedicated `tests/factories/` package or each app's `tests/factories.py`
- **`tests/load/locustfile.py`** is a load test that should be in `scripts/` or a dedicated `load_tests/` directory
- **No test configuration**: `pytest.ini` exists at root but `tests/` has no `conftest.py` (the root `conftest.py` handles this)

**Recommended Structure:**
- Keep cross-cutting tests at top-level `tests/` but rename to `tests/cross_cutting/` or similar
- Move app-specific tests from top-level to each app's `tests/` (already done for most apps)
- Move `tests/load/` to `scripts/load/`
- Add `tests/factories/` package with per-app factory modules
- Ensure `architecture/contracts/` is populated or remove architecture contract tests

---

### 22. `tools`

| Attribute | Value |
|-----------|-------|
| **Purpose** | CI guards, migration guards, security guards, report generators, autofix, ship (deployment) scripts |
| **Ownership** | Platform / DevOps |
| **Architecture Layer** | Infrastructure / Tooling |
| **Bounded Context** | Development Tooling |

**Problems:**
- **Mixed tooling**: Contains both runtime tools (`ship.py`, `autofix.py`) and CI guards (`ci_guard.py`, `security_guard.py`, `migration_guard.py`)
- **`migration_rollback_validator.py`** and `migration_guard.py` should be in `scripts/` or `management/commands/`
- **`report_generator.py`** duplicates functionality in `scripts/diagrams/generate_*.py`
- **`security_guard.py`** duplicates security checks in `.github/workflows/security.yml`

**Recommended Structure:**
- Split into `tools/ci/` (guards, validators) and `tools/dev/` (autofix, ship)
- Move migration tools to `scripts/migrations/`
- Consolidate report generation with diagram scripts

---

## Cross-Cutting Concerns & Misplaced Files

### Cross-Cutting Concerns (Properly Abstracted but Misused)

| Concern | Current Location | Should Be | Issue |
|---------|-----------------|-----------|-------|
| **Payment Processing** | `rentsecure_be/services/cashfree_service.py`, `rentsecure_be/services/razorpay_service.py` | `finance/services/` or `payments/` | Payment logic lives in project config, not in a domain app |
| **i18n / Translation** | `rentsecure_be/services/i18n_service.py` | `shared/services/` or `i18n/` | Used by notification and ai_assistant but lives in project config |
| **Export Utilities** | `rentsecure_be/utils/export_utils.py` and `core/utils/export_utils.py` | `shared/utils/` or `documents/utils/` | Duplicated across project config and core |
| **Type Compatibility** | `rentsecure_be/type_compat.py` | `shared/type_compat.py` | Used across all apps but lives in project config |
| **Leegality E-Signature** | `rentsecure_be/services/leegality_service.py` and `smartbot/services/leegality_service.py` | `smartbot/services/` or `documents/services/` | Duplicated across project config and smartbot |

### Misplaced Files

| File | Current Location | Should Be | Reason |
|------|-----------------|-----------|--------|
| `fonts/*.ttf`, `fonts/RentSecureLogo.png` | `fonts/` (top-level) | `documents/assets/fonts/` or `static/fonts/` | WeasyPrint font assets should be with document generation |
| `properties/static/*.pdf`, `properties/static/*.png` | `properties/static/` | `documents/output/` or `media/` | Generated PDFs and images are not static assets |
| `management/commands/*.py` (15 files) | `management/commands/` | App-specific `*/management/commands/` | Global commands scatter domain logic |
| `properties/communication/*.py` | `properties/communication/` | `properties/management/commands/` | These are management commands, not communication utilities |
| `properties/scheduler.py` | `properties/scheduler.py` | `properties/management/commands/` | Cron scheduling belongs in management commands |
| `smartbot/tests.py` | `smartbot/tests.py` | `smartbot/tests/test_smartbot.py` | Test file at module root |
| `architecture/generated/architecture.json` | `architecture/generated/` | `build/` or `.generated/` | Generated artifacts should not be in source tree |
| `docs/uml/generated/` | `docs/uml/generated/` | `build/` or CI artifacts | Generated UML diagrams should not be in docs |

---

## Single Responsibility Principle Violations

### 1. `core/` — Identity + Subscription

**Violation:** `core/models.py` contains 9 model classes spanning two bounded contexts (Identity: `User`, `UserProfile`, `OTP`, `NotificationPreference`; Subscription: `SubscriptionPlan`, `UserSubscription`, `AddOnPurchase`, `PlanFeatureLimit`, `UsageLimit`). `core/views.py` is 566 lines handling OTP, auth, subscriptions, bank details, webhooks, and owner reporting.

**Impact:** Changes to subscription logic risk breaking identity logic and vice versa. The `properties/models/subscription_models.py` placeholder confirms the team intended to split these.

**Recommendation:** Extract `SubscriptionPlan`, `UserSubscription`, `AddOnPurchase`, `PlanFeatureLimit`, `UsageLimit`, `OwnerBankDetails` to a `subscription/` or `billing/` app. Keep `User`, `UserProfile`, `OTP` in `core/`.

---

### 2. `properties/` — Property Management (God Module)

**Violation:** `properties/` contains 10 model files, 7 serializer files, 8 view files, 7 service files, 4 admin files, 2 repository files, 1 policy file, 1 scheduler, 1 cron module, 1 communication module, 1 feature enforcer, 1 constants file, static files, templates, and tests. This single app owns Buildings, Units, Renters, RentRecords, Caretakers, ExtraCharges, PropertyTax, RentAgreementDrafts, PoliceVerification, and more.

**Impact:** The app is difficult to test, maintain, and reason about. Any change to rent records risks affecting unit views. The module boundary documentation says this is acceptable "for now" but it already violates SRP.

**Recommendation:** Split into sub-packages: `properties/buildings/`, `properties/units/`, `properties/renters/`, `properties/rent_records/`. Each sub-package should have its own models, serializers, views, services, and tests.

---

### 3. `notification/` — Communication + Business Rules

**Violation:** `notification/services/` contains not just channel adapters but also domain-specific reminder logic:
- `extra_charge_reminders.py` — knows about `ExtraCharge` model and when to remind
- `late_fees_notify_service.py` — knows about late fee business rules
- `rent_notify_service.py` — knows about rent status and notification timing

**Impact:** The notification module becomes a dumping ground for "when to notify" logic from every domain. Changes to rent reminder logic require modifying the notification app.

**Recommendation:** Move reminder logic to domain apps (`properties/services/rent_reminder_service.py`, `finance/services/tax_reminder_service.py`). Keep only channel adapters in `notification/`.

---

### 4. `smartbot/` — AI Chat + Actions + Domain Logic

**Violation:** `smartbot/actions.py` contains `send_rent_reminder` (notification), `retry_payout` (finance), `send_rent_agreement` (documents), and `send_agreement_for_signature` (smartbot). The module also has its own `whatsapp_service.py` (duplicate of notification's), cron jobs, and Leegality integration.

**Impact:** SmartBot becomes a god module that knows about every domain. Intent extraction and action execution are tightly coupled.

**Recommendation:** Keep only AI orchestration in `smartbot/`. Move `actions.py` content to domain-specific action handlers. Remove duplicate `whatsapp_service.py`.

---

### 5. `ai_assistant/` — Duplicate Analytics + Chat

**Violation:** `ai_assistant/views.py` contains `ai_assistant_insights`, `rent_analytics_data`, `financial_health_report`, and `chat_with_assistant` — duplicating `dashboard/views.py`, `properties/views/owner_dashboard.py`, and `smartbot/views.py`.

**Impact:** Three apps (`dashboard`, `ai_assistant`, `properties`) contain overlapping analytics endpoints. No single source of truth for dashboard data.

**Recommendation:** Consolidate analytics into `dashboard/`. Remove `ai_assistant/` or repurpose it as a pure AI service layer without views.

---

### 6. `rentsecure_be/` — Project Config + Domain Services

**Violation:** The Django project configuration directory contains domain-specific services (`cashfree_service.py`, `razorpay_service.py`, `i18n_service.py`, `leegality_service.py`) and utilities (`cashfree_payout.py`, `export_utils.py`).

**Impact:** Project configuration becomes a catch-all for services that don't have a clear home. All apps depend on `rentsecure_be` for both configuration and domain logic.

**Recommendation:** Move all services and utilities to their respective domain apps. Keep `rentsecure_be/` strictly for Django configuration (settings, urls, wsgi, asgi).

---

## Additional Structural Issues

### Duplicate Management Commands

| Command | Locations |
|---------|-----------|
| `send_monthly_rent_summary` | `management/commands/` AND `properties/management/commands/` |
| Rent reminder logic | `management/commands/daily_rent_reminder.py`, `management/commands/rent_reminder_service.py`, `management/commands/send_rent_reminders.py`, `notification/services/schedule_reminders.py`, `properties/scheduler.py`, `smartbot/cron/reminders.py` |
| `retry_failed_payouts` | `management/commands/` AND `properties/communication/` |

### Duplicate Service Implementations

| Service | Locations |
|---------|-----------|
| Leegality e-signature | `rentsecure_be/services/leegality_service.py` AND `smartbot/services/leegality_service.py` |
| Export utilities | `rentsecure_be/utils/export_utils.py` AND `core/utils/export_utils.py` |
| WhatsApp wrapper | `notification/services/whatsapp_service.py` (real) AND `smartbot/whatsapp_service.py` (thin wrapper) |

### Empty / Placeholder Modules

- `properties/models/subscription_models.py` — empty placeholder
- `properties/models/usage_limit_models.py` — empty placeholder
- `ai_assistant/models.py` — empty (1 line)
- `architecture/contracts/` — empty directory (documented as required)

### Unused / Underutilized Modules

- `shared/interfaces.py` — protocols defined but never implemented
- `shared/constants.py` — exists but contains no constants
- `shared/types.py` — minimal usage
- `architecture/contracts/` — documented but empty
- `dashboard/` — not wired in URLs, duplicate functionality

---

## Recommended Priority Actions

### P0 — Critical (Address Immediately)

1. **Remove duplicate `ai_assistant/` or consolidate into `smartbot/`** — eliminates 3 duplicate bounded contexts
2. **Move payment services from `rentsecure_be/services/` to `finance/services/`** — fixes domain service placement
3. **Split `core/` into Identity and Subscription** — aligns with documented bounded contexts
4. **Remove empty placeholder files** (`properties/models/subscription_models.py`, `properties/models/usage_limit_models.py`, `ai_assistant/models.py`)
5. **Consolidate duplicate management commands** — single source of truth for rent reminders, monthly summaries, payout retries

### P1 — High (Address in Next Sprint)

6. **Move business logic out of `notification/services/`** — reminder services belong in domain apps
7. **Move static files from `properties/static/` to `documents/output/` or `static/`**
8. **Move `fonts/` to `documents/assets/fonts/`**
9. **Populate or remove `architecture/contracts/`**
10. **Wire `dashboard/urls.py` and `ai_assistant/urls.py` into root URLs** or remove unused apps

### P2 — Medium (Address in Next Month)

11. **Split `properties/` into sub-packages** (buildings, units, renters, rent_records)
12. **Consolidate `architecture/` and `docs/architecture/`**
13. **Move generated artifacts out of source tree** (`architecture/generated/`, `docs/uml/generated/`)
14. **Extract `rentsecure_be/utils/` and `rentsecure_be/services/` to domain apps**
15. **Split `settings.py` into environment-specific files**

### P3 — Low (Technical Debt)

16. **Utilize `shared/interfaces.py` protocols** — implement Repository/Service patterns
17. **Consolidate CI workflows** — reduce from 25+ to ~8 workflows
18. **Move `scripts/diagrams/` to CI-only execution**
19. **Add README to `fonts/` documenting WeasyPrint configuration**
20. **Organize `tools/` into `tools/ci/` and `tools/dev/`**

---

## Architecture Compliance Notes

The project has extensive architecture documentation (`module-boundaries.md`, `dependency-rules.md`, ADRs) but significant gaps between documentation and implementation:

- **Documented**: "No Cross-Context Model Imports"
  **Reality**: `ai_assistant/views.py`, `smartbot/actions.py`, `notification/services/` all import models from other contexts

- **Documented**: "Service Interfaces Only" for cross-context communication
  **Reality**: `shared/interfaces.py` exists but is never used; apps import directly from each other

- **Documented**: "Apps must not import from each other" (import-linter)
  **Reality**: Import-linter is configured but `ai_assistant` and `smartbot` violate the rules; `core/views.py` imports from `rentsecure_be.services`

- **Documented**: "Extract each bounded context into its own package structure" (Phase 6-12)
  **Reality**: `core/` still mixes Identity + Subscription; `properties/` is a god module; `ai_assistant/` duplicates `smartbot/`

---

*End of Report*
