import logging

import requests
from notifications.models import DeviceToken

logger = logging.getLogger(__name__)


def send_push_notification(user, title, message):
    try:
        token = DeviceToken.objects.get(user=user).token
        payload = {
            "to": token,
            "sound": "default",
            "title": title,
            "body": message
        }
        headers = {"Content-Type": "application/json"}
        requests.post(
            "https://exp.host/--/api/v2/push/send",
            json=payload,
            headers=headers,
            timeout=10,
        )
    except Exception as e:
        logger.exception(f"Failed to send push notification to user {user.id}: {e}")


# # Rent paid
# send_push_notification(rent.renter.user, "✅ Rent Paid", f"Your rent ₹{rent.amount} has been paid.")

# # Agreement signed
# send_push_notification(rent.renter.user, "📝 Agreement Signed", "Thanks for signing the rent agreement.")
