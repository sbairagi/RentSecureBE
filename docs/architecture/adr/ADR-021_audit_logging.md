# ADR-021: Audit Logging Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure needs audit logging for:
- Compliance (tax records, financial transactions)
- Security (user actions, permission changes)
- Debugging (who did what and when)

---

## Decision

RentSecure uses **django-simple-history** for model-level audit logging, combined with **structured application logging** for action-level audit trails.

**Rules:**
1. All mutations to sensitive models are tracked via `django-simple-history`
2. All application service methods log entry/exit with structured context
3. Audit logs include: user_id, action, timestamp, changes, IP address
4. Audit logs are immutable (append-only)
5. Audit logs are retained for 7 years (compliance requirement)

---

## Alternatives Considered

### 1. Manual Audit Logging

**Description:** Manually create audit log entries in services.

**Pros:**
- Full control
- Flexible format

**Cons:**
- Easy to forget
- Inconsistent across services
- Hard to maintain

**Decision:** Rejected. Error-prone.

### 2. Django-Simple-History Only

**Description:** Use only django-simple-history for all audit logging.

**Pros:**
- Automatic model tracking
- Minimal code

**Cons:**
- Only tracks model changes
- No action-level logging
- No request context

**Decision:** Rejected. Insufficient for security logging.

### 3. Combined Approach (Selected)

**Description:** django-simple-history for model changes + structured logging for actions.

**Pros:**
- Automatic model tracking
- Action-level logging with context
- Consistent format
- Easy to query

**Cons:**
- Two mechanisms to maintain

**Decision:** Accepted. Best coverage.

---

## Implementation

```python
# Model-level audit (automatic)
class Payment(models.Model):
    # ... fields ...

    history = HistoricalRecords()

# Action-level audit (manual in services)
class PaymentService:
    def verify_payment(self, command: VerifyPaymentCommand) -> PaymentResult:
        logger.info(
            "payment.verification.started",
            extra={
                "user_id": command.owner_id,
                "payment_id": command.payment_id,
                "ip_address": get_client_ip(),
            }
        )
        # ... business logic ...
        logger.info(
            "payment.verification.completed",
            extra={
                "user_id": command.owner_id,
                "payment_id": payment.id,
                "status": payment.status,
            }
        )
```

---

## Consequences

### Positive
- Complete audit trail
- Compliant with regulations
- Easy to debug issues
- Immutable logs

### Negative
- Storage cost for long retention
- Two mechanisms to maintain

### Neutral
- Logs are structured JSON for easy querying
- Retention policy is configurable

---

## References

- [Security Rules](../../../.kilo/instructions/security.md)
- [Architecture Principles](../../../architecture/ARCHITECTURE_PRINCIPLES.md)
