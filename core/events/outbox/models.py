from __future__ import annotations

import uuid

from django.db import models

from core.events.outbox.enums import OutboxEventStatus
from shared.type_compat import override

_OUTBOX_STATUS_CHOICES = [
    (OutboxEventStatus.PENDING, OutboxEventStatus.PENDING),
    (OutboxEventStatus.PROCESSING, OutboxEventStatus.PROCESSING),
    (OutboxEventStatus.PUBLISHED, OutboxEventStatus.PUBLISHED),
    (OutboxEventStatus.FAILED, OutboxEventStatus.FAILED),
    (OutboxEventStatus.DEAD_LETTER, OutboxEventStatus.DEAD_LETTER),
]


class OutboxEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    aggregate_id = models.UUIDField(db_index=True)
    aggregate_type = models.CharField(max_length=100, db_index=True)
    event_type = models.CharField(max_length=255, db_index=True)
    event_version = models.CharField(max_length=20, default="1.0")
    payload = models.JSONField()
    headers = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=_OUTBOX_STATUS_CHOICES,
        default=OutboxEventStatus.PENDING,
        db_index=True,
    )
    retry_count = models.PositiveIntegerField(default=0)
    max_retry = models.PositiveIntegerField(default=6)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "outbox_event"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "next_retry_at"]),
            models.Index(fields=["aggregate_id", "event_type"]),
        ]

    @override
    def __str__(self) -> str:
        return (
            f"{self.aggregate_type}:{self.aggregate_id} "
            f"event={self.event_type} status={self.status}"
        )
