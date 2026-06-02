import logging

from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)


def send_sms(phone, message):
    try:
        client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,  # Store this in settings too
            to=phone,
        )
        return True
    except Exception as e:
        logger.error(f"SMS sending failed: {e}")
        return False
