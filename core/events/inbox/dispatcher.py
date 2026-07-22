from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from django.db import transaction

from core.config.settings import get_inbox_batch_size
from core.events.bus.handlers import ExecutionReport
from core.events.inbox.constants import (
    BACKOFF_BASE_SECONDS,
    BACKOFF_MAX_SECONDS,
    BACKOFF_MULTIPLIER,
)
from core.events.inbox.models import InboxEvent
from core.events.inbox.repository import InboxEventRepository
from core.shared.time import utc_now

logger = logging.getLogger(__name__)


EventHandler = Callable[[dict[str, Any]], ExecutionReport | None]


class InboxDispatcher:
    def __init__(self, handler: EventHandler) -> None:
        self._handler = handler
        self._repo = InboxEventRepository()
        self._batch_size = get_inbox_batch_size()

    def dispatch(self) -> int:
        now = utc_now()
        dispatched = 0
        while True:
            with transaction.atomic():
                events = list(self._repo.pending(self._batch_size, before=now))
                if not events:
                    break
                self._process_batch(events, now)
                dispatched += len(events)
        return dispatched

    def _process_batch(
        self,
        events: list[InboxEvent],
        now: datetime,
    ) -> None:
        for event in events:
            self._repo.mark_processing(event.id, now=now)
            try:
                enriched_payload = {"event_type": event.event_type, **event.payload}
                report = self._handler(enriched_payload)
            except Exception as exc:
                logger.exception(
                    "Failed to process inbox event %s: %s",
                    event.event_id,
                    exc,
                )
                retry_count = event.retry_count + 1
                if retry_count >= event.max_retry:
                    self._repo.mark_dead_letter(
                        event.id,
                        now=now,
                        last_error=str(exc),
                    )
                else:
                    next_retry = now + timedelta(
                        minutes=min(
                            BACKOFF_BASE_SECONDS
                            * (BACKOFF_MULTIPLIER ** (retry_count - 1)),
                            BACKOFF_MAX_SECONDS,
                        )
                        // 60
                    )
                    self._repo.mark_failed(
                        event.id,
                        retry_count=retry_count,
                        next_retry_at=next_retry,
                        last_error=str(exc),
                        now=now,
                    )
            else:
                if isinstance(report, ExecutionReport) and not report.all_succeeded:
                    logger.exception(
                        "Failed to process inbox event %s: handlers failed",
                        event.event_id,
                    )
                    retry_count = event.retry_count + 1
                    if retry_count >= event.max_retry:
                        self._repo.mark_dead_letter(
                            event.id,
                            now=now,
                            last_error="handlers_failed",
                        )
                    else:
                        next_retry = now + timedelta(
                            minutes=min(
                                BACKOFF_BASE_SECONDS
                                * (BACKOFF_MULTIPLIER ** (retry_count - 1)),
                                BACKOFF_MAX_SECONDS,
                            )
                            // 60
                        )
                        self._repo.mark_failed(
                            event.id,
                            retry_count=retry_count,
                            next_retry_at=next_retry,
                            last_error="handlers_failed",
                            now=now,
                        )
                else:
                    self._repo.mark_processed(event.id, now=now)


__all__ = ["InboxDispatcher"]
