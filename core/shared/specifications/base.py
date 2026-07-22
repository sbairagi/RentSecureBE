from __future__ import annotations

from typing import Any


class Specification:
    def is_satisfied_by(self, candidate: Any) -> bool:
        raise NotImplementedError

    def __and__(self, other: Specification) -> Specification:
        return AndSpecification(self, other)

    def __or__(self, other: Specification) -> Specification:
        return OrSpecification(self, other)

    def __invert__(self) -> Specification:
        return NotSpecification(self)


class AndSpecification(Specification):
    def __init__(self, left: Specification, right: Specification) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self._left.is_satisfied_by(candidate) and self._right.is_satisfied_by(
            candidate
        )


class OrSpecification(Specification):
    def __init__(self, left: Specification, right: Specification) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self._left.is_satisfied_by(candidate) or self._right.is_satisfied_by(
            candidate
        )


class NotSpecification(Specification):
    def __init__(self, spec: Specification) -> None:
        self._spec = spec

    def is_satisfied_by(self, candidate: Any) -> bool:
        return not self._spec.is_satisfied_by(candidate)


__all__ = [
    "Specification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
]
