from __future__ import annotations

import logging

from django.core.management.base import BaseCommand

from core.events.inbox.cleanup import InboxCleanupService
from shared.type_compat import override

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clean up old processed inbox events."

    @override
    def handle(self, *args: object, **options: object) -> None:
        service = InboxCleanupService()
        deleted = service.cleanup()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} old inbox events."))
