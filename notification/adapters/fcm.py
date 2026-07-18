from typing import Any


class FirebaseAdapter:
    """Firebase Cloud Messaging push notification adapter.

    This adapter is enabled and will be implemented in a later task.
    """

    def send_whatsapp_message(self, phone: str, text: str) -> bool:
        raise NotImplementedError

    def send_whatsapp_audio(self, phone: str, audio_path: str) -> bool:
        raise NotImplementedError

    def send_sms(self, phone: str, message: str) -> bool:
        raise NotImplementedError

    def send_push_notification(
        self, user: Any, title: str, message: str
    ) -> bool | None:
        raise NotImplementedError

    def generate_voice_note(self, text: str, lang: str) -> str:
        raise NotImplementedError
