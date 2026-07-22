from __future__ import annotations

import uuid
from typing import Any

import pytest

from django.db import transaction

from core.events.bus.decorators import event_handler, get_registry
from core.events.bus.dispatcher import EventBus
from core.events.bus.middleware import MetricsMiddleware
from core.events.bus.registry import EventHandlerRegistry
from core.events.domain.publisher import DomainEventPublisher
from core.events.domain.user_events import UserCreated
from core.events.inbox.dispatcher import InboxDispatcher
from core.events.inbox.enums import InboxEventStatus
from core.events.inbox.models import InboxEvent
from core.events.outbox.dispatcher import OutboxDispatcher
from core.events.outbox.enums import OutboxEventStatus
from core.events.outbox.models import OutboxEvent
from core.shared.time import utc_now
from shared.domain_events import BaseDomainEvent


class FakeEvent(BaseDomainEvent):
    event_type: str = "FakeEvent"


def _clear_registry() -> None:
    get_registry().clear()


def _reset_publisher_singleton() -> None:
    DomainEventPublisher._instance = None


@pytest.fixture(autouse=True)
def _reset_event_state() -> Any:
    _clear_registry()
    _reset_publisher_singleton()
    yield


# ---------------------------------------------------------------------------
# DomainEventPublisher → Outbox only (no direct EventBus dispatch)
# ---------------------------------------------------------------------------
class TestDomainEventPublisherIntegration:
    @pytest.mark.django_db(transaction=True)
    def test_publish_stores_event_in_outbox_on_commit(self) -> None:
        event = UserCreated(
            aggregate_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            phone="+9999999999",
            email="test@example.com",
            full_name="Test User",
        )
        actual_event_id = uuid.UUID(str(event.event_id))

        with transaction.atomic():
            DomainEventPublisher.get_instance().publish(event)

        stored = OutboxEvent.objects.filter(event_id=actual_event_id).first()
        assert stored is not None
        assert stored.status == OutboxEventStatus.PENDING
        assert stored.event_type == "UserCreated"
        assert "user_id" in stored.payload

    @pytest.mark.django_db(transaction=True)
    def test_publish_does_not_dispatch_eventbus(self) -> None:
        called: list[str] = []

        @event_handler(UserCreated)
        def _handler(payload: dict[str, Any]) -> None:
            called.append(payload.get("email", ""))

        event = UserCreated(
            aggregate_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            phone="+9999999999",
            email="nodispatch@example.com",
            full_name="No Dispatch Test",
        )

        with transaction.atomic():
            DomainEventPublisher.get_instance().publish(event)

        assert called == []
        stored = OutboxEvent.objects.filter(aggregate_id=event.aggregate_id).first()
        assert stored is not None
        assert stored.status == OutboxEventStatus.PENDING

    @pytest.mark.django_db(transaction=True)
    def test_publish_does_not_dispatch_on_rollback(self) -> None:
        called: list[str] = []

        @event_handler(UserCreated)
        def _handler(payload: dict[str, Any]) -> None:
            called.append(payload.get("email", ""))

        event = UserCreated(
            aggregate_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            phone="+9999999999",
            email="rollback@example.com",
            full_name="Rollback Test",
        )

        try:
            with transaction.atomic():
                DomainEventPublisher.get_instance().publish(event)
                raise ValueError("force rollback")
        except ValueError:
            pass

        assert called == []
        assert OutboxEvent.objects.filter(aggregate_id=event.aggregate_id).count() == 0

    @pytest.mark.django_db(transaction=True)
    def test_duplicate_event_suppressed_and_not_dispatched(self) -> None:
        called: list[str] = []

        @event_handler(UserCreated)
        def _handler(payload: dict[str, Any]) -> None:
            called.append(payload.get("email", ""))

        event = UserCreated(
            aggregate_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            phone="+9999999999",
            email="dup@example.com",
            full_name="Dup Test",
        )

        with transaction.atomic():
            DomainEventPublisher.get_instance().publish(event)
            DomainEventPublisher.get_instance().publish(event)

        assert called == []
        assert OutboxEvent.objects.filter(aggregate_id=event.aggregate_id).count() == 1

    def test_publish_preserves_singleton_behavior(self) -> None:
        a = DomainEventPublisher.get_instance()
        b = DomainEventPublisher.get_instance()
        assert a is b

    def test_publish_invalid_event_id_logs_error(self, caplog: Any) -> None:
        class BadEvent:
            event_id = "not-a-uuid"
            aggregate_id = uuid.uuid4()

            def to_payload(self) -> dict[str, Any]:
                return {}

        with transaction.atomic():
            DomainEventPublisher.get_instance().publish(BadEvent())
        assert "Invalid event_id" in caplog.text

    def test_publish_missing_aggregate_id_logs_error(self, caplog: Any) -> None:
        class NoAggEvent:
            event_id = uuid.uuid4()

            def to_payload(self) -> dict[str, Any]:
                return {}

        with transaction.atomic():
            DomainEventPublisher.get_instance().publish(NoAggEvent())
        assert "missing aggregate_id" in caplog.text.lower()

    @pytest.mark.django_db(transaction=True)
    def test_outbox_dispatcher_marks_published_only_after_successful_dispatch(
        self,
    ) -> None:
        good_calls: list[str] = []

        @event_handler(UserCreated)
        def _good_handler(payload: dict[str, Any]) -> None:
            good_calls.append(payload.get("email", ""))

        event = UserCreated(
            aggregate_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            phone="+9999999999",
            email="success@example.com",
            full_name="Success Test",
        )

        with transaction.atomic():
            DomainEventPublisher.get_instance().publish(event)

        stored = OutboxEvent.objects.filter(aggregate_id=event.aggregate_id).first()
        assert stored is not None
        assert stored.status == OutboxEventStatus.PENDING
        assert good_calls == []

        bus = EventBus()
        bus.discover()

        dispatcher = OutboxDispatcher(publisher=bus.dispatch_payload)  # type: ignore[arg-type]
        dispatcher.dispatch()

        stored.refresh_from_db()
        assert stored.status == OutboxEventStatus.PUBLISHED
        assert good_calls == ["success@example.com"]


# ---------------------------------------------------------------------------
# OutboxDispatcher → EventBus integration
# ---------------------------------------------------------------------------
class TestOutboxDispatcherEventBusIntegration:
    def test_outbox_dispatcher_enriches_payload_with_event_type(self) -> None:
        called: list[dict[str, Any]] = []

        def publisher(payload: dict[str, Any]) -> None:
            called.append(payload)

        event = OutboxEvent(
            event_id=uuid.uuid4(),
            aggregate_id=uuid.uuid4(),
            aggregate_type="User",
            event_type="UserCreated",
            event_version="1.0",
            payload={"email": "outbox@example.com"},
        )
        event.save()
        dispatcher = OutboxDispatcher(publisher=publisher)
        dispatched = dispatcher.dispatch()
        assert dispatched == 1
        assert len(called) == 1
        assert called[0]["event_type"] == "UserCreated"
        assert called[0]["email"] == "outbox@example.com"

    def test_outbox_dispatcher_with_eventbus_publisher(self) -> None:
        called: list[str] = []

        @event_handler(FakeEvent)
        def _handler(payload: dict[str, Any]) -> None:
            called.append(payload.get("dummy", "MISSING"))

        event = OutboxEvent(
            event_id=uuid.uuid4(),
            aggregate_id=uuid.uuid4(),
            aggregate_type="Fake",
            event_type="FakeEvent",
            event_version="1.0",
            payload={"dummy": "value"},
        )
        event.save()

        bus = EventBus()
        bus.discover()

        dispatcher = OutboxDispatcher(publisher=bus.dispatch_payload)  # type: ignore[arg-type]
        dispatched = dispatcher.dispatch()
        assert dispatched == 1
        assert called == ["value"]

        event.refresh_from_db()
        assert event.status == OutboxEventStatus.PUBLISHED

    def test_outbox_dispatcher_marks_failed_event_as_dead_letter(self) -> None:
        event = OutboxEvent(
            event_id=uuid.uuid4(),
            aggregate_id=uuid.uuid4(),
            aggregate_type="Fake",
            event_type="FakeEvent",
            status=OutboxEventStatus.FAILED,
            retry_count=5,
            max_retry=6,
            next_retry_at=utc_now(),
            payload={"dummy": "value"},
        )
        event.save()

        def publisher(payload: dict[str, Any]) -> None:
            raise RuntimeError("boom")

        dispatcher = OutboxDispatcher(publisher=publisher)
        dispatched = dispatcher.dispatch()
        assert dispatched == 1
        event.refresh_from_db()
        assert event.status == OutboxEventStatus.DEAD_LETTER


# ---------------------------------------------------------------------------
# InboxDispatcher → EventBus integration
# ---------------------------------------------------------------------------
class TestInboxDispatcherEventBusIntegration:
    def test_inbox_dispatcher_enriches_payload_with_event_type(self) -> None:
        called: list[dict[str, Any]] = []

        def handler(payload: dict[str, Any]) -> None:
            called.append(payload)

        event = InboxEvent(
            event_id=uuid.uuid4(),
            event_type="UserCreated",
            aggregate_id=uuid.uuid4(),
            aggregate_type="User",
            payload={"email": "inbox@example.com"},
        )
        event.save()
        dispatcher = InboxDispatcher(handler=handler)
        processed = dispatcher.dispatch()
        assert processed == 1
        assert len(called) == 1
        assert called[0]["event_type"] == "UserCreated"
        assert called[0]["email"] == "inbox@example.com"

    def test_inbox_dispatcher_with_eventbus_handler(self) -> None:
        called: list[str] = []

        @event_handler(FakeEvent)
        def _handler(payload: dict[str, Any]) -> None:
            called.append(payload.get("dummy", "MISSING"))

        event = InboxEvent(
            event_id=uuid.uuid4(),
            event_type="FakeEvent",
            aggregate_id=uuid.uuid4(),
            aggregate_type="Fake",
            payload={"dummy": "value"},
        )
        event.save()

        bus = EventBus()
        bus.discover()

        dispatcher = InboxDispatcher(handler=bus.dispatch_payload)  # type: ignore[arg-type]
        processed = dispatcher.dispatch()
        assert processed == 1
        assert called == ["value"]

        event.refresh_from_db()
        assert event.status == InboxEventStatus.PROCESSED

    def test_inbox_dispatcher_marks_failed_event_as_dead_letter(self) -> None:
        event = InboxEvent(
            event_id=uuid.uuid4(),
            event_type="FakeEvent",
            aggregate_id=uuid.uuid4(),
            aggregate_type="Fake",
            status=InboxEventStatus.FAILED,
            retry_count=5,
            max_retry=6,
            next_retry_at=utc_now(),
            payload={"dummy": "value"},
        )
        event.save()

        def handler(payload: dict[str, Any]) -> None:
            raise RuntimeError("boom")

        dispatcher = InboxDispatcher(handler=handler)
        processed = dispatcher.dispatch()
        assert processed == 1
        event.refresh_from_db()
        assert event.status == InboxEventStatus.DEAD_LETTER


# ---------------------------------------------------------------------------
# EventBus behavior verification
# ---------------------------------------------------------------------------
class TestEventBusBehaviorAfterIntegration:
    def setup_method(self) -> None:
        self._registry = EventHandlerRegistry()

    def test_multiple_handlers_execute(self) -> None:
        calls: list[str] = []

        @event_handler(FakeEvent)
        def h1(event: Any) -> None:
            calls.append("h1")

        @event_handler(FakeEvent)
        def h2(event: Any) -> None:
            calls.append("h2")

        bus = EventBus()
        bus.publish(FakeEvent())
        assert "h1" in calls
        assert "h2" in calls

    def test_one_handler_failure_does_not_stop_remaining(self) -> None:
        calls: list[str] = []

        @event_handler(FakeEvent)
        def good(event: Any) -> None:
            calls.append("good")

        @event_handler(FakeEvent)
        def bad(event: Any) -> None:
            calls.append("bad")
            raise RuntimeError("bad")

        bus = EventBus()
        report = bus.publish(FakeEvent())
        assert report.success_count == 1
        assert report.failure_count == 1
        assert "good" in calls
        assert "bad" in calls

    def test_handler_ordering_is_deterministic(self) -> None:
        order: list[str] = []

        @event_handler(FakeEvent)
        def first(event: Any) -> None:
            order.append("first")

        @event_handler(FakeEvent)
        def second(event: Any) -> None:
            order.append("second")

        bus = EventBus()
        bus.publish(FakeEvent())
        assert order == ["first", "second"]

    def test_no_handlers_returns_empty_report(self) -> None:
        bus = EventBus()
        report = bus.publish(FakeEvent())
        assert report.total_handlers == 0
        assert report.success_count == 0
        assert report.failure_count == 0
        assert report.all_succeeded is False

    def test_middleware_executes_before_and_after(self) -> None:
        order: list[str] = []

        class OrderMW:
            def before_dispatch(
                self, event: Any, context: dict[str, Any]
            ) -> dict[str, Any]:
                order.append("before")
                return context

            def after_dispatch(
                self, event: Any, context: dict[str, Any], result: Any
            ) -> Any:
                order.append("after")
                return result

        bus = EventBus(middleware=[OrderMW()])

        @event_handler(FakeEvent)
        def h(event: Any) -> None:
            order.append("handler")

        bus.publish(FakeEvent())
        assert order.index("before") < order.index("handler")
        assert order.index("handler") < order.index("after")

    def test_metrics_middleware_updates_counters(self) -> None:
        from core.events.bus.metrics import EventMetrics

        metrics = EventMetrics()

        @event_handler(FakeEvent)
        def h(event: Any) -> None:
            pass

        bus = EventBus(middleware=[MetricsMiddleware(metrics)])
        bus.publish(FakeEvent())
        snapshot = metrics.snapshot()
        assert snapshot["events_dispatched"] == 1
        assert snapshot["handlers_executed"] == 1
        assert snapshot["handler_failures"] == 0

    def test_execution_report_populated_correctly(self) -> None:
        bus = EventBus()

        @event_handler(FakeEvent)
        def h(event: Any) -> None:
            pass

        report = bus.publish(FakeEvent())
        assert report.event_type == "FakeEvent"
        assert report.success_count == 1
        assert report.failure_count == 0
        assert report.duration_seconds >= 0
        assert report.dispatched_at != ""

    def test_dispatch_payload_no_matching_handler(self) -> None:
        bus = EventBus()
        payload = {"event_type": "UnknownEvent", "event_id": "x1"}
        report = bus.dispatch_payload(payload)
        assert report.total_handlers == 0
        assert report.event_type == "UnknownEvent"


# ---------------------------------------------------------------------------
# Transaction.on_commit behavior
# ---------------------------------------------------------------------------
class TestTransactionOnCommitBehavior:
    @pytest.mark.django_db(transaction=True)
    def test_on_commit_callback_stores_event_after_commit(self) -> None:
        event = UserCreated(
            aggregate_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            phone="+9999999999",
            email="commit@example.com",
            full_name="Commit Test",
        )
        actual_event_id = uuid.UUID(str(event.event_id))

        with transaction.atomic():
            DomainEventPublisher.get_instance().publish(event)
            assert OutboxEvent.objects.filter(event_id=actual_event_id).count() == 0

        stored = OutboxEvent.objects.filter(event_id=actual_event_id).first()
        assert stored is not None
        assert stored.status == OutboxEventStatus.PENDING

    @pytest.mark.django_db(transaction=True)
    def test_on_commit_callback_not_run_after_rollback(self) -> None:
        event_id = uuid.uuid4()
        event = UserCreated(
            aggregate_id=event_id,
            user_id=event_id,
            phone="+9999999999",
            email="noroll@example.com",
            full_name="No Roll Test",
        )

        try:
            with transaction.atomic():
                DomainEventPublisher.get_instance().publish(event)
                raise RuntimeError("abort")
        except RuntimeError:
            pass

        assert OutboxEvent.objects.filter(event_id=event_id).count() == 0


# ---------------------------------------------------------------------------
# Management command integration
# ---------------------------------------------------------------------------
class TestManagementCommandIntegration:
    def test_dispatch_outbox_events_command_uses_eventbus(self) -> None:
        called: list[str] = []

        @event_handler(FakeEvent)
        def _handler(payload: dict[str, Any]) -> None:
            called.append(payload.get("dummy", "MISSING"))

        event = OutboxEvent(
            event_id=uuid.uuid4(),
            aggregate_id=uuid.uuid4(),
            aggregate_type="Fake",
            event_type="FakeEvent",
            payload={"dummy": "cmd"},
        )
        event.save()

        dispatcher = OutboxDispatcher(publisher=EventBus().dispatch_payload)  # type: ignore[arg-type]
        dispatched = dispatcher.dispatch()

        assert dispatched == 1
        assert called == ["cmd"]
        event.refresh_from_db()
        assert event.status == OutboxEventStatus.PUBLISHED


# ---------------------------------------------------------------------------
# end-to-end: publisher → outbox → bus → handlers (NO double dispatch)
# ---------------------------------------------------------------------------
class TestEndToEndFlow:
    @pytest.mark.django_db(transaction=True)
    def test_full_flow_business_service_via_publisher(self) -> None:
        bus = EventBus()
        bus.discover()

        calls: list[str] = []

        @event_handler(UserCreated)
        def _handler(payload: dict[str, Any]) -> None:
            calls.append(payload.get("email", ""))

        event_id = uuid.uuid4()
        event = UserCreated(
            aggregate_id=event_id,
            user_id=event_id,
            phone="+9999999999",
            email="e2e@example.com",
            full_name="E2E Test",
        )
        actual_event_id = uuid.UUID(str(event.event_id))

        with transaction.atomic():
            DomainEventPublisher.get_instance().publish(event)

        stored = OutboxEvent.objects.filter(event_id=actual_event_id).first()
        assert stored is not None
        assert stored.status == OutboxEventStatus.PENDING
        assert calls == []

        dispatcher = OutboxDispatcher(publisher=bus.dispatch_payload)  # type: ignore[arg-type]
        dispatcher.dispatch()

        assert calls == ["e2e@example.com"]

        stored.refresh_from_db()
        assert stored.status == OutboxEventStatus.PUBLISHED


# ---------------------------------------------------------------------------
# Regression: exactly-once handler execution
# ---------------------------------------------------------------------------
class TestExactlyOnceExecution:
    @pytest.mark.django_db(transaction=True)
    def test_single_published_event_results_in_exactly_one_handler_invocation(
        self,
    ) -> None:
        calls: list[str] = []

        @event_handler(UserCreated)
        def _handler(payload: dict[str, Any]) -> None:
            calls.append(payload.get("email", ""))

        event = UserCreated(
            aggregate_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            phone="+9999999999",
            email="exactly.once@example.com",
            full_name="Exactly Once",
        )

        with transaction.atomic():
            DomainEventPublisher.get_instance().publish(event)

        bus = EventBus()
        bus.discover()
        dispatcher = OutboxDispatcher(publisher=bus.dispatch_payload)  # type: ignore[arg-type]

        dispatcher.dispatch()
        dispatcher.dispatch()

        assert calls == ["exactly.once@example.com"]

        stored = OutboxEvent.objects.filter(aggregate_id=event.aggregate_id).first()
        assert stored is not None
        assert stored.status == OutboxEventStatus.PUBLISHED


__all__ = [
    "TestDomainEventPublisherIntegration",
    "TestOutboxDispatcherEventBusIntegration",
    "TestInboxDispatcherEventBusIntegration",
    "TestEventBusBehaviorAfterIntegration",
    "TestTransactionOnCommitBehavior",
    "TestManagementCommandIntegration",
    "TestEndToEndFlow",
    "TestExactlyOnceExecution",
]
