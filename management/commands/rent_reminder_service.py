from datetime import date
from typing import Any

from notification.services.notification_service import NotificationService


def send_rent_reminder(renter: Any, days_left: int) -> None:
    rent_due_date = date.today().replace(day=renter.rent_due_day)

    if days_left > 0:
        msg = f"📢 Reminder: Your rent of ₹{renter.monthly_rent} is due on {rent_due_date.strftime('%d %b')}. Please pay on time to avoid penalty."
    elif days_left == 0:
        msg = f"📆 Today is your rent due date ({rent_due_date.strftime('%d %b')}). Kindly complete payment."
    else:
        msg = f"⚠️ Rent payment is overdue since {rent_due_date.strftime('%d %b')}. Please pay immediately to avoid late fees."

    NotificationService().send_whatsapp_message(renter.phone, msg)
