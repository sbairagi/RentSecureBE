from __future__ import annotations

from abc import abstractmethod
from typing import Any, TypeVar

T = TypeVar("T")


class IRepository[T]:
    @abstractmethod
    def get(self, id: Any) -> T | None: ...

    @abstractmethod
    def list(self, **filters: Any) -> list[T]: ...

    @abstractmethod
    def add(self, entity: T) -> T: ...

    @abstractmethod
    def remove(self, entity: T) -> None: ...


__all__ = ["IRepository"]
