# services/cashfree_service.py
from core.models import OwnerBankDetails
from notification.services.rent_notify_service import (
    notify_owner,
    notify_owner_post_payout,
    notify_renter,
    send_payout_notification,
)
from properties.models import RentRecord
from rentsecure_be.utils.cashfree_payout import add_beneficiary, make_payout

# from core.models import

def register_owner_with_cashfree(owner: OwnerBankDetails):
    bene_id = f"owner_{owner.id}"

    data = {
        "beneId": bene_id,
        "name": owner.user.get_full_name(),
        "email": owner.user.email,
        "phone": owner.user.phone_number,
        "bankAccount": owner.bank_account_number,
        "ifsc": owner.ifsc_code,
        "address1": "India",  # optional
    }
    response = add_beneficiary(data)

    if response.get("status") == "SUCCESS":
        owner.beneficiary_id = bene_id
        owner.bank_account_verified = True
        owner.save()
    return



def pay_owner_after_rent(rent: RentRecord):
    if not rent.owner.beneficiary_id:
        raise Exception("Owner not registered with Cashfree")

    transfer_id = f"rent_{rent.id}"
    response = make_payout(
        transfer_id=transfer_id,
        amount=rent.amount,
        remarks=f"Rent for property {rent.property.id}",
        bene_id=rent.owner.beneficiary_id
    )

    # Save result
    if response.get("status") == "SUCCESS":
        rent.payout_status = "SUCCESS"
        rent.payout_reference = transfer_id
    else:
        rent.payout_status = "FAILED"


    if rent.payout_status == "SUCCESS":
        # msg = f"Namaste! Aapka ₹{rent.amount} rent {rent.updated_at.date()} ko jama hua hai."
        # notify_renter(rent.renter, msg)
        msg_renter = f"✅ Aapka ₹{rent.amount} rent {rent.updated_at.date()} ko jama ho gaya hai."
        notify_renter(rent.renter, msg_renter)

        msg_owner = f"🎉 ₹{rent.amount} rent {rent.updated_at.date()} ko aapke account mein transfer ho gaya hai."
        notify_owner(rent.owner, msg_owner)

    elif rent.payout_status == "FAILED":
        msg = (
            f"⚠️ ₹{rent.amount} rent ka transfer fail ho gaya hai. "
            f"Kripya apna bank detail verify karein."
        )
        notify_renter(rent.renter, msg)

    rent = rent.save()

    # 🔔 WhatsApp Alert After Saving
    owner = rent.renter.property.owner
    phone = owner.profile.whatsapp_number  # Make sure this is stored in +91 format

    if phone:
        send_payout_notification(rent)
    return response


def register_cashfree_beneficiary(bank_details: OwnerBankDetails):
    bene_id = f"owner_{bank_details.owner.id}"

    payload = {
        "beneId": bene_id,
        "name": bank_details.owner.get_full_name(),
        "email": bank_details.owner.email,
        "phone": bank_details.owner.profile.phone_number,  # adjust as per your model
        "bankAccount": bank_details.bank_account_number,
        "ifsc": bank_details.ifsc_code,
        "address1": "India"
    }

    response = add_beneficiary(payload)

    if response.get("status") == "SUCCESS":
        bank_details.beneficiary_id = bene_id
        bank_details.bank_account_verified = True
        bank_details.save()

    return response



def process_rent_payout(rent: RentRecord):
    bank_details = OwnerBankDetails.objects.get(owner=rent.renter.property.owner)

    if not bank_details.beneficiary_id:
        raise Exception("Owner not yet registered as beneficiary")

    transfer_id = f"rent_{rent.id}"
    response = make_payout(
        transfer_id=transfer_id,
        amount=rent.amount,
        remarks="Monthly rent payout",
        bene_id=bank_details.beneficiary_id
    )

    # Set initial status
    if response.get("status") == "SUCCESS":
        rent.payout_status = "SUCCESS"
        rent.payout_reference = transfer_id
    else:
        rent.payout_status = "FAILED"

    rent = rent.save()
    notify_owner_post_payout(rent)

    # 🔔 WhatsApp Alert After Saving
    owner = rent.renter.property.owner
    phone = owner.profile.whatsapp_number  # Make sure this is stored in +91 format

    if phone:
        send_payout_notification(rent)

    return response


BASE_URL = ''
import requests
from django.conf import settings


# cashfree_service.py
def delete_beneficiary(beneficiary_id: str):
    from .cashfree_service import get_auth_token
    url = f"{settings.CASHFREE_PAYOUT_BASE_TEST_URL}/payout/v1/deleteBeneficiary"
    payload = {
        "beneId": beneficiary_id
    }
    headers = {
        "Authorization": f"Bearer {get_auth_token()}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
