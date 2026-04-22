# cron/flag_defaulters.py

from datetime import timezone
from properties.models import RentRecord
from properties.signals import update_renter_defaulter_status


def flag_repeat_defaulters():
    overdue_rents = RentRecord.objects.filter(status="UNPAID", due_date__lt=timezone.now().date())
    for rent in overdue_rents:
        update_renter_defaulter_status(rent)