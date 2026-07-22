from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IEventHandler(Protocol):
    """Protocol for event handlers."""

    def execute(self, event: Any) -> Any: ...


@runtime_checkable
class IMiddleware(Protocol):
    """Protocol for middleware in the event bus pipeline."""

    def before_dispatch(
        self, event: Any, context: dict[str, Any]
    ) -> dict[str, Any]: ...

    def after_dispatch(
        self,
        event: Any,
        context: dict[str, Any],
        result: Any,
    ) -> Any: ...


@runtime_checkable
class IEventBus(Protocol):
    """Protocol for the event bus."""

    def publish(self, event: Any) -> Any: ...

    def subscribe(self, event_type: type, handler: Any) -> None: ...

    def unsubscribe(self, event_type: type, handler: Any) -> None: ...

    def get_handlers(self, event_type: type) -> list[Any]: ...


HandlerFunc = Callable[..., Any]

__all__ = [
    "IEventHandler",
    "IMiddleware",
    "IEventBus",
    "HandlerFunc",
]
