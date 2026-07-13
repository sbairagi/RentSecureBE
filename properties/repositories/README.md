# Properties Repositories

This directory contains the repository layer for the Properties bounded context.

## Purpose

Repositories centralize ORM access and provide reusable queryset methods.
They hide Django ORM details from higher layers (services, views, serializers).

## Constraints

- No business logic
- No validation
- No permissions
- No HTTP concerns
- No serializer concerns
- Only ORM operations

## Dependency Direction

```
Views / Serializers / Services
        ↓
Repositories
        ↓
Django ORM / Models
```

## Future Migration

Future phases will migrate existing model queries from views and services
into these repositories, then update callers to use repository methods.
