from datetime import date

from rent.models import Renter
from services.rent_reminder_service import send_rent_reminder


def run():
    today = date.today()
    all_renters = Renter.objects.all()

    for renter in all_renters:
        due_day = renter.rent_due_day
        days_left = (date(today.year, today.month, due_day) - today).days

        if days_left in [3, 0, -2]:  # 3 days before, on time, 2 days late
            send_rent_reminder(renter, days_left)
