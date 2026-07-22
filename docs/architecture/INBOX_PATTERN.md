# Inbox Pattern

## Overview

The Inbox Pattern provides idempotent consumption of external events. It prevents duplicate event processing when the same event arrives multiple times (e.g., 100 times).

**Table:** `inbox_event` in the `core` Django app.

**Ownership:** `core.events.inbox` module.

**Phase:** Phase 2.3 — Transactional Outbox Pattern follow-up.

## Architecture

```
External Source
      |
      v
  receive_event(event_id, ...)
      |
      v
  InboxEvent[RECEIVED]
      |
      v
  process_event(event_id) -> InboxEvent[PROCESSING]
      |
      v
  handler(payload)
      |
  [success] --> InboxEvent[PROCESSED]
  [failure] --> InboxEvent[FAILED]
              -> next_retry_at
              -> retry_count++
              -> if max_retry: DEAD_LETTER
```

## Modules

| Module | Path | Role |
|--------|------|------|
| Model | `core/events/inbox/models.py` | InboxEvent Django model |
| Enum | `core/events/inbox/enums.py` | InboxEventStatus statuses |
| Constants | `core/events/inbox/constants.py` | Batch sizes, retry limits, backoffs |
| Exceptions | `core/events/inbox/exceptions.py` | InboxError hierarchy |
| Repository | `core/events/inbox/repository.py` | Data access methods |
| Service | `core/events/inbox/service.py` | Business logic orchestration |
| Dispatcher | `core/events/inbox/dispatcher.py` | Event delivery loop |
| Serializer | `core/events/inbox/serializers.py` | Event serialization |
| Cleanup | `core/events/inbox/cleanup.py` | Old event removal |
| Admin | `core/events/inbox/admin.py` | Django admin read-only view |

## Idempotency

The core guarantee: the same `event_id` stored once, processed once, duplicates ignored.

```python
# First call: persists InboxEvent[RECEIVED]
inbox_service.receive_event(event_id=uuid4(), ...)

# Second call with same event_id: returns existing record
existing = inbox_service.receive_event(event_id=same_uuid, ...)
assert existing.id == first.id  # no duplicate row
```

Implementation detail in `InboxService.receive_event`:

```python
existing = self._repo.get_by_event_id(event_id)
if existing is not None:
    return existing
return self._repo.save(InboxEvent(...))
```

## Statuses

| Status | Meaning |
|--------|---------|
| RECEIVED | Event stored, awaiting processing |
| PROCESSING | Currently being handled by dispatcher |
| PROCESSED | Successfully handled |
| FAILED | Handler raised exception, retry scheduled |
| DEAD_LETTER | Max retries exceeded, requires manual intervention |

## Retry Policy

- On handler exception: increment `retry_count`, set `next_retry_at`
- Backoff: exponential, base 60s, multiplier 2x, cap 32 minutes
- When `retry_count >= max_retry`: move to DEAD_LETTER
- Manual retry: `InboxService.retry()` moves FAILED events back to RECEIVED

## Dead Letter

Events in DEAD_LETTER status are never reprocessed automatically.
They are preserved until cleanup retention expires.
Manual retry via `InboxService.retry()` is required.

## Cleanup

Only `PROCESSED` events older than `retention_days` (default: 30) are deleted.

Never deleted:
- RECEIVED
- PROCESSING
- FAILED
- DEAD_LETTER

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `INBOX_BATCH_SIZE` | 100 | Events per dispatch loop iteration |
| `INBOX_MAX_RETRY` | 6 | Maximum handler retry attempts |
| `INBOX_RETENTION_DAYS` | 30 | Days before PROCESSED events are cleaned up |
| `INBOX_PROCESS_INTERVAL` | 60 | Seconds between dispatch cycles (systemd/cron) |

Configuration helpers are defined in `core.config.settings`:
- `get_inbox_batch_size()`
- `get_inbox_max_retry()`
- `get_inbox_retention_days()`
- `get_inbox_process_interval()`

## Management Commands

```bash
# Process pending inbox events
python manage.py process_inbox_events

# Cleanup old processed events
python manage.py cleanup_inbox
```

## Dispatch Pattern

The dispatcher uses `select_for_update(skip_locked=True)` for safe concurrent processing.

```python
from core.events.inbox.dispatcher import InboxDispatcher

def my_handler(payload: dict[str, Any]) -> None:
    process(payload)

dispatcher = InboxDispatcher(handler=my_handler)
dispatcher.dispatch()
```

## Database Schema

**Table:** `inbox_event`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | Default `uuid.uuid4()` |
| event_id | UUID (UNIQUE) | External event identifier |
| event_type | varchar(255) | Indexed |
| aggregate_id | UUID | Indexed |
| aggregate_type | varchar(100) | Indexed |
| payload | JSON | Full event payload |
| headers | JSON | Optional metadata |
| status | varchar(20) | Indexed |
| received_at | datetime | Auto, Indexed |
| processed_at | datetime | Nullable |
| retry_count | int | Default 0 |
| max_retry | int | Default 6 |
| next_retry_at | datetime | Nullable, Indexed |
| last_error | text | Blank |
| created_at | datetime | Auto, Indexed |
| updated_at | datetime | Auto |

**Indexes:**
- `event_id` (unique)
- `status`
- `received_at`
- `event_type`
- `aggregate_id`
- Composite: `status + received_at`
- Composite: `event_type + aggregate_id`

## Admin

Read-only at `core.events.inbox.admin.InboxEventAdmin`:
- Search: `event_id`, `aggregate_id`, `event_type`
- Filters: `status`, `event_type`, `created_at`
- No add, change, delete permissions

## Testing

Tests are in `core/events/tests/test_inbox.py`.

Coverage target: >= 95%.

## Future Integrations

### Kafka Integration

```python
from core.events.inbox.dispatcher import InboxDispatcher

# Kafka consumer callback
def on_kafka_message(payload: dict[str, Any]) -> None:
    pass

dispatcher = InboxDispatcher(handler=on_kafka_message)
```

### SQS Integration

```
def on_sqs_message(payload: dict[str, Any]) -> None:
    pass

dispatcher = InboxDispatcher(handler=on_sqs_message)
```

### RabbitMQ Integration

```
def on_rabbitmq_message(payload: dict[str, Any]) -> None:
    pass

dispatcher = InboxDispatcher(handler=on_rabbitmq_message)
```

### Celery Integration

```python
from core.events.inbox.dispatcher import InboxDispatcher

@shared_task
def celery_handler(payload: dict[str, Any]) -> None:
    pass

dispatcher = InboxDispatcher(handler=celery_handler.delay)
dispatcher.dispatch()
```

## Backward Compatibility

- No existing code is modified.
- Outbox pattern is unchanged.
- New database table is additive.

## Production Readiness

- [x] Idempotent by design (unique `event_id`)
- [x] Atomic transactions (`select_for_update`)
- [x] Retry with exponential backoff
- [x] Dead letter queue for manual intervention
- [x] Cleanup job to prevent unbounded growth
- [x] Comprehensive logging
- [x] Read-only admin for audit
- [x] Management commands for ops
- [x] Python 3.12, Django 4.2+ compatible
- [x] SQLite + PostgreSQL compatible

## Known Limitations

1. **Year 1:** In-process dispatch only. No distributed consumer.
2. **Single handler:** `InboxDispatcher` accepts a single callable. For multi-handler scenarios, compose at the handler level.
3. **No native ordering:** `received_at` ordering ensures FIFO per aggregate.
4. **No payload versioning:** Relies on consumer-side compatibility.
