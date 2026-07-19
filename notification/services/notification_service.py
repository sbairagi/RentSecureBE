from __future__ import annotations

import logging
from typing import Any

from notification.ports.notification_payloads import (
    NotificationRequest,
    VoiceRequest,
    WhatsAppRequest,
)
from notification.services.notification_dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)


class NotificationService:
    """Orchestration layer for multi-channel notifications.

    This is the single public entry point for all notification operations.
    """

    def __init__(self) -> None:
        self._dispatcher = NotificationDispatcher()

    def send_otp(self, phone: str, code: str) -> bool:
        return self._dispatcher.dispatch_otp(phone, code)

    def send_email(
        self,
        subject: str,
        message: str,
        recipient_list: list[str],
        from_email: str | None = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> bool:
        return self._dispatcher.dispatch_email(
            subject, message, recipient_list, from_email, attachments
        )

    def send_push_notification(
        self, user: Any, title: str, message: str
    ) -> bool | None:
        return self._dispatcher.dispatch_push(user, title, message)

    def send_sms(self, phone: str, message: str) -> bool:
        return self._dispatcher.dispatch_sms(phone, message)

    def send_whatsapp_message(self, phone: str, text: str) -> bool:
        return self._dispatcher.dispatch_whatsapp_message(phone, text)

    def send_whatsapp_audio(self, phone: str, audio_path: str) -> bool:
        return self._dispatcher.dispatch_whatsapp_audio(phone, audio_path)

    def generate_voice_note(self, text: str, lang: str) -> str:
        return self._dispatcher.dispatch_voice(text, lang)

    def _dispatch(self, channel: str, func, *args: Any, **kwargs: Any) -> bool:
        try:
            return bool(func(*args, **kwargs))
        except Exception:
            logger.exception("%s notification failed", channel)
            return False

    def notify(self, request: NotificationRequest) -> dict[str, bool]:
        result: dict[str, bool] = {
            "email": False,
            "push": False,
            "sms": False,
            "whatsapp": False,
            "voice": False,
        }

        if request.email:
            result["email"] = self._dispatch(
                "Email",
                self._dispatcher.dispatch_email,
                request.email.subject,
                request.email.message,
                request.email.recipient_list,
                request.email.from_email,
                request.email.attachments,
            )

        if request.push:
            result["push"] = self._dispatch(
                "Push",
                self._dispatcher.dispatch_push,
                request.push.user,
                request.push.title,
                request.push.message,
            )

        if request.sms:
            result["sms"] = self._dispatch(
                "SMS",
                self._dispatcher.dispatch_sms,
                request.sms.phone,
                request.sms.message,
            )

        if request.whatsapp:
            result["whatsapp"] = self._dispatch(
                "WhatsApp",
                self._dispatcher.dispatch_whatsapp_message,
                request.whatsapp.phone,
                request.whatsapp.text,
            )
            if result["whatsapp"] and request.whatsapp.audio_path:
                result["whatsapp"] = self._dispatch(
                    "WhatsApp audio",
                    self._dispatcher.dispatch_whatsapp_audio,
                    request.whatsapp.phone,
                    request.whatsapp.audio_path,
                )

        if request.voice:
            result["voice"] = self._dispatch(
                "Voice",
                self._dispatcher.dispatch_voice,
                request.voice.text,
                request.voice.lang,
            )

        return result

    def notify_rent_due(
        self,
        renter: Any,
        amount: float | int,
        due_date: str,
        message: str | None = None,
    ) -> dict[str, bool]:
        from notification.services.i18n_service import translate_msg

        lang = getattr(getattr(renter, "user", None), "profile", None)
        lang = getattr(lang, "language_preference", "en") or "en" if lang else "en"
        phone = getattr(getattr(renter, "user", None), "profile", None)
        phone = (
            getattr(phone, "whatsapp_number", None)
            or getattr(renter, "whatsapp_number", None)
            or getattr(renter, "phone", None)
            or ""
        )

        base_message = message or (
            f"Namaste! Aapka ₹{amount} rent {due_date} ko due hai. "
            "Kripya samay par jama karein."
        )
        try:
            translated_message = translate_msg(base_message, lang)
        except Exception:
            translated_message = base_message

        request = NotificationRequest(
            whatsapp=WhatsAppRequest(
                phone=phone,
                text=translated_message,
            ),
            voice=VoiceRequest(
                text=translated_message,
                lang=lang,
            ),
        )
        return self.notify(request)

    def notify_payment_received(
        self,
        renter: Any,
        amount: float | int,
        paid_on: str,
        message: str | None = None,
    ) -> dict[str, bool]:
        from notification.services.i18n_service import translate_msg

        lang = getattr(getattr(renter, "user", None), "profile", None)
        lang = getattr(lang, "language_preference", "en") or "en" if lang else "en"
        phone = getattr(getattr(renter, "user", None), "profile", None)
        phone = (
            getattr(phone, "whatsapp_number", None)
            or getattr(renter, "whatsapp_number", None)
            or getattr(renter, "phone", None)
            or ""
        )

        base_message = message or (
            f"Namaste! Aapka ₹{amount} rent {paid_on} ko jama hua hai."
        )
        try:
            translated_message = translate_msg(base_message, lang)
        except Exception:
            translated_message = base_message

        request = NotificationRequest(
            whatsapp=WhatsAppRequest(
                phone=phone,
                text=translated_message,
            ),
            voice=VoiceRequest(
                text=translated_message,
                lang=lang,
            ),
        )
        return self.notify(request)
