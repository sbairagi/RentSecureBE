# Legacy implementation archived

######################################################################################################################




from django.core.management.base import BaseCommand
from rent.models import RentRecord
from rent.services import process_rent_payout


class Command(BaseCommand):
    help = "Retry failed payouts for paid rent records"

    def handle(self, *args, **kwargs):
        failed_rents = RentRecord.objects.filter(
            payment_status="PAID",
            payout_status="FAILED",
            retry_count__lt=3  # 👈 Limit max retries
        )

        for rent in failed_rents:
            try:
                self.stdout.write(f"Retrying payout for Rent ID: {rent.id}")
                process_rent_payout(rent)
                rent.retry_count += 1
                rent.save()
            except Exception as e:
                self.stderr.write(f"Error: {e}")
