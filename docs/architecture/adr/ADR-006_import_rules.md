# ADR-006: Import Rules and Architecture Enforcement

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

As the codebase grows, maintaining clean boundaries between modules becomes increasingly difficult. Without enforcement, developers will inadvertently create cross-module dependencies, leading to:
- Circular imports
- Tight coupling between modules
- Difficulty in testing modules in isolation
- Inability to extract services later

---

## Decision

RentSecure uses **import-linter** to enforce architecture rules in CI.

**Key rules:**
- Apps cannot import from other apps directly
- Dependencies flow inward (presentation → application → domain)
- `shared/` must not import from `apps/`
- `platform/` must not import from `apps/`
- All violations block CI

---

## Alternatives Considered

### 1. Manual Code Review

**Description:** Rely on code review to enforce architecture rules.

**Pros:**
- No tooling overhead
- Human judgment for edge cases

**Cons:**
- Inconsistent enforcement
- High reviewer burden
- Easy to miss violations in large PRs
- No automated regression prevention

**Decision:** Rejected. Unreliable at scale.

### 2. Pylint/Ruff Custom Rules

**Description:** Write custom pylint or ruff rules to enforce boundaries.

**Pros:**
- Integrated with existing linting
- Fast execution

**Cons:**
- Complex to write custom rules
- Hard to maintain
- Limited expressiveness for complex rules

**Decision:** Rejected. import-linter is purpose-built for this.

### 3. Import-Linter (Selected)

**Description:** Use import-linter to enforce layer and container boundaries.

**Pros:**
- Purpose-built for architecture enforcement
- Declarative configuration
- Supports layers and containers
- Fast execution
- Good error messages
- Integrates with CI

**Cons:**
- Requires configuration maintenance
- False positives for edge cases

**Decision:** Accepted. Best tool for the job.

---

## Consequences

### Positive
- Architecture violations are caught in CI
- Consistent enforcement across the team
- Prevents architectural drift
- Clear error messages for violations

### Negative
- Requires configuration maintenance
- Some legitimate patterns need exceptions
- Adds CI time (minimal)

### Neutral
- Exceptions are documented in ADRs
- Import-linter configuration is versioned

---

## References

- [Dependency Rules](../future/05_dependency_rules.md)
- [Layer Rules](../future/04_layer_rules.md)
- [Import-Linter Configuration](../../../import-linter.ini)
