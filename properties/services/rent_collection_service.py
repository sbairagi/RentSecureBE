"""Rent collection workflows.

The rules implemented here mirror the approved "Rent collection" concept:

* a rent record is **never deleted** — it is cancelled with a mandatory
  reason and stays visible for the audit trail;
* a settled (``paid``) or cancelled record is fully locked;
* a part payment is allowed while the month is **pending or overdue** and
  the unit allows part payments; the amount must be positive, must not
  exceed the remaining balance, and the paid-on date cannot be earlier
  than the rent due date;
* the last part settles the month and issues the settlement receipt.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from rest_framework.exceptions import ValidationError

from django.core.mail import EmailMessage
from django.utils import timezone

from documents.receipt import build_receipt, receipt_filename
from notification.services.whatsapp_service import send_whatsapp_message
from properties.models import RentRecord, RentRecordPart
from properties.services.receipt_service import (
    generate_rent_receipt_pdf,
    send_rent_part_receipt_email,
)

logger = logging.getLogger(__name__)

ZERO = Decimal("0")


def _format_money(value: Any) -> str:
    amount = int(Decimal(value or 0).quantize(Decimal("1")))
    return f"₹{amount:,}"


def _renter_phone(rent_record: RentRecord) -> str:
    renter = rent_record.renter
    if renter is None:
        return ""
    return getattr(renter, "whatsapp_number", "") or getattr(renter, "phone", "") or ""


def cancel_rent_record(rent_record: RentRecord, reason: str, user: Any) -> RentRecord:
    """Cancel a rent record with a mandatory reason.

    Args:
        rent_record: The record to cancel.
        reason: Why the record is being voided — required.
        user: The owner cancelling the record.

    Returns:
        The cancelled :class:`RentRecord`.

    Raises:
        ValidationError: When the record cannot be cancelled.
    """
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(
            {
                "error": (
                    "A reason is required so the ledger history explains the "
                    "cancellation."
                )
            }
        )

    status = str(rent_record.status or "").lower()
    if status == RentRecord.Status.CANCELLED:
        raise ValidationError({"error": "This rent record is already cancelled."})
    if status == RentRecord.Status.PAID:
        raise ValidationError(
            {
                "error": (
                    "This rent record is settled — money was received, so it cannot be "
                    "cancelled. Raise an adjustment instead."
                )
            }
        )
    if (rent_record.amount_paid or ZERO) > 0:
        raise ValidationError(
            {
                "error": (
                    f"Part payments of {_format_money(rent_record.amount_paid)} were "
                    "received against this record, so it can no longer be cancelled."
                )
            }
        )

    rent_record.status = RentRecord.Status.CANCELLED
    rent_record.cancel_reason = reason
    rent_record.cancelled_at = timezone.now()
    rent_record.cancelled_by = user
    rent_record.save(
        update_fields=[
            "status",
            "cancel_reason",
            "cancelled_at",
            "cancelled_by",
            "updated_at",
        ]
    )
    return rent_record


def record_part_payment(
    rent_record: RentRecord,
    *,
    amount: Decimal,
    paid_on: Any,
    payment_method: str,
    transaction_id: str = "",
    note: str = "",
    user: Any = None,
) -> RentRecordPart:
    """Record one instalment against a monthly rent record.

    Args:
        rent_record: The monthly record the part belongs to.
        amount: How much was received — positive, at most the balance.
        paid_on: When it was received — never before the due date.
        payment_method: Mode of payment for this part.
        transaction_id: Optional gateway / bank reference.
        note: Optional note for this part.
        user: The owner recording the part.

    Returns:
        The created :class:`RentRecordPart`.

    Raises:
        ValidationError: When the part cannot be recorded.
    """
    status = str(rent_record.status or "").lower()
    if status == RentRecord.Status.CANCELLED:
        raise ValidationError(
            {
                "error": (
                    "This rent record was cancelled, so no part payment can be "
                    "recorded."
                )
            }
        )
    if status == RentRecord.Status.PAID:
        raise ValidationError(
            {
                "error": (
                    "This rent record is already settled — there is no balance left to "
                    "split."
                )
            }
        )
    if not getattr(rent_record.unit, "allow_partial_payments", False):
        raise ValidationError(
            {
                "error": (
                    "Part payments are off for this unit. Turn them on in Unit details "
                    "to split the rent."
                )
            }
        )
    if amount is None or amount <= ZERO:
        raise ValidationError({"error": "Part amount must be greater than zero."})

    balance = rent_record.balance
    if amount > balance:
        raise ValidationError(
            {
                "error": (
                    f"A part cannot be larger than the remaining balance of "
                    f"{_format_money(balance)}."
                )
            }
        )
    if paid_on is not None and rent_record.due_date and paid_on < rent_record.due_date:
        raise ValidationError(
            {
                "error": (
                    "The paid-on date cannot be earlier than the rent due date "
                    f"({rent_record.due_date.strftime('%d %b %Y')})."
                )
            }
        )

    part = RentRecordPart.objects.create(
        rent_record=rent_record,
        amount=amount,
        paid_on=paid_on,
        payment_method=payment_method,
        transaction_id=transaction_id or "",
        note=note or "",
        created_by=user,
    )

    rent_record.amount_paid = (rent_record.amount_paid or ZERO) + amount
    rent_record.transaction_id = transaction_id or rent_record.transaction_id
    if rent_record.amount_paid >= rent_record.total_due:
        rent_record.status = RentRecord.Status.PAID
        rent_record.paid_on = paid_on
        rent_record.payment_method = payment_method
    rent_record.save(
        update_fields=[
            "amount_paid",
            "status",
            "paid_on",
            "payment_method",
            "transaction_id",
            "updated_at",
        ]
    )

    # Every part carries its own receipt — the renter is never left without
    # proof of what was paid.  A failed delivery must not undo the payment.
    _send_part_receipt(rent_record, part)
    return part


def _send_part_receipt(rent_record: RentRecord, part: RentRecordPart) -> bool:
    """Email the receipt of a part payment, swallowing delivery failures."""
    try:
        delivered = send_rent_part_receipt_email(rent_record, part)
    except Exception:  # pragma: no cover - defensive, the service catches
        logger.exception(
            "Failed to send the part receipt for rent %s part %s",
            rent_record.id,
            part.id,
        )
        return False
    if delivered:
        part.receipt_no = receipt_filename(rent_record, part)
        part.save(update_fields=["receipt_no", "updated_at"])
    return bool(delivered)


def send_rent_reminder(rent_record: RentRecord, user: Any = None) -> bool:
    """Nudge the renter for whatever balance is still left.

    Args:
        rent_record: The record to follow up on.
        user: The owner sending the reminder.

    Returns:
        ``True`` when the message was handed to WhatsApp.
    """
    balance = rent_record.balance
    if balance <= ZERO:
        raise ValidationError(
            {"error": "This rent record is settled — there is nothing to follow up on."}
        )

    phone = _renter_phone(rent_record)
    if not phone:
        raise ValidationError(
            {"error": "This renter has no phone number on file to remind."}
        )

    period = rent_record.due_date.strftime("%B %Y") if rent_record.due_date else ""
    message = (
        f"Hello {getattr(rent_record.renter, 'name', 'there')}, a gentle reminder that "
        f"{_format_money(balance)} of rent for {period} is still due"
        f" (due {rent_record.due_date.strftime('%d %b %Y')})."
    )
    sent = send_whatsapp_message(
        phone,
        message,
        user=user,
        rent_record=rent_record,
    )

    rent_record.last_reminded_at = timezone.now()
    rent_record.save(update_fields=["last_reminded_at", "updated_at"])
    return bool(sent)


def send_rent_receipt(rent_record: RentRecord, user: Any = None) -> bool:
    """Send the receipt the renter is owed to the renter.

    A settled month gets the settlement receipt; a month that is still
    open gets the receipt of the latest part.

    Args:
        rent_record: The record to send the receipt for.
        user: The owner sending the receipt.

    Returns:
        ``True`` when the receipt was sent.
    """
    renter = rent_record.renter
    if renter is None:
        raise ValidationError({"error": "This rent record has no renter to send to."})

    parts = list(rent_record.parts.all())
    part = None
    if parts and str(rent_record.status or "").lower() != RentRecord.Status.PAID:
        part = parts[-1]

    receipt = build_receipt(rent_record, part)
    pdf_bytes = generate_rent_receipt_pdf(rent_record, part)

    delivered = False
    email = getattr(renter, "email", "") or ""
    if email:
        period = rent_record.due_date.strftime("%B %Y") if rent_record.due_date else ""
        subject = f"Rent Receipt - {period} | {receipt.total_amount}"
        body = (
            f"Dear {getattr(renter, 'name', 'there')},\n\n"
            f"Please find attached your rent receipt for {period}.\n\n"
            f"Property: {rent_record.unit.unit}\n"
            f"Amount: {receipt.total_amount}\n"
            f"Date Paid: {receipt.paid_on}\n"
            f"Payment Status: {rent_record.get_status_display()}\n\n"
            f"Thank you for your timely payment!\n\n"
            f"Best regards,\n"
            f"RentSecure Team"
        )
        message = EmailMessage(
            subject=subject,
            body=body,
            from_email="no-reply@rentsecure.in",
            to=[email],
        )
        message.attach(
            receipt_filename(rent_record, part), pdf_bytes, "application/pdf"
        )
        message.send(fail_silently=True)
        delivered = True

    phone = _renter_phone(rent_record)
    if phone:
        share_message = (
            f"Hello {getattr(renter, 'name', 'there')}, your rent receipt for "
            f"{rent_record.due_date.strftime('%B %Y')} "
            f"({receipt.total_amount}) is ready."
        )
        try:
            send_whatsapp_message(
                phone,
                share_message,
                user=user,
                rent_record=rent_record,
            )
            delivered = True
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("Failed to share receipt on WhatsApp: %s", exc)

    rent_record.receipt_sent_at = timezone.now()
    rent_record.save(update_fields=["receipt_sent_at", "updated_at"])
    return delivered
