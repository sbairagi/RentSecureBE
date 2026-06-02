# cron/vacate_reminder.py

from datetime import timedelta

from communication.utils import send_whatsapp_message
from django.utils import timezone

from properties.models import Renter

# from renters.models import Renter
# from services.whatsapp_service import send_whatsapp_message


def send_vacate_reminders():
    cutoff_date = timezone.now() - timedelta(days=3)

    renters_to_remind = Renter.objects.filter(
        is_agreement_revoked=True,
        vacated_on__isnull=True,
        revoked_on__lte=cutoff_date,
        status__in=["active", "notice_period"],
    )

    for renter in renters_to_remind:
        owner = renter.property.owner
        message = (
            f"⏰ Reminder: Renter {renter.full_name}'s agreement was revoked on "
            f"{renter.revoked_on.date()}, but the tenant is still marked active.\n"
            f"Please update their status if they’ve vacated."
        )
        send_whatsapp_message(owner.profile.whatsapp_number, message)
