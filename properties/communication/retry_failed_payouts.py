from datetime import timedelta

from communication.utils import send_whatsapp_message
from django.utils.timezone import now

from properties.models import RentRecord
from rentsecure_be.services.cashfree_service import process_rent_payout


def retry_failed_payouts():
    failed_rents = RentRecord.objects.filter(
        payment_status="PAID",
        payout_status="FAILED",
        payout_retries__lt=3  # Limit retry attempts
    )

    for rent in failed_rents:
        # Optional: Wait at least 6 hrs from last retry
        if rent.last_payout_retry and now() - rent.last_payout_retry < timedelta(hours=6):
            continue

        try:
            response = process_rent_payout(rent)
            rent.payout_retries += 1
            rent.last_payout_retry = now()
            rent.save()

            # Notify owner again if successful
            if rent.payout_status == "SUCCESS":
                owner = rent.renter.property.owner
                phone = owner.profile.whatsapp_number  # Make sure this is stored in +91 format

                if phone:
                    owner = rent.renter.property.owner
                    send_whatsapp_message(
                        owner.profile.whatsapp_number,
                        f"✅ Rent ₹{rent.amount} has now been credited to your account (after retry)."
                    )

        except Exception as e:
            print(f"Payout retry failed for Rent ID {rent.id}: {e}")
