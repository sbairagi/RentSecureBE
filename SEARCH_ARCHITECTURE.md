# RentSecure Search Architecture

## 1. Overview

RentSecure provides two layers of search:

1. **Global Search** — cross-resource search across buildings, units, renters, caretakers, rent records, visitors, and agreements via `/api/search/`.
2. **Module-level Search** — per-endpoint search/filter/ordering on list views.

All authorization is enforced at the database level. Frontend-side filtering is never trusted for security.

---

## 2. Global Search API

### Endpoint

```
GET /api/search/
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | No | Search query. When empty, returns `available_resource_types` only. |
| `resource_type` | string | No | Comma-separated resource types to include. Default: all. |
| `page` | int | No | Page number (default: 1). |
| `page_size` | int | No | Results per page (default: 20, max: 50). |
| `ordering` | string | No | `newest`, `oldest`, or `relevance` (default). |
| `include_archived` | bool | No | Include archived items (default: false). |

### Searchable Resource Types

| Resource Type | Search Fields |
|---------------|---------------|
| `buildings` | `name`, `address_line`, `city`, `state`, `country`, `postal_code` |
| `units` | `unit`, `building_name`, `address_line`, `landmark`, `city`, `state` |
| `renters` | `name`, `email`, `phone`, `alternate_phone` |
| `caretakers` | `name`, `email`, `phone`, `alternate_phone`, `address` |
| `rent_records` | `renter__name`, `unit__unit`, `transaction_id`, `notes` |
| `visitors` | `visitor_name`, `phone_number`, `vehicle_number`, `purpose` |
| `agreements` | `renter__name`, `unit__unit`, `leegality_document_id` |

### Response Shape

```json
{
  "query": "sunshine",
  "total_results": 3,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "results": [
    {
      "resource_type": "buildings",
      "id": 1,
      "title": "Sunshine Complex",
      "subtitle": "123 Main St, Mumbai",
      "status": "Active",
      "metadata": { /* serialized model data */ },
      "last_updated": "2024-01-01T00:00:00Z",
      "navigation_target": "buildings-detail"
    }
  ],
  "available_resource_types": ["buildings", "units", "renters"]
}
```

### Authorization

All results are scoped to `request.user`. Cross-owner results are never returned.

### Suggestions Endpoint

```
GET /api/search/suggestions/?q=Sun&limit=10
```

Returns matching building names, unit identifiers, renter names, and visitor names.
Minimum query length: 2 characters.

---

## 3. Module-level Search API Mapping

### Buildings

```
GET /api/buildings/
```

| Parameter | Description |
|-----------|-------------|
| `search` | icontains across `name`, `address_line`, `city`, `state`, `country`, `postal_code` |
| `city` | icontains on `city` |
| `state` | icontains on `state` |
| `country` | icontains on `country` |
| `is_archived` | `true` or `false` |
| `ordering` | `name`, `-name`, `created_at`, `-created_at` |

**Cache behavior:** Unfiltered requests use a 5-minute per-user cache. Requests with any filter parameter bypass cache.

### Units

```
GET /api/units/
```

| Parameter | Description |
|-----------|-------------|
| `search` | icontains across `unit`, `building_name`, `address_line`, `landmark`, `city`, `state` |
| `building` | exact match on `building_id` |
| `city` | icontains on `city` |
| `status` | exact match on `status` (`VACANT`/`OCCUPIED`) |
| `unit_type` | exact match on `unit_type` |
| `is_archived` | `true` or `false` |
| `ordering` | `unit`, `-unit`, `created_at`, `-created_at` |

**Cache behavior:** Unfiltered requests use a 5-minute per-user cache. Requests with any filter parameter bypass cache.

### Renters

```
GET /api/renters/
```

| Parameter | Description |
|-----------|-------------|
| `search` | icontains across `name`, `phone`, `email` |
| `status` | exact match on `status` |
| `building` | filter by `unit__building_id` |
| `unit` | filter by `unit_id` |
| `ordering` | `name`, `rent_amount`, `start_date`, `status`, `-start_date`, `-created_at` |

**Cache behavior:** Unfiltered requests use a 5-minute per-user cache. Requests with any filter parameter bypass cache.

### Caretakers

```
GET /api/caretakers/
```

| Parameter | Description |
|-----------|-------------|
| `search` | icontains across `name`, `phone`, `email` |
| `unit` | exact match on `unit_id` |
| `is_active` | `true` or `false` |
| `ordering` | `joining_date`, `-joining_date`, `name`, `-name` |

**Pagination:** Page size 20, max 100 (`?limit=`).

### Rent Records

```
GET /api/rent-records/
```

| Parameter | Description |
|-----------|-------------|
| `search` | icontains across `renter__name`, `unit__unit`, `transaction_id`, `notes` |
| `status` | exact match on `status` (`PENDING`/`PAID`/`OVERDUE`/`CANCELLED`) |
| `unit` | exact match on `unit_id` |
| `ordering` | `due_date`, `-due_date`, `amount`, `-amount`, `created_at`, `-created_at` |

**Cache behavior:** Unfiltered requests use a 5-minute per-user cache. Requests with any filter parameter bypass cache.

---

## 4. Frontend Search Architecture

### Global Search Screen

- **Route:** `/(drawer)/(tabs)/search`
- **Components:** `SearchBar`, `FilterPanel`, `SearchResults`, `SearchResultItem`, `SearchSuggestions`, `SearchHistory`, `EmptyState`, `NoResultsState`, `ErrorState`
- **Hook:** `useSearch(query, filters)` — debounced at 400ms
- **Suggestions:** `useSearchSuggestions(query)` — debounced at 300ms, min 2 chars

### Module-level List Screens

| Screen | Search | Filter | Sort |
|--------|--------|--------|------|
| `BuildingListScreen` | Yes | `BuildingFilterSheet` | `BuildingSortSheet` |
| `UnitListScreen` | `UnitSearchBar` | `UnitFilterSheet` | `UnitSortSheet` |
| `RenterListScreen` | `RenterSearchBar` | `RenterFilterChips` | Not implemented |
| `CaretakerListScreen` | `CaretakerSearchBar` | `CaretakerFilterSheet` | `CaretakerSortSheet` |

All module-level list screens now pass search/filter/sort parameters to the backend API instead of performing client-side filtering.

### Debouncing

- Global search: 400ms
- Suggestions: 300ms
- Module-level search: 300ms (UnitListScreen)

### React Query Keys

Query keys include all parameters that affect the result:

```ts
['search', 'global', debouncedQuery, {
  resource_type: debouncedResourceType,
  ordering: filters.ordering,
  page: filters.page,
  page_size: filters.page_size,
}]
```

Module-level keys follow the same pattern per feature.

### Cache Policy

- Global search: `staleTime: 2min`, `gcTime: 5min`
- Module-level lists: `staleTime: 5min`, `gcTime: 10min`
- Search cancellation: React Query cancels pending queries when query key changes

---

## 5. Authorization Rules

| Role | Global Search | Building Search | Unit Search | Renter Search | Caretaker Search | Rent Search |
|------|---------------|-----------------|-------------|---------------|------------------|-------------|
| `property_owner` | Own resources only | Own buildings | Own units | Own renters (via unit) | Own caretakers (via unit) | Own rent records (via unit) |
| `renter` | Own profile/rent only | Not applicable | Not applicable | Not applicable | Not applicable | Own rent records only |
| `caretaker` | Assigned buildings/units | Assigned buildings | Assigned units | Assigned units' renters | Own record | Assigned units' rent records |
| `admin` | All resources | All buildings | All units | All renters | All caretakers | All rent records |

Cross-owner isolation is enforced in `get_queryset()` on every ViewSet.

---

## 6. Database Index Recommendations

Currently indexed fields:

| Model | Indexed Fields |
|-------|---------------|
| `Building` | `city`, `created_at`, `owner` |
| `Unit` | `city`, `created_at`, `owner` |
| `Renter` | `start_date`, `unit`, `phone` |
| `RentRecord` | `due_date`, `unit`, `renter` |
| `CareTaker` | `joining_date`, `unit`, `phone` |

For PostgreSQL production, consider adding GIN indexes on frequently searched text fields if `pg_trgm` is available:

```sql
CREATE INDEX buildings_name_trgm ON properties_building USING GIN (name gin_trgm_ops);
CREATE INDEX units_unit_trgm ON properties_unit USING GIN (unit gin_trgm_ops);
CREATE INDEX renters_name_trgm ON properties_renter USING GIN (name gin_trgm_ops);
```

Do not add indexes blindly. Monitor slow queries before adding.

---

## 7. Security & Privacy

- No passwords, tokens, bank details, or identity documents are exposed in search results.
- `RenterSerializer` is used in global search; sensitive fields (`id_proof`, `rent_agreement`) are included as file URLs only.
- Agreement search results use a custom serializer that excludes sensitive fields.
- Search history is stored locally (MMKV) and sanitized before storage.

---

## 8. Testing Strategy

### Backend Tests

- `search/tests/test_search_api.py` — global search endpoint
- `properties/tests/test_renter_views.py` — renter search/filter/ordering
- `properties/tests/test_building_views.py` — building search/filter/ordering
- `properties/tests/test_unit_views.py` — unit search/filter/ordering
- `properties/tests/test_rent_record_views.py` — rent record search/filter/ordering
- `properties/tests/test_caretaker_views.py` — caretaker search/filter/ordering

### Frontend Tests

- `features/search/tests/searchApi.test.ts` — API service
- `features/search/tests/useSearch.test.ts` — search hook
- `features/search/tests/useSearch.test.ts` — suggestions hook
- `features/search/tests/debounce.test.ts` — debounce hook
- `features/search/tests/searchHistory.test.ts` — history store
- `features/search/tests/search.utils.test.ts` — utilities

### Test Coverage Goals

- Search functionality: all searchable fields
- Filter combinations: single and multiple filters
- Ordering: ascending and descending
- Authorization: cross-owner isolation, role-based access
- Edge cases: empty query, no results, special characters
- Pagination: page boundaries

---

## 9. Backend Changes Required

### Modified Files

| File | Change |
|------|--------|
| `properties/views/renter_views.py` | Added manual search/filter/ordering in `get_queryset()` |
| `properties/views/building_views.py` | Added manual search/filter/ordering; dynamic cache bypass |
| `properties/views/unit_views.py` | Added manual search/filter/ordering; dynamic cache bypass |
| `properties/views/rent_record_views.py` | Added manual search/filter/ordering; dynamic cache bypass |
| `search/views.py` | No changes (global search already existed) |

### No New Dependencies

All search/filter/ordering uses Django's built-in `Q` objects and `icontains`. No `django-filter` or additional packages required.

---

## 10. Known Limitations

1. **Date filtering** — Module-level date filtering is not implemented. Backend views do not accept date range parameters.
2. **Maintenance search** — There is no `Maintenance` model in the backend. Maintenance is represented as `ExtraCharge.name` strings.
3. **Full-text search** — Uses `icontains` which does not leverage PostgreSQL full-text search. Consider `SearchVector`/`SearchQuery` for production scaling.
4. **Client-side filter state** — Some list screens maintain local filter state that is not persisted in URL query parameters.
