# 02 Import Matrix

## Overview

This matrix documents every package in the repository, showing:
- **Imports From**: Packages this module imports from
- **Imported By**: Packages that import from this module
- **Fan In**: Number of modules importing this module
- **Fan Out**: Number of modules this module imports
- **Number of Imports**: Total import statements
- **Number of Public Symbols**: Classes, functions, assignments
- **Risk Level**: Based on coupling and cross-app imports

**Analysis scope:** 321 modules, 387 total imports, 340 Python files.
**Source:** `docs/architecture/audit_data.json`

## Package-Level Import Matrix

### core

| Metric | Value |
|--------|-------|
| Modules | 25 |
| Total Imports (Fan Out) | 51 |
| Imported By (Fan In) | 86 |
| Public Symbols | 532 |
| Files | 25 |
| Cross-App Imports | 54 |

**Imports From (project-internal):**
- `rentsecure_be` (36 occurrences)
- `properties` (13 occurrences)
- `notification` (5 occurrences)
- `referral_and_earn` (2 occurrences)
- `shared` (1 occurrence)

**Evidence:**
- `core.models` imports `rentsecure_be.type_compat` (fan-in: 63)
- `core.views` imports `notification.services.rent_notify_service`, `properties.models.rent_record_models`, `rentsecure_be.services.cashfree_service` (fan-out: 13)
- `core.services.bank_details_service` imports `properties.models.rent_record_models`, `rentsecure_be.utils.cashfree_payout`
- `core.services.referral_service` imports `referral_and_earn.models`

### properties

| Metric | Value |
|--------|-------|
| Modules | 111 |
| Total Imports (Fan Out) | 162 |
| Imported By (Fan In) | 130 |
| Public Symbols | 2332 |
| Files | 111 |
| Cross-App Imports | 38 |

**Imports From (project-internal):**
- `core` (various models and utilities)
- `notification` (services, models)
- `rentsecure_be` (type_compat, services)

**Evidence:**
- `properties.models` is the most imported module (fan-in: 74)
- `properties.models.renter_models` imports `core.models`, `rentsecure_be.type_compat`
- `properties.models.building_models` imports `core.models`
- `properties.models.unit_models` imports `core.models`, `properties.models`, `properties.models.renter_models`, `properties.utils.utils`, `rentsecure_be.type_compat`
- `properties.signals` imports `notification.models`, `notification.services.whatsapp_service`, `properties.scheduler`, `properties.services.receipt_service`

### notification

| Metric | Value |
|--------|-------|
| Modules | 28 |
| Total Imports (Fan Out) | 39 |
| Imported By (Fan In) | 57 |
| Public Symbols | 277 |
| Files | 28 |
| Cross-App Imports | 14 |

**Imports From (project-internal):**
- `properties` (models)
- `rentsecure_be` (services)

**Evidence:**
- `notification.services.whatsapp_service` is imported by 21 modules (fan-in: 21)
- `notification.services.rent_notify_service` imports `rentsecure_be.services.i18n_service`
- `notification.services.voice_note_service` imports `properties.models.renter_models`
- `notification.services.schedule_reminders` imports `properties.models.property_tax_models`, `properties.models.rent_record_models`
- `notification.services.extra_charge_reminders` imports `properties.models.extra_charge_models`, `rentsecure_be.services.i18n_service`

### smartbot

| Metric | Value |
|--------|-------|
| Modules | 19 |
| Total Imports (Fan Out) | 26 |
| Imported By (Fan In) | 16 |
| Public Symbols | 187 |
| Files | 19 |
| Cross-App Imports | 4 |

**Imports From (project-internal):**
- `properties` (models)
- `notification` (utils)
- `rentsecure_be` (services)

**Evidence:**
- `smartbot.actions` imports `notification.utils`, `properties.models`, `rentsecure_be.services.cashfree_service`
- `smartbot.views` imports `properties.models`
- `smartbot.services.chatbot_service` imports `properties.models`
- `smartbot.services.services` imports `properties.models`
- `smartbot.whatsapp_service` imports `notification.utils`

### finance

| Metric | Value |
|--------|-------|
| Modules | 12 |
| Total Imports (Fan Out) | 16 |
| Imported By (Fan In) | 7 |
| Public Symbols | 116 |
| Files | 12 |
| Cross-App Imports | 3 |

**Imports From (project-internal):**
- `core` (models)
- `properties` (models)
- `rentsecure_be` (type_compat)

**Evidence:**
- `finance.views` imports `core.models`, `properties.models`, `rentsecure_be.type_compat`
- `finance.utils` imports `properties.models`
- `finance.models` imports `rentsecure_be.type_compat`

### documents

| Metric | Value |
|--------|-------|
| Modules | 11 |
| Total Imports (Fan Out) | 12 |
| Imported By (Fan In) | 6 |
| Public Symbols | 156 |
| Files | 11 |
| Cross-App Imports | 3 |

**Imports From (project-internal):**
- `core` (models)
- `properties` (models, serializers)

**Evidence:**
- `documents.views` imports `core.models`, `properties.models`, `properties.serializers`
- `documents.utils` imports `properties.models`

### ai_assistant

| Metric | Value |
|--------|-------|
| Modules | 13 |
| Total Imports (Fan Out) | 18 |
| Imported By (Fan In) | 9 |
| Public Symbols | 103 |
| Files | 13 |
| Cross-App Imports | 4 |

**Imports From (project-internal):**
- `properties` (models, signals)
- `core` (models)
- `notification` (services)
- `smartbot` (services)

**Evidence:**
- `ai_assistant.views` imports `core.models`, `properties.models`, `notification.services.whatsapp_service`, `smartbot.services.chatbot_service`
- `ai_assistant.receivers` imports `properties.models`, `properties.signals.renter_signals`
- `ai_assistant.services.archive_service` imports `properties.models`
- `ai_assistant.services.invoice_service` imports `properties.models`
- `ai_assistant.services.unit_service` imports `properties.models`

### dashboard

| Metric | Value |
|--------|-------|
| Modules | 4 |
| Total Imports (Fan Out) | 3 |
| Imported By (Fan In) | 1 |
| Public Symbols | 14 |
| Files | 4 |
| Cross-App Imports | 2 |

**Imports From (project-internal):**
- `properties` (models)
- `smartbot` (actions)

**Evidence:**
- `dashboard.views` imports `properties.models`, `smartbot.actions`

### referral_and_earn

| Metric | Value |
|--------|-------|
| Modules | 5 |
| Total Imports (Fan Out) | 3 |
| Imported By (Fan In) | 3 |
| Public Symbols | 11 |
| Files | 5 |
| Cross-App Imports | 1 |

**Imports From (project-internal):**
- `rentsecure_be` (type_compat)

**Evidence:**
- `referral_and_earn.models` imports `rentsecure_be.type_compat`
- `referral_and_earn.apps` imports `rentsecure_be.type_compat`

### rentsecure_be

| Metric | Value |
|--------|-------|
| Modules | 16 |
| Total Imports (Fan Out) | 7 |
| Imported By (Fan In) | 54 |
| Public Symbols | 151 |
| Files | 16 |
| Cross-App Imports | 9 |

**Imports From (project-internal):**
- `core` (models)
- `properties` (models)
- `notification` (services)

**Evidence:**
- `rentsecure_be.services.cashfree_service` imports `core.models`, `notification.services.rent_notify_service`, `properties.models.rent_record_models`
- `rentsecure_be.utils.export_utils` imports `properties.models.rent_record_models`

### shared

| Metric | Value |
|--------|-------|
| Modules | 9 |
| Total Imports (Fan Out) | 1 |
| Imported By (Fan In) | 4 |
| Public Symbols | 41 |
| Files | 9 |
| Cross-App Imports | 3 |

**Imports From (project-internal):**
- `shared` (validators imports validators - internal)

**Evidence:**
- `shared.utils` imports `shared.validators`
- `core.services.otp_service` imports `shared.exceptions`
- `core.services.referral_service` imports `shared.exceptions`
- `core.views` imports `shared.exceptions`
- `properties.utils.utils` imports `notification.services.late_fees_notify_service` (NOTE: this is a cross-layer violation)

### management

| Metric | Value |
|--------|-------|
| Modules | 16 |
| Total Imports (Fan Out) | 27 |
| Imported By (Fan In) | 0 |
| Public Symbols | 94 |
| Files | 16 |
| Cross-App Imports | 14 |

**Imports From (project-internal):**
- `notification` (services, utils)
- `properties` (models, services)
- `core` (models)
- `rentsecure_be` (type_compat, services)

**Evidence:**
- `management.commands.apply_late_fees` imports `notification.services.whatsapp_service`, `properties.models`, `rentsecure_be.type_compat`
- `management.commands.send_rent_reminders` imports `notification.services.whatsapp_service`, `properties.models`, `rentsecure_be.type_compat`
- `management.commands.retry_failed_payouts` imports `properties.models`, `rentsecure_be.services.cashfree_service`, `rentsecure_be.type_compat`

### tests

| Metric | Value |
|--------|-------|
| Modules | 11 |
| Total Imports (Fan Out) | 13 |
| Imported By (Fan In) | 3 |
| Public Symbols | 227 |
| Files | 11 |
| Cross-App Imports | 5 |

**Imports From (project-internal):**
- `core` (models)
- `properties` (models, services, views)
- `rentsecure_be` (services)
- `scripts` (architecture_contract)
- `conftest` (test utilities)
- `tests.factories` (test factories)

**Evidence:**
- `tests.test_query_count` imports `core.models`, `properties.models`, `properties.services.unit_service`, `properties.views.renter_views`, `properties.views.unit_views`
- `tests.test_performance_benchmarks` imports `core.models`, `properties.models`, `properties.services.unit_service`
- `tests.test_api_contracts` imports `core.models`, `tests.factories`

### tools

| Metric | Value |
|--------|-------|
| Modules | 8 |
| Total Imports (Fan Out) | 4 |
| Imported By (Fan In) | 4 |
| Public Symbols | 166 |
| Files | 8 |
| Cross-App Imports | 0 |

**Imports From (project-internal):**
- `tools` (ci_guard imports migration_guard, security_guard; ship imports ci_guard, report_generator)

**Evidence:**
- `tools.ci_guard` imports `tools.migration_guard`, `tools.security_guard`
- `tools.ship` imports `tools.ci_guard`, `tools.report_generator`

### scripts

| Metric | Value |
|--------|-------|
| Modules | 29 |
| Total Imports (Fan Out) | 1 |
| Imported By (Fan In) | 1 |
| Public Symbols | 761 |
| Files | 29 |
| Cross-App Imports | 1 |

**Imports From (project-internal):**
- `core` (models)

**Evidence:**
- `scripts.seed_load_test_data` imports `core.models`
- `scripts.diagrams.*` modules have 0 project imports (isolated tooling)

## Module-Level Import Matrix (Top 20)

| Module | Imports From | Imported By | Fan In | Fan Out | Risk Level |
|--------|-------------|-------------|--------|---------|------------|
| `properties.models` | - | 74 | 74 | 0 | **CRITICAL** |
| `core.models` | `rentsecure_be.type_compat` | 63 | 63 | 1 | **CRITICAL** |
| `rentsecure_be.type_compat` | stdlib | 36 | 36 | 0 | **HIGH** |
| `notification.services.whatsapp_service` | stdlib, twilio, boto3 | 21 | 21 | 0 | **HIGH** |
| `core.services.base` | stdlib | 8 | 8 | 0 | MEDIUM |
| `properties.feature_enforcer` | `core.models` | 7 | 7 | 1 | MEDIUM |
| `properties.models.rent_record_models` | `rentsecure_be.type_compat` | 6 | 6 | 1 | HIGH |
| `rentsecure_be.services.cashfree_service` | `core.models`, `notification.services.rent_notify_service`, `properties.models.rent_record_models` | 6 | 6 | 4 | **HIGH** |
| `conftest` | `core.models`, `properties.models` | 6 | 6 | 2 | MEDIUM |
| `notification.utils` | stdlib | 6 | 6 | 0 | MEDIUM |
| `notification.models` | django | 6 | 6 | 0 | MEDIUM |
| `notification.services.rent_notify_service` | `notification.services.voice_service`, `notification.services.whatsapp_service`, `rentsecure_be.services.i18n_service` | 5 | 5 | 3 | HIGH |
| `notification.services.voice_service` | stdlib | 5 | 5 | 0 | MEDIUM |
| `documents.views` | `core.models`, `properties.models`, `properties.serializers` | 4 | 4 | 3 | MEDIUM |
| `notification.services.extra_charge_reminders` | `notification.services.voice_service`, `notification.services.whatsapp_service`, `properties.models.extra_charge_models`, `rentsecure_be.services.i18n_service` | 4 | 4 | 4 | HIGH |
| `properties.views.unit_views` | `core.models`, `rentsecure_be.services.leegality_service`, `rentsecure_be.type_compat` | 4 | 4 | 3 | HIGH |
| `shared.exceptions` | stdlib | 3 | 3 | 0 | LOW |
| `core.views` | 13 modules | 3 | 3 | 13 | **CRITICAL** |
| `smartbot.actions` | `notification.utils`, `properties.models`, `rentsecure_be.services.cashfree_service` | 3 | 3 | 4 | HIGH |
| `finance.models` | `rentsecure_be.type_compat` | 3 | 3 | 1 | MEDIUM |

## Risk Level Definitions

| Risk Level | Criteria |
|------------|----------|
| **CRITICAL** | Fan-in > 50 OR Fan-out > 10 OR Cross-app imports > 5 |
| **HIGH** | Fan-in > 20 OR Cross-app imports > 3 |
| **MEDIUM** | Fan-in > 5 OR Cross-app imports > 1 |
| **LOW** | All other modules |
