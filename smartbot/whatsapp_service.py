# services/whatsapp_service.py
from typing import Any

from notification.services.notification_service import NotificationService


def send_whatsapp_message(phone: str, text: str) -> bool:
    return NotificationService().send_whatsapp_message(phone, text)


def send_agreement_via_whatsapp(renter: Any, pdf_url: str) -> None:
    msg = f"📄 Your rent agreement is ready.\nDownload: {pdf_url}"
    phone = getattr(renter, "phone", "")
    send_whatsapp_message(phone, msg)
