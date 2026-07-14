# Architecture Dependency Audit

**Date:** 2026-07-14
**Scope:** RentSecureBE backend (340 Python files, 321 modules)
**Method:** AST-based static analysis + import-linter v1.6.0
**Status:** Analysis only — no source code modified

## Executive Summary

This document summarizes the complete architecture dependency audit for the RentSecureBE backend. The audit inspected every Python file in the repository and produced evidence-backed reports on module coupling, package dependencies, architecture violations, circular imports, dead modules, layering violations, import boundaries, and dependency hotspots.

## Overall Architecture Health

**Architecture Score: 42 / 100**

### Score Breakdown

| Category | Score | Weight | Weighted |
|----------|-------|--------|----------|
| Circular Dependencies | 100 | 10% | 10.0 |
| Dead Code | 60 | 10% | 6.0 |
| Import Matrix Clarity | 30 | 15% | 4.5 |
| Cross-App Dependencies | 20 | 20% | 4.0 |
| Boundary Violations | 25 | 20% | 5.0 |
| Hotspot Concentration | 30 | 15% | 4.5 |
| Metrics / Stability | 40 | 10% | 4.0 |
| **Total** | | | **42.0** |

### Health Assessment

- **Strengths:** No circular dependencies, clear app structure, active use of services layer in some areas.
- **Weaknesses:** Extreme centralization of `properties.models` and `core.models`, 53% cross-app coupling, many dead/placeholder modules, views contain business logic.

## Critical Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| 1 | **God Models** (`properties.models` fan-in: 74, `core.models` fan-in: 63) | Any change breaks 74+ modules | HIGH | Introduce DTOs, use `settings.AUTH_USER_MODEL` |
| 2 | **God View** (`core.views` fan-out: 13) | Business logic scattered across views | HIGH | Extract services, split viewsets |
| 3 | **Notification Hub** (`whatsapp_service` fan-in: 21) | Hidden coupling across 6 apps | HIGH | Define notification interface in shared |
| 4 | **Bidirectional App Coupling** (core ↔ properties) | Refactoring is extremely risky | HIGH | Introduce bounded context boundaries |
| 5 | **Cross-App Signal Handlers** (`properties.signals` fan-out: 10) | Runtime coupling, hard to test | MEDIUM | Convert to explicit service calls |

## Medium Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| 6 | **Payment Service Leakage** (`cashfree_service` touches 3 apps) | Payment logic scattered | MEDIUM | Move to dedicated payments app or interface |
| 7 | **Dead Repositories** (4 unused repository modules) | Dead code confusion | MEDIUM | Remove or integrate |
| 8 | **Dead Services** (10 unused service modules) | Dead code confusion | MEDIUM | Remove or integrate |
| 9 | **Import-Linter False Negatives** | Architecture rules not enforced | MEDIUM | Reconfigure contracts, add AST tests |
| 10 | **Management Command Coupling** (14 cross-app imports) | Commands bypass service layer | MEDIUM | Use services in commands |

## Low Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| 11 | **Placeholder Modules** (10 empty modules) | Codebase clutter | LOW | Document as intentional or remove |
| 12 | **Shared Underutilization** | Duplicate utilities across apps | LOW | Migrate common utils to shared |
| 13 | **Test Coupling** (high fan-out in test modules) | Tests break on API changes | LOW | Keep tests focused, use factories |

## Top 20 Recommendations

1. **P0:** Split `core/views.py` into focused viewsets or move business logic to services.
2. **P0:** Define a `NotificationService` interface in `shared/interfaces.py` and refactor all direct imports of `whatsapp_service`.
3. **P1:** Introduce DTOs for `properties.models` to reduce direct model imports from 74 to < 20.
4. **P1:** Refactor `properties/signals/__init__.py` to use domain events instead of direct service calls.
5. **P1:** Isolate `rentsecure_be/services/cashfree_service.py` behind a payment interface.
6. **P1:** Replace direct `core.models` imports in `properties/models/*` with `settings.AUTH_USER_MODEL` string references.
7. **P2:** Remove or integrate the 4 dead repository modules in `properties/repositories/`.
8. **P2:** Remove or integrate the 10 dead service modules.
9. **P2:** Reconfigure `import-linter.ini` to enforce strict app isolation contracts.
10. **P2:** Add AST-based architecture tests in `tests/test_architecture_contract/`.
11. **P2:** Consolidate `rentsecure_be/type_compat.py` usage — consider making it a project-wide standard.
12. **P3:** Document the 10 placeholder modules as intentional future work or remove them.
13. **P3:** Move `ReferralService` from `core/services/` to `referral_and_earn/apps.py`.
14. **P3:** Introduce a `properties.services.rent_record_api` for cross-app rent record access.
15. **P3:** Create a `shared/base_models` module for common Django model utilities.
16. **P3:** Convert `management/commands/` to use service layer instead of direct model imports.
17. **P3:** Evaluate whether `ai_assistant` should be a separate bounded context or part of `smartbot`.
18. **P3:** Move document generation logic from `documents/` to `properties/` or a shared service.
19. **P3:** Implement `shared/domain_events.py` for event-driven cross-app communication.
20. **P3:** Set up CI enforcement for import-linter and architecture tests.

## Refactoring Priority

### Phase 1: Stabilize Foundation (Weeks 1-4)
- Split `core/views.py`
- Introduce `NotificationService` interface
- Replace direct `core.models` imports with `AUTH_USER_MODEL` strings
- Reconfigure import-linter

### Phase 2: Decouple Domains (Weeks 5-12)
- Introduce DTOs for `properties.models`
- Refactor `properties.signals` to use domain events
- Isolate payment services
- Remove dead repositories and services

### Phase 3: Consolidate Boundaries (Weeks 13-20)
- Enforce strict import-linter contracts in CI
- Add AST-based architecture tests
- Migrate common utilities to `shared`
- Document remaining cross-app boundaries

## Suggested Execution Order

1. **Immediate (Week 1):**
   - Run import-linter in CI on every PR
   - Add `# noqa: architecture` comments to intentional cross-app imports
   - Document placeholder modules

2. **Short-term (Weeks 2-4):**
   - Split `core/views.py`
   - Create `NotificationService` interface
   - Replace `core.models` imports in `properties/models/`

3. **Medium-term (Weeks 5-12):**
   - Introduce DTOs for cross-app data exchange
   - Refactor signal handlers to services
   - Remove dead code

4. **Long-term (Weeks 13-20):**
   - Migrate to bounded context architecture
   - Implement domain events
   - Set up architecture scorecard in CI

## Report Index

| Report | Description |
|--------|-------------|
| `01_dependency_graph.md` | Package, app, and module dependency graphs with Mermaid diagrams |
| `02_import_matrix.md` | Per-package import matrix with fan-in/fan-out metrics |
| `03_circular_dependencies.md` | Circular dependency analysis (none found) |
| `04_cross_app_dependencies.md` | Detailed analysis of all 205 cross-app imports |
| `05_architecture_boundary_violations.md` | Layer and boundary violation audit |
| `06_dead_modules.md` | Dead code and placeholder module inventory |
| `07_hotspots.md` | Top 25 highest-coupled files with risk ratings |
| `08_import_linter_audit.md` | import-linter validation and contract audit |
| `09_dependency_metrics.md` | Quantitative dependency metrics and stability estimates |

## Evidence

All claims in this audit are backed by:
- `docs/architecture/audit_data.json` — Complete AST-based dependency data
- `scripts/arch_audit.py` — Reproducible analysis script
- Direct file inspections of hotspot modules
- `lint-imports` (import-linter v1.6.0) execution logs

## Validation

To reproduce this analysis:
```bash
python3 scripts/arch_audit.py
```

To run import-linter:
```bash
lint-imports --config import-linter.ini
```
