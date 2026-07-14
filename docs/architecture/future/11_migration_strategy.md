# Migration Strategy

This document defines the phased migration from the current modular monolith to the target architecture. Each phase is independent, reversible, and keeps CI green.

---

## Migration Principles

1. **No Big Bang:** Changes are incremental and reversible.
2. **CI Always Green:** Every phase passes all tests, lint, and type checks.
3. **No API Changes:** External APIs remain stable throughout.
4. **One Context at a Time:** Each phase focuses on one bounded context.
5. **Business Logic Unchanged:** Behavior is preserved; only structure changes.
6. **Feature Flags for New Code:** All new patterns are behind feature flags during transition.

---

## Phase 1: Architecture Cleanup

**Objective:** Remove dead code, fix circular imports, and prepare for structured migration.

**Duration:** 1–2 sprints
**Risk:** Low
**Rollback:** Git revert (no structural changes)

### Deliverables
- Remove unused imports and dead code
- Fix existing circular dependencies
- Clean up legacy files in `properties/_legacy/`
- Consolidate duplicate code
- Update `import-linter.ini` baseline

### Validation
- `pytest tests/` passes
- `ruff check .` passes
- `mypy .` passes
- `import-linter` passes

### Key Actions
```bash
# 1. Identify dead code
pytest --deadcode

# 2. Fix circular imports
import-linter --strict

# 3. Remove legacy files
rm -rf properties/_legacy/
rm properties/refactored_models_combined.py
rm properties/original_models.py
```

---

## Phase 2: Move Files (Structural)

**Objective:** Reorganize existing code into the target folder structure without changing behavior.

**Duration:** 3–4 sprints
**Risk:** Low
**Rollback:** Git revert (all moves are tracked)

### Deliverables
- Move `core/` → `apps/identity/` and `apps/subscription/`
- Move `properties/` → `apps/property/`
- Move `smartbot/` + `ai_assistant/` → `apps/ai/`
- Move `referral_and_earn/` → `apps/referral/`
- Move `finance/` → `apps/finance/`
- Move `notification/` → `apps/notification/`
- Move `documents/` → `apps/document/`
- Move `dashboard/` → `apps/dashboard/`
- Move `rentsecure_be/` services → `platform/` and context services
- Create `config/settings/` from `rentsecure_be/settings.py`

### Internal App Structure

Within each app, create the target internal structure:

```
apps/<context>/
├── domain/                    # New: extract domain logic
├── application/               # New: extract services
├── infrastructure/            # New: consolidate models + repos
└── interfaces/                # New: consolidate views + serializers
```

### Migration Order
1. `apps/identity/` (simplest, fewest dependencies)
2. `apps/subscription/` (depends on identity)
3. `apps/document/` (fewest dependencies)
4. `apps/notification/` (depends on identity)
5. `apps/referral/` (depends on identity, payment)
6. `apps/property/` (complex, many models)
7. `apps/rent/` (new context, extracted from property)
8. `apps/payment/` (depends on rent, document, notification)
9. `apps/finance/` (depends on property, payment)
10. `apps/ai/` (depends on multiple contexts)
11. `apps/dashboard/` (depends on all contexts)

### Validation
- All tests pass (same test suite, new paths)
- All URLs resolve correctly
- All migrations apply cleanly
- Import-linter passes with new structure

---

## Phase 3: Split God Classes

**Objective:** Break up large classes and modules into focused, single-responsibility components.

**Duration:** 2–3 sprints
**Risk:** Medium
**Rollback:** Git revert

### Deliverables

#### Property Context
- Split `properties/models/` (multiple model files) into focused entities
- Split `properties/services/` (large service files) into per-entity services
- Split `properties/views/` (large view files) into per-entity views
- Split `properties/serializers/` into per-entity serializers

#### Core/Identity Context
- Split `core/models.py` into User, OTP, Permission models
- Split `core/services/` into Auth, Registration, Permission services
- Split `core/views.py` into Login, Register, Password views

#### SmartBot/AI Context
- Consolidate `smartbot/` and `ai_assistant/` into `apps/ai/`
- Split AI services into Chat, DocumentAnalysis, RentSuggestion services

### Rules
1. **One class per file:** Each file contains one primary class.
2. **Single responsibility:** Each class has exactly one reason to change.
3. **Max 500 lines per file:** Files exceeding 500 lines must be split.
4. **Max 10 methods per class:** Classes exceeding 10 methods must be split.

### Validation
- No file exceeds 500 lines
- No class exceeds 10 public methods
- All tests pass
- Import-linter passes

---

## Phase 4: Repository Pattern

**Objective:** Introduce repository interfaces and implementations for all data access.

**Duration:** 2–3 sprints
**Risk:** Medium
**Rollback:** Git revert

### Deliverables

#### Step 1: Define Repository Interfaces (Domain Layer)

```python
# apps/property/domain/repositories/building_repository.py
class BuildingRepository(ABC):
    @abstractmethod
    def get(self, building_id: UUID) -> Building: ...
    @abstractmethod
    def list_by_owner(self, owner_id: UUID) -> List[Building]: ...
    @abstractmethod
    def create(self, building: Building) -> Building: ...
    @abstractmethod
    def update(self, building: Building) -> Building: ...
    @abstractmethod
    def delete(self, building_id: UUID) -> None: ...
```

#### Step 2: Implement Repositories (Infrastructure Layer)

```python
# apps/property/infrastructure/repositories/django_building_repository.py
class DjangoBuildingRepository(BuildingRepository):
    def get(self, building_id: UUID) -> Building:
        model = BuildingModel.objects.get(id=building_id)
        return self._to_entity(model)

    def _to_entity(self, model: BuildingModel) -> Building:
        return Building(
            id=model.id,
            name=model.name,
            address=model.address,
            ...
        )
```

#### Step 3: Inject Repositories into Services

```python
class PropertyService:
    def __init__(self, building_repo: BuildingRepository):
        self.building_repo = building_repo

    def create_building(self, owner_id: UUID, data: CreateBuildingDTO) -> Building:
        building = Building.create(owner_id=owner_id, **data.dict())
        return self.building_repo.create(building)
```

#### Step 4: Remove Direct ORM Access from Services

```python
# Before (forbidden)
class PropertyService:
    def create_building(self, data):
        return BuildingModel.objects.create(**data)

# After (correct)
class PropertyService:
    def create_building(self, data):
        building = Building.create(**data)
        return self.building_repo.create(building)
```

### Context Order
1. `apps/identity/` (simplest models)
2. `apps/subscription/`
3. `apps/document/`
4. `apps/notification/`
5. `apps/referral/`
6. `apps/property/`
7. `apps/rent/`
8. `apps/payment/`
9. `apps/finance/`
10. `apps/ai/`
11. `apps/dashboard/`

### Validation
- All repositories implement domain interfaces
- No direct ORM queries in application services
- All tests pass
- Integration tests verify repository implementations

---

## Phase 5: Service Layer

**Objective:** Ensure all business logic lives in services, not views or serializers.

**Duration:** 2–3 sprints
**Risk:** Medium
**Rollback:** Git revert

### Deliverables

#### Step 1: Extract Business Logic from Views

```python
# Before (forbidden)
class BuildingViewSet(viewsets.ModelViewSet):
    def create(self, request):
        building = BuildingModel.objects.create(**request.data)
        # Business logic here
        return Response(...)

# After (correct)
class BuildingViewSet(viewsets.ModelViewSet):
    def create(self, request):
        command = CreateBuildingCommand(**request.data)
        result = self.property_service.create_building(command)
        return Response(BuildingOutputSerializer(result.building).data)
```

#### Step 2: Extract Business Logic from Serializers

```python
# Before (forbidden)
class BuildingSerializer(serializers.ModelSerializer):
    def validate(self, data):
        # Business logic here
        return data

# After (correct)
class BuildingSerializer(serializers.ModelSerializer):
    def validate(self, data):
        # Validation only, no business logic
        return data
```

#### Step 3: Ensure All Workflows Go Through Services

```python
# Every view method should:
# 1. Parse request → DTO/Command
# 2. Call application service
# 3. Serialize response
# 4. Return response
```

### Validation
- `grep -r "Business logic in views"` finds no matches
- `grep -r "Business logic in serializers"` finds no matches
- All tests pass
- Architecture tests verify thin views

---

## Phase 6: Import Boundaries

**Objective:** Enforce strict import boundaries between layers and contexts.

**Duration:** 2 sprints
**Risk:** Low
**Rollback:** Git revert

### Deliverables

#### Step 1: Update Import-Linter Configuration

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
```

#### Step 2: Add Container Contracts

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

#### Step 3: Fix Violations

```bash
# Run import-linter to find violations
lint-imports

# Fix violations one by one
# Move code to correct layer
# Introduce interfaces where needed
```

### Validation
- `import-linter --strict` passes
- Architecture contract tests pass
- No cross-app direct imports

---

## Phase 7: Dead Code Removal

**Objective:** Remove unused code, unused migrations, and unused dependencies.

**Duration:** 1–2 sprints
**Risk:** Low
**Rollback:** Git revert

### Deliverables

#### Step 1: Identify Dead Code

```bash
# Find unused imports
ruff check --select F401 .

# Find unused variables
ruff check --select F841 .

# Find unused migrations
python manage.py showmigrations --plan

# Find unused dependencies
pipdeptree --warn silence
```

#### Step 2: Remove Unused Code

```bash
# Remove unused imports
ruff check --fix --select F401 .

# Remove unused variables
ruff check --fix --select F841 .

# Remove unused migrations (carefully)
# Squash migrations where possible
```

#### Step 3: Clean Dependencies

```bash
# Remove unused packages
pip uninstall <unused-package>

# Update requirements.txt
```

### Validation
- All tests pass
- Application starts cleanly
- No unused imports (ruff F401 clean)
- No unused variables (ruff F841 clean)

---

## Phase 8: Performance Improvements

**Objective:** Optimize database queries, add caching, and improve API response times.

**Duration:** 2–3 sprints
**Risk:** Low
**Rollback:** Git revert

### Deliverables

#### Step 1: Query Optimization

```python
# Before
buildings = BuildingModel.objects.filter(owner_id=owner_id)
for building in buildings:
    units = building.unit_set.all()  # N+1 query

# After
buildings = BuildingModel.objects.prefetch_related("unit_set").filter(owner_id=owner_id)
```

#### Step 2: Add Caching

```python
from platform.cache.interfaces import CachePort

class PropertyDashboardSelector:
    def __init__(self, cache: CachePort, ...):
        self.cache = cache

    def get_owner_dashboard(self, owner_id: UUID) -> OwnerDashboard:
        cache_key = f"dashboard:owner:{owner_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        dashboard = self._compute_dashboard(owner_id)
        self.cache.set(cache_key, dashboard, timeout=300)
        return dashboard
```

#### Step 3: Add Database Indexes

```python
class Meta:
    indexes = [
        models.Index(fields=["owner_id", "created_at"]),
        models.Index(fields=["unit_id", "due_date"]),
    ]
```

#### Step 4: Add Selectors for Complex Reads

```python
class OwnerDashboardSelector:
    def execute(self, owner_id: UUID) -> OwnerDashboard:
        # Optimized read query using selectors
        return OwnerDashboard(...)
```

### Validation
- API response times < 200ms at p95
- N+1 queries eliminated
- Cache hit rate > 60%
- Database connection pool healthy

---

## Phase 9: Architecture Freeze

**Objective:** Lock architecture decisions and enforce boundaries permanently.

**Duration:** Ongoing
**Risk:** N/A
**Rollback:** N/A

### Deliverables

#### Step 1: Finalize Import-Linter Rules

```ini
# All containers strictly enforced
[importlinter:containers]
type = containers
name = App Boundaries
containers =
    apps/identity
    apps/subscription
    ...
    shared
    platform

# All layer rules strictly enforced
[importlinter:identity]
type = layers
...
```

#### Step 2: Add Architecture Tests to CI

```python
# tests/test_architecture_contract/test_dependencies.py
def test_no_cross_app_imports():
    """Verify no direct imports between apps."""
    violations = find_cross_app_imports()
    assert not violations, f"Cross-app imports found: {violations}"

def test_domain_has_no_framework_imports():
    """Verify domain layer has no Django imports."""
    violations = find_framework_imports_in_domain()
    assert not violations, f"Framework imports in domain: {violations}"
```

#### Step 3: Documentation Freeze

- All ADRs are approved
- Architecture docs are current
- Runbooks are complete
- Onboarding docs are updated

#### Step 4: Monitoring

- Import-linter runs on every PR
- Architecture tests run on every PR
- Dependency drift alerts set up
- Quarterly architecture reviews scheduled

---

## Phase Dependencies

```
Phase 1 (Cleanup)
    │
    ▼
Phase 2 (Move Files)
    │
    ├──▶ Phase 3 (Split God Classes)
    │
    ├──▶ Phase 4 (Repository Pattern)
    │
    ├──▶ Phase 5 (Service Layer)
    │
    ├──▶ Phase 6 (Import Boundaries)
    │
    ▼
Phase 7 (Dead Code Removal)
    │
    ▼
Phase 8 (Performance)
    │
    ▼
Phase 9 (Architecture Freeze)
```

Phases 3–6 can run in parallel after Phase 2, as long as each context is completed independently.

---

## Rollback Procedures

| Phase | Rollback Method | Time to Rollback |
|-------|----------------|-----------------|
| 1 | Git revert | < 1 hour |
| 2 | Git revert (all moves tracked) | < 2 hours |
| 3 | Git revert | < 2 hours |
| 4 | Git revert + feature flag | < 2 hours |
| 5 | Git revert | < 2 hours |
| 6 | Disable import-linter temporarily | < 1 hour |
| 7 | Git revert | < 1 hour |
| 8 | Disable caching, remove indexes | < 1 hour |
| 9 | N/A (final phase) | N/A |

---

## Success Criteria

| Metric | Target |
|--------|--------|
| CI pipeline duration | < 10 minutes |
| Test coverage | > 80% |
| Import-linter violations | 0 |
| Architecture test failures | 0 |
| Dead code | < 1% of codebase |
| Average API response time | < 200ms (p95) |
| N+1 queries | 0 in critical paths |
| Developer onboarding time | < 2 days per context |

---

*This migration strategy is designed to be executed by a single team over 6–9 months, with each phase delivering working software.*
