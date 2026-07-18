from datetime import timedelta

from django.utils.timezone import now

from notification.services.whatsapp_service import send_whatsapp_message
from payments.adapters.cashfree import CashfreeAdapter
from payments.services.payment_service import PaymentService
from properties.models import RentRecord


def retry_failed_payouts() -> None:
    failed_rents = RentRecord.objects.filter(
        payout_status="FAILED",
        payout_retries__lt=3,
    )

    for rent in failed_rents:
        if _should_skip_retry(rent):
            continue
        _process_payout_retry(rent)


def _should_skip_retry(rent: RentRecord) -> bool:
    return (
        rent.last_payout_retry is not None
        and now() - rent.last_payout_retry < timedelta(hours=6)
    )


def _process_payout_retry(rent: RentRecord) -> None:
    try:
        PaymentService(CashfreeAdapter()).process_payout(rent)
    except Exception as e:
        print(f"Payout retry failed for Rent ID {rent.id}: {e}")
        return

    rent.payout_retries += 1
    rent.last_payout_retry = now()
    rent.save()

    if rent.payout_status == "SUCCESS":
        _notify_owner_on_successful_retry(rent)


def _notify_owner_on_successful_retry(rent: RentRecord) -> None:
    owner = rent.renter.unit.owner if rent.renter else None
    if owner is None:
        return
    phone: str | None = getattr(owner, "whatsapp_number", None)
    if phone:
        send_whatsapp_message(
            phone,
            (
                f"✅ Rent ₹{rent.amount} has now been credited "
                "to your account (after retry)."
            ),
        )
