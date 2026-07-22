from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """Middleware that logs every dispatch before and after handler execution."""

    def before_dispatch(self, event: Any, context: dict[str, Any]) -> dict[str, Any]:
        event_type = type(event).__name__
        context["start_time"] = time.perf_counter()
        logger.debug("Dispatching event: %s", event_type)
        return context

    def after_dispatch(
        self,
        event: Any,
        context: dict[str, Any],
        result: Any,
    ) -> Any:
        start = context.get("start_time")
        duration = time.perf_counter() - start if start is not None else 0.0
        logger.debug(
            "Event %s dispatched in %.4fs",
            type(event).__name__,
            duration,
        )
        return result


class MetricsMiddleware:
    """Middleware that records metrics via the event bus metrics collector."""

    def __init__(self, metrics_collector: Any) -> None:
        self._metrics = metrics_collector

    def before_dispatch(self, event: Any, context: dict[str, Any]) -> dict[str, Any]:
        if hasattr(self._metrics, "record_dispatched"):
            self._metrics.record_dispatched()
        context["start_time"] = time.perf_counter()
        return context

    def after_dispatch(
        self,
        event: Any,
        context: dict[str, Any],
        result: Any,
    ) -> Any:
        event_type = type(event).__name__
        if context.get("handler_failed"):
            if hasattr(self._metrics, "record_handler_failure"):
                self._metrics.record_handler_failure(event_type)
        else:
            duration = context.get("duration", 0.0)
            if hasattr(self._metrics, "record_handler_executed"):
                self._metrics.record_handler_executed(event_type, duration)
        return result


__all__ = ["LoggingMiddleware", "MetricsMiddleware"]
