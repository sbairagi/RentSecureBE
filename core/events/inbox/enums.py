from __future__ import annotations

from core.infrastructure.enums import StringEnum


class InboxEventStatus(StringEnum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


__all__ = ["InboxEventStatus"]
