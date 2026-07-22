from __future__ import annotations

from typing import Any, Protocol, TypeVar

from core.shared.repositories.base import IRepository

T = TypeVar("T")

Repository = IRepository


class Service(Protocol):
    def execute(self, *args: Any, **kwargs: Any) -> Any: ...


class EventBus(Protocol):
    def publish(self, event: Any) -> None: ...

    def subscribe(self, event_type: type, handler: Any) -> None: ...


__all__ = ["Repository", "Service", "EventBus"]
