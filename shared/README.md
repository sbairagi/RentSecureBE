# Shared Foundation

This package provides generic, reusable foundations for the RentSecureBE codebase.

## Purpose

`shared/` contains low-level building blocks that are independent of any
business domain. These foundations are established once and reused across
all architecture phases.

## Contents

| Module | Purpose |
|--------|---------|
| `constants.py` | Global reusable constants |
| `exceptions.py` | Generic base exception hierarchy |
| `types.py` | Reusable typing aliases |
| `enums.py` | Generic enum base types |
| `utils.py` | Generic utility functions |
| `validators.py` | Generic reusable validators |
| `interfaces.py` | Base Protocols / ABCs |
| `domain_events.py` | Base domain event infrastructure |

## Constraints

- No RentSecure-specific business logic
- No direct imports from application modules
- No side effects on import
- Production code does not import `shared/` until a future phase introduces it
