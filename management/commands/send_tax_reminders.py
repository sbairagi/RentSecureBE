from typing import Any

from django.core.management.base import BaseCommand

from notification.services.schedule_reminders import process_tax_reminders
from rentsecure_be.type_compat import override


class Command(BaseCommand):
    help = "Send upcoming tax-due reminders to owners via WhatsApp."

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        processed = process_tax_reminders()
        self.stdout.write(
            self.style.SUCCESS(f"✅ Tax reminder job completed. Processed={processed}")
        )
