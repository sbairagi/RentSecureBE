from datetime import date
from typing import Any

from django.core.management.base import BaseCommand

from properties.models import Renter, RentRecord
from shared.type_compat import override


class Command(BaseCommand):
    help = "Generate RentRecords for all active renters monthly"

    @override
    def handle(self, *args: Any, **kwargs: Any) -> None:
        today = date.today()
        month = today.month
        year = today.year

        renters = Renter.objects.filter(
            is_active=True, status__in=["active", "notice_period"]
        )

        for renter in renters:
            due_date = date(year, month, 1)
            exists = RentRecord.objects.filter(
                renter=renter, due_date=due_date
            ).exists()
            if exists:
                continue

            RentRecord.objects.create(
                renter=renter,
                unit=renter.unit,
                amount=renter.rent_amount,
                due_date=due_date,
                status=RentRecord.Status.PENDING,
                payout_status="PENDING",
            )
            self.stdout.write(f"RentRecord created for renter: {renter.name}")
