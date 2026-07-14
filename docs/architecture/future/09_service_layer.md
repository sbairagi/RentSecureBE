# Service Layer

This document defines the service layer responsibilities for the RentSecure platform.

---

## Service Types

RentSecure uses three types of services:

| Type | Location | Responsibility | Example |
|------|----------|---------------|---------|
| **Application Service** | `application/services/` | Orchestrates workflows, coordinates between repositories and external services | `PaymentService.submit_payment()` |
| **Domain Service** | `domain/policies/` | Encapsulates domain logic that doesn't naturally belong to an entity | `LateFeeCalculator.calculate()` |
| **Infrastructure Service** | `infrastructure/` or `platform/` | Wraps external systems (payment gateways, email providers) | `RazorpayAdapter.create_payment()` |

---

## Application Services

### Responsibilities

Application services are the **only entry point for business workflows**. They:

1. Receive input from the presentation layer
2. Validate input using domain policies
3. Load entities via repositories
4. Execute domain logic on entities
5. Persist changes via repositories
6. Publish domain events
7. Return results to the presentation layer

### Rules

```python
class ApplicationService:
    """Base class for all application services."""

    def __init__(self, dependencies...):
        self._dependencies = dependencies

    def _validate(self, command: Command) -> None:
        """Validate command using domain policies."""
        raise NotImplementedError

    def _execute(self, command: Command) -> Result:
        """Execute the core business workflow."""
        raise NotImplementedError

    def _publish_events(self, entity: Entity) -> None:
        """Publish any domain events from the entity."""
        raise NotImplementedError

    def handle(self, command: Command) -> Result:
        """Public entry point. Orchestrates the workflow."""
        self._validate(command)
        result = self._execute(command)
        self._publish_events(result.entity)
        return result
```

### Example: PaymentService

```python
# apps/payment/application/services/payment_service.py
class PaymentService:
    def __init__(
        self,
        payment_repo: PaymentRepository,
        rent_repo: RentRecordRepository,
        gateway: PaymentGateway,
        notifier: NotificationService,
        receipt_generator: DocumentService,
        event_bus: EventBus,
    ):
        self.payment_repo = payment_repo
        self.rent_repo = rent_repo
        self.gateway = gateway
        self.notifier = notifier
        self.receipt_generator = receipt_generator
        self.event_bus = event_bus

    def submit_payment(self, command: SubmitPaymentCommand) -> PaymentResult:
        rent = self.rent_repo.get(command.rent_id)

        payment = Payment.create(
            tenant_id=command.tenant_id,
            rent_id=command.rent_id,
            amount=rent.amount_due,
            utr=command.utr,
            method="manual_upi",
        )

        self.payment_repo.create(payment)
        self.event_bus.publish(PaymentSubmitted(
            payment_id=payment.id,
            tenant_id=payment.tenant_id,
            amount=payment.amount,
        ))

        self.notifier.send(
            recipient=rent.owner_id,
            event="PaymentSubmitted",
            context={"payment_id": payment.id, "amount": payment.amount},
        )

        return PaymentResult.success(payment)

    def verify_payment(self, command: VerifyPaymentCommand) -> PaymentResult:
        payment = self.payment_repo.get(command.payment_id)

        if payment.tenant_id != command.tenant_id:
            raise PermissionDenied("Cannot verify another user's payment")

        payment.mark_verified(verified_by=command.owner_id)
        self.payment_repo.update(payment)

        receipt = self.receipt_generator.generate(
            template_id="rent_receipt",
            context={"payment": payment, "rent": payment.rent},
        )

        self.event_bus.publish(PaymentVerified(
            payment_id=payment.id,
            tenant_id=payment.tenant_id,
            receipt_id=receipt.id,
        ))

        self.notifier.send(
            recipient=payment.tenant_id,
            event="PaymentVerified",
            context={"payment_id": payment.id, "receipt_url": receipt.url},
        )

        return PaymentResult.success(payment, receipt=receipt)
```

### Rules

1. **Stateless:** Application services have no instance state. All state is passed via method arguments.
2. **Single Responsibility:** Each method handles one use case.
3. **No HTTP:** Services must not import Django request/response objects.
4. **No Serializers:** Services must not import or use DRF serializers.
5. **No Direct Model Queries:** Services use repositories, not raw ORM queries.
6. **Dependency Injection:** All dependencies are injected via constructor.
7. **Return DTOs:** Services return Data Transfer Objects, not domain entities (unless read-only).
8. **Publish Events:** State changes are communicated via domain events.

---

## Domain Services

### Responsibilities

Domain services encapsulate business logic that doesn't naturally belong to a single entity.

### When to Use a Domain Service

Use a domain service when:
- Logic involves multiple entities
- Logic is a natural verb that doesn't belong to one entity
- Logic is shared across multiple aggregates

### Example: LateFeeCalculator

```python
# apps/rent/domain/policies/late_fee_calculator.py
class LateFeeCalculator:
    """Calculates late fees based on policy and days overdue."""

    def __init__(self, policy: LateFeePolicy):
        self.policy = policy

    def calculate(self, rent_record: RentRecord, today: date) -> Decimal:
        days_late = (today - rent_record.due_date).days
        if days_late <= self.policy.grace_period_days:
            return Decimal("0.00")

        late_days = days_late - self.policy.grace_period_days
        flat_fee = self.policy.flat_fee
        percentage_fee = rent_record.amount * (self.policy.percentage / 100)

        return flat_fee + percentage_fee
```

### Rules

1. **Pure Functions:** Domain services should be stateless and deterministic.
2. **No Side Effects:** Domain services must not modify state directly (they return values).
3. **Depend on Domain Only:** Domain services can only depend on domain entities and value objects.
4. **No Infrastructure:** Domain services must not import from infrastructure or platform layers.

---

## Infrastructure Services (Adapters)

### Responsibilities

Infrastructure services implement external system integrations (payment gateways, email providers, storage).

### Example: ManualPaymentAdapter

```python
# apps/payment/infrastructure/adapters/manual_payment_adapter.py
class ManualPaymentAdapter(PaymentGateway):
    """Year 1 manual UPI payment adapter."""

    def create_payment(self, order: PaymentOrder) -> PaymentResult:
        return PaymentResult(
            status="pending_manual",
            reference=order.id,
            instructions=f"Pay {order.amount} via UPI to owner@upi",
        )

    def verify_payment(self, payment_id: UUID, utr: str) -> PaymentVerification:
        return PaymentVerification(
            status="manual_verification_required",
            message="Payment must be verified by owner",
        )
```

### Example: RazorpayAdapter (Stage 2, Disabled)

```python
# apps/payment/infrastructure/adapters/razorpay_payment_adapter.py
class RazorpayAdapter(PaymentGateway):
    """Stage 2 Razorpay payment adapter."""

    def __init__(self, api_key: str, api_secret: str):
        self.client = razorpay.Client(a=(api_key, api_secret))

    def create_payment(self, order: PaymentOrder) -> PaymentResult:
        razorpay_order = self.client.order.create({
            "amount": int(order.amount * 100),
            "currency": "INR",
            "receipt": str(order.id),
        })
        return PaymentResult(
            status="created",
            reference=razorpay_order["id"],
            payment_url=razorpay_order["short_url"],
        )
```

### Rules

1. **Implement Interfaces:** All adapters implement platform-defined interfaces.
2. **Feature Flags:** Premium adapters are disabled via feature flags.
3. **Error Wrapping:** External errors are wrapped in domain exceptions.
4. **Retry Logic:** Infrastructure services implement retry logic with exponential backoff.
5. **No Business Logic:** Adapters translate between external APIs and domain interfaces only.

---

## External Service Wrappers

### Notification Service

```python
# apps/notification/application/services/notification_service.py
class NotificationService:
    """Orchestrates notification dispatch across channels."""

    def __init__(
        self,
        channels: List[NotificationChannel],  # Injected via DI
        preference_repo: NotificationPreferenceRepository,
        template_repo: NotificationTemplateRepository,
        event_bus: EventBus,
    ):
        self.channels = channels
        self.preference_repo = preference_repo
        self.template_repo = template_repo
        self.event_bus = event_bus

    def send(self, user_id: UUID, event: str, context: dict) -> NotificationResult:
        prefs = self.preference_repo.get_for_user(user_id)
        template = self.template_repo.get_by_event(event, prefs.preferred_channel)

        results = []
        for channel in self.channels:
            if not prefs.is_channel_enabled(channel.name):
                continue

            result = channel.send(
                recipient=user_id,
                template=template,
                context=context,
            )
            results.append(result)

        self.event_bus.publish(NotificationSent(
            user_id=user_id,
            event=event,
            results=results,
        ))

        return NotificationResult.aggregate(results)
```

---

## Service Layer Rules Summary

| Rule | Description |
|------|-------------|
| **Services are stateless** | No instance state; all data via method arguments |
| **Services orchestrate** | Services coordinate, not execute domain logic |
| **Services depend on abstractions** | Constructor injection of interfaces |
| **Services publish events** | All state changes emit domain events |
| **Services are testable** | Dependencies are mockable via interfaces |
| **Services are thin** | Complex logic belongs in domain services or entities |
| **Services handle errors** | Wrap external errors in domain exceptions |
| **Services enforce transactions** | Define transaction boundaries |

---

## Transaction Boundaries

```python
class PaymentService:
    @transaction.atomic
    def submit_payment(self, command: SubmitPaymentCommand) -> PaymentResult:
        """All database operations in this method are atomic."""
        payment = self.payment_repo.create(...)
        self.rent_repo.update(...)
        return PaymentResult.success(payment)
```

---

*The service layer is the contract between the presentation layer and the domain. All business workflows must pass through services.*
