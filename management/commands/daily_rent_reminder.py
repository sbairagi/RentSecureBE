from datetime import date
from typing import Any

from django.core.management.base import BaseCommand

from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import Renter
from rentsecure_be.type_compat import override


class Command(BaseCommand):
    help = "Send daily rent reminders to renters approaching due dates."

    @override
    def add_arguments(self, parser: Any) -> None:
        pass

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        today = date.today()
        all_renters = Renter.objects.all()

        for renter in all_renters:
            due_day: int = getattr(renter, "rent_due_day", 1)
            days_left = (date(today.year, today.month, due_day) - today).days

            if days_left in [3, 0, -2]:
                send_whatsapp_message(
                    renter.phone,
                    f"Reminder: Your rent is due in {days_left} days.",
                )
