from __future__ import annotations

import logging

from twilio.rest import Client

from django.conf import settings

logger = logging.getLogger(__name__)


class SMSAdapter:
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
