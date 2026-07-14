# Dependency Rules

This document defines the complete dependency graph for the target architecture, including allowed and forbidden imports.

---

## Core Principle

Dependencies flow inward only. Outer layers depend on inner layers, never the reverse.

```
  Presentation
       │
       ▼
  Application
       │
       ▼
     Domain
       │
       ▼
  Infrastructure
       │
       ▼
   Platform
       │
       ▼
   Shared
```

---

## Allowed Imports

### Shared Layer

```python
# shared/domain_events.py
from shared.types import UUID  # OK: within shared
from dataclasses import dataclass  # OK: stdlib
```

**Rule:** `shared/` must never import from `apps/`, `platform/`, or `config/`.

### Platform Layer

```python
# platform/cache/interfaces.py
from shared.interfaces import CachePort  # OK: shared is foundational
from shared.types import UUID  # OK: shared types
```

**Rule:** `platform/` must never import from `apps/`.

### Domain Layer (within an app)

```python
# apps/property/domain/entities/building.py
from shared.domain_events import DomainEvent  # OK: shared
from shared.types import UUID  # OK: shared
from shared.exceptions import DomainException  # OK: shared
```

**Rule:** Domain must never import from `infrastructure/`, `application/`, `interfaces/`, or other apps.

### Application Layer

```python
# apps/property/application/services/property_service.py
from apps.property.domain.entities.building import Building  # OK: same app domain
from apps.property.domain.policies import OwnershipPolicy  # OK: same app domain
from apps.property.infrastructure.repositories import BuildingRepository  # OK: same app infra
from platform.cache.interfaces import CachePort  # OK: platform
```

**Rule:** Application must never import from `interfaces/` (presentation) or other apps' layers.

### Infrastructure Layer

```python
# apps/property/infrastructure/persistence/models.py
from django.db import models  # OK: Django
from shared.types import UUID  # OK: shared
# Must NOT import from application/ or interfaces/
```

**Rule:** Infrastructure must never import from `application/` or `interfaces/`.

### Presentation Layer

```python
# apps/property/interfaces/views/building_view.py
from apps.property.application.services import PropertyService  # OK: same app application
from apps.property.interfaces.serializers import BuildingSerializer  # OK: same app interfaces
```

**Rule:** Presentation must never import from `domain/` or `infrastructure/`.

---

## Forbidden Imports

### ❌ Domain → Infrastructure

```python
# apps/property/domain/entities/building.py
from apps.property.infrastructure.repositories import BuildingRepository  # FORBIDDEN
```

**Why:** Domain must remain pure and framework-independent.

### ❌ Domain → Application

```python
# apps/property/domain/entities/building.py
from apps.property.application.services import PropertyService  # FORBIDDEN
```

**Why:** Domain must not know about application orchestration.

### ❌ Application → Presentation

```python
# apps/property/application/services/property_service.py
from apps.property.interfaces.serializers import BuildingSerializer  # FORBIDDEN
from apps.property.interfaces.views import BuildingView  # FORBIDDEN
```

**Why:** Application must not know about HTTP.

### ❌ Presentation → Domain

```python
# apps/property/interfaces/views/building_view.py
from apps.property.domain.entities.building import Building  # FORBIDDEN
from apps.property.domain.policies import OwnershipPolicy  # FORBIDDEN
```

**Why:** Presentation must not know about domain internals.

### ❌ Presentation → Infrastructure

```python
# apps/property/interfaces/views/building_view.py
from apps.property.infrastructure.persistence.models import Building  # FORBIDDEN
from apps.property.infrastructure.repositories import BuildingRepository  # FORBIDDEN
```

**Why:** Presentation must not query the database directly.

### ❌ Cross-App Direct Import

```python
# apps/property/application/services/property_service.py
from apps.rent.domain.entities.rent_record import RentRecord  # FORBIDDEN
```

**Why:** Bounded contexts must communicate through service interfaces or domain events.

### ❌ Shared → App

```python
# shared/utils.py
from apps.property.models import Property  # FORBIDDEN
```

**Why:** Shared must remain generic.

---

## Import Direction Summary

| Source | Target | Allowed? |
|--------|--------|----------|
| Shared | Shared | ✅ |
| Platform | Shared | ✅ |
| Domain (app) | Shared | ✅ |
| Application (app) | Domain (same app) | ✅ |
| Application (app) | Infrastructure (same app) | ✅ |
| Application (app) | Platform | ✅ |
| Infrastructure (app) | Domain (same app) | ✅ |
| Infrastructure (app) | Platform | ✅ |
| Presentation (app) | Application (same app) | ✅ |
| Presentation (app) | Shared | ✅ |
| Domain (app A) | Domain (app B) | ❌ |
| Application (app A) | Application (app B) | ❌ |
| Infrastructure (app A) | Infrastructure (app B) | ❌ |
| Presentation (app A) | Presentation (app B) | ❌ |
| Any (app) | Any (other app) | ❌ (unless via shared interface) |

---

## Cross-App Communication

### Allowed: Service Interface in Shared

```python
# shared/interfaces.py
class PaymentGateway(ABC):
    @abstractmethod
    def create_payment(self, order: PaymentOrder) -> PaymentResult: ...

# apps/property/application/services/property_service.py
from shared.interfaces import PaymentGateway  # OK: shared interface

class PropertyService:
    def __init__(self, payment_gateway: PaymentGateway):  # Injected via DI
        self.payment_gateway = payment_gateway
```

### Allowed: Domain Event

```python
# apps/property/domain/events/rent_generated.py
class RentGenerated(DomainEvent):
    event_type = "rent.generated"
    property_id: UUID
    amount: Decimal

# apps/property/application/services/property_service.py
event_bus.publish(RentGenerated(property_id, amount))  # OK: decoupled
```

### Allowed: Selector (Read Model)

```python
# apps/dashboard/application/queries/owner_metrics.py
class OwnerMetricsQuery:
    def execute(self, owner_id: UUID) -> OwnerMetrics:
        # Uses selectors from other contexts via injected dependencies
        property_metrics = self.property_selector.get_metrics(owner_id)
        rent_metrics = self.rent_selector.get_metrics(owner_id)
        return OwnerMetrics.combine(property_metrics, rent_metrics)
```

---

## Import-Linter Contracts

### Current Contracts (import-linter.ini)

```ini
[importlinter:rentsecure_be]
type = layers
name = rentsecure_be
layers =
    rentsecure_be

[importlinter:core]
type = layers
name = core
layers =
    core
    rentsecure_be
```

### Future Contracts

```ini
[importlinter:identity]
type = layers
name = identity
layers =
    identity.domain
    identity.application
    identity.infrastructure
    identity.interfaces

[importlinter:property]
type = layers
name = property
layers =
    property.domain
    property.application
    property.infrastructure
    property.interfaces

[importlinter:shared]
type = layers
name = shared
layers =
    shared

[importlinter:platform]
type = layers
name = platform
layers =
    platform
```

### Container Contracts (Cross-App)

```ini
[importlinter:containers]
type = containers
name = App Boundaries
containers =
    apps/identity
    apps/subscription
    apps/property
    apps/rent
    apps/payment
    apps/notification
    apps/document
    apps/finance
    apps/referral
    apps/ai
    apps/dashboard
    shared
    platform
    config
```

---

## Exceptions

All dependency rule exceptions must:
1. Be documented in an ADR
2. Be approved by architecture review
3. Have a time-boxed migration plan
4. Be tracked in the architecture backlog

---

*These rules are enforced by import-linter in CI. Any PR that violates these rules fails the build.*
