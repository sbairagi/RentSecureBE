# Layer Rules

This document defines strict architecture rules for each layer in the RentSecure platform.

---

## Layer Hierarchy

```
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 5: Presentation (interfaces/)                                  │
│ - Views, Serializers, Permissions, Filters, URL config              │
│ - Handles HTTP concerns, input/output transformation                │
│ - No business logic                                                  │
└──────────────────────────────────────────────────────────────────────┘
                              │ depends on
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 4: Application (application/)                                  │
│ - Services, Commands, Queries, Selectors                            │
│ - Orchestrates workflows, enforces use cases                        │
│ - Depends on domain interfaces only                                  │
└──────────────────────────────────────────────────────────────────────┘
                              │ depends on
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 3: Domain (domain/)                                            │
│ - Entities, Value Objects, Domain Events, Policies, Exceptions       │
│ - Pure business logic, zero framework dependencies                   │
│ - The heart of the application                                       │
└──────────────────────────────────────────────────────────────────────┘
                              │ depends on
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 2: Infrastructure (infrastructure/)                            │
│ - Repository implementations, external adapters, Django models       │
│ - Implements domain interfaces                                       │
│ - Depends on domain only                                             │
└──────────────────────────────────────────────────────────────────────┘
                              │ depends on
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Layer 1: Platform (platform/, shared/)                               │
│ - Cache, storage, search, queue adapters                             │
│ - Generic utilities, base classes                                    │
│ - No app-specific logic                                              │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Layer Definitions

### Layer 1: Platform + Shared

**Purpose:** Generic infrastructure primitives and cross-cutting utilities. No business logic.

**Contains:**
- Cache adapters
- Storage adapters
- Search adapters
- Queue adapters
- Event bus
- Dependency injection
- Base exceptions
- Base interfaces
- Generic utilities

**Allowed imports:**
- Python standard library
- Third-party libraries (Django, DRF, etc.)
- Nothing from `apps/`

**Forbidden imports:**
- Any module from `apps/`
- Any business logic
- Any Django model from an app

**Rules:**
1. `shared/` must never import from `apps/`
2. `platform/` must never import from `apps/`
3. All code must be generic and reusable
4. No side effects (no database writes, no network calls in utilities)

---

### Layer 2: Infrastructure

**Purpose:** Implements domain interfaces using concrete technologies (Django ORM, external APIs).

**Contains:**
- Django models (ORM)
- Repository implementations
- External service adapters (payment gateways, notification providers)
- Signal handlers
- Management commands
- Task definitions

**Allowed imports:**
- Domain layer (interfaces and entities)
- Platform layer
- Django ORM, DRF
- Third-party libraries

**Forbidden imports:**
- `application/` layer
- `interfaces/` layer (presentation)
- Other apps' infrastructure layers

**Rules:**
1. Infrastructure must implement domain interfaces, never define business logic
2. Models are persistence artifacts, not domain entities (domain entities are separate)
3. External adapters implement platform interfaces
4. Signal handlers must delegate to application services
5. Management commands must delegate to application services

---

### Layer 3: Domain

**Purpose:** Pure business logic. Zero framework dependencies. The heart of the application.

**Contains:**
- Domain entities (rich models with behavior)
- Value objects (immutable types)
- Domain events
- Domain policies (business rules)
- Domain exceptions
- Repository interfaces (abstract)

**Allowed imports:**
- Python standard library
- `shared/` (types, exceptions, domain events base)
- Nothing from Django, DRF, or any external framework

**Forbidden imports:**
- `infrastructure/` layer
- `application/` layer
- `interfaces/` layer
- Django imports
- Database queries

**Rules:**
1. Domain layer must be importable without Django installed
2. No database queries in domain layer
3. No HTTP concerns in domain layer
4. No serialization/deserialization in domain layer
5. Domain events are the only way to communicate outside the aggregate

---

### Layer 4: Application

**Purpose:** Orchestrates workflows, enforces use cases, coordinates between domain and infrastructure.

**Contains:**
- Application services
- Command handlers
- Query handlers
- Selectors
- DTOs (Data Transfer Objects)

**Allowed imports:**
- Domain layer
- Infrastructure layer (repositories)
- Platform layer
- `shared/` utilities

**Forbidden imports:**
- `interfaces/` layer (presentation)
- Django request/response objects
- Django settings
- Other apps' application services

**Rules:**
1. Application services are the only entry point for business workflows
2. Application services depend on domain interfaces, not infrastructure implementations
3. Application services must not know about HTTP
4. Application services must not import serializers or views
5. One application service method = one use case
6. Application services are stateless

---

### Layer 5: Presentation (Interfaces)

**Purpose:** Handles HTTP concerns, input/output transformation, authentication, and authorization.

**Contains:**
- API views (ViewSets, APIViews)
- Serializers (DRF)
- Permissions (DRF)
- Filters (DRF)
- URL configurations
- Request/response DTOs
- OpenAPI schemas

**Allowed imports:**
- Application services
- Serializers
- Permissions
- Filters
- `shared/` utilities

**Forbidden imports:**
- Domain layer (entities, value objects)
- Infrastructure layer (models, repositories)
- Business logic

**Rules:**
1. Views must be thin—only orchestration, no business logic
2. Views must delegate to application services
3. Views must not query models directly (except for simple list queries via selectors)
4. Views must not modify domain entities directly
5. Serializers validate and transform data only—no business rules
6. Permissions check access only—no business logic
7. URL configuration is the public API contract

---

## Cross-Cutting Concerns

### Logging
- Structured logging is applied at the application service layer
- Domain events include logging context
- Infrastructure layer logs external calls

### Validation
- Input validation: Serializers (presentation layer)
- Business validation: Domain policies and application services
- Cross-field validation: Domain policies

### Authorization
- Authentication: Identity context
- Authorization: Permission checks in views
- Resource-level authorization: Application services

### Error Handling
- Domain exceptions: Raised in domain layer, caught in application layer
- Infrastructure exceptions: Wrapped in domain exceptions
- HTTP exceptions: Raised in presentation layer only

### Caching
- Cache interface: Defined in `platform/cache/`
- Cache usage: Application services and selectors
- Cache invalidation: Application services after mutations

---

## Dependency Matrix

| Layer | May import from | Must NOT import from |
|-------|----------------|---------------------|
| Platform/Shared | stdlib, third-party | apps/ |
| Infrastructure | Domain, Platform, Shared | Application, Interfaces |
| Domain | Shared (base classes only) | Everything else |
| Application | Domain, Infrastructure, Platform | Interfaces |
| Presentation | Application, Shared | Domain, Infrastructure |

---

*These rules are enforced by import-linter and architecture contract tests. Violations block CI.*
