


# Notify Renter
from ai_assistant.services.whatsapp_service import send_whatsapp_message
from wealth_concierge_platform.models import RentRecord


def notify_renter_about_late_fee(rent: RentRecord, late_fee):
    msg = (
        f"⚠️ You've paid rent late by ₹{late_fee}.\n"
        f"This has been added to next month's rent.\n\nReason: {rent.adjustment_reason}"
    )
    send_whatsapp_message(rent.renter.whatsapp_number, msg)


# Notify Owner
def notify_owner_about_late_fee(rent: RentRecord, late_fee):
    msg = (
        f"ℹ️ Your renter paid rent late by ₹{late_fee} "
        f"({rent.adjustment_reason}). We've added this to their next month's rent."
    )
    send_whatsapp_message(rent.renter.property.owner.profile.whatsapp_number, msg)