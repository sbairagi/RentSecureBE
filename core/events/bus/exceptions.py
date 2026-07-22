from __future__ import annotations

from core.infrastructure.exceptions import InfrastructureError


class EventBusError(InfrastructureError):
    """Base exception for event bus failures."""


class HandlerExecutionError(EventBusError):
    """Raised when an event handler raises an exception."""

    def __init__(
        self,
        message: str = "",
        *,
        event_type: str = "",
        handler_name: str = "",
        original_exception: BaseException | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(message, **kwargs)
        self.event_type = event_type
        self.handler_name = handler_name
        self.original_exception = original_exception


class MiddlewareExecutionError(EventBusError):
    """Raised when middleware raises an exception."""

    def __init__(
        self,
        message: str = "",
        *,
        middleware_name: str = "",
        original_exception: BaseException | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(message, **kwargs)
        self.middleware_name = middleware_name
        self.original_exception = original_exception


__all__ = [
    "EventBusError",
    "HandlerExecutionError",
    "MiddlewareExecutionError",
]
