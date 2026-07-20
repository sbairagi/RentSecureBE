# ADR-006: Import Rules

**Status:** Accepted
**Date:** 2026-07-19
**Deciders:** Chief Software Architect, Staff Engineer, Platform Team Lead
**Supersedes:** ADR-006 (v1.1 — Import Rules)

---

## Context

The v1.0 `import-linter.ini` configuration created a God-layer anti-pattern by allowing every app to import from `rentsecure_be/`. This meant:
- 145+ cross-app import violations were not caught by import-linter
- Apps used `rentsecure_be/` as a hidden service locator
- `rentsecure_be/services/` contained `cashfree_service.py`, `razorpay_service.py`, `leegality_service.py`, and `i18n_service.py` imported by 9+ files across 6 apps
- `rentsecure_be/utils/` contained `cashfree_payout.py` and `export_utils.py` imported across multiple apps
- The architecture compliance report showed "100/100 COMPLIANT" because import-linter was configured to allow the violations

Additional dependency matrix inconsistencies in v1.0:
- Row `rent/` listed `notification/` and `finance/` as "cannot import" but `rent/` was deferred
- Row `payment/` listed `property/` as "cannot import" yet payment adapters needed `RentRecord` data
- Row `ai/` listed `rent/` as a dependency but `rent/` did not exist
- Matrix omitted `ai_assistant/` and `dashboard/` entirely

The v2.0 import rules must eliminate the God-layer anti-pattern, correct the dependency matrix, and enforce boundaries via architecture tests.

---

## Decision

RentSecureBE uses **import-linter with a corrected layer configuration** and **AST-based architecture tests** to enforce import boundaries.

### Corrected Allowed Import Matrix (v2.0)

| Source | shared | platform | identity | subscription | property | payment | notification | document | finance | referral | dashboard |
|--------|--------|----------|----------|--------------|----------|---------|--------------|----------|---------|----------|-----------|
| **shared** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **platform** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **identity** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **subscription** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **property** | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **payment** | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **notification** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **document** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **finance** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ |
| **referral** | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **dashboard** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ |
| **ai_assistant** | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ |

### Key Rules

1. **No app may import from `rentsecure_be/`** (except `rentsecure_be/` itself). This is the most critical rule.
2. **`payment/` may import from `property/`** (needs `RentRecord` data). This corrects the v1.0 matrix error.
3. **`notification/` may NOT import from `property/`** directly. Domain notification triggers live in `properties/services/` and call `notification/` adapters.
4. **`ai_assistant/` is deferred** — partial dependencies shown, but no active enforcement until activated.
5. **`rent/` is removed** from the matrix entirely. Rent logic stays in `properties/`.
6. **`config/` is removed** from the matrix. Configuration stays in `rentsecure_be/`.
7. **`dashboard/` is deferred / not deployed** — not in `INSTALLED_APPS`.

### Enforcement Mechanism

1. **import-linter.ini** is rewritten in Phase 0 without `rentsecure_be` as an allowed layer.
2. **Architecture tests** run on every commit:
   - `test_import_rules.py`: No `razorpay`/`cashfree` imports in non-adapter files
   - `test_layer_compliance.py`: Views do not import models from other apps
   - `test_sdk_placement.py`: Payment SDKs only in `payments/adapters/`
   - `test_rentsecure_be_boundary.py`: No app imports from `rentsecure_be/`
   - `test_shared_purity.py`: `shared/` does not import Django or apps
   - `test_circular_deps.py`: No circular dependencies
3. **All violations block CI.** No exceptions without ADR.

---

## Alternatives Considered

### 1. Keep `rentsecure_be/` as Allowed Layer (v1.0 Approach)

**Description:** Continue allowing all apps to import from `rentsecure_be/` as a utility layer.

**Pros:**
- Easy for developers (one place for utilities)
- No need to move `cashfree_payout.py`, `export_utils.py`, etc.

**Cons:**
- `rentsecure_be/` becomes a God module (21 modules importing from it)
- Prevents true modularity
- Cannot extract `payments/` as a microservice without `rentsecure_be/`
- Architectural violations are "allowed" by import-linter
- Violates the principle of explicit dependencies

**Decision:** Rejected. Creates God-layer anti-pattern and prevents future service extraction.

### 2. Manual Code Review Only

**Description:** Rely on code review to enforce import boundaries.

**Pros:**
- No tooling overhead
- Human judgment for edge cases

**Cons:**
- Inconsistent enforcement
- High reviewer burden
- Easy to miss violations in large PRs
- No automated regression prevention
- import-linter compliance report was "100/100" despite 145+ violations

**Decision:** Rejected. Unreliable at scale.

### 3. import-linter with Corrected Matrix (Selected)

**Description:** Rewrite `import-linter.ini` to enforce the corrected dependency matrix. Add AST-based architecture tests for rules import-linter cannot express.

**Pros:**
- Purpose-built for architecture enforcement
- Declarative configuration
- Fast execution
- Good error messages
- Integrates with CI
- Architecture tests catch violations import-linter misses (e.g., SDK placement, god views)

**Cons:**
- Requires configuration maintenance
- False positives for edge cases (mitigated by ADR process)
- Adds CI time (minimal)

**Decision:** Accepted. Best tool for the job. Combined with architecture tests, provides comprehensive enforcement.

---

## Consequences

### Positive
- Architecture violations are caught in CI (not just in code review)
- `rentsecure_be/` boundary is enforced: no app imports from project config
- Payment SDKs are confined to `payments/adapters/`
- `shared/` purity is enforced
- Circular dependencies are detected before they cause runtime errors
- Import-linter compliance report is meaningful (0 violations = truly compliant)

### Negative
- Requires configuration maintenance for `import-linter.ini`
- Some legitimate patterns need exceptions (handled via ADR)
- Adds CI time (minimal, ~30 seconds)
- Developers must learn the dependency matrix

### Neutral
- Exceptions are documented in ADRs
- Import-linter configuration is versioned
- Architecture tests are colocated in `tests/architecture/`

---

## Migration Notes

### Phase -1: Break Circular Dependencies
- Move `type_compat.py` from `rentsecure_be/` to `shared/`
- Update 20+ importers
- Keep deprecated shim in `rentsecure_be/`
- Add `test_rentsecure_be_boundary.py` (fails before fix, passes after)

### Phase 0: Rewrite import-linter.ini
- Remove `rentsecure_be` as allowed layer for all apps
- Add all apps per v2.0 matrix
- Correct `payment/ → property/` dependency
- Remove `rent/` row entirely
- Add `ai_assistant/` row (deferred)
- Remove `config/` as separate app
- Add all 8 architecture test files to `tests/architecture/`
- Verify `import-linter check` passes with 0 violations

### Ongoing
- Every PR runs `import-linter check` and `pytest tests/architecture/`
- New apps require `import-linter.ini` update + ADR approval
- Violations block CI merge

---

## Future Evolution

### Short-term (Phase 6)
- Dependency matrix may expand if new bounded contexts are activated (`ai/`, `dashboard/`)
- Architecture tests may add new rules (e.g., no `requests` calls outside `platform/`)

### Medium-term
- If microservices are extracted, import-linter rules become service-to-service API contracts
- `rentsecure_be/` may become a true deployment configuration package (no Python code)

### Long-term
- Import rules remain stable; no new apps added without ADR
- Architecture tests evolve to cover new patterns (e.g., event bus usage)

---

## References

- [Architecture v2.0 Release Candidate — Finding AD-06, CD-01](../../../ARCHITECTURE_V2.0_RELEASE_CANDIDATE.md)
- [Implementation Master Plan — Phase -1, Phase 0](../../../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [import-linter.ini](../../../import-linter.ini)
- [Shared Kernel Rules](./ADR-005_shared_kernel_rules.md)
