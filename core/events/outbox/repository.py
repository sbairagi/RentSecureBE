from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from django.db import connection
from django.db.models import F, Q, QuerySet

from core.events.outbox.enums import OutboxEventStatus
from core.events.outbox.models import OutboxEvent
from core.shared.time import utc_now


class OutboxEventRepository:
    def save(self, event: OutboxEvent) -> OutboxEvent:
        event.full_clean()
        event.save()
        return event

    def save_many(self, events: Sequence[OutboxEvent]) -> int:
        OutboxEvent.objects.bulk_create(list(events))
        return len(events)

    def get_pending(
        self,
        limit: int,
        before: datetime | None = None,
    ) -> QuerySet[OutboxEvent]:
        cutoff = before or utc_now()
        queryset = OutboxEvent.objects.filter(
            Q(status=OutboxEventStatus.PENDING)
            | Q(
                status=OutboxEventStatus.FAILED,
                next_retry_at__lte=cutoff,
                retry_count__lt=F("max_retry"),
            )
        ).order_by("created_at")[:limit]
        if (
            connection.features.has_select_for_update
            and connection.features.has_select_for_update_skip_locked
        ):
            queryset = queryset.select_for_update(skip_locked=True)
        return queryset

    def mark_processing(self, event_id: uuid.UUID, *, now: datetime) -> int:
        return OutboxEvent.objects.filter(id=event_id).update(
            status=OutboxEventStatus.PROCESSING,
            updated_at=now,
        )

    def mark_published(self, event_id: uuid.UUID, *, now: datetime) -> int:
        return OutboxEvent.objects.filter(id=event_id).update(
            status=OutboxEventStatus.PUBLISHED,
            published_at=now,
            updated_at=now,
        )

    def mark_failed(
        self,
        event_id: uuid.UUID,
        *,
        retry_count: int,
        next_retry_at: datetime,
        now: datetime,
    ) -> int:
        return OutboxEvent.objects.filter(id=event_id).update(
            status=OutboxEventStatus.FAILED,
            retry_count=retry_count,
            next_retry_at=next_retry_at,
            updated_at=now,
        )

    def mark_dead(self, event_id: uuid.UUID, *, now: datetime) -> int:
        return OutboxEvent.objects.filter(id=event_id).update(
            status=OutboxEventStatus.DEAD_LETTER,
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
                OutboxEventStatus.PENDING,
                OutboxEventStatus.PROCESSING,
                OutboxEventStatus.FAILED,
                OutboxEventStatus.DEAD_LETTER,
            ]
        )
        qs = OutboxEvent.objects.filter(created_at__lt=before)
        for status in keep:
            qs = qs.exclude(status=status)
        count, _ = qs.delete()
        return count

    def count_pending(self) -> int:
        return OutboxEvent.objects.filter(status=OutboxEventStatus.PENDING).count()
