from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import requests

from django.conf import settings

from rentsecure_be.utils.cashfree_payout import (
    add_beneficiary,
    get_auth_token,
    make_payout,
)

if TYPE_CHECKING:
    from core.models import OwnerBankDetails
    from rentsecure_be.rent_record_models import RentRecord

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
    bene_id = f"owner_{bank_details.owner.id}"

    payload = {
        "beneId": bene_id,
        "name": bank_details.owner.get_full_name(),
        "email": bank_details.owner.email,
        "phone": (
            getattr(
                getattr(bank_details.owner, "profile", None), "whatsapp_number", None
            )
            or bank_details.owner.phone
        ),
        "bankAccount": bank_details.bank_account_number,
        "ifsc": bank_details.ifsc_code,
        "address1": "India",
    }

    response = add_beneficiary(payload)

    if response.get("status") == "SUCCESS":
        bank_details.beneficiary_id = bene_id
        bank_details.bank_account_verified = True
        bank_details.save()

    return response


def process_rent_payout(rent: RentRecord) -> dict[str, Any]:
    from core.models import OwnerBankDetails
    from notification.services.rent_notify_service import (
        notify_owner_post_payout,
        send_payout_notification,
    )

    if not isinstance(rent, RentRecord):
        raise TypeError("rent must be a RentRecord instance")
    owner = rent.renter.unit.owner if rent.renter else None
    if owner is None:
        rent.payout_status = "FAILED"
        rent.save(update_fields=["payout_status"])
        return {"status": "FAILED", "message": "Owner not found for rent"}

    try:
        bank_details = OwnerBankDetails.objects.get(owner=owner)
    except OwnerBankDetails.DoesNotExist:
        logger.warning(f"No bank details found for owner {owner.id} (rent {rent.id})")
        rent.payout_status = "FAILED"
        rent.save(update_fields=["payout_status"])
        return {"status": "FAILED", "message": "Owner bank details not found"}

    if not bank_details.beneficiary_id:
        logger.warning(f"No beneficiary_id for owner {owner.id} (rent {rent.id})")
        rent.payout_status = "FAILED"
        rent.save(update_fields=["payout_status"])
        return {
            "status": "FAILED",
            "message": "Owner not yet registered as beneficiary",
        }

    transfer_id = f"rent_{rent.id}"
    try:
        response = make_payout(
            transfer_id=transfer_id,
            amount=rent.amount_paid,
            remarks="Monthly rent payout",
            bene_id=bank_details.beneficiary_id,
        )
    except Exception as e:
        logger.exception(f"Cashfree payout API error for rent {rent.id}: {e}")
        rent.payout_status = "FAILED"
        rent.save(update_fields=["payout_status"])
        return {"status": "FAILED", "message": str(e)}

    if response.get("status") == "SUCCESS":
        rent.payout_status = "SUCCESS"
        rent.payout_reference = transfer_id
    else:
        rent.payout_status = "FAILED"

    rent.save(update_fields=["payout_status", "payout_reference"])

    try:
        notify_owner_post_payout(rent)
    except Exception as e:
        logger.warning(f"Failed to notify owner after payout for rent {rent.id}: {e}")

    try:
        send_payout_notification(rent)
    except Exception as e:
        logger.warning(f"Failed to send payout notification for rent {rent.id}: {e}")

    return response


BASE_URL = ""


def delete_beneficiary(beneficiary_id: str) -> dict[str, Any]:
    url = f"{settings.CASHFREE_PAYOUT_BASE_TEST_URL}/payout/v1/deleteBeneficiary"
    payload = {"beneId": beneficiary_id}
    headers = {
        "Authorization": f"Bearer {get_auth_token()}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    data: dict[str, Any] = response.json()
    return data
