# Properties Services

This directory contains the service layer for the Properties bounded context.

## Purpose

The Properties bounded context owns all domain logic related to physical
property management: buildings, units, renters, rent records, occupancy,
and vacancy.

Services here are pure business capabilities. They must not import DRF,
Request, Response, ViewSets, or any HTTP-specific types.

## Dependency Direction

```
Views / API Layer
        ↓
Properties Services
        ↓
Properties Models
        ↓
Database
```

Properties services may depend on:
- `core/services/` for shared business capabilities
- `shared/` for generic utilities
- Django ORM for persistence

Properties services must not depend on:
- DRF
- HTTP request/response objects
- Views or ViewSets
- Other bounded contexts directly

## Services

| Service | Responsibility |
|---------|----------------|
| `building_service.py` | Building creation, updates, archive/restore, owner aggregation |
| `unit_service.py` | Unit status, analytics, occupancy synchronization |
| `renter_service.py` | Renter profiles, status management, verification |
| `rent_service.py` | Rent records, payment status, amount calculation, history |
| `occupancy_service.py` | Occupancy status, rate calculation, history tracking |
| `vacancy_service.py` | Vacancy detection, period tracking, vacancy analytics |

## Future Migration Plan

1. Phase 1: Create service skeletons (current phase)
2. Phase 2: Extract building business logic from views into `BuildingService`
3. Phase 3: Extract unit business logic from views into `UnitService`
4. Phase 4: Extract renter business logic from views into `RenterService`
5. Phase 5: Extract rent business logic from views into `RentService`
6. Phase 6: Enforce service-layer contracts in views and serializers
7. Phase 7: Add architecture tests for Properties bounded context

## Constraints

- No business logic is moved in this phase
- No views or serializers are modified
- No models are modified
- No HTTP imports are allowed in this package
