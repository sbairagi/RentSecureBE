from __future__ import annotations

from core.events.bus.metrics import EventMetrics


class TestEventMetrics:
    def test_record_dispatched(self) -> None:
        metrics = EventMetrics()
        metrics.record_dispatched()
        assert metrics.events_dispatched == 1

    def test_record_multiple_dispatched(self) -> None:
        metrics = EventMetrics()
        for _ in range(5):
            metrics.record_dispatched()
        assert metrics.events_dispatched == 5

    def test_record_handler_executed(self) -> None:
        metrics = EventMetrics()
        metrics.record_handler_executed("UserCreated", 0.05)
        assert metrics.handlers_executed == 1
        assert metrics.average_duration("UserCreated") == 0.05

    def test_record_multiple_handler_executions(self) -> None:
        metrics = EventMetrics()
        metrics.record_handler_executed("UserCreated", 0.1)
        metrics.record_handler_executed("UserCreated", 0.3)
        assert metrics.handlers_executed == 2
        assert abs(metrics.average_duration("UserCreated") - 0.2) < 1e-9

    def test_record_handler_failure(self) -> None:
        metrics = EventMetrics()
        metrics.record_handler_failure("UserCreated")
        assert metrics.handler_failures == 1

    def test_average_duration_unknown_type_returns_zero(self) -> None:
        metrics = EventMetrics()
        assert metrics.average_duration("Unknown") == 0.0

    def test_snapshot_returns_copy(self) -> None:
        metrics = EventMetrics()
        metrics.record_dispatched()
        metrics.record_handler_executed("X", 0.1)
        snap = metrics.snapshot()
        assert snap["events_dispatched"] == 1
        assert snap["handlers_executed"] == 1
        assert "X" in snap["average_durations"]
        metrics.record_dispatched()
        assert snap["events_dispatched"] == 1

    def test_reset_clears_all_counters(self) -> None:
        metrics = EventMetrics()
        metrics.record_dispatched()
        metrics.record_handler_executed("X", 0.1)
        metrics.record_handler_failure("X")
        metrics.reset()
        assert metrics.events_dispatched == 0
        assert metrics.handlers_executed == 0
        assert metrics.handler_failures == 0
        assert metrics.average_duration("X") == 0.0

    def test_thread_safety_concurrent_writes(self) -> None:
        import threading

        metrics = EventMetrics()
        errors: list[Exception] = []

        def writer() -> None:
            try:
                for _ in range(100):
                    metrics.record_dispatched()
                    metrics.record_handler_executed("T", 0.01)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=writer) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        assert metrics.events_dispatched == 400
        assert metrics.handlers_executed == 400

    def test_repr(self) -> None:
        metrics = EventMetrics()
        metrics.record_dispatched()
        metrics.record_handler_executed("X", 0.1)
        r = repr(metrics)
        assert "dispatched=1" in r
        assert "executed=1" in r


__all__ = ["TestEventMetrics"]
