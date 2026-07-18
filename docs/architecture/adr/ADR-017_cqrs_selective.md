# ADR-017: CQRS for Read/Write Separation

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure has read-heavy workloads (dashboards, analytics) and write-heavy workloads (payment processing, rent generation). Mixing read and write models creates:
- Complex queries for read operations
- Performance bottlenecks on write paths
- Difficult query optimization
- No clear separation of concerns

---

## Decision

RentSecure uses **CQRS selectively** where read and write models diverge significantly.

**When to use CQRS:**
- Dashboard analytics (read model is denormalized)
- Search operations (read model is optimized for search)
- Reporting (read model is pre-aggregated)

**When NOT to use CQRS:**
- Simple CRUD operations
- Operations where read/write models are identical
- Low-traffic endpoints

---

## Alternatives Considered

### 1. CQRS Everywhere

**Description:** Apply CQRS to all operations.

**Pros:**
- Consistent pattern
- Maximum optimization potential

**Cons:**
- Massive code duplication
- Synchronization complexity
- Overkill for simple operations
- High maintenance burden

**Decision:** Rejected. Too complex.

### 2. No CQRS

**Description:** Use single model for all operations.

**Pros:**
- Simple
- No synchronization needed
- Less code

**Cons:**
- Read performance suffers for complex queries
- Query optimization conflicts with write optimization
- No denormalization for analytics

**Decision:** Rejected. Performance issues for dashboards.

### 3. Selective CQRS (Selected)

**Description:** Apply CQRS only where read/write models diverge.

**Pros:**
- Optimizes where needed
- Keeps simple operations simple
- Clear separation for analytics
- Supports materialized views

**Cons:**
- Requires judgment on when to apply
- Some synchronization logic

**Decision:** Accepted. Best balance.

---

## Implementation

### Write Model (Command Side)

```python
class PaymentService:
    def submit_payment(self, command: SubmitPaymentCommand) -> Payment:
        payment = Payment.create(...)
        self.payment_repo.create(payment)
        return payment
```

### Read Model (Query Side)

```python
class PaymentDashboardSelector:
    def get_payment_metrics(self, owner_id: UUID) -> PaymentMetrics:
        # Uses denormalized read model
        return PaymentMetrics.read(owner_id)
```

---

## Consequences

### Positive
- Read performance optimized for dashboards
- Write path remains simple
- Analytics use pre-aggregated data
- Clear separation of concerns

### Negative
- Synchronization logic for read models
- More code for CQRS paths
- Requires judgment on when to apply

### Neutral
- Most operations don't use CQRS
- Read models are eventually consistent

---

## References

- [Architecture Principles](../../../architecture/ARCHITECTURE_PRINCIPLES.md)
- [Repository Pattern](../future/08_repository_pattern.md)
