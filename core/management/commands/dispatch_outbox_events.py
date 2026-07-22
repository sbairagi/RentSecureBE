from __future__ import annotations

import logging

from django.core.management.base import BaseCommand

from core.events.bus.handlers import ExecutionReport
from core.events.outbox.dispatcher import OutboxDispatcher
from shared.type_compat import override

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dispatch pending outbox events."

    @override
    def handle(self, *args: object, **options: object) -> None:
        from core.events.bus.dispatcher import EventBus

        bus = EventBus()
        bus.discover()

        def _default_publisher(payload: dict[str, object]) -> ExecutionReport:
            return bus.dispatch_payload(payload)

        dispatcher = OutboxDispatcher(publisher=_default_publisher)
        dispatched = dispatcher.dispatch()
        self.stdout.write(self.style.SUCCESS(f"Dispatched {dispatched} outbox events."))
