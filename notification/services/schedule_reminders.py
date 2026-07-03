# tasks/schedule_reminders.py
import logging
from datetime import timedelta
from typing import Any

from django.utils.timezone import now

from notification.services.voice_service import generate_voice_note
from notification.services.whatsapp_service import send_whatsapp_audio
from properties.models import PropertyTaxRecord, RentRecord

logger = logging.getLogger(__name__)


def get_upcoming_rent_dues() -> Any:
    target_date = now().date() + timedelta(days=3)
    return RentRecord.objects.filter(due_date=target_date)


def get_upcoming_tax_dues() -> Any:
    target_date = now().date() + timedelta(days=3)
    return PropertyTaxRecord.objects.filter(due_date=target_date, paid=False)


def generate_rent_reminder_msg(rent: RentRecord) -> str:
    if rent.renter is None:
        return ""
    name = rent.renter.full_name
    amount = rent.amount
    due = rent.due_date.strftime("%d %B")
    return (
        f"Namaste {name}! Aapka ₹{amount} rent {due} ko due hai. "
        "Kripya samay par jama karein."
    )


def generate_tax_reminder_msg(tax: PropertyTaxRecord) -> str:
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


def process_rent_reminders() -> None:
    for rent in get_upcoming_rent_dues():
        phone = rent.renter.whatsapp_number or rent.renter.phone or ""
        lang = _safe_lang_for_renter(rent.renter)
        if phone:
            msg = generate_rent_reminder_msg(rent)
            try:
                audio_path = generate_voice_note(msg, lang)
                send_whatsapp_audio(phone, audio_path)
            except Exception:
                logger.exception(
                    "Failed to send rent reminder for rent %s: %s", rent.id
                )


def process_tax_reminders() -> None:
    for tax in get_upcoming_tax_dues():
        owner = tax.property.owner
        phone = _safe_whatsapp(owner)
        lang = (
            getattr(getattr(owner, "profile", None), "language_preference", None)
            or "hi"
        )
        if phone:
            msg = generate_tax_reminder_msg(tax)
            try:
                audio_path = generate_voice_note(msg, lang)
                send_whatsapp_audio(phone, audio_path)
            except Exception:
                logger.exception(
                    "Failed to send tax reminder for tax record %s", tax.id
                )


# Step 4: Schedule Cron Job (Every Morning)

# cron: daily at 9AM
# 0 9 * * * /path/to/venv/bin/python /path/to/manage.py runscript schedule_reminders
