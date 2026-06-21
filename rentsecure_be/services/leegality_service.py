from typing import Any

import requests
from django.conf import settings

LEEGALITY_URL = "https://sandbox.leegality.com/api/v3/document"


def send_agreement_for_signature(
    agreement: Any, owner_email: str, renter_email: str | None = None
) -> dict[str, Any]:
    headers = {
        "X-API-KEY": settings.LEEGALITY_API_KEY,
        "X-ORG-ID": settings.LEEGALITY_ORG_ID,
        "Content-Type": "application/json",
    }

    template_id = settings.LEEGALITY_TEMPLATE_ID or settings.LEEGALITY_WORKFLOW_ID
    if not template_id:
        raise ValueError("Leegality template/workflow ID is not configured.")

    owner_name = getattr(agreement.user, "get_full_name", None)
    if callable(owner_name):
        owner_display_name = owner_name()
    else:
        owner_display_name = agreement.user.username

    data = {
        "template_id": template_id,
        "participants": [
            {
                "name": owner_display_name,
                "email": owner_email,
                "signing_order": 1,
                "identifier": "OWNER",
            }
        ],
        "display_on_page": "both",
    }

    if renter_email:
        data["participants"].append(
            {
                "name": agreement.renter.name,
                "email": renter_email,
                "signing_order": 2,
                "identifier": "RENTER",
            }
        )

    response = requests.post(LEEGALITY_URL, headers=headers, json=data, timeout=10)
    response.raise_for_status()
    resp_json: dict[str, Any] = response.json()

    agreement.leegality_document_id = (
        resp_json.get("document_id")
        or resp_json.get("documentId")
        or resp_json.get("documentKey")
    )
    agreement.save(update_fields=["leegality_document_id"])
    return resp_json
