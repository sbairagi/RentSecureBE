from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from core.events.bus.interfaces import IEventHandler
from core.events.bus.registry import EventHandlerRegistry
from shared.type_compat import override

_registry: EventHandlerRegistry = EventHandlerRegistry()


def get_registry() -> EventHandlerRegistry:
    return _registry


class EventHandler:
    """Wrapper that makes a plain callable conform to IEventHandler."""

    def __init__(self, event_type: type, func: Callable[..., Any]) -> None:
        self._event_type = event_type
        self._func = func
        functools.update_wrapper(self, func)  # type: ignore[arg-type]

    @property
    def event_type(self) -> type:
        return self._event_type

    def execute(self, event: Any) -> Any:
        return self._func(event)

    @override
    def __repr__(self) -> str:
        return f"EventHandler({self._event_type.__name__}, {self._func!r})"


def event_handler(
    event_type: type,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that registers a handler function for the given event type.

    Usage::

        @event_handler(UserCreated)
        def send_welcome_email(event):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        handler = EventHandler(event_type, func)
        _registry.register(event_type, handler)
        func._event_type = event_type
        func._registered = True
        func._handler = handler

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        wrapper._event_type = event_type
        wrapper._registered = True
        wrapper._handler = handler
        return wrapper

    return decorator


def register_handler(
    event_type: type,
    handler: IEventHandler | Callable[..., Any],
) -> None:
    if not isinstance(handler, IEventHandler):
        handler = EventHandler(event_type, handler)
    _registry.register(event_type, handler)


def unregister_handler(
    event_type: type,
    handler: IEventHandler | Callable[..., Any],
) -> None:
    _registry.unregister(event_type, handler)


__all__ = [
    "event_handler",
    "EventHandler",
    "register_handler",
    "unregister_handler",
    "get_registry",
]
