from properties.models import RentRecord, Renter
from rentsecure_be.services.razorpay_service import create_payment_link
from communication.utils import send_whatsapp_message
from datetime import date

def auto_generate_rent_records():
    today = date.today()
    renters = Renter.objects.all()
    
    for renter in renters:
        rent, created = RentRecord.objects.get_or_create(
            renter=renter,
            month=today.month,
            year=today.year,
            defaults={"amount": renter.monthly_rent}
        )

        if created:
            # ✅ Create payment link
            link = create_payment_link(rent)
            rent.payment_link = link
            rent.save()

            # ✅ Send WhatsApp reminder
            send_whatsapp_message(renter.phone, f"📩 Pay your rent for {today.strftime('%B')}:\n{link}")