# 07 Hotspots

## Summary

This report identifies the top 25 highest-coupled files in the RentSecureBE codebase. Files are ranked by a composite score of Fan In, Fan Out, Total Imports, Cross-App Imports, and Complexity.

**Analysis scope:** 321 modules, 387 total imports, 205 cross-app imports.

## Ranking Methodology

1. **Primary sort:** Total Imports (Fan In + Fan Out) descending
2. **Secondary sort:** Fan Out descending
3. **Tertiary sort:** Cross-App Imports descending
4. **Complexity proxy:** Number of public symbols

## Top 25 Hotspots

| Rank | Module | Fan In | Fan Out | Total | Cross-App | Symbols | Risk Level |
|------|--------|--------|---------|-------|-----------|---------|------------|
| 1 | `properties.models` | 74 | 0 | 74 | 38 | 1 | **CRITICAL** |
| 2 | `core.models` | 63 | 1 | 64 | 54 | 68 | **CRITICAL** |
| 3 | `rentsecure_be.type_compat` | 36 | 0 | 36 | 36 | 3 | **HIGH** |
| 4 | `notification.services.whatsapp_service` | 21 | 0 | 21 | 14 | 15 | **HIGH** |
| 5 | `core.views` | 3 | 13 | 16 | 5 | 62 | **CRITICAL** |
| 6 | `properties.signals` | 3 | 10 | 13 | 4 | 27 | **HIGH** |
| 7 | `rentsecure_be.services.cashfree_service` | 6 | 4 | 10 | 9 | 22 | **HIGH** |
| 8 | `smartbot.tests` | 0 | 8 | 8 | 0 | 43 | MEDIUM |
| 9 | `notification.services.extra_charge_reminders` | 4 | 4 | 8 | 2 | 11 | HIGH |
| 10 | `notification.services.rent_notify_service` | 5 | 3 | 8 | 5 | 16 | HIGH |
| 11 | `conftest` | 6 | 2 | 8 | 6 | 120 | MEDIUM |
| 12 | `properties.feature_enforcer` | 7 | 1 | 8 | 1 | 19 | MEDIUM |
| 13 | `core.services.base` | 8 | 0 | 8 | 0 | 7 | MEDIUM |
| 14 | `properties.views.rent_record_views` | 1 | 6 | 7 | 6 | 27 | HIGH |
| 15 | `smartbot.actions` | 3 | 4 | 7 | 4 | 13 | HIGH |
| 16 | `properties.utils.utils` | 3 | 4 | 7 | 2 | 28 | MEDIUM |
| 17 | `properties.views.unit_views` | 4 | 3 | 7 | 4 | 21 | HIGH |
| 18 | `documents.views` | 4 | 3 | 7 | 3 | 23 | MEDIUM |
| 19 | `properties.models.rent_record_models` | 6 | 1 | 7 | 7 | 48 | HIGH |
| 20 | `properties.tests.test_unit_views` | 0 | 6 | 6 | 1 | 214 | MEDIUM |
| 21 | `notification.tests.test_notification_services` | 0 | 6 | 6 | 0 | 51 | MEDIUM |
| 22 | `notification.services.voice_note_service` | 3 | 3 | 6 | 3 | 6 | MEDIUM |
| 23 | `notification.utils` | 6 | 0 | 6 | 5 | 7 | MEDIUM |
| 24 | `notification.models` | 6 | 0 | 6 | 3 | 9 | MEDIUM |
| 25 | `tests.test_query_count` | 0 | 5 | 5 | 5 | 23 | MEDIUM |

## Critical Hotspot Analysis

### 1. `properties.models` (Rank 1)
- **Fan In:** 74 modules
- **Risk:** CRITICAL
- **Why it's a hotspot:** This is the central domain model package for the entire application. Every app that needs property data imports from here.
- **Impact:** Any change to `properties.models` has a blast radius of 74 modules. A breaking change here would cascade through the entire codebase.
- **Recommendation:** Introduce DTOs and service interfaces to reduce direct model imports. Consider splitting into bounded context packages.

### 2. `core.models` (Rank 2)
- **Fan In:** 63 modules
- **Risk:** CRITICAL
- **Why it's a hotspot:** Contains the User model and other core entities. Every app imports from here.
- **Impact:** Second-highest blast radius. Changes to User model or core entities affect 63 modules.
- **Recommendation:** Minimize cross-app imports by using string references (`settings.AUTH_USER_MODEL`) instead of direct imports. Move business logic out of models.

### 3. `rentsecure_be.type_compat` (Rank 3)
- **Fan In:** 36 modules
- **Risk:** HIGH
- **Why it's a hotspot:** A Python 3.12 compatibility shim that provides `typing.override`. It is imported by nearly every app.
- **Impact:** While low-risk itself, its high fan-in indicates a dependency on infrastructure details from domain layers.
- **Recommendation:** Consider making this a standard library backport available via `shared` or as a project-wide pre-commit hook.

### 4. `notification.services.whatsapp_service` (Rank 4)
- **Fan In:** 21 modules
- **Risk:** HIGH
- **Why it's a hotspot:** The WhatsApp service is the de facto notification hub. 21 modules across 6 apps import it directly.
- **Impact:** Changes to WhatsApp service signatures break 21 callers. It creates a hidden coupling between notification and all other domains.
- **Recommendation:** Create a notification service interface in `shared/interfaces.py`. Apps should depend on the interface, not the concrete implementation.

### 5. `core.views` (Rank 5)
- **Fan In:** 3 modules
- **Fan Out:** 13 modules
- **Risk:** CRITICAL
- **Why it's a hotspot:** 566 lines, 62 public symbols, imports 13 modules including payment gateways and notification services.
- **Impact:** This is a God View. It orchestrates authentication, payments, notifications, and reporting.
- **Recommendation:** Split into multiple viewsets or move business logic to dedicated services.

### 6. `properties.signals` (Rank 6)
- **Fan In:** 3 modules
- **Fan Out:** 10 modules
- **Risk:** HIGH
- **Why it's a hotspot:** 248 lines of signal handlers that import from notification, properties services, and properties utils.
- **Impact:** Signal handlers create implicit coupling. Changes to signal receiver signatures can break Django's signal dispatch.
- **Recommendation:** Convert signal handlers to explicit service calls. Consider using Django's `@receiver` decorator more carefully or move to event-driven architecture.

### 7. `rentsecure_be.services.cashfree_service` (Rank 7)
- **Fan In:** 6 modules
- **Fan Out:** 4 modules
- **Risk:** HIGH
- **Why it's a hotspot:** Payment service that imports from core, properties, and notification.
- **Impact:** Payment logic is scattered across apps. Cashfree service touches 3 domain apps.
- **Recommendation:** Move payment service to a dedicated `payments` app or keep in `rentsecure_be` but define strict interfaces.

### 8. `smartbot.tests` (Rank 8)
- **Fan In:** 0
- **Fan Out:** 8 modules
- **Risk:** MEDIUM
- **Why it's a hotspot:** Test module with 43 public symbols importing 8 modules.
- **Impact:** High test complexity. Changes to smartbot APIs require test updates across many modules.
- **Recommendation:** Keep tests focused and minimize test-to-test dependencies.

### 9. `notification.services.extra_charge_reminders` (Rank 9)
- **Fan In:** 4 modules
- **Fan Out:** 4 modules
- **Risk:** HIGH
- **Why it's a hotspot:** Crosses notification and properties boundaries.
- **Recommendation:** Use domain events to decouple.

### 10. `notification.services.rent_notify_service` (Rank 10)
- **Fan In:** 5 modules
- **Fan Out:** 3 modules
- **Risk:** HIGH
- **Why it's a hotspot:** Central notification service imported by core, rentsecure_be, and properties.
- **Recommendation:** Define notification interface in shared.

## Hotspot Distribution by App

| App | Hotspots in Top 25 | Percentage |
|-----|-------------------|------------|
| properties | 8 | 32% |
| notification | 6 | 24% |
| core | 3 | 12% |
| rentsecure_be | 2 | 8% |
| smartbot | 2 | 8% |
| documents | 1 | 4% |
| conftest | 1 | 4% |
| tests | 1 | 4% |
| shared | 0 | 0% |

## High-Risk Patterns

1. **God Models:** `properties.models` and `core.models` are imported by 74 and 63 modules respectively.
2. **Service Hub:** `notification.services.whatsapp_service` is imported by 21 modules.
3. **God View:** `core.views` imports 13 modules and contains 62 public symbols.
4. **Cross-App Signal Handlers:** `properties.signals` imports 10 modules from 3 apps.
5. **Payment Service Coupling:** `rentsecure_be.services.cashfree_service` touches 3 domain apps.

## Recommendations Priority

| Priority | Action | Target Hotspots |
|----------|--------|-----------------|
| P0 | Split `core.views` into focused viewsets | #5 |
| P0 | Introduce notification service interface | #4, #9, #10 |
| P1 | Introduce DTOs for `properties.models` | #1 |
| P1 | Refactor `properties.signals` to use events | #6 |
| P1 | Isolate payment services with interfaces | #7 |
| P2 | Remove dead repositories and services | Various |
| P2 | Consolidate `rentsecure_be.type_compat` usage | #3 |
