from datetime import timedelta

from django.utils.timezone import now

from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import RentRecord
from rentsecure_be.services.cashfree_service import process_rent_payout


def retry_failed_payouts() -> None:
    failed_rents = RentRecord.objects.filter(
        payout_status="FAILED",
        payout_retries__lt=3,
    )

    for rent in failed_rents:
        if rent.last_payout_retry and now() - rent.last_payout_retry < timedelta(
            hours=6
        ):
            continue

        try:
            process_rent_payout(rent)
            rent.payout_retries += 1
            rent.last_payout_retry = now()
            rent.save()

            if rent.payout_status == "SUCCESS":
                owner = rent.renter.unit.owner if rent.renter else None
                if owner is None:
                    continue
                phone: str | None = getattr(owner, "whatsapp_number", None)

                if phone:
                    send_whatsapp_message(
                        phone,
                        (
                            f"✅ Rent ₹{rent.amount} has now been credited "
                            "to your account (after retry)."
                        ),
                    )

        except Exception as e:
            print(f"Payout retry failed for Rent ID {rent.id}: {e}")
