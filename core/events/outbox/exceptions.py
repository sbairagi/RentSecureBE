from __future__ import annotations

from core.infrastructure.exceptions import InfrastructureError


class OutboxError(InfrastructureError):
    """Base exception for outbox failures."""


class OutboxEventNotFoundError(OutboxError):
    """Raised when an expected outbox event is missing."""


class OutboxDuplicateEventError(OutboxError):
    """Raised when a duplicate event_id is detected."""


__all__ = [
    "OutboxError",
    "OutboxEventNotFoundError",
    "OutboxDuplicateEventError",
]
