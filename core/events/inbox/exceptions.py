from __future__ import annotations

from core.infrastructure.exceptions import InfrastructureError


class InboxError(InfrastructureError):
    """Base exception for inbox failures."""


class InboxEventNotFoundError(InboxError):
    """Raised when an expected inbox event is missing."""


class InboxDuplicateEventError(InboxError):
    """Raised when a duplicate event_id is detected."""


__all__ = [
    "InboxError",
    "InboxEventNotFoundError",
    "InboxDuplicateEventError",
]
