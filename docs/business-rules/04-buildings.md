# Building Rules

## Model

`properties.models.Building` — top of the property hierarchy.

## Business rules

1. Every building **must** have an `owner` (`User`).
2. **Uniqueness:** one owner cannot have two buildings with the same `name`, `address_line`, and `city`.
3. **`is_archived`:** soft-hide; non-archived buildings count toward limits and default listings.
4. **Create:** `FeatureEnforcer.can_create('max_buildings')` required; on success `increment('max_buildings')`.
5. **Update/delete:** only the owner; delete calls `decrement('max_buildings')`.
6. **Expired subscription (past grace):** list queryset may return only the first N active buildings per free limit.

## API

| Method | Path |
|--------|------|
| GET/POST | `/api/buildings/` |
| GET/PUT/PATCH/DELETE | `/api/buildings/{id}/` |

## Serializer / validation

- `BuildingSerializer` — address fields required per model.
- Owner set in `perform_create`, not from client payload.

## Related files

- `properties/models/building_models.py`
- `properties/views/building_views.py`
- `properties/serializers/building_serializers.py`

## See also

- [Units](./05-units.md)
- [Subscription limits](./02-subscription-and-usage-limits.md)
