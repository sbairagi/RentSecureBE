from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from payments.adapters.cashfree import CashfreeAdapter
from payments.services.payment_service import PaymentService

if TYPE_CHECKING:
    from core.models import OwnerBankDetails
    from properties.models.rent_record_models import RentRecord  # nosonar

logger = logging.getLogger(__name__)


def register_owner_with_cashfree(owner: OwnerBankDetails) -> None:
    from core.models import OwnerBankDetails

    if not isinstance(owner, OwnerBankDetails):
        raise TypeError("owner must be an OwnerBankDetails instance")
    bene_id = f"owner_{owner.id}"

    data = {
        "beneId": bene_id,
        "name": owner.owner.get_full_name(),
        "email": owner.owner.email,
        "phone": owner.owner.phone,
        "bankAccount": owner.bank_account_number,
        "ifsc": owner.ifsc_code,
        "address1": "India",  # optional
    }
    from payments.utils.cashfree_payout import add_beneficiary

    response = add_beneficiary(data)

    if response.get("status") == "SUCCESS":
        owner.beneficiary_id = bene_id
        owner.bank_account_verified = True
        owner.save()


def pay_owner_after_rent(rent: RentRecord) -> dict[str, Any]:
    from core.models import OwnerBankDetails
    from notification.services.rent_notify_service import notify_owner, notify_renter

    if rent.payout_status == "SUCCESS":
        return {"status": "ALREADY_PAID", "message": "Payout already completed"}

    owner = rent.renter.unit.owner if rent.renter else None
    if owner is None:
        raise ValueError("Owner not found for rent")

    try:
        bank_details = OwnerBankDetails.objects.get(owner=owner)
    except OwnerBankDetails.DoesNotExist:
        raise ValueError("Owner not registered with Cashfree") from None

    if not bank_details.beneficiary_id:
        raise ValueError("Owner not registered with Cashfree")

    transfer_id = f"rent_{rent.id}"
    from payments.utils.cashfree_payout import make_payout

    response = make_payout(
        transfer_id=transfer_id,
        amount=rent.amount_paid,
        remarks=f"Rent for property {rent.unit.id}",
        bene_id=bank_details.beneficiary_id,
    )

    if response.get("status") == "SUCCESS":
        rent.payout_status = "SUCCESS"
        rent.payout_reference = transfer_id
    else:
        rent.payout_status = "FAILED"

    rent.save()

    if rent.payout_status == "SUCCESS":
        msg_renter = (
            f"✅ Aapka ₹{rent.amount_paid} rent {rent.updated_at.date()} "
            "ko jama ho gaya hai."
        )
        notify_renter(rent.renter, msg_renter)

        msg_owner = (
            f"🎉 ₹{rent.amount_paid} rent {rent.updated_at.date()} "
            "ko aapke account mein transfer ho gaya hai."
        )
        notify_owner(owner, msg_owner)
    elif rent.payout_status == "FAILED":
        msg = (
            f"⚠️ ₹{rent.amount_paid} rent ka transfer fail ho gaya hai. "
            f"Kripya apna bank detail verify karein."
        )
        notify_renter(rent.renter, msg)

    _send_whatsapp_payout_alert(rent)
    return response


def _send_whatsapp_payout_alert(rent: RentRecord) -> None:
    from notification.services.rent_notify_service import send_payout_notification

    if rent.renter is None:
        return
    owner = rent.renter.unit.owner
    profile = getattr(owner, "profile", None)
    phone = getattr(profile, "whatsapp_number", None)
    if phone:
        send_payout_notification(rent)


def register_cashfree_beneficiary(bank_details: OwnerBankDetails) -> dict[str, Any]:
    from core.models import OwnerBankDetails

    if not isinstance(bank_details, OwnerBankDetails):
        raise TypeError("bank_details must be an OwnerBankDetails instance")

    return PaymentService(CashfreeAdapter()).register_beneficiary(bank_details)


def process_rent_payout(rent: RentRecord) -> dict[str, Any]:

    if not isinstance(rent, RentRecord):
        raise TypeError("rent must be a RentRecord instance")

    return PaymentService(CashfreeAdapter()).process_payout(rent)


BASE_URL = ""


def delete_beneficiary(beneficiary_id: str) -> dict[str, Any]:
    return PaymentService(CashfreeAdapter()).delete_beneficiary(beneficiary_id)
