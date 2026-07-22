from __future__ import annotations

import importlib
import threading
from collections.abc import Callable
from typing import Any, TypeVar

from django.conf import settings

from core.events.bus.interfaces import IEventHandler

T = TypeVar("T")


class EventHandlerRegistry:
    """Thread-safe registry mapping event types to ordered handler lists."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[IEventHandler | Callable[..., Any]]] = {}
        self._lock = threading.RLock()

    def register(
        self, event_type: type, handler: IEventHandler | Callable[..., Any]
    ) -> None:
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)

    def unregister(
        self, event_type: type, handler: IEventHandler | Callable[..., Any]
    ) -> None:
        with self._lock:
            if event_type in self._handlers:
                self._handlers[event_type] = [
                    h for h in self._handlers[event_type] if h is not handler
                ]
                if not self._handlers[event_type]:
                    del self._handlers[event_type]

    def get_handlers(
        self, event_type: type
    ) -> list[IEventHandler | Callable[..., Any]]:
        with self._lock:
            return list(self._handlers.get(event_type, []))

    def clear(self) -> None:
        with self._lock:
            self._handlers.clear()

    def reset(self) -> None:
        self.clear()

    def discover(self) -> int:
        discovered = 0
        for app_name in getattr(settings, "INSTALLED_APPS", []):
            handlers_module = f"{app_name}.bus.handlers"
            try:
                module = importlib.import_module(handlers_module)
            except ImportError:
                continue
            for attr_name in dir(module):
                if attr_name.startswith("_"):
                    continue
                attr = getattr(module, attr_name)
                if callable(attr) and hasattr(attr, "_event_type"):
                    if not hasattr(attr, "_registered") or not attr._registered:
                        event_type = attr._event_type
                        self.register(event_type, attr)
                        try:
                            attr._registered = True
                        except (AttributeError, TypeError):
                            pass
                        discovered += 1
        return discovered

    def all_registered_types(self) -> dict[type, list[Any]]:
        with self._lock:
            return {k: list(v) for k, v in self._handlers.items()}


__all__ = ["EventHandlerRegistry"]
