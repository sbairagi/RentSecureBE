from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from django.db import connection
from django.db.models import F, Q, QuerySet

from core.events.inbox.enums import InboxEventStatus
from core.events.inbox.models import InboxEvent
from core.shared.time import utc_now


class InboxEventRepository:
    def save(self, event: InboxEvent) -> InboxEvent:
        event.full_clean()
        event.save()
        return event

    def save_many(self, events: Sequence[InboxEvent]) -> int:
        InboxEvent.objects.bulk_create(list(events))
        return len(events)

    def exists(self, event_id: uuid.UUID) -> bool:
        return InboxEvent.objects.filter(event_id=event_id).exists()

    def get_by_event_id(self, event_id: uuid.UUID) -> InboxEvent | None:
        return InboxEvent.objects.filter(event_id=event_id).first()

    def pending(
        self, limit: int, before: datetime | None = None
    ) -> QuerySet[InboxEvent]:
        cutoff = before or utc_now()
        queryset = InboxEvent.objects.filter(
            Q(status=InboxEventStatus.RECEIVED)
            | Q(
                status=InboxEventStatus.FAILED,
                next_retry_at__lte=cutoff,
                retry_count__lt=F("max_retry"),
            )
        ).order_by("received_at")[:limit]
        if (
            connection.features.has_select_for_update
            and connection.features.has_select_for_update_skip_locked
        ):
            queryset = queryset.select_for_update(skip_locked=True)
        return queryset

    def mark_processing(self, event_id: uuid.UUID, *, now: datetime) -> int:
        return InboxEvent.objects.filter(id=event_id).update(
            status=InboxEventStatus.PROCESSING,
            updated_at=now,
        )

    def mark_processed(self, event_id: uuid.UUID, *, now: datetime) -> int:
        return InboxEvent.objects.filter(id=event_id).update(
            status=InboxEventStatus.PROCESSED,
            processed_at=now,
            updated_at=now,
        )

    def mark_failed(
        self,
        event_id: uuid.UUID,
        *,
        retry_count: int,
        next_retry_at: datetime,
        last_error: str = "",
        now: datetime,
    ) -> int:
        return InboxEvent.objects.filter(id=event_id).update(
            status=InboxEventStatus.FAILED,
            retry_count=retry_count,
            next_retry_at=next_retry_at,
            last_error=last_error,
            updated_at=now,
        )

    def mark_dead_letter(
        self, event_id: uuid.UUID, *, now: datetime, last_error: str = ""
    ) -> int:
        return InboxEvent.objects.filter(id=event_id).update(
            status=InboxEventStatus.DEAD_LETTER,
            last_error=last_error,
            updated_at=now,
        )

    def cleanup(
        self,
        before: datetime,
        *,
        statuses_to_keep: Sequence[str] | None = None,
    ) -> int:
        keep = set(
            statuses_to_keep
            or [
                InboxEventStatus.RECEIVED,
                InboxEventStatus.PROCESSING,
                InboxEventStatus.FAILED,
                InboxEventStatus.DEAD_LETTER,
            ]
        )
        qs = InboxEvent.objects.filter(created_at__lt=before)
        for status in keep:
            qs = qs.exclude(status=status)
        count, _ = qs.delete()
        return count

    def count(self) -> int:
        return InboxEvent.objects.count()

    def count_pending(self) -> int:
        return InboxEvent.objects.filter(status=InboxEventStatus.RECEIVED).count()


__all__ = ["InboxEventRepository"]
