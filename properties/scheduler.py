# services/scheduler.py

from django_celery_beat.models import PeriodicTask

from notification.services.voice_note_service import (
    alert_owner_about_delay,
    send_late_rent_reminder,
)


def cancel_reminder_job(task_id: str):
    try:
        task = PeriodicTask.objects.get(name=task_id)
        task.delete()
    except PeriodicTask.DoesNotExist:
        pass


from django.utils.timezone import now

from .models import RentRecord


def get_late_rent_records():
    today = now().date()
    return RentRecord.objects.filter(
        due_date__lt=today,
        payment_status="UNPAID",
        reminder_sent=False  # Prevent repeat reminders
    )

def process_late_rent_followups():
    for rent in get_late_rent_records():
        send_late_rent_reminder(rent)
        alert_owner_about_delay(rent)

        # Example: Increment "late_count" for renter
        rent.renter.late_payment_count += 1
        rent.renter.save()

