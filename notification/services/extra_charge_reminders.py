import logging
from datetime import timedelta

from django.utils import timezone

# nosonar
from ai_assistant.services.i18n_service import translate_msg
from notification.services.voice_service import generate_voice_note
from notification.services.whatsapp_service import (
    send_whatsapp_audio,
    send_whatsapp_message,
)
from properties.models import ExtraCharge  # nosonar

logger = logging.getLogger(__name__)


def send_due_extra_charge_reminders(days_ahead: int = 0) -> int:
    target_date = timezone.now().date() + timedelta(days=days_ahead)
    charges = ExtraCharge.objects.filter(
        status=ExtraCharge.Status.DUE,
        due_date=target_date,
    ).select_related("renter", "renter__user", "renter__user__userprofile")

    charge_list = list(charges)
    for charge in charge_list:
        renter = charge.renter
        phone = renter.whatsapp_number or renter.phone
        if not phone:
            continue

        lang = "en"
        if renter.user and hasattr(renter.user, "userprofile"):
            lang = getattr(renter.user.userprofile, "language_preference", "en") or "en"

        message = (
            f"Reminder: You have an unpaid charge of ₹{charge.amount} "
            f"for '{charge.name}' "
            f"due today ({charge.due_date}). Please pay on time to avoid late fees."
        )
        translated_message = translate_msg(message, lang)

        try:
            send_whatsapp_message(phone, translated_message)
        except Exception as e:
            logger.warning(f"Failed to send WhatsApp message to {phone}: {e}")
            continue

        audio_path = generate_voice_note(translated_message, lang)
        if audio_path:
            try:
                send_whatsapp_audio(phone, audio_path)
            except Exception as e:
                logger.warning(f"Failed to send WhatsApp audio to {phone}: {e}")
                continue

    return len(charge_list)
