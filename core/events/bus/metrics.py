from __future__ import annotations

import logging
from typing import Any

from shared.type_compat import override

logger = logging.getLogger(__name__)


class EventMetrics:
    """Lightweight in-memory metrics for the event bus.

    Tracks:
    - events_dispatched
    - handlers_executed
    - handler_failures
    - durations per event type
    """

    def __init__(self) -> None:
        self.events_dispatched: int = 0
        self.handlers_executed: int = 0
        self.handler_failures: int = 0
        self._durations: dict[str, list[float]] = {}
        self._lock = __import__("threading").RLock()

    def record_dispatched(self) -> None:
        with self._lock:
            self.events_dispatched += 1

    def record_handler_executed(self, event_type: str, duration_seconds: float) -> None:
        with self._lock:
            self.handlers_executed += 1
            self._durations.setdefault(event_type, []).append(duration_seconds)

    def record_handler_failure(self, event_type: str) -> None:
        with self._lock:
            self.handler_failures += 1

    def average_duration(self, event_type: str) -> float:
        with self._lock:
            durations = self._durations.get(event_type, [])
            if not durations:
                return 0.0
            return sum(durations) / len(durations)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "events_dispatched": self.events_dispatched,
                "handlers_executed": self.handlers_executed,
                "handler_failures": self.handler_failures,
                "average_durations": {
                    event_type: self.average_duration(event_type)
                    for event_type in self._durations
                },
            }

    def reset(self) -> None:
        with self._lock:
            self.events_dispatched = 0
            self.handlers_executed = 0
            self.handler_failures = 0
            self._durations.clear()

    @override
    def __repr__(self) -> str:
        return (
            f"EventMetrics("
            f"dispatched={self.events_dispatched}, "
            f"executed={self.handlers_executed}, "
            f"failures={self.handler_failures})"
        )


__all__ = ["EventMetrics"]
