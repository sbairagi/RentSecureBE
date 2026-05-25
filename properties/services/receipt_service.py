"""
Rent Receipt Service

Generates and sends monthly rent receipts to renters via email.
"""

import logging

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from weasyprint import HTML

from properties.models import RentRecord

logger = logging.getLogger(__name__)


def generate_rent_receipt_pdf(rent_record):
    """
    Generate a rent receipt PDF from a RentRecord.

    Args:
        rent_record: RentRecord instance

    Returns:
        bytes: PDF file content
    """
    try:
        context = {
            'rent': rent_record,
            'renter': rent_record.renter,
            'unit': rent_record.unit,
            'owner': rent_record.owner,
        }

        html_string = render_to_string('pdf/rent_receipt.html', context)
        html = HTML(string=html_string)
        pdf_bytes = html.write_pdf()

        return pdf_bytes
    except Exception as exc:
        logger.exception(
            f"Failed to generate rent receipt PDF for rent {rent_record.id}: {exc}"
        )
        raise


def send_rent_receipt_email(rent_record):
    """
    Send rent receipt email to renter with PDF attachment.

    Args:
        rent_record: RentRecord instance

    Returns:
        bool: True if email was sent successfully
    """
    renter = rent_record.renter

    # Check if renter has email
    if not renter.email:
        logger.warning(f"Renter {renter.id} has no email. Cannot send receipt.")
        return False

    try:
        # Generate PDF
        pdf_bytes = generate_rent_receipt_pdf(rent_record)

        # Build email
        month_year = rent_record.rent_month.strftime("%B %Y")
        subject = f"Rent Receipt - {month_year} | ₹{rent_record.amount_paid}"

        body = (
            f"Dear {renter.name},\n\n"
            f"Please find attached your rent receipt for {month_year}.\n\n"
            f"Property: {rent_record.unit.unit}\n"
            f"Amount: ₹{rent_record.amount_paid}\n"
            f"Date Paid: {rent_record.date_paid}\n"
            f"Payment Status: {rent_record.get_payment_status_display()}\n\n"
            f"Thank you for your timely payment!\n\n"
            f"Best regards,\n"
            f"RentSecure Team"
        )

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email="no-reply@rentsecure.in",
            to=[renter.email]
        )

        # Attach PDF
        filename = f"rent_receipt_{rent_record.id}_{rent_record.rent_month.strftime('%Y%m')}.pdf"
        email.attach(filename, pdf_bytes, 'application/pdf')

        # Send
        email.send(fail_silently=False)

        logger.info(f"Rent receipt email sent to {renter.email} for rent {rent_record.id}")
        return True

    except Exception as exc:
        logger.exception(f"Failed to send rent receipt email to {renter.email}: {exc}")
        return False


def send_rent_receipt_on_payment(rent_record):
    """
    Auto-send receipt when rent payment is marked as successful.

    Args:
        rent_record: RentRecord instance

    Returns:
        bool: True if email sent
    """
    if rent_record.payment_status != RentRecord.PaymentStatus.PAID:
        logger.debug(f"Rent {rent_record.id} not marked as PAID. Skipping receipt email.")
        return False

    return send_rent_receipt_email(rent_record)
