from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from django.db import transaction

from core.config.settings import get_outbox_batch_size
from core.events.bus.handlers import ExecutionReport
from core.events.outbox.constants import (
    BACKOFF_BASE_SECONDS,
    BACKOFF_MAX_SECONDS,
    BACKOFF_MULTIPLIER,
)
from core.events.outbox.models import OutboxEvent
from core.events.outbox.repository import OutboxEventRepository
from core.shared.time import utc_now

logger = logging.getLogger(__name__)


DispatchPublisher = Callable[[dict[str, Any]], ExecutionReport | None]


class OutboxDispatcher:
    def __init__(self, publisher: DispatchPublisher) -> None:
        self._publisher = publisher
        self._repo = OutboxEventRepository()
        self._batch_size = get_outbox_batch_size()

    def dispatch(self) -> int:
        now = utc_now()
        dispatched = 0
        while True:
            with transaction.atomic():
                events = list(self._repo.get_pending(self._batch_size, before=now))
                if not events:
                    break
                self._process_batch(events, now)
                dispatched += len(events)
        return dispatched

    def _process_batch(
        self,
        events: list[OutboxEvent],
        now: datetime,
    ) -> None:
        for event in events:
            self._repo.mark_processing(event.id, now=now)
            try:
                enriched_payload = {"event_type": event.event_type, **event.payload}
                report = self._publisher(enriched_payload)
            except Exception as exc:
                logger.exception(
                    "Failed to publish outbox event %s: %s",
                    event.event_id,
                    exc,
                )
                retry_count = event.retry_count + 1
                if retry_count >= event.max_retry:
                    self._repo.mark_dead(event.id, now=now)
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
                        now=now,
                    )
            else:
                if isinstance(report, ExecutionReport) and not report.all_succeeded:
                    logger.exception(
                        "Failed to publish outbox event %s: handlers failed",
                        event.event_id,
                    )
                    retry_count = event.retry_count + 1
                    if retry_count >= event.max_retry:
                        self._repo.mark_dead(event.id, now=now)
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
                            now=now,
                        )
                else:
                    self._repo.mark_published(event.id, now=now)
