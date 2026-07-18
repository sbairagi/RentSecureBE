from typing import Any


class ManualPaymentAdapter:
    """Year 1 manual UPI payment adapter.

    This adapter represents the current manual payment flow
    and will be implemented in a later task.
    """

    def create_payment_link(self, rent_record: Any) -> str:
        raise NotImplementedError

    def process_payout(self, rent: Any) -> dict[str, Any]:
        raise NotImplementedError

    def register_beneficiary(self, bank_details: Any) -> dict[str, Any]:
        raise NotImplementedError

    def delete_beneficiary(self, beneficiary_id: str) -> dict[str, Any]:
        raise NotImplementedError
