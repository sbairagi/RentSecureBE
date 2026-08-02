"""Late-rent scheduler helpers.

Pure service layer for finding overdue rent records and triggering
notifications. Designed to be called from Celery beat tasks.

Dedup strategy:
  ``RentRecord`` has no ``reminder_sent`` flag. We use
  :class:`properties.models.RentReminderLog` as the source of truth:
  a renter who has already received a ``LATE`` reminder today is
  skipped on subsequent polls, so the cron never spams the same
  renter with the same reminder twice in 24 h.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from django_celery_beat.models import PeriodicTask  # type: ignore[import-untyped]

from django.db.models import QuerySet
from django.utils.timezone import get_default_timezone, make_aware, now

from notification.services.voice_note_service import (
    alert_owner_about_delay,
    send_late_rent_reminder,
)

from .models import RentRecord, RentReminderLog

if TYPE_CHECKING:
    pass  # RentRecord and queryset types are already concrete.


def cancel_reminder_job(task_id: str) -> bool:
    """Cancel a Celery beat task by name.

    Args:
        task_id: The ``PeriodicTask.name`` to cancel.

    Returns:
        ``True`` if the task existed and was deleted, ``False`` otherwise.
    """
    deleted: bool = False
    try:
        task: PeriodicTask = PeriodicTask.objects.get(name=task_id)
        task.delete()
        deleted = True
    except PeriodicTask.DoesNotExist:
        deleted = False
    return deleted


def get_late_rent_records() -> QuerySet[RentRecord]:
    """Return overdue rent records that have not yet been reminded today.

    A renter who already received a ``LATE`` reminder in the last 24
    hours is excluded via :class:`RentReminderLog`.
    """
    today = now().date()
    day_start = now() - timedelta(hours=24)

    already_reminded_renter_ids: set[int] = set(
        RentReminderLog.objects.filter(
            message_type="LATE",
            sent_at__gte=day_start,
        ).values_list("renter_id", flat=True)
    )

    return RentRecord.objects.filter(
        due_date__lt=today,
        status="PENDING",
    ).exclude(renter_id__in=already_reminded_renter_ids)


def _should_send_reminder(owner: Any) -> bool:
    """Check if reminders should be sent for this owner now.

    Returns ``True`` if the current time is within the allowed window
    (default ±5 minutes) of the owner's preferred
    :attr:`reminder_time`, or if the owner has no profile/default time.
    """
    try:
        from core.models import UserProfile

        profile = UserProfile.objects.get(user=owner)
        reminder_time = profile.reminder_time
        if reminder_time is None:
            return True
        current_time = now()
        reminder_dt = datetime.combine(current_time.date(), reminder_time)
        reminder_dt = make_aware(reminder_dt, get_default_timezone())
        diff = abs((current_time - reminder_dt).total_seconds())
        return diff <= 300  # within 5 minutes
    except Exception:
        return True


def process_late_rent_followups() -> int:
    """Send late-rent notifications and bump the renter's late count.

    Respects each owner's :attr:`core.models.UserProfile.reminder_time`
    setting: reminders are only sent when the current time matches the
    owner's preferred reminder time.

    Returns the number of renters processed.
    """
    processed = 0
    for rent in get_late_rent_records():
        if rent.renter is not None:
            owner = rent.renter.unit.owner
            if not _should_send_reminder(owner):
                continue
        send_late_rent_reminder(rent)
        alert_owner_about_delay(rent)
        if rent.renter is not None:
            rent.renter.late_payment_count += 1
            rent.renter.save()
        processed += 1
    return processed
