from typing import Any

from ..models import Notification
from ..utils import send_whatsapp_message


def notify_user(user: Any, title: str, message: str) -> None:
    Notification.objects.create(user=user, title=title, message=message)


def notify_owner_renter_flagged(renter: Any) -> None:
    owner = renter.property.owner
    msg = (
        f"🚨 Alert: Renter {renter.name} missed 3 rent payments. "
        "Their rent agreement has been revoked."
    )
    send_whatsapp_message(owner.profile.whatsapp_number, msg)
