from __future__ import annotations

# utils/cashfree_payout.py
from typing import Any

import requests

from django.conf import settings


def get_auth_token() -> str | None:
    url = f"{settings.CASHFREE_PAYOUT_BASE_URL}/payout/v1/authorize"
    res = requests.post(
        url,
        auth=(settings.CASHFREE_CLIENT_ID, settings.CASHFREE_CLIENT_SECRET),
        timeout=10,
    )
    data: dict[str, Any] = res.json()
    token: str | None = data.get("data", {}).get("token") or None
    return token


def add_beneficiary(data: dict[str, Any]) -> dict[str, Any]:
    url = f"{settings.CASHFREE_PAYOUT_BASE_URL}/payout/v1/addBeneficiary"
    headers = {"Authorization": f"Bearer {get_auth_token()}"}
    res = requests.post(url, json=data, headers=headers, timeout=10)
    data: dict[str, Any] = res.json()
    return data


def make_payout(
    transfer_id: str, amount: float, remarks: str, bene_id: str
) -> dict[str, Any]:
    url = f"{settings.CASHFREE_PAYOUT_BASE_URL}/payout/v1/requestTransfer"
    headers = {"Authorization": f"Bearer {get_auth_token()}"}
    payload = {
        "beneId": bene_id,
        "amount": str(amount),
        "transferId": transfer_id,
        "transferMode": "IMPS",  # or "UPI"
        "remarks": remarks,
    }
    res = requests.post(url, json=payload, headers=headers, timeout=10)
    data: dict[str, Any] = res.json()
    return data
