# Foundation Infrastructure

**Phase:** Phase 1 — Foundation Infrastructure
**Status:** Implemented
**Date:** 2026-07-21

## Purpose

The Foundation Infrastructure layer provides generic, reusable building blocks for the entire RentSecure backend. These components are intentionally free of business logic and can be safely imported by any module.

## Folder Layout

```
core/
  infrastructure/
    __init__.py
    constants.py      # Generic infrastructure constants (timeouts, retries, cache TTLs)
    enums.py          # Base enum helpers (StringEnum, IntEnum)
    exceptions.py     # Infrastructure exception hierarchy
    ids.py            # EntityId base value object
    typing.py         # Shared TypeVar definitions
  config/
    __init__.py       # Re-exports config helpers
    constants.py      # Environment name constants
    settings.py       # Thin wrappers around decouple.config
  shared/
    __init__.py       # Re-exports shared primitives
    time.py           # UTC time utilities (Django timezone aware)
    ids.py            # UUID generation and validation utilities
    result.py         # Generic Result[T] outcome type
    exceptions.py     # Domain exception hierarchy
    pagination.py     # Generic PageRequest / PageResponse DTOs
    value_objects/
      __init__.py
      email.py        # Immutable email validation VOO
      money.py        # Immutable money arithmetic VOO
      phone.py        # E.164-normalized phone VOO
    repositories/
      __init__.py
      base.py         # Generic IRepository[T] interface
    services/
      __init__.py
      base.py         # DomainService marker class
    specifications/
      __init__.py
      base.py         # Specification pattern (and / or / not)
    serializers/
      __init__.py
      mixins.py       # Reusable DRF serializer mixins
```

## Design Decisions

### 1. Layering (core/infrastructure vs core/shared)

- `core.infrastructure` contains the lowest-level primitives: error types, constants, enums, and typing helpers. No Django imports here.
- `core.shared` contains higher-level reusable utilities that depend on Django or are specific to domain modeling (time, UUIDs, value objects, pagination).
- `core.config` isolates environment-configuration logic so settings behavior remains unchanged while centralizing helpers.

### 2. Immutability

All value objects (`Money`, `Email`, `Phone`) use `@dataclass(frozen=True)`. Once created, their state cannot change. This prevents accidental mutation in shared caches, session state, and message payloads.

### 3. No Business Logic

None of the files in `core/infrastructure` or `core/shared` import from app modules (`properties`, `finance`, `notification`, etc.). They depend only on the Python standard library, Django utilities, or `decouple`.

### 4. Why New Files Instead of Moving Existing ones

The existing `shared/` package is imported by 50+ modules. Moving files would require a massive, risky refactor. Instead, the new `core/infrastructure/` and `core/shared/` packages are additive. New code should import from the new locations.

## Examples

### Money

```python
from decimal import Decimal
from core.shared.value_objects import Money

rent = Money(Decimal("15000.00"), "INR")
deposit = Money(Decimal("30000.00"), "INR")

total = rent.add(deposit)   # 45000.00 INR
monthly = total.multiply(3) # 135000.00 INR
```

### Result

```python
from core.shared.result import Result

def update_username(user, name: str) -> Result[User]:
    if not name:
        return Result.fail("name is required")
    user.name = name
    return Result.ok(user)
```

### Specification

```python
from core.shared.specifications.base import Specification, AndSpecification, OrSpecification

class VerifiedSpec(Specification):
    def is_satisfied_by(self, user) -> bool:
        return user.is_verified

class ActiveSpec(Specification):
    def is_satisfied_by(self, user) -> bool:
        return user.is_active

rule = VerifiedSpec() & ActiveSpec()
if rule.is_satisfied_by(user):
    ...
```

### Pagination

```python
from core.shared.pagination import PageRequest, PageResponse

req = PageRequest(page=1, page_size=20, filters={"city": "Mumbai"})
page: PageResponse[Building] = service.list_buildings(req)
for building in page.items:
    ...
if page.has_next:
    req.page += 1
```

## Backward Compatibility

- No existing `shared/` files were modified or moved.
- No existing `core/services/base.py` was modified.
- All new modules are additive. Existing imports continue to work without change.
- `core.shared` re-exports selected types so new code has a single import path.

## Testing

All components have unit tests under `core/tests/`. Run with:

```bash
pytest core/tests/ -v
```
