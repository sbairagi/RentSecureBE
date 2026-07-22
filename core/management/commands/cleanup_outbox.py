from __future__ import annotations

import logging

from django.core.management.base import BaseCommand

from core.events.outbox.cleanup import OutboxCleanupService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clean up old published outbox events."

    def handle(self, *args: object, **options: object) -> None:
        service = OutboxCleanupService()
        deleted = service.cleanup()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} old outbox events."))
