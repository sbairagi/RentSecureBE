# services/whatsapp_service.py
from typing import Any

from notification.utils import send_whatsapp_message


def send_agreement_via_whatsapp(renter: Any, pdf_url: str) -> None:
    msg = f"📄 Your rent agreement is ready.\nDownload: {pdf_url}"
    phone = getattr(renter, "phone", "")
    send_whatsapp_message(phone, msg)
