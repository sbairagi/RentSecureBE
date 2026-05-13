# services/whatsapp_service.py

import os
import logging
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)

def send_whatsapp_message(phone, text):
    try:
        client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
        client.messages.create(
            body=text,
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{phone}'
        )
        return True
    except Exception as exc:
        logger.error("WhatsApp sending failed: %s", exc)
        return False


def send_whatsapp_audio(phone, audio_path):
    try:
        media_url = upload_to_s3(audio_path)

        client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
        client.messages.create(
            media_url=[media_url],
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{phone}'
        )
        return True
    except Exception as exc:
        logger.error("WhatsApp audio failed: %s", exc)
        return False


def upload_to_s3(file_path):
    try:
        import boto3
    except ImportError:
        raise RuntimeError("boto3 is required for upload_to_s3")

    bucket_name = settings.AWS_S3_BUCKET_NAME
    if not bucket_name:
        raise RuntimeError("AWS_S3_BUCKET_NAME must be configured in settings.")

    filename = os.path.basename(file_path)
    key = f"voice_notes/{filename}"

    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, key, ExtraArgs={'ContentType': 'audio/mpeg'})
    return f"https://{bucket_name}.s3.amazonaws.com/{key}"


def send_agreement_via_whatsapp(renter, pdf_url):
    msg = f"📄 Your rent agreement is ready.\nDownload: {pdf_url}"
    send_whatsapp_message(renter.phone, msg)