from __future__ import annotations

from typing import Any

from shared.validators import validate_non_empty_string


def to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def sanitize_phone(phone: str) -> str:
    validate_non_empty_string(phone, "phone")
    return "".join(ch for ch in phone if ch.isdigit() or ch in {"+", "-"})


__all__ = ["to_bool", "sanitize_phone"]
