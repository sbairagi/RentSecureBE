from datetime import date, datetime, timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from core.models import UserProfile
from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import Renter
from rentsecure_be.type_compat import override


class Command(BaseCommand):
    help = "Send rent due reminders to tenants 3 days before due date"

    @override
    def handle(self, *args: Any, **kwargs: Any) -> None:
        today = date.today()
        target_date = today + timedelta(days=3)

        renters = Renter.objects.filter(
            rent_due_date=target_date, status__in=["active", "notice_period"]
        )

        current_time = now()
        for renter in renters:
            if not renter.whatsapp_number or renter.rent_due_date is None:
                continue

            owner = renter.unit.owner
            if not self._should_send_reminder(owner, current_time):
                continue

            msg = f"""📢 *Rent Due Reminder*
Hi {renter.name}, your rent of ₹{renter.rent_amount} for *{renter.property.name}* is due on *{renter.rent_due_date.strftime("%d %B")}*.
Please pay on time to avoid late fees. Thank you! 🙏
"""
            send_whatsapp_message(renter.whatsapp_number, msg)
            self.stdout.write(f"Reminder sent to {renter.name}")

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
