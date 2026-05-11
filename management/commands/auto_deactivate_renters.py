# tasks.py or management/commands/auto_deactivate_renters.py

from datetime import date, timedelta

from notification.utils import send_whatsapp_message
from properties.models import Renter
# from yourapp.models import Renter

def auto_deactivate_notice_period_renters():
    today = date.today()
    one_month_ago = today - timedelta(days=30)

    renters = Renter.objects.filter(
        status="notice_period",
        notice_start_date__lte=one_month_ago
    )

    for renter in renters:
        renter.status = "deactivated"
        renter.save()
        print(f"✅ Deactivated renter {renter.name} from unit {renter.unit}")
        send_whatsapp_message(
            renter.unit.owner.whatsapp_number,
            f"ℹ️ Your renter {renter.name} has been auto-deactivated after 1-month notice period."
        )

        # Optional: notify owner via WhatsApp or push


# @periodic_task(run_every=crontab(hour=0, minute=0))
# def run_auto_deactivation():
#     auto_deactivate_notice_period_renters()