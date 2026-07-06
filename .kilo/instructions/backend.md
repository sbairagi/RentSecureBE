# Backend Engineering Rules

## Architecture Rules
- Business logic must not remain inside views.
- Views should stay thin.
- Use service layer for workflows.
- External integrations must stay isolated.
- Long-running tasks must use Celery.
- Avoid fat serializers.
- Never call third-party APIs directly from views.

## Performance Rules
- Use caching for analytics/dashboard APIs.
- Use Redis for rate limiting and queues.
- Heavy PDF generation must be async.
- Avoid synchronous external API calls.

## Backend Rules
- Use DRF best practices.
- Use serializers for validation.
- Add permissions/authentication properly.
- Optimize database queries using select_related/prefetch_related.
- Add migrations carefully.
- Never delete data fields without warning.
