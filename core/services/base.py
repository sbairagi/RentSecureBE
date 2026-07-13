from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class ServiceError:
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceResult[T]:
    success: bool
    data: T | None = None
    error: ServiceError | None = None

    @classmethod
    def ok(cls, data: T) -> ServiceResult[T]:
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, code: str, message: str, **details: Any) -> ServiceResult[T]:
        return cls(
            success=False,
            error=ServiceError(code=code, message=message, details=details),
        )


class BaseService:
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError
