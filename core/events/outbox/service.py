from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from django.db.models import Count, F

from core.config.settings import (
    get_outbox_batch_size,
    get_outbox_max_retry,
    get_outbox_retention_days,
)
from core.events.outbox.enums import OutboxEventStatus
from core.events.outbox.exceptions import OutboxDuplicateEventError
from core.events.outbox.models import OutboxEvent
from core.events.outbox.repository import OutboxEventRepository
from core.shared.time import utc_now


class OutboxService:
    def __init__(
        self,
        *,
        batch_size: int | None = None,
        max_retry: int | None = None,
        retention_days: int | None = None,
    ) -> None:
        self._repo = OutboxEventRepository()
        self._batch_size = batch_size or get_outbox_batch_size()
        self._max_retry = max_retry or get_outbox_max_retry()
        self._retention_days = retention_days or get_outbox_retention_days()

    def store_event(
        self,
        *,
        event_id: uuid.UUID,
        aggregate_id: uuid.UUID,
        aggregate_type: str,
        event_type: str,
        payload: dict[str, Any],
        event_version: str = "1.0",
        headers: dict[str, Any] | None = None,
        max_retry: int | None = None,
        published_at: datetime | None = None,
    ) -> OutboxEvent:
        if OutboxEvent.objects.filter(event_id=event_id).exists():
            raise OutboxDuplicateEventError(f"Duplicate event_id: {event_id}")
        return self._repo.save(
            OutboxEvent(
                event_id=event_id,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                event_type=event_type,
                event_version=event_version,
                payload=payload,
                headers=headers or {},
                max_retry=max_retry or self._max_retry,
                published_at=published_at,
            )
        )

    def store_events(
        self,
        events_data: Sequence[dict[str, Any]],
    ) -> int:
        events = []
        for data in events_data:
            events.append(
                OutboxEvent(
                    event_id=data["event_id"],
                    aggregate_id=data["aggregate_id"],
                    aggregate_type=data["aggregate_type"],
                    event_type=data["event_type"],
                    event_version=data.get("event_version", "1.0"),
                    payload=data["payload"],
                    headers=data.get("headers") or {},
                    max_retry=data.get("max_retry") or self._max_retry,
                    published_at=data.get("published_at"),
                )
            )
        existing_ids = set(
            OutboxEvent.objects.filter(
                event_id__in=[e.event_id for e in events]
            ).values_list("event_id", flat=True)
        )
        new_events = [e for e in events if e.event_id not in existing_ids]
        if not new_events:
            return 0
        return self._repo.save_many(new_events)

    def mark_published(
        self, event_id: uuid.UUID, *, now: datetime | None = None
    ) -> int:
        now = now or utc_now()
        return self._repo.mark_published(event_id, now=now)

    def retry_failed(self, limit: int | None = None) -> int:
        failed_events = OutboxEvent.objects.filter(
            status=OutboxEventStatus.FAILED,
            retry_count__lt=F("max_retry"),
        ).order_by("created_at")
        if limit is not None:
            failed_events = failed_events[:limit]
        count = 0
        for event in failed_events.iterator():
            event.status = OutboxEventStatus.PENDING
            event.next_retry_at = None
            event.save(update_fields=["status", "next_retry_at", "updated_at"])
            count += 1
        return count

    def cleanup_old(self, *, before: datetime | None = None) -> int:
        cutoff = before or (utc_now() - timedelta(days=self._retention_days))
        return self._repo.cleanup(cutoff)

    def get_statistics(self) -> dict[str, int]:
        qs = OutboxEvent.objects.values("status").annotate(count=Count("id"))
        result = {item["status"]: item["count"] for item in qs}
        for status in OutboxEventStatus:
            result.setdefault(status, 0)
        return result


__all__ = ["OutboxService"]
