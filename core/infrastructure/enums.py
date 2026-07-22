from __future__ import annotations

from enum import Enum, StrEnum


class StringEnum(StrEnum):
    """Base enum for string-based choices."""


class IntEnum(int, Enum):
    """Base enum for integer-based choices."""


__all__ = ["StringEnum", "IntEnum"]
