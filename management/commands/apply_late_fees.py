# management/commands/apply_late_fees.py
from datetime import timedelta
from django.core.management.base import BaseCommand
from rent.models import RentRecord
from django.utils.timezone import now
from decimal import Decimal
from services.whatsapp_service import send_whatsapp_message

class Command(BaseCommand):
    help = 'Apply late fee to unpaid rents after due date and send reminders'

    def handle(self, *args, **kwargs):
        today = now().date()
        grace_days = 3
        late_fee_amount = Decimal('300.00')

        overdue_rents = RentRecord.objects.filter(
            payment_status='DUE',
            late_fee=0,
            due_date__lt=today - timedelta(days=grace_days)
        )

        for rent in overdue_rents:
            property = rent.renter.property
            due_with_grace = rent.due_date + timedelta(days=property.grace_days)

            if today > due_with_grace:
                rent.late_fee = property.late_fee_amount
                rent.save()

                # WhatsApp message
                message = (
                    f"⚠️ Your rent of ₹{rent.amount} for {property.title} is overdue.\n"
                    f"A late fee of ₹{rent.late_fee} has been applied.\n"
                    f"Pay ASAP: {rent.payment_link or 'App'}"
                )
                send_whatsapp_message(rent.renter.phone, message)

        # for rent in overdue_rents:
        #     rent.late_fee = late_fee_amount
        #     rent.save()

        #     renter = rent.renter
        #     phone = renter.phone

        #     message = f"⚠️ Your rent of ₹{rent.amount} is overdue. A late fee of ₹{late_fee_amount} has been applied. Please pay ASAP to avoid further action.\nPay here: {rent.payment_link or 'App'}"

        #     send_whatsapp_message(phone, message)

        self.stdout.write(self.style.SUCCESS(f'Late fees applied to {overdue_rents.count()} rent records.'))


# 0 2 * * * /path/to/venv/bin/python /path/to/manage.py apply_late_fees