from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from django.db.models import Count, F

from core.config.settings import (
    get_inbox_batch_size,
    get_inbox_max_retry,
    get_inbox_retention_days,
)
from core.events.inbox.enums import InboxEventStatus
from core.events.inbox.models import InboxEvent
from core.events.inbox.repository import InboxEventRepository
from core.shared.time import utc_now


class InboxService:
    def __init__(
        self,
        *,
        batch_size: int | None = None,
        max_retry: int | None = None,
        retention_days: int | None = None,
    ) -> None:
        self._repo = InboxEventRepository()
        self._batch_size = batch_size or get_inbox_batch_size()
        self._max_retry = max_retry or get_inbox_max_retry()
        self._retention_days = retention_days or get_inbox_retention_days()

    def receive_event(
        self,
        *,
        event_id: uuid.UUID,
        event_type: str,
        aggregate_id: uuid.UUID,
        aggregate_type: str,
        payload: dict[str, Any],
        headers: dict[str, Any] | None = None,
        max_retry: int | None = None,
    ) -> InboxEvent:
        existing = self._repo.get_by_event_id(event_id)
        if existing is not None:
            return existing
        return self._repo.save(
            InboxEvent(
                event_id=event_id,
                event_type=event_type,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                payload=payload,
                headers=headers or {},
                max_retry=max_retry or self._max_retry,
            )
        )

    def receive_many(
        self,
        events_data: Sequence[dict[str, Any]],
    ) -> list[InboxEvent]:
        received: list[InboxEvent] = []
        for data in events_data:
            event = self.receive_event(
                event_id=data["event_id"],
                event_type=data["event_type"],
                aggregate_id=data["aggregate_id"],
                aggregate_type=data["aggregate_type"],
                payload=data["payload"],
                headers=data.get("headers") or {},
                max_retry=data.get("max_retry"),
            )
            received.append(event)
        return received

    def process_event(
        self,
        event_id: uuid.UUID,
        *,
        now: datetime | None = None,
    ) -> InboxEvent | None:
        now = now or utc_now()
        event = InboxEvent.objects.select_for_update().get(id=event_id)
        if event.status in (
            InboxEventStatus.PROCESSED,
            InboxEventStatus.PROCESSING,
        ):
            return event
        self._repo.mark_processing(event.id, now=now)
        event.refresh_from_db()
        return event

    def mark_processed(
        self, event_id: uuid.UUID, *, now: datetime | None = None
    ) -> int:
        now = now or utc_now()
        return self._repo.mark_processed(event_id, now=now)

    def retry(self, limit: int | None = None) -> int:
        failed_events = InboxEvent.objects.filter(
            status=InboxEventStatus.FAILED,
            retry_count__lt=F("max_retry"),
        ).order_by("received_at")
        if limit is not None:
            failed_events = failed_events[:limit]
        count = 0
        for event in failed_events.iterator():
            event.status = InboxEventStatus.RECEIVED
            event.next_retry_at = None
            event.save(update_fields=["status", "next_retry_at", "updated_at"])
            count += 1
        return count

    def mark_failed(
        self,
        event_id: uuid.UUID,
        *,
        retry_count: int,
        next_retry_at: datetime,
        last_error: str = "",
        now: datetime | None = None,
    ) -> int:
        now = now or utc_now()
        return self._repo.mark_failed(
            event_id,
            retry_count=retry_count,
            next_retry_at=next_retry_at,
            last_error=last_error,
            now=now,
        )

    def mark_dead_letter(
        self,
        event_id: uuid.UUID,
        *,
        last_error: str = "",
        now: datetime | None = None,
    ) -> int:
        now = now or utc_now()
        return self._repo.mark_dead_letter(event_id, now=now, last_error=last_error)

    def cleanup(self, *, before: datetime | None = None) -> int:
        cutoff = before or (utc_now() - timedelta(days=self._retention_days))
        return self._repo.cleanup(cutoff)

    def statistics(self) -> dict[str, int]:
        qs = InboxEvent.objects.values("status").annotate(count=Count("id"))
        result = {item["status"]: item["count"] for item in qs}
        for status in InboxEventStatus:
            result.setdefault(status, 0)
        return result

    def count(self) -> int:
        return self._repo.count()


__all__ = ["InboxService"]
