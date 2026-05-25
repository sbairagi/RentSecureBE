# Caretaker Rules

## Model

`properties.models.Caretaker` — person assigned to maintain/watch a unit.

## Business rules

1. **Belongs to** exactly one `Unit`.
2. **Access:** requester must own the unit (`unit.owner == request.user`).
3. **Phone:** validated with shared regex (`^\+?1?\d{9,15}$`).
4. **Dates:** `end_date` cannot be before `start_date`.
5. **Uniqueness:** one caretaker phone number per unit.
6. **Limits:** `max_caretakers` via `FeatureEnforcer` on create.
7. **Usage signals:** post_save/post_delete update `UsageLimit` for `max_caretakers` (when signals are wired).

## API

| Method | Path |
|--------|------|
| GET/POST | `/api/caretakers/` |

## Related files

- `properties/models/caretaker_models.py`
- `properties/views/caretaker_views.py`
- `properties/serializers/caretaker_serializers.py`
