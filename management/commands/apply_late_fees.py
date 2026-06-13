"""Apply late fees to overdue rent records.

This management command walks all overdue rent records past their
grace window and applies a late fee. Only fields that exist on the
canonical :class:`properties.models.RentRecord` model are used.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import RentRecord

# Default grace window used for late-fee calculation. The previous
# implementation tried to read ``property.grace_days`` and
# ``property.late_fee_amount`` from a related Building; neither
# attribute exists on Building. The grace window is therefore
# defined here as a constant.
DEFAULT_GRACE_DAYS = 3


class Command(BaseCommand):
    help = "Apply late fee to unpaid rents after due date and send reminders"

    def handle(self, *args, **kwargs) -> None:
        today = now().date()
        grace_days = DEFAULT_GRACE_DAYS

        overdue_rents = RentRecord.objects.filter(
            payment_status="PENDING",
            late_fee=0,
            rent_due_date__lt=today - timedelta(days=grace_days),
        )

        processed = 0
        for rent in overdue_rents:
            # Use the per-record grace_days if the owner customised it
            # on a specific rent record; otherwise fall back to the
            # command-level default. There is no ``property.grace_days``.
            record_grace = getattr(rent, "grace_days", grace_days) or grace_days
            due_with_grace = rent.rent_due_date + timedelta(days=record_grace)

            if today <= due_with_grace:
                continue

            rent.late_fee = Decimal("100.00")
            rent.save(update_fields=["late_fee"])
            processed += 1

            # WhatsApp notification to the renter
            renter = rent.renter
            message = (
                f"⚠️ Your rent of ₹{rent.amount_paid} for {renter.unit.unit} "
                f"is overdue.\nA late fee of ₹{rent.late_fee} has been applied.\n"
                f"Pay ASAP: {rent.payment_link or 'App'}"
            )
            send_whatsapp_message(renter.phone, message)

        self.stdout.write(
            self.style.SUCCESS(
                f"Late fees applied to {processed} rent records."
            )
        )


# 0 2 * * * /path/to/venv/bin/python /path/to/manage.py apply_late_fees
