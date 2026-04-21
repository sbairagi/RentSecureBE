from django.core.management.base import BaseCommand
from rent.models import Renter, RentRecord
from datetime import date

class Command(BaseCommand):
    help = "Generate RentRecords for all active renters monthly"

    def handle(self, *args, **kwargs):
        today = date.today()
        month = today.month
        year = today.year

        renters = Renter.objects.filter(is_active=True, status__in=["active", "notice_period"])

        for renter in renters:
            # Prevent duplicate rent record
            exists = RentRecord.objects.filter(renter=renter, month=month, year=year).exists()
            if exists:
                continue

            RentRecord.objects.create(
                renter=renter,
                amount=renter.rent_amount,
                month=month,
                year=year,
                payment_status="UNPAID",
                payout_status="PENDING"
            )
            self.stdout.write(f"RentRecord created for renter: {renter.name}")