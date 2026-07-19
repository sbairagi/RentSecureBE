from datetime import date

from notification.services.notification_service import NotificationService
from payments.adapters.razorpay import RazorpayAdapter
from payments.services.payment_service import PaymentService
from properties.models import Renter, RentRecord


def auto_generate_rent_records() -> None:
    today = date.today()
    renters = Renter.objects.all()

    for renter in renters:
        rent, created = RentRecord.objects.get_or_create(
            renter=renter,
            due_date__month=today.month,
            due_date__year=today.year,
            defaults={"amount": renter.rent_amount},
        )

        if created:
            link = PaymentService(RazorpayAdapter()).create_payment_link(rent)
            rent.payment_link = link
            rent.save()

            NotificationService().send_whatsapp_message(
                renter.phone, f"📩 Pay your rent for {today.strftime('%B')}:\n{link}"
            )
