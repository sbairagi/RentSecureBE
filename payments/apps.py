from __future__ import annotations

from django.apps import AppConfig

from shared.type_compat import override


class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payments"

    @override
    def ready(self) -> None:
        from payments.adapters.manual import ManualPaymentAdapter
        from payments.services.payment_service import PaymentService
        from properties.services.payment_orchestrator import set_payment_gateway

        set_payment_gateway(PaymentService(ManualPaymentAdapter()))
