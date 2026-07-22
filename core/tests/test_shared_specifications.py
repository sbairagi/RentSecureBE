from __future__ import annotations

from core.shared.specifications.base import Specification


class EvenSpecification(Specification):
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate % 2 == 0


class GreaterThanSpecification(Specification):
    def __init__(self, threshold: int) -> None:
        self._threshold = threshold

    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate > self._threshold


class TestSpecification:
    def test_even_specification(self):
        spec = EvenSpecification()
        assert spec.is_satisfied_by(2) is True
        assert spec.is_satisfied_by(3) is False

    def test_and_specification(self):
        even = EvenSpecification()
        greater = GreaterThanSpecification(5)
        combined: Specification = even & greater
        assert combined.is_satisfied_by(6) is True
        assert combined.is_satisfied_by(4) is False
        assert combined.is_satisfied_by(7) is False

    def test_or_specification(self):
        even = EvenSpecification()
        greater = GreaterThanSpecification(5)
        combined: Specification = even | greater
        assert combined.is_satisfied_by(1) is False
        assert combined.is_satisfied_by(3) is False
        assert combined.is_satisfied_by(6) is True
        assert combined.is_satisfied_by(7) is True

    def test_not_specification(self):
        even = EvenSpecification()
        not_even: Specification = ~even
        assert not_even.is_satisfied_by(3) is True
        assert not_even.is_satisfied_by(2) is False

    def test_complex_combination(self):
        even = EvenSpecification()
        greater = GreaterThanSpecification(3)
        spec = ~(even & greater)
        assert spec.is_satisfied_by(4) is False
        assert spec.is_satisfied_by(3) is True
        assert spec.is_satisfied_by(7) is True
