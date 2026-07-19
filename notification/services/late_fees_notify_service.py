from __future__ import annotations

import logging
from typing import Any

from notification.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def notify_renter_about_late_fee(rent: Any, late_fee: int | float) -> None:

    if rent.renter is None:
        return
    msg = (
        f"⚠️ You've paid rent late by ₹{late_fee}.\n"
        f"This has been added to next month's rent.\n\nReason: {rent.adjustment_reason}"
    )
    NotificationService().send_whatsapp_message(rent.renter.whatsapp_number or "", msg)


# Notify Owner
def notify_owner_about_late_fee(rent: Any, late_fee: int | float) -> None:

    if rent.renter is None or rent.renter.unit is None:
        return
    msg = (
        f"ℹ️ Your renter paid rent late by ₹{late_fee} "
        f"({rent.adjustment_reason}). We've added this to their next month's rent."
    )
    owner_number = rent.renter.unit.owner.whatsapp_number
    NotificationService().send_whatsapp_message(owner_number or "", msg)
