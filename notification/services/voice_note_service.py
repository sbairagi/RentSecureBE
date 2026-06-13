"""Voice-note notification service for renters and owners.

The reminder-sent state for a given renter is recorded on
:class:`properties.models.RentReminderLog` (the canonical model),
*not* on :class:`properties.models.RentRecord` (which has no
``reminder_sent`` field). This module writes to the log and never
attempts to set non-existent fields on ``RentRecord``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from notification.services.voice_service import generate_voice_note
from notification.services.whatsapp_service import (
    send_whatsapp_audio,
    send_whatsapp_message,
)
from properties.models import RentReminderLog

if TYPE_CHECKING:
    from properties.models import RentRecord


def send_thank_you_voice_note(rent: "RentRecord") -> None:
    """Send a thank-you voice note to a renter after a successful payment."""
    name: str = rent.renter.full_name
    amount = rent.amount_paid
    date_str: str = rent.date_paid.strftime("%d %B")
    msg: str = (
        f"Shukriya {name}! Aapne ₹{amount} rent {date_str} ko time se pehle "
        "jama kiya. Aapki samay par payment ki hum sarahna karte hain."
    )

    audio_path: str | None = generate_voice_note(msg, lang="hi")
    if audio_path is not None:
        send_whatsapp_audio(rent.renter.whatsapp_number, audio_path)


def send_late_rent_reminder(rent: "RentRecord") -> None:
    """Send a Hindi voice-note reminder to a renter with overdue rent.

    Records the reminder in :class:`RentReminderLog` so we never spam
    the same renter with the same reminder type on the same day.
    """
    name: str = rent.renter.full_name
    amount = rent.amount_paid
    due_date_str: str = rent.rent_due_date.strftime("%d %B")

    msg: str = (
        f"Namaste {name}, aapka ₹{amount} rent {due_date_str} ko due tha. "
        "Kripya jald se jald jama karein. Dhanyawaad."
    )

    audio_path: str | None = generate_voice_note(msg, lang="hi")
    if audio_path is not None:
        send_whatsapp_audio(rent.renter.whatsapp_number, audio_path)

    # Record that we sent the reminder. RentReminderLog is the
    # canonical record; RentRecord has no reminder_sent field.
    RentReminderLog.objects.create(
        renter=rent.renter,
        message_type="LATE",
    )


def alert_owner_about_delay(rent: "RentRecord") -> None:
    """Send a WhatsApp text alert to the owner about a delayed rent."""
    owner = rent.renter.unit.owner
    msg: str = (
        f"⚠️ Alert: Your renter {rent.renter.full_name} "
        f"has not paid rent ₹{rent.amount_paid} due on {rent.rent_due_date}."
    )
    if getattr(owner, "profile", None) is not None:
        send_whatsapp_message(owner.profile.whatsapp_number, msg)
