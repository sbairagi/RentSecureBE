# ADR-008: Shared Module Rules

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

The `shared/` directory contains utilities used across the codebase. Without strict rules, `shared/` tends to accumulate:
- Business logic that bleeds across contexts
- Django-specific code that shouldn't be generic
- App-specific utilities that belong in the app
- Uncontrolled growth making it a "junk drawer"

---

## Decision

`shared/` contains **only generic, reusable code with no business logic and no app imports**.

**Rules:**
1. `shared/` must not contain RentSecure-specific logic
2. `shared/` must not import from any Django app
3. `shared/` must not contain Django model definitions
4. `shared/` must not contain business services
5. `shared/` code must be usable without Django installed

**Allowed in `shared/`:**
- Base exception classes
- Domain event base class
- Abstract interface definitions (ports)
- Generic utilities (date, string, math)
- Shared enumerations
- Shared type definitions

---

## Alternatives Considered

### 1. Allow Business Logic in Shared

**Description:** Let `shared/` contain common business utilities.

**Pros:**
- Avoids duplication across contexts
- Easy to share common logic

**Cons:**
- `shared/` becomes a dumping ground
- Business logic leaks across context boundaries
- Changes to shared affect all contexts
- Violates bounded context isolation

**Decision:** Rejected. Creates coupling.

### 2. No Shared Module

**Description:** Each context has its own utilities.

**Pros:**
- Complete isolation
- No coupling risk

**Cons:**
- Code duplication across contexts
- Inconsistent implementations
- Hard to maintain common patterns

**Decision:** Rejected. Too much duplication.

### 3. Strict Shared Module (Selected)

**Description:** `shared/` contains only generic, reusable code. Business logic stays in contexts.

**Pros:**
- Clear boundary
- No business logic leakage
- Generic code is truly reusable
- Easy to maintain

**Cons:**
- Some duplication across contexts
- Requires discipline to keep shared clean

**Decision:** Accepted. Best balance.

---

## Consequences

### Positive
- `shared/` remains clean and focused
- No business logic leakage across contexts
- Generic utilities are truly reusable
- Easy to understand what shared provides

### Negative
- Some duplication across contexts
- Requires discipline to keep shared clean
- Developers may push inappropriate code to shared

### Neutral
- Common patterns are duplicated but localized
- Each context owns its business logic

---

## References

- [Layer Rules](../future/04_layer_rules.md)
- [Dependency Rules](../future/05_dependency_rules.md)
