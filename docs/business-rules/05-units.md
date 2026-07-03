# Unit Rules

## Model

`properties.models.Unit` — rentable space within a building.

## Business rules

1. **Ownership:** `Unit.owner` must match authenticated user for all mutations.
2. **Building:** optional `ForeignKey` to `Building`; must belong to same owner when set.
3. **Uniqueness:** per owner, combination of `unit`, `building`, and `address_line` must be unique.
4. **Occupancy:** `status` (`vacant` / `occupied`) and `is_vacant` must stay in sync — updated by `update_unit_status()` when renters change.
5. **Geo:** latitude ∈ [-90, 90]; longitude ∈ [-180, 180].
6. **Types:** `flat`, `house`, `commercial_shop`, `villa`, `office`, `paying_guest`, `land`, etc.
7. **Create:** `max_units` limit via `FeatureEnforcer`; increment/decrement on create/delete.
8. **Reminders:** `rent_due_reminder` and related fields drive scheduled notifications.
9. **Past grace on expired plan:** list may slice to free-tier unit count.

## API

| Method | Path |
|--------|------|
| GET/POST | `/api/units/` |

## Side effects

- Creating/updating/deleting renters calls `update_unit_status(unit)` from `properties/services/unit_service.py`.

## Related files

- `properties/models/unit_models.py`
- `properties/views/unit_views.py`
- `properties/services/unit_service.py`

## See also

- [Renters](./07-renters.md)
- [Unit images & documents](./09-unit-images-and-documents.md)
