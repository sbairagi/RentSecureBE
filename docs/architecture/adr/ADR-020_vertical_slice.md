# ADR-020: Vertical Slice Architecture for Features

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure features span multiple layers (views, services, repositories, models). Without a clear organization pattern:
- Related code is scattered across layers
- Developers must navigate multiple directories
- Feature changes touch many files
- Onboarding is difficult

---

## Decision

RentSecure uses **vertical slice architecture** for feature organization, where practical.

**Vertical slice:** Each feature is organized as a vertical slice through the architecture:
```
features/
├── submit_payment/
│   ├── command.py           # SubmitPaymentCommand
│   ├── handler.py           # SubmitPaymentHandler
│   ├── service.py           # PaymentService.submit_payment()
│   ├── repository.py        # PaymentRepository
│   ├── serializer.py        # SubmitPaymentSerializer
│   └── view.py              # SubmitPaymentView
```

**When to use vertical slices:**
- New features
- Complex features spanning multiple layers
- Features with clear boundaries

**When NOT to use vertical slices:**
- Shared domain logic (belongs in domain layer)
- Cross-cutting concerns (belongs in shared/platform)
- Simple CRUD (use standard structure)

---

## Alternatives Considered

### 1. Horizontal Layering

**Description:** Organize by layer (all views together, all services together).

**Pros:**
- Familiar Django pattern
- Easy to find all views

**Cons:**
- Related code is scattered
- Feature changes touch many directories
- Hard to understand feature as a whole

**Decision:** Rejected. Navigation cost is high.

### 2. Vertical Slices Only

**Description:** Organize everything as vertical slices.

**Pros:**
- Features are self-contained
- Easy to understand feature as a whole

**Cons:**
- Code duplication across slices
- Hard to share domain logic
- Unclear where shared code lives

**Decision:** Rejected. Duplicates shared logic.

### 3. Hybrid Approach (Selected)

**Description:** Horizontal structure for shared code; vertical slices for features.

**Pros:**
- Shared code is centralized
- Features are self-contained
- Clear ownership

**Cons:**
- Two organization patterns
- Requires judgment on which to use

**Decision:** Accepted. Best balance.

---

## Consequences

### Positive
- Features are self-contained
- Easy to understand feature as a whole
- Shared code is centralized
- Clear ownership

### Negative
- Two organization patterns
- Requires judgment

### Neutral
- Standard app structure for shared code
- Vertical slices for features

---

## References

- [Target Folder Structure](docs/architecture/future/03_target_folder_structure.md)
- [Architecture Principles](architecture/ARCHITECTURE_PRINCIPLES.md)
