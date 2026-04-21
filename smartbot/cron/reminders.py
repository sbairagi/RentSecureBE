from wealth_concierge_platform.models import RentRecord
from communication.utils import send_whatsapp_message

def send_signature_reminders():
    rents = RentRecord.objects.filter(signature_status="PENDING")
    for rent in rents:
        send_whatsapp_message(rent.renter.phone, "🖊️ Reminder: Please sign your rent agreement.")