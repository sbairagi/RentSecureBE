# ADR-011: Notification Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure needs a notification system that:
- Is cost-free in Year 1 (Email + FCM Push + In-App)
- Supports WhatsApp/SMS in Stage 2
- Allows users to customize notification preferences
- Provides fallback channels
- Tracks delivery status

---

## Decision

RentSecure uses a **notification channel abstraction** with feature-flagged adapters.

**Year 1 (Active):**
- `EmailAdapter`: Django SMTP / AWS SES
- `FCMAdapter`: Firebase Cloud Messaging
- `InAppAdapter`: Database-backed in-app notifications

**Stage 2 (Disabled):**
- `WhatsAppAdapter`: WhatsApp Business API
- `SMSAdapter`: Twilio / MSG91
- Enabled via feature flags

**Key rules:**
- All adapters implement `NotificationChannel` interface
- Notification preferences are user-configurable
- Fallback logic: primary channel → secondary → email
- All notifications emit `NotificationSent` or `NotificationFailed` events
- Templates are context-specific (provided by domain contexts)

---

## Alternatives Considered

### 1. Direct Notification Calls

**Description:** Call email/push services directly from business logic.

**Pros:**
- Simple, no abstraction

**Cons:**
- Tight coupling to notification providers
- Hard to add channels
- Hard to test
- No fallback logic

**Decision:** Rejected. Creates coupling.

### 2. Single Notification Service

**Description:** One notification service with conditional logic for each channel.

**Pros:**
- Centralized notification logic

**Cons:**
- Service becomes too complex
- Hard to add new channels
- Conditional logic is hard to maintain

**Decision:** Rejected. Doesn't scale.

### 3. Channel Abstraction with Feature Flags (Selected)

**Description:** Each channel is an adapter implementing a common interface.

**Pros:**
- Easy to add new channels
- Consistent behavior across channels
- Easy to test with mocks
- Supports fallback logic
- Feature flags control channel availability

**Cons:**
- More code (interface + adapters)
- Requires discipline

**Decision:** Accepted. Best for long-term flexibility.

---

## Notification Flow

```
Business event occurs (e.g., PaymentSubmitted)
    │
    ▼
NotificationService.send(user_id, "PaymentSubmitted", context)
    │
    ├──▶ Get user preferences
    ├──▶ Get template for event + channel
    ├──▶ For each enabled channel:
    │       ├──▶ Render template with context
    │       ├──▶ Send via adapter
    │       └──▶ Track result
    │
    ├──▶ Publish NotificationSent event
    └──▶ Return aggregated result
```

---

## Consequences

### Positive
- Zero cost in Year 1 (free channels)
- Easy to add WhatsApp/SMS in Stage 2
- User-customizable preferences
- Fallback logic ensures delivery
- Easy to test

### Negative
- More code (interface + adapters)
- Template management complexity

### Neutral
- Templates are provided by domain contexts
- Notification service is the single entry point

---

## References

- [Notification Rules](.kilo/instructions/notifications.md)
- [Production Architecture](docs/architecture/production-architecture.md)
- [Bounded Contexts](docs/architecture/future/02_bounded_contexts.md)
