# tasks/schedule_reminders.py
import logging
from datetime import datetime, timedelta
from typing import Any

from django.utils.timezone import now

from notification.services.voice_service import generate_voice_note  # nosonar
from notification.services.whatsapp_service import send_whatsapp_audio  # nosonar
from notification.services.whatsapp_service import (
    send_whatsapp_message,  # nosonar; nosonar; nosonar
)

logger = logging.getLogger(__name__)


def get_upcoming_rent_dues() -> Any:
    from properties.models.rent_record_models import RentRecord  # nosonar

    target_date = now().date() + timedelta(days=3)
    return RentRecord.objects.filter(due_date=target_date)


def get_upcoming_tax_dues() -> Any:
    from properties.models.property_tax_models import PropertyTaxRecord

    target_date = now().date() + timedelta(days=3)
    return PropertyTaxRecord.objects.filter(due_date=target_date, paid=False)


def generate_rent_reminder_msg(rent: Any) -> str:

    if rent.renter is None:
        return ""
    name = rent.renter.full_name
    amount = rent.amount
    due = rent.due_date.strftime("%d %B")
    return (
        f"Namaste {name}! Aapka ₹{amount} rent {due} ko due hai. "
        "Kripya samay par jama karein."
    )


def generate_tax_reminder_msg(tax: Any) -> str:

    amount = tax.amount
    due = tax.due_date.strftime("%d %B")
    return f"Kripya dhyaan dein – property tax ₹{amount} {due} tak jama karna hai."


def _safe_lang_for_renter(renter: Any, default: str = "hi") -> str:
    """Best-effort language preference from the renter's linked user profile."""
    user_profile = getattr(getattr(renter, "user", None), "profile", None)
    return getattr(user_profile, "language_preference", None) or default


def _safe_whatsapp(owner: Any) -> str:
    """Best-effort WhatsApp number for an owner (User instance)."""
    return getattr(owner, "whatsapp_number", None) or ""


def _should_send_reminder_for_owner(owner: Any) -> bool:
    """Check if reminders should be sent for this owner now.

    Returns ``True`` if the current time is within the allowed window
    (default ±5 minutes) of the owner's preferred reminder_time,
    or if the owner has no profile/default time.
    """
    try:
        from django.utils.timezone import get_default_timezone, make_aware

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


def _owner_allows_rent_reminders(owner: Any) -> bool:
    """Return True if the owner has rent reminders enabled."""
    try:
        from core.models import UserProfile

        profile = UserProfile.objects.get(user=owner)
        return bool(profile.rent_reminders_enabled)
    except UserProfile.DoesNotExist:
        return True
    except Exception:
        return True


def _send_rent_reminder_for_rent(rent: Any) -> None:
    """Send WhatsApp and optional voice note for a single rent record."""
    if rent.renter is None:
        return
    owner = rent.renter.unit.owner
    if not _should_send_reminder_for_owner(owner):
        return
    if not _owner_allows_rent_reminders(owner):
        return

    phone = rent.renter.whatsapp_number or rent.renter.phone or ""
    lang = _safe_lang_for_renter(rent.renter)
    if not phone:
        return

    from properties.models.renter_models import RentReminderLog

    already_reminded = RentReminderLog.objects.filter(
        renter=rent.renter,
        message_type="DUE",
        sent_at__date=now().date(),
    ).exists()
    if already_reminded:
        return

    msg = generate_rent_reminder_msg(rent)
    try:
        send_whatsapp_message(phone, msg)
    except Exception:
        logger.exception("Failed to send rent reminder text for rent %s", rent.id)

    try:
        audio_path = generate_voice_note(msg, lang)
        if audio_path:
            send_whatsapp_audio(phone, audio_path)
    except OSError:
        logger.exception("Failed to send rent reminder audio for rent %s", rent.id)

    RentReminderLog.objects.create(
        renter=rent.renter,
        message_type="DUE",
    )


def process_rent_reminders() -> None:
    """Send upcoming rent reminders to renters."""
    for rent in get_upcoming_rent_dues():
        _send_rent_reminder_for_rent(rent)


def process_tax_reminders() -> None:
    for tax in get_upcoming_tax_dues():
        owner = tax.property.owner
        if not _should_send_reminder_for_owner(owner):
            continue

        phone = _safe_whatsapp(owner)
        lang = (
            getattr(getattr(owner, "profile", None), "language_preference", None)
            or "hi"
        )
        if not phone:
            continue

        msg = generate_tax_reminder_msg(tax)
        try:
            send_whatsapp_message(phone, msg)
        except Exception:
            logger.exception(
                "Failed to send tax reminder text for tax record %s", tax.id
            )

        try:
            audio_path = generate_voice_note(msg, lang)
            if audio_path:
                send_whatsapp_audio(phone, audio_path)
        except OSError:
            logger.exception(
                "Failed to send tax reminder audio for tax record %s", tax.id
            )


# Step 4: Schedule Cron Job (Every Morning)

# cron: daily at 9AM
# 0 9 * * * /path/to/venv/bin/python /path/to/manage.py runscript schedule_reminders
