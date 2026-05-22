import logging

from ai_assistant.services.i18n_service import translate_msg
from notification.services.voice_service import generate_voice_note
from notification.services.whatsapp_service import (
    send_whatsapp_audio,
    send_whatsapp_message,
)

logger = logging.getLogger(__name__)

def notify_renter(renter, message: str):
    lang = renter.profile.language_preference or "en"

    try:
        translated_text = translate_msg(message, lang)
    except Exception as e:
        logger.error(f"Translation failed for user {renter.id}: {e}")
        translated_text = message  # fallback to original

    try:
        send_whatsapp_message(renter.profile.whatsapp_number, translated_text)
    except Exception as e:
        logger.error(f"WhatsApp text message failed for user {renter.id}: {e}")

    try:
        audio_path = generate_voice_note(translated_text, lang)
        if audio_path:
            send_whatsapp_audio(renter.profile.whatsapp_number, audio_path)
    except Exception as e:
        logger.error(f"WhatsApp voice note failed for user {renter.id}: {e}")


def notify_owner(owner, message: str):
    lang = owner.profile.language_preference or "en"

    try:
        translated_text = translate_msg(message, lang)
    except Exception as e:
        logger.error(f"Translation failed for user {owner.id}: {e}")
        translated_text = message  # fallback to original

    try:
        send_whatsapp_message(owner.profile.whatsapp_number, translated_text)
    except Exception as e:
        logger.error(f"WhatsApp text message failed for user {owner.id}: {e}")

    # translated_text = translate_msg(message, lang)
    # send_whatsapp_message(owner.profile.whatsapp_number, translated_text)

    try:
        audio_path = generate_voice_note(translated_text, lang)
        if audio_path:
            send_whatsapp_audio(owner.profile.whatsapp_number, audio_path)
    except Exception as e:
        logger.error(f"WhatsApp voice note failed for user {owner.id}: {e}")

    audio_path = generate_voice_note(translated_text, lang)
    if audio_path:
        send_whatsapp_audio(owner.profile.whatsapp_number, audio_path)


def send_payout_notification(rent):
    """
    Sends a WhatsApp message to renter based on payout status.
    """
    try:
        if rent.payout_status == "SUCCESS":
            msg = f"Namaste! Aapka ₹{rent.amount} rent {rent.updated_at.date()} ko jama hua hai."
        elif rent.payout_status == "FAILED":
            msg = f"⚠️ ₹{rent.amount} rent ka transfer fail ho gaya hai. Kripya apna bank detail verify karein."
        else:
            logger.info(f"No notification sent for rent ID {rent.id} with status {rent.payout_status}")
            return

        notify_renter(rent.renter, msg)
    except Exception as e:
        logger.exception(f"Failed to notify renter for rent ID {rent.id}: {e}")



def notify_owner_post_payout(rent):
    owner = rent.renter.property.owner
    phone = owner.profile.whatsapp_number
    lang = owner.profile.language_preference or "hi"

    if rent.payout_status == "SUCCESS":
        msg = f"Namaste! Aapka ₹{rent.amount} rent {rent.updated_at.date()} ko jama hua hai."
    else:
        msg = f"⚠️ Aapka ₹{rent.amount} rent ka payment fail ho gaya hai. Kripya bank details verify karein."

    translated_msg = translate_msg(msg, lang)
    audio_path = generate_voice_note(translated_msg, lang=lang)

    # 1. Send text
    send_whatsapp_message(phone, translated_msg)

    # 2. Send voice note
    if audio_path:
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
#         msg = f"Namaste! Aapka ₹{rent.amount} rent {rent.updated_at.date()} ko jama hua hai."
#     elif rent.payout_status == "FAILED":
#         msg = f"⚠️ ₹{rent.amount} rent ka transfer fail ho gaya hai. Kripya apna bank detail verify karein."
#     else:
#         msg = None

#     if msg:
#         try:
#             notify_renter(rent.renter, msg)
#         except Exception as e:
#             print(f"WhatsApp message failed: {e}")
