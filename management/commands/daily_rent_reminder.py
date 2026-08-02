from datetime import date, datetime
from typing import Any

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from core.models import UserProfile
from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import Renter
from rentsecure_be.type_compat import override


class Command(BaseCommand):
    help = "Send daily rent reminders to renters approaching due dates."

    @override
    def add_arguments(self, parser: Any) -> None:
        """No custom arguments needed for this command."""

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        today = date.today()
        all_renters = Renter.objects.all()

        current_time = now()
        for renter in all_renters:
            due_day: int = getattr(renter, "rent_due_day", 1)
            days_left = (date(today.year, today.month, due_day) - today).days

            if days_left not in [3, 0, -2]:
                continue

            owner = renter.unit.owner
            if not self._should_send_reminder(owner, current_time):
                continue

            send_whatsapp_message(
                renter.phone,
                f"Reminder: Your rent is due in {days_left} days.",
            )

    def _should_send_reminder(self, owner: Any, current_time: Any) -> bool:
        try:
            profile = UserProfile.objects.get(user=owner)
            reminder_time = profile.reminder_time
            if reminder_time is None:
                return True
            reminder_dt = datetime.combine(current_time.date(), reminder_time)
            reminder_dt = (
                current_time.tzinfo.localize(reminder_dt)
                if current_time.tzinfo
                else reminder_dt
            )
            diff = abs((current_time - reminder_dt).total_seconds())
            return diff <= 300  # within 5 minutes
        except Exception:
            return True
