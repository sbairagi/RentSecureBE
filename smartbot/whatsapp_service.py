# services/whatsapp_service.py
from notification.utils import send_whatsapp_message


def send_agreement_via_whatsapp(renter, pdf_url):
    msg = f"📄 Your rent agreement is ready.\nDownload: {pdf_url}"
    send_whatsapp_message(renter.phone, msg)
