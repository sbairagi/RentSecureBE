from __future__ import annotations

import logging

from django.core.management.base import BaseCommand

from core.events.bus.handlers import ExecutionReport
from core.events.inbox.dispatcher import InboxDispatcher
from shared.type_compat import override

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process pending inbox events."

    @override
    def handle(self, *args: object, **options: object) -> None:
        from core.events.bus.dispatcher import EventBus

        bus = EventBus()
        bus.discover()

        def _default_handler(payload: dict[str, object]) -> ExecutionReport:
            return bus.dispatch_payload(payload)

        dispatcher = InboxDispatcher(handler=_default_handler)
        processed = dispatcher.dispatch()
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} inbox events."))
