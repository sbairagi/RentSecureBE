from __future__ import annotations

import logging
import os
from typing import Any

try:
    import boto3  # type: ignore[import-untyped]
except ImportError:
    boto3 = None
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from django.conf import settings

from notification.models import WhatsAppLog

logger = logging.getLogger(__name__)


def _create_whatsapp_log(
    phone: str,
    message_type: str,
    message_content: str,
    status: str,
    user: Any = None,
    rent_record: Any = None,
    media_url: str | None = None,
    retry_count: int = 0,
) -> None:
    """Create a WhatsAppLog entry for audit trail."""
    try:
        WhatsAppLog.objects.create(
            phone=phone,
            user=user,
            rent_record=rent_record,
            message_type=message_type,
            message_content=message_content,
            media_url=media_url,
            status=status,
            retry_count=retry_count,
        )
    except Exception:
        logger.exception("Failed to create WhatsApp log")


def send_whatsapp_message(
    phone: str,
    text: str,
    user: Any = None,
    rent_record: Any = None,
    retry_count: int = 0,
) -> bool:
    try:
        sid = getattr(settings, "TWILIO_SID", settings.TWILIO_ACCOUNT_SID)
        token = getattr(settings, "TWILIO_TOKEN", settings.TWILIO_AUTH_TOKEN)
        client = Client(sid, token)
        client.messages.create(
            body=text, from_=settings.TWILIO_WHATSAPP_NUMBER, to=f"whatsapp:{phone}"
        )
        _create_whatsapp_log(
            phone=phone,
            message_type=WhatsAppLog.TEXT,
            message_content=text,
            status=WhatsAppLog.SENT,
            user=user,
            rent_record=rent_record,
            retry_count=retry_count,
        )
        return True
    except TwilioRestException:
        logger.exception("WhatsApp sending failed: %s")
        _create_whatsapp_log(
            phone=phone,
            message_type=WhatsAppLog.TEXT,
            message_content=text,
            status=WhatsAppLog.FAILED,
            user=user,
            rent_record=rent_record,
            retry_count=retry_count,
        )
        return False


def send_whatsapp_audio(
    phone: str,
    audio_path: str,
    user: Any = None,
    rent_record: Any = None,
    retry_count: int = 0,
) -> bool:
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
        _create_whatsapp_log(
            phone=phone,
            message_type=WhatsAppLog.AUDIO,
            message_content="Voice Note",
            status=WhatsAppLog.SENT,
            user=user,
            rent_record=rent_record,
            media_url=media_url,
            retry_count=retry_count,
        )
        return True
    except (TwilioRestException, OSError):
        logger.exception("WhatsApp audio failed: %s")
        _create_whatsapp_log(
            phone=phone,
            message_type=WhatsAppLog.AUDIO,
            message_content="Voice Note",
            status=WhatsAppLog.FAILED,
            user=user,
            rent_record=rent_record,
            retry_count=retry_count,
        )
        return False


def send_whatsapp_file(
    phone: str,
    file_path: str,
    content_type: str = "application/pdf",
    user: Any = None,
    rent_record: Any = None,
    retry_count: int = 0,
) -> bool:
    try:
        media_url = upload_to_s3(file_path)

        sid = getattr(settings, "TWILIO_SID", settings.TWILIO_ACCOUNT_SID)
        token = getattr(settings, "TWILIO_TOKEN", settings.TWILIO_AUTH_TOKEN)
        client = Client(sid, token)
        client.messages.create(
            media_url=[media_url],
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{phone}",
        )
        _create_whatsapp_log(
            phone=phone,
            message_type=WhatsAppLog.AUDIO,
            message_content=f"File: {os.path.basename(file_path)}",
            status=WhatsAppLog.SENT,
            user=user,
            rent_record=rent_record,
            media_url=media_url,
            retry_count=retry_count,
        )
        return True
    except (TwilioRestException, OSError):
        logger.exception("WhatsApp file send failed: %s")
        _create_whatsapp_log(
            phone=phone,
            message_type=WhatsAppLog.AUDIO,
            message_content=f"File: {os.path.basename(file_path)}",
            status=WhatsAppLog.FAILED,
            user=user,
            rent_record=rent_record,
            retry_count=retry_count,
        )
        return False


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


def send_agreement_via_whatsapp(renter: Any, pdf_url: str) -> bool:
    msg = f"📄 Your rent agreement is ready.\nDownload: {pdf_url}"
    return send_whatsapp_message(renter.phone, msg)
