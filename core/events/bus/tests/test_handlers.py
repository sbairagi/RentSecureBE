from __future__ import annotations

import pytest

from core.events.bus.handlers import ExecutionReport, HandlerResult


class TestHandlerResult:
    def test_success_result(self) -> None:
        result = HandlerResult.success_result("handler_a", 0.05)
        assert result.handler_name == "handler_a"
        assert result.success is True
        assert result.duration_seconds == 0.05
        assert result.exception is None
        assert result.exception_traceback == ""

    def test_failure_result(self) -> None:
        exc = ValueError("boom")
        result = HandlerResult.failure_result("handler_a", 0.1, exc)
        assert result.handler_name == "handler_a"
        assert result.success is False
        assert result.duration_seconds == 0.1
        assert result.exception is exc
        assert "boom" in result.exception_traceback

    def test_failure_result_immutable(self) -> None:
        result = HandlerResult.success_result("h", 0.0)
        with pytest.raises(AttributeError):
            result.handler_name = "other"

    def test_success_result_immutable(self) -> None:
        result = HandlerResult.success_result("h", 0.0)
        with pytest.raises(AttributeError):
            result.success = False


class TestExecutionReport:
    def test_empty_report(self) -> None:
        report = ExecutionReport(event_type="UserCreated", event_id="abc")
        assert report.success_count == 0
        assert report.failure_count == 0
        assert report.total_handlers == 0
        assert report.all_succeeded is False

    def test_report_with_successes(self) -> None:
        report = ExecutionReport(
            event_type="UserCreated",
            event_id="abc",
            successful_handlers=("h1", "h2"),
            failed_handlers=(),
            total_handlers=2,
        )
        assert report.success_count == 2
        assert report.failure_count == 0
        assert report.all_succeeded is True

    def test_report_with_failures(self) -> None:
        result = HandlerResult.failure_result("h1", 0.1, ValueError("x"))
        report = ExecutionReport(
            event_type="UserCreated",
            event_id="abc",
            successful_handlers=(),
            failed_handlers=(result,),
            total_handlers=1,
        )
        assert report.success_count == 0
        assert report.failure_count == 1
        assert report.all_succeeded is False

    def test_report_mixed(self) -> None:
        fail = HandlerResult.failure_result("h2", 0.1, ValueError("x"))
        report = ExecutionReport(
            event_type="UserCreated",
            event_id="abc",
            successful_handlers=("h1",),
            failed_handlers=(fail,),
            total_handlers=2,
        )
        assert report.all_succeeded is False

    def test_report_includes_dispatched_at(self) -> None:
        report = ExecutionReport(event_type="UserCreated", event_id="abc")
        assert report.dispatched_at != ""

    def test_report_immutable(self) -> None:
        report = ExecutionReport(
            event_type="UserCreated",
            event_id="abc",
            successful_handlers=("h1",),
        )
        with pytest.raises(AttributeError):
            report.successful_handlers = ("h2",)


__all__ = ["TestHandlerResult", "TestExecutionReport"]
