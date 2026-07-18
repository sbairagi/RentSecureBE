from typing import Any


class CashfreeAdapter:
    """Cashfree payout adapter.

    This adapter is disabled behind a feature flag
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
