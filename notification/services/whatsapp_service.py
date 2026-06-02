# services/whatsapp_service.py

import logging
import os
from typing import List, Optional

try:
    import boto3
except ImportError:
    boto3 = None
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)


def send_whatsapp_message(phone: str, text: str) -> bool:
    try:
        sid = getattr(settings, "TWILIO_SID", settings.TWILIO_ACCOUNT_SID)
        token = getattr(settings, "TWILIO_TOKEN", settings.TWILIO_AUTH_TOKEN)
        client = Client(sid, token)
        client.messages.create(
            body=text, from_=settings.TWILIO_WHATSAPP_NUMBER, to=f"whatsapp:{phone}"
        )
        return True
    except Exception as exc:
        logger.error("WhatsApp sending failed: %s", exc)
        return False


def send_whatsapp_audio(phone: str, audio_path: str) -> bool:
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
    except Exception as exc:
        logger.error("WhatsApp audio failed: %s", exc)
        return False


def upload_to_s3(file_path: str) -> Optional[str]:
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


def send_agreement_via_whatsapp(renter: Any, pdf_url: str) -> bool:
    msg = f"📄 Your rent agreement is ready.\nDownload: {pdf_url}"
    return send_whatsapp_message(renter.phone, msg)
