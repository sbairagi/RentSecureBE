from __future__ import annotations

from typing import Any

from shared.domain_events import BaseDomainEvent


class EventSerializer:
    @staticmethod
    def to_dict(event: BaseDomainEvent | dict[str, Any]) -> dict[str, Any]:
        if isinstance(event, BaseDomainEvent):
            if hasattr(event.metadata, "to_dict"):
                metadata = event.metadata.to_dict()
            else:
                metadata = event.metadata
            return {
                "event_id": str(event.event_id),
                "occurred_at": str(event.occurred_at),
                "metadata": metadata,
            }
        return dict(event)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> dict[str, Any]:
        return data


__all__ = ["EventSerializer"]
