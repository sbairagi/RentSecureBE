"""
Compatibility shim for ``typing.override``.

Python 3.12+ provides ``typing.override`` natively; older versions
fall back to a no-op identity decorator so the call works at runtime.
"""

from collections.abc import Callable
from typing import Any, TypeVar

__all__ = ["override"]

try:
    from typing import override as _override
except ImportError:  # pragma: no cover – Python < 3.12 runtime path
    F = TypeVar("F", bound=Callable[..., Any])

    def _override(method: F, /, *args: Any, **kwargs: Any) -> F:  # noqa: UP047
        return method


override = _override
