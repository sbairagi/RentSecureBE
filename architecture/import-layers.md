# Import Layers

This document defines the allowed import layers for the RentSecureBE codebase.

## Layering Overview

The architecture follows a strict layered dependency model:

```
Views / API Layer
    ↓
Services Layer
    ↓
Models Layer
    ↓
Database
```

## Allowed Import Directions

### Views Layer
Views may import:
- Services
- Serializers
- Permissions
- Django/DRF utilities
- `shared/` utilities (read-only)

Views must NOT import:
- Models directly (except for queryset definitions in ViewSets)
- Other views
- Business logic utilities from `properties/`, `finance/`, etc.

### Services Layer
Services may import:
- Models
- Other services within the same app
- `shared/` utilities
- Django utilities

Services must NOT import:
- Views
- Serializers
- Request/Response objects
- HTTP-specific logic

### Models Layer
Models may import:
- `shared/` utilities
- Django model base classes

Models must NOT import:
- Views
- Serializers
- Services
- Request/Response objects

### Shared Layer
`shared/` may import:
- Python standard library only

`shared/` must NOT import:
- Any Django app code
- Any project-specific code
- Any service, model, view, or serializer

## Forbidden Imports

The following imports are strictly forbidden:

1. **Model → View**: Models must never know about views
2. **Model → Serializer**: Models must never know about serializers
3. **Serializer → View**: Serializers must never import views
4. **View → View**: Views must not import other views
5. **Service → View**: Services must never import views
6. **Shared → App**: Shared must never import from any app
7. **Cross-app direct imports**: Apps must communicate through services only

## Current Import Constraints

The current `import-linter.ini` enforces:

- Each Django app is a root package
- `rentsecure_be` may import from any app
- Apps may import from `rentsecure_be` for configuration
- Apps must not import from each other directly

## Future Import Constraints

As bounded contexts are extracted:

1. Each bounded context gets its own import-linter contract
2. Cross-context communication happens through:
   - Service interfaces in `shared/`
   - Domain events
   - Explicit API contracts
3. No direct model imports across bounded contexts

## Import Best Practices

1. Use absolute imports within the project
2. Group imports: stdlib, third-party, local
3. No circular imports
4. Import-linter violations block CI
5. Document exceptions in ADRs

## Enforcement

- `import-linter` runs in CI
- Pre-commit hooks check imports
- Architecture phases update import-linter contracts before implementation
