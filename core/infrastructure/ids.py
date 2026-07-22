from __future__ import annotations

from uuid import UUID


class EntityId(UUID):
    """Base value object for entity identifiers."""

    @classmethod
    def from_string(cls, value: str) -> EntityId:
        try:
            return cls(value)
        except (AttributeError, ValueError) as exc:
            raise ValueError(f"Invalid entity ID: {value}") from exc

    def __str__(self) -> str:
        return UUID.__str__(self)


__all__ = ["EntityId"]
