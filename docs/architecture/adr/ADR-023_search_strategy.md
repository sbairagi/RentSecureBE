# ADR-023: Search Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure needs search for:
- Property search (name, address, amenities)
- Renter search
- Document search

Year 1 constraints:
- Single EC2 instance
- Zero additional infrastructure cost
- PostgreSQL full-text search

Stage 3 trigger:
- Search latency > 500ms
- Search complexity requires faceting, highlighting, synonyms

---

## Decision

RentSecure uses **PostgreSQL full-text search** in Year 1, with an **OpenSearch abstraction** for Stage 3.

**Year 1:**
- PostgreSQL full-text search with trigram indexes
- `SearchVector`, `SearchQuery`, `SearchRank`
- `GinIndex` with `gin_trgm_ops`

**Stage 3:**
- OpenSearch for advanced search features
- Faceted search, highlighting, synonyms
- Dual-write during transition

---

## Alternatives Considered

### 1. OpenSearch from Day 1

**Description:** Use OpenSearch for all search.

**Pros:**
- Advanced features from day 1
- Scalable

**Cons:**
- Additional infrastructure
- Cost in Year 1
- Overkill for < 10K users

**Decision:** Rejected. Premature.

### 2. No Search

**Description:** Use simple filter/search.

**Pros:**
- Simple
- No additional infrastructure

**Cons:**
- Poor search experience
- No relevance ranking
- No fuzzy matching

**Decision:** Rejected. Poor UX.

### 3. PostgreSQL with OpenSearch Abstraction (Selected)

**Description:** PostgreSQL full-text in Year 1; OpenSearch abstraction for Stage 3.

**Pros:**
- Zero cost in Year 1
- Good search experience
- Easy migration to OpenSearch
- Supports advanced features later

**Cons:**
- Limited features in Year 1
- Requires abstraction layer

**Decision:** Accepted. Best balance.

---

## Consequences

### Positive
- Zero additional infrastructure in Year 1
- Good search experience
- Easy migration to OpenSearch
- Supports advanced features later

### Negative
- Limited features in Year 1
- Requires abstraction layer

### Neutral
- PostgreSQL search is sufficient for < 10K users
- OpenSearch migration is a configuration change

---

## References

- [Production Architecture](docs/architecture/production-architecture.md)
- [Platform Adapters](docs/architecture/future/03_target_folder_structure.md)
