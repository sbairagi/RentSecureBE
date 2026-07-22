from __future__ import annotations

import logging
from typing import Any

from core.models import OwnerBankDetails, User
from core.services.base import BaseService, ServiceResult
from payments.utils.cashfree_payout import add_beneficiary
from properties.models.rent_record_models import RentRecord
from shared.type_compat import override

logger = logging.getLogger(__name__)


class BankDetailsService(BaseService):
    @staticmethod
    def validate_fields(data: dict[str, Any]) -> None:
        required_fields = ["account_number", "ifsc_code", "account_holder_name"]
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

    @staticmethod
    def get_existing_bank(owner: User) -> OwnerBankDetails | None:
        return OwnerBankDetails.objects.filter(owner=owner).first()

    @staticmethod
    def register_beneficiary(owner: User, data: dict[str, Any]) -> dict[str, Any]:
        bene_id = f"owner_{owner.pk}_{data.get('bene_id_suffix', '')}"
        payload = {
            "beneId": bene_id,
            "name": data["account_holder_name"],
            "phone": owner.phone or "",
            "email": owner.email or "",
            "bankAccount": data["account_number"],
            "ifsc": data["ifsc_code"],
            "address1": "India",
        }
        return add_beneficiary(payload)

    @staticmethod
    def save_bank_details(
        bank: OwnerBankDetails, data: dict[str, Any], beneficiary_id: str
    ) -> OwnerBankDetails:
        bank.bank_account_number = data["account_number"]
        bank.ifsc_code = data["ifsc_code"]
        bank.beneficiary_id = beneficiary_id
        bank.save()
        return bank

    @staticmethod
    def retry_failed_payouts(owner: User) -> None:
        RentRecord.objects.filter(unit__owner=owner, payout_status="FAILED").update(
            payout_status="PENDING"
        )

    @override
    def execute(self, *args: Any, **kwargs: Any) -> ServiceResult[Any]:
        raise NotImplementedError
