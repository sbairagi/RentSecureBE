from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass
class Result[T]:
    is_success: bool
    value: T | None = None
    error: str | None = None

    @staticmethod
    def ok(value: T) -> Result[T]:
        return Result(is_success=True, value=value)

    @staticmethod
    def fail(error: str) -> Result[T]:
        return Result(is_success=False, error=error)


__all__ = ["Result"]
