# 06 Dead Modules

## Summary

**Total dead modules detected:** 46
**Analysis method:** AST-based static analysis identifying modules with fan-in = 0 and no public symbols.

## Dead Modules List

### Placeholder / Empty Modules

These modules exist as placeholders for future functionality but contain no executable code.

| Module | File Path | Evidence |
|--------|-----------|----------|
| `properties.models.subscription_models` | `properties/models/subscription_models.py` | Contains only docstring and `__all__ = []`. Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `properties.models.usage_limit_models` | `properties/models/usage_limit_models.py` | Contains only docstring and `__all__ = []`. Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `properties.serializers.subscription_serializers` | `properties/serializers/subscription_serializers.py` | Contains only docstring and `__all__ = []`. Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `properties.serializers.usage_limit_serializers` | `properties/serializers/usage_limit_serializers.py` | Contains only docstring and `__all__ = []`. Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `properties.views.subscription_views` | `properties/views/subscription_views.py` | Contains only docstring and `__all__ = []`. Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `properties.views.usage_limit_views` | `properties/views/usage_limit_views.py` | Contains only docstring and `__all__ = []`. Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `properties.admin.subscription_admin` | `properties/admin/subscription_admin.py` | Contains only docstring and `__all__ = []`. Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `properties.admin.property_tax_admin` | `properties/admin/property_tax_admin.py` | Contains only docstring and `__all__ = []`. Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `properties.admin.usage_limit_admin` | `properties/admin/usage_limit_admin.py` | Contains only docstring and `__all__ = []`. Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `ai_assistant.models` | `ai_assistant/models.py` | Contains only comment `# Create your models here.`. Fan-in: 0, Fan-out: 0, Symbols: 0. |

**Assessment:** These are intentional placeholders for future features. They are not dead code in the traditional sense, but they should be documented as such.

### Empty Package Modules

These `__init__.py` files contain no code and are not imported by any module.

| Module | File Path | Evidence |
|--------|-----------|----------|
| `properties` | `properties/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `properties.utils` | `properties/utils/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `properties.services` | `properties/services/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `properties.serializers` | `properties/serializers/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `properties.views` | `properties/views/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `properties.policies` | `properties/policies/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `properties.repositories` | `properties/repositories/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `properties.management` | `properties/management/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `properties.management.commands` | `properties/management/commands/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `notification` | `notification/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `notification.management` | `notification/management/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `notification.management.commands` | `notification/management/commands/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `notification.tests` | `notification/tests/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `management` | `management/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `management.commands` | `management/commands/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `tests` | `tests/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `tests.load` | `tests/load/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `shared` | `shared/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `tools` | `tools/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `core` | `core/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `dashboard` | `dashboard/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `referral_and_earn` | `referral_and_earn/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `rentsecure_be` | `rentsecure_be/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `smartbot` | `smartbot/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `ai_assistant` | `ai_assistant/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |
| `documents` | `documents/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |

**Assessment:** These are standard Python package markers. Not dead code.

### Unused Management Commands

These management commands exist but are not imported or referenced by any other module.

| Module | File Path | Evidence |
|--------|-----------|----------|
| `management.commands.archive_expired_users_data` | `management/commands/archive_expired_users_data.py` | Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `management.commands.downgrade_expired_users` | `management/commands/downgrade_expired_users.py` | Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `management.commands.seed_subscription_plans` | `management/commands/seed_subscription_plans.py` | Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `management.commands.send_tax_reminders` | `management/commands/send_tax_reminders.py` | Fan-in: 0, Fan-out: 0, Symbols: 0. |

**Assessment:** These commands are likely run manually via `python manage.py <command>`. They are not dead code, but they should be documented in a README.

### Unused Admin Modules

| Module | File Path | Evidence |
|--------|-----------|----------|
| `referral_and_earn.admin` | `referral_and_earn/admin.py` | Fan-in: 0, Fan-out: 0, Symbols: 0. |

**Assessment:** The `Referral` model exists but is not registered in admin. May be intentional or forgotten.

### Unused Test Modules

| Module | File Path | Evidence |
|--------|-----------|----------|
| `documents.tests` | `documents/tests/__init__.py` | Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `tests.test_architecture_contract.conftest` | `tests/test_architecture_contract/conftest.py` | Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `rentsecure_be.tests` | `rentsecure_be/tests/__init__.py` | Fan-in: 0, Fan-out: 0, Symbols: 0. |
| `properties.tests` | `properties/tests/__init__.py` | Fan-in: 0, Fan-out: 0, Symbols: 0. |

**Assessment:** These are empty test package markers. Not dead code.

### Dead Repositories

| Module | File Path | Evidence |
|--------|-----------|----------|
| `properties.repositories.building_repository` | `properties/repositories/building_repository.py` | Fan-in: 0, Fan-out: 0, Symbols: 7. |
| `properties.repositories.rent_record_repository` | `properties/repositories/rent_record_repository.py` | Fan-in: 0, Fan-out: 0, Symbols: 7. |
| `properties.repositories.renter_repository` | `properties/repositories/renter_repository.py` | Fan-in: 0, Fan-out: 0, Symbols: 7. |
| `properties.repositories.unit_repository` | `properties/repositories/unit_repository.py` | Fan-in: 0, Fan-out: 0, Symbols: 12. |

**Root Cause:** Repository pattern was introduced but never integrated into services.

**Recommendation:** Either remove these modules or start migrating services to use them.

### Dead Services

| Module | File Path | Evidence |
|--------|-----------|----------|
| `properties.services.building_service` | `properties/services/building_service.py` | Fan-in: 0, Fan-out: 0, Symbols: 12. |
| `properties.services.extra_charge_service` | `properties/services/extra_charge_service.py` | Fan-in: 0, Fan-out: 0, Symbols: 2. |
| `properties.services.rent_service` | `properties/services/rent_service.py` | Fan-in: 0, Fan-out: 0, Symbols: 6. |
| `properties.services.renter_service` | `properties/services/renter_service.py` | Fan-in: 0, Fan-out: 0, Symbols: 6. |
| `properties.services.occupancy_service` | `properties/services/occupancy_service.py` | Fan-in: 0, Fan-out: 0, Symbols: 5. |
| `properties.services.vacancy_service` | `properties/services/vacancy_service.py` | Fan-in: 0, Fan-out: 0, Symbols: 5. |
| `smartbot.services.agreement_service` | `smartbot/services/agreement_service.py` | Fan-in: 2, Fan-out: 0, Symbols: 4. (Used only in tests) |
| `smartbot.services.gpt_services` | `smartbot/services/gpt_services.py` | Fan-in: 2, Fan-out: 0, Symbols: 3. (Used only in tests) |
| `smartbot.services.leegality_service` | `smartbot/services/leegality_service.py` | Fan-in: 2, Fan-out: 0, Symbols: 9. (Used only in tests) |
| `rentsecure_be.services.i18n_service` | `rentsecure_be/services/i18n_service.py` | Fan-in: 3, Fan-out: 0, Symbols: 1. (Used only in tests and notification) |

**Assessment:** Many services are defined but not used by production code. Some are only used in tests.

### Dead Views

| Module | File Path | Evidence |
|--------|-----------|----------|
| `properties.views.owner_dashboard` | `properties/views/owner_dashboard.py` | Fan-in: 0, Fan-out: 0, Symbols: 14. |
| `properties.views.subscription_views` | `properties/views/subscription_views.py` | Empty placeholder. Fan-in: 0, Fan-out: 0. |
| `properties.views.usage_limit_views` | `properties/views/usage_limit_views.py` | Empty placeholder. Fan-in: 0, Fan-out: 0. |
| `notification.views` | `notification/views.py` | Fan-in: 2, Fan-out: 0, Symbols: 9. (Only imported by tests) |

### Dead Utilities

| Module | File Path | Evidence |
|--------|-----------|----------|
| `properties.utils` | `properties/utils/__init__.py` | Empty package marker. Fan-in: 0, Fan-out: 0. |

## Dead Code Summary Table

| Category | Count | Action |
|----------|-------|--------|
| Placeholder / Empty modules | 10 | Document as intentional, add `# placeholder` comment |
| Empty package `__init__.py` | 26 | No action needed (standard Python) |
| Unused management commands | 4 | Document in README or remove |
| Unused admin modules | 1 | Register model or remove |
| Unused repositories | 4 | Remove or integrate |
| Unused services | 10 | Remove or integrate |
| Unused views | 4 | Remove or integrate |
| Unused test packages | 4 | No action needed (standard Python) |

**Total actionable dead modules:** 19
