from ..models import Notification
from ..utils import send_whatsapp_message

# Use Cases Integration

# Example: Rent Created

# notify_user(
#     user=rent.renter.user,
#     title="📩 New Rent Due",
#     message=(
#         f"₹{rent.amount} rent due for {rent.month}/{rent.year}. "
#         "Please pay using the link."
#     )
# )

# Payout Success

# notify_user(
#     user=rent.renter.property.owner,
#     title="✅ Rent Payout Credited",
#     message=f"Rent ₹{rent.amount} has been credited to your account."
# )

# Payout Failed

# notify_user(
#     user=rent.renter.property.owner,
#     title="⚠️ Rent Payout Failed",
#     message=f"Payout for ₹{rent.amount} failed. Retry or check bank details."
# )


def notify_user(user, title, message):
    Notification.objects.create(user=user, title=title, message=message)


def notify_owner_renter_flagged(renter):
    owner = renter.property.owner
    msg = (
        f"🚨 Alert: Renter {renter.name} missed 3 rent payments. "
        "Their rent agreement has been revoked."
    )
    send_whatsapp_message(owner.profile.whatsapp_number, msg)
