# ADR-014: Background Jobs Strategy

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** RentSecure Engineering

---

## Context

RentSecure needs background job processing for:
- Daily rent reminders
- Late fee calculation
- Weekly reports
- Subscription expiry checks
- Notification retries

Year 1 constraints:
- Single EC2 instance (no distributed workers)
- Zero additional infrastructure cost
- Simple debugging and monitoring

---

## Decision

RentSecure uses **Django management commands + cron/systemd timers** in Year 1. Celery + Redis is introduced in Stage 2.

**Year 1 Architecture:**
- Scheduled jobs: systemd timers or crontab
- Job implementation: Django management commands
- Job registration: `apps/<context>/management/commands/`
- Execution: `python manage.py <command>`
- No message broker

**Stage 2+ Architecture:**
- Celery + Redis for distributed workers
- Celery Beat replaces systemd timers
- Priority queues for critical jobs
- Retry with exponential backoff

---

## Alternatives Considered

### 1. Celery + Redis from Day 1

**Description:** Use Celery for all background jobs.

**Pros:**
- Production-ready from day 1
- Easy to scale later

**Cons:**
- Additional infrastructure (Redis)
- Additional operational complexity
- Cost in Year 1 (minimal but non-zero)
- Overkill for < 10K users

**Decision:** Rejected. Premature for Year 1.

### 2. Django Q / Huey

**Description:** Use lighter alternatives to Celery.

**Pros:**
- Simpler than Celery
- Django-integrated

**Cons:**
- Less mature than Celery
- Smaller community
- Still requires database or Redis backend

**Decision:** Rejected. Celery is the standard; use when needed.

### 3. Management Commands + Cron (Selected)

**Description:** Django management commands triggered by systemd timers or crontab.

**Pros:**
- Zero additional infrastructure
- Simple to debug
- Django-native
- Easy to monitor
- Sufficient for < 10K users

**Cons:**
- No distributed processing
- No built-in retry (handled in code)
- No task prioritization

**Decision:** Accepted. Best for Year 1 constraints.

---

## Job Registration

```python
# apps/rent/management/commands/send_rent_reminders.py
from django.core.management.base import BaseCommand
from apps.rent.application.services import RentService

class Command(BaseCommand):
    help = "Send daily rent reminders to tenants"

    def handle(self, *args, **options):
        service = RentService(...)
        service.send_rent_reminders()
        self.stdout.write("Sent rent reminders")
```

```cron
# /etc/cron.d/rentsecure
0 9 * * * ubuntu /home/ubuntu/rentsecure/venv/bin/python manage.py send_rent_reminders >> /var/log/rentsecure/cron.log 2>&1
```

---

## Job Design Rules

1. **Idempotent:** Jobs can be safely re-run without duplicate side effects
2. **Small batches:** Process records in batches (100–1000 per run)
3. **Progress logging:** Log progress for monitoring
4. **Error handling:** Log errors, continue processing, alert on failure
5. **No user-facing timeouts:** Jobs run independently of HTTP requests

---

## Migration to Celery (Stage 2)

```python
# apps/rent/tasks/send_rent_reminders.py (Stage 2)
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def send_rent_reminders_task(self):
    try:
        service = RentService(...)
        service.send_rent_reminders()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

---

## Consequences

### Positive
- Zero additional infrastructure in Year 1
- Simple to debug and monitor
- Django-native pattern
- Easy migration to Celery later

### Negative
- No distributed processing in Year 1
- No built-in retry (must implement in code)
- No task prioritization

### Neutral
- Migration to Celery is straightforward (wrap management commands as tasks)
- Jobs are idempotent by design

---

## References

- [Production Architecture](../production-architecture.md)
- [Architecture Principles](../../../architecture/ARCHITECTURE_PRINCIPLES.md)
