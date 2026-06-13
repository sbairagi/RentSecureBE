import logging

from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import RentAgreementDraft

logger = logging.getLogger(__name__)


def send_signature_reminders():
    """Send reminders for rent agreements where the renter has not yet signed.

    ``RentRecord`` has no ``signature_status`` column — signature tracking
    lives on ``RentAgreementDraft``.  We query that model instead.
    """
    unsigned = RentAgreementDraft.objects.filter(
        renter_signed=False,
    ).select_related("renter")
    for draft in unsigned:
        phone = draft.renter.whatsapp_number or draft.renter.phone or ""
        if not phone:
            logger.warning(
                "No phone number for renter %s — skipping signature reminder",
                draft.renter_id,
            )
            continue
        try:
            send_whatsapp_message(
                phone, "🖊️ Reminder: Please sign your rent agreement."
            )
        except Exception as e:
            logger.error(
                "Failed to send signature reminder to renter %s: %s",
                draft.renter_id,
                e,
            )
