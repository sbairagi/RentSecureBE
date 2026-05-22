# utils/cashfree_payout.py
import requests
from django.conf import settings


def get_auth_token():
    url = f"{settings.CASHFREE_PAYOUT_BASE_URL}/payout/v1/authorize"
    res = requests.post(url, auth=(settings.CASHFREE_CLIENT_ID, settings.CASHFREE_CLIENT_SECRET))
    return res.json().get("data", {}).get("token")

def add_beneficiary(data):
    url = f"{settings.CASHFREE_PAYOUT_BASE_URL}/payout/v1/addBeneficiary"
    headers = {"Authorization": f"Bearer {get_auth_token()}"}
    res = requests.post(url, json=data, headers=headers)
    return res.json()

def make_payout(transfer_id, amount, remarks, bene_id):
    url = f"{settings.CASHFREE_PAYOUT_BASE_URL}/payout/v1/requestTransfer"
    headers = {"Authorization": f"Bearer {get_auth_token()}"}
    payload = {
        "beneId": bene_id,
        "amount": str(amount),
        "transferId": transfer_id,
        "transferMode": "IMPS",  # or "UPI"
        "remarks": remarks,
    }
    res = requests.post(url, json=payload, headers=headers)
    return res.json()
