# Dependency Rules

This document defines the dependency direction and rules for the RentSecureBE codebase.

## Core Principle

Dependencies flow inward only. Outer layers depend on inner layers, never the reverse.

```
┌─────────────────────────────────────────┐
│  Views / API Layer                      │
│  (Presentation)                         │
└─────────────────────────────────────────┘
              ↓ depends on
┌─────────────────────────────────────────┐
│  Services Layer                         │
│  (Business Logic)                       │
└─────────────────────────────────────────┘
              ↓ depends on
┌─────────────────────────────────────────┐
│  Models Layer                           │
│  (Domain & Persistence)                 │
└─────────────────────────────────────────┘
              ↓ depends on
┌─────────────────────────────────────────┐
│  Database / External Services           │
└─────────────────────────────────────────┘
```

## Dependency Direction Rules

### Allowed Dependencies

| Layer | May Depend On |
|-------|---------------|
| Views | Services, Serializers, Permissions, Shared utilities |
| Services | Models, Other services (same context), Shared utilities |
| Models | Shared utilities, Django base classes |
| Shared | Python standard library only |

### Forbidden Dependencies

| Layer | Must NOT Depend On |
|-------|-------------------|
| Views | Models (except queryset), Other views, Business logic |
| Services | Views, Serializers, Request/Response objects |
| Models | Views, Serializers, Services, Request/Response objects |
| Shared | Any Django app code, Project-specific code |

## Service Layer Rules

1. **Single Responsibility**: Each service method handles one business operation
2. **No HTTP Logic**: Services must not know about HTTP requests/responses
3. **No Serializer Logic**: Services must not import or use serializers
4. **Direct Model Access**: Services may query models directly
5. **Reusable**: Services are reusable across views and other services

## Shared Module Rules

The `shared/` package provides generic foundations:

1. **No Business Logic**: `shared/` must not contain RentSecure-specific logic
2. **No App Imports**: `shared/` must not import from any Django app
3. **Read-Only**: Views may use `shared/` utilities but must not modify shared state
4. **Generic Only**: Only generic, reusable code belongs in `shared/`

## Cross-App Communication

### Current Pattern

Currently, apps may import from `rentsecure_be` for configuration:

```
core        → rentsecure_be
properties  → rentsecure_be
finance     → rentsecure_be
...
```

### Future Pattern

As bounded contexts are extracted:

1. **Service Interfaces**: Define interfaces in `shared/interfaces.py`
2. **Domain Events**: Use `shared/domain_events.py` for event-based communication
3. **Explicit Contracts**: Each context exposes contracts in `architecture/contracts/`
4. **No Direct Imports**: Contexts must not import directly from each other

## Import-Linter Enforcement

Current `import-linter.ini` enforces:

1. Each app is a root package
2. Apps may import from themselves and `rentsecure_be`
3. Apps must not import from each other

Future enforcement will add:

1. Bounded context contracts
2. Service interface compliance
3. Domain event usage rules
4. Cross-context communication audit

## Forbidden Import Examples

### ❌ Model → View
```python
# models.py
from myapp.views import MyView  # FORBIDDEN
```

### ❌ Model → Serializer
```python
# models.py
from myapp.serializers import MySerializer  # FORBIDDEN
```

### ❌ Serializer → View
```python
# serializers.py
from myapp.views import MyView  # FORBIDDEN
```

### ❌ Service → View
```python
# services.py
from myapp.views import MyView  # FORBIDDEN
```

### ❌ Shared → App
```python
# shared/utils.py
from myapp.models import MyModel  # FORBIDDEN
```

### ❌ Cross-app direct model import
```python
# properties/models.py
from core.models import User  # FORBIDDEN (must go through service)
```

## Migration Rules

When moving code between layers:

1. **Views → Services**: Move business logic, keep orchestration in views
2. **Services → Models**: Move only persistence logic, keep business rules in services
3. **Cross-app → Service**: Introduce service interfaces before moving logic
4. **Shared additions**: Only add generic, reusable code to `shared/`

## CI Enforcement

Future CI will enforce:

1. `import-linter` checks on every PR
2. Architecture tests verify dependency rules
3. Contract tests verify cross-context communication
4. No forbidden imports in production code

## Exceptions

All exceptions must be:

1. Documented in an ADR
2. Approved by architecture review
3. Time-boxed with a migration plan
4. Tracked in the architecture backlog
