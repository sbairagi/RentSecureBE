# 09 Dependency Metrics

## Summary

**Analysis scope:** 340 Python files, 321 modules (excluding migrations, tests, management by some tools)
**Total imports:** 387
**Total cross-app imports:** 205
**Total dead modules:** 46 (19 actionable)

## Core Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Total modules | 321 | Excludes migrations, `__pycache__`, `.venv`, `.nox` |
| Total imports | 387 | Project-internal imports only |
| Average imports/module | 1.21 | Low average, but highly skewed distribution |
| Average fan-in | 1.21 | |
| Average fan-out | 1.21 | |
| Total cross-app imports | 205 | 53% of all imports cross app boundaries |
| Circular dependencies | 0 | No cycles detected |

## Most Imported Modules (Top 10)

| Rank | Module | Fan In | % of Total Imports |
|------|--------|--------|-------------------|
| 1 | `properties.models` | 74 | 19.1% |
| 2 | `core.models` | 63 | 16.3% |
| 3 | `rentsecure_be.type_compat` | 36 | 9.3% |
| 4 | `notification.services.whatsapp_service` | 21 | 5.4% |
| 5 | `core.services.base` | 8 | 2.1% |
| 6 | `properties.feature_enforcer` | 7 | 1.8% |
| 7 | `properties.models.rent_record_models` | 6 | 1.6% |
| 8 | `rentsecure_be.services.cashfree_service` | 6 | 1.6% |
| 9 | `conftest` | 6 | 1.6% |
| 10 | `notification.utils` | 6 | 1.6% |

**Observation:** The top 4 most imported modules account for 50.1% of all imports. This indicates extreme centralization.

## Most Dependent Modules (Top 10)

| Rank | Module | Fan Out | Notes |
|------|--------|---------|-------|
| 1 | `core.views` | 13 | God view with 62 symbols |
| 2 | `properties.signals` | 10 | Signal handlers with high coupling |
| 3 | `smartbot.tests` | 8 | Test module |
| 4 | `notification.tests.test_notification_services` | 6 | Test module |
| 5 | `properties.tests.test_unit_views` | 6 | Test module |
| 6 | `properties.views.rent_record_views` | 6 | High fan-out view |
| 7 | `ai_assistant.tests.test_services` | 5 | Test module |
| 8 | `ai_assistant.views` | 5 | View importing 4 apps |
| 9 | `properties.models.unit_models` | 5 | Model with many internal imports |
| 10 | `properties.tests.test_caretaker_views` | 5 | Test module |

**Observation:** 6 of the top 10 most-dependent modules are test modules. Production code with high fan-out is concentrated in views and signal handlers.

## App-Level Metrics

| App | Modules | Imports | Imported By | Symbols | Cross-App | Instability |
|-----|---------|---------|-------------|---------|-----------|-------------|
| properties | 111 | 162 | 130 | 2332 | 38 | 0.55 |
| core | 25 | 51 | 86 | 532 | 54 | 0.37 |
| notification | 28 | 39 | 57 | 277 | 14 | 0.41 |
| smartbot | 19 | 26 | 16 | 187 | 4 | 0.62 |
| finance | 12 | 16 | 7 | 116 | 3 | 0.70 |
| rentsecure_be | 16 | 7 | 54 | 151 | 9 | 0.11 |
| ai_assistant | 13 | 18 | 9 | 103 | 4 | 0.67 |
| dashboard | 4 | 3 | 1 | 14 | 2 | 0.75 |
| documents | 11 | 12 | 6 | 156 | 3 | 0.67 |
| referral_and_earn | 5 | 3 | 3 | 11 | 1 | 0.50 |
| shared | 9 | 1 | 4 | 41 | 0 | 0.80 |
| management | 16 | 27 | 0 | 94 | 14 | 1.00 |
| tests | 11 | 13 | 3 | 227 | 5 | 0.71 |
| tools | 8 | 4 | 4 | 166 | 0 | 0.50 |
| scripts | 29 | 1 | 1 | 761 | 1 | 0.50 |

**Instability = Fan Out / (Fan In + Fan Out)**

## Architecture Stability Analysis

### Most Stable Apps (Low Instability)

| App | Instability | Rationale |
|-----|-------------|-----------|
| `rentsecure_be` | 0.11 | Infrastructure layer, imported by many but imports few |
| `core` | 0.37 | Foundation app, widely imported |
| `notification` | 0.41 | Mid-tier, moderate coupling |
| `referral_and_earn` | 0.50 | Small, isolated app |
| `shared` | 0.80 | Utility layer, should be stable (but underutilized) |

### Most Unstable Apps (High Instability)

| App | Instability | Rationale |
|-----|-------------|-----------|
| `management` | 1.00 | Orchestration layer, imports everything, imported by nobody |
| `dashboard` | 0.75 | Thin app, imports 2 other apps |
| `tests` | 0.71 | Test suite, imports production code |
| `ai_assistant` | 0.67 | New app, imports many existing apps |
| `documents` | 0.67 | Thin app, imports core and properties |

## Abstractness Estimate

**Abstractness** = (abstract classes + interfaces) / (total classes)

Based on `shared/interfaces.py`, there are 3 protocols (`Repository`, `Service`, `EventBus`) defined. The codebase has hundreds of concrete classes.

**Estimated Abstractness:** ~2-3%

This is very low. The codebase is heavily concrete with minimal abstraction.

## Coupling Score Estimate

**Afferent Coupling (Fan In):** Total fan-in across all modules = 387
**Efferent Coupling (Fan Out):** Total fan-out across all modules = 387
**Total Coupling:** 774

**Normalized Coupling Score:** 774 / 321 modules = 2.41 imports per module

**Cross-App Coupling Ratio:** 205 / 387 = 53%

This indicates that over half of all imports cross app boundaries, which is a significant architecture smell.

## Dependency Hotspot Concentration

**Gini Coefficient Approximation:**
- Top 10 modules account for ~60% of all imports
- Bottom 50% of modules account for ~5% of all imports

This indicates a highly skewed dependency distribution where a small number of modules are critical infrastructure.

## Recommendations

1. **Reduce `properties.models` coupling:** Introduce DTOs and service interfaces to bring fan-in from 74 to < 20.
2. **Reduce `core.models` coupling:** Use string references for ForeignKeys. Bring fan-in from 63 to < 30.
3. **Decouple `notification.services.whatsapp_service`:** Create a notification interface. Reduce fan-in from 21 to < 5.
4. **Refactor `core.views`:** Split into multiple viewsets. Reduce fan-out from 13 to < 5.
5. **Increase abstractness:** Define more interfaces in `shared/interfaces.py`. Target abstractness > 10%.
6. **Reduce cross-app coupling:** Target cross-app ratio < 20% (currently 53%).
