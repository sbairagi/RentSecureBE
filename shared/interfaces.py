from __future__ import annotations

from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class Repository(Protocol[T]):
    def get(self, id: Any) -> T | None: ...

    def list(self, **filters: Any) -> list[T]: ...

    def add(self, entity: T) -> T: ...

    def remove(self, entity: T) -> None: ...


class Service(Protocol):
    def execute(self, *args: Any, **kwargs: Any) -> Any: ...


class EventBus(Protocol):
    def publish(self, event: Any) -> None: ...

    def subscribe(self, event_type: type, handler: Any) -> None: ...


__all__ = ["Repository", "Service", "EventBus"]
