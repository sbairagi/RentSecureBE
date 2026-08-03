from typing import Any

from django.core.management.base import BaseCommand

from notification.services.schedule_reminders import process_itr_reminders
from rentsecure_be.type_compat import override


class Command(BaseCommand):
    help = (
        "Send monthly ITR reminder WhatsApp messages to property owners, "
        "encouraging them to log rent income and deductions for the current month."
    )

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("Starting monthly ITR reminder job...")
        process_itr_reminders()
        self.stdout.write(self.style.SUCCESS("Monthly ITR reminder job completed."))
