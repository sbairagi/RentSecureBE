# Naming Conventions

This document defines naming conventions for all code artifacts in the RentSecure platform.

---

## Python Naming

| Artifact | Convention | Example |
|----------|-----------|---------|
| Module | `snake_case` | `property_service.py` |
| Package | `snake_case` | `infrastructure/` |
| Class | `PascalCase` | `PaymentService` |
| Function | `snake_case` | `submit_payment()` |
| Method | `snake_case` | `get_building()` |
| Variable | `snake_case` | `payment_amount` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| Private | `_leading_underscore` | `_internal_method()` |
| Type alias | `snake_case` | `user_id: UUID` |

---

## Django Naming

| Artifact | Convention | Example |
|----------|-----------|---------|
| App name | `snake_case` | `property`, `notification` |
| Model class | `PascalCase` (singular) | `Building`, `RentRecord` |
| Model field | `snake_case` | `rent_amount` |
| Model Meta class | `Meta` | `class Meta:` |
| Migration file | `NNNN_description.py` | `0001_initial.py` |
| Management command | `snake_case` | `generate_rent_records` |
| Template | `snake_case.html` | `rent_receipt.html` |

### Model Naming

```python
class Building(models.Model):  # Singular, PascalCase
    name = models.CharField(max_length=255)
    address = models.TextField()

    class Meta:
        verbose_name = "Building"
        verbose_name_plural = "Buildings"
        db_table = "property_building"
```

---

## API Naming

### URL Patterns

| Pattern | Example |
|---------|---------|
| Collection | `/api/v1/buildings/` |
| Detail | `/api/v1/buildings/{id}/` |
| Action | `/api/v1/buildings/{id}/add-unit/` |
| Nested | `/api/v1/buildings/{id}/units/` |

### HTTP Methods

| Operation | Method | URL |
|-----------|--------|-----|
| List | `GET` | `/api/v1/buildings/` |
| Create | `POST` | `/api/v1/buildings/` |
| Retrieve | `GET` | `/api/v1/buildings/{id}/` |
| Update | `PUT/PATCH` | `/api/v1/buildings/{id}/` |
| Delete | `DELETE` | `/api/v1/buildings/{id}/` |
| Custom action | `POST` | `/api/v1/buildings/{id}/add-unit/` |

### Response Keys

| Type | Convention | Example |
|------|-----------|---------|
| JSON key | `snake_case` | `building_name` |
| Pagination | Standard DRF | `count`, `next`, `previous`, `results` |
| Error | `snake_case` | `field_name`, `non_field_errors` |

---

## Serializer Naming

| Type | Convention | Example |
|------|-----------|---------|
| Serializer class | `PascalCaseSerializer` | `BuildingSerializer` |
| Input serializer | `...InputSerializer` | `CreateBuildingInputSerializer` |
| Output serializer | `...OutputSerializer` | `BuildingOutputSerializer` |
| List serializer | `...ListSerializer` | `BuildingListSerializer` |
| Nested serializer | `...NestedSerializer` | `UnitNestedSerializer` |

```python
class BuildingOutputSerializer(serializers.ModelSerializer):
    """Serializer for building detail responses."""
    unit_count = serializers.IntegerField()

    class Meta:
        model = Building
        fields = ["id", "name", "address", "unit_count", "created_at"]

class CreateBuildingInputSerializer(serializers.Serializer):
    """Serializer for building creation input."""
    name = serializers.CharField(max_length=255)
    address = serializers.CharField()
```

---

## Repository Naming

| Type | Convention | Example |
|------|-----------|---------|
| Interface | `PascalCaseRepository` | `BuildingRepository` |
| Implementation | `DjangoPascalCaseRepository` or `PascalCaseRepository` | `DjangoBuildingRepository` |

```python
# Domain layer (interface)
class BuildingRepository(ABC):
    @abstractmethod
    def get(self, building_id: UUID) -> Building: ...
    @abstractmethod
    def list_by_owner(self, owner_id: UUID) -> List[Building]: ...

# Infrastructure layer (implementation)
class DjangoBuildingRepository(BuildingRepository):
    def get(self, building_id: UUID) -> Building:
        ...
```

---

## Service Naming

| Type | Convention | Example |
|------|-----------|---------|
| Application service | `PascalCaseService` | `PaymentService` |
| Domain service | `PascalCaseService` or `PascalCase` | `LateFeeCalculator` |
| Infrastructure adapter | `PascalCaseAdapter` | `RazorpayAdapter` |

```python
# Application service
class PaymentService:
    def submit_payment(self, command: SubmitPaymentCommand) -> PaymentResult: ...

# Domain service
class LateFeeCalculator:
    def calculate(self, rent: RentRecord, today: date) -> Decimal: ...

# Infrastructure adapter
class RazorpayAdapter(PaymentGateway):
    def create_payment(self, order: PaymentOrder) -> PaymentResult: ...
```

---

## Policy Naming

| Type | Convention | Example |
|------|-----------|---------|
| Policy class | `PascalCasePolicy` | `OwnershipPolicy` |
| Policy method | `snake_case` | `is_owner_of_building()` |

```python
class OwnershipPolicy:
    def is_owner_of_building(self, user_id: UUID, building_id: UUID) -> bool: ...
    def can_assign_renter(self, user_id: UUID, unit_id: UUID) -> bool: ...
```

---

## Selector Naming

| Type | Convention | Example |
|------|-----------|---------|
| Selector class | `PascalCaseSelector` | `PropertyDashboardSelector` |
| Method | `snake_case` | `get_owner_dashboard()` |

```python
class PropertyDashboardSelector:
    def get_owner_dashboard(self, owner_id: UUID) -> OwnerDashboard: ...
    def get_tenant_dashboard(self, tenant_id: UUID) -> TenantDashboard: ...
```

---

## Command Naming

| Type | Convention | Example |
|------|-----------|---------|
| Command class | `PascalCaseCommand` | `SubmitPaymentCommand` |
| Command handler | `PascalCaseCommandHandler` | `SubmitPaymentCommandHandler` |

```python
@dataclass
class SubmitPaymentCommand:
    tenant_id: UUID
    rent_id: UUID
    utr: str

class SubmitPaymentCommandHandler:
    def handle(self, command: SubmitPaymentCommand) -> PaymentResult: ...
```

---

## Event Naming

| Type | Convention | Example |
|------|-----------|---------|
| Event class | `PascalCase` (past tense) | `PaymentSubmitted` |
| Event type string | `snake_case` | `"payment.submitted"` |

```python
class PaymentSubmitted(DomainEvent):
    event_type = "payment.submitted"
    payment_id: UUID
    tenant_id: UUID
    amount: Decimal
```

---

## File Naming

| Type | Convention | Example |
|------|-----------|---------|
| Module | `snake_case.py` | `payment_service.py` |
| Test file | `test_snake_case.py` | `test_payment_service.py` |
| Fixture file | `snake_case.json` | `buildings.json` |
| Template | `snake_case.html` | `rent_receipt.html` |

### File Naming Rules

1. **One class per file:** Each file contains one primary class (exception: small helper classes).
2. **File name matches primary class:** `PaymentService` → `payment_service.py`.
3. **Test files match source files:** `payment_service.py` → `test_payment_service.py`.
4. **Init files are minimal:** `__init__.py` contains only imports.

---

## Package Naming

| Type | Convention | Example |
|------|-----------|---------|
| App package | `snake_case` | `apps/property/` |
| Domain subpackage | `snake_case` | `domain/entities/` |
| Subpackage | `snake_case` | `infrastructure/repositories/` |

---

## Migration Naming

| Convention | Example |
|-----------|---------|
| `NNNN_description.py` | `0001_initial.py`, `0002_add_rent_amount.py` |
| Description in `snake_case` | `add_rent_amount`, `create_payment_table` |

---

## Naming Anti-Patterns

| Anti-Pattern | Correct | Why |
|--------------|---------|-----|
| `UserManager` | `UserService` | "Manager" is vague |
| `Helper` suffix | Descriptive name | `EmailHelper` → `EmailRenderer` |
| `Utils` class | Module-level functions | `class StringUtils` → `def truncate_string()` in `utils.py` |
| `Base` prefix without base class | Remove prefix | `BasePaymentService` → `PaymentService` |
| Abbreviations | Full words | `usr` → `user`, `amt` → `amount` |
| `data` as variable name | Descriptive name | `data` → `payment_data` |

---

*Consistency is more important than perfection. Follow existing patterns when extending code, propose new patterns when creating new concepts.*
