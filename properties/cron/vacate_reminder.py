# cron/vacate_reminder.py

from datetime import timedelta

from django.utils import timezone

from notification.services.notification_service import NotificationService
from properties.models import Renter


def send_vacate_reminders() -> None:
    cutoff_date = timezone.now() - timedelta(days=3)

    renters_to_remind = Renter.objects.filter(
        is_agreement_revoked=True,
        vacated_on__isnull=True,
        revoked_on__lte=cutoff_date,
        status__in=["active", "notice_period"],
    )

    for renter in renters_to_remind:
        if renter.revoked_on is None:
            continue
        owner = renter.property.owner
        message = (
            f"⏰ Reminder: Renter {renter.full_name}'s agreement was revoked on "
            f"{renter.revoked_on.date()}, but the tenant is still marked active.\n"
            f"Please update their status if they've vacated."
        )
        NotificationService().send_whatsapp_message(owner.whatsapp_number, message)
