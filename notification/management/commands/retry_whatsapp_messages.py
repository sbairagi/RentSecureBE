import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from notification.models import WhatsAppLog
from notification.services.whatsapp_service import (
    send_whatsapp_audio,
    send_whatsapp_message,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class Command(BaseCommand):
    help = "Retry failed WhatsApp messages up to 3 times."

    def handle(self, *args, **options):
        failed_logs = WhatsAppLog.objects.filter(
            status=WhatsAppLog.FAILED,
            retry_count__lt=MAX_RETRIES,
        )

        retried = 0
        for log in failed_logs:
            try:
                if log.message_type == WhatsAppLog.TEXT:
                    success = send_whatsapp_message(
                        log.phone,
                        log.message_content,
                        user=log.user,
                        rent_record=log.rent_record,
                        retry_count=log.retry_count + 1,
                    )
                elif log.message_type == WhatsAppLog.AUDIO:
                    if not log.media_url:
                        logger.warning(
                            "Skipping retry for log %s: missing media_url", log.pk
                        )
                        continue
                    success = send_whatsapp_audio(
                        log.phone,
                        log.media_url,
                        user=log.user,
                        rent_record=log.rent_record,
                        retry_count=log.retry_count + 1,
                    )
                else:
                    logger.warning(
                        "Unknown message_type %s for log %s",
                        log.message_type,
                        log.pk,
                    )
                    continue

                log.retry_count += 1
                log.last_retry_at = timezone.now()
                if success:
                    log.status = WhatsAppLog.SENT
                    self.stdout.write(f"Retried and sent message to {log.phone}")
                else:
                    log.status = (
                        WhatsAppLog.PERMANENT_FAILED
                        if log.retry_count >= MAX_RETRIES
                        else WhatsAppLog.FAILED
                    )
                    self.stderr.write(f"Retry failed for {log.phone}")
                log.save()
                retried += 1
            except Exception as exc:
                logger.exception("Retry failed for %s", log.phone)
                log.retry_count += 1
                log.last_retry_at = timezone.now()
                log.status = (
                    WhatsAppLog.PERMANENT_FAILED
                    if log.retry_count >= MAX_RETRIES
                    else WhatsAppLog.FAILED
                )
                log.save()
                self.stderr.write(f"Retry error for {log.phone}: {exc}")

        self.stdout.write(f"Retried {retried} message(s).")
