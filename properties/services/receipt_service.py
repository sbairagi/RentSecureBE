"""Rent receipt service.

Generates and sends monthly rent receipts to renters via email. Every
public function is fully typed and uses ``TypedDict`` for return shapes
so callers can rely on a stable contract.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from weasyprint import HTML

if TYPE_CHECKING:
    from properties.models import RentRecord

logger = logging.getLogger(__name__)


def generate_rent_receipt_pdf(rent_record: RentRecord) -> bytes:
    """Render the HTML receipt template to PDF bytes.

    Args:
        rent_record: The paid :class:`RentRecord` to render.

    Returns:
        The raw PDF bytes — callers can either attach to an email or
        persist to a ``FileField``.

    Raises:
        Exception: Re-raises the underlying rendering exception after
            logging context.
    """
    try:
        context: dict[str, Any] = {
            "rent": rent_record,
            "renter": rent_record.renter,
            "unit": rent_record.unit,
            "owner": rent_record.renter.unit.owner if rent_record.renter else None,
        }

        html_string: str = render_to_string("pdf/rent_receipt.html", context)
        html = HTML(string=html_string)
        pdf_bytes: bytes = html.write_pdf()
    except Exception as exc:
        logger.exception(
            "Failed to generate rent receipt PDF for rent %s: %s",
            rent_record.id,
            exc,
        )
        raise
    else:
        return pdf_bytes


def send_rent_receipt_email(rent_record: RentRecord) -> bool:
    """Send the rent receipt email with PDF attachment to the renter.

    Args:
        rent_record: The :class:`RentRecord` to email a receipt for.

    Returns:
        ``True`` on successful send, ``False`` otherwise.
    """
    renter = rent_record.renter

    if renter is None:
        logger.warning(
            "Renter is None for rent %s. Cannot send receipt.", rent_record.id
        )
        return False

    if not getattr(renter, "email", None):
        logger.warning(
            "Renter %s has no email. Cannot send receipt.", getattr(renter, "id", None)
        )
        return False

    try:
        pdf_bytes: bytes = generate_rent_receipt_pdf(rent_record)

        month_year: str = rent_record.due_date.strftime("%B %Y")
        subject: str = f"Rent Receipt - {month_year} | ₹{rent_record.amount}"

        body: str = (
            f"Dear {renter.name},\n\n"
            f"Please find attached your rent receipt for {month_year}.\n\n"
            f"Property: {rent_record.unit.unit}\n"
            f"Amount: ₹{rent_record.amount}\n"
            f"Date Paid: {rent_record.paid_on}\n"
            f"Payment Status: {rent_record.get_status_display()}\n\n"
            f"Thank you for your timely payment!\n\n"
            f"Best regards,\n"
            f"RentSecure Team"
        )

        email_to: list[str] = [renter.email] if renter.email else []
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email="no-reply@rentsecure.in",
            to=email_to,
        )

        receipt_month: str = rent_record.due_date.strftime("%Y%m")
        filename: str = f"rent_receipt_{rent_record.id}_{receipt_month}.pdf"
        email.attach(filename, pdf_bytes, "application/pdf")
        email.send(fail_silently=False)

        logger.info(
            "Rent receipt email sent to %s for rent %s", renter.email, rent_record.id
        )
    except Exception as exc:
        logger.exception(
            "Failed to send rent receipt email to %s: %s", renter.email, exc
        )
        return False
    else:
        return True


def send_rent_receipt_on_payment(rent_record: RentRecord) -> bool:
    """Send a receipt if (and only if) the rent record is fully paid.

    Args:
        rent_record: The :class:`RentRecord` to evaluate.

    Returns:
        ``True`` if the email was sent, ``False`` otherwise.
    """
    if rent_record.payment_status != "paid":
        logger.debug(
            "Rent %s not marked as PAID. Skipping receipt email.", rent_record.id
        )
        return False

    return send_rent_receipt_email(rent_record)
