from __future__ import annotations

import uuid

from django.db import models

from core.events.inbox.enums import InboxEventStatus
from shared.type_compat import override

_INBOX_STATUS_CHOICES = [
    (InboxEventStatus.RECEIVED, InboxEventStatus.RECEIVED),
    (InboxEventStatus.PROCESSING, InboxEventStatus.PROCESSING),
    (InboxEventStatus.PROCESSED, InboxEventStatus.PROCESSED),
    (InboxEventStatus.FAILED, InboxEventStatus.FAILED),
    (InboxEventStatus.DEAD_LETTER, InboxEventStatus.DEAD_LETTER),
]


class InboxEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.UUIDField(unique=True, editable=False, default=uuid.uuid4)
    event_type = models.CharField(max_length=255, db_index=True)
    aggregate_id = models.UUIDField(db_index=True)
    aggregate_type = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField()
    headers = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=_INBOX_STATUS_CHOICES,
        default=InboxEventStatus.RECEIVED,
        db_index=True,
    )
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retry = models.PositiveIntegerField(default=6)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "inbox_event"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_id"]),
            models.Index(fields=["status", "received_at"]),
            models.Index(fields=["event_type", "aggregate_id"]),
        ]

    @override
    def __str__(self) -> str:
        return (
            f"{self.aggregate_type}:{self.aggregate_id} "
            f"event={self.event_type} status={self.status}"
        )
