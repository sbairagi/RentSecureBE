from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from core.events.bus.handlers import ExecutionReport, HandlerResult
from core.events.inbox.cleanup import InboxCleanupService
from core.events.inbox.dispatcher import InboxDispatcher
from core.events.inbox.enums import InboxEventStatus
from core.events.inbox.models import InboxEvent
from core.events.inbox.repository import InboxEventRepository
from core.events.inbox.serializers import InboxEventSerializer
from core.events.inbox.service import InboxService
from core.shared.time import utc_now

pytestmark = pytest.mark.django_db


def _make_payload() -> dict[str, Any]:
    return {
        "type": "rent.paid",
        "amount": "1000.00",
        "rent_record_id": str(uuid.uuid4()),
    }


def _build_unsaved_event(**overrides: Any) -> InboxEvent:
    defaults: dict[str, Any] = {
        "event_id": overrides.pop("event_id", uuid.uuid4()),
        "aggregate_id": overrides.pop("aggregate_id", uuid.uuid4()),
        "aggregate_type": overrides.pop("aggregate_type", "RentRecord"),
        "event_type": overrides.pop("event_type", "rent.paid"),
        "payload": overrides.pop("payload", _make_payload()),
        "headers": overrides.pop("headers", {"source": "test"}),
        "status": overrides.pop("status", InboxEventStatus.RECEIVED),
        "retry_count": overrides.pop("retry_count", 0),
        "max_retry": overrides.pop("max_retry", 6),
        "next_retry_at": overrides.pop("next_retry_at", None),
        "processed_at": overrides.pop("processed_at", None),
        "last_error": overrides.pop("last_error", ""),
    }
    return InboxEvent(**{**defaults, **overrides})


def _build_event(**overrides: Any) -> InboxEvent:
    event = _build_unsaved_event(**overrides)
    event.save()
    return event


def _set_created_at(event: InboxEvent, dt: datetime) -> None:
    InboxEvent.objects.filter(pk=event.pk).update(created_at=dt)


class TestInboxEventSerializer:
    def test_to_dict_from_base_event(self) -> None:
        from shared.domain_events import BaseDomainEvent, EventMetadata

        event = BaseDomainEvent(
            event_id=str(uuid.uuid4()),
            metadata=EventMetadata(source="test"),
        )
        result = InboxEventSerializer.to_dict(event)
        assert result["event_id"] == event.event_id
        assert result["metadata"]["source"] == "test"

    def test_to_dict_from_plain_dict(self) -> None:
        raw = {"event_id": str(uuid.uuid4()), "data": "hello"}
        result = InboxEventSerializer.to_dict(raw)
        assert result == raw

    def test_from_dict_roundtrip(self) -> None:
        data = {"hello": "world"}
        assert InboxEventSerializer.from_dict(data) is data


class TestInboxEventRepository:
    def test_save_persists_event(self) -> None:
        event = _build_event()
        repo = InboxEventRepository()
        saved = repo.save(event)
        assert saved.id is not None
        assert saved.event_id == event.event_id

    def test_save_many_bulk_insert(self) -> None:
        repo = InboxEventRepository()
        events = [_build_unsaved_event() for _ in range(3)]
        count = repo.save_many(events)
        assert count == 3
        assert InboxEvent.objects.count() == 3

    def test_exists_true_for_existing(self) -> None:
        event = _build_event()
        repo = InboxEventRepository()
        assert repo.exists(event.event_id) is True

    def test_exists_false_for_missing(self) -> None:
        repo = InboxEventRepository()
        assert repo.exists(uuid.uuid4()) is False

    def test_get_by_event_id(self) -> None:
        event = _build_event()
        repo = InboxEventRepository()
        found = repo.get_by_event_id(event.event_id)
        assert found is not None
        assert found.id == event.id

    def test_get_by_event_id_returns_none_when_missing(self) -> None:
        repo = InboxEventRepository()
        assert repo.get_by_event_id(uuid.uuid4()) is None

    def test_pending_returns_received_events(self) -> None:
        _build_event(status=InboxEventStatus.RECEIVED)
        _build_event(status=InboxEventStatus.PROCESSED)
        repo = InboxEventRepository()
        events = list(repo.pending(10))
        assert len(events) == 1
        assert events[0].status == InboxEventStatus.RECEIVED

    def test_pending_returns_retryable_failed(self) -> None:
        past = utc_now() - timedelta(minutes=5)
        _build_event(
            status=InboxEventStatus.FAILED,
            next_retry_at=past,
        )
        _build_event(
            status=InboxEventStatus.FAILED,
            next_retry_at=utc_now() + timedelta(minutes=30),
        )
        repo = InboxEventRepository()
        events = list(repo.pending(10))
        assert len(events) == 1
        assert events[0].next_retry_at <= utc_now()

    def test_pending_excludes_failed_at_max_retry(self) -> None:
        past = utc_now() - timedelta(minutes=5)
        _build_event(
            status=InboxEventStatus.FAILED,
            retry_count=6,
            max_retry=6,
            next_retry_at=past,
        )
        repo = InboxEventRepository()
        events = list(repo.pending(10))
        assert len(events) == 0

    def test_pending_omits_dead_letter(self) -> None:
        _build_event(status=InboxEventStatus.DEAD_LETTER)
        _build_event(
            status=InboxEventStatus.FAILED,
            next_retry_at=utc_now() - timedelta(minutes=1),
        )
        repo = InboxEventRepository()
        events = list(repo.pending(10))
        assert len(events) == 1
        assert events[0].status == InboxEventStatus.FAILED

    def test_pending_respects_limit(self) -> None:
        for _ in range(5):
            _build_event(status=InboxEventStatus.RECEIVED)
        repo = InboxEventRepository()
        events = list(repo.pending(3))
        assert len(events) == 3

    def test_mark_processing(self) -> None:
        event = _build_event()
        repo = InboxEventRepository()
        rows = repo.mark_processing(event.id, now=utc_now())
        assert rows == 1
        event.refresh_from_db()
        assert event.status == InboxEventStatus.PROCESSING

    def test_mark_processed(self) -> None:
        event = _build_event()
        now = utc_now()
        repo = InboxEventRepository()
        repo.mark_processed(event.id, now=now)
        event.refresh_from_db()
        assert event.status == InboxEventStatus.PROCESSED
        assert event.processed_at == now

    def test_mark_failed(self) -> None:
        event = _build_event()
        now = utc_now()
        next_retry = now + timedelta(minutes=1)
        repo = InboxEventRepository()
        repo.mark_failed(
            event.id,
            retry_count=1,
            next_retry_at=next_retry,
            last_error="boom",
            now=now,
        )
        event.refresh_from_db()
        assert event.status == InboxEventStatus.FAILED
        assert event.retry_count == 1
        assert event.next_retry_at == next_retry
        assert event.last_error == "boom"

    def test_mark_dead_letter(self) -> None:
        event = _build_event()
        now = utc_now()
        repo = InboxEventRepository()
        repo.mark_dead_letter(event.id, now=now, last_error="oops")
        event.refresh_from_db()
        assert event.status == InboxEventStatus.DEAD_LETTER
        assert event.last_error == "oops"

    def test_cleanup_deletes_only_processed(self) -> None:
        old = _build_event(status=InboxEventStatus.PROCESSED)
        _set_created_at(old, utc_now() - timedelta(days=60))
        fresh = _build_event(status=InboxEventStatus.PROCESSED)
        _set_created_at(fresh, utc_now() - timedelta(days=1))
        _build_event(status=InboxEventStatus.FAILED)
        repo = InboxEventRepository()
        cutoff = utc_now() - timedelta(days=30)
        deleted = repo.cleanup(cutoff)
        assert deleted == 1
        assert InboxEvent.objects.filter(status=InboxEventStatus.FAILED).exists()

    def test_cleanup_respects_statuses_to_keep(self) -> None:
        failed = _build_event(status=InboxEventStatus.FAILED)
        _set_created_at(failed, utc_now() - timedelta(days=60))
        cutoff = utc_now() - timedelta(days=30)
        repo = InboxEventRepository()
        deleted = repo.cleanup(cutoff, statuses_to_keep=[InboxEventStatus.FAILED])
        assert deleted == 0

    def test_count(self) -> None:
        for _ in range(3):
            _build_event()
        repo = InboxEventRepository()
        assert repo.count() == 3

    def test_count_pending(self) -> None:
        for _ in range(3):
            _build_event(status=InboxEventStatus.RECEIVED)
        _build_event(status=InboxEventStatus.PROCESSED)
        repo = InboxEventRepository()
        assert repo.count_pending() == 3


class TestInboxService:
    def test_receive_event_creates_event(self) -> None:
        service = InboxService()
        event = service.receive_event(
            event_id=uuid.uuid4(),
            aggregate_id=uuid.uuid4(),
            aggregate_type="RentRecord",
            event_type="rent.paid",
            payload=_make_payload(),
        )
        assert event.id is not None
        assert event.status == InboxEventStatus.RECEIVED

    def test_receive_event_returns_existing_on_duplicate(self) -> None:
        service = InboxService()
        event_id = uuid.uuid4()
        first = service.receive_event(
            event_id=event_id,
            aggregate_id=uuid.uuid4(),
            aggregate_type="RentRecord",
            event_type="rent.paid",
            payload=_make_payload(),
        )
        second = service.receive_event(
            event_id=event_id,
            aggregate_id=uuid.uuid4(),
            aggregate_type="RentRecord",
            event_type="rent.paid",
            payload=_make_payload(),
        )
        assert second.id == first.id
        assert InboxEvent.objects.count() == 1

    def test_receive_many_idempotent(self) -> None:
        service = InboxService()
        event_id = uuid.uuid4()
        data = [
            {
                "event_id": event_id,
                "aggregate_id": uuid.uuid4(),
                "aggregate_type": "RentRecord",
                "event_type": "rent.paid",
                "payload": _make_payload(),
            },
            {
                "event_id": event_id,
                "aggregate_id": uuid.uuid4(),
                "aggregate_type": "RentRecord",
                "event_type": "rent.paid",
                "payload": _make_payload(),
            },
        ]
        received = service.receive_many(data)
        assert len(received) == 2
        assert received[0].id == received[1].id
        assert InboxEvent.objects.count() == 1

    def test_process_event_marks_processing(self) -> None:
        event = _build_event(status=InboxEventStatus.RECEIVED)
        service = InboxService()
        result = service.process_event(event.id)
        assert result is not None
        assert result.status == InboxEventStatus.PROCESSING

    def test_mark_processed(self) -> None:
        event = _build_event(status=InboxEventStatus.RECEIVED)
        service = InboxService()
        service.process_event(event.id)
        service.mark_processed(event.id)
        event.refresh_from_db()
        assert event.status == InboxEventStatus.PROCESSED

    def test_mark_failed(self) -> None:
        event = _build_event(status=InboxEventStatus.RECEIVED)
        service = InboxService()
        now = utc_now()
        service.mark_failed(
            event.id,
            retry_count=1,
            next_retry_at=now + timedelta(minutes=1),
            last_error="error",
            now=now,
        )
        event.refresh_from_db()
        assert event.status == InboxEventStatus.FAILED
        assert event.retry_count == 1
        assert event.last_error == "error"

    def test_mark_dead_letter(self) -> None:
        event = _build_event(status=InboxEventStatus.FAILED)
        service = InboxService()
        now = utc_now()
        service.mark_dead_letter(event.id, last_error="final error", now=now)
        event.refresh_from_db()
        assert event.status == InboxEventStatus.DEAD_LETTER
        assert event.last_error == "final error"

    def test_retry_resets_failed_to_received(self) -> None:
        event = _build_event(status=InboxEventStatus.FAILED)
        service = InboxService()
        count = service.retry()
        assert count == 1
        event.refresh_from_db()
        assert event.status == InboxEventStatus.RECEIVED

    def test_retry_ignores_dead_letter(self) -> None:
        _build_event(status=InboxEventStatus.DEAD_LETTER)
        service = InboxService()
        count = service.retry()
        assert count == 0

    def test_cleanup_old_removes_processed(self) -> None:
        old = _build_event(status=InboxEventStatus.PROCESSED)
        _set_created_at(old, utc_now() - timedelta(days=60))
        service = InboxService(retention_days=30)
        deleted = service.cleanup()
        assert deleted == 1

    def test_get_statistics_counts_by_status(self) -> None:
        _build_event(status=InboxEventStatus.RECEIVED)
        _build_event(status=InboxEventStatus.PROCESSED)
        service = InboxService()
        stats = service.statistics()
        assert stats[InboxEventStatus.RECEIVED] >= 1
        assert stats[InboxEventStatus.PROCESSED] >= 1

    def test_count(self) -> None:
        for _ in range(3):
            _build_event()
        service = InboxService()
        assert service.count() == 3


class TestInboxDispatcher:
    def test_dispatch_processes_received(self) -> None:
        event = _build_event(status=InboxEventStatus.RECEIVED)
        handler = MagicMock(return_value=None)
        dispatcher = InboxDispatcher(handler)
        processed = dispatcher.dispatch()
        assert processed == 1
        event.refresh_from_db()
        assert event.status == InboxEventStatus.PROCESSED

    def test_dispatch_moves_failed_to_dead_after_max_retry(self) -> None:
        event = _build_event(
            status=InboxEventStatus.FAILED,
            retry_count=5,
            max_retry=6,
            next_retry_at=utc_now() - timedelta(minutes=1),
        )
        handler = MagicMock(side_effect=RuntimeError("boom"))
        dispatcher = InboxDispatcher(handler)
        processed = dispatcher.dispatch()
        assert processed == 1
        event.refresh_from_db()
        assert event.status == InboxEventStatus.DEAD_LETTER

    def test_dispatch_respects_batch_size(self) -> None:
        for _ in range(5):
            _build_event(status=InboxEventStatus.RECEIVED)
        handler = MagicMock(return_value=None)
        dispatcher = InboxDispatcher(handler)
        processed = dispatcher.dispatch()
        assert processed == 5

    def test_dispatch_increments_retry_count_on_failure(self) -> None:
        event = _build_event(
            status=InboxEventStatus.FAILED,
            retry_count=1,
            max_retry=6,
            next_retry_at=utc_now() - timedelta(minutes=1),
        )
        handler = MagicMock(side_effect=RuntimeError("boom"))
        dispatcher = InboxDispatcher(handler)
        dispatcher.dispatch()
        event.refresh_from_db()
        assert event.retry_count == 2
        assert event.status == InboxEventStatus.FAILED

    def test_dispatch_marks_failed_when_report_all_succeeded_false(self) -> None:
        event = _build_event(status=InboxEventStatus.RECEIVED)
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
        handler = MagicMock(return_value=report)
        dispatcher = InboxDispatcher(handler)
        dispatcher.dispatch()
        event.refresh_from_db()
        assert event.status == InboxEventStatus.FAILED
        assert event.retry_count == 1

    def test_dispatch_marks_processed_when_report_all_succeeded_true(self) -> None:
        event = _build_event(status=InboxEventStatus.RECEIVED)
        report = ExecutionReport(
            event_type="rent.paid",
            event_id=str(event.event_id),
            successful_handlers=("handler_a",),
            failed_handlers=(),
            total_handlers=1,
        )
        handler = MagicMock(return_value=report)
        dispatcher = InboxDispatcher(handler)
        dispatcher.dispatch()
        event.refresh_from_db()
        assert event.status == InboxEventStatus.PROCESSED

    def test_dispatch_moves_to_dead_letter_after_max_retry_on_report_failure(
        self,
    ) -> None:
        event = _build_event(
            status=InboxEventStatus.FAILED,
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
        handler = MagicMock(return_value=report)
        dispatcher = InboxDispatcher(handler)
        dispatcher.dispatch()
        event.refresh_from_db()
        assert event.status == InboxEventStatus.DEAD_LETTER


class TestInboxCleanupService:
    def test_cleanup_removes_old_processed(self) -> None:
        old = _build_event(status=InboxEventStatus.PROCESSED)
        _set_created_at(old, utc_now() - timedelta(days=60))
        service = InboxCleanupService(retention_days=30)
        deleted = service.cleanup()
        assert deleted == 1

    def test_cleanup_preserves_non_processed(self) -> None:
        failed = _build_event(status=InboxEventStatus.FAILED)
        _set_created_at(failed, utc_now() - timedelta(days=60))
        service = InboxCleanupService(retention_days=30)
        deleted = service.cleanup()
        assert deleted == 0
