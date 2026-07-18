# ADR-016: Feature Flag Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure needs feature flags to:
- Control premium integrations (payment gateways, notification channels)
- Enable canary releases
- Support gradual rollout of new features
- Allow A/B testing
- Provide kill switches for problematic features

---

## Decision

RentSecure uses **environment-based feature flags** with a centralized registry.

**Implementation:**
- Feature flags defined in `config/settings/base.py`
- Feature flag checks via `features.flags.is_enabled(flag_name, user_id=None)`
- UI displays "Coming Soon" for disabled features
- Premium integrations are always behind feature flags

**Key flags:**
```python
FEATURE_FLAGS = {
    # Payment
    "CASHFREE_PAYMENTS_ENABLED": False,
    "RAZORPAY_PAYMENTS_ENABLED": False,
    "UPI_PAYMENT_ENABLED": True,

    # Notification
    "WHATSAPP_NOTIFICATIONS_ENABLED": False,
    "SMS_NOTIFICATIONS_ENABLED": False,

    # Search
    "OPENSEARCH_ENABLED": False,

    # Background Jobs
    "CELERY_ENABLED": False,
}
```

---

## Alternatives Considered

### 1. No Feature Flags

**Description:** Deploy features directly without flags.

**Pros:**
- Simple
- No flag management overhead

**Cons:**
- No kill switch for problematic features
- No gradual rollout
- No canary releases
- High risk for premium integrations

**Decision:** Rejected. Too risky for premium features.

### 2. Third-Party Feature Flag Service

**Description:** Use LaunchDarkly, Split.io, etc.

**Pros:**
- Rich UI
- Analytics
- A/B testing support

**Cons:**
- Additional cost
- External dependency
- Latency overhead
- Overkill for current scale

**Decision:** Rejected. Cost and dependency concerns for Year 1.

### 3. Environment-Based Flags (Selected)

**Description:** Feature flags in settings, checked at runtime.

**Pros:**
- Simple implementation
- No external dependencies
- Fast (no network call)
- Easy to test
- Supports gradual rollout via user targeting

**Cons:**
- No UI for flag management
- Requires deployment to change flags
- No analytics

**Decision:** Accepted. Best for Year 1. Upgrade to third-party in Stage 3 if needed.

---

## Consequences

### Positive
- Premium integrations are safely controlled
- Kill switches for problematic features
- Supports gradual rollout
- No external dependencies
- Fast flag evaluation

### Negative
- Requires deployment to change flags
- No UI for non-technical users
- No analytics on flag usage

### Neutral
- Flags are environment-specific
- User-targeted flags can be added later

---

## References

- [Production Architecture](../production-architecture.md)
- [Payment Rules](../../../.kilo/instructions/finance.md)
- [Notification Rules](../../../.kilo/instructions/notifications.md)
