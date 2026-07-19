from __future__ import annotations

import logging
import os

try:
    import boto3  # type: ignore[import-untyped]
except ImportError:
    boto3 = None
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from django.conf import settings

logger = logging.getLogger(__name__)


def upload_to_s3(file_path: str) -> str | None:
    bucket_name = settings.AWS_S3_BUCKET_NAME
    if not bucket_name:
        raise RuntimeError("AWS_S3_BUCKET_NAME must be configured in settings.")
    if boto3 is None:
        raise RuntimeError("boto3 is required for upload_to_s3")

    filename = os.path.basename(file_path)
    key = f"voice_notes/{filename}"

    s3 = boto3.client("s3")
    s3.upload_file(file_path, bucket_name, key, ExtraArgs={"ContentType": "audio/mpeg"})
    return f"https://{bucket_name}.s3.amazonaws.com/{key}"


class WhatsAppAdapter:
    def send_whatsapp_message(self, phone: str, text: str) -> bool:
        try:
            sid = getattr(settings, "TWILIO_SID", settings.TWILIO_ACCOUNT_SID)
            token = getattr(settings, "TWILIO_TOKEN", settings.TWILIO_AUTH_TOKEN)
            client = Client(sid, token)
            client.messages.create(
                body=text, from_=settings.TWILIO_WHATSAPP_NUMBER, to=f"whatsapp:{phone}"
            )
            return True
        except TwilioRestException:
            logger.exception("WhatsApp sending failed: %s")
            return False

    def send_whatsapp_audio(self, phone: str, audio_path: str) -> bool:
        try:
            media_url = upload_to_s3(audio_path)

            sid = getattr(settings, "TWILIO_SID", settings.TWILIO_ACCOUNT_SID)
            token = getattr(settings, "TWILIO_TOKEN", settings.TWILIO_AUTH_TOKEN)
            client = Client(sid, token)
            client.messages.create(
                media_url=[media_url],
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                to=f"whatsapp:{phone}",
            )
            return True
        except (TwilioRestException, OSError):
            logger.exception("WhatsApp audio failed: %s")
            return False
