from __future__ import annotations

import traceback
from dataclasses import dataclass, field

from core.shared.time import utc_now


@dataclass(frozen=True)
class HandlerResult:
    """Immutable result of executing a single handler."""

    handler_name: str
    success: bool
    duration_seconds: float
    exception: BaseException | None = field(default=None, compare=False)
    exception_traceback: str = ""

    @classmethod
    def success_result(
        cls,
        handler_name: str,
        duration_seconds: float,
    ) -> HandlerResult:
        return cls(
            handler_name=handler_name,
            success=True,
            duration_seconds=duration_seconds,
        )

    @classmethod
    def failure_result(
        cls,
        handler_name: str,
        duration_seconds: float,
        exception: BaseException,
    ) -> HandlerResult:
        tb_lines = traceback.format_exception(
            type(exception), exception, exception.__traceback__
        )
        return cls(
            handler_name=handler_name,
            success=False,
            duration_seconds=duration_seconds,
            exception=exception,
            exception_traceback="".join(tb_lines),
        )


@dataclass(frozen=True)
class ExecutionReport:
    """Immutable execution report for a single event dispatch."""

    event_type: str
    event_id: str
    successful_handlers: tuple[str, ...] = ()
    failed_handlers: tuple[HandlerResult, ...] = ()
    total_handlers: int = 0
    duration_seconds: float = 0.0
    dispatched_at: str = field(default_factory=lambda: utc_now().isoformat())

    @property
    def success_count(self) -> int:
        return len(self.successful_handlers)

    @property
    def failure_count(self) -> int:
        return len(self.failed_handlers)

    @property
    def all_succeeded(self) -> bool:
        return self.failure_count == 0 and self.total_handlers > 0


__all__ = ["HandlerResult", "ExecutionReport"]
