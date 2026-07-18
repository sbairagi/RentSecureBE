# ADR-010: Payment Integration Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure needs a payment integration that:
- Is cost-free in Year 1 (manual UPI)
- Supports payment gateways in Stage 2 (Razorpay/Cashfree)
- Is idempotent and supports retries
- Generates receipts automatically
- Supports refunds

---

## Decision

RentSecure uses a **payment gateway abstraction** with feature-flagged adapters.

**Year 1 (Active):**
- `ManualPaymentAdapter`: Manual UPI payment flow
- Tenant submits UTR, owner verifies manually
- Zero transaction fees

**Stage 2 (Disabled):**
- `RazorpayAdapter`: Razorpay integration
- `CashfreeAdapter`: Cashfree integration
- Enabled via `PAYMENT_GATEWAY_ENABLED` feature flag

**Key rules:**
- All adapters implement `PaymentGateway` interface
- Payment flows are idempotent
- All state changes emit domain events
- Receipts are generated via Document service
- Notifications are sent via Notification service

---

## Alternatives Considered

### 1. Direct Payment Gateway Integration

**Description:** Integrate Razorpay/Cashfree directly without abstraction.

**Pros:**
- Simple implementation
- No abstraction overhead

**Cons:**
- Hard to switch gateways later
- No fallback to manual payments
- Tightly coupled to one provider
- Difficult to test

**Decision:** Rejected. Locks into one provider.

### 2. Multiple Integrations Without Abstraction

**Description:** Support multiple gateways but without common interface.

**Pros:**
- Multiple options for users

**Cons:**
- Code duplication across gateways
- Inconsistent behavior
- Hard to maintain

**Decision:** Rejected. Needs common interface.

### 3. Gateway Abstraction with Feature Flags (Selected)

**Description:** All gateways implement `PaymentGateway` interface; selection via feature flag.

**Pros:**
- Easy to switch gateways
- Fallback to manual payments
- Consistent behavior across gateways
- Easy to test with mocks
- Supports future gateways

**Cons:**
- More code (interface + adapters)
- Requires discipline to maintain interface

**Decision:** Accepted. Best for long-term flexibility.

---

## Payment Flow (Year 1)

```
Tenant clicks "Pay Rent"
    │
    ▼
PaymentService.submit_payment(tenant_id, rent_id, utr)
    │
    ├──▶ Create Payment record (status: pending)
    ├──▶ Publish PaymentSubmitted event
    ├──▶ Notify owner: "Payment pending verification"
    │
Owner reviews payment
    │
    ▼
PaymentService.verify_payment(payment_id, owner_id)
    │
    ├──▶ Update Payment (status: verified)
    ├──▶ DocumentService.generate_receipt(payment_id)
    ├──▶ Publish PaymentVerified event
    ├──▶ Notify tenant: "Payment approved"
    │
Tenant receives receipt
```

---

## Consequences

### Positive
- Zero transaction fees in Year 1
- Easy to add payment gateways in Stage 2
- Idempotent payment flows
- Consistent behavior across payment methods
- Easy to test

### Negative
- Manual verification overhead in Year 1
- More code (interface + adapters)

### Neutral
- Stage 2 migration is a configuration change
- Manual UPI remains as fallback

---

## References

- [Production Architecture](../production-architecture.md)
- [Finance Rules](../../../.kilo/instructions/finance.md)
- [Bounded Contexts](../future/02_bounded_contexts.md)
