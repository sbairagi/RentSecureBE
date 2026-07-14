# 04 Cross-App Dependencies

## Summary

**Total cross-app imports:** 205
**Total modules analyzed:** 321
**Analysis date:** 2026-07-14

## Cross-App Dependency Map

```
core
├── properties (13 imports)
├── notification (5 imports)
├── referral_and_earn (2 imports)
├── shared (1 import)
└── rentsecure_be (36 imports)

properties
├── core (13 imports)
├── notification (10 imports)
└── rentsecure_be (36 imports)

smartbot
├── properties (4 imports)
├── notification (2 imports)
└── rentsecure_be (3 imports)

finance
├── core (3 imports)
├── properties (3 imports)
└── rentsecure_be (3 imports)

notification
├── properties (10 imports)
└── rentsecure_be (3 imports)

documents
├── core (2 imports)
└── properties (3 imports)

ai_assistant
├── properties (4 imports)
├── core (1 import)
├── notification (1 import)
└── smartbot (1 import)

dashboard
├── properties (1 import)
└── smartbot (1 import)

management
├── properties (14 imports)
├── notification (7 imports)
├── core (4 imports)
└── rentsecure_be (7 imports)
```

## Detailed Cross-App Dependencies

### core → properties

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `core.services.bank_details_service` | `properties.models.rent_record_models` | Bank details service needs rent record data | Partially | Yes - core should not directly import property models | Move rent record access to a property service interface |
| `core.services.owner_reporting_service` | `properties.models.rent_record_models` | Reporting needs rent data | Partially | Yes - same as above | Introduce reporting DTOs from properties |
| `core.views` | `properties.models.rent_record_models` | Views orchestrate rent record operations | Partially | Yes - views importing models directly | Views should use property services |
| `core.tests.test_core_webhooks` | `properties.models` | Tests need property fixtures | Yes (test code) | No | Keep in tests |
| `core.tests.test_views` | `properties.models` | Tests need property fixtures | Yes (test code) | No | Keep in tests |

**Root Cause:** The `core` app contains business logic that legitimately needs property data, but it bypasses the `properties` service layer and imports models directly.

**Recommendation:** Introduce service interfaces in `shared/interfaces.py` for cross-context communication. Create a `properties.services.rent_record_api` that `core` can call without importing models.

### core → notification

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `core.views` | `notification.services.rent_notify_service` | Webhook triggers rent notifications | Partially | Yes - core importing notification services | Use domain events or notification interface |

**Root Cause:** Core views trigger notifications directly instead of publishing domain events.

**Recommendation:** Implement `shared/domain_events.py` patterns. Core should publish `RentPaidEvent` and notification app should subscribe.

### core → referral_and_earn

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `core.services.referral_service` | `referral_and_earn.models` | Referral service creates referral records | Partially | Yes - core importing referral models | Move referral logic to referral_and_earn app |

**Root Cause:** Referral business logic is split between `core` and `referral_and_earn`.

**Recommendation:** Move `ReferralService` entirely to `referral_and_earn` app.

### core → shared

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `core.services.otp_service` | `shared.exceptions` | Uses custom validation error | Yes | No | Keep |
| `core.services.referral_service` | `shared.exceptions` | Uses custom validation error | Yes | No | Keep |
| `core.views` | `shared.exceptions` | Uses custom validation error | Yes | No | Keep |

**Assessment:** Acceptable. `shared` is designed for cross-cutting concerns.

### properties → core

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `properties.models.building_models` | `core.models` | Building has ForeignKey to User | Partially | Yes - domain model importing core model | Consider making `core.models.User` a shared base or Django user model |
| `properties.models.renter_models` | `core.models` | Renter has ForeignKey to User | Partially | Yes - same as above | Same as above |
| `properties.models.unit_models` | `core.models` | Unit has ForeignKey to User | Partially | Yes - same as above | Same as above |
| `properties.feature_enforcer` | `core.models` | Feature enforcement checks user types | Yes | No (reads core models) | Keep, but consider moving feature flags to shared |
| `properties.services.unit_service` | `core.models` | Unit service needs user context | Partially | Yes | Use user context from request instead |
| `properties.services.summary_service` | `core.models` | Summary needs user data | Partially | Yes | Pass user as parameter |
| `properties.signals` | `properties.signals.renter_signals` | Internal signal reference | Yes | No | Keep |

**Root Cause:** `core.models.User` is the Django user model and many domain models need to reference it. This is a fundamental coupling that requires careful refactoring.

**Recommendation:** Create a `shared.base_models` module with the User model reference, or use Django's `settings.AUTH_USER_MODEL` string references in ForeignKeys instead of direct imports.

### properties → notification

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `properties.signals` | `notification.models` | Signal handlers need notification types | Partially | Yes - properties importing notification models | Use notification service instead |
| `properties.signals` | `notification.services.whatsapp_service` | Direct WhatsApp calls in signals | No | Yes - business logic in signals | Move to notification service |
| `properties.signals` | `notification.services.voice_note_service` | Voice note triggers in signals | No | Yes - same | Move to notification service |
| `properties.services.renter_onboarding_service` | `notification.services.whatsapp_service` | Onboarding sends WhatsApp | Partially | Yes - properties importing notification service | Use domain event |
| `properties.services.summary_service` | `notification.services.whatsapp_service` | Summary sends WhatsApp | Partially | Yes | Use domain event |
| `notification.services.extra_charge_reminders` | `properties.models.extra_charge_models` | Needs extra charge data | Yes | No (notification needs domain data) | Keep, but consider DTOs |
| `notification.services.schedule_reminders` | `properties.models.property_tax_models` | Needs tax data | Yes | No | Keep |
| `notification.services.schedule_reminders` | `properties.models.rent_record_models` | Needs rent data | Yes | No | Keep |
| `notification.services.voice_note_service` | `properties.models.renter_models` | Needs renter data | Yes | No | Keep |

**Root Cause:** Properties app directly invokes notification services instead of using events.

**Recommendation:** Implement event-driven notification triggers.

### properties → rentsecure_be

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `properties.apps` | `rentsecure_be.type_compat` | Uses `override` decorator | Yes | No | Keep |
| `properties.models.*` | `rentsecure_be.type_compat` | Uses `override` decorator | Yes | No | Keep |
| `properties.serializers.*` | `rentsecure_be.type_compat` | Uses `override` decorator | Yes | No | Keep |
| `properties.views.*` | `rentsecure_be.type_compat` | Uses `override` decorator | Yes | No | Keep |
| `properties.management.commands.*` | `rentsecure_be.type_compat` | Uses `override` decorator | Yes | No | Keep |

**Assessment:** Acceptable. `rentsecure_be.type_compat` is a Python compatibility shim.

### smartbot → properties

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `smartbot.actions` | `properties.models` | Actions need property data | Partially | Yes | Use property service |
| `smartbot.services.chatbot_service` | `properties.models` | Chatbot needs property data | Partially | Yes | Use property service |
| `smartbot.services.services` | `properties.models` | Service needs property data | Partially | Yes | Use property service |
| `smartbot.views` | `properties.models` | View needs property data | Partially | Yes | Use property service |
| `smartbot.cron.reminders` | `properties.models` | Reminder needs property data | Partially | Yes | Use property service |
| `smartbot.tests.*` | `properties.models` | Test fixtures | Yes (test code) | No | Keep |

**Root Cause:** SmartBot directly imports property models for data access.

**Recommendation:** SmartBot should interact with properties through a service interface.

### smartbot → notification

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `smartbot.actions` | `notification.utils` | Actions use notification utilities | Partially | Yes | Use notification service interface |
| `smartbot.whatsapp_service` | `notification.utils` | WhatsApp service uses notification utils | Partially | Yes | Consolidate notification utils |

**Root Cause:** SmartBot has its own WhatsApp service that reuses notification utilities.

**Recommendation:** Consolidate WhatsApp logic into `notification` app or define a clear interface.

### smartbot → rentsecure_be

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `smartbot.actions` | `rentsecure_be.services.cashfree_service` | Actions trigger payouts | Partially | Yes | Use finance/payment service interface |

**Root Cause:** SmartBot actions trigger financial operations directly.

**Recommendation:** Introduce payment service interface in `shared/interfaces.py`.

### finance → core

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `finance.views` | `core.models` | Finance views need user data | Partially | Yes | Use user from request context |
| `finance.tests.test_finance_utils` | `core.models` | Test fixtures | Yes (test code) | No | Keep |
| `finance.tests.test_finance_views` | `core.models` | Test fixtures | Yes (test code) | No | Keep |

### finance → properties

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `finance.views` | `properties.models` | Finance views need property data | Partially | Yes | Use property service |
| `finance.utils` | `properties.models` | Finance utils need property data | Partially | Yes | Use property service |
| `finance.tests.test_finance_views` | `properties.models` | Test fixtures | Yes (test code) | No | Keep |
| `finance.tests.test_finance_utils` | `properties.models` | Test fixtures | Yes (test code) | No | Keep |

### ai_assistant → properties

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `ai_assistant.views` | `properties.models` | AI views need property data | Partially | Yes | Use property service |
| `ai_assistant.receivers` | `properties.models` | Receivers need property data | Partially | Yes | Use property service |
| `ai_assistant.services.archive_service` | `properties.models` | Archive service needs property data | Partially | Yes | Use property service |
| `ai_assistant.services.invoice_service` | `properties.models` | Invoice service needs property data | Partially | Yes | Use property service |
| `ai_assistant.services.unit_service` | `properties.models` | Unit service needs property data | Partially | Yes | Use property service |
| `ai_assistant.receivers` | `properties.signals.renter_signals` | Signal handler reference | Partially | Yes | Use domain events |

### ai_assistant → core

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `ai_assistant.views` | `core.models` | AI views need user data | Partially | Yes | Use user from request |

### ai_assistant → notification

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `ai_assistant.views` | `notification.services.whatsapp_service` | AI views trigger WhatsApp | Partially | Yes | Use domain events |

### ai_assistant → smartbot

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `ai_assistant.views` | `smartbot.services.chatbot_service` | AI integrates with chatbot | Partially | Yes | Consolidate AI and SmartBot or use interface |

### dashboard → properties

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `dashboard.views` | `properties.models` | Dashboard needs property data | Partially | Yes | Use property service |

### dashboard → smartbot

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `dashboard.views` | `smartbot.actions` | Dashboard triggers SmartBot actions | Partially | Yes | Use SmartBot service interface |

### documents → core

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `documents.views` | `core.models` | Document views need user data | Partially | Yes | Use user from request |

### documents → properties

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `documents.views` | `properties.models` | Document views need property data | Partially | Yes | Use property service |
| `documents.views` | `properties.serializers` | Document views use property serializers | Partially | Yes | Document app should have its own serializers |
| `documents.utils` | `properties.models` | Document utils need property data | Partially | Yes | Use property service |

### management → properties

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `management.commands.*` | `properties.models` | Commands need property data | Partially | Yes | Commands should use property services |
| `management.commands.send_monthly_rent_summary` | `properties.services.summary_service` | Command uses property service | Yes | No | Keep |
| `management.commands.generate_monthly_extra_charges` | `properties.services.extra_charge_service` | Command uses property service | Yes | No | Keep |

### management → notification

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `management.commands.apply_late_fees` | `notification.services.whatsapp_service` | Command sends WhatsApp reminders | Partially | Yes | Use notification service interface |
| `management.commands.send_rent_reminders` | `notification.services.whatsapp_service` | Command sends rent reminders | Partially | Yes | Use notification service interface |
| `management.commands.rent_reminder_service` | `notification.services.whatsapp_service` | Service sends reminders | Partially | Yes | Use notification service interface |
| `management.commands.check_vacant_units` | `notification.services.whatsapp_service` | Command sends vacancy alerts | Partially | Yes | Use notification service interface |
| `management.commands.auto_deactivate_renters` | `notification.utils` | Command uses notification utils | Partially | Yes | Use notification service interface |
| `management.commands.monthly_whatsapp_and_email_summary_to_owner` | `notification.services.whatsapp_service` | Command sends owner summary | Partially | Yes | Use notification service interface |

### management → core

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `management.commands.monthly_whatsapp_and_email_summary_to_owner` | `core.models` | Command needs user data | Partially | Yes | Pass user ID, not model |
| `management.commands.send_monthly_rent_summary` | `core.models` | Command needs user data | Partially | Yes | Pass user ID, not model |

### rentsecure_be → core

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `rentsecure_be.services.cashfree_service` | `core.models` | Cashfree service needs OwnerBankDetails | Partially | Yes | Cashfree service should be in core or use interface |

**Root Cause:** Payment gateway services are placed in `rentsecure_be` but need to access `core.models.OwnerBankDetails`.

**Recommendation:** Move payment-related models to a shared location or create a payment service interface.

### rentsecure_be → properties

| Source Module | Target Module | Why It Exists | Acceptable? | Violates Architecture? | Future Direction |
|---------------|---------------|---------------|-------------|------------------------|------------------|
| `rentsecure_be.services.cashfree_service` | `properties.models.rent_record_models` | Cashfree needs rent record data | Partially | Yes | Use rent record service interface |
| `rentsecure_be.utils.export_utils` | `properties.models.rent_record_models` | Export utility needs rent data | Partially | Yes | Move export to properties app or use DTO |

## Summary of Violations

| Violation Type | Count | Severity |
|----------------|-------|----------|
| Domain app importing Infrastructure | 42 | HIGH |
| App importing another app's models directly | 38 | HIGH |
| App importing another app's services directly | 18 | MEDIUM |
| App importing another app's views | 0 | N/A |
| Shared importing app | 0 | N/A |

## Overall Assessment

The codebase has **extensive cross-app dependencies** (205 imports). The most critical violations are:

1. **core ↔ properties bidirectional coupling:** Both apps import each other's models and services extensively. This creates a maintenance nightmare.
2. **Direct model imports across apps:** 38 instances where app A imports models from app B directly, bypassing service layers.
3. **Notification as a service hub:** `notification.services.whatsapp_service` is imported by 21 modules across 6 apps, making it a hidden dependency hub.
4. **rentsecure_be as a service container:** `rentsecure_be` hosts payment, PDF, and translation services that are imported by 54 modules, creating a God-app-like dependency pattern.
