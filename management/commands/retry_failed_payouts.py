# Legacy implementation archived

######################################################################################################################


from django.core.management.base import BaseCommand

from properties.models import RentRecord
from rentsecure_be.services.cashfree_service import process_rent_payout
from rentsecure_be.type_compat import override


class Command(BaseCommand):
    help = "Retry failed payouts for paid rent records"

    @override
    def handle(self, *args, **kwargs):
        failed_rents = RentRecord.objects.filter(
            status="PAID",
            payout_status="FAILED",
            payout_retry_count__lt=3,
        )

        for rent in failed_rents:
            try:
                self.stdout.write(f"Retrying payout for Rent ID: {rent.id}")
                process_rent_payout(rent)
                rent.payout_retry_count += 1
                rent.save(update_fields=["payout_retry_count"])
            except Exception as e:
                self.stderr.write(f"Error: {e}")
