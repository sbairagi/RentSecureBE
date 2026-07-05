# Backend Architecture Guidance

Use this guidance when architecting Django/DRF backend features.

## Principles
- Keep views thin.
- Keep serializers focused on validation and representation.
- Put business workflows in the service layer.
- Isolate external integrations behind service boundaries.
- Run long-running or external calls through Celery.
- Avoid adding duplicate logic across apps.

## Review Checklist
- Check existing models and serializers before adding new ones.
- Prefer extending existing services over creating new ones.
- Add migrations carefully and never delete data fields without a deprecation plan.
- Use `select_related` / `prefetch_related` on querysets that cross relations.
- Keep async behavior explicit.
