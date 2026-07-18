# ADR-013: Error Handling Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure needs a consistent error handling strategy that:
- Provides clear error messages to API consumers
- Logs errors with sufficient context for debugging
- Handles domain errors, infrastructure errors, and validation errors differently
- Supports internationalization
- Maintains security (no stack traces in production)

---

## Decision

RentSecure uses a **layered exception hierarchy** with domain-specific exceptions.

**Exception hierarchy:**
```
DomainException (base)
├── ValidationException
│   ├── InvalidInputException
│   └── BusinessRuleViolationException
├── NotFoundException
├── PermissionDeniedException
├── ConflictException (e.g., duplicate resource)
└── ExternalServiceException

InfrastructureException (wraps external errors)
├── DatabaseException
├── PaymentGatewayException
├── NotificationException
└── StorageException
```

**Rules:**
1. Domain layer raises domain exceptions
2. Infrastructure layer wraps external errors in infrastructure exceptions
3. Application layer translates exceptions to HTTP responses
4. Presentation layer returns consistent error envelopes
5. All exceptions are logged with structured context

---

## Alternatives Considered

### 1. Django's Built-in Exceptions

**Description:** Use Django's HTTP exceptions directly.

**Pros:**
- Simple, Django-native

**Cons:**
- No domain-specific exceptions
- Hard to distinguish domain vs infrastructure errors
- No structured error response format
- Inconsistent error messages

**Decision:** Rejected. Lacks domain semantics.

### 2. DRF's Exception Handler

**Description:** Use DRF's default exception handling.

**Pros:**
- Integrated with DRF
- Handles common exceptions

**Cons:**
- Not domain-aware
- Hard to customize consistently
- No structured error responses

**Decision:** Rejected. Needs domain layer.

### 3. Layered Exception Hierarchy (Selected)

**Description:** Domain exceptions → Infrastructure exceptions → HTTP exceptions.

**Pros:**
- Clear error semantics
- Consistent error responses
- Easy to debug
- Supports i18n
- Separates domain and infrastructure errors

**Cons:**
- More code (exception classes)
- Requires discipline

**Decision:** Accepted. Best for maintainability.

---

## Error Response Format

```json
{
    "error": {
        "code": "PAYMENT_ALREADY_VERIFIED",
        "message": "This payment has already been verified",
        "details": {
            "payment_id": "123e4567-e89b-12d3-a456-426614174000"
        },
        "timestamp": "2026-07-14T10:30:00Z",
        "request_id": "req-abc123"
    }
}
```

---

## Consequences

### Positive
- Clear error semantics across layers
- Consistent API error responses
- Easy to debug with structured logging
- Supports i18n error messages
- Domain errors are distinguishable from infrastructure errors

### Negative
- More exception classes to maintain
- Requires discipline to use correctly

### Neutral
- DRF exception handler translates domain exceptions to HTTP responses
- Infrastructure exceptions are wrapped in domain exceptions

---

## References

- [Layer Rules](../future/04_layer_rules.md)
- [Architecture Principles](../../../architecture/ARCHITECTURE_PRINCIPLES.md)
