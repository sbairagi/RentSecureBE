# Ownership & Access Rules

## Rules

1. All property entities belong to a `User` owner (`Building.owner`, `Unit.owner`, or via `unit.owner` for child records).
2. Owners may only **create, read, update, delete** records they own.
3. Child objects (renter, caretaker, rent record, images) validate ownership through the linked **unit** or **building**.
4. Ownership mismatch → `PermissionDenied` (403) or `ValidationError` (400) from serializers.

## Enforcement locations

| Layer | Mechanism |
|-------|-----------|
| ViewSets | `get_queryset()` filtered by `request.user` |
| `perform_create` / `perform_update` / `perform_destroy` | Compare `instance.owner` or `unit.owner` to `request.user` |
| Serializers | `validate()` checks `unit.owner == user`, `renter.unit == unit` |

## Authentication

- All property ViewSets use `permission_classes = [IsAuthenticated]`.
- JWT via `rest_framework_simplejwt` (see [Authentication](./15-authentication.md)).

## Renter access

- Renters use the same `User` model with a linked `Renter` profile (`renter_profile`).
- Renter endpoints resolve the tenant from `request.user`, not from owner-scoped querysets.

## Related files

- `properties/views/building_views.py`
- `properties/views/unit_views.py`
- `properties/views/renter_views.py`
- `properties/serializers/*`

## See also

- [Renter-facing APIs](./13-renter-facing-apis.md)
- [Owner reporting](./12-owner-reporting.md)
