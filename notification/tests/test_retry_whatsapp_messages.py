from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from notification.models import WhatsAppLog

User = get_user_model()


def _create_failed_text_log(**overrides):
    user = User.objects.create_user(
        username=overrides.pop("username", "retry_user"),
        email="retry@test.com",
        password="p",
        full_name="Retry",
        phone="+1",
    )
    defaults = {
        "phone": "+911234567890",
        "message_type": WhatsAppLog.TEXT,
        "message_content": "Hello",
        "status": WhatsAppLog.FAILED,
        "retry_count": 0,
        "user": user,
    }
    defaults.update(overrides)
    return WhatsAppLog.objects.create(**defaults)


class RetryWhatsAppMessagesCommandTest(TestCase):
    def test_retries_failed_text_messages(self):
        log = _create_failed_text_log()

        with patch(
            "notification.management.commands.retry_whatsapp_messages.send_whatsapp_message",
            return_value=True,
        ) as mock_send:
            self.call_command()

        mock_send.assert_called_once_with(
            log.phone,
            log.message_content,
            user=log.user,
            rent_record=log.rent_record,
            retry_count=1,
        )
        log.refresh_from_db()
        self.assertEqual(log.status, WhatsAppLog.SENT)
        self.assertEqual(log.retry_count, 1)
        self.assertIsNotNone(log.last_retry_at)

    def test_retries_failed_audio_messages(self):
        user = User.objects.create_user(
            username="retry_audio_user",
            email="retryaudio@test.com",
            password="p",
            full_name="RetryAudio",
            phone="+1",
        )
        log = WhatsAppLog.objects.create(
            phone="+911234567891",
            message_type=WhatsAppLog.AUDIO,
            message_content="Voice Note",
            media_url="https://example.com/audio.mp3",
            status=WhatsAppLog.FAILED,
            retry_count=0,
            user=user,
        )

        with patch(
            "notification.management.commands.retry_whatsapp_messages.send_whatsapp_audio",
            return_value=True,
        ) as mock_send:
            self.call_command()

        mock_send.assert_called_once_with(
            log.phone,
            log.media_url,
            user=log.user,
            rent_record=log.rent_record,
            retry_count=1,
        )
        log.refresh_from_db()
        self.assertEqual(log.status, WhatsAppLog.SENT)
        self.assertEqual(log.retry_count, 1)

    def test_marks_permanently_failed_after_max_retries(self):
        log = _create_failed_text_log(retry_count=2)

        with patch(
            "notification.management.commands.retry_whatsapp_messages.send_whatsapp_message",
            return_value=False,
        ) as mock_send:
            self.call_command()

        mock_send.assert_called_once()
        log.refresh_from_db()
        self.assertEqual(log.status, WhatsAppLog.PERMANENT_FAILED)
        self.assertEqual(log.retry_count, 3)

    def test_skips_already_sent_logs(self):
        _create_failed_text_log(status=WhatsAppLog.SENT)

        with patch(
            "notification.management.commands.retry_whatsapp_messages.send_whatsapp_message"
        ) as mock_send:
            self.call_command()

        mock_send.assert_not_called()

    def test_skips_audio_logs_without_media_url(self):
        log = _create_failed_text_log(
            message_type=WhatsAppLog.AUDIO,
            media_url=None,
        )

        with patch(
            "notification.management.commands.retry_whatsapp_messages.send_whatsapp_audio"
        ) as mock_send:
            self.call_command()

        mock_send.assert_not_called()
        log.refresh_from_db()
        self.assertEqual(log.status, WhatsAppLog.FAILED)

    def call_command(self):
        from django.core.management import call_command

        call_command("retry_whatsapp_messages")
