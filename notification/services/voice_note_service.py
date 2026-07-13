"""Voice-note notification service for renters and owners.

The reminder-sent state for a given renter is recorded on
:class:`properties.models.RentReminderLog` (the canonical model),
*not* on :class:`properties.models.RentRecord` (which has no
``reminder_sent`` field). This module writes to the log and never
attempts to set non-existent fields on ``RentRecord``.
"""

from __future__ import annotations

import logging
from typing import Any

from notification.services.voice_service import generate_voice_note  # nosonar
from notification.services.whatsapp_service import send_whatsapp_audio  # nosonar
from notification.services.whatsapp_service import (
    send_whatsapp_message,  # nosonar; nosonar
)

logger = logging.getLogger(__name__)


def send_thank_you_voice_note(rent: Any) -> None:
    """Send a Hindi thank-you voice note to a renter who paid rent early."""
    if rent.renter is None:
        return
    name: str = rent.renter.full_name
    amount = rent.amount
    date_str: str = rent.paid_on.strftime("%d %B") if rent.paid_on else ""
    msg: str = (
        f"Shukriya {name}! Aapne ₹{amount} rent {date_str} ko time se pehle "
        "jama kiya. Aapki samay par payment ki hum sarahna karte hain."
    )

    audio_path: str | None = generate_voice_note(msg, lang="hi")
    if audio_path is not None and rent.renter.whatsapp_number:
        send_whatsapp_audio(rent.renter.whatsapp_number, audio_path)


def send_late_rent_reminder(rent: Any) -> None:
    """Send a Hindi voice-note reminder to a renter with overdue rent.

    Records the reminder in :class:`RentReminderLog` so we never spam
    the same renter with the same reminder type on the same day.
    """
    from properties.models.renter_models import RentReminderLog

    if rent.renter is None:
        return
    name: str = rent.renter.full_name
    amount = rent.amount
    due_date_str: str = rent.due_date.strftime("%d %B")

    msg: str = (
        f"Namaste {name}, aapka ₹{amount} rent {due_date_str} ko due tha. "
        "Kripya jald se jald jama karein. Dhanyawaad."
    )

    audio_path: str | None = generate_voice_note(msg, lang="hi")
    if audio_path is not None and rent.renter.whatsapp_number:
        send_whatsapp_audio(rent.renter.whatsapp_number, audio_path)

    RentReminderLog.objects.create(
        renter=rent.renter,
        message_type="LATE",
    )


def alert_owner_about_delay(rent: Any) -> None:
    """Send a WhatsApp text alert to the owner about a delayed rent."""

    if rent.renter is None:
        return
    owner = rent.renter.unit.owner
    msg: str = (
        f"⚠️ Alert: Your renter {rent.renter.full_name} "
        f"has not paid rent ₹{rent.amount} due on {rent.due_date}."
    )
    if owner.whatsapp_number:
        send_whatsapp_message(owner.whatsapp_number, msg)
