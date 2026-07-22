from __future__ import annotations

import logging
import uuid
from typing import Any

from django.db import transaction

from core.events.outbox.exceptions import OutboxDuplicateEventError
from core.events.outbox.service import OutboxService

logger = logging.getLogger(__name__)


class DomainEventPublisher:
    _instance: DomainEventPublisher | None = None

    def __init__(self, outbox_service: OutboxService | None = None) -> None:
        self._outbox = outbox_service or OutboxService()

    @classmethod
    def get_instance(cls) -> DomainEventPublisher:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def publish(self, event: Any) -> None:
        try:
            event_id = uuid.UUID(str(event.event_id))
        except (ValueError, TypeError) as exc:
            logger.error("Invalid event_id for domain event: %s", exc)
            return

        aggregate_id = getattr(event, "aggregate_id", None)
        if aggregate_id is None:
            logger.error("Domain event missing aggregate_id: %s", type(event).__name__)
            return

        aggregate_type = getattr(event, "aggregate_type", type(event).__name__)
        event_type = type(event).__name__
        event_version = getattr(event, "version", "1.0")
        payload = {**event.to_payload(), "event_type": event_type}

        def _store() -> None:
            try:
                self._outbox.store_event(
                    event_id=event_id,
                    aggregate_id=aggregate_id,
                    aggregate_type=aggregate_type,
                    event_type=event_type,
                    payload=payload,
                    event_version=str(event_version),
                    headers={"source": "domain_event_publisher"},
                )
            except OutboxDuplicateEventError:
                logger.debug("Duplicate domain event suppressed: %s", event_id)

        transaction.on_commit(_store)


__all__ = ["DomainEventPublisher"]
