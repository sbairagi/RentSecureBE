from __future__ import annotations

from shared.ports.payment_gateway import PaymentGateway


class PaymentProviderFactory:
    @staticmethod
    def create(provider: str) -> PaymentGateway:
        provider = provider.lower()
        if provider == "razorpay":
            from payments.adapters.razorpay import RazorpayAdapter

            return RazorpayAdapter()
        if provider == "cashfree":
            from payments.adapters.cashfree import CashfreeAdapter

            return CashfreeAdapter()
        from payments.adapters.manual import ManualPaymentAdapter

        return ManualPaymentAdapter()
