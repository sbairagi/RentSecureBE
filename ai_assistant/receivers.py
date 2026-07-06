import logging

from django.dispatch import receiver

from ai_assistant.services.archive_service import archive_renter_data
from ai_assistant.services.invoice_service import generate_final_invoice_pdf
from properties.signals.renter_signals import renter_archived, renter_exited

logger = logging.getLogger(__name__)


@receiver(renter_exited)
def handle_renter_exit(
    sender: type, instance: object, latest_rent: object, **kwargs: object
) -> None:
    from properties.models import Renter, RentRecord

    if not isinstance(instance, Renter) or not isinstance(latest_rent, RentRecord):
        return

    try:
        pdf_path = generate_final_invoice_pdf(instance, latest_rent)
        instance.final_invoice_path = pdf_path
        instance.save(update_fields=["final_invoice_path"])
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Failed to generate final invoice for renter %s: %s", instance.id, exc
        )


@receiver(renter_archived)
def handle_renter_archive(sender: type, instance: object, **kwargs: object) -> None:
    from properties.models import Renter

    if not isinstance(instance, Renter):
        return

    try:
        archive_renter_data(instance)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to archive renter %s: %s", instance.id, exc)
