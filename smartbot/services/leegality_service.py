import json
import requests
from django.conf import settings

LEEGALITY_API_URL = "https://api.leegality.com/v3/document/upload"

def initiate_signature(renter, file_path):
    with open(file_path, 'rb') as f:
        files = {'file': ('agreement.pdf', f, 'application/pdf')}
        data = {
            "recipients": [{
                "name": renter.name,
                "email": renter.email,
                "phone": renter.phone,
                "signType": "esign",
                "allowEmailOTP": True,
                "workflowId": settings.LEEGALITY_WORKFLOW_ID
            }],
            "sendNow": True
        }
        headers = {
            "X-API-KEY": settings.LEEGALITY_API_KEY,
            "X-ORG-ID": settings.LEEGALITY_ORG_ID
        }
        response = requests.post(LEEGALITY_API_URL, files=files, data={"data": json.dumps(data)}, headers=headers)
        return response.json()