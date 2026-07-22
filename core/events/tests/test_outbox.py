from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from core.events.bus.handlers import ExecutionReport, HandlerResult
from core.events.outbox.cleanup import OutboxCleanupService
from core.events.outbox.dispatcher import OutboxDispatcher
from core.events.outbox.enums import OutboxEventStatus
from core.events.outbox.exceptions import OutboxDuplicateEventError
from core.events.outbox.models import OutboxEvent
from core.events.outbox.repository import OutboxEventRepository
from core.events.outbox.serializers import EventSerializer
from core.events.outbox.service import OutboxService
from core.shared.time import utc_now

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_payload() -> dict[str, Any]:
    return {
        "type": "rent.paid",
        "amount": "1000.00",
        "rent_record_id": str(uuid.uuid4()),
    }


def _build_unsaved_event(**overrides: Any) -> OutboxEvent:
    defaults: dict[str, Any] = {
        "event_id": overrides.pop("event_id", uuid.uuid4()),
        "aggregate_id": overrides.pop("aggregate_id", uuid.uuid4()),
        "aggregate_type": overrides.pop("aggregate_type", "RentRecord"),
        "event_type": overrides.pop("event_type", "rent.paid"),
        "event_version": overrides.pop("event_version", "1.0"),
        "payload": overrides.pop("payload", _make_payload()),
        "headers": overrides.pop("headers", {"source": "test"}),
        "status": overrides.pop("status", OutboxEventStatus.PENDING),
        "retry_count": overrides.pop("retry_count", 0),
        "max_retry": overrides.pop("max_retry", 6),
        "next_retry_at": overrides.pop("next_retry_at", None),
        "published_at": overrides.pop("published_at", None),
    }
    return OutboxEvent(**{**defaults, **overrides})


def _build_event(**overrides: Any) -> OutboxEvent:
    event = _build_unsaved_event(**overrides)
    event.save()
    return event


def _set_created_at(event: OutboxEvent, dt: datetime) -> None:
    OutboxEvent.objects.filter(pk=event.pk).update(created_at=dt)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------
class TestEventSerializer:
    def test_to_dict_from_base_event(self):
        from shared.domain_events import BaseDomainEvent, EventMetadata

        event = BaseDomainEvent(
            event_id=str(uuid.uuid4()),
            metadata=EventMetadata(source="test"),
        )
        result = EventSerializer.to_dict(event)
        assert result["event_id"] == event.event_id
        assert result["metadata"]["source"] == "test"

    def test_to_dict_from_plain_dict(self):
        raw = {"event_id": str(uuid.uuid4()), "data": "hello"}
        result = EventSerializer.to_dict(raw)
        assert result == raw

    def test_from_dict_roundtrip(self):
        data = {"hello": "world"}
        assert EventSerializer.from_dict(data) is data


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------
class TestOutboxEventRepository:
    def test_save_persists_event(self):
        event = _build_event()
        repo = OutboxEventRepository()
        saved = repo.save(event)
        assert saved.id is not None
        assert saved.event_id == event.event_id

    def test_save_many_bulk_insert(self):
        repo = OutboxEventRepository()
        events = [_build_unsaved_event() for _ in range(3)]
        count = repo.save_many(events)
        assert count == 3
        assert OutboxEvent.objects.count() == 3

    def test_get_pending_returns_pending_events(self):
        _build_event(status=OutboxEventStatus.PENDING)
        _build_event(status=OutboxEventStatus.PUBLISHED)
        repo = OutboxEventRepository()
        events = list(repo.get_pending(10))
        assert len(events) == 1
        assert events[0].status == OutboxEventStatus.PENDING

    def test_get_pending_returns_retryable_failed(self):
        past = utc_now() - timedelta(minutes=5)
        _build_event(
            status=OutboxEventStatus.FAILED,
            next_retry_at=past,
        )
        _build_event(
            status=OutboxEventStatus.FAILED,
            next_retry_at=utc_now() + timedelta(minutes=30),
        )
        repo = OutboxEventRepository()
        events = list(repo.get_pending(10))
        assert len(events) == 1
        assert events[0].next_retry_at <= utc_now()

    def test_get_pending_excludes_failed_at_max_retry(self):
        past = utc_now() - timedelta(minutes=5)
        _build_event(
            status=OutboxEventStatus.FAILED,
            retry_count=6,
            max_retry=6,
            next_retry_at=past,
        )
        repo = OutboxEventRepository()
        events = list(repo.get_pending(10))
        assert len(events) == 0

    def test_get_pending_omits_dead_letter(self):
        _build_event(status=OutboxEventStatus.DEAD_LETTER)
        _build_event(
            status=OutboxEventStatus.FAILED,
            next_retry_at=utc_now() - timedelta(minutes=1),
        )
        repo = OutboxEventRepository()
        events = list(repo.get_pending(10))
        assert len(events) == 1
        assert events[0].status == OutboxEventStatus.FAILED

    def test_get_pending_respects_limit(self):
        for _ in range(5):
            _build_event(status=OutboxEventStatus.PENDING)
        repo = OutboxEventRepository()
        events = list(repo.get_pending(3))
        assert len(events) == 3

    def test_mark_processing(self):
        event = _build_event()
        repo = OutboxEventRepository()
        rows = repo.mark_processing(event.id, now=utc_now())
        assert rows == 1
        event.refresh_from_db()
        assert event.status == OutboxEventStatus.PROCESSING

    def test_mark_published(self):
        event = _build_event()
        now = utc_now()
        repo = OutboxEventRepository()
        repo.mark_published(event.id, now=now)
        event.refresh_from_db()
        assert event.status == OutboxEventStatus.PUBLISHED
        assert event.published_at == now

    def test_mark_failed(self):
        event = _build_event()
        now = utc_now()
        next_retry = now + timedelta(minutes=1)
        repo = OutboxEventRepository()
        repo.mark_failed(
            event.id,
            retry_count=1,
            next_retry_at=next_retry,
            now=now,
        )
        event.refresh_from_db()
        assert event.status == OutboxEventStatus.FAILED
        assert event.retry_count == 1
        assert event.next_retry_at == next_retry

    def test_mark_dead(self):
        event = _build_event()
        now = utc_now()
        repo = OutboxEventRepository()
        repo.mark_dead(event.id, now=now)
        event.refresh_from_db()
        assert event.status == OutboxEventStatus.DEAD_LETTER

    def test_cleanup_deletes_only_published(self):
        old = _build_event(status=OutboxEventStatus.PUBLISHED)
        _set_created_at(old, utc_now() - timedelta(days=60))
        fresh = _build_event(status=OutboxEventStatus.PUBLISHED)
        _set_created_at(fresh, utc_now() - timedelta(days=1))
        _build_event(status=OutboxEventStatus.FAILED)
        repo = OutboxEventRepository()
        cutoff = utc_now() - timedelta(days=30)
        deleted = repo.cleanup(cutoff)
        assert deleted == 1
        assert OutboxEvent.objects.filter(status=OutboxEventStatus.FAILED).exists()

    def test_cleanup_respects_statuses_to_keep(self):
        failed = _build_event(status=OutboxEventStatus.FAILED)
        _set_created_at(failed, utc_now() - timedelta(days=60))
        cutoff = utc_now() - timedelta(days=30)
        repo = OutboxEventRepository()
        deleted = repo.cleanup(cutoff, statuses_to_keep=[OutboxEventStatus.FAILED])
        assert deleted == 0

    def test_count_pending(self):
        for _ in range(3):
            _build_event(status=OutboxEventStatus.PENDING)
        _build_event(status=OutboxEventStatus.PUBLISHED)
        repo = OutboxEventRepository()
        assert repo.count_pending() == 3


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class TestOutboxService:
    def test_store_event_creates_event(self):
        service = OutboxService()
        event = service.store_event(
            event_id=uuid.uuid4(),
            aggregate_id=uuid.uuid4(),
            aggregate_type="RentRecord",
            event_type="rent.paid",
            payload=_make_payload(),
        )
        assert event.id is not None
        assert event.status == OutboxEventStatus.PENDING

    def test_store_event_rejects_duplicate_event_id(self):
        service = OutboxService()
        event_id = uuid.uuid4()
        service.store_event(
            event_id=event_id,
            aggregate_id=uuid.uuid4(),
            aggregate_type="RentRecord",
            event_type="rent.paid",
            payload=_make_payload(),
        )
        with pytest.raises(OutboxDuplicateEventError):
            service.store_event(
                event_id=event_id,
                aggregate_id=uuid.uuid4(),
                aggregate_type="RentRecord",
                event_type="rent.paid",
                payload=_make_payload(),
            )

    def test_store_events_bulk_creates(self):
        service = OutboxService()
        data = [
            {
                "event_id": uuid.uuid4(),
                "aggregate_id": uuid.uuid4(),
                "aggregate_type": "RentRecord",
                "event_type": "rent.paid",
                "payload": _make_payload(),
            }
            for _ in range(3)
        ]
        count = service.store_events(data)
        assert count == 3

    def test_retry_failed_resets_failed(self):
        failed = _build_event(status=OutboxEventStatus.FAILED)
        service = OutboxService()
        count = service.retry_failed()
        failed.refresh_from_db()
        assert count == 1
        assert failed.status == OutboxEventStatus.PENDING

    def test_retry_failed_ignores_dead_letter(self):
        _build_event(status=OutboxEventStatus.DEAD_LETTER)
        service = OutboxService()
        count = service.retry_failed()
        assert count == 0

    def test_cleanup_old_removes_published(self):
        old = _build_event(status=OutboxEventStatus.PUBLISHED)
        _set_created_at(old, utc_now() - timedelta(days=60))
        service = OutboxService(retention_days=30)
        deleted = service.cleanup_old()
        assert deleted == 1

    def test_get_statistics_counts_by_status(self):
        _build_event(status=OutboxEventStatus.PENDING)
        _build_event(status=OutboxEventStatus.FAILED)
        service = OutboxService()
        stats = service.get_statistics()
        assert stats[OutboxEventStatus.PENDING] >= 1
        assert stats[OutboxEventStatus.FAILED] >= 1


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
class TestOutboxDispatcher:
    def test_dispatch_publishes_pending(self):
        event = _build_event(status=OutboxEventStatus.PENDING)
        publisher = MagicMock(return_value=None)
        dispatcher = OutboxDispatcher(publisher)
        dispatched = dispatcher.dispatch()
        assert dispatched == 1
        event.refresh_from_db()
        assert event.status == OutboxEventStatus.PUBLISHED

    def test_dispatch_moves_failed_to_dead_after_max_retry(self):
        event = _build_event(
            status=OutboxEventStatus.FAILED,
            retry_count=5,
            max_retry=6,
            next_retry_at=utc_now() - timedelta(minutes=1),
        )
        publisher = MagicMock(side_effect=RuntimeError("boom"))
        dispatcher = OutboxDispatcher(publisher)
        dispatched = dispatcher.dispatch()
        assert dispatched == 1
        event.refresh_from_db()
        assert event.status == OutboxEventStatus.DEAD_LETTER

    def test_dispatch_respects_batch_size(self):
        for _ in range(5):
            _build_event(status=OutboxEventStatus.PENDING)
        publisher = MagicMock(return_value=None)
        dispatcher = OutboxDispatcher(publisher)
        dispatched = dispatcher.dispatch()
        assert dispatched == 5

    def test_dispatch_increments_retry_count_on_failure(self):
        event = _build_event(
            status=OutboxEventStatus.FAILED,
            retry_count=1,
            max_retry=6,
            next_retry_at=utc_now() - timedelta(minutes=1),
        )
        publisher = MagicMock(side_effect=RuntimeError("boom"))
        dispatcher = OutboxDispatcher(publisher)
        dispatcher.dispatch()
        event.refresh_from_db()
        assert event.retry_count == 2
        assert event.status == OutboxEventStatus.FAILED

    def test_dispatch_marks_failed_when_report_all_succeeded_false(self):
        event = _build_event(status=OutboxEventStatus.PENDING)
        failed_result = HandlerResult.failure_result(
            "handler_a", 0.1, RuntimeError("handler failed")
        )
        report = ExecutionReport(
            event_type="rent.paid",
            event_id=str(event.event_id),
            successful_handlers=(),
            failed_handlers=(failed_result,),
            total_handlers=1,
        )
        publisher = MagicMock(return_value=report)
        dispatcher = OutboxDispatcher(publisher)
        dispatcher.dispatch()
        event.refresh_from_db()
        assert event.status == OutboxEventStatus.FAILED
        assert event.retry_count == 1

    def test_dispatch_marks_published_when_report_all_succeeded_true(self):
        event = _build_event(status=OutboxEventStatus.PENDING)
        report = ExecutionReport(
            event_type="rent.paid",
            event_id=str(event.event_id),
            successful_handlers=("handler_a",),
            failed_handlers=(),
            total_handlers=1,
        )
        publisher = MagicMock(return_value=report)
        dispatcher = OutboxDispatcher(publisher)
        dispatcher.dispatch()
        event.refresh_from_db()
        assert event.status == OutboxEventStatus.PUBLISHED

    def test_dispatch_moves_to_dead_letter_after_max_retry_on_report_failure(self):
        event = _build_event(
            status=OutboxEventStatus.FAILED,
            retry_count=5,
            max_retry=6,
            next_retry_at=utc_now() - timedelta(minutes=1),
        )
        failed_result = HandlerResult.failure_result(
            "handler_a", 0.1, RuntimeError("handler failed")
        )
        report = ExecutionReport(
            event_type="rent.paid",
            event_id=str(event.event_id),
            successful_handlers=(),
            failed_handlers=(failed_result,),
            total_handlers=1,
        )
        publisher = MagicMock(return_value=report)
        dispatcher = OutboxDispatcher(publisher)
        dispatcher.dispatch()
        event.refresh_from_db()
        assert event.status == OutboxEventStatus.DEAD_LETTER


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
class TestOutboxCleanupService:
    def test_cleanup_removes_old_published(self):
        old = _build_event(status=OutboxEventStatus.PUBLISHED)
        _set_created_at(old, utc_now() - timedelta(days=60))
        service = OutboxCleanupService(retention_days=30)
        deleted = service.cleanup()
        assert deleted == 1

    def test_cleanup_preserves_non_published(self):
        failed = _build_event(status=OutboxEventStatus.FAILED)
        _set_created_at(failed, utc_now() - timedelta(days=60))
        service = OutboxCleanupService(retention_days=30)
        deleted = service.cleanup()
        assert deleted == 0
