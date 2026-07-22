from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar

T = TypeVar("T")


@dataclass
class PageRequest[T]:
    page: int = 1
    page_size: int = 20
    filters: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = 1
        if self.page_size > 100:
            self.page_size = 100


@dataclass
class PageResponse[T]:
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.total == 0:
            return 0
        return max(1, (self.total + self.page_size - 1) // self.page_size)

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1


__all__ = ["PageRequest", "PageResponse"]
