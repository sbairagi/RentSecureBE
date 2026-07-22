from __future__ import annotations

import logging
from datetime import datetime, timedelta

from django.core.management import call_command

from core.events.inbox.constants import DEFAULT_RETENTION_DAYS
from core.events.inbox.repository import InboxEventRepository
from core.shared.time import utc_now

logger = logging.getLogger(__name__)


class InboxCleanupService:
    def __init__(self, retention_days: int | None = None) -> None:
        self._repo = InboxEventRepository()
        self._retention_days = retention_days or DEFAULT_RETENTION_DAYS

    def cleanup(self, *, before: datetime | None = None) -> int:
        cutoff = before or (utc_now() - timedelta(days=self._retention_days))
        return self._repo.cleanup(cutoff)

    def run_management_command(self, **kwargs: object) -> None:
        call_command("cleanup_inbox", **kwargs)


__all__ = ["InboxCleanupService"]
