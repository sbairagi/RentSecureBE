import logging

from services.notifications import send_push_notification
from services.sms_service import send_sms

from notification.services.whatsapp_service import send_whatsapp_message

logger = logging.getLogger(__name__)


def send_smart_alert(user, message, title=None, urgent=False):
    status = {"whatsapp": False, "push": False, "sms": False}

    if user.profile.whatsapp_opt_in and user.profile.whatsapp_number:
        status["whatsapp"] = send_whatsapp_message(
            user.profile.whatsapp_number, message
        )

    device_token = getattr(user, "device_token", None)
    if device_token:
        status["push"] = send_push_notification(
            user, title or "RentSecure Alert", message
        )

    if not any(status.values()) or urgent:
        status["sms"] = send_sms(user.profile.phone, message)

    return status


# # Rent due alert example
# send_smart_alert(rent.renter.user, f"Rent ₹{rent.amount} is due tomorrow.", title="🏠 Rent Due")

# # Payout failed alert
# send_smart_alert(
#     rent.renter.property.owner,
#     "⚠️ Rent payout failed. Please update your bank details.",
#     urgent=True
# )
