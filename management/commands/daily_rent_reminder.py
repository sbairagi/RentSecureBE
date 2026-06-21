from datetime import date
from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand

from rentsecure_be.type_compat import override


class Command(BaseCommand):
    help = "Send daily rent reminders to renters approaching due dates."

    def add_arguments(self, parser: Any) -> None:
        pass

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        today = date.today()
        Renter = apps.get_model("rent", "Renter")
        all_renters = Renter.objects.all()

        for renter in all_renters:
            if renter is None:
                continue
            due_day = renter.rent_due_day
            days_left = (date(today.year, today.month, due_day) - today).days

            if days_left in [3, 0, -2]:  # 3 days before, on time, 2 days late
                send_rent_reminder = apps.get_app_config(
                    "rent"
                ).module.send_rent_reminder
                send_rent_reminder(renter, days_left)
