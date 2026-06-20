from datetime import date

from django.apps import apps

from core.utils.export_utils import get_model


def run() -> None:
    today = date.today()
    Renter = get_model("rent", "Renter")
    all_renters = Renter.objects.all()

    for renter in all_renters:
        due_day = renter.rent_due_day
        days_left = (date(today.year, today.month, due_day) - today).days

        if days_left in [3, 0, -2]:  # 3 days before, on time, 2 days late
            send_rent_reminder = apps.get_app_config("rent").module.send_rent_reminder
            send_rent_reminder(renter, days_left)
