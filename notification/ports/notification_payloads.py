from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EmailRequest:
    subject: str
    message: str
    recipient_list: list[str]
    from_email: str | None = None
    attachments: list[tuple[str, bytes, str]] | None = None


@dataclass
class PushRequest:
    user: Any
    title: str
    message: str


@dataclass
class SMSRequest:
    phone: str
    message: str


@dataclass
class WhatsAppRequest:
    phone: str
    text: str
    audio_path: str | None = None


@dataclass
class VoiceRequest:
    text: str
    lang: str


@dataclass
class NotificationRequest:
    email: EmailRequest | None = None
    push: PushRequest | None = None
    sms: SMSRequest | None = None
    whatsapp: WhatsAppRequest | None = None
    voice: VoiceRequest | None = None
