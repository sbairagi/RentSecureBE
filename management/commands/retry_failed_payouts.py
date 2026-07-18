from typing import Any

from django.core.management.base import BaseCommand

from payments.adapters.cashfree import CashfreeAdapter
from payments.services.payment_service import PaymentService
from properties.models import RentRecord
from shared.type_compat import override


class Command(BaseCommand):
    help = "Retry failed payouts for paid rent records"

    @override
    def handle(self, *args: Any, **kwargs: Any) -> None:
        payment_service = PaymentService(CashfreeAdapter())
        failed_rents = RentRecord.objects.filter(
            status="PAID",
            payout_status="FAILED",
            payout_retry_count__lt=3,
        )

        for rent in failed_rents:
            try:
                self.stdout.write(f"Retrying payout for Rent ID: {rent.id}")
                payment_service.process_payout(rent)
                rent.payout_retry_count += 1
                rent.save(update_fields=["payout_retry_count"])
            except Exception as e:
                self.stderr.write(f"Error: {e}")
