import logging
from typing import Any

from twilio.rest import Client

from django.conf import settings

logger = logging.getLogger(__name__)


class SMSAdapter:
    """SMS notification adapter.

    This adapter is disabled behind a feature flag
    and will be implemented in a later task.
    """

    def send_whatsapp_message(self, phone: str, text: str) -> bool:
        raise NotImplementedError

    def send_whatsapp_audio(self, phone: str, audio_path: str) -> bool:
        raise NotImplementedError

    def send_sms(self, phone: str, message: str) -> bool:
        try:
            sid = getattr(settings, "TWILIO_SID", settings.TWILIO_ACCOUNT_SID)
            token = getattr(settings, "TWILIO_TOKEN", settings.TWILIO_AUTH_TOKEN)
            client = Client(sid, token)
            client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone,
            )
            return True
        except Exception as e:
            logger.exception(f"SMS sending failed: {e}")
            return False

    def send_push_notification(
        self, user: Any, title: str, message: str
    ) -> bool | None:
        raise NotImplementedError

    def generate_voice_note(self, text: str, lang: str) -> str:
        raise NotImplementedError
