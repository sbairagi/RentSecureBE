"""
Compatibility shim for ``typing.override``.

Python 3.12+ provides ``typing.override`` natively; older versions
fall back to ``typing_extensions`` or a no-op identity decorator so
the call works at runtime.
"""

from collections.abc import Callable
from typing import Any, TypeVar

__all__ = ["override"]

try:
    from typing import override
except ImportError:
    try:
        from typing_extensions import override  # noqa: UP035
    except ImportError:
        F = TypeVar("F", bound=Callable[..., Any])

        def override(method: F, /) -> F:  # noqa: UP047
            return method
