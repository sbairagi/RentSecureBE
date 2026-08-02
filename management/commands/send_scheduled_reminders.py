from typing import Any

from django.core.management.base import BaseCommand

from notification.services.schedule_reminders import (
    process_rent_reminders,
    process_tax_reminders,
)
from rentsecure_be.type_compat import override


class Command(BaseCommand):
    help = (
        "Send scheduled WhatsApp rent and tax reminders to owners and renters "
        "based on each owner's preferred reminder_time."
    )

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("Starting scheduled reminder job...")
        process_rent_reminders()
        process_tax_reminders()
        self.stdout.write(self.style.SUCCESS("Scheduled reminder job completed."))
