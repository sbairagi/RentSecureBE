# ADR-005: Shared Kernel Rules

**Status:** Accepted
**Date:** 2026-07-19
**Deciders:** Chief Software Architect, Staff Engineer, Platform Team Lead
**Supersedes:** ADR-008 (v1.0 — Shared Module Rules)

---

## Context

The `shared/` directory contains utilities used across the codebase. Without strict rules, `shared/` tends to accumulate:
- Business logic that bleeds across contexts
- Django-specific code that shouldn't be generic
- App-specific utilities that belong in the app
- Uncontrolled growth making it a "junk drawer"

In v1.0, `shared/` already had naming conflicts (`ValidationError` in both `exceptions.py` and `types.py`) and unused code. The v1.0 document said "shared/ is sacred" but provided no enforcement mechanism.

The v1.1 review found that `rentsecure_be/type_compat.py` was imported by 20+ files across 6 apps, creating hard dependencies on the project config layer. Moving `type_compat.py` to `shared/` in Phase -1 is the first test of the shared kernel rules.

---

## Decision

RentSecureBE uses a **strict shared kernel** with automated enforcement via architecture tests.

### What Belongs in `shared/`

| Category | Examples | Rationale |
|----------|----------|-----------|
| Base exception classes | `ValidationError`, `BusinessRuleViolation` | Truly generic, no Django imports |
| Domain event base class | `DomainEvent`, `EventMetadata` | Used by all contexts |
| Abstract interface definitions | `PaymentGateway` (port), `NotificationChannel` (port) | Contracts between contexts |
| Generic utilities | Date helpers, string helpers, math helpers | Pure functions, no Django |
| Shared enumerations | `PaymentStatus`, `UserRole` | Used across multiple contexts |
| Shared type definitions | `Money`, `PhoneNumber` | Type safety, no business logic |
| Encrypted field types | `EncryptedCharField`, `EncryptedTextField` | Security infrastructure, used by `payments/` |

### What Does NOT Belong in `shared/`

| Category | Examples | Rationale |
|----------|----------|-----------|
| Django model definitions | `User`, `OwnerBankDetails` | Domain concerns, belong in owning context |
| Business services | `PaymentService`, `NotificationService` | Domain logic, belong in owning context |
| Django-specific utilities | `django.conf.settings` wrappers | Configuration, belong in `platform/` or `rentsecure_be/` |
| App-specific utilities | `properties.utils.export_utils` | Belongs in owning app |
| Third-party SDK wrappers | `cashfree_client`, `razorpay_client` | Belong in adapter modules |

### Enforcement Rules

1. **No `django` imports in `shared/`** (except `django.db.models` for abstract base classes if absolutely necessary — requires ADR)
2. **No app imports in `shared/`** — `shared/` must not import from `core/`, `properties/`, `payments/`, etc.
3. **No business logic in `shared/`** — only pure functions and abstract interfaces
4. **Every addition to `shared/` requires an ADR** — no exceptions
5. **Architecture test `test_shared_purity.py`** fails if any `shared/` file imports from `django` or any app

### Resolution of v1.0 Naming Conflicts

- `shared/exceptions.py` and `shared/types.py` both defined `ValidationError` — resolved by keeping only `shared/exceptions.py` and removing duplicate from `types.py`
- Unused code in `shared/` removed in Phase 0

---

## Alternatives Considered

### 1. Allow Business Logic in `shared/`

**Description:** Let `shared/` contain common business utilities shared across contexts.

**Pros:**
- Avoids duplication across contexts
- Easy to share common logic

**Cons:**
- `shared/` becomes a dumping ground for domain logic
- Business logic leaks across context boundaries
- Changes to shared affect all contexts
- Violates bounded context isolation
- `shared/` grows without bound

**Decision:** Rejected. Creates coupling and violates bounded context isolation.

### 2. No Shared Module

**Description:** Each context has its own utilities. No `shared/` directory.

**Pros:**
- Complete isolation between contexts
- No coupling risk

**Cons:**
- Code duplication across contexts (e.g., `EncryptedCharField` would exist in both `payments/` and `core/`)
- Inconsistent implementations of common patterns
- Hard to maintain common utilities (bug fixes in 5 places)
- Violates DRY principle for truly generic code

**Decision:** Rejected. Too much duplication for generic utilities like encrypted fields and base exceptions.

### 3. Strict Shared Kernel (Selected)

**Description:** `shared/` contains only generic, reusable code. Business logic stays in contexts. Enforced by architecture tests.

**Pros:**
- Clear boundary between shared and domain-specific code
- No business logic leakage
- Generic code is truly reusable
- Easy to understand what shared provides
- Automated enforcement prevents drift

**Cons:**
- Some duplication across contexts for domain-adjacent utilities
- Requires discipline to keep shared clean
- Developers may push inappropriate code to shared (mitigated by ADR requirement)

**Decision:** Accepted. Best balance of reuse and isolation.

---

## Consequences

### Positive
- `shared/` remains clean and focused
- No business logic leakage across contexts
- Generic utilities are truly reusable
- Easy to understand what shared provides
- Automated enforcement prevents drift
- `type_compat.py` move to `shared/` in Phase -1 validates the rules

### Negative
- Some duplication across contexts for domain-adjacent utilities
- Requires discipline to keep shared clean
- ADR requirement for every addition adds process overhead
- `EncryptedCharField` in `shared/` is a borderline case (security infrastructure, not business logic)

### Neutral
- `shared/` is versioned with the codebase (no separate package)
- `shared/` imports are allowed by all contexts per the dependency matrix
- `shared/` does not depend on any app or Django settings

---

## Migration Notes

### Phase -1: Move `type_compat.py`
- Move `rentsecure_be/type_compat.py` → `shared/type_compat.py`
- Update 20+ importers across 6 apps
- Keep deprecated shim in `rentsecure_be/type_compat.py` for one release cycle
- Validates that `shared/` can hold infrastructure utilities

### Phase 0: Add Encrypted Fields
- Add `EncryptedCharField` and `EncryptedTextField` to `shared/fields.py`
- Used by `payments/models.py` for `bank_account_number` and `ifsc_code`
- Validates that `shared/` can hold security infrastructure

### Phase 0: Resolve Naming Conflicts
- Remove duplicate `ValidationError` from `shared/types.py`
- Keep only `shared/exceptions.py` version
- Remove unused code from `shared/`

### Enforcement
- `tests/architecture/test_shared_purity.py` runs on every commit
- Test fails if any `shared/` file imports from `django` or any app
- `import-linter.ini` layer configuration: `shared/` cannot import from any layer

---

## Future Evolution

### Short-term (Phase 6)
- `shared/` may contain `domain_events.py` base classes
- `shared/` may contain repository base classes (if repository pattern is adopted)

### Medium-term
- If `shared/` grows beyond 20 files, consider splitting into `shared/types/`, `shared/exceptions/`, `shared/interfaces/`
- `shared/` may be extracted to a separate Python package if multiple services need it

### Long-term
- `shared/` remains a strict kernel with no business logic
- Every addition still requires ADR
- `shared/` is one of the most protected modules in the codebase

---

## References

- [Architecture v1.1 Release Candidate — Finding AD-07, FM-04](../../../ARCHITECTURE_V1.1_RELEASE_CANDIDATE.md)
- [Implementation Master Plan — Phase -1, Phase 0](../../../ARCHITECTURE_V1.1_IMPLEMENTATION_MASTER_PLAN.md)
- [Import Rules](./ADR-006_import_rules.md)
- [Testing Strategy](./ADR-009_testing_strategy.md)
