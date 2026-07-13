from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class BaseDomainEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.occurred_at:
            self.occurred_at = self._now()

    def _now(self) -> str:
        return ""


@dataclass
class EventMetadata:
    correlation_id: str | None = None
    causation_id: str | None = None
    user_id: str | None = None
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "user_id": self.user_id,
            "source": self.source,
        }


__all__ = ["BaseDomainEvent", "EventMetadata"]
