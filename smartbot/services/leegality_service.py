import json
from typing import Any

import requests
from django.conf import settings

LEEGALITY_API_URL = "https://api.leegality.com/v3/document/upload"
LEEGALITY_DOCUMENT_URL = "https://api.leegality.com/v3/document"


def initiate_signature(renter: dict[str, Any], file_path: str) -> dict[str, Any]:
    with open(file_path, "rb") as f:
        files = {"file": ("agreement.pdf", f, "application/pdf")}
        data = {
            "recipients": [
                {
                    "name": renter.name,
                    "email": renter.email,
                    "phone": renter.phone,
                    "signType": "esign",
                    "allowEmailOTP": True,
                    "workflowId": settings.LEEGALITY_WORKFLOW_ID,
                }
            ],
            "sendNow": True,
        }
        headers = {
            "X-API-KEY": settings.LEEGALITY_API_KEY,
            "X-ORG-ID": settings.LEEGALITY_ORG_ID,
        }
        response = requests.post(
            LEEGALITY_API_URL,
            files=files,
            data={"data": json.dumps(data)},
            headers=headers,
            timeout=10,
        )
        data: dict[str, Any] = response.json()
    return data


def check_signature_status(signature_request_id: str) -> str | None:
    headers = {
        "X-API-KEY": settings.LEEGALITY_API_KEY,
        "X-ORG-ID": settings.LEEGALITY_ORG_ID,
    }
    response = requests.get(
        f"{LEEGALITY_DOCUMENT_URL}/{signature_request_id}",
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    raw_status = data.get("status") or data.get("documentStatus")
    return str(raw_status) if raw_status is not None else None
