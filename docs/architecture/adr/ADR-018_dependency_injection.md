# ADR-018: Dependency Injection Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure services need dependencies (repositories, external adapters) injected. Without a clear DI strategy:
- Services create their own dependencies (hard to test)
- Dependency configuration is scattered
- Test setup is complex
- Service substitution is difficult

---

## Decision

RentSecure uses **constructor injection** with a central service container.

**Rules:**
1. All dependencies are injected via constructor
2. Service container is defined in `platform/di/`
3. Production container wires real implementations
4. Test container wires mock implementations
5. No `import` of concrete implementations in domain/application layers

---

## Alternatives Considered

### 1. Service Locator Pattern

**Description:** Services pull dependencies from a global registry.

**Pros:**
- Simple to implement
- Dependencies are optional

**Cons:**
- Hidden dependencies
- Hard to test
- Violates dependency inversion

**Decision:** Rejected. Hidden dependencies are bad.

### 2. Framework DI (e.g., django-injector)

**Description:** Use a third-party DI framework.

**Pros:**
- Automated injection
- Less boilerplate

**Cons:**
- Additional dependency
- Magic behavior
- Hard to debug
- Less explicit

**Decision:** Rejected. Explicit is better than magic.

### 3. Constructor Injection with Container (Selected)

**Description:** Dependencies are explicit in constructors; container wires them.

**Pros:**
- Explicit dependencies
- Easy to test
- No magic
- Clear wiring

**Cons:**
- More boilerplate
- Container maintenance

**Decision:** Accepted. Best for testability and explicitness.

---

## Service Container

```python
# platform/di/container.py
class ServiceContainer:
    def __init__(self):
        self._services = {}

    def register(self, interface, implementation):
        self._services[interface] = implementation

    def resolve(self, interface):
        return self._services[interface]

# platform/di/providers.py
def setup_production_container() -> ServiceContainer:
    container = ServiceContainer()

    # Identity
    container.register(UserRepository, DjangoUserRepository())
    container.register(PermissionRepository, DjangoPermissionRepository())

    # Property
    container.register(BuildingRepository, DjangoBuildingRepository())
    container.register(UnitRepository, DjangoUnitRepository())

    # Services
    container.register(PropertyService, lambda c: PropertyService(
        building_repo=c.resolve(BuildingRepository),
        unit_repo=c.resolve(UnitRepository),
    ))

    return container
```

---

## Test Container

```python
# platform/di/providers.py
def setup_test_container() -> ServiceContainer:
    container = ServiceContainer()

    # Mock repositories
    container.register(UserRepository, MockUserRepository())
    container.register(BuildingRepository, MockBuildingRepository())

    return container
```

---

## Consequences

### Positive
- Dependencies are explicit
- Easy to test with mocks
- No hidden dependencies
- Clear wiring

### Negative
- More boilerplate
- Container maintenance

### Neutral
- Container is set up once per process
- Test container is set up per test suite

---

## References

- [Service Layer](../future/09_service_layer.md)
- [Architecture Principles](../../../architecture/ARCHITECTURE_PRINCIPLES.md)
