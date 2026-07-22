from __future__ import annotations

import re
from dataclasses import dataclass

_PHONE_RE = re.compile(r"^\+[1-9]\d{6,14}$")


@dataclass(frozen=True)
class Phone:
    value: str

    def __post_init__(self) -> None:
        normalized = self._normalize(self.value)
        if not _PHONE_RE.match(normalized):
            raise ValueError(f"Invalid phone number: {self.value}")
        object.__setattr__(self, "value", normalized)

    @staticmethod
    def _normalize(value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if not digits.startswith("+"):
            digits = "+" + digits
        return digits

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Phone):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


__all__ = ["Phone"]
