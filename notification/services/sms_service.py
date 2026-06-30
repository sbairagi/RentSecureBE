import logging

from twilio.rest import Client

from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(phone: str, message: str) -> bool:
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,  # Store this in settings too
            to=phone,
        )
        return True
    except Exception as e:
        logger.error(f"SMS sending failed: {e}")
        return False
