from __future__ import annotations

import logging
from typing import Any

import requests

from django.conf import settings

logger = logging.getLogger(__name__)


def _get_auth_token() -> str:
    from rentsecure_be.utils.cashfree_payout import get_auth_token  # nosonar

    return get_auth_token()


def _add_beneficiary(data: dict[str, Any]) -> dict[str, Any]:
    from rentsecure_be.utils.cashfree_payout import add_beneficiary  # nosonar

    return add_beneficiary(data)


def _make_payout(
    transfer_id: str,
    amount: float,
    remarks: str,
    bene_id: str,
) -> dict[str, Any]:
    from rentsecure_be.utils.cashfree_payout import make_payout  # nosonar

    return make_payout(
        transfer_id=transfer_id,
        amount=amount,
        remarks=remarks,
        bene_id=bene_id,
    )


def _resolve_owner(rent: Any) -> Any | None:
    renter = getattr(rent, "renter", None)
    return renter.unit.owner if renter is not None else None


def _load_bank_details(owner: Any, rent: Any) -> Any | None:
    from core.models import OwnerBankDetails

    try:
        bank_details = OwnerBankDetails.objects.get(owner=owner)
    except OwnerBankDetails.DoesNotExist:
        logger.warning(f"No bank details found for owner {owner.id} (rent {rent.id})")
        rent.payout_status = "FAILED"
        if hasattr(rent, "save"):
            rent.save(update_fields=["payout_status"])
        return None

    if not bank_details.beneficiary_id:
        logger.warning(f"No beneficiary_id for owner {owner.id} (rent {rent.id})")
        rent.payout_status = "FAILED"
        if hasattr(rent, "save"):
            rent.save(update_fields=["payout_status"])
        return None

    return bank_details


def _execute_payout(rent: Any, bank_details: Any) -> dict[str, Any]:
    transfer_id = f"rent_{rent.id}"
    try:
        return _make_payout(
            transfer_id=transfer_id,
            amount=rent.amount_paid,
            remarks="Monthly rent payout",
            bene_id=bank_details.beneficiary_id,
        )
    except Exception as exc:
        logger.exception(f"Cashfree payout API error for rent {rent.id}: {exc}")
        rent.payout_status = "FAILED"
        if hasattr(rent, "save"):
            rent.save(update_fields=["payout_status"])
        return {"status": "FAILED", "message": str(exc)}


def _apply_payout_status(rent: Any, response: dict[str, Any]) -> None:
    if response.get("status") == "SUCCESS":
        rent.payout_status = "SUCCESS"
        rent.payout_reference = f"rent_{rent.id}"
    else:
        rent.payout_status = "FAILED"

    if hasattr(rent, "save"):
        rent.save(update_fields=["payout_status", "payout_reference"])


def _notify_payout_success(rent: Any) -> None:
    from notification.services.rent_notify_service import (
        notify_owner_post_payout,
        notify_renter,
    )

    try:
        notify_owner_post_payout(rent)
    except Exception as exc:
        logger.warning(f"Failed to notify owner after payout for rent {rent.id}: {exc}")

    try:
        msg_renter = (
            f"✅ Aapka ₹{rent.amount_paid} rent {rent.updated_at.date()} "
            "ko jama ho gaya hai."
        )
        notify_renter(rent.renter, msg_renter)
    except Exception as exc:
        logger.warning(f"Failed to send payout notification for rent {rent.id}: {exc}")


def _notify_renter_failure(rent: Any) -> None:
    from notification.services.rent_notify_service import notify_renter

    try:
        msg = (
            f"⚠️ ₹{rent.amount_paid} rent ka transfer fail ho gaya hai. "
            f"Kripya apna bank detail verify karein."
        )
        notify_renter(rent.renter, msg)
    except Exception as exc:
        logger.warning(f"Failed to send payout notification for rent {rent.id}: {exc}")


class CashfreeAdapter:
    """Cashfree payout adapter.

    Implements PaymentGateway using the existing Cashfree payout
    helper utilities.
    """

    def create_payment_link(self, rent_record: Any) -> str:
        raise NotImplementedError

    def process_payout(self, rent: Any) -> dict[str, Any]:
        if not hasattr(rent, "payout_status"):
            raise TypeError("rent must be a RentRecord-like instance")

        if rent.payout_status == "SUCCESS":
            return {"status": "ALREADY_PAID", "message": "Payout already completed"}

        owner = _resolve_owner(rent)
        if owner is None:
            return {"status": "FAILED", "message": "Owner not found for rent"}

        bank_details = _load_bank_details(owner, rent)
        if bank_details is None:
            return {"status": "FAILED", "message": "Owner not registered with Cashfree"}

        response = _execute_payout(rent, bank_details)
        _apply_payout_status(rent, response)

        if response.get("status") == "SUCCESS":
            _notify_payout_success(rent)
        else:
            _notify_renter_failure(rent)

        return response

    def register_beneficiary(self, bank_details: Any) -> dict[str, Any]:
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
                    getattr(bank_details.owner, "profile", None),
                    "whatsapp_number",
                    None,
                )
                or bank_details.owner.phone
            ),
            "bankAccount": bank_details.bank_account_number,
            "ifsc": bank_details.ifsc_code,
            "address1": "India",
        }

        response = _add_beneficiary(payload)

        if response.get("status") == "SUCCESS":
            bank_details.beneficiary_id = bene_id
            bank_details.bank_account_verified = True
            bank_details.save()

        return response

    def delete_beneficiary(self, beneficiary_id: str) -> dict[str, Any]:
        url = f"{settings.CASHFREE_PAYOUT_BASE_TEST_URL}" "/payout/v1/deleteBeneficiary"
        payload = {"beneId": beneficiary_id}
        headers = {
            "Authorization": f"Bearer {_get_auth_token()}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        return dict(response.json())
