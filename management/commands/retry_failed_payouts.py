# # management/commands/retry_failed_payouts.py

# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from rent.models import RentRecord
# from rent.services.cashfree_service import make_payout

# class Command(BaseCommand):
#     help = 'Retry failed rent payouts'

#     def handle(self, *args, **kwargs):
#         failed_rents = RentRecord.objects.filter(payout_status='FAILED', payout_retry_count__lt=3)
#         for rent in failed_rents:
#             try:
#                 transfer_id = f"rent_{rent.id}_retry{rent.payout_retry_count + 1}"
#                 response = make_payout(
#                     transfer_id=transfer_id,
#                     amount=rent.amount,
#                     remarks="Rent payout retry",
#                     bene_id=rent.renter.property.ownerbankdetails.beneficiary_id
#                 )

#                 if response.get("status") == "SUCCESS":
#                     rent.payout_status = "SUCCESS"
#                     rent.payout_reference = transfer_id
#                 else:
#                     rent.payout_retry_count += 1
#                     rent.last_retry_on = timezone.now()

#                 rent.save()
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"Error retrying payout: {str(e)}"))

# first approch

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
