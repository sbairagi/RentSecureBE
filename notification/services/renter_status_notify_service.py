from __future__ import annotations

import logging
from typing import Any

from notification.services.rent_notify_service import notify_renter

logger = logging.getLogger(__name__)

STATUS_MESSAGES: dict[str, str] = {
    "notice_period": (
        "You are now in NOTICE PERIOD. Please vacate the property " "within 30 days."
    ),
    "revoked": "Your rent agreement has been revoked due to payment default.",
    "deactivated": ("You have been deactivated and cannot make further payments."),
}


def send_renter_status_change_notification(
    renter: Any, old_status: str, new_status: str
) -> None:
    msg = STATUS_MESSAGES.get(new_status)
    if not msg:
        return

    try:
        notify_renter(renter, msg)
    except Exception:
        logger.exception(
            "Failed to send status change notification for renter %s",
            getattr(renter, "id", None),
        )
