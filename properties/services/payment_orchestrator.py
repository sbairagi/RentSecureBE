"""Payment orchestration for the properties domain.

Owns rent payment workflows so that views stay thin controllers.
Delegates provider selection and execution to an injected PaymentGateway.
No adapter imports allowed here.
"""

from __future__ import annotations

import logging
from typing import Any

from notification.services.notification_service import NotificationService
from notification.services.rent_notify_service import send_payout_notification
from shared.ports.payment_gateway import PaymentGateway

logger = logging.getLogger(__name__)

_payment_gateway: PaymentGateway | None = None


def set_payment_gateway(gateway: PaymentGateway) -> None:
    global _payment_gateway
    _payment_gateway = gateway


def get_payment_gateway() -> PaymentGateway:
    if _payment_gateway is None:
        raise RuntimeError("Payment gateway is not configured")
    return _payment_gateway


class PaymentOrchestrator:
    @staticmethod
    def create_payment_link(rent: Any) -> str:
        gateway = get_payment_gateway()
        link = gateway.create_payment_link(rent)
        rent.payment_link = link
        rent.save(update_fields=["payment_link"])
        phone = getattr(getattr(rent, "renter", None), "phone", None) or ""
        if phone:
            NotificationService().send_whatsapp_message(
                phone, f"📩 Pay your rent: {link}"
            )
        return link

    @staticmethod
    def retry_payout(rent: Any) -> dict[str, Any]:
        gateway = get_payment_gateway()
        result = gateway.process_payout(rent)
        rent.refresh_from_db()
        if rent.payout_status == "SUCCESS":
            send_payout_notification(rent)
        return result
