# ADR-022: Cache Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure needs caching for:
- Dashboard analytics (expensive aggregations)
- Subscription feature flags
- User permissions
- API rate limiting

Year 1 constraints:
- Single EC2 instance
- Zero additional infrastructure cost
- Django Local Memory Cache

---

## Decision

RentSecure uses **Django Local Memory Cache** in Year 1, with a **cache abstraction** that allows swapping to Redis later.

**Cache layers:**
1. **L1: In-memory cache** (Django LocMemCache) - Year 1
2. **L2: Redis** (Stage 2) - When multiple workers are needed

**Cache strategy:**
- Cache-aside for expensive queries
- TTL-based invalidation
- Event-based invalidation for mutations
- No cache for user-specific data (LocMem is per-process)

---

## Alternatives Considered

### 1. Redis from Day 1

**Description:** Use Redis for all caching.

**Pros:**
- Production-ready
- Shared across workers
- Atomic operations

**Cons:**
- Additional infrastructure
- Cost in Year 1
- Overkill for single instance

**Decision:** Rejected. Premature for Year 1.

### 2. No Caching

**Description:** Query database directly.

**Pros:**
- Simple
- No cache invalidation

**Cons:**
- Slow dashboards
- High database load
- Poor user experience

**Decision:** Rejected. Performance issues.

### 3. Cache Abstraction (Selected)

**Description:** Abstract cache behind interface; use LocMem in Year 1, Redis later.

**Pros:**
- Zero cost in Year 1
- Easy migration to Redis
- Consistent cache usage
- Testable

**Cons:**
- More code (interface + implementations)

**Decision:** Accepted. Best for Year 1.

---

## Consequences

### Positive
- Zero additional infrastructure in Year 1
- Easy migration to Redis later
- Consistent cache usage
- Fast dashboard loads

### Negative
- Cache is per-process (not shared)
- Cache invalidation is per-process

### Neutral
- Redis migration is a configuration change
- Cache interface remains stable

---

## References

- [Production Architecture](../production-architecture.md)
- [Platform Adapters](../future/03_target_folder_structure.md)
