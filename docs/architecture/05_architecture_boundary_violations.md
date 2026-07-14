# 05 Architecture Boundary Violations

## Summary

This report validates the architecture boundaries defined in `architecture/dependency-rules.md` and `import-linter.ini`.

**Key finding:** The codebase violates its own documented dependency rules extensively. While `import-linter` reports 0 broken contracts (due to contract misconfiguration), AST analysis reveals 205 cross-app imports that violate the intended layered architecture.

## Boundary Definitions

Based on `architecture/dependency-rules.md`:

| Layer | May Depend On | Must NOT Depend On |
|-------|---------------|-------------------|
| Views | Services, Serializers, Permissions, Shared utilities | Models (except queryset), Other views, Business logic |
| Services | Models, Other services (same context), Shared utilities | Views, Serializers, Request/Response objects |
| Models | Shared utilities, Django base classes | Views, Serializers, Services, Request/Response objects |
| Shared | Python standard library only | Any Django app code, Project-specific code |

## Violations by Layer

### Domain Layer Violations

**Definition:** Domain models should only depend on Django base classes and shared utilities.

| File | Violation | Severity | Evidence |
|------|-----------|----------|----------|
| `properties/models/building_models.py` | Imports `core.models` | HIGH | Direct model-to-model import across apps |
| `properties/models/renter_models.py` | Imports `core.models` | HIGH | Direct model-to-model import across apps |
| `properties/models/unit_models.py` | Imports `core.models` | HIGH | Direct model-to-model import across apps |
| `core/models.py` | Imports `rentsecure_be.type_compat` | MEDIUM | Domain model importing infrastructure shim |
| `finance/models.py` | Imports `rentsecure_be.type_compat` | MEDIUM | Domain model importing infrastructure shim |
| `referral_and_earn/models.py` | Imports `rentsecure_be.type_compat` | MEDIUM | Domain model importing infrastructure shim |

**Root Cause:** The `User` model in `core` is the Django auth user model. Many domain models need a ForeignKey to `User`, but they import `core.models.User` directly instead of using `settings.AUTH_USER_MODEL` string references.

**Recommendation:** Use `settings.AUTH_USER_MODEL` in ForeignKey definitions. If type hints are needed, use `TYPE_CHECKING` blocks.

### Application Layer Violations

**Definition:** Services should not depend on views, serializers, or request/response objects.

| File | Violation | Severity | Evidence |
|------|-----------|----------|----------|
| `core/services/bank_details_service.py` | Imports `properties.models.rent_record_models` | HIGH | Service importing another app's domain model |
| `core/services/owner_reporting_service.py` | Imports `properties.models.rent_record_models` | HIGH | Service importing another app's domain model |
| `properties/services/renter_onboarding_service.py` | Imports `notification.services.whatsapp_service` | HIGH | Service importing another app's infrastructure |
| `properties/services/summary_service.py` | Imports `notification.services.whatsapp_service` | HIGH | Service importing another app's infrastructure |
| `rentsecure_be/services/cashfree_service.py` | Imports `core.models`, `notification.services.rent_notify_service`, `properties.models.rent_record_models` | HIGH | Infrastructure service importing domain models and other services |
| `properties/utils/utils.py` | Imports `notification.services.late_fees_notify_service` | MEDIUM | Utility importing notification service |
| `smartbot/actions.py` | Imports `notification.utils`, `properties.models`, `rentsecure_be.services.cashfree_service` | HIGH | Action class importing multiple domains |

**Root Cause:** Services are not isolated by bounded context. They directly import models and services from other apps.

**Recommendation:** Introduce service interfaces in `shared/interfaces.py`. Use dependency injection or event-driven communication.

### Infrastructure Layer Violations

**Definition:** Infrastructure code should not leak into domain or application layers.

| File | Violation | Severity | Evidence |
|------|-----------|----------|----------|
| `core/views.py` | Imports `razorpay` (payment gateway) | HIGH | View importing payment gateway directly |
| `core/views.py` | Imports `twilio.rest.Client` | HIGH | View importing SMS/WhatsApp gateway directly |
| `core/views.py` | Imports `rentsecure_be.services.cashfree_service` | HIGH | View importing infrastructure service |
| `properties/views/rent_record_views.py` | Imports `rentsecure_be.services.cashfree_service` | HIGH | View importing payment service |
| `properties/views/rent_record_views.py` | Imports `rentsecure_be.services.razorpay_service` | HIGH | View importing payment service |
| `notification/services/whatsapp_service.py` | Imports `boto3`, `twilio` | MEDIUM | Service importing cloud/SMS SDKs directly (acceptable for Year 1, but should be isolated) |

**Root Cause:** Views contain business logic and directly invoke payment/notification gateways.

**Recommendation:** Move all third-party API calls into dedicated adapter classes in `rentsecure_be` or the respective app. Views should only call domain services.

### Presentation Layer Violations

**Definition:** Views should be thin and delegate to services.

| File | Violation | Severity | Evidence |
|------|-----------|----------|----------|
| `core/views.py` | 62 public symbols, imports 13 modules | CRITICAL | God-view file with excessive business logic |
| `properties/views/rent_record_views.py` | 27 public symbols, 6 imports | HIGH | View with too much logic |
| `properties/views/unit_views.py` | 21 public symbols, 3 imports | HIGH | View with too much logic |
| `ai_assistant/views.py` | 36 public symbols, 5 imports | HIGH | View importing 4 other apps |

**Root Cause:** Views contain significant business logic instead of delegating to services.

**Recommendation:** Extract business logic from views into dedicated service methods.

### Shared Layer Violations

**Definition:** Shared should only depend on Python standard library.

| File | Violation | Severity | Evidence |
|------|-----------|----------|----------|
| `shared/utils.py` | Imports `shared.validators` | LOW | Internal shared import (acceptable) |
| `shared/` | Not imported by any app | MEDIUM | Underutilized shared layer |

**Assessment:** `shared` is correctly isolated from Django apps. However, it is significantly underutilized. Many utilities that should be in `shared` are scattered across apps.

### Repository Layer Violations

**Definition:** Repositories should only depend on models and Django ORM.

| File | Violation | Severity | Evidence |
|------|-----------|----------|----------|
| `properties/repositories/__init__.py` | Empty placeholder | LOW | No violation, but unused package |
| `properties/repositories/building_repository.py` | No imports | INFO | Dead module (fan-in: 0, fan-out: 0) |
| `properties/repositories/rent_record_repository.py` | No imports | INFO | Dead module |
| `properties/repositories/renter_repository.py` | No imports | INFO | Dead module |
| `properties/repositories/unit_repository.py` | No imports | INFO | Dead module |

**Root Cause:** Repository pattern was introduced but never adopted. Services query models directly.

**Recommendation:** Either remove the repository packages or start migrating services to use them.

### Service Layer Violations

**Definition:** Services should not import views, serializers, or request/response objects.

No direct violations found. Services correctly avoid importing views or serializers.

## Cross-App Import Summary

| Source App | Target App | Import Count | Severity |
|------------|------------|--------------|----------|
| core | properties | 13 | HIGH |
| core | notification | 5 | HIGH |
| core | referral_and_earn | 2 | MEDIUM |
| core | shared | 1 | LOW |
| properties | core | 13 | HIGH |
| properties | notification | 10 | HIGH |
| properties | rentsecure_be | 36 | MEDIUM |
| smartbot | properties | 4 | HIGH |
| smartbot | notification | 2 | MEDIUM |
| smartbot | rentsecure_be | 3 | MEDIUM |
| finance | core | 3 | MEDIUM |
| finance | properties | 3 | MEDIUM |
| finance | rentsecure_be | 3 | MEDIUM |
| notification | properties | 10 | HIGH |
| notification | rentsecure_be | 3 | MEDIUM |
| documents | core | 2 | MEDIUM |
| documents | properties | 3 | MEDIUM |
| ai_assistant | properties | 4 | HIGH |
| ai_assistant | core | 1 | MEDIUM |
| ai_assistant | notification | 1 | MEDIUM |
| ai_assistant | smartbot | 1 | MEDIUM |
| dashboard | properties | 1 | MEDIUM |
| dashboard | smartbot | 1 | MEDIUM |
| rentsecure_be | core | 3 | HIGH |
| rentsecure_be | properties | 3 | HIGH |
| rentsecure_be | notification | 3 | HIGH |

## Import-Linter vs Reality

**import-linter reports:** 0 broken contracts
**AST analysis finds:** 205 cross-app imports

### Why the Discrepancy?

The `import-linter.ini` contracts define layers as:
```
core: layers = core, rentsecure_be
properties: layers = properties, rentsecure_be
...
```

This means each app is allowed to import from itself and `rentsecure_be`. However, the tool reports 0 violations despite clear cross-app imports. Possible reasons:

1. **Tool limitation:** `lint-imports` may be excluding files that contain violations (e.g., management commands, tests).
2. **Squashed modules:** The `squashed_modules` configuration may be affecting layer resolution.
3. **Contract scope:** The contracts only check for "illegal chains" from outer to inner layers, not all cross-app imports.

**Recommendation:** Reconfigure import-linter to enforce stricter contracts or supplement with AST-based architecture tests.
