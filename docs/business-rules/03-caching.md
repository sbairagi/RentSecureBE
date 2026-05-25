# Caching Rules

## Policy

- List querysets for a user are cached in Django’s cache backend (default: locmem, 5 minutes).
- Cache is **cleared** after create, update, or delete on that resource type.

## Cache keys

| Key pattern | Resource |
|-------------|----------|
| `buildings_user_{user.id}` | Buildings |
| `units_user_{user.id}` | Units |
| `caretakers_user_{user.id}` | Caretakers |
| `renters_user_{user.id}` | Renters |
| `rent_records_user_{user.id}` | Rent records |
| `unit_images_user_{user.id}` | Unit images |
| `unit_docs_user_{user.id}` | Unit documents |
| `rent_drafts_user_{user.id}` | Agreement drafts |

## Timeouts

Defined in `properties/constants.py`:

- `BUILDINGS_CACHE_TIMEOUT` — 300s
- `UNITS_CACHE_TIMEOUT` — 300s
- `RENTERS_CACHE_TIMEOUT` — 300s

## Rules

1. Do not rely on cache for write authorization — always check DB ownership.
2. Admin or shell changes may leave stale lists until TTL expires unless cache is cleared manually.
3. Expired-subscription **read slicing** happens after cache fetch in some ViewSets (buildings, units).

## Related files

- `properties/views/building_views.py`
- `properties/views/unit_views.py`
- `properties/views/renter_views.py`
- `properties/views/rent_record_views.py`
