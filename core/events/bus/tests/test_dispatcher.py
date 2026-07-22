from __future__ import annotations

from typing import Any

from core.events.bus.dispatcher import EventBus
from core.events.bus.exceptions import MiddlewareExecutionError
from core.events.bus.handlers import ExecutionReport
from core.events.bus.middleware import MetricsMiddleware
from core.events.bus.registry import EventHandlerRegistry


class FakeEvent:
    def __init__(self, event_id: str = "e1") -> None:
        self.event_id = event_id


class AnotherEvent:
    pass


class MagicMockMetrics:
    def __init__(self) -> None:
        self.dispatched = 0
        self.executed = 0
        self.failures = 0
        self.last_event_type = ""
        self.last_duration = 0.0

    def record_dispatched(self) -> None:
        self.dispatched += 1

    def record_handler_executed(self, event_type: str, duration: float) -> None:
        self.executed += 1
        self.last_event_type = event_type
        self.last_duration = duration

    def record_handler_failure(self, event_type: str) -> None:
        self.failures += 1


class TestEventBusDispatch:
    def setup_method(self) -> None:
        self._registry = EventHandlerRegistry()
        self._metrics = MagicMockMetrics()

    def _make_bus(self, middleware: list[Any] | None = None) -> EventBus:
        actual_middleware: list[Any] = list(middleware or [])
        return EventBus(
            registry=self._registry,
            middleware=actual_middleware,
        )

    def test_publish_no_handlers(self) -> None:
        bus = self._make_bus()
        event = FakeEvent()
        report = bus.publish(event)
        assert report.total_handlers == 0
        assert report.success_count == 0
        assert report.failure_count == 0

    def test_publish_single_handler_succeeds(self) -> None:
        called: list[str] = []

        def handler(event: Any) -> None:
            called.append(type(event).__name__)

        bus = self._make_bus()
        bus.subscribe(FakeEvent, handler)
        event = FakeEvent()
        bus.publish(event)
        assert called == ["FakeEvent"]

    def test_publish_multiple_handlers_succeed(self) -> None:
        calls: list[str] = []

        def handler_a(event: Any) -> None:
            calls.append("a")

        def handler_b(event: Any) -> None:
            calls.append("b")

        bus = self._make_bus()
        bus.subscribe(FakeEvent, handler_a)
        bus.subscribe(FakeEvent, handler_b)
        bus.publish(FakeEvent())
        assert "a" in calls
        assert "b" in calls

    def test_handler_failure_does_not_block_others(self) -> None:
        calls: list[str] = []

        def good_handler(event: Any) -> None:
            calls.append("good")

        def bad_handler(event: Any) -> None:
            calls.append("bad")
            raise RuntimeError("handler error")

        bus = self._make_bus()
        bus.subscribe(FakeEvent, good_handler)
        bus.subscribe(FakeEvent, bad_handler)
        report = bus.publish(FakeEvent())
        assert report.total_handlers == 2
        assert report.success_count == 1
        assert report.failure_count == 1
        assert "bad" in calls
        assert report.failed_handlers[0].handler_name == "bad_handler"

    def test_report_includes_duration(self) -> None:
        def handler(event: Any) -> None:
            pass

        bus = self._make_bus()
        bus.subscribe(FakeEvent, handler)
        report = bus.publish(FakeEvent())
        assert report.duration_seconds > 0

    def test_publish_updates_metrics(self) -> None:
        bus = self._make_bus(middleware=[MetricsMiddleware(self._metrics)])
        bus.subscribe(FakeEvent, lambda e: None)
        bus.publish(FakeEvent())
        assert self._metrics.dispatched == 1
        assert self._metrics.executed == 1

    def test_subscribe_and_get_handlers(self) -> None:
        bus = self._make_bus()

        def handler(event: Any) -> None:
            pass

        bus.subscribe(FakeEvent, handler)
        handlers = bus.get_handlers(FakeEvent)
        assert handler in handlers

    def test_unsubscribe_removes_handler(self) -> None:
        bus = self._make_bus()

        def handler(event: Any) -> None:
            pass

        bus.subscribe(FakeEvent, handler)
        bus.unsubscribe(FakeEvent, handler)
        assert bus.get_handlers(FakeEvent) == []

    def test_clear_removes_all(self) -> None:
        bus = self._make_bus()
        bus.subscribe(FakeEvent, lambda e: None)
        bus.subscribe(AnotherEvent, lambda e: None)
        bus.clear()
        assert bus.get_handlers(FakeEvent) == []
        assert bus.get_handlers(AnotherEvent) == []

    def test_handler_with_exception_has_traceback(self) -> None:
        def bad(event: Any) -> None:
            raise ValueError("test error")

        bus = self._make_bus()
        bus.subscribe(FakeEvent, bad)
        report = bus.publish(FakeEvent())
        assert report.failed_handlers[0].exception_traceback != ""
        assert "test error" in report.failed_handlers[0].exception_traceback

    def test_execution_report_all_succeeded_false_when_no_handlers(self) -> None:
        report = ExecutionReport(event_type="X", event_id="1")
        assert report.all_succeeded is False

    def test_execution_report_all_succeeded_true_on_full_success(self) -> None:
        bus = self._make_bus()
        bus.subscribe(FakeEvent, lambda e: None)
        report = bus.publish(FakeEvent())
        assert report.all_succeeded is True

    def test_i_event_handler_passed_directly(self) -> None:
        class EventWithId:
            event_id = "x"

        class MyHandler:
            def execute(self, event: Any) -> None:
                self.called = True

        handler_obj = MyHandler()
        bus = self._make_bus()
        bus.subscribe(EventWithId, handler_obj)
        bus.publish(EventWithId())
        assert handler_obj.called

    def test_discover_calls_registry_discover(self) -> None:
        bus = self._make_bus()
        count = bus.discover()
        assert isinstance(count, int)

    def test_resolve_name_for_function(self) -> None:
        bus = self._make_bus()

        def my_handler(event: Any) -> None:
            pass

        assert bus._resolve_name(my_handler) == "my_handler"

    def test_resolve_name_for_object_with_execute(self) -> None:
        bus = self._make_bus()

        class HandlerObj:
            def execute(self, event: Any) -> None:
                pass

        obj = HandlerObj()
        assert bus._resolve_name(obj) == "HandlerObj"

    def test_resolve_name_for_other_object(self) -> None:
        bus = self._make_bus()
        obj = object()
        result = bus._resolve_name(obj)
        assert "object" in result or result.startswith("<")

    def test_middleware_before_failure_continues_to_next_handler(self) -> None:
        class FailingBefore:
            def before_dispatch(
                self, event: Any, context: dict[str, Any]
            ) -> dict[str, Any]:
                raise MiddlewareExecutionError(
                    "before fail", middleware_name="FailingBefore"
                )

            def after_dispatch(
                self, event: Any, context: dict[str, Any], result: Any
            ) -> Any:
                return result

        def handler(event: Any) -> None:
            pass

        bus = self._make_bus(middleware=[FailingBefore()])
        bus.subscribe(FakeEvent, handler)
        report = bus.publish(FakeEvent())
        assert report.failure_count == 1
        assert report.total_handlers == 1

    def test_middleware_before_failure_continues_in_payload_path(self) -> None:
        class FailingBefore:
            def before_dispatch(
                self, event: Any, context: dict[str, Any]
            ) -> dict[str, Any]:
                raise MiddlewareExecutionError(
                    "before fail", middleware_name="FailingBefore"
                )

            def after_dispatch(
                self, event: Any, context: dict[str, Any], result: Any
            ) -> Any:
                return result

        bus = self._make_bus(middleware=[FailingBefore()])
        bus.subscribe(FakeEvent, lambda p: None)
        payload = {"event_type": "FakeEvent", "event_id": "p1"}
        report = bus.dispatch_payload(payload)
        assert report.failure_count == 1

    def test_middleware_after_failure_in_payload_path(self) -> None:
        call_log: list[str] = []

        class FailingAfter:
            def before_dispatch(
                self, event: Any, context: dict[str, Any]
            ) -> dict[str, Any]:
                return context

            def after_dispatch(
                self, event: Any, context: dict[str, Any], result: Any
            ) -> Any:
                call_log.append("after")
                raise RuntimeError("after boom")

        bus = self._make_bus(middleware=[FailingAfter()])
        bus.subscribe(FakeEvent, lambda p: call_log.append("handler"))
        payload = {"event_type": "FakeEvent", "event_id": "p1"}
        bus.dispatch_payload(payload)
        assert call_log == ["handler", "after"]

    def test_metrics_middleware_records_failure_on_handler_exception(self) -> None:
        metrics = MagicMockMetrics()

        def bad_handler(event: Any) -> None:
            raise RuntimeError("oops")

        bus = self._make_bus(middleware=[MetricsMiddleware(metrics)])
        bus.subscribe(FakeEvent, bad_handler)
        bus.publish(FakeEvent())
        assert metrics.failures == 1


class TestDispatchPayload:
    def setup_method(self) -> None:
        self._registry = EventHandlerRegistry()

    def _make_bus(self) -> EventBus:
        return EventBus(registry=self._registry)

    def test_dispatch_payload_no_matching_handler(self) -> None:
        bus = self._make_bus()
        payload = {"event_type": "UnknownEvent", "event_id": "x1"}
        report = bus.dispatch_payload(payload)
        assert report.total_handlers == 0
        assert report.event_type == "UnknownEvent"

    def test_dispatch_payload_with_matching_handler(self) -> None:
        calls: list[dict[str, Any]] = []

        def handler(payload: dict[str, Any]) -> None:
            calls.append(payload)

        bus = self._make_bus()
        bus.subscribe(FakeEvent, handler)
        payload = {"event_type": "FakeEvent", "event_id": "p1"}
        bus.dispatch_payload(payload)
        assert len(calls) == 1
        assert calls[0]["event_id"] == "p1"

    def test_dispatch_payload_handler_failure_tracked(self) -> None:
        def bad_handler(payload: dict[str, Any]) -> None:
            raise RuntimeError("payload boom")

        bus = self._make_bus()
        bus.subscribe(FakeEvent, bad_handler)
        payload = {"event_type": "FakeEvent", "event_id": "p1"}
        report = bus.dispatch_payload(payload)
        assert report.failure_count == 1
        assert report.failed_handlers[0].handler_name == "bad_handler"


__all__ = [
    "TestEventBusDispatch",
    "TestDispatchPayload",
    "MagicMockMetrics",
]
