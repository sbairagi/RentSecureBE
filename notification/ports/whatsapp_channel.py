from __future__ import annotations

from typing import Protocol


class WhatsAppChannel(Protocol):
    def send_whatsapp_message(self, phone: str, text: str) -> bool: ...

    def send_whatsapp_audio(self, phone: str, audio_path: str) -> bool: ...
