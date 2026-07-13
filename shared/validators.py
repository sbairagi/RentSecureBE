from __future__ import annotations

from typing import Any


def validate_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def validate_positive_number(value: Any, field_name: str) -> None:
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{field_name} must be a positive number")


__all__ = ["validate_non_empty_string", "validate_positive_number"]
