# ADR-009: Configuration Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure needs a configuration strategy that:
- Supports multiple environments (development, staging, production)
- Keeps secrets out of version control
- Makes environment-specific settings explicit
- Supports feature flags
- Allows easy deployment configuration changes

---

## Decision

Configuration is organized into **environment-specific settings files** with a clear inheritance hierarchy.

**Structure:**
```
config/settings/
├── __init__.py          # Exports current environment settings
├── base.py              # Shared settings (all environments)
├── development.py       # Local development overrides
├── production.py        # Production overrides
├── testing.py           # Test environment overrides
└── ci.py                # CI environment overrides
```

**Rules:**
1. `base.py` contains all default settings
2. Environment files override only what's different
3. Secrets come from environment variables, never from code
4. Feature flags are in `base.py` with environment overrides
5. `DJANGO_SETTINGS_MODULE` selects the environment

---

## Alternatives Considered

### 1. Single settings.py with Environment Variables

**Description:** One settings file with `os.getenv()` everywhere.

**Pros:**
- Simple, single file
- Django community standard

**Cons:**
- Settings file becomes huge
- Hard to see what's environment-specific
- Easy to accidentally commit secrets
- Difficult to compare environments

**Decision:** Rejected. Doesn't scale.

### 2. Django-Environ / python-decouple

**Description:** Use a library to manage environment variables.

**Pros:**
- Handles type casting
- `.env` file support
- Validation

**Cons:**
- Additional dependency
- Still single settings file
- Doesn't solve environment comparison

**Decision:** Rejected. Single file problem remains.

### 3. Split Settings (Selected)

**Description:** Environment-specific settings files with base inheritance.

**Pros:**
- Clear environment separation
- Easy to compare environments
- Secrets only in environment files
- Supports `from base import *` pattern

**Cons:**
- More files
- Requires discipline

**Decision:** Accepted. Best for multi-environment support.

---

## Configuration Hierarchy

```python
# config/settings/__init__.py
from .base import *  # Start with base settings

env = os.environ.get("DJANGO_ENV", "development")

if env == "production":
    from .production import *
elif env == "testing":
    from .testing import *
elif env == "ci":
    from .ci import *
else:
    from .development import *
```

```python
# config/settings/base.py
INSTALLED_APPS = [
    "django.contrib.admin",
    "apps.identity",
    "apps.subscription",
    ...
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    ...
]

# Feature flags
FEATURE_FLAGS = {
    "CASHFREE_PAYMENTS": env("CASHFREE_PAYMENTS_ENABLED", default=False),
    "WHATSAPP_NOTIFICATIONS": env("WHATSAPP_NOTIFICATIONS_ENABLED", default=False),
    ...
}
```

---

## Secrets Management

```python
# config/settings/base.py
import os
from pathlib import Path

# Never hardcode secrets
SECRET_KEY = env("DJANGO_SECRET_KEY")
DATABASE_URL = env("DATABASE_URL")
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
```

**Rules:**
1. Secrets come from environment variables only
2. `.env` files are gitignored
3. `.env.example` contains placeholder values
4. No secrets in settings files

---

## Feature Flags

```python
# config/settings/base.py
FEATURE_FLAGS = {
    # Payment
    "CASHFREE_PAYMENTS_ENABLED": env.bool("CASHFREE_PAYMENTS_ENABLED", default=False),
    "RAZORPAY_PAYMENTS_ENABLED": env.bool("RAZORPAY_PAYMENTS_ENABLED", default=False),
    "UPI_PAYMENT_ENABLED": env.bool("UPI_PAYMENT_ENABLED", default=True),

    # Notification
    "WHATSAPP_NOTIFICATIONS_ENABLED": env.bool("WHATSAPP_NOTIFICATIONS_ENABLED", default=False),
    "SMS_NOTIFICATIONS_ENABLED": env.bool("SMS_NOTIFICATIONS_ENABLED", default=False),

    # Search
    "OPENSEARCH_ENABLED": env.bool("OPENSEARCH_ENABLED", default=False),

    # Background Jobs
    "CELERY_ENABLED": env.bool("CELERY_ENABLED", default=False),
}
```

---

## Consequences

### Positive
- Clear environment separation
- Easy to compare settings across environments
- Secrets are never in version control
- Feature flags are explicit
- Easy to add new environments

### Negative
- More files to manage
- Requires discipline to keep environments in sync

### Neutral
- Settings are versioned
- Environment selection via `DJANGO_SETTINGS_MODULE`

---

## References

- [Production Architecture](../production-architecture.md)
- [Architecture Principles](../../../architecture/ARCHITECTURE_PRINCIPLES.md)
