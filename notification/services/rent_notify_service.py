"""Rent notification service for renters and owners.

``Renter`` has no ``profile`` reverse relation — that lives on ``User``.
We therefore resolve the language preference and the WhatsApp number
with safe fallbacks, in order of preference:

    1. ``renter.user.profile`` when the renter is linked to a user
       and the profile has the data we need.
    2. ``renter.whatsapp_number`` (canonical column on ``Renter``).
    3. The hard-coded English / "" fallbacks below.

This keeps every call site runtime-safe without changing business
logic or adding new model fields.
"""

import logging

from ai_assistant.services.i18n_service import translate_msg
from notification.services.voice_service import generate_voice_note
from notification.services.whatsapp_service import (
    send_whatsapp_audio,
    send_whatsapp_message,
)

logger = logging.getLogger(__name__)


def _renter_phone(renter) -> str:
    """Return the best-available phone number for a renter."""
    user_profile = getattr(getattr(renter, "user", None), "profile", None)
    if user_profile is not None and getattr(user_profile, "whatsapp_number", None):
        return user_profile.whatsapp_number
    return renter.whatsapp_number or renter.phone or ""


def _renter_lang(renter, default: str = "en") -> str:
    """Return the best-available language preference for a renter."""
    user_profile = getattr(getattr(renter, "user", None), "profile", None)
    if user_profile is not None and getattr(user_profile, "language_preference", None):
        return user_profile.language_preference
    return default


def notify_renter(renter, message: str):
    lang = _renter_lang(renter, default="en")
    phone = _renter_phone(renter)

    try:
        translated_text = translate_msg(message, lang)
    except Exception as e:
        logger.error(f"Translation failed for user {renter.id}: {e}")
        translated_text = message  # fallback to original

    try:
        if phone:
            send_whatsapp_message(phone, translated_text)
    except Exception as e:
        logger.error(f"WhatsApp text message failed for user {renter.id}: {e}")

    try:
        audio_path = generate_voice_note(translated_text, lang)
        if audio_path and phone:
            send_whatsapp_audio(phone, audio_path)
    except Exception as e:
        logger.error(f"WhatsApp voice note failed for user {renter.id}: {e}")


def notify_owner(owner, message: str):
    lang = (getattr(getattr(owner, "profile", None), "language_preference", None) or "en")
    phone = (getattr(getattr(owner, "profile", None), "whatsapp_number", None) or owner.phone or "")

    try:
        translated_text = translate_msg(message, lang)
    except Exception as e:
        logger.error(f"Translation failed for user {owner.id}: {e}")
        translated_text = message  # fallback to original

    try:
        if phone:
            send_whatsapp_message(phone, translated_text)
    except Exception as e:
        logger.error(f"WhatsApp text message failed for user {owner.id}: {e}")

    try:
        audio_path = generate_voice_note(translated_text, lang)
        if audio_path and phone:
            send_whatsapp_audio(phone, audio_path)
    except Exception as e:
        logger.error(f"WhatsApp voice note failed for user {owner.id}: {e}")


def send_payout_notification(rent):
    """
    Sends a WhatsApp message to renter based on payout status.
    """
    try:
        if rent.payout_status == "SUCCESS":
            msg = (
                f"Namaste! Aapka ₹{rent.amount} rent "
                f"{rent.updated_at.date()} ko jama hua hai."
            )
        elif rent.payout_status == "FAILED":
            msg = (
                f"⚠️ ₹{rent.amount} rent ka transfer fail ho gaya hai. "
                f"Kripya apna bank detail verify karein."
            )
        else:
            logger.info(
                f"No notification sent for rent ID {rent.id} "
                f"with status {rent.payout_status}"
            )
            return

        notify_renter(rent.renter, msg)
    except Exception as e:
        logger.exception(f"Failed to notify renter for rent ID {rent.id}: {e}")


def notify_owner_post_payout(rent):
    owner = rent.renter.unit.owner
    profile = getattr(owner, "profile", None)
    phone = (getattr(profile, "whatsapp_number", None) or owner.phone or "")
    lang = (getattr(profile, "language_preference", None) or "hi")

    if rent.payout_status == "SUCCESS":
        msg = (
            f"Namaste! Aapka ₹{rent.amount} rent "
            f"{rent.updated_at.date()} ko jama hua hai."
        )
    else:
        msg = (
            f"⚠️ Aapka ₹{rent.amount} rent ka payment fail ho gaya hai. "
            f"Kripya bank details verify karein."
        )

    translated_msg = translate_msg(msg, lang)
    audio_path = generate_voice_note(translated_msg, lang=lang)

    # 1. Send text
    if phone:
        send_whatsapp_message(phone, translated_msg)

    # 2. Send voice note
    if audio_path and phone:
        send_whatsapp_audio(phone, audio_path)


# # services/rent_notify_service.py

# from services.i18n_service import translate_msg
# from services.voice_service import generate_voice_note
# from services.whatsapp_service import send_whatsapp_message, send_whatsapp_audio

# def notify_renter(renter, message: str):
#     lang = renter.profile.language_preference or "en"
#     translated_text = translate_msg(message, lang)

#     # Send translated text
#     send_whatsapp_message(renter.phone, translated_text)

#     # Send voice note
#     audio_path = generate_voice_note(translated_text, lang)
#     if audio_path:
#         send_whatsapp_audio(renter.phone, audio_path)


# # notifications/utils.py

# def send_payout_notification(rent):
#     """
#     Sends a WhatsApp message to renter based on payout status.
#     """
#     if rent.payout_status == "SUCCESS":
#         msg = (
#             f"Namaste! Aapka ₹{rent.amount} rent "
#             f"{rent.updated_at.date()} ko jama hua hai."
#         )
#     elif rent.payout_status == "FAILED":
#         msg = (
#             f"⚠️ ₹{rent.amount} rent ka transfer fail ho gaya hai. "
#             f"Kripya apna bank detail verify karein."
#         )
#     else:
#         msg = None

#     if msg:
#         try:
#             notify_renter(rent.renter, msg)
#         except Exception as e:
#             print(f"WhatsApp message failed: {e}")
