from typing import Any

from shared.ports.payment_gateway import PaymentGateway


class PaymentService:
    """Orchestration layer for payment operations.

    Delegates all payment operations to a configured PaymentGateway
    implementation. This service does not contain any payment provider
    logic or business rules.
    """

    def __init__(self, gateway: PaymentGateway) -> None:
        self._gateway = gateway

    def create_payment_link(self, rent_record: Any) -> str:
        return self._gateway.create_payment_link(rent_record)

    def process_payout(self, rent: Any) -> dict[str, Any]:
        return self._gateway.process_payout(rent)

    def register_beneficiary(self, bank_details: Any) -> dict[str, Any]:
        return self._gateway.register_beneficiary(bank_details)

    def delete_beneficiary(self, beneficiary_id: str) -> dict[str, Any]:
        return self._gateway.delete_beneficiary(beneficiary_id)
