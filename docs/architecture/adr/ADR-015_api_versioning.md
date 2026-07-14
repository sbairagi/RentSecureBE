# ADR-015: API Versioning Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure's API is consumed by:
- Web frontend (Expo React Native)
- Mobile apps (iOS, Android)
- Third-party integrations (future)

API changes are inevitable as the product evolves. We need a versioning strategy that:
- Maintains backward compatibility
- Allows incremental API improvements
- Supports multiple API versions simultaneously
- Provides clear deprecation path

---

## Decision

RentSecure uses **URL path versioning** for API versioning.

**Format:** `/api/v{version}/{endpoint}`

**Examples:**
- `/api/v1/buildings/`
- `/api/v1/buildings/{id}/`
- `/api/v1/rent-records/`

**Rules:**
1. All API endpoints are versioned
2. Breaking changes require a new version
3. Non-breaking changes (new fields, new endpoints) do not require a new version
4. Deprecated versions are supported for at least 6 months
5. Deprecation is communicated via API headers and documentation

---

## Alternatives Considered

### 1. No Versioning

**Description:** Change API without versioning.

**Pros:**
- Simple URL structure
- No version management

**Cons:**
- Breaking changes break clients
- No deprecation path
- Risky for external consumers

**Decision:** Rejected. Too risky for production.

### 2. Header Versioning

**Description:** Version via `Accept` or custom header.

**Pros:**
- Clean URLs
- Content negotiation

**Cons:**
- Hard to test (browsers don't support well)
- Invisible in browser
- Caching complications

**Decision:** Rejected. Poor developer experience.

### 3. Query Parameter Versioning

**Description:** Version via `?version=1` query parameter.

**Pros:**
- Simple to implement
- Easy to test

**Cons:**
- Not RESTful
- Easy to forget
- Caching complications

**Decision:** Rejected. Not RESTful.

### 4. URL Path Versioning (Selected)

**Description:** Version in URL path (`/api/v1/`).

**Pros:**
- Clear and visible
- RESTful
- Easy to test
- Works with all HTTP clients
- Clear deprecation path

**Cons:**
- URLs change between versions
- More version management

**Decision:** Accepted. Best developer experience.

---

## Versioning Rules

### What Requires a New Version

- Removing a field from response
- Renaming a field
- Changing a field type
- Removing an endpoint
- Changing request/response format

### What Does NOT Require a New Version

- Adding a new endpoint
- Adding optional fields to response
- Adding optional query parameters
- Bug fixes
- Performance improvements

---

## Deprecation Process

1. **Announce:** Add deprecation notice to API docs and response headers
2. **Warn:** Return `Deprecation` header for 3 months
3. **Sunset:** Return `Sunset` header with date 6 months after announcement
4. **Remove:** Remove deprecated version after sunset date

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: </api/v2/buildings/>; rel="successor-version"
```

---

## URL Configuration

```python
# config/urls.py
urlpatterns = [
    path("api/v1/", include("apps.identity.urls.v1")),
    path("api/v1/", include("apps.property.urls.v1")),
    path("api/v1/", include("apps.rent.urls.v1")),
    # Future versions
    # path("api/v2/", include("apps.identity.urls.v2")),
]
```

---

## Consequences

### Positive
- Clear version boundaries
- Backward compatibility is maintainable
- Easy to deprecate old versions
- RESTful and testable
- Clear migration path for clients

### Negative
- URL management overhead
- Multiple versions in codebase simultaneously
- Requires deprecation communication

### Neutral
- Most changes don't require version bumps
- Version support is time-boxed (6 months)

---

## References

- [Architecture Principles](architecture/ARCHITECTURE_PRINCIPLES.md)
- [Production Architecture](docs/architecture/production-architecture.md)
