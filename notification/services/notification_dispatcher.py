from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

from notification.ports.email_channel import EmailChannel
from notification.ports.push_notification_channel import PushNotificationChannel
from notification.ports.sms_channel import SMSChannel
from notification.ports.voice_channel import VoiceChannel
from notification.ports.whatsapp_channel import WhatsAppChannel

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    def __init__(self) -> None:
        self._email_adapter: EmailChannel | None = None
        self._sms_adapter: SMSChannel | None = None
        self._push_adapter: PushNotificationChannel | None = None
        self._whatsapp_adapter: WhatsAppChannel | None = None
        self._voice_adapter: VoiceChannel | None = None

    def _get_email_adapter(self) -> EmailChannel | None:
        if self._email_adapter is None and getattr(settings, "ENABLE_EMAIL", True):
            from notification.adapters.email import EmailAdapter

            self._email_adapter = EmailAdapter()
        return self._email_adapter

    def _get_sms_adapter(self) -> SMSChannel | None:
        if self._sms_adapter is None and getattr(settings, "ENABLE_SMS", False):
            from notification.adapters.sms import SMSAdapter

            self._sms_adapter = SMSAdapter()
        return self._sms_adapter

    def _get_push_adapter(self) -> PushNotificationChannel | None:
        if self._push_adapter is None and getattr(
            settings, "ENABLE_PUSH_NOTIFICATION", True
        ):
            from notification.adapters.fcm import FirebaseAdapter

            self._push_adapter = FirebaseAdapter()
        return self._push_adapter

    def _get_whatsapp_adapter(self) -> WhatsAppChannel | None:
        if self._whatsapp_adapter is None and getattr(
            settings, "ENABLE_WHATSAPP", False
        ):
            from notification.adapters.whatsapp import WhatsAppAdapter

            self._whatsapp_adapter = WhatsAppAdapter()
        return self._whatsapp_adapter

    def _get_voice_adapter(self) -> VoiceChannel | None:
        if self._voice_adapter is None and getattr(settings, "ENABLE_VOICE", False):
            from notification.adapters.voice import VoiceAdapter

            self._voice_adapter = VoiceAdapter()
        return self._voice_adapter

    def dispatch_email(
        self,
        subject: str,
        message: str,
        recipient_list: list[str],
        from_email: str | None = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> bool:
        adapter = self._get_email_adapter()
        if adapter is None:
            return False
        try:
            return adapter.send_email(
                subject, message, recipient_list, from_email, attachments
            )
        except Exception:
            logger.exception("Email notification failed")
            return False

    def dispatch_push(self, user: Any, title: str, message: str) -> bool | None:
        adapter = self._get_push_adapter()
        if adapter is None:
            return None
        try:
            return adapter.send_push_notification(user, title, message)
        except Exception:
            logger.exception("Push notification failed")
            return None

    def dispatch_sms(self, phone: str, message: str) -> bool:
        adapter = self._get_sms_adapter()
        if adapter is None:
            return False
        try:
            return adapter.send_sms(phone, message)
        except Exception:
            logger.exception("SMS notification failed")
            return False

    def dispatch_whatsapp_message(self, phone: str, text: str) -> bool:
        adapter = self._get_whatsapp_adapter()
        if adapter is None:
            return False
        try:
            return adapter.send_whatsapp_message(phone, text)
        except Exception:
            logger.exception("WhatsApp notification failed")
            return False

    def dispatch_whatsapp_audio(self, phone: str, audio_path: str) -> bool:
        adapter = self._get_whatsapp_adapter()
        if adapter is None:
            return False
        try:
            return adapter.send_whatsapp_audio(phone, audio_path)
        except Exception:
            logger.exception("WhatsApp audio notification failed")
            return False

    def dispatch_otp(self, phone: str, code: str) -> bool:
        message = f"Your verification code is {code}"
        return self.dispatch_sms(phone, message)

    def dispatch_voice(self, text: str, lang: str) -> str:
        adapter = self._get_voice_adapter()
        if adapter is None:
            return ""
        try:
            return adapter.generate_voice_note(text, lang)
        except Exception:
            logger.exception("Voice notification failed")
            return ""
