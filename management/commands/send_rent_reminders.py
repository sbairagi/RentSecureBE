from datetime import date, timedelta

from django.core.management.base import BaseCommand
from rent.models import Renter

from notification.services.whatsapp_service import send_whatsapp_message


class Command(BaseCommand):
    help = "Send rent due reminders to tenants 3 days before due date"

    def handle(self, *args, **kwargs):
        today = date.today()
        target_date = today + timedelta(days=3)

        renters = Renter.objects.filter(
            rent_due_date=target_date, status__in=["active", "notice_period"]
        )

        for renter in renters:
            if not renter.whatsapp_number:
                continue

            msg = f"""📢 *Rent Due Reminder*
Hi {renter.name}, your rent of ₹{renter.rent_amount} for *{renter.property.name}* is due on *{renter.rent_due_date.strftime('%d %B')}*.
Please pay on time to avoid late fees. Thank you! 🙏
"""
            send_whatsapp_message(renter.whatsapp_number, msg)
            self.stdout.write(f"Reminder sent to {renter.name}")
