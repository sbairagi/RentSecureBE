# Repository Pattern

This document defines the repository interfaces (ports) used across the RentSecure platform. Repositories abstract persistence operations from domain logic.

---

## Core Principle

Repositories are **interfaces defined in the domain layer** and **implemented in the infrastructure layer**. Domain code depends on repository interfaces; infrastructure provides concrete implementations.

```python
# Domain layer
class BuildingRepository(ABC):
    @abstractmethod
    def get(self, building_id: UUID) -> Building: ...
    @abstractmethod
    def list_by_owner(self, owner_id: UUID) -> List[Building]: ...

# Infrastructure layer
class DjangoBuildingRepository(BuildingRepository):
    def get(self, building_id: UUID) -> Building:
        return BuildingModel.objects.get(id=building_id)
```

---

## Generic Repository Interfaces

### Repository (Base)

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional
from shared.types import UUID

T = TypeVar("T")

class Repository(ABC, Generic[T]):
    """Base repository interface."""

    @abstractmethod
    def get(self, id: UUID) -> T: ...

    @abstractmethod
    def list(self, **filters) -> List[T]: ...

    @abstractmethod
    def create(self, entity: T) -> T: ...

    @abstractmethod
    def update(self, entity: T) -> T: ...

    @abstractmethod
    def delete(self, id: UUID) -> None: ...

    @abstractmethod
    def exists(self, id: UUID) -> bool: ...
```

---

## Bounded Context Repositories

### Identity Repositories

```python
class UserRepository(Repository[User]):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    def get_active_users(self) -> List[User]: ...

    @abstractmethod
    def update_last_login(self, user_id: UUID) -> None: ...

class PermissionRepository(Repository[Permission]):
    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Permission]: ...

    @abstractmethod
    def list_for_user(self, user_id: UUID) -> List[Permission]: ...

class OTPRepository(Repository[OTPToken]):
    @abstractmethod
    def get_valid_token(self, user_id: UUID, code: str) -> Optional[OTPToken]: ...

    @abstractmethod
    def invalidate_user_tokens(self, user_id: UUID) -> None: ...
```

### Subscription Repositories

```python
class SubscriptionPlanRepository(Repository[SubscriptionPlan]):
    @abstractmethod
    def get_active_plans(self) -> List[SubscriptionPlan]: ...

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[SubscriptionPlan]: ...

class SubscriptionRepository(Repository[Subscription]):
    @abstractmethod
    def get_active_for_user(self, user_id: UUID) -> Optional[Subscription]: ...

    @abstractmethod
    def has_active_subscription(self, user_id: UUID) -> bool: ...

class UsageRepository(Repository[UsageRecord]):
    @abstractmethod
    def get_usage(self, user_id: UUID, feature: str) -> int: ...

    @abstractmethod
    def increment_usage(self, user_id: UUID, feature: str, amount: int) -> None: ...

class FeatureFlagRepository(Repository[FeatureFlag]):
    @abstractmethod
    def is_enabled(self, flag_name: str, user_id: UUID = None) -> bool: ...
```

### Property Repositories

```python
class BuildingRepository(Repository[Building]):
    @abstractmethod
    def list_by_owner(self, owner_id: UUID) -> List[Building]: ...

    @abstractmethod
    def count_units(self, building_id: UUID) -> int: ...

class UnitRepository(Repository[Unit]):
    @abstractmethod
    def list_by_building(self, building_id: UUID) -> List[Unit]: ...

    @abstractmethod
    def list_vacant(self, building_id: UUID) -> List[Unit]: ...

    @abstractmethod
    def get_by_renter(self, renter_id: UUID) -> Optional[Unit]: ...

class RenterRepository(Repository[Renter]):
    @abstractmethod
    def get_active_for_unit(self, unit_id: UUID) -> Optional[Renter]: ...

    @abstractmethod
    def list_by_owner(self, owner_id: UUID) -> List[Renter]: ...

class RentRecordRepository(Repository[RentRecord]):
    @abstractmethod
    def get_current_for_unit(self, unit_id: UUID) -> Optional[RentRecord]: ...

    @abstractmethod
    def list_pending_for_owner(self, owner_id: UUID) -> List[RentRecord]: ...

    @abstractmethod
    def list_for_tenant(self, tenant_id: UUID) -> List[RentRecord]: ...

    @abstractmethod
    def list_for_month(self, month: date) -> List[RentRecord]: ...
```

### Rent Repositories

```python
class RentCycleRepository(Repository[RentCycle]):
    @abstractmethod
    def get_active_for_unit(self, unit_id: UUID) -> Optional[RentCycle]: ...

    @abstractmethod
    def generate_for_building(self, building_id: UUID, month: date) -> List[RentRecord]: ...

class LateFeePolicyRepository(Repository[LateFeePolicy]):
    @abstractmethod
    def get_for_building(self, building_id: UUID) -> LateFeePolicy: ...

    @abstractmethod
    def get_default(self) -> LateFeePolicy: ...

class AgreementDraftRepository(Repository[AgreementDraft]):
    @abstractmethod
    def get_pending_for_unit(self, unit_id: UUID) -> Optional[AgreementDraft]: ...
```

### Payment Repositories

```python
class PaymentRepository(Repository[Payment]):
    @abstractmethod
    def get_pending_for_owner(self, owner_id: UUID) -> List[Payment]: ...

    @abstractmethod
    def get_history_for_user(self, user_id: UUID) -> List[Payment]: ...

    @abstractmethod
    def get_by_utr(self, utr: str) -> Optional[Payment]: ...

class TransactionRepository(Repository[PaymentTransaction]):
    @abstractmethod
    def list_for_payment(self, payment_id: UUID) -> List[PaymentTransaction]: ...

    @abstractmethod
    def create_manual(self, payment_id: UUID, utr: str, amount: Decimal) -> PaymentTransaction: ...
```

### Notification Repositories

```python
class NotificationRepository(Repository[Notification]):
    @abstractmethod
    def list_unread_for_user(self, user_id: UUID) -> List[Notification]: ...

    @abstractmethod
    def mark_as_read(self, notification_id: UUID) -> None: ...

    @abstractmethod
    def list_for_user(self, user_id: UUID, limit: int = 50) -> List[Notification]: ...

class NotificationPreferenceRepository(Repository[NotificationPreference]):
    @abstractmethod
    def get_for_user(self, user_id: UUID) -> NotificationPreference: ...

    @abstractmethod
    def update_for_user(self, user_id: UUID, prefs: dict) -> NotificationPreference: ...

class NotificationTemplateRepository(Repository[NotificationTemplate]):
    @abstractmethod
    def get_by_event(self, event_type: str, channel: str) -> NotificationTemplate: ...
```

### Document Repositories

```python
class DocumentRepository(Repository[Document]):
    @abstractmethod
    def get_by_owner(self, owner_id: UUID, document_type: str) -> List[Document]: ...

    @abstractmethod
    def get_latest_for_rent(self, rent_id: UUID) -> Optional[Document]: ...

class DocumentTemplateRepository(Repository[DocumentTemplate]):
    @abstractmethod
    def get_by_context(self, context: str) -> List[DocumentTemplate]: ...

    @abstractmethod
    def get_default(self, context: str) -> DocumentTemplate: ...
```

### Finance Repositories

```python
class TaxRecordRepository(Repository[TaxRecord]):
    @abstractmethod
    def list_for_owner(self, owner_id: UUID, financial_year: str) -> List[TaxRecord]: ...

    @abstractmethod
    def get_by_acknowledgement(self, ack_number: str) -> Optional[TaxRecord]: ...

class CAProfileRepository(Repository[CAProfile]):
    @abstractmethod
    def list_for_owner(self, owner_id: UUID) -> List[CAProfile]: ...

    @abstractmethod
    def get_primary_for_owner(self, owner_id: UUID) -> Optional[CAProfile]: ...
```

### Referral Repositories

```python
class ReferralCodeRepository(Repository[ReferralCode]):
    @abstractmethod
    def get_by_code(self, code: str) -> Optional[ReferralCode]: ...

    @abstractmethod
    def get_active_for_user(self, user_id: UUID) -> Optional[ReferralCode]: ...

class ReferralBonusRepository(Repository[ReferralBonus]):
    @abstractmethod
    def list_for_user(self, user_id: UUID) -> List[ReferralBonus]: ...

    @abstractmethod
    def get_pending_for_user(self, user_id: UUID) -> List[ReferralBonus]: ...
```

### AI Repositories

```python
class ChatSessionRepository(Repository[ChatSession]):
    @abstractmethod
    def get_active_for_user(self, user_id: UUID) -> Optional[ChatSession]: ...

    @abstractmethod
    def list_for_user(self, user_id: UUID, limit: int = 50) -> List[ChatSession]: ...

class ChatMessageRepository(Repository[ChatMessage]):
    @abstractmethod
    def list_for_session(self, session_id: UUID, limit: int = 100) -> List[ChatMessage]: ...

class PromptRepository(Repository[AIPrompt]):
    @abstractmethod
    def get_active(self, prompt_name: str) -> AIPrompt: ...

    @abstractmethod
    def list_by_context(self, context: str) -> List[AIPrompt]: ...
```

### Dashboard Repositories

```python
class MetricRepository(Repository[DashboardMetric]):
    @abstractmethod
    def get_for_owner(self, owner_id: UUID, metric_name: str, period: str) -> DashboardMetric: ...

    @abstractmethod
    def compute_owner_metrics(self, owner_id: UUID) -> OwnerMetrics: ...

class ReportRepository(Repository[ReportJob]):
    @abstractmethod
    def get_pending_for_user(self, user_id: UUID) -> List[ReportJob]: ...
```

---

## Repository Implementation Rules

1. **Interface in Domain, Implementation in Infrastructure:** Repository interfaces live in `domain/`, implementations in `infrastructure/`.
2. **No Business Logic in Repositories:** Repositories handle data access only. Business rules live in domain services.
3. **No Cross-App Repositories:** Each context has its own repositories. Cross-context data access goes through application services.
4. **Optimized Queries:** Implementations use `select_related`/`prefetch_related` where appropriate.
5. **Transaction Boundaries:** Repositories do not manage transactions. Application services define transaction boundaries.
6. **Testability:** Repositories can be mocked using the interface. Implementations are tested with integration tests.

---

## Query Objects / Selectors

For complex read operations that don't return domain entities, use selectors:

```python
class PropertyDashboardSelector:
    def __init__(self, building_repo: BuildingRepository, unit_repo: UnitRepository):
        self.building_repo = building_repo
        self.unit_repo = unit_repo

    def get_owner_dashboard(self, owner_id: UUID) -> OwnerDashboard:
        buildings = self.building_repo.list_by_owner(owner_id)
        total_units = sum(self.unit_repo.count_for_building(b.id) for b in buildings)
        return OwnerDashboard(
            building_count=len(buildings),
            unit_count=total_units,
            occupancy_rate=self._calculate_occupancy(buildings),
        )
```

Selectors live in `application/queries/` and are read-only. They do not modify data.

---

*Repositories are the boundary between domain logic and persistence. Changes to database schema do not affect domain code.*
