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
from rentsecure_be.services.message_template_service import (
    get_rent_reminder_msg,
    get_tax_reminder_msg,
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


def generate_rent_reminder_msg(rent: Any, lang: str = "en") -> str:
    """Generate a localized rent reminder message.

    Args:
        rent: Rent record instance.
        lang: Language code for translation.

    Returns:
        Localized reminder message string.
    """
    if rent.renter is None:
        return ""
    return get_rent_reminder_msg(
        name=rent.renter.full_name,
        amount=rent.amount,
        due_date=rent.due_date,
        lang=lang,
    )


def generate_tax_reminder_msg(tax: Any, lang: str = "en") -> str:
    """Generate a localized tax reminder message.

    Args:
        tax: Property tax record instance.
        lang: Language code for translation.

    Returns:
        Localized reminder message string.
    """
    return get_tax_reminder_msg(
        name=getattr(tax.property.owner, "full_name", "Owner"),
        amount=tax.amount,
        due_date=tax.due_date,
        lang=lang,
    )


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

    msg = generate_rent_reminder_msg(rent, lang=lang)
    try:
        send_whatsapp_message(
            phone,
            msg,
            user=rent.renter.user if rent.renter else None,
            rent_record=rent,
        )
    except Exception:
        logger.exception("Failed to send rent reminder text for rent %s", rent.id)

    try:
        audio_path = generate_voice_note(msg, lang)
        if audio_path:
            send_whatsapp_audio(
                phone,
                audio_path,
                user=rent.renter.user if rent.renter else None,
                rent_record=rent,
            )
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

        msg = generate_tax_reminder_msg(tax, lang=lang)
        try:
            send_whatsapp_message(phone, msg, user=owner, rent_record=None)
        except Exception:
            logger.exception(
                "Failed to send tax reminder text for tax record %s", tax.id
            )

        try:
            audio_path = generate_voice_note(msg, lang)
            if audio_path:
                send_whatsapp_audio(phone, audio_path, user=owner, rent_record=None)
        except OSError:
            logger.exception(
                "Failed to send tax reminder audio for tax record %s", tax.id
            )


def process_itr_reminders() -> None:
    """Send monthly ITR reminders to all active owners."""
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    current_month = now().strftime("%B %Y")

    for user in user_model.objects.filter(is_active=True):
        phone = _safe_whatsapp(user)
        if not phone:
            continue

        lang = (
            getattr(getattr(user, "profile", None), "language_preference", None) or "en"
        )

        message = (
            f"📆 Hello {user.first_name or user.get_full_name() or ''}! "
            f"It's time to log your rent income and deductions for {current_month}. "
            f"Stay ITR-ready and save on taxes with RentSecure. 💸"
        )

        try:
            send_whatsapp_message(phone, message, user=user, rent_record=None)
        except Exception:
            logger.exception("Failed to send ITR reminder text for user %s", user.id)

        try:
            audio_path = generate_voice_note(message, lang)
            if audio_path:
                send_whatsapp_audio(phone, audio_path, user=user, rent_record=None)
        except OSError:
            logger.exception("Failed to send ITR reminder audio for user %s", user.id)


# Step 4: Schedule Cron Job (Every Morning)

# cron: daily at 9AM
# 0 9 * * * /path/to/venv/bin/python /path/to/manage.py runscript schedule_reminders
