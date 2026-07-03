from typing import Any

from django.core.management.base import BaseCommand

from notification.services.extra_charge_reminders import send_due_extra_charge_reminders
from rentsecure_be.type_compat import override  # nosonar


class Command(BaseCommand):
    help = "Send WhatsApp and voice reminders for extra charges due today."

    @override
    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--days-ahead",
            type=int,
            default=0,
            help="Send reminders for extra charges due this many days from today.",
        )

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        days_ahead = options["days_ahead"]
        count = send_due_extra_charge_reminders(days_ahead=days_ahead)
        self.stdout.write(
            self.style.SUCCESS(f"Sent reminders for {count} extra charge(s).")
        )
