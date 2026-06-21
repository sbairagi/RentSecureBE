import logging
from typing import Any

from notification.services.notifications import send_push_notification
from notification.services.sms_service import send_sms
from notification.services.whatsapp_service import send_whatsapp_message

logger = logging.getLogger(__name__)


def send_smart_alert(
    user: Any, message: str, title: str | None = None, urgent: bool = False
) -> dict[str, bool]:
    status: dict[str, bool] = {"whatsapp": False, "push": False, "sms": False}

    user_profile = getattr(user, "userprofile", None)
    if user_profile and user_profile.whatsapp_opt_in and user_profile.whatsapp_number:
        status["whatsapp"] = send_whatsapp_message(
            user_profile.whatsapp_number, message
        )

    device_token: str | None = getattr(user, "device_token", None)
    if device_token:
        status["push"] = (
            send_push_notification(user, title or "RentSecure Alert", message) or False
        )

    if not any(status.values()) or urgent:
        status["sms"] = send_sms(user.phone, message)

    return status


# # Rent due alert example
# send_smart_alert(
#     rent.renter.user,
#     f"Rent ₹{rent.amount} is due tomorrow.",
#     title="🏠 Rent Due",
# )

# # Payout failed alert
# send_smart_alert(
#     rent.renter.property.owner,
#     "⚠️ Rent payout failed. Please update your bank details.",
#     urgent=True
# )
