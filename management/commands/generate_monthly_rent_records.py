from datetime import date

from django.core.management.base import BaseCommand

from properties.models import Renter, RentRecord
from rentsecure_be.type_compat import override


class Command(BaseCommand):
    help = "Generate RentRecords for all active renters monthly"

    @override
    def handle(self, *args, **kwargs):
        today = date.today()
        month = today.month
        year = today.year

        renters = Renter.objects.filter(
            is_active=True, status__in=["active", "notice_period"]
        )

        for renter in renters:
            # Prevent duplicate rent record
            exists = RentRecord.objects.filter(
                renter=renter, rent_month__month=month, rent_month__year=year
            ).exists()
            if exists:
                continue

            RentRecord.objects.create(
                renter=renter,
                amount=renter.rent_amount,
                month=month,
                year=year,
                payment_status="PENDING",
                payout_status="PENDING",
            )
            self.stdout.write(f"RentRecord created for renter: {renter.name}")
