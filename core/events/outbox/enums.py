from __future__ import annotations

from core.infrastructure.enums import StringEnum


class OutboxEventStatus(StringEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


__all__ = ["OutboxEventStatus"]
