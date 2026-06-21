# cron/flag_defaulters.py

from django.utils import timezone

from properties.models import RentRecord
from properties.signals import update_renter_defaulter_status


def flag_repeat_defaulters() -> None:
    overdue_rents = RentRecord.objects.filter(
        payout_status="PENDING", due_date__lt=timezone.now().date()
    )
    for rent in overdue_rents:
        update_renter_defaulter_status(rent)
