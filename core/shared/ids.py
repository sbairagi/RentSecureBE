from __future__ import annotations

import uuid


def new_uuid() -> str:
    return str(uuid.uuid4())


def parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"Invalid UUID: {value}") from exc


def validate_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (AttributeError, ValueError):
        return False


__all__ = [
    "new_uuid",
    "parse_uuid",
    "validate_uuid",
]
