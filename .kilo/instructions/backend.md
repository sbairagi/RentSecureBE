# Backend Engineering Rules

## Architecture Rules
- Business logic must not remain inside views.
- Views should stay thin.
- Use service layer for workflows.
- External integrations must stay isolated.
- Avoid fat serializers.
- Never call third-party APIs directly from views.

## Performance Rules
- Use caching for analytics/dashboard APIs.
- Use Django Local Memory Cache for Year 1.
- Heavy PDF generation must be async (use management command or sync with timeout).
- Avoid synchronous external API calls.

## Background Jobs Rules (Year 1)
- Prefer Django management commands over Celery.
- Use systemd timers or crontab for scheduled tasks.
- Celery is Stage 2 upgrade.
- No message broker required in Year 1.

## Cache Rules
- Year 1: Django Local Memory Cache (LocMemCache).
- Redis is optional and becomes Stage 2.
- Document when Redis becomes necessary.

## Search Rules
- Year 1: PostgreSQL full-text search with trigram indexes.
- OpenSearch is Stage 3 upgrade.
- Do not introduce OpenSearch without clear trigger.

## Backend Rules
- Use DRF best practices.
- Use serializers for validation.
- Add permissions/authentication properly.
- Optimize database queries using select_related/prefetch_related.
- Add migrations carefully.
- Never delete data fields without warning.
