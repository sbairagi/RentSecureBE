from __future__ import annotations

import time
from typing import Any

from core.events.bus.dispatcher import EventBus
from core.events.bus.exceptions import MiddlewareExecutionError
from core.events.bus.middleware import LoggingMiddleware, MetricsMiddleware
from core.events.bus.registry import EventHandlerRegistry


class FakeEvent:
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


class TestLoggingMiddleware:
    def test_before_sets_start_time(self) -> None:
        mw = LoggingMiddleware()
        context: dict[str, Any] = {}
        event = FakeEvent()
        result = mw.before_dispatch(event, context)
        assert "start_time" in result

    def test_after_completes(self) -> None:
        mw = LoggingMiddleware()
        context = {"start_time": time.perf_counter() - 0.05}
        result = mw.after_dispatch(FakeEvent(), context, None)
        assert result is None


class TestMetricsMiddleware:
    def test_before_records_dispatched(self) -> None:
        metrics = MagicMockMetrics()
        mw = MetricsMiddleware(metrics)
        context: dict[str, Any] = {}
        result = mw.before_dispatch(FakeEvent(), context)
        assert metrics.dispatched == 1
        assert "start_time" in result

    def test_after_records_handler_execution(self) -> None:
        metrics = MagicMockMetrics()
        mw = MetricsMiddleware(metrics)
        context = {"start_time": time.perf_counter() - 0.05, "duration": 0.05}
        mw.after_dispatch(FakeEvent(), context, None)
        assert metrics.executed == 1
        assert metrics.last_event_type == "FakeEvent"
        assert metrics.last_duration > 0

    def test_after_does_nothing_when_no_metrics(self) -> None:
        mw = MetricsMiddleware(None)
        context: dict[str, Any] = {}
        result = mw.after_dispatch(FakeEvent(), context, "result")
        assert result == "result"


class TestMiddlewarePipeline:
    def test_middleware_order_before_runs_in_registration_order(self) -> None:
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

        registry = EventHandlerRegistry()

        def handler(event: Any) -> None:
            order.append("handler")

        bus = EventBus(registry=registry, middleware=[OrderMW()])
        bus.subscribe(FakeEvent, handler)
        bus.publish(FakeEvent())
        assert order.index("before") < order.index("handler")
        assert order.index("handler") < order.index("after")

    def test_middleware_after_runs_in_reverse_order(self) -> None:
        order: list[str] = []

        class FirstMW:
            def before_dispatch(
                self, event: Any, context: dict[str, Any]
            ) -> dict[str, Any]:
                order.append("first_before")
                return context

            def after_dispatch(
                self, event: Any, context: dict[str, Any], result: Any
            ) -> Any:
                order.append("first_after")
                return result

        class SecondMW:
            def before_dispatch(
                self, event: Any, context: dict[str, Any]
            ) -> dict[str, Any]:
                order.append("second_before")
                return context

            def after_dispatch(
                self, event: Any, context: dict[str, Any], result: Any
            ) -> Any:
                order.append("second_after")
                return result

        registry = EventHandlerRegistry()

        def handler(event: Any) -> None:
            order.append("handler")

        bus = EventBus(
            registry=registry,
            middleware=[FirstMW(), SecondMW()],
        )
        bus.subscribe(FakeEvent, handler)
        bus.publish(FakeEvent())
        before_idx = {name: order.index(name) for name in order}
        assert before_idx["first_before"] < before_idx["second_before"]
        assert before_idx["first_after"] > before_idx["second_after"]

    def test_middleware_exception_before_does_not_block_remaining_handlers(
        self,
    ) -> None:
        call_count = 0

        class FailingMW:
            def before_dispatch(
                self, event: Any, context: dict[str, Any]
            ) -> dict[str, Any]:
                raise MiddlewareExecutionError("mw fail", middleware_name="FailingMW")

            def after_dispatch(
                self, event: Any, context: dict[str, Any], result: Any
            ) -> Any:
                return result

        registry = EventHandlerRegistry()

        def handler(event: Any) -> None:
            nonlocal call_count
            call_count += 1

        bus = EventBus(registry=registry, middleware=[FailingMW()])
        bus.subscribe(FakeEvent, handler)
        report = bus.publish(FakeEvent())
        assert report.failure_count == 1
        assert report.total_handlers == 1

    def test_multiple_middleware_all_run(self) -> None:
        calls: list[str] = []

        class TrackingMW:
            def __init__(self, name: str) -> None:
                self.name = name

            def before_dispatch(
                self, event: Any, context: dict[str, Any]
            ) -> dict[str, Any]:
                calls.append(f"{self.name}_before")
                return context

            def after_dispatch(
                self, event: Any, context: dict[str, Any], result: Any
            ) -> Any:
                calls.append(f"{self.name}_after")
                return result

        registry = EventHandlerRegistry()

        def handler(event: Any) -> None:
            pass

        bus = EventBus(
            registry=registry,
            middleware=[TrackingMW("a"), TrackingMW("b")],
        )
        bus.subscribe(FakeEvent, handler)
        bus.publish(FakeEvent())
        assert "a_before" in calls
        assert "b_before" in calls
        assert "a_after" in calls
        assert "b_after" in calls


__all__ = [
    "TestLoggingMiddleware",
    "TestMetricsMiddleware",
    "TestMiddlewarePipeline",
]
